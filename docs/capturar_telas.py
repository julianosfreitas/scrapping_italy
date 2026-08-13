"""Captura as telas do Ponte Italia para os slides da apresentação.

Uso (com a api no ar em http://localhost:8000):

    PONTE_EMAIL=... PONTE_SENHA=... python docs/capturar_telas.py

Gera PNGs em docs/screenshots/. As telas privadas (perfil, cofre) recebem o
token JWT no localStorage antes da navegação, do mesmo jeito que o front faz
depois do login — por isso o cofre e o comparativo aparecem preenchidos.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx
from playwright.sync_api import Page, sync_playwright

API = os.environ.get("PONTE_API", "http://localhost:8000")
SAIDA = Path(__file__).resolve().parent / "screenshots"
LARGURA, ALTURA = 1440, 900


@dataclass(frozen=True)
class Tela:
    """Uma captura: arquivo de saída, caminho no site e se exige sessão."""

    arquivo: str
    caminho: str
    autenticada: bool = False
    pagina_inteira: bool = True
    espera: str | None = None


TELAS: tuple[Tela, ...] = (
    Tela("01-home.png", "/"),
    Tela("02-estudantes.png", "/estudantes"),
    Tela("03-perfil-cofre.png", "/estudantes/1", autenticada=True, espera="#cofre .rounded-2xl"),
    Tela("04-universidades.png", "/universidades"),
    Tela("05-universidade-detalhe.png", "/universidades/2"),
    Tela("06-radar.png", "/radar"),
    Tela("07-radar-filtro-vistos.png", "/radar?categoria=vistos"),
    Tela("08-newsletter.png", "/newsletter"),
    Tela("10-ajuda.png", "/ajuda"),
    Tela("11-ajuda-categoria.png", "/ajuda?categoria=1"),
    Tela("12-swagger.png", "/docs", espera=".opblock"),
)


def obter_token() -> str:
    email, senha = os.environ.get("PONTE_EMAIL"), os.environ.get("PONTE_SENHA")
    if not email or not senha:
        raise SystemExit("Defina PONTE_EMAIL e PONTE_SENHA para capturar as telas privadas.")
    resposta = httpx.post(f"{API}/api/auth/login", json={"email": email, "senha": senha})
    resposta.raise_for_status()
    dados = resposta.json()
    return f"{dados['access_token']}|{dados['estudante_id']}"


def data_da_ultima_edicao() -> str | None:
    """A página do arquivo depende de existir edição — descobre a mais recente."""
    resposta = httpx.get(f"{API}/api/newsletter/edicoes")
    resposta.raise_for_status()
    edicoes = resposta.json()
    return edicoes[0]["data"] if edicoes else None


def capturar(pagina: Page, tela: Tela) -> None:
    pagina.goto(f"{API}{tela.caminho}", wait_until="networkidle")
    if tela.espera:
        try:
            pagina.wait_for_selector(tela.espera, timeout=8000)
        except Exception:  # noqa: BLE001 — print sem o seletor ainda é útil
            print(f"  aviso: seletor {tela.espera!r} não apareceu em {tela.caminho}")
    pagina.wait_for_timeout(700)  # fontes e transições
    destino = SAIDA / tela.arquivo
    pagina.screenshot(path=str(destino), full_page=tela.pagina_inteira)
    print(f"  ok  {tela.arquivo:34} {tela.caminho}")


def main() -> int:
    SAIDA.mkdir(parents=True, exist_ok=True)
    token, estudante_id = obter_token().split("|")

    telas = list(TELAS)
    if (data := data_da_ultima_edicao()) is not None:
        telas.insert(8, Tela("09-newsletter-edicao.png", f"/newsletter/{data}"))
    else:
        print("  aviso: nenhuma edição arquivada — pulando a tela do arquivo")

    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        contexto = navegador.new_context(
            viewport={"width": LARGURA, "height": ALTURA},
            device_scale_factor=2,  # retina: legível quando projetado
            locale="pt-BR",
        )
        # o front guarda a sessão no localStorage; injetar antes de navegar
        # faz as telas privadas renderizarem já autenticadas
        contexto.add_init_script(
            f"localStorage.setItem('token', '{token}');"
            f"localStorage.setItem('estudante_id', '{estudante_id}');"
        )
        pagina = contexto.new_page()

        print(f"Capturando {len(telas)} tela(s) de {API} em {SAIDA}")
        for tela in telas:
            capturar(pagina, tela)

        navegador.close()

    print(f"\nConcluído: {len(list(SAIDA.glob('*.png')))} arquivo(s) em {SAIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
