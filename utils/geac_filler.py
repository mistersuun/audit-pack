"""GEAC_UX sheet auto-fill from parsed Daily Revenue and AR Summary data.

Computes card variance (top) and balance sheet (bottom) sections.
Returns a dict of {(row, col): value} for use with RJFillerCOM.write_geac().
"""


def compute_geac_data(dr_data, ar_data):
    """Compute all GEAC_UX cell values from parsed source data.

    Accepts raw DailyRevenueParser and ARSummaryParser output directly.

    Args:
        dr_data: DailyRevenueParser.extracted_data dict with keys:
            settlements: {american_express, visa, mastercard, facture_direct}
            deposits_received: {ax, visa, mastercard}
            balance: {prev_day, today, new_balance}
            advance_deposits: {applied}
        ar_data: ARSummaryParser.extracted_data dict with keys:
            front_office_transfers: {guest_folios}

    Returns:
        dict of {(row, col): value} for GEAC cells (1-based row/col)
    """
    # Extract settlement amounts (absolute values)
    settlements = dr_data.get('settlements', {})
    amex_settle = abs(settlements.get('american_express', 0) or 0)
    mc_settle = abs(settlements.get('mastercard', 0) or 0)
    visa_settle = abs(settlements.get('visa', 0) or 0)

    # Extract deposits received (parser key: deposits_received)
    deps = dr_data.get('deposits_received', {})
    amex_dep = abs(deps.get('ax', 0) or 0)
    mc_dep = abs(deps.get('mastercard', 0) or 0)
    visa_dep = abs(deps.get('visa', 0) or 0)

    # Cash out = Settlement - Deposit
    amex_cashout = amex_settle - amex_dep
    mc_cashout = mc_settle - mc_dep
    visa_cashout = visa_settle - visa_dep

    # Balance sheet values (all positive/abs)
    balance = dr_data.get('balance', {})
    bal_prev = abs(balance.get('prev_day', 0) or 0)
    bal_today = abs(balance.get('today', 0) or 0)
    new_bal = abs(balance.get('new_balance', 0) or 0)

    # Advance deposits applied (parser key: advance_deposits.applied)
    adv_dep_applied = abs(
        dr_data.get('advance_deposits', {}).get('applied', 0) or 0
    )

    # AR Guest Folios (parser key: front_office_transfers.guest_folios)
    ar_guest_folios = abs(
        ar_data.get('front_office_transfers', {}).get('guest_folios', 0) or 0
    )

    # Facture Direct for B41 (parser key: settlements.facture_direct)
    # B41 = FD, G41 = AR Guest Folios.  They equal when no GEAC compensation.
    facture_direct = abs(settlements.get('facture_direct', 0) or 0)
    if facture_direct == 0:
        # When FD unavailable, use guest_folios (assumes FD = AR)
        facture_direct = ar_guest_folios

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
        (41, 2): facture_direct,  # B41 = DR Facture Direct
        (41, 7): ar_guest_folios, # G41 = AR Guest Folios
        (44, 2): adv_dep_applied, # B44 Adv Dep Applied
        (44, 10): adv_dep_applied, # J44 mirror
        (53, 2): new_bal,         # B53 New Balance
        (53, 5): new_bal,         # E53 mirror
    }
