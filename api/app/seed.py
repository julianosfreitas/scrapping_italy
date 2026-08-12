"""Seed idempotente dos estudantes iniciais (Sprint 1).

Uso: ``python -m app.seed`` (com o MySQL do docker-compose no ar e a
migration aplicada). Rodar mais de uma vez não duplica registros: a
verificação é por e-mail (chave única).

Os dados ficam em uma tupla de dataclasses congeladas — imutáveis por
construção — e a decisão "o que falta inserir" é uma função pura, separada
do I/O de banco.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import select

from app.models import Estudante

# Senha marcada como inutilizável até a Sprint 2 (auth com hash de verdade).
_SENHA_NAO_DEFINIDA = "!"


@dataclass(frozen=True)
class EstudanteSeed:
    nome: str
    email: str
    area_estudo: str
    bio: str
    nivel_italiano: str
    nivel_ingles: str


ESTUDANTES_INICIAIS: tuple[EstudanteSeed, ...] = (
    EstudanteSeed(
        nome="Juliano Freitas",
        email="julianof29contato@gmail.com",
        area_estudo="Ciência da Computação",
        bio="Rumo ao mestrado em Ciência da Computação na Itália.",
        nivel_italiano="A2",
        nivel_ingles="B2",
    ),
    EstudanteSeed(
        nome="Davi Neves",
        email="davi.neves@ponteitalia.example",
        area_estudo="Engenharia",
        bio="Planejando graduação/mestrado em Engenharia na Itália.",
        nivel_italiano="A1",
        nivel_ingles="B1",
    ),
)


def faltantes(
    candidatos: Iterable[EstudanteSeed], emails_existentes: frozenset[str]
) -> tuple[EstudanteSeed, ...]:
    """Função pura: filtra os candidatos cujo e-mail ainda não existe no banco."""
    return tuple(c for c in candidatos if c.email not in emails_existentes)


def executar_seed() -> int:
    """Insere os estudantes que faltam; devolve quantos foram criados."""
    from app.core.db import get_sessionmaker

    with get_sessionmaker()() as sessao:
        existentes = frozenset(sessao.scalars(select(Estudante.email)).all())
        novos = faltantes(ESTUDANTES_INICIAIS, existentes)
        sessao.add_all(
            Estudante(
                nome=n.nome,
                email=n.email,
                senha_hash=_SENHA_NAO_DEFINIDA,
                area_estudo=n.area_estudo,
                bio=n.bio,
                nivel_italiano=n.nivel_italiano,
                nivel_ingles=n.nivel_ingles,
            )
            for n in novos
        )
        sessao.commit()
        return len(novos)


if __name__ == "__main__":
    criados = executar_seed()
    print(f"Seed concluído: {criados} estudante(s) criado(s).")
