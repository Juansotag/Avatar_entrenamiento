from collections.abc import Generator

from sqlmodel import Session as DBSession
from sqlmodel import SQLModel, create_engine, select

from app.config import get_settings

settings = get_settings()

engine_args = {}
if settings.database_url.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_args)

_DEFAULT_CASE_TITLE = "Fondo parafiscal ganadero — Llanos Orientales"

_DEFAULT_CASE_SCENARIO = (
    "Representas a la Federación de Ganaderos de los Llanos Orientales (FEDEGAN-LLO). "
    "El sector ganadero de la región enfrenta una crisis de rentabilidad: los costos de "
    "sanidad animal y comercialización han subido un 30% en dos años, mientras que el "
    "precio al productor se mantiene estancado. Tu objetivo es negociar con el Mandatario "
    "la reforma al reglamento del Fondo de Fomento Ganadero y Lechero (FFGL) para:\n"
    "1. Redirigir al menos el 25% del recaudo parafiscal hacia subsidios directos a "
    "pequeños y medianos ganaderos de la región.\n"
    "2. Crear una junta regional con participación del gremio en las decisiones de inversión "
    "del fondo en los Llanos Orientales.\n"
    "3. Establecer un precio mínimo de sustentación para la carne en pie, indexado al costo "
    "de producción certificado por el ICA.\n"
    "El Mandatario ha mostrado simpatía pública con el campo, pero el Ministerio de "
    "Hacienda se opone a cualquier destino específico de los parafiscales que reduzca "
    "la flexibilidad fiscal. Tienes 5 minutos de audiencia."
)

_DEFAULT_CASE_NOTES = (
    "Los ganaderos de los Llanos tienen peso político en cinco departamentos clave "
    "(Meta, Casanare, Vichada, Arauca, Guainía). El gremio movilizó votos para el "
    "Mandatario en la última elección. Úsalo como palanca, pero con cuidado: el "
    "Mandatario rechaza el clientelismo explícito."
)


def init_db() -> None:
    from sqlmodel import text
    if settings.database_url.startswith("sqlite"):
        with DBSession(engine) as db:
            db.exec(text("PRAGMA journal_mode=WAL;"))
            db.commit()
    # Migrar la base de datos de manera dinámica si las nuevas columnas no existen
    with engine.begin() as conn:
        for col, col_type in [
            ("avatar_name", "TEXT DEFAULT 'Contraparte'"),
            ("duration_seconds", "INTEGER DEFAULT 300"),
            ("user_name", "TEXT DEFAULT ''"),
            ("user_role", "TEXT DEFAULT ''"),
            ("user_organization", "TEXT DEFAULT ''"),
            ("user_objectives", "TEXT DEFAULT ''"),
            ("avatar_profile", "TEXT"),
            ("avatar_tone", "TEXT"),
            ("avatar_rules", "TEXT"),
            ("avatar_voice", "TEXT DEFAULT 'onyx'"),
        ]:
            try:
                conn.execute(text(f'ALTER TABLE "case" ADD COLUMN {col} {col_type};'))
            except Exception:
                pass
        for col in ["happiness", "anger", "sadness", "fear"]:
            try:
                conn.execute(text(f'ALTER TABLE "nonverbalsnapshot" ADD COLUMN {col} FLOAT;'))
            except Exception:
                pass
    SQLModel.metadata.create_all(engine)
    _seed_default_case()
    _seed_default_negotiator_profile()


def _seed_default_case() -> None:
    """Inserta los 10 casos representativos (5 públicos, 5 privados) y sesiones sintéticas si no existen."""
    from app.models import Case
    with DBSession(engine) as db:
        if db.exec(select(Case)).first() is not None:
            return
    try:
        from scripts.seed_10_cases_and_sessions import seed_all_cases_and_sessions
        seed_all_cases_and_sessions(purge_existing=False)
    except Exception as e:
        logger.warning("No se pudo ejecutar la siembra de los 10 casos: %s", e)



def _seed_default_negotiator_profile() -> None:
    """Crea un perfil de negociante vacío si no existe ninguno."""
    from app.models import NegotiatorProfile  # importación local para evitar ciclos

    with DBSession(engine) as db:
        existing = db.exec(select(NegotiatorProfile)).first()
        if existing is not None:
            return
        profile = NegotiatorProfile(
            name="",
            role="",
            organization="",
            objectives="",
        )
        db.add(profile)
        db.commit()


def get_db() -> Generator[DBSession, None, None]:
    with DBSession(engine) as db:
        yield db
