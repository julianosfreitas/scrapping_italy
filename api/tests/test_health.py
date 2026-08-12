from app.main import app
from fastapi.testclient import TestClient

cliente = TestClient(app)


def test_health_responde_ok() -> None:
    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "ok"
    assert "ambiente" in corpo
