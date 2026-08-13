"""Seed do FAQ: categorias aninhadas + perguntas por curadoria manual.

Uso: ``python -m app.seed_faq`` (com o MySQL no ar e a migration aplicada).
Idempotente: a verificação é pelo nome da categoria raiz, então rodar duas
vezes não duplica a árvore.

O conteúdo veio de curadoria manual das dúvidas recorrentes do processo
Itália, com a fonte oficial de cada resposta registrada em `fontes`. A Reddit
API NÃO foi usada — depende de autorização (auth/custo) ainda não concedida.

A árvore do seed tem 3 níveis (raiz → subcategoria → pergunta), o que exercita
a recursão de `app.services.faq` com dado real.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ItemFaq


@dataclass(frozen=True)
class PerguntaSeed:
    pergunta: str
    resposta: str
    fontes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CategoriaSeed:
    nome: str
    perguntas: tuple[PerguntaSeed, ...] = ()
    subcategorias: tuple[CategoriaSeed, ...] = field(default_factory=tuple)


ARVORE_INICIAL: tuple[CategoriaSeed, ...] = (
    CategoriaSeed(
        nome="Vistos e permanência",
        perguntas=(
            PerguntaSeed(
                pergunta="Preciso de visto para estudar na Itália?",
                resposta=(
                    "Sim, para cursos com duração acima de 90 dias o estudante "
                    "brasileiro precisa do visto nacional de tipo D por motivo de "
                    "estudo, solicitado no consulado italiano da sua jurisdição "
                    "antes da viagem. Cursos curtos (até 90 dias) podem ser feitos "
                    "sem visto, na condição de turista."
                ),
                fontes=("https://vistoperitalia.esteri.it",),
            ),
        ),
        subcategorias=(
            CategoriaSeed(
                nome="Visto de estudo (tipo D)",
                perguntas=(
                    PerguntaSeed(
                        pergunta=("Quais documentos o consulado costuma pedir para o visto?"),
                        resposta=(
                            "Em geral: passaporte válido, formulário de solicitação, "
                            "foto, comprovante de pré-inscrição no Universitaly, carta "
                            "de aceite da universidade, comprovação de meios financeiros, "
                            "seguro-saúde com cobertura na Itália e comprovante de "
                            "alojamento. A lista exata varia por consulado — confirme "
                            "sempre na página da sua jurisdição."
                        ),
                        fontes=(
                            "https://vistoperitalia.esteri.it",
                            "https://www.universitaly.it",
                        ),
                    ),
                    PerguntaSeed(
                        pergunta="Quanto tempo demora a análise do visto?",
                        resposta=(
                            "O prazo varia bastante por consulado e por época do ano; "
                            "nos meses de pico (julho a setembro) costuma ser mais "
                            "longo. Por isso o recomendado é iniciar o processo assim "
                            "que sair a carta de aceite, sem esperar o prazo final."
                        ),
                        fontes=("https://vistoperitalia.esteri.it",),
                    ),
                ),
            ),
            CategoriaSeed(
                nome="Permesso di soggiorno",
                perguntas=(
                    PerguntaSeed(
                        pergunta="O que preciso fazer ao chegar na Itália?",
                        resposta=(
                            "Solicitar o permesso di soggiorno per studio dentro de 8 "
                            "dias úteis da chegada. O pedido é feito pelo kit postal "
                            "retirado nos Correios (Poste Italiane) habilitados, e "
                            "depois há uma convocação na Questura para coleta de "
                            "impressões digitais."
                        ),
                        fontes=("https://www.portaleimmigrazione.it",),
                    ),
                    PerguntaSeed(
                        pergunta="O permesso precisa ser renovado todo ano?",
                        resposta=(
                            "O permesso per studio é normalmente emitido com validade "
                            "anual e renovado enquanto durar o curso, mediante "
                            "comprovação de matrícula ativa e de aproveitamento "
                            "acadêmico. A renovação deve ser pedida antes do vencimento."
                        ),
                        fontes=("https://www.portaleimmigrazione.it",),
                    ),
                ),
            ),
        ),
    ),
    CategoriaSeed(
        nome="Documentação acadêmica",
        subcategorias=(
            CategoriaSeed(
                nome="Tradução e legalização",
                perguntas=(
                    PerguntaSeed(
                        pergunta="O que é a Dichiarazione di Valore?",
                        resposta=(
                            "É um documento emitido pelo consulado italiano que "
                            "descreve o valor legal do seu diploma no país de origem: "
                            "duração do curso, natureza da instituição e a que "
                            "corresponde no sistema italiano. Muitas universidades "
                            "aceitam, no lugar dela, o Statement of Comparability do "
                            "CIMEA — confirme o que o seu curso exige antes de gastar "
                            "com o processo consular."
                        ),
                        fontes=("https://www.cimea.it",),
                    ),
                    PerguntaSeed(
                        pergunta="Meus documentos precisam de apostila de Haia?",
                        resposta=(
                            "Sim. Brasil e Itália são signatários da Convenção de Haia, "
                            "então diplomas e históricos são apostilados em cartório "
                            "habilitado no Brasil e depois traduzidos por tradutor "
                            "juramentado. A tradução também costuma precisar de apostila."
                        ),
                        fontes=("https://www.cnj.jus.br/poder-judiciario/apostila-da-haia/",),
                    ),
                ),
            ),
            CategoriaSeed(
                nome="Reconhecimento do diploma",
                perguntas=(
                    PerguntaSeed(
                        pergunta="Preciso revalidar meu diploma brasileiro?",
                        resposta=(
                            "Para ingressar em um mestrado, normalmente não: a "
                            "universidade faz uma avaliação de equivalência para fins "
                            "de admissão, com base na Dichiarazione di Valore ou no "
                            "documento do CIMEA. A revalidação formal só é necessária "
                            "para exercer profissões regulamentadas na Itália."
                        ),
                        fontes=("https://www.cimea.it",),
                    ),
                ),
            ),
        ),
    ),
    CategoriaSeed(
        nome="Admissão e universidades",
        perguntas=(
            PerguntaSeed(
                pergunta="O que é o Universitaly e por que ele é obrigatório?",
                resposta=(
                    "É o portal oficial do Ministério da Universidade onde o estudante "
                    "estrangeiro faz a pré-inscrição no curso escolhido. O comprovante "
                    "gerado ali é o que vincula sua candidatura ao pedido de visto no "
                    "consulado — sem ele, o visto de estudo não avança."
                ),
                fontes=("https://www.universitaly.it",),
            ),
        ),
        subcategorias=(
            CategoriaSeed(
                nome="Requisitos de idioma",
                perguntas=(
                    PerguntaSeed(
                        pergunta="Preciso falar italiano para fazer mestrado na Itália?",
                        resposta=(
                            "Depende do idioma do curso. Cursos ministrados em italiano "
                            "costumam exigir nível B2 comprovado (CILS, CELI, PLIDA ou "
                            "teste da própria universidade). Há uma oferta grande de "
                            "mestrados inteiramente em inglês, que pedem IELTS ou TOEFL "
                            "no lugar. Mesmo nesses, o italiano do dia a dia faz muita "
                            "diferença na vida prática."
                        ),
                        fontes=("https://www.universitaly.it",),
                    ),
                ),
            ),
        ),
    ),
    CategoriaSeed(
        nome="Dinheiro e vida prática",
        subcategorias=(
            CategoriaSeed(
                nome="Bolsas e taxas",
                perguntas=(
                    PerguntaSeed(
                        pergunta="Como funcionam as bolsas do DSU?",
                        resposta=(
                            "O Diritto allo Studio Universitario é regional: cada região "
                            "publica seu próprio bando anual, com bolsa, isenção de taxas "
                            "e às vezes moradia e refeitório. A concessão é por faixa de "
                            "renda e por mérito acadêmico, e o prazo costuma cair entre "
                            "julho e setembro — perder o bando significa esperar o ano "
                            "seguinte."
                        ),
                        fontes=("https://www.laziodisco.it",),
                    ),
                    PerguntaSeed(
                        pergunta="Quanto custam as taxas universitárias?",
                        resposta=(
                            "Nas universidades públicas as taxas são progressivas: o "
                            "valor depende da renda familiar declarada no ISEE (ou no "
                            "ISEE parificato, versão para quem tem renda no exterior). "
                            "Faixas de renda mais baixas chegam à isenção total, o que "
                            "torna o custo bem menor do que a média de outros destinos."
                        ),
                        fontes=("https://www.laziodisco.it",),
                    ),
                ),
            ),
            CategoriaSeed(
                nome="Moradia e burocracia local",
                perguntas=(
                    PerguntaSeed(
                        pergunta="O que é o codice fiscale e quando preciso dele?",
                        resposta=(
                            "É o equivalente italiano ao CPF, necessário para praticamente "
                            "tudo: assinar contrato de aluguel, abrir conta em banco, "
                            "fazer matrícula e contratar plano de celular. Pode ser "
                            "solicitado no consulado ainda no Brasil ou na Agenzia delle "
                            "Entrate depois da chegada."
                        ),
                        fontes=("https://www.agenziaentrate.gov.it",),
                    ),
                    PerguntaSeed(
                        pergunta="Vale a pena procurar moradia antes de viajar?",
                        resposta=(
                            "O comprovante de alojamento costuma ser pedido no visto, "
                            "então algum endereço você precisa ter. O caminho mais seguro "
                            "é começar por residência estudantil da universidade ou do "
                            "DSU e, já na Itália, procurar contrato de longo prazo — "
                            "fechar aluguel à distância é onde mais aparecem golpes."
                        ),
                        fontes=("https://www.laziodisco.it",),
                    ),
                ),
            ),
        ),
    ),
)


def _inserir(categoria: CategoriaSeed, pai_id: int | None, sessao: Session) -> int:
    """Insere a categoria e, RECURSIVAMENTE, tudo que está abaixo dela.

    Espelha a forma da árvore: a mesma função trata raiz e subcategoria.
    """
    no = ItemFaq(categoria_id=pai_id, nome=categoria.nome, ordem=0)
    sessao.add(no)
    sessao.flush()  # precisa do id para pendurar os filhos

    for ordem, pergunta in enumerate(categoria.perguntas):
        sessao.add(
            ItemFaq(
                categoria_id=no.id,
                pergunta=pergunta.pergunta,
                resposta=pergunta.resposta,
                fontes=list(pergunta.fontes),
                ordem=ordem,
            )
        )
    for subcategoria in categoria.subcategorias:
        _inserir(subcategoria, no.id, sessao)
    return no.id


def executar_seed() -> int:
    """Insere as categorias raiz que ainda não existem; devolve quantas criou."""
    from app.core.db import get_sessionmaker

    with get_sessionmaker()() as sessao:
        existentes = frozenset(
            sessao.scalars(select(ItemFaq.nome).where(ItemFaq.categoria_id.is_(None))).all()
        )
        novas = tuple(c for c in ARVORE_INICIAL if c.nome not in existentes)
        for categoria in novas:
            _inserir(categoria, None, sessao)
        sessao.commit()
        return len(novas)


if __name__ == "__main__":
    criadas = executar_seed()
    print(f"Seed do FAQ concluído: {criadas} categoria(s) raiz criada(s).")
