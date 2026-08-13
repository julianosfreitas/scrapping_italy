"""FAQ (/api/faq): a árvore de categorias e a busca por perguntas.

O router faz só I/O: lê as linhas planas da tabela `faq`, converte para
`LinhaFaq` (congelada) e entrega tudo à recursão pura de
`app.services.faq`. Nenhuma regra de navegação mora aqui.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_sessao
from app.models import ItemFaq
from app.schemas.faq import CategoriaPublica, PerguntaPublica
from app.services.faq import (
    Categoria,
    LinhaFaq,
    buscar,
    caminho_ate,
    contar_perguntas,
    montar_arvore,
)

router = APIRouter(prefix="/api/faq", tags=["faq"])

Sessao = Annotated[Session, Depends(get_sessao)]


def _para_linha(item: ItemFaq) -> LinhaFaq:
    return LinhaFaq(
        id=item.id,
        categoria_id=item.categoria_id,
        nome=item.nome,
        pergunta=item.pergunta,
        resposta=item.resposta,
        fontes=tuple(str(f) for f in (item.fontes or ())),
        ordem=item.ordem,
    )


def carregar_arvore(sessao: Session) -> tuple[Categoria, ...]:
    """Todas as linhas em UMA consulta; a hierarquia é montada em memória.

    Uma árvore de FAQ é pequena e lida a cada visita — buscar tudo de uma vez
    e montar com a função pura evita o N+1 que um passeio recursivo pelo ORM
    provocaria (um SELECT por nível, por nó).
    """
    linhas = sessao.scalars(select(ItemFaq).order_by(ItemFaq.ordem, ItemFaq.id)).all()
    return montar_arvore(_para_linha(item) for item in linhas)


def _para_schema(categoria: Categoria) -> CategoriaPublica:
    """Conversão RECURSIVA: a subárvore inteira vira schema Pydantic."""
    return CategoriaPublica(
        id=categoria.id,
        nome=categoria.nome,
        perguntas=tuple(
            PerguntaPublica(id=p.id, pergunta=p.pergunta, resposta=p.resposta, fontes=p.fontes)
            for p in categoria.perguntas
        ),
        subcategorias=tuple(_para_schema(s) for s in categoria.subcategorias),
        total_perguntas=contar_perguntas(categoria),
    )


@router.get("")
def listar_faq(sessao: Sessao) -> tuple[CategoriaPublica, ...]:
    """A árvore completa, com a contagem recursiva de perguntas por categoria."""
    return tuple(_para_schema(c) for c in carregar_arvore(sessao))


@router.get("/buscar")
def buscar_perguntas(
    sessao: Sessao, q: str = "", categoria_id: int | None = None
) -> tuple[PerguntaPublica, ...]:
    """Busca em toda a árvore, ou só na subárvore de `categoria_id`."""
    arvore = carregar_arvore(sessao)
    escopo = arvore
    if categoria_id is not None:
        escopo = tuple(
            achada
            for raiz in arvore
            if (caminho := caminho_ate(raiz, categoria_id))
            for achada in (caminho[-1],)
        )
        if not escopo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada")

    return tuple(
        PerguntaPublica(id=p.id, pergunta=p.pergunta, resposta=p.resposta, fontes=p.fontes)
        for categoria in escopo
        for p in buscar(categoria, q)
    )
