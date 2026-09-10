from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.utcnow()


class Case(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # 1. Faceta Escenario
    title: str
    scenario_text: str
    duration_seconds: int = Field(default=300)
    created_at: datetime = Field(default_factory=utcnow)

    # 2. Faceta Negociante (Tú)
    user_name: Optional[str] = Field(default="")
    user_role: Optional[str] = Field(default="")
    user_organization: Optional[str] = Field(default="")
    user_objectives: Optional[str] = Field(default="")

    # 3. Faceta Contraparte (Avatar)
    avatar_name: str = Field(default="Contraparte")
    avatar_profile: Optional[str] = Field(default=None)
    avatar_tone: Optional[str] = Field(default=None)
    avatar_rules: Optional[str] = Field(default=None)
    persona_notes: Optional[str] = Field(default=None)


class NegotiationSession(SQLModel, table=True):
    """Una sesión de negociación. Se llama NegotiationSession (no Session) para no
    chocar con sqlmodel.Session, que se usa para las conexiones a la base de datos."""

    __tablename__ = "session"

    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id")
    started_at: datetime = Field(default_factory=utcnow)
    ended_at: Optional[datetime] = None
    status: str = Field(default="active")  # "active" | "completed"
    nonverbal_summary_json: Optional[str] = None
    coaching_report_json: Optional[str] = None  # JSON con el análisis de coaching de Claude


class Turn(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id")
    turn_index: int
    role: str  # "user" | "persona"
    text: str
    audio_path: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class NonverbalSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id")
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


class NegotiatorProfile(SQLModel, table=True):
    """Perfil del negociante (usuario). Un solo registro editable (id=1)."""

    __tablename__ = "negotiatorprofile"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(default="")
    role: str = Field(default="")           # cargo / rol
    organization: str = Field(default="")  # empresa u organización
    objectives: str = Field(default="")    # objetivos y contexto de negociación
    updated_at: datetime = Field(default_factory=utcnow)
