"""FAQ: árvore aninhada na API e a página /ajuda com busca e navegação."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from app.models import ItemFaq
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture()
def com_faq(cliente: TestClient, sessao_teste: sessionmaker[Session]) -> Iterator[TestClient]:
    """Árvore de 3 níveis: Vistos > Estudo > (2 perguntas) + 1 pergunta na raiz."""
    with sessao_teste() as sessao:
        raiz = ItemFaq(nome="Vistos", ordem=0)
        sessao.add(raiz)
        sessao.flush()
        sub = ItemFaq(categoria_id=raiz.id, nome="Visto de estudo", ordem=0)
        sessao.add(sub)
        sessao.flush()
        sessao.add_all(
            [
                ItemFaq(
                    categoria_id=raiz.id,
                    pergunta="Preciso de visto?",
                    resposta="Sim, para cursos acima de 90 dias.",
                    ordem=0,
                ),
                ItemFaq(
                    categoria_id=sub.id,
                    pergunta="Quais documentos levar?",
                    resposta="Passaporte e comprovante do Universitaly.",
                    fontes=["https://www.universitaly.it"],
                    ordem=0,
                ),
                ItemFaq(
                    categoria_id=sub.id,
                    pergunta="Quanto tempo demora?",
                    resposta="Depende do consulado.",
                    ordem=1,
                ),
            ]
        )
        sessao.commit()
    yield cliente


# ── API ──────────────────────────────────────────────────


def test_faq_devolve_a_arvore_aninhada(com_faq: TestClient) -> None:
    arvore = com_faq.get("/api/faq").json()
    assert len(arvore) == 1
    raiz = arvore[0]
    assert raiz["nome"] == "Vistos"
    assert [s["nome"] for s in raiz["subcategorias"]] == ["Visto de estudo"]


def test_contagem_de_perguntas_e_recursiva(com_faq: TestClient) -> None:
    """A raiz conta as próprias perguntas MAIS as das subcategorias."""
    raiz = com_faq.get("/api/faq").json()[0]
    assert raiz["total_perguntas"] == 3
    assert raiz["subcategorias"][0]["total_perguntas"] == 2


def test_busca_atravessa_a_arvore_inteira(com_faq: TestClient) -> None:
    encontradas = com_faq.get("/api/faq/buscar", params={"q": "universitaly"}).json()
    assert len(encontradas) == 1
    assert encontradas[0]["pergunta"] == "Quais documentos levar?"


def test_busca_restrita_a_uma_subcategoria(com_faq: TestClient) -> None:
    raiz = com_faq.get("/api/faq").json()[0]
    sub_id = raiz["subcategorias"][0]["id"]
    na_sub = com_faq.get("/api/faq/buscar", params={"categoria_id": sub_id}).json()
    assert len(na_sub) == 2  # só as da subcategoria, não a da raiz


def test_busca_em_categoria_inexistente_da_404(com_faq: TestClient) -> None:
    assert com_faq.get("/api/faq/buscar", params={"categoria_id": 999}).status_code == 404


def test_faq_vazio_devolve_lista_vazia(cliente: TestClient) -> None:
    assert cliente.get("/api/faq").json() == []


def test_fontes_chegam_na_resposta(com_faq: TestClient) -> None:
    encontradas = com_faq.get("/api/faq/buscar", params={"q": "documentos"}).json()
    assert encontradas[0]["fontes"] == ["https://www.universitaly.it"]


# ── página /ajuda ────────────────────────────────────────


def test_pagina_ajuda_responde(com_faq: TestClient) -> None:
    resposta = com_faq.get("/ajuda")
    assert resposta.status_code == 200
    assert "Vistos" in resposta.text


def test_pagina_ajuda_com_busca(com_faq: TestClient) -> None:
    resposta = com_faq.get("/ajuda", params={"q": "consulado"})
    assert resposta.status_code == 200
    assert "Quanto tempo demora?" in resposta.text
    assert "Preciso de visto?" not in resposta.text


def test_pagina_ajuda_filtra_por_categoria(com_faq: TestClient) -> None:
    raiz = com_faq.get("/api/faq").json()[0]
    sub_id = raiz["subcategorias"][0]["id"]
    resposta = com_faq.get("/ajuda", params={"categoria": sub_id})
    assert resposta.status_code == 200
    assert "Quais documentos levar?" in resposta.text
    assert "Preciso de visto?" not in resposta.text  # é da raiz, fora do escopo


def test_pagina_ajuda_com_categoria_inexistente_da_404(com_faq: TestClient) -> None:
    assert com_faq.get("/ajuda", params={"categoria": 999}).status_code == 404


def test_pagina_ajuda_sem_conteudo_nao_quebra(cliente: TestClient) -> None:
    resposta = cliente.get("/ajuda")
    assert resposta.status_code == 200
    assert "Nada encontrado" in resposta.text
