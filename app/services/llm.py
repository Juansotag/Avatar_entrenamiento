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
    persona_notes: Optional[str] = None,
    query: str = "",
    avatar_name: str = "la contraparte",
    time_context: Optional[str] = None,
    negotiator_info: Optional[dict] = None,
    avatar_profile: Optional[str] = None,
    avatar_tone: Optional[str] = None,
    avatar_rules: Optional[str] = None,
) -> str:
    context_snippets = get_relevant_context(query)
    
    if avatar_profile and avatar_profile.strip():
        persona_prompt = (
            f"# IDENTIDAD Y ROL DEL AVATAR\n"
            f"Eres {avatar_name}.\n"
            f"{avatar_profile.strip()}\n\n"
            f"## TONO Y ESTILO DE COMUNICACIÓN\n"
            f"{avatar_tone.strip() if avatar_tone else 'Mantén un tono natural, coherente con tu rol, contexto y personalidad.'}\n\n"
            f"## REGLAS DE CONDUCTA Y LÍMITES\n"
            f"{avatar_rules.strip() if avatar_rules else 'Mantén tu personaje en todo momento.'}\n"
            f"- Responde siempre en primera persona como {avatar_name}.\n"
            f"- Mantén respuestas directas, realistas y conversacionales (de 1 a 4 párrafos cortos).\n"
            f"- Nunca salgas del personaje ni admitas ser una inteligencia artificial."
        )
    else:
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
    parts.append("\n## Contexto y escenario de la interacción\n" + scenario_text)

    if negotiator_info:
        user_parts = []
        if negotiator_info.get("name"):
            user_parts.append(f"- **Nombre del interlocutor:** {negotiator_info['name']}")
        if negotiator_info.get("role"):
            user_parts.append(f"- **Cargo / Rol:** {negotiator_info['role']}")
        if negotiator_info.get("organization"):
            user_parts.append(f"- **Organización o Entidad:** {negotiator_info['organization']}")
        if negotiator_info.get("objectives"):
            user_parts.append(f"- **Objetivos conocidos o planteados:** {negotiator_info['objectives']}")
        if user_parts:
            parts.append("\n## Perfil del interlocutor (usuario que entrena)\n" + "\n".join(user_parts))

    if persona_notes:
        parts.append(f"\n## Notas específicas para {avatar_name} en este caso\n" + persona_notes)
    if context_snippets:
        parts.append(
            "\n## Información de referencia / contexto adicional relevante\n" + "\n\n---\n\n".join(context_snippets)
        )
    if time_context:
        parts.append(time_context)
    return "\n".join(parts)


def get_opening_instruction(avatar_name: str = "la contraparte", user_role: Optional[str] = None) -> str:
    interlocutor_str = f"a la persona en su rol de {user_role}" if user_role else "a tu interlocutor"
    return (
        f"Estás a punto de iniciar la conversación/reunión con {interlocutor_str} en el escenario descrito arriba. "
        f"Abre la interacción en persona, en primera persona, en dos o tres frases breves y directas, tal como lo haría "
        f"{avatar_name}: manteniendo tu personaje, tu estilo y estableciendo el tono de la reunión sin rodeos."
    )


def _build_messages(
    stored_turns: list[tuple[str, str]],
    user_message: Optional[str] = None,
    opening_instruction: Optional[str] = None,
) -> list[dict]:
    """Construye la lista de mensajes para la API de Claude.

    La API exige que el primer mensaje sea 'user' y que los roles alternen.
    Se antepone la instrucción de apertura sintética (nunca visible al usuario).
    """
    instr = opening_instruction or get_opening_instruction()
    messages: list[dict] = [{"role": "user", "content": instr}]
    for role, text in stored_turns:
        messages.append({
            "role": "assistant" if role == "persona" else "user",
            "content": text,
        })
    if user_message:
        messages.append({"role": "user", "content": user_message})
    return messages


def generate_opening_line(
    scenario_text: str,
    persona_notes: Optional[str] = None,
    avatar_name: str = "El Mandatario",
    negotiator_info: Optional[dict] = None,
    avatar_profile: Optional[str] = None,
    avatar_tone: Optional[str] = None,
    avatar_rules: Optional[str] = None,
) -> str:
    """Genera la línea de apertura del personaje al comenzar la sesión."""
    system_prompt = build_system_prompt(
        scenario_text=scenario_text,
        persona_notes=persona_notes,
        query=scenario_text,
        avatar_name=avatar_name,
        negotiator_info=negotiator_info,
        avatar_profile=avatar_profile,
        avatar_tone=avatar_tone,
        avatar_rules=avatar_rules,
    )
    user_role = negotiator_info.get("role") if negotiator_info else None
    opening_instruction = get_opening_instruction(avatar_name, user_role)

    message = _client_instance().messages.create(
        model=settings.model_name,
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": opening_instruction}],
    )
    for block in message.content:
        if block.type == "text":
            return block.text
    return ""


def generate_reply(
    scenario_text: str,
    persona_notes: Optional[str] = None,
    stored_turns: list[tuple[str, str]] = None,
    user_message: str = "",
    avatar_name: str = "El Mandatario",
    time_context: Optional[str] = None,
    negotiator_info: Optional[dict] = None,
    avatar_profile: Optional[str] = None,
    avatar_tone: Optional[str] = None,
    avatar_rules: Optional[str] = None,
) -> str:
    """Genera la respuesta del personaje en un turno dado."""
    if stored_turns is None:
        stored_turns = []
    system_prompt = build_system_prompt(
        scenario_text=scenario_text,
        persona_notes=persona_notes,
        query=user_message,
        avatar_name=avatar_name,
        time_context=time_context,
        negotiator_info=negotiator_info,
        avatar_profile=avatar_profile,
        avatar_tone=avatar_tone,
        avatar_rules=avatar_rules,
    )
    user_role = negotiator_info.get("role") if negotiator_info else None
    opening_instruction = get_opening_instruction(avatar_name, user_role)
    messages = _build_messages(stored_turns, user_message, opening_instruction=opening_instruction)

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
    persona_notes: Optional[str] = None,
    stored_turns: list[tuple[str, str]] = None,
    user_message: str = "",
    avatar_name: str = "El Mandatario",
    time_context: Optional[str] = None,
    negotiator_info: Optional[dict] = None,
    avatar_profile: Optional[str] = None,
    avatar_tone: Optional[str] = None,
    avatar_rules: Optional[str] = None,
) -> Generator[str, None, None]:
    """Igual que generate_reply pero en modo streaming."""
    if stored_turns is None:
        stored_turns = []
    system_prompt = build_system_prompt(
        scenario_text=scenario_text,
        persona_notes=persona_notes,
        query=user_message,
        avatar_name=avatar_name,
        time_context=time_context,
        negotiator_info=negotiator_info,
        avatar_profile=avatar_profile,
        avatar_tone=avatar_tone,
        avatar_rules=avatar_rules,
    )
    user_role = negotiator_info.get("role") if negotiator_info else None
    opening_instruction = get_opening_instruction(avatar_name, user_role)
    messages = _build_messages(stored_turns, user_message, opening_instruction=opening_instruction)

    with _client_instance().messages.stream(
        model=settings.model_name,
        max_tokens=5000,
        system=system_prompt,
        messages=messages,
    ) as stream:
        for text_chunk in stream.text_stream:
            yield text_chunk
