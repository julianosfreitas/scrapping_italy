"""Regras puras de cursos: ordenação por prazo e proximidade de prazo."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date, timedelta

JANELA_PRAZO_PROXIMO_DIAS = 60


def ordenar_por_prazo[T](
    cursos: Iterable[T], prazo_de: Callable[[T], date | None]
) -> tuple[T, ...]:
    """Cursos com prazo mais próximo primeiro; sem prazo vão para o fim.

    HOF + lambda: `sorted` recebe a chave como função. A tupla `(sem_prazo,
    prazo)` ordena False < True, então quem tem prazo vem antes.
    """
    return tuple(sorted(cursos, key=lambda c: (prazo_de(c) is None, prazo_de(c) or date.max)))


def prazo_proximo(
    prazo: date | None, data_atual: date, janela_dias: int = JANELA_PRAZO_PROXIMO_DIAS
) -> bool:
    """True se o prazo está dentro da janela de alerta (e ainda não passou)."""
    return prazo is not None and data_atual <= prazo <= data_atual + timedelta(days=janela_dias)
