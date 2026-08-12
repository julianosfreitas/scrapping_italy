from datetime import UTC, datetime, timedelta

import pytest
from app.core.seguranca import (
    criar_token,
    decodificar_token,
    hash_senha,
    verificar_senha,
)
from fastapi import HTTPException

SEGREDO = "segredo-de-teste-com-mais-de-32-bytes-ok"


def test_hash_e_verificacao_de_senha() -> None:
    hash_gerado = hash_senha("minha-senha-forte")
    assert hash_gerado != "minha-senha-forte"
    assert verificar_senha("minha-senha-forte", hash_gerado)
    assert not verificar_senha("senha-errada", hash_gerado)


def test_senha_inutilizavel_do_seed_nunca_autentica() -> None:
    assert not verificar_senha("qualquer-coisa", "!")


def test_token_roundtrip() -> None:
    token = criar_token("42", SEGREDO, timedelta(minutes=5))
    payload = decodificar_token(token, SEGREDO)
    assert payload["sub"] == "42"


def test_token_expirado_e_rejeitado() -> None:
    passado = datetime.now(UTC) - timedelta(hours=2)
    token = criar_token("42", SEGREDO, timedelta(minutes=5), agora=passado)
    with pytest.raises(HTTPException) as erro:
        decodificar_token(token, SEGREDO)
    assert erro.value.status_code == 401


def test_token_com_segredo_errado_e_rejeitado() -> None:
    token = criar_token("42", SEGREDO, timedelta(minutes=5))
    with pytest.raises(HTTPException):
        decodificar_token(token, "outro-segredo-tambem-com-32-bytes-aqui")


def test_claims_extras_entram_no_payload() -> None:
    token = criar_token("7", SEGREDO, timedelta(minutes=5), claims_extras={"escopo": "download"})
    assert decodificar_token(token, SEGREDO)["escopo"] == "download"
