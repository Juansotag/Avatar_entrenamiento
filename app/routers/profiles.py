from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session as DBSession
from sqlmodel import select

from app.config import get_settings
from app.db import get_db
from app.models import NegotiatorProfile
from app.schemas import (
    AvatarProfileRead,
    AvatarProfileUpdate,
    NegotiatorProfileRead,
    NegotiatorProfileUpdate,
)

router = APIRouter(prefix="/api/profiles", tags=["profiles"])
settings = get_settings()

_PERSONA_BRIEF_PATH = settings.data_dir / "persona_brief.md"

# ── Cabecera fija del archivo ──────────────────────────────────────────────────
_FILE_HEADER = (
    "# Perfil de Contraparte / Avatar de Entrenamiento\n\n"
    "Este personaje representa a la contraparte en la simulación de negociación o conversación difícil. "
    "Ha sido configurado para fines de entrenamiento profesional.\n\n"
)

# ── Instrucciones fijas que siempre cierran el archivo ────────────────────────
_FILE_FOOTER = (
    "## Instrucciones para el modelo\n\n"
    "Responde siempre en español, asumiendo estrictamente el personaje y rol de la contraparte descrita, en primera persona. "
    "No rompas el personaje ni menciones que eres una inteligencia artificial. "
    "Adapta tus reacciones, objeciones y demandas de manera coherente con el escenario, tu perfil y tus reglas de interacción. "
    "Mantén una actitud realista y constructivamente desafiante acorde a la situación planteada.\n"
)


def _parse_persona_brief() -> dict[str, str]:
    """Lee persona_brief.md y extrae las secciones estructuradas."""
    if not _PERSONA_BRIEF_PATH.exists():
        return {"perfil": "", "tono_estilo": "", "reglas": ""}

    text = _PERSONA_BRIEF_PATH.read_text(encoding="utf-8")
    sections: dict[str, str] = {"perfil": "", "tono_estilo": "", "reglas": ""}

    import re
    blocks = re.split(r"^##\s+", text, flags=re.MULTILINE)
    for block in blocks:
        parts = block.split("\n", 1)
        header = parts[0].strip().lower()
        body = parts[1].strip() if len(parts) > 1 else ""
        if header.startswith("perfil"):
            sections["perfil"] = body
        elif header.startswith("tono"):
            sections["tono_estilo"] = body
        elif header.startswith("reglas"):
            sections["reglas"] = body

    return sections


def _build_persona_brief(perfil: str, tono_estilo: str, reglas: str) -> str:
    """Reconstruye el contenido de persona_brief.md desde los campos estructurados."""
    return (
        _FILE_HEADER
        + "## Perfil\n\n" + perfil.strip() + "\n\n"
        + "## Tono y estilo de habla\n\n" + tono_estilo.strip() + "\n\n"
        + "## Reglas de interacción\n\n" + reglas.strip() + "\n\n"
        + _FILE_FOOTER
    )


# ─── Negociante ───────────────────────────────────────────────────────────────

@router.get("/negotiator", response_model=NegotiatorProfileRead)
def get_negotiator_profile(db: DBSession = Depends(get_db)) -> NegotiatorProfile:
    profile = db.exec(select(NegotiatorProfile)).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil de negociante no encontrado")
    return profile


@router.put("/negotiator", response_model=NegotiatorProfileRead)
def update_negotiator_profile(
    payload: NegotiatorProfileUpdate, db: DBSession = Depends(get_db)
) -> NegotiatorProfile:
    profile = db.exec(select(NegotiatorProfile)).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil de negociante no encontrado")
    if payload.name is not None:
        profile.name = payload.name
    if payload.role is not None:
        profile.role = payload.role
    if payload.organization is not None:
        profile.organization = payload.organization
    if payload.objectives is not None:
        profile.objectives = payload.objectives
    profile.updated_at = datetime.now(timezone.utc)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


# ─── Avatar ───────────────────────────────────────────────────────────────────

@router.get("/avatar", response_model=AvatarProfileRead)
def get_avatar_profile() -> AvatarProfileRead:
    sections = _parse_persona_brief()
    return AvatarProfileRead(**sections)


@router.put("/avatar", response_model=AvatarProfileRead)
def update_avatar_profile(payload: AvatarProfileUpdate) -> AvatarProfileRead:
    from app.services.persona import clear_persona_cache

    content = _build_persona_brief(
        perfil=payload.perfil,
        tono_estilo=payload.tono_estilo,
        reglas=payload.reglas,
    )
    _PERSONA_BRIEF_PATH.write_text(content, encoding="utf-8")
    clear_persona_cache()
    return AvatarProfileRead(
        perfil=payload.perfil,
        tono_estilo=payload.tono_estilo,
        reglas=payload.reglas,
    )
