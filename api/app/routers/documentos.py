"""Cofre de documentos: upload, listagem e download com URL assinada.

Todo o cálculo (status, sanitização, validação de upload) é delegado às
funções puras de ``app/services/documentos.py``; aqui fica apenas o I/O
(banco, disco, relógio, HTTP).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_sessao
from app.core.seguranca import criar_token, decodificar_token, exigir_auth
from app.models import CategoriaDocumento, Documento, Estudante
from app.schemas.documento import DocumentoPublico, UrlAssinada
from app.services.documentos import (
    calcular_status,
    sanitizar_nome_arquivo,
    validar_upload,
)

router = APIRouter(prefix="/api", tags=["documentos"])

Sessao = Annotated[Session, Depends(get_sessao)]

VALIDADE_URL_ASSINADA_SEGUNDOS = 300

_TIPOS_MIME = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}


def _para_publico(documento: Documento, data_atual: date) -> DocumentoPublico:
    """Monta o schema de saída com o status derivado (nunca lido do banco)."""
    return DocumentoPublico(
        id=documento.id,
        estudante_id=documento.estudante_id,
        categoria=documento.categoria,
        tipo=documento.tipo,
        nome_arquivo=documento.arquivo_url.rsplit("_", 1)[-1],
        data_validade=documento.data_validade,
        status=calcular_status(documento.data_validade, data_atual),
        criado_em=documento.criado_em,
    )


def _exigir_dono(request: Request, estudante_id: int) -> None:
    if request.state.estudante_id != estudante_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso restrito ao dono do cofre")


def _buscar_documento(sessao: Session, documento_id: int) -> Documento:
    documento = sessao.get(Documento, documento_id)
    if documento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento não encontrado")
    return documento


@router.post("/estudantes/{estudante_id}/documentos", status_code=status.HTTP_201_CREATED)
@exigir_auth
async def enviar_documento(
    estudante_id: int,
    request: Request,
    sessao: Sessao,
    arquivo: UploadFile,
    categoria: Annotated[CategoriaDocumento, Form()],
    tipo: Annotated[str, Form(min_length=2, max_length=80)],
    data_validade: Annotated[date | None, Form()] = None,
) -> DocumentoPublico:
    _exigir_dono(request, estudante_id)
    if sessao.get(Estudante, estudante_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Estudante não encontrado")

    settings = get_settings()
    conteudo = await arquivo.read(settings.upload_max_bytes + 1)
    erro = validar_upload(arquivo.filename or "", len(conteudo), settings.upload_max_bytes)
    if erro is not None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, erro)

    nome_seguro = sanitizar_nome_arquivo(arquivo.filename or "")
    caminho_relativo = f"{estudante_id}/{uuid.uuid4().hex}_{nome_seguro}"
    destino = Path(settings.upload_dir) / caminho_relativo
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(conteudo)

    documento = Documento(
        estudante_id=estudante_id,
        categoria=categoria,
        tipo=tipo,
        arquivo_url=caminho_relativo,
        data_validade=data_validade,
    )
    sessao.add(documento)
    sessao.commit()
    sessao.refresh(documento)
    return _para_publico(documento, datetime.now(UTC).date())


@router.get("/estudantes/{estudante_id}/documentos")
@exigir_auth
async def listar_documentos(
    estudante_id: int, request: Request, sessao: Sessao
) -> list[DocumentoPublico]:
    _exigir_dono(request, estudante_id)
    documentos = sessao.scalars(
        select(Documento)
        .where(Documento.estudante_id == estudante_id)
        .order_by(Documento.categoria, Documento.criado_em)
    ).all()
    hoje = datetime.now(UTC).date()
    return [_para_publico(d, hoje) for d in documentos]


@router.get("/documentos/{documento_id}/url-assinada")
@exigir_auth
async def gerar_url_assinada(documento_id: int, request: Request, sessao: Sessao) -> UrlAssinada:
    """URL de download autenticada: token assinado, de escopo único e curto."""
    documento = _buscar_documento(sessao, documento_id)
    _exigir_dono(request, documento.estudante_id)
    token = criar_token(
        sub=str(documento.estudante_id),
        segredo=get_settings().jwt_segredo,
        expira_em=timedelta(seconds=VALIDADE_URL_ASSINADA_SEGUNDOS),
        claims_extras={"escopo": "download", "doc": documento.id},
    )
    return UrlAssinada(
        url=f"/api/documentos/{documento.id}/download?token={token}",
        expira_em_segundos=VALIDADE_URL_ASSINADA_SEGUNDOS,
    )


@router.get("/documentos/{documento_id}/download")
def baixar_documento(documento_id: int, token: str, sessao: Sessao) -> FileResponse:
    """Serve o arquivo somente com um token assinado válido para ESTE documento."""
    payload = decodificar_token(token, get_settings().jwt_segredo)
    if payload.get("escopo") != "download" or payload.get("doc") != documento_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token não autoriza este download")
    documento = _buscar_documento(sessao, documento_id)
    caminho = Path(get_settings().upload_dir) / documento.arquivo_url
    if not caminho.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo não encontrado no cofre")
    extensao = documento.arquivo_url.rsplit(".", 1)[-1].lower()
    return FileResponse(
        caminho,
        media_type=_TIPOS_MIME.get(extensao, "application/octet-stream"),
        filename=documento.arquivo_url.rsplit("_", 1)[-1],
    )
