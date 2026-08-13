"""Fila Redis da newsletter — ponte entre a curadoria (Python) e o worker (.NET).

Uma lista Redis simples: o Python faz `LPUSH` da edição já serializada e o
worker .NET faz `BRPOP` do outro lado (FIFO). O mesmo fallback gracioso do
cache vale aqui: sem Redis, `publicar_edicao` devolve False e quem chamou
decide — a edição continua salva no banco e visível em `/newsletter/{data}`.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis

# importado como MÓDULO de propósito: `from ... import get_redis` congelaria a
# referência no import e o override dos testes (que troca cache.get_redis)
# não teria efeito aqui — a fila acabaria falando com o Redis de verdade.
from app.core import cache

logger = logging.getLogger(__name__)

FILA_NEWSLETTER = "newsletter:fila"


def publicar_edicao(payload: Any) -> bool:
    """Enfileira a edição para o worker. Devolve False se o Redis não respondeu."""
    cliente = cache.get_redis()
    if cliente is None:
        logger.warning("Redis indisponível — edição não enfileirada")
        return False
    try:
        cliente.lpush(FILA_NEWSLETTER, json.dumps(payload, ensure_ascii=False))
        return True
    except redis.RedisError as erro:
        logger.warning("falha ao enfileirar edição: %s", erro)
        return False


def tamanho_fila() -> int:
    """Quantas edições aguardam o worker (usado no smoke test da demo)."""
    cliente = cache.get_redis()
    if cliente is None:
        return 0
    try:
        return int(cliente.llen(FILA_NEWSLETTER))
    except redis.RedisError:
        return 0
