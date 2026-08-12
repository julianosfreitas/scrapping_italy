from app.seed import ESTUDANTES_INICIAIS, faltantes


def test_faltantes_sem_ninguem_no_banco() -> None:
    assert faltantes(ESTUDANTES_INICIAIS, frozenset()) == ESTUDANTES_INICIAIS


def test_faltantes_e_idempotente_quando_todos_existem() -> None:
    emails = frozenset(e.email for e in ESTUDANTES_INICIAIS)
    assert faltantes(ESTUDANTES_INICIAIS, emails) == ()


def test_faltantes_parcial() -> None:
    primeiro = ESTUDANTES_INICIAIS[0]
    resultado = faltantes(ESTUDANTES_INICIAIS, frozenset({primeiro.email}))
    assert primeiro not in resultado
    assert len(resultado) == len(ESTUDANTES_INICIAIS) - 1
