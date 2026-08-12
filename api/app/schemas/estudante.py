"""Schemas de estudantes — todos imutáveis (frozen=True)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

PADRAO_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class _Congelado(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)


class EstudanteCriar(_Congelado):
    nome: str = Field(min_length=2, max_length=120)
    email: str = Field(pattern=PADRAO_EMAIL, max_length=255)
    senha: str = Field(min_length=8, max_length=128)
    area_estudo: str | None = Field(default=None, max_length=120)
    bio: str | None = None
    nivel_italiano: str | None = Field(default=None, max_length=10)
    nivel_ingles: str | None = Field(default=None, max_length=10)


class EstudanteEditar(_Congelado):
    """Edição parcial: só os campos enviados são alterados."""

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    foto_url: str | None = Field(default=None, max_length=500)
    area_estudo: str | None = Field(default=None, max_length=120)
    bio: str | None = None
    nivel_italiano: str | None = Field(default=None, max_length=10)
    nivel_ingles: str | None = Field(default=None, max_length=10)


class EstudantePublico(_Congelado):
    id: int
    nome: str
    email: str = Field(pattern=PADRAO_EMAIL, max_length=255)
    foto_url: str | None
    area_estudo: str | None
    bio: str | None
    nivel_italiano: str | None
    nivel_ingles: str | None
    criado_em: datetime
