"""Radar: ingestão em lote com dedupe e feed paginado com filtros."""

from fastapi.testclient import TestClient

from tests.test_rotas_estudantes import registrar_e_logar

LOTE = [
    {
        "titulo": "Nuovo bando borse di studio DSU",
        "url": "https://laziodisco.it/bando-2026",
        "fonte": "laziodisco",
        "categoria": "bolsas",
        "resumo": "Bando aberto",
        "idioma": "it",
        "publicada_em": "2026-08-11T08:00:00",
    },
    {
        "titulo": "Student visa Italy: new rules",
        "url": "https://esempio.it/visa",
        "fonte": "google_news",
        "categoria": "vistos",
        "idioma": "en",
        "publicada_em": "2026-08-10T10:00:00",
    },
]


def ingerir(cliente: TestClient, token: str, lote: list[dict[str, object]]) -> dict[str, int]:
    resposta = cliente.post(
        "/api/noticias", json=lote, headers={"Authorization": f"Bearer {token}"}
    )
    assert resposta.status_code == 201, resposta.text
    return dict(resposta.json())


def test_ingestao_exige_auth(cliente: TestClient) -> None:
    assert cliente.post("/api/noticias", json=LOTE).status_code == 401


def test_ingestao_com_dedupe_por_url(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    primeira = ingerir(cliente, token, LOTE)
    assert primeira == {"criadas": 2, "ignoradas": 0}
    segunda = ingerir(cliente, token, LOTE)  # mesmo lote de novo
    assert segunda == {"criadas": 0, "ignoradas": 2}
    repetida_no_lote = [LOTE[0], LOTE[0]]  # dupla intra-lote com URL nova? não: já existe
    assert ingerir(cliente, token, repetida_no_lote) == {"criadas": 0, "ignoradas": 2}


def test_feed_ordenado_e_filtrado(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    ingerir(cliente, token, LOTE)
    feed = cliente.get("/api/noticias").json()
    assert feed["total"] == 2
    assert [n["categoria"] for n in feed["itens"]] == ["bolsas", "vistos"]  # mais recente 1º

    bolsas = cliente.get("/api/noticias?categoria=bolsas").json()
    assert bolsas["total"] == 1
    assert bolsas["itens"][0]["fonte"] == "laziodisco"

    fonte = cliente.get("/api/noticias?fonte=google_news").json()
    assert fonte["total"] == 1


def test_feed_paginado(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    lote = [
        {
            "titulo": f"Notícia {i}",
            "url": f"https://esempio.it/n/{i}",
            "fonte": "google_news",
            "categoria": "geral",
            "publicada_em": f"2026-08-{i:02d}T09:00:00",
        }
        for i in range(1, 13)
    ]
    ingerir(cliente, token, lote)
    pagina1 = cliente.get("/api/noticias?por_pagina=5").json()
    assert pagina1["total"] == 12
    assert pagina1["total_paginas"] == 3
    assert len(pagina1["itens"]) == 5
    assert pagina1["itens"][0]["titulo"] == "Notícia 12"  # desc por publicada_em
    pagina3 = cliente.get("/api/noticias?por_pagina=5&pagina=3").json()
    assert len(pagina3["itens"]) == 2


def test_pagina_radar_renderiza(cliente: TestClient) -> None:
    _, token = registrar_e_logar(cliente)
    ingerir(cliente, token, LOTE)
    resposta = cliente.get("/radar")
    assert resposta.status_code == 200
    assert "Nuovo bando borse di studio DSU" in resposta.text
    filtrada = cliente.get("/radar?categoria=vistos")
    assert "Student visa" in filtrada.text
    assert "Nuovo bando" not in filtrada.text
