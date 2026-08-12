"""Fluxo completo: registro → login → CRUD, com SQLite em memória."""

from fastapi.testclient import TestClient

JULIA = {
    "nome": "Julia Teste",
    "email": "julia@teste.com",
    "senha": "senha-forte-123",
    "area_estudo": "Design",
}


def registrar_e_logar(cliente: TestClient, dados: dict[str, str] | None = None) -> tuple[int, str]:
    corpo = dados or JULIA
    registro = cliente.post("/api/auth/registrar", json=corpo)
    assert registro.status_code == 201, registro.text
    login = cliente.post("/api/auth/login", json={"email": corpo["email"], "senha": corpo["senha"]})
    assert login.status_code == 200, login.text
    dados_login = login.json()
    return dados_login["estudante_id"], dados_login["access_token"]


def test_registro_login_e_detalhe(cliente: TestClient) -> None:
    estudante_id, _token = registrar_e_logar(cliente)
    detalhe = cliente.get(f"/api/estudantes/{estudante_id}")
    assert detalhe.status_code == 200
    corpo = detalhe.json()
    assert corpo["nome"] == "Julia Teste"
    assert "senha" not in corpo and "senha_hash" not in corpo  # nunca vazar credencial


def test_email_duplicado_da_409(cliente: TestClient) -> None:
    registrar_e_logar(cliente)
    de_novo = cliente.post("/api/auth/registrar", json=JULIA)
    assert de_novo.status_code == 409


def test_login_com_senha_errada_da_401(cliente: TestClient) -> None:
    registrar_e_logar(cliente)
    login = cliente.post("/api/auth/login", json={"email": JULIA["email"], "senha": "senha-errada"})
    assert login.status_code == 401


def test_listar_estudantes(cliente: TestClient) -> None:
    registrar_e_logar(cliente)
    lista = cliente.get("/api/estudantes")
    assert lista.status_code == 200
    assert [e["nome"] for e in lista.json()] == ["Julia Teste"]


def test_editar_proprio_perfil(cliente: TestClient) -> None:
    estudante_id, token = registrar_e_logar(cliente)
    resposta = cliente.patch(
        f"/api/estudantes/{estudante_id}",
        json={"bio": "Nova bio", "nivel_italiano": "B1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resposta.status_code == 200
    assert resposta.json()["bio"] == "Nova bio"
    assert resposta.json()["nivel_italiano"] == "B1"


def test_editar_sem_token_da_401(cliente: TestClient) -> None:
    estudante_id, _ = registrar_e_logar(cliente)
    resposta = cliente.patch(f"/api/estudantes/{estudante_id}", json={"bio": "x"})
    assert resposta.status_code == 401


def test_editar_perfil_alheio_da_403(cliente: TestClient) -> None:
    registrar_e_logar(cliente)
    outra = {"nome": "Outra Pessoa", "email": "outra@teste.com", "senha": "senha-forte-456"}
    outra_id, token_outra = registrar_e_logar(cliente, outra)
    alvo = cliente.get("/api/estudantes").json()
    id_julia = next(e["id"] for e in alvo if e["email"] == JULIA["email"])
    resposta = cliente.patch(
        f"/api/estudantes/{id_julia}",
        json={"bio": "invasão"},
        headers={"Authorization": f"Bearer {token_outra}"},
    )
    assert resposta.status_code == 403
    assert outra_id != id_julia


def test_paginas_html_no_ar(cliente: TestClient) -> None:
    for caminho in ("/", "/login", "/estudantes"):
        resposta = cliente.get(caminho)
        assert resposta.status_code == 200
        assert "Ponte" in resposta.text
