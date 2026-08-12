"""Universidades, cursos e "Minhas universidades" ponta a ponta."""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from tests.test_rotas_estudantes import registrar_e_logar

BOLONHA = {
    "nome": "Università di Bologna",
    "cidade": "Bologna",
    "site_oficial": "https://www.unibo.it",
    "fonte": "manual",
    "cursos": [
        {
            "nome": "Computer Science",
            "grau": "mestrado",
            "idioma": "inglês",
            "custo_anual": "3500.00",
            "prazo_inscricao": "2026-09-10",
            "tempo_preparacao_meses": 6,
            "requisitos": [
                {"categoria": "identidade", "descricao": "Passaporte válido"},
                {"categoria": "idioma", "descricao": "Inglês B2 (IELTS/TOEFL)"},
                {"categoria": "academico", "descricao": "Diploma de graduação"},
            ],
        },
        {
            "nome": "Engenharia Civil",
            "grau": "grad",
            "idioma": "italiano",
            "prazo_inscricao": None,
            "requisitos": [],
        },
    ],
}


def cadastrar_bolonha(cliente: TestClient, token: str) -> dict[str, object]:
    resposta = cliente.post(
        "/api/universidades", json=BOLONHA, headers={"Authorization": f"Bearer {token}"}
    )
    assert resposta.status_code == 201, resposta.text
    return dict(resposta.json())


def test_cadastro_exige_auth(cliente: TestClient) -> None:
    assert cliente.post("/api/universidades", json=BOLONHA).status_code == 401


def test_cadastro_listagem_e_busca(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    cadastrar_bolonha(cliente, token)
    todas = cliente.get("/api/universidades").json()
    assert [u["nome"] for u in todas] == ["Università di Bologna"]
    assert todas[0]["total_cursos"] == 2
    assert cliente.get("/api/universidades?q=bologna").json() != []
    assert cliente.get("/api/universidades?q=milano").json() == []


def test_detalhe_ordena_cursos_por_prazo_com_lambda(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    universidade = cadastrar_bolonha(cliente, token)
    detalhe = cliente.get(f"/api/universidades/{universidade['id']}").json()
    nomes = [c["nome"] for c in detalhe["cursos"]]
    assert nomes == ["Computer Science", "Engenharia Civil"]  # sem prazo vai ao fim


def test_cadastro_e_upsert_idempotente(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    primeira = cadastrar_bolonha(cliente, token)
    segunda = cadastrar_bolonha(cliente, token)  # repetido: atualiza, não duplica
    assert primeira["id"] == segunda["id"]
    assert len(cliente.get("/api/universidades").json()) == 1
    assert len(segunda["cursos"]) == 2


def test_adicionar_curso_e_ver_comparativo(cliente: TestClient) -> None:
    estudante_id, token = registrar_e_logar(cliente)
    universidade = cadastrar_bolonha(cliente, token)
    curso_id = next(c["id"] for c in universidade["cursos"] if c["nome"] == "Computer Science")

    # documento que atende "identidade" (ok) e um de idioma vencendo
    validade_ok = (date.today() + timedelta(days=365)).isoformat()
    validade_vencendo = (date.today() + timedelta(days=10)).isoformat()
    for nome, categoria, tipo, validade in (
        ("passaporte.pdf", "identidade", "passaporte", validade_ok),
        ("ielts.pdf", "idioma", "ielts", validade_vencendo),
    ):
        envio = cliente.post(
            f"/api/estudantes/{estudante_id}/documentos",
            headers={"Authorization": f"Bearer {token}"},
            files={"arquivo": (nome, b"%PDF-1.4 x", "application/pdf")},
            data={"categoria": categoria, "tipo": tipo, "data_validade": validade},
        )
        assert envio.status_code == 201

    adicao = cliente.post(
        f"/api/estudantes/{estudante_id}/universidades",
        json={"curso_id": curso_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert adicao.status_code == 201, adicao.text
    corpo = adicao.json()
    assert corpo["status"] == "interessado"
    gap = corpo["gap"]
    assert [i["descricao"] for i in gap["atendidos"]] == ["Passaporte válido"]
    assert [i["descricao"] for i in gap["vencendo"]] == ["Inglês B2 (IELTS/TOEFL)"]
    assert [i["descricao"] for i in gap["faltando"]] == ["Diploma de graduação"]
    assert gap["percentual_pronto"] == 33


def test_adicionar_curso_duplicado_da_409(cliente: TestClient) -> None:
    estudante_id, token = registrar_e_logar(cliente)
    universidade = cadastrar_bolonha(cliente, token)
    curso_id = universidade["cursos"][0]["id"]
    cabecalho = {"Authorization": f"Bearer {token}"}
    corpo = {"curso_id": curso_id}
    caminho = f"/api/estudantes/{estudante_id}/universidades"
    assert cliente.post(caminho, json=corpo, headers=cabecalho).status_code == 201
    assert cliente.post(caminho, json=corpo, headers=cabecalho).status_code == 409


def test_editar_status_e_alerta_e_remover(cliente: TestClient) -> None:
    estudante_id, token = registrar_e_logar(cliente)
    universidade = cadastrar_bolonha(cliente, token)
    curso_id = universidade["cursos"][0]["id"]
    cabecalho = {"Authorization": f"Bearer {token}"}
    caminho = f"/api/estudantes/{estudante_id}/universidades"
    cliente.post(caminho, json={"curso_id": curso_id}, headers=cabecalho)

    editada = cliente.patch(
        f"{caminho}/{curso_id}",
        json={"status": "preparando", "alerta_prazo": False},
        headers=cabecalho,
    )
    assert editada.status_code == 200
    assert editada.json()["status"] == "preparando"
    assert editada.json()["alerta_prazo"] is False

    assert cliente.delete(f"{caminho}/{curso_id}", headers=cabecalho).status_code == 204
    assert cliente.get(caminho, headers=cabecalho).json() == []


def test_minhas_universidades_de_outro_estudante_da_403(cliente: TestClient) -> None:
    estudante_id, _token = registrar_e_logar(cliente)
    outra = {"nome": "Outra Pessoa", "email": "outra@teste.com", "senha": "senha-forte-456"}
    _, token_outra = registrar_e_logar(cliente, outra)
    resposta = cliente.get(
        f"/api/estudantes/{estudante_id}/universidades",
        headers={"Authorization": f"Bearer {token_outra}"},
    )
    assert resposta.status_code == 403
