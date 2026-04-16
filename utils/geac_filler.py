"""GEAC_UX sheet auto-fill from parsed Daily Revenue and AR Summary data.

Computes card variance (top) and balance sheet (bottom) sections.
Returns a dict of {(row, col): value} for use with RJFillerCOM.write_geac().
"""


def compute_geac_data(dr_data, ar_data):
    """Compute all GEAC_UX cell values from parsed source data.

    Args:
        dr_data: parsed Daily Revenue dict with keys:
            settlements.american_express, settlements.visa, settlements.mastercard
            deposits.dep_rcvd_ax, deposits.dep_rcvd_visa, deposits.dep_rcvd_master
            balance.balance_prev_day, balance.balance_today
            balance.new_balance, balance.adv_dep_applied
        ar_data: parsed AR Summary dict with keys:
            guest_folios

    Returns:
        dict of {(row, col): value} for GEAC cells
    """
    # Extract settlement amounts (absolute values)
    amex_settle = abs(dr_data.get('settlements', {}).get('american_express', 0))
    mc_settle = abs(dr_data.get('settlements', {}).get('mastercard', 0))
    visa_settle = abs(dr_data.get('settlements', {}).get('visa', 0))

    # Extract deposits received
    amex_dep = abs(dr_data.get('deposits', {}).get('dep_rcvd_ax', 0))
    mc_dep = abs(dr_data.get('deposits', {}).get('dep_rcvd_master', 0))
    visa_dep = abs(dr_data.get('deposits', {}).get('dep_rcvd_visa', 0))

    # Cash out = Settlement - Deposit
    amex_cashout = amex_settle - amex_dep
    mc_cashout = mc_settle - mc_dep
    visa_cashout = visa_settle - visa_dep

    # Balance sheet values (all positive/abs)
    bal_prev = abs(dr_data.get('balance', {}).get('balance_prev_day', 0))
    bal_today = abs(dr_data.get('balance', {}).get('balance_today', 0))
    new_bal = abs(dr_data.get('balance', {}).get('new_balance', 0))
    adv_dep_applied = abs(dr_data.get('balance', {}).get('adv_dep_applied', 0))
    ar_guest_folios = abs(ar_data.get('guest_folios', 0))

    return {
        # Top: Card Variance — cols B=2, G=7, J=10
        (6, 2): amex_cashout,     # B6 AMEX Cash Out
        (6, 7): mc_cashout,       # G6 MC Cash Out
        (6, 10): visa_cashout,    # J6 VISA Cash Out
        (8, 2): amex_dep,         # B8 AMEX Deposit
        (8, 7): mc_dep,           # G8 MC Deposit
        (8, 10): visa_dep,        # J8 VISA Deposit
        # R10 is formula — skip
        (12, 2): amex_settle,     # B12 AMEX Daily Revenue
        (12, 7): mc_settle,       # G12 MC Daily Revenue
        (12, 10): visa_settle,    # J12 VISA Daily Revenue
        # Bottom: Balance Sheet
        (32, 2): bal_prev,        # B32 Balance Prev Day
        (32, 5): bal_prev,        # E32 mirror
        (37, 2): bal_today,       # B37 Balance Today
        (37, 5): -bal_today,      # E37 negative
        (41, 2): ar_guest_folios, # B41 = AR Guest Folios
        (41, 7): ar_guest_folios, # G41 = same
        (44, 2): adv_dep_applied, # B44 Adv Dep Applied
        (44, 10): adv_dep_applied, # J44 mirror
        (53, 2): new_bal,         # B53 New Balance
        (53, 5): new_bal,         # E53 mirror
    }
