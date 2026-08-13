"""Gera os assets monocromáticos do logo a partir do mockup em papel.

Uso: ``python docs/gerar_logo.py``

O arquivo de origem é um mockup (baixo-relevo em papel texturizado), não um
asset limpo. A extração separa tinta de papel pela luminância: o histograma
tem um vale claro entre a tinta (96–127) e o papel (160–223), então um corte
em 140 recupera a silhueta exata — inclusive os vazados do monograma PI e
dos arcos da ponte, que ficam do lado claro e viram transparência.

Saídas em `api/app/static/img/` (monocromia — uma cor só, sem gradiente):

    logo-completo.svg        marca + lettering, verde — slides e materiais
    logo-marca.svg           só a marca, verde — cabeçalho do site
    logo-marca-branco.svg    só a marca, branca — fundos escuros
    logo-marca.png           marca em PNG — e-mail (clientes ignoram SVG)
    favicon-32.png           aba do navegador
    favicon-180.png          atalho iOS
    favicon.ico              compatibilidade

A cor fica GRAVADA em cada arquivo em vez de `currentColor`: SVG carregado
por `<img>` ou `<link rel=icon>` não herda a cor da página, então herdar
deixaria o logo preto.
"""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "PONTEITALIALOGO.jpg"
DESTINO = RAIZ / "api" / "app" / "static" / "img"

# vale do histograma entre a tinta e o papel do mockup
CORTE_LUMINANCIA = 140
# o lettering começa por volta de 68% da altura; acima disso fica só a marca
FIM_DA_MARCA = 0.675
VERDE = "#2E7D5B"  # verde de ação do site (seção 8 do README)
SALVIA = "#797963"  # tom do próprio logo impresso — usado no e-mail e nos slides


def silhueta(caminho: Path) -> Image.Image:
    """Mockup -> máscara L (255 = tinta), recortada no conteúdo."""
    cinza = Image.open(caminho).convert("L")
    mascara = cinza.point(lambda v: 255 if v < CORTE_LUMINANCIA else 0, mode="L")
    caixa = mascara.getbbox()
    if caixa is None:
        raise SystemExit("nenhuma tinta encontrada — confira o corte de luminância")
    return mascara.crop(caixa)


def colorir(mascara: Image.Image, cor: str) -> Image.Image:
    """Máscara -> RGBA de UMA cor com fundo transparente (monocromia)."""
    solida = Image.new("RGBA", mascara.size, cor)
    solida.putalpha(mascara)
    return solida


def como_svg(mascara: Image.Image, cor: str, titulo: str) -> str:
    """Embrulha a máscara num SVG que pinta a cor via `mask` — troca de cor por CSS.

    Guardar a silhueta como máscara (e não como PNG colorido) mantém a
    monocromia real: o `fill` do retângulo é a única cor do arquivo, e pode
    ser trocado sem reexportar nada.
    """
    largura, altura = mascara.size
    buffer = BytesIO()
    mascara.save(buffer, format="PNG", optimize=True)
    dados = base64.b64encode(buffer.getvalue()).decode("ascii")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {altura}" '
        f'role="img" aria-label="{titulo}">\n'
        f"  <title>{titulo}</title>\n"
        f"  <mask id=\"m\">\n"
        f'    <image href="data:image/png;base64,{dados}" '
        f'width="{largura}" height="{altura}"/>\n'
        f"  </mask>\n"
        f'  <rect width="{largura}" height="{altura}" fill="{cor}" mask="url(#m)"/>\n'
        f"</svg>\n"
    )


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    completo = silhueta(ORIGEM)
    largura, altura = completo.size
    marca = completo.crop((0, 0, largura, int(altura * FIM_DA_MARCA)))
    marca = marca.crop(marca.getbbox() or (0, 0, largura, altura))

    (DESTINO / "logo-completo.svg").write_text(
        como_svg(completo, VERDE, "Ponte Italia"), encoding="utf-8"
    )
    (DESTINO / "logo-marca.svg").write_text(
        como_svg(marca, VERDE, "Ponte Italia"), encoding="utf-8"
    )
    (DESTINO / "logo-marca-branco.svg").write_text(
        como_svg(marca, "#FFFFFF", "Ponte Italia"), encoding="utf-8"
    )

    (DESTINO / "logo-marca-salvia.svg").write_text(
        como_svg(marca, SALVIA, "Ponte Italia"), encoding="utf-8"
    )
    (DESTINO / "logo-completo-salvia.svg").write_text(
        como_svg(completo, SALVIA, "Ponte Italia"), encoding="utf-8"
    )

    # PNG da marca: cliente de e-mail não renderiza SVG. O e-mail usa a
    # variante sálvia, que é a cor do logo impresso no papel.
    for nome, cor in (("logo-marca.png", VERDE), ("logo-marca-salvia.png", SALVIA)):
        png_marca = colorir(marca, cor)
        png_marca.thumbnail((240, 240), Image.LANCZOS)
        png_marca.save(DESTINO / nome)

    # favicon: a marca centrada num quadrado, com respiro nas bordas
    for tamanho in (32, 180):
        lado = int(tamanho * 0.86)
        copia = colorir(marca, VERDE)
        copia.thumbnail((lado, lado), Image.LANCZOS)
        quadro = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
        quadro.paste(
            copia,
            ((tamanho - copia.width) // 2, (tamanho - copia.height) // 2),
            copia,
        )
        quadro.save(DESTINO / f"favicon-{tamanho}.png")

    icone = colorir(marca, VERDE)
    icone.thumbnail((64, 64), Image.LANCZOS)
    quadro = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    quadro.paste(icone, ((64 - icone.width) // 2, (64 - icone.height) // 2), icone)
    quadro.save(DESTINO / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

    print(f"lockup completo: {largura}x{altura}")
    print(f"marca:           {marca.size[0]}x{marca.size[1]}")
    for arquivo in sorted(DESTINO.iterdir()):
        print(f"  {arquivo.name:22} {arquivo.stat().st_size // 1024:4d} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
