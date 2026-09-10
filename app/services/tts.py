from openai import OpenAI
from typing import Optional

from app.config import get_settings

settings = get_settings()
_client: Optional[OpenAI] = None


def _client_instance() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def synthesize_speech(text: str, voice: Optional[str] = None) -> bytes:
    """Genera audio a partir de texto via la API de TTS de OpenAI.

    Usa el modelo tts-1 (optimizado para baja latencia en tiempo real).
    Soporta selección de voz dinámica según el perfil y género del avatar:
    - Femeninas: nova, shimmer
    - Masculinas: onyx, echo
    - Neutras: alloy, fable

    NOTA: el audio devuelto está en formato mp3.
    """
    selected_voice = voice or settings.openai_tts_voice
    response = _client_instance().audio.speech.create(
        model="tts-1",
        voice=selected_voice,
        input=text,
        response_format="mp3",
    )
    return response.content
