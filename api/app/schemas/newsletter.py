"""Schemas da newsletter — imutáveis (frozen=True).

`EdicaoPublica` é o CONTRATO entre três partes: a curadoria em Python que a
monta, a fila do Redis que a transporta e o worker .NET que a renderiza. Por
isso ela é serializada com `model_dump(mode="json")` — datas viram strings
ISO-8601, que o `System.Text.Json` lê sem conversor customizado.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.estudante import PADRAO_EMAIL


class _Congelado(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)


class InscricaoCriar(_Congelado):
    email: str = Field(pattern=PADRAO_EMAIL, max_length=255)

    @field_validator("email", mode="before")
    @classmethod
    def _normalizar(cls, valor: object) -> object:
        """Normaliza ANTES do regex: espaço e caixa não são erro do usuário.

        O e-mail é a chave única da inscrição, então normalizar aqui garante
        que "Davi@Teste.COM " e "davi@teste.com" sejam a MESMA linha.
        """
        return valor.strip().lower() if isinstance(valor, str) else valor


class InscricaoPublica(_Congelado):
    id: int
    email: str
    ativo: bool
    criado_em: datetime


class ItemEdicao(_Congelado):
    titulo: str
    url: str
    fonte: str
    resumo: str | None = None
    publicada_em: datetime | None = None


class TopicoEdicao(_Congelado):
    chave: str
    rotulo: str
    itens: tuple[ItemEdicao, ...]


class EdicaoPublica(_Congelado):
    data: date
    gerada_em: datetime
    total: int
    topicos: tuple[TopicoEdicao, ...]


class EdicaoArquivada(_Congelado):
    """Uma linha do arquivo de edições (`/newsletter/{data}`)."""

    data: date
    enviada_em: datetime | None
    total: int
