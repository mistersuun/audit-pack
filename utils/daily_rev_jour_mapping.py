"""
Comprehensive mapping configuration for Daily Revenue report to Jour sheet columns.

This module defines exactly which Daily Revenue report values go into which
RJ jour sheet columns, based on user-specified business rules.

Column References:
- Column letters are mapped to 0-indexed column numbers
- Row 8 (index 7) is used for Day 4 (Feb 4, 2026) in the jour sheet
- All monetary values are in CAD

Data Sources:
- PAGE 1: Revenue Departments (Chambres, Telephones, etc.)
- PAGE 2: Autres Revenus + Non-Revenue start (taxes, special services)
- PAGE 3: Non-Revenue continued (TVQ Internet)
- PAGE 4: Non-Revenue taxes (TPS/TVQ for telephones)
- PAGE 5: More taxes (TPS/TVQ for other services and internet)
- PAGE 6: Settlements section (Gift cards, Bons d'achat)
- PAGE 7: Balance section (New Balance, Front Office Transfers)
- Sales Journal: Restaurant/bar revenue (Piazza sales)
"""

# =============================================================================
# COLUMN LETTER TO INDEX MAPPING
# =============================================================================
COLUMN_MAP = {
    'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7,
    'I': 8, 'J': 9, 'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15,
    'Q': 16, 'R': 17, 'S': 18, 'T': 19, 'U': 20, 'V': 21, 'W': 22, 'X': 23,
    'Y': 24, 'Z': 25,
    'AA': 26, 'AB': 27, 'AC': 28, 'AD': 29, 'AE': 30, 'AF': 31, 'AG': 32,
    'AH': 33, 'AI': 34, 'AJ': 35, 'AK': 36, 'AL': 37, 'AM': 38, 'AN': 39,
    'AO': 40, 'AP': 41, 'AQ': 42, 'AR': 43, 'AS': 44, 'AT': 45, 'AU': 46,
    'AV': 47, 'AW': 48, 'AX': 49, 'AY': 50, 'AZ': 51,
    'BA': 52, 'BB': 53, 'BC': 54, 'BD': 55, 'BE': 56, 'BF': 57, 'BG': 58,
    'BH': 59, 'BI': 60, 'BJ': 61, 'BK': 62, 'BL': 63, 'BM': 64, 'BN': 65,
    'BO': 66, 'BP': 67, 'BQ': 68, 'BR': 69, 'BS': 70, 'BT': 71, 'BU': 72,
    'BV': 73, 'BW': 74, 'BX': 75, 'BY': 76, 'BZ': 77, 'CA': 78,
    'CB': 79, 'CC': 80, 'CD': 81, 'CE': 82, 'CF': 83,
    'CG': 84, 'CH': 85, 'CI': 86, 'CJ': 87, 'CK': 88, 'CL': 89,
    'CM': 90, 'CN': 91, 'CO': 92, 'CP': 93, 'CQ': 94, 'CR': 95,
    'CS': 96, 'CT': 97, 'CU': 98, 'CV': 99, 'CW': 100,
    'CX': 101, 'CY': 102, 'CZ': 103,
    'DA': 104, 'DB': 105, 'DC': 106, 'DD': 107, 'DE': 108, 'DF': 109,
    'DG': 110, 'DH': 111, 'DI': 112, 'DJ': 113, 'DK': 114, 'DL': 115,
    'DM': 116,
}


def col_letter_to_index(letter):
    """Convert column letter (e.g., 'AK') to 0-indexed column number."""
    return COLUMN_MAP.get(letter.upper(), None)


def col_index_to_letter(index):
    """Convert 0-indexed column number to column letter (e.g., 36 -> 'AK')."""
    result = ''
    col = index + 1  # Convert to 1-indexed
    while col > 0:
        col -= 1
        result = chr(65 + (col % 26)) + result
        col //= 26
    return result


# =============================================================================
# MAIN MAPPING: DAILY REVENUE TO JOUR COLUMNS
# =============================================================================
DAILY_REV_TO_JOUR = {
    # =========================================================================
    # PAGE 1: REVENUE DEPARTMENTS
    # =========================================================================
    'AK': {
        'column_index': 36,
        'label_en': 'Chambres (minus Club Lounge)',
        'label_fr': 'Chambres (- Club Lounge)',
        'source_page': 'PAGE 1',
        'source_line': 'Chambres Total',
        'operation': 'subtract',
        'base_field': 'revenue.chambres.total',
        'subtract_field': 'non_revenue.club_lounge.total',
        'expected_value': 50936.60,  # 50936.60 - 0 = 50936.60
        'description': 'Room revenue minus any Club Lounge charges',
        'sign_handling': 'keep_sign'
    },
    'AL': {
        'column_index': 37,
        'label_en': 'Telephone Local',
        'label_fr': 'Téléphone Local',
        'source_page': 'PAGE 1',
        'source_line': 'Telephone Local',
        'operation': 'direct',
        'base_field': 'revenue.telephones.local',
        'expected_value': 0.00,
        'description': 'Local telephone revenue',
        'sign_handling': 'keep_sign'
    },
    'AM': {
        'column_index': 38,
        'label_en': 'Telephone Interurbain',
        'label_fr': 'Téléphone Interurbain',
        'source_page': 'PAGE 1',
        'source_line': 'Interurbain',
        'operation': 'direct',
        'base_field': 'revenue.telephones.interurbain',
        'expected_value': 0.00,
        'description': 'Long-distance telephone revenue',
        'sign_handling': 'keep_sign'
    },
    'AN': {
        'column_index': 39,
        'label_en': 'Telephones Publics',
        'label_fr': 'Téléphones Publics',
        'source_page': 'PAGE 1',
        'source_line': 'Telephones Publics',
        'operation': 'direct',
        'base_field': 'revenue.telephones.publics',
        'expected_value': 0.00,
        'description': 'Public telephone revenue',
        'sign_handling': 'keep_sign'
    },

    # =========================================================================
    # PAGE 2: AUTRES REVENUS + NON-REVENUE START
    # =========================================================================
    'AO': {
        'column_index': 40,
        'label_en': 'Nettoyeur - Dry Cleaning',
        'label_fr': 'Nettoyeur - Dry Cleaning',
        'source_page': 'PAGE 2',
        'source_line': 'Nettoyeur-Dry Cleaning',
        'operation': 'direct',
        'base_field': 'revenue.autres_revenus.nettoyeur',
        'expected_value': 0.00,
        'description': 'Dry cleaning service revenue',
        'sign_handling': 'keep_sign'
    },
    'AP': {
        'column_index': 41,
        'label_en': 'Machine Distributrice',
        'label_fr': 'MACHINE DISTRIBUTRICE',
        'source_page': 'PAGE 2',
        'source_line': 'MACHINE DISTRIBUTRICE',
        'operation': 'direct',
        'base_field': 'revenue.autres_revenus.machine_distributrice',
        'expected_value': 0.00,
        'description': 'Vending machine revenue',
        'sign_handling': 'keep_sign'
    },
    'AS': {
        'column_index': 44,
        'label_en': 'Autres Grand Livre Total',
        'label_fr': 'Autres Grand Livre Total',
        'source_page': 'PAGE 2',
        'source_line': 'Autres Grand Livre Total',
        'operation': 'direct',
        'base_field': 'revenue.comptabilite.autres_grand_livre',
        'expected_value': -92589.85,
        'description': 'Other general ledger entries (keep sign: negative if negative)',
        'sign_handling': 'keep_sign',
        'note': 'Keep sign: negative if negative, positive if positive'
    },
    'AT': {
        'column_index': 45,
        'label_en': 'Sonifi',
        'label_fr': 'Sonifi',
        'source_page': 'PAGE 2',
        'source_line': 'Sonifi',
        'operation': 'direct',
        'base_field': 'revenue.autres_revenus.sonifi',
        'expected_value': 0.00,
        'description': 'Sonifi in-room entertainment revenue',
        'sign_handling': 'keep_sign'
    },
    'AU': {
        'column_index': 46,
        'label_en': 'Lit Pliant',
        'label_fr': 'Lit Pliant',
        'source_page': 'PAGE 2',
        'source_line': 'Lit Pliant',
        'operation': 'direct',
        'base_field': 'revenue.autres_revenus.lit_pliant',
        'expected_value': 0.00,
        'description': 'Rollaway bed rental fee',
        'sign_handling': 'keep_sign'
    },
    'AV': {
        'column_index': 47,
        'label_en': 'Location De Boutique',
        'label_fr': 'Location De Boutique',
        'source_page': 'PAGE 2',
        'source_line': 'Location De Boutique',
        'operation': 'direct',
        'base_field': 'revenue.autres_revenus.location_boutique',
        'expected_value': 0.00,
        'description': 'Boutique rental income',
        'sign_handling': 'keep_sign'
    },
    'AW': {
        'column_index': 48,
        'label_en': 'Internet',
        'label_fr': 'Internet',
        'source_page': 'PAGE 2',
        'source_line': 'Internet',
        'operation': 'direct',
        'base_field': 'revenue.internet.total',
        'expected_value': -0.46,
        'description': 'Internet service revenue',
        'sign_handling': 'keep_sign'
    },
    'BA': {
        'column_index': 52,
        'label_en': 'Massage',
        'label_fr': 'Massage',
        'source_page': 'PAGE 2',
        'source_line': 'Massage',
        'operation': 'direct',
        'base_field': 'revenue.autres_revenus.massage',
        'expected_value': 383.30,
        'description': 'Massage and spa service revenue',
        'sign_handling': 'keep_sign'
    },
    'AG': {
        'column_index': 32,
        'label_en': 'Location Salle Forfait',
        'label_fr': 'Location Salle Forfait',
        'source_page': 'PAGE 2',
        'source_line': 'Location Salle Forfa',
        'operation': 'direct',
        'base_field': 'revenue.autres_revenus.location_salle_forfait',
        'expected_value': 1620.00,
        'description': 'Banquet room rental (forfait)',
        'sign_handling': 'keep_sign'
    },

    # =========================================================================
    # PAGE 3: NON-REVENUE CONTINUED (TAXES)
    # =========================================================================
    'AZ': {
        'column_index': 51,
        'label_en': 'Taxe Hebergement',
        'label_fr': 'Taxe Hebergement',
        'source_page': 'PAGE 2',
        'source_line': 'Taxe Hebergement',
        'operation': 'direct',
        'base_field': 'non_revenue.chambres_tax.taxe_hebergement',
        'expected_value': 1783.53,
        'description': 'Accommodation tax',
        'sign_handling': 'keep_sign'
    },
    'AY': {
        'column_index': 50,
        'label_en': 'TPS Accumulator',
        'label_fr': 'TPS Accumulator',
        'source_page': 'PAGES 2, 3, 4, 5 + Sales Journal',
        'source_line': 'Multiple TPS lines (accumulates DR non-rev + restaurant + SJ POS)',
        'operation': 'accumulate',
        'accumulator_fields': [
            # DR Non-Revenue taxes
            'non_revenue.chambres_tax.tps',
            'non_revenue.telephones_tax.tps_local',
            'non_revenue.telephones_tax.tps_interurbain',
            'non_revenue.autres_tax.tps_autres',
            'non_revenue.internet_nonrev.tps',
            # DR Restaurant/F&B taxes
            'non_revenue.restaurant_piazza.tps',
            'non_revenue.banquet.tps',
            'non_revenue.la_spesa.tps',
            'non_revenue.services_chambres.tps',
            # Sales Journal POS taxes
            'sales_journal.taxes.tps',
        ],
        'expected_value': 3788.92,  # Sum of all TPS sources (DR non-rev + restaurants + SJ)
        'description': 'Accumulator for all TPS (GST) taxes from DR and Sales Journal',
        'sign_handling': 'keep_sign'
    },
    'AX': {
        'column_index': 49,
        'label_en': 'TVQ Accumulator',
        'label_fr': 'TVQ Accumulator',
        'source_page': 'PAGES 3, 4, 5 + Sales Journal',
        'source_line': 'Multiple TVQ lines (accumulates DR non-rev + restaurant + SJ POS)',
        'operation': 'accumulate',
        'accumulator_fields': [
            # DR Non-Revenue taxes
            'non_revenue.chambres_tax.tvq',
            'non_revenue.telephones_tax.tvq_local',
            'non_revenue.telephones_tax.tvq_interurbain',
            'non_revenue.autres_tax.tvq_autres',
            'non_revenue.internet_nonrev.tvq',
            # DR Restaurant/F&B taxes
            'non_revenue.restaurant_piazza.tvq',
            'non_revenue.banquet.tvq',
            'non_revenue.la_spesa.tvq',
            'non_revenue.services_chambres.tvq',
            # Sales Journal POS taxes
            'sales_journal.taxes.tvq',
        ],
        'expected_value': 7558.53,  # Sum of all TVQ sources (DR non-rev + restaurants + SJ)
        'description': 'Accumulator for all TVQ (QST) taxes from DR and Sales Journal',
        'sign_handling': 'keep_sign'
    },

    # =========================================================================
    # PAGE 6: SETTLEMENTS SECTION (GIFT CARDS & BONS)
    # =========================================================================
    'BC': {
        'column_index': 54,
        'label_en': 'Gift Card & Bon d\'achat Accumulator',
        'label_fr': 'Gift Card & Bon d\'achat Accumulator',
        'source_page': 'PAGES 2, 6',
        'source_line': 'Multiple lines (accumulates)',
        'operation': 'accumulate',
        'accumulator_fields': [
            'revenue.givex.total',
            'settlements.bon_dachat',
            'settlements.gift_card',
            'settlements.bon_dachat_remanco'
        ],
        'expected_value': 400.00,  # Will sum all gift card sources
        'description': 'Accumulator: GiveX + Bon d\'achat + Gift Card + Bon d\'achat Remanco',
        'sign_handling': 'keep_sign'
    },
    'CC': {
        'column_index': 80,
        'label_en': 'Certificat Cadeaux',
        'label_fr': 'Certificat Cadeaux',
        'source_page': 'PAGE 6',
        'source_line': 'Certificat Cadeaux',
        'operation': 'direct',
        'base_field': 'settlements.certificat_cadeaux',
        'expected_value': 0.00,
        'description': 'Gift certificate settlements',
        'sign_handling': 'keep_sign'
    },

    # =========================================================================
    # PAGE 7: BALANCE & TRANSFERS SECTION
    # =========================================================================
    'D': {
        'column_index': 3,
        'label_en': 'New Balance (negative)',
        'label_fr': 'Nouveau Solde (négatif)',
        'source_page': 'PAGE 7',
        'source_line': 'New Balance - Deposit on Hand',
        'operation': 'formula',
        'formula': '-(balance.new_balance) - deposits.deposit_on_hand',
        'base_field': 'balance.new_balance',
        'expected_value': 3871908.19,
        'description': 'New Balance as negative, then subtract Deposit on Hand from Advance Deposit Balance Sheet',
        'sign_handling': 'negate_result',
        'note': 'Put in NEGATIVE, then subtract Deposit on Hand from Advance Deposit Balance Sheet'
    },
    'CF': {
        'column_index': 83,
        'label_en': 'A/R Misc & Front Office Transfers',
        'label_fr': 'A/R Misc & Front Office Transfers',
        'source_page': 'PAGES 2, 7',
        'source_line': 'A/R Misc Total and Front Office Transfers',
        'operation': 'combined',
        'formula': '-(total_transfers - payments)',
        'accumulator_fields': [
            'non_revenue.ar_activity.total',
            'balance.front_office_transfers'
        ],
        'expected_value': 0.00,
        'description': 'A/R Misc (always negative) + Front Office Transfers (Total Transfers - Payments)',
        'sign_handling': 'always_negative',
        'note': 'ALWAYS negative for both sources'
    },

    # =========================================================================
    # SPECIAL CALCULATED COLUMNS
    # =========================================================================
    'BF': {
        'column_index': 57,
        'label_en': 'Club Lounge & Forfait Calculation',
        'label_fr': 'Club Lounge & Forfait Calculation',
        'source_page': 'DERIVED',
        'source_line': 'Calculated from diff_forfait',
        'operation': 'formula',
        'formula': '-forfait + club_lounge_value',
        'base_field': 'derived.diff_forfait',
        'expected_value': 0.00,
        'description': 'Column BF = -Forfait + Club Lounge value (from diff_forfait)',
        'sign_handling': 'keep_sign'
    },

    # =========================================================================
    # SALES JOURNAL: RESTAURANT/BAR DEPARTMENTS
    # =========================================================================

    # --- PAUSE SPESA / CAFE LINK (E-I, cols 4-8) ---
    'E': {
        'column_index': 4,
        'label_en': 'Cafe Link Nourriture',
        'label_fr': 'Nou_Link',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Cafe Link - Food',
        'operation': 'direct',
        'base_field': 'sales_journal.cafe_link.nourriture',
        'description': 'Cafe Link food sales',
        'sign_handling': 'keep_sign'
    },
    'F': {
        'column_index': 5,
        'label_en': 'Cafe Link Boisson',
        'label_fr': 'Boi_Link',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Cafe Link - Alcohol',
        'operation': 'direct',
        'base_field': 'sales_journal.cafe_link.boisson',
        'description': 'Cafe Link alcohol sales',
        'sign_handling': 'keep_sign'
    },
    'G': {
        'column_index': 6,
        'label_en': 'Cafe Link Bières',
        'label_fr': 'Bie_Link',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Cafe Link - Beer',
        'operation': 'direct',
        'base_field': 'sales_journal.cafe_link.bieres',
        'description': 'Cafe Link beer sales',
        'sign_handling': 'keep_sign'
    },
    'H': {
        'column_index': 7,
        'label_en': 'Cafe Link Minéraux',
        'label_fr': 'Min_Link',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Cafe Link - Non-Alcoholic',
        'operation': 'direct',
        'base_field': 'sales_journal.cafe_link.mineraux',
        'description': 'Cafe Link non-alcoholic sales',
        'sign_handling': 'keep_sign'
    },
    'I': {
        'column_index': 8,
        'label_en': 'Cafe Link Vins',
        'label_fr': 'Vin_Link',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Cafe Link - Wine',
        'operation': 'direct',
        'base_field': 'sales_journal.cafe_link.vins',
        'description': 'Cafe Link wine sales',
        'sign_handling': 'keep_sign'
    },

    # --- PIAZZA/CUPOLA (J-N, cols 9-13) ---
    'J': {
        'column_index': 9,
        'label_en': 'Piazza Nourriture',
        'label_fr': 'Nou_piazza',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Piazza Restaurant - Food',
        'operation': 'direct',
        'base_field': 'sales_journal.piazza.nourriture',
        'adjustments': ['minus_hp_deductions', 'minus_adjustments'],
        'expected_value': 1981.40,
        'description': 'Food/Nourriture sales minus HP deductions and adjustments',
        'sign_handling': 'keep_sign'
    },
    'K': {
        'column_index': 10,
        'label_en': 'Piazza Alcool (Boisson)',
        'label_fr': 'Boi_piazza',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Piazza Restaurant - Alcohol/Beverages',
        'operation': 'direct',
        'base_field': 'sales_journal.piazza.boisson',
        'expected_value': 75.00,
        'description': 'Alcohol/Beverage sales from Piazza restaurant',
        'sign_handling': 'keep_sign'
    },
    'L': {
        'column_index': 11,
        'label_en': 'Piazza Bières',
        'label_fr': 'Bie_piazza',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Piazza Restaurant - Beer',
        'operation': 'direct',
        'base_field': 'sales_journal.piazza.bieres',
        'expected_value': 198.00,
        'description': 'Beer sales from Piazza restaurant',
        'sign_handling': 'keep_sign'
    },
    'M': {
        'column_index': 12,
        'label_en': 'Piazza Non Alcool Bar (Minéraux)',
        'label_fr': 'Min_piazza',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Piazza Restaurant - Non-Alcoholic',
        'operation': 'direct',
        'base_field': 'sales_journal.piazza.mineraux',
        'expected_value': 19.00,
        'description': 'Non-alcoholic beverages from Piazza restaurant',
        'sign_handling': 'keep_sign'
    },
    'N': {
        'column_index': 13,
        'label_en': 'Piazza Vins',
        'label_fr': 'Vin_piazza',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Piazza Restaurant - Wine',
        'operation': 'direct',
        'base_field': 'sales_journal.piazza.vins',
        'expected_value': 219.00,
        'description': 'Wine sales from Piazza restaurant',
        'sign_handling': 'keep_sign'
    },

    # --- MARCHÉ LA SPESA (O-S, cols 14-18) ---
    'O': {
        'column_index': 14,
        'label_en': 'Marché La Spesa Nourriture',
        'label_fr': 'Nou_mar',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Spesa - Food',
        'operation': 'direct',
        'base_field': 'sales_journal.spesa.nourriture',
        'description': 'La Spesa food sales',
        'sign_handling': 'keep_sign'
    },
    'P': {
        'column_index': 15,
        'label_en': 'Marché La Spesa Boisson',
        'label_fr': 'Boi_mar',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Spesa - Alcohol',
        'operation': 'direct',
        'base_field': 'sales_journal.spesa.boisson',
        'description': 'La Spesa alcohol sales',
        'sign_handling': 'keep_sign'
    },
    'Q': {
        'column_index': 16,
        'label_en': 'Marché La Spesa Bières',
        'label_fr': 'Bie_mar',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Spesa - Beer',
        'operation': 'direct',
        'base_field': 'sales_journal.spesa.bieres',
        'description': 'La Spesa beer sales',
        'sign_handling': 'keep_sign'
    },
    'R': {
        'column_index': 17,
        'label_en': 'Marché La Spesa Minéraux',
        'label_fr': 'Min_mar',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Spesa - Non-Alcoholic',
        'operation': 'direct',
        'base_field': 'sales_journal.spesa.mineraux',
        'description': 'La Spesa non-alcoholic sales',
        'sign_handling': 'keep_sign'
    },
    'S': {
        'column_index': 18,
        'label_en': 'Marché La Spesa Vins',
        'label_fr': 'Vin_mar',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Spesa - Wine',
        'operation': 'direct',
        'base_field': 'sales_journal.spesa.vins',
        'description': 'La Spesa wine sales',
        'sign_handling': 'keep_sign'
    },

    # --- SERVICE AUX CHAMBRES (T-X, cols 19-23) ---
    'T': {
        'column_index': 19,
        'label_en': 'Service Chambres Nourriture',
        'label_fr': 'Nou_schbr',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Chambres - Food',
        'operation': 'direct',
        'base_field': 'sales_journal.chambres.nourriture',
        'description': 'Room service food sales',
        'sign_handling': 'keep_sign'
    },
    'U': {
        'column_index': 20,
        'label_en': 'Service Chambres Boisson',
        'label_fr': 'Boi_schbr',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Chambres - Alcohol',
        'operation': 'direct',
        'base_field': 'sales_journal.chambres.boisson',
        'description': 'Room service alcohol sales',
        'sign_handling': 'keep_sign'
    },
    'V': {
        'column_index': 21,
        'label_en': 'Service Chambres Bières',
        'label_fr': 'Bie_schbr',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Chambres - Beer',
        'operation': 'direct',
        'base_field': 'sales_journal.chambres.bieres',
        'description': 'Room service beer sales',
        'sign_handling': 'keep_sign'
    },
    'W': {
        'column_index': 22,
        'label_en': 'Service Chambres Minéraux',
        'label_fr': 'Min_schbr',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Chambres - Non-Alcoholic',
        'operation': 'direct',
        'base_field': 'sales_journal.chambres.mineraux',
        'description': 'Room service non-alcoholic sales',
        'sign_handling': 'keep_sign'
    },
    'X': {
        'column_index': 23,
        'label_en': 'Service Chambres Vins',
        'label_fr': 'Vin_schbr',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Chambres - Wine',
        'operation': 'direct',
        'base_field': 'sales_journal.chambres.vins',
        'description': 'Room service wine sales',
        'sign_handling': 'keep_sign'
    },

    # --- BANQUET (Y-AC, cols 24-28) ---
    'Y': {
        'column_index': 24,
        'label_en': 'Banquet Nourriture',
        'label_fr': 'Nou_bqt',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Banquet - Food',
        'operation': 'direct',
        'base_field': 'sales_journal.banquet.nourriture',
        'description': 'Banquet food sales',
        'sign_handling': 'keep_sign'
    },
    'Z': {
        'column_index': 25,
        'label_en': 'Banquet Boisson',
        'label_fr': 'Boi_bqt',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Banquet - Alcohol',
        'operation': 'direct',
        'base_field': 'sales_journal.banquet.boisson',
        'description': 'Banquet alcohol sales',
        'sign_handling': 'keep_sign'
    },
    'AA': {
        'column_index': 26,
        'label_en': 'Banquet Bières',
        'label_fr': 'Biere Banquet',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Banquet - Beer',
        'operation': 'direct',
        'base_field': 'sales_journal.banquet.bieres',
        'description': 'Banquet beer sales',
        'sign_handling': 'keep_sign'
    },
    'AB': {
        'column_index': 27,
        'label_en': 'Banquet Minéraux',
        'label_fr': 'Min_bqt',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Banquet - Non-Alcoholic',
        'operation': 'direct',
        'base_field': 'sales_journal.banquet.mineraux',
        'description': 'Banquet non-alcoholic sales',
        'sign_handling': 'keep_sign'
    },
    'AC': {
        'column_index': 28,
        'label_en': 'Banquet Vins',
        'label_fr': 'Vin_bqt',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Banquet - Wine',
        'operation': 'direct',
        'base_field': 'sales_journal.banquet.vins',
        'description': 'Banquet wine sales',
        'sign_handling': 'keep_sign'
    },

    # =========================================================================
    # SALES JOURNAL: OTHER ITEMS
    # =========================================================================
    'AD': {
        'column_index': 29,
        'label_en': 'Pourboires',
        'label_fr': 'Pourboires',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Pourboires (gratuities)',
        'operation': 'direct',
        'base_field': 'sales_journal.adjustments.pourboire_charge',
        'description': 'Gratuity charges from Sales Journal',
        'sign_handling': 'keep_sign'
    },
    'AJ': {
        'column_index': 35,
        'label_en': 'Tabagie',
        'label_fr': 'Tabagie',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Tabagie / Tobacco',
        'operation': 'direct',
        'base_field': 'sales_journal.spesa.tabagie',
        'description': 'Tobacco/tabagie sales (Spesa dept)',
        'sign_handling': 'keep_sign'
    },

    # =========================================================================
    # CREDIT CARD COLUMNS (from Transelect/calcul_carte)
    # =========================================================================
    'BI': {
        'column_index': 60,
        'label_en': 'Amex ELAVON',
        'label_fr': 'Amex ELAVON',
        'source_page': 'TRANSELECT',
        'source_line': 'Amex total from Transelect row 14',
        'operation': 'direct',
        'base_field': 'transelect.amex_total',
        'description': 'Amex ELAVON card total from Transelect',
        'sign_handling': 'keep_sign'
    },
    'BJ': {
        'column_index': 61,
        'label_en': 'Discover',
        'label_fr': 'Discover',
        'source_page': 'TRANSELECT',
        'source_line': 'Discover total from Transelect',
        'operation': 'direct',
        'base_field': 'transelect.discover_total',
        'description': 'Discover card total from Transelect',
        'sign_handling': 'keep_sign'
    },
    'BK': {
        'column_index': 62,
        'label_en': 'Master Charge',
        'label_fr': 'Master Charge',
        'source_page': 'TRANSELECT',
        'source_line': 'MasterCard total from Transelect',
        'operation': 'direct',
        'base_field': 'transelect.master_total',
        'description': 'MasterCard total from Transelect',
        'sign_handling': 'keep_sign'
    },
    'BL': {
        'column_index': 63,
        'label_en': 'Visa',
        'label_fr': 'Visa',
        'source_page': 'TRANSELECT',
        'source_line': 'Visa total from Transelect',
        'operation': 'direct',
        'base_field': 'transelect.visa_total',
        'description': 'Visa card total from Transelect',
        'sign_handling': 'keep_sign'
    },
    'BM': {
        'column_index': 64,
        'label_en': 'Carte Debit',
        'label_fr': 'Carte Debit',
        'source_page': 'TRANSELECT',
        'source_line': 'Debit total from Transelect',
        'operation': 'direct',
        'base_field': 'transelect.debit_total',
        'description': 'Debit card total from Transelect',
        'sign_handling': 'keep_sign'
    },
    'BN': {
        'column_index': 65,
        'label_en': 'Amex GLOBAL',
        'label_fr': 'Amex GLOBAL',
        'source_page': 'TRANSELECT',
        'source_line': 'Amex Global total from Transelect',
        'operation': 'direct',
        'base_field': 'transelect.amex_global_total',
        'description': 'Amex GLOBAL card total from Transelect',
        'sign_handling': 'keep_sign'
    },

    # =========================================================================
    # HP DEDUCTIONS (from HP Excel parser)
    # =========================================================================
    'BQ': {
        'column_index': 68,
        'label_en': 'H/P Administration 14',
        'label_fr': 'H/P Administration 14',
        'source_page': 'HP EXCEL',
        'source_line': 'HP administration deductions',
        'operation': 'direct',
        'base_field': 'hp.administration_total',
        'description': 'HP administration charges',
        'sign_handling': 'keep_sign'
    },
    'BR': {
        'column_index': 69,
        'label_en': 'Hotel Promotion 15',
        'label_fr': 'Hotel Promotion 15',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Hotel Promotion adjustments',
        'operation': 'direct',
        'base_field': 'sales_journal.adjustments.hotel_promotion',
        'description': 'Hotel promotion adjustments from Sales Journal',
        'sign_handling': 'keep_sign'
    },

    # =========================================================================
    # POS SUMMARY TOTALS (calculated sums of restaurant columns)
    # =========================================================================
    'DG': {
        'column_index': 110,
        'label_en': 'NOURRITURE Total',
        'label_fr': 'NOURRITURE',
        'source_page': 'CALCULATED',
        'source_line': 'Sum of all food columns',
        'operation': 'accumulate',
        'accumulator_fields': [
            'sales_journal.cafe_link.nourriture',
            'sales_journal.piazza.nourriture',
            'sales_journal.spesa.nourriture',
            'sales_journal.chambres.nourriture',
            'sales_journal.banquet.nourriture',
        ],
        'description': 'Total food (nourriture) across all F&B departments',
        'sign_handling': 'keep_sign'
    },
    'DH': {
        'column_index': 111,
        'label_en': 'ALCOOL Total',
        'label_fr': 'ALCOOL',
        'source_page': 'CALCULATED',
        'source_line': 'Sum of all alcohol columns',
        'operation': 'accumulate',
        'accumulator_fields': [
            'sales_journal.cafe_link.boisson',
            'sales_journal.piazza.boisson',
            'sales_journal.spesa.boisson',
            'sales_journal.chambres.boisson',
            'sales_journal.banquet.boisson',
        ],
        'description': 'Total alcohol (boisson) across all F&B departments',
        'sign_handling': 'keep_sign'
    },
    'DI': {
        'column_index': 112,
        'label_en': 'BIÈRES Total',
        'label_fr': 'BIÈRES',
        'source_page': 'CALCULATED',
        'source_line': 'Sum of all beer columns',
        'operation': 'accumulate',
        'accumulator_fields': [
            'sales_journal.cafe_link.bieres',
            'sales_journal.piazza.bieres',
            'sales_journal.spesa.bieres',
            'sales_journal.chambres.bieres',
            'sales_journal.banquet.bieres',
        ],
        'description': 'Total beer (bières) across all F&B departments',
        'sign_handling': 'keep_sign'
    },
    'DJ': {
        'column_index': 113,
        'label_en': 'MINÉRAUX Total',
        'label_fr': 'MINÉRAUX',
        'source_page': 'CALCULATED',
        'source_line': 'Sum of all non-alcoholic columns',
        'operation': 'accumulate',
        'accumulator_fields': [
            'sales_journal.cafe_link.mineraux',
            'sales_journal.piazza.mineraux',
            'sales_journal.spesa.mineraux',
            'sales_journal.chambres.mineraux',
            'sales_journal.banquet.mineraux',
        ],
        'description': 'Total non-alcoholic (minéraux) across all F&B departments',
        'sign_handling': 'keep_sign'
    },
    'DK': {
        'column_index': 114,
        'label_en': 'VINS Total',
        'label_fr': 'VINS',
        'source_page': 'CALCULATED',
        'source_line': 'Sum of all wine columns',
        'operation': 'accumulate',
        'accumulator_fields': [
            'sales_journal.cafe_link.vins',
            'sales_journal.piazza.vins',
            'sales_journal.spesa.vins',
            'sales_journal.chambres.vins',
            'sales_journal.banquet.vins',
        ],
        'description': 'Total wine (vins) across all F&B departments',
        'sign_handling': 'keep_sign'
    },
    'DM': {
        'column_index': 116,
        'label_en': 'TOTAL BOISSON',
        'label_fr': 'TOTAL BOISSON',
        'source_page': 'CALCULATED',
        'source_line': 'Sum of DH+DI+DJ+DK',
        'operation': 'accumulate',
        'accumulator_fields': [
            'sales_journal.cafe_link.boisson',
            'sales_journal.piazza.boisson',
            'sales_journal.spesa.boisson',
            'sales_journal.chambres.boisson',
            'sales_journal.banquet.boisson',
            'sales_journal.cafe_link.bieres',
            'sales_journal.piazza.bieres',
            'sales_journal.spesa.bieres',
            'sales_journal.chambres.bieres',
            'sales_journal.banquet.bieres',
            'sales_journal.cafe_link.mineraux',
            'sales_journal.piazza.mineraux',
            'sales_journal.spesa.mineraux',
            'sales_journal.chambres.mineraux',
            'sales_journal.banquet.mineraux',
            'sales_journal.cafe_link.vins',
            'sales_journal.piazza.vins',
            'sales_journal.spesa.vins',
            'sales_journal.chambres.vins',
            'sales_journal.banquet.vins',
        ],
        'description': 'Total beverages (alcool + bières + minéraux + vins)',
        'sign_handling': 'keep_sign'
    },
}


# =============================================================================
# ACCUMULATOR COLUMNS (special handling for columns that sum multiple sources)
# =============================================================================
ACCUMULATOR_COLUMNS = {
    'AX': {
        'label_en': 'TVQ Total',
        'label_fr': 'TVQ Total',
        'sources': [
            # DR Non-Revenue taxes
            {
                'page': 3,
                'line': 'TVQ 1019892413',
                'field': 'non_revenue.chambres_tax.tvq'
            },
            {
                'page': 4,
                'line': 'TVQ Tel Local',
                'field': 'non_revenue.telephones_tax.tvq_local',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 4,
                'line': 'TVQ Tel Interurbain',
                'field': 'non_revenue.telephones_tax.tvq_interurbain',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 5,
                'line': 'TVQ Autres',
                'field': 'non_revenue.autres_tax.tvq_autres',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 5,
                'line': 'TVQ Internet',
                'field': 'non_revenue.internet_nonrev.tvq',
                'action': 'ADD_TO_EXISTING'
            },
            # DR Restaurant/F&B taxes
            {
                'page': 3,
                'line': 'TVQ Restaurant Piazza',
                'field': 'non_revenue.restaurant_piazza.tvq',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 3,
                'line': 'TVQ Banquet',
                'field': 'non_revenue.banquet.tvq',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 3,
                'line': 'TVQ La Spesa',
                'field': 'non_revenue.la_spesa.tvq',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 3,
                'line': 'TVQ Services Chambres',
                'field': 'non_revenue.services_chambres.tvq',
                'action': 'ADD_TO_EXISTING'
            },
            # Sales Journal POS taxes
            {
                'page': 'SJ',
                'line': 'TVQ Sales Journal POS',
                'field': 'sales_journal.taxes.tvq',
                'action': 'ADD_TO_EXISTING'
            }
        ],
        'operation': 'sum_all',
        'expected_total': 7558.53
    },
    'AY': {
        'label_en': 'TPS Total',
        'label_fr': 'TPS Total',
        'sources': [
            # DR Non-Revenue taxes
            {
                'page': 2,
                'line': 'TPS 141740175',
                'field': 'non_revenue.chambres_tax.tps'
            },
            {
                'page': 4,
                'line': 'TPS Tel Local',
                'field': 'non_revenue.telephones_tax.tps_local',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 4,
                'line': 'TPS Tel Interurbain',
                'field': 'non_revenue.telephones_tax.tps_interurbain',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 5,
                'line': 'TPS Autres',
                'field': 'non_revenue.autres_tax.tps_autres',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 5,
                'line': 'TPS Internet',
                'field': 'non_revenue.internet_nonrev.tps',
                'action': 'ADD_TO_EXISTING'
            },
            # DR Restaurant/F&B taxes
            {
                'page': 3,
                'line': 'TPS Restaurant Piazza',
                'field': 'non_revenue.restaurant_piazza.tps',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 3,
                'line': 'TPS Banquet',
                'field': 'non_revenue.banquet.tps',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 3,
                'line': 'TPS La Spesa',
                'field': 'non_revenue.la_spesa.tps',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 3,
                'line': 'TPS Services Chambres',
                'field': 'non_revenue.services_chambres.tps',
                'action': 'ADD_TO_EXISTING'
            },
            # Sales Journal POS taxes
            {
                'page': 'SJ',
                'line': 'TPS Sales Journal POS',
                'field': 'sales_journal.taxes.tps',
                'action': 'ADD_TO_EXISTING'
            }
        ],
        'operation': 'sum_all',
        'expected_total': 3788.92
    },
    'BC': {
        'label_en': 'Gift Cards & Bons d\'achat Total',
        'label_fr': 'Gift Cards & Bons d\'achat Total',
        'sources': [
            {
                'page': 2,
                'line': 'Adj GiveX Gift Card',
                'field': 'revenue.givex.total'
            },
            {
                'page': 6,
                'line': 'Bon D\'achat',
                'field': 'settlements.bon_dachat',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 6,
                'line': 'Gift Card',
                'field': 'settlements.gift_card',
                'action': 'ADD_TO_EXISTING'
            },
            {
                'page': 6,
                'line': 'Bon D\'achat Remanco',
                'field': 'settlements.bon_dachat_remanco',
                'action': 'ADD_TO_EXISTING'
            }
        ],
        'operation': 'sum_all',
        'expected_total': 400.00
    }
}


# =============================================================================
# SPECIAL RULES AND NOTES
# =============================================================================
SPECIAL_RULES = {
    'column_d_calculation': {
        'description': 'Column D = -(New Balance) - Deposit on Hand Today',
        'formula': 'negative(balance.new_balance) - deposits.deposit_on_hand',
        'example': '3871908.19 - 0 = 3871908.19'
    },
    'column_cf_rule': {
        'description': 'Column CF = -(Total Transfers - Payments) [ALWAYS negative]',
        'formula': 'negative(balance.front_office_transfers - balance.front_office_payments)',
        'note': 'ALWAYS negative for both A/R Misc and Front Office Transfers'
    },
    'bf_calculation': {
        'description': 'Column BF = -Forfait + Club Lounge value (from diff_forfait)',
        'base_field': 'derived.diff_forfait',
        'note': 'Calculated column, not directly from Daily Revenue'
    },
    'sales_journal_rule': {
        'description': 'All DEBITS are NEGATIVE, all CREDITS are POSITIVE',
        'source': 'Sales Journal (separate from Daily Revenue)',
        'note': 'Sign handling is important for these columns'
    },
    'accumulator_rule': {
        'description': 'Accumulator columns sum multiple sources from different pages',
        'columns_affected': ['AX', 'AY', 'CB'],
        'action': 'ADD_TO_EXISTING means cumulative sum, not replace'
    }
}


# =============================================================================
# QUICK REFERENCE: ALL COLUMNS BY CATEGORY
# =============================================================================
COLUMNS_BY_CATEGORY = {
    'REVENUE_DEPARTMENTS': ['AK', 'AL', 'AM', 'AN'],
    'AUTRES_REVENUS': ['AO', 'AP', 'AS', 'AT', 'AU', 'AV', 'AW', 'BA', 'AG'],
    'TAXES': ['AZ', 'AX', 'AY'],
    'SETTLEMENTS': ['BC', 'CC'],
    'BALANCE_AND_TRANSFERS': ['D', 'CF'],
    'SPECIAL_CALCULATED': ['BF'],
    'SALES_JOURNAL_CAFE_LINK': ['E', 'F', 'G', 'H', 'I'],
    'SALES_JOURNAL_PIAZZA': ['J', 'K', 'L', 'M', 'N'],
    'SALES_JOURNAL_SPESA': ['O', 'P', 'Q', 'R', 'S'],
    'SALES_JOURNAL_CHAMBRES': ['T', 'U', 'V', 'W', 'X'],
    'SALES_JOURNAL_BANQUET': ['Y', 'Z', 'AA', 'AB', 'AC'],
    'SALES_JOURNAL_OTHER': ['AD', 'AJ', 'BR'],
    'CREDIT_CARDS': ['BI', 'BJ', 'BK', 'BL', 'BM', 'BN'],
    'HP_DEDUCTIONS': ['BQ'],
    'POS_TOTALS': ['DG', 'DH', 'DI', 'DJ', 'DK', 'DM'],
}


# =============================================================================
# REVENUE FROM DAILY REVENUE PARSER (Feb 4, 2026)
# =============================================================================
EXPECTED_VALUES_FEB_4 = {
    'chambres_total': 50936.60,
    'telephones_local': 0.00,
    'telephones_interurbain': 0.00,
    'telephones_publics': 0.00,
    'nettoyeur_dry_cleaning': 0.00,
    'sonifi': 0.00,
    'location_boutique': 0.00,
    'lit_pliant': 0.00,
    'machine_distributrice': 0.00,
    'autres_revenus_taxable': 0.00,
    'autre_payer_taxable': 0.00,
    'massage': 383.30,
    'location_salle_forfait': 1620.00,
    'internet': -0.46,
    'autres_grand_livre_total': -92589.85,
    'adj_givex_gift_card': 400.00,
    'ar_misc_total': 0.00,
    'taxe_hebergement': 1783.53,
    'tps_141740175': 2635.79,
    'tvq_1019892413': 5257.25,
    'tps_tel_local': 0.00,
    'tps_tel_interurbain': 0.00,
    'tvq_tel_local': 0.00,
    'tvq_tel_interurbain': 0.00,
    'tps_autres': 100.17,
    'tvq_autres': 200.23,
    'tps_internet': 0.00,
    'tvq_internet': 0.46,
    'bon_dachat': 0.00,
    'certificat_cadeaux': 0.00,
    'gift_card': 0.00,
    'bon_dachat_remanco': 0.00,
    'new_balance': -3871908.19,
    'deposit_on_hand': 0.00,
    'front_office_transfers': 0.00,
}


# =============================================================================
# SALES JOURNAL MAPPING (Separate from Daily Revenue PDF)
# =============================================================================
SALES_JOURNAL_MAPPING = {
    'J': {
        'column_index': 9,
        'label': 'Piazza Nourriture',
        'source': 'Sales Journal',
        'calculation': 'sum(DEBITS) - sum(CREDITS) - hp_deductions - adjustments',
        'sign_rule': 'DEBIT=negative, CREDIT=positive',
        'feb4_expected': 1981.40
    },
    'K': {
        'column_index': 10,
        'label': 'Piazza Alcool (Boisson)',
        'source': 'Sales Journal',
        'sign_rule': 'DEBIT=negative, CREDIT=positive',
        'feb4_expected': 75.00
    },
    'L': {
        'column_index': 11,
        'label': 'Piazza Bières',
        'source': 'Sales Journal',
        'sign_rule': 'DEBIT=negative, CREDIT=positive',
        'feb4_expected': 198.00
    },
    'M': {
        'column_index': 12,
        'label': 'Piazza Non Alcool Bar (Minéraux)',
        'source': 'Sales Journal',
        'sign_rule': 'DEBIT=negative, CREDIT=positive',
        'feb4_expected': 19.00
    },
    'N': {
        'column_index': 13,
        'label': 'Piazza Vins',
        'source': 'Sales Journal',
        'sign_rule': 'DEBIT=negative, CREDIT=positive',
        'feb4_expected': 219.00
    }
}


# =============================================================================
# HELPER FUNCTION: Get all mappings for a given jour column
# =============================================================================
def get_mapping_for_column(column_letter):
    """
    Get the complete mapping configuration for a jour sheet column.

    Args:
        column_letter (str): Column letter (e.g., 'AK', 'AY', 'BC')

    Returns:
        dict: Complete mapping configuration for that column, or None if not found
    """
    return DAILY_REV_TO_JOUR.get(column_letter.upper(), None)


def get_accumulator_config(column_letter):
    """
    Get the accumulator configuration for columns that sum multiple sources.

    Args:
        column_letter (str): Column letter (e.g., 'AX', 'AY', 'CB')

    Returns:
        dict: Accumulator configuration, or None if not an accumulator column
    """
    return ACCUMULATOR_COLUMNS.get(column_letter.upper(), None)


def get_all_columns():
    """Get a list of all jour columns that have Daily Revenue mappings."""
    return list(DAILY_REV_TO_JOUR.keys())


def get_columns_by_category(category):
    """Get all columns in a specific category."""
    return COLUMNS_BY_CATEGORY.get(category, [])
