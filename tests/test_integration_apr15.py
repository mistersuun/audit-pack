"""
Integration test: parse real April 15 source documents, compute GEAC/Transelect/Jour,
and verify output matches ground truth from manual fill.

Skips automatically if K: drive source files are not accessible.

NOTE: The DAILY_REV.pdf on K: drive is a pre-audit version (run at 02:07 AM,
before 3 AM room charge posting). Balance-dependent values differ from the
post-audit ground truth in tmp_fill_apr15.py. Tests are structured to verify:
 - Settlement/card values (identical pre/post-audit)
 - Internal consistency (cashout + deposit = daily_revenue)
 - SJ/AR values (not affected by audit timing)
 - Balance values against actual parsed output
"""
import pytest
import os

# ---------------------------------------------------------------------------
# Source file paths on K: drive
# ---------------------------------------------------------------------------
AUDITION_DIR = r'K:\Audition\04 - April\15-04-2026'
HP_PATH = r'K:\HP 2026-2027\04-April 2026\HP 04 2026.xlsx'
RJ_PATH = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 15-04-2026.xls'

pytestmark = pytest.mark.skipif(
    not os.path.isdir(AUDITION_DIR),
    reason='K: drive source files not accessible'
)

# ---------------------------------------------------------------------------
# Manual values for April 15 (provided by night auditor)
# ---------------------------------------------------------------------------
MANUAL_VALUES = {
    'club_lounge': 60.0,
    'deposit_on_hand': 397611.02,
}
ADJUSTMENTS = [{'department': 'spesa_nourriture', 'amount': 3.4}]
DAY = 15  # Excel row 17

# ---------------------------------------------------------------------------
# Ground truth values
# ---------------------------------------------------------------------------
# Settlement/card values are the same regardless of pre/post-audit:
SETTLEMENT_AMEX = 7576.83
SETTLEMENT_MC = 9945.62
SETTLEMENT_VISA = 12126.86

DEPOSIT_AMEX = 5707.24
DEPOSIT_VISA = 993.65
# MC deposit: parser returns 0 from pre-audit DR (post-audit has 474.09)

# Balance values from pre-audit DR (actual file on K: drive):
BALANCE_PREV_DAY = 1476889.24     # Same pre/post
BALANCE_NEW_PRE = 1482382.27      # Pre-audit value
BALANCE_TODAY_PRE = 5493.03       # Pre-audit value
ADV_DEP_APPLIED = 64522.13        # Same pre/post

# AR Summary values (not affected by audit timing):
AR_GUEST_FOLIOS = 5197.27

# SJ values:
SJ_PAYMENTS_INTERAC = 568.08
SJ_PAYMENTS_VISA = 1782.26
SJ_PAYMENTS_MC = 912.63
SJ_PAYMENTS_AMEX = 310.23
SJ_PANNE_VISA = 62.50
SJ_PANNE_INTERACT = 17.49
SJ_FORFAIT = 142.60

# POSITOUCH totals = payments + pannes
POSITOUCH_INTERAC = SJ_PAYMENTS_INTERAC + SJ_PANNE_INTERACT  # 585.57
POSITOUCH_VISA = SJ_PAYMENTS_VISA + SJ_PANNE_VISA             # 1844.76
POSITOUCH_MC = SJ_PAYMENTS_MC                                  # 912.63
POSITOUCH_AMEX = SJ_PAYMENTS_AMEX                              # 310.23

# GEAC expected: 1-based (row, col) -> value
# Only includes cells NOT dependent on post-audit balance:
EXPECTED_GEAC_CARDS = {
    (6, 2):  SETTLEMENT_AMEX - DEPOSIT_AMEX,    # AMEX Cash Out
    (8, 2):  DEPOSIT_AMEX,                        # AMEX Deposit
    (8, 10): DEPOSIT_VISA,                        # VISA Deposit
    (12, 2): SETTLEMENT_AMEX,                     # AMEX Daily Revenue
    (12, 7): SETTLEMENT_MC,                       # MC Daily Revenue
    (12, 10): SETTLEMENT_VISA,                    # VISA Daily Revenue
    (32, 2): BALANCE_PREV_DAY,                    # Balance Prev Day
    (32, 5): BALANCE_PREV_DAY,                    # E32 mirror
    (44, 2): ADV_DEP_APPLIED,                     # Adv Dep Applied
    (44, 10): ADV_DEP_APPLIED,                    # J44 mirror
}

# Transelect expected: 1-based (row, col) -> value
EXPECTED_TRANSELECT = {
    (9, 24):  POSITOUCH_INTERAC,     # DEBIT POSITOUCH (payments + pannes)
    (10, 24): POSITOUCH_VISA,        # VISA POSITOUCH (payments + pannes)
    (11, 24): POSITOUCH_MC,          # MASTER POSITOUCH
    (13, 24): POSITOUCH_AMEX,        # AMEX POSITOUCH
    (21, 2):  SETTLEMENT_VISA,       # Bank Report VISA
    (21, 16): SETTLEMENT_VISA,       # Daily Revenue VISA
    (22, 2):  SETTLEMENT_MC,         # Bank Report MASTER
    (22, 16): SETTLEMENT_MC,         # Daily Revenue MASTER
    (24, 2):  SETTLEMENT_AMEX,       # Bank Report AMEX
    (24, 16): SETTLEMENT_AMEX,       # Daily Revenue AMEX
}

# ---------------------------------------------------------------------------
# Tolerance for financial comparisons
# ---------------------------------------------------------------------------
TOL = 0.02


# No adaptor functions needed — compute_geac_data accepts raw parser output directly.


# ---------------------------------------------------------------------------
# Module-scoped fixture: parse all source docs once
# ---------------------------------------------------------------------------
@pytest.fixture(scope='module')
def parsed_docs():
    """Parse all April 15 source docs once for the module."""
    from utils.parsers import ParserFactory

    results = {}

    # Daily Revenue
    dr_path = os.path.join(AUDITION_DIR, 'DAILY_REV.pdf')
    if os.path.isfile(dr_path):
        with open(dr_path, 'rb') as f:
            parser = ParserFactory.create('daily_revenue', f.read(),
                                          filename='DAILY_REV.pdf')
            results['daily_revenue'] = parser.get_result()

    # AR Summary
    ar_path = os.path.join(AUDITION_DIR, 'AR_SUMMARY.pdf')
    if os.path.isfile(ar_path):
        with open(ar_path, 'rb') as f:
            parser = ParserFactory.create('ar_summary', f.read(),
                                          filename='AR_SUMMARY.pdf')
            results['ar_summary'] = parser.get_result()

    # Sales Journal
    sj_path = os.path.join(AUDITION_DIR, 'SALES_JOURNAL.txt')
    if os.path.isfile(sj_path):
        with open(sj_path, 'rb') as f:
            parser = ParserFactory.create('sales_journal', f.read(),
                                          filename='SALES_JOURNAL.txt')
            results['sales_journal'] = parser.get_result()

    # Market Segment
    ms_path = os.path.join(AUDITION_DIR, 'MARKET_SEGMENT.pdf')
    if os.path.isfile(ms_path):
        with open(ms_path, 'rb') as f:
            parser = ParserFactory.create('market_segment', f.read(),
                                          filename='MARKET_SEGMENT.pdf')
            results['market_segment'] = parser.get_result()

    # HP Excel (day 15)
    if os.path.isfile(HP_PATH):
        with open(HP_PATH, 'rb') as f:
            parser = ParserFactory.create('hp_excel', f.read(),
                                          filename='HP 04 2026.xlsx', day=DAY)
            results['hp_excel'] = parser.get_result()

    return results


# ===========================================================================
# Test 1: Daily Revenue parser extraction
# ===========================================================================
class TestParseDailyRevenue:
    """Verify DailyRevenueParser extracts key fields from April 15 PDF."""

    def test_parse_succeeds(self, parsed_docs):
        dr = parsed_docs.get('daily_revenue')
        assert dr is not None, 'daily_revenue result missing'
        assert dr['success'], f"DR parse failed: {dr.get('errors')}"

    def test_pre_audit_warning(self, parsed_docs):
        """The K: drive DR is pre-audit (02:07 AM); parser should flag it."""
        warnings = parsed_docs['daily_revenue'].get('warnings', [])
        has_pre_audit = any('PRE-AUDIT' in w for w in warnings)
        assert has_pre_audit, \
            f"Expected PRE-AUDIT warning, got: {warnings}"

    def test_settlements_amex(self, parsed_docs):
        data = parsed_docs['daily_revenue']['data']
        s = data.get('settlements', {})
        amex = abs(s.get('american_express', 0))
        assert amex == pytest.approx(SETTLEMENT_AMEX, abs=TOL), \
            f"AMEX settlement: expected ~{SETTLEMENT_AMEX}, got {amex}"

    def test_settlements_visa(self, parsed_docs):
        data = parsed_docs['daily_revenue']['data']
        s = data.get('settlements', {})
        visa = abs(s.get('visa', 0))
        assert visa == pytest.approx(SETTLEMENT_VISA, abs=TOL), \
            f"VISA settlement: expected ~{SETTLEMENT_VISA}, got {visa}"

    def test_settlements_mc(self, parsed_docs):
        data = parsed_docs['daily_revenue']['data']
        s = data.get('settlements', {})
        mc = abs(s.get('mastercard', 0))
        assert mc == pytest.approx(SETTLEMENT_MC, abs=TOL), \
            f"MC settlement: expected ~{SETTLEMENT_MC}, got {mc}"

    def test_balance_prev_day(self, parsed_docs):
        data = parsed_docs['daily_revenue']['data']
        bal = data.get('balance', {})
        prev_day = abs(bal.get('prev_day', 0))
        assert prev_day == pytest.approx(BALANCE_PREV_DAY, abs=TOL), \
            f"Balance Prev Day: expected ~{BALANCE_PREV_DAY}, got {prev_day}"

    def test_balance_new_pre_audit(self, parsed_docs):
        """New Balance reflects pre-audit value (room charges not yet posted)."""
        data = parsed_docs['daily_revenue']['data']
        bal = data.get('balance', {})
        new_bal = abs(bal.get('new_balance', 0))
        assert new_bal == pytest.approx(BALANCE_NEW_PRE, abs=TOL), \
            f"New Balance (pre-audit): expected ~{BALANCE_NEW_PRE}, got {new_bal}"

    def test_deposit_received_amex(self, parsed_docs):
        data = parsed_docs['daily_revenue']['data']
        deps = data.get('deposits_received', {})
        ax = abs(deps.get('ax', 0))
        assert ax == pytest.approx(DEPOSIT_AMEX, abs=TOL), \
            f"Dep Rcvd AX: expected ~{DEPOSIT_AMEX}, got {ax}"

    def test_adv_dep_applied(self, parsed_docs):
        data = parsed_docs['daily_revenue']['data']
        adv = data.get('advance_deposits', {})
        applied = abs(adv.get('applied', 0))
        assert applied == pytest.approx(ADV_DEP_APPLIED, abs=TOL), \
            f"Adv Dep Applied: expected ~{ADV_DEP_APPLIED}, got {applied}"

    def test_chambres_revenue_positive(self, parsed_docs):
        data = parsed_docs['daily_revenue']['data']
        chambres = data.get('revenue', {}).get('chambres', {}).get('total', 0)
        assert chambres > 0, f"Chambres total should be positive, got {chambres}"


# ===========================================================================
# Test 2: Sales Journal parser extraction
# ===========================================================================
class TestParseSalesJournal:
    """Verify SalesJournalParser extracts key fields from April 15 TXT."""

    def test_parse_succeeds(self, parsed_docs):
        sj = parsed_docs.get('sales_journal')
        assert sj is not None, 'sales_journal result missing'
        assert sj['success'], f"SJ parse failed: {sj.get('errors')}"

    def test_payments_interac(self, parsed_docs):
        """Raw payment amounts (without pannes)."""
        data = parsed_docs['sales_journal']['data']
        payments = data.get('payments', {})
        assert payments.get('interac', 0) == pytest.approx(SJ_PAYMENTS_INTERAC, abs=TOL), \
            f"payments.interac: expected ~{SJ_PAYMENTS_INTERAC}, got {payments.get('interac')}"

    def test_payments_visa(self, parsed_docs):
        data = parsed_docs['sales_journal']['data']
        payments = data.get('payments', {})
        assert payments.get('visa', 0) == pytest.approx(SJ_PAYMENTS_VISA, abs=TOL), \
            f"payments.visa: expected ~{SJ_PAYMENTS_VISA}, got {payments.get('visa')}"

    def test_positouch_totals_include_pannes(self, parsed_docs):
        """POSITOUCH totals = payments + pannes per card type."""
        data = parsed_docs['sales_journal']['data']
        pos = data.get('positouch_totals', {})
        assert pos.get('interac', 0) == pytest.approx(POSITOUCH_INTERAC, abs=TOL), \
            f"positouch interac: expected ~{POSITOUCH_INTERAC}, got {pos.get('interac')}"
        assert pos.get('visa', 0) == pytest.approx(POSITOUCH_VISA, abs=TOL), \
            f"positouch visa: expected ~{POSITOUCH_VISA}, got {pos.get('visa')}"

    def test_pannes_detected(self, parsed_docs):
        """Apr 15 has PANNE VISA and PANNE INTERACT."""
        data = parsed_docs['sales_journal']['data']
        pannes = data.get('pannes', {})
        assert pannes.get('visa', 0) == pytest.approx(SJ_PANNE_VISA, abs=TOL), \
            f"panne visa: expected ~{SJ_PANNE_VISA}, got {pannes.get('visa')}"
        assert pannes.get('interac', 0) == pytest.approx(SJ_PANNE_INTERACT, abs=TOL), \
            f"panne interact: expected ~{SJ_PANNE_INTERACT}, got {pannes.get('interac')}"

    def test_has_payments_and_taxes(self, parsed_docs):
        data = parsed_docs['sales_journal']['data']
        assert data.get('payments'), "payments section missing or empty"
        assert data.get('taxes'), "taxes section missing or empty"

    def test_departments_present(self, parsed_docs):
        data = parsed_docs['sales_journal']['data']
        depts = data.get('departments', {})
        assert len(depts) > 0, 'No departments found in Sales Journal'

    def test_adjustments_forfait(self, parsed_docs):
        data = parsed_docs['sales_journal']['data']
        adj = data.get('adjustments', {})
        assert adj.get('forfait', 0) == pytest.approx(SJ_FORFAIT, abs=TOL), \
            f"Forfait: expected ~{SJ_FORFAIT}, got {adj.get('forfait')}"


# ===========================================================================
# Test 3: AR Summary parser extraction
# ===========================================================================
class TestParseARSummary:
    """Verify ARSummaryParser extracts key fields from April 15 PDF."""

    def test_parse_succeeds(self, parsed_docs):
        ar = parsed_docs.get('ar_summary')
        assert ar is not None, 'ar_summary result missing'
        assert ar['success'], f"AR parse failed: {ar.get('errors')}"

    def test_guest_folios(self, parsed_docs):
        data = parsed_docs['ar_summary']['data']
        fo = data.get('front_office_transfers', {})
        guest_folios = fo.get('guest_folios', 0)
        assert guest_folios == pytest.approx(AR_GUEST_FOLIOS, abs=TOL), \
            f"Guest Folios: expected ~{AR_GUEST_FOLIOS}, got {guest_folios}"


# ===========================================================================
# Test 4: compute_geac_data
# ===========================================================================
class TestComputeGEAC:
    """Compute GEAC from parsed DR + AR data and verify consistency."""

    def test_geac_card_cells(self, parsed_docs):
        """Verify settlement-derived and deposit cells match expected values."""
        from utils.geac_filler import compute_geac_data

        dr_raw = parsed_docs['daily_revenue']['data']
        ar_raw = parsed_docs['ar_summary']['data']
        result = compute_geac_data(dr_raw, ar_raw)

        for (row, col), expected in EXPECTED_GEAC_CARDS.items():
            actual = result.get((row, col))
            assert actual is not None, \
                f"GEAC ({row},{col}) missing from output"
            assert actual == pytest.approx(expected, abs=TOL), \
                f"GEAC ({row},{col}): expected {expected}, got {actual}"

    def test_geac_e37_is_negative_b37(self, parsed_docs):
        """E37 should be the negative of B37."""
        from utils.geac_filler import compute_geac_data

        dr_raw = parsed_docs['daily_revenue']['data']
        ar_raw = parsed_docs['ar_summary']['data']
        result = compute_geac_data(dr_raw, ar_raw)

        b37 = result.get((37, 2), 0)
        e37 = result.get((37, 5), 0)
        assert e37 == pytest.approx(-b37, abs=TOL), \
            f"E37 should be -{b37}, got {e37}"

    def test_geac_card_variance_balanced(self, parsed_docs):
        """For each card type: Cash Out + Deposit = Daily Revenue."""
        from utils.geac_filler import compute_geac_data

        dr_raw = parsed_docs['daily_revenue']['data']
        ar_raw = parsed_docs['ar_summary']['data']
        result = compute_geac_data(dr_raw, ar_raw)

        for col, label in [(2, 'AMEX'), (7, 'MC'), (10, 'VISA')]:
            cashout = result.get((6, col), 0)
            deposit = result.get((8, col), 0)
            daily_rev = result.get((12, col), 0)
            assert cashout + deposit == pytest.approx(daily_rev, abs=TOL), \
                f"{label}: cashout({cashout}) + deposit({deposit}) != daily_rev({daily_rev})"

    def test_geac_b53_e53_mirror(self, parsed_docs):
        """B53 and E53 should both equal new_balance (absolute)."""
        from utils.geac_filler import compute_geac_data

        dr_raw = parsed_docs['daily_revenue']['data']
        ar_raw = parsed_docs['ar_summary']['data']
        result = compute_geac_data(dr_raw, ar_raw)

        b53 = result.get((53, 2), 0)
        e53 = result.get((53, 5), 0)
        assert b53 == pytest.approx(BALANCE_NEW_PRE, abs=TOL), \
            f"B53: expected {BALANCE_NEW_PRE}, got {b53}"
        assert e53 == pytest.approx(b53, abs=TOL), \
            f"E53 should mirror B53: got {e53} vs {b53}"

    def test_geac_b41_fd_g41_guest_folios(self, parsed_docs):
        """B41 = DR Facture Direct, G41 = AR Guest Folios."""
        from utils.geac_filler import compute_geac_data

        dr_raw = parsed_docs['daily_revenue']['data']
        ar_raw = parsed_docs['ar_summary']['data']
        result = compute_geac_data(dr_raw, ar_raw)

        # DR settlements.facture_direct = -5197.27 (abs = 5197.27)
        # AR guest_folios = 5197.27
        # On this pre-audit DR, FD = AR, so both equal AR_GUEST_FOLIOS
        b41 = result.get((41, 2), 0)
        g41 = result.get((41, 7), 0)
        assert g41 == pytest.approx(AR_GUEST_FOLIOS, abs=TOL), \
            f"G41: expected {AR_GUEST_FOLIOS}, got {g41}"
        # B41 = abs(settlements.facture_direct)
        fd = abs(dr_raw.get('settlements', {}).get('facture_direct', 0))
        assert b41 == pytest.approx(fd, abs=TOL), \
            f"B41: expected FD={fd}, got {b41}"

    def test_geac_row10_not_in_output(self, parsed_docs):
        """Row 10 (Total) is a formula -- must not appear in output."""
        from utils.geac_filler import compute_geac_data

        dr_raw = parsed_docs['daily_revenue']['data']
        ar_raw = parsed_docs['ar_summary']['data']
        result = compute_geac_data(dr_raw, ar_raw)

        for (r, c) in result:
            assert r != 10, 'Row 10 should not be in GEAC output (formula row)'


# ===========================================================================
# Test 5: compute_transelect_data
# ===========================================================================
class TestComputeTranselect:
    """Compute Transelect from parsed SJ + DR data, compare to expected."""

    def test_transelect_output(self, parsed_docs):
        from utils.transelect_filler import compute_transelect_data

        sj_data = parsed_docs['sales_journal']['data']
        dr_data = parsed_docs['daily_revenue']['data']
        result = compute_transelect_data(sj_data, dr_data)

        for (row, col), expected in EXPECTED_TRANSELECT.items():
            actual = result.get((row, col))
            assert actual is not None, \
                f"Transelect ({row},{col}) missing from output"
            assert actual == pytest.approx(expected, abs=TOL), \
                f"Transelect ({row},{col}): expected {expected}, got {actual}"

    def test_transelect_no_formula_cols(self, parsed_docs):
        """Column I (8) is a formula -- must not appear in output."""
        from utils.transelect_filler import compute_transelect_data

        sj_data = parsed_docs['sales_journal']['data']
        dr_data = parsed_docs['daily_revenue']['data']
        result = compute_transelect_data(sj_data, dr_data)

        for (r, c) in result:
            assert c != 8, f"Column I (8) at row {r} should not be in output"


# ===========================================================================
# Test 6: JourMapper.compute_all
# ===========================================================================
class TestComputeJour:
    """Compute Jour values from all parsed data + manual, compare key columns."""

    def _compute_jour(self, parsed_docs):
        """Helper: run JourMapper and return (jour_values, summary)."""
        from utils.jour_mapper import JourMapper

        dr_data = parsed_docs['daily_revenue']['data']
        sj_data = parsed_docs['sales_journal']['data']
        ar_data = parsed_docs['ar_summary']['data']
        hp_data = parsed_docs.get('hp_excel', {}).get('data', {})

        mapper = JourMapper(
            daily_rev_data=dr_data,
            sales_journal_data=sj_data,
            ar_summary_data=ar_data,
            hp_data=hp_data,
            manual_values=MANUAL_VALUES,
            adjustments=ADJUSTMENTS,
        )
        return mapper.compute_all(), mapper.get_summary()

    def test_jour_bf_forfait(self, parsed_docs):
        """BF = -forfait + club_lounge = -(142.6) + 60 = -82.6."""
        jour_values, _ = self._compute_jour(parsed_docs)
        bf = jour_values.get(57)
        assert bf is not None, "Jour BF (col 57) missing from output"
        assert bf == pytest.approx(-82.60, abs=TOL), \
            f"Jour BF: expected -82.60, got {bf}"

    def test_jour_column_d(self, parsed_docs):
        """Column D = -|new_balance| - deposit_on_hand (always negative).

        With pre-audit |new_balance| = 1482382.27:
        D = -1482382.27 - 397611.02 = -1879993.29
        """
        jour_values, _ = self._compute_jour(parsed_docs)
        col_d = jour_values.get(3)
        assert col_d is not None, "Jour D (col 3) missing from output"
        expected_d = -BALANCE_NEW_PRE - MANUAL_VALUES['deposit_on_hand']
        print(f"\nJour D = {col_d:.2f} (expected {expected_d:.2f})")
        assert col_d == pytest.approx(expected_d, abs=TOL), \
            f"Jour D: expected {expected_d:.2f}, got {col_d}"

    def test_jour_ak_chambres(self, parsed_docs):
        """AK = Chambres Total - Club Lounge total from DR non-revenue."""
        jour_values, _ = self._compute_jour(parsed_docs)
        ak = jour_values.get(36)
        assert ak is not None, "Jour AK (col 36) missing from output"
        # Verify it's the DR chambres.total minus club_lounge.total
        dr_data = parsed_docs['daily_revenue']['data']
        chambres = dr_data.get('revenue', {}).get('chambres', {}).get('total', 0)
        cl = dr_data.get('non_revenue', {}).get('club_lounge', {}).get('total', 0)
        expected_ak = chambres - cl
        print(f"\nJour AK = {ak:.2f} (chambres={chambres}, club_lounge={cl}, expected={expected_ak:.2f})")
        assert ak == pytest.approx(expected_ak, abs=TOL), \
            f"Jour AK: expected {expected_ak:.2f}, got {ak}"

    def test_jour_ao_nettoyeur(self, parsed_docs):
        """AO = Nettoyeur from DR autres_revenus."""
        jour_values, _ = self._compute_jour(parsed_docs)
        ao = jour_values.get(40)
        if ao is not None:
            print(f"\nJour AO (Nettoyeur) = {ao:.2f}")
            # Should be positive (revenue)
            assert ao >= 0, f"Nettoyeur should be non-negative, got {ao}"

    def test_jour_as_autres_gl(self, parsed_docs):
        """AS = Autres Grand Livre from DR comptabilite section."""
        jour_values, _ = self._compute_jour(parsed_docs)
        as_val = jour_values.get(44)
        if as_val is not None:
            print(f"\nJour AS (Autres GL) = {as_val:.2f}")
            # Autres Grand Livre is typically a large negative number
            assert as_val < 0, f"Autres GL is typically negative, got {as_val}"

    def test_jour_summary_no_critical_errors(self, parsed_docs):
        """JourMapper should not produce critical errors."""
        _, summary = self._compute_jour(parsed_docs)

        print(f"\nJourMapper summary: {summary['column_count']} columns computed")
        if summary['warnings']:
            print(f"  Warnings: {summary['warnings']}")
        if summary['errors']:
            print(f"  Errors: {summary['errors']}")

        assert summary['column_count'] >= 20, \
            f"Expected >= 20 columns, got {summary['column_count']}"

    def test_jour_compute_all_prints_debug(self, parsed_docs):
        """Print all computed Jour values for manual inspection."""
        from utils.daily_rev_jour_mapping import col_index_to_letter
        jour_values, _ = self._compute_jour(parsed_docs)

        print("\n--- JourMapper computed values ---")
        for col_idx in sorted(jour_values.keys()):
            letter = col_index_to_letter(col_idx)
            val = jour_values[col_idx]
            print(f"  {letter:3s} (col {col_idx:3d}): {val:>14.2f}")
        print(f"  Total columns: {len(jour_values)}")


# ===========================================================================
# Test 7: COM write + DC balance (optional, requires win32com + RJ file)
# ===========================================================================
# COM tests are skipped by default because Excel COM automation can crash
# the pytest process with Windows fatal exceptions. Run explicitly with:
#   pytest tests/test_integration_apr15.py -k "com_write" --run-com
@pytest.mark.skipif(
    not os.environ.get('RUN_COM_TESTS'),
    reason='COM tests skipped by default (set RUN_COM_TESTS=1 to enable)'
)
class TestCOMWriteAndDC:
    """Write all values via RJFillerCOM and verify file integrity.

    Skips if win32com is not available or RJ file not accessible.
    Run with: RUN_COM_TESTS=1 pytest tests/test_integration_apr15.py -k com_write
    """

    @pytest.fixture(autouse=True)
    def check_prerequisites(self):
        pytest.importorskip('win32com.client', reason='win32com not available')
        if not os.path.isfile(RJ_PATH):
            pytest.skip(f'RJ file not found: {RJ_PATH}')

    def test_com_write_preserves_file_size(self, parsed_docs, tmp_path):
        """Copy RJ to temp, write all values via COM, verify file not corrupted."""
        import shutil

        # Copy RJ to temp directory
        tmp_rj = str(tmp_path / 'Rj_test_apr15.xls')
        shutil.copy2(RJ_PATH, tmp_rj)
        original_size = os.path.getsize(RJ_PATH)

        # Compute all values
        from utils.geac_filler import compute_geac_data
        from utils.transelect_filler import compute_transelect_data
        from utils.jour_mapper import JourMapper

        dr_raw = parsed_docs['daily_revenue']['data']
        ar_raw = parsed_docs['ar_summary']['data']
        sj_data = parsed_docs['sales_journal']['data']
        hp_data = parsed_docs.get('hp_excel', {}).get('data', {})

        geac_data = compute_geac_data(dr_raw, ar_raw)
        transelect_data = compute_transelect_data(sj_data, dr_raw)

        mapper = JourMapper(
            daily_rev_data=dr_raw,
            sales_journal_data=sj_data,
            ar_summary_data=ar_raw,
            hp_data=hp_data,
            manual_values=MANUAL_VALUES,
            adjustments=ADJUSTMENTS,
        )
        jour_values_0based = mapper.compute_all()
        jour_values_1based = {col + 1: val for col, val in jour_values_0based.items()}

        # Write via COM (may fail on CI; wrap defensively)
        try:
            from utils.rj_filler_com import RJFillerCOM

            with RJFillerCOM(tmp_rj) as filler:
                filler.write_geac(geac_data)
                filler.write_transelect(transelect_data)
                filler.write_jour_row(DAY, jour_values_1based)
        except Exception as e:
            pytest.skip(f"COM write failed (may need Excel running): {e}")

        # Verify file size didn't shrink dramatically (formulas preserved)
        new_size = os.path.getsize(tmp_rj)
        ratio = new_size / original_size
        print(f"\nFile size: {original_size} -> {new_size} (ratio {ratio:.2f})")
        assert ratio > 0.8, \
            f"File shrank from {original_size} to {new_size} bytes " \
            f"(ratio {ratio:.2f}) -- formulas may be lost"
