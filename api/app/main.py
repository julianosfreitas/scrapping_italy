"""Ponto de entrada da API Ponte Italia."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.routers import (
    auth,
    documentos,
    estudantes,
    faq,
    newsletter,
    noticias,
    paginas,
    universidades,
)


@asynccontextmanager
async def _ciclo_de_vida(_app: FastAPI) -> AsyncIterator[None]:
    Path(get_settings().upload_dir).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Ponte Italia — API",
    description="Plataforma de intercâmbio acadêmico Brasil → Itália/Europa.",
    version="0.2.0",
    lifespan=_ciclo_de_vida,
)

# JS/CSS estáticos (Sprint 6): fora dos templates, cacheáveis pelo navegador
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent / "static")),
    name="static",
)

app.include_router(auth.router)
app.include_router(estudantes.router)
app.include_router(documentos.router)
app.include_router(universidades.router)
app.include_router(noticias.router)
app.include_router(newsletter.router)
app.include_router(faq.router)
app.include_router(paginas.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Healthcheck simples: confirma que a API está de pé e em qual ambiente."""
    settings = get_settings()
    return {"status": "ok", "ambiente": settings.app_env}
