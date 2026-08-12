"""Cache Redis do feed do Radar — com fallback gracioso.

Se o Redis estiver fora do ar (ou não configurado), a aplicação segue sem
cache: nenhuma rota depende dele para funcionar, apenas para acelerar.
"""

from __future__ import annotations

import contextlib
import json
import logging
from functools import lru_cache
from typing import Any

import redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

TTL_FEED_SEGUNDOS = 300
PREFIXO_FEED = "radar:feed:"


@lru_cache(maxsize=1)
def get_redis() -> redis.Redis | None:
    settings = get_settings()
    try:
        cliente = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        cliente.ping()
        return cliente
    except redis.RedisError as erro:
        logger.warning("Redis indisponível (%s) — seguindo sem cache", erro)
        return None


def ler_feed_cacheado(chave: str) -> Any | None:
    cliente = get_redis()
    if cliente is None:
        return None
    try:
        bruto = cliente.get(f"{PREFIXO_FEED}{chave}")
        return json.loads(bruto) if isinstance(bruto, str) else None
    except redis.RedisError:
        return None


def gravar_feed_cacheado(chave: str, valor: Any) -> None:
    cliente = get_redis()
    if cliente is None:
        return
    with contextlib.suppress(redis.RedisError):
        cliente.setex(f"{PREFIXO_FEED}{chave}", TTL_FEED_SEGUNDOS, json.dumps(valor))


def invalidar_feed() -> int:
    """Apaga todas as páginas cacheadas do feed (chamado após cada coleta)."""
    cliente = get_redis()
    if cliente is None:
        return 0
    try:
        chaves = list(cliente.scan_iter(f"{PREFIXO_FEED}*"))
        return int(cliente.delete(*chaves)) if chaves else 0
    except redis.RedisError:
        return 0
