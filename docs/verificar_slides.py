"""Verifica os critérios de pontuação da apresentação (.pptx ou .pdf).

Uso:

    python docs/verificar_slides.py [caminho.pptx|caminho.pdf]

Confere, slide a slide:
  - tamanho de fonte no CORPO (mínimo 16pt; rodapé é isento pela regra);
  - presença de rodapé com numeração em todos os slides;
  - presença da marca de fonte `[n]` no rodapé.

No `.pptx` a medição é exata (lê o atributo `sz` do XML). No `.pdf` a medição
é a mesma que um avaliador faria abrindo o arquivo — e é lá que aparece o
fator de escala da exportação.
"""

from __future__ import annotations

import re
import sys
import zipfile
import zlib
from pathlib import Path

MINIMO_CORPO = 16.0
# tolerância para o fator de escala do export (16pt costuma sair 15,96)
TOLERANCIA = 0.1

# O rodapé é isento pela regra ("um slide possui TÍTULO, CORPO e RODAPÉ").
# Reconhecê-lo pelo CONTEÚDO — e não pelo tamanho — evita que um texto pequeno
# no corpo passe despercebido só por coincidir com o tamanho do rodapé.
ASSINATURA_RODAPE = "programação funcional em python"
RE_NUMERO = re.compile(r"^\d{1,3}$")
RE_MARCA = re.compile(r"^\[\d+\]$")


def eh_rodape(texto: str) -> bool:
    limpo = texto.strip()
    return (
        ASSINATURA_RODAPE in limpo.lower()
        or bool(RE_NUMERO.match(limpo))
        or bool(RE_MARCA.match(limpo))
    )

RE_TF = re.compile(rb"/[A-Za-z0-9]+\s+([0-9.]+)\s+Tf")
RE_STR = re.compile(rb"\((?:[^()\\]|\\.)*\)", re.S)
RE_SHOW = re.compile(rb"(?:\((?:[^()\\]|\\.)*\)|\[[^\]]*\])\s*(?:Tj|TJ)", re.S)


def _limpar(bruto: bytes) -> str:
    partes = RE_STR.findall(bruto)
    texto = b"".join(p[1:-1] for p in partes).decode("latin-1", "ignore")
    return re.sub(r"\\(\d{3}|.)", "", texto).strip()


def itens_do_stream(buf: bytes) -> list[tuple[float, str]]:
    """(tamanho_pt, texto) na ordem de desenho do stream."""
    tamanhos = [(m.start(), float(m.group(1))) for m in RE_TF.finditer(buf)]
    saida: list[tuple[float, str]] = []
    for marca in RE_SHOW.finditer(buf):
        atual = None
        for posicao, valor in tamanhos:
            if posicao < marca.start():
                atual = valor
            else:
                break
        texto = _limpar(marca.group(0))
        if texto and atual is not None:
            saida.append((atual, texto))
    return saida


def paginas(pdf: Path) -> list[list[tuple[float, str]]]:
    dados = pdf.read_bytes()
    resultado = []
    for bruto in re.findall(rb"stream\r?\n(.*?)endstream", dados, re.S):
        try:
            buf = zlib.decompress(bruto)
        except zlib.error:
            continue
        if lista := itens_do_stream(buf):
            resultado.append(lista)
    return resultado


RE_RUN = re.compile(
    rb'<a:rPr[^>]*\bsz="(\d+)"[^>]*/?>.*?<a:t>(.*?)</a:t>', re.S
)


def slides_pptx(caminho: Path) -> list[list[tuple[float, str]]]:
    """(tamanho_pt, texto) por slide, lido direto do XML do .pptx.

    O atributo `sz` vem em centésimos de ponto: sz="1800" = 18pt.
    """
    resultado: list[list[tuple[float, str]]] = []
    with zipfile.ZipFile(caminho) as pacote:
        nomes = sorted(
            (n for n in pacote.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
            key=lambda n: int(re.findall(r"\d+", n)[-1]),
        )
        for nome in nomes:
            xml = pacote.read(nome)
            itens = [
                (int(sz) / 100, texto.decode("utf-8", "ignore"))
                for sz, texto in RE_RUN.findall(xml)
            ]
            resultado.append(itens)
    return resultado


def main(argumentos: list[str]) -> int:
    caminho = Path(argumentos[0]) if argumentos else Path(__file__).with_name(
        "PF-Python-Ponte-Italia.pptx"
    )
    if not caminho.exists():
        print(f"arquivo não encontrado: {caminho}")
        return 2

    slides = slides_pptx(caminho) if caminho.suffix == ".pptx" else paginas(caminho)
    print(f"{caminho.name}: {len(slides)} slide(s) com texto\n")

    pequenos, sem_rodape, sem_marca = [], [], []
    for numero, lista in enumerate(slides, start=1):
        corpo = [
            (t, x)
            for t, x in lista
            if not eh_rodape(x) and t < MINIMO_CORPO - TOLERANCIA
        ]
        if corpo:
            pequenos.append((numero, sorted({t for t, _ in corpo}), corpo[0][1]))

        rodape = [x.strip() for _, x in lista if eh_rodape(x)]
        if not any(RE_NUMERO.match(x) and int(x) == numero for x in rodape):
            sem_rodape.append(numero)
        if not any("[" in x for x in rodape):
            sem_marca.append(numero)

    if pequenos:
        print(f"CORPO ABAIXO DE {MINIMO_CORPO:.0f}pt — {len(pequenos)} slide(s):")
        for numero, tamanhos, amostra in pequenos:
            marcas = ", ".join(f"{t:.2f}" for t in tamanhos)
            print(f"  slide {numero:2d}  [{marcas}]  {amostra[:52]}")
    else:
        print(f"CORPO: nenhum texto abaixo de {MINIMO_CORPO:.0f}pt.")

    print()
    if sem_rodape:
        print(f"RODAPÉ/NUMERAÇÃO AUSENTE — slide(s): {sorted(set(sem_rodape))}")
    else:
        print("RODAPÉ: número presente em todos os slides.")

    # Se a assinatura do rodapé não aparece em NENHUM slide, o extrator não
    # conseguiu decodificar aquele texto (exportação com subconjunto de fonte)
    # — é diferente de o rodapé não existir. Só o .pptx mede isso com certeza.
    legivel = any(
        ASSINATURA_RODAPE in x.lower() for lista in slides for _, x in lista
    )
    if not legivel and caminho.suffix == ".pdf":
        print("MARCA DE FONTE: não verificável neste PDF "
              "(texto do rodapé com subconjunto de fonte) — confira no .pptx.")
        sem_marca = []
    elif sem_marca:
        print(f"SEM MARCA DE FONTE [n] — slide(s): {sem_marca}")
    else:
        print("MARCA DE FONTE: [n] presente em todos os slides.")

    print()
    if pequenos or sem_rodape or sem_marca:
        print("Resultado: AINDA HÁ AJUSTES (cada item vale −1,0 ponto).")
        return 1
    print("Resultado: OK nos critérios verificáveis automaticamente.")
    print("Confira à mão: o texto do slide de fontes e o contraste de cores.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
