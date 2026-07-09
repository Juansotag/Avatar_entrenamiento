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


COACHING_SYSTEM_PROMPT = """Eres un coach experto en negociación, comunicación política y relaciones empresa-Estado.
Tu tarea es analizar la transcripción de una práctica de negociación entre un empresario (el usuario que practica)
y un personaje político (interpretado por IA) y entregar un informe de retroalimentación claro, específico, honesto y constructivo.

El informe debe ser útil para que el empresario mejore sus habilidades reales de negociación con figuras de poder público.

INSTRUCCIONES:
- Sé directo y concreto. Cita fragmentos textuales de lo que dijo el usuario para ilustrar cada punto.
- No seas condescendiente ni elogies de manera genérica. Si el desempeño fue pobre, dilo claramente.
- Identifica patrones de comportamiento, no eventos aislados.
- El puntaje (0–100) debe ser realista: un 90+ es excepcional, un 50 es promedio.
- Responde SIEMPRE en español, en formato JSON válido, sin texto antes ni después del JSON.
"""

COACHING_USER_TEMPLATE = """A continuación tienes el contexto de la negociación y la transcripción completa.

## Escenario de negociación:
{scenario_text}

## Perfil del personaje político con quien negoció el usuario:
{persona_brief}

## Transcripción completa de la sesión:
{transcript}

---

Genera un informe de coaching completo en el siguiente formato JSON exacto:

{{
  "score": <entero 0-100>,
  "resultado_final": "<acuerdo_parcial | aplazamiento | rechazo>",
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
      "sugerencia_reformulacion": "<cómo debería haberlo dicho>"
    }}
  ],
  "tacticas_efectivas": ["<tactica1>", "<tactica2>"],
  "oportunidades_perdidas": ["<oportunidad1>", "<oportunidad2>"],
  "recomendacion_principal": "<una sola recomendación clave para la próxima práctica>"
}}
"""


def analyze_session(
    scenario_text: str,
    turns: list[tuple[str, str]],  # [(role, text), ...]
) -> dict:
    """
    Analiza la transcripción de una sesión de negociación y devuelve
    un diccionario con el informe de coaching generado por Claude.

    Usa extended thinking para un razonamiento profundo sobre el desempeño.
    """
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY no configurada. No se puede generar el informe de coaching.")
        return _empty_report()

    # Formatear la transcripción
    transcript_lines = []
    for role, text in turns:
        label = "USUARIO" if role == "user" else "PERSONAJE (IA)"
        transcript_lines.append(f"[{label}]: {text}")
    transcript = "\n\n".join(transcript_lines)

    persona_brief = get_persona_system_prompt()

    prompt = COACHING_USER_TEMPLATE.format(
        scenario_text=scenario_text,
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
