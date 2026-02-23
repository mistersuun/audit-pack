"""
Jour Mapping Dictionary — NightAuditSession jour_* fields to Excel JOUR sheet columns.

Maps NAS jour_* database field names to their corresponding Excel column indices (0-indexed)
in the JOUR sheet of the RJ Excel workbook.

This is a bidirectional mapping:
- JOUR_NAS_TO_COL: For EXPORT (NAS → Excel)
- JOUR_COL_TO_NAS: For IMPORT (Excel → NAS)
- JOUR_MACRO_COLS: Identifies columns from the "envoie_dans_jour" macro (skip/treat specially)

Usage:
    from utils.jour_mapping import JOUR_NAS_TO_COL, nas_jour_to_excel_dict

    # Convert a NightAuditSession to Excel format
    session = NightAuditSession.query.filter_by(audit_date='2026-02-04').first()
    jour_dict = nas_jour_to_excel_dict(session)
    # jour_dict = {4: 1500.25, 5: 200.00, 9: 1981.40, ...}

    # Pass to RJFiller
    filler = RJFiller('path/to/RJ.xlsx')
    filler.fill_jour_day(row_index=7, jour_values=jour_dict)
"""

# ==============================================================================
# F&B REVENUE — CAFÉ PAUSE SPESA (Columns 4-8)
# ==============================================================================
# Café Link (also called "Pause Spesa Nouveau" or "Link Grill")
# These 5 columns represent beverage categories for the café outlet.
JOUR_NAS_TO_COL = {
    # ────── F&B DEPARTMENTS ──────
    # Café/Pause Spesa (cols 4-8)
    'jour_cafe_nourriture': 4,      # Col E: PAUSE SPESA Nou (food)
    'jour_cafe_boisson': 5,         # Col F: Boi_Link (beverages)
    'jour_cafe_bieres': 6,          # Col G: Bie_Link (beer)
    'jour_cafe_mineraux': 7,        # Col H: Min_Link (non-alcoholic)
    'jour_cafe_vins': 8,            # Col I: Vin_Link (wine)

    # Piazza/Cupola (cols 9-13)
    'jour_piazza_nourriture': 9,    # Col J: PIAZZA/CUPOLA Nou (food)
    'jour_piazza_boisson': 10,      # Col K: Boi_piazza (beverages)
    'jour_piazza_bieres': 11,       # Col L: Bie_piazza (beer)
    'jour_piazza_mineraux': 12,     # Col M: Min_piazza (non-alcoholic)
    'jour_piazza_vins': 13,         # Col N: Vin_piazza (wine)

    # Marché La Spesa (cols 14-18)
    'jour_spesa_nourriture': 14,    # Col O: MARCHÉ LA SPESA (food)
    'jour_spesa_boisson': 15,       # Col P: Boi_mar (beverages)
    'jour_spesa_bieres': 16,        # Col Q: Bie_mar (beer)
    'jour_spesa_mineraux': 17,      # Col R: Min_mar (non-alcoholic)
    'jour_spesa_vins': 18,          # Col S: Vin_mar (wine)

    # Service Aux Chambres (Room Service, cols 19-23)
    'jour_chambres_svc_nourriture': 19,   # Col T: SERVICE AUX CHAMBRES (food)
    'jour_chambres_svc_boisson': 20,      # Col U: Boi_svc (beverages)
    'jour_chambres_svc_bieres': 21,       # Col V: Bie_svc (beer)
    'jour_chambres_svc_mineraux': 22,     # Col W: Min_svc (non-alcoholic)
    'jour_chambres_svc_vins': 23,         # Col X: Vin_svc (wine)

    # Banquet (cols 24-28)
    'jour_banquet_nourriture': 24,  # Col Y: BANQUET Nou (food)
    'jour_banquet_boisson': 25,     # Col Z: Boi_banquet (beverages)
    'jour_banquet_bieres': 26,      # Col AA: Bie_banquet (beer)
    'jour_banquet_mineraux': 27,    # Col AB: Min_banquet (non-alcoholic)
    'jour_banquet_vins': 28,        # Col AC: Vin_banquet (wine)

    # Other F&B items
    'jour_pourboires': 29,          # Col AD: Pourboires (tips)
    'jour_tabagie': 35,             # Col AJ: Tabagie (tobacco/retail)
    'jour_location_salle': 32,      # Col AG: Location de Salles (room rental)

    # ────── ROOMS & TELEPHONES ──────
    'jour_room_revenue': 36,        # Col AK: Chambres (room revenue)
    'jour_tel_local': 37,           # Col AL: Tel local
    'jour_tel_interurbain': 38,     # Col AM: Tel interurbain
    'jour_tel_publics': 39,         # Col AN: Tel publics

    # ────── AUTRES REVENUS (OTHER REVENUE) ──────
    'jour_autres_gl': 44,           # Col AS: Autres Grand Livre (General Ledger misc)
    'jour_nettoyeur': 40,           # Col AO: Nettoyeur (dry cleaning)
    'jour_machine_distrib': 41,     # Col AP: Machine Distributrice (vending machines)
    'jour_sonifi': 45,              # Col AT: Sonifi (in-room entertainment)
    'jour_lit_pliant': 46,          # Col AU: Lit pliant (cot rental)
    'jour_boutique': 47,            # Col AV: Location De Boutique (shop rental)
    'jour_internet': 48,            # Col AW: Internet
    'jour_massage': 52,             # Col BA: Massage

    # ────── TAXES ──────
    'jour_tvq': 49,                 # Col AX: TVQ Provinciale (QST)
    'jour_tps': 50,                 # Col AY: TPS Federale (GST)
    'jour_taxe_hebergement': 51,    # Col AZ: Taxe hébergement (room tax)

    # ────── SETTLEMENTS & SPECIAL ──────
    'jour_gift_cards': 54,          # Col BC: Gift Cards & Bon d'achat
    'jour_certificats': 80,         # Col CC: Certificat Cadeaux (gift certificates)
    'jour_club_lounge': 57,         # Col BF: Club Lounge & Forfait (special calculated)
    'jour_deposit_on_hand': 86,     # Col CI: Deposit on hand (advance deposits balance sheet)
    'jour_ar_misc': 83,             # Col CF: A/R Misc + Front Office Transfers

    # ────── OCCUPANCY & ROOMS SOLD ──────
    'jour_rooms_simple': 88,        # Col CM: SIMPLE (simple rooms sold)
    'jour_rooms_double': 89,        # Col CN: DOUBLE (double rooms sold)
    'jour_rooms_suite': 90,         # Col CO: SUITE (suite rooms sold)
    'jour_rooms_comp': 91,          # Col CP: COMP (complimentary rooms)
    'jour_nb_clients': 92,          # Col CQ: # CLIENT (number of guests)
    'jour_rooms_hors_usage': 93,    # Col CR: HORS D'USAGE (out of service)
}

# Reverse mapping: Excel column index → NAS field name
JOUR_COL_TO_NAS = {v: k for k, v in JOUR_NAS_TO_COL.items()}

# ────── DERIVED/CALCULATED FIELDS (NOT mapped to spreadsheet directly) ──────
# These are calculated in the NAS model using calculate_jour_kpis()
JOUR_CALCULATED_FIELDS = {
    'jour_total_fb': None,          # Sum of all F&B + tips + room rental
    'jour_total_revenue': None,     # Grand total revenue
    'jour_adr': None,               # Average Daily Rate (room revenue / rooms sold)
    'jour_revpar': None,            # Revenue Per Available Room
    'jour_occupancy_rate': None,    # Occupancy % (rooms sold / available * 100)
}

# ────── COLUMNS FROM EXCEL MACROS (envoie_dans_jour) ──────
# These columns are populated by the Excel macro, NOT user input.
# They should be skipped during import or treated specially.
JOUR_MACRO_COLS = [
    72,  # Col BS: Argent recu (from Recap macro — cash received)
    73,  # Col BT: Remb Serveurs (from Recap macro — server reimbursement)
    74,  # Col BU: Remb Gratuite (from Recap macro — complimentary reimbursement)
    75,  # Col BV: (unnamed, from Recap macro)
    76,  # Col BW: Due back reception (from Recap macro)
    77,  # Col BX: (unnamed, from Recap macro)
    78,  # Col BY: Surplus/Def (from Recap macro — cash surplus/deficit)
]

# ────── SPECIAL/CALCULATED COLUMNS ──────
# These columns have special formulas or business rules
JOUR_SPECIAL_COLS = {
    3: 'jour_new_balance',      # Col D: New Balance (from Daily Revenue parser)
    1: 'jour_opening_balance',  # Col B: Bal. ouv. (opening balance)
    2: 'jour_cash_difference',  # Col C: Diff. Caisse (calculated difference)
}


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def nas_jour_to_excel_dict(nas):
    """
    Convert a NightAuditSession to a dictionary of {col_index: value} for export to Excel.

    This function reads all jour_* fields from a NAS instance and produces a dict
    suitable for RJFiller.fill_jour_day(row_index, jour_values).

    Args:
        nas (NightAuditSession): A NightAuditSession instance with jour_* fields populated.

    Returns:
        dict: {column_index (int): value} where column_index is 0-indexed.
              Only includes columns with non-None/non-zero values.

    Example:
        session = NightAuditSession.query.filter_by(audit_date='2026-02-04').first()
        jour_dict = nas_jour_to_excel_dict(session)
        # Result:
        # {
        #     4: 1500.25,      # jour_cafe_nourriture
        #     9: 1981.40,      # jour_piazza_nourriture
        #     36: 50936.60,    # jour_room_revenue
        #     49: 5457.94,     # jour_tvq
        #     ...
        # }
    """
    jour_dict = {}

    for nas_field, col_idx in JOUR_NAS_TO_COL.items():
        value = getattr(nas, nas_field, None)

        # Only include non-None values
        if value is not None:
            # Handle integers (for room counts)
            if isinstance(value, int):
                jour_dict[col_idx] = value
            else:
                # Round floats to 2 decimals for consistency
                try:
                    jour_dict[col_idx] = round(float(value), 2)
                except (ValueError, TypeError):
                    # Skip values that can't be converted to float
                    pass

    return jour_dict


def excel_jour_to_nas_dict(jour_row_data):
    """
    Convert Excel JOUR row data to a dictionary of NAS field names and values.

    This function takes a dict of {col_index: value} from RJReader.read_jour_day()
    and maps it back to NAS field names for database insertion.

    Args:
        jour_row_data (dict): {column_index (int): value} from Excel JOUR sheet.
                              Column indices are 0-indexed.

    Returns:
        dict: {nas_field_name: value} ready for NightAuditSession.

    Example:
        reader = RJReader('path/to/RJ.xlsx')
        jour_row = reader.read_jour_day(row_index=7)
        # jour_row = {4: 1500.25, 9: 1981.40, 36: 50936.60, ...}

        nas_dict = excel_jour_to_nas_dict(jour_row)
        # Result:
        # {
        #     'jour_cafe_nourriture': 1500.25,
        #     'jour_piazza_nourriture': 1981.40,
        #     'jour_room_revenue': 50936.60,
        #     ...
        # }
    """
    nas_dict = {}

    for col_idx, value in jour_row_data.items():
        # Skip macro columns and special columns
        if col_idx in JOUR_MACRO_COLS or col_idx in JOUR_SPECIAL_COLS:
            continue

        # Look up the NAS field name
        nas_field = JOUR_COL_TO_NAS.get(col_idx)
        if nas_field and value is not None:
            nas_dict[nas_field] = value

    return nas_dict


def get_jour_column_info(col_idx_or_field):
    """
    Get information about a JOUR column by index or NAS field name.

    Args:
        col_idx_or_field (int or str): Either column index (int) or NAS field name (str).

    Returns:
        dict: {'column_index': int, 'nas_field': str, 'is_macro': bool, 'is_special': bool}
              or None if not found.

    Example:
        info = get_jour_column_info(36)  # Column AK
        # {'column_index': 36, 'nas_field': 'jour_room_revenue', 'is_macro': False, 'is_special': False}

        info = get_jour_column_info('jour_room_revenue')
        # {'column_index': 36, 'nas_field': 'jour_room_revenue', 'is_macro': False, 'is_special': False}
    """
    if isinstance(col_idx_or_field, int):
        # Column index lookup
        col_idx = col_idx_or_field
        nas_field = JOUR_COL_TO_NAS.get(col_idx)
    elif isinstance(col_idx_or_field, str):
        # NAS field name lookup
        nas_field = col_idx_or_field
        col_idx = JOUR_NAS_TO_COL.get(nas_field)
    else:
        return None

    if col_idx is None or nas_field is None:
        return None

    return {
        'column_index': col_idx,
        'nas_field': nas_field,
        'is_macro': col_idx in JOUR_MACRO_COLS,
        'is_special': col_idx in JOUR_SPECIAL_COLS,
    }


def list_jour_columns_by_category():
    """
    Return a dictionary of JOUR columns grouped by category/department.

    Returns:
        dict: {category: [{col_idx: int, nas_field: str, description: str}, ...]}

    Useful for UI generation or documentation.
    """
    return {
        'cafe': [
            {'col_idx': 4, 'nas_field': 'jour_cafe_nourriture', 'description': 'Nourriture'},
            {'col_idx': 5, 'nas_field': 'jour_cafe_boisson', 'description': 'Boisson'},
            {'col_idx': 6, 'nas_field': 'jour_cafe_bieres', 'description': 'Bières'},
            {'col_idx': 7, 'nas_field': 'jour_cafe_mineraux', 'description': 'Minéraux'},
            {'col_idx': 8, 'nas_field': 'jour_cafe_vins', 'description': 'Vins'},
        ],
        'piazza': [
            {'col_idx': 9, 'nas_field': 'jour_piazza_nourriture', 'description': 'Nourriture'},
            {'col_idx': 10, 'nas_field': 'jour_piazza_boisson', 'description': 'Boisson'},
            {'col_idx': 11, 'nas_field': 'jour_piazza_bieres', 'description': 'Bières'},
            {'col_idx': 12, 'nas_field': 'jour_piazza_mineraux', 'description': 'Minéraux'},
            {'col_idx': 13, 'nas_field': 'jour_piazza_vins', 'description': 'Vins'},
        ],
        'spesa': [
            {'col_idx': 14, 'nas_field': 'jour_spesa_nourriture', 'description': 'Nourriture'},
            {'col_idx': 15, 'nas_field': 'jour_spesa_boisson', 'description': 'Boisson'},
            {'col_idx': 16, 'nas_field': 'jour_spesa_bieres', 'description': 'Bières'},
            {'col_idx': 17, 'nas_field': 'jour_spesa_mineraux', 'description': 'Minéraux'},
            {'col_idx': 18, 'nas_field': 'jour_spesa_vins', 'description': 'Vins'},
        ],
        'chambres_svc': [
            {'col_idx': 19, 'nas_field': 'jour_chambres_svc_nourriture', 'description': 'Nourriture'},
            {'col_idx': 20, 'nas_field': 'jour_chambres_svc_boisson', 'description': 'Boisson'},
            {'col_idx': 21, 'nas_field': 'jour_chambres_svc_bieres', 'description': 'Bières'},
            {'col_idx': 22, 'nas_field': 'jour_chambres_svc_mineraux', 'description': 'Minéraux'},
            {'col_idx': 23, 'nas_field': 'jour_chambres_svc_vins', 'description': 'Vins'},
        ],
        'banquet': [
            {'col_idx': 24, 'nas_field': 'jour_banquet_nourriture', 'description': 'Nourriture'},
            {'col_idx': 25, 'nas_field': 'jour_banquet_boisson', 'description': 'Boisson'},
            {'col_idx': 26, 'nas_field': 'jour_banquet_bieres', 'description': 'Bières'},
            {'col_idx': 27, 'nas_field': 'jour_banquet_mineraux', 'description': 'Minéraux'},
            {'col_idx': 28, 'nas_field': 'jour_banquet_vins', 'description': 'Vins'},
        ],
        'other_fb': [
            {'col_idx': 29, 'nas_field': 'jour_pourboires', 'description': 'Pourboires'},
            {'col_idx': 32, 'nas_field': 'jour_location_salle', 'description': 'Location Salle'},
            {'col_idx': 35, 'nas_field': 'jour_tabagie', 'description': 'Tabagie'},
        ],
        'rooms_and_tel': [
            {'col_idx': 36, 'nas_field': 'jour_room_revenue', 'description': 'Chambres'},
            {'col_idx': 37, 'nas_field': 'jour_tel_local', 'description': 'Téléphone Local'},
            {'col_idx': 38, 'nas_field': 'jour_tel_interurbain', 'description': 'Téléphone Interurbain'},
            {'col_idx': 39, 'nas_field': 'jour_tel_publics', 'description': 'Téléphones Publics'},
        ],
        'autres_revenus': [
            {'col_idx': 40, 'nas_field': 'jour_nettoyeur', 'description': 'Nettoyeur'},
            {'col_idx': 41, 'nas_field': 'jour_machine_distrib', 'description': 'Machine Distributrice'},
            {'col_idx': 44, 'nas_field': 'jour_autres_gl', 'description': 'Autres G/L'},
            {'col_idx': 45, 'nas_field': 'jour_sonifi', 'description': 'Sonifi'},
            {'col_idx': 46, 'nas_field': 'jour_lit_pliant', 'description': 'Lit pliant'},
            {'col_idx': 47, 'nas_field': 'jour_boutique', 'description': 'Boutique'},
            {'col_idx': 48, 'nas_field': 'jour_internet', 'description': 'Internet'},
            {'col_idx': 52, 'nas_field': 'jour_massage', 'description': 'Massage'},
        ],
        'taxes': [
            {'col_idx': 49, 'nas_field': 'jour_tvq', 'description': 'TVQ'},
            {'col_idx': 50, 'nas_field': 'jour_tps', 'description': 'TPS'},
            {'col_idx': 51, 'nas_field': 'jour_taxe_hebergement', 'description': 'Taxe hébergement'},
        ],
        'special': [
            {'col_idx': 54, 'nas_field': 'jour_gift_cards', 'description': 'Gift Cards'},
            {'col_idx': 57, 'nas_field': 'jour_club_lounge', 'description': 'Club Lounge & Forfait'},
            {'col_idx': 80, 'nas_field': 'jour_certificats', 'description': 'Certificat Cadeaux'},
            {'col_idx': 83, 'nas_field': 'jour_ar_misc', 'description': 'A/R Misc'},
            {'col_idx': 86, 'nas_field': 'jour_deposit_on_hand', 'description': 'Deposit on hand'},
        ],
        'occupancy': [
            {'col_idx': 88, 'nas_field': 'jour_rooms_simple', 'description': 'Simple'},
            {'col_idx': 89, 'nas_field': 'jour_rooms_double', 'description': 'Double'},
            {'col_idx': 90, 'nas_field': 'jour_rooms_suite', 'description': 'Suite'},
            {'col_idx': 91, 'nas_field': 'jour_rooms_comp', 'description': 'Comp'},
            {'col_idx': 92, 'nas_field': 'jour_nb_clients', 'description': '# Clients'},
            {'col_idx': 93, 'nas_field': 'jour_rooms_hors_usage', 'description': 'Hors Usage'},
        ],
    }
