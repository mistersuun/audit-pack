"""Transelect sheet auto-fill from parsed Sales Journal and Daily Revenue data.

Computes POSITOUCH values (restaurant) and Reception bank values.
Returns a dict of {(row, col): value} for use with RJFillerCOM.write_transelect().
"""


def compute_transelect_data(sj_data, dr_data):
    """Compute Transelect cell values from parsed SJ + DR data.

    Args:
        sj_data: parsed Sales Journal dict with keys:
            payments: {visa, mastercard, amex, interac}
            positouch_totals: {visa, mastercard, amex, interac} (card + panne)
            pannes: {visa, mastercard, amex, interac, lien_hotel}
        dr_data: parsed Daily Revenue dict with keys:
            settlements: {american_express, visa, mastercard, carte_debit}

    Returns:
        dict of {(row, col): value} for Transelect cells
    """
    result = {}

    # Restaurant POSITOUCH (col X = col 24)
    # POSITOUCH = SJ card debit + SJ PANNE per card type
    pos = sj_data.get('positouch_totals', {})
    result[(9, 24)] = pos.get('interac', 0)      # R9 DEBIT POSITOUCH
    result[(10, 24)] = pos.get('visa', 0)         # R10 VISA POSITOUCH
    result[(11, 24)] = pos.get('mastercard', 0)   # R11 MASTER POSITOUCH
    result[(13, 24)] = pos.get('amex', 0)         # R13 AMEX POSITOUCH

    # Reception Bank Report (col B = col 2) + Daily Revenue (col P = col 16)
    # Both get the same value = DR Settlement per card (abs)
    # Col I (col 8) is a FORMULA — do NOT include
    settlements = dr_data.get('settlements', {})
    visa_settle = abs(settlements.get('visa', 0))
    mc_settle = abs(settlements.get('mastercard', 0))
    amex_settle = abs(settlements.get('american_express', 0))

    if visa_settle > 0:
        result[(21, 2)] = visa_settle     # B21 Bank Report VISA
        result[(21, 16)] = visa_settle    # P21 Daily Revenue VISA
    if mc_settle > 0:
        result[(22, 2)] = mc_settle       # B22 Bank Report MASTER
        result[(22, 16)] = mc_settle      # P22 Daily Revenue MASTER
    if amex_settle > 0:
        result[(24, 2)] = amex_settle     # B24 Bank Report AMEX
        result[(24, 16)] = amex_settle    # P24 Daily Revenue AMEX

    return result
