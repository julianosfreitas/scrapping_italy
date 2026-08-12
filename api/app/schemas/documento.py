"""Schemas do cofre de documentos — imutáveis (frozen=True)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.documento import CategoriaDocumento, StatusDocumento


class _Congelado(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)


class DocumentoPublico(_Congelado):
    id: int
    estudante_id: int
    categoria: CategoriaDocumento
    tipo: str
    nome_arquivo: str
    data_validade: date | None
    status: StatusDocumento  # derivado por função pura, nunca lido do banco
    criado_em: datetime


class UrlAssinada(_Congelado):
    url: str
    expira_em_segundos: int
