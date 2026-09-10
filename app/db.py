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
        for col, col_type in [("avatar_name", "TEXT DEFAULT 'El Mandatario'"), ("duration_seconds", "INTEGER DEFAULT 300")]:
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
    """Inserta los casos precargados si no existen (verificación por título)."""
    from app.models import Case  # importación local para evitar ciclos

    cases_to_seed = [
        {
            "title": _DEFAULT_CASE_TITLE,
            "scenario_text": _DEFAULT_CASE_SCENARIO,
            "persona_notes": _DEFAULT_CASE_NOTES,
        },
        {
            "title": "Régimen de regalías carboníferas — Cesar y Córdoba",
            "scenario_text": (
                "Representas a la Asociación Colombiana de Minería (ACM), sección carbón térmico, "
                "en nombre de los productores del Cesar y Córdoba. El gobierno ha presentado un "
                "proyecto de decreto que elevaría la tarifa de regalías sobre el carbón térmico del "
                "10% al 18% para financiar el Fondo de Transición Energética. El sector argumenta que "
                "esto haría inviable la exportación frente a competidores australianos e indonesios, "
                "con quienes ya se compite en márgenes estrechos.\n"
                "Tu objetivo es negociar con el Mandatario:\n"
                "1. Mantener la tarifa actual para proyectos con contratos de exportación vigentes "
                "por los próximos 5 años (cláusula de estabilidad jurídica).\n"
                "2. Proponer un esquema gradual: 12% en 2026, 15% en 2028, revisión en 2030 sujeta "
                "a precio internacional del carbón.\n"
                "3. Ofrecer una contribución voluntaria al Fondo de Transición equivalente al 1% "
                "de las utilidades netas del sector, a cambio de la gradualidad.\n"
                "El Mandatario necesita mostrar avances en transición energética para cumplir compromisos "
                "ante la COP. La región del Cesar depende del carbón para el 40% de su empleo formal."
            ),
            "persona_notes": (
                "El Mandatario tiene un ala ambientalista en su coalición que presiona por el 18% "
                "sin concesiones. Pero también tiene gobernadores del Cesar y Córdoba que lo apoyaron "
                "electoralmente y que temen el desempleo masivo. El número que más le importa: "
                "empleos directos en riesgo. Concretar cifras de empleo en la negociación es clave."
            ),
        },
        {
            "title": "Subsidio VIS y déficit habitacional urbano — Bogotá, Medellín, Cali",
            "scenario_text": (
                "Representas a Camacol (Cámara Colombiana de la Construcción), sección vivienda de "
                "interés social. El gobierno ha congelado los desembolsos del subsidio Semillero de "
                "Propietarios durante seis meses por un ajuste fiscal, dejando 28.000 hogares en lista "
                "de espera en las tres principales ciudades. La tasa de interés del crédito hipotecario "
                "social ha subido al 12% EA, haciendo inaccesible la cuota para familias con ingresos "
                "de 2-4 SMLV.\n"
                "Tu objetivo es negociar con el Mandatario:\n"
                "1. Reanudar los desembolsos del Semillero antes del 30 de septiembre con al menos "
                "$800.000 millones del presupuesto de inversión.\n"
                "2. Crear una línea de crédito subsidiada al 7% EA para VIS con cobertura de tasa "
                "del Gobierno durante 10 años.\n"
                "3. Agilizar la expedición de licencias de construcción mediante ventanilla única "
                "digital en los 12 municipios con mayor déficit cuantitativo.\n"
                "El Ministerio de Hacienda se opone al desembolso por el déficit fiscal actual. "
                "El sector privado tiene proyectos listos para iniciar en 90 días si se liberan los recursos."
            ),
            "persona_notes": (
                "El Mandatario lanzó 'Techo Digno' como programa bandera en su primer año y políticamente "
                "no puede admitir que está frenado. Prefiere marcos que le permitan anunciarlo como "
                "'relanzamiento' o 'nueva fase'. Evitar la palabra 'congelación' y proponer narrativas "
                "de 'aceleración' aumenta las probabilidades de acuerdo."
            ),
        },
        {
            "title": "Concesión de vías terciarias — Pacífico colombiano (Chocó)",
            "scenario_text": (
                "Representas a un consorcio regional de ingeniería (Consorcio Pacífico Vial) que ha "
                "presentado una propuesta para tomar en concesión social el mantenimiento de 380 km "
                "de vías terciarias en el Chocó, conectando 14 municipios productores de madera legal, "
                "cacao y plátano con los puertos de Buenaventura y Turbo.\n"
                "El modelo propuesto es de APP social (Asociación Público-Privada), donde el consorcio "
                "aporta maquinaria y operación; el Estado aporta el 60% del costo vía transferencias "
                "de regalías del OCAD-Paz.\n"
                "Tu objetivo es negociar con el Mandatario:\n"
                "1. Firma del convenio marco en un plazo máximo de 60 días.\n"
                "2. Garantía de transferencia de al menos $45.000 millones del OCAD-Paz en el primer año.\n"
                "3. Inclusión de una cláusula de empleo local: mínimo el 70% de la mano de obra debe "
                "ser de comunidades chocoanas (afrodescendientes e indígenas), con capacitación técnica "
                "certificada por el SENA.\n"
                "El INVÍAS tiene objeciones técnicas sobre la capacidad del consorcio para proyectos "
                "de esta escala. La comunidad local respalda la propuesta con carta de 23 JAC."
            ),
            "persona_notes": (
                "El Chocó es políticamente sensible para el Mandatario: tiene deuda histórica con la "
                "región y hay presión de organizaciones étnico-territoriales. El argumento de empleo "
                "local y paz territorial es su punto blando. Las objeciones del INVÍAS las puede "
                "resolver administrativamente si quiere; el verdadero cuello de botella es el OCAD-Paz, "
                "que requiere su voluntad política directa."
            ),
        },
    ]

    with DBSession(engine) as db:
        existing_titles = {c.title for c in db.exec(select(Case)).all()}
        for data in cases_to_seed:
            if data["title"] not in existing_titles:
                db.add(Case(**data))
        db.commit()



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
