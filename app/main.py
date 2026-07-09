from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import init_db
from app.routers import cases, profiles, review, sessions

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Simulador de negociación", lifespan=lifespan)


@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    # Forzar al navegador a descargar las versiones más recientes de JS, CSS y HTML sin usar caché
    if path.startswith("/static/") or path.endswith(".html") or path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

app.include_router(cases.router)
app.include_router(sessions.router)
app.include_router(review.router)
app.include_router(profiles.router)

app.mount("/audio", StaticFiles(directory=str(settings.audio_storage_dir)), name="audio")
app.mount("/persona-assets", StaticFiles(directory=str(settings.data_dir)), name="persona-assets")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
