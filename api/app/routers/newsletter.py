"""Newsletter: inscrições públicas, curadoria diária e arquivo de edições.

Divisão da regra 2 do CLAUDE.md: este router faz TODO o I/O (banco, Redis,
relógio) e delega o cálculo da edição para `app.services.curadoria`, que é
puro. A rota de curadoria é autenticada — quem a dispara é o job agendado,
com as mesmas credenciais usadas pela ingestão do Radar na Sprint 4.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_sessao
from app.core.fila import publicar_edicao
from app.core.seguranca import exigir_auth
from app.models import EdicaoNewsletter, InscricaoNewsletter, Noticia
from app.schemas.newsletter import (
    EdicaoArquivada,
    EdicaoPublica,
    InscricaoCriar,
    InscricaoPublica,
    ItemEdicao,
    TopicoEdicao,
)
from app.services.curadoria import JANELA_HORAS, Edicao, NoticiaResumo, curar

router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])

Sessao = Annotated[Session, Depends(get_sessao)]


# ── inscrições (públicas) ────────────────────────────────


@router.post("/inscricoes", status_code=status.HTTP_201_CREATED)
def inscrever(dados: InscricaoCriar, sessao: Sessao) -> InscricaoPublica:
    """Inscrição pública. Reinscrever um e-mail cancelado apenas o reativa."""
    email = dados.email.strip().lower()
    inscricao = sessao.scalar(select(InscricaoNewsletter).where(InscricaoNewsletter.email == email))
    if inscricao is None:
        inscricao = InscricaoNewsletter(email=email, ativo=True)
        sessao.add(inscricao)
    else:
        inscricao.ativo = True
    sessao.commit()
    sessao.refresh(inscricao)
    return InscricaoPublica.model_validate(inscricao)


@router.post("/inscricoes/cancelar")
def cancelar(dados: InscricaoCriar, sessao: Sessao) -> InscricaoPublica:
    """Cancelamento público (soft delete: `ativo=False`, histórico preservado)."""
    email = dados.email.strip().lower()
    inscricao = sessao.scalar(select(InscricaoNewsletter).where(InscricaoNewsletter.email == email))
    if inscricao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "E-mail não inscrito")
    inscricao.ativo = False
    sessao.commit()
    sessao.refresh(inscricao)
    return InscricaoPublica.model_validate(inscricao)


# ── curadoria (autenticada — job das 08h30) ──────────────


def _para_resumo(noticia: Noticia) -> NoticiaResumo:
    """ORM → snapshot congelado que a função pura entende."""
    return NoticiaResumo(
        titulo=noticia.titulo,
        url=noticia.url,
        fonte=noticia.fonte,
        categoria=noticia.categoria,
        coletada_em=noticia.coletada_em,
        resumo=noticia.resumo,
        publicada_em=noticia.publicada_em,
    )


def _para_schema(edicao: Edicao, data_referencia: date) -> EdicaoPublica:
    """Edição (dataclass pura) → schema Pydantic serializável para a fila."""
    return EdicaoPublica(
        data=data_referencia,
        gerada_em=edicao.data_referencia,
        total=edicao.total,
        topicos=tuple(
            TopicoEdicao(
                chave=topico.chave,
                rotulo=topico.rotulo,
                itens=tuple(
                    ItemEdicao(
                        titulo=item.titulo,
                        url=item.url,
                        fonte=item.fonte,
                        resumo=item.resumo,
                        publicada_em=item.publicada_em,
                    )
                    for item in topico.itens
                ),
            )
            for topico in edicao.topicos
        ),
    )


@router.post("/curadoria", status_code=status.HTTP_201_CREATED)
@exigir_auth
async def executar_curadoria(
    request: Request,
    sessao: Sessao,
    janela_horas: Annotated[int, Query(ge=1, le=720)] = JANELA_HORAS,
) -> EdicaoPublica:
    """Monta a edição do dia, arquiva no banco e publica na fila do Redis.

    Idempotente por dia: rodar de novo na mesma data ATUALIZA a edição
    (a coluna `data` é única), em vez de criar uma segunda.
    """
    agora = datetime.now(UTC).replace(tzinfo=None)
    noticias = tuple(_para_resumo(n) for n in sessao.scalars(select(Noticia).order_by(Noticia.id)))
    edicao = curar(noticias, agora, janela_horas=janela_horas)
    publica = _para_schema(edicao, agora.date())
    payload: dict[str, Any] = publica.model_dump(mode="json")

    arquivada = sessao.scalar(select(EdicaoNewsletter).where(EdicaoNewsletter.data == agora.date()))
    if arquivada is None:
        sessao.add(EdicaoNewsletter(data=agora.date(), conteudo=payload))
    else:
        arquivada.conteudo = payload
        arquivada.enviada_em = None  # edição refeita volta à fila
    sessao.commit()

    publicar_edicao(payload)
    return publica


# ── arquivo de edições (público) ─────────────────────────


@router.get("/edicoes")
def listar_edicoes(sessao: Sessao) -> tuple[EdicaoArquivada, ...]:
    edicoes = sessao.scalars(select(EdicaoNewsletter).order_by(EdicaoNewsletter.data.desc())).all()
    return tuple(
        EdicaoArquivada(
            data=e.data,
            enviada_em=e.enviada_em,
            total=int(e.conteudo.get("total", 0)),
        )
        for e in edicoes
    )


@router.get("/edicoes/{data_edicao}")
def obter_edicao(data_edicao: date, sessao: Sessao) -> EdicaoPublica:
    edicao = sessao.scalar(select(EdicaoNewsletter).where(EdicaoNewsletter.data == data_edicao))
    if edicao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Edição não encontrada")
    return EdicaoPublica.model_validate(edicao.conteudo)


@router.post("/edicoes/{data_edicao}/enviada")
@exigir_auth
async def marcar_enviada(data_edicao: date, request: Request, sessao: Sessao) -> EdicaoArquivada:
    """Log de envio: o worker .NET confirma o disparo da edição."""
    edicao = sessao.scalar(select(EdicaoNewsletter).where(EdicaoNewsletter.data == data_edicao))
    if edicao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Edição não encontrada")
    edicao.enviada_em = datetime.now(UTC).replace(tzinfo=None)
    sessao.commit()
    sessao.refresh(edicao)
    return EdicaoArquivada(
        data=edicao.data,
        enviada_em=edicao.enviada_em,
        total=int(edicao.conteudo.get("total", 0)),
    )


@router.get("/inscritos")
@exigir_auth
async def listar_inscritos(request: Request, sessao: Sessao) -> tuple[str, ...]:
    """Destinatários ativos — consumido pelo worker .NET antes do disparo."""
    return tuple(
        sessao.scalars(
            select(InscricaoNewsletter.email)
            .where(InscricaoNewsletter.ativo.is_(True))
            .order_by(InscricaoNewsletter.email)
        )
    )
