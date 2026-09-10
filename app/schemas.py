from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class CaseCreate(BaseModel):
    title: str
    scenario_text: str
    persona_notes: Optional[str] = None
    avatar_name: Optional[str] = "El Mandatario"
    duration_seconds: Optional[int] = 300


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    scenario_text: Optional[str] = None
    persona_notes: Optional[str] = None
    avatar_name: Optional[str] = None
    duration_seconds: Optional[int] = None


class CaseRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    scenario_text: str
    persona_notes: Optional[str]
    avatar_name: str
    duration_seconds: int
    created_at: datetime


class TurnRead(BaseModel):
    turn_index: int
    role: str
    text: str
    audio_url: Optional[str] = None
    created_at: datetime


class SessionStartResponse(BaseModel):
    session_id: int
    case: CaseRead
    duration_seconds: int
    opening_turn: TurnRead


class TurnResponse(BaseModel):
    turn_index: int
    user_text: str
    persona_text: str
    persona_audio_url: Optional[str]
    granted_seconds: int = 0


class NonverbalSnapshotIn(BaseModel):
    ts_ms: int
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    looking_at_camera: bool = False
    smile_score: Optional[float] = None
    happiness: Optional[float] = None
    anger: Optional[float] = None
    sadness: Optional[float] = None
    fear: Optional[float] = None
    raw_json: Optional[str] = None


class NonverbalBatchIn(BaseModel):
    snapshots: list[NonverbalSnapshotIn]


class NonverbalSummary(BaseModel):
    sample_count: int
    pct_looking_at_camera: float
    avg_yaw_abs: float
    avg_pitch_abs: float
    avg_smile_score: Optional[float]
    pct_happiness: float = 0.0
    pct_anger: float = 0.0
    pct_sadness: float = 0.0
    pct_fear: float = 0.0


class SessionEndResponse(BaseModel):
    session_id: int
    status: str
    nonverbal_summary: NonverbalSummary


# ─── Coaching Report (generado por Claude al finalizar la sesión) ─────────────

class CoachingStrength(BaseModel):
    titulo: str
    descripcion: str
    cita_usuario: str


class CoachingImprovementArea(BaseModel):
    titulo: str
    descripcion: str
    cita_usuario: str
    sugerencia_reformulacion: str


class CoachingReport(BaseModel):
    score: Optional[int] = None
    resultado_final: Optional[str] = None
    resumen_ejecutivo: str = ""
    fortalezas: list[CoachingStrength] = []
    areas_de_mejora: list[CoachingImprovementArea] = []
    tacticas_efectivas: list[str] = []
    oportunidades_perdidas: list[str] = []
    recomendacion_principal: str = ""


# ─── Review Response (pantalla de revisión post-sesión) ───────────────────────

class SessionReviewResponse(BaseModel):
    session_id: int
    case: Optional[CaseRead] = None
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    transcript: list[TurnRead]
    nonverbal_summary: Optional[NonverbalSummary]
    nonverbal_timeline: list[NonverbalSnapshotIn]
    coaching_report: Optional[CoachingReport] = None  # Informe de coaching de Claude


class SessionListItem(BaseModel):
    session_id: int
    case_title: str
    started_at: datetime
    status: str


# ─── Perfiles ─────────────────────────────────────────────────────────────────

class NegotiatorProfileRead(BaseModel):
    id: int
    name: str
    role: str
    organization: str
    objectives: str
    updated_at: datetime


class NegotiatorProfileUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    organization: Optional[str] = None
    objectives: Optional[str] = None


class AvatarProfileRead(BaseModel):
    perfil: str          # ## Perfil
    tono_estilo: str     # ## Tono y estilo de habla
    reglas: str          # ## Reglas de negociación


class AvatarProfileUpdate(BaseModel):
    perfil: str
    tono_estilo: str
    reglas: str
