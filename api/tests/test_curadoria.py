"""Testes da curadoria — funções puras, sem banco, sem Redis, sem relógio real.

Todo o tempo entra por parâmetro (`agora`), então nenhum teste precisa
congelar o relógio nem tolerar flutuação de fuso.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.services.curadoria import (
    TOPICOS,
    NoticiaResumo,
    agrupar_por_topico,
    curar,
    nas_ultimas_horas,
    ranquear,
)

AGORA = datetime(2026, 8, 13, 8, 30)


def noticia(
    titulo: str,
    categoria: str = "vistos",
    horas_atras: float = 1,
    fonte: str = "google_news",
) -> NoticiaResumo:
    momento = AGORA - timedelta(hours=horas_atras)
    return NoticiaResumo(
        titulo=titulo,
        url=f"https://exemplo.it/{titulo.lower().replace(' ', '-')}",
        fonte=fonte,
        categoria=categoria,
        coletada_em=momento,
        publicada_em=momento,
    )


# ── janela das últimas 24h ───────────────────────────────


def test_janela_mantem_noticia_recente_e_descarta_antiga() -> None:
    dentro = noticia("Novo visto", horas_atras=3)
    fora = noticia("Visto antigo", horas_atras=30)
    assert nas_ultimas_horas((dentro, fora), AGORA) == (dentro,)


def test_janela_descarta_noticia_com_data_no_futuro() -> None:
    """Fonte com data errada não pode furar a fila da edição."""
    futura = noticia("Ainda não aconteceu", horas_atras=-5)
    assert nas_ultimas_horas((futura,), AGORA) == ()


def test_janela_usa_coletada_em_quando_nao_ha_publicada_em() -> None:
    sem_publicacao = NoticiaResumo(
        titulo="Sem data de publicação",
        url="https://exemplo.it/sem-data",
        fonte="laziodisco",
        categoria="bolsas",
        coletada_em=AGORA - timedelta(hours=2),
        publicada_em=None,
    )
    assert nas_ultimas_horas((sem_publicacao,), AGORA) == (sem_publicacao,)


def test_janela_e_configuravel() -> None:
    antiga = noticia("Três dias atrás", horas_atras=72)
    assert nas_ultimas_horas((antiga,), AGORA) == ()
    assert nas_ultimas_horas((antiga,), AGORA, janela_horas=96) == (antiga,)


# ── ranking ──────────────────────────────────────────────


def test_ranquear_poe_a_mais_recente_primeiro() -> None:
    velha = noticia("Velha", horas_atras=20)
    nova = noticia("Nova", horas_atras=1)
    assert ranquear((velha, nova)) == (nova, velha)


def test_ranquear_nao_muta_a_entrada() -> None:
    entrada = (noticia("A", horas_atras=20), noticia("B", horas_atras=1))
    copia = tuple(entrada)
    ranquear(entrada)
    assert entrada == copia


# ── agrupamento (reduce) ─────────────────────────────────


def test_agrupar_por_topico_separa_categorias() -> None:
    visto = noticia("Visto novo", categoria="vistos")
    bolsa = noticia("Bolsa DSU", categoria="bolsas")
    agrupado = agrupar_por_topico((visto, bolsa))
    assert agrupado["vistos"] == (visto,)
    assert agrupado["bolsas"] == (bolsa,)


def test_agrupar_preserva_a_ordem_de_entrada_dentro_do_topico() -> None:
    primeira = noticia("Primeira", horas_atras=1)
    segunda = noticia("Segunda", horas_atras=2)
    assert agrupar_por_topico((primeira, segunda))["vistos"] == (primeira, segunda)


def test_agrupar_de_colecao_vazia_da_mapa_vazio() -> None:
    assert dict(agrupar_por_topico(())) == {}


# ── curar (a composição) ─────────────────────────────────


def test_curar_agrupa_nos_dez_topicos_na_ordem_da_secao_7() -> None:
    edicao = curar(
        (
            noticia("Mercado de trabalho", categoria="mercado"),
            noticia("Visto de estudo", categoria="vistos"),
            noticia("Bolsa regional", categoria="bolsas"),
        ),
        AGORA,
    )
    ordem_canonica = [chave for chave, _ in TOPICOS]
    chaves = [topico.chave for topico in edicao.topicos]
    assert chaves == sorted(chaves, key=ordem_canonica.index)
    assert chaves == ["vistos", "bolsas", "mercado"]


def test_curar_ignora_noticias_classificadas_como_geral() -> None:
    """"geral" não é um dos 10 tópicos da seção 7 — fica fora do e-mail."""
    edicao = curar((noticia("Notícia solta", categoria="geral"),), AGORA)
    assert edicao.topicos == ()
    assert edicao.total == 0


def test_curar_limita_itens_por_topico() -> None:
    muitas = tuple(noticia(f"Visto {i}", horas_atras=i + 1) for i in range(12))
    edicao = curar(muitas, AGORA, maximo_por_topico=3)
    assert len(edicao.topicos[0].itens) == 3
    assert edicao.total == 3


def test_curar_usa_o_rotulo_legivel_do_topico() -> None:
    edicao = curar((noticia("Vida na Itália", categoria="vida_na_italia"),), AGORA)
    assert edicao.topicos[0].rotulo == "Vida na Itália"


def test_curar_e_deterministica() -> None:
    """Mesma entrada + mesmo `agora` = mesma edição. Transparência referencial."""
    entrada = (
        noticia("Visto", categoria="vistos"),
        noticia("Bolsa", categoria="bolsas", horas_atras=5),
    )
    assert curar(entrada, AGORA) == curar(entrada, AGORA)


def test_curar_sem_noticias_da_edicao_vazia() -> None:
    edicao = curar((), AGORA)
    assert edicao.total == 0
    assert edicao.topicos == ()
    assert edicao.data_referencia == AGORA
