"""Autenticação: hash de senha (bcrypt), tokens JWT e o decorador @exigir_auth.

A emissão/decodificação de token é escrita como função com relógio injetável
(``agora``): com os mesmos argumentos, o mesmo token — o que permite testar
expiração sem esperar o tempo passar. O ``@exigir_auth`` é mais um exemplo
real de decorador/closure do relatório de PF: envolve o endpoint, valida o
Bearer token e deixa o id do estudante em ``request.state``.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, cast

import bcrypt
import jwt
from fastapi import HTTPException, Request, status

from app.core.config import get_settings

ALGORITMO = "HS256"


# ── Senhas ────────────────────────────────────────────────


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode(), senha_hash.encode())
    except ValueError:  # hash inválido/inutilizável (ex.: seed "!")
        return False


# ── Tokens JWT ────────────────────────────────────────────


def criar_token(
    sub: str,
    segredo: str,
    expira_em: timedelta,
    agora: datetime | None = None,
    claims_extras: dict[str, Any] | None = None,
) -> str:
    """Emite um JWT. ``agora`` é injetável para tornar a expiração testável."""
    emitido_em = agora if agora is not None else datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": sub,
        "iat": emitido_em,
        "exp": emitido_em + expira_em,
        **(claims_extras or {}),
    }
    return jwt.encode(payload, segredo, algorithm=ALGORITMO)


def decodificar_token(token: str, segredo: str) -> dict[str, Any]:
    """Valida assinatura e expiração; devolve o payload ou levanta 401."""
    try:
        return jwt.decode(token, segredo, algorithms=[ALGORITMO])
    except jwt.PyJWTError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from erro


def _extrair_bearer(request: Request) -> str:
    autorizacao = request.headers.get("Authorization", "")
    esquema, _, token = autorizacao.partition(" ")
    if esquema.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais ausentes",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


# ── Decorador @exigir_auth ───────────────────────────────


def exigir_auth[**P, R](funcao: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    """Protege um endpoint FastAPI: exige `Bearer <jwt>` válido.

    Closure sem estado próprio: toda a configuração vem das settings no
    momento da chamada. O endpoint decorado precisa declarar um parâmetro
    ``request: Request``; após a validação, ``request.state.estudante_id``
    contém o id autenticado.
    """

    @wraps(funcao)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        request = next(
            (v for v in (*args, *kwargs.values()) if isinstance(v, Request)),
            None,
        )
        if request is None:  # erro de programação, não de credencial
            raise RuntimeError(
                f"@exigir_auth: {funcao.__qualname__} precisa de um parâmetro Request"
            )
        payload = decodificar_token(_extrair_bearer(request), get_settings().jwt_segredo)
        if payload.get("escopo") is not None:  # token de escopo restrito não dá acesso geral
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        request.state.estudante_id = int(payload["sub"])
        resultado = funcao(*args, **kwargs)
        if inspect.isawaitable(resultado):
            return await resultado
        return cast(R, resultado)

    return wrapper
