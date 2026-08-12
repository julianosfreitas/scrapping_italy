"""Fixtures dos testes de rotas: SQLite em memória no lugar do MySQL.

O SQLite NÃO faz parte da aplicação — vive apenas aqui, para que os testes
de auth/CRUD/upload rodem rápido em qualquer máquina e no CI, sem Docker.
A troca acontece pelo override da dependência ``get_sessao``.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from app.core.config import get_settings
from app.core.db import get_sessao
from app.main import app
from app.models import Base
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def sessao_teste() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


@pytest.fixture()
def cliente(
    sessao_teste: sessionmaker[Session],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("JWT_SEGREDO", "segredo-somente-teste-com-32-bytes-ok")
    get_settings.cache_clear()

    def _sessao_de_teste() -> Iterator[Session]:
        with sessao_teste() as sessao:
            yield sessao

    app.dependency_overrides[get_sessao] = _sessao_de_teste
    with TestClient(app) as cliente_http:
        yield cliente_http
    app.dependency_overrides.clear()
    get_settings.cache_clear()
