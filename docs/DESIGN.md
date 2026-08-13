# Design — Ponte Italia

Detalhamento da seção 8 do README: as decisões visuais, os componentes e as
regras de acessibilidade que valem para todas as telas.

## Princípio

Referência Duolingo: **clean, muito espaço em branco, uma cor de ação só**.
A informação do processo já é confusa o suficiente — a interface não pode
competir com ela. Nada de neon, nada de gradiente chamativo.

## Paleta

| Papel | Hex | Onde |
|---|---|---|
| Fundo | `#FAFAF7` | `bg-fundo` — corpo de todas as páginas |
| Texto | `#1F2933` | `text-grafite` |
| Ação | `#2E7D5B` | `bg-verde` / `text-verde` — botões, links, destaques |
| Ação (fundo suave) | `#EAF3EF` | `bg-verde-claro` — badges e chips |
| Apoio | cinzas do Tailwind | bordas (`gray-100/200`), texto secundário (`gray-500/600`) |

Semânticos, usados só para status de documento e prazo:

| Estado | Classe |
|---|---|
| Em dia / atendido | `bg-verde-claro text-verde` |
| Vencendo / prazo próximo | `bg-amber-100 text-amber-800` |
| Vencido / faltando | `bg-red-100 text-red-800` |

O verde é um aceno à bandeira italiana sem cair no clichê tricolor. O mesmo
trio de cores atravessa o site **e o HTML da newsletter** — o e-mail é testado
contra esses três hex em `MontagemEdicaoTests`.

## Tipografia

**Inter** (400/600/700/800), com fallback `system-ui`. Títulos em 800 com
`tracking-tight`; corpo em 400 com entrelinha generosa (`leading-relaxed` nos
textos longos do FAQ). Escala: `text-3xl` para o H1 da página, `text-xl` para
seções, `text-sm` para apoio.

## Componentes

- **Cards** — `rounded-2xl` (16px), `bg-white`, `border-gray-100`,
  `shadow-sm`. No hover: `hover:border-verde/40 hover:shadow`.
- **Botões** — `rounded-xl`, `bg-verde`, texto branco `font-bold`,
  `hover:opacity-90`.
- **Badges/chips** — `rounded-full px-3 py-1 text-xs font-semibold`.
- **Campos** — `rounded-xl border-gray-200 px-4 py-2.5`, com
  `focus:ring-2 focus:ring-verde`.
- **Navegação** — cabeçalho `sticky` com blur, links em `font-semibold` que
  ganham verde no hover.

## Acessibilidade

Revisado na Sprint 6, aplicado em todas as telas:

- **Contraste AA.** Grafite `#1F2933` sobre `#FAFAF7` passa folgado (~14:1);
  branco sobre o verde `#2E7D5B` fica acima de 4.5:1. Texto secundário nunca
  desce abaixo de `gray-500`.
- **Foco visível.** Todo elemento interativo tem `focus:ring-2
  focus:ring-verde`. Nenhum `outline-none` foi deixado sem anel substituto.
- **Semântica antes de estilo.** O FAQ usa `<details>/<summary>` (abre e fecha
  no teclado sem JavaScript); as navegações são `<nav>` com `aria-label`; a
  busca é `role="search"`; a barra de prontidão é `role="progressbar"` com
  `aria-valuenow`.
- **Labels sempre presentes** — visíveis, ou `sr-only` quando o placeholder já
  explica o campo.
- **Ícones decorativos** (`✓`, `✗`, `›`) marcados com `aria-hidden="true"`; a
  informação nunca depende só deles — vem também no texto do badge.
- **Mensagens dinâmicas** com `role="status"` e `aria-live="polite"`, para o
  leitor de tela anunciar o resultado da inscrição na newsletter.

## Responsividade

Mobile-first. Container em `max-width: 5xl` com `px-6`. Grades sobem de uma
para várias colunas com `sm:` / `md:` (`sm:grid-cols-2` nos documentos,
`md:grid-cols-[16rem_1fr]` no FAQ, onde o menu de categorias vira topo no
celular). Filtros usam `flex-wrap`, nunca estouram a largura.

## JavaScript

Fase 1 sem framework. Desde a Sprint 6 o script do perfil vive em
`api/app/static/js/perfil.js`, fora do template: é cacheável, e o id do dono
do perfil chega por `data-estudante-id` em vez de interpolação Jinja — o que
deixa o caminho aberto para uma CSP sem `unsafe-inline`. Todo texto vindo da
API passa por `escapar()` antes de entrar no `innerHTML`.

## Próximos passos (fase 2)

Tailwind hoje vem do CDN, o que é ótimo para prototipar e ruim para produção
(sem purge, sem versão fixa). A migração para React + Vite + TypeScript da
fase 2 traz o Tailwind compilado junto; até lá, o CDN é uma dívida consciente.
