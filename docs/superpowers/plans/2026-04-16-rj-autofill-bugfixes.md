# RJ Auto-Fill Bugfixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 9 bugs in the RJ auto-fill pipeline so that computed Jour column values match the authoritative spec at `docs/RJ_AUTOFILL_MASTER.md`.

**Architecture:** Two independent streams — Stream A fixes parsers (`utils/parsers/`), Stream B fixes column mappings (`utils/daily_rev_jour_mapping.py`). Both streams produce testable, isolated changes.

**Tech Stack:** Python 3, pdfplumber, xlrd, openpyxl, pytest

---

## File Map

| File | Changes | Responsibility |
|---|---|---|
| `utils/parsers/daily_revenue_parser.py` | Resolve merge conflicts, add InterHotel XferIn extraction, add Autre A Payer Taxable, add DR timestamp validation | Stream A |
| `utils/parsers/sales_journal_parser.py` | Add PANNE accumulation into card type POSITOUCH values | Stream A |
| `utils/daily_rev_jour_mapping.py` | Fix AP, AX, AY, AW, CF column mappings | Stream B |
| `tests/test_mapping_fixes.py` | New: tests for corrected column mappings | Stream B |
| `tests/test_parser_fixes.py` | New: tests for parser fixes | Stream A |

---

## Stream A: Parser Fixes

### Task 1: Resolve merge conflicts in DailyRevenueParser

**Files:**
- Modify: `utils/parsers/daily_revenue_parser.py:193-434`

The file has 4 merge conflict blocks. The correct resolution: keep the **newer branch** code (after `=======`) which adds F&B restaurant tax extraction AND page-specific text parsing. The HEAD branch is the older, less complete version.

- [ ] **Step 1: Identify all conflict markers**

Search for `<<<<<<<`, `=======`, `>>>>>>>` in the file. There are 4 blocks:
- Line ~193: `fax` field in autres_revenus (keep newer: adds fax extraction)
- Line ~279-283: Club Lounge end marker (keep newer: `'DO NOT USE'` uppercase)
- Line ~290-342: F&B tax sections vs Debourse (keep newer: adds F&B tax extraction + Debourse)
- Line ~350-432: Autres tax sections + total_tvq/total_tps (keep newer: page-specific parsing + includes F&B in totals)

- [ ] **Step 2: Resolve conflict block 1 (fax field)**

In `_parse_revenue_departments`, around line 193, replace the conflict block with the newer version:

```python
            'fax': self._get_today(ar_text, 'Fax & Photocopies') if ar_text else 0.0,
            'machine_distributrice': self._get_today(ar_text, 'MACHINE DISTRIBUTRIC'),
            'autre_a_payer_taxable': self._get_today(ar_text, 'Autre A Payer Taxabl'),
            'total': self._get_section_total(text12, 'Autres Revenus'),
```

Note: also add `autre_a_payer_taxable` extraction here (needed for BC column).

- [ ] **Step 3: Resolve conflict block 2 (Club Lounge)**

Replace the conflict block with:

```python
        cl_text = self._get_between(non_rev_text, 'Club Lounge', 'DO NOT USE')
```

- [ ] **Step 4: Resolve conflict block 3 (F&B tax sections + Debourse)**

Keep the newer branch code that adds Restaurant Piazza, Services Chambres, Banquet, La Spesa tax extraction. Then the Debourse section follows.

Delete lines from `<<<<<<< HEAD` through `=======` (the old HEAD code that only had `# Debourse`).
Delete the `>>>>>>> 324e10b...` marker line after the newer code block.

- [ ] **Step 5: Resolve conflict block 4 (Autres tax + totals)**

Keep the newer branch code that:
- Uses `p5` (page 5 text) for Autres tax parsing
- Uses `'TVQ Autres'` and `'TPS Autres'` labels (more specific)
- Includes F&B restaurant taxes in `total_tvq` / `total_tps` aggregates

Delete the HEAD version and conflict markers.

- [ ] **Step 6: Verify no remaining conflict markers**

```bash
grep -n "<<<<<<\|======\|>>>>>>" utils/parsers/daily_revenue_parser.py
```

Expected: no output (all conflicts resolved).

- [ ] **Step 7: Run existing tests**

```bash
pytest tests/ -v --tb=short 2>&1 | head -50
```

Expected: no new failures from conflict resolution.

- [ ] **Step 8: Commit**

```bash
git add utils/parsers/daily_revenue_parser.py
git commit -m "fix: resolve merge conflicts in DailyRevenueParser"
```

---

### Task 2: Add InterHotel XferIn extraction to DailyRevenueParser

**Files:**
- Modify: `utils/parsers/daily_revenue_parser.py` (in `_parse_balance` method)
- Test: `tests/test_parser_fixes.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_parser_fixes.py`:

```python
"""Tests for parser bugfixes per docs/RJ_AUTOFILL_MASTER.md."""


def test_interhotel_extracted_from_balance():
    """InterHotel XferIn must be extracted from DR page 7."""
    # Simulate a DR page 7 text with InterHotel
    from utils.parsers.daily_revenue_parser import DailyRevenueParser
    # We test the _get_today helper directly with known text
    parser = DailyRevenueParser(b'', filename='test.pdf')
    text = "InterHotel XferIn 19.98 329.65 0.00 549.45"
    val = parser._get_today(text, 'InterHotel XferIn')
    assert val == 19.98, f"Expected 19.98, got {val}"
```

- [ ] **Step 2: Run test to verify it passes (helper already works)**

```bash
pytest tests/test_parser_fixes.py::test_interhotel_extracted_from_balance -v
```

Expected: PASS (the `_get_today` helper already handles this pattern).

- [ ] **Step 3: Add InterHotel to _parse_balance method**

Find the `_parse_balance` method in `daily_revenue_parser.py`. Add after the existing balance extractions:

```python
        # InterHotel XferIn (page 7) — needed for AW (Internet) column
        balance['interhotel_xferin'] = self._get_today(p7, 'InterHotel XferIn')
```

- [ ] **Step 4: Add Adv Dep DNA extraction if missing**

In the same `_parse_balance` method, ensure DNA is extracted:

```python
        balance['adv_dep_dna'] = self._get_today(p7, 'Adv Dep DNA')
```

- [ ] **Step 5: Commit**

```bash
git add utils/parsers/daily_revenue_parser.py tests/test_parser_fixes.py
git commit -m "feat: extract InterHotel XferIn and Adv Dep DNA from DR page 7"
```

---

### Task 3: Add PANNE accumulation to SalesJournalParser

**Files:**
- Modify: `utils/parsers/sales_journal_parser.py` (in `_parse_adjustments` or `_parse_payments`)
- Test: `tests/test_parser_fixes.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_parser_fixes.py`:

```python
def test_panne_accumulated_into_card_type():
    """PANNE VISA must be added to VISA for POSITOUCH values."""
    from utils.parsers.sales_journal_parser import SalesJournalParser

    sj_text = b"""HOTEL SHERATON LAVAL                                                   PAGE:   1
REPORT DATE: 04/15/2026                                 REPORT TIME:  1:07:16.86
--------------------------------------------------------------------------------
                      SALES JOURNAL REPORT FOR 04/15/2026
                         SALES JOURNAL for Entire house
Account #         Account Name               Debits      Credits
--------------------------------------------------------------------------------
                 PIAZZA
                  NOURRITURE                             2828.50

                  TPS                                    1950.85
                  TVQ                                    3891.46

                                               0.00
                  COMPTANT                                640.92

                  VISA                      1782.26
                  MASTERCARD                 912.63
                  AMEX                       310.23
                  INTERAC                    568.08
                  CHAMBRE                  41791.03
                  PANNE VISA                  62.50
                  PANNE INTERACT              17.49
                  ADMINISTRATION             348.58
                  HOTEL PROMOTION            101.50
                  FORFAIT                    142.60
                  PANNE LIEN HOTEL             9.00

                  POURBOIRE CHARGE           817.97       817.97

                                         ----------   ----------
                                           53392.62 *   53392.62 *
"""
    parser = SalesJournalParser(sj_text, filename='test_sj.txt')
    parser.parse()
    result = parser.get_result()

    payments = result['data'].get('payments', {})
    adjustments = result['data'].get('adjustments', {})

    # POSITOUCH values = card + panne
    positouch = result['data'].get('positouch_totals', {})
    assert positouch.get('visa', 0) == 1782.26 + 62.50, "VISA POSITOUCH should include PANNE VISA"
    assert positouch.get('interac', 0) == 568.08 + 17.49, "INTERAC POSITOUCH should include PANNE INTERACT"
    assert positouch.get('mastercard', 0) == 912.63, "MC POSITOUCH unchanged (no panne)"
    assert positouch.get('amex', 0) == 310.23, "AMEX POSITOUCH unchanged (no panne)"

    # Panne amounts tracked separately
    pannes = result['data'].get('pannes', {})
    assert pannes.get('visa', 0) == 62.50
    assert pannes.get('interac', 0) == 17.49
    assert pannes.get('lien_hotel', 0) == 9.00
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_parser_fixes.py::test_panne_accumulated_into_card_type -v
```

Expected: FAIL — `positouch_totals` key doesn't exist yet.

- [ ] **Step 3: Add PANNE extraction to _parse_adjustments**

In `sales_journal_parser.py`, modify `_parse_adjustments` to also extract PANNE amounts:

```python
        # PANNE amounts — failed terminal transactions still in POS
        panne_items = {
            'panne_visa': r'PANNE VISA\s+(\d[\d,]*\.\d+)',
            'panne_master': r'PANNE MASTER\s+(\d[\d,]*\.\d+)',
            'panne_amex': r'PANNE AMEX\s+(\d[\d,]*\.\d+)',
            'panne_interact': r'PANNE INTERACT\s+(\d[\d,]*\.\d+)',
            'panne_lien_hotel': r'PANNE LIEN HOTEL\s+(\d[\d,]*\.\d+)',
        }

        pannes = {}
        for key, pattern in panne_items.items():
            match = re.search(pattern, page2)
            if not match:
                match = re.search(pattern, text)  # fallback to full text
            if match:
                pannes[key] = float(match.group(1).replace(',', ''))

        adjustments['pannes'] = pannes
```

- [ ] **Step 4: Add positouch_totals computation to extracted_data**

In the `parse()` method, after building `self.extracted_data`, add:

```python
            # Compute POSITOUCH totals = card payment + matching PANNE per card type
            pannes = adjustments.get('pannes', {})
            self.extracted_data['pannes'] = {
                'visa': pannes.get('panne_visa', 0),
                'mastercard': pannes.get('panne_master', 0),
                'amex': pannes.get('panne_amex', 0),
                'interac': pannes.get('panne_interact', 0),
                'lien_hotel': pannes.get('panne_lien_hotel', 0),
            }
            self.extracted_data['positouch_totals'] = {
                'visa': payments.get('visa', 0) + pannes.get('panne_visa', 0),
                'mastercard': payments.get('mastercard', 0) + pannes.get('panne_master', 0),
                'amex': payments.get('amex', 0) + pannes.get('panne_amex', 0),
                'interac': payments.get('interac', 0) + pannes.get('panne_interact', 0),
            }
```

- [ ] **Step 5: Run test**

```bash
pytest tests/test_parser_fixes.py::test_panne_accumulated_into_card_type -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add utils/parsers/sales_journal_parser.py tests/test_parser_fixes.py
git commit -m "feat: accumulate PANNE amounts into card POSITOUCH totals in SalesJournalParser"
```

---

### Task 4: Add DR timestamp validation

**Files:**
- Modify: `utils/parsers/daily_revenue_parser.py` (in `_extract_metadata`)
- Test: `tests/test_parser_fixes.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_parser_fixes.py`:

```python
def test_pre_audit_dr_warning():
    """DR run before 3AM should generate a validation warning."""
    from utils.parsers.daily_revenue_parser import DailyRevenueParser

    parser = DailyRevenueParser(b'', filename='test.pdf')
    # Simulate metadata extraction
    parser.extracted_data = {}
    parser._check_timestamp_validity("15-APR-2026 12:59 AM")
    assert any('pre-audit' in w.lower() for w in parser.validation_warnings), \
        "Should warn about pre-audit timestamp"

    parser.validation_warnings = []
    parser._check_timestamp_validity("15-APR-2026 03:28 AM")
    assert not any('pre-audit' in w.lower() for w in parser.validation_warnings), \
        "Post-audit timestamp should not warn"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_parser_fixes.py::test_pre_audit_dr_warning -v
```

Expected: FAIL — `_check_timestamp_validity` doesn't exist.

- [ ] **Step 3: Implement timestamp validation**

Add to `daily_revenue_parser.py`:

```python
    def _check_timestamp_validity(self, timestamp_str):
        """Warn if DR was run before 3:00 AM (pre-audit, missing room charges).

        A pre-audit DR will be missing ~$50K+ of room charges, taxes, and
        balance data. See docs/RJ_AUTOFILL_MASTER.md section 1b.
        """
        try:
            # Parse "DD-MMM-YYYY HH:MM AM/PM" format
            dt = datetime.strptime(timestamp_str.strip(), "%d-%b-%Y %I:%M %p")
            if dt.hour < 3:
                self.validation_warnings.append(
                    f"PRE-AUDIT WARNING: DR timestamp {timestamp_str} is before 3:00 AM. "
                    f"Room charges, taxes, and balance data may be incomplete. "
                    f"Request the post-audit version."
                )
        except (ValueError, AttributeError):
            pass  # Can't parse timestamp — don't block
```

- [ ] **Step 4: Wire into _extract_metadata**

In `_extract_metadata`, after extracting the timestamp:

```python
        # Check for pre-audit timestamp
        ts_match = re.search(r'(\d{2}-\w{3}-\d{4}\s+\d{1,2}:\d{2}\s+[AP]M)', self.raw_text)
        if ts_match:
            self.extracted_data['report_timestamp'] = ts_match.group(1)
            self._check_timestamp_validity(ts_match.group(1))
```

- [ ] **Step 5: Run test**

```bash
pytest tests/test_parser_fixes.py::test_pre_audit_dr_warning -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add utils/parsers/daily_revenue_parser.py tests/test_parser_fixes.py
git commit -m "feat: add pre-audit DR timestamp validation warning"
```

---

## Stream B: Column Mapping Fixes

### Task 5: Fix AP column (GEAC compensation)

**Files:**
- Modify: `utils/daily_rev_jour_mapping.py:138-149`
- Test: `tests/test_mapping_fixes.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_mapping_fixes.py`:

```python
"""Tests for column mapping fixes per docs/RJ_AUTOFILL_MASTER.md."""
from utils.daily_rev_jour_mapping import DAILY_REV_TO_JOUR


def test_ap_is_geac_compensation_not_machine_distributrice():
    """AP (col 41) must be GEAC compensation = -(FD - AR Guest Folios), NOT vending machines."""
    ap = DAILY_REV_TO_JOUR['AP']
    assert ap['column_index'] == 41
    # Must NOT reference machine_distributrice
    assert 'machine_distributrice' not in str(ap.get('base_field', ''))
    assert 'machine_distributrice' not in str(ap.get('accumulator_fields', ''))
    # Must reference GEAC/AR fields
    desc = ap.get('description', '').lower()
    assert 'geac' in desc or 'ar' in desc or 'facture direct' in desc, \
        f"AP description should mention GEAC/AR, got: {ap.get('description')}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_mapping_fixes.py::test_ap_is_geac_compensation_not_machine_distributrice -v
```

Expected: FAIL — AP currently references machine_distributrice.

- [ ] **Step 3: Fix AP mapping**

In `utils/daily_rev_jour_mapping.py`, replace the AP entry (around line 138):

```python
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
        'note': 'Requires both DR Facture Direct and AR Summary Guest Folios. See docs/RJ_AUTOFILL_MASTER.md section 7.3'
    },
```

- [ ] **Step 4: Run test**

```bash
pytest tests/test_mapping_fixes.py::test_ap_is_geac_compensation_not_machine_distributrice -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/daily_rev_jour_mapping.py tests/test_mapping_fixes.py
git commit -m "fix: AP column (41) now maps to GEAC compensation, not machine distributrice"
```

---

### Task 6: Fix AX/AY tax accumulators (remove F&B OPERA taxes)

**Files:**
- Modify: `utils/daily_rev_jour_mapping.py:251-302`
- Test: `tests/test_mapping_fixes.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_mapping_fixes.py`:

```python
def test_ax_ay_exclude_fb_opera_taxes():
    """AX (TVQ) and AY (TPS) must NOT include F&B OPERA taxes (Piazza/Bqt/Spesa/ServCh).

    These are already captured in sales_journal.taxes.tvq/tps.
    Including them would double-count ~$3,771 (real example April 14, 2026).
    See docs/RJ_AUTOFILL_MASTER.md section 7.3 AX/AY rules.
    """
    ay = DAILY_REV_TO_JOUR['AY']
    ax = DAILY_REV_TO_JOUR['AX']

    fb_opera_fields = [
        'non_revenue.restaurant_piazza.tps',
        'non_revenue.restaurant_piazza.tvq',
        'non_revenue.banquet.tps',
        'non_revenue.banquet.tvq',
        'non_revenue.la_spesa.tps',
        'non_revenue.la_spesa.tvq',
        'non_revenue.services_chambres.tps',
        'non_revenue.services_chambres.tvq',
    ]

    for field in fb_opera_fields:
        if 'tps' in field:
            assert field not in ay.get('accumulator_fields', []), \
                f"AY should NOT include {field} (F&B OPERA tax double-count)"
        if 'tvq' in field:
            assert field not in ax.get('accumulator_fields', []), \
                f"AX should NOT include {field} (F&B OPERA tax double-count)"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_mapping_fixes.py::test_ax_ay_exclude_fb_opera_taxes -v
```

Expected: FAIL — AX/AY currently include F&B OPERA tax fields.

- [ ] **Step 3: Fix AY accumulator**

In `utils/daily_rev_jour_mapping.py`, replace AY's `accumulator_fields` (around line 258):

```python
        'accumulator_fields': [
            # DR Non-Revenue taxes (Chambres + Autres + Internet + Telephones)
            'non_revenue.chambres_tax.tps',
            'non_revenue.telephones_tax.tps_local',
            'non_revenue.telephones_tax.tps_interurbain',
            'non_revenue.autres_tax.tps_autres',
            'non_revenue.internet_nonrev.tps',
            # Sales Journal POS taxes (covers ALL F&B — do NOT add DR F&B OPERA taxes here)
            'sales_journal.taxes.tps',
            # DR Comptabilite TPS (if present)
            'non_revenue.comptabilite_nonrev.tps',
        ],
```

- [ ] **Step 4: Fix AX accumulator**

Replace AX's `accumulator_fields` (around line 284):

```python
        'accumulator_fields': [
            # DR Non-Revenue taxes (Chambres + Autres + Internet + Telephones)
            'non_revenue.chambres_tax.tvq',
            'non_revenue.telephones_tax.tvq_local',
            'non_revenue.telephones_tax.tvq_interurbain',
            'non_revenue.autres_tax.tvq_autres',
            'non_revenue.internet_nonrev.tvq',
            # Sales Journal POS taxes (covers ALL F&B — do NOT add DR F&B OPERA taxes here)
            'sales_journal.taxes.tvq',
        ],
```

- [ ] **Step 5: Run test**

```bash
pytest tests/test_mapping_fixes.py::test_ax_ay_exclude_fb_opera_taxes -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add utils/daily_rev_jour_mapping.py tests/test_mapping_fixes.py
git commit -m "fix: remove F&B OPERA taxes from AX/AY accumulators (prevents $3,771 double-count)"
```

---

### Task 7: Fix CF column (Transfer to A/R)

**Files:**
- Modify: `utils/daily_rev_jour_mapping.py:354-370`
- Test: `tests/test_mapping_fixes.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_mapping_fixes.py`:

```python
def test_cf_uses_ar_guest_folios_minus_payments_minus_ar_misc():
    """CF (col 83) = AR Guest Folios - AR Payments - DR AR Misc.

    NOT simply DR Facture Direct or AR aggregates.
    See docs/RJ_AUTOFILL_MASTER.md section 7.3 CF rule.
    Confirmed from Jour cell header note: 'Total Transfers (AR summary Report)
    - Payments (AR summary Report) - AR Misc (Daily Revenue Report page 2)'
    """
    cf = DAILY_REV_TO_JOUR['CF']
    assert cf['column_index'] == 83
    desc = cf.get('description', '') + cf.get('note', '') + cf.get('formula', '')
    # Must mention Guest Folios/Total Transfers AND Payments AND AR Misc
    desc_lower = desc.lower()
    assert 'payment' in desc_lower or 'subtract' in desc_lower, \
        f"CF must reference AR Payments subtraction, got: {desc}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_mapping_fixes.py::test_cf_uses_ar_guest_folios_minus_payments_minus_ar_misc -v
```

Expected: FAIL.

- [ ] **Step 3: Fix CF mapping**

Replace the CF entry in `daily_rev_jour_mapping.py`:

```python
    'CF': {
        'column_index': 83,
        'label_en': 'Transfer to A/R',
        'label_fr': 'Transfer to A/R',
        'source_page': 'AR Summary + PAGE 2',
        'source_line': 'AR Guest Folios - AR Payments - DR AR Misc',
        'operation': 'cf_transfer',
        'formula': 'ar_guest_folios - ar_payments - dr_ar_misc',
        'accumulator_fields': [
            'balance.front_office_transfers',      # AR Guest Folios (positive)
            '-balance.ar_payments',                 # AR Payments (subtract)
            '-non_revenue.ar_activity.total',       # DR AR Misc (subtract)
        ],
        'description': 'CF = AR Summary Guest Folios - AR Summary Payments - DR p.2 AR Misc. '
                       'From Jour cell header: "Total Transfers (AR summary Report) '
                       '- Payments (AR summary Report) - AR Misc (Daily Revenue Report page 2)"',
        'sign_handling': 'keep_sign',
        'note': 'When Guest Folios = DR FD and Payments = 0 and AR Misc = 0, CF simplifies to DR FD. '
                'But the full formula must always be used. See docs/RJ_AUTOFILL_MASTER.md.'
    },
```

- [ ] **Step 4: Run test**

```bash
pytest tests/test_mapping_fixes.py::test_cf_uses_ar_guest_folios_minus_payments_minus_ar_misc -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/daily_rev_jour_mapping.py tests/test_mapping_fixes.py
git commit -m "fix: CF column uses AR Guest Folios - Payments - AR Misc formula"
```

---

### Task 8: Fix AW column (Internet = 3 components)

**Files:**
- Modify: `utils/daily_rev_jour_mapping.py:199-210`
- Test: `tests/test_mapping_fixes.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_mapping_fixes.py`:

```python
def test_aw_has_three_components():
    """AW (Internet, col 48) = DR Internet + SJ Bqt Internet + InterHotel XferIn.

    All 3 components required. DR Internet is often negative.
    See docs/RJ_AUTOFILL_MASTER.md section 10.1.
    Real example April 15: AW = -17.38 + 460 + 19.98 = 462.60
    """
    aw = DAILY_REV_TO_JOUR['AW']
    assert aw['column_index'] == 48

    # Must be an accumulator with 3 fields, not a single 'direct' field
    assert aw['operation'] == 'accumulate', \
        f"AW should be accumulate operation, got {aw['operation']}"
    fields = aw.get('accumulator_fields', [])
    assert len(fields) == 3, f"AW needs 3 components, got {len(fields)}: {fields}"
    # Check all 3 are present
    field_str = ' '.join(fields)
    assert 'internet' in field_str.lower(), "AW must include DR Internet"
    assert 'interhotel' in field_str.lower() or 'inter_hotel' in field_str.lower(), \
        "AW must include InterHotel XferIn"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_mapping_fixes.py::test_aw_has_three_components -v
```

Expected: FAIL — AW currently is `operation: 'direct'` with single field.

- [ ] **Step 3: Fix AW mapping**

Replace the AW entry:

```python
    'AW': {
        'column_index': 48,
        'label_en': 'Internet (3 components)',
        'label_fr': 'Internet (3 composantes)',
        'source_page': 'PAGE 2 + Sales Journal + PAGE 7',
        'source_line': 'DR Internet + SJ Bqt Internet + InterHotel XferIn',
        'operation': 'accumulate',
        'accumulator_fields': [
            'revenue.internet.total',           # DR Internet (often NEGATIVE — keep sign!)
            'sales_journal.banquet.internet',    # SJ Banquet INTERNET (always positive)
            'balance.interhotel_xferin',         # DR p.7 InterHotel XferIn ($9.99-$49.95)
        ],
        'description': 'AW = DR Internet (signed, often negative!) + SJ Banquet Internet + '
                       'DR InterHotel XferIn (p.7). All 3 components every time. '
                       'Real example Apr 15: -17.38 + 460 + 19.98 = 462.60',
        'sign_handling': 'keep_sign',
        'note': 'DR Internet can be negative (corrections). InterHotel often $9.99 weekday, '
                '$49.95 Sunday. Missing any component causes DC error by that amount.'
    },
```

- [ ] **Step 4: Run test**

```bash
pytest tests/test_mapping_fixes.py::test_aw_has_three_components -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/daily_rev_jour_mapping.py tests/test_mapping_fixes.py
git commit -m "fix: AW column now accumulates DR Internet + SJ Bqt Internet + InterHotel XferIn"
```

---

### Task 9: Document xlutils.copy limitation

**Files:**
- Modify: `utils/rj_filler.py` (add prominent warning)
- Create: `docs/XLUTILS_WARNING.md`

- [ ] **Step 1: Add warning to rj_filler.py**

At the top of `rj_filler.py`, after the imports, add:

```python
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ WARNING: xlutils.copy() DESTROYS Excel formulas, tab colors, and macros.   ║
# ║ This is a KNOWN BUG. The RJ .xls files lose ~470KB of formula data.       ║
# ║ For production use, migrate to pywin32 Excel COM (Windows) or openpyxl     ║
# ║ (.xlsx). See docs/XLUTILS_WARNING.md and docs/RJ_AUTOFILL_MASTER.md §4.  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
```

- [ ] **Step 2: Create warning doc**

Create `docs/XLUTILS_WARNING.md`:

```markdown
# xlutils.copy Limitation

## Problem
`utils/rj_filler.py` uses `xlutils.copy()` to create writable copies of .xls workbooks.
This function only preserves **cell values**, not:
- Formulas (DC formula, Bal_Ouv chain, escompte calcs, category totals)
- Tab colors
- VBA macros
- Cell comments

File size drops from ~2.27 MB to ~1.8 MB (470 KB of metadata lost).

## Impact
Any .xls file saved through RJFiller will have ALL formulas replaced with static values.
The user's custom RJ template (with colored tabs, formula chains, macros) is destroyed.

## Workaround (Current)
Use pywin32 Excel COM for direct writes on Windows:
```python
import win32com.client as win32
excel = win32.Dispatch('Excel.Application')
wb = excel.Workbooks.Open(path)
ws.Cells(row, col).Formula = '=value'
wb.Save()
```

## Long-term Fix
Migrate RJ workbook to .xlsx format and use openpyxl (preserves formulas).
Or implement RJFillerCOM class using pywin32 for .xls files.
```

- [ ] **Step 3: Commit**

```bash
git add utils/rj_filler.py docs/XLUTILS_WARNING.md
git commit -m "docs: add prominent xlutils.copy formula destruction warning"
```

---

## Post-Implementation Verification

After all 9 tasks are complete:

- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Verify no merge conflict markers remain: `grep -rn "<<<<<<\|======\|>>>>>>" utils/`
- [ ] Verify AX/AY no longer reference F&B OPERA: `grep -n "restaurant_piazza\|banquet\.\|la_spesa\.\|services_chambres" utils/daily_rev_jour_mapping.py` — should only appear in comments, not in accumulator_fields
- [ ] Verify AP references GEAC: `grep -A5 "'AP'" utils/daily_rev_jour_mapping.py` — should show geac_compensation
- [ ] Cross-reference against `docs/RJ_AUTOFILL_MASTER.md` sections 7.3, 9, 10
