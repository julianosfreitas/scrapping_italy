"""Ponto de entrada da API Ponte Italia."""

from __future__ import annotations

from fastapi import FastAPI

from app.core.config import get_settings

app = FastAPI(
    title="Ponte Italia — API",
    description="Plataforma de intercâmbio acadêmico Brasil → Itália/Europa.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Healthcheck simples: confirma que a API está de pé e em qual ambiente."""
    settings = get_settings()
    return {"status": "ok", "ambiente": settings.app_env}
