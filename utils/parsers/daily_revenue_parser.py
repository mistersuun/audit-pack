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
        # These are informational — actual auto-fill goes through JourMapper (fill_jour endpoint)
        'room_revenue': 'AK',
        'new_balance': 'D',
        'balance_today': 'E',
    }

    def __init__(self, file_bytes, filename=None):
        super().__init__(file_bytes, filename)
        self.raw_text = None
        self._pages_text = []

    def parse(self):
        """Parse the Daily Revenue PDF — actually reads the PDF, no hardcoded values."""
        try:
            import pdfplumber
        except ImportError:
            self.validation_errors.append("pdfplumber not installed")
            self._parsed = True
            return

        try:
            with pdfplumber.open(io.BytesIO(self.file_bytes)) as pdf:
                self._pages_text = []
                for page in pdf.pages:
                    self._pages_text.append(page.extract_text() or "")

            self.raw_text = "\n".join(self._pages_text)

            self._extract_metadata()
            self._parse_revenue_departments()
            self._parse_non_revenue_departments()
            self._parse_settlements()
            self._parse_deposits()
            self._parse_balance()
            self._compute_rj_mapping()

            self.confidence = 0.90
            self._parsed = True

        except Exception as e:
            self.validation_errors.append(f"PDF parsing failed: {str(e)}")
            self.confidence = 0.0
            self._parsed = True

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_today(self, text, label, negate=False):
        """Extract the Today (first numeric column) value for a line starting with label.

        Numbers may have commas (1,234.56) and trailing '-' for negative values.
        Some lines have an account number (integer) before the Today value — these
        are skipped by requiring a decimal point in the matched value.
        """
        escaped = re.escape(label.strip())
        # Match label, then optionally skip leading integers (account numbers), then the
        # first decimal-formatted number (currency value).
        pattern = rf'(?:^|\n)\s*{escaped}\s+(?:\d+\s+)*([\d,]+\.\d+)(-?)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = float(match.group(1).replace(',', ''))
            if match.group(2) == '-':
                val = -val
            return -val if negate else val
        return 0.0

    def _get_section_total(self, text, section_header):
        """Extract the 'Total' line value that follows a given section header."""
        escaped = re.escape(section_header.strip())
        # Find section header, then look for next 'Total' line within 3000 chars
        pattern = rf'(?:^|\n)\s*{escaped}\s*\n(.*?)(?:^|\n)\s*Total\s+([\d,]+\.?\d*)(-?)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            val = float(match.group(2).replace(',', ''))
            if match.group(3) == '-':
                val = -val
            return val
        return 0.0

    def _get_between(self, text, start_label, end_label=None):
        """Return text between start_label and end_label (or end of text)."""
        start_pat = re.search(
            rf'(?:^|\n)\s*{re.escape(start_label)}\s*\n',
            text, re.IGNORECASE
        )
        if not start_pat:
            return ""
        start_pos = start_pat.end()
        if end_label:
            end_pat = re.search(
                rf'(?:^|\n)\s*{re.escape(end_label)}',
                text[start_pos:], re.IGNORECASE
            )
            if end_pat:
                return text[start_pos:start_pos + end_pat.start()]
        return text[start_pos:]

    # ── Metadata ─────────────────────────────────────────────────────────────

    def _extract_metadata(self):
        """Extract report date, auditor, and property name."""
        date_match = re.search(
            r'Current Day\s+\w+\s+(\w+\s+\d{1,2},\s+\d{4})',
            self.raw_text
        )
        if date_match:
            self.extracted_data['report_date'] = date_match.group(1)

        auditor_match = re.search(
            r'^([A-Za-z\s]+)\s+Current Day',
            self.raw_text, re.MULTILINE
        )
        if auditor_match:
            self.extracted_data['auditor'] = auditor_match.group(1).strip()

        property_match = re.search(r'(Sheraton\s+\w+)\s+\w+\s+Daily Revenue', self.raw_text)
        if property_match:
            self.extracted_data['property'] = property_match.group(1).strip()

        # Check for pre-audit timestamp
        ts_match = re.search(r'(\d{2}-\w{3}-\d{4}\s+\d{1,2}:\d{2}\s+[AP]M)', self.raw_text)
        if ts_match:
            self.extracted_data['report_timestamp'] = ts_match.group(1)
            self._check_timestamp_validity(ts_match.group(1))

    def _check_timestamp_validity(self, timestamp_str):
        """Warn if DR was run before 3:00 AM (pre-audit, missing room charges).

        A pre-audit DR will be missing ~$50K+ of room charges, taxes, and
        balance data. See docs/RJ_AUTOFILL_MASTER.md section 1b.
        """
        try:
            dt = datetime.strptime(timestamp_str.strip(), "%d-%b-%Y %I:%M %p")
            if dt.hour < 3:
                self.validation_warnings.append(
                    f"PRE-AUDIT WARNING: DR timestamp {timestamp_str} is before 3:00 AM. "
                    f"Room charges, taxes, and balance data may be incomplete. "
                    f"Request the post-audit version."
                )
        except (ValueError, AttributeError):
            pass

    # ── Revenue Departments (Pages 1-2) ──────────────────────────────────────

    def _parse_revenue_departments(self):
        """Parse Revenue Departments section from pages 1-2."""
        # Use pages 1-2 for revenue sections
        p1 = self._pages_text[0] if len(self._pages_text) > 0 else ""
        p2 = self._pages_text[1] if len(self._pages_text) > 1 else ""
        text = p1 + "\n" + p2

        revenue = {}

        # Chambres section — bounded by "Chambres\n" ... "TELEPHONES"
        ch_text = self._get_between(text, 'Chambres', 'TELEPHONES')
        chambres_total = self._get_today(ch_text + "\nTotal ", 'Total') if ch_text else 0.0
        if chambres_total == 0.0:
            # Fallback: find Total line after Chambres header in page 1
            chambres_total = self._get_section_total(p1, 'Chambres')
        revenue['chambres'] = {
            'total': chambres_total,
            'room_charge_standard': self._get_today(ch_text, 'Room Chrg - Standard'),
            'room_charge_premium': self._get_today(ch_text, 'Room Chrg - Premium'),
            'guaranteed_no_show': self._get_today(ch_text, 'Guaranteed No Show'),
            'late_checkout': self._get_today(ch_text, 'Late Checkout Fee'),
            'reservation_cancel': self._get_today(ch_text, 'Reservation/Cancella'),
        }

        # Telephones
        tel_text = self._get_between(text, 'TELEPHONES', 'Autres Revenus')
        if not tel_text:
            tel_text = self._get_between(text, 'TELEPHONES', 'Total')
        revenue['telephones'] = {
            'local': self._get_today(tel_text, 'Telephone Local'),
            'interurbain': self._get_today(tel_text, 'Interurbain'),
            'publics': self._get_today(tel_text, 'Telephone Publics'),
            'total': self._get_section_total(text, 'TELEPHONES'),
        }

        # Autres Revenus — header is at end of page 1, items/total continue on page 2
        text12 = p1 + "\n" + p2
        ar_text = self._get_between(text12, 'Autres Revenus', 'Internet')
        revenue['autres_revenus'] = {
            'massage': self._get_today(ar_text, 'Massage'),
            'location_salle_forfait': self._get_today(ar_text, 'Location Salle Forfa'),
            'location_boutique': self._get_today(ar_text, 'Location De Boutique'),
            'nettoyeur': self._get_today(ar_text, 'Nettoyeur-Dry Cleani'),
            'sonifi': self._get_today(ar_text, 'Sonifi'),
            'lit_pliant': self._get_today(ar_text, 'Lit Pliant'),
            'fax': self._get_today(ar_text, 'Fax & Photocopies') if ar_text else 0.0,
            'machine_distributrice': self._get_today(ar_text, 'MACHINE DISTRIBUTRIC'),
            'autre_a_payer_taxable': self._get_today(ar_text, 'Autre A Payer Taxabl'),
            'total': self._get_section_total(text12, 'Autres Revenus'),
        }

        # Internet
        int_text = self._get_between(p2, 'Internet', 'Comptabilite')
        revenue['internet'] = {
            'total': self._get_section_total(p2, 'Internet'),
        }

        # Comptabilite revenue section
        comp_text = self._get_between(p2, 'Comptabilite', 'GiveX')
        revenue['comptabilite'] = {
            'autres_grand_livre': self._get_today(comp_text, 'Autres Grand Livre'),
            'total': self._get_section_total(p2, 'Comptabilite'),
        }
        # Handle negative "Autres Grand Livre" — the large negative entry
        # Find the largest (most negative) Autres Grand Livre line
        if comp_text:
            ag_matches = re.findall(r'Autres Grand Livre\s*\w*\s+([\d,]+\.\d+)(-?)', comp_text, re.IGNORECASE)
            if ag_matches:
                values = []
                for num_str, sign in ag_matches:
                    v = float(num_str.replace(',', ''))
                    if sign == '-':
                        v = -v
                    values.append(v)
                # Use the sum (net GL activity)
                revenue['comptabilite']['autres_grand_livre'] = sum(values)

        # GiveX
        revenue['givex'] = {
            'total': self._get_section_total(p2, 'GiveX'),
        }

        # AR Activity
        revenue['ar_activity'] = {
            'total': self._get_section_total(p2, 'AR Activity'),
        }

        # Subtotal Revenue Departments
        sub_match = re.search(
            r'Subtotal Revenue Dept\S*\s+([\d,]+\.?\d*)(-?)',
            self.raw_text, re.IGNORECASE
        )
        if sub_match:
            val = float(sub_match.group(1).replace(',', ''))
            if sub_match.group(2) == '-':
                val = -val
            revenue['subtotal'] = val

        self.extracted_data['revenue'] = revenue

    # ── Non-Revenue Departments (Pages 2-5) ──────────────────────────────────

    def _parse_non_revenue_departments(self):
        """Parse Non-Revenue Departments section."""
        # Pages 2-5 contain non-revenue
        p2 = self._pages_text[1] if len(self._pages_text) > 1 else ""
        p3 = self._pages_text[2] if len(self._pages_text) > 2 else ""
        p4 = self._pages_text[3] if len(self._pages_text) > 3 else ""
        p5 = self._pages_text[4] if len(self._pages_text) > 4 else ""

        # Non-revenue section starts after "Non-Revenue Departments" header
        # Chambres tax section (p2)
        non_rev_start = self.raw_text.find('Non-Revenue Departments')
        non_rev_text = self.raw_text[non_rev_start:] if non_rev_start >= 0 else self.raw_text

        non_revenue = {}

        # Chambres (Taxes)
        ch_tax_text = self._get_between(non_rev_text, 'Chambres', 'Club Lounge')
        if not ch_tax_text:
            ch_tax_text = non_rev_text[:2000]
        non_revenue['chambres_tax'] = {
            'taxe_hebergement': self._get_today(ch_tax_text, 'Taxe Hebergement'),
            'tps': self._get_today(ch_tax_text, 'TPS'),
            'tvq': self._get_today(ch_tax_text, 'TVQ'),
            'total': self._get_section_total(non_rev_text, 'Chambres'),
        }

        # Club Lounge
        cl_text = self._get_between(non_rev_text, 'Club Lounge', 'DO NOT USE')
        if not cl_text:
            cl_text = self._get_between(non_rev_text, 'Club Lounge', 'Restaurant')
        non_revenue['club_lounge'] = {
            'total': self._get_section_total(non_rev_text, 'Club Lounge'),
        }

        # ── F&B Restaurant tax sections (pages 3-4) ────────────────────────
        # These sections contain TPS/TVQ for each F&B department.
        # Use page-level text to avoid matching Revenue-section headers.
        nr_pages34 = p3 + "\n" + p4

        # Restaurant Piazza
        piaz_text = self._get_between(nr_pages34, 'Restaurant Piazza', 'Bar Cupola')
        if not piaz_text:
            piaz_text = self._get_between(non_rev_text, 'Restaurant Piazza', 'Bar Cupola')
        non_revenue['restaurant_piazza'] = {
            'tps': self._get_today(piaz_text, 'TPS Rest Piazza') if piaz_text else 0.0,
            'tvq': self._get_today(piaz_text, 'TVQ Rest Piazza') if piaz_text else 0.0,
            'total': self._get_section_total(nr_pages34, 'Restaurant Piazza') if piaz_text else 0.0,
        }

        # Services Aux Chambres (Room Service)
        servch_text = self._get_between(nr_pages34, 'SERVICES AUX CHAMBRES', 'BANQUET')
        if not servch_text:
            servch_text = self._get_between(non_rev_text, 'SERVICES AUX CHAMBRES', 'BANQUET')
        non_revenue['services_chambres'] = {
            'tps': self._get_today(servch_text, 'TPS Serv Chamb') if servch_text else 0.0,
            'tvq': self._get_today(servch_text, 'TVQ Serv Chamb') if servch_text else 0.0,
            'total': self._get_section_total(nr_pages34, 'SERVICES AUX CHAMBRES') if servch_text else 0.0,
        }

        # Banquet
        bqt_text = self._get_between(nr_pages34, 'BANQUET', 'La Spesa')
        if not bqt_text:
            bqt_text = self._get_between(non_rev_text, 'BANQUET', 'La Spesa')
        non_revenue['banquet'] = {
            'tps': self._get_today(bqt_text, 'TPS Bqt') if bqt_text else 0.0,
            'tvq': self._get_today(bqt_text, 'TVQ Bqt') if bqt_text else 0.0,
            'equipement_audio': self._get_today(bqt_text, 'Equipement Audio') if bqt_text else 0.0,
            'equipement_divers': self._get_today(bqt_text, 'Equipement Divers') if bqt_text else 0.0,
            'location_salle': self._get_today(bqt_text, 'Location De Salle') if bqt_text else 0.0,
            'total': self._get_section_total(nr_pages34, 'BANQUET') if bqt_text else 0.0,
        }

        # La Spesa
        spesa_text = self._get_between(nr_pages34, 'La Spesa', 'TELEPHONES')
        if not spesa_text:
            spesa_text = self._get_between(non_rev_text, 'La Spesa', 'TELEPHONES')
        non_revenue['la_spesa'] = {
            'tps': self._get_today(spesa_text, 'Tps- La Spesa') if spesa_text else 0.0,
            'tvq': self._get_today(spesa_text, 'Tvq - La Spesa') if spesa_text else 0.0,
            'total': self._get_section_total(nr_pages34, 'La Spesa') if spesa_text else 0.0,
        }

        # ── Debourse ────────────────────────────────────────────────────────
        deb_text = self._get_between(non_rev_text, 'Debourse', 'Package')
        non_revenue['debourse'] = {
            'debourse': self._get_today(deb_text, 'Debourse'),
            'remboursement_serveur': self._get_today(deb_text, 'Remboursement Serveu'),
            'total': self._get_section_total(non_rev_text, 'Debourse'),
        }

        # ── Autres Revenus tax section (page 5) ────────────────────────────
        # Use page 5 text specifically to avoid matching the Revenue "Autres Revenus" on p1-2
        nr_page5 = p5
        ar_nr_text = self._get_between(nr_page5, 'AUTRES REVENUS', 'Internet')
        if not ar_nr_text:
            # Fallback: search in full non-rev text (after the F&B sections)
            ar_nr_text = self._get_between(non_rev_text, 'AUTRES REVENUS', 'Internet')
        non_revenue['autres_tax'] = {
            'tvq_autres': self._get_today(ar_nr_text, 'TVQ Autres') if ar_nr_text else 0.0,
            'tps_autres': self._get_today(ar_nr_text, 'TPS Autres') if ar_nr_text else 0.0,
        }

        # Internet tax section in non-revenue (page 5)
        int_nr_text = self._get_between(nr_page5, 'Internet', 'Comptabilite')
        if not int_nr_text:
            int_nr_text = self._get_between(non_rev_text, 'Internet', 'Comptabilite')
        non_revenue['internet_nonrev'] = {
            'tvq': self._get_today(int_nr_text, 'TVQ Internet') if int_nr_text else 0.0,
            'tps': self._get_today(int_nr_text, 'TPS Internet') if int_nr_text else 0.0,
        }

        # Comptabilite tax section in non-revenue (page 5)
        comp_nr_text = self._get_between(nr_page5, 'Comptabilite', 'Debourse')
        if not comp_nr_text:
            comp_nr_text = self._get_between(non_rev_text, 'Comptabilite', 'Debourse')
        non_revenue['comptabilite_nonrev'] = {
            'tvq': self._get_today(comp_nr_text, 'Tvq') if comp_nr_text else 0.0,
            'tps': self._get_today(comp_nr_text, 'Tps') if comp_nr_text else 0.0,
        }

        # Combined tax totals — convenience aggregate for test pipeline and quick reads
        # Includes ALL departments: chambres + F&B restaurants + autres + internet + comptabilite
        non_revenue['total_tvq'] = (
            non_revenue.get('chambres_tax', {}).get('tvq', 0) +
            non_revenue.get('restaurant_piazza', {}).get('tvq', 0) +
            non_revenue.get('services_chambres', {}).get('tvq', 0) +
            non_revenue.get('banquet', {}).get('tvq', 0) +
            non_revenue.get('la_spesa', {}).get('tvq', 0) +
            non_revenue.get('autres_tax', {}).get('tvq_autres', 0) +
            non_revenue.get('internet_nonrev', {}).get('tvq', 0) +
            non_revenue.get('comptabilite_nonrev', {}).get('tvq', 0)
        )
        non_revenue['total_tps'] = (
            non_revenue.get('chambres_tax', {}).get('tps', 0) +
            non_revenue.get('restaurant_piazza', {}).get('tps', 0) +
            non_revenue.get('services_chambres', {}).get('tps', 0) +
            non_revenue.get('banquet', {}).get('tps', 0) +
            non_revenue.get('la_spesa', {}).get('tps', 0) +
            non_revenue.get('autres_tax', {}).get('tps_autres', 0) +
            non_revenue.get('internet_nonrev', {}).get('tps', 0) +
            non_revenue.get('comptabilite_nonrev', {}).get('tps', 0)
        )

        # Subtotal Non-Revenue
        sub_match = re.search(
            r'Subtotal Non-Rev Dept\S*\s+([\d,]+\.?\d*)(-?)',
            self.raw_text, re.IGNORECASE
        )
        if sub_match:
            val = float(sub_match.group(1).replace(',', ''))
            if sub_match.group(2) == '-':
                val = -val
            non_revenue['subtotal'] = val

        self.extracted_data['non_revenue'] = non_revenue

    # ── Settlements (Pages 5-6) ───────────────────────────────────────────────

    def _parse_settlements(self):
        """Parse Settlements section — Today column values."""
        # Settlements appear starting on page 5
        p5 = self._pages_text[4] if len(self._pages_text) > 4 else ""
        p6 = self._pages_text[5] if len(self._pages_text) > 5 else ""
        settle_text = p5 + "\n" + p6

        # Find settlement section
        settle_start = settle_text.find('Settlements\n')
        if settle_start >= 0:
            settle_text = settle_text[settle_start:]

        settlements = {}

        settle_items = [
            ('comptant', 'Comptant'),
            ('american_express', 'American Express'),
            ('visa', 'Visa'),
            ('mastercard', 'MasterCard'),
            ('diners', 'Diners'),
            ('discover', 'Discover'),
            ('carte_debit', 'Carte Debit'),
            ('cheque', 'Cheque'),
            ('facture_direct', 'Facture Direct'),
            ('certificat_cadeaux', 'Gift Card'),
            ('hotel_promotion', 'Hotel Promotion'),
        ]

        for key, label in settle_items:
            settlements[key] = self._get_today(settle_text, label)

        # Total settlements
        total_match = re.search(
            r'Total Settlements\s+([\d,]+\.?\d*)(-?)',
            settle_text, re.IGNORECASE
        )
        if total_match:
            val = float(total_match.group(1).replace(',', ''))
            if total_match.group(2) == '-':
                val = -val
            settlements['total'] = val

        self.extracted_data['settlements'] = settlements

    # ── Deposits (Page 6) ─────────────────────────────────────────────────────

    def _parse_deposits(self):
        """Parse Deposits Received and Advance Deposits sections."""
        p6 = self._pages_text[5] if len(self._pages_text) > 5 else ""
        p7 = self._pages_text[6] if len(self._pages_text) > 6 else ""
        dep_text = p6 + "\n" + p7

        deposits_received = {
            'ax': self._get_today(dep_text, 'Dep Recvd - AX'),
            'visa': self._get_today(dep_text, 'Dep Recvd - Visa'),
            'mastercard': self._get_today(dep_text, 'Dep Recvd - Master'),
            'total': 0.0,
        }
        # Total Net Dep Rcvd
        total_dep_match = re.search(
            r'Total Net Dep Rcvd\s+([\d,]+\.?\d*)(-?)',
            dep_text, re.IGNORECASE
        )
        if total_dep_match:
            val = float(total_dep_match.group(1).replace(',', ''))
            if total_dep_match.group(2) == '-':
                val = -val
            deposits_received['total'] = val

        self.extracted_data['deposits_received'] = deposits_received

        # Advance Deposits (page 7)
        advance = {
            'applied': self._get_today(dep_text, 'Adv Dep Applied'),
            'cancel': self._get_today(dep_text, 'Adv Dep Cancel'),
            'dna': self._get_today(dep_text, 'Adv Dep DNA'),
        }
        self.extracted_data['advance_deposits'] = advance

    # ── Balance (Page 7) ──────────────────────────────────────────────────────

    def _parse_balance(self):
        """Parse Balance section from last page."""
        last_page = self._pages_text[-1] if self._pages_text else ""
        # Fallback: search entire text
        text = last_page if 'Balance Today' in last_page else self.raw_text
        p7 = self._pages_text[6] if len(self._pages_text) > 6 else ""

        def _bal(label):
            m = re.search(rf'{re.escape(label)}\s+([\d,]+\.?\d*)(-?)', text, re.IGNORECASE)
            if m:
                v = float(m.group(1).replace(',', ''))
                if m.group(2) == '-':
                    v = -v
                return v
            return 0.0

        balance = {
            'today': _bal('Balance Today'),
            'prev_day': _bal('Balance Prev Day'),
            'hotel_moved_in': _bal('Today Hotel Moved In'),
            'hotel_moved_out': _bal('Today Hotel Moved Out'),
            'new_balance': _bal('New Balance'),
        }

        # InterHotel XferIn (page 7) — needed for AW (Internet) column
        balance['interhotel_xferin'] = self._get_today(p7, 'InterHotel XferIn')

        self.extracted_data['balance'] = balance

    # ── RJ Mapping ────────────────────────────────────────────────────────────

    def _compute_rj_mapping(self):
        """Build rj_mapping with computed aggregates for downstream consumers."""
        balance = self.extracted_data.get('balance', {})
        settlements = self.extracted_data.get('settlements', {})
        deposits = self.extracted_data.get('deposits_received', {})
        adv_deps = self.extracted_data.get('advance_deposits', {})
        revenue = self.extracted_data.get('revenue', {})
        non_revenue = self.extracted_data.get('non_revenue', {})

        self.extracted_data['rj_mapping'] = {
            'geac_ux': {
                'balance_prev_day': abs(balance.get('prev_day', 0)),
                'balance_today': abs(balance.get('today', 0)),
                'new_balance': abs(balance.get('new_balance', 0)),
                'room_revenue_today': revenue.get('chambres', {}).get('total', 0),
                'settlement_amex': abs(settlements.get('american_express', 0)),
                'settlement_visa': abs(settlements.get('visa', 0)),
                'settlement_mc': abs(settlements.get('mastercard', 0)),
                'settlement_total': abs(settlements.get('total', 0)),
                'dep_received_total': deposits.get('total', 0),
                'adv_dep_applied': abs(adv_deps.get('applied', 0)),
            },
            'jour': {
                'room_revenue': revenue.get('chambres', {}).get('total', 0),
                'taxe_hebergement': non_revenue.get('chambres_tax', {}).get('taxe_hebergement', 0),
                'tps_chambres': non_revenue.get('chambres_tax', {}).get('tps', 0),
                'tvq_chambres': non_revenue.get('chambres_tax', {}).get('tvq', 0),
                # Combined TVQ/TPS across all departments → Jour AX (col 49) and AY (col 50)
                'tvq_total': non_revenue.get('total_tvq', 0),
                'tps_total': non_revenue.get('total_tps', 0),
            },
        }

    def validate(self):
        """Validate extracted data."""
        if not self.extracted_data:
            self.validation_errors.append("No data extracted from PDF")
            return False

        balance = self.extracted_data.get('balance', {})
        if balance.get('new_balance', 0) == 0:
            self.validation_warnings.append("New Balance is zero — balance section may not have parsed correctly")

        revenue = self.extracted_data.get('revenue', {})
        chambres_total = revenue.get('chambres', {}).get('total', 0)
        if chambres_total == 0:
            self.validation_warnings.append("Chambres total is zero — revenue section may not have parsed correctly")

        return len(self.validation_errors) == 0
