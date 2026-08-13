"""Modelos da newsletter (seção 5 do README + arquivo de edições).

`inscricoes_news` guarda quem recebe o e-mail diário — o cancelamento é um
soft delete (`ativo=False`), para que reinscrever não esbarre na unicidade
do e-mail nem apague o histórico.

`edicoes_newsletter` é o ARQUIVO: uma linha por dia (`data` única, o que
torna a curadoria idempotente — rodar duas vezes no mesmo dia atualiza a
edição em vez de duplicar) com o JSON já curado. `enviada_em` fica nulo até
o worker .NET confirmar o disparo.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InscricaoNewsletter(Base):
    __tablename__ = "inscricoes_news"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    ativo: Mapped[bool] = mapped_column(default=True, server_default=true())
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class EdicaoNewsletter(Base):
    __tablename__ = "edicoes_newsletter"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column(Date, unique=True, index=True)
    # JSON é portável MySQL/SQLite — o mesmo payload que vai para a fila do Redis
    conteudo: Mapped[dict[str, Any]] = mapped_column(JSON)
    enviada_em: Mapped[datetime | None] = mapped_column(DateTime)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
