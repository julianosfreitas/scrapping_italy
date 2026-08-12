"""Pipeline funcional de limpeza de notícias — o coração da Sprint 4.

Cada etapa é uma função pura sobre tuplas imutáveis; `processar` é apenas a
COMPOSIÇÃO delas. Nenhuma etapa conhece rede, banco ou relógio — os testes
rodam inteiramente em memória.

    brutas ─ map(normalizar) ─ filter(eh_valida) ─ dedupe ─ map(classificar) → limpas
                                                                 └→ reduce(estatísticas)
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import replace
from functools import reduce
from types import MappingProxyType

from scraper.sources.base import NoticiaColetada

# palavras-chave → um dos 10 tópicos da seção 7 do README
_CATEGORIAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("vistos", ("visto", "visa", "permesso di soggiorno", "consolato", "consulado")),
    ("bolsas", ("bolsa", "borsa", "borse", "scholarship", "grant", "bando", "dsu")),
    ("prazos", ("prazo", "scadenza", "deadline", "scade", "graduatoria")),
    ("idioma", ("italiano b", "ielts", "toefl", "cils", "celi", "language requirement")),
    ("moradia", ("moradia", "alloggio", "housing", "affitto", "residenza", "dormitório")),
    ("financas", ("tasse", "tuition", "isee", "taxa", "custo", "fees")),
    ("documentacao", ("dichiarazione di valore", "apostila", "apostille", "traduzione", "cimea")),
    ("admissoes", ("ammissione", "admission", "enrollment", "immatricolazione", "iscrizione")),
    ("mercado", ("lavoro", "job", "stage", "tirocinio", "internship", "carreira")),
    ("vida_na_italia", ("vita in italia", "living in italy", "erasmus", "campus life")),
)

_TAGS_HTML = re.compile(r"<[^>]+>")
_ESPACOS = re.compile(r"\s+")
_TAMANHO_MAXIMO_RESUMO = 500


# ── etapas (todas puras) ─────────────────────────────────


def limpar_texto(texto: str | None) -> str | None:
    """Remove tags HTML e colapsa espaços — comprehension-friendly, sem mutação."""
    if texto is None:
        return None
    limpo = _ESPACOS.sub(" ", _TAGS_HTML.sub(" ", texto)).strip()
    return limpo[:_TAMANHO_MAXIMO_RESUMO] or None


def normalizar(noticia: NoticiaColetada) -> NoticiaColetada:
    """Devolve uma NOVA notícia normalizada (dataclasses.replace, sem mutar)."""
    return replace(
        noticia,
        titulo=(limpar_texto(noticia.titulo) or "")[:300],
        resumo=limpar_texto(noticia.resumo),
        url=noticia.url.strip()[:500],
    )


def eh_valida(noticia: NoticiaColetada) -> bool:
    return bool(noticia.titulo) and noticia.url.startswith("http")


def classificar(noticia: NoticiaColetada) -> NoticiaColetada:
    """Atribui um dos 10 tópicos da seção 7 por palavras-chave; senão 'geral'."""
    texto = f"{noticia.titulo} {noticia.resumo or ''}".lower()
    categoria = next(
        (nome for nome, palavras in _CATEGORIAS if any(p in texto for p in palavras)),
        "geral",
    )
    return replace(noticia, categoria=categoria)


def dedupe_por_url(noticias: tuple[NoticiaColetada, ...]) -> tuple[NoticiaColetada, ...]:
    """Mantém a primeira ocorrência de cada URL (dict preserva ordem de inserção)."""
    return tuple({noticia.url: noticia for noticia in reversed(noticias)}.values())[::-1]


def filtrar_por_categoria(
    noticias: tuple[NoticiaColetada, ...], categoria: str
) -> tuple[NoticiaColetada, ...]:
    """conceito 7: `filter` com predicado — nenhuma lista intermediária mutada."""
    return tuple(filter(lambda n: n.categoria == categoria, noticias))


def processar(brutas: tuple[NoticiaColetada, ...]) -> tuple[NoticiaColetada, ...]:
    """A composição inteira: map → filter → dedupe → map.

    conceito 7 (map/filter aplicados a funções nomeadas) e conceito 4 (cada
    etapa é uma função passada como valor para a próxima).
    """
    normalizadas = map(normalizar, brutas)
    validas = filter(eh_valida, normalizadas)
    unicas = dedupe_por_url(tuple(validas))
    return tuple(map(classificar, unicas))


# ── estatísticas da coleta (functools.reduce) ────────────


def _acumular(acc: Mapping[str, int], noticia: NoticiaColetada) -> Mapping[str, int]:
    """Um passo do reduce: devolve um NOVO mapa com os contadores incrementados."""
    fonte = f"fonte:{noticia.fonte}"
    categoria = f"categoria:{noticia.categoria}"
    return {
        **acc,
        "total": acc.get("total", 0) + 1,
        fonte: acc.get(fonte, 0) + 1,
        categoria: acc.get(categoria, 0) + 1,
    }


def estatisticas(noticias: tuple[NoticiaColetada, ...]) -> Mapping[str, int]:
    """conceito 8: reduce dobra a coleção num único mapa de contadores.

    O acumulador nunca é mutado — cada passo devolve um dict novo — e o
    resultado sai embrulhado em MappingProxyType (imutável para quem recebe).
    """
    vazio: Mapping[str, int] = {}
    resultado: Mapping[str, int] = reduce(_acumular, noticias, vazio)
    return MappingProxyType(dict(resultado))
