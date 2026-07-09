from io import BytesIO
from typing import Optional

from openai import OpenAI

from app.config import get_settings

settings = get_settings()
_client: Optional[OpenAI] = None


def _client_instance() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def clean_transcription(text: str) -> str:
    cleaned = text.strip()
    lower = cleaned.lower()
    # Eliminar alucinaciones comunes de Whisper en silencios
    if "amara.org" in lower:
        if any(msg in lower for msg in ["subtítulos", "subtitulos", "comunidad", "amara"]):
            return ""
        cleaned = cleaned.replace("Subtítulos realizados por la comunidad de Amara.org", "")
        cleaned = cleaned.replace("Subtítulos por la comunidad de Amara.org", "")
        cleaned = cleaned.replace("Subtítulos por Amara.org", "")
        cleaned = cleaned.replace("subtítulos por amara.org", "")
    
    # Eliminar palabras sueltas comunes generadas por ruido/silencio
    if cleaned.lower().strip(" .,!?¿¡") in {"gracias", "¡gracias!", "thank you", "thank you.", "yeah", "o", "a", "as"}:
        return ""
    return cleaned.strip()


def transcribe_audio(audio_bytes: bytes, filename: str = "turn.webm") -> str:
    """Transcribe el audio del usuario a texto via la API de Whisper de OpenAI.

    NOTA: el nombre exacto del modelo de transcripcion de OpenAI ha cambiado
    entre lanzamientos (whisper-1 y modelos mas nuevos). Verificar el nombre
    vigente contra la documentacion de OpenAI antes de la demo si esto falla
    con un error de "modelo no encontrado".
    """
    buffer = BytesIO(audio_bytes)
    buffer.name = filename
    transcript = _client_instance().audio.transcriptions.create(
        model="whisper-1",
        file=buffer,
        language="es",
    )
    return clean_transcription(transcript.text)
