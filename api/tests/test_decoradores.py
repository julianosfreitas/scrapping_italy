import pytest
from app.core.decoradores import cronometrar, retry_backoff

# ── @cronometrar ──────────────────────────────────────────


def test_cronometrar_preserva_resultado_e_metadados() -> None:
    @cronometrar
    def somar(a: int, b: int) -> int:
        """Soma dois inteiros."""
        return a + b

    assert somar(2, 3) == 5
    assert somar.__name__ == "somar"  # functools.wraps preservou o nome
    assert somar.__doc__ == "Soma dois inteiros."


def test_cronometrar_propaga_excecao() -> None:
    @cronometrar
    def explode() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        explode()


# ── @retry_backoff ────────────────────────────────────────


def test_retry_backoff_sucesso_apos_falhas() -> None:
    chamadas: list[int] = []
    atrasos: list[float] = []

    @retry_backoff(tentativas=4, atraso_base=0.1, fator=2.0, dormir=atrasos.append)
    def instavel() -> str:
        chamadas.append(1)
        if len(chamadas) < 3:
            raise ConnectionError("rede fora")
        return "ok"

    assert instavel() == "ok"
    assert len(chamadas) == 3
    assert atrasos == [0.1, 0.2]  # backoff exponencial: base * fator**n


def test_retry_backoff_esgota_tentativas_e_relanca() -> None:
    atrasos: list[float] = []

    @retry_backoff(tentativas=3, atraso_base=1.0, fator=3.0, dormir=atrasos.append)
    def sempre_falha() -> None:
        raise TimeoutError("sem resposta")

    with pytest.raises(TimeoutError, match="sem resposta"):
        sempre_falha()
    assert atrasos == [1.0, 3.0]  # dormiu entre as 3 tentativas, não depois da última


def test_retry_backoff_so_captura_excecoes_configuradas() -> None:
    @retry_backoff(tentativas=5, excecoes=(ConnectionError,), dormir=lambda _s: None)
    def erro_de_programacao() -> None:
        raise ValueError("bug de verdade")

    with pytest.raises(ValueError, match="bug de verdade"):  # não fez retry
        erro_de_programacao()


def test_retry_backoff_valida_parametros() -> None:
    with pytest.raises(ValueError, match="tentativas"):
        retry_backoff(tentativas=0)


def test_retry_backoff_politicas_independentes() -> None:
    """Cada closure guarda sua própria configuração — sem estado compartilhado."""
    atrasos_a: list[float] = []
    atrasos_b: list[float] = []

    @retry_backoff(tentativas=2, atraso_base=0.5, dormir=atrasos_a.append)
    def a() -> None:
        raise ConnectionError

    @retry_backoff(tentativas=2, atraso_base=9.0, dormir=atrasos_b.append)
    def b() -> None:
        raise ConnectionError

    with pytest.raises(ConnectionError):
        a()
    with pytest.raises(ConnectionError):
        b()
    assert atrasos_a == [0.5]
    assert atrasos_b == [9.0]
