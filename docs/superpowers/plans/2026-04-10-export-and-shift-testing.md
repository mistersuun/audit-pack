# Export Verification & Full Shift Simulation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the Excel export produces a cell-accurate RJ file matching the auditor's ground truth, and that the full shift flow (import → clear → upload → fill → DC=$0.00 → export → verify) works end-to-end in the browser.

**Architecture:** Sub-project A (pytest): for consecutive fixture day pairs, load day N-1's ground-truth as the RJFiller base template, seed day N's NAS via the existing `extract_all()`, run the export pipeline, compare cell-by-cell against day N's ground-truth. Sub-project B (Playwright): one shift simulation for 2026-03-29 → 2026-03-30 that drives the full browser UI including import, "Tout effacer", PDF uploads, form fills, DC verification, and .xls download verification.

**Tech Stack:** Python + xlrd + xlutils/xlwt (existing `RJFiller`), pytest parametrize, Playwright 1.59 (existing), SheetJS (`xlsx` npm package) for reading .xls in Node.js.

**Spec:** `docs/superpowers/specs/2026-04-10-export-and-shift-testing-design.md`

---

## Key Facts (read before starting)

1. **Export endpoint:** `GET /api/rj/native/export/rj-filled/<audit_date>` at `routes/audit/rj_native.py:1281`. Returns binary `.xls` via `send_file()`. Uses `RJFiller` to fill the base template, then `rebuild_xls_with_vba()` to preserve VBA.

2. **Export UI:** `#btn-export` button calls `exportRJExcel()` (JS, line 2287) which does `fetch` → blob → creates download link. NOT a navigation-based download.

3. **Import endpoint:** `POST /api/rj/native/import/excel` at line 557. Upload via `#file-import-rj` file input. Creates a session for day+1, archives the file to DB.

4. **Clear tabs:** `POST /api/rj/native/clear/all-daily`. UI button: `onclick="clearMacro('all-daily')"` (line 887) with a `confirm()` dialog.

5. **RJFiller key methods:** `fill_sheet(sheet_name, data_dict)`, `fill_jour_day(day, values)`, `envoie_dans_jour(day)`, `calcul_carte(day)`, `reset_tabs()`, `save_to_bytes()`.

6. **CELL_MAPPINGS** in `utils/rj_mapper.py:397`: covers `controle`, `Recap`, `transelect`, `geac_ux`. Each maps NAS field names to cell addresses (e.g., `'comptant_lightspeed_lecture': 'C6'`).

7. **Consecutive fixture pairs available:** (03-02→03-03), (03-03→03-04), (03-29→03-30), (04-03→04-04), (04-04→04-05).

8. **Ground-truth RJ has 38 sheets** (verified on 2026-03-21).

9. **Do NOT commit.** User handles all git operations.

10. **Existing seeder:** `tests/fixtures/ground_truth_seeder.py` with `extract_all(day)` → returns flat dict of NAS attribute values. Already tested on 18 days.

---

## File Map

| File | Change | Responsibility |
|---|---|---|
| `tests/test_export_verification.py` | Create | Sub-project A: parametrized pytest, cell-level comparison |
| `tests/playwright/shift-simulation.spec.js` | Create | Sub-project B: full shift simulation |
| `tests/playwright/fixtures/seed-2026-03-30.json` | Create | Seeded values for the shift simulation |
| `utils/rj_filler.py` | Modify (fix-loop only) | If cell is written wrong |
| `utils/rj_mapper.py` | Modify (fix-loop only) | If CELL_MAPPINGS has wrong entry |

---

## Sub-project A — Export cell-level verification

### Task 1: Export test skeleton with one pair

**Files:**
- Create: `tests/test_export_verification.py`

- [ ] **Step 1: Write the test file**

Create `/home/v/Documents/Projects/audit-pack/tests/test_export_verification.py`:

```python
"""Export cell-level verification.

For consecutive fixture day pairs, load day N-1's ground-truth as the
RJFiller base template, seed day N's NAS data, run the export pipeline,
and compare the exported .xls cell-by-cell against day N's ground-truth.

Tests:
  - All 38 sheets exist with correct names
  - Jour row for day N matches ground truth (cols 1-86)
  - Filled tabs (Recap, transelect, geac_ux, controle) match ground truth cells
"""
from __future__ import annotations

import io
import json
from datetime import date
from pathlib import Path

import pytest
import xlrd

from tests.fixtures.ground_truth_seeder import extract_all, _open_workbook

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = PROJECT_ROOT / "test_fixtures"

# ── Consecutive pairs available ──────────────────────────────────
CONSECUTIVE_PAIRS = [
    ("2026-03-02", "2026-03-03"),
    ("2026-03-03", "2026-03-04"),
    ("2026-03-29", "2026-03-30"),
    ("2026-04-03", "2026-04-04"),
    ("2026-04-04", "2026-04-05"),
]


def _load_ground_truth_bytes(day: str) -> bytes:
    """Load the ground-truth RJ as raw bytes."""
    path = FIXTURES_DIR / day / "ground_truth_rj.xls"
    if not path.exists():
        pytest.skip(f"No ground_truth_rj.xls for {day}")
    return path.read_bytes()


def _get_sheet_names(wb: xlrd.Book) -> list[str]:
    return wb.sheet_names()


def _read_cell(sheet: xlrd.sheet.Sheet, row: int, col: int) -> float | str | None:
    """Read a cell value, returning float for numbers, str for text, None for empty."""
    if row >= sheet.nrows or col >= sheet.ncols:
        return None
    ctype = sheet.cell_type(row, col)
    if ctype == xlrd.XL_CELL_EMPTY:
        return None
    val = sheet.cell_value(row, col)
    if ctype == xlrd.XL_CELL_NUMBER:
        return float(val)
    if ctype == xlrd.XL_CELL_TEXT:
        return str(val).strip()
    return val


def _compare_cells(exported_wb: xlrd.Book, gt_wb: xlrd.Book,
                   sheet_name: str, cells: list[tuple[int, int]],
                   tolerance: float = 0.01) -> list[dict]:
    """Compare specific cells between exported and ground-truth workbooks.

    Args:
        cells: list of (row, col) tuples to compare

    Returns:
        list of diffs: [{'sheet', 'row', 'col', 'exported', 'expected', 'diff'}]
    """
    diffs = []
    try:
        exp_sh = exported_wb.sheet_by_name(sheet_name)
    except xlrd.biffh.XLRDError:
        diffs.append({'sheet': sheet_name, 'row': 0, 'col': 0,
                      'exported': 'MISSING SHEET', 'expected': 'exists', 'diff': 'N/A'})
        return diffs
    try:
        gt_sh = gt_wb.sheet_by_name(sheet_name)
    except xlrd.biffh.XLRDError:
        return []  # GT doesn't have this sheet — nothing to compare

    for row, col in cells:
        exp_val = _read_cell(exp_sh, row, col)
        gt_val = _read_cell(gt_sh, row, col)

        # Both None/empty → match
        if exp_val is None and gt_val is None:
            continue
        # One None, other not → diff
        if exp_val is None or gt_val is None:
            diffs.append({'sheet': sheet_name, 'row': row + 1, 'col': col,
                          'exported': exp_val, 'expected': gt_val, 'diff': 'missing'})
            continue
        # Both numeric → compare with tolerance
        if isinstance(exp_val, (int, float)) and isinstance(gt_val, (int, float)):
            if abs(float(exp_val) - float(gt_val)) > tolerance:
                diffs.append({'sheet': sheet_name, 'row': row + 1, 'col': col,
                              'exported': round(float(exp_val), 2),
                              'expected': round(float(gt_val), 2),
                              'diff': round(float(exp_val) - float(gt_val), 2)})
            continue
        # Text → exact match
        if str(exp_val) != str(gt_val):
            diffs.append({'sheet': sheet_name, 'row': row + 1, 'col': col,
                          'exported': exp_val, 'expected': gt_val, 'diff': 'text mismatch'})

    return diffs


def _get_jour_row_for_day(day_num: int) -> int:
    """Map day number to the jour sheet row (0-indexed).

    Import this from utils/rj_mapper.py if available, otherwise replicate.
    The jour sheet typically has day 1 at row 2, day 2 at row 3, etc.
    """
    from utils.rj_mapper import get_jour_row_for_day
    return get_jour_row_for_day(day_num)


def _build_export_diagnostic(base_day: str, target_day: str, diffs: list[dict]) -> str:
    """Format cell diffs for pytest.fail()."""
    lines = [
        f"",
        f"Export verification FAILED: {base_day} → {target_day}",
        f"─────────────────────────────────────────────────────",
        f"{len(diffs)} cell(s) differ:",
        "",
    ]
    for d in diffs[:50]:  # cap at 50 to avoid overwhelming output
        lines.append(
            f"  {d['sheet']:15s}  row {d['row']:3d}  col {d['col']:3d}  "
            f"exported={d['exported']}  expected={d['expected']}  diff={d['diff']}"
        )
    if len(diffs) > 50:
        lines.append(f"  ... and {len(diffs) - 50} more")
    lines.append("─────────────────────────────────────────────────────")
    return "\n".join(lines)


def _run_export_pipeline(app, base_day: str, target_day: str) -> bytes:
    """Run the RJFiller export pipeline and return exported .xls bytes.

    This replicates what the export endpoint does:
    1. Load base (day N-1) as template
    2. Create NAS for target day, seed it
    3. Fill all sheets via RJFiller
    4. Run macro equivalents (envoie_dans_jour, calcul_carte)
    5. Return saved bytes
    """
    from database.models import db, NightAuditSession
    from utils.rj_filler import RJFiller
    from utils.rj_mapper import nas_jour_to_excel_dict

    base_bytes = _load_ground_truth_bytes(base_day)
    y, m, d_num = (int(p) for p in target_day.split("-"))
    audit_date = date(y, m, d_num)
    day = d_num

    with app.app_context():
        # Clean + create session
        NightAuditSession.query.filter_by(audit_date=audit_date).delete()
        db.session.commit()

        nas = NightAuditSession(audit_date=audit_date, auditor_name="test")
        seed = extract_all(target_day)
        for key, value in seed.items():
            if hasattr(nas, key):
                setattr(nas, key, value)
        db.session.add(nas)
        db.session.commit()

        # Run filler
        filler = RJFiller(io.BytesIO(base_bytes))
        filler.update_controle(vjour=day, mois=m, annee=y)

        # Fill Recap
        recap_data = {
            'comptant_lightspeed_lecture': nas.cash_ls_lecture or 0,
            'comptant_lightspeed_corr': nas.cash_ls_corr or 0,
            'comptant_positouch_lecture': nas.cash_pos_lecture or 0,
            'comptant_positouch_corr': nas.cash_pos_corr or 0,
            'cheque_payment_register_lecture': nas.cheque_ar_lecture or 0,
            'cheque_payment_register_corr': nas.cheque_ar_corr or 0,
            'cheque_daily_revenu_lecture': nas.cheque_dr_lecture or 0,
            'cheque_daily_revenu_corr': nas.cheque_dr_corr or 0,
            'remb_gratuite_lecture': nas.remb_gratuite_lecture or 0,
            'remb_gratuite_corr': nas.remb_gratuite_corr or 0,
            'remb_client_lecture': nas.remb_client_lecture or 0,
            'remb_client_corr': nas.remb_client_corr or 0,
            'due_back_reception_lecture': nas.dueback_reception_lecture or 0,
            'due_back_reception_corr': nas.dueback_reception_corr or 0,
            'due_back_nb_lecture': nas.dueback_nb_lecture or 0,
            'due_back_nb_corr': nas.dueback_nb_corr or 0,
            'prepare_par': nas.auditor_name or '',
        }
        filler.fill_sheet('Recap', recap_data)

        # Fill Transelect (replicate export endpoint logic)
        rest_data = json.loads(nas.transelect_restaurant or '{}')
        recep_data = json.loads(nas.transelect_reception or '{}')
        trans_dict = {}
        term_to_prefix = {
            'Bar 701': 'bar_701', 'Bar 702': 'bar_702', 'Bar 703': 'bar_703',
            'Spesa 704': 'spesa_704', 'Room 705': 'room_705'
        }
        for term_name, prefix in term_to_prefix.items():
            td = rest_data.get(term_name, {})
            for card, card_key in [('debit', 'debit'), ('visa', 'visa'),
                                    ('mc', 'master'), ('amex', 'amex')]:
                val = td.get(card, 0)
                if val:
                    trans_dict[f'{prefix}_{card_key}'] = val
        for card, card_key in [('debit', 'debit'), ('visa', 'visa'),
                                ('mc', 'master'), ('amex', 'amex')]:
            cd = recep_data.get(card, {})
            if card == 'debit':
                if cd.get('k053'): trans_dict['reception_debit'] = cd['k053']
                if cd.get('term8'): trans_dict['reception_debit_term8'] = cd['term8']
            else:
                if cd.get('fusebox'): trans_dict[f'fusebox_{card_key}'] = cd['fusebox']
                if cd.get('k053'): trans_dict[f'reception_{card_key}_term'] = cd['k053']
        if trans_dict:
            filler.fill_sheet('transelect', trans_dict)

        # Fill GEAC
        geac_co = json.loads(nas.geac_cashout or '{}')
        geac_dr_data = json.loads(nas.geac_daily_rev or '{}')
        geac_dict = {}
        for c in ['amex', 'diners', 'master', 'visa', 'discover']:
            if geac_co.get(c): geac_dict[f'{c}_cash_out'] = geac_co[c]
            if geac_dr_data.get(c): geac_dict[f'{c}_daily_revenue'] = geac_dr_data[c]
        if geac_dict:
            filler.fill_sheet('geac_ux', geac_dict)

        # Fill Jour
        jour_dict = nas_jour_to_excel_dict(nas)
        if jour_dict:
            filler.fill_jour_day(day, jour_dict)

        # Run macro equivalents
        try:
            filler.envoie_dans_jour(day)
        except Exception:
            pass
        try:
            filler.calcul_carte(day)
        except Exception:
            pass

        # Save
        exported_bytes = filler.save_to_bytes().getvalue()

        # Cleanup
        NightAuditSession.query.filter_by(audit_date=audit_date).delete()
        db.session.commit()

        return exported_bytes


def test_export_2026_03_29_to_30_smoke(app):
    """Smoke test: export produces valid .xls with 38 sheets."""
    exported_bytes = _run_export_pipeline(app, "2026-03-29", "2026-03-30")
    wb = xlrd.open_workbook(file_contents=exported_bytes)
    sheets = wb.sheet_names()
    assert len(sheets) >= 38, f"Expected 38 sheets, got {len(sheets)}: {sheets}"

    gt_wb = xlrd.open_workbook(
        file_contents=_load_ground_truth_bytes("2026-03-30")
    )
    gt_sheets = gt_wb.sheet_names()
    assert set(sheets) == set(gt_sheets), (
        f"Sheet name mismatch.\n"
        f"  Extra in export: {set(sheets) - set(gt_sheets)}\n"
        f"  Missing from export: {set(gt_sheets) - set(sheets)}"
    )
```

- [ ] **Step 2: Run the smoke test**

```bash
source .venv/bin/activate && python -m pytest tests/test_export_verification.py::test_export_2026_03_29_to_30_smoke -v
```

Expected: PASS (38 sheets, names match). If it fails, the filler or the base template has issues — read the error and fix.

- [ ] **Step 3: Skip commit**

---

### Task 2: Jour row cell-level comparison

**Files:**
- Modify: `tests/test_export_verification.py`

- [ ] **Step 1: Add the jour row comparison test**

Append to `tests/test_export_verification.py`:

```python
def test_export_2026_03_29_to_30_jour_row(app):
    """Jour sheet: day 30's row matches ground truth cell-by-cell."""
    exported_bytes = _run_export_pipeline(app, "2026-03-29", "2026-03-30")
    exp_wb = xlrd.open_workbook(file_contents=exported_bytes)
    gt_wb = xlrd.open_workbook(file_contents=_load_ground_truth_bytes("2026-03-30"))

    day_row = _get_jour_row_for_day(30)
    cells = [(day_row, col) for col in range(1, 87)]  # cols 1-86

    diffs = _compare_cells(exp_wb, gt_wb, 'jour', cells)
    if diffs:
        pytest.fail(_build_export_diagnostic("2026-03-29", "2026-03-30", diffs))
```

- [ ] **Step 2: Run the test**

```bash
source .venv/bin/activate && python -m pytest tests/test_export_verification.py::test_export_2026_03_29_to_30_jour_row -v
```

Expected: likely FAIL with diffs. Record which columns differ — this is the entry point for the fix-loop.

- [ ] **Step 3: Skip commit**

---

### Task 3: Filled tabs comparison + parametrize

**Files:**
- Modify: `tests/test_export_verification.py`

- [ ] **Step 1: Add tab comparison + parametrize**

Append to `tests/test_export_verification.py`:

```python
def _get_recap_cells() -> list[tuple[int, int]]:
    """Return (row, col) list for all cells in CELL_MAPPINGS['Recap']."""
    from utils.rj_mapper import CELL_MAPPINGS
    cells = []
    mapping = CELL_MAPPINGS.get('Recap', {})
    for field_name, cell_addr in mapping.items():
        # cell_addr is like 'C6' → parse to (row, col)
        col_letter = ''.join(c for c in cell_addr if c.isalpha())
        row_num = int(''.join(c for c in cell_addr if c.isdigit()))
        col = 0
        for ch in col_letter.upper():
            col = col * 26 + (ord(ch) - ord('A'))
        cells.append((row_num - 1, col))  # convert to 0-indexed
    return cells


def _get_mapping_cells(sheet_name: str) -> list[tuple[int, int]]:
    """Return (row, col) list for all cells in CELL_MAPPINGS[sheet_name]."""
    from utils.rj_mapper import CELL_MAPPINGS
    cells = []
    mapping = CELL_MAPPINGS.get(sheet_name, {})
    for field_name, cell_addr in mapping.items():
        if not isinstance(cell_addr, str) or not any(c.isdigit() for c in cell_addr):
            continue
        col_letter = ''.join(c for c in cell_addr if c.isalpha())
        row_num = int(''.join(c for c in cell_addr if c.isdigit()))
        col = 0
        for ch in col_letter.upper():
            col = col * 26 + (ord(ch) - ord('A'))
        cells.append((row_num - 1, col))
    return cells


@pytest.mark.parametrize("base_day,target_day", CONSECUTIVE_PAIRS,
                         ids=[f"{b}→{t}" for b, t in CONSECUTIVE_PAIRS])
def test_export_matches_ground_truth(app, base_day, target_day):
    """Full export verification: 38 sheets + cell-level on filled sheets."""
    exported_bytes = _run_export_pipeline(app, base_day, target_day)
    exp_wb = xlrd.open_workbook(file_contents=exported_bytes)
    gt_wb = xlrd.open_workbook(file_contents=_load_ground_truth_bytes(target_day))

    # 1. Sheet names must match
    exp_sheets = set(exp_wb.sheet_names())
    gt_sheets = set(gt_wb.sheet_names())
    assert exp_sheets == gt_sheets, (
        f"Sheet mismatch: extra={exp_sheets - gt_sheets}, missing={gt_sheets - exp_sheets}"
    )

    # 2. Jour row for the target day
    _, _, d_num = (int(p) for p in target_day.split("-"))
    day_row = _get_jour_row_for_day(d_num)
    jour_cells = [(day_row, col) for col in range(1, 87)]
    all_diffs = _compare_cells(exp_wb, gt_wb, 'jour', jour_cells)

    # 3. Filled tabs
    for sheet_name in ['Recap', 'transelect', 'geac_ux', 'controle']:
        tab_cells = _get_mapping_cells(sheet_name)
        if tab_cells:
            all_diffs.extend(_compare_cells(exp_wb, gt_wb, sheet_name, tab_cells))

    if all_diffs:
        pytest.fail(_build_export_diagnostic(base_day, target_day, all_diffs))
```

- [ ] **Step 2: Run all 5 pairs**

```bash
source .venv/bin/activate && python -m pytest tests/test_export_verification.py::test_export_matches_ground_truth -v --tb=no
```

Record how many pass. This is the baseline for the fix-loop.

- [ ] **Step 3: Skip commit**

---

### Task 4: Fix-loop — get all 5 export pairs green

**Files (modified as needed):**
- `tests/test_export_verification.py` (if the test helper or comparison logic needs adjustment)
- `utils/rj_filler.py` (if a cell is written to the wrong address)
- `utils/rj_mapper.py` (if CELL_MAPPINGS has wrong entries)
- `tests/fixtures/ground_truth_seeder.py` (if seeder provides wrong values)

**Exit criterion:** `python -m pytest tests/test_export_verification.py::test_export_matches_ground_truth -v --tb=no` reports all 5 pairs PASS.

- [ ] **Step 1: Get the diagnostic for the first failing pair**

```bash
source .venv/bin/activate && python -m pytest tests/test_export_verification.py::test_export_matches_ground_truth -v -x
```

The `-x` flag stops at the first failure. Read the cell diff diagnostic.

- [ ] **Step 2: Diagnose the root cause**

Common patterns:

| Diff pattern | Likely cause |
|---|---|
| Jour col N: exported=0, expected=X | `nas_jour_to_excel_dict` doesn't map this NAS field, or seeder didn't populate it |
| Recap cell C6: exported=X, expected=Y | Recap field mapping key mismatch between seeder and export |
| Transelect cells: all zero | Transelect JSON blob terminal names in seeder don't match the `term_to_prefix` mapping in export |
| GEAC cells: all zero | GEAC balance sheet JSON keys from seeder don't match what the export expects |
| Controle date: exported=wrong | `update_controle` called with wrong args |
| Jour col: off by HP deduction amount | HP entries not applied — check `_run_export_pipeline` doesn't call HP deductions |

- [ ] **Step 3: Fix the root cause**

Make the minimal change. Verify with the specific failing pair:

```bash
source .venv/bin/activate && python -m pytest tests/test_export_verification.py -v -k "<pair_id>"
```

- [ ] **Step 4: Run all 5 pairs to check regressions**

```bash
source .venv/bin/activate && python -m pytest tests/test_export_verification.py::test_export_matches_ground_truth -v --tb=no
```

- [ ] **Step 5: Also verify nightly-balance (Layer 2) still passes**

```bash
source .venv/bin/activate && python -m pytest tests/test_nightly_balance.py -v --tb=no
```

Expected: 18 passed (no regressions).

- [ ] **Step 6: Loop back to Step 1 until all 5 export pairs pass**

- [ ] **Step 7: Skip commit**

---

## Sub-project B — Full shift simulation (Playwright)

### Task 5: Install SheetJS + generate seed JSON

**Files:**
- Create: `tests/playwright/fixtures/seed-2026-03-30.json`

- [ ] **Step 1: Install SheetJS**

```bash
cd /home/v/Documents/Projects/audit-pack && npm install --save-dev xlsx
```

- [ ] **Step 2: Generate seed JSON**

```bash
source .venv/bin/activate && python -c "
import json
from tests.fixtures.ground_truth_seeder import extract_all
print(json.dumps(extract_all('2026-03-30'), indent=2, sort_keys=True))
" > tests/playwright/fixtures/seed-2026-03-30.json
```

- [ ] **Step 3: Verify**

```bash
python -c "import json; d=json.load(open('tests/playwright/fixtures/seed-2026-03-30.json')); print(len(d), 'keys'); assert len(d) >= 10"
```

- [ ] **Step 4: Skip commit**

---

### Task 6: Write the shift simulation spec

**Files:**
- Create: `tests/playwright/shift-simulation.spec.js`

This is the largest single task. The implementer MUST first discover the real DOM selectors by reading `templates/audit/rj/rj_native.html`, then write the test with those selectors.

- [ ] **Step 1: Discover selectors**

Read the template and find the ACTUAL selectors for:
- Import file input: `#file-import-rj` (line 865)
- "Tout effacer" button: `onclick="clearMacro('all-daily')"` (line 887)
- Source file upload: `#file-report-upload` (line 609)
- Export button: `#btn-export` (line 682) — calls `exportRJExcel()`
- Every form field the seeder populates (see the existing `nightly-flow.spec.js` for patterns)

Also understand how `exportRJExcel()` works (line 2287): it uses `fetch()` → blob → programmatic `<a>` click. Playwright can intercept this via `page.waitForEvent('download')` OR by directly calling the fetch URL and reading the response bytes.

- [ ] **Step 2: Write the spec**

Create `/home/v/Documents/Projects/audit-pack/tests/playwright/shift-simulation.spec.js`:

```js
// @ts-check
// Full shift simulation: import → clear → upload → fill → DC=$0.00 → export → verify .xls
//
// Uses the 2026-03-29 → 2026-03-30 consecutive pair.
// Yesterday's ground-truth (2026-03-29) is imported as the base.
// Today's data (2026-03-30) is seeded and uploaded.
// The exported .xls is verified with SheetJS.

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const XLSX = require('xlsx');

const SEED = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'fixtures/seed-2026-03-30.json'), 'utf8')
);
const SESSION_COOKIE = fs.readFileSync(
  path.join(__dirname, '.session-cookie'), 'utf8'
).trim();
const FIXTURE_DIR_BASE = path.join(__dirname, '../../test_fixtures/2026-03-29');
const FIXTURE_DIR_TARGET = path.join(__dirname, '../../test_fixtures/2026-03-30');

async function injectAuth(context) {
  await context.addCookies([{
    name: 'session', value: SESSION_COOKIE,
    domain: '127.0.0.1', path: '/', httpOnly: true, sameSite: 'Lax',
  }]);
}

test('complete shift simulation: 2026-03-29 → 2026-03-30', async ({ page }) => {
  test.setTimeout(180_000);

  await injectAuth(page.context());
  await page.addInitScript(() => {
    localStorage.setItem('rjn_ui_mode', 'livecard');
  });

  // Auto-accept confirmation dialogs (for "Tout effacer")
  page.on('dialog', dialog => dialog.accept());

  // ── 1. Navigate ──
  await page.goto('/rj/native');
  await page.waitForSelector('#livecard', { state: 'attached' });

  // ── 2. Import yesterday's RJ ──
  const importPath = path.join(FIXTURE_DIR_BASE, 'ground_truth_rj.xls');
  await page.setInputFiles('#file-import-rj', importPath);
  // Wait for import to complete — the page should show the new session
  await page.waitForTimeout(3000);
  // Verify the session date is now 2026-03-30 (day after the imported file)
  const sessionDate = await page.evaluate(() => window.SESSION && window.SESSION.audit_date);
  expect(sessionDate).toBe('2026-03-30');

  // ── 3. Clear daily tabs ──
  // Click "Tout effacer (Recap+Trans+GEAC)" — dialog auto-accepted
  await page.click('button[onclick*="clearMacro(\'all-daily\')"]');
  await page.waitForTimeout(1000);

  // ── 4. Upload tonight's PDFs ──
  const sources = [
    'sales_journal.txt', 'daily_revenue.pdf', 'ar_summary.pdf',
    'hp.xlsx', 'market_segment.pdf',
  ];
  for (const name of sources) {
    const filePath = path.join(FIXTURE_DIR_TARGET, name);
    if (!fs.existsSync(filePath)) continue;
    await page.setInputFiles('#file-report-upload', filePath);
    await page.waitForTimeout(2000);
  }

  // ── 5. Fill seeded fields ──
  // (The implementer should adapt the field-fill logic from
  //  nightly-flow.spec.js, using SEED data for 2026-03-30.
  //  This section is identical in structure to nightly-flow.spec.js
  //  steps 4-5, just with different seed data.
  //  Read the existing nightly-flow.spec.js and replicate the
  //  tab-switching + field-filling pattern with SEED values.)

  // Recap tab
  await page.click('button[data-tab="recap"]');
  // ... fill recap fields from SEED ...

  // Transelect tab
  await page.click('button[data-tab="transelect"]');
  // ... fill transelect fields from SEED ...

  // GEAC tab
  await page.click('button[data-tab="geac"]');
  // ... fill GEAC fields from SEED ...

  // DueBack tab
  await page.click('button[data-tab="dueback"]');
  // ... fill dueback entries from SEED ...

  // SD tab
  await page.click('button[data-tab="sd"]');
  // ... fill SD entries from SEED ...

  // Jour tab
  await page.click('button[data-tab="jour"]');
  // ... fill jour fields from SEED ...

  // ── 6. Wait for final refresh ──
  await page.waitForTimeout(2000);

  // ── 7. Verify DC = $0.00 on livecard ──
  await page.waitForFunction(() =>
    window.livecard && typeof window.livecard.render === 'function'
  );
  const dcText = await page.locator('#livecard-dc').textContent();
  console.log('Livecard DC:', dcText);
  // Parse DC — should be $0.00 or very close
  const dcNum = parseFloat(dcText.replace('$', '').replace(',', ''));
  expect(Math.abs(dcNum)).toBeLessThan(1.0);

  // ── 8. Export the completed RJ ──
  // exportRJExcel() uses fetch → blob → programmatic download.
  // Intercept the fetch to capture the response bytes.
  const exportDate = '2026-03-30';
  const exportUrl = `/api/rj/native/export/rj-filled/${exportDate}`;
  const responsePromise = page.waitForResponse(resp =>
    resp.url().includes(exportUrl) && resp.status() === 200
  );
  await page.click('#btn-export');
  const response = await responsePromise;
  const exportBuffer = await response.body();

  // ── 9. Verify the downloaded .xls ──
  const wb = XLSX.read(exportBuffer, { type: 'buffer' });

  // 9a. All 38 sheets present
  console.log('Exported sheets:', wb.SheetNames.length, wb.SheetNames);
  expect(wb.SheetNames.length).toBeGreaterThanOrEqual(38);

  // 9b. Controle date is correct
  const controle = wb.Sheets['controle'];
  if (controle) {
    // The controle sheet should have day=30 somewhere
    const sheetData = XLSX.utils.sheet_to_json(controle, { header: 1 });
    const flatValues = sheetData.flat().filter(v => v !== undefined && v !== '');
    expect(flatValues).toContain(30);  // vjour
  }

  // 9c. Jour sheet has data for day 30
  const jour = wb.Sheets['jour'];
  expect(jour).toBeTruthy();

  // 9d. Screenshot the livecard
  await page.locator('#livecard').screenshot({
    path: 'test-results/shift-simulation-2026-03-30.png',
  });

  console.log('Shift simulation complete: DC =', dcText);
});
```

**IMPORTANT:** The `// ... fill X fields from SEED ...` sections above are placeholders that the implementer MUST fill in. Read the existing `nightly-flow.spec.js` to see the exact pattern for each tab (field selectors, tab switching, blur triggers). Copy and adapt that pattern for 2026-03-30 seed data.

- [ ] **Step 3: Regenerate auth cookie**

```bash
source .venv/bin/activate && python -c "
from main import create_app
from flask.sessions import SecureCookieSessionInterface
app = create_app()
with app.test_request_context():
    s = SecureCookieSessionInterface().get_signing_serializer(app)
    print(s.dumps({
        'authenticated': True, 'user_id': 1,
        'user_role_type': 'night_auditor', 'user_role': 'back',
        'user_name': 'Test Auditor', 'login_role_type': 'night_auditor',
    }))
" 2>&1 | tail -1 > tests/playwright/.session-cookie
```

- [ ] **Step 4: Start Flask + run the test**

```bash
source .venv/bin/activate && python main.py &
sleep 4
npx playwright test tests/playwright/shift-simulation.spec.js --config=tests/playwright/playwright.config.js
```

Fix any failures (selector mismatches, timing, export intercept issues).

- [ ] **Step 5: Stop the Flask server**

```bash
kill $(pgrep -f "python main.py") 2>/dev/null || true
```

- [ ] **Step 6: Skip commit**

---

### Task 7: Final verification — all layers

**Files:** none (verification only)

- [ ] **Step 1: Seeder tests**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py -v --tb=no
```

Expected: 26 passed.

- [ ] **Step 2: Nightly balance (Layer 2)**

```bash
source .venv/bin/activate && python -m pytest tests/test_nightly_balance.py -v --tb=no
```

Expected: 18 passed.

- [ ] **Step 3: Export verification (Sub-project A)**

```bash
source .venv/bin/activate && python -m pytest tests/test_export_verification.py -v --tb=no
```

Expected: all pairs passed (smoke + jour + parametrized).

- [ ] **Step 4: All Playwright tests**

```bash
source .venv/bin/activate && python main.py &
sleep 4
npx playwright test --config=tests/playwright/playwright.config.js
pkill -f "python main.py" || true
```

Expected: 21+ passed (19 livecard + 1 nightly-flow + 1 shift-simulation).

- [ ] **Step 5: Fixture regression**

```bash
source .venv/bin/activate && python scripts/fixture_regression.py 2>&1 | grep "Parseable today"
```

Expected: 18 parseable (unchanged).

- [ ] **Step 6: Report summary**

```
Export & Shift Testing — complete.

Sub-project A (export pytest):   PASS  (N pairs, cell-level match)
Sub-project B (shift Playwright): PASS  (DC=$0.00, 38 sheets, correct date)
Nightly balance:                  PASS  (18 days)
Livecard:                         PASS  (19 tests)
Nightly-flow:                     PASS  (1 test)
Seeder:                           PASS  (26 tests)
fixture_regression.py:            18 parseable (unchanged)

Fixes applied:
- <file>:<function> — <one-line why>
...
```

- [ ] **Step 7: Skip commit (user handles git)**

---

## Self-review checklist

- [x] Every spec section has a task:
  - Spec §2 Sub-project A (export) → Tasks 1, 2, 3, 4
  - Spec §3 Sub-project B (shift simulation) → Tasks 5, 6
  - Spec §4 Success criteria → Task 7
  - Spec §6 Risks (dialog blocking, export intercept) → handled in Task 6 code
  - Spec §7 YAGNI → no VBA execution, no formatting, no formula evaluation
- [x] No placeholders except Task 6's field-fill sections which are explicitly flagged with instructions to copy from nightly-flow.spec.js
- [x] Function names consistent: `_run_export_pipeline`, `_compare_cells`, `_build_export_diagnostic`, `_get_mapping_cells`, `_load_ground_truth_bytes`, `_read_cell`
- [x] All commit steps say "skip commit — user handles git"
- [x] Test commands include expected output
- [x] Fix-loop (Task 4) has exit criterion + anti-patterns
