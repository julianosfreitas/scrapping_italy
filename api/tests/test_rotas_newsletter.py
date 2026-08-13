"""Newsletter: inscrições públicas, curadoria autenticada e arquivo de edições."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from tests.test_rotas_estudantes import registrar_e_logar


def _agora() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def lote_de_noticias() -> list[dict[str, object]]:
    """Notícias recentes o bastante para caírem na janela de 24h da curadoria."""
    recente = (_agora() - timedelta(hours=2)).isoformat()
    return [
        {
            "titulo": "Nuove regole per il visto studio",
            "url": "https://esempio.it/visto",
            "fonte": "google_news",
            "categoria": "vistos",
            "publicada_em": recente,
        },
        {
            "titulo": "Bando DSU 2026/2027",
            "url": "https://laziodisco.it/bando",
            "fonte": "laziodisco",
            "categoria": "bolsas",
            "publicada_em": recente,
        },
        {
            "titulo": "Notícia sem tópico definido",
            "url": "https://esempio.it/geral",
            "fonte": "google_news",
            "categoria": "geral",
            "publicada_em": recente,
        },
    ]


# ── inscrições ───────────────────────────────────────────


def test_inscricao_publica_nao_exige_auth(cliente: TestClient) -> None:
    resposta = cliente.post("/api/newsletter/inscricoes", json={"email": "davi@teste.com"})
    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["ativo"] is True


def test_inscricao_normaliza_o_email(cliente: TestClient) -> None:
    resposta = cliente.post("/api/newsletter/inscricoes", json={"email": "  Davi@Teste.COM "})
    assert resposta.json()["email"] == "davi@teste.com"


def test_inscricao_com_email_invalido_da_422(cliente: TestClient) -> None:
    assert (
        cliente.post("/api/newsletter/inscricoes", json={"email": "sem-arroba"}).status_code == 422
    )


def test_reinscrever_reativa_sem_duplicar(cliente: TestClient) -> None:
    cliente.post("/api/newsletter/inscricoes", json={"email": "davi@teste.com"})
    cliente.post("/api/newsletter/inscricoes/cancelar", json={"email": "davi@teste.com"})
    reativada = cliente.post("/api/newsletter/inscricoes", json={"email": "davi@teste.com"})
    assert reativada.json()["ativo"] is True

    _, token = registrar_e_logar(cliente)
    inscritos = cliente.get(
        "/api/newsletter/inscritos", headers={"Authorization": f"Bearer {token}"}
    )
    assert inscritos.json() == ["davi@teste.com"]  # uma só linha


def test_cancelar_desativa_mas_preserva_a_linha(cliente: TestClient) -> None:
    cliente.post("/api/newsletter/inscricoes", json={"email": "davi@teste.com"})
    resposta = cliente.post("/api/newsletter/inscricoes/cancelar", json={"email": "davi@teste.com"})
    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is False

    _, token = registrar_e_logar(cliente)
    inscritos = cliente.get(
        "/api/newsletter/inscritos", headers={"Authorization": f"Bearer {token}"}
    )
    assert inscritos.json() == []  # cancelado não recebe


def test_cancelar_email_nao_inscrito_da_404(cliente: TestClient) -> None:
    resposta = cliente.post("/api/newsletter/inscricoes/cancelar", json={"email": "x@teste.com"})
    assert resposta.status_code == 404


def test_listar_inscritos_exige_auth(cliente: TestClient) -> None:
    assert cliente.get("/api/newsletter/inscritos").status_code == 401


# ── curadoria ────────────────────────────────────────────


def test_curadoria_exige_auth(cliente: TestClient) -> None:
    assert cliente.post("/api/newsletter/curadoria").status_code == 401


def test_curadoria_monta_edicao_agrupada_e_ignora_geral(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    auth = {"Authorization": f"Bearer {token}"}
    cliente.post("/api/noticias", json=lote_de_noticias(), headers=auth)

    resposta = cliente.post("/api/newsletter/curadoria", headers=auth)
    assert resposta.status_code == 201, resposta.text
    edicao = resposta.json()
    assert [t["chave"] for t in edicao["topicos"]] == ["vistos", "bolsas"]
    assert edicao["total"] == 2  # a notícia "geral" não entra


def test_curadoria_e_idempotente_no_mesmo_dia(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    auth = {"Authorization": f"Bearer {token}"}
    cliente.post("/api/noticias", json=lote_de_noticias(), headers=auth)

    cliente.post("/api/newsletter/curadoria", headers=auth)
    cliente.post("/api/newsletter/curadoria", headers=auth)
    arquivo = cliente.get("/api/newsletter/edicoes").json()
    assert len(arquivo) == 1  # atualizou, não duplicou


def test_curadoria_respeita_a_janela_de_horas(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    auth = {"Authorization": f"Bearer {token}"}
    antiga = [
        {
            "titulo": "Visto de dez dias atrás",
            "url": "https://esempio.it/antiga",
            "fonte": "google_news",
            "categoria": "vistos",
            "publicada_em": (_agora() - timedelta(days=10)).isoformat(),
        }
    ]
    cliente.post("/api/noticias", json=antiga, headers=auth)

    padrao = cliente.post("/api/newsletter/curadoria", headers=auth).json()
    assert padrao["total"] == 0

    ampla = cliente.post("/api/newsletter/curadoria?janela_horas=480", headers=auth).json()
    assert ampla["total"] == 1


# ── arquivo de edições ───────────────────────────────────


def test_arquivo_de_edicoes_e_publico(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    auth = {"Authorization": f"Bearer {token}"}
    cliente.post("/api/noticias", json=lote_de_noticias(), headers=auth)
    cliente.post("/api/newsletter/curadoria", headers=auth)

    hoje = _agora().date().isoformat()
    assert cliente.get("/api/newsletter/edicoes").status_code == 200
    assert cliente.get(f"/api/newsletter/edicoes/{hoje}").status_code == 200


def test_edicao_inexistente_da_404(cliente: TestClient) -> None:
    assert cliente.get("/api/newsletter/edicoes/2020-01-01").status_code == 404


def test_marcar_enviada_registra_o_log_de_envio(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    auth = {"Authorization": f"Bearer {token}"}
    cliente.post("/api/noticias", json=lote_de_noticias(), headers=auth)
    cliente.post("/api/newsletter/curadoria", headers=auth)

    hoje = _agora().date().isoformat()
    resposta = cliente.post(f"/api/newsletter/edicoes/{hoje}/enviada", headers=auth)
    assert resposta.status_code == 200
    assert resposta.json()["enviada_em"] is not None


def test_marcar_enviada_exige_auth(cliente: TestClient) -> None:
    hoje = _agora().date().isoformat()
    assert cliente.post(f"/api/newsletter/edicoes/{hoje}/enviada").status_code == 401


# ── páginas ──────────────────────────────────────────────


def test_pagina_newsletter_responde(cliente: TestClient) -> None:
    assert cliente.get("/newsletter").status_code == 200


def test_pagina_da_edicao_responde_e_404_quando_nao_existe(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    auth = {"Authorization": f"Bearer {token}"}
    cliente.post("/api/noticias", json=lote_de_noticias(), headers=auth)
    cliente.post("/api/newsletter/curadoria", headers=auth)

    hoje = _agora().date().isoformat()
    assert cliente.get(f"/newsletter/{hoje}").status_code == 200
    assert cliente.get("/newsletter/2020-01-01").status_code == 404
