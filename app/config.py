from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    # Voz para TTS de OpenAI. Opciones: alloy, echo, fable, onyx, nova, shimmer.
    # 'onyx' es grave y profesional, ideal para avatar de negociación.
    openai_tts_voice: str = "onyx"

    # Modelo para diálogo en vivo (alta velocidad de respuesta y roleplay nítido)
    dialogue_model_name: str = "claude-3-5-sonnet-20241022"

    # Modelo para análisis exhaustivo de coaching post-sesión (con extended thinking)
    coaching_model_name: str = "claude-opus-4-8"

    # Modelo principal retrocompatible
    model_name: str = "claude-3-5-sonnet-20241022"

    # Presupuesto de tokens de pensamiento extendido para el análisis de coaching.
    # 8000 es suficiente para sesiones de 5 min; aumentar para análisis más profundos.
    coaching_thinking_budget: int = 8000

    database_url: str = f"sqlite:///{BASE_DIR / 'storage.db'}"

    audio_storage_dir: Path = BASE_DIR / "app" / "storage" / "audio"
    session_duration_seconds: int = 300  # 5 minutos

    data_dir: Path = BASE_DIR / "app" / "data"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.audio_storage_dir.mkdir(parents=True, exist_ok=True)
    return settings
