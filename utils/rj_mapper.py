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

    # Financial YTD data (verified against Jan 2026 production file)
    'dollar_sales_ytd': 'B10',       # Vente dollar annuel (YTD)
    'dollar_sales_prev': 'B11',      # Vente dollar annuel (previous year)
    'rooms_available_ytd': 'B12',    # Ch. disponible (YTD)
    'rooms_available_prev': 'B13',   # Ch. disponible (previous year)
    'rooms_occupied_ytd': 'B14',     # Ch. Occupées (YTD)
    'rooms_occupied_prev': 'B15',    # Ch. Occupées (previous year)
    'room_revenue_ytd': 'B16',       # Revenu Chambre (YTD)
    'room_revenue_prev': 'B17',      # Revenu Chambre (previous year)
    'closing_balance': 'B18',        # Balance de fermeture

    # Hotel metadata
    'hotel_name': 'B20',             # HÔTEL SHERATON LAVAL
    'total_rooms': 'B21',            # 252

    # Period info
    'days_in_month': 'B27',          # e.g. 28, 31
    'audit_date': 'B28',             # Excel serial date
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
    'cheque_daily_revenu_lecture': 'B9',
    'cheque_daily_revenu_corr': 'C9',
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
    # Row 22: Dépôt Canadien - NOT EDITABLE (calculated by Excel from SD file)
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
    # Reception Terminal K053 - D Columns
    'reception_debit': 'D20',
    'reception_visa_term': 'D21',
    'reception_master_term': 'D22',
    'reception_amex_term': 'D24',

    # Reception Terminal 8.0 - C Columns (debit can appear here)
    'reception_debit_term8': 'C20',

    # Bank Report (Fuseboxe/FreedomPay) - B Columns
    'fusebox_visa': 'B21',
    'fusebox_master': 'B22',
    'fusebox_amex': 'B24',

    # Quasimodo reconciliation fields (verified against Feb 2026 data)
    'quasimodo_debit': 'E20',
    'quasimodo_visa': 'E21',
    'quasimodo_master': 'E22',
    'quasimodo_amex': 'E24',
}

# Sheet: geac_ux
GEAC_UX_MAPPING = {
    'date': 'E22',

    # Daily Cash Out (Row 6)
    'amex_cash_out': 'B6',
    'diners_cash_out': 'E6',
    'master_cash_out': 'G6',
    'visa_cash_out': 'J6',
    'discover_cash_out': 'K6',

    # Total (Row 10) - auto-calculated, but mapped for reference
    'amex_total': 'B10',
    'diners_total': 'E10',
    'master_total': 'G10',
    'visa_total': 'J10',
    'discover_total': 'K10',

    # Daily Revenue (Row 12)
    'amex_daily_revenue': 'B12',
    'diners_daily_revenue': 'E12',
    'master_daily_revenue': 'G12',
    'visa_daily_revenue': 'J12',
    'discover_daily_revenue': 'K12',

    # Balance Previous Day (Row 32)
    'balance_previous': 'B32',
    'balance_previous_guest': 'E32',

    # Balance Today (Row 37)
    'balance_today': 'B37',
    'balance_today_guest': 'E37',

    # Facture Direct (Row 41)
    'facture_direct': 'B41',
    'facture_direct_guest': 'G41',

    # Adv deposit applied (Row 44)
    'adv_deposit': 'B44',
    'adv_deposit_applied': 'J44',

    # New Balance (Row 53) - auto-calculated
    'new_balance': 'B53',
    'new_balance_guest': 'E53',
}

# Sheet: DUBACK# (DueBack)
# This is more complex - it's a daily table
# Row structure: Day X (row 2*X-1) = Balance, row 2*X = Operations
# Columns: B=Date, C-Z=Receptionists (24 total)

# DueBack sheet receptionist columns.
# MAINTENANCE: Update this mapping when receptionists change.
# Each key is the receptionist name as it appears in the Excel header (row 3),
# and the value is the Excel column letter.
# TODO: Consider reading this dynamically from row 3 of the DUBACK# sheet.
DUEBACK_RECEPTIONIST_COLUMNS = {
    'Araujo': 'C',          # Debby
    'Latulippe': 'D',       # Josée
    'Caron': 'E',           # Isabelle
    'Nader': 'F',           # Laeticia
    'Mompremier': 'G',      # Rose-Delande
    'oppong': 'H',          # zaneta
    'SEDDIK': 'I',          # ZAYEN
    'Kimberly': 'J',        # Tavarez
    'AYA': 'K',             # BACHIRI
    'Leo': 'L',             # Scarpa
    'THANKARAJAH': 'M',     # THANEEKAN
    'CINDY': 'N',           # PIERRE
    'Manolo': 'O',          # Cabrera
    'MOUATARIF': 'P',       # KHALIL
    'KRAY': 'Q',            # VALERIE
    'NITHYA': 'R',          # SAY
    'DAMAL': 'S',           # Kelly
    'MAUDE': 'T',           # LEVESQUE
    'OLGA': 'U',            # ARHANTOU
    'Sylvie': 'V',          # Pierre
    'Emery': 'W',           # Uwimana
    'Ben mansour': 'X',     # Ramzi
    'ANNIE-LIS': 'Y',       # KASPERIAN
    'Total': 'Z',           # Total column
}

def get_dueback_row_for_day(day):
    """
    Get row indices for a given day in the DueBack sheet.

    Args:
        day: Day of month (1-31)

    Returns:
        Tuple of (balance_row, operations_row) as 0-based row indices
        suitable for xlrd/xlwt.

    Examples:
        Day 1: (4, 5)   → Excel rows 5, 6
        Day 11: (24, 25) → Excel rows 25, 26
        Day 31: (64, 65) → Excel rows 65, 66
    """
    balance_row = 2 + (day * 2)
    operations_row = balance_row + 1
    return balance_row, operations_row

# Sheet: SetD
SETD_MAPPING = {
    'date': 'A1',
    # Each day has a row (A5 = day 1, A6 = day 2, etc.)
    # Column B = RJ (total for the day)
    # Other columns for specific personnel accounts
}

# SetD Personnel Column Mapping (135 personnel - excludes system entries)
SETD_PERSONNEL_COLUMNS = {
    'Martine Breton': 'C',
    'Petite Caisse': 'E',
    'Conc. Banc.': 'F',
    'Corr. Mois suivant': 'G',
    'JEAN PHILIPPE': 'H',
    'Tristan Tremblay': 'I',
    'Mandy Le': 'J',
    'Frederic Dupont': 'K',
    'Florence Roy': 'L',
    'Marie Carlesso': 'M',
    'Patrick Caron': 'N',
    'KARL LECLERC': 'O',
    'Stéphane Latulippe': 'P',
    'natalie rousseau': 'Q',
    'DAVID GIORGI': 'R',
    'YOUSSIF GANNI': 'S',
    'MYRLENE BELIVEAU': 'T',
    'EMMANUELLE LUSSIER': 'U',
    'DANIELLE BELANGER': 'V',
    'VALERIE GUERIN': 'W',
    'Youri Georges': 'X',
    'Alexandre Thifault': 'Y',
    'Julie Dagenais': 'Z',
    'PATRICK MARTEL': 'AA',
    'Nelson Dacosta': 'AB',
    'NAOMIE COLIN': 'AC',
    'SOPHIE CHIARUCCI': 'AD',
    'CHRISTOS MORENTZOS': 'AE',
    'WOODS John': 'AF',
    'MARCO Sabourin': 'AG',
    'sachetti francois': 'AH',
    'caouette Phillipe': 'AI',
    'Caron Patrick': 'AJ',
    'MIXOLOGUE': 'AK',
    'GIOVANNI TOMANELLI': 'AL',
    'Mathieu Guerit': 'AN',
    'Marie Eve': 'AO',
    'CARL Tourangeau': 'AP',
    'MAUDE GAUTHIER': 'AQ',
    'Stephane Bernachez': 'AR',
    'Jonathan Samedy': 'AS',
    'NICOLAS Bernatchez': 'AT',
    'JULIEN BAZAGLE': 'AU',
    'Panayota Lappas': 'AV',
    'PLINIO TESTA Campos': 'AW',
    'spiro Katsenis': 'AX',
    'Isabelle Leclair': 'AY',
    'ANAIS BESETTE': 'AZ',
    'DRAGAN MILOVIC': 'BA',
    'LIDA RAMASAN': 'BB',
    'RAFFI OYAN': 'BC',
    'CECIL PATRICIA': 'BD',
    'QUENTIN BRUNET': 'BE',
    'Sabrina Gagnon': 'BF',
    'NOEMY ROY': 'BG',
    'Melanie Guilemette': 'BH',
    'Pierre-luc Lapointe': 'BI',
    'Adelaide Rancourt': 'BJ',
    'theriault emilie': 'BK',
    'Sandra Tremblay': 'BL',
    'DAVID DFAUCHER': 'BM',
    'LINDA': 'BN',
    'olivier lamothe': 'BO',
    'gozzi alexandra': 'BP',
    'Sarah Vesnaver': 'BQ',
    'Forget Caroline': 'BR',
    'ANDREW STEPHANE': 'BS',
    'Tremblay Caroline': 'BT',
    'jessica simon': 'BU',
    'Francis Latour': 'BV',
    'Constantino Difruschia': 'BW',
    'Cuong Tran': 'BX',
    'MATHIEU GUERIT': 'BY',
    'Youri George': 'BZ',
    'Arnaud Duguay': 'CA',
    'JOSE LATUPLIPPE': 'CB',
    'Mixologue 2.0': 'CC',
    'MIXOLOGUE 3.0': 'CE',
    'Dany Prouxl-Rivard': 'CF',
    'JONNI LANGLOIS': 'CG',
    'Laurence': 'CH',
    'Morgane Muffait': 'CI',
    'NICOLE': 'CJ',
    'VICTOR GUEFAELLY': 'CK',
    'Emma Heguy': 'CL',
    'MANON RINGROSE': 'CM',
    'lethicia heinmeyer': 'CN',
    'Stephanie desjardins': 'CO',
    'Elisabetta Lungarini': 'CP',
    'France bergeron': 'CR',
    'kalena Caticchio': 'CS',
    'Nicolle Blanchard': 'CT',
    'DRAGANA RADOVANOVIC': 'CU',
    'elena kaltsoudas': 'CV',
    'Jean-Seb. Pitre': 'CW',
    'CHARLES R': 'CX',
    'Pier Audrey Belanger': 'CY',
    'GINO MOURIN': 'CZ',
    'Sophie c': 'DA',
    'Philippe Caouette': 'DB',
    'Marly Innocent': 'DC',
    'MOHAMED ELSABER': 'DD',
    'SOULEYMANE CAMARA': 'DE',
    'KHALIL MOUATARIF': 'DF',
    'MANOLO C': 'DG',
    'Laeticia Nader': 'DH',
    'Sylvie Pierre': 'DI',
    'Debbie Fleurant-Rioux': 'DJ',
    'Debby Araujo': 'DK',
    'Isabelle Caron': 'DL',
    'Rose-Delande Mompremier': 'DM',
    'ANGELO JOSEPH': 'DN',
    'ANNIE': 'DO',
    'JEAN-MICHEL CYR': 'DP',
    'damal Kelly': 'DQ',
    'JESSICA SIMON': 'DR',
    'levesque MAUDE': 'DS',
    'Josée Latulippe': 'DT',
    'SARAH MADITUKA': 'DU',
    'LEO SCARPA': 'DV',
    'Schneidine': 'DX',
    'thaneekan': 'DY',
    'AYA BACHARI': 'DZ',
    'SEDDIK ZAYEN': 'EA',
    'VALERIE KRAY': 'EB',
    'sarah': 'EC',
    'OPPONG ZANETA': 'ED',
    'guylaine': 'EE',
    'pierre cindy': 'EF',
    'Cristancho Natalia': 'EH',
    'Durocher Stéphanie': 'EI',
}

def get_setd_row_for_day(day):
    """
    Get row index for a given day in SetD sheet.

    Args:
        day: Day of month (1-31)

    Returns:
        0-based row index suitable for xlrd/xlwt.
        (Day 1 = index 5, Day 2 = index 6, which are Excel rows 6, 7)
    """
    return 4 + day  # Day 1 = 5, Day 2 = 6, etc.

def get_setd_cell(day, column_letter):
    """
    Get Excel cell reference for SetD entry.

    Args:
        day (int): Day of month (1-31)
        column_letter (str): Column letter ('B' for RJ, 'C'-'AX' for personnel)

    Returns:
        str: Excel cell reference (e.g., 'B5', 'I19', 'O14')

    Examples:
        get_setd_cell(1, 'B') → 'B5' (Day 1, RJ)
        get_setd_cell(23, 'B') → 'B27' (Day 23, RJ)
        get_setd_cell(15, 'I') → 'I19' (Day 15, Tristan Tremblay)
    """
    row = 4 + day
    return f"{column_letter}{row}"


# Complete cell mapping dictionary
CELL_MAPPINGS = {
    'controle': CONTROLE_MAPPING,
    'Recap': RECAP_MAPPING,
    'transelect': TRANSELECT_MAPPING,
    'geac_ux': GEAC_UX_MAPPING,
}

# Ranges to clear when starting a new day (SheetName: [List of Ranges or Columns])
# Based on VBA macros: efface_recap(), eff_trans(), efface_rapport_geac(), Eff_depot()
RESET_RANGES = {
    # efface() / efface_recap() - VBA from Module7:
    # Range("B6:C20").ClearContents
    # Range("D9:D10").ClearContents
    # Range("D12:D14").ClearContents
    # Range("D16").ClearContents
    # Range("D18").ClearContents
    'Recap': [
        # B6:C20 - Lecture and Corr columns (row 5-19, col 1-2)
        {'row_start': 5, 'row_end': 20, 'col_start': 1, 'col_end': 3},
        # D9:D10 - Net column rows 9-10 (row 8-9, col 3)
        {'row_start': 8, 'row_end': 10, 'col': 3},
        # D12:D14 - Net column rows 12-14 (row 11-13, col 3)
        {'row_start': 11, 'row_end': 14, 'col': 3},
        # D16 - Net column row 16 (row 15, col 3)
        {'row': 15, 'col': 3},
        # D18 - Net column row 18 (row 17, col 3)
        {'row': 17, 'col': 3},
    ],

    # eff_trans() - VBA: Range("B9:U13,X9:X13,B20:H24,J20:P24").ClearContents
    'transelect': [
        # B9:U13 - Credit card data (row 8-12, col 1-20)
        {'row_start': 8, 'row_end': 13, 'col_start': 1, 'col_end': 21},
        # X9:X13 - Column X totals (row 8-12, col 23)
        {'row_start': 8, 'row_end': 13, 'col': 23},
        # B20:H24 - Bank report section (row 19-23, col 1-7)
        {'row_start': 19, 'row_end': 24, 'col_start': 1, 'col_end': 8},
        # J20:P24 - Additional sections (row 19-23, col 9-15)
        {'row_start': 19, 'row_end': 24, 'col_start': 9, 'col_end': 16},
    ],

    # efface_rapport_geac() - VBA: Range("B6:C6,E6,G6:H6,J6,B8:C8,E8,G8:H8,J8,
    #   B12:C12,E12,G12:H12,J12,B32:C32,E32,B37:C37,E37,B41:C41,G41:H41,
    #   B44:C44,J44:K44,B47:C47,E47,B50:C50,E50,B53:C53,E53").ClearContents
    'geac_ux': [
        # Row 6: B6:C6, E6, G6:H6, J6
        {'row': 5, 'col_start': 1, 'col_end': 3},   # B6:C6
        {'row': 5, 'col': 4},                        # E6
        {'row': 5, 'col_start': 6, 'col_end': 8},   # G6:H6
        {'row': 5, 'col': 9},                        # J6
        # Row 8: B8:C8, E8, G8:H8, J8
        {'row': 7, 'col_start': 1, 'col_end': 3},   # B8:C8
        {'row': 7, 'col': 4},                        # E8
        {'row': 7, 'col_start': 6, 'col_end': 8},   # G8:H8
        {'row': 7, 'col': 9},                        # J8
        # Row 12: B12:C12, E12, G12:H12, J12
        {'row': 11, 'col_start': 1, 'col_end': 3},  # B12:C12
        {'row': 11, 'col': 4},                       # E12
        {'row': 11, 'col_start': 6, 'col_end': 8},  # G12:H12
        {'row': 11, 'col': 9},                       # J12
        # Row 32: B32:C32, E32
        {'row': 31, 'col_start': 1, 'col_end': 3},  # B32:C32
        {'row': 31, 'col': 4},                       # E32
        # Row 37: B37:C37, E37
        {'row': 36, 'col_start': 1, 'col_end': 3},  # B37:C37
        {'row': 36, 'col': 4},                       # E37
        # Row 41: B41:C41, G41:H41
        {'row': 40, 'col_start': 1, 'col_end': 3},  # B41:C41
        {'row': 40, 'col_start': 6, 'col_end': 8},  # G41:H41
        # Row 44: B44:C44, J44:K44
        {'row': 43, 'col_start': 1, 'col_end': 3},  # B44:C44
        {'row': 43, 'col_start': 9, 'col_end': 11}, # J44:K44
        # Row 47: B47:C47, E47
        {'row': 46, 'col_start': 1, 'col_end': 3},  # B47:C47
        {'row': 46, 'col': 4},                       # E47
        # Row 50: B50:C50, E50
        {'row': 49, 'col_start': 1, 'col_end': 3},  # B50:C50
        {'row': 49, 'col': 4},                       # E50
        # Row 53: B53:C53, E53
        {'row': 52, 'col_start': 1, 'col_end': 3},  # B53:C53
        {'row': 52, 'col': 4},                       # E53
    ],

    # Eff_depot() - VBA: Range("eff_depot").ClearContents (A10:K42)
    'depot': [
        # A10:K42 - All deposit entries (row 9-41, col 0-10)
        {'row_start': 9, 'row_end': 42, 'col_start': 0, 'col_end': 11},
    ],

    # eff_daily() - VBA: Range("B2:B41,B44,B47").ClearContents
    # This is for the "daily" sheet (daily revenue summary)
    'daily': [
        # B2:B41 - Main data (row 1-40, col 1)
        {'row_start': 1, 'row_end': 41, 'col': 1},
        # B44 - Single cell (row 43, col 1)
        {'row': 43, 'col': 1},
        # B47 - Single cell (row 46, col 1)
        {'row': 46, 'col': 1},
    ],
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

# =============================================================================
# JOUR SHEET COLUMN CONSTANTS
# =============================================================================
# These define where macros write data into the jour sheet.
# Previously hardcoded in rj_filler.py, now centralized here.

# Row offset for days in jour sheet: Day 1 = row 5 (index 4), Day 2 = row 6, etc.
JOUR_DAY_ROW_OFFSET = 4  # target_row = JOUR_DAY_ROW_OFFSET + day - 1

def get_jour_row_for_day(day):
    """Get 0-indexed row number for a day in the jour sheet."""
    return JOUR_DAY_ROW_OFFSET + day - 1

# envoie_dans_jour macro: copies Recap H19:N19 → jour columns BU:CA
# BU=72, BV=73, BW=74, BX=75, BY=76, BZ=77, CA=78 (0-indexed)
JOUR_RECAP_COLS = [72, 73, 74, 75, 76, 77, 78]  # BU through CA
JOUR_RECAP_SOURCE = {'sheet': 'Recap', 'row': 18, 'cols': list(range(7, 14))}  # H19:N19

# calcul_carte macro: copies transelect totals → jour columns starting at BF
# BF=57 (0-indexed)
JOUR_CC_START_COL = 57  # BF column
JOUR_CC_SOURCE = {'sheet': 'transelect', 'row': 13}  # Row 14 totals

# Jour sheet total columns count
JOUR_TOTAL_COLUMNS = 117

