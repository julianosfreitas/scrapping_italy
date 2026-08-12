"""Registro e login com JWT (rotas em /api/auth)."""

from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_sessao
from app.core.seguranca import criar_token, verificar_senha
from app.models import Estudante
from app.routers.estudantes import criar_estudante
from app.schemas.auth import LoginDados, TokenResposta
from app.schemas.estudante import EstudanteCriar, EstudantePublico

router = APIRouter(prefix="/api/auth", tags=["auth"])

Sessao = Annotated[Session, Depends(get_sessao)]


@router.post("/registrar", status_code=status.HTTP_201_CREATED)
def registrar(dados: EstudanteCriar, sessao: Sessao) -> EstudantePublico:
    return EstudantePublico.model_validate(criar_estudante(sessao, dados))


@router.post("/login")
def login(dados: LoginDados, sessao: Sessao) -> TokenResposta:
    estudante = sessao.scalar(select(Estudante).where(Estudante.email == dados.email))
    if estudante is None or not verificar_senha(dados.senha, estudante.senha_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    settings = get_settings()
    token = criar_token(
        sub=str(estudante.id),
        segredo=settings.jwt_segredo,
        expira_em=timedelta(minutes=settings.jwt_exp_minutos),
    )
    return TokenResposta(access_token=token, estudante_id=estudante.id)
