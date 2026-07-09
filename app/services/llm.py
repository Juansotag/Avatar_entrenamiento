from typing import Generator, Optional

from anthropic import Anthropic

from app.config import get_settings
from app.services.persona import get_persona_system_prompt
from app.services.rag import get_relevant_context

settings = get_settings()
_client: Optional[Anthropic] = None


def _client_instance() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def build_system_prompt(
    scenario_text: str,
    persona_notes: Optional[str],
    query: str,
    avatar_name: str = "El Mandatario",
    time_context: Optional[str] = None,
) -> str:
    context_snippets = get_relevant_context(query)
    persona_prompt = get_persona_system_prompt()
    if avatar_name and avatar_name != "El Mandatario":
        persona_prompt = (
            persona_prompt
            .replace("El Mandatario", avatar_name)
            .replace("el Mandatario", avatar_name)
            .replace("El Presidente", avatar_name)
            .replace("el Presidente", avatar_name)
            .replace("Nicasio Páez", avatar_name)
        )
    parts = [persona_prompt]
    parts.append("\n## Caso de negociación\n" + scenario_text)
    if persona_notes:
        parts.append("\n## Notas adicionales sobre el personaje para este caso\n" + persona_notes)
    if context_snippets:
        parts.append(
            "\n## Contexto de política pública relevante\n" + "\n\n---\n\n".join(context_snippets)
        )
    if time_context:
        parts.append(time_context)
    return "\n".join(parts)


def _build_messages(stored_turns: list[tuple[str, str]], user_message: Optional[str] = None) -> list[dict]:
    """Construye la lista de mensajes para la API de Claude.

    La API exige que el primer mensaje sea 'user' y que los roles alternen.
    Se antepone la instrucción de apertura sintética (nunca visible al usuario).
    """
    messages: list[dict] = [{"role": "user", "content": OPENING_INSTRUCTION}]
    for role, text in stored_turns:
        messages.append({
            "role": "assistant" if role == "persona" else "user",
            "content": text,
        })
    if user_message:
        messages.append({"role": "user", "content": user_message})
    return messages


# Instrucción sintética de apertura (nunca se guarda ni muestra en la transcripción)
OPENING_INSTRUCTION = (
    "Estás a punto de recibir a un empresario en tu despacho para negociar sobre "
    "el caso descrito arriba. Abre la reunión en persona, en dos o tres frases, tal "
    "como lo haría El Mandatario: directo, sin rodeos, dejando claro que escucha "
    "pero no regala nada."
)


def generate_opening_line(scenario_text: str, persona_notes: Optional[str], avatar_name: str = "El Mandatario") -> str:
    """Genera la línea de apertura del personaje al comenzar la sesión."""
    system_prompt = build_system_prompt(scenario_text, persona_notes, query=scenario_text, avatar_name=avatar_name)
    message = _client_instance().messages.create(
        model=settings.model_name,
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": OPENING_INSTRUCTION}],
    )
    for block in message.content:
        if block.type == "text":
            return block.text
    return ""


def generate_reply(
    scenario_text: str,
    persona_notes: Optional[str],
    stored_turns: list[tuple[str, str]],
    user_message: str,
    avatar_name: str = "El Mandatario",
    time_context: Optional[str] = None,
) -> str:
    """Genera la respuesta del personaje en un turno dado.

    stored_turns: lista de (role, text) tal como se guardaron en la DB,
    empezando desde la línea de apertura del personaje (role='persona').
    """
    system_prompt = build_system_prompt(scenario_text, persona_notes, query=user_message, avatar_name=avatar_name, time_context=time_context)
    messages = _build_messages(stored_turns, user_message)

    message = _client_instance().messages.create(
        model=settings.model_name,
        max_tokens=5000,
        system=system_prompt,
        messages=messages,
    )
    for block in message.content:
        if block.type == "text":
            return block.text
    return ""


def generate_reply_stream(
    scenario_text: str,
    persona_notes: Optional[str],
    stored_turns: list[tuple[str, str]],
    user_message: str,
    avatar_name: str = "El Mandatario",
    time_context: Optional[str] = None,
) -> Generator[str, None, None]:
    """Igual que generate_reply pero en modo streaming.

    Hace yield de cada fragmento de texto (delta) a medida que Claude lo genera.
    El caller puede transmitirlo al frontend mediante SSE o WebSocket.
    """
    system_prompt = build_system_prompt(scenario_text, persona_notes, query=user_message, avatar_name=avatar_name, time_context=time_context)
    messages = _build_messages(stored_turns, user_message)

    with _client_instance().messages.stream(
        model=settings.model_name,
        max_tokens=5000,
        system=system_prompt,
        messages=messages,
    ) as stream:
        for text_chunk in stream.text_stream:
            yield text_chunk
