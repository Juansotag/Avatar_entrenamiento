import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session as DBSession
from sqlmodel import select

from app.config import get_settings
from app.db import get_db, engine
from app.models import Case, NegotiationSession, NegotiatorProfile, NonverbalSnapshot, Turn
from app.schemas import (
    CaseRead,
    NonverbalBatchIn,
    NonverbalSummary,
    SessionEndResponse,
    SessionStartResponse,
    TurnRead,
    TurnResponse,
)
from app.services import llm, stt, tts, coach

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _save_audio(session_id: int, turn_index: int, role: str, data: bytes, ext: str) -> str:
    session_dir = settings.audio_storage_dir / str(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{turn_index}_{role}.{ext}"
    (session_dir / filename).write_bytes(data)
    return f"{session_id}/{filename}"


def _audio_url(audio_path: Optional[str]) -> Optional[str]:
    return f"/audio/{audio_path}" if audio_path else None


def _synthesize_or_none(text: str, session_id: int, turn_index: int) -> Optional[str]:
    """La voz del personaje es un extra, no algo que deba tumbar la conversacion si
    OpenAI TTS no esta configurado o falla. Si falla, se sigue solo con texto."""
    if not settings.openai_api_key:
        return None
    try:
        audio_bytes = tts.synthesize_speech(text)
        return _save_audio(session_id, turn_index, "persona", audio_bytes, "mp3")
    except Exception:
        logger.exception("TTS fallo para session_id=%s turn_index=%s, se sigue solo con texto", session_id, turn_index)
        return None


def _get_negotiator_info(db: DBSession) -> Optional[dict]:
    """Obtiene los datos del perfil del negociante si están diligenciados."""
    profile = db.exec(select(NegotiatorProfile)).first()
    if not profile:
        return None
    info = {
        "name": (profile.name or "").strip(),
        "role": (profile.role or "").strip(),
        "organization": (profile.organization or "").strip(),
        "objectives": (profile.objectives or "").strip(),
    }
    return info if any(info.values()) else None


@router.post("", response_model=SessionStartResponse)
def start_session(case_id: int, db: DBSession = Depends(get_db)) -> SessionStartResponse:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    session = NegotiationSession(case_id=case_id)
    db.add(session)
    db.commit()
    db.refresh(session)

    # Capturar variables del caso y perfil del usuario antes de cerrar el session db
    scenario_text = case.scenario_text
    persona_notes = case.persona_notes
    avatar_name = case.avatar_name
    session_id = session.id
    duration_seconds = case.duration_seconds or settings.session_duration_seconds
    case_read = CaseRead.model_validate(case)
    negotiator_info = _get_negotiator_info(db)
    db.close()

    # Llamadas a APIs externas
    opening_text = llm.generate_opening_line(
        scenario_text, persona_notes, avatar_name, negotiator_info=negotiator_info
    )
    audio_path = _synthesize_or_none(opening_text, session_id, 0)

    # Registrar el turno en la DB en una transacción corta
    opening_turn = Turn(
        session_id=session_id,
        turn_index=0,
        role="persona",
        text=opening_text,
        audio_path=audio_path,
    )
    with DBSession(engine) as write_db:
        write_db.add(opening_turn)
        write_db.commit()
        write_db.refresh(opening_turn)
        
        turn_index = opening_turn.turn_index
        role = opening_turn.role
        text = opening_turn.text
        audio_url = _audio_url(opening_turn.audio_path)
        created_at = opening_turn.created_at

    return SessionStartResponse(
        session_id=session_id,
        case=case_read,
        duration_seconds=duration_seconds,
        opening_turn=TurnRead(
            turn_index=turn_index,
            role=role,
            text=text,
            audio_url=audio_url,
            created_at=created_at,
        ),
    )


@router.post("/{session_id}/turns", response_model=TurnResponse)
def submit_turn(
    session_id: int,
    audio: Optional[UploadFile] = File(default=None),
    text: Optional[str] = Form(default=None),
    remaining_seconds: Optional[int] = Form(default=None),
    request_extension: bool = Form(default=False),
    db: DBSession = Depends(get_db),
) -> TurnResponse:
    session = db.get(NegotiationSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")
    if session.status != "active":
        raise HTTPException(status_code=409, detail="La sesion ya termino")

    case = db.get(Case, session.case_id)
    scenario_text = case.scenario_text
    persona_notes = case.persona_notes
    avatar_name = case.avatar_name

    prior_turns = list(
        db.exec(
            select(Turn).where(Turn.session_id == session_id).order_by(Turn.turn_index)
        )
    )
    next_index = len(prior_turns)
    stored_turns = [(t.role, t.text) for t in prior_turns]
    
    # Cerrar la sesión para liberar bloqueos antes del procesamiento lento
    negotiator_info = _get_negotiator_info(db)
    db.close()

    # 1. Procesar transcripción si es necesario (llamada de red larga a Whisper)
    if text and text.strip():
        user_text = text.strip()
        user_audio_path = None
    elif audio is not None:
        audio_bytes = audio.file.read()
        user_text = stt.transcribe_audio(audio_bytes, filename=audio.filename or "turn.webm")
        ext = (audio.filename or "turn.webm").rsplit(".", 1)[-1]
        user_audio_path = _save_audio(session_id, next_index, "user", audio_bytes, ext)
    else:
        raise HTTPException(status_code=400, detail="Hay que enviar audio o texto")

    # 2. Guardar el turno del usuario en una transacción corta
    user_turn = Turn(
        session_id=session_id,
        turn_index=next_index,
        role="user",
        text=user_text,
        audio_path=user_audio_path,
    )
    with DBSession(engine) as write_db:
        # Validar de nuevo que la sesión siga activa antes de escribir
        sess = write_db.get(NegotiationSession, session_id)
        if sess is None:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        if sess.status != "active":
            raise HTTPException(status_code=409, detail="La sesión ya terminó")
        write_db.add(user_turn)
        write_db.commit()

    # 3. Generar respuesta de Claude (llamada de red larga) con información de tiempo y extensión si aplica
    time_context = None
    if remaining_seconds is not None:
        mins = remaining_seconds // 60
        secs = remaining_seconds % 60
        time_context = f"\n\n[Nota del sistema: Quedan {mins} minutos y {secs} segundos para finalizar la conversación.]"
        
    if request_extension:
        mins = (remaining_seconds or 0) // 60
        secs = (remaining_seconds or 0) % 60
        time_context = (time_context or "") + (
            f"\n\n[INSTRUCCIÓN DE SISTEMA: El interlocutor está solicitando formalmente una extensión del tiempo de la conversación/reunión. "
            f"Evalúa el desarrollo de la interacción hasta este momento (si el interlocutor ha sido constructivo, empático, respetuoso "
            f"y ha presentado argumentos, propuestas o inquietudes lógicas acordes a la situación):"
            f"\n1. Si consideras que el interlocutor se ha desempeñado mal, ha sido evasivo, hostil, negligente o irrespetuoso, rechaza la extensión (0 segundos adicionales)."
            f"\n2. Si la interacción va por buen camino o requiere un poco más de tiempo, puedes otorgarle un minuto adicional (60 segundos)."
            f"\n3. Si quedan 30 segundos o menos para terminar la reunión (tiempo restante actual: {mins} min {secs} seg) y el interlocutor "
            f"ha hecho un trabajo excelente y constructivo, puedes conceder hasta 5 minutos adicionales (300 segundos)."
            f"\n\nResponde en tu rol y estilo de {avatar_name}. Al final de tu respuesta, de forma obligatoria, "
            f"escribe el tag XML con el valor que hayas decidido: <granted_seconds>NUM_SEGUNDOS</granted_seconds> "
            f"(donde NUM_SEGUNDOS debe ser un entero como 0, 60 o hasta 300).]"
        )

    persona_text = llm.generate_reply(
        scenario_text,
        persona_notes,
        stored_turns,
        user_text,
        avatar_name,
        time_context=time_context,
        negotiator_info=negotiator_info,
    )
    
    # Parsear y limpiar granted_seconds
    import re
    granted_seconds = 0
    match = re.search(r'<granted_seconds>(\d+)</granted_seconds>', persona_text)
    if match:
        try:
            granted_seconds = int(match.group(1))
        except ValueError:
            pass
        persona_text = re.sub(r'<granted_seconds>\d+</granted_seconds>', '', persona_text).strip()

    persona_index = next_index + 1
    persona_audio_path = _synthesize_or_none(persona_text, session_id, persona_index)

    # 4. Guardar el turno de la persona en una transacción corta
    persona_turn = Turn(
        session_id=session_id,
        turn_index=persona_index,
        role="persona",
        text=persona_text,
        audio_path=persona_audio_path,
    )
    with DBSession(engine) as write_db:
        sess = write_db.get(NegotiationSession, session_id)
        if sess is not None and sess.status == "active":
            write_db.add(persona_turn)
            write_db.commit()

    return TurnResponse(
        turn_index=persona_index,
        user_text=user_text,
        persona_text=persona_text,
        persona_audio_url=_audio_url(persona_audio_path),
        granted_seconds=granted_seconds,
    )


@router.post("/{session_id}/nonverbal")
def submit_nonverbal(session_id: int, payload: NonverbalBatchIn, db: DBSession = Depends(get_db)) -> dict:
    session = db.get(NegotiationSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")

    for snap in payload.snapshots:
        db.add(
            NonverbalSnapshot(
                session_id=session_id,
                ts_ms=snap.ts_ms,
                yaw=snap.yaw,
                pitch=snap.pitch,
                roll=snap.roll,
                looking_at_camera=snap.looking_at_camera,
                smile_score=snap.smile_score,
                happiness=snap.happiness,
                anger=snap.anger,
                sadness=snap.sadness,
                fear=snap.fear,
                raw_json=snap.raw_json,
            )
        )
    db.commit()
    return {"received": len(payload.snapshots)}


def compute_nonverbal_summary(db: DBSession, session_id: int) -> NonverbalSummary:
    snapshots = list(
        db.exec(select(NonverbalSnapshot).where(NonverbalSnapshot.session_id == session_id))
    )
    if not snapshots:
        return NonverbalSummary(
            sample_count=0,
            pct_looking_at_camera=0.0,
            avg_yaw_abs=0.0,
            avg_pitch_abs=0.0,
            avg_smile_score=None,
            pct_happiness=0.0,
            pct_anger=0.0,
            pct_sadness=0.0,
            pct_fear=0.0,
        )

    n = len(snapshots)
    pct_looking = 100.0 * sum(1 for s in snapshots if s.looking_at_camera) / n
    avg_yaw_abs = sum(abs(s.yaw) for s in snapshots) / n
    avg_pitch_abs = sum(abs(s.pitch) for s in snapshots) / n
    smile_scores = [s.smile_score for s in snapshots if s.smile_score is not None]
    avg_smile = (sum(smile_scores) / len(smile_scores)) if smile_scores else None

    # Emotion calculations (percentage of time spent with emotion > 0.05 to capture micro-expressions)
    pct_happiness = 100.0 * sum(1 for s in snapshots if s.happiness and s.happiness > 0.05) / n
    pct_anger = 100.0 * sum(1 for s in snapshots if s.anger and s.anger > 0.05) / n
    pct_sadness = 100.0 * sum(1 for s in snapshots if s.sadness and s.sadness > 0.05) / n
    pct_fear = 100.0 * sum(1 for s in snapshots if s.fear and s.fear > 0.05) / n

    return NonverbalSummary(
        sample_count=n,
        pct_looking_at_camera=round(pct_looking, 1),
        avg_yaw_abs=round(avg_yaw_abs, 2),
        avg_pitch_abs=round(avg_pitch_abs, 2),
        avg_smile_score=round(avg_smile, 3) if avg_smile is not None else None,
        pct_happiness=round(pct_happiness, 1),
        pct_anger=round(pct_anger, 1),
        pct_sadness=round(pct_sadness, 1),
        pct_fear=round(pct_fear, 1),
    )


@router.post("/{session_id}/end", response_model=SessionEndResponse)
def end_session(session_id: int, db: DBSession = Depends(get_db)) -> SessionEndResponse:
    from datetime import datetime

    session = db.get(NegotiationSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")

    # 1. Calcular resumen de lenguaje no verbal
    summary = compute_nonverbal_summary(db, session_id)
    summary_json = summary.model_dump_json()

    # 2. Generar informe de coaching con Claude (extended thinking)
    case = db.get(Case, session.case_id)
    scenario_text = case.scenario_text if case else ""
    avatar_name = case.avatar_name if case else "la contraparte"
    all_turns = list(db.exec(select(Turn).where(Turn.session_id == session_id).order_by(Turn.turn_index)))
    turns_for_coach = [(t.role, t.text) for t in all_turns]
    negotiator_info = _get_negotiator_info(db)

    # Cerrar la sesión de DB para liberar bloqueos durante la llamada larga de Claude Coaching
    db.close()

    coaching_report_json = None
    try:
        coaching_data = coach.analyze_session(
            scenario_text=scenario_text,
            turns=turns_for_coach,
            negotiator_info=negotiator_info,
            avatar_name=avatar_name,
        )
        import json
        coaching_report_json = json.dumps(coaching_data, ensure_ascii=False)
    except Exception:
        logger.exception("El análisis de coaching falló para session_id=%s, se continúa sin él", session_id)

    # 3. Marcar sesión como completada en una transacción corta
    with DBSession(engine) as write_db:
        sess = write_db.get(NegotiationSession, session_id)
        if sess is not None:
            sess.nonverbal_summary_json = summary_json
            if coaching_report_json is not None:
                sess.coaching_report_json = coaching_report_json
            sess.status = "completed"
            sess.ended_at = datetime.utcnow()
            write_db.add(sess)
            write_db.commit()
            status = sess.status
        else:
            status = "completed"

    return SessionEndResponse(session_id=session_id, status=status, nonverbal_summary=summary)
