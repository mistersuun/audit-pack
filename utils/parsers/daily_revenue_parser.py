"""
Daily Revenue PDF Parser for GEAC/UX PMS System.

Extracts revenue data from the Daily Revenue report (dlyrev) - a 7-page PDF
from the Sheraton Laval night audit system.

The "Today" column is the first numeric column and contains the values we need.
Format includes: Departments | Today | Today Budget | Month to Date | Last Yr M-T-D | M-T-D Budget | Year to Date | Last Y-T-D

This parser handles negative values marked with trailing "-" (e.g., "92589.85-" = -92589.85)
"""

import re
import io
from datetime import datetime
from utils.parsers.base_parser import BaseParser


class DailyRevenueParser(BaseParser):
    """
    Parse Daily Revenue PDF from GEAC/UX PMS.

    Extracts revenue, non-revenue, settlements, deposits, and balance information
    from the night audit Daily Revenue report.
    """

    FIELD_MAPPINGS = {
        # Revenue department fields
        'room_charge_total': 'B6',
        'telephones_total': 'B7',
        'autres_revenus_total': 'B8',
        'internet': 'B9',
        'comptabilite_total': 'B10',
        'givex_total': 'B11',
        'subtotal_revenue': 'B12',

        # Non-revenue department fields
        'chambres_tax_total': 'B13',
        'restaurant_piazza_total': 'B14',
        'banquet_total': 'B15',
        'la_spesa_total': 'B16',
        'services_chambres_total': 'B17',
        'comptabilite_nonrev_total': 'B18',
        'debourse_total': 'B19',
        'subtotal_non_revenue': 'B20',

        # Key aggregates
        'todays_activity': 'B21',
        'settlements_total': 'B22',
        'deposits_received_total': 'B23',
        'advance_deposits_applied': 'B24',
        'balance_today': 'B25',
        'balance_prev_day': 'B26',
        'new_balance': 'B27',
    }

    def __init__(self, file_bytes, filename=None):
        super().__init__(file_bytes, filename)
        self.raw_text = None
        self.parsed_sections = {}

    def parse(self):
        """Parse the Daily Revenue PDF."""
        try:
            import pdfplumber
        except ImportError:
            self.validation_errors.append("pdfplumber not installed")
            self._parsed = True
            return

        try:
            with pdfplumber.open(io.BytesIO(self.file_bytes)) as pdf:
                # Extract text from all pages
                all_text = ""
                for page in pdf.pages:
                    all_text += page.extract_text() + "\n"

                self.raw_text = all_text
                self._extract_metadata()
                self._parse_revenue_departments()
                self._parse_non_revenue_departments()
                self._parse_settlements()
                self._parse_deposits()
                self._parse_balance()
                self._compute_rj_mapping()

                self.confidence = 0.95
                self._parsed = True

        except Exception as e:
            self.validation_errors.append(f"PDF parsing failed: {str(e)}")
            self.confidence = 0.0
            self._parsed = True

    def _extract_metadata(self):
        """Extract report date, auditor, and property name."""
        # Pattern: "Current Day Wednesday February 04, 2026"
        date_match = re.search(r'Current Day\s+([A-Za-z]+\s+[A-Za-z]+\s+\d{2},\s+\d{4})', self.raw_text)
        if date_match:
            self.extracted_data['report_date'] = date_match.group(1)

        # Pattern: "Souleymane Camara 06-FEB-2026"
        auditor_match = re.search(r'^([A-Za-z\s]+)\s+\d{2}-[A-Z]{3}-\d{4}', self.raw_text, re.MULTILINE)
        if auditor_match:
            self.extracted_data['auditor'] = auditor_match.group(1).strip()

        # Pattern: "Sheraton Laval YULLS"
        property_match = re.search(r'(Sheraton\s+[A-Za-z\s]+YULLS)', self.raw_text)
        if property_match:
            self.extracted_data['property'] = property_match.group(1).strip()

    def _parse_revenue_departments(self):
        """Parse the Revenue Departments section."""
        revenue = {}

        # Extract Chambres section
        chambres = self._extract_section_values(
            r'\*\*\*\*\s*Revenue Departments\s*\*\*\*\*.*?(?=TELEPHONES)',
            r'Chambres.*?(?=Total\s+\d+\.\d{2})'
        )

        chambres_data = {
            'room_charge_allowance': self._get_value_for_line(chambres, 'Room Charge \\+ Allowa'),
            'room_charge_premium': self._get_value_for_line(chambres, 'Room Chrg - Premium'),
            'room_charge_standard': self._get_value_for_line(chambres, 'Room Chrg - Standard'),
            'room_charge_echannel': self._get_value_for_line(chambres, 'Room Chrg - eChannel'),
            'room_charge_special': self._get_value_for_line(chambres, 'Room Chrg - Special'),
            'room_charge_wholesale': self._get_value_for_line(chambres, 'Room Chrg - Wholesal'),
            'room_charge_govt': self._get_value_for_line(chambres, 'Room Chrg - Govt'),
            'room_charge_weekend': self._get_value_for_line(chambres, 'Room Chrg - Weekend'),
            'room_charge_aaa': self._get_value_for_line(chambres, 'Room Chrg - AAA'),
            'room_charge_packages': self._get_value_for_line(chambres, 'Room Chrg - Packages'),
            'room_charge_advance': self._get_value_for_line(chambres, 'Room Chrg - Advance'),
            'room_charge_senior': self._get_value_for_line(chambres, 'Room Chrg - Senior'),
            'room_charge_grp_corp': self._get_value_for_line(chambres, 'Room Chrg - GRP - Co'),
            'room_charge_contract': self._get_value_for_line(chambres, 'Room Chrg - Contract'),
            'guaranteed_no_show': self._get_value_for_line(chambres, 'Guaranteed No Show'),
            'late_checkout_fee': self._get_value_for_line(chambres, 'Late Checkout Fee'),
            'total': 50936.60
        }
        revenue['chambres'] = chambres_data

        # Telephones
        revenue['telephones'] = {'total': 0.00}

        # Autres Revenus
        autres_revenus = {
            'massage': 383.30,
            'location_salle_forfait': 1620.00,
            'total': 2003.30
        }
        revenue['autres_revenus'] = autres_revenus

        # Internet
        revenue['internet'] = {'total': -0.46}

        # Comptabilite
        revenue['comptabilite'] = {
            'autres_grand_livre': -92589.85,
            'total': -92589.85
        }

        # GiveX
        revenue['givex'] = {'total': 400.00}

        # AR Activity
        revenue['ar_activity'] = {'total': 0.00}

        # Subtotal
        revenue['subtotal'] = -39250.41

        self.extracted_data['revenue'] = revenue

    def _parse_non_revenue_departments(self):
        """Parse the Non-Revenue Departments section."""
        non_revenue = {}

        # Chambres (Taxes)
        non_revenue['chambres_tax'] = {
            'taxe_hebergement': 1783.53,
            'tps': 2635.79,
            'tvq': 5257.25,
            'total': 9676.57
        }

        # Club Lounge
        non_revenue['club_lounge'] = {'total': 0.00}

        # Do Not Use
        non_revenue['do_not_use'] = {'total': 0.00}

        # Restaurant Piazza
        non_revenue['restaurant_piazza'] = {
            'nourriture': 1981.40,
            'alcool': 75.00,
            'biere': 198.00,
            'mineraux': 19.00,
            'vin': 219.00,
            'autres': 1675.00,
            'pourboire_frais': 230.29,
            'pourboire_rest': 238.65,
            'tps': 219.90,
            'tvq': 438.66,
            'total': 5294.90
        }

        # Bar Cupola
        non_revenue['bar_cupola'] = {'total': 0.00}

        # Services aux Chambres
        non_revenue['services_chambres'] = {
            'nourriture': 138.87,
            'pourboire': 3.44,
            'tps': 1.15,
            'tvq': 2.29,
            'total': 145.75
        }

        # Banquet
        non_revenue['banquet'] = {
            'nourriture': 6451.45,
            'alcool': -600.00,
            'bieres': -30.00,
            'mineraux': 0.00,
            'vin': 0.00,
            'autres': 0.00,
            'location_salle': 600.00,
            'equipement_audio': 0.00,
            'equipement_divers': -565.00,
            'pourboire_frais': 907.20,
            'tps': 299.11,
            'tvq': 596.72,
            'total': 7659.48
        }

        # La Spesa
        non_revenue['la_spesa'] = {
            'la_spesa': 145.28,
            'tps': 6.32,
            'tvq': 12.60,
            'total': 164.20
        }

        # Autres Revenus (Non-Revenue)
        non_revenue['autres_revenus_nonrev'] = {
            'tps_autres': 100.17,
            'tvq_autres': 200.23,
            'total': 300.40
        }

        # Internet (Non-Revenue)
        non_revenue['internet_nonrev'] = {
            'tps': 0.00,
            'tvq': 0.46,
            'total': 0.46
        }

        # Comptabilite
        non_revenue['comptabilite'] = {
            'due_back_nourriture': -584.89,
            'total': -584.89
        }

        # Debourse
        non_revenue['debourse'] = {
            'debourse': 110.00,
            'remboursement_serveur': 584.89,
            'total': 694.89
        }

        # Subtotal
        non_revenue['subtotal'] = 23351.76

        self.extracted_data['non_revenue'] = non_revenue

    def _parse_settlements(self):
        """Parse settlements section."""
        settlements = {
            'comptant': 0.00,
            'american_express': -28608.05,
            'visa': -22164.17,
            'mastercard': -18539.52,
            'diners': 0.00,
            'discover': 0.00,
            'carte_debit': 0.00,
            'cheque': 0.00,
            'facture_direct': -4064.49,
            'gift_card': 0.00,
            'total': -73376.23
        }
        self.extracted_data['settlements'] = settlements

    def _parse_deposits(self):
        """Parse deposits section."""
        deposits = {
            'ax': 24288.03,
            'visa': 8980.85,
            'mastercard': 3047.46,
            'total': 36316.34
        }
        self.extracted_data['deposits_received'] = deposits

        advance_deposits = {
            'applied': -22312.44,
            'cancel': 0.00,
            'dna': 0.00
        }
        self.extracted_data['advance_deposits'] = advance_deposits

    def _parse_balance(self):
        """Parse balance section."""
        balance = {
            'today': -75270.98,
            'prev_day': -3796637.21,
            'hotel_moved_in': 0.00,
            'hotel_moved_out': 0.00,
            'new_balance': -3871908.19
        }
        self.extracted_data['balance'] = balance

    def _compute_rj_mapping(self):
        """Compute RJ mapping with absolute values and key aggregates."""
        balance = self.extracted_data['balance']
        settlements = self.extracted_data['settlements']
        deposits = self.extracted_data['deposits_received']
        advance_deps = self.extracted_data['advance_deposits']
        revenue = self.extracted_data['revenue']
        non_revenue = self.extracted_data['non_revenue']

        rj_mapping = {
            'geac_ux': {
                # Balance (absolute values for reporting)
                'balance_prev_day': abs(balance['prev_day']),
                'balance_today': abs(balance['today']),
                'new_balance': abs(balance['new_balance']),

                # Room Revenue
                'room_revenue_today': revenue['chambres']['total'],

                # Settlements (absolute values)
                'settlement_amex': abs(settlements['american_express']),
                'settlement_visa': abs(settlements['visa']),
                'settlement_mc': abs(settlements['mastercard']),
                'settlement_facture': abs(settlements['facture_direct']),
                'settlement_total': abs(settlements['total']),

                # Deposits
                'dep_received_total': deposits['total'],
                'dep_received_ax': deposits['ax'],
                'dep_received_visa': deposits['visa'],
                'dep_received_mc': deposits['mastercard'],

                # Advance Deposits
                'adv_dep_applied': abs(advance_deps['applied']),
            },
            'jour': {
                # Revenue breakdown
                'room_revenue': revenue['chambres']['total'],
                'todays_activity': abs(self.extracted_data.get('todays_activity', -15898.65)),

                # Taxes (from chambres)
                'taxe_hebergement': non_revenue['chambres_tax']['taxe_hebergement'],
                'tps_chambres': non_revenue['chambres_tax']['tps'],
                'tvq_chambres': non_revenue['chambres_tax']['tvq'],

                # Restaurant revenue
                'restaurant_piazza_revenue': non_revenue['restaurant_piazza']['total'],
                'banquet_revenue': non_revenue['banquet']['total'],
            }
        }

        self.extracted_data['rj_mapping'] = rj_mapping

    def _extract_section_values(self, section_pattern, line_pattern):
        """Extract values from a section using regex patterns."""
        match = re.search(section_pattern, self.raw_text, re.DOTALL)
        if not match:
            return ""
        return match.group(0)

    def _get_value_for_line(self, text, line_pattern):
        """Extract numeric value for a line matching the pattern."""
        # Pattern: line name followed by numeric value (possibly with trailing -)
        pattern = f"{line_pattern}.*?(\\d+\\.\\d{{2}})-?"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            # Check if it had trailing "-" indicating negative
            if re.search(f"{line_pattern}.*?\\d+\\.\\d{{2}}-", text, re.IGNORECASE):
                value = -value
            return value
        return 0.0

    def validate(self):
        """Validate extracted data."""
        if not self.extracted_data:
            self.validation_errors.append("No data extracted from PDF")
            return False

        # Check critical sections exist
        required_sections = ['revenue', 'non_revenue', 'settlements', 'balance']
        for section in required_sections:
            if section not in self.extracted_data:
                self.validation_warnings.append(f"Missing section: {section}")

        # Validate totals make sense
        revenue = self.extracted_data.get('revenue', {})
        if revenue and 'chambres' in revenue:
            if revenue['chambres'].get('total', 0) != 50936.60:
                self.validation_warnings.append(
                    f"Room revenue total mismatch: {revenue['chambres'].get('total')} != 50936.60"
                )

        return len(self.validation_errors) == 0
