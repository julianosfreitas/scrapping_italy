from datetime import date

from app.services.cursos import ordenar_por_prazo, prazo_proximo

HOJE = date(2026, 8, 12)


def test_ordena_prazo_mais_proximo_primeiro_e_sem_prazo_no_fim() -> None:
    cursos = (
        ("sem prazo", None),
        ("dezembro", date(2026, 12, 1)),
        ("setembro", date(2026, 9, 1)),
    )
    ordenados = ordenar_por_prazo(cursos, lambda c: c[1])
    assert [c[0] for c in ordenados] == ["setembro", "dezembro", "sem prazo"]


def test_prazo_proximo_dentro_da_janela() -> None:
    assert prazo_proximo(date(2026, 9, 1), HOJE)  # 20 dias
    assert prazo_proximo(HOJE, HOJE)  # vence hoje ainda conta


def test_prazo_fora_da_janela_ou_passado() -> None:
    assert not prazo_proximo(date(2026, 12, 1), HOJE)  # além de 60 dias
    assert not prazo_proximo(date(2026, 8, 11), HOJE)  # já passou
    assert not prazo_proximo(None, HOJE)
