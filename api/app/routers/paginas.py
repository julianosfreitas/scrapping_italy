"""Páginas HTML (fase 1: Jinja2 + Tailwind servidos pelo FastAPI).

Todas as páginas usam a MESMA dependência de sessão das rotas de API
(`get_sessao`) — nos testes, o override troca o banco de uma vez só.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_sessao
from app.models import Curso, EdicaoNewsletter, Estudante, Noticia, Universidade
from app.routers.faq import _para_schema as _faq_publica
from app.routers.faq import carregar_arvore
from app.routers.newsletter import listar_edicoes
from app.routers.noticias import montar_feed
from app.routers.universidades import _curso_publico
from app.schemas.newsletter import EdicaoPublica
from app.services.cursos import ordenar_por_prazo
from app.services.faq import Categoria as CategoriaFaq
from app.services.faq import buscar, caminho_ate
from app.services.feed import TAMANHO_PAGINA_PADRAO

ROTULOS_CATEGORIAS = {
    "vistos": "Vistos",
    "prazos": "Prazos",
    "bolsas": "Bolsas",
    "idioma": "Idioma",
    "moradia": "Moradia",
    "financas": "Finanças",
    "documentacao": "Documentação",
    "admissoes": "Admissões",
    "vida_na_italia": "Vida na Itália",
    "mercado": "Mercado",
    "geral": "Geral",
}

router = APIRouter(include_in_schema=False)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))

Sessao = Annotated[Session, Depends(get_sessao)]


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "home.html")


@router.get("/login", response_class=HTMLResponse)
def login(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html")


@router.get("/estudantes", response_class=HTMLResponse)
def estudantes(request: Request, sessao: Sessao) -> HTMLResponse:
    lista = sessao.scalars(select(Estudante).order_by(Estudante.nome)).all()
    return templates.TemplateResponse(request, "estudantes.html", {"estudantes": lista})


@router.get("/estudantes/{estudante_id}", response_class=HTMLResponse)
def perfil(request: Request, estudante_id: int, sessao: Sessao) -> HTMLResponse:
    estudante = sessao.get(Estudante, estudante_id)
    if estudante is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Estudante não encontrado")
    return templates.TemplateResponse(request, "perfil.html", {"estudante": estudante})


@router.get("/radar", response_class=HTMLResponse)
def radar(
    request: Request,
    sessao: Sessao,
    categoria: str | None = None,
    fonte: str | None = None,
    pagina: int = 1,
) -> HTMLResponse:
    feed = montar_feed(sessao, categoria, fonte, max(1, pagina), TAMANHO_PAGINA_PADRAO)
    fontes = sessao.scalars(select(Noticia.fonte).distinct().order_by(Noticia.fonte)).all()
    categorias = sessao.scalars(
        select(Noticia.categoria).distinct().order_by(Noticia.categoria)
    ).all()
    return templates.TemplateResponse(
        request,
        "radar.html",
        {
            "feed": feed,
            "fontes": fontes,
            "categorias": categorias,
            "categoria_ativa": categoria or "",
            "fonte_ativa": fonte or "",
            "rotulos": ROTULOS_CATEGORIAS,
        },
    )


@router.get("/newsletter", response_class=HTMLResponse)
def newsletter(request: Request, sessao: Sessao) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "newsletter.html", {"edicoes": listar_edicoes(sessao)}
    )


@router.get("/newsletter/{data_edicao}", response_class=HTMLResponse)
def newsletter_edicao(request: Request, data_edicao: date, sessao: Sessao) -> HTMLResponse:
    arquivada = sessao.scalar(select(EdicaoNewsletter).where(EdicaoNewsletter.data == data_edicao))
    if arquivada is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Edição não encontrada")
    return templates.TemplateResponse(
        request,
        "newsletter_edicao.html",
        {
            "edicao": EdicaoPublica.model_validate(arquivada.conteudo),
            "enviada_em": arquivada.enviada_em,
        },
    )


@router.get("/ajuda", response_class=HTMLResponse)
def ajuda(
    request: Request,
    sessao: Sessao,
    q: str = "",
    categoria: int | None = None,
) -> HTMLResponse:
    """FAQ: árvore recursiva no menu + busca na subárvore escolhida."""
    arvore = carregar_arvore(sessao)
    trilha: tuple[CategoriaFaq, ...] = ()
    if categoria is not None:
        trilha = next((caminho for raiz in arvore if (caminho := caminho_ate(raiz, categoria))), ())
        if not trilha:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada")

    escopo = (trilha[-1],) if trilha else arvore
    perguntas = tuple(p for alvo in escopo for p in buscar(alvo, q))
    return templates.TemplateResponse(
        request,
        "ajuda.html",
        {
            "arvore": [_faq_publica(raiz) for raiz in arvore],
            "perguntas": perguntas,
            "consulta": q,
            "categoria_ativa": categoria,
            "trilha": trilha,
        },
    )


@router.get("/universidades", response_class=HTMLResponse)
def universidades(request: Request, sessao: Sessao, q: str | None = None) -> HTMLResponse:
    consulta = select(Universidade).options(selectinload(Universidade.cursos))
    if q:
        consulta = consulta.where(Universidade.nome.ilike(f"%{q}%"))
    lista = sessao.scalars(consulta.order_by(Universidade.nome)).all()
    return templates.TemplateResponse(
        request, "universidades.html", {"universidades": lista, "consulta": q}
    )


@router.get("/universidades/{universidade_id}", response_class=HTMLResponse)
def universidade_detalhe(request: Request, universidade_id: int, sessao: Sessao) -> HTMLResponse:
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
