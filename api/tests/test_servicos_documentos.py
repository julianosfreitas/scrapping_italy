from app.models.documento import CategoriaDocumento
from app.services.documentos import (
    agrupar_por_categoria,
    extensao_de,
    sanitizar_nome_arquivo,
    validar_upload,
)

UM_MB = 1024 * 1024


# ── sanitização ───────────────────────────────────────────


def test_sanitizar_remove_path_traversal() -> None:
    assert sanitizar_nome_arquivo("../../etc/senha.pdf") == "senha.pdf"
    assert sanitizar_nome_arquivo("..\\..\\windows\\system32\\x.png") == "x.png"


def test_sanitizar_translitera_e_preserva_extensao() -> None:
    assert (
        sanitizar_nome_arquivo("Histórico Escolar (2ª via)!.pdf") == "historico-escolar-2a-via.pdf"
    )


def test_sanitizar_nunca_devolve_vazio() -> None:
    assert sanitizar_nome_arquivo("////") == "arquivo"
    assert sanitizar_nome_arquivo("!!!.pdf") == "arquivo.pdf"


def test_sanitizar_limita_tamanho() -> None:
    assert len(sanitizar_nome_arquivo("a" * 300 + ".pdf")) <= 80


# ── validação de upload ──────────────────────────────────


def test_validar_upload_aceita_pdf_jpg_png() -> None:
    for nome in ("passaporte.pdf", "foto.JPG", "scan.png", "certidao.jpeg"):
        assert validar_upload(nome, UM_MB, 10 * UM_MB) is None


def test_validar_upload_recusa_extensao() -> None:
    erro = validar_upload("script.exe", UM_MB, 10 * UM_MB)
    assert erro is not None and ".exe" in erro


def test_validar_upload_recusa_sem_extensao() -> None:
    assert validar_upload("passaporte", UM_MB, 10 * UM_MB) is not None


def test_validar_upload_recusa_grande_e_vazio() -> None:
    assert validar_upload("a.pdf", 11 * UM_MB, 10 * UM_MB) is not None
    assert validar_upload("a.pdf", 0, 10 * UM_MB) is not None


def test_extensao_de() -> None:
    assert extensao_de("a.PDF") == "pdf"
    assert extensao_de("sem-extensao") == ""


# ── agrupamento (HOF) ────────────────────────────────────


def test_agrupar_por_categoria_ordena_pelo_enum_e_omite_vazias() -> None:
    docs = (
        ("passaporte", CategoriaDocumento.IDENTIDADE),
        ("ielts", CategoriaDocumento.IDIOMA),
        ("rg", CategoriaDocumento.IDENTIDADE),
    )
    grupos = agrupar_por_categoria(docs, lambda d: d[1])
    assert list(grupos) == [CategoriaDocumento.IDENTIDADE, CategoriaDocumento.IDIOMA]
    assert grupos[CategoriaDocumento.IDENTIDADE] == (docs[0], docs[2])
    assert CategoriaDocumento.VISTO not in grupos
