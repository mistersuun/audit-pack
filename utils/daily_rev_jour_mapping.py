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
        'label_en': 'GEAC Compensation (Mch/Liqueur)',
        'label_fr': 'Compensation GEAC',
        'source_page': 'GEAC_UX + AR Summary',
        'source_line': '-(Facture Direct - AR Guest Folios)',
        'operation': 'geac_compensation',
        'formula': '-(facture_direct - ar_guest_folios)',
        'base_field': 'derived.geac_compensation',
        'description': 'GEAC compensation: -(DR Facture Direct - AR Guest Folios). Zero if FD = AR. Positive if FD < AR.',
        'sign_handling': 'keep_sign',
        'note': 'Requires both DR Facture Direct and AR Summary Guest Folios'
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
        'label_en': 'Autres Revenus (Lit Pliant + Fr/Etage + InterHotel)',
        'label_fr': 'Autres Rev',
        'source_page': 'PAGE 2 + SALES JOURNAL + PAGE 7',
        'source_line': 'DR Lit Pliant + SJ Piazza/Chambres fr_etage + DR InterHotel XferIn',
        'operation': 'accumulate',
        'accumulator_fields': [
            'revenue.autres_revenus.lit_pliant',
            'sales_journal.piazza.fr_etage',
            'sales_journal.chambres.fr_etage',
            'balance.interhotel_xferin',
        ],
        'description': 'AU = DR rollaway bed + SJ Piazza fr_etage (debit/credit) + SJ Chambres fr_etage + InterHotel XferIn. '
                       'Matches balancer calc[46]. SJ debits stored as negative — addition gives bqt + (-piaz_debit) = bqt - piaz.',
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
        'label_en': 'Internet (DR + SJ Banquet)',
        'label_fr': 'Internet',
        'source_page': 'PAGE 2 + Sales Journal',
        'source_line': 'DR Internet + SJ Bqt Internet',
        'operation': 'accumulate',
        'accumulator_fields': [
            'revenue.internet.total',
            'sales_journal.banquet.internet',
        ],
        'description': 'AW = DR Internet (signed, often negative) + SJ Banquet Internet. '
                       'User rule Apr 23: InterHotel XferIn is NOT in AW — it moved to AU.',
        'sign_handling': 'keep_sign',
        'note': 'DR Internet can be negative (corrections). InterHotel goes to AU, not here.'
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
        'label_en': 'Location Salle (Banquet + Piazza + DR)',
        'label_fr': 'Location de Salles',
        'source_page': 'SALES JOURNAL + PAGE 2',
        'source_line': 'SJ banquet + piazza location_salle + DR location_salle_forfait',
        'operation': 'accumulate',
        'accumulator_fields': [
            'sales_journal.banquet.location_salle',
            'sales_journal.piazza.location_salle',
            'revenue.autres_revenus.location_salle_forfait',
        ],
        'description': 'Room rental: banquet + piazza (SJ) + forfait (DR). Matches balancer calc[32]',
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
            'non_revenue.comptabilite_nonrev.tps',
            # NOTE: F&B OPERA taxes (Piazza/Bqt/Spesa/ServCh) deliberately excluded — already in sales_journal.taxes.tps
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
            'non_revenue.comptabilite_nonrev.tvq',
            # NOTE: F&B OPERA taxes (Piazza/Bqt/Spesa/ServCh) deliberately excluded — already in sales_journal.taxes.tvq
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
        'label_en': 'Autre Revenu Taxable + Bon d\'achat',
        'label_fr': 'Autre Rev Taxable + Bon d\'achat',
        'source_page': 'PAGES 2, 6',
        'source_line': 'Autre a Payer Taxable + Bons d\'achat',
        'operation': 'accumulate',
        'accumulator_fields': [
            'revenue.autres_revenus.autre_a_payer_taxable',
            'settlements.bon_dachat',
            'settlements.gift_card',
            'settlements.bon_dachat_remanco',
        ],
        'description': 'Autre Revenu Taxable (DR p.2) + Bon d\'achat + Gift Card + Bon d\'achat Remanco. '
                       'GiveX removed Apr 23: it belongs in CB col 79 as always_negative (not BC as credit).',
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
        'expected_value': -3871908.19,
        'description': 'D = -|New Balance| - Deposit on Hand (always negative)',
        'sign_handling': 'keep_sign',
        'note': 'Result is always negative: -abs(new_balance) - deposit_on_hand'
    },
    'CF': {
        'column_index': 83,
        'label_en': 'Transfer to A/R',
        'label_fr': 'Transfer to A/R',
        'source_page': 'AR Summary + PAGE 2',
        'source_line': 'AR Guest Folios - AR Payments - DR AR Misc',
        'operation': 'cf_transfer',
        'formula': 'ar_guest_folios - ar_payments - dr_ar_misc',
        'accumulator_fields': [
            'ar_summary.front_office_transfers.guest_folios',
            '-ar_summary.payments',
            '-revenue.ar_activity.total',
        ],
        'description': 'CF = AR Summary Guest Folios - AR Summary Payments - DR p.2 AR Misc. '
                       'From Jour cell header: "Total Transfers (AR summary Report) '
                       '- Payments (AR summary Report) - AR Misc (Daily Revenue Report page 2)"',
        'sign_handling': 'keep_sign',
        'note': 'When Guest Folios = DR FD and Payments = 0 and AR Misc = 0, CF simplifies to DR FD.'
    },

    # =========================================================================
    # SPECIAL CALCULATED COLUMNS
    # =========================================================================
    'BF': {
        'column_index': 57,
        'label_en': 'Club Lounge & Forfait Calculation',
        'label_fr': 'Club Lounge & Forfait Calculation',
        'source_page': 'DERIVED',
        'source_line': 'Calculated from -SJ Forfait + Club Lounge + G4',
        'operation': 'formula',
        'formula': '-forfait + club_lounge + g4',
        'base_field': 'derived.diff_forfait',
        'expected_value': 0.00,
        'description': 'Column BF = -SJ Forfait + Club Lounge + G4 (Apr 23 GT: -120.18 + 0 + 40 = -80.18).',
        'sign_handling': 'keep_sign'
    },

    # =========================================================================
    # SALES JOURNAL: RESTAURANT/BAR DEPARTMENTS
    # =========================================================================

    # --- PAUSE SPESA / CAFE LINK (E-I, cols 4-8) ---
    'E': {
        'column_index': 4,
        'label_en': 'Pause Spesa / Cafe Link Nourriture',
        'label_fr': 'Nou_Link',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Pause Spesa (banquet + piazza) + Cafe Link Food',
        'operation': 'accumulate',
        'accumulator_fields': [
            'sales_journal.banquet.pause_spesa',
            'sales_journal.piazza.pause_spesa',
            'sales_journal.cafe_link.nourriture',
        ],
        'description': 'E = SJ banquet pause_spesa + piazza pause_spesa + cafe_link nourriture. Apr 21: 6020.5+78 = 6098.5',
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
        'label_en': 'Pourboires à Payer (Total)',
        'label_fr': 'Pourboires à Payer',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Total pourboire_a_payer across all F&B depts',
        'operation': 'accumulate',
        'accumulator_fields': [
            'sales_journal.piazza.pourboire_a_payer',
            'sales_journal.banquet.pourboire_a_payer',
            'sales_journal.spesa.pourboire_a_payer',
            'sales_journal.chambres.pourboire_a_payer',
        ],
        'description': 'Sum of pourboire_a_payer across Piazza, Banquet, Spesa, Chambres (matches balancer calc[29])',
        'sign_handling': 'keep_sign'
    },
    'AH': {
        'column_index': 33,
        'label_en': 'Droits d\'auteur SOCAN',
        'label_fr': 'SOCAN',
        'source_page': 'SALES JOURNAL',
        'source_line': 'SOCAM (SOCAN rights fees)',
        'operation': 'direct',
        'base_field': 'sales_journal.banquet.socam',
        'description': 'SOCAN copyright fees from SJ banquet.socam. Sign preserved: negative if DEBIT, positive if CREDIT.',
        'sign_handling': 'keep_sign'
    },
    'AJ': {
        'column_index': 35,
        'label_en': 'Tabagie',
        'label_fr': 'Tabagie',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Tabagie / Tobacco (Spesa + Piazza + Chambres)',
        'operation': 'accumulate',
        'accumulator_fields': [
            'sales_journal.spesa.tabagie',
            'sales_journal.piazza.tabagie',
            'sales_journal.chambres.tabagie',
        ],
        'description': 'Tobacco/tabagie sales: Spesa + Piazza + Chambres (matches balancer calc[35]).',
        'sign_handling': 'keep_sign'
    },
    'AE': {
        'column_index': 30,
        'label_en': 'Equipement Audio Visuel (Banquet - Piazza reversal)',
        'label_fr': 'Equipement Audio',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Banquet Equip Audio Visuel + Piazza Equip Audio',
        'operation': 'accumulate',
        'accumulator_fields': [
            'sales_journal.banquet.equip_audio_visuel',
            'sales_journal.piazza.equip_audio',
        ],
        'description': 'Banquet AV credit + Piazza AV reversal (debit stored as negative). Matches balancer calc[30]=bqt_eq_audio - piaz_eq_audio.',
        'sign_handling': 'keep_sign'
    },
    'AF': {
        'column_index': 31,
        'label_en': 'Divers Banquet + Piazza',
        'label_fr': 'Divers Banq',
        'source_page': 'SALES JOURNAL',
        'source_line': 'Banquet EQ Divers + Piazza EQ Divers',
        'operation': 'accumulate',
        'accumulator_fields': [
            'sales_journal.banquet.eq_divers',
            'sales_journal.piazza.eq_divers',
        ],
        'description': 'Divers equipment from Banquet + Piazza. Apr 23: =-17.4+8517.4 = 8500.',
        'sign_handling': 'keep_sign'
    },
    'CB': {
        'column_index': 79,
        'label_en': 'Certificat Cadx (SJ Cert Cadeau − |GiveX|)',
        'label_fr': 'Cert Cadx',
        'source_page': 'PAGE 2',
        'source_line': 'SJ CERT CADEAU debit − DR GiveX adjustment (abs)',
        'operation': 'cf_transfer',
        'accumulator_fields': [
            'sales_journal.adjustments.cert_cadeau',  # SJ cert cadeau debit (positive)
            '-|revenue.givex.total|',                 # subtract abs(GiveX), robust to DR sign
        ],
        'description': 'CB = SJ cert_cadeau − |GiveX| (matches balancer calc[79]). When cert_cadeau=0, behaves as -|GiveX|. abs() guards against DR sign drift.',
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
    # BQ/BR: HP Administration and Hotel Promotion tips.
    # These come from HP Excel daily extraction (jour_deductions cols 68/69),
    # NOT from SJ adjustments (which are period totals, not nightly values).
    # The HP deduction pipeline (_apply_hp_deductions, HP_DIRECT_COLS) handles
    # writing these when HP data is available. No DAILY_REV_TO_JOUR entry needed
    # since they're written by the HP path, not by compute_all().

    # =========================================================================
    # POS SUMMARY TOTALS — Excel formula cells, NOT writable.
    # DG(110)=SUM(E+J+O+T+Y), DH(111)=SUM(F+K+P+U+Z), DI(112)=SUM(G+L+Q+V+AA),
    # DJ(113)=SUM(H+M+R+W+AB), DK(114)=SUM(I+N+S+X+AC), DM(116)=DH+DI+DJ+DK.
    # Protected by FORMULA_COLUMNS in RJFillerCOM — do not add entries here.
    # =========================================================================

    # =========================================================================
    # ROOM STATISTICS (from Market Segment report)
    # =========================================================================
    'CK': {
        'column_index': 88,
        'label_en': 'Simple (rooms sold)',
        'label_fr': 'SIMPLE',
        'source_page': 'Market Segment',
        'source_line': 'TOTAL Rooms today',
        'operation': 'direct',
        'base_field': 'market_segment.total_rooms_today',
        'description': 'Rooms sold from Market Segment. Written as integer value, overwriting the default formula.',
        'sign_handling': 'keep_sign'
    },
    'CN': {
        'column_index': 91,
        'label_en': 'Complimentary rooms',
        'label_fr': 'COMP.',
        'source_page': 'Market Segment',
        'source_line': 'T62 Complimentary Rooms today',
        'operation': 'direct',
        'base_field': 'market_segment.complimentary_rooms_today',
        'description': 'Complimentary rooms count from Market Segment T62 line.',
        'sign_handling': 'keep_sign'
    },
    'CO': {
        'column_index': 92,
        'label_en': 'Number of clients',
        'label_fr': '# CLIENT',
        'source_page': 'Market Segment',
        'source_line': 'TOTAL Guests today',
        'operation': 'direct',
        'base_field': 'market_segment.total_guests_today',
        'description': 'Total guest count from Market Segment TOTAL line.',
        'sign_handling': 'keep_sign'
    },
    'CP': {
        'column_index': 93,
        'label_en': 'Out of order rooms',
        'label_fr': "HORS D'USAGE",
        'source_page': 'DBRS',
        'source_line': 'OOO column',
        'operation': 'direct',
        'base_field': 'dbrs.ooo_rooms',
        'description': 'Out of order rooms from DBRS report OOO column. Default 0 if not available.',
        'sign_handling': 'keep_sign'
    },
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
    'SALES_JOURNAL_OTHER': ['AD', 'AJ'],
    'CREDIT_CARDS': ['BI', 'BJ', 'BK', 'BL', 'BM', 'BN'],
    # BQ/BR (HP tips) are written by _apply_hp_deductions, not via DAILY_REV_TO_JOUR.
    # They are not in this category mapping because they have no DAILY_REV_TO_JOUR entry.
    'ROOM_STATISTICS': ['CK', 'CN', 'CO', 'CP'],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_mapping_for_column(column_letter):
    """Get the mapping configuration for a jour sheet column."""
    return DAILY_REV_TO_JOUR.get(column_letter.upper(), None)


def get_all_columns():
    """Get a list of all jour columns that have Daily Revenue mappings."""
    return list(DAILY_REV_TO_JOUR.keys())


def get_columns_by_category(category):
    """Get all columns in a specific category."""
    return COLUMNS_BY_CATEGORY.get(category, [])
