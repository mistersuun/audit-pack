"""Tests for GEAC auto-filler."""
from utils.geac_filler import compute_geac_data


def test_geac_card_variance_balanced():
    """Cash Out + Deposit should equal Daily Revenue per card."""
    dr = {
        'settlements': {'american_express': -7576.83, 'mastercard': -9945.62, 'visa': -12126.86},
        'deposits': {'dep_rcvd_ax': 5707.24, 'dep_rcvd_master': 474.09, 'dep_rcvd_visa': 993.65},
        'balance': {'balance_prev_day': -1476889.24, 'balance_today': -5493.03,
                    'new_balance': -1482382.27, 'adv_dep_applied': -64522.13},
    }
    ar = {'guest_folios': 5197.27}
    result = compute_geac_data(dr, ar)

    # AMEX: cashout + deposit = daily revenue
    assert result[(6, 2)] + result[(8, 2)] == result[(12, 2)]
    # MC
    assert abs(result[(6, 7)] + result[(8, 7)] - result[(12, 7)]) < 0.01
    # VISA
    assert abs(result[(6, 10)] + result[(8, 10)] - result[(12, 10)]) < 0.01


def test_geac_balance_sheet_values():
    """Balance sheet should have correct abs values."""
    dr = {
        'settlements': {'american_express': 0, 'mastercard': 0, 'visa': 0},
        'deposits': {},
        'balance': {'balance_prev_day': -1476889.24, 'balance_today': -5493.03,
                    'new_balance': -1482382.27, 'adv_dep_applied': -64522.13,
                    'front_office_transfers': 1641.73},
    }
    ar = {'guest_folios': 5197.27}
    result = compute_geac_data(dr, ar)
    assert result[(32, 2)] == 1476889.24
    assert result[(37, 5)] == -5493.03  # E37 negative
    assert result[(41, 2)] == 1641.73   # B41 = DR Facture Direct
    assert result[(41, 7)] == 5197.27   # G41 = AR Guest Folios
    assert result[(53, 2)] == 1482382.27


def test_geac_b41_equals_g41_when_fd_equals_ar():
    """When FD = AR, B41 and G41 should match (no GEAC compensation)."""
    dr = {
        'settlements': {}, 'deposits': {},
        'balance': {'front_office_transfers': 5000.00},
    }
    ar = {'guest_folios': 5000.00}
    result = compute_geac_data(dr, ar)
    assert result[(41, 2)] == 5000.00  # B41 = FD
    assert result[(41, 7)] == 5000.00  # G41 = AR


def test_geac_b41_differs_from_g41_when_fd_ne_ar():
    """When FD != AR, B41 = FD, G41 = AR Guest Folios."""
    dr = {
        'settlements': {}, 'deposits': {},
        'balance': {'front_office_transfers': 1641.73},
    }
    ar = {'guest_folios': 5197.27}
    result = compute_geac_data(dr, ar)
    assert result[(41, 2)] == 1641.73  # B41 = FD
    assert result[(41, 7)] == 5197.27  # G41 = AR


def test_geac_row10_not_in_output():
    """Row 10 (Total) is a formula — must not appear in output."""
    dr = {'settlements': {}, 'deposits': {}, 'balance': {}}
    ar = {}
    result = compute_geac_data(dr, ar)
    for (r, c) in result:
        assert r != 10, 'Row 10 should not be in GEAC output (formula row)'
