"""Universidades, cursos e a associação "Minhas universidades" (+ comparativo).

Routers fazem I/O e conversão ORM → snapshots imutáveis; todo cálculo
(ordenação por prazo, proximidade de prazo, gap) é delegado às funções puras
de ``app/services``.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_sessao
from app.core.seguranca import exigir_auth
from app.models import (
    Curso,
    Documento,
    Estudante,
    EstudanteUniversidade,
    RequisitoCurso,
    Universidade,
)
from app.schemas.universidade import (
    AssociacaoCriar,
    AssociacaoEditar,
    CursoPublico,
    GapPublico,
    ItemGapPublico,
    MinhaUniversidade,
    RequisitoPublico,
    UniversidadeCriar,
    UniversidadeDetalhe,
    UniversidadePublica,
)
from app.services.comparativo import DocumentoResumo, Gap, Requisito, calcular_gap
from app.services.cursos import ordenar_por_prazo, prazo_proximo
from app.services.documentos import calcular_status

router = APIRouter(prefix="/api", tags=["universidades"])

Sessao = Annotated[Session, Depends(get_sessao)]


# ── conversões ORM → schemas ─────────────────────────────


def _curso_publico(curso: Curso, hoje: date) -> CursoPublico:
    return CursoPublico(
        id=curso.id,
        universidade_id=curso.universidade_id,
        nome=curso.nome,
        grau=curso.grau,
        idioma=curso.idioma,
        custo_anual=curso.custo_anual,
        prazo_inscricao=curso.prazo_inscricao,
        tempo_preparacao_meses=curso.tempo_preparacao_meses,
        prazo_proximo=prazo_proximo(curso.prazo_inscricao, hoje),
        requisitos=tuple(RequisitoPublico.model_validate(r) for r in curso.requisitos),
    )


def _universidade_publica(universidade: Universidade) -> UniversidadePublica:
    return UniversidadePublica(
        id=universidade.id,
        nome=universidade.nome,
        pais=universidade.pais,
        cidade=universidade.cidade,
        site_oficial=universidade.site_oficial,
        fonte=universidade.fonte,
        total_cursos=len(universidade.cursos),
    )


def _gap_publico(gap: Gap) -> GapPublico:
    def _itens(itens: tuple) -> tuple[ItemGapPublico, ...]:  # type: ignore[type-arg]
        return tuple(
            ItemGapPublico(
                categoria=item.requisito.categoria,
                descricao=item.requisito.descricao,
                obrigatorio=item.requisito.obrigatorio,
                documentos=item.documentos,
            )
            for item in itens
        )

    return GapPublico(
        atendidos=_itens(gap.atendidos),
        faltando=_itens(gap.faltando),
        vencendo=_itens(gap.vencendo),
        percentual_pronto=gap.percentual_pronto,
    )


# ── universidades e cursos ───────────────────────────────


@router.get("/universidades")
def listar_universidades(sessao: Sessao, q: str | None = None) -> list[UniversidadePublica]:
    consulta = select(Universidade).options(selectinload(Universidade.cursos))
    if q:
        consulta = consulta.where(Universidade.nome.ilike(f"%{q}%"))
    universidades = sessao.scalars(consulta.order_by(Universidade.nome)).all()
    return [_universidade_publica(u) for u in universidades]


@router.get("/universidades/{universidade_id}")
def detalhar_universidade(universidade_id: int, sessao: Sessao) -> UniversidadeDetalhe:
    universidade = sessao.get(
        Universidade,
        universidade_id,
        options=[selectinload(Universidade.cursos).selectinload(Curso.requisitos)],
    )
    if universidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Universidade não encontrada")
    hoje = datetime.now(UTC).date()
    cursos = ordenar_por_prazo(universidade.cursos, lambda c: c.prazo_inscricao)
    return UniversidadeDetalhe(
        **_universidade_publica(universidade).model_dump(),
        cursos=tuple(_curso_publico(c, hoje) for c in cursos),
    )


@router.post("/universidades", status_code=status.HTTP_201_CREATED)
@exigir_auth
async def cadastrar_universidade(
    dados: UniversidadeCriar, request: Request, sessao: Sessao
) -> UniversidadeDetalhe:
    """Cadastro manual autenticado. Upsert por (nome, cidade): recadastrar a
    mesma universidade atualiza os dados e faz merge dos cursos por (nome, grau)
    — é o que torna a ingestão do scraper idempotente."""
    universidade = sessao.scalar(
        select(Universidade).where(
            Universidade.nome == dados.nome, Universidade.cidade == dados.cidade
        )
    )
    if universidade is None:
        universidade = Universidade(nome=dados.nome, cidade=dados.cidade)
        sessao.add(universidade)
    universidade.pais = dados.pais
    universidade.site_oficial = dados.site_oficial
    universidade.fonte = dados.fonte

    existentes = {(c.nome, c.grau): c for c in universidade.cursos}
    for curso_novo in dados.cursos:
        curso = existentes.get((curso_novo.nome, curso_novo.grau))
        if curso is None:
            curso = Curso(nome=curso_novo.nome, grau=curso_novo.grau)
            universidade.cursos.append(curso)
        curso.idioma = curso_novo.idioma
        curso.custo_anual = curso_novo.custo_anual
        curso.prazo_inscricao = curso_novo.prazo_inscricao
        curso.tempo_preparacao_meses = curso_novo.tempo_preparacao_meses
        curso.requisitos = [
            RequisitoCurso(categoria=r.categoria, descricao=r.descricao, obrigatorio=r.obrigatorio)
            for r in curso_novo.requisitos
        ]
    sessao.commit()
    sessao.refresh(universidade)
    hoje = datetime.now(UTC).date()
    cursos = ordenar_por_prazo(universidade.cursos, lambda c: c.prazo_inscricao)
    return UniversidadeDetalhe(
        **_universidade_publica(universidade).model_dump(),
        cursos=tuple(_curso_publico(c, hoje) for c in cursos),
    )


# ── "Minhas universidades" ───────────────────────────────


def _exigir_dono(request: Request, estudante_id: int) -> None:
    if request.state.estudante_id != estudante_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso restrito ao dono do perfil")


@router.post("/estudantes/{estudante_id}/universidades", status_code=status.HTTP_201_CREATED)
@exigir_auth
async def adicionar_curso(
    estudante_id: int, dados: AssociacaoCriar, request: Request, sessao: Sessao
) -> MinhaUniversidade:
    _exigir_dono(request, estudante_id)
    if sessao.get(Estudante, estudante_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Estudante não encontrado")
    curso = sessao.get(Curso, dados.curso_id, options=[selectinload(Curso.requisitos)])
    if curso is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Curso não encontrado")
    if sessao.get(EstudanteUniversidade, (estudante_id, dados.curso_id)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Curso já está no seu perfil")
    associacao = EstudanteUniversidade(
        estudante_id=estudante_id, curso_id=dados.curso_id, alerta_prazo=dados.alerta_prazo
    )
    sessao.add(associacao)
    sessao.commit()
    sessao.refresh(associacao)
    return _minha_universidade(associacao, sessao)


@router.get("/estudantes/{estudante_id}/universidades")
@exigir_auth
async def minhas_universidades(
    estudante_id: int, request: Request, sessao: Sessao
) -> list[MinhaUniversidade]:
    _exigir_dono(request, estudante_id)
    associacoes = sessao.scalars(
        select(EstudanteUniversidade)
        .where(EstudanteUniversidade.estudante_id == estudante_id)
        .options(
            selectinload(EstudanteUniversidade.curso).selectinload(Curso.requisitos),
            selectinload(EstudanteUniversidade.curso).selectinload(Curso.universidade),
        )
    ).all()
    ordenadas = ordenar_por_prazo(associacoes, lambda a: a.curso.prazo_inscricao)
    return [_minha_universidade(a, sessao) for a in ordenadas]


@router.patch("/estudantes/{estudante_id}/universidades/{curso_id}")
@exigir_auth
async def editar_associacao(
    estudante_id: int,
    curso_id: int,
    dados: AssociacaoEditar,
    request: Request,
    sessao: Sessao,
) -> MinhaUniversidade:
    _exigir_dono(request, estudante_id)
    associacao = sessao.get(EstudanteUniversidade, (estudante_id, curso_id))
    if associacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Curso não está no seu perfil")
    for campo, valor in dados.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(associacao, campo, valor)
    sessao.commit()
    sessao.refresh(associacao)
    return _minha_universidade(associacao, sessao)


@router.delete(
    "/estudantes/{estudante_id}/universidades/{curso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@exigir_auth
async def remover_curso(estudante_id: int, curso_id: int, request: Request, sessao: Sessao) -> None:
    _exigir_dono(request, estudante_id)
    associacao = sessao.get(EstudanteUniversidade, (estudante_id, curso_id))
    if associacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Curso não está no seu perfil")
    sessao.delete(associacao)
    sessao.commit()


def _minha_universidade(associacao: EstudanteUniversidade, sessao: Session) -> MinhaUniversidade:
    """Monta o item de "Minhas universidades": snapshots imutáveis + gap puro."""
    hoje = datetime.now(UTC).date()
    curso = associacao.curso
    requisitos = tuple(
        Requisito(categoria=r.categoria, descricao=r.descricao, obrigatorio=r.obrigatorio)
        for r in curso.requisitos
    )
    documentos = tuple(
        DocumentoResumo(
            categoria=d.categoria,
            tipo=d.tipo,
            status=calcular_status(d.data_validade, hoje),
        )
        for d in sessao.scalars(
            select(Documento).where(Documento.estudante_id == associacao.estudante_id)
        )
    )
    return MinhaUniversidade(
        curso=_curso_publico(curso, hoje),
        universidade=_universidade_publica(curso.universidade),
        status=associacao.status,
        alerta_prazo=associacao.alerta_prazo,
        adicionado_em=associacao.adicionado_em,
        gap=_gap_publico(calcular_gap(requisitos, documentos)),
    )
