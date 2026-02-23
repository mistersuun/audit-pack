"""
Balance Checker — Comprehensive Night Audit Reconciliation Engine.

Reads an RJ Excel file and cross-validates all financial balances that should
net to zero. Identifies discrepancies, suggests corrections, and pinpoints
the likely source of errors.

6 core checks:
1. Quasimodo (Card Reconciliation): terminal vs bank by card type
2. Cash Recap: system total vs counted amount
3. AR Balance: (previous + charges - payments) = new balance
4. DueBack: sum of receptionist balances = recap total
5. Deposit: declared vs verified amounts
6. Revenue Cross-Check: jour totals vs recap + card + cash totals
"""

import io
import logging
from datetime import datetime
from collections import OrderedDict

logger = logging.getLogger(__name__)


class BalanceChecker:
    """Run all reconciliation checks on a single night's data."""

    TOLERANCE = 0.01  # $0.01 tolerance for floating point

    def __init__(self):
        self.checks = OrderedDict()
        self.rj_data = {}
        self.files_loaded = []
        self.audit_date = None

    def load_rj(self, rj_bytes):
        """Load and parse the main RJ file."""
        try:
            import xlrd
            wb = xlrd.open_workbook(file_contents=rj_bytes if isinstance(rj_bytes, bytes) else rj_bytes.read())
            self.rj_data['workbook'] = wb
            self.files_loaded.append('RJ')

            # Extract date from controle sheet
            try:
                ctrl = wb.sheet_by_name('controle')
                day = int(self._cell(ctrl, 2, 1) or 0)
                month = int(self._cell(ctrl, 3, 1) or 0)
                year = int(self._cell(ctrl, 4, 1) or 0)
                if day and month and year:
                    self.audit_date = f"{year}-{month:02d}-{day:02d}"
            except Exception:
                pass

            # Parse all relevant sheets
            self._parse_recap(wb)
            self._parse_transelect(wb)
            self._parse_geac_ux(wb)
            self._parse_dueback(wb)
            self._parse_jour(wb)
            self._parse_setd(wb)
            self._parse_depot(wb)

            return True
        except Exception as e:
            logger.error(f"Error loading RJ: {e}")
            return False

    def load_quasimodo(self, file_bytes):
        """Load a Quasimodo report file for card reconciliation."""
        try:
            from utils.quasimodo import QuasimodoReconciler
            qr = QuasimodoReconciler()
            result = qr.load_from_quasimodo_file(file_bytes if isinstance(file_bytes, bytes) else file_bytes.read())
            self.rj_data['quasimodo_file'] = result
            self.files_loaded.append('Quasimodo')
            return True
        except Exception as e:
            logger.error(f"Error loading Quasimodo: {e}")
            return False

    def load_sd(self, file_bytes, day=None):
        """Load an SD (Sommaire des Dépôts) file."""
        try:
            import xlrd
            wb = xlrd.open_workbook(file_contents=file_bytes if isinstance(file_bytes, bytes) else file_bytes.read())
            # SD files have 31 sheets (one per day)
            target_sheet = day if day else 1
            if isinstance(target_sheet, int) and target_sheet <= wb.nsheets:
                ws = wb.sheet_by_index(target_sheet - 1)
                sd_data = []
                for row_idx in range(1, ws.nrows):
                    dept = self._cell(ws, row_idx, 0) or ''
                    name = self._cell(ws, row_idx, 1) or ''
                    declared = self._safe_float(self._cell(ws, row_idx, 3))
                    verified = self._safe_float(self._cell(ws, row_idx, 4))
                    if name:
                        sd_data.append({
                            'department': str(dept).strip(),
                            'employee': str(name).strip(),
                            'declared': declared,
                            'verified': verified,
                            'variance': round(declared - verified, 2)
                        })
                self.rj_data['sd'] = sd_data
                self.files_loaded.append('SD')
            return True
        except Exception as e:
            logger.error(f"Error loading SD: {e}")
            return False

    # ──────────────────────────────────────────────
    # PARSERS
    # ──────────────────────────────────────────────

    def _parse_recap(self, wb):
        """Parse the Recap sheet — cash and payment summary."""
        try:
            ws = wb.sheet_by_name('Recap')
            self.rj_data['recap'] = {
                'comptant_ls_lecture': self._safe_float(self._cell(ws, 5, 1)),
                'comptant_ls_corr': self._safe_float(self._cell(ws, 5, 2)),
                'comptant_pos_lecture': self._safe_float(self._cell(ws, 6, 1)),
                'comptant_pos_corr': self._safe_float(self._cell(ws, 6, 2)),
                'cheque_lecture': self._safe_float(self._cell(ws, 7, 1)),
                'cheque_corr': self._safe_float(self._cell(ws, 7, 2)),
                'remb_gratuite': self._safe_float(self._cell(ws, 10, 1)),
                'remb_client': self._safe_float(self._cell(ws, 11, 1)),
                'dueback_total': self._safe_float(self._cell(ws, 16, 1)),
                'surplus_deficit': self._safe_float(self._cell(ws, 18, 1)),
                'total_net': self._safe_float(self._cell(ws, 24, 3)),
            }
        except Exception as e:
            logger.warning(f"Could not parse Recap: {e}")
            self.rj_data['recap'] = {}

    def _parse_transelect(self, wb):
        """Parse the transelect sheet — credit card terminal totals."""
        try:
            ws = wb.sheet_by_name('transelect')
            # Quasimodo totals (column E, rows 20-24)
            self.rj_data['transelect'] = {
                'debit_total': self._safe_float(self._cell(ws, 19, 4)),
                'visa_total': self._safe_float(self._cell(ws, 20, 4)),
                'mc_total': self._safe_float(self._cell(ws, 21, 4)),
                'amex_total': self._safe_float(self._cell(ws, 23, 4)),
                'discover_total': self._safe_float(self._cell(ws, 24, 4)),
                # POS terminal breakdowns (rows 9-13, various columns)
                'bar_debit': self._safe_float(self._cell(ws, 8, 1)),
                'bar_visa': self._safe_float(self._cell(ws, 9, 1)),
                'bar_mc': self._safe_float(self._cell(ws, 10, 1)),
                'bar_amex': self._safe_float(self._cell(ws, 11, 1)),
                # Reception terminal
                'rec_debit': self._safe_float(self._cell(ws, 19, 3)),
                'rec_visa': self._safe_float(self._cell(ws, 20, 3)),
                'rec_mc': self._safe_float(self._cell(ws, 21, 3)),
                'rec_amex': self._safe_float(self._cell(ws, 23, 3)),
                # Fusebox/bank
                'bank_visa': self._safe_float(self._cell(ws, 20, 1)),
                'bank_mc': self._safe_float(self._cell(ws, 21, 1)),
                'bank_amex': self._safe_float(self._cell(ws, 23, 1)),
            }
        except Exception as e:
            logger.warning(f"Could not parse transelect: {e}")
            self.rj_data['transelect'] = {}

    def _parse_geac_ux(self, wb):
        """Parse the geac_ux sheet — bank settlements and AR balances."""
        try:
            ws = wb.sheet_by_name('geac_ux')
            self.rj_data['geac'] = {
                # Cash out row (row 6) by card type
                'cashout_visa': self._safe_float(self._cell(ws, 5, 1)),
                'cashout_mc': self._safe_float(self._cell(ws, 5, 4)),
                'cashout_amex': self._safe_float(self._cell(ws, 5, 6)),
                'cashout_debit': self._safe_float(self._cell(ws, 5, 9)),
                'cashout_discover': self._safe_float(self._cell(ws, 5, 10)),
                # Daily revenue row (row 12)
                'rev_visa': self._safe_float(self._cell(ws, 11, 1)),
                'rev_mc': self._safe_float(self._cell(ws, 11, 4)),
                'rev_amex': self._safe_float(self._cell(ws, 11, 6)),
                'rev_debit': self._safe_float(self._cell(ws, 11, 9)),
                'rev_discover': self._safe_float(self._cell(ws, 11, 10)),
                # AR balances
                'ar_previous': self._safe_float(self._cell(ws, 31, 1)),
                'ar_charges': self._safe_float(self._cell(ws, 32, 1)),
                'ar_payments': self._safe_float(self._cell(ws, 33, 1)),
                'ar_new_balance': self._safe_float(self._cell(ws, 36, 1)),
            }
        except Exception as e:
            logger.warning(f"Could not parse geac_ux: {e}")
            self.rj_data['geac'] = {}

    def _parse_dueback(self, wb):
        """Parse the DUBACK# sheet — receptionist balances."""
        try:
            ws = wb.sheet_by_name('DUBACK#')
            receptionists = []
            # Columns C through Y (index 2-24), one per receptionist
            for col in range(2, min(25, ws.ncols)):
                name = str(self._cell(ws, 0, col) or '').strip()
                if not name:
                    continue
                # Sum all amounts in this column (rows 2+)
                total = 0
                for row in range(2, ws.nrows):
                    val = self._safe_float(self._cell(ws, row, col))
                    total += val
                if total != 0:
                    receptionists.append({'name': name, 'balance': round(total, 2)})

            # Column Z = total (index 25)
            grand_total = self._safe_float(self._cell(ws, ws.nrows - 1, min(25, ws.ncols - 1)))

            self.rj_data['dueback'] = {
                'receptionists': receptionists,
                'grand_total': grand_total,
                'calculated_total': round(sum(r['balance'] for r in receptionists), 2)
            }
        except Exception as e:
            logger.warning(f"Could not parse DUBACK#: {e}")
            self.rj_data['dueback'] = {}

    def _parse_jour(self, wb):
        """Parse the jour sheet — daily revenue totals."""
        try:
            ws = wb.sheet_by_name('jour')
            # Find today's column (last filled column with data)
            # jour has dates in row 3, data starts col 1
            today_col = None
            for col in range(ws.ncols - 1, 0, -1):
                val = self._cell(ws, 6, col)  # Room revenue row
                if val and self._safe_float(val) != 0:
                    today_col = col
                    break

            if today_col:
                self.rj_data['jour'] = {
                    'column': today_col,
                    'room_revenue': self._safe_float(self._cell(ws, 6, today_col)),
                    'fb_revenue': self._safe_float(self._cell(ws, 30, today_col)),
                    'total_revenue': self._safe_float(self._cell(ws, 48, today_col)),
                    'total_rooms_sold': self._safe_float(self._cell(ws, 4, today_col)),
                    'adr': self._safe_float(self._cell(ws, 7, today_col)),
                    'visa_payments': self._safe_float(self._cell(ws, 56, today_col)),
                    'mc_payments': self._safe_float(self._cell(ws, 57, today_col)),
                    'amex_payments': self._safe_float(self._cell(ws, 58, today_col)),
                    'debit_payments': self._safe_float(self._cell(ws, 59, today_col)),
                    'cash_payments': self._safe_float(self._cell(ws, 62, today_col)),
                }
            else:
                self.rj_data['jour'] = {}
        except Exception as e:
            logger.warning(f"Could not parse jour: {e}")
            self.rj_data['jour'] = {}

    def _parse_setd(self, wb):
        """Parse the SetD sheet — personnel deposit variances."""
        try:
            ws = wb.sheet_by_name('SetD')
            variances = []
            for col in range(1, min(ws.ncols, 30)):
                name = str(self._cell(ws, 0, col) or '').strip()
                if not name:
                    continue
                # Row with variance amount (usually one of the last rows)
                variance = self._safe_float(self._cell(ws, ws.nrows - 2, col))
                if variance != 0:
                    variances.append({'name': name, 'variance': round(variance, 2)})
            self.rj_data['setd'] = {
                'variances': variances,
                'total_variance': round(sum(v['variance'] for v in variances), 2)
            }
        except Exception as e:
            logger.warning(f"Could not parse SetD: {e}")
            self.rj_data['setd'] = {}

    def _parse_depot(self, wb):
        """Parse the depot sheet — deposit details."""
        try:
            ws = wb.sheet_by_name('depot')
            deposits = []
            total = 0
            for row in range(1, ws.nrows):
                amount = self._safe_float(self._cell(ws, row, 1))
                desc = str(self._cell(ws, row, 0) or '').strip()
                if amount != 0 and desc:
                    deposits.append({'description': desc, 'amount': round(amount, 2)})
                    total += amount
            self.rj_data['depot'] = {
                'entries': deposits,
                'total': round(total, 2)
            }
        except Exception as e:
            logger.warning(f"Could not parse depot: {e}")
            self.rj_data['depot'] = {}

    # ──────────────────────────────────────────────
    # BALANCE CHECKS
    # ──────────────────────────────────────────────

    def run_all_checks(self):
        """Run all 6 balance verification checks."""
        self.checks = OrderedDict()
        self._check_quasimodo()
        self._check_cash_recap()
        self._check_ar_balance()
        self._check_dueback()
        self._check_deposit_variance()
        self._check_revenue_crosscheck()
        return self.get_report()

    def _check_quasimodo(self):
        """Check 1: Card reconciliation — terminal vs bank by card type."""
        check = {
            'name': 'Réconciliation Cartes (Quasimodo)',
            'description': 'Terminal (transelect) vs Banque (geac_ux) par type de carte',
            'status': 'skip',
            'severity': 'info',
            'items': [],
            'total_variance': 0,
            'suggestion': ''
        }

        ts = self.rj_data.get('transelect', {})
        geac = self.rj_data.get('geac', {})
        qf = self.rj_data.get('quasimodo_file', {})

        if not ts and not qf:
            check['suggestion'] = 'Aucune donnée transelect trouvée. Téléversez le fichier RJ.'
            self.checks['quasimodo'] = check
            return

        card_checks = [
            ('Visa', ts.get('visa_total', 0), geac.get('cashout_visa', 0)),
            ('MasterCard', ts.get('mc_total', 0), geac.get('cashout_mc', 0)),
            ('Amex', ts.get('amex_total', 0), geac.get('cashout_amex', 0)),
            ('Débit', ts.get('debit_total', 0), geac.get('cashout_debit', 0)),
            ('Discover', ts.get('discover_total', 0), geac.get('cashout_discover', 0)),
        ]

        # If Quasimodo file loaded, use its totals instead
        if qf and qf.get('card_totals'):
            ct = qf['card_totals']
            card_checks = [
                ('Visa', ct.get('visa', 0), geac.get('cashout_visa', 0)),
                ('MasterCard', ct.get('mastercard', 0), geac.get('cashout_mc', 0)),
                ('Amex', ct.get('amex', 0), geac.get('cashout_amex', 0)),
                ('Débit', ct.get('debit', 0), geac.get('cashout_debit', 0)),
                ('Discover', ct.get('discover', 0), geac.get('cashout_discover', 0)),
            ]

        total_var = 0
        all_ok = True
        for card_name, terminal, bank in card_checks:
            variance = round(terminal - bank, 2)
            ok = abs(variance) <= self.TOLERANCE
            if not ok:
                all_ok = False
            total_var += abs(variance)
            check['items'].append({
                'label': card_name,
                'expected': round(bank, 2),
                'actual': round(terminal, 2),
                'variance': variance,
                'ok': ok
            })

        check['total_variance'] = round(total_var, 2)
        check['status'] = 'ok' if all_ok else 'error'
        check['severity'] = 'ok' if all_ok else ('warning' if total_var < 10 else 'error')

        if not all_ok:
            bad_cards = [i['label'] for i in check['items'] if not i['ok']]
            check['suggestion'] = f"Écart sur {', '.join(bad_cards)}. Vérifiez le batch Moneris et le rapport FreedomPay. Si l'écart est petit (<$1), c'est probablement un pourboire non-réconcilié."

        self.checks['quasimodo'] = check

    def _check_cash_recap(self):
        """Check 2: Cash — system total vs expected."""
        check = {
            'name': 'Balance Comptant (Recap)',
            'description': 'Comptant système (Lightspeed + POS) vs dépôt attendu',
            'status': 'skip',
            'severity': 'info',
            'items': [],
            'total_variance': 0,
            'suggestion': ''
        }

        recap = self.rj_data.get('recap', {})
        if not recap:
            check['suggestion'] = 'Aucune donnée Recap trouvée.'
            self.checks['cash_recap'] = check
            return

        ls_net = round((recap.get('comptant_ls_lecture', 0) or 0) + (recap.get('comptant_ls_corr', 0) or 0), 2)
        pos_net = round((recap.get('comptant_pos_lecture', 0) or 0) + (recap.get('comptant_pos_corr', 0) or 0), 2)
        total_cash = round(ls_net + pos_net, 2)
        surplus = recap.get('surplus_deficit', 0) or 0

        check['items'].append({'label': 'Lightspeed comptant', 'expected': ls_net, 'actual': ls_net, 'variance': 0, 'ok': True})
        check['items'].append({'label': 'Positouch comptant', 'expected': pos_net, 'actual': pos_net, 'variance': 0, 'ok': True})
        check['items'].append({'label': 'Total comptant système', 'expected': total_cash, 'actual': total_cash, 'variance': 0, 'ok': True})
        check['items'].append({
            'label': 'Surplus / Déficit',
            'expected': 0,
            'actual': surplus,
            'variance': surplus,
            'ok': abs(surplus) <= self.TOLERANCE
        })

        check['total_variance'] = abs(surplus)
        all_ok = abs(surplus) <= self.TOLERANCE
        check['status'] = 'ok' if all_ok else 'error'
        check['severity'] = 'ok' if all_ok else ('warning' if abs(surplus) < 50 else 'error')

        if not all_ok:
            if surplus > 0:
                check['suggestion'] = f"Surplus de ${surplus:.2f}. Vérifiez si un paiement n'a pas été enregistré dans Lightspeed ou POSitouch."
            else:
                check['suggestion'] = f"Déficit de ${abs(surplus):.2f}. Vérifiez les reçus de carte qui auraient pu être comptés comme comptant, ou un no-show non chargé."

        self.checks['cash_recap'] = check

    def _check_ar_balance(self):
        """Check 3: AR Balance — previous + charges - payments = new balance."""
        check = {
            'name': 'Balance AR (Comptes Recevables)',
            'description': 'Solde précédent + charges − paiements = nouveau solde',
            'status': 'skip',
            'severity': 'info',
            'items': [],
            'total_variance': 0,
            'suggestion': ''
        }

        geac = self.rj_data.get('geac', {})
        if not geac or not geac.get('ar_previous'):
            check['suggestion'] = 'Aucune donnée AR trouvée dans geac_ux.'
            self.checks['ar_balance'] = check
            return

        prev = geac.get('ar_previous', 0) or 0
        charges = geac.get('ar_charges', 0) or 0
        payments = geac.get('ar_payments', 0) or 0
        new_bal = geac.get('ar_new_balance', 0) or 0
        expected = round(prev + charges - payments, 2)
        variance = round(expected - new_bal, 2)

        check['items'] = [
            {'label': 'Solde précédent', 'expected': prev, 'actual': prev, 'variance': 0, 'ok': True},
            {'label': '+ Charges du jour', 'expected': charges, 'actual': charges, 'variance': 0, 'ok': True},
            {'label': '− Paiements du jour', 'expected': payments, 'actual': payments, 'variance': 0, 'ok': True},
            {'label': '= Solde calculé', 'expected': expected, 'actual': new_bal, 'variance': variance, 'ok': abs(variance) <= self.TOLERANCE}
        ]

        check['total_variance'] = abs(variance)
        all_ok = abs(variance) <= self.TOLERANCE
        check['status'] = 'ok' if all_ok else 'error'
        check['severity'] = 'ok' if all_ok else 'error'

        if not all_ok:
            check['suggestion'] = f"Écart de ${abs(variance):.2f} dans la balance AR. Causes probables : ajustement manquant, transfert de folio incomplet, ou paiement non posté. Vérifiez le journal des transactions dans Lightspeed."

        self.checks['ar_balance'] = check

    def _check_dueback(self):
        """Check 4: DueBack — sum of receptionist balances = recap total."""
        check = {
            'name': 'Balance DueBack (Réceptionnistes)',
            'description': 'Somme des balances réceptionnistes = total Recap',
            'status': 'skip',
            'severity': 'info',
            'items': [],
            'total_variance': 0,
            'suggestion': ''
        }

        db = self.rj_data.get('dueback', {})
        recap = self.rj_data.get('recap', {})

        if not db or not db.get('receptionists'):
            check['suggestion'] = 'Aucune donnée DueBack trouvée.'
            self.checks['dueback'] = check
            return

        calc_total = db.get('calculated_total', 0)
        recap_total = recap.get('dueback_total', 0) or 0

        for r in db.get('receptionists', []):
            check['items'].append({
                'label': r['name'],
                'expected': r['balance'],
                'actual': r['balance'],
                'variance': 0,
                'ok': True
            })

        variance = round(calc_total - recap_total, 2)
        check['items'].append({
            'label': 'Total calculé vs Recap',
            'expected': recap_total,
            'actual': calc_total,
            'variance': variance,
            'ok': abs(variance) <= self.TOLERANCE
        })

        check['total_variance'] = abs(variance)
        all_ok = abs(variance) <= self.TOLERANCE
        check['status'] = 'ok' if all_ok else 'error'
        check['severity'] = 'ok' if all_ok else ('warning' if abs(variance) < 10 else 'error')

        if not all_ok:
            check['suggestion'] = f"Écart de ${abs(variance):.2f} entre DueBack et Recap. Vérifiez si un réceptionniste a oublié de fermer sa caisse ou si un paiement a été posté après la fermeture."

        self.checks['dueback'] = check

    def _check_deposit_variance(self):
        """Check 5: Deposit — declared vs verified amounts (from SD file)."""
        check = {
            'name': 'Variances Dépôts (SD)',
            'description': 'Montants déclarés vs vérifiés par employé',
            'status': 'skip',
            'severity': 'info',
            'items': [],
            'total_variance': 0,
            'suggestion': ''
        }

        sd = self.rj_data.get('sd', [])
        setd = self.rj_data.get('setd', {})

        if not sd and not setd.get('variances'):
            check['suggestion'] = 'Aucun fichier SD téléversé et aucune donnée SetD dans le RJ.'
            self.checks['deposit_variance'] = check
            return

        # Use SD file if available, otherwise SetD from RJ
        variances_data = sd if sd else [{'employee': v['name'], 'declared': 0, 'verified': 0, 'variance': v['variance']} for v in setd.get('variances', [])]

        total_var = 0
        for entry in variances_data:
            var = entry.get('variance', 0)
            total_var += abs(var)
            check['items'].append({
                'label': entry.get('employee', entry.get('name', '?')),
                'expected': entry.get('verified', 0),
                'actual': entry.get('declared', 0),
                'variance': var,
                'ok': abs(var) <= self.TOLERANCE
            })

        check['total_variance'] = round(total_var, 2)
        has_issues = any(not i['ok'] for i in check['items'])
        check['status'] = 'ok' if not has_issues else 'error'
        check['severity'] = 'ok' if not has_issues else ('warning' if total_var < 50 else 'error')

        if has_issues:
            bad = [i['label'] for i in check['items'] if not i['ok']]
            check['suggestion'] = f"Variances détectées pour: {', '.join(bad)}. Vérifiez les reçus et le comptage de caisse de chaque employé."

        self.checks['deposit_variance'] = check

    def _check_revenue_crosscheck(self):
        """Check 6: Revenue — jour totals vs payments breakdown."""
        check = {
            'name': 'Croisement Revenus (Jour vs Paiements)',
            'description': 'Revenu total jour = carte + comptant + AR + autre',
            'status': 'skip',
            'severity': 'info',
            'items': [],
            'total_variance': 0,
            'suggestion': ''
        }

        jour = self.rj_data.get('jour', {})
        geac = self.rj_data.get('geac', {})

        if not jour or not jour.get('total_revenue'):
            check['suggestion'] = 'Aucune donnée jour trouvée.'
            self.checks['revenue_crosscheck'] = check
            return

        total_rev = jour.get('total_revenue', 0)
        card_total = sum([
            jour.get('visa_payments', 0) or 0,
            jour.get('mc_payments', 0) or 0,
            jour.get('amex_payments', 0) or 0,
            jour.get('debit_payments', 0) or 0,
        ])
        cash_total = jour.get('cash_payments', 0) or 0
        payments_sum = round(card_total + cash_total, 2)

        check['items'] = [
            {'label': 'Revenu total (jour)', 'expected': total_rev, 'actual': total_rev, 'variance': 0, 'ok': True},
            {'label': 'Visa', 'expected': jour.get('visa_payments', 0), 'actual': geac.get('cashout_visa', 0), 'variance': round((jour.get('visa_payments', 0) or 0) - (geac.get('cashout_visa', 0) or 0), 2), 'ok': abs((jour.get('visa_payments', 0) or 0) - (geac.get('cashout_visa', 0) or 0)) <= 1},
            {'label': 'MasterCard', 'expected': jour.get('mc_payments', 0), 'actual': geac.get('cashout_mc', 0), 'variance': round((jour.get('mc_payments', 0) or 0) - (geac.get('cashout_mc', 0) or 0), 2), 'ok': abs((jour.get('mc_payments', 0) or 0) - (geac.get('cashout_mc', 0) or 0)) <= 1},
            {'label': 'Amex', 'expected': jour.get('amex_payments', 0), 'actual': geac.get('cashout_amex', 0), 'variance': round((jour.get('amex_payments', 0) or 0) - (geac.get('cashout_amex', 0) or 0), 2), 'ok': abs((jour.get('amex_payments', 0) or 0) - (geac.get('cashout_amex', 0) or 0)) <= 1},
        ]

        total_var = sum(abs(i['variance']) for i in check['items'])
        check['total_variance'] = round(total_var, 2)
        has_issues = any(not i['ok'] for i in check['items'])
        check['status'] = 'ok' if not has_issues else 'error'
        check['severity'] = 'ok' if not has_issues else 'warning'

        if has_issues:
            check['suggestion'] = "Les montants de paiements par carte dans le jour ne correspondent pas aux encaissements bancaires. Vérifiez s'il y a des transactions en suspens ou des ajustements manuels."

        self.checks['revenue_crosscheck'] = check

    # ──────────────────────────────────────────────
    # REPORT
    # ──────────────────────────────────────────────

    def get_report(self):
        """Generate the full balance check report."""
        total_checks = len(self.checks)
        passed = sum(1 for c in self.checks.values() if c['status'] == 'ok')
        failed = sum(1 for c in self.checks.values() if c['status'] == 'error')
        skipped = sum(1 for c in self.checks.values() if c['status'] == 'skip')

        total_variance = sum(c.get('total_variance', 0) for c in self.checks.values())

        # Overall health
        if failed == 0 and skipped == 0:
            health = 'perfect'
            health_label = 'Tout est balancé'
        elif failed == 0:
            health = 'good'
            health_label = f'{passed}/{total_checks} vérifications réussies'
        elif failed <= 2:
            health = 'warning'
            health_label = f'{failed} écart(s) détecté(s)'
        else:
            health = 'critical'
            health_label = f'{failed} problèmes critiques'

        return {
            'audit_date': self.audit_date,
            'files_loaded': self.files_loaded,
            'summary': {
                'total_checks': total_checks,
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'total_variance': round(total_variance, 2),
                'health': health,
                'health_label': health_label,
            },
            'checks': dict(self.checks)
        }

    # ──────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────

    @staticmethod
    def _cell(ws, row, col):
        """Safely read a cell value."""
        try:
            return ws.cell_value(row, col)
        except (IndexError, Exception):
            return None

    @staticmethod
    def _safe_float(value, default=0.0):
        """Safely convert value to float."""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                cleaned = value.replace('$', '').replace(',', '').replace(' ', '').strip()
                if cleaned in ('', '-', 'N/A', 'n/a'):
                    return default
                return float(cleaned)
            return float(value)
        except (ValueError, TypeError):
            return default
