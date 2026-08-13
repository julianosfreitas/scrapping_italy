"""A fila do Redis precisa respeitar o override dos testes.

Regressão: `fila.py` importava `get_redis` por valor, então o monkeypatch do
conftest não a alcançava e a suíte publicava edições no Redis REAL.
"""

from __future__ import annotations

import pytest
from app.core import cache, fila


def test_publicar_usa_o_get_redis_do_modulo_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Com o Redis desligado pelo override, publicar não estoura e devolve False."""
    monkeypatch.setattr(cache, "get_redis", lambda: None)
    assert fila.publicar_edicao({"data": "2026-08-13"}) is False


def test_tamanho_da_fila_sem_redis_e_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cache, "get_redis", lambda: None)
    assert fila.tamanho_fila() == 0
