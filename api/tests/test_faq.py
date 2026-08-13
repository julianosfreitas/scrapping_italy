"""Recursão sobre a árvore do FAQ — árvore rasa, profunda e vazia.

Tudo puro: nenhuma fixture de banco, nenhum mock. As árvores são montadas à
mão com dataclasses congeladas.
"""

from __future__ import annotations

import sys

from app.services.faq import (
    Categoria,
    LinhaFaq,
    Pergunta,
    achatar,
    buscar,
    caminho_ate,
    contar_perguntas,
    iterar_categorias,
    montar_arvore,
    profundidade,
    todas_perguntas,
)


def pergunta(numero: int, texto: str = "Como faço?") -> Pergunta:
    return Pergunta(id=numero, pergunta=texto, resposta=f"Resposta {numero}")


# ── árvore rasa (caso base) ──────────────────────────────


def test_categoria_folha_devolve_apenas_as_proprias_perguntas() -> None:
    folha = Categoria(id=1, nome="Vistos", perguntas=(pergunta(1), pergunta(2)))
    assert todas_perguntas(folha) == (pergunta(1), pergunta(2))
    assert profundidade(folha) == 1


def test_categoria_vazia_nao_tem_perguntas() -> None:
    """Caso base extremo: nem perguntas, nem subcategorias."""
    vazia = Categoria(id=1, nome="Sem conteúdo")
    assert todas_perguntas(vazia) == ()
    assert contar_perguntas(vazia) == 0
    assert profundidade(vazia) == 1


def test_floresta_vazia_monta_nada() -> None:
    assert montar_arvore(()) == ()


# ── árvore profunda (passo recursivo) ────────────────────


def arvore_profunda(niveis: int) -> Categoria:
    """Cadeia com uma pergunta por nível: nível N contém o nível N+1."""
    categoria = Categoria(id=niveis, nome=f"Nível {niveis}", perguntas=(pergunta(niveis),))
    for numero in range(niveis - 1, 0, -1):
        categoria = Categoria(
            id=numero,
            nome=f"Nível {numero}",
            perguntas=(pergunta(numero),),
            subcategorias=(categoria,),
        )
    return categoria


def test_recursao_desce_por_todos_os_niveis() -> None:
    raiz = arvore_profunda(5)
    assert contar_perguntas(raiz) == 5
    assert profundidade(raiz) == 5
    assert [p.id for p in todas_perguntas(raiz)] == [1, 2, 3, 4, 5]


def test_perguntas_do_no_vem_antes_das_subcategorias() -> None:
    """Ordem de profundidade: primeiro o nó, depois os filhos."""
    raiz = Categoria(
        id=1,
        nome="Documentação",
        perguntas=(pergunta(10),),
        subcategorias=(Categoria(id=2, nome="Tradução", perguntas=(pergunta(20),)),),
    )
    assert [p.id for p in todas_perguntas(raiz)] == [10, 20]


def test_ramos_irmaos_sao_visitados_na_ordem() -> None:
    raiz = Categoria(
        id=1,
        nome="Raiz",
        subcategorias=(
            Categoria(id=2, nome="A", perguntas=(pergunta(1),)),
            Categoria(id=3, nome="B", perguntas=(pergunta(2),)),
        ),
    )
    assert [p.id for p in todas_perguntas(raiz)] == [1, 2]


def test_profundidade_fica_muito_abaixo_do_limite_do_python() -> None:
    """O FAQ real tem 2–3 níveis; o limite do interpretador é ~1000 frames.

    Documenta o custo da recursão em Python: sem tail-call optimization, a
    profundidade da árvore é o número de frames empilhados.
    """
    raiz = arvore_profunda(3)
    assert profundidade(raiz) == 3
    assert profundidade(raiz) < sys.getrecursionlimit()


# ── caminho e achatamento ────────────────────────────────


def test_caminho_ate_uma_subcategoria_profunda() -> None:
    raiz = arvore_profunda(4)
    caminho = caminho_ate(raiz, 3)
    assert [c.id for c in caminho] == [1, 2, 3]


def test_caminho_para_id_inexistente_e_vazio() -> None:
    assert caminho_ate(arvore_profunda(3), 99) == ()


def test_achatar_marca_o_nivel_de_cada_categoria() -> None:
    achatada = achatar(arvore_profunda(3))
    assert [(nivel, c.id) for nivel, c in achatada] == [(0, 1), (1, 2), (2, 3)]


def test_iterar_categorias_e_um_gerador_lazy() -> None:
    gerador = iterar_categorias((arvore_profunda(3),))
    assert next(gerador).id == 1  # nada além do primeiro nó foi produzido


# ── busca ────────────────────────────────────────────────


def test_busca_ignora_acento_e_caixa() -> None:
    raiz = Categoria(
        id=1,
        nome="Vistos",
        perguntas=(Pergunta(id=1, pergunta="Preciso de tradução juramentada?", resposta="Sim"),),
    )
    assert len(buscar(raiz, "TRADUCAO")) == 1
    assert len(buscar(raiz, "traduçÃo")) == 1


def test_busca_encontra_pelo_texto_da_resposta() -> None:
    raiz = Categoria(
        id=1,
        nome="Bolsas",
        perguntas=(Pergunta(id=1, pergunta="Como pedir bolsa?", resposta="Pelo portal do DSU"),),
    )
    assert len(buscar(raiz, "dsu")) == 1


def test_busca_vazia_devolve_tudo() -> None:
    raiz = arvore_profunda(3)
    assert buscar(raiz, "   ") == todas_perguntas(raiz)


def test_busca_sem_resultado_devolve_tupla_vazia() -> None:
    assert buscar(arvore_profunda(2), "criptomoeda") == ()


# ── montagem a partir das linhas planas ──────────────────


LINHAS = (
    LinhaFaq(id=1, categoria_id=None, nome="Vistos", pergunta=None, resposta=None, ordem=0),
    LinhaFaq(id=2, categoria_id=1, nome="Estudo", pergunta=None, resposta=None, ordem=0),
    LinhaFaq(
        id=3,
        categoria_id=2,
        nome=None,
        pergunta="Qual visto para mestrado?",
        resposta="Visto D de estudo.",
        fontes=("https://vistoperitalia.esteri.it",),
        ordem=0,
    ),
    LinhaFaq(
        id=4,
        categoria_id=1,
        nome=None,
        pergunta="Quanto tempo demora?",
        resposta="De 3 a 8 semanas.",
        ordem=1,
    ),
)


def test_montar_arvore_respeita_a_hierarquia() -> None:
    (raiz,) = montar_arvore(LINHAS)
    assert raiz.nome == "Vistos"
    assert [p.id for p in raiz.perguntas] == [4]
    assert [s.nome for s in raiz.subcategorias] == ["Estudo"]
    assert contar_perguntas(raiz) == 2
    assert profundidade(raiz) == 2


def test_montar_arvore_preserva_as_fontes() -> None:
    (raiz,) = montar_arvore(LINHAS)
    assert raiz.subcategorias[0].perguntas[0].fontes == ("https://vistoperitalia.esteri.it",)


def test_montar_arvore_ignora_linha_orfa() -> None:
    """Pai inexistente não pode derrubar a página do FAQ."""
    orfa = LinhaFaq(id=9, categoria_id=404, nome=None, pergunta="Solta?", resposta="Sim", ordem=0)
    arvore = montar_arvore((*LINHAS, orfa))
    assert len(arvore) == 1  # a órfã não vira raiz, porque não é categoria


def test_montar_arvore_e_deterministica() -> None:
    assert montar_arvore(LINHAS) == montar_arvore(LINHAS)
