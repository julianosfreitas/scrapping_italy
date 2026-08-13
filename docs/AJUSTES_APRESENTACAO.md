# Ajustes da apresentação — conformidade, layout e roteiro

Documento de trabalho sobre `PF-Python-Ponte-Italia.pdf` (53 slides).
Objetivo: garantir os **3,0 pontos da apresentação** e preparar os **7,0
pontos das perguntas**.

Tudo aqui foi medido no PDF entregue, não estimado. O script de verificação
está em `docs/` e pode ser rodado de novo depois das correções.

---

## 1. Conformidade com os critérios de pontuação

| Critério | Situação | Risco |
|---|---|---|
| Fonte ≥ 16pt no CORPO | ❌ **12 slides violam** | −1,0 |
| Numeração no rodapé | ✅ presente nos 53 slides | — |
| Slides de terceiros/IA identificados | ⚠️ **slide 53 está com placeholder** | −1,0 ou **zero** |
| Contraste / legibilidade | ✅ com 2 ressalvas | −1,0 |
| Duração 1h20 | ⚠️ sem plano de tempo | — |

### 1.1 O problema mais grave: o slide 53 (créditos)

Hoje o slide 53 diz:

> `[n]` Reservado para slides gerados por IA: indicar a IA usada e o prompt
> exato. *Ex.: [1] ChatGPT — "gerar diagrama de arquitetura em camadas".*

Isso é um **texto de instrução, não uma atribuição**. Do jeito que está, a
apresentação declara que existe conteúdo de IA e ao mesmo tempo não o
identifica. Pela regra:

- 1 slide não identificado → **−1,0**
- mais de 1 slide não identificado → **nota final ZERO (plágio)**

**Só você sabe quais slides foram gerados com auxílio de IA.** Percorra os 53
e classifique cada um. Depois substitua o slide 53 por uma lista real. Se
nenhum slide foi gerado por IA, remova o parágrafo do placeholder — deixá-lo
lá levanta a dúvida sem necessidade.

**Formato exigido, com exemplos preenchidos:**

```
FONTES

[1]  Claude (Anthropic) — "gerar um slide comparando a versão funcional e a
     versão imperativa do cálculo de gap, lado a lado, com código Python"
[2]  ChatGPT (OpenAI) — "criar linha do tempo visual: cálculo-λ 1936, Lisp
     1958, Haskell 1990, Python hoje"
[3]  Slide 12 de https://www.exemplo.edu/curso/aula05.ppt

Demais slides: autoria própria, a partir do código do projeto Ponte Italia
(github.com/julianosfreitas/scrapping_italy).
```

E no rodapé de CADA slide que usou aquele recurso, o número entre colchetes:
`[1]`, ao lado da numeração que já existe.

> Recomendação honesta: prefira declarar a mais. Declarar uma ajuda de IA que
> talvez nem precisasse de citação custa zero pontos; deixar de declarar duas
> custa a nota inteira.

---

## 2. Os 12 slides com fonte abaixo de 16pt

Medição direta dos operadores `Tf` do PDF. **Rodapé não conta** (9pt e
11,04pt são o rodapé e estão liberados pela regra).

| Slide | Tamanhos no corpo | Texto afetado | Correção |
|---|---|---|---|
| 1 | 14,04 | "Faculdade Nova Roma" | subir para 18 |
| 5 | 15,0 | legendas dos dois cartões | subir para 18 |
| 6 | 15,0 | descrições da linha do tempo | subir para 18 |
| 11 | 15,0 / 15,02 | descrições dos 3 cartões | subir para 18 |
| 32 | 15,0 | bullets de `lru_cache` | subir para 18 |
| 36 | 15,0 / 15,02 | notas do `@cronometrar` | subir para 18 |
| 37 | 15,0 | notas do `retry_backoff` | subir para 18 |
| 40 | **12,96** | "Exemplo previsto · Sprint 4" | ver §3 — texto sai |
| 42 | **12,96** / 15,0 | "Exemplo previsto · Sprint 6" | ver §3 — texto sai |
| 44 | 14,04 / 15,0 | rótulos do diagrama de camadas | subir para 18 |
| 45 | **12,0** / 15,0 | "(trecho condensado)" + bullets | subir para 18 |
| 53 | 15,0 | texto do placeholder | reescrever (§1.1) |

### 2.1 A armadilha do 15,96pt

Existem **442 ocorrências de 15,96pt / 15,98pt** no deck. É o corpo padrão:
foi escrito como 16pt e o PDF saiu com um fator de escala de ~0,25%, o que
derrubou para 15,96.

No PowerPoint a caixa mostra 16. Mas se o avaliador medir **no PDF**, lê
15,96 — abaixo do mínimo. É um risco de 1,0 ponto por uma diferença de
0,04pt.

**Correção recomendada: adotar 18pt como corpo padrão de todo o deck.** Além
de eliminar a ambiguidade com folga, 18pt projeta melhor numa sala.

### 2.2 Escala tipográfica sugerida

| Elemento | Hoje | Passar para |
|---|---|---|
| Título do slide | 34–40 | manter |
| Sobretítulo (BLOCO 1 · PILARES) | 16 | 18 |
| Corpo / bullets | 15,96 | **18** |
| Legenda de cartão | 15,0 | **18** |
| Código | 15,96–17 | **18 mono** |
| Rodapé | 9 / 11 | manter (liberado) |

---

## 3. Conteúdo desatualizado — os slides "previsto"

Três slides prometem coisas que **já foram implementadas** desde então. Se um
avaliador abrir o repositório, a divergência pesa contra.

| Slide | Diz hoje | Realidade |
|---|---|---|
| 40 | "Exemplo previsto · Sprint 4 Radar" | Implementado: `iterar_itens_rss`, `paginar`, `janelas` |
| 42 | "Exemplo previsto · Sprint 6 FAQ" | Implementado: `todas_perguntas`, `profundidade`, `caminho_ate` |
| 46 | "Generators (previsto)" e "Recursão (previsto)" | Ambos ✅ implementados e testados |

**Correção do slide 46** — a tabela "Cada conceito vive em código real" passa a:

| Conceito | Onde |
|---|---|
| Generators / lazy | `iterar_itens_rss`, `paginar`, `janelas` |
| Recursão | `todas_perguntas`, `montar_arvore` (FAQ) |
| reduce | `estatisticas`, `agrupar_por_topico` |

E vale acrescentar a linha que hoje não existe: **16/16 conceitos
documentados** em `docs/RELATORIO_FP.md`.

---

## 4. Defeitos de layout (código estourando a caixa)

Três slides têm linha de código que vaza para fora do bloco escuro — fica
visualmente quebrado e prejudica a leitura:

| Slide | Onde quebra | Correção |
|---|---|---|
| 10 | `total += x  # efeito colateral` — a palavra "colateral" cai fora | encurtar o comentário para `# efeito` |
| 48 | `if doc.status == "ok": # status velho` — "velho" cai fora | trocar por `# status defasado` em linha própria |
| 45 | bloco de `calcular_gap` muito cheio | cortar 2 linhas; o slide já diz "(trecho condensado)" |

Regra prática: **máximo de 52 caracteres por linha de código** num slide
16:9 com fonte 18 mono. Prefira quebrar a linha a diminuir a fonte.

---

## 5. Contraste — duas ressalvas

O esquema geral está correto: grafite `#1F2933` sobre off-white `#FAFAF7`
(~14:1) e branco sobre navy `#16232B` (~15:1). Sem risco.

Duas exceções a revisar:

1. **Comentários dentro dos blocos de código.** O cinza usado nos comentários
   (`# pura`, `# impura: depende de estado externo`) sobre o fundo navy fica
   perto do limite de 4.5:1. Clarear o cinza dos comentários resolve.
2. **Slide 49** usa laranja (`#B45309`) para os títulos dos quatro cartões
   sobre fundo cinza-claro. Passa, mas é o par mais fraco do deck — se puder,
   escurecer um tom.

---

## 6. Onde entram os prints do sistema

12 capturas em `docs/screenshots/`, em 2880×1800 (retina), prontas para
projeção. Sugestão de inserção — **todas de autoria própria, não precisam de
`[n]`**:

| Print | Slide sugerido | Por que ali |
|---|---|---|
| `03-perfil-cofre.png` | **após o 45** (`calcular_gap`) | mostra o resultado da função pura na tela: 33% pronto, ✓ atendido, ✗ faltando |
| `06-radar.png` | após o 40 (generators) | o feed paginado que os generators alimentam |
| `07-radar-filtro-vistos.png` | junto do anterior | o `filter` do pipeline em ação |
| `09-newsletter-edicao.png` | após o slide de `reduce` | a edição agrupada nos 10 tópicos |
| `10-ajuda.png` | após o 42 (recursão) | a árvore de categorias renderizada |
| `11-ajuda-categoria.png` | junto do anterior | `caminho_ate` gerando a trilha |
| `12-swagger.png` | no bloco do projeto | evidência de que a API é real |
| `01-home.png` | slide 43 (abertura do bloco 9) | contexto do produto |
| `02`, `04`, `05`, `08` | reserva | usar se sobrar tempo |

**Slide novo que vale muito a pena** — logo depois do `03-perfil-cofre.png`:

> **Título:** Da função pura à tela
> **Corpo (18pt):** o mesmo `calcular_gap` que roda em 14 testes sem banco é o
> que desenha esta barra de 33%. Entrada: 3 requisitos + 2 documentos. Saída:
> um `Gap` congelado. Nenhuma consulta ao banco dentro da regra.

É o slide que conecta teoria e prática — provavelmente o mais forte da
apresentação.

---

## 7. Plano de tempo — 1h20

80 minutos. O deck tem 53 slides: ~1,5 min por slide na média, mas os slides
de seção passam em segundos e os de código pedem mais.

| Bloco | Slides | Tempo | Acumulado |
|---|---|---|---|
| Abertura + roteiro + objetivos | 1–3 | 4 min | 4 |
| 1. O que é e por que importa | 4–8 | 7 min | 11 |
| 2. Os pilares | 9–15 | 10 min | 21 |
| 3. Funções como valores | 16–21 | 7 min | 28 |
| 4. Ferramental (map/filter/comprehension) | 22–27 | 8 min | 36 |
| 5. functools | 28–33 | 7 min | 43 |
| 6. Closures e decoradores | 34–38 | 7 min | 50 |
| 7. Avaliação preguiçosa | 39–41 | 5 min | 55 |
| 8. Recursão | 42 | 4 min | 59 |
| **9. Estudo de caso + prints** | 43–46 | **9 min** | 68 |
| 10. PF × imperativo e limites | 47–50 | 7 min | 75 |
| Fechamento + fontes | 51–53 | 5 min | **80** |

Margem: se atrasar, os blocos 3 e 4 aceitam corte de 2 min cada sem perda.

### 7.1 Os 20 minutos de dicas pessoais

O enunciado libera **até 20 min** para dicas de Python fora do tema. Duas
formas de usar, e a segunda é melhor:

- ❌ um bloco de 20 min no fim — o público já está saturado;
- ✅ **pílulas de 2–3 min distribuídas**, cada uma com um slide próprio
  marcado com um selo visual ("DICA PESSOAL"), para o avaliador reconhecer
  que aquilo está dentro da cota permitida.

Sugestões que combinam com o projeto e você viveu na prática:

| Dica | Onde encaixa | Gancho real |
|---|---|---|
| `ruff` + `black` + `mypy` no CI desde o dia 1 | após o bloco 4 | os três rodam em todo PR do projeto |
| Type hints salvam refatoração | bloco 5 | o `mypy --strict` pegou o erro do `reduce` com `MappingProxyType` |
| Como testar sem mock | bloco 9 | 154 testes sem banco porque a regra é pura |
| `pytest` com fixture de SQLite em memória | bloco 9 | `conftest.py` troca o MySQL por SQLite |
| Armadilha do import por valor | bloco 6 | bug real: `from cache import get_redis` furou o monkeypatch e a suíte escreveu no Redis de produção |

A última é ouro numa apresentação: é um bug **de verdade**, com causa,
sintoma e correção — e ensina como o `import` funciona em Python.

---

## 8. Preparação para as perguntas (7,0 pontos)

Vale mais que a apresentação inteira. 3 a 5 perguntas, até 40 min. As mais
prováveis, dado o tema, com o rumo da resposta:

**1. "Python é funcional?"**
Não é puro — é multiparadigma. Não tem imutabilidade por padrão, não tem
avaliação preguiçosa por padrão nem TCO. Mas tem funções de primeira classe,
closures, `functools`, generators e comprehensions. A resposta madura é a do
slide 8: use funcional onde calcula, imperativo nas bordas.

**2. "Qual a diferença entre função pura e transparência referencial?"**
Pura = mesma entrada, mesma saída, sem efeitos. Transparência referencial =
a chamada pode ser **substituída pelo seu resultado** sem mudar o programa.
Toda função pura é referencialmente transparente. O exemplo do projeto:
`calcular_status` só ficou transparente quando o relógio virou parâmetro —
antes ela lia `date.today()` por dentro e a mesma entrada dava saídas
diferentes em dias diferentes. É por isso que `requisitos_por_categoria`
pode ter `@lru_cache` com segurança.

**3. "Por que recursão se o Python não otimiza chamada de cauda?"**
Porque a estrutura era recursiva (árvore do FAQ) e a profundidade é limitada
pelo domínio: 3 níveis, contra um limite de ~1000 frames. Se a profundidade
fosse arbitrária — um filesystem — a versão iterativa com pilha explícita
seria a correta. Tem o teste que mede isso:
`test_profundidade_fica_muito_abaixo_do_limite_do_python`.

**4. "`map`/`filter` ou comprehension?"**
Comprehension quase sempre — é mais legível e idiomática (o próprio Guido
preferia). `map`/`filter` ganham quando a função já existe e tem nome
(`map(normalizar, brutas)` lê melhor que a comprehension equivalente) e
quando você quer o iterador preguiçoso sem materializar.

**5. "Imutabilidade não desperdiça memória?"**
Sim, pode. Recriar estrutura grande a cada passo custa. O contra-argumento
é medir antes: no projeto os volumes são pequenos (dezenas de notícias,
poucos requisitos) e a segurança compensou. Em volume grande, mutação local
dentro de uma função que **continua pura por fora** é o meio-termo honesto.

**6. "Onde a PF atrapalhou no seu projeto?"**
Não caia na armadilha de dizer "em lugar nenhum". Respostas reais: o `reduce`
que criava um dict novo a cada passo é O(n²) em memória para coleções
grandes; e o `mypy --strict` obrigou a ligar o resultado do `reduce` a uma
variável antes de envolvê-lo em `MappingProxyType`, porque a inferência
dirigida por contexto quebrava.

> Dica de postura: para o que você não souber, "não sei, mas eu investigaria
> assim…" vale mais que uma resposta inventada. O professor mede raciocínio.

---

## 9. Checklist final antes de apresentar

- [ ] Corpo em 18pt em todos os slides (rodar o script de verificação)
- [ ] Slide 53 com as fontes REAIS preenchidas; `[n]` no rodapé dos slides correspondentes
- [ ] Slides 40, 42 e 46: remover "previsto", já está implementado
- [ ] Slides 10, 45 e 48: corrigir o código que vaza da caixa
- [ ] Prints inseridos (§6) + o slide "Da função pura à tela"
- [ ] Clarear os comentários dentro dos blocos de código
- [ ] Ensaiar cronometrado uma vez — 80 min é mais curto do que parece
- [ ] Levar o projeto rodando local como plano B para a demo (sem depender de rede)
- [ ] `git log --format=full` conferido; repositório público e acessível
