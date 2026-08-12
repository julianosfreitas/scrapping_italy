"""Modelo da tabela `noticias` (seção 5 do README).

A URL é única: é ela que garante o dedupe entre coletas — a mesma notícia
vinda duas vezes (ou por duas fontes que apontam para o mesmo link) só entra
uma vez. `categoria` é um dos 10 tópicos da seção 7 (ou "geral" quando o
classificador não reconhece nenhum).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Noticia(Base):
    __tablename__ = "noticias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(300))
    resumo: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    fonte: Mapped[str] = mapped_column(String(40), index=True)
    categoria: Mapped[str] = mapped_column(String(40), index=True)
    idioma: Mapped[str | None] = mapped_column(String(10))
    publicada_em: Mapped[datetime | None] = mapped_column(DateTime)
    coletada_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
