"""Verifica os critérios de pontuação da apresentação direto no PDF.

Uso:

    python docs/verificar_slides.py [caminho.pdf]

Confere, slide a slide:
  - tamanho de fonte no CORPO (mínimo 16pt; rodapé é isento pela regra);
  - presença de rodapé em todos os slides.

Roda de novo depois de cada rodada de correções — é o mesmo critério que o
avaliador aplicaria medindo o arquivo.
"""

from __future__ import annotations

import re
import sys
import zlib
from pathlib import Path

MINIMO_CORPO = 16.0
# tamanhos usados exclusivamente pelo rodapé neste template (isentos)
TAMANHOS_RODAPE = frozenset({9.0, 11.04})
# tolerância para o fator de escala do export (16pt costuma sair 15,96)
TOLERANCIA = 0.1

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


def main(argumentos: list[str]) -> int:
    caminho = Path(argumentos[0]) if argumentos else Path(__file__).with_name(
        "PF-Python-Ponte-Italia.pdf"
    )
    if not caminho.exists():
        print(f"arquivo não encontrado: {caminho}")
        return 2

    slides = paginas(caminho)
    print(f"{caminho.name}: {len(slides)} slide(s) com texto\n")

    pequenos, sem_rodape = [], []
    for numero, lista in enumerate(slides, start=1):
        corpo = [
            (t, x)
            for t, x in lista
            if t not in TAMANHOS_RODAPE and t < MINIMO_CORPO - TOLERANCIA
        ]
        if corpo:
            pequenos.append((numero, sorted({t for t, _ in corpo}), corpo[0][1]))
        if not any(t in TAMANHOS_RODAPE for t, _ in lista):
            sem_rodape.append(numero)

    if pequenos:
        print(f"CORPO ABAIXO DE {MINIMO_CORPO:.0f}pt — {len(pequenos)} slide(s):")
        for numero, tamanhos, amostra in pequenos:
            marcas = ", ".join(f"{t:.2f}" for t in tamanhos)
            print(f"  slide {numero:2d}  [{marcas}]  {amostra[:52]}")
    else:
        print(f"CORPO: nenhum texto abaixo de {MINIMO_CORPO:.0f}pt.")

    print()
    if sem_rodape:
        print(f"SEM RODAPÉ — slide(s): {sem_rodape}")
    else:
        print("RODAPÉ: presente em todos os slides.")

    print()
    if pequenos or sem_rodape:
        print("Resultado: AINDA HÁ AJUSTES (cada item vale −1,0 ponto).")
        return 1
    print("Resultado: OK nos critérios verificáveis automaticamente.")
    print("Confira à mão: atribuição de fontes/IA e contraste de cores.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
