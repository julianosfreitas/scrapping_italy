"""Curadoria da newsletter diária — função-pipeline pura (seção 7 do README).

Módulo 100% puro: nada aqui lê banco, Redis ou relógio. O router busca as
notícias, converte para `NoticiaResumo` (congelada) e delega; o horário entra
como parâmetro `agora`, o mesmo truque de `calcular_status` — assim a edição
das 08h30 é reproduzível em teste sem congelar o relógio do sistema.

    recentes ── filter(janela) ── sorted(relevância) ── reduce(agrupar) → Edição
                                                             └ 10 tópicos

O agrupamento reaproveita o classificador da Sprint 4: `categoria` já vem
decidida por `scraper.pipeline.classificar`, então aqui só resta dobrar a
coleção nos tópicos da seção 7 — sem reclassificar nada.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import reduce
from types import MappingProxyType

# os 10 tópicos essenciais da seção 7, na ordem em que saem no e-mail
TOPICOS: tuple[tuple[str, str], ...] = (
    ("vistos", "Vistos"),
    ("prazos", "Prazos"),
    ("bolsas", "Bolsas"),
    ("idioma", "Idioma"),
    ("moradia", "Moradia"),
    ("financas", "Finanças"),
    ("documentacao", "Documentação"),
    ("admissoes", "Admissões"),
    ("vida_na_italia", "Vida na Itália"),
    ("mercado", "Mercado para estrangeiros"),
)

JANELA_HORAS = 24
MAXIMO_POR_TOPICO = 5


@dataclass(frozen=True)
class NoticiaResumo:
    """Snapshot imutável de uma notícia — o que a curadoria precisa saber."""

    titulo: str
    url: str
    fonte: str
    categoria: str
    coletada_em: datetime
    resumo: str | None = None
    publicada_em: datetime | None = None


@dataclass(frozen=True)
class Topico:
    chave: str
    rotulo: str
    itens: tuple[NoticiaResumo, ...]


@dataclass(frozen=True)
class Edicao:
    """A edição do dia, pronta para virar JSON na fila e página no arquivo."""

    data_referencia: datetime
    total: int
    topicos: tuple[Topico, ...]


# ── etapas (todas puras) ─────────────────────────────────


def momento_de(noticia: NoticiaResumo) -> datetime:
    """Instante que representa a notícia: a publicação quando existe, senão a coleta."""
    return noticia.publicada_em or noticia.coletada_em


def nas_ultimas_horas(
    noticias: tuple[NoticiaResumo, ...], agora: datetime, janela_horas: int = JANELA_HORAS
) -> tuple[NoticiaResumo, ...]:
    """`filter` com o relógio INJETADO — nada de datetime.now() aqui dentro."""
    corte = agora - timedelta(hours=janela_horas)
    return tuple(filter(lambda n: corte <= momento_de(n) <= agora, noticias))


def ranquear(noticias: tuple[NoticiaResumo, ...]) -> tuple[NoticiaResumo, ...]:
    """Mais recente primeiro. `sorted` devolve lista nova — a entrada não é tocada."""
    return tuple(sorted(noticias, key=momento_de, reverse=True))


def _acumular_topico(
    acc: dict[str, tuple[NoticiaResumo, ...]], noticia: NoticiaResumo
) -> dict[str, tuple[NoticiaResumo, ...]]:
    """Um passo do reduce: NOVO mapa com a notícia anexada ao seu tópico."""
    return {**acc, noticia.categoria: (*acc.get(noticia.categoria, ()), noticia)}


def agrupar_por_topico(
    noticias: tuple[NoticiaResumo, ...],
) -> Mapping[str, tuple[NoticiaResumo, ...]]:
    """conceito 8: `reduce` dobra a coleção num índice tópico → notícias.

    Mesmo idioma de `scraper.pipeline.estatisticas`, mas acumulando tuplas em
    vez de contadores: o acumulador nunca é mutado (cada passo devolve um dict
    novo) e o resultado sai imutável. Como a entrada já vem ranqueada e o
    `reduce` preserva a ordem de iteração, cada tópico herda o ranking.
    """
    vazio: dict[str, tuple[NoticiaResumo, ...]] = {}
    agrupado: dict[str, tuple[NoticiaResumo, ...]] = reduce(_acumular_topico, noticias, vazio)
    return MappingProxyType(agrupado)


def curar(
    noticias: tuple[NoticiaResumo, ...],
    agora: datetime,
    janela_horas: int = JANELA_HORAS,
    maximo_por_topico: int = MAXIMO_POR_TOPICO,
) -> Edicao:
    """A composição inteira: janela → ranking → agrupamento nos 10 tópicos.

    Função pura: mesmas notícias + mesmo `agora` = mesma edição, sempre.
    Tópicos vazios não entram (o `if` da comprehension descarta), e notícias
    fora dos 10 tópicos — as classificadas como "geral" — ficam de fora do
    e-mail por definição da seção 7.
    """
    por_topico = agrupar_por_topico(ranquear(nas_ultimas_horas(noticias, agora, janela_horas)))
    topicos = tuple(
        Topico(chave=chave, rotulo=rotulo, itens=itens[:maximo_por_topico])
        for chave, rotulo in TOPICOS
        if (itens := por_topico.get(chave, ()))
    )
    return Edicao(
        data_referencia=agora,
        total=sum(len(topico.itens) for topico in topicos),
        topicos=topicos,
    )
