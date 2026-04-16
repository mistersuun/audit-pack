"""Tests for Transelect auto-filler."""
from utils.transelect_filler import compute_transelect_data


def test_positouch_includes_pannes():
    """POSITOUCH values must include PANNE amounts."""
    sj = {
        'payments': {'visa': 1782.26, 'mastercard': 912.63, 'amex': 310.23, 'interac': 568.08},
        'positouch_totals': {
            'visa': 1782.26 + 62.50,
            'mastercard': 912.63,
            'amex': 310.23,
            'interac': 568.08 + 17.49,
        },
        'pannes': {'visa': 62.50, 'interac': 17.49, 'lien_hotel': 9.00},
    }
    dr = {'settlements': {'american_express': -7576.83, 'visa': -12126.86, 'mastercard': -9945.62}}
    result = compute_transelect_data(sj, dr)

    assert result[(10, 24)] == 1844.76, 'VISA POSITOUCH should include PANNE'
    assert result[(9, 24)] == 585.57, 'DEBIT POSITOUCH should include PANNE'
    assert result[(11, 24)] == 912.63, 'MC POSITOUCH unchanged (no panne)'
    assert result[(13, 24)] == 310.23, 'AMEX POSITOUCH unchanged (no panne)'


def test_reception_bank_from_dr_settlements():
    """Reception Bank Report and Daily Revenue should use DR Settlement abs values."""
    sj = {'payments': {}, 'positouch_totals': {}, 'pannes': {}}
    dr = {'settlements': {'american_express': -7576.83, 'visa': -12126.86, 'mastercard': -9945.62}}
    result = compute_transelect_data(sj, dr)

    assert result[(21, 2)] == 12126.86   # B21 VISA
    assert result[(21, 16)] == 12126.86  # P21 VISA (same)
    assert result[(22, 2)] == 9945.62    # B22 MC
    assert result[(24, 2)] == 7576.83    # B24 AMEX


def test_col_i_not_in_output():
    """Column I (col 8) is a formula — must not appear in output."""
    sj = {'payments': {}, 'positouch_totals': {}, 'pannes': {}}
    dr = {'settlements': {'visa': -1000}}
    result = compute_transelect_data(sj, dr)
    for (r, c) in result:
        assert c != 8, 'Column I (8) should not be in output (formula column)'
