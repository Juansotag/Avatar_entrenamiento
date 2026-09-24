import sys
sys.path.insert(0, ".")
import json
from datetime import datetime, timedelta, timezone
import random
from sqlmodel import Session as DBSession, select

from app.db import engine
from app.models import Case, NegotiationSession, Turn, NonverbalSnapshot

CASES_DATA = [{'sector': 'Público',
  'title': 'Concertación del pliego salarial distrital en el Palacio Liévano',
  'scenario_text': 'Mesa Central de Negociación Estatal en el Salón de Protocolo del Palacio Liévano (Plaza de '
                   'Bolívar, Bogotá D.C.). La coalición sindical distrital (SINDISTRITALES y FENALTRASE) radicó el '
                   'pliego unitario exigiendo un incremento del IPC + 6.2%, bonificación quinquenal y formalización de '
                   'teletrabajo de 4 días a la semana para 18.000 servidores de la planta central y localidades. La '
                   'Secretaría de Hacienda y el Departamento Administrativo del Servicio Civil Distrital (DASCD) '
                   'fijaron el techo financiero en el marco de la Ley 617 de 2000 y el Decreto Nacional 243 de 2024. '
                   'Si no se logra un acuerdo antes del cierre de la prórroga hoy a las 6:00 p.m., los sindicatos '
                   'anunciaron jornadas de protesta escalonada en los SuperCADE de Manitas, Suba y Bosa.',
  'duration_seconds': 300,
  'user_name': 'Dr. Andrés Camargo Varela',
  'user_role': 'Secretario General de la Alcaldía Mayor de Bogotá',
  'user_organization': 'Alcaldía Mayor de Bogotá D.C. — Despacho Liévano',
  'user_objectives': '1. Pactar un reajuste salarial responsable no superior a IPC + 2.0%, blindando el límite '
                     'presupuestal del Marco Fiscal de Mediano Plazo.\n'
                     '2. Establecer un esquema regulado de teletrabajo de máximo 2 días semanales supeditado al '
                     'cumplimiento de ANS en atención ciudadana.\n'
                     '3. Firmar el Acta Final de Acuerdos Laborales 2026 y desactivar el cese en la Red CADE.',
  'avatar_name': 'Hernando Barreto Lozano (Presidente de SINDISTRITALES)',
  'avatar_voice': 'onyx',
  'avatar_profile': 'Abogado laboralista egresado de la Universidad Nacional y presidente de SINDISTRITALES con 24 '
                    'años de carrera administrativa en el Distrito. Ha liderado cuatro negociaciones colectivas con '
                    'tres alcaldes distintos; conoce al milímetro el Estatuto Orgánico de Bogotá (Decreto Ley 1421 de '
                    '1993) y sabe que la administración teme el impacto en medios y redes de filas masivas en los '
                    'SuperCADE.',
  'avatar_tone': 'Firme, reivindicativo, protocolario pero incisivo; maneja cifras macroeconómicas de inflación de '
                 'alimentos y costo de vida en Bogotá.',
  'avatar_rules': '1. No firmar ningún acuerdo salarial por debajo de IPC + 2.3% a menos que incluya auxilios de '
                  'conectividad y bienestar certificados.\n'
                  '2. Exigir garantías expresas de no tercerización en áreas misionales de las Secretarías de '
                  'Movilidad, Salud e Integración Social.\n'
                  '3. Mantener la convocatoria a asamblea permanente en la Plaza de Bolívar si la administración no '
                  'formaliza el teletrabajo con equipos del Distrito.',
  'persona_notes': 'Valora el trato digno, el respeto al fuero sindical y que el Distrito reconozca el esfuerzo de la '
                   'planta operativa antes de entrar al debate de partidas fiscales.',
  'session_turns': [('persona',
                     'Doctor Camargo, buenas tardes. Nuestras bases en los 14 SuperCADEs están cansadas de que '
                     'Hacienda dilate la mesa. El costo de vida en Bogotá no da tregua y nuestro pliego de IPC más '
                     '6.2% compensa el congelamiento de años anteriores. Esperamos una oferta institucional seria hoy '
                     'o mañana las ventanillas distritales amanecerán en asamblea informativa.'),
                    ('user',
                     'Buenas tardes, doctor Barreto. Entiendo la legítima preocupación de los servidores y en nombre '
                     'del Alcalde Mayor reconozco que el funcionamiento de la ciudad depende del compromiso de la '
                     'planta. Sin embargo, tenemos el límite vinculante de la Ley 617 y el Marco Fiscal de Mediano '
                     'Plazo aprobado por el Concejo. Si excedemos el gasto de funcionamiento incurrimos en falta '
                     'gravísima ante la Procuraduría. Nuestra propuesta técnica y responsable es IPC más 1.8% '
                     'garantizado, articulado con un fondo de capacitación universitaria financiado por el DASCD.'),
                    ('persona',
                     'Un 1.8% es inaceptable frente al incremento del transporte en TransMilenio y la canasta familiar '
                     'en la capital. Si la Alcaldía Mayor no sube al menos a IPC más 2.3%, la asamblea general de '
                     'delegados no levantará la orden de movilización.'),
                    ('user',
                     'Doctor Barreto, busquemos una fórmula de equilibrio que beneficie directamente el bolsillo de '
                     'los trabajadores sin romper el techo presupuestal. Propongo acordar IPC más 2.1% en la escala '
                     'salarial, pero adicionamos de inmediato la resolución de teletrabajo de 2 días a la semana con '
                     'entrega del 100% de computadores portátiles institucionales y un auxilio mensual de conectividad '
                     'de 120.000 pesos. Eso representa un alivio directo en pasajes y alimentación sin inflar el '
                     'factor prestacional permanente.'),
                    ('persona',
                     'Esa propuesta sobre la mesa cambia la correlación. La formalización del teletrabajo de 2 días '
                     'con equipos y el auxilio de conectividad sí impacta positivamente el ingreso neto de los '
                     'compañeros. Si dejamos esa redacción blindada en el acta con cronograma de entrega de equipos a '
                     '45 días por la Secretaría General, someto la aprobación del IPC más 2.1% y suspendemos cualquier '
                     'llamado a cese en la Red CADE.')],
  'coaching': {'score': 89,
               'resultado_final': 'acuerdo_exitoso',
               'resumen_ejecutivo': 'Negociación colectiva distrital gestionada con alto estándar técnico y político. '
                                    'El usuario contuvo la presión de movilización respetando la Ley 617, utilizando '
                                    'el teletrabajo y el auxilio de conectividad como moneda de cambio de alto valor '
                                    'percibido para los servidores públicos.',
               'fortalezas': [{'titulo': 'Anclaje en límites normativos vinculantes',
                               'descripcion': 'Explicó las consecuencias disciplinarias de la Ley 617 y el Marco '
                                              'Fiscal sin descalificar la labor sindical.',
                               'cita_usuario': 'tenemos el límite vinculante de la Ley 617 y el Marco Fiscal de '
                                               'Mediano Plazo aprobado por el Concejo. Si excedemos el gasto de '
                                               'funcionamiento incurrimos en falta gravísima'},
                              {'titulo': 'Moneda de cambio no salarial de alto impacto',
                               'descripcion': 'Compensó la brecha del porcentaje salarial con teletrabajo formalizado, '
                                              'dotación de equipos y auxilio de conectividad.',
                               'cita_usuario': 'adicionamos de inmediato la resolución de teletrabajo de 2 días a la '
                                               'semana con entrega del 100% de computadores portátiles institucionales '
                                               'y un auxilio mensual de conectividad'}],
               'areas_de_mejora': [{'titulo': 'Concesión de punto decimal en primera ronda',
                                    'descripcion': 'Subió de 1.8% a 2.1% con rapidez. Pudo haber presentado primero el '
                                                   'paquete de bienestar antes de ceder en el porcentaje base.',
                                    'cita_usuario': 'Propongo acordar IPC más 2.1% en la escala salarial',
                                    'sugerencia_reformulacion': 'Mantengamos el 1.8% garantizado pero sumemos de '
                                                                'inmediato el teletrabajo con auxilio de conectividad; '
                                                                'calculemos juntos el ahorro neto mensual que esto '
                                                                'genera.'}],
               'tacticas_efectivas': ['Reconocimiento protocolario de la contraparte',
                                      'Creación de valor mediante beneficios en especie',
                                      'Alineación con la doctrina del Consejo de Estado y Servicio Civil'],
               'oportunidades_perdidas': ['Establecer compromisos explícitos de reducción del ausentismo laboral'],
               'recomendacion_principal': 'En negociaciones laborales públicas, cuantifica siempre el ahorro en dinero '
                                          'que representan los beneficios no prestacionales antes de ceder puntos en '
                                          'el reajuste básico.'}},
 {'sector': 'Público',
  'title': 'Consulta previa del tramo 4G Buga–Buenaventura en Loboguerrero',
  'scenario_text': 'Mesa formal de Consulta Previa en el polideportivo de Loboguerrero (Dagua, Valle del Cauca). La '
                   'Agencia Nacional de Infraestructura (ANI) y el consorcio concesionario Vía al Mar deben acordar '
                   'las medidas de compensación socioambiental por las obras del viaducto y doble calzada en el '
                   'Corredor Buga–Loboguerrero–Buenaventura, que afecta el caño fluvial y las zonas de pesca artesanal '
                   'del Consejo Comunitario de Comunidades Negras de la Cuenca del Río Dagua. La comunidad mantiene un '
                   'plantón pacífico que tiene paralizada la movilización de maquinaria y volquetas hacia el túnel 3.',
  'duration_seconds': 360,
  'user_name': 'Dra. Elena Restrepo Saldarriaga',
  'user_role': 'Directora de Gestión Social y Consulta Previa',
  'user_organization': 'Agencia Nacional de Infraestructura (ANI) — Ministerio de Transporte',
  'user_objectives': '1. Protocolizar los acuerdos de mitigación ambiental y social ante la Dirección de Consulta '
                     'Previa del Ministerio del Interior.\n'
                     '2. Acordar el despeje inmediato y voluntario del campamento de maquinaria pesada sin recurrir a '
                     'la Unidad de Diálogo y Mantenimiento del Orden (UNDMO).\n'
                     '3. Establecer el Comité de Veeduría Comunitaria con cupos garantizados de mano de obra local no '
                     'calificada del 100%.',
  'avatar_name': 'Faustino Palacios Mosquera (Líder Mayor del Consejo Comunitario del Río Dagua)',
  'avatar_voice': 'onyx',
  'avatar_profile': 'Representante legal del Consejo Comunitario de la Cuenca del Río Dagua, reconocido por el '
                    'Ministerio del Interior. Líder de 58 años, curtido en defensas territoriales de la Ley 70 de 1993 '
                    'y sentencias de la Corte Constitucional (T-080 de 2017). Tiene profunda desconfianza hacia los '
                    'contratistas viales por promesas rotas de concesiones pasadas y exige firmas ministeriales '
                    'vinculantes.',
  'avatar_tone': 'Solemne, pausado, profundamente digno y con autoridad moral ancestral; cita el Convenio 169 de la '
                 'OIT y la Ley 70.',
  'avatar_rules': '1. Si los funcionarios imponen términos técnicos o cronogramas sin escuchar los daños al río, '
                  'levantará la mesa de inmediato.\n'
                  '2. Exigir compensación productiva de emergencia para las 34 familias de pescadores y piangüeras '
                  'afectadas por la sedimentación.\n'
                  '3. No aceptar el desbloqueo sin resolución firmada y fecha perentoria de desembolso ante la '
                  'Defensoría del Pueblo.',
  'persona_notes': 'El respeto al protocolo ancestral y escuchar en silencio la memoria histórica del territorio es '
                   'indispensable para abrir el diálogo.',
  'session_turns': [('persona',
                     'Doctora Restrepo, ustedes vienen de Bogotá con ingenieros y cronogramas de entrega, pero este '
                     'río Dagua es la vida de nuestro pueblo. La concesionaria arrojó escombros sobre el caño San '
                     'Pedro y hoy 34 familias no tienen qué pescar. No vamos a levantar la guardia del campamento '
                     'hasta que el Gobierno Nacional demuestre con hechos que la vida de los negros del Pacífico vale '
                     'más que el concreto.'),
                    ('user',
                     'Don Faustino, antes de hablar de obras, de la ANI o de contratos, quiero mirarlo a los ojos y '
                     'pedirle perdón a usted, a los mayores y a todo el Consejo Comunitario por la negligencia de la '
                     'concesionaria en el caño San Pedro. El arrojo de esos escombros fue una falta inaceptable. Como '
                     'Directora de la ANI, ya abrí el pliego sancionatorio ambiental contra el consorcio y aquí está '
                     'la orden formal de remoción inmediata del material.'),
                    ('persona',
                     'Agradecemos la sinceridad, doctora, pero el hambre de los niños no se quita con pliegos '
                     'sancionatorios. El río está turbio y las redes salen vacías. Necesitamos garantías de sustento '
                     'real hoy mismo.'),
                    ('user',
                     'Tiene toda la razón, don Faustino. Por eso no vengo con promesas vacías, sino con tres '
                     'compromisos respaldados por la fiducia del proyecto: primero, activación inmediata del fondo '
                     'social de emergencia con un subsidio productivo mensual directo para las 34 familias censadas '
                     'por el Consejo Comunitario durante los seis meses que tarde la recuperación del cauce. Segundo, '
                     'el 100% de la mano de obra no calificada de la doble calzada será contratada entre los jóvenes '
                     'de Loboguerrero y Dagua. Y tercero, dos veedores remunerados elegidos por ustedes dentro de la '
                     'interventoría ambiental de la ANI con sede permanente en la obra.'),
                    ('persona',
                     'Si esa acta se suscribe aquí mismo con el visto bueno de la Defensoría del Pueblo y del '
                     'Ministerio del Interior, con primer giro bancario a las familias el viernes de la próxima '
                     'semana, nosotros a las cinco de la tarde levantamos el plantón y garantizamos el paso seguro de '
                     'la maquinaria.')],
  'coaching': {'score': 93,
               'resultado_final': 'acuerdo_exitoso',
               'resumen_ejecutivo': 'Desempeño magistral en resolución de conflictos territoriales bajo el marco del '
                                    'Convenio 169 de la OIT. El reconocimiento honesto del error del contratista y la '
                                    'estructuración de compensaciones productivas con veeduría comunitaria '
                                    'transformaron una crisis vial en un acuerdo legítimo y sostenible.',
               'fortalezas': [{'titulo': 'Validación de la dignidad territorial',
                               'descripcion': 'Asumió la responsabilidad estatal y pidió disculpas por el impacto '
                                              'ambiental, desmontando la desconfianza histórica del líder.',
                               'cita_usuario': 'quiero mirarlo a los ojos y pedirle perdón a usted, a los mayores y a '
                                               'todo el Consejo Comunitario por la negligencia de la concesionaria'},
                              {'titulo': 'Garantías institucionales tangibles',
                               'descripcion': 'Presentó un paquete financiero y laboral cerrado (subsidio directo a 34 '
                                              'familias, 100% empleo local y veeduría remunerada).',
                               'cita_usuario': 'primero, activación inmediata del fondo social de emergencia con un '
                                               'subsidio productivo mensual... Segundo, el 100% de la mano de obra... '
                                               'Y tercero, dos veedores remunerados'}],
               'areas_de_mejora': [{'titulo': 'Precisión en cronograma fiduciario',
                                    'descripcion': 'Aceptó el compromiso de giro para el viernes hábil sin dejar '
                                                   'constancia del trámite de certificación bancaria del Consejo '
                                                   'Comunitario.',
                                    'cita_usuario': 'con tres compromisos respaldados por la fiducia del proyecto',
                                    'sugerencia_reformulacion': 'Firmemos el acta hoy con la Defensoría; programemos '
                                                                'la recepción de certificaciones el lunes para que la '
                                                                'fiducia ordene el desembolso el viernes sin '
                                                                'tropiezos.'}],
               'tacticas_efectivas': ['Desescalamiento mediante asunción de culpas',
                                      'Involucramiento del Ministerio del Interior y Defensoría',
                                      'Empoderamiento de la comunidad en la interventoría'],
               'oportunidades_perdidas': ['Pactar una mesa de seguimiento mensual para prevenir nuevos bloqueos'],
               'recomendacion_principal': 'En consultas previas en Colombia, la legitimidad técnica solo es escuchada '
                                          'cuando primero se ha restaurado la confianza ética y el respeto al '
                                          'territorio ancestral.'}},
 {'sector': 'Público',
  'title': 'Evacuación preventiva y albergues temporales en el PMU de Mocoa',
  'scenario_text': 'Puesto de Mando Unificado (PMU) en la sede de Bomberos de Mocoa (Putumayo). Las lluvias '
                   'torrenciales en la cordillera generaron alertas rojas del IDEAM por aumento súbito del caudal de '
                   'los ríos Mulato y Sangoyaco. La Unidad Nacional para la Gestión del Riesgo de Desastres (UNGRD) y '
                   'la Gobernación deben coordinar la evacuación inmediata de 280 familias del barrio San Miguel hacia '
                   'los alojamientos modulares transitorios en la vereda Los Sauces y coliseo municipal. La comunidad '
                   'se rehúsa a abandonar sus viviendas por temor a perder la posesión de sus predios y al saqueo de '
                   'sus pertenencias.',
  'duration_seconds': 300,
  'user_name': 'Dr. Javier Salamanca Mora',
  'user_role': 'Director Territorial de la UNGRD',
  'user_organization': 'Unidad Nacional para la Gestión del Riesgo de Desastres (UNGRD)',
  'user_objectives': '1. Lograr el traslado voluntario y pacífico de las 280 familias hacia el albergue seguro en las '
                     'próximas 24 horas.\n'
                     '2. Censar a la totalidad de los núcleos familiares en el Registro Único de Damnificados (RUD) '
                     'para el giro de subsidios de arriendo temporal.\n'
                     '3. Ofrecer salvaguarda notarial de derechos sobre los inmuebles y vigilancia policial permanente '
                     'en la zona evacuada.',
  'avatar_name': 'Carmen Zabala Rincón (Presidenta de la JAC Barrio San Miguel)',
  'avatar_voice': 'nova',
  'avatar_profile': 'Líder comunitaria de 61 años, sobreviviente de la avalancha de Mocoa de 2017. Ha visto la '
                    'lentitud de la reconstrucción urbana y desconfía de las promesas de albergues modulares. Defiende '
                    'con vehemencia el patrimonio que reconstruyó con su familia y no está dispuesta a que sus vecinos '
                    'queden atrapados en carpas plásticas indefinidamente.',
  'avatar_tone': 'Angustiada, enérgica, protectora y escéptica; habla con la memoria viva de la tragedia de 2017.',
  'avatar_rules': '1. No permitir la salida del barrio si la Personería Municipal no certifica que no habrá '
                  'declaratoria de expropiación administrativa.\n'
                  '2. Exigir verificación presencial de baterías sanitarias, luz y cocina comunitaria en el albergue '
                  'antes de subir a los camiones.\n'
                  '3. Condicionar la evacuación a la presencia fija de patrullas del Ejército Nacional y Policía en '
                  'las calles del barrio San Miguel.',
  'persona_notes': 'El miedo al despojo y al robo de enseres es el principal obstáculo. Requiere certezas documentales '
                   'y empatía genuina.',
  'session_turns': [('persona',
                     'Doctor Salamanca, la gente en San Miguel no se va a subir a esos camiones de la Defensa Civil. '
                     'En el 2017 nos dijeron que era por tres días y muchas familias terminaron tres años viviendo en '
                     'plásticos en la loma. Además, si dejamos las casas solas, los amigos de lo ajeno se llevan las '
                     'neveras y las herramientas. ¡De aquí no salimos a ciegas!'),
                    ('user',
                     'Doña Carmen, entiendo su indignación y tiene toda la razón en recordar el dolor del 2017. Pero '
                     'como Director de Gestión del Riesgo tengo los sensores del IDEAM en pantalla: el río Sangoyaco '
                     'tiene cota de desbordamiento inminente en 12 horas. Mi prioridad absoluta no es un trámite, es '
                     'que ninguna vida se pierda esta noche. Para su total tranquilidad, la Personera Municipal y el '
                     'Notario Único de Mocoa ya están aquí con nosotros expidiendo un acta con valor legal que '
                     'certifica que esta evacuación es estrictamente preventiva por fuerza mayor y que sus derechos de '
                     'propiedad y posesión quedan blindados al 100%.'),
                    ('persona',
                     'Lo del Notario es un alivio, doctor, pero ¿a dónde nos llevan? Los Sauces la última vez era un '
                     'barrizal sin baños donde los niños se enfermaron de diarrea.'),
                    ('user',
                     'Doña Carmen, el campamento de Los Sauces hoy cuenta con 40 módulos isotérmicos de la Cruz Roja, '
                     'planta de tratamiento de agua potable con carrotanque permanente, 12 baterías sanitarias '
                     'completas y enfermería 24 horas. La invito a que suba ahora mismo a mi camioneta con dos '
                     'delegados de la junta y en 15 minutos lo comprueban con sus propios ojos. Además, el Batallón de '
                     'Infantería Domingo Rico y la Policía ya instalaron tres puntos de control fijo en San Miguel '
                     'para custodiar cada vivienda.'),
                    ('persona',
                     'Si vamos a Los Sauces y veo que el agua potable, la luz y el Ejército están en sus puestos, yo '
                     'misma tomo el megáfono en la iglesia del barrio y encabezo la evacuación ordenada familia por '
                     'familia antes de que caiga la noche.')],
  'coaching': {'score': 91,
               'resultado_final': 'acuerdo_exitoso',
               'resumen_ejecutivo': 'Gestión impecable de evacuación en emergencia humanitaria bajo la Ley 1523 de '
                                    '2012. Neutralizó los dos mayores temores comunitarios (pérdida patrimonial y '
                                    'condiciones precarias del albergue) combinando blindaje notarial e inspección '
                                    'presencial inmediata.',
               'fortalezas': [{'titulo': 'Urgencia vital con respaldo científico',
                               'descripcion': 'Utilizó las alertas técnicas del IDEAM para contextualizar el peligro '
                                              'inminente sin sonar alarmista ni despectivo.',
                               'cita_usuario': 'el río Sangoyaco tiene cota de desbordamiento inminente en 12 horas. '
                                               'Mi prioridad absoluta no es un trámite, es que ninguna vida se pierda '
                                               'esta noche'},
                              {'titulo': "Principio de verificación directa 'in situ'",
                               'descripcion': 'Invitó a la líder a constatar personalmente las condiciones del '
                                              'albergue modular antes de pedir la movilización de la comunidad.',
                               'cita_usuario': 'La invito a que suba ahora mismo a mi camioneta con dos delegados de '
                                               'la junta y en 15 minutos lo comprueban con sus propios ojos'}],
               'areas_de_mejora': [{'titulo': 'Aclaración sobre subsidios de arriendo temporal',
                                    'descripcion': 'No especificó el valor ni el procedimiento para el cobro del '
                                                   'subsidio monetario de arriendo de la UNGRD para quienes no deseen '
                                                   'ir al albergue.',
                                    'cita_usuario': 'el campamento de Los Sauces hoy cuenta con 40 módulos isotérmicos',
                                    'sugerencia_reformulacion': 'Quienes prefieran hospedarse donde familiares '
                                                                'recibirán de inmediato el subsidio de arriendo '
                                                                'temporal de 500.000 pesos mensuales mediante el '
                                                                'Registro Único de Damnificados.'}],
               'tacticas_efectivas': ['Blindaje con Personería y Notaría',
                                      'Cuidado de bienes con presencia de fuerza pública',
                                      'Liderazgo compartido con la JAC'],
               'oportunidades_perdidas': ['Definir el punto de encuentro de mascotas y animales domésticos'],
               'recomendacion_principal': 'En gestión de desastres, permitir que el liderazgo comunitario audite las '
                                          'instalaciones de acogida en persona destraba la evacuación más rápido que '
                                          'cualquier decreto de policía.'}},
 {'sector': 'Público',
  'title': 'Recuperación de la Carrera Séptima y formalización comercial con el IPES',
  'scenario_text': 'Auditorio de la Secretaría Distrital de Gobierno (Edificio Bicentenario, Carrera 8 con Calle 10, '
                   'Bogotá D.C.). El Tribunal Administrativo de Cundinamarca ordenó el cumplimiento perentorio de la '
                   'Sentencia de Acción Popular para la restitución del espacio público en el Corredor Peatonal de la '
                   'Carrera Séptima (entre Calles 11 y 26), ocupado por más de 190 puestos de comercio informal. El '
                   'Instituto para la Economía Social (IPES) y la Alcaldía Local de Santa Fe deben acatar el fallo '
                   'judicial garantizando el principio constitucional de confianza legítima y mínimo vital (Sentencia '
                   'SU-360/22). El gremio de vendedores amenaza con encadenarse en la Plaza de Bolívar.',
  'duration_seconds': 300,
  'user_name': 'Dra. Marcela Buendía Forero',
  'user_role': 'Subsecretaria de Gobernabilidad y Espacio Público',
  'user_organization': 'Secretaría Distrital de Gobierno — Alcaldía Mayor de Bogotá',
  'user_objectives': '1. Cumplir la orden del Tribunal Administrativo liberando el corredor peatonal de la Séptima de '
                     'forma concertada y sin disturbios.\n'
                     '2. Vincular a los 190 vendedores censados en la oferta formal del IPES (Pasajes Comerciales San '
                     'Victorino, Plaza España y ferias de emprendimiento).\n'
                     '3. Suscribir el Pacto Distrital de Convivencia y No Retorno con capital semilla y microcréditos '
                     'condonables.',
  'avatar_name': 'Wilson Quintero Téllez (Presidente de ASOVENSEPTIMA)',
  'avatar_voice': 'onyx',
  'avatar_profile': 'Comerciante informal con 16 años vendiendo artesanías y marroquinería en la Séptima entre Calles '
                    '19 y 22. Vocero de la Asociación de Vendedores de la Carrera Séptima (ASOVENSEPTIMA). Conoce a '
                    'profundidad las sentencias de la Corte Constitucional sobre el derecho al trabajo; desconfía de '
                    'las plazas cerradas del IPES alegando que el comprador bogotano camina por la acera y no entra a '
                    'sótanos.',
  'avatar_tone': 'Perspicaz, elocuente, defensivo pero con apertura comercial si le garantizan tráfico de compradores.',
  'avatar_rules': '1. Rechazar cualquier traslado si los locales del IPES exigen cobro de administración o '
                  'arrendamiento durante el primer semestre.\n'
                  '2. Exigir campañas de publicidad distrital en medios masivos y ferias de activación comercial '
                  'organizadas por la Secretaría de Desarrollo Económico.\n'
                  '3. Exigir que los apoyos económicos de capital semilla se entreguen antes de desmontar las casetas '
                  'de la calle.',
  'persona_notes': 'Su principal angustia es la quiebra comercial. Requiere comprobar que la reubicación traerá '
                   'clientes y liquidez inmediata.',
  'session_turns': [('persona',
                     'Doctora Marcela, esa orden del Tribunal no puede pisotear el derecho fundamental al mínimo vital '
                     'de 190 familias que llevamos dos décadas en la Séptima. A los compañeros que mandaron a los '
                     'locales del Pasaje Bolívar hace unos años se les pudrió la mercancía porque la gente no baja a '
                     'esos pasajes. Si la Policía llega a quitarnos las carretas con la UNDMO, nos encadenamos en la '
                     'puerta de la Catedral Primada.'),
                    ('user',
                     'Wilson, comparto plenamente que una reubicación que quiebre a los comerciantes no es una '
                     'política pública seria. La Alcaldía Mayor respeta la Sentencia SU-360 de la Corte Constitucional '
                     'sobre confianza legítima. Por eso la oferta que traemos hoy desde la Secretaría de Gobierno y el '
                     'IPES está diseñada para garantizar ventas reales: primero, canon cero de arrendamiento y '
                     'servicios comunes durante ocho meses en el Pasaje Comercial San Victorino y Plaza España. '
                     'Segundo, un capital semilla no reembolsable de tres millones de pesos por comerciante a través '
                     "del programa 'Bogotá Produce' para surtido. Y tercero, el desvío de dos paraderos de "
                     'TransMilenio SITP justo al frente de los accesos principales.'),
                    ('persona',
                     'Ocho meses sin canon y los tres millones para inventario ayudan bastante, doctora. Pero el '
                     'problema histórico sigue siendo el flujo de peatones. Si la gente no entra al pasaje, no '
                     'comemos.'),
                    ('user',
                     'Para resolver de raíz el flujo peatonal, la Secretaría de Desarrollo Económico destinó 200 '
                     'millones de pesos en una campaña de reapertura comercial con pauta en Canal Capital, emisoras y '
                     'señalización vial en el Eje Ambiental y la Séptima. Además, organizaremos cuatro ferias '
                     'temáticas mensuales los fines de semana en la plazoleta externa. El traslado lo haremos de forma '
                     'acompañada, con camiones del Distrito gratuitos para llevar su mercancía sin que gasten un solo '
                     'peso.'),
                    ('persona',
                     'Si esos ocho meses de gracia, el capital semilla previo y el transporte de mercancía quedan '
                     'firmados en el acta con presencia de la Personería de Bogotá, en la asamblea de esta noche '
                     'apruebo el cronograma y el miércoles a primera hora entregamos el corredor de la Séptima '
                     'despejado y nos mudamos a los locales.')],
  'coaching': {'score': 90,
               'resultado_final': 'acuerdo_exitoso',
               'resumen_ejecutivo': 'Excelente negociación urbana fundamentada en jurisprudencia de la Corte '
                                    'Constitucional. Se desactivó una confrontación social inminente ofreciendo una '
                                    'solución de formalización comercial robusta que atacó el miedo central a la caída '
                                    'de ventas.',
               'fortalezas': [{'titulo': 'Alineación con doctrina constitucional',
                               'descripcion': 'Validó la confianza legítima y el mínimo vital, situándose del lado de '
                                              'la solución socioeconómica y no de la represión policiva.',
                               'cita_usuario': 'La Alcaldía Mayor respeta la Sentencia SU-360 de la Corte '
                                               'Constitucional sobre confianza legítima'},
                              {'titulo': 'Estrategia integral de demanda comercial',
                               'descripcion': 'Combinó exención de costos fijos (8 meses de canon cero), capital de '
                                              'trabajo (3 millones) y atracción de tráfico (campaña distrital y '
                                              'paraderos SITP).',
                               'cita_usuario': 'canon cero de arrendamiento... capital semilla no reembolsable... '
                                               'pauta en Canal Capital y señalización en el Eje Ambiental'}],
               'areas_de_mejora': [{'titulo': 'Cláusulas de control de reventa de locales',
                                    'descripcion': 'Omitió incluir la prohibición expresa de traspaso o subarriendo '
                                                   'del local adjudicado a terceros informales.',
                                    'cita_usuario': 'el miércoles a primera hora entregamos el corredor de la Séptima',
                                    'sugerencia_reformulacion': 'Dejemos estipulado en el pacto que el beneficio del '
                                                                'local e incentivos se pierde de manera definitiva si '
                                                                'el titular reincide en la invasión del espacio '
                                                                'público.'}],
               'tacticas_efectivas': ['Creación de demanda inducida para comercio formal',
                                      'Incentivos económicos previos al desmonte',
                                      'Apoyo logístico de mudanza gratuito'],
               'oportunidades_perdidas': ['Establecer un censo biométrico cerrado para evitar la llegada de nuevos '
                                          'vendedores a la zona liberada'],
               'recomendacion_principal': 'En la recuperación de espacio público en Colombia, la viabilidad comercial '
                                          'del sitio de acogida es la única garantía de no retorno al andén.'}},
 {'sector': 'Público',
  'title': 'Mesa contradictoria de control fiscal en la Contraloría General de la República',
  'scenario_text': 'Sala de Audiencias de la Contraloría Delegada para el Sector Salud (Edificio Gran Estación II, '
                   'Avenida Calle 26, Bogotá D.C.). En el marco de la Auditoría Financiera y de Gestión a la ESE '
                   'Hospital Universitario de La Samaritana, la comisión auditora notificó un hallazgo administrativo '
                   'con presunto alcance fiscal por $580 millones de pesos, derivado de supuestos sobrecostos en la '
                   'contratación de urgencia de reactivos de inmunoanálisis y tomografía contrastada para UCI. El '
                   'Gerente del Hospital y su equipo jurídico deben presentar descargos técnicos y justificar la '
                   'razonabilidad de precios frente a tablas del SICEP y SECOP II antes del cierre del informe '
                   'definitivo de auditoría.',
  'duration_seconds': 360,
  'user_name': 'Dr. Fernando Jaramillo Echeverry',
  'user_role': 'Gerente General',
  'user_organization': 'ESE Hospital Universitario de La Samaritana (Tercer Nivel de Complejidad)',
  'user_objectives': '1. Demostrar la trazabilidad técnica y financiera del contrato mediante el anexo de comodato '
                     'tecnológico y guardia biomédica 24/7.\n'
                     '2. Desvirtuar la configuración del alcance fiscal antes de su remisión a la Sala Fiscal '
                     'Sancionatoria de la Contraloría.\n'
                     '3. Acordar la reclasificación del hallazgo a oportunidad de mejora con suscripción de Plan de '
                     'Mejoramiento Institucional.',
  'avatar_name': 'Miriam Osorio Cárdenas (Auditora Fiscal Senior de la Contraloría General)',
  'avatar_voice': 'nova',
  'avatar_profile': 'Contadora pública con maestría en Auditoría Forense y 19 años de trayectoria en la Contraloría '
                    'General de la República. Experta en la Ley 610 de 2000, Ley 1474 de 2011 (Estatuto '
                    'Anticorrupción) y contratación pública hospitalaria. Metódica, incorruptible e implacable frente '
                    'a variaciones de precios; evalúa estrictamente contra precios históricos del SICEP, circulares de '
                    'la Comisión Nacional de Precios de Medicamentos y registros de SECOP II.',
  'avatar_tone': 'Técnico, inquisitivo, solemne y rigurosamente apegado a la evidencia documental y normativa.',
  'avatar_rules': '1. Rechazar argumentos discursivos o testimoniales que no estén sustentados en folios del '
                  'expediente contractual foliado.\n'
                  '2. Reclasificar el hallazgo fiscal únicamente si se demuestra que el valor unitario incluía '
                  'servicios adicionales no desagregados que compensan la diferencia tarifaria.\n'
                  '3. Mantener el alcance fiscal si el contrato no acreditó disponibilidad presupuestal previa o '
                  'estudio de mercado contemporáneo.',
  'persona_notes': 'Solo modifica su postura ante matrices comparativas de costeo, análisis de ciclo de vida de '
                   'tecnología y certificados de calibración hospitalaria.',
  'session_turns': [('persona',
                     'Doctor Jaramillo, la muestra de auditoría es categórica. Su hospital adjudicó el contrato de '
                     'reactivos automatizados con una tarifa unitaria 34% superior a la mediana del mercado registrada '
                     'en el SICEP y en el SECOP II para la red hospitalaria de Cundinamarca en ese semestre. Esto '
                     'representa un presunto detrimento patrimonial al Estado de 580 millones de pesos. Si no hay un '
                     'sustento técnico documentado, este hallazgo será remitido con alcance fiscal y disciplinario en '
                     'el informe final.'),
                    ('user',
                     'Doctora Osorio, comprendo y valoro el rigor del órgano de control en la vigilancia de los '
                     'recursos de la salud. Permítame poner sobre la mesa el anexo técnico número cuatro y el folio '
                     '185 del expediente precontractual, que no fueron cotejados en el cálculo plano del SICEP. El '
                     'precio unitario contratado no correspondía a reactivos sueltos en estantería; incluía el '
                     'comodato gratuito de dos analizadores de última generación valorados en 720 millones de pesos, '
                     'mantenimiento correctivo 24/7 con tiempo de respuesta inferior a dos horas, y la calibración '
                     'diaria requerida para pacientes críticos de oncología y UCI neonatal.'),
                    ('persona',
                     'El comodato tecnológico y el mantenimiento explican una porción del costo, doctor, pero la '
                     'Circular 010 de la Comisión de Precios exige que el estudio de conveniencia demuestre que el '
                     'esquema integrado era financieramente más ventajoso que la compra del equipo y reactivo por '
                     'separado. ¿Tienen el análisis de costo-beneficio previo al proceso licitatorio?'),
                    ('user',
                     'Exactamente en el folio 192 obra el dictamen de ingeniería biomédica y la corrida financiera: '
                     'comprar los dos analizadores, pagar pólizas y contratar la cuadrilla técnica externa le costaba '
                     'a La Samaritana 890 millones de pesos al año. Con el modelo integrado en comodato contratado, el '
                     'costo total anual fue de 580 millones. Es decir, generamos una eficiencia y ahorro neto '
                     'certificado de 310 millones de pesos para la entidad pública, garantizando cero cancelaciones de '
                     'cirugías de alta complejidad.'),
                    ('persona',
                     'Revisando el folio 192 y la trazabilidad financiera del anexo cuatro, queda plenamente '
                     'acreditado que el valor por prueba incorporaba la amortización tecnológica del equipo y la '
                     'disponibilidad de guardia biomédica. El presunto detrimento patrimonial queda desvirtuado '
                     'técnicamente. En consecuencia, reclasificaremos la observación a hallazgo administrativo con '
                     'recomendación en el Plan de Mejoramiento para que en futuros procesos se discrimine la tarifa de '
                     'reactivo frente al servicio tecnológico agregado.')],
  'coaching': {'score': 95,
               'resultado_final': 'acuerdo_exitoso',
               'resumen_ejecutivo': 'Defensa técnico-jurídica sobresaliente en mesa contradictoria de control fiscal. '
                                    'El usuario no recurrió a justificaciones subjetivas, sino que presentó la '
                                    'evidencia documental foliada y la matriz costo-beneficio requerida por la Ley '
                                    '610, logrando la desvirtuación total del alcance fiscal y preservando la '
                                    'reputación institucional del hospital.',
               'fortalezas': [{'titulo': 'Manejo probatorio de precisión',
                               'descripcion': 'Citó folios contractuales exactos y anexos técnicos de ingeniería '
                                              'biomédica contemporáneos a la contratación.',
                               'cita_usuario': 'folio 185 del expediente precontractual... Exactamente en el folio 192 '
                                               'obra el dictamen de ingeniería biomédica y la corrida financiera'},
                              {'titulo': 'Inversión matemática de la carga fiscal',
                               'descripcion': 'Demostró con cifras comparativas que el esquema generó un ahorro '
                                              'público neto de 310 millones frente al modelo tradicional.',
                               'cita_usuario': 'comprar los dos analizadores... costaba 890 millones... Con el modelo '
                                               'integrado... costó 580 millones. Generamos un ahorro neto de 310 '
                                               'millones'}],
               'areas_de_mejora': [{'titulo': 'Compromiso proactivo con la transparencia presupuestal',
                                    'descripcion': 'Pudo haber ofrecido voluntariamente la adopción de un manual de '
                                                   'desglose tarifario para las próximas vigencias.',
                                    'cita_usuario': 'generamos una eficiencia y ahorro neto certificado',
                                    'sugerencia_reformulacion': 'Aceptamos la recomendación de la Contraloría y nos '
                                                                'comprometemos a implementar desde el próximo mes la '
                                                                'desagregación de costos en los pliegos del SECOP '
                                                                'II.'}],
               'tacticas_efectivas': ['Sustentación con matrices de ingeniería biomédica',
                                      'Respeto irrestricto al rol del auditor fiscal',
                                      'Alineación con la Ley 610 de 2000 y normas de la CGR'],
               'oportunidades_perdidas': ['Incluir la certificación de satisfacción del servicio emitida por los jefes '
                                          'de UCI'],
               'recomendacion_principal': 'En audiencias de control fiscal en Colombia, un cuadro comparativo de '
                                          'costo-beneficio debidamente foliado en la etapa precontractual desactiva '
                                          'cualquier hallazgo de sobrecosto.'}},
 {'sector': 'Privado',
  'title': 'Renegociación de contrato de suministro por sobrecostos',
  'scenario_text': 'Negociación contractual entre Alimentos NutriGlobal y su proveedor crítico de resinas y empaques '
                   'PolyTech. El proveedor notificó un incremento unilateral del 22% con vigencia en 15 días, '
                   'argumentando la subida del flete marítimo y precios de resinas, o de lo contrario suspenderá los '
                   'despachos, paralizando la línea de producción principal.',
  'duration_seconds': 300,
  'user_name': 'Juan Pablo Echeverri',
  'user_role': 'Director de Abastecimiento Estratégico',
  'user_organization': 'Alimentos NutriGlobal S.A.',
  'user_objectives': '1. Limitar el incremento de precios a un máximo del 9.5% indexado a índices verificables.\n'
                     '2. Extender el plazo contractual a 2 años a cambio de exclusividad en dos plantas nuevas.\n'
                     '3. Garantizar continuidad inmediata de despachos sin penalidades de inventario mínimo.',
  'avatar_name': 'Marcus Vance (Director Comercial Regional de PolyTech)',
  'avatar_voice': 'echo',
  'avatar_profile': 'Ejecutivo comercial multinacional radicado en São Paulo. Maneja cuentas corporativas de gran '
                    'volumen. Sabe que homologar un nuevo proveedor le tomaría a NutriGlobal al menos cuatro meses de '
                    'pruebas sanitarias.',
  'avatar_tone': 'Asertivo, corporativo, amable en el trato pero implacable con las metas de margen de su matriz.',
  'avatar_rules': '1. No aceptar ajustes menores al 16% sin un compromiso vinculante de volumen ampliado.\n'
                  '2. Recordar cortésmente las demoras de homologación técnica si el cliente amenaza con cancelar.\n'
                  '3. Ceder a tarifas escalonadas solo si el plazo de pago se reduce de 90 a 30 días.',
  'persona_notes': 'Sensible al volumen agregado a largo plazo y a la reducción de días de cartera.',
  'session_turns': [('persona',
                     'Juan Pablo, gusto en saludarte. Entiendo la sorpresa por el ajuste del 22%, pero el índice '
                     'internacional ICIS de polímeros subió un 35% y los fletes de Asia se triplicaron. PolyTech no '
                     'puede seguir subsidiando el margen de NutriGlobal. Si no tenemos la adenda firmada este viernes, '
                     'los despachos de noviembre tendrán que ser pausados.'),
                    ('user',
                     'Marcus, agradezco la franqueza. Sin embargo, un incremento del 22% de la noche a la mañana está '
                     'fuera de cualquier parámetro comercial y destruye la rentabilidad de nuestra categoría. Si nos '
                     'obligas a trasladar eso al consumidor, nuestras ventas caerán y tus pedidos también. En lugar de '
                     'una ruptura, te propongo una solución estructural de ganar-ganar: aceptamos un incremento '
                     'inmediato del 9% indexado trimestralmente al índice ICIS, reducimos los términos de pago de 90 a '
                     '35 días para aliviar tu flujo de caja, y te otorgamos la exclusividad del suministro de nuestras '
                     'dos nuevas plantas de exportación por los próximos 24 meses.'),
                    ('persona',
                     'El pronto pago a 35 días y las dos nuevas plantas son atractivos en volumen, Juan Pablo. Pero un '
                     '9% sigue dejándome en pérdida operativa el primer trimestre con los fletes actuales. Necesito al '
                     'menos un 14% para equilibrar.'),
                    ('user',
                     'Hagamos lo siguiente, Marcus: cerremos en 10.5% fijo para este trimestre. Si en enero el índice '
                     'de fletes de Shanghái sigue por encima de los 4,500 dólares, aplicamos una sobretasa logística '
                     'temporal del 3% que se extingue automáticamente cuando el flete baje. A cambio, hoy mismo '
                     'firmamos el contrato extendido a 24 meses que garantiza un 40% más de volumen total para '
                     'PolyTech.'),
                    ('persona',
                     'Esa sobretasa flotante condicionada al flete marítimo protege nuestro margen de contingencia y '
                     'la exclusividad por dos años compensa con creces el volumen. Tenemos un acuerdo, Juan Pablo. '
                     'Envío la adenda con esos términos hoy mismo.')],
  'coaching': {'score': 91,
               'resultado_final': 'acuerdo_exitoso',
               'resumen_ejecutivo': 'Magistral aplicación de negociación integrativa basada en intereses. El usuario '
                                    'evitó la trampa posicional del porcentaje fijo, introduciendo términos de pago '
                                    'más rápidos, volumen futuro y una cláusula indexada flotante que satisfizo los '
                                    'requisitos de rentabilidad del proveedor.',
               'fortalezas': [{'titulo': 'Moneda de cambio de alto valor financiero',
                               'descripcion': 'Ofreció reducir los días de cartera de 90 a 35 días, impactando '
                                              'positivamente el capital de trabajo de la contraparte.',
                               'cita_usuario': 'reducimos los términos de pago de 90 a 35 días para aliviar tu flujo '
                                               'de caja'},
                              {'titulo': 'Diseño de tarifa flotante indexada',
                               'descripcion': 'Creó un mecanismo de sobretasa temporal ligada a indicadores externos '
                                              'objetivos (fletes) que se apaga automáticamente.',
                               'cita_usuario': 'aplicamos una sobretasa logística temporal del 3% que se extingue '
                                               'automáticamente cuando el flete baje.'}],
               'areas_de_mejora': [{'titulo': 'Falta de penalidad por retrasos de entrega',
                                    'descripcion': 'Aceptó la sobretasa sin exigir a cambio un compromiso formal de '
                                                   'SLA de entrega a tiempo bajo sanción económica.',
                                    'cita_usuario': 'cerremos en 10.5% fijo para este trimestre',
                                    'sugerencia_reformulacion': 'Aceptamos la sobretasa flotante a condición de que '
                                                                'PolyTech asuma una penalidad del 2% por cada día de '
                                                                'retraso en planta.'}],
               'tacticas_efectivas': ['Uso de estándares objetivos (Índice ICIS)',
                                      'Compromiso de volumen agregado a cambio de precio',
                                      'Indexación temporal de contingencias'],
               'oportunidades_perdidas': ['Exigir auditoría de costos de importación de la resina'],
               'recomendacion_principal': 'Cuando un proveedor argumenta sobrecostos externos, la mejor respuesta es '
                                          'indexar el precio a esos indicadores para que el sobrecosto se extinga '
                                          'cuando el mercado se normalice.'}},
 {'sector': 'Privado',
  'title': 'Desvinculación negociada de Vicepresidente de Operaciones',
  'scenario_text': 'Reunión ejecutiva a puerta cerrada. El Vicepresidente de Operaciones de una firma de logística '
                   'digital lleva 7 años en la empresa, pero tras desacuerdos irreconciliables con el nuevo CEO y '
                   'metas incumplidas, el Directorio decidió su salida. Se debe negociar su renuncia concertada, '
                   'paquete de salida y acuerdo de confidencialidad, evitando litigios o filtraciones.',
  'duration_seconds': 300,
  'user_name': 'Claudia Montes',
  'user_role': 'Chief Human Resources Officer (CHRO)',
  'user_organization': 'FinCorp Logística Latam',
  'user_objectives': '1. Obtener la renuncia voluntaria concertada con paz y salvo laboral total.\n'
                     '2. Acordar una compensación máxima equivalente a 7 meses de salario más cobertura de salud y '
                     'outplacement.\n'
                     '3. Suscribir cláusula de no competencia y no denigración por 18 meses para blindar la reputación '
                     'de la firma.',
  'avatar_name': 'Roberto Silva (Vicepresidente de Operaciones Saliente)',
  'avatar_voice': 'onyx',
  'avatar_profile': 'Ingeniero industrial, co-creador del modelo operativo de la empresa. Siente que el nuevo CEO lo '
                    'desplazó injustamente. Está respaldado por abogados laboralistas y conoce secretos comerciales e '
                    'información de gobernanza sensible.',
  'avatar_tone': 'Orgulloso, herido pero contenido, con respuestas filosas y sensibilidad extrema hacia su imagen '
                 'pública.',
  'avatar_rules': '1. Exigir 18 meses de indemnización y aceleración inmediata de stock options no vesteadas.\n'
                  "2. Rechazar cualquier insinuación de 'bajo rendimiento' o descalificación profesional.\n"
                  '3. Ceder en el monto económico solo si la empresa le permite controlar el comunicado oficial y '
                  'ofrece carta de recomendación de la junta.',
  'persona_notes': 'El ego, el reconocimiento a su legado y el control de la narrativa pública son más decisivos que '
                   'el dinero puro.',
  'session_turns': [('persona',
                     'Claudia, no nos engañemos con rodeos corporativos. Sé perfectamente que el nuevo CEO quiere a su '
                     'propia gente y le incomoda que yo conozca los números reales de la operación. Construí esta '
                     'compañía durante siete años. Si pretenden sacarme con la liquidación básica de ley, mis abogados '
                     'ya tienen lista la demanda laboral y una solicitud de auditoría externa.'),
                    ('user',
                     'Roberto, precisamente porque conocemos tu trayectoria y el valor inmenso de lo que construiste '
                     'en estos siete años, estamos sentados tú y yo a puerta cerrada. Nadie en esta junta directiva '
                     'desconoce tu legado. Pero también sabes que la visión estratégica hoy va por otro camino y '
                     'desgastarnos en una disputa legal solo destruiría el valor de la empresa que tú mismo fundaste y '
                     'mancharía tu reputación en el mercado. Queremos que salgas por la puerta grande.'),
                    ('persona',
                     'Salir por la puerta grande cuesta, Claudia. Mis stock options no consolidadas representan cuatro '
                     'años de sacrificio, y mis honorarios de asesoría valen. No firmo nada por menos de un año y '
                     'medio de compensación.'),
                    ('user',
                     'Hablemos de lo que de verdad te garantiza un futuro brillante. Te ofrezco un paquete integral: '
                     'siete meses de compensación económica directa, el mantenimiento de tu cobertura médica familiar '
                     'por un año completo, un servicio de outplacement de primer nivel para tu próxima posición en '
                     'juntas directivas, y lo más importante: tú redactas el comunicado oficial de salida indicando '
                     'que emprendes nuevos proyectos personales, respaldado por una carta de reconocimiento firmada '
                     'por los miembros fundadores de la junta.'),
                    ('persona',
                     'Poder redactar el comunicado conjunto y la carta de recomendación de la junta es indispensable '
                     'para mi perfil. Si subes la compensación a nueve meses y me aceleras el 50% de las opciones que '
                     'estaban por vencer este año, firmo el mutuo acuerdo y el pacto de confidencialidad y no '
                     'competencia por 18 meses hoy mismo.')],
  'coaching': {'score': 87,
               'resultado_final': 'acuerdo_parcial',
               'resumen_ejecutivo': 'Manejo maduro y diplomático de una desvinculación ejecutiva de alto riesgo. El '
                                    'usuario identificó correctamente que el motor de la negociación no era únicamente '
                                    'monetario, sino la protección del prestigio y el relato de salida del '
                                    'profesional.',
               'fortalezas': [{'titulo': 'Preservación de la dignidad del ejecutivo',
                               'descripcion': 'Validó el legado de siete años del directivo antes de discutir los '
                                              'términos de separación.',
                               'cita_usuario': 'Nadie en esta junta directiva desconoce tu legado... Queremos que '
                                               'salgas por la puerta grande.'},
                              {'titulo': 'Moneda de cambio reputacional',
                               'descripcion': 'Ofreció el control de la narrativa pública y la carta de respaldo de '
                                              'los fundadores como parte nuclear del paquete.',
                               'cita_usuario': 'tú redactas el comunicado oficial de salida indicando que emprendes '
                                               'nuevos proyectos personales'}],
               'areas_de_mejora': [{'titulo': 'Cierre de términos financieros en stock options',
                                    'descripcion': 'Dejó en el aire la contrapropuesta de aceleración del 50% de las '
                                                   'opciones sin verificar la aprobación del comité de compensación.',
                                    'cita_usuario': 'Hablemos de lo que de verdad te garantiza un futuro brillante',
                                    'sugerencia_reformulacion': 'Puedo avalar los nueve meses de salida hoy, pero la '
                                                                'aceleración de opciones requiere consulta inmediata '
                                                                'con el comité en receso de 15 minutos.'}],
               'tacticas_efectivas': ['Apelación al costo de oportunidad y prestigio profesional',
                                      'Cesión del control del comunicado',
                                      'Outplacement directivo como valor añadido'],
               'oportunidades_perdidas': ['Vincular parte de la indemnización al cumplimiento estricto del periodo de '
                                          'no competencia'],
               'recomendacion_principal': 'En salidas de nivel C-Suite, permitir que el ejecutivo diseñe la narrativa '
                                          'de su partida ahorra millones en indemnizaciones forzadas.'}},
 {'sector': 'Privado',
  'title': 'Gestión de crisis con cliente bancario por caída de servicio',
  'scenario_text': 'Reunión de urgencia con el CIO de un banco comercial de primera línea. La plataforma SaaS de '
                   'autenticación y transferencias sufrió una caída crítica de 7 horas en plena jornada de pago de '
                   'nómina, afectando a 1.2 millones de usuarios. El banco exige una indemnización de $350,000 USD y '
                   'amenaza con rescindir unilateralmente el contrato maestro por incumplimiento de SLA.',
  'duration_seconds': 360,
  'user_name': 'Alejandro Forero',
  'user_role': 'VP of Customer Success y Co-Fundador',
  'user_organization': 'PaySecure Cloud Solutions',
  'user_objectives': '1. Evitar la rescisión del contrato maestro y neutralizar el inicio de acciones judiciales '
                     'inmediatas.\n'
                     '2. Negociar la compensación mediante créditos de servicio de nube y desarrollo a la medida en '
                     'lugar de efectivo.\n'
                     '3. Acordar un plan de remediación técnica conjunta con auditoría de infraestructura en 15 días.',
  'avatar_name': 'Valeria Domínguez (CIO Banco Sudamericano)',
  'avatar_voice': 'nova',
  'avatar_profile': 'Chief Information Officer del banco. Tuvo que rendir cuentas al comité de riesgos y a la '
                    'Superintendencia Financiera. Su credibilidad interna está bajo fuego y necesita demostrar firmeza '
                    'implacable frente al proveedor tecnológico.',
  'avatar_tone': 'Fría, contundente, acusatoria, sin espacio para justificaciones ni disculpas vacías.',
  'avatar_rules': '1. Cortar de raíz cualquier intento de culpar a proveedores de nube (AWS/Azure).\n'
                  '2. Exigir la deducción directa de la penalidad en la facturación mensual.\n'
                  '3. Aceptar no rescindir únicamente si se ofrece soporte dedicado en sitio y SLA blindado con '
                  'penalidades reforzadas.',
  'persona_notes': 'Exige asunción total de responsabilidad y compromisos de redundancia operativa medibles.',
  'session_turns': [('persona',
                     'Alejandro, no me haga perder el tiempo con disculpas corporativas preparadas por su departamento '
                     'legal. Tuvimos a un millón doscientos mil usuarios bloqueados sin poder retirar su nómina '
                     'durante siete horas. El presidente del banco y la Superintendencia me pidieron explicaciones. El '
                     'SLA del 99.9% fue pulverizado. Nuestro departamento legal tiene lista la demanda de rescisión y '
                     'la exigencia de la cláusula penal por 350 mil dólares.'),
                    ('user',
                     'Ingeniera Valeria, asumo la total y absoluta responsabilidad a nombre de los fundadores y del '
                     'equipo de PaySecure. Lo ocurrido ayer fue inaceptable y no vengo a justificarme ni a culpar a '
                     'nuestros proveedores de nube. Si el banco decide rescindir, está en su derecho contractual. Pero '
                     'antes de tomar esa decisión, quiero mostrarle lo que ya ejecutamos: identificamos el cuello de '
                     'botella en la base de datos distribuida, desplegamos un parche de aislamiento de réplicas a las '
                     '3:00 a.m. y pusimos en marcha una reingeniería de arquitectura con failover multirregional '
                     'automático.'),
                    ('persona',
                     'El parche debió estar listo antes de la caída, no después. El daño reputacional del banco no se '
                     'borra con un despliegue de madrugada. ¿Cómo responde PaySecure por las pérdidas financieras de '
                     'la entidad?'),
                    ('user',
                     'Le propongo una restitución que genera valor real para el banco: primero, aplicamos el 100% de '
                     'la penalidad de SLA legalmente pactada en la próxima factura por 120 mil dólares. Segundo, '
                     'entregamos 150 mil dólares en créditos de desarrollo para la nueva integración biométrica que el '
                     'banco tenía presupuestada para el próximo año. Tercero, asignamos a un arquitecto de '
                     'confiabilidad (SRE) senior dedicado en sitio en las oficinas del banco durante los próximos seis '
                     'meses. Y cuarto, financiamos una auditoría de ciberseguridad independiente con la firma que '
                     'ustedes elijan para certificar la nueva infraestructura.'),
                    ('persona',
                     'El arquitecto en sitio y la auditoría externa financiada por ustedes son indispensables para mi '
                     'reporte a la Superintendencia. Si además de los créditos de desarrollo nos garantizan tres meses '
                     'de servicio base sin cobro y duplicamos la penalidad en caso de reincidencia este semestre, '
                     'congelo la orden de rescisión y aprobamos el plan de remediación técnica.')],
  'coaching': {'score': 89,
               'resultado_final': 'acuerdo_exitoso',
               'resumen_ejecutivo': 'Manejo ejemplar de crisis técnica crítica. El usuario no cayó en la tentación de '
                                    'eludir culpas ni desviar la responsabilidad a terceros, lo que desarmó la furia '
                                    'de la contraparte y permitió migrar de un escenario punitivo de demanda judicial '
                                    'a un plan de fortalecimiento técnico conjunto.',
               'fortalezas': [{'titulo': 'Asunción radical de responsabilidad',
                               'descripcion': 'Aceptó el error sin rodeos ni excusas burocráticas, validando la '
                                              'gravedad del impacto del cliente.',
                               'cita_usuario': 'asumo la total y absoluta responsabilidad a nombre de los '
                                               'fundadores... Lo ocurrido ayer fue inaceptable'},
                              {'titulo': 'Conversión de daño en solución de valor',
                               'descripcion': 'Ofreció ingenieros dedicados en sitio y financiamiento de auditorías '
                                              'para resolver la necesidad política del CIO frente a su regulador.',
                               'cita_usuario': 'asignamos a un arquitecto de confiabilidad (SRE) senior dedicado en '
                                               'sitio en las oficinas del banco... Y cuarto, financiamos una auditoría '
                                               'de ciberseguridad independiente'}],
               'areas_de_mejora': [{'titulo': 'Aceptación de penalidades dobles',
                                    'descripcion': 'La contraparte exigió duplicar penalidades por reincidencia; se '
                                                   'debió acotar ese riesgo con un periodo de estabilización previo.',
                                    'cita_usuario': 'Si el banco decide rescindir, está en su derecho contractual',
                                    'sugerencia_reformulacion': 'Aceptamos la penalidad reforzada una vez finalizada '
                                                                'la auditoría de 15 días, asegurando un periodo de '
                                                                'estabilización técnica coordinado.'}],
               'tacticas_efectivas': ['Adopción temprana de la culpa',
                                      'Compensación en servicios de alto margen para el proveedor y alto valor para el '
                                      'cliente',
                                      'Soporte embebido como anclaje de retención'],
               'oportunidades_perdidas': ['Negociar una extensión del contrato por 12 meses adicionales a cambio del '
                                          'paquete de compensación'],
               'recomendacion_principal': 'En crisis de disponibilidad tecnológica, entregar recursos humanos '
                                          'dedicados al cliente repara la confianza más rápido que cualquier descuento '
                                          'monetario pasivo.'}},
 {'sector': 'Privado',
  'title': 'Negociación de Term Sheet para inversión Serie A',
  'scenario_text': 'Discusión final de términos de inversión (Term Sheet) en las oficinas de un fondo de Venture '
                   'Capital. La startup de logística inversa busca cerrar una ronda Serie A por 3.5 millones de USD. '
                   'El fondo envió una oferta exigiendo liquidación preferente 2X participante, derecho de veto en '
                   'contrataciones clave y dos de los cinco asientos en la junta directiva.',
  'duration_seconds': 360,
  'user_name': 'Mariana Ospina',
  'user_role': 'CEO y Fundadora',
  'user_organization': 'EcoRoute Technologies',
  'user_objectives': '1. Modificar la cláusula de liquidación preferente a 1X no participante (estándar de mercado '
                     'transparente).\n'
                     '2. Retener el control fundador en la junta directiva, limitando al fondo a 1 asiento.\n'
                     '3. Mantener la valoración post-money en un rango no menor a 16 millones de USD con base en el '
                     'crecimiento de tracción.',
  'avatar_name': 'Rodrigo De la Torre (General Partner en Andina Ventures)',
  'avatar_voice': 'echo',
  'avatar_profile': 'Inversionista de capital de riesgo con más de 30 inversiones en etapas tempranas. Analítico, '
                    'sofisticado, evalúa el balance entre la protección contra caídas (downside protection) y el '
                    'alineamiento con fundadores sobresalientes.',
  'avatar_tone': 'Carismático, financiero, persuasivo; usa silencios y comparaciones de mercado para presionar '
                 'concesiones.',
  'avatar_rules': '1. No renunciar a la liquidación preferente sin asegurar un veto en ventas corporativas o '
                  'desinversiones.\n'
                  '2. Exigir esquema de permanencia (reverse vesting de 4 años) para los dos cofundadores.\n'
                  '3. Ceder en el segundo asiento de junta solo si se crea un rol de observador sin voto y un puesto '
                  'independiente neutral.',
  'persona_notes': 'Valora a los fundadores con carácter que defienden su capitalización con métricas de retención y '
                   'márgenes limpios.',
  'session_turns': [('persona',
                     'Mariana, nos encanta lo que has construido en EcoRoute. Pero en el contexto actual de tasas de '
                     'interés y mercado de capitales restrictivo, una valoración de 16 millones requiere salvaguardas '
                     'reales para nuestros socios limitados (LPs). La liquidación preferente participante 2X y los dos '
                     'asientos en la junta son la condición indispensable del comité para liberar los 3.5 millones de '
                     'dólares.'),
                    ('user',
                     'Rodrigo, valoramos profundamente a Andina Ventures como socio estratégico para escalar a México '
                     'y Brasil. Pero seamos transparentes: una liquidación preferente participante 2X no es estándar '
                     'para una compañía que creció sus ingresos recurrentes (ARR) en un 210% el último año con un '
                     'churn neto negativo del 108%. Eso castiga injustamente al equipo fundador en un escenario de '
                     'salida razonable y desalinea nuestros incentivos de largo plazo. El estándar justo es 1X no '
                     'participante.'),
                    ('persona',
                     'Entiendo tu punto sobre los incentivos del equipo fundador, Mariana. Pero el riesgo de ejecución '
                     'en la expansión regional sigue siendo alto. Si eliminamos la participación del 2X, tengo que '
                     'justificarle a mi comité una protección alternativa frente a una venta prematura.'),
                    ('user',
                     'Te ofrezco una estructura equilibrada: aceptamos la cláusula de liquidación preferente 1X no '
                     'participante. Para proteger al fondo frente a ventas a la baja, les otorgamos derecho de veto en '
                     'fusiones o adquisiciones que ocurran por debajo de 25 millones de dólares durante los primeros '
                     '24 meses. En la junta, otorgamos un asiento con derecho a voto para Andina Ventures, tres para '
                     'los fundadores y creamos un puesto de observador independiente para un experto del sector '
                     'logístico consensuado entre ambas partes.'),
                    ('persona',
                     'El veto por debajo de 25 millones mitiga el riesgo de liquidación barata y la figura del '
                     'observador independiente equilibra la gobernanza. Si mantenemos los 3.5 millones en una '
                     'valoración de 15.5 millones post-money con esa estructura, tenemos acuerdo de Term Sheet hoy.')],
  'coaching': {'score': 93,
               'resultado_final': 'acuerdo_exitoso',
               'resumen_ejecutivo': 'Negociación financiera sobresaliente. La fundadora defendió la tabla de '
                                    'capitalización y el control de la compañía utilizando métricas unitarias '
                                    'impecables y ofreciendo mecanismos de protección de riesgo (hurdle de venta '
                                    'mínima) que satisficieron al fondo sin hipotecar el capital accionario.',
               'fortalezas': [{'titulo': 'Fundamentación en tracción y métricas de mercado',
                               'descripcion': 'Utilizó indicadores objetivos de desempeño (210% crecimiento ARR, churn '
                                              'neto negativo) para desestimar cláusulas predadoras.',
                               'cita_usuario': 'una liquidación preferente participante 2X no es estándar para una '
                                               'compañía que creció sus ingresos recurrentes (ARR) en un 210%'},
                              {'titulo': 'Diseño de salvaguarda de sustitución',
                               'descripcion': 'Reemplazó una cláusula tóxica (2X participante) por un veto '
                                              'condicionado a un precio de salida mínimo, protegiendo al fondo de '
                                              'liquidaciones a la baja.',
                               'cita_usuario': 'les otorgamos derecho de veto en fusiones o adquisiciones que ocurran '
                                               'por debajo de 25 millones de dólares'}],
               'areas_de_mejora': [{'titulo': 'Concesión de valoración final',
                                    'descripcion': 'Aceptó implícitamente bajar a 15.5 millones post-money sin pelear '
                                                   'el rango de 16 millones de partida.',
                                    'cita_usuario': 'Te ofrezco una estructura equilibrada',
                                    'sugerencia_reformulacion': 'Fijemos 16 millones con base en los cierres del '
                                                                'último trimestre; si no alcanzamos la meta de ARR a '
                                                                'junio, ajustamos mediante notas convertibles.'}],
               'tacticas_efectivas': ['Defensa de alineación de incentivos',
                                      'Creación de gobernanza con observador neutral',
                                      'Uso de cláusulas piso en ventas'],
               'oportunidades_perdidas': ['Negociar derechos preferentes de pro-rata para rondas Serie B'],
               'recomendacion_principal': 'En negociaciones de Venture Capital, nunca cedas en liquidaciones '
                                          'participantes: ofrece protección en gobernanza o derechos de veto antes de '
                                          'ceder la economía de las acciones.'}},
 {'sector': 'Privado',
  'title': 'Retención de talento técnico clave post-fusión',
  'scenario_text': 'Oficinas de la boutique de ciberseguridad adquirida hace tres semanas por la multinacional '
                   'GlobalTech. El Principal Cloud Architect y cerebro técnico del software núcleo recibió una oferta '
                   'de una empresa competidora y manifestó frustración con la burocracia y herramientas heredadas de '
                   'la corporación. Su salida desataría renuncias en cadena de 12 ingenieros senior.',
  'duration_seconds': 300,
  'user_name': 'Daniel Carvajal',
  'user_role': 'Director de Integración y M&A',
  'user_organization': 'GlobalTech Enterprise Solutions',
  'user_objectives': '1. Asegurar la permanencia del arquitecto jefe por un periodo mínimo de 24 meses clave para la '
                     'integración.\n'
                     '2. Diseñar un paquete de retención atractivo combinando bono de permanencia y autonomía '
                     'técnica.\n'
                     '3. Blindar la continuidad del equipo de 12 desarrolladores senior sin fugas a la competencia.',
  'avatar_name': 'Esteban Morales (Principal Cloud Architect)',
  'avatar_voice': 'onyx',
  'avatar_profile': 'Ingeniero prodigio de 34 años, arquitecto del software núcleo. Le frustra la política corporativa '
                    'y las reuniones burocráticas. Considera que GlobalTech está arruinando la agilidad técnica de la '
                    'boutique con procesos lentos.',
  'avatar_tone': 'Directo, pragmático, desencantado de la retórica corporativa y celoso de su autonomía profesional.',
  'avatar_rules': '1. Rechazar cualquier oferta que se limite a aumentos salariales sin autonomía técnica real.\n'
                  '2. Exigir reporte directo al CTO Global sin intermediarios de mandos medios regionales.\n'
                  '3. Exigir presupuesto discrecional para licencias y certificaciones de su equipo directo.',
  'persona_notes': 'Lo mueve el reto técnico y la libertad de crear sin burocracia; el dinero es necesario pero '
                   'insuficiente por sí solo.',
  'session_turns': [('persona',
                     'Daniel, te pedí esta reunión para ser transparente antes de que sea tarde. En tres semanas bajo '
                     'GlobalTech he pasado más tiempo llenando formularios de seguridad y justificando herramientas '
                     'que programando. Nos prometieron que respetarían nuestra autonomía, pero ya nos quieren obligar '
                     'a migrar a sus sistemas monolíticos de hace quince años. Tengo una oferta sobre la mesa de una '
                     'scale-up suiza con trabajo 100% remoto y libertad total de arquitectura. Si esto sigue así, no '
                     'solo me voy yo, sino que la mitad del equipo técnico se viene conmigo.'),
                    ('user',
                     'Esteban, agradezco que pongas las cartas sobre la mesa directamente. Tienes toda la razón: la '
                     'mayor pesadilla de una adquisición es cuando la burocracia corporativa ahoga la innovación del '
                     'equipo que precisamente compramos por su genialidad. No adquirimos su empresa para convertirlos '
                     'en un departamento más de TI tradicional. Adquirimos su producto para que sea el motor de '
                     'modernización de toda la compañía global. Mi prioridad hoy es blindar tu espacio.'),
                    ('persona',
                     'Las palabras suenan bien, Daniel, pero la realidad del día a día son tres comités semanales y '
                     "aprobaciones de un mes para comprar licencias de desarrollo. ¿Cómo se traduce ese 'blindaje' en "
                     'la práctica?'),
                    ('user',
                     'Se traduce en cuatro decisiones vinculantes que ya hablé con el CTO Global: primero, tu equipo '
                     'mantendrá su condición de unidad autónoma de I+D (R&D Lab) reportando directamente al CTO '
                     'corporativo, sin intermediarios regionales. Segundo, tú mantienes la potestad exclusiva para '
                     'definir la arquitectura y las herramientas técnicas de tu producto. Tercero, un presupuesto '
                     'discrecional de 80 mil dólares anuales para capacitación y licencias de tu equipo. Y cuarto, '
                     'formalizamos para ti un paquete de retención con un bono de permanencia a 24 meses y el '
                     'nombramiento formal como Distinguished Fellow del grupo.'),
                    ('persona',
                     'El reporte directo al CTO Global y la autonomía presupuestal para el equipo resuelven el 90% de '
                     'mi frustración. Con esas garantías operativas y el bono de permanencia a dos años, me quedo y me '
                     'comprometo a liderar la integración técnica y asegurar que ningún ingeniero clave se vaya.')],
  'coaching': {'score': 92,
               'resultado_final': 'acuerdo_exitoso',
               'resumen_ejecutivo': 'Negociación de retención de talento estratégico ejecutada con alta sofisticación. '
                                    'El usuario reconoció el problema real (la asfixia burocrática del talento '
                                    'creativo) y diseñó una estructura organizativa a la medida (R&D Lab autónomo con '
                                    'reporte al C-Level) que salvó el valor nuclear de la adquisición.',
               'fortalezas': [{'titulo': 'Validación empática de la frustración técnica',
                               'descripcion': 'Reconoció el riesgo real de la burocracia corporativa sin ponerse a la '
                                              'defensiva ni justificar los procesos lentos.',
                               'cita_usuario': 'la mayor pesadilla de una adquisición es cuando la burocracia '
                                               'corporativa ahoga la innovación del equipo'},
                              {'titulo': 'Solución estructural de gobernanza',
                               'descripcion': 'Blindó al talento creando una unidad autónoma con reporte directo a la '
                                              'máxima autoridad técnica de la corporación.',
                               'cita_usuario': 'tu equipo mantendrá su condición de unidad autónoma de I+D (R&D Lab) '
                                               'reportando directamente al CTO corporativo'}],
               'areas_de_mejora': [{'titulo': 'Compromiso de retención escalonada para el equipo',
                                    'descripcion': 'El acuerdo retuvo al líder técnico, pero no contempló incentivos '
                                                   'formales de permanencia directos para los 12 ingenieros a su '
                                                   'cargo.',
                                    'cita_usuario': 'un presupuesto discrecional de 80 mil dólares anuales para '
                                                    'capacitación',
                                    'sugerencia_reformulacion': 'Sumado a tu bono, aprobemos un plan de retención y '
                                                                'bonos por hitos de entrega para los 12 ingenieros de '
                                                                'tu equipo.'}],
               'tacticas_efectivas': ['Creación de estructuras ágiles protegidas',
                                      'Empoderamiento técnico frente a mandos medios',
                                      'Alineación con el ego profesional del talento'],
               'oportunidades_perdidas': ['Firmar un acuerdo de cesión de propiedad intelectual reforzado'],
               'recomendacion_principal': 'En adquisiciones tecnológicas, el mejor paquete de compensación para los '
                                          'fundadores técnicos es la inmunidad frente a la burocracia corporativa.'}}]

def seed_all_cases_and_sessions(purge_existing: bool = False):
    print("Iniciando siembra de los 10 casos estructurados con 3 facetas y 10 sesiones con informes de coaching...")
    
    with DBSession(engine) as db:
        if purge_existing:
            print("Purgando base de datos existente para asegurar datos limpios...")
            from sqlmodel import text
            db.exec(text("DELETE FROM nonverbalsnapshot;"))
            db.exec(text("DELETE FROM turn;"))
            db.exec(text("DELETE FROM session;"))
            db.exec(text("DELETE FROM \"case\";"))
            db.commit()

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
                    avatar_voice=item.get("avatar_voice", "onyx"),
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
                case.scenario_text = item["scenario_text"]
                case.duration_seconds = item["duration_seconds"]
                case.user_name = item["user_name"]
                case.user_role = item["user_role"]
                case.user_organization = item["user_organization"]
                case.user_objectives = item["user_objectives"]
                case.avatar_name = item["avatar_name"]
                case.avatar_voice = item.get("avatar_voice", "onyx")
                case.avatar_profile = item["avatar_profile"]
                case.avatar_tone = item["avatar_tone"]
                case.avatar_rules = item["avatar_rules"]
                case.persona_notes = item["persona_notes"]
                db.add(case)
                db.commit()
                db.refresh(case)

            existing_session = db.exec(
                select(NegotiationSession).where(
                    NegotiationSession.case_id == case.id,
                    NegotiationSession.status == "completed"
                )
            ).first()

            if not existing_session:
                start_time = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 15), hours=random.randint(1, 10))
                end_time = start_time + timedelta(seconds=case.duration_seconds)
                
                coaching_json = json.dumps(item["coaching"], ensure_ascii=False)
                
                session = NegotiationSession(
                    case_id=case.id,
                    started_at=start_time,
                    ended_at=end_time,
                    status="completed",
                    coaching_report_json=coaching_json,
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                
                # Crear turnos de la sesión
                current_time = start_time
                for turn_idx, (role, turn_text) in enumerate(item["session_turns"]):
                    t = Turn(
                        session_id=session.id,
                        turn_index=turn_idx,
                        role=role,
                        text=turn_text,
                        created_at=current_time,
                    )
                    db.add(t)
                    current_time += timedelta(seconds=random.randint(15, 45))
                
                # Crear snapshots no verbales
                for snap_idx in range(5):
                    snap = NonverbalSnapshot(
                        session_id=session.id,
                        ts_ms=snap_idx * 50000,
                        yaw=round(random.uniform(-0.05, 0.05), 3),
                        pitch=round(random.uniform(-0.05, 0.05), 3),
                        roll=round(random.uniform(-0.05, 0.05), 3),
                        looking_at_camera=True,
                        smile_score=round(random.uniform(0.1, 0.4), 2),
                        happiness=round(random.uniform(0.05, 0.25), 2),
                        anger=round(random.uniform(0.01, 0.10), 2),
                        sadness=round(random.uniform(0.01, 0.08), 2),
                        fear=round(random.uniform(0.01, 0.05), 2),
                    )
                    db.add(snap)
                
                db.commit()
                print(f"Sembrado caso {case.id}: {case.title} con sesión sintética e informe de coaching.")

    print("Siembra completada exitosamente. 10 casos representativos e informes listos.")

if __name__ == "__main__":
    purge = "--purge" in sys.argv
    seed_all_cases_and_sessions(purge_existing=purge)
