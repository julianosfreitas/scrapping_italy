"""Páginas HTML (fase 1: Jinja2 + Tailwind servidos pelo FastAPI)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.db import get_sessionmaker
from app.models import Curso, Estudante, Universidade
from app.routers.universidades import _curso_publico
from app.services.cursos import ordenar_por_prazo

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


@router.get("/universidades", response_class=HTMLResponse)
def universidades(request: Request, q: str | None = None) -> HTMLResponse:
    with get_sessionmaker()() as sessao:
        consulta = select(Universidade).options(selectinload(Universidade.cursos))
        if q:
            consulta = consulta.where(Universidade.nome.ilike(f"%{q}%"))
        lista = sessao.scalars(consulta.order_by(Universidade.nome)).all()
        return templates.TemplateResponse(
            request, "universidades.html", {"universidades": lista, "consulta": q}
        )


@router.get("/universidades/{universidade_id}", response_class=HTMLResponse)
def universidade_detalhe(request: Request, universidade_id: int) -> HTMLResponse:
    with get_sessionmaker()() as sessao:
        universidade = sessao.get(
            Universidade,
            universidade_id,
            options=[selectinload(Universidade.cursos).selectinload(Curso.requisitos)],
        )
        if universidade is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Universidade não encontrada")
        hoje = datetime.now(UTC).date()
        cursos = [
            _curso_publico(c, hoje)
            for c in ordenar_por_prazo(universidade.cursos, lambda c: c.prazo_inscricao)
        ]
        return templates.TemplateResponse(
            request,
            "universidade_detalhe.html",
            {"universidade": universidade, "cursos": cursos},
        )
