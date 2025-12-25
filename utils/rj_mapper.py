"""
Mapping configuration for RJ Excel file.
Defines which form fields map to which Excel cells in each sheet.
"""

# Sheet: controle
CONTROLE_MAPPING = {
    'jour': 'B3',          # Day (DD)
    'mois': 'B4',          # Month (MM)
    'annee': 'B5',         # Year (YYYY)
    'temperature': 'B6',   # Temperature
    'condition': 'B7',     # Weather condition
    'chambres_refaire': 'B9',  # Rooms to redo
    'prepare_par': 'B2',   # Prepared by
}

# Sheet: Recap
RECAP_MAPPING = {
    'date': 'E1',
    'comptant_lightspeed_lecture': 'B6',
    'comptant_lightspeed_corr': 'C6',
    'comptant_positouch_lecture': 'B7',
    'comptant_positouch_corr': 'C7',
    'cheque_payment_register_lecture': 'B8',
    'cheque_payment_register_corr': 'C8',
    'remb_gratuite_lecture': 'B11',
    'remb_gratuite_corr': 'C11',
    'remb_client_lecture': 'B12',
    'remb_client_corr': 'C12',
    'due_back_reception_lecture': 'B16',
    'due_back_reception_corr': 'C16',
    'due_back_nb_lecture': 'B17',
    'due_back_nb_corr': 'C17',
    'surplus_deficit_lecture': 'B19',
    'surplus_deficit_corr': 'C19',
    'depot_canadien_lecture': 'B22',
    'depot_canadien_corr': 'C22',
    'argent_recu': 'B24',
    'prepare_par': 'B26',
}

# Sheet: transelect
TRANSELECT_MAPPING = {
    'date': 'B5',
    'prepare_par': 'B6',

    # --- SECTION 1: POSITOUCH (RESTAURANT/BAR) ---
    # BAR 701
    'bar_701_debit': 'B9',
    'bar_701_visa': 'B10',
    'bar_701_master': 'B11',
    'bar_701_amex': 'B13',

    # BAR 702
    'bar_702_debit': 'C9',
    'bar_702_visa': 'C10',
    'bar_702_master': 'C11',
    'bar_702_amex': 'C13',

    # BAR 703
    'bar_703_debit': 'D9',
    'bar_703_visa': 'D10',
    'bar_703_master': 'D11',
    'bar_703_amex': 'D13',

    # SPESA 704
    'spesa_704_debit': 'E9',
    'spesa_704_visa': 'E10',
    'spesa_704_master': 'E11',
    'spesa_704_amex': 'E13',

    # ROOM 705
    'room_705_visa': 'F10',

    # --- SECTION 2: RÉCEPTION / BANK ---
    # Reception (Terminal) - D Columns
    'reception_debit': 'D20',
    'reception_visa_term': 'D21',
    'reception_master_term': 'D22',
    'reception_amex_term': 'D24',

    # Bank Report (Fuseboxe) - B Columns
    'fusebox_visa': 'B21',
    'fusebox_master': 'B22',
    'fusebox_amex': 'B24',
}

# Sheet: geac_ux
GEAC_UX_MAPPING = {
    'date': 'E22',

    # Daily Cash Out
    'amex_cash_out': 'B6',
    'master_cash_out': 'G6',
    'visa_cash_out': 'J6',

    # Total
    'amex_total': 'B10',
    'discover_total': 'E10',
    'master_total': 'G10',
    'visa_total': 'J10',

    # Daily Revenue
    'amex_daily_revenue': 'B12',
    'master_daily_revenue': 'G12',
    'visa_daily_revenue': 'J12',

    # Balance Previous Day
    'balance_previous': 'B32',

    # Balance Today
    'balance_today': 'B37',

    # Facture Direct
    'facture_direct': 'B41',
    'facture_direct_corr': 'D41',

    # Adv deposit applied
    'adv_deposit': 'B44',
    'adv_deposit_applied': 'J44',

    # New Balance
    'new_balance': 'B53',
}

# Sheet: DUBACK# (DueBack)
# This is more complex - it's a daily table
# Row structure: Day X (row 2*X-1) = Balance, row 2*X = Operations
# Columns: B=Date, C=Araujo, D=Latulippe, E=Caron, F=Aguilar, etc.
DUEBACK_RECEPTIONIST_COLUMNS = {
    'Araujo': 'C',
    'Latulippe': 'D',
    'Caron': 'E',
    'Aguilar': 'F',
    'Nader': 'G',
    'Mompremier': 'H',
    'Oppong': 'I',
    'Seddik': 'J',
    'Dormeus': 'K',
}

def get_dueback_row_for_day(day):
    """Get Excel row numbers for a given day in DueBack sheet."""
    # Day 1 is rows 5-6, Day 2 is rows 7-8, etc.
    balance_row = 3 + (day * 2)
    operations_row = balance_row + 1
    return balance_row, operations_row

# Sheet: SetD
SETD_MAPPING = {
    'date': 'A1',
    # Each day has a row (A5 = day 1, A6 = day 2, etc.)
    # Column B = RJ (total for the day)
    # Other columns for specific accounts
}

def get_setd_row_for_day(day):
    """Get Excel row number for a given day in SetD sheet."""
    return 4 + day  # Day 1 = row 5, Day 2 = row 6, etc.


# Complete cell mapping dictionary
CELL_MAPPINGS = {
    'controle': CONTROLE_MAPPING,
    'Recap': RECAP_MAPPING,
    'transelect': TRANSELECT_MAPPING,
    'geac_ux': GEAC_UX_MAPPING,
}

# Ranges to clear when starting a new day (SheetName: [List of Ranges or Columns])
RESET_RANGES = {
    'Recap': [
        # Lecture Column (B6:B25)
        {'row_start': 5, 'row_end': 24, 'col': 1},
        # Due Back Reception (B16)
        {'row': 15, 'col': 1}
    ],
    'transelect': [
        # Daily Transactions (Row 9-16, Cols B-U)
        {'row_start': 8, 'row_end': 15, 'col_start': 1, 'col_end': 20},
        # Reception Transactions (Row 20-25, Cols B-D)
        {'row_start': 19, 'row_end': 24, 'col_start': 1, 'col_end': 3},
        # Bank Report (Row 20-25, Col A/B) - Verify range
        {'row_start': 19, 'row_end': 24, 'col_start': 0, 'col_end': 0} 
    ],
    'geac_ux': [
        # Daily Cash Out (B6, G6, J6)
        {'row': 5, 'col': 1},
        {'row': 5, 'col': 6},
        {'row': 5, 'col': 9},
        # Daily Revenue (B12, G12, J12)
        {'row': 11, 'col': 1},
        {'row': 11, 'col': 6},
        {'row': 11, 'col': 9}
    ]
}

# Mapping for Syncing DUBACK# values to SetD
# Format: { 'Duback_Name': 'SetD_Name' }
# If SetD_Name is same, it will find it by header match
DUBACK_TO_SETD_MAPPING = {
    'Debby': 'Debby',
    'Josée': 'Josée',
    'Isabelle': 'Isabelle',
    'Dayannis': 'Dayannis',
    'Laeticia': 'Laeticia',
    'Rose-Delande': 'Rose-Delande',
    'zaneta': 'zaneta',
    'ZAYEN': 'ZAYEN',
    'DORMEUS': 'DORMEUS',
    'BACHIRI ': 'BACHIRI',
    'Marly': 'Marly',
    'ROCHE': 'ROCHE',
    'THANEEKAN': 'THANEEKAN',
    'VALERIE': 'VALERIE',
    'Kelly': 'Kelly',
    'LEVESQUE': 'LEVESQUE',
    'Durocher': 'Durocher',
    'Ramzi': 'RAMZI',
    'Jessica': 'JESSICA',
    'Mathieu': 'MATHIEU'
}

