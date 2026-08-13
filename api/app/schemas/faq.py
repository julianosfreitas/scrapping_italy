"""Schemas do FAQ — imutáveis (frozen=True) e recursivos como a árvore."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _Congelado(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)


class PerguntaPublica(_Congelado):
    id: int
    pergunta: str
    resposta: str
    fontes: tuple[str, ...] = ()


class CategoriaPublica(_Congelado):
    """O schema se referencia a si mesmo — a recursão atravessa até o JSON."""

    id: int
    nome: str
    perguntas: tuple[PerguntaPublica, ...] = ()
    subcategorias: tuple[CategoriaPublica, ...] = ()
    total_perguntas: int = 0
