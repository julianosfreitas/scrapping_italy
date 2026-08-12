"""Cofre de documentos ponta a ponta: upload, listagem, URL assinada, download."""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from tests.test_rotas_estudantes import registrar_e_logar

PDF_MINIMO = b"%PDF-1.4 conteudo de teste"


def _enviar(
    cliente: TestClient,
    estudante_id: int,
    token: str,
    nome: str = "Passaporte (2ª via).pdf",
    validade: str | None = None,
) -> dict[str, object]:
    dados: dict[str, str] = {"categoria": "identidade", "tipo": "passaporte"}
    if validade:
        dados["data_validade"] = validade
    resposta = cliente.post(
        f"/api/estudantes/{estudante_id}/documentos",
        headers={"Authorization": f"Bearer {token}"},
        files={"arquivo": (nome, PDF_MINIMO, "application/pdf")},
        data=dados,
    )
    assert resposta.status_code == 201, resposta.text
    return dict(resposta.json())


def test_upload_sanitiza_nome_e_deriva_status(cliente: TestClient) -> None:
    estudante_id, token = registrar_e_logar(cliente)
    validade = (date.today() + timedelta(days=10)).isoformat()
    documento = _enviar(cliente, estudante_id, token, validade=validade)
    assert documento["nome_arquivo"] == "passaporte-2a-via.pdf"  # sanitizado
    assert documento["status"] == "vencendo"  # derivado, não gravado


def test_upload_sem_token_da_401(cliente: TestClient) -> None:
    estudante_id, _ = registrar_e_logar(cliente)
    resposta = cliente.post(
        f"/api/estudantes/{estudante_id}/documentos",
        files={"arquivo": ("a.pdf", PDF_MINIMO, "application/pdf")},
        data={"categoria": "identidade", "tipo": "passaporte"},
    )
    assert resposta.status_code == 401


def test_upload_extensao_proibida_da_422(cliente: TestClient) -> None:
    estudante_id, token = registrar_e_logar(cliente)
    resposta = cliente.post(
        f"/api/estudantes/{estudante_id}/documentos",
        headers={"Authorization": f"Bearer {token}"},
        files={"arquivo": ("virus.exe", b"MZ...", "application/octet-stream")},
        data={"categoria": "outros", "tipo": "programa"},
    )
    assert resposta.status_code == 422


def test_listar_cofre_alheio_da_403(cliente: TestClient) -> None:
    estudante_id, _token = registrar_e_logar(cliente)
    outra = {"nome": "Outra Pessoa", "email": "outra@teste.com", "senha": "senha-forte-456"}
    _outra_id, token_outra = registrar_e_logar(cliente, outra)
    resposta = cliente.get(
        f"/api/estudantes/{estudante_id}/documentos",
        headers={"Authorization": f"Bearer {token_outra}"},
    )
    assert resposta.status_code == 403


def test_download_via_url_assinada(cliente: TestClient) -> None:
    estudante_id, token = registrar_e_logar(cliente)
    documento = _enviar(cliente, estudante_id, token)
    assinada = cliente.get(
        f"/api/documentos/{documento['id']}/url-assinada",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert assinada.status_code == 200
    download = cliente.get(assinada.json()["url"])
    assert download.status_code == 200
    assert download.content == PDF_MINIMO
    assert download.headers["content-type"].startswith("application/pdf")


def test_download_sem_token_ou_com_token_de_sessao_falha(cliente: TestClient) -> None:
    estudante_id, token = registrar_e_logar(cliente)
    documento = _enviar(cliente, estudante_id, token)
    sem_token = cliente.get(f"/api/documentos/{documento['id']}/download")
    assert sem_token.status_code == 422  # token é query param obrigatório
    token_errado = cliente.get(f"/api/documentos/{documento['id']}/download?token={token}")
    assert token_errado.status_code == 401  # token de sessão não tem escopo de download


def test_token_de_download_nao_da_acesso_geral(cliente: TestClient) -> None:
    """Token de escopo restrito (download) não pode ser usado como sessão."""
    estudante_id, token = registrar_e_logar(cliente)
    documento = _enviar(cliente, estudante_id, token)
    url = cliente.get(
        f"/api/documentos/{documento['id']}/url-assinada",
        headers={"Authorization": f"Bearer {token}"},
    ).json()["url"]
    token_download = url.split("token=")[1]
    invasao = cliente.get(
        f"/api/estudantes/{estudante_id}/documentos",
        headers={"Authorization": f"Bearer {token_download}"},
    )
    assert invasao.status_code == 401
