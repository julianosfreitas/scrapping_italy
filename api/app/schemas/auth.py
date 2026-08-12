"""Schemas de autenticação — imutáveis (frozen=True)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

PADRAO_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class _Congelado(BaseModel):
    model_config = ConfigDict(frozen=True)


class LoginDados(_Congelado):
    email: str = Field(pattern=PADRAO_EMAIL, max_length=255)
    senha: str = Field(min_length=1, max_length=128)


class TokenResposta(_Congelado):
    access_token: str
    token_type: str = "bearer"
    estudante_id: int
