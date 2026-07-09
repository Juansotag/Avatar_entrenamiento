# Avatar de Entrenamiento en Negociación

Un simulador de negociación empresa-Estado donde un avatar de IA (impulsado por Claude) actúa como mandatario político. Al finalizar cada sesión, Claude genera un **informe de coaching** detallado sobre el desempeño del negociador.

---

## Arquitectura

```
Avatar/
├── app/                         # Producto principal: Avatar de Entrenamiento
│   ├── data/
│   │   ├── persona_brief.md     # Perfil y reglas del personaje político (avatar)
│   │   └── policy_snippets/     # Base de conocimiento del avatar (RAG)
│   ├── routers/
│   │   ├── cases.py             # CRUD de casos de negociación
│   │   ├── sessions.py          # Lógica de sesión (turnos, audio, cierre)
│   │   └── review.py            # Revisión post-sesión + informe de coaching
│   ├── services/
│   │   ├── llm.py               # Claude — cerebro del avatar (con streaming)
│   │   ├── coach.py             # Claude — análisis de coaching post-sesión
│   │   ├── rag.py               # Recuperación de contexto de política pública
│   │   ├── persona.py           # Carga del perfil del personaje
│   │   ├── stt.py               # Transcripción de audio (OpenAI Whisper)
│   │   └── tts.py               # Voz del avatar (ElevenLabs)
│   ├── config.py                # Configuración del servidor
│   ├── db.py                    # Base de datos SQLite
│   ├── models.py                # Modelos de datos
│   ├── schemas.py               # Esquemas Pydantic
│   └── main.py                  # Servidor FastAPI
├── frontend/                    # Interfaz web
│   ├── index.html               # Inicio: crear/seleccionar caso
│   ├── session.html             # Sesión de negociación en vivo
│   ├── review.html              # Revisión post-sesión con informe de coaching
│   └── static/                 # CSS y JS
├── scripts/                     # Herramientas opcionales de enriquecimiento del corpus
│   ├── main.py                  # CLI unificada de extracción
│   ├── youtube_extractor.py     # Extrae subtítulos de YouTube
│   ├── twitter_scraper.py       # Extrae tweets con Playwright
│   ├── transcript_corrector.py  # Corrige subtítulos con IA
│   ├── rag_formatter.py         # Formatea a Markdown para el RAG
│   └── config.py                # Configuración de los scripts de extracción
├── .env                         # Variables de entorno (no commitear)
├── .env.example                 # Plantilla de configuración
├── requirements.txt             # Dependencias
└── storage.db                   # Base de datos SQLite
```

---

## Cómo funciona

### El Avatar de Entrenamiento

1. **Creas un caso** desde la pantalla de inicio: defines el escenario de negociación (quién eres, qué quieres del mandatario).
2. **Inicias la sesión**: el avatar (Claude, en rol de El Mandatario) abre la reunión con una frase de apertura.
3. **Negocias**: envías audio o texto, el avatar responde en personaje, con voz opcional via ElevenLabs.
4. **Finalizas la sesión**: Claude analiza la transcripción completa con *extended thinking* y genera un **informe de coaching** que incluye:
   - **Puntaje global** (0–100)
   - **Resultado final**: acuerdo parcial, aplazamiento o rechazo
   - **Fortalezas** con citas textuales de lo que dijiste
   - **Áreas de mejora** con citas y sugerencias de cómo reformularlo
   - **Tácticas efectivas** y **oportunidades perdidas**
   - **Recomendación principal** para tu próxima práctica

### El RAG (Base de conocimiento del avatar)

El avatar conoce los temas de política pública que están en `app/data/policy_snippets/*.md`. Para enriquecer su conocimiento puedes agregar archivos Markdown manualmente o usar los **scripts de extracción**.

---

## Configuración

### Variables de entorno (`.env`)

```env
# Obligatorio para el avatar
ANTHROPIC_API_KEY=tu_clave_aqui

# Opcional: voz del avatar
ELEVENLABS_API_KEY=tu_clave_aqui
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB

# Necesario si usas entrada de voz (STT)
OPENAI_API_KEY=tu_clave_aqui

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

