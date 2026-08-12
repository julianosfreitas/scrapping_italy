"""Schemas do Radar de notícias — imutáveis (frozen=True)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class _Congelado(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)


class NoticiaCriar(_Congelado):
    titulo: str = Field(min_length=3, max_length=300)
    url: str = Field(pattern=r"^https?://", max_length=500)
    fonte: str = Field(min_length=2, max_length=40)
    categoria: str = Field(default="geral", max_length=40)
    resumo: str | None = Field(default=None, max_length=1000)
    idioma: str | None = Field(default=None, max_length=10)
    publicada_em: datetime | None = None


class NoticiaPublica(_Congelado):
    id: int
    titulo: str
    resumo: str | None
    url: str
    fonte: str
    categoria: str
    idioma: str | None
    publicada_em: datetime | None
    coletada_em: datetime


class ResultadoIngestao(_Congelado):
    criadas: int
    ignoradas: int  # URLs que já existiam (dedupe)


class FeedPagina(_Congelado):
    itens: tuple[NoticiaPublica, ...]
    pagina: int
    por_pagina: int
    total: int
    total_paginas: int
