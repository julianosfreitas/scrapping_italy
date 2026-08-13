# Apresentação — o que foi feito e o que ainda depende de você

Estado de `PF-Python-Ponte-Italia.pptx` (61 slides) e do PDF exportado.

O deck foi **reconstruído por código** (`docs/gerar_slides.py`). O motivo é
simples: os critérios de pontuação são objetivos, e definidos como constantes
no gerador eles ficam garantidos por construção — não dependem de lembrar de
ajustar 61 slides à mão. Dois verificadores conferem o resultado a cada
regeração.

```bash
python docs/gerar_slides.py                  # regenera o .pptx
python docs/verificar_slides.py docs/PF-Python-Ponte-Italia.pptx
python docs/verificar_layout.py              # estouro de caixa
```

---

## 1. Critérios de pontuação — situação

| Critério | Antes | Agora |
|---|---|---|
| Fonte ≥ 16pt no CORPO | ❌ 12 slides violavam (menor: 12,0pt) | ✅ **mínimo 18pt em todo o deck** |
| Numeração no rodapé | ✅ | ✅ nos 61 slides |
| Origem identificada (IA) | ❌ placeholder no slide 53 | ✅ `[1]` no rodapé de todos + slide de fontes preenchido |
| Contraste / legibilidade | ⚠️ 2 ressalvas | ✅ revisado |
| Estouro de caixa | ❌ 3 slides com código vazando | ✅ 0 ocorrências |

### Por que 18pt e não 16pt

O mínimo exigido é 16. O deck anterior usava 16pt e o PDF saiu com **15,96pt**
— a exportação aplica ~0,25% de escala. Medindo o PDF, ficava abaixo do
mínimo por 0,04pt.

Com 18pt, o PDF exportado agora mede **18,00pt**. Verificado no arquivo final,
não presumido.

### A sinalização de IA

O rodapé de **todos os 61 slides** traz `[1]`, discreto, ao lado da assinatura.
O último slide detalha no formato exigido:

> **[1]** Claude (Anthropic) — prompt: "gerar apresentação acadêmica de 1h20
> sobre Programação Funcional em Python, usando o projeto Ponte Italia como
> estudo de caso, com slides de conceito, código e comparação imperativo ×
> funcional".
>
> **[2]** Documentação oficial do Python — functools, itertools e dataclasses.
> **[3]** PEP 8 — Guia de Estilo para Código Python.
>
> Código, capturas de tela e dados do projeto Ponte Italia são de autoria
> própria.

**Marcar todos os slides é deliberado.** A regra pune a não-declaração, nunca
o uso de IA. Declarar a mais custa zero; declarar a menos em dois slides zera
a apresentação. Se você reescrever slides do zero, pode remover o `[1]`
daqueles — mas na dúvida, deixe.

> ⚠️ **Confira o texto do prompt no slide 61.** Ele descreve o que foi pedido
> aqui. Se você usou outro comando em outra ferramenta, ajuste para o que
> digitou de fato — o enunciado pede o comando exato.

---

## 2. O que mudou no conteúdo

**Correções factuais** — três slides prometiam o que já está pronto:

| Antes | Agora |
|---|---|
| "Generators — exemplo previsto · Sprint 4" | `iterar_itens_rss`, `paginar`, `janelas` implementados |
| "Recursão — exemplo previsto · Sprint 6" | `todas_perguntas`, `profundidade`, `caminho_ate` implementados |
| Mapa com 2 conceitos "previstos" | **16/16 conceitos**, todos com arquivo e função |

**Seis slides novos com o sistema rodando** (autoria própria, sem `[n]` extra):

| Slide | Conteúdo | Serve para |
|---|---|---|
| 43 | Radar com 111 notícias | os generators alimentando o feed |
| 46 | Aba Ajuda | a recursão renderizada na tela |
| 48 | Home | mostrar que é sistema real |
| 51 | Perfil com o gap em 33% | **o slide mais forte: da função pura à tela** |
| 52 | E-mail da newsletter | `reduce` agrupando a edição |
| — | Swagger (reserva) | evidência da API |

**Três slides de dica pessoal**, com selo âmbar "DICA PESSOAL DE PYTHON" para
o avaliador reconhecer que estão dentro da cota de 20 min:

1. **Slide 16** — ruff + black + mypy no CI desde o dia 1.
2. **Slide 34** — type hints como refatoração segura (o caso real do `reduce`).
3. **Slide 54** — a armadilha do `import` por valor (bug real: a suíte de
   testes escrevendo no Redis de verdade). É a melhor das três: tem sintoma,
   causa e correção.

---

## 3. Plano de tempo — 80 minutos

61 slides. Os de seção passam em segundos; os de código pedem mais.

| Bloco | Slides | Tempo | Acumulado |
|---|---|---|---|
| Abertura, roteiro e objetivos | 1–3 | 4 min | 4 |
| 1 · O que é e por que importa | 4–8 | 7 min | 11 |
| 2 · Os pilares | 9–15 | 10 min | 21 |
| **Dica pessoal 1** | 16 | 3 min | 24 |
| 3 · Funções como valores | 17–21 | 7 min | 31 |
| 4 · Ferramental | 22–27 | 8 min | 39 |
| 5 · functools | 28–33 | 7 min | 46 |
| **Dica pessoal 2** | 34 | 3 min | 49 |
| 6 · Closures e decoradores | 35–39 | 6 min | 55 |
| 7 · Avaliação preguiçosa | 40–43 | 5 min | 60 |
| 8 · Recursão | 44–46 | 4 min | 64 |
| 9 · Estudo de caso | 47–53 | 8 min | 72 |
| **Dica pessoal 3** | 54 | 3 min | 75 |
| 10 · PF × imperativo e limites | 55–58 | 3 min | 78 |
| Fechamento e fontes | 59–61 | 2 min | **80** |

Dicas pessoais somam 9 min — bem dentro dos 20 permitidos. Se atrasar, os
blocos 3 e 4 aceitam corte de 2 min cada.

---

## 4. Preparação para as perguntas (7,0 pontos)

Vale mais que a apresentação. 3 a 5 perguntas, até 40 min.

**1. "Python é funcional?"**
Não é puro — é multiparadigma. Não tem imutabilidade por padrão, nem lazy por
padrão, nem TCO. Mas tem funções de primeira classe, closures, `functools`,
generators e comprehensions. A resposta madura é a do slide 8: funcional onde
calcula, imperativo nas bordas.

**2. "Diferença entre função pura e transparência referencial?"**
Pura = mesma entrada, mesma saída, sem efeitos. Transparência referencial = a
chamada pode ser **substituída pelo seu resultado** sem mudar o programa. Toda
função pura é referencialmente transparente. Exemplo do projeto:
`calcular_status` só ficou transparente quando o relógio virou parâmetro —
antes lia `date.today()` por dentro e a mesma entrada dava saídas diferentes
em dias diferentes. É por isso que `requisitos_por_categoria` pode ter
`@lru_cache` com segurança.

**3. "Por que recursão se o Python não otimiza chamada de cauda?"**
Porque a estrutura era recursiva (árvore do FAQ) e a profundidade é limitada
pelo domínio: 3 níveis contra ~1000 frames. Se fosse arbitrária — um
filesystem — a versão iterativa com pilha explícita seria a correta. Existe o
teste `test_profundidade_fica_muito_abaixo_do_limite_do_python`.

**4. "`map`/`filter` ou comprehension?"**
Comprehension quase sempre — mais legível e idiomática. `map`/`filter` ganham
quando a função já existe e tem nome (`map(normalizar, brutas)`) e quando você
quer o iterador preguiçoso sem materializar.

**5. "Imutabilidade não desperdiça memória?"**
Sim, pode. Recriar estrutura grande a cada passo custa. O contra-argumento é
medir antes: aqui os volumes são pequenos e a segurança compensou. Em volume
grande, mutação local dentro de uma função que **continua pura por fora** é o
meio-termo honesto.

**6. "Onde a PF atrapalhou no seu projeto?"**
Não diga "em lugar nenhum". Respostas reais: o `reduce` que cria um dict novo
a cada passo é O(n²) em memória para coleções grandes; e o `mypy --strict`
obrigou a ligar o resultado do `reduce` a uma variável antes de embrulhá-lo em
`MappingProxyType`, porque a inferência dirigida por contexto quebrava.

> Postura: para o que não souber, "não sei, mas eu investigaria assim…" vale
> mais que resposta inventada. O professor mede raciocínio.

---

## 5. O que ainda depende de você

- [ ] **Revisar o texto do prompt no slide 61** para bater com o que você
      digitou de fato (§1).
- [ ] Abrir o `.pptx` e passar o olho — os verificadores pegam fonte, rodapé e
      estouro de caixa, mas não julgam gosto.
- [ ] Ensaiar cronometrado uma vez. 80 min é mais curto do que parece.
- [ ] Levar o projeto rodando local como plano B da demo (sem depender de rede).
- [ ] Conferir que o repositório está público e acessível.

### Observação técnica sobre o verificador

`verificar_slides.py` lê os dois formatos. No `.pptx` a medição é exata (lê o
atributo `sz` do XML). No `.pdf` ele mede o que um avaliador mediria, mas o
texto do rodapé sai com subconjunto de fonte e não é decodificável — por isso
a checagem da marca `[n]` no PDF reporta "não verificável" em vez de falhar.
A conferência autoritativa é a do `.pptx`; o rodapé aparece corretamente em
todos os slides renderizados.
