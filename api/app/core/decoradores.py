"""Decoradores funcionais da aplicação.

Dois exemplos centrais do relatório de Programação Funcional:

- ``@cronometrar`` — decorador simples com ``functools.wraps``, que mede o
  tempo de execução da função decorada sem alterar seu comportamento.
- ``@retry_backoff(...)`` — fábrica de decoradores: uma closure parametrizada
  que captura a configuração (tentativas, atraso base, fator) e devolve o
  decorador. A função de espera é injetável, o que torna o backoff testável
  sem dormir de verdade.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps

logger = logging.getLogger(__name__)


def cronometrar[**P, R](funcao: Callable[P, R]) -> Callable[P, R]:
    """Loga a duração da chamada, preservando assinatura e metadados (@wraps)."""

    @wraps(funcao)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        inicio = time.perf_counter()
        try:
            return funcao(*args, **kwargs)
        finally:
            duracao_ms = (time.perf_counter() - inicio) * 1000
            logger.info("%s levou %.1f ms", funcao.__qualname__, duracao_ms)

    return wrapper


def retry_backoff[**P, R](
    tentativas: int = 3,
    atraso_base: float = 0.5,
    fator: float = 2.0,
    excecoes: tuple[type[BaseException], ...] = (Exception,),
    dormir: Callable[[float], None] = time.sleep,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Fábrica de decoradores de retry com backoff exponencial.

    A closure ``decorador`` captura os parâmetros desta chamada; cada função
    decorada ganha sua própria política de retry sem estado global. A espera
    entre tentativas é ``atraso_base * fator**n`` (n = nº de falhas anteriores).
    ``dormir`` é injetável: nos testes, passa-se uma função que apenas registra
    os atrasos, sem bloquear.
    """
    if tentativas < 1:
        raise ValueError("tentativas deve ser >= 1")

    def decorador(funcao: Callable[P, R]) -> Callable[P, R]:
        @wraps(funcao)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for tentativa in range(tentativas):
                try:
                    return funcao(*args, **kwargs)
                except excecoes as erro:
                    if tentativa == tentativas - 1:
                        raise
                    atraso = atraso_base * fator**tentativa
                    logger.warning(
                        "%s falhou (%s) — tentativa %d/%d, aguardando %.2fs",
                        funcao.__qualname__,
                        erro,
                        tentativa + 1,
                        tentativas,
                        atraso,
                    )
                    dormir(atraso)
            raise AssertionError("inalcançável")  # pragma: no cover

        return wrapper

    return decorador
