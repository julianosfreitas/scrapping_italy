"""Bateria de fronteiras da função pura calcular_status.

data_atual de referência: 2026-08-12 (injetada — nenhum teste depende do
relógio real).
"""

from datetime import date, timedelta

from app.models.documento import StatusDocumento
from app.services.documentos import calcular_status

HOJE = date(2026, 8, 12)


def test_sem_validade_e_ok() -> None:
    assert calcular_status(None, HOJE) is StatusDocumento.OK


def test_vencido_ontem() -> None:
    assert calcular_status(HOJE - timedelta(days=1), HOJE) is StatusDocumento.VENCIDO


def test_vence_hoje_ainda_vale_mas_alerta() -> None:
    assert calcular_status(HOJE, HOJE) is StatusDocumento.VENCENDO


def test_vence_exatamente_em_30_dias_fronteira_interna() -> None:
    assert calcular_status(HOJE + timedelta(days=30), HOJE) is StatusDocumento.VENCENDO


def test_vence_em_31_dias_fora_da_janela() -> None:
    assert calcular_status(HOJE + timedelta(days=31), HOJE) is StatusDocumento.OK


def test_vencido_ha_muito_tempo() -> None:
    assert calcular_status(date(2020, 1, 1), HOJE) is StatusDocumento.VENCIDO


def test_janela_customizada() -> None:
    validade = HOJE + timedelta(days=60)
    assert calcular_status(validade, HOJE, janela_vencendo_dias=90) is StatusDocumento.VENCENDO
    assert calcular_status(validade, HOJE, janela_vencendo_dias=30) is StatusDocumento.OK


def test_transparencia_referencial() -> None:
    """Mesma entrada -> mesma saída, sempre: a chamada pode ser substituída pelo valor."""
    resultados = {calcular_status(HOJE + timedelta(days=10), HOJE) for _ in range(100)}
    assert resultados == {StatusDocumento.VENCENDO}
