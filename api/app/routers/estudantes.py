"""CRUD de estudantes (rotas REST em /api/estudantes)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_sessao
from app.core.seguranca import exigir_auth, hash_senha
from app.models import Estudante
from app.schemas.estudante import EstudanteCriar, EstudanteEditar, EstudantePublico

router = APIRouter(prefix="/api/estudantes", tags=["estudantes"])

Sessao = Annotated[Session, Depends(get_sessao)]


def criar_estudante(sessao: Session, dados: EstudanteCriar) -> Estudante:
    """Cria o estudante (usado também pelo /api/auth/registrar)."""
    ja_existe = sessao.scalar(select(Estudante.id).where(Estudante.email == dados.email))
    if ja_existe is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    estudante = Estudante(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        area_estudo=dados.area_estudo,
        bio=dados.bio,
        nivel_italiano=dados.nivel_italiano,
        nivel_ingles=dados.nivel_ingles,
    )
    sessao.add(estudante)
    sessao.commit()
    sessao.refresh(estudante)
    return estudante


@router.post("", status_code=status.HTTP_201_CREATED)
def criar(dados: EstudanteCriar, sessao: Sessao) -> EstudantePublico:
    """Cadastro aberto: qualquer pessoa pode criar um perfil."""
    return EstudantePublico.model_validate(criar_estudante(sessao, dados))


@router.get("")
def listar(sessao: Sessao) -> list[EstudantePublico]:
    estudantes = sessao.scalars(select(Estudante).order_by(Estudante.nome)).all()
    return [EstudantePublico.model_validate(e) for e in estudantes]


@router.get("/{estudante_id}")
def detalhar(estudante_id: int, sessao: Sessao) -> EstudantePublico:
    estudante = sessao.get(Estudante, estudante_id)
    if estudante is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Estudante não encontrado")
    return EstudantePublico.model_validate(estudante)


@router.patch("/{estudante_id}")
@exigir_auth
async def editar(
    estudante_id: int,
    dados: EstudanteEditar,
    request: Request,
    sessao: Sessao,
) -> EstudantePublico:
    """Edita o próprio perfil (token obrigatório; só o dono edita)."""
    if request.state.estudante_id != estudante_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Só é possível editar o próprio perfil")
    estudante = sessao.get(Estudante, estudante_id)
    if estudante is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Estudante não encontrado")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(estudante, campo, valor)
    sessao.commit()
    sessao.refresh(estudante)
    return EstudantePublico.model_validate(estudante)
