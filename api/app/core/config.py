"""Configuração da aplicação.

Settings imutáveis (dataclass congelada) montadas a partir do ambiente.
A leitura do arquivo .env é separada em uma função pura (`parse_env_linhas`),
que recebe linhas e devolve um dict — sem tocar em disco nem em os.environ —
o que a torna trivialmente testável.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# raiz do repositório: api/app/core/config.py -> sobe 3 níveis a partir de app/
_RAIZ_REPO = Path(__file__).resolve().parents[3]
_ARQUIVO_ENV = _RAIZ_REPO / ".env"


def parse_env_linhas(linhas: Iterable[str]) -> dict[str, str]:
    """Função pura: converte linhas no formato KEY=VALUE em um dict.

    Ignora comentários e linhas em branco; remove aspas envolvendo o valor.
    """
    pares = (
        linha.split("=", 1)
        for linha in map(str.strip, linhas)
        if linha and not linha.startswith("#") and "=" in linha
    )
    return {
        chave.strip(): valor.strip().strip("'\"").split("#", 1)[0].strip() for chave, valor in pares
    }


@dataclass(frozen=True)
class Settings:
    """Snapshot imutável da configuração — seguro para cachear e compartilhar."""

    app_env: str
    app_debug: bool
    mysql_host: str
    mysql_port: int
    mysql_database: str
    mysql_user: str
    mysql_password: str
    redis_host: str
    redis_port: int

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


def _ler_ambiente() -> dict[str, str]:
    """Única função com I/O deste módulo: .env (se existir) + os.environ.

    Variáveis reais de ambiente têm precedência sobre o arquivo.
    """
    do_arquivo = (
        parse_env_linhas(_ARQUIVO_ENV.read_text(encoding="utf-8").splitlines())
        if _ARQUIVO_ENV.exists()
        else {}
    )
    return {**do_arquivo, **os.environ}


def montar_settings(ambiente: dict[str, str]) -> Settings:
    """Função pura: dict de ambiente -> Settings (com defaults de dev)."""
    return Settings(
        app_env=ambiente.get("APP_ENV", "dev"),
        app_debug=ambiente.get("APP_DEBUG", "true").lower() == "true",
        mysql_host=ambiente.get("MYSQL_HOST", "localhost"),
        mysql_port=int(ambiente.get("MYSQL_PORT", "3306")),
        mysql_database=ambiente.get("MYSQL_DATABASE", "ponte_italia"),
        mysql_user=ambiente.get("MYSQL_USER", "ponte"),
        mysql_password=ambiente.get("MYSQL_PASSWORD", "ponte"),
        redis_host=ambiente.get("REDIS_HOST", "localhost"),
        redis_port=int(ambiente.get("REDIS_PORT", "6379")),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Settings da aplicação, calculadas uma única vez (lru_cache).

    O cache é seguro porque Settings é imutável (frozen=True).
    """
    return montar_settings(_ler_ambiente())
