"""Regras de negócio do cofre de documentos — só funções puras, zero I/O.

Nenhuma função aqui lê banco, disco ou relógio: tudo que varia (inclusive a
data de hoje) entra como parâmetro. Os routers fazem o I/O e delegam o
cálculo para cá.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable
from datetime import date, timedelta

from app.models.documento import CategoriaDocumento, StatusDocumento

EXTENSOES_PERMITIDAS: frozenset[str] = frozenset({"pdf", "jpg", "jpeg", "png"})
JANELA_VENCENDO_DIAS = 30


def calcular_status(
    data_validade: date | None,
    data_atual: date,
    janela_vencendo_dias: int = JANELA_VENCENDO_DIAS,
) -> StatusDocumento:
    """Deriva o status do documento a partir da validade e da data de referência.

    Função pura com relógio injetado: mesma entrada, mesma saída, sempre —
    transparência referencial de verdade (uma chamada pode ser substituída
    pelo seu resultado sem mudar o programa).

    Regras:
    - sem data de validade -> OK (documento não expira);
    - validade anterior à data atual -> VENCIDO;
    - vence hoje ou dentro da janela (30 dias) -> VENCENDO;
    - depois da janela -> OK.
    """
    if data_validade is None:
        return StatusDocumento.OK
    if data_validade < data_atual:
        return StatusDocumento.VENCIDO
    if data_validade <= data_atual + timedelta(days=janela_vencendo_dias):
        return StatusDocumento.VENCENDO
    return StatusDocumento.OK


def extensao_de(nome_arquivo: str) -> str:
    """'passaporte.PDF' -> 'pdf'; sem extensão -> ''."""
    _, ponto, extensao = nome_arquivo.rpartition(".")
    return extensao.lower() if ponto else ""


def _transliterar(texto: str) -> str:
    """'Histórico (2ª)' -> 'historico-2a': ascii minúsculo, resto vira hífen."""
    sem_acentos = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").lower()
    )
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9_-]+", "-", sem_acentos)).strip("-")


def sanitizar_nome_arquivo(nome: str) -> str:
    """Reduz um nome vindo do cliente a algo seguro para o sistema de arquivos.

    Remove diretórios (path traversal) e translitera radical e extensão
    separadamente — o ponto da extensão é preservado.
    """
    base = nome.replace("\\", "/").rsplit("/", 1)[-1]
    radical, ponto, extensao = base.rpartition(".")
    if not ponto:
        radical, extensao = base, ""
    radical_limpo = _transliterar(radical)[:70] or "arquivo"
    extensao_limpa = _transliterar(extensao)
    return f"{radical_limpo}.{extensao_limpa}" if extensao_limpa else radical_limpo


def validar_upload(nome_arquivo: str, tamanho_bytes: int, max_bytes: int) -> str | None:
    """Devolve a mensagem de erro, ou None se o upload é válido."""
    extensao = extensao_de(nome_arquivo)
    if extensao not in EXTENSOES_PERMITIDAS:
        permitidas = ", ".join(sorted(EXTENSOES_PERMITIDAS))
        return f"Extensão '.{extensao or '?'}' não permitida (aceitas: {permitidas})"
    if tamanho_bytes <= 0:
        return "Arquivo vazio"
    if tamanho_bytes > max_bytes:
        return f"Arquivo excede o limite de {max_bytes // (1024 * 1024)} MB"
    return None


def agrupar_por_categoria[T](
    itens: Iterable[T], categoria_de: Callable[[T], CategoriaDocumento]
) -> dict[CategoriaDocumento, tuple[T, ...]]:
    """Agrupa itens por categoria preservando a ordem das categorias do enum.

    HOF: recebe a função `categoria_de` que extrai a categoria de cada item —
    o agrupamento não conhece o tipo concreto (ORM, schema, dict...).
    """
    materializados = tuple(itens)
    return {
        categoria: agrupados
        for categoria in CategoriaDocumento
        if (agrupados := tuple(i for i in materializados if categoria_de(i) == categoria))
    }
