import sys
sys.path.insert(0, ".")
import json
from datetime import datetime, timedelta
import random
from sqlmodel import Session as DBSession, select

from app.db import engine
from app.models import Case, NegotiationSession, Turn, NonverbalSnapshot

CASES_DATA = [
    # ── 1. PÚBLICO: SINDICATO DE SERVIDORES PÚBLICOS ──
    {
        "sector": "Público",
        "title": "Concertación de pliego salarial con sindicato distrital",
        "scenario_text": (
            "Mesa formal de concertación laboral en la Secretaría General de la Alcaldía Mayor. El sindicato mayoritario "
            "radicó un pliego exigiendo un incremento del IPC + 6.5%, bonificación por quinquenio y teletrabajo de 4 días a la semana. "
            "La administración enfrenta el techo fiscal estricto de la Ley 617 sobre gastos de funcionamiento y advertencia de la Contraloría. "
            "Si no se logra un acuerdo razonable hoy, las bases sindicales convocarán a cese escalonado en puntos de atención ciudadana."
        ),
        "duration_seconds": 300,
        "user_name": "Dr. Andrés Camargo",
        "user_role": "Secretario General Distrital",
        "user_organization": "Alcaldía Mayor",
        "user_objectives": (
            "1. Mantener el reajuste salarial en el IPC + 1.8% acorde a la viabilidad presupuestal de Hacienda.\n"
            "2. Conceder flexibilidad en teletrabajo (máximo 2 días por semana) condicionado a metas de servicio al ciudadano.\n"
            "3. Desactivar la amenaza de cese de actividades mediante la firma de un acta de acuerdos concertados."
        ),
        "avatar_name": "Hernando Barreto (Presidente Sindical)",
        "avatar_profile": (
            "Abogado laboralista y líder sindical con 24 años de carrera administrativa. Conoce la jurisprudencia al detalle y sabe "
            "que la administración teme el costo mediático de filas de ciudadanos sin atención."
        ),
        "avatar_tone": "Enérgico, reivindicativo, usa argumentos de justicia social pero sabe negociar con cifras.",
        "avatar_rules": (
            "1. No aceptar incrementos inferiores a IPC + 2.5% sin una compensación tangible en capacitación o bienestar.\n"
            "2. Exigir respeto al fuero sindical y garantías de no represalias.\n"
            "3. Flexibilizar el teletrabajo a 2 días solo si el Distrito provee equipos institucionales."
        ),
        "persona_notes": "Valora el reconocimiento explícito a la dignidad del servidor público antes de entrar a la discusión presupuestal.",
        "session_turns": [
            ("persona", "Doctor Camargo, buenas tardes. Nuestras bases están cansadas de dilaciones. El costo de vida no da tregua y nuestro pliego de IPC más 6.5% representa el rezago de años. Esperamos una oferta seria hoy o mañana las ventanillas distritales no abrirán."),
            ("user", "Buenas tardes, don Hernando. Entiendo perfectamente la presión que sienten los servidores y reconocemos el valor de su trabajo para la ciudad. Sin embargo, tenemos el límite vinculante de la Ley 617 de Hacienda. Si excedemos el gasto de funcionamiento incurrimos en falta disciplinaria. Nuestra propuesta responsable es IPC más 1.8% garantizado, combinado con un plan de bienestar integral y capacitación financiada."),
            ("persona", "Un 1.8% adicional es insuficiente frente a lo que han perdido los salarios en alimentación y transporte. Si el Distrito no sube al menos a IPC más 2.5%, la asamblea no aprobará el acta y el paro será inevitable."),
            ("user", "Hernando, cuidemos la ciudad y la estabilidad del Distrito. Propongo una fórmula intermedia: acordemos IPC más 2.1% en lo salarial, pero autoricemos de inmediato 2 días de teletrabajo a la semana con entrega de equipos para el 100% de la planta y subsidio de conectividad. Eso alivia de inmediato los gastos de transporte de sus afiliados sin violar el techo fiscal."),
            ("persona", "Eso cambia el panorama. El teletrabajo formalizado de 2 días con equipos y auxilio de conectividad sí representa un ahorro directo en el bolsillo de los compañeros. Si dejamos eso por escrito en el acta con cronograma a 30 días, someto la aprobación del IPC más 2.1% y suspendemos cualquier llamado a cese de actividades.")
        ],
        "coaching": {
            "score": 88,
            "resultado_final": "acuerdo_exitoso",
            "resumen_ejecutivo": "Excelente manejo de la tensión política y legal. El usuario logró desactivar la amenaza de paro sin vulnerar los límites fiscales de la Ley 617, compensando creativamente la diferencia salarial con teletrabajo y subsidios en especie.",
            "fortalezas": [
                {"titulo": "Anclaje institucional y normativo", "descripcion": "Explicó con firmeza y serenidad los límites legales de la Ley 617 sin sonar despectivo hacia el sindicato.", "cita_usuario": "Sin embargo, tenemos el límite vinculante de la Ley 617 de Hacienda. Si excedemos el gasto de funcionamiento incurrimos en falta disciplinaria."},
                {"titulo": "Moneda de cambio no monetaria", "descripcion": "Utilizó el teletrabajo de 2 días y subsidio de conectividad como valor real para el bolsillo del empleado sin inflar la base salarial permanente.", "cita_usuario": "autoricemos de inmediato 2 días de teletrabajo a la semana con entrega de equipos para el 100% de la planta y subsidio de conectividad."}
            ],
            "areas_de_mejora": [
                {"titulo": "Concesión anticipada de porcentaje", "descripcion": "Subió de 1.8% a 2.1% rápidamente en un solo turno. Pudo haber explorado primero la oferta de teletrabajo antes de ceder puntos decimales.", "cita_usuario": "acordemos IPC más 2.1% en lo salarial", "sugerencia_reformulacion": "Mantengamos el 1.8% garantizado pero sumemos de inmediato el teletrabajo con subsidio; evaluemos juntos el ahorro mensual que esto genera."}
            ],
            "tacticas_efectivas": ["Validación de la dignidad del trabajador", "Ampliación del pastel de negociación", "Anclaje en restricciones legales vinculantes"],
            "oportunidades_perdidas": ["Retención del margen de ajuste salarial para una segunda ronda"],
            "recomendacion_principal": "En negociaciones públicas con restricciones fiscales, presenta primero los beneficios colaterales antes de ceder en el componente salarial directo."
        }
    },

    # ── 2. PÚBLICO: CONSULTA PREVIA DE INFRAESTRUCTURA ──
    {
        "sector": "Público",
        "title": "Consulta previa por trazado de doble calzada nacional",
        "scenario_text": (
            "Audiencia de consulta previa territorial en la vereda El Palmar. El Ministerio de Transporte y la ANI deben "
            "acordar las medidas de compensación ambiental y social por el trazado de la doble calzada que interviene un humedal y áreas de pesca "
            "artesanal de un Consejo Comunitario afrodescendiente. La comunidad mantiene bloqueado el campamento de maquinaria pesada."
        ),
        "duration_seconds": 360,
        "user_name": "Dra. Elena Restrepo",
        "user_role": "Directora de Gestión Social y Consulta Previa",
        "user_organization": "Ministerio de Transporte",
        "user_objectives": (
            "1. Suscribir el protocolo de compensaciones socioambientales dentro del marco presupuestal del Fondo de Mitigación.\n"
            "2. Acordar el levantamiento pacífico del bloqueo a la maquinaria sin intervención de la fuerza pública.\n"
            "3. Formalizar una mesa de veeduría comunitaria con contratación del 100% de mano de obra local no calificada."
        ),
        "avatar_name": "Faustino Palacios (Líder del Consejo Comunitario)",
        "avatar_profile": (
            "Representante legal del Consejo Comunitario. Desconfía de concesionarios viales por acuerdos incumplidos en proyectos anteriores. "
            "Exige respeto al territorio ancestral y compromisos con firmas ministeriales vinculantes."
        ),
        "avatar_tone": "Solemne, pausado, firme y profundamente arraigado a la memoria territorial colectiva.",
        "avatar_rules": (
            "1. Si percibe prisa técnica o indiferencia por el humedal, suspende la sesión de inmediato.\n"
            "2. Exigir compensación productiva directa para las 28 familias de pescadores antes de mover maquinaria.\n"
            "3. Exigir que la interventoría ambiental incluya veedores de la comunidad con estipendio logístico."
        ),
        "persona_notes": "Escuchar sin interrumpir los antecedentes históricos es condición obligatoria para generar confianza.",
        "session_turns": [
            ("persona", "Doctora Elena, ustedes vienen de Bogotá con planos y cronogramas, pero este humedal es donde nuestros abuelos enseñaron a pescar a nuestros hijos. La concesionaria ya taponó un caño y no vamos a movernos del campamento hasta que haya respeto real por nuestra vida y nuestro territorio."),
            ("user", "Don Faustino, antes de hablar de ingeniería o de plazos, quiero pedirle disculpas a usted y a toda la comunidad por el taponamiento de ese caño. Eso fue una falta grave del contratista y ya ordené a la interventoría abrir el proceso sancionatorio. Estoy aquí en su territorio para escuchar y concertar, no para imponer."),
            ("persona", "Agradezco sus palabras, doctora, pero el hambre de las familias no se quita con procesos sancionatorios. Son 28 familias que viven de esa ciénaga y hoy no tienen qué pescar porque el agua está turbia por las retroexcavadoras."),
            ("user", "Tiene toda la razón, don Faustino. Por eso traemos una propuesta concreta y vinculante hoy: primero, la activación inmediata del fondo de mitigación de emergencia con apoyo alimentario y productivo directo para las 28 familias censadas. Segundo, la contratación del 100% de la mano de obra no calificada con jóvenes y adultos de la vereda. Y tercero, dos asientos remunerados para el Consejo Comunitario en la veeduría ambiental de la obra."),
            ("persona", "Si usted firma aquí mismo esa resolución ministerial con fecha de desembolso del apoyo para este viernes y el contrato de veeduría, nosotros hoy mismo a las cinco de la tarde levantamos la protesta y dejamos trabajar a la maquinaria.")
        ],
        "coaching": {
            "score": 92,
            "resultado_final": "acuerdo_exitoso",
            "resumen_ejecutivo": "Desempeño sobresaliente en resolución de conflictos territoriales. La disculpa sincera y la validación de los daños abrieron la puerta a una negociación cooperativa donde se protegieron tanto los derechos comunitarios como el cronograma del proyecto nacional.",
            "fortalezas": [
                {"titulo": "Empatía táctica inicial", "descripcion": "Pidió disculpas por el daño ambiental del contratista, desarmando la postura defensiva del líder comunitario.", "cita_usuario": "Don Faustino, antes de hablar de ingeniería o de plazos, quiero pedirle disculpas a usted y a toda la comunidad por el taponamiento de ese caño."},
                {"titulo": "Propuesta integral estructurada", "descripcion": "Presentó una tríada de soluciones balanceada (apoyo directo a familias, empleo local y veeduría comunitaria vinculante).", "cita_usuario": "primero, la activación inmediata del fondo de mitigación... Segundo, la contratación del 100% de la mano de obra... Y tercero, dos asientos remunerados para el Consejo Comunitario"}
            ],
            "areas_de_mejora": [
                {"titulo": "Compromiso de fecha muy ajustada", "descripcion": "Aceptó implícitamente el desembolso para el viernes sin verificar los tiempos de tesorería del ministerio.", "cita_usuario": "Por eso traemos una propuesta concreta y vinculante hoy", "sugerencia_reformulacion": "Firmemos el acta hoy y comprometamos la resolución para este viernes, con primer desembolso el martes hábil para no fallarles en la fecha."}
            ],
            "tacticas_efectivas": ["Reconocimiento de errores del contratista", "Descentralización de la veeduría ambiental", "Legitimación del liderazgo comunitario"],
            "oportunidades_perdidas": ["Establecer un protocolo de contingencia si se detecta un nuevo impacto ambiental"],
            "recomendacion_principal": "En consultas territoriales, la legitimidad se gana asumiendo la responsabilidad del Estado antes de exigir el levantamiento de medidas de hecho."
        }
    },

    # ── 3. PÚBLICO: ALBERGUES POR OLA INVERNAL ──
    {
        "sector": "Público",
        "title": "Reubicación urgente y albergues por ola invernal",
        "scenario_text": (
            "Puesto de Mando Unificado (PMU) municipal. Las lluvias desbordaron el río tutelar, dejando 350 familias sin vivienda. "
            "La Unidad de Gestión del Riesgo debe concertar el traslado desde un coliseo hacinado hacia un terreno fiscal con albergues "
            "modulares transitorios y subsidios de arriendo temporal, mientras los líderes temen que el traslado sea una excusa de desalojo permanente."
        ),
        "duration_seconds": 300,
        "user_name": "Dr. Javier Salamanca",
        "user_role": "Director Departamental de Gestión del Riesgo",
        "user_organization": "UNGRD Regional",
        "user_objectives": (
            "1. Obtener el consentimiento voluntario para el traslado al albergue modular seguro en 48 horas.\n"
            "2. Completar el censo oficial en el Registro Único de Damnificados (RUD) para viabilizar subsidios.\n"
            "3. Garantizar a las familias la preservación de sus derechos sobre los predios mediante acta notarial."
        ),
        "avatar_name": "Carmen Zabala (Vocera de la Junta Ribereña)",
        "avatar_profile": (
            "Líder comunitaria de 61 años. Ha visto promesas rotas en tres administraciones pasadas donde damnificados quedaron olvidados en carpas plásticas durante años. Defiende la dignidad y los bienes de sus vecinos con tenacidad."
        ),
        "avatar_tone": "Angustiada, enérgica, defensiva y escéptica frente a promesas burocráticas.",
        "avatar_rules": (
            "1. Exigir certificado de que el traslado temporal no extingue sus títulos de posesión.\n"
            "2. No aceptar la salida del coliseo sin verificar en persona los módulos con agua potable y saneamiento.\n"
            "3. Exigir custodia policial permanente para los enseres que quedaron en la zona de riesgo."
        ),
        "persona_notes": "La seguridad sobre sus pertenencias y la certeza jurídica de propiedad son indispensables para destrabar el traslado.",
        "session_turns": [
            ("persona", "Doctor Salamanca, la gente en el coliseo está asustada. Dicen que si nos montamos en esos buses hacia los módulos, la Alcaldía nos va a declarar zona de reserva y nos van a quitar los lotes donde levantamos nuestras casas con tanto sudor. ¡De aquí no nos movemos a ciegas!"),
            ("user", "Doña Carmen, entiendo su angustia y es completamente legítima. Por eso quiero ser categórico: el riesgo de un nuevo alud en la ribera en las próximas 48 horas es del 90% según el IDEAM; mi deber prioritario es salvar la vida de sus hijos y de ustedes. Para su absoluta tranquilidad jurídica, hoy mismo la Personería y la Notaría emitirán un certificado individual de derechos posesorios que garantiza que este traslado es temporal por calamidad y no afecta la titularidad de sus predios."),
            ("persona", "Eso de la Notaría ayuda a calmar a la gente, doctor. Pero, ¿y las condiciones del nuevo sitio? No queremos ir a pasar frío a un lodazal sin baños ni agua."),
            ("user", "La invito a que usted y tres delegados de la junta vayan conmigo en una camioneta en 30 minutos a inspeccionar el terreno. Los módulos cuentan con energía eléctrica, baterias sanitarias completas, cocina comunitaria y carpas médicas. Además, la Policía instalará un cuadrante fijo en el albergue y otro vigilando las casas ribereñas para evitar saqueos de lo que quedó."),
            ("persona", "Si vamos a revisar y constatamos con nuestros propios ojos que hay agua, luz y la presencia policial, yo misma tomo el micrófono en el coliseo y organizo el traslado ordenado por manzanas a primera hora de mañana.")
        ],
        "coaching": {
            "score": 90,
            "resultado_final": "acuerdo_exitoso",
            "resumen_ejecutivo": "Manejo impecable de crisis humanitaria. Supo disipar el temor central de la comunidad (el despojo de tierras) mediante intervención notarial y ofreció transparencia absoluta permitiendo la inspección previa de los albergues.",
            "fortalezas": [
                {"titulo": "Garantía jurídica contundente", "descripcion": "Involucró a la Personería y Notaría para neutralizar el miedo a la pérdida de propiedad.", "cita_usuario": "hoy mismo la Personería y la Notaría emitirán un certificado individual de derechos posesorios que garantiza que este traslado es temporal"},
                {"titulo": "Principio de verificación directa", "descripcion": "Invitó a la líder a comprobar personalmente las condiciones del albergue antes de exigir el traslado.", "cita_usuario": "La invito a que usted y tres delegados de la junta vayan conmigo en una camioneta en 30 minutos a inspeccionar el terreno."}
            ],
            "areas_de_mejora": [
                {"titulo": "Detalle sobre subsidios económicos", "descripcion": "Omitió mencionar los subsidios monetarios de arriendo temporal, enfocándose solo en los albergues físicos.", "cita_usuario": "Los módulos cuentan con energía eléctrica, baterias sanitarias completas", "sugerencia_reformulacion": "Sumado a los módulos, activaremos de inmediato el subsidio de arriendo por tres meses para quienes prefieran ubicarse con familiares."}
            ],
            "tacticas_efectivas": ["Separación de urgencia vital vs certidumbre jurídica", "Inspección conjunta sobre el terreno", "Protección de enseres contra robos"],
            "oportunidades_perdidas": ["Presentar el calendario de soluciones de vivienda definitiva post-emergencia"],
            "recomendacion_principal": "En gestión de desastres, la transparencia física (ver antes de trasladarse) supera cualquier promesa verbal en un comité."
        }
    },

    # ── 4. PÚBLICO: ESPACIO PÚBLICO Y COMERCIO INFORMAL ──
    {
        "sector": "Público",
        "title": "Recuperación de espacio público y reubicación comercial",
        "scenario_text": (
            "Salón de audiencias de la Secretaría de Gobierno. Un fallo judicial de tutela ordenó la recuperación del espacio "
            "público en el corredor peatonal central de la ciudad, ocupado por más de 180 puestos informales. La administración debe cumplir "
            "la orden sin vulnerar el principio de confianza legítima, ofreciendo reubicación en pasajes comerciales y capital semilla."
        ),
        "duration_seconds": 300,
        "user_name": "Dra. Marcela Buendía",
        "user_role": "Subsecretaria de Seguridad y Convivencia",
        "user_organization": "Secretaría Distrital de Gobierno",
        "user_objectives": (
            "1. Cumplir el fallo judicial despejando el corredor peatonal antes del plazo legal del viernes sin uso de la fuerza.\n"
            "2. Lograr la inscripción de al menos el 80% de los comerciantes en los pasajes comerciales distritales.\n"
            "3. Firmar un pacto de convivencia y no retorno respaldado por incentivos económicos de formalización."
        ),
        "avatar_name": "Wilson Quintero (Vocero de Comerciantes Informales)",
        "avatar_profile": (
            "Comerciante informal con 15 años en el centro. Articulado, conoce las sentencias de la Corte Constitucional sobre el mínimo vital "
            "y desconfía de las plazas cerradas porque afirma que allí no hay flujo peatonal."
        ),
        "avatar_tone": "Desafiante, perspicaz, con lenguaje directo pero fundamentos jurídicos sólidos.",
        "avatar_rules": (
            "1. Rechazar el traslado si los locales comerciales tienen costos de arrendamiento inmediatos.\n"
            "2. Exigir campañas de publicidad distrital y rutas de transporte hacia los nuevos pasajes comerciales.\n"
            "3. Amenazar con resistencia pacífica en la calle si el Distrito utiliza la fuerza sin agotar alternativas de sustento."
        ),
        "persona_notes": "Necesita garantías de que sus ventas no colapsarán al pasar de la acera a un local interior.",
        "session_turns": [
            ("persona", "Doctora Marcela, ese fallo de tutela no puede estar por encima de nuestro derecho fundamental al trabajo y a la comida de nuestros hijos. A los compañeros que mandaron a la plaza de San Victorino hace tres años se les quebró el negocio porque allá no entra ni el viento. ¡De la carrera séptima no nos sacan para irnos a morir de hambre!"),
            ("user", "Wilson, comparto que una solución que quiebre a los comerciantes no es una solución real. La Corte Constitucional nos obliga a proteger el mínimo vital y la confianza legítima. Por eso no les estamos proponiendo que se vayan a la suerte. La propuesta de la Alcaldía incluye tres compromisos vinculantes: canon cero de arrendamiento durante los primeros seis meses en el Pasaje Bolívar, una línea de microcrédito condonable de dos millones de pesos por comerciante para surtido, y el desvío de dos rutas alimentadoras del sistema integrado justo frente a la entrada del pasaje."),
            ("persona", "Seis meses de gracia ayudan, pero el problema es el flujo de clientes. Si la gente no sabe que estamos allá, no vendemos un peso."),
            ("user", "Para eso destinamos un presupuesto de 150 millones de pesos en una feria comercial de reapertura, pauta en radio y señalización en todo el centro anunciando la reubicación de sus marcas. Además, el traslado lo haremos de manera escalonada y organizada, con acompañamiento logístico del Distrito para transportar su mercancía sin costo."),
            ("persona", "Si garantizan por escrito los seis meses libres de canon, el microcrédito sin fiador y el apoyo de transporte para la mercancía, nosotros firmamos el pacto de no retorno y empezamos la mudanza voluntaria este mismo miércoles.")
        ],
        "coaching": {
            "score": 86,
            "resultado_final": "acuerdo_exitoso",
            "resumen_ejecutivo": "Negociación muy estructurada y orientada a la viabilidad comercial. Resolvió la objeción principal de la contraparte (la falta de ventas en locales interiores) combinando exención de costos fijos, reactivación de demanda con transporte público y capital de trabajo.",
            "fortalezas": [
                {"titulo": "Resolución de la objeción de fondo", "descripcion": "Abordó de manera integral la preocupación del tráfico peatonal mediante rutas alimentadoras y presupuesto de mercadeo.", "cita_usuario": "el desvío de dos rutas alimentadoras del sistema integrado justo frente a la entrada del pasaje."},
                {"titulo": "Alivio de barreras de entrada", "descripcion": "Ofreció canon cero y crédito condonable para mitigar el riesgo financiero del comerciante en la transición.", "cita_usuario": "canon cero de arrendamiento durante los primeros seis meses... una línea de microcrédito condonable"}
            ],
            "areas_de_mejora": [
                {"titulo": "Falta de definición de penalidades por reincidencia", "descripcion": "No quedó explícito qué ocurrirá si un comerciante beneficiado decide subarrendar el local y volver a la acera.", "cita_usuario": "empezamos la mudanza voluntaria este mismo miércoles", "sugerencia_reformulacion": "Establezcamos en el acta que la asignación del local y el crédito están condicionados a no reincidir en la invasión del andén."}
            ],
            "tacticas_efectivas": ["Alineación con jurisprudencia constitucional", "Mitigación del costo de transición", "Creación de demanda inducida"],
            "oportunidades_perdidas": ["Comprometer a la asociación en el autocontrol del espacio recuperado"],
            "recomendacion_principal": "En procesos de reubicación comercial, asegurar la clientela futura es más persuasivo que cualquier argumento legal sobre el orden público."
        }
    },

    # ── 5. PÚBLICO: AUDITORÍA DE CONTRATACIÓN HOSPITALARIA ──
    {
        "sector": "Público",
        "title": "Descargos en auditoría fiscal de contratación médica",
        "scenario_text": (
            "Auditoría especial de la Contraloría General en el Hospital Universitario. Los auditores levantaron un hallazgo administrativo "
            "con presunto alcance fiscal por $420 millones de pesos por presuntos sobrecostos en la compra de urgencia de reactivos y tomografía. "
            "El Gerente debe justificar la razonabilidad de los precios en mesa contradictoria antes del cierre del informe final."
        ),
        "duration_seconds": 360,
        "user_name": "Dr. Fernando Jaramillo",
        "user_role": "Gerente del Hospital Universitario",
        "user_organization": "ESE Hospitalaria Departamental",
        "user_objectives": (
            "1. Demostrar la trazabilidad técnica que justifica el diferencial de precios por mantenimiento 24/7 y calibración biomédica.\n"
            "2. Desvirtuar la configuración del alcance fiscal antes de la emisión del informe definitivo.\n"
            "3. Acordar la reclasificación del hallazgo a oportunidad de mejora o plan de mejoramiento administrativo."
        ),
        "avatar_name": "Miriam Osorio (Auditora Líder de Contraloría)",
        "avatar_profile": (
            "Contadora pública y especialista en control fiscal con 18 años en el ente de control. Implacable, metódica y rigurosa. "
            "No acepta justificaciones retóricas sin soportes documentales foliados."
        ),
        "avatar_tone": "Técnico, protocolario, distante e inquisitivo; evalúa estrictamente contra tablas del SICEP y normas de contratación.",
        "avatar_rules": (
            "1. No aceptar explicaciones verbales sin estudios de mercado previos y cotizaciones contemporáneas.\n"
            "2. Reclasificar a hallazgo administrativo solo si se demuestra que el precio incluía servicios agregados no estándar.\n"
            "3. Mantener el alcance fiscal si el contrato no acreditó disponibilidad presupuestal previa."
        ),
        "persona_notes": "Solo se conmueve con números auditables, cuadros comparativos de especificaciones y soportes foliados.",
        "session_turns": [
            ("persona", "Doctor Jaramillo, la muestra de auditoría es concluyente. Su hospital contrató reactivos para laboratorio con un valor 32% por encima del precio promedio registrado en la plataforma SICEP para ese trimestre. Esto configura un detrimento patrimonial presunto de 420 millones de pesos. Si no hay una justificación documental contundente, el hallazgo fiscal se mantendrá en el informe final."),
            ("user", "Doctora Osorio, comprendo perfectamente su rigor y comparto el celo por los recursos públicos. Permítame poner sobre la mesa el anexo técnico número tres del contrato que no fue considerado en el cálculo plano del SICEP. Los reactivos que adquirimos no eran de entrega estándar en bodega; el contrato incluía la entrega de dos analizadores automatizados en comodato gratuito, soporte biomédico presencial 24/7 con reposición de repuestos en menos de dos horas, y calibración continua para pacientes de UCI neonatal."),
            ("persona", "El comodato de equipos explica parte del costo, pero los precios de referencia de la circular de salud ya contemplan márgenes de intermediación razonables. ¿Dónde está el estudio de mercado que acreditó que esa modalidad era más económica para el hospital que comprar los reactivos y pagar el mantenimiento por separado?"),
            ("user", "Aquí tiene el folio 142 del expediente precontractual, doctora. Hicimos el costeo financiero comparativo: comprar los analizadores y contratar soporte externo costaba 610 millones de pesos al año. El modelo de comodato integrado con reactivos costó 420 millones. Es decir, generamos un ahorro neto de 190 millones de pesos para la entidad pública, garantizando cero paradas en cuidados intensivos pediátricos."),
            ("persona", "Examinando el folio 142 y la matriz de costo-beneficio, efectivamente se acredita que el valor unitario incluía la amortización del equipo y la disponibilidad permanente de guardia biomédica. El sobrecosto aparente queda desvirtuado técnicamente. Modificaremos el hallazgo a alcance meramente administrativo con recomendación de mejorar la discriminación de ítems en futuras convocatorias.")
        ],
        "coaching": {
            "score": 94,
            "resultado_final": "acuerdo_exitoso",
            "resumen_ejecutivo": "Defensa técnica ejemplar en un escenario de alta presión regulatoria. El usuario no apeló a excusas emocionales, sino que utilizó pruebas documentales foliadas y una matriz de costo-beneficio que transformó la acusación de sobrecosto en una demostración de ahorro público.",
            "fortalezas": [
                {"titulo": "Sustentación documental precisa", "descripcion": "Remitió al auditor a folios contractuales exactos con datos numéricos comparativos.", "cita_usuario": "Aquí tiene el folio 142 del expediente precontractual, doctora. Hicimos el costeo financiero comparativo"},
                {"titulo": "Desagregación del valor agregado", "descripcion": "Evidenció que el precio unitario incorporaba comodato de tecnología y servicio biomédico crítico no cubierto en el precio base de referencia.", "cita_usuario": "el contrato incluía la entrega de dos analizadores automatizados en comodato gratuito, soporte biomédico presencial 24/7"}
            ],
            "areas_de_mejora": [
                {"titulo": "Autocrítica sobre la estructura de ítems", "descripcion": "Pudo haber reconocido desde el principio la falta de claridad en la factura antes de que la auditora lo señalara en sus conclusiones.", "cita_usuario": "Permítame poner sobre la mesa el anexo técnico número tres", "sugerencia_reformulacion": "Reconocemos que la facturación debió desagregar el comodato para facilitar su lectura, pero los números demuestran la eficiencia del gasto."}
            ],
            "tacticas_efectivas": ["Uso de pruebas documentales foliadas", "Inversión de la carga: demostrar ahorro en vez de sobrecosto", "Tono profesional y respetuoso del órgano de control"],
            "oportunidades_perdidas": ["Ofrecer de inmediato la adopción del nuevo formato de discriminación presupuestal"],
            "recomendacion_principal": "Frente a auditorías de control fiscal, el único lenguaje eficaz son las matrices comparativas de mercado y la trazabilidad contractual."
        }
    },

    # ── 6. PRIVADO: CONTRATO DE SUMINISTRO POR INFLACIÓN ──
    {
        "sector": "Privado",
        "title": "Renegociación de contrato de suministro por sobrecostos",
        "scenario_text": (
            "Negociación contractual entre Alimentos NutriGlobal y su proveedor crítico de resinas y empaques PolyTech. "
            "El proveedor notificó un incremento unilateral del 22% con vigencia en 15 días, argumentando la subida del flete marítimo "
            "y precios de resinas, o de lo contrario suspenderá los despachos, paralizando la línea de producción principal."
        ),
        "duration_seconds": 300,
        "user_name": "Juan Pablo Echeverri",
        "user_role": "Director de Abastecimiento Estratégico",
        "user_organization": "Alimentos NutriGlobal S.A.",
        "user_objectives": (
            "1. Limitar el incremento de precios a un máximo del 9.5% indexado a índices verificables.\n"
            "2. Extender el plazo contractual a 2 años a cambio de exclusividad en dos plantas nuevas.\n"
            "3. Garantizar continuidad inmediata de despachos sin penalidades de inventario mínimo."
        ),
        "avatar_name": "Marcus Vance (Director Comercial Regional de PolyTech)",
        "avatar_profile": (
            "Ejecutivo comercial multinacional radicado en São Paulo. Maneja cuentas corporativas de gran volumen. Sabe que homologar "
            "un nuevo proveedor le tomaría a NutriGlobal al menos cuatro meses de pruebas sanitarias."
        ),
        "avatar_tone": "Asertivo, corporativo, amable en el trato pero implacable con las metas de margen de su matriz.",
        "avatar_rules": (
            "1. No aceptar ajustes menores al 16% sin un compromiso vinculante de volumen ampliado.\n"
            "2. Recordar cortésmente las demoras de homologación técnica si el cliente amenaza con cancelar.\n"
            "3. Ceder a tarifas escalonadas solo si el plazo de pago se reduce de 90 a 30 días."
        ),
        "persona_notes": "Sensible al volumen agregado a largo plazo y a la reducción de días de cartera.",
        "session_turns": [
            ("persona", "Juan Pablo, gusto en saludarte. Entiendo la sorpresa por el ajuste del 22%, pero el índice internacional ICIS de polímeros subió un 35% y los fletes de Asia se triplicaron. PolyTech no puede seguir subsidiando el margen de NutriGlobal. Si no tenemos la adenda firmada este viernes, los despachos de noviembre tendrán que ser pausados."),
            ("user", "Marcus, agradezco la franqueza. Sin embargo, un incremento del 22% de la noche a la mañana está fuera de cualquier parámetro comercial y destruye la rentabilidad de nuestra categoría. Si nos obligas a trasladar eso al consumidor, nuestras ventas caerán y tus pedidos también. En lugar de una ruptura, te propongo una solución estructural de ganar-ganar: aceptamos un incremento inmediato del 9% indexado trimestralmente al índice ICIS, reducimos los términos de pago de 90 a 35 días para aliviar tu flujo de caja, y te otorgamos la exclusividad del suministro de nuestras dos nuevas plantas de exportación por los próximos 24 meses."),
            ("persona", "El pronto pago a 35 días y las dos nuevas plantas son atractivos en volumen, Juan Pablo. Pero un 9% sigue dejándome en pérdida operativa el primer trimestre con los fletes actuales. Necesito al menos un 14% para equilibrar."),
            ("user", "Hagamos lo siguiente, Marcus: cerremos en 10.5% fijo para este trimestre. Si en enero el índice de fletes de Shanghái sigue por encima de los 4,500 dólares, aplicamos una sobretasa logística temporal del 3% que se extingue automáticamente cuando el flete baje. A cambio, hoy mismo firmamos el contrato extendido a 24 meses que garantiza un 40% más de volumen total para PolyTech."),
            ("persona", "Esa sobretasa flotante condicionada al flete marítimo protege nuestro margen de contingencia y la exclusividad por dos años compensa con creces el volumen. Tenemos un acuerdo, Juan Pablo. Envío la adenda con esos términos hoy mismo.")
        ],
        "coaching": {
            "score": 91,
            "resultado_final": "acuerdo_exitoso",
            "resumen_ejecutivo": "Magistral aplicación de negociación integrativa basada en intereses. El usuario evitó la trampa posicional del porcentaje fijo, introduciendo términos de pago más rápidos, volumen futuro y una cláusula indexada flotante que satisfizo los requisitos de rentabilidad del proveedor.",
            "fortalezas": [
                {"titulo": "Moneda de cambio de alto valor financiero", "descripcion": "Ofreció reducir los días de cartera de 90 a 35 días, impactando positivamente el capital de trabajo de la contraparte.", "cita_usuario": "reducimos los términos de pago de 90 a 35 días para aliviar tu flujo de caja"},
                {"titulo": "Diseño de tarifa flotante indexada", "descripcion": "Creó un mecanismo de sobretasa temporal ligada a indicadores externos objetivos (fletes) que se apaga automáticamente.", "cita_usuario": "aplicamos una sobretasa logística temporal del 3% que se extingue automáticamente cuando el flete baje."}
            ],
            "areas_de_mejora": [
                {"titulo": "Falta de penalidad por retrasos de entrega", "descripcion": "Aceptó la sobretasa sin exigir a cambio un compromiso formal de SLA de entrega a tiempo bajo sanción económica.", "cita_usuario": "cerremos en 10.5% fijo para este trimestre", "sugerencia_reformulacion": "Aceptamos la sobretasa flotante a condición de que PolyTech asuma una penalidad del 2% por cada día de retraso en planta."}
            ],
            "tacticas_efectivas": ["Uso de estándares objetivos (Índice ICIS)", "Compromiso de volumen agregado a cambio de precio", "Indexación temporal de contingencias"],
            "oportunidades_perdidas": ["Exigir auditoría de costos de importación de la resina"],
            "recomendacion_principal": "Cuando un proveedor argumenta sobrecostos externos, la mejor respuesta es indexar el precio a esos indicadores para que el sobrecosto se extinga cuando el mercado se normalice."
        }
    },

    # ── 7. PRIVADO: DESVINCULACIÓN DE EJECUTIVO C-LEVEL ──
    {
        "sector": "Privado",
        "title": "Desvinculación negociada de Vicepresidente de Operaciones",
        "scenario_text": (
            "Reunión ejecutiva a puerta cerrada. El Vicepresidente de Operaciones de una firma de logística digital lleva 7 años "
            "en la empresa, pero tras desacuerdos irreconciliables con el nuevo CEO y metas incumplidas, el Directorio decidió su salida. "
            "Se debe negociar su renuncia concertada, paquete de salida y acuerdo de confidencialidad, evitando litigios o filtraciones."
        ),
        "duration_seconds": 300,
        "user_name": "Claudia Montes",
        "user_role": "Chief Human Resources Officer (CHRO)",
        "user_organization": "FinCorp Logística Latam",
        "user_objectives": (
            "1. Obtener la renuncia voluntaria concertada con paz y salvo laboral total.\n"
            "2. Acordar una compensación máxima equivalente a 7 meses de salario más cobertura de salud y outplacement.\n"
            "3. Suscribir cláusula de no competencia y no denigración por 18 meses para blindar la reputación de la firma."
        ),
        "avatar_name": "Roberto Silva (Vicepresidente de Operaciones Saliente)",
        "avatar_profile": (
            "Ingeniero industrial, co-creador del modelo operativo de la empresa. Siente que el nuevo CEO lo desplazó injustamente. "
            "Está respaldado por abogados laboralistas y conoce secretos comerciales e información de gobernanza sensible."
        ),
        "avatar_tone": "Orgulloso, herido pero contenido, con respuestas filosas y sensibilidad extrema hacia su imagen pública.",
        "avatar_rules": (
            "1. Exigir 18 meses de indemnización y aceleración inmediata de stock options no vesteadas.\n"
            "2. Rechazar cualquier insinuación de 'bajo rendimiento' o descalificación profesional.\n"
            "3. Ceder en el monto económico solo si la empresa le permite controlar el comunicado oficial y ofrece carta de recomendación de la junta."
        ),
        "persona_notes": "El ego, el reconocimiento a su legado y el control de la narrativa pública son más decisivos que el dinero puro.",
        "session_turns": [
            ("persona", "Claudia, no nos engañemos con rodeos corporativos. Sé perfectamente que el nuevo CEO quiere a su propia gente y le incomoda que yo conozca los números reales de la operación. Construí esta compañía durante siete años. Si pretenden sacarme con la liquidación básica de ley, mis abogados ya tienen lista la demanda laboral y una solicitud de auditoría externa."),
            ("user", "Roberto, precisamente porque conocemos tu trayectoria y el valor inmenso de lo que construiste en estos siete años, estamos sentados tú y yo a puerta cerrada. Nadie en esta junta directiva desconoce tu legado. Pero también sabes que la visión estratégica hoy va por otro camino y desgastarnos en una disputa legal solo destruiría el valor de la empresa que tú mismo fundaste y mancharía tu reputación en el mercado. Queremos que salgas por la puerta grande."),
            ("persona", "Salir por la puerta grande cuesta, Claudia. Mis stock options no consolidadas representan cuatro años de sacrificio, y mis honorarios de asesoría valen. No firmo nada por menos de un año y medio de compensación."),
            ("user", "Hablemos de lo que de verdad te garantiza un futuro brillante. Te ofrezco un paquete integral: siete meses de compensación económica directa, el mantenimiento de tu cobertura médica familiar por un año completo, un servicio de outplacement de primer nivel para tu próxima posición en juntas directivas, y lo más importante: tú redactas el comunicado oficial de salida indicando que emprendes nuevos proyectos personales, respaldado por una carta de reconocimiento firmada por los miembros fundadores de la junta."),
            ("persona", "Poder redactar el comunicado conjunto y la carta de recomendación de la junta es indispensable para mi perfil. Si subes la compensación a nueve meses y me aceleras el 50% de las opciones que estaban por vencer este año, firmo el mutuo acuerdo y el pacto de confidencialidad y no competencia por 18 meses hoy mismo.")
        ],
        "coaching": {
            "score": 87,
            "resultado_final": "acuerdo_parcial",
            "resumen_ejecutivo": "Manejo maduro y diplomático de una desvinculación ejecutiva de alto riesgo. El usuario identificó correctamente que el motor de la negociación no era únicamente monetario, sino la protección del prestigio y el relato de salida del profesional.",
            "fortalezas": [
                {"titulo": "Preservación de la dignidad del ejecutivo", "descripcion": "Validó el legado de siete años del directivo antes de discutir los términos de separación.", "cita_usuario": "Nadie en esta junta directiva desconoce tu legado... Queremos que salgas por la puerta grande."},
                {"titulo": "Moneda de cambio reputacional", "descripcion": "Ofreció el control de la narrativa pública y la carta de respaldo de los fundadores como parte nuclear del paquete.", "cita_usuario": "tú redactas el comunicado oficial de salida indicando que emprendes nuevos proyectos personales"}
            ],
            "areas_de_mejora": [
                {"titulo": "Cierre de términos financieros en stock options", "descripcion": "Dejó en el aire la contrapropuesta de aceleración del 50% de las opciones sin verificar la aprobación del comité de compensación.", "cita_usuario": "Hablemos de lo que de verdad te garantiza un futuro brillante", "sugerencia_reformulacion": "Puedo avalar los nueve meses de salida hoy, pero la aceleración de opciones requiere consulta inmediata con el comité en receso de 15 minutos."}
            ],
            "tacticas_efectivas": ["Apelación al costo de oportunidad y prestigio profesional", "Cesión del control del comunicado", "Outplacement directivo como valor añadido"],
            "oportunidades_perdidas": ["Vincular parte de la indemnización al cumplimiento estricto del periodo de no competencia"],
            "recomendacion_principal": "En salidas de nivel C-Suite, permitir que el ejecutivo diseñe la narrativa de su partida ahorra millones en indemnizaciones forzadas."
        }
    },

    # ── 8. PRIVADO: CRISIS SAAS CON CLIENTE BANCARIO ──
    {
        "sector": "Privado",
        "title": "Gestión de crisis con cliente bancario por caída de servicio",
        "scenario_text": (
            "Reunión de urgencia con el CIO de un banco comercial de primera línea. La plataforma SaaS de autenticación y transferencias "
            "sufrió una caída crítica de 7 horas en plena jornada de pago de nómina, afectando a 1.2 millones de usuarios. El banco exige "
            "una indemnización de $350,000 USD y amenaza con rescindir unilateralmente el contrato maestro por incumplimiento de SLA."
        ),
        "duration_seconds": 360,
        "user_name": "Alejandro Forero",
        "user_role": "VP of Customer Success y Co-Fundador",
        "user_organization": "PaySecure Cloud Solutions",
        "user_objectives": (
            "1. Evitar la rescisión del contrato maestro y neutralizar el inicio de acciones judiciales inmediatas.\n"
            "2. Negociar la compensación mediante créditos de servicio de nube y desarrollo a la medida en lugar de efectivo.\n"
            "3. Acordar un plan de remediación técnica conjunta con auditoría de infraestructura en 15 días."
        ),
        "avatar_name": "Valeria Domínguez (CIO Banco Sudamericano)",
        "avatar_profile": (
            "Chief Information Officer del banco. Tuvo que rendir cuentas al comité de riesgos y a la Superintendencia Financiera. "
            "Su credibilidad interna está bajo fuego y necesita demostrar firmeza implacable frente al proveedor tecnológico."
        ),
        "avatar_tone": "Fría, contundente, acusatoria, sin espacio para justificaciones ni disculpas vacías.",
        "avatar_rules": (
            "1. Cortar de raíz cualquier intento de culpar a proveedores de nube (AWS/Azure).\n"
            "2. Exigir la deducción directa de la penalidad en la facturación mensual.\n"
            "3. Aceptar no rescindir únicamente si se ofrece soporte dedicado en sitio y SLA blindado con penalidades reforzadas."
        ),
        "persona_notes": "Exige asunción total de responsabilidad y compromisos de redundancia operativa medibles.",
        "session_turns": [
            ("persona", "Alejandro, no me haga perder el tiempo con disculpas corporativas preparadas por su departamento legal. Tuvimos a un millón doscientos mil usuarios bloqueados sin poder retirar su nómina durante siete horas. El presidente del banco y la Superintendencia me pidieron explicaciones. El SLA del 99.9% fue pulverizado. Nuestro departamento legal tiene lista la demanda de rescisión y la exigencia de la cláusula penal por 350 mil dólares."),
            ("user", "Ingeniera Valeria, asumo la total y absoluta responsabilidad a nombre de los fundadores y del equipo de PaySecure. Lo ocurrido ayer fue inaceptable y no vengo a justificarme ni a culpar a nuestros proveedores de nube. Si el banco decide rescindir, está en su derecho contractual. Pero antes de tomar esa decisión, quiero mostrarle lo que ya ejecutamos: identificamos el cuello de botella en la base de datos distribuida, desplegamos un parche de aislamiento de réplicas a las 3:00 a.m. y pusimos en marcha una reingeniería de arquitectura con failover multirregional automático."),
            ("persona", "El parche debió estar listo antes de la caída, no después. El daño reputacional del banco no se borra con un despliegue de madrugada. ¿Cómo responde PaySecure por las pérdidas financieras de la entidad?"),
            ("user", "Le propongo una restitución que genera valor real para el banco: primero, aplicamos el 100% de la penalidad de SLA legalmente pactada en la próxima factura por 120 mil dólares. Segundo, entregamos 150 mil dólares en créditos de desarrollo para la nueva integración biométrica que el banco tenía presupuestada para el próximo año. Tercero, asignamos a un arquitecto de confiabilidad (SRE) senior dedicado en sitio en las oficinas del banco durante los próximos seis meses. Y cuarto, financiamos una auditoría de ciberseguridad independiente con la firma que ustedes elijan para certificar la nueva infraestructura."),
            ("persona", "El arquitecto en sitio y la auditoría externa financiada por ustedes son indispensables para mi reporte a la Superintendencia. Si además de los créditos de desarrollo nos garantizan tres meses de servicio base sin cobro y duplicamos la penalidad en caso de reincidencia este semestre, congelo la orden de rescisión y aprobamos el plan de remediación técnica.")
        ],
        "coaching": {
            "score": 89,
            "resultado_final": "acuerdo_exitoso",
            "resumen_ejecutivo": "Manejo ejemplar de crisis técnica crítica. El usuario no cayó en la tentación de eludir culpas ni desviar la responsabilidad a terceros, lo que desarmó la furia de la contraparte y permitió migrar de un escenario punitivo de demanda judicial a un plan de fortalecimiento técnico conjunto.",
            "fortalezas": [
                {"titulo": "Asunción radical de responsabilidad", "descripcion": "Aceptó el error sin rodeos ni excusas burocráticas, validando la gravedad del impacto del cliente.", "cita_usuario": "asumo la total y absoluta responsabilidad a nombre de los fundadores... Lo ocurrido ayer fue inaceptable"},
                {"titulo": "Conversión de daño en solución de valor", "descripcion": "Ofreció ingenieros dedicados en sitio y financiamiento de auditorías para resolver la necesidad política del CIO frente a su regulador.", "cita_usuario": "asignamos a un arquitecto de confiabilidad (SRE) senior dedicado en sitio en las oficinas del banco... Y cuarto, financiamos una auditoría de ciberseguridad independiente"}
            ],
            "areas_de_mejora": [
                {"titulo": "Aceptación de penalidades dobles", "descripcion": "La contraparte exigió duplicar penalidades por reincidencia; se debió acotar ese riesgo con un periodo de estabilización previo.", "cita_usuario": "Si el banco decide rescindir, está en su derecho contractual", "sugerencia_reformulacion": "Aceptamos la penalidad reforzada una vez finalizada la auditoría de 15 días, asegurando un periodo de estabilización técnica coordinado."}
            ],
            "tacticas_efectivas": ["Adopción temprana de la culpa", "Compensación en servicios de alto margen para el proveedor y alto valor para el cliente", "Soporte embebido como anclaje de retención"],
            "oportunidades_perdidas": ["Negociar una extensión del contrato por 12 meses adicionales a cambio del paquete de compensación"],
            "recomendacion_principal": "En crisis de disponibilidad tecnológica, entregar recursos humanos dedicados al cliente repara la confianza más rápido que cualquier descuento monetario pasivo."
        }
    },

    # ── 9. PRIVADO: RONDA VENTURE CAPITAL SERIE A ──
    {
        "sector": "Privado",
        "title": "Negociación de Term Sheet para inversión Serie A",
        "scenario_text": (
            "Discusión final de términos de inversión (Term Sheet) en las oficinas de un fondo de Venture Capital. La startup de logística "
            "inversa busca cerrar una ronda Serie A por 3.5 millones de USD. El fondo envió una oferta exigiendo liquidación preferente 2X "
            "participante, derecho de veto en contrataciones clave y dos de los cinco asientos en la junta directiva."
        ),
        "duration_seconds": 360,
        "user_name": "Mariana Ospina",
        "user_role": "CEO y Fundadora",
        "user_organization": "EcoRoute Technologies",
        "user_objectives": (
            "1. Modificar la cláusula de liquidación preferente a 1X no participante (estándar de mercado transparente).\n"
            "2. Retener el control fundador en la junta directiva, limitando al fondo a 1 asiento.\n"
            "3. Mantener la valoración post-money en un rango no menor a 16 millones de USD con base en el crecimiento de tracción."
        ),
        "avatar_name": "Rodrigo De la Torre (General Partner en Andina Ventures)",
        "avatar_profile": (
            "Inversionista de capital de riesgo con más de 30 inversiones en etapas tempranas. Analítico, sofisticado, evalúa el balance "
            "entre la protección contra caídas (downside protection) y el alineamiento con fundadores sobresalientes."
        ),
        "avatar_tone": "Carismático, financiero, persuasivo; usa silencios y comparaciones de mercado para presionar concesiones.",
        "avatar_rules": (
            "1. No renunciar a la liquidación preferente sin asegurar un veto en ventas corporativas o desinversiones.\n"
            "2. Exigir esquema de permanencia (reverse vesting de 4 años) para los dos cofundadores.\n"
            "3. Ceder en el segundo asiento de junta solo si se crea un rol de observador sin voto y un puesto independiente neutral."
        ),
        "persona_notes": "Valora a los fundadores con carácter que defienden su capitalización con métricas de retención y márgenes limpios.",
        "session_turns": [
            ("persona", "Mariana, nos encanta lo que has construido en EcoRoute. Pero en el contexto actual de tasas de interés y mercado de capitales restrictivo, una valoración de 16 millones requiere salvaguardas reales para nuestros socios limitados (LPs). La liquidación preferente participante 2X y los dos asientos en la junta son la condición indispensable del comité para liberar los 3.5 millones de dólares."),
            ("user", "Rodrigo, valoramos profundamente a Andina Ventures como socio estratégico para escalar a México y Brasil. Pero seamos transparentes: una liquidación preferente participante 2X no es estándar para una compañía que creció sus ingresos recurrentes (ARR) en un 210% el último año con un churn neto negativo del 108%. Eso castiga injustamente al equipo fundador en un escenario de salida razonable y desalinea nuestros incentivos de largo plazo. El estándar justo es 1X no participante."),
            ("persona", "Entiendo tu punto sobre los incentivos del equipo fundador, Mariana. Pero el riesgo de ejecución en la expansión regional sigue siendo alto. Si eliminamos la participación del 2X, tengo que justificarle a mi comité una protección alternativa frente a una venta prematura."),
            ("user", "Te ofrezco una estructura equilibrada: aceptamos la cláusula de liquidación preferente 1X no participante. Para proteger al fondo frente a ventas a la baja, les otorgamos derecho de veto en fusiones o adquisiciones que ocurran por debajo de 25 millones de dólares durante los primeros 24 meses. En la junta, otorgamos un asiento con derecho a voto para Andina Ventures, tres para los fundadores y creamos un puesto de observador independiente para un experto del sector logístico consensuado entre ambas partes."),
            ("persona", "El veto por debajo de 25 millones mitiga el riesgo de liquidación barata y la figura del observador independiente equilibra la gobernanza. Si mantenemos los 3.5 millones en una valoración de 15.5 millones post-money con esa estructura, tenemos acuerdo de Term Sheet hoy.")
        ],
        "coaching": {
            "score": 93,
            "resultado_final": "acuerdo_exitoso",
            "resumen_ejecutivo": "Negociación financiera sobresaliente. La fundadora defendió la tabla de capitalización y el control de la compañía utilizando métricas unitarias impecables y ofreciendo mecanismos de protección de riesgo (hurdle de venta mínima) que satisficieron al fondo sin hipotecar el capital accionario.",
            "fortalezas": [
                {"titulo": "Fundamentación en tracción y métricas de mercado", "descripcion": "Utilizó indicadores objetivos de desempeño (210% crecimiento ARR, churn neto negativo) para desestimar cláusulas predadoras.", "cita_usuario": "una liquidación preferente participante 2X no es estándar para una compañía que creció sus ingresos recurrentes (ARR) en un 210%"},
                {"titulo": "Diseño de salvaguarda de sustitución", "descripcion": "Reemplazó una cláusula tóxica (2X participante) por un veto condicionado a un precio de salida mínimo, protegiendo al fondo de liquidaciones a la baja.", "cita_usuario": "les otorgamos derecho de veto en fusiones o adquisiciones que ocurran por debajo de 25 millones de dólares"}
            ],
            "areas_de_mejora": [
                {"titulo": "Concesión de valoración final", "descripcion": "Aceptó implícitamente bajar a 15.5 millones post-money sin pelear el rango de 16 millones de partida.", "cita_usuario": "Te ofrezco una estructura equilibrada", "sugerencia_reformulacion": "Fijemos 16 millones con base en los cierres del último trimestre; si no alcanzamos la meta de ARR a junio, ajustamos mediante notas convertibles."}
            ],
            "tacticas_efectivas": ["Defensa de alineación de incentivos", "Creación de gobernanza con observador neutral", "Uso de cláusulas piso en ventas"],
            "oportunidades_perdidas": ["Negociar derechos preferentes de pro-rata para rondas Serie B"],
            "recomendacion_principal": "En negociaciones de Venture Capital, nunca cedas en liquidaciones participantes: ofrece protección en gobernanza o derechos de veto antes de ceder la economía de las acciones."
        }
    },

    # ── 10. PRIVADO: RETENCIÓN DE TALENTO CLAVE M&A ──
    {
        "sector": "Privado",
        "title": "Retención de talento técnico clave post-fusión",
        "scenario_text": (
            "Oficinas de la boutique de ciberseguridad adquirida hace tres semanas por la multinacional GlobalTech. "
            "El Principal Cloud Architect y cerebro técnico del software núcleo recibió una oferta de una empresa competidora "
            "y manifestó frustración con la burocracia y herramientas heredadas de la corporación. Su salida desataría renuncias en cadena de 12 ingenieros senior."
        ),
        "duration_seconds": 300,
        "user_name": "Daniel Carvajal",
        "user_role": "Director de Integración y M&A",
        "user_organization": "GlobalTech Enterprise Solutions",
        "user_objectives": (
            "1. Asegurar la permanencia del arquitecto jefe por un periodo mínimo de 24 meses clave para la integración.\n"
            "2. Diseñar un paquete de retención atractivo combinando bono de permanencia y autonomía técnica.\n"
            "3. Blindar la continuidad del equipo de 12 desarrolladores senior sin fugas a la competencia."
        ),
        "avatar_name": "Esteban Morales (Principal Cloud Architect)",
        "avatar_profile": (
            "Ingeniero prodigio de 34 años, arquitecto del software núcleo. Le frustra la política corporativa y las reuniones burocráticas. "
            "Considera que GlobalTech está arruinando la agilidad técnica de la boutique con procesos lentos."
        ),
        "avatar_tone": "Directo, pragmático, desencantado de la retórica corporativa y celoso de su autonomía profesional.",
        "avatar_rules": (
            "1. Rechazar cualquier oferta que se limite a aumentos salariales sin autonomía técnica real.\n"
            "2. Exigir reporte directo al CTO Global sin intermediarios de mandos medios regionales.\n"
            "3. Exigir presupuesto discrecional para licencias y certificaciones de su equipo directo."
        ),
        "persona_notes": "Lo mueve el reto técnico y la libertad de crear sin burocracia; el dinero es necesario pero insuficiente por sí solo.",
        "session_turns": [
            ("persona", "Daniel, te pedí esta reunión para ser transparente antes de que sea tarde. En tres semanas bajo GlobalTech he pasado más tiempo llenando formularios de seguridad y justificando herramientas que programando. Nos prometieron que respetarían nuestra autonomía, pero ya nos quieren obligar a migrar a sus sistemas monolíticos de hace quince años. Tengo una oferta sobre la mesa de una scale-up suiza con trabajo 100% remoto y libertad total de arquitectura. Si esto sigue así, no solo me voy yo, sino que la mitad del equipo técnico se viene conmigo."),
            ("user", "Esteban, agradezco que pongas las cartas sobre la mesa directamente. Tienes toda la razón: la mayor pesadilla de una adquisición es cuando la burocracia corporativa ahoga la innovación del equipo que precisamente compramos por su genialidad. No adquirimos su empresa para convertirlos en un departamento más de TI tradicional. Adquirimos su producto para que sea el motor de modernización de toda la compañía global. Mi prioridad hoy es blindar tu espacio."),
            ("persona", "Las palabras suenan bien, Daniel, pero la realidad del día a día son tres comités semanales y aprobaciones de un mes para comprar licencias de desarrollo. ¿Cómo se traduce ese 'blindaje' en la práctica?"),
            ("user", "Se traduce en cuatro decisiones vinculantes que ya hablé con el CTO Global: primero, tu equipo mantendrá su condición de unidad autónoma de I+D (R&D Lab) reportando directamente al CTO corporativo, sin intermediarios regionales. Segundo, tú mantienes la potestad exclusiva para definir la arquitectura y las herramientas técnicas de tu producto. Tercero, un presupuesto discrecional de 80 mil dólares anuales para capacitación y licencias de tu equipo. Y cuarto, formalizamos para ti un paquete de retención con un bono de permanencia a 24 meses y el nombramiento formal como Distinguished Fellow del grupo."),
            ("persona", "El reporte directo al CTO Global y la autonomía presupuestal para el equipo resuelven el 90% de mi frustración. Con esas garantías operativas y el bono de permanencia a dos años, me quedo y me comprometo a liderar la integración técnica y asegurar que ningún ingeniero clave se vaya.")
        ],
        "coaching": {
            "score": 92,
            "resultado_final": "acuerdo_exitoso",
            "resumen_ejecutivo": "Negociación de retención de talento estratégico ejecutada con alta sofisticación. El usuario reconoció el problema real (la asfixia burocrática del talento creativo) y diseñó una estructura organizativa a la medida (R&D Lab autónomo con reporte al C-Level) que salvó el valor nuclear de la adquisición.",
            "fortalezas": [
                {"titulo": "Validación empática de la frustración técnica", "descripcion": "Reconoció el riesgo real de la burocracia corporativa sin ponerse a la defensiva ni justificar los procesos lentos.", "cita_usuario": "la mayor pesadilla de una adquisición es cuando la burocracia corporativa ahoga la innovación del equipo"},
                {"titulo": "Solución estructural de gobernanza", "descripcion": "Blindó al talento creando una unidad autónoma con reporte directo a la máxima autoridad técnica de la corporación.", "cita_usuario": "tu equipo mantendrá su condición de unidad autónoma de I+D (R&D Lab) reportando directamente al CTO corporativo"}
            ],
            "areas_de_mejora": [
                {"titulo": "Compromiso de retención escalonada para el equipo", "descripcion": "El acuerdo retuvo al líder técnico, pero no contempló incentivos formales de permanencia directos para los 12 ingenieros a su cargo.", "cita_usuario": "un presupuesto discrecional de 80 mil dólares anuales para capacitación", "sugerencia_reformulacion": "Sumado a tu bono, aprobemos un plan de retención y bonos por hitos de entrega para los 12 ingenieros de tu equipo."}
            ],
            "tacticas_efectivas": ["Creación de estructuras ágiles protegidas", "Empoderamiento técnico frente a mandos medios", "Alineación con el ego profesional del talento"],
            "oportunidades_perdidas": ["Firmar un acuerdo de cesión de propiedad intelectual reforzado"],
            "recomendacion_principal": "En adquisiciones tecnológicas, el mejor paquete de compensación para los fundadores técnicos es la inmunidad frente a la burocracia corporativa."
        }
    }
]


from sqlalchemy import text as sql_text

def seed_all_cases_and_sessions(purge_existing: bool = True):
    with DBSession(engine) as db:
        if purge_existing:
            print("Eliminando informes, sesiones, turnos y casos anteriores...")
            try:
                db.exec(sql_text('DELETE FROM nonverbalsnapshot;'))
                db.exec(sql_text('DELETE FROM turn;'))
                db.exec(sql_text('DELETE FROM session;'))
                db.exec(sql_text('DELETE FROM "case";'))
                db.commit()
                print("Purga de registros antiguos completada con éxito.")
            except Exception as e:
                print(f"Aviso durante la purga: {e}")
                db.rollback()

        for idx, item in enumerate(CASES_DATA):
            title = item["title"]
            existing_case = db.exec(select(Case).where(Case.title == title)).first()
            
            if not existing_case:
                case = Case(
                    title=title,
                    scenario_text=item["scenario_text"],
                    duration_seconds=item["duration_seconds"],
                    user_name=item["user_name"],
                    user_role=item["user_role"],
                    user_organization=item["user_organization"],
                    user_objectives=item["user_objectives"],
                    avatar_name=item["avatar_name"],
                    avatar_profile=item["avatar_profile"],
                    avatar_tone=item["avatar_tone"],
                    avatar_rules=item["avatar_rules"],
                    persona_notes=item["persona_notes"],
                )
                db.add(case)
                db.commit()
                db.refresh(case)
            else:
                case = existing_case
                # Actualizar campos por si acaso
                case.scenario_text = item["scenario_text"]
                case.duration_seconds = item["duration_seconds"]
                case.user_name = item["user_name"]
                case.user_role = item["user_role"]
                case.user_organization = item["user_organization"]
                case.user_objectives = item["user_objectives"]
                case.avatar_name = item["avatar_name"]
                case.avatar_profile = item["avatar_profile"]
                case.avatar_tone = item["avatar_tone"]
                case.avatar_rules = item["avatar_rules"]
                case.persona_notes = item["persona_notes"]
                db.add(case)
                db.commit()
                db.refresh(case)

            # Verificar si ya tiene sesión completada con coaching report
            existing_session = db.exec(
                select(NegotiationSession).where(
                    NegotiationSession.case_id == case.id,
                    NegotiationSession.status == "completed"
                )
            ).first()

            if not existing_session:
                start_time = datetime.utcnow() - timedelta(days=random.randint(1, 15), hours=random.randint(1, 10))
                end_time = start_time + timedelta(minutes=random.randint(4, 7))
                
                # Métricas sintéticas de cámara
                pct_cam = round(random.uniform(72.0, 94.0), 1)
                avg_yaw = round(random.uniform(4.5, 9.8), 2)
                avg_pitch = round(random.uniform(3.2, 7.5), 2)
                happy = round(random.uniform(12.0, 28.0), 1)
                sad = round(random.uniform(2.0, 8.0), 1)
                anger = round(random.uniform(1.0, 5.0), 1)
                fear = round(random.uniform(0.5, 4.0), 1)

                nonverbal_summary = {
                    "sample_count": 85,
                    "pct_looking_at_camera": pct_cam,
                    "avg_yaw_abs": avg_yaw,
                    "avg_pitch_abs": avg_pitch,
                    "avg_smile_score": 0.21,
                    "pct_happiness": happy,
                    "pct_anger": anger,
                    "pct_sadness": sad,
                    "pct_fear": fear,
                }

                session = NegotiationSession(
                    case_id=case.id,
                    started_at=start_time,
                    ended_at=end_time,
                    status="completed",
                    nonverbal_summary_json=json.dumps(nonverbal_summary),
                    coaching_report_json=json.dumps(item["coaching"], ensure_ascii=False)
                )
                db.add(session)
                db.commit()
                db.refresh(session)

                # Agregar turnos de diálogo
                for t_idx, (role, text) in enumerate(item["session_turns"]):
                    turn = Turn(
                        session_id=session.id,
                        turn_index=t_idx,
                        role=role,
                        text=text,
                        created_at=start_time + timedelta(seconds=t_idx * 45)
                    )
                    db.add(turn)

                # Generar snapshots de prueba para el gráfico
                for snap_idx in range(40):
                    ts_ms = snap_idx * 5000
                    snapshot = NonverbalSnapshot(
                        session_id=session.id,
                        ts_ms=ts_ms,
                        yaw=round(random.uniform(-10.0, 10.0), 2),
                        pitch=round(random.uniform(-8.0, 8.0), 2),
                        roll=round(random.uniform(-4.0, 4.0), 2),
                        looking_at_camera=random.random() > 0.15,
                        happiness=round(random.uniform(0.0, 0.4), 2),
                        anger=round(random.uniform(0.0, 0.1), 2),
                        sadness=round(random.uniform(0.0, 0.1), 2),
                        fear=round(random.uniform(0.0, 0.05), 2),
                    )
                    db.add(snapshot)

                db.commit()
                print(f"[{idx+1}/10] Sembrada sesión e informe para: {case.title} (Sector {item['sector']})")
            else:
                print(f"[{idx+1}/10] Caso y sesión ya existían: {case.title}")

    print("¡Todos los 10 casos e informes sintéticos han sido generados con éxito!")

if __name__ == "__main__":
    seed_all_cases_and_sessions()
