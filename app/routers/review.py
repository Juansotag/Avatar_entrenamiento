import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session as DBSession
from sqlmodel import select

from app.db import get_db
from app.models import Case, NegotiationSession, NonverbalSnapshot, Turn
from app.schemas import (
    CaseRead,
    CoachingReport,
    NonverbalSnapshotIn,
    NonverbalSummary,
    SessionListItem,
    SessionReviewResponse,
    TurnRead,
)

router = APIRouter(prefix="/api/sessions", tags=["review"])


@router.get("", response_model=list[SessionListItem])
def list_sessions(db: DBSession = Depends(get_db)) -> list[SessionListItem]:
    sessions = list(db.exec(select(NegotiationSession).order_by(NegotiationSession.started_at.desc())))
    items = []
    for session in sessions:
        case = db.get(Case, session.case_id)
        items.append(
            SessionListItem(
                session_id=session.id,
                case_title=case.title if case else "(caso eliminado)",
                started_at=session.started_at,
                status=session.status,
            )
        )
    return items


@router.get("/{session_id}", response_model=SessionReviewResponse)
def get_session_review(session_id: int, db: DBSession = Depends(get_db)) -> SessionReviewResponse:
    session = db.get(NegotiationSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")
    case = db.get(Case, session.case_id)

    turns = list(db.exec(select(Turn).where(Turn.session_id == session_id).order_by(Turn.turn_index)))
    transcript = [
        TurnRead(
            turn_index=t.turn_index,
            role=t.role,
            text=t.text,
            audio_url=f"/audio/{t.audio_path}" if t.audio_path else None,
            created_at=t.created_at,
        )
        for t in turns
    ]

    snapshots = list(
        db.exec(select(NonverbalSnapshot).where(NonverbalSnapshot.session_id == session_id).order_by(NonverbalSnapshot.ts_ms))
    )
    timeline = [
        NonverbalSnapshotIn(
            ts_ms=s.ts_ms,
            yaw=s.yaw,
            pitch=s.pitch,
            roll=s.roll,
            looking_at_camera=s.looking_at_camera,
            smile_score=s.smile_score,
            happiness=s.happiness,
            anger=s.anger,
            sadness=s.sadness,
            fear=s.fear,
            raw_json=s.raw_json,
        )
        for s in snapshots
    ]

    summary = None
    if session.nonverbal_summary_json:
        summary = NonverbalSummary(**json.loads(session.nonverbal_summary_json))

    coaching_report = None
    if session.coaching_report_json:
        try:
            coaching_report = CoachingReport(**json.loads(session.coaching_report_json))
        except Exception:
            pass  # Si el JSON no parsea, simplemente no se muestra el reporte

    return SessionReviewResponse(
        session_id=session.id,
        case=CaseRead.model_validate(case),
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        transcript=transcript,
        nonverbal_summary=summary,
        nonverbal_timeline=timeline,
        coaching_report=coaching_report,
    )
