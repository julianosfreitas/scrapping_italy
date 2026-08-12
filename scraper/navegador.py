"""Obtenção de páginas via navegador real (Playwright) — fallback para WAF.

O Universitaly fica atrás de AWS WAF com challenge JavaScript; httpx recebe
HTTP 202 vazio. O Playwright executa o challenge como um navegador comum.
Se mesmo assim o WAF persistir, a coleta da fonte mantém a fixture — a
decisão registrada na Sprint 3/4 é NÃO insistir em contornar bloqueios.
"""

from __future__ import annotations

from scraper.coleta import TIMEOUT_SEGUNDOS, USER_AGENT, ColetaBloqueada


def obter_com_navegador(url: str) -> str:
    """Baixa a página renderizada (pós-challenge). Levanta ColetaBloqueada se falhar."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        navegador = pw.chromium.launch(headless=True)
        try:
            pagina = navegador.new_page(user_agent=USER_AGENT)
            resposta = pagina.goto(url, timeout=TIMEOUT_SEGUNDOS * 1000, wait_until="networkidle")
            html: str = pagina.content()
            status = resposta.status if resposta else 0
            if status != 200 or len(html) < 2000:
                raise ColetaBloqueada(f"{url} continua bloqueada via navegador (HTTP {status})")
            return html
        finally:
            navegador.close()
