"""Fonte Universitaly (universitaly.it) — seção 6 do README.

O parser desta fonte é o parser genérico ESPECIALIZADO com
``functools.partial``: nenhuma subclasse, nenhuma cópia de código — só a
configuração de seletores aplicada parcialmente.

Nota operacional: o site está atrás de AWS WAF com challenge JavaScript
(HTTP 202). A coleta ao vivo com Playwright entra na Sprint 4; até lá o
parser é exercitado com fixtures de HTML e a ingestão manual/via fixture.
"""

from __future__ import annotations

from functools import partial

from scraper.sources.base import SeletoresFonte, parse_universidades

URL_BASE = "https://www.universitaly.it"
URLS_COLETA = (f"{URL_BASE}/cerca-corsi",)

SELETORES_UNIVERSITALY = SeletoresFonte(
    universidade="div.ateneo-card",
    nome="h3.ateneo-nome",
    cidade="span.ateneo-citta",
    site="a.ateneo-sito",
    curso="li.corso-item",
    curso_nome="span.corso-nome",
    curso_grau="span.corso-tipo",
    curso_idioma="span.corso-lingua",
    curso_prazo="span.corso-scadenza",
    grau_mapa=(
        ("laurea magistrale", "mestrado"),
        ("laurea triennale", "grad"),
        ("laurea", "grad"),  # fallback: "Corso di Laurea" genérico
    ),
)

# conceito 11: especialização por aplicação parcial — o parser da fonte É o
# parser genérico com os argumentos de configuração pré-preenchidos.
parser_universitaly = partial(
    parse_universidades, fonte="universitaly", seletores=SELETORES_UNIVERSITALY
)
