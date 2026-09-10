# Simulador y Avatar de Entrenamiento en Negociaciones y Conversaciones Críticas

Un simulador interactivo multi-escenario donde un avatar de IA (impulsado por Claude) actúa como contraparte adaptativa. Permite entrenar cualquier clase de negociación o conversación difícil:
- **Discusión y concertación pública o política** (ej. gremios vs. mandatarios).
- **Entregas de noticias complejas o de alta sensibilidad** (ej. noticias médicas a pacientes o familiares).
- **Sesiones de retroalimentación crítica** (ej. feedback de desempeño a estudiantes o colaboradores).
- **Negociaciones comerciales y estratégicas** (ej. clientes, proveedores, resolución de conflictos).

Al finalizar cada sesión, Claude genera un **informe de coaching** detallado y personalizado sobre el desempeño comunicativo y estratégico del negociador.

---

## Arquitectura

```
Avatar/
├── app/                         # Producto principal: Avatar de Entrenamiento
│   ├── data/
│   │   ├── persona_brief.md     # Perfil, estilo y reglas de la contraparte (avatar)
│   │   └── policy_snippets/     # Base de conocimiento de referencia (RAG)
│   ├── routers/
│   │   ├── cases.py             # CRUD de casos y escenarios
│   │   ├── profiles.py          # Gestión de perfil del negociante y contraparte
│   │   ├── sessions.py          # Lógica de sesión (turnos, audio, cámara, extensiones)
│   │   └── review.py            # Revisión post-sesión + informe de coaching
│   ├── services/
│   │   ├── llm.py               # Claude — cerebro adaptativo del avatar (con streaming)
│   │   ├── coach.py             # Claude — análisis de coaching post-sesión
│   │   ├── rag.py               # Recuperación de contexto de referencia
│   │   ├── persona.py           # Carga y gestión dinámica del perfil del avatar
│   │   ├── stt.py               # Transcripción de audio (OpenAI Whisper)
│   │   └── tts.py               # Voz del avatar (OpenAI TTS)
│   ├── config.py                # Configuración del servidor
│   ├── db.py                    # Base de datos SQLite / PostgreSQL
│   ├── models.py                # Modelos de datos SQLModel
│   ├── schemas.py               # Esquemas Pydantic
│   └── main.py                  # Servidor FastAPI
├── frontend/                    # Interfaz web
│   ├── index.html               # Inicio: crear/seleccionar escenario
│   ├── profiles.html            # Configuración de perfil de usuario y avatar
│   ├── session.html             # Sesión de simulación en vivo (video/audio)
│   ├── review.html              # Revisión post-sesión con informe de coaching
│   └── static/                 # CSS, fuentes y JavaScript (MediaPipe, Chart.js)
├── scripts/                     # Herramientas opcionales de extracción de corpus
│   ├── main.py                  # CLI unificada de extracción
│   ├── youtube_extractor.py     # Extrae subtítulos de YouTube
│   ├── twitter_scraper.py       # Extrae tweets con Playwright
│   ├── transcript_corrector.py  # Corrige subtítulos con IA (Gemini)
│   ├── rag_formatter.py         # Formatea a Markdown para el RAG
│   └── config.py                # Configuración de los scripts de extracción
├── .env                         # Variables de entorno (no commitear)
├── .env.example                 # Plantilla de configuración
├── requirements.txt             # Dependencias
└── storage.db                   # Base de datos local SQLite
```

---

## Cómo funciona

### El Avatar de Entrenamiento

1. **Configuras tu perfil de negociador**: define tu nombre, cargo, organización y objetivos en la pestaña *Perfiles*. El avatar y el coach usarán esta información para calibrar la interacción.
2. **Creas o seleccionas un caso**: defines el escenario, los objetivos en juego, el nombre de la contraparte y el tiempo de negociación.
3. **Inicias la sesión**: el avatar abre la interacción en personaje de forma coherente con la situación planteada.
4. **Interactúas**: envías audio o texto. El avatar responde en personaje con voz sintetizada (OpenAI TTS), evaluando tus argumentos.
5. **Finalizas la sesión**: Claude analiza la transcripción y tus objetivos mediante *extended thinking* y genera un **informe de coaching** que incluye:
   - **Puntaje global** (0–100)
   - **Resultado final** (acuerdo parcial, aplazamiento, rechazo, acuerdo exitoso, etc.)
   - **Fortalezas** con citas textuales de lo que dijiste
   - **Áreas de mejora** con citas y sugerencias de cómo reformularlo
   - **Tácticas efectivas** y **oportunidades perdidas**
   - **Recomendación principal** para tu próxima práctica

---

## Configuración

### Variables de entorno (`.env`)

```env
# Obligatorio para el avatar y el coaching (Anthropic Claude)
ANTHROPIC_API_KEY=tu_clave_aqui

# Necesario para entrada de voz (Whisper) y voz de la contraparte (TTS)
OPENAI_API_KEY=tu_clave_aqui

# Opcional: Voz del avatar para TTS (alloy, echo, fable, onyx, nova, shimmer)
OPENAI_TTS_VOICE=onyx

# Opcional: Modelo de Claude (por defecto: claude-opus-4-8)
MODEL_NAME=claude-opus-4-8

# Opcional: para los scripts de extracción de YouTube/Twitter
GEMINI_API_KEY=tu_clave_aqui
```

Copia `.env.example` a `.env` y llena las claves que necesites.

---

## Instalación y ejecución

```bash
pip install -r requirements.txt
```

### Iniciar el servidor del Avatar

```bash
uvicorn app.main:app --reload
```

Abrir en el navegador: **http://localhost:8000**

---

## Scripts de enriquecimiento del corpus (opcionales)

Estas herramientas alimentan la base de conocimiento (`app/data/policy_snippets/`) del avatar. Son completamente opcionales y no afectan el servidor principal.

### Extraer de YouTube

```bash
python scripts/main.py --channel "https://www.youtube.com/@canal" \
  --start-date 2024-01-01 --end-date 2025-01-01 \
  --language es --model gemini-2.5-flash
```

### Extraer de Twitter/X

```bash
# Primera vez (abre navegador para login manual):
python scripts/main.py --twitter "@usuario" --visible

# Usos posteriores (sesión guardada):
python scripts/main.py --twitter "@usuario"
```

### Opciones combinadas

```bash
python scripts/main.py \
  --channel "https://www.youtube.com/@canal" \
  --twitter "@usuario" \
  --start-date 2024-01-01 \
  --end-date 2025-01-01
```

---

## Personalización del avatar

El comportamiento del avatar se controla desde `app/data/persona_brief.md`. Puedes modificar:
- **El perfil** del personaje (quién es, qué cargo tiene, de qué país)
- **El tono y estilo** de habla
- **Las reglas de negociación** (cuándo cede, qué líneas rojas tiene)

Los cambios en `persona_brief.md` se aplican **inmediatamente** sin reiniciar el servidor (cuando se usa `--reload`).

---

## Despliegue en Railway (con PostgreSQL)

Este proyecto está completamente preparado para desplegarse en [Railway](https://railway.app/).

### Pasos para desplegar la aplicación:

1. **Crear base de datos PostgreSQL:**
   - En tu panel de Railway, haz clic en **New** -> **Database** -> **PostgreSQL**.
2. **Conectar tu Repositorio de GitHub:**
   - Sube este proyecto a tu repositorio de GitHub y conéctalo como un nuevo servicio web en Railway.
   - El sistema detectará automáticamente el archivo `requirements.txt` y levantará el backend con Python.
3. **Configurar un Volumen Persistente (Volumen de Railway):**
   - El simulador guarda los archivos de audio MP3 generados localmente. Para evitar que se eliminen al reiniciar el contenedor, agrega un volumen persistente en Railway (por ejemplo, con tamaño `1 GB`, nombre `data` y ruta de montaje `/data`).
4. **Configurar Variables de Entorno en el Servicio Web:**
   - En la pestaña de configuración del servicio en Railway, agrega las siguientes variables de entorno:
     ```env
     PORT=8000
     DATABASE_URL= (Conéctala y asóciala a la variable que provee tu servicio de PostgreSQL en Railway)
     AUDIO_STORAGE_DIR=/data/audio
     DATA_DIR=/data/persona-assets
     ANTHROPIC_API_KEY=tu_clave_de_api_de_claude
     OPENAI_API_KEY=tu_clave_de_api_de_openai
     ```
5. **Comando de Inicio (Start Command):**
   - La aplicación detectará el puerto automáticamente y correrá mediante: `python run.py`.

