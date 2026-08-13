"""Pipeline de limpeza: todas as etapas puras, sem rede."""

import dataclasses
from types import MappingProxyType

import pytest

from scraper.pipeline import (
    classificar,
    dedupe_por_url,
    eh_valida,
    estatisticas,
    filtrar_por_categoria,
    limpar_texto,
    normalizar,
    processar,
)
from scraper.sources.base import NoticiaColetada


def noticia(**campos: object) -> NoticiaColetada:
    base: dict[str, object] = {
        "titulo": "Título",
        "url": "https://exemplo.it/a",
        "fonte": "google_news",
    }
    return NoticiaColetada(**{**base, **campos})  # type: ignore[arg-type]


# ── normalização (comprehensions/replace) ────────────────


def test_limpar_texto_remove_html_e_espacos() -> None:
    assert limpar_texto("  <b>Bando</b>\n\n  DSU <a href='x'>2026</a> ") == "Bando DSU 2026"
    assert limpar_texto(None) is None
    assert limpar_texto("<p></p>") is None


def test_limpar_texto_decodifica_entidades_html() -> None:
    """O Google News manda &nbsp; e &amp; no resumo; sem decodificar, vaza na tela."""
    assert limpar_texto("Visto&nbsp;&nbsp;de estudo") == "Visto de estudo"
    assert limpar_texto("Bolsas &amp; prazos") == "Bolsas & prazos"
    assert limpar_texto("aspas &quot;duplas&quot;") == 'aspas "duplas"'


def test_limpar_texto_nao_ressuscita_tag_escapada() -> None:
    """`&lt;b&gt;` é texto literal, não marcação: precisa sobreviver à limpeza."""
    assert limpar_texto("use &lt;b&gt; para negrito") == "use <b> para negrito"


def test_normalizar_devolve_nova_noticia_sem_mutar_a_original() -> None:
    original = noticia(titulo=" <i>Visto</i> studio ", resumo="<p>Novas  regras</p>")
    normalizada = normalizar(original)
    assert normalizada.titulo == "Visto studio"
    assert normalizada.resumo == "Novas regras"
    assert original.titulo == " <i>Visto</i> studio "  # imutável: original intacta


def test_eh_valida() -> None:
    assert eh_valida(noticia())
    assert not eh_valida(noticia(titulo=""))
    assert not eh_valida(noticia(url="ftp://x"))


# ── classificação ────────────────────────────────────────


def test_classificar_por_palavra_chave() -> None:
    assert classificar(noticia(titulo="Nuovo bando borse di studio DSU")).categoria == "bolsas"
    assert classificar(noticia(titulo="Student visa: new rules")).categoria == "vistos"
    assert classificar(noticia(titulo="Scadenza immatricolazioni")).categoria == "prazos"
    assert classificar(noticia(titulo="Meteo a Roma")).categoria == "geral"


# ── dedupe e filtro (map/filter) ─────────────────────────


def test_dedupe_mantem_primeira_ocorrencia() -> None:
    a1 = noticia(url="https://a.it", titulo="Primeira")
    a2 = noticia(url="https://a.it", titulo="Repetida")
    b = noticia(url="https://b.it")
    assert dedupe_por_url((a1, a2, b)) == (a1, b)


def test_filtrar_por_categoria() -> None:
    bolsa = classificar(noticia(url="https://a.it", titulo="Bando borse"))
    visto = classificar(noticia(url="https://b.it", titulo="Visa update"))
    assert filtrar_por_categoria((bolsa, visto), "bolsas") == (bolsa,)


# ── composição completa ──────────────────────────────────


def test_processar_compoe_todas_as_etapas() -> None:
    brutas = (
        noticia(titulo=" <b>Bando</b> DSU ", url="https://a.it "),
        noticia(titulo="Bando DSU (duplicada)", url="https://a.it"),
        noticia(titulo="", url="https://vazia.it"),
        noticia(titulo="Student visa Italy", url="https://b.it"),
    )
    limpas = processar(brutas)
    assert [n.url for n in limpas] == ["https://a.it", "https://b.it"]
    assert [n.categoria for n in limpas] == ["bolsas", "vistos"]
    assert limpas[0].titulo == "Bando DSU"


def test_processar_e_deterministico_e_nao_muta() -> None:
    brutas = (noticia(), noticia(url="https://b.it"))
    assert processar(brutas) == processar(brutas)
    assert brutas[0].titulo == "Título"


# ── reduce ───────────────────────────────────────────────


def test_estatisticas_com_reduce() -> None:
    coletadas = processar(
        (
            noticia(titulo="Bando borse", url="https://a.it", fonte="laziodisco"),
            noticia(titulo="Borsa di studio", url="https://b.it", fonte="laziodisco"),
            noticia(titulo="Student visa", url="https://c.it", fonte="google_news"),
        )
    )
    numeros = estatisticas(coletadas)
    assert numeros["total"] == 3
    assert numeros["fonte:laziodisco"] == 2
    assert numeros["fonte:google_news"] == 1
    assert numeros["categoria:bolsas"] == 2
    assert numeros["categoria:vistos"] == 1


def test_estatisticas_vazia_e_imutavel() -> None:
    numeros = estatisticas(())
    assert dict(numeros) == {}
    assert isinstance(numeros, MappingProxyType)
    with pytest.raises(TypeError):
        numeros["total"] = 1  # type: ignore[index]


def test_noticia_coletada_e_imutavel() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        noticia().titulo = "outro"  # type: ignore[misc]
