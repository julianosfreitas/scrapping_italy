"""Tradução dos textos da newsletter — camada de I/O, isolada de propósito.

As fontes publicam em italiano e inglês; o e-mail sai em português. Traduzir
é I/O de rede, então mora aqui e não em `services/`: a curadoria continua
pura e o texto já chega traduzido para ela.

Três cuidados, porque o tradutor é um serviço externo e não oficial:

* **falha nunca derruba a edição** — se o serviço cair, devolve o original;
* **`lru_cache`** evita repetir a mesma chamada (a mesma notícia aparece em
  edições seguidas enquanto estiver na janela);
* **timeout curto** — a curadoria roda às 08h30 e não pode ficar pendurada.
"""

from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

IDIOMA_DESTINO = "pt"
LIMITE_CARACTERES = 4800  # limite prático do serviço por chamada


@lru_cache(maxsize=512)
def traduzir(texto: str, destino: str = IDIOMA_DESTINO) -> str:
    """Traduz para `destino`; em qualquer falha, devolve o texto original.

    O cache é seguro porque a função é determinística do ponto de vista de
    quem chama: mesma entrada, mesma saída dentro do processo — e o pior caso
    de um erro é devolver o original, nunca uma exceção.
    """
    limpo = texto.strip()
    if not limpo:
        return texto
    try:
        from deep_translator import GoogleTranslator

        traduzido = GoogleTranslator(source="auto", target=destino).translate(
            limpo[:LIMITE_CARACTERES]
        )
        return traduzido or texto
    except Exception as erro:  # noqa: BLE001 — tradução é acessório, não pode quebrar
        logger.warning("tradução indisponível (%s) — mantendo o original", erro)
        return texto


def traduzir_opcional(texto: str | None, destino: str = IDIOMA_DESTINO) -> str | None:
    """Versão que aceita None, para os campos opcionais da notícia."""
    return None if texto is None else traduzir(texto, destino)
