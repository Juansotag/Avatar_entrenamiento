from datetime import datetime
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
    "# Persona: El Mandatario (arquetipo compuesto, ficticio)\n\n"
    "Este personaje es un arquetipo político compuesto, inventado para fines de "
    "entrenamiento. No representa, retrata, ni cita a ninguna persona real, viva o "
    "histórica. No tiene nombre propio dentro de la aplicacion: se le llama "
    "\"el Mandatario\" o \"el Presidente\".\n\n"
)

# ── Instrucciones fijas que siempre cierran el archivo ────────────────────────
_FILE_FOOTER = (
    "## Instrucciones para el modelo\n\n"
    "Responde siempre en español, en el personaje de El Mandatario, en primera persona. "
    "No rompas el personaje ni menciones que eres una inteligencia artificial. "
    "No inventes cifras oficiales específicas y verificables de ningún país real; "
    "si necesitas un dato, habla en términos generales (\"miles de familias\", "
    "\"una parte importante del sector\") en vez de cifras falsas y precisas. "
    "Basa tus posiciones de política pública en los temas descritos en los archivos "
    "de app/data/policy_snippets, no en hechos atribuidos a un mandatario real.\n"
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
        lower = block.lower()
        if lower.startswith("perfil"):
            sections["perfil"] = block[len("perfil"):].strip()
        elif lower.startswith("tono"):
            sections["tono_estilo"] = block[block.index("\n"):].strip()
        elif lower.startswith("reglas"):
            sections["reglas"] = block[block.index("\n"):].strip()

    return sections


def _build_persona_brief(perfil: str, tono_estilo: str, reglas: str) -> str:
    """Reconstruye el contenido de persona_brief.md desde los campos estructurados."""
    return (
        _FILE_HEADER
        + "## Perfil\n\n" + perfil.strip() + "\n\n"
        + "## Tono y estilo de habla\n\n" + tono_estilo.strip() + "\n\n"
        + "## Reglas de negociación\n\n" + reglas.strip() + "\n\n"
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
    profile.updated_at = datetime.utcnow()
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
    content = _build_persona_brief(
        perfil=payload.perfil,
        tono_estilo=payload.tono_estilo,
        reglas=payload.reglas,
    )
    _PERSONA_BRIEF_PATH.write_text(content, encoding="utf-8")
    return AvatarProfileRead(
        perfil=payload.perfil,
        tono_estilo=payload.tono_estilo,
        reglas=payload.reglas,
    )
