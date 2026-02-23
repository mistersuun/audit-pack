"""
Quasimodo — Automated Credit Card Reconciliation Engine.
Compares terminal totals (transelect) vs bank settlements (geac_ux) by card type.

Quasimodo is the credit card reconciliation process at Sheraton Laval hotel. It compares:
- Terminal side (transelect sheet): credit card totals from POS terminals and Moneris batch reports
- Bank side (geac_ux sheet): settlement amounts reported by the bank (FreedomPay/Fusebox)

For each card type (Visa, MasterCard, Amex, Debit, Discover), the terminal total minus the
bank cash-out should equal zero (±$0.01 tolerance).
"""

import io
import xlrd
from utils.rj_reader import RJReader


class QuasimodoReconciler:
    """Automated card reconciliation (terminal vs. bank)."""

    CARD_TYPES = ['visa', 'mastercard', 'amex', 'debit', 'discover']
    TOLERANCE = 0.01  # Allow $0.01 variance

    def __init__(self):
        self.terminal_data = {}  # From transelect
        self.bank_data = {}       # From geac_ux
        self.reconciliation = None

    def load_from_rj(self, rj_bytes):
        """
        Load data from RJ file.

        Uses the convenience methods from rj_reader:
        - read_transelect_totals() returns {'visa': total, 'mastercard': total, 'amex': total, 'debit': total, 'discover': total}
        - read_geac_cash_out() returns {'visa': amount, 'mastercard': amount, 'amex': amount, 'debit': 0, 'discover': amount, 'diners': amount}
        """
        reader = RJReader(rj_bytes)
        self.terminal_data = reader.read_transelect_totals()
        self.bank_data = reader.read_geac_cash_out()

    def load_from_quasimodo_file(self, file_bytes):
        """
        Load terminal totals directly from a Quasimodo .xls file.

        Quasimodo files contain terminal sales by card type from the POS system.
        Structure:
        - Row 0: Headers (GL, amounts, descriptions, sources)
        - Rows 1+: Card type entries (DEBIT, VISA, MC, DC, AX)
        - Multiple source types: GLB (GLB entries), REC (REC entries), MON (MON entries),
          CAN (Canada), US, TRANSIT (settlement)
        - Column A: Date code (e.g., '0206' for Feb 6)
        - Column B: Amount
        - Column C: GL code (100200, 100210, 100400, etc.)
        - Column G: Description/Source

        Returns:
        {
            'date': '0206',
            'card_totals': {
                'debit': total_amount,
                'visa': total_amount,
                'mastercard': total_amount,
                'amex': total_amount,
                'discover': total_amount,
            },
            'by_source': {
                'glb': {'debit': amount, 'visa': amount, ...},
                'rec': {'debit': amount, 'visa': amount, ...},
                'mon': {'debit': amount, 'visa': amount, ...},
            },
            'transit_amount': amount,  # TRANSIT settlement
            'gross_total': total_sales,
            'file_date': date_extracted,
        }
        """
        try:
            file_stream = io.BytesIO(file_bytes)
            wb = xlrd.open_workbook(file_contents=file_bytes)
            ws = wb.sheet_by_index(0)

            # Card type mapping
            card_map = {
                'DEBIT': 'debit',
                'VISA': 'visa',
                'MC': 'mastercard',
                'DC': 'discover',
                'AX': 'amex',
            }

            # Initialize result structure
            result = {
                'date': None,
                'card_totals': {k: 0.0 for k in ['debit', 'visa', 'mastercard', 'amex', 'discover']},
                'by_source': {
                    'glb': {k: 0.0 for k in ['debit', 'visa', 'mastercard', 'amex', 'discover']},
                    'rec': {k: 0.0 for k in ['debit', 'visa', 'mastercard', 'amex', 'discover']},
                    'mon': {k: 0.0 for k in ['debit', 'visa', 'mastercard', 'amex', 'discover']},
                    'can': 0.0,
                    'us': 0.0,
                },
                'transit_amount': 0.0,
                'gross_total': 0.0,
                'file_date': None,
            }

            # Parse each row (skip header row 0)
            for row_idx in range(1, ws.nrows):
                date_code = ws.cell_value(row_idx, 0)  # Column A
                amount = self._safe_float(ws.cell_value(row_idx, 1))  # Column B
                gl_code = ws.cell_value(row_idx, 2)  # Column C
                description = ws.cell_value(row_idx, 3)  # Column D (description)
                source_desc = ws.cell_value(row_idx, 6)  # Column G (source)

                # Extract date from first row
                if result['date'] is None and date_code:
                    result['date'] = str(date_code)

                if not description or not source_desc:
                    continue

                # Parse card type and source from description
                # e.g., "VENTES FEVRIER 2026 DEBIT GLB" -> DEBIT, GLB
                #       "VENTES FEVRIER 2026 VISA REC" -> VISA, REC
                #       "VENTES FEVRIER 2026 TRANSIT" -> TRANSIT

                desc_upper = str(description).upper()
                source_upper = str(source_desc).upper()

                # Check for TRANSIT
                if 'TRANSIT' in desc_upper:
                    result['transit_amount'] += amount
                    result['by_source']['can'] = amount if 'CAN' in source_upper else result['by_source']['can']
                    result['by_source']['us'] = amount if 'US' in source_upper else result['by_source']['us']
                    continue

                # Extract card type
                card_type = None
                for card_key, card_label in card_map.items():
                    if card_key in desc_upper:
                        card_type = card_label
                        break

                if not card_type:
                    continue

                # Extract source type (GLB, REC, MON)
                source_type = None
                for src in ['GLB', 'REC', 'MON']:
                    if src in source_upper:
                        source_type = src.lower()
                        break

                # Add to card totals
                result['card_totals'][card_type] += amount
                result['gross_total'] += amount

                # Add to source breakdown
                if source_type:
                    result['by_source'][source_type][card_type] += amount

            # Store file date if available (reconstruct from date code)
            if result['date']:
                result['file_date'] = f"2026-02-{result['date']}"

            # Set terminal_data for reconciliation
            self.terminal_data = result['card_totals']

            return result

        except Exception as e:
            # Return error structure
            return {
                'error': str(e),
                'card_totals': {k: 0.0 for k in ['debit', 'visa', 'mastercard', 'amex', 'discover']},
                'by_source': {},
                'transit_amount': 0.0,
                'gross_total': 0.0,
            }

    @staticmethod
    def _safe_float(value, default=0.0):
        """Safely convert value to float."""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                cleaned = value.replace('$', '').replace(',', '').strip()
                if cleaned == '' or cleaned == '-':
                    return default
                return float(cleaned)
            return float(value)
        except (ValueError, TypeError):
            return default

    def load_manual(self, terminal_data, bank_data):
        """Load data manually (for testing or manual entry)."""
        self.terminal_data = terminal_data
        self.bank_data = bank_data

    def reconcile(self):
        """
        Calculate reconciliation by card type.

        Returns dict:
        {
            'cards': {
                'visa': {'terminal': 5000.00, 'bank': 5000.00, 'variance': 0.00, 'reconciled': True},
                'mastercard': {...},
                'amex': {...},
                'debit': {...},
                'discover': {...},
            },
            'summary': {
                'total_terminal': 25000.00,
                'total_bank': 24999.50,
                'total_variance': 0.50,
                'status': 'reconciled' or 'discrepancy',
                'discrepancy_cards': ['visa']  # list of cards with issues
            }
        }
        """
        result = {
            'cards': {},
            'summary': {
                'total_terminal': 0,
                'total_bank': 0,
                'total_variance': 0,
                'status': 'reconciled',
                'discrepancy_cards': []
            }
        }

        for card_type in self.CARD_TYPES:
            terminal = self.terminal_data.get(card_type, 0) or 0
            bank = self.bank_data.get(card_type, 0) or 0
            variance = round(terminal - bank, 2)
            reconciled = abs(variance) <= self.TOLERANCE

            result['cards'][card_type] = {
                'terminal': round(terminal, 2),
                'bank': round(bank, 2),
                'variance': variance,
                'reconciled': reconciled
            }

            result['summary']['total_terminal'] += terminal
            result['summary']['total_bank'] += bank

            if not reconciled:
                result['summary']['status'] = 'discrepancy'
                result['summary']['discrepancy_cards'].append(card_type)

        result['summary']['total_terminal'] = round(result['summary']['total_terminal'], 2)
        result['summary']['total_bank'] = round(result['summary']['total_bank'], 2)
        result['summary']['total_variance'] = round(
            result['summary']['total_terminal'] - result['summary']['total_bank'], 2
        )

        self.reconciliation = result
        return result

    def get_status_message_fr(self):
        """Get French status message for display."""
        if not self.reconciliation:
            return "Réconciliation non effectuée"

        status = self.reconciliation['summary']['status']
        if status == 'reconciled':
            return "✓ Toutes les cartes sont réconciliées"
        else:
            cards = self.reconciliation['summary']['discrepancy_cards']
            card_names = {'visa': 'Visa', 'mastercard': 'MasterCard', 'amex': 'Amex', 'debit': 'Débit', 'discover': 'Discover'}
            names = [card_names.get(c, c) for c in cards]
            return f"⚠ Écart détecté: {', '.join(names)} — Vérifier batch Moneris ou contacter Roula/Mandy"

    def to_printable_report(self):
        """Generate a text-based printable report."""
        if not self.reconciliation:
            return "Aucune réconciliation disponible."

        lines = []
        lines.append("=" * 70)
        lines.append("QUASIMODO — RÉCONCILIATION DES CARTES DE CRÉDIT")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"{'Type de carte':<15} {'Terminal':>12} {'Banque':>12} {'Écart':>12} {'Statut':>10}")
        lines.append("-" * 70)

        card_labels = {'visa': 'Visa', 'mastercard': 'MasterCard', 'amex': 'Amex', 'debit': 'Débit', 'discover': 'Discover'}

        for card_type in self.CARD_TYPES:
            card = self.reconciliation['cards'][card_type]
            status = "✓ OK" if card['reconciled'] else "✗ ÉCART"
            lines.append(f"{card_labels[card_type]:<15} {card['terminal']:>12,.2f} {card['bank']:>12,.2f} {card['variance']:>12,.2f} {status:>10}")

        lines.append("-" * 70)
        s = self.reconciliation['summary']
        lines.append(f"{'TOTAL':<15} {s['total_terminal']:>12,.2f} {s['total_bank']:>12,.2f} {s['total_variance']:>12,.2f}")
        lines.append("")
        lines.append(self.get_status_message_fr())
        lines.append("=" * 70)

        return "\n".join(lines)
