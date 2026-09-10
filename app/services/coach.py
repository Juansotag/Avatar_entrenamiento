"""
Módulo de análisis de coaching post-sesión.

Después de una sesión de negociación, este módulo envía la transcripción
completa a Claude (con extended thinking) para obtener un informe de coaching
estructurado que el entrenado puede revisar.
"""

import json
import logging
from typing import Optional

from anthropic import Anthropic

from app.config import get_settings
from app.services.persona import get_persona_system_prompt

logger = logging.getLogger(__name__)
settings = get_settings()

_client: Optional[Anthropic] = None


def _client_instance() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


COACHING_SYSTEM_PROMPT = """Eres un coach experto en negociación, comunicación estratégica interpersonal y manejo de conversaciones críticas y de alta tensión (incluyendo negociaciones comerciales, diálogo político, retroalimentación académica o laboral, y entrega de noticias complejas o sensibles).
Tu tarea es analizar la transcripción de una práctica entre un usuario (la persona que entrena) y una contraparte (interpretada por IA) y entregar un informe de retroalimentación riguroso, específico, honesto y constructivo.

El informe debe ser útil para que el usuario perfeccione sus habilidades de comunicación, escucha activa, manejo de objeciones, empatía táctica y logro de acuerdos u objetivos según el rol y escenario planteado.

INSTRUCCIONES:
- Sé directo y concreto. Cita fragmentos textuales exactos de lo que dijo el usuario para ilustrar cada fortaleza o área de mejora.
- No seas condescendiente ni elogies de manera genérica. Si el desempeño fue débil, contraproducente o evasivo, dilo claramente.
- Evalúa si el usuario avanzó hacia sus objetivos declarados o si cometió fallos tácticos en el manejo de la conversación.
- El puntaje (0–100) debe ser realista y calibrado: 90+ es excepcional, 70-89 es bueno con técnica sólida, 50-69 es regular con vacíos notorios, menos de 50 es insatisfactorio.
- El campo "resultado_final" debe resumir el desenlace (por ejemplo: "acuerdo_parcial", "aplazamiento", "rechazo", "acuerdo_exitoso", "sin_acuerdo").
- Responde SIEMPRE en español, en formato JSON válido, sin texto antes ni después del JSON.
"""

COACHING_USER_TEMPLATE = """A continuación tienes el contexto de la interacción, los perfiles y la transcripción completa.

## Escenario de la interacción:
{scenario_text}

## Perfil del usuario que practica:
{negotiator_profile}

## Perfil de la contraparte ({avatar_name}):
{persona_brief}

## Transcripción completa de la sesión:
{transcript}

---

Genera un informe de coaching completo en el siguiente formato JSON exacto:

{{
  "score": <entero 0-100>,
  "resultado_final": "<acuerdo_parcial | aplazamiento | rechazo | acuerdo_exitoso | sin_acuerdo>",
  "resumen_ejecutivo": "<2-3 oraciones que resumen el desempeño general>",
  "fortalezas": [
    {{
      "titulo": "<nombre corto>",
      "descripcion": "<qué hizo bien el usuario>",
      "cita_usuario": "<fragmento textual de lo que dijo>"
    }}
  ],
  "areas_de_mejora": [
    {{
      "titulo": "<nombre corto>",
      "descripcion": "<qué debería mejorar y por qué>",
      "cita_usuario": "<fragmento textual de lo que dijo>",
      "sugerencia_reformulacion": "<cómo debería haberlo dicho o enfocado>"
    }}
  ],
  "tacticas_efectivas": ["<tactica1>", "<tactica2>"],
  "oportunidades_perdidas": ["<oportunidad1>", "<oportunidad2>"],
  "recomendacion_principal": "<una sola recomendación clave y accionable para la próxima práctica>"
}}
"""


def analyze_session(
    scenario_text: str,
    turns: list[tuple[str, str]],  # [(role, text), ...]
    negotiator_info: Optional[dict] = None,
    avatar_name: str = "la contraparte",
) -> dict:
    """
    Analiza la transcripción de una sesión y devuelve
    un diccionario con el informe de coaching generado por Claude.

    Usa extended thinking para un razonamiento profundo sobre el desempeño.
    """
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY no configurada. No se puede generar el informe de coaching.")
        return _empty_report()

    # Formatear la transcripción
    transcript_lines = []
    for role, text in turns:
        label = "USUARIO" if role == "user" else f"CONTRAPARTE ({avatar_name})"
        transcript_lines.append(f"[{label}]: {text}")
    transcript = "\n\n".join(transcript_lines)

    persona_brief = get_persona_system_prompt()

    user_profile_lines = []
    if negotiator_info:
        if negotiator_info.get("name"):
            user_profile_lines.append(f"- Nombre: {negotiator_info['name']}")
        if negotiator_info.get("role"):
            user_profile_lines.append(f"- Rol / Cargo: {negotiator_info['role']}")
        if negotiator_info.get("organization"):
            user_profile_lines.append(f"- Organización: {negotiator_info['organization']}")
        if negotiator_info.get("objectives"):
            user_profile_lines.append(f"- Objetivos planteados: {negotiator_info['objectives']}")
    negotiator_profile_str = "\n".join(user_profile_lines) if user_profile_lines else "No especificado."

    prompt = COACHING_USER_TEMPLATE.format(
        scenario_text=scenario_text,
        negotiator_profile=negotiator_profile_str,
        avatar_name=avatar_name,
        persona_brief=persona_brief,
        transcript=transcript,
    )

    try:
        # Usar extended thinking para análisis profundo
        try:
            response = _client_instance().messages.create(
                model=settings.model_name,
                max_tokens=16000,
                thinking={
                    "type": "enabled",
                    "budget_tokens": settings.coaching_thinking_budget,
                },
                system=COACHING_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as thinking_err:
            logger.warning(
                "No se pudo usar thinking para el analisis de coaching (%s). Reintentando sin thinking...",
                thinking_err
            )
            response = _client_instance().messages.create(
                model=settings.model_name,
                max_tokens=4096,
                system=COACHING_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

        # Extraer el bloque de texto (ignorar el bloque de thinking)
        report_text = ""
        for block in response.content:
            if block.type == "text":
                report_text = block.text.strip()
                break

        # Parsear JSON
        # Limpiar posibles marcadores de código markdown
        if report_text.startswith("```"):
            report_text = report_text.split("```")[1]
            if report_text.startswith("json"):
                report_text = report_text[4:]

        report = json.loads(report_text)
        return report

    except json.JSONDecodeError as e:
        logger.error("Claude devolvió JSON inválido en el coaching: %s", e)
        logger.debug("Respuesta completa: %s", report_text)
        return _empty_report(error="El análisis se generó pero no pudo parsearse correctamente.")
    except Exception as e:
        logger.exception("Error al generar el informe de coaching: %s", e)
        return _empty_report(error=str(e))


def _empty_report(error: Optional[str] = None) -> dict:
    """Devuelve un informe vacío/de error para no bloquear el flujo."""
    return {
        "score": None,
        "resultado_final": "sin_datos",
        "resumen_ejecutivo": error or "No fue posible generar el análisis de coaching.",
        "fortalezas": [],
        "areas_de_mejora": [],
        "tacticas_efectivas": [],
        "oportunidades_perdidas": [],
        "recomendacion_principal": "",
    }
