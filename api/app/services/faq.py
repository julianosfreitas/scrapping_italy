"""FAQ — RECURSÃO sobre a árvore de categorias (conceito 15, exemplo central).

Módulo 100% puro: nenhuma função aqui toca banco, rede ou relógio. O router
lê as linhas da tabela `faq`, monta a árvore imutável com `montar_arvore` e
delega toda a navegação para cá.

Por que recursão e não um loop? Porque a estrutura é recursiva por natureza:
uma categoria contém perguntas E subcategorias, que por sua vez contêm
perguntas e subcategorias, sem profundidade fixa. Um loop precisaria de uma
pilha explícita — que é justamente o que a recursão já dá de graça, com o
caso base ("categoria sem subcategorias") escrito em uma linha.

LIMITE DO PYTHON: o interpretador não faz *tail-call optimization*, então
cada chamada consome um frame e o limite padrão é ~1000 (`sys.getrecursionlimit`).
Para uma árvore de FAQ isso é irrelevante — a profundidade real é 2 ou 3, e
mil níveis de subcategoria não existem em nenhum FAQ do mundo. Em estruturas
que podem ser profundas de verdade (um filesystem, por exemplo), a versão
iterativa com pilha explícita seria a escolha correta. `profundidade` abaixo
mede exatamente esse número e é o teste que documenta o limite.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Pergunta:
    """Folha da árvore — imutável desde o nascimento."""

    id: int
    pergunta: str
    resposta: str
    fontes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Categoria:
    """Nó interno: perguntas próprias + subcategorias (recursivo por definição)."""

    id: int
    nome: str
    perguntas: tuple[Pergunta, ...] = ()
    subcategorias: tuple[Categoria, ...] = field(default_factory=tuple)


# ── as funções recursivas (o coração do conceito 15) ─────


def todas_perguntas(categoria: Categoria) -> tuple[Pergunta, ...]:
    """Todas as perguntas da categoria e de TODAS as subcategorias, em profundidade.

    CASO BASE: categoria sem subcategorias -> devolve apenas as próprias
    perguntas (a comprehension sobre `()` não produz nada e a recursão para).
    PASSO RECURSIVO: concatena as próprias perguntas com o resultado da mesma
    função aplicada a cada subcategoria.
    """
    return categoria.perguntas + tuple(
        pergunta
        for subcategoria in categoria.subcategorias
        for pergunta in todas_perguntas(subcategoria)
    )


def contar_perguntas(categoria: Categoria) -> int:
    """Quantas perguntas a subárvore contém. Mesma forma, acumulando números."""
    return len(categoria.perguntas) + sum(
        contar_perguntas(subcategoria) for subcategoria in categoria.subcategorias
    )


def profundidade(categoria: Categoria) -> int:
    """Altura da subárvore: 1 para uma folha, 1 + a maior altura dos filhos.

    É esta função que dá a medida do limite de recursão do Python: o número
    de frames empilhados no pior caminho é exatamente a profundidade.
    """
    if not categoria.subcategorias:
        return 1
    return 1 + max(profundidade(subcategoria) for subcategoria in categoria.subcategorias)


def achatar(categoria: Categoria, nivel: int = 0) -> tuple[tuple[int, Categoria], ...]:
    """Lineariza a árvore em (nível, categoria) — alimenta o menu indentado da página."""
    return ((nivel, categoria),) + tuple(
        item
        for subcategoria in categoria.subcategorias
        for item in achatar(subcategoria, nivel + 1)
    )


def caminho_ate(categoria: Categoria, alvo_id: int) -> tuple[Categoria, ...]:
    """Trilha da raiz até a categoria de id `alvo_id`; vazio se não estiver na subárvore.

    Busca em profundidade recursiva: o `next` para na primeira subárvore que
    devolve um caminho não vazio — nenhuma outra é visitada.
    """
    if categoria.id == alvo_id:
        return (categoria,)
    return next(
        (
            (categoria, *abaixo)
            for subcategoria in categoria.subcategorias
            if (abaixo := caminho_ate(subcategoria, alvo_id))
        ),
        (),
    )


def buscar(categoria: Categoria, termo: str) -> tuple[Pergunta, ...]:
    """Filtra, na subárvore inteira, as perguntas que casam com o termo.

    Compõe a recursão (`todas_perguntas`) com um `filter` — a busca não
    precisa saber que a estrutura é uma árvore.
    """
    normalizado = normalizar(termo)
    if not normalizado:
        return todas_perguntas(categoria)
    return tuple(
        filter(
            lambda p: normalizado in normalizar(f"{p.pergunta} {p.resposta}"),
            todas_perguntas(categoria),
        )
    )


def normalizar(texto: str) -> str:
    """'Visto de Estudo' -> 'visto de estudo' (sem acento): busca tolerante."""
    sem_acento = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").lower()
    )
    return " ".join(sem_acento.split())


# ── montagem da árvore a partir das linhas planas ────────


@dataclass(frozen=True)
class LinhaFaq:
    """Snapshot imutável de uma linha da tabela `faq` (o router converte o ORM)."""

    id: int
    categoria_id: int | None
    nome: str | None
    pergunta: str | None
    resposta: str | None
    fontes: tuple[str, ...] = ()
    ordem: int = 0


def montar_arvore(linhas: Iterable[LinhaFaq]) -> tuple[Categoria, ...]:
    """Linhas planas -> floresta imutável. Também recursiva, pela mesma razão.

    Função pura: a mesma lista de linhas produz sempre a mesma árvore. Linhas
    órfãs (pai inexistente) são simplesmente ignoradas, então um dado ruim no
    banco não derruba a página.
    """
    materializadas = tuple(linhas)
    filhos_de: dict[int | None, tuple[LinhaFaq, ...]] = {}
    for linha in sorted(materializadas, key=lambda linha: (linha.ordem, linha.id)):
        filhos_de[linha.categoria_id] = (*filhos_de.get(linha.categoria_id, ()), linha)

    ids = {linha.id for linha in materializadas}
    raizes = tuple(
        linha
        for pai, linhas_do_pai in filhos_de.items()
        if pai is None or pai not in ids
        for linha in linhas_do_pai
    )
    return tuple(_para_categoria(linha, filhos_de) for linha in raizes if linha.resposta is None)


def _para_categoria(
    linha: LinhaFaq, filhos_de: dict[int | None, tuple[LinhaFaq, ...]]
) -> Categoria:
    """Passo recursivo da montagem: um nó vira Categoria com os filhos já montados."""
    filhos = filhos_de.get(linha.id, ())
    return Categoria(
        id=linha.id,
        nome=linha.nome or linha.pergunta or "",
        perguntas=tuple(
            Pergunta(
                id=filho.id,
                pergunta=filho.pergunta or "",
                resposta=filho.resposta,
                fontes=filho.fontes,
            )
            for filho in filhos
            if filho.resposta is not None
        ),
        subcategorias=tuple(
            _para_categoria(filho, filhos_de) for filho in filhos if filho.resposta is None
        ),
    )


def iterar_categorias(categorias: Iterable[Categoria]) -> Iterator[Categoria]:
    """GERADOR recursivo: percorre a floresta inteira sob demanda (conceito 10)."""
    for categoria in categorias:
        yield categoria
        yield from iterar_categorias(categoria.subcategorias)
