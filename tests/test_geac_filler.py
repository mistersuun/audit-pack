"""Tests for GEAC auto-filler.

Uses parser-format field names (matching DailyRevenueParser/ARSummaryParser output).
"""
import pytest
from utils.geac_filler import compute_geac_data


def test_geac_card_variance_balanced():
    """Cash Out + Deposit should equal Daily Revenue per card."""
    dr = {
        'settlements': {'american_express': -7576.83, 'mastercard': -9945.62,
                        'visa': -12126.86, 'facture_direct': -5197.27},
        'deposits_received': {'ax': 5707.24, 'mastercard': 474.09, 'visa': 993.65},
        'balance': {'prev_day': -1476889.24, 'today': -5493.03,
                    'new_balance': -1482382.27},
        'advance_deposits': {'applied': -64522.13},
    }
    ar = {'front_office_transfers': {'guest_folios': 5197.27}}
    result = compute_geac_data(dr, ar)

    # AMEX: cashout + deposit = daily revenue
    assert result[(6, 2)] + result[(8, 2)] == pytest.approx(result[(12, 2)], abs=0.01)
    # MC
    assert result[(6, 7)] + result[(8, 7)] == pytest.approx(result[(12, 7)], abs=0.01)
    # VISA
    assert result[(6, 10)] + result[(8, 10)] == pytest.approx(result[(12, 10)], abs=0.01)


def test_geac_balance_sheet_values():
    """Balance sheet should have correct abs values from parser fields."""
    dr = {
        'settlements': {'american_express': 0, 'mastercard': 0, 'visa': 0,
                        'facture_direct': -1641.73},
        'deposits_received': {},
        'balance': {'prev_day': -1476889.24, 'today': -5493.03,
                    'new_balance': -1482382.27},
        'advance_deposits': {'applied': -64522.13},
    }
    ar = {'front_office_transfers': {'guest_folios': 5197.27}}
    result = compute_geac_data(dr, ar)
    assert result[(32, 2)] == pytest.approx(1476889.24, abs=0.01)
    assert result[(37, 5)] == pytest.approx(-5493.03, abs=0.01)  # E37 negative
    assert result[(41, 2)] == pytest.approx(1641.73, abs=0.01)   # B41 = DR Facture Direct
    assert result[(41, 7)] == pytest.approx(5197.27, abs=0.01)   # G41 = AR Guest Folios
    assert result[(44, 2)] == pytest.approx(64522.13, abs=0.01)  # Adv Dep Applied
    assert result[(53, 2)] == pytest.approx(1482382.27, abs=0.01)


def test_geac_b41_equals_g41_when_fd_equals_ar():
    """When FD = AR, B41 and G41 should match (no GEAC compensation)."""
    dr = {
        'settlements': {'facture_direct': -5000.00},
        'deposits_received': {},
        'balance': {},
        'advance_deposits': {},
    }
    ar = {'front_office_transfers': {'guest_folios': 5000.00}}
    result = compute_geac_data(dr, ar)
    assert result[(41, 2)] == pytest.approx(5000.00, abs=0.01)
    assert result[(41, 7)] == pytest.approx(5000.00, abs=0.01)


def test_geac_b41_differs_from_g41_when_fd_ne_ar():
    """When FD != AR, B41 = FD, G41 = AR Guest Folios."""
    dr = {
        'settlements': {'facture_direct': -1641.73},
        'deposits_received': {},
        'balance': {},
        'advance_deposits': {},
    }
    ar = {'front_office_transfers': {'guest_folios': 5197.27}}
    result = compute_geac_data(dr, ar)
    assert result[(41, 2)] == pytest.approx(1641.73, abs=0.01)
    assert result[(41, 7)] == pytest.approx(5197.27, abs=0.01)


def test_geac_row10_not_in_output():
    """Row 10 (Total) is a formula — must not appear in output."""
    dr = {'settlements': {}, 'deposits_received': {}, 'balance': {},
          'advance_deposits': {}}
    ar = {}
    result = compute_geac_data(dr, ar)
    for (r, c) in result:
        assert r != 10, 'Row 10 should not be in GEAC output (formula row)'


def test_geac_none_values_treated_as_zero():
    """None values in parser output should not crash — treated as 0."""
    dr = {
        'settlements': {'american_express': None, 'visa': None},
        'deposits_received': {'ax': None},
        'balance': {'prev_day': None, 'today': None, 'new_balance': None},
        'advance_deposits': {'applied': None},
    }
    ar = {'front_office_transfers': {'guest_folios': None}}
    result = compute_geac_data(dr, ar)
    assert result[(6, 2)] == 0   # AMEX Cash Out
    assert result[(32, 2)] == 0  # Balance Prev Day
