"""Radar de notícias: feed paginado com cache Redis e ingestão em lote."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.cache import gravar_feed_cacheado, invalidar_feed, ler_feed_cacheado
from app.core.db import get_sessao
from app.core.seguranca import exigir_auth
from app.models import Noticia
from app.schemas.noticia import FeedPagina, NoticiaCriar, NoticiaPublica, ResultadoIngestao
from app.services.feed import TAMANHO_PAGINA_MAXIMO, TAMANHO_PAGINA_PADRAO, paginar

router = APIRouter(prefix="/api/noticias", tags=["noticias"])

Sessao = Annotated[Session, Depends(get_sessao)]


def montar_feed(
    sessao: Session,
    categoria: str | None,
    fonte: str | None,
    pagina: int,
    por_pagina: int,
) -> FeedPagina:
    """Monta uma página do feed; usada pela rota JSON e pela página /radar."""
    # portável MySQL/SQLite: is_(None) ordena não-nulos primeiro (False < True)
    consulta = select(Noticia).order_by(
        Noticia.publicada_em.is_(None),
        Noticia.publicada_em.desc(),
        Noticia.coletada_em.desc(),
    )
    contagem = select(func.count()).select_from(Noticia)
    if categoria:
        consulta = consulta.where(Noticia.categoria == categoria)
        contagem = contagem.where(Noticia.categoria == categoria)
    if fonte:
        consulta = consulta.where(Noticia.fonte == fonte)
        contagem = contagem.where(Noticia.fonte == fonte)

    total = sessao.scalar(contagem) or 0
    # generator: o Result do SQLAlchemy é consumido lazy — paginar() usa
    # islice e só materializa as linhas da página pedida
    linhas = sessao.scalars(consulta)
    itens = tuple(NoticiaPublica.model_validate(n) for n in paginar(linhas, pagina, por_pagina))
    return FeedPagina(
        itens=itens,
        pagina=pagina,
        por_pagina=por_pagina,
        total=total,
        total_paginas=max(1, -(-total // por_pagina)),
    )


@router.get("")
def listar_noticias(
    sessao: Sessao,
    categoria: str | None = None,
    fonte: str | None = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
    por_pagina: Annotated[int, Query(ge=1, le=TAMANHO_PAGINA_MAXIMO)] = TAMANHO_PAGINA_PADRAO,
) -> FeedPagina:
    chave = f"{categoria or '-'}:{fonte or '-'}:{pagina}:{por_pagina}"
    cacheado = ler_feed_cacheado(chave)
    if cacheado is not None:
        return FeedPagina.model_validate(cacheado)
    feed = montar_feed(sessao, categoria, fonte, pagina, por_pagina)
    gravar_feed_cacheado(chave, feed.model_dump(mode="json"))
    return feed


@router.post("", status_code=201)
@exigir_auth
async def ingerir_noticias(
    lote: list[NoticiaCriar], request: Request, sessao: Sessao
) -> ResultadoIngestao:
    """Ingestão em lote (scraper). Dedupe pela URL única; cache invalidado ao final."""
    existentes = frozenset(
        sessao.scalars(select(Noticia.url).where(Noticia.url.in_([n.url for n in lote])))
    )
    novas = tuple({n.url: n for n in lote if n.url not in existentes}.values())  # dedupe intra-lote
    sessao.add_all(
        Noticia(
            titulo=n.titulo,
            resumo=n.resumo,
            url=n.url,
            fonte=n.fonte,
            categoria=n.categoria,
            idioma=n.idioma,
            publicada_em=n.publicada_em,
        )
        for n in novas
    )
    sessao.commit()
    invalidar_feed()
    return ResultadoIngestao(criadas=len(novas), ignoradas=len(lote) - len(novas))
