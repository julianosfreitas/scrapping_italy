"""Páginas HTML (fase 1: Jinja2 + Tailwind servidos pelo FastAPI)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.core.db import get_sessionmaker
from app.models import Estudante

router = APIRouter(include_in_schema=False)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "home.html")


@router.get("/login", response_class=HTMLResponse)
def login(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html")


@router.get("/estudantes", response_class=HTMLResponse)
def estudantes(request: Request) -> HTMLResponse:
    with get_sessionmaker()() as sessao:
        lista = sessao.scalars(select(Estudante).order_by(Estudante.nome)).all()
        return templates.TemplateResponse(request, "estudantes.html", {"estudantes": lista})


@router.get("/estudantes/{estudante_id}", response_class=HTMLResponse)
def perfil(request: Request, estudante_id: int) -> HTMLResponse:
    with get_sessionmaker()() as sessao:
        estudante = sessao.get(Estudante, estudante_id)
        if estudante is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Estudante não encontrado")
        return templates.TemplateResponse(request, "perfil.html", {"estudante": estudante})
