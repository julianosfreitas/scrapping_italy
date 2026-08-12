"""Bateria do calcular_gap — todos os cruzamentos requisito × documento."""

import dataclasses

import pytest
from app.models.documento import CategoriaDocumento as Cat
from app.models.documento import StatusDocumento as St
from app.services.comparativo import (
    DocumentoResumo,
    Gap,
    Requisito,
    calcular_gap,
    requisitos_por_categoria,
)

PASSAPORTE_REQ = Requisito(Cat.IDENTIDADE, "Passaporte válido")
IDIOMA_REQ = Requisito(Cat.IDIOMA, "Certificado B2 de inglês")
FINANCEIRO_REQ = Requisito(Cat.FINANCEIRO, "Comprovante de renda", obrigatorio=False)


def doc(categoria: Cat, tipo: str, status: St) -> DocumentoResumo:
    return DocumentoResumo(categoria, tipo, status)


# ── cruzamentos básicos ───────────────────────────────────


def test_documento_ok_atende_requisito() -> None:
    gap = calcular_gap((PASSAPORTE_REQ,), (doc(Cat.IDENTIDADE, "passaporte", St.OK),))
    assert [i.requisito for i in gap.atendidos] == [PASSAPORTE_REQ]
    assert gap.atendidos[0].documentos == ("passaporte",)
    assert gap.faltando == () and gap.vencendo == ()


def test_documento_vencendo_poe_requisito_em_alerta() -> None:
    gap = calcular_gap((PASSAPORTE_REQ,), (doc(Cat.IDENTIDADE, "passaporte", St.VENCENDO),))
    assert [i.requisito for i in gap.vencendo] == [PASSAPORTE_REQ]


def test_documento_vencido_nao_atende() -> None:
    gap = calcular_gap((PASSAPORTE_REQ,), (doc(Cat.IDENTIDADE, "passaporte", St.VENCIDO),))
    assert [i.requisito for i in gap.faltando] == [PASSAPORTE_REQ]
    assert gap.faltando[0].documentos == ()


def test_sem_documento_falta() -> None:
    gap = calcular_gap((PASSAPORTE_REQ,), ())
    assert [i.requisito for i in gap.faltando] == [PASSAPORTE_REQ]


def test_documento_de_outra_categoria_nao_conta() -> None:
    gap = calcular_gap((IDIOMA_REQ,), (doc(Cat.IDENTIDADE, "passaporte", St.OK),))
    assert [i.requisito for i in gap.faltando] == [IDIOMA_REQ]


# ── precedência e múltiplos documentos ───────────────────


def test_ok_vence_sobre_vencendo_na_mesma_categoria() -> None:
    documentos = (
        doc(Cat.IDIOMA, "toefl", St.VENCENDO),
        doc(Cat.IDIOMA, "ielts", St.OK),
    )
    gap = calcular_gap((IDIOMA_REQ,), documentos)
    assert gap.atendidos[0].documentos == ("ielts",)  # só os OK sustentam


def test_vencendo_vence_sobre_vencido() -> None:
    documentos = (
        doc(Cat.IDIOMA, "toefl", St.VENCIDO),
        doc(Cat.IDIOMA, "ielts", St.VENCENDO),
    )
    gap = calcular_gap((IDIOMA_REQ,), documentos)
    assert gap.vencendo[0].documentos == ("ielts",)


def test_um_documento_atende_varios_requisitos_da_categoria() -> None:
    reqs = (Requisito(Cat.ACADEMICO, "Histórico"), Requisito(Cat.ACADEMICO, "Diploma"))
    gap = calcular_gap(reqs, (doc(Cat.ACADEMICO, "historico", St.OK),))
    assert len(gap.atendidos) == 2


# ── particionamento completo e percentual ────────────────


def test_particao_cobre_todos_os_requisitos_sem_sobreposicao() -> None:
    reqs = (PASSAPORTE_REQ, IDIOMA_REQ, FINANCEIRO_REQ)
    documentos = (
        doc(Cat.IDENTIDADE, "passaporte", St.OK),
        doc(Cat.IDIOMA, "ielts", St.VENCENDO),
    )
    gap = calcular_gap(reqs, documentos)
    assert gap.total == 3
    assert {i.requisito for i in gap.atendidos} == {PASSAPORTE_REQ}
    assert {i.requisito for i in gap.vencendo} == {IDIOMA_REQ}
    assert {i.requisito for i in gap.faltando} == {FINANCEIRO_REQ}
    assert gap.percentual_pronto == 33


def test_curso_sem_requisitos_esta_100_pronto() -> None:
    gap = calcular_gap((), (doc(Cat.IDIOMA, "ielts", St.OK),))
    assert gap == Gap((), (), ())
    assert gap.percentual_pronto == 100


# ── propriedades funcionais ──────────────────────────────


def test_gap_e_imutavel() -> None:
    gap = calcular_gap((PASSAPORTE_REQ,), ())
    with pytest.raises(dataclasses.FrozenInstanceError):
        gap.atendidos = ()  # type: ignore[misc]


def test_determinismo() -> None:
    reqs = (PASSAPORTE_REQ, IDIOMA_REQ)
    documentos = (doc(Cat.IDENTIDADE, "rg", St.OK),)
    assert calcular_gap(reqs, documentos) == calcular_gap(reqs, documentos)


def test_nao_muta_entradas() -> None:
    reqs = (PASSAPORTE_REQ,)
    documentos = (doc(Cat.IDENTIDADE, "passaporte", St.OK),)
    calcular_gap(reqs, documentos)
    assert reqs == (PASSAPORTE_REQ,)
    assert documentos == (doc(Cat.IDENTIDADE, "passaporte", St.OK),)


# ── lru_cache dos requisitos por curso ───────────────────


def test_requisitos_por_categoria_usa_cache() -> None:
    requisitos_por_categoria.cache_clear()
    reqs = (PASSAPORTE_REQ, IDIOMA_REQ)
    primeira = requisitos_por_categoria(reqs)
    segunda = requisitos_por_categoria((PASSAPORTE_REQ, IDIOMA_REQ))  # tupla igual, novo objeto
    assert primeira is segunda  # mesmo resultado memoizado
    info = requisitos_por_categoria.cache_info()
    assert info.hits == 1 and info.misses == 1


def test_indice_de_requisitos_e_imutavel() -> None:
    indice = requisitos_por_categoria((PASSAPORTE_REQ,))
    with pytest.raises(TypeError):
        indice[Cat.IDIOMA] = ()  # type: ignore[index]
