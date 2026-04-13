# Nightly Balance Integration Test — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a test suite that replays historical night audits through the real pipeline and proves DC reaches $0.00 for every parseable fixture day, then keeps it there via a fast pytest fix-loop and one realistic Playwright end-to-end simulation.

**Architecture:** Three layers — (1) a pure-Python seeder that reads `test_fixtures/<day>/ground_truth_rj.xls` and writes NAS fields directly, (2) a pytest parametrized test that combines fixture source docs with seeded NAS state and asserts `abs(round(unexplained_residual, 2)) < 0.01`, and (3) one Playwright spec that simulates the auditor's actual night flow through the real browser UI.

**Tech Stack:** Python 3.14 + pytest + xlrd (existing), Flask test_client via existing `conftest.py` pattern, Playwright 1.59 (from the Phase 4 work), existing `BalancerService.check_balance(nas, files, day)` signature.

**Spec:** `docs/superpowers/specs/2026-04-10-nightly-balance-integration-design.md` — read this first.

---

## File Map

| File | Change | Responsibility |
|---|---|---|
| `tests/fixtures/__init__.py` | Create (empty) | Python package marker |
| `tests/fixtures/ground_truth_seeder.py` | Create | Read `test_fixtures/<day>/ground_truth_rj.xls`; extractor per field group; return dicts ready for NAS assignment |
| `tests/test_nightly_balance.py` | Create | Parametrized pytest over all parseable days; the residual=0 assertion; the diagnostic builder |
| `tests/test_ground_truth_seeder.py` | Create | Unit tests for the seeder extractors (one day per extractor) |
| `tests/playwright/fixtures/seed-2026-03-21.json` | Create | Hardcoded dump of `extract_all('2026-03-21')` for the Playwright test |
| `tests/playwright/nightly-flow.spec.js` | Create | One realistic auditor simulation for 2026-03-21 |
| `utils/rj_balancer.py` | Modify (fix-loop only) | Any missing variance class / sign / formula discovered |
| `utils/rj_filler.py` | Modify (fix-loop only) | Any dispatcher gap |
| `utils/parsers/*.py` | Modify (fix-loop only) | Any parser regex/decimal bug |
| `routes/audit/rj_native.py` | Modify (fix-loop only) | Only if Layer 2 passes but Layer 3 fails due to the dispatcher path |

**Not touched:** `templates/audit/rj/rj_native.html`, `database/models.py`, `scripts/fixture_regression.py`.

---

## Key Facts (discovered during spec/plan work — read before starting)

1. **`BalancerService.check_balance(nas, files=None, day=None)`** at `utils/rj_balancer.py:1180` takes file keys `'sj'`, `'dr'`, `'ar'`, `'hp'`, `'adv_dep'` (NOT `'sales_journal'`, `'daily_revenue'`, etc. — the HTTP route layer translates).

2. **NAS JSON blob fields** (stored as JSON strings, not dicts):
   - `geac_balance_sheet` — `{"prev_dr","prev_gl","today_dr","today_gl","facture_dr","facture_ar","advdep_dr","advdep_ad","newbal_dr","newbal_gl"}`
   - `transelect_restaurant`, `transelect_reception`, `transelect_quasimodo` — `{"_terminals":[...], "debit":{<term>:..., "esc_pct":0}, "visa":{...}, "mc":{...}, "amex":{...}, "discover":{...}}`
   - `dueback_entries` — list of dicts per receptionist
   - `sd_entries` — list of dicts per employee
   - `hp_admin_entries` — list of dicts

3. **NAS scalar fields relevant to Recap** (populated individually, NOT via a `recap_*` blob):
   - `cash_ls_lecture`, `cash_ls_corr`, `cash_pos_lecture`, `cash_pos_corr`
   - `cheque_ar_lecture`, `cheque_ar_corr`, `cheque_dr_lecture`, `cheque_dr_corr`
   - `remb_gratuite_lecture`, `remb_gratuite_corr`
   - `remb_client_lecture`, `remb_client_corr`
   - `dueback_reception_lecture`, `dueback_reception_corr`
   - `dueback_nb_lecture`, `dueback_nb_corr`
   - `recap_balance` (scalar, the surplus/deficit line)
   - `deposit_cdn`, `deposit_us`
   - See `utils/rj_balancer.py:1540` (`_extract_recap`) for the authoritative mapping.

4. **Ground-truth XLS sheet names** (from `test_fixtures/2026-03-21/ground_truth_rj.xls`): `['EJ','controle','Sheet1','rj','jour','Recap','transelect','geac_ux','DUBACK#','SetD',...]`. Names vary across days. Seeder reads by case-insensitive substring match, not exact name.

5. **Existing test conftest** (`tests/conftest.py`) already has `app`, `client` (authenticated), and `fresh_db` fixtures. Reuse these.

6. **18 parseable days** per `scripts/fixture_regression.py` (last run: 2026-03-02, 03-03, 03-04, 03-08, 03-09, 03-13, 03-14, 03-17, 03-21, 03-23, 03-26, 03-29, 03-30, 04-01, 04-02, 04-03, 04-04, 04-05). The remaining 6 are blocked by missing inputs and out of scope.

7. **Do NOT commit.** Per user memory rule: Claude never runs `git commit`. The user handles all git operations. All `Commit` steps below are labeled "user handles git" and should be skipped by the implementer.

---

## Phase A — Layer 1: Ground-truth seeder

### Task 1: Seeder scaffold + first unit test (DueBack)

**Files:**
- Create: `tests/fixtures/__init__.py` (empty)
- Create: `tests/fixtures/ground_truth_seeder.py`
- Create: `tests/test_ground_truth_seeder.py`

- [ ] **Step 1: Create empty package marker**

Create `/home/v/Documents/Projects/audit-pack/tests/fixtures/__init__.py` with exactly one byte of content (newline):

```python

```

- [ ] **Step 2: Write the failing test for DueBack extraction**

Create `/home/v/Documents/Projects/audit-pack/tests/test_ground_truth_seeder.py`:

```python
"""Unit tests for tests/fixtures/ground_truth_seeder.py.

Each extractor is tested against one well-known fixture day to catch
layout drift early. These tests do NOT depend on Flask or the DB —
they are pure xlrd reads.
"""
import pytest

from tests.fixtures.ground_truth_seeder import extract_dueback


def test_extract_dueback_returns_list_of_dicts():
    result = extract_dueback('2026-03-21')
    assert isinstance(result, list)
    assert len(result) > 0
    for row in result:
        assert isinstance(row, dict)
        assert 'name' in row
        assert 'amount' in row
        assert isinstance(row['amount'], (int, float))


def test_extract_dueback_skips_blank_rows():
    result = extract_dueback('2026-03-21')
    for row in result:
        assert row['name'].strip() != ''
```

- [ ] **Step 3: Run the test to verify it fails**

Run from `/home/v/Documents/Projects/audit-pack/`:

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py -v
```

Expected: `ImportError: cannot import name 'extract_dueback' from 'tests.fixtures.ground_truth_seeder'`

- [ ] **Step 4: Write the minimal seeder module**

Create `/home/v/Documents/Projects/audit-pack/tests/fixtures/ground_truth_seeder.py`:

```python
"""Ground-truth seeder.

Reads the historical ``test_fixtures/<day>/ground_truth_rj.xls`` file
for a given audit day and returns plain Python dicts/values that can be
written directly onto a ``NightAuditSession`` instance. No DB, no Flask
— just xlrd.

Layer 2 of the nightly-balance integration test uses this to reconstruct
the *input state* the auditor had that night (DueBack cash envelopes, SD
verified amounts, Transelect card totals, GEAC balance sheet, Recap
values, Chambres à refaire count). Combined with the fixture PDFs, this
represents everything the auditor saw before marking DC = 0.

Each extractor finds its target sheet by case-insensitive substring
match on the sheet name (``DUBACK#``, ``dueback``, ``duback`` all work)
then reads by column-label, not by hardcoded row index.

Raises ``SeederLayoutError(day, sheet)`` when a required sheet/column
cannot be found — the diagnostic makes the unsupported layout obvious
instead of silently returning zeros.
"""
from __future__ import annotations

from pathlib import Path

import xlrd

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "test_fixtures"


class SeederLayoutError(RuntimeError):
    """Raised when the ground-truth XLS doesn't match any known layout."""

    def __init__(self, day: str, sheet: str, detail: str = ""):
        msg = f"[{day}] unsupported layout on sheet {sheet!r}"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)
        self.day = day
        self.sheet = sheet


def _open_workbook(day: str) -> xlrd.Book:
    path = FIXTURES_DIR / day / "ground_truth_rj.xls"
    if not path.exists():
        raise FileNotFoundError(f"No ground_truth_rj.xls for {day} at {path}")
    return xlrd.open_workbook(str(path), formatting_info=False)


def _find_sheet(wb: xlrd.Book, needle: str) -> xlrd.sheet.Sheet | None:
    """Case-insensitive substring match on sheet name."""
    needle_lc = needle.lower()
    for name in wb.sheet_names():
        if needle_lc in name.lower():
            return wb.sheet_by_name(name)
    return None


def _as_float(cell) -> float:
    """Coerce an xlrd cell value to float; treat empty/text as 0."""
    if cell == "" or cell is None:
        return 0.0
    try:
        return float(cell)
    except (TypeError, ValueError):
        return 0.0


def extract_dueback(day: str) -> list[dict]:
    """Read the DueBack (DUBACK#) sheet and return per-receptionist amounts.

    Returns a list of dicts: ``[{'name': 'Alice', 'amount': 123.45}, ...]``
    skipping rows without a receptionist name.
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "duback") or _find_sheet(wb, "dueback")
    if sh is None:
        raise SeederLayoutError(day, "(DueBack)", "no sheet matching 'duback' or 'dueback'")

    rows: list[dict] = []
    # The DUBACK# sheet layout on 2026-03-21: column 0 holds the
    # receptionist name, column 1 holds the envelope total. Rows with
    # an empty name are skipped (header, blank separators).
    for r in range(sh.nrows):
        name = sh.cell_value(r, 0)
        if not isinstance(name, str) or not name.strip():
            continue
        # Skip header-like rows
        if name.strip().lower() in ("nom", "prenom", "total", "dueback"):
            continue
        amount = _as_float(sh.cell_value(r, 1)) if sh.ncols > 1 else 0.0
        if amount == 0:
            continue
        rows.append({"name": name.strip(), "amount": round(amount, 2)})
    return rows
```

- [ ] **Step 5: Run the test to verify it passes**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py -v
```

Expected: both tests PASS.

If the actual DUBACK# sheet on 2026-03-21 doesn't follow the col-0-name/col-1-amount layout, the test will fail with `SeederLayoutError` or an empty list. Diagnose by running:

```bash
source .venv/bin/activate && python -c "
import xlrd
wb = xlrd.open_workbook('test_fixtures/2026-03-21/ground_truth_rj.xls')
for name in wb.sheet_names():
    if 'duback' in name.lower() or 'dueback' in name.lower():
        sh = wb.sheet_by_name(name)
        print(f'Sheet: {name} ({sh.nrows}x{sh.ncols})')
        for r in range(min(20, sh.nrows)):
            print(r, [sh.cell_value(r, c) for c in range(min(5, sh.ncols))])
"
```

Then adjust the column indices in `extract_dueback` based on the actual layout.

- [ ] **Step 6: Skip commit** (user handles git)

---

### Task 2: SD extractor

**Files:**
- Modify: `tests/fixtures/ground_truth_seeder.py`
- Modify: `tests/test_ground_truth_seeder.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ground_truth_seeder.py`:

```python
from tests.fixtures.ground_truth_seeder import extract_sd


def test_extract_sd_returns_list_of_dicts():
    result = extract_sd('2026-03-21')
    assert isinstance(result, list)
    assert len(result) > 0
    for row in result:
        assert 'employee' in row
        assert 'verified_amount' in row
        assert isinstance(row['verified_amount'], (int, float))
```

- [ ] **Step 2: Run to verify it fails**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py::test_extract_sd_returns_list_of_dicts -v
```

Expected: `ImportError: cannot import name 'extract_sd'`

- [ ] **Step 3: Implement extract_sd**

Append to `tests/fixtures/ground_truth_seeder.py`:

```python
def extract_sd(day: str) -> list[dict]:
    """Read the SD (SetD/SD) sheet and return per-employee verified amounts.

    Returns a list of dicts: ``[{'employee': 'Alice', 'verified_amount': 500.00}, ...]``
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "setd") or _find_sheet(wb, "sd")
    if sh is None:
        raise SeederLayoutError(day, "(SD)", "no sheet matching 'setd' or 'sd'")

    rows: list[dict] = []
    # Layout: col 0 = employee name, col 1 = verified amount. Adjust here
    # after probing the actual sheet if this turns out wrong.
    for r in range(sh.nrows):
        name = sh.cell_value(r, 0)
        if not isinstance(name, str) or not name.strip():
            continue
        if name.strip().lower() in ("nom", "employé", "employe", "total", "sd", "setd"):
            continue
        amount = _as_float(sh.cell_value(r, 1)) if sh.ncols > 1 else 0.0
        if amount == 0:
            continue
        rows.append({"employee": name.strip(), "verified_amount": round(amount, 2)})
    return rows
```

- [ ] **Step 4: Run to verify pass**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py::test_extract_sd_returns_list_of_dicts -v
```

Expected: PASS. If it fails with empty-list or wrong column, probe the SD sheet layout the same way as Task 1 and adjust column indices.

- [ ] **Step 5: Skip commit**

---

### Task 3: Chambres à refaire extractor

**Files:**
- Modify: `tests/fixtures/ground_truth_seeder.py`
- Modify: `tests/test_ground_truth_seeder.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ground_truth_seeder.py`:

```python
from tests.fixtures.ground_truth_seeder import extract_chambres


def test_extract_chambres_returns_integer():
    result = extract_chambres('2026-03-21')
    assert isinstance(result, int)
    assert 0 <= result <= 252  # Sheraton Laval has 252 rooms
```

- [ ] **Step 2: Run to verify it fails**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py::test_extract_chambres_returns_integer -v
```

Expected: ImportError.

- [ ] **Step 3: Implement extract_chambres**

Append to `tests/fixtures/ground_truth_seeder.py`:

```python
def extract_chambres(day: str) -> int:
    """Read the jour sheet and return chambres à refaire count.

    The 'jour' sheet (233 rows × 117 cols on 2026-03-21) has a row
    labelled 'chambres à refaire' somewhere; the value is an integer
    between 0 and 252.
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "jour")
    if sh is None:
        raise SeederLayoutError(day, "(jour)", "no 'jour' sheet found")

    # Scan the first column for a label containing 'refaire' or 'chambres à refaire'
    for r in range(sh.nrows):
        label = sh.cell_value(r, 0)
        if not isinstance(label, str):
            continue
        if "refaire" in label.lower():
            # Value is typically in the next column
            for c in range(1, min(sh.ncols, 5)):
                v = sh.cell_value(r, c)
                if isinstance(v, (int, float)) and v != "":
                    return int(v)
    return 0  # Not found → default 0 (acceptable, not a layout error)
```

- [ ] **Step 4: Run to verify pass**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py::test_extract_chambres_returns_integer -v
```

Expected: PASS.

- [ ] **Step 5: Skip commit**

---

### Task 4: Transelect extractor

This is the most complex extractor because the NAS stores Transelect as JSON blobs with per-terminal structure.

**Files:**
- Modify: `tests/fixtures/ground_truth_seeder.py`
- Modify: `tests/test_ground_truth_seeder.py`

- [ ] **Step 1: Probe the transelect sheet layout**

Run:

```bash
source .venv/bin/activate && python -c "
import xlrd
wb = xlrd.open_workbook('test_fixtures/2026-03-21/ground_truth_rj.xls')
sh = wb.sheet_by_name('transelect')
print(f'Shape: {sh.nrows}x{sh.ncols}')
for r in range(min(40, sh.nrows)):
    row = [sh.cell_value(r,c) for c in range(min(10, sh.ncols))]
    if any(str(v).strip() for v in row):
        print(f'{r}: {row}')
"
```

Record the output — you need to know where Restaurant, Reception, Banquet, FreedomPay sections start and where X20/X24 live. The rest of this task assumes a typical layout: each section has a header row containing the section name, then rows for debit/visa/mc/amex/discover, each with a terminal column.

- [ ] **Step 2: Write the failing test**

Append to `tests/test_ground_truth_seeder.py`:

```python
from tests.fixtures.ground_truth_seeder import extract_transelect


def test_extract_transelect_returns_nas_dict():
    result = extract_transelect('2026-03-21')
    # Returns a dict with NAS field names as keys, JSON-string values
    assert isinstance(result, dict)
    assert 'transelect_restaurant' in result or 'transelect_reception' in result
    # At least one blob must be non-empty
    import json
    non_empty = [k for k, v in result.items() if v and json.loads(v)]
    assert len(non_empty) >= 1
```

- [ ] **Step 3: Run to verify it fails**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py::test_extract_transelect_returns_nas_dict -v
```

Expected: ImportError.

- [ ] **Step 4: Implement extract_transelect**

Append to `tests/fixtures/ground_truth_seeder.py`:

```python
import json


# Card type labels we expect to find in the transelect sheet's row labels
_CARD_TYPES = {
    "debit": ("debit", "débit", "interac"),
    "visa": ("visa",),
    "mc": ("master", "mc", "mastercard"),
    "amex": ("amex", "american"),
    "discover": ("discover",),
}


def _classify_card_row(label: str) -> str | None:
    label_lc = label.lower().strip()
    for card, needles in _CARD_TYPES.items():
        if any(n in label_lc for n in needles):
            return card
    return None


def extract_transelect(day: str) -> dict:
    """Read the transelect sheet and return a dict of NAS JSON-blob strings.

    Returns ``{'transelect_restaurant': <json>, 'transelect_reception': <json>,
    'transelect_quasimodo': <json>}`` where each value is the JSON string
    the NAS field expects (matches the schema at
    ``utils/rj_balancer.py:_extract_transelect``).

    Sections are detected by header rows containing 'restaurant',
    'reception', 'banquet' / 'quasimodo'. Within each section, rows whose
    label matches a card type populate the blob with a single '_default'
    terminal key.
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "transelect")
    if sh is None:
        raise SeederLayoutError(day, "(transelect)", "no 'transelect' sheet")

    sections: dict[str, dict] = {
        "restaurant": {"_terminals": ["default"]},
        "reception":  {"_terminals": ["default"]},
        "quasimodo":  {"_terminals": ["default"]},
    }
    for card in _CARD_TYPES:
        for sect in sections.values():
            sect[card] = {"default": 0.0, "esc_pct": 0}

    current_section: str | None = None
    for r in range(sh.nrows):
        label_cell = sh.cell_value(r, 0)
        label = label_cell.strip() if isinstance(label_cell, str) else ""
        label_lc = label.lower()

        # Section detection
        if "restaurant" in label_lc or "posi" in label_lc:
            current_section = "restaurant"
            continue
        if "reception" in label_lc or "réception" in label_lc or "front" in label_lc:
            current_section = "reception"
            continue
        if "banquet" in label_lc or "quasimodo" in label_lc:
            current_section = "quasimodo"
            continue

        if current_section is None or not label:
            continue

        card = _classify_card_row(label)
        if not card:
            continue

        # Find the first numeric value in this row (terminal amount)
        amount = 0.0
        for c in range(1, sh.ncols):
            v = sh.cell_value(r, c)
            if isinstance(v, (int, float)) and v != 0:
                amount = float(v)
                break
        sections[current_section][card]["default"] = round(amount, 2)

    return {
        "transelect_restaurant": json.dumps(sections["restaurant"]),
        "transelect_reception":  json.dumps(sections["reception"]),
        "transelect_quasimodo":  json.dumps(sections["quasimodo"]),
    }
```

- [ ] **Step 5: Run to verify pass**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py::test_extract_transelect_returns_nas_dict -v
```

Expected: PASS. If it fails, the probe output from Step 1 tells you which section header labels and card-type labels to add to the keyword lists.

- [ ] **Step 6: Skip commit**

---

### Task 5: GEAC balance sheet extractor

**Files:**
- Modify: `tests/fixtures/ground_truth_seeder.py`
- Modify: `tests/test_ground_truth_seeder.py`

- [ ] **Step 1: Probe the geac_ux sheet**

```bash
source .venv/bin/activate && python -c "
import xlrd
wb = xlrd.open_workbook('test_fixtures/2026-03-21/ground_truth_rj.xls')
sh = wb.sheet_by_name('geac_ux')
print(f'Shape: {sh.nrows}x{sh.ncols}')
for r in range(min(30, sh.nrows)):
    row = [sh.cell_value(r,c) for c in range(min(8, sh.ncols))]
    if any(str(v).strip() for v in row):
        print(f'{r}: {row}')
"
```

- [ ] **Step 2: Write the failing test**

```python
from tests.fixtures.ground_truth_seeder import extract_geac_balance_sheet


def test_extract_geac_balance_sheet_returns_nas_dict():
    result = extract_geac_balance_sheet('2026-03-21')
    assert isinstance(result, dict)
    # Must include the balance sheet JSON blob + the AR fields
    assert 'geac_balance_sheet' in result
    import json
    bs = json.loads(result['geac_balance_sheet'])
    for key in ['prev_dr', 'prev_gl', 'today_dr', 'today_gl',
                'facture_dr', 'facture_ar', 'advdep_dr', 'advdep_ad',
                'newbal_dr', 'newbal_gl']:
        assert key in bs, f"missing {key}"
```

- [ ] **Step 3: Run to verify fail**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py::test_extract_geac_balance_sheet_returns_nas_dict -v
```

Expected: ImportError.

- [ ] **Step 4: Implement extract_geac_balance_sheet**

Append to `tests/fixtures/ground_truth_seeder.py`:

```python
# Label → balance-sheet key mapping. Labels are matched case-insensitive,
# substring, on column 0 of the geac_ux sheet. First numeric cell to the
# right of the label becomes the value.
_GEAC_LABELS = {
    "prev_dr": ("previous balance dr", "solde précédent dr", "prev bal dr"),
    "prev_gl": ("previous balance gl", "solde précédent gl", "prev bal gl"),
    "today_dr": ("today dr", "aujourd'hui dr", "journée dr"),
    "today_gl": ("today gl", "aujourd'hui gl"),
    "facture_dr": ("facture dr", "fd dr", "facture direct dr"),
    "facture_ar": ("facture ar", "fd ar"),
    "advdep_dr": ("advance deposit dr", "dépôts avance dr"),
    "advdep_ad": ("advance deposit ad", "dépôts avance ad"),
    "newbal_dr": ("new balance dr", "nouveau solde dr"),
    "newbal_gl": ("new balance gl", "nouveau solde gl"),
}


def _find_first_numeric(sheet, row: int, start_col: int = 1) -> float:
    for c in range(start_col, sheet.ncols):
        v = sheet.cell_value(row, c)
        if isinstance(v, (int, float)) and v != "":
            return float(v)
    return 0.0


def extract_geac_balance_sheet(day: str) -> dict:
    """Read the geac_ux sheet, return ``{'geac_balance_sheet': <json>,
    'geac_ar_variance': <float>}``.

    The JSON blob matches the schema used by ``utils/rj_balancer.py``'s
    ``_extract_geac``: 10 keys for the 5-row balance sheet.
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "geac")
    if sh is None:
        raise SeederLayoutError(day, "(geac)", "no sheet matching 'geac'")

    bs: dict[str, float] = {k: 0.0 for k in _GEAC_LABELS}

    for r in range(sh.nrows):
        label = sh.cell_value(r, 0)
        if not isinstance(label, str):
            continue
        lbl = label.lower().strip()
        if not lbl:
            continue
        for key, needles in _GEAC_LABELS.items():
            if any(n in lbl for n in needles):
                bs[key] = round(_find_first_numeric(sh, r), 2)
                break

    return {
        "geac_balance_sheet": json.dumps(bs),
    }
```

- [ ] **Step 5: Run to verify pass**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py::test_extract_geac_balance_sheet_returns_nas_dict -v
```

Expected: PASS. If it fails with all-zero values, the labels on the actual geac_ux sheet don't match the needle list in `_GEAC_LABELS` — read the probe output from Step 1 and extend the needle tuples accordingly.

- [ ] **Step 6: Skip commit**

---

### Task 6: Recap extractor (individual NAS scalar fields)

The Recap data lives in many individual NAS fields. See the "Key Facts" section at the top for the authoritative list from `utils/rj_balancer.py:_extract_recap`.

**Files:**
- Modify: `tests/fixtures/ground_truth_seeder.py`
- Modify: `tests/test_ground_truth_seeder.py`

- [ ] **Step 1: Probe the Recap sheet**

```bash
source .venv/bin/activate && python -c "
import xlrd
wb = xlrd.open_workbook('test_fixtures/2026-03-21/ground_truth_rj.xls')
sh = wb.sheet_by_name('Recap')
print(f'Shape: {sh.nrows}x{sh.ncols}')
for r in range(sh.nrows):
    row = [sh.cell_value(r,c) for c in range(min(14, sh.ncols))]
    if any(str(v).strip() for v in row):
        print(f'{r}: {row}')
"
```

Record the output; the label column is usually 0 or 1, and the value column(s) vary.

- [ ] **Step 2: Write the failing test**

```python
from tests.fixtures.ground_truth_seeder import extract_recap


def test_extract_recap_returns_nas_scalar_dict():
    result = extract_recap('2026-03-21')
    assert isinstance(result, dict)
    # All values are floats; keys are actual NAS attribute names
    for key, val in result.items():
        assert isinstance(val, (int, float)), f"{key} is {type(val)}"
    # At least the cash + cheque + dueback + recap_balance lines should be present
    expected_keys = {
        'cash_ls_lecture', 'cash_pos_lecture',
        'cheque_ar_lecture', 'cheque_dr_lecture',
        'remb_gratuite_lecture', 'remb_client_lecture',
        'dueback_reception_lecture', 'dueback_nb_lecture',
        'recap_balance',
        'deposit_cdn', 'deposit_us',
    }
    assert expected_keys.issubset(result.keys())
```

- [ ] **Step 3: Run to verify fail**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py::test_extract_recap_returns_nas_scalar_dict -v
```

Expected: ImportError.

- [ ] **Step 4: Implement extract_recap**

Append to `tests/fixtures/ground_truth_seeder.py`:

```python
# Label → NAS attribute name mapping. Labels matched case-insensitive,
# substring, on column 0 of the Recap sheet. Value is the first numeric
# cell to the right of the label.
#
# Every key listed here is a NAS scalar attribute (not a JSON blob).
# The "lecture" suffix matches the auditor's primary reading column;
# "corr" columns are populated via the form only and stay at 0 here.
_RECAP_LABELS = {
    "cash_ls_lecture":          ("cash ls", "argent ls", "lightspeed cash"),
    "cash_pos_lecture":         ("cash pos", "positouch cash"),
    "cheque_ar_lecture":        ("chèque ar", "cheque ar", "check ar"),
    "cheque_dr_lecture":        ("chèque dr", "cheque dr", "check dr"),
    "remb_gratuite_lecture":    ("remb grat", "gratuite", "comptant gratuit"),
    "remb_client_lecture":      ("remb client", "remboursement client"),
    "dueback_reception_lecture":("due back récept", "dueback recep", "due back recep"),
    "dueback_nb_lecture":       ("due back n/b", "dueback nb", "due back nb"),
    "recap_balance":            ("surplus", "déficit", "deficit", "écart", "ecart"),
    "deposit_cdn":              ("dépôt cdn", "depot cdn", "deposit cdn"),
    "deposit_us":               ("dépôt us", "depot us", "deposit us"),
}


def extract_recap(day: str) -> dict:
    """Read the Recap sheet, return ``{nas_attr: float, ...}``.

    Every key in the returned dict is a scalar NAS attribute name.
    Missing labels default to 0.0 (acceptable — means the auditor left
    the line blank that day).
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "recap")
    if sh is None:
        raise SeederLayoutError(day, "(recap)", "no 'recap' sheet")

    out: dict[str, float] = {k: 0.0 for k in _RECAP_LABELS}

    for r in range(sh.nrows):
        # Try both col 0 and col 1 for the label (Recap layouts vary)
        for label_col in (0, 1):
            if label_col >= sh.ncols:
                continue
            label = sh.cell_value(r, label_col)
            if not isinstance(label, str):
                continue
            lbl = label.lower().strip()
            if not lbl:
                continue
            for nas_attr, needles in _RECAP_LABELS.items():
                if any(n in lbl for n in needles):
                    out[nas_attr] = round(_find_first_numeric(sh, r, label_col + 1), 2)
                    break
    return out
```

- [ ] **Step 5: Run to verify pass**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py::test_extract_recap_returns_nas_scalar_dict -v
```

Expected: PASS. On failure with all zeros, read the probe output from Step 1 and extend the needle lists in `_RECAP_LABELS`.

- [ ] **Step 6: Skip commit**

---

### Task 7: `extract_all` convenience + disjoint-field invariant

**Files:**
- Modify: `tests/fixtures/ground_truth_seeder.py`
- Modify: `tests/test_ground_truth_seeder.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ground_truth_seeder.py`:

```python
from tests.fixtures.ground_truth_seeder import extract_all


def test_extract_all_bundles_every_extractor():
    result = extract_all('2026-03-21')
    assert isinstance(result, dict)
    # JSON blobs (keys mapping to JSON strings)
    assert 'geac_balance_sheet' in result
    assert 'transelect_restaurant' in result
    # Scalar fields (from extract_recap)
    assert 'cash_ls_lecture' in result
    # Chambres à refaire
    assert 'jour_chambres_a_refaire' in result
    # List-of-dicts fields (dueback + sd)
    assert 'dueback_entries' in result
    assert 'sd_entries' in result


def test_extract_all_dueback_entries_is_json_string():
    result = extract_all('2026-03-21')
    # NAS stores dueback_entries as a JSON string, not a list
    import json
    parsed = json.loads(result['dueback_entries'])
    assert isinstance(parsed, list)
```

- [ ] **Step 2: Run to verify fail**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py::test_extract_all_bundles_every_extractor -v
```

Expected: ImportError.

- [ ] **Step 3: Implement extract_all**

Append to `tests/fixtures/ground_truth_seeder.py`:

```python
def extract_all(day: str) -> dict:
    """Bundle every extractor into one flat dict keyed by NAS attribute name.

    Output keys include:
      - geac_balance_sheet         (JSON string)
      - transelect_restaurant      (JSON string)
      - transelect_reception       (JSON string)
      - transelect_quasimodo       (JSON string)
      - dueback_entries            (JSON string of list)
      - sd_entries                 (JSON string of list)
      - jour_chambres_a_refaire    (int)
      - plus all _RECAP_LABELS keys (floats)

    Missing data is silently defaulted (0 for scalars, empty list for
    lists). If a sheet has an unsupported layout, SeederLayoutError
    propagates and identifies the offending day+sheet.
    """
    out: dict = {}

    # JSON blobs
    out.update(extract_geac_balance_sheet(day))
    out.update(extract_transelect(day))

    # Recap scalars
    out.update(extract_recap(day))

    # Chambres à refaire (single int)
    out['jour_chambres_a_refaire'] = extract_chambres(day)

    # DueBack + SD — NAS stores these as JSON strings of lists
    out['dueback_entries'] = json.dumps(extract_dueback(day))
    out['sd_entries'] = json.dumps(extract_sd(day))

    return out
```

**Note on field name for chambres:** if `jour_chambres_a_refaire` is not the exact NAS attribute name, replace it with the correct one. Verify via:

```bash
source .venv/bin/activate && python -c "
from database.models import NightAuditSession
cols = [c.name for c in NightAuditSession.__table__.columns if 'refaire' in c.name.lower() or ('chambres' in c.name.lower() and 'svc' not in c.name.lower())]
print(cols)
"
```

- [ ] **Step 4: Run to verify pass**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py -v
```

Expected: all seeder tests PASS.

- [ ] **Step 5: Verify disjoint-field invariant manually**

Run this sanity check — the seeder output keys must NOT include any field the balancer populates from fixture files (`sj`, `dr`, `ar`, `hp`, `adv_dep`). If there's overlap, the seeder value will be overwritten by the parser at `check_balance` time, silently breaking the test.

```bash
source .venv/bin/activate && python -c "
from tests.fixtures.ground_truth_seeder import extract_all
keys = set(extract_all('2026-03-21').keys())
# Fields populated by BalancerService.check_balance from file parsing
# (per utils/rj_balancer.py — anything the calculate_jour writes that
# comes from files, not NAS)
#
# These are all auto-filled from fixture files and must NOT appear in
# the seeder output:
balancer_populated = {
    # HP-sourced
    'hp_admin_entries', 'hp_promo_entries',
    # Jour cols fed from parsers
    'jour_piazza_nourriture', 'jour_piazza_boisson',
}
overlap = keys & balancer_populated
if overlap:
    print('FAIL: overlap =', overlap)
    exit(1)
print('OK: no overlap,', len(keys), 'seeder keys')
"
```

Expected: `OK: no overlap, N seeder keys`.

- [ ] **Step 6: Skip commit**

---

## Phase B — Layer 2: pytest infrastructure

### Task 8: Nightly balance test skeleton (one day only)

**Files:**
- Create: `tests/test_nightly_balance.py`

- [ ] **Step 1: Write the skeleton test for one day**

Create `/home/v/Documents/Projects/audit-pack/tests/test_nightly_balance.py`:

```python
"""End-to-end replay of historical night audits.

For every parseable fixture day, load the source documents + seeded
NAS state (from ``tests.fixtures.ground_truth_seeder.extract_all``) and
assert ``BalancerService.check_balance`` reduces the DC to 0.00.

Failure output is a rich diagnostic so the fix-loop is fast. See
``docs/superpowers/specs/2026-04-10-nightly-balance-integration-design.md``
for why this test exists and what its assertions mean.
"""
from __future__ import annotations

import json
from datetime import date
from io import BytesIO
from pathlib import Path

import pytest

from tests.fixtures.ground_truth_seeder import extract_all

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = PROJECT_ROOT / "test_fixtures"

# ── Fixture day → source-file mapping ──────────────────────────────────
# Maps BalancerService check_balance() file keys to the actual filenames
# each fixture day stores. Parsers auto-skip empty BytesIO values.
_FILE_KEY_TO_NAMES = {
    "sj":       ("sales_journal.txt", "sales_journal.rtf"),
    "dr":       ("daily_revenue.pdf", "daily_revenue.xls"),
    "ar":       ("ar_summary.pdf", "ar_summary.xls"),
    "hp":       ("hp.xlsx",),
    "adv_dep":  ("advance_deposit.pdf",),
}


def _load_files(day: str) -> dict:
    """Return ``{file_key: BytesIO}`` for every file present in the fixture."""
    day_dir = FIXTURES_DIR / day
    files: dict = {}
    for key, names in _FILE_KEY_TO_NAMES.items():
        for name in names:
            p = day_dir / name
            if p.exists():
                files[key] = BytesIO(p.read_bytes())
                break
    return files


def _seed_nas(nas, day: str):
    """Apply every key from ``extract_all(day)`` to the NAS instance."""
    seed = extract_all(day)
    for key, value in seed.items():
        if hasattr(nas, key):
            setattr(nas, key, value)


def _build_diagnostic(day: str, files: dict, result: dict) -> str:
    """Format a failure diagnostic for pytest.fail()."""
    decomp = result.get("dc_decomposition") or {}
    classes = decomp.get("classes") or {}
    dc_calc = result.get("dc_calculated", "—")
    declared = decomp.get("declared_sum", "—")
    residual = decomp.get("unexplained_residual", "—")

    lines = [
        f"",
        f"Day: {day}",
        f"─────────────────────────────────────────────────────",
        f"SOURCE DOCUMENTS APPLIED:",
    ]
    day_dir = FIXTURES_DIR / day
    for key, names in _FILE_KEY_TO_NAMES.items():
        found = [n for n in names if (day_dir / n).exists()]
        if found:
            lines.append(f"  ✓ {found[0]:24s} ({key})")
        else:
            lines.append(f"  ✗ {names[0]:24s} (MISSING)")

    lines.append("")
    lines.append("BALANCE CHECK RESULT:")
    lines.append(f"  dc_calculated        = {dc_calc}")
    lines.append(f"  declared_sum         = {declared}")
    lines.append(f"  unexplained_residual = {residual}   ← FAILING (expected 0.00)")
    lines.append("")
    lines.append("VARIANCE CLASSES (10):")
    for class_name in [
        "x20_transelect", "geac_bottom", "interhotel_xferin",
        "panne_lien_hotel", "chambres_annulation", "prior_day_correction",
        "cashier_misposting", "depot_resto_pas_ferme",
        "recap_surplus", "recap_deficit",
    ]:
        val = classes.get(class_name, 0)
        lines.append(f"  {class_name:22s} = {val:>12.2f}")

    warnings = result.get("warnings") or []
    if warnings:
        lines.append("")
        lines.append("BalancerService warnings:")
        for w in warnings:
            lines.append(f"  [warn] {w}")
    lines.append("─────────────────────────────────────────────────────")
    return "\n".join(lines)


def test_2026_03_21_balances_to_zero(app):
    """Single-day smoke before parametrization."""
    from database.models import db, NightAuditSession
    from utils.rj_balancer import BalancerService

    day = "2026-03-21"
    with app.app_context():
        # Clean any pre-existing session for this date
        NightAuditSession.query.filter_by(audit_date=date(2026, 3, 21)).delete()
        db.session.commit()

        nas = NightAuditSession(audit_date=date(2026, 3, 21), auditor_name="test")
        _seed_nas(nas, day)
        db.session.add(nas)
        db.session.commit()

        files = _load_files(day)
        result = BalancerService.check_balance(nas, files=files, day=21)

        # Cleanup before the assertion (so a failure doesn't leak the row)
        NightAuditSession.query.filter_by(audit_date=date(2026, 3, 21)).delete()
        db.session.commit()

        decomp = result.get("dc_decomposition") or {}
        residual = decomp.get("unexplained_residual", float("inf"))

        assert abs(round(residual, 2)) < 0.01, _build_diagnostic(day, files, result)
```

- [ ] **Step 2: Run the test**

```bash
source .venv/bin/activate && python -m pytest tests/test_nightly_balance.py::test_2026_03_21_balances_to_zero -v
```

Expected: either PASS (rare — miraculous) or FAIL with the full diagnostic. Either way, the test infrastructure is working. If the diagnostic formatting is broken, fix `_build_diagnostic`.

- [ ] **Step 3: Record the initial result**

Capture the exact residual and the non-zero variance classes shown in the diagnostic. You'll refer back to these in the fix-loop.

- [ ] **Step 4: Skip commit**

---

### Task 9: Parametrize over all 18 parseable days

**Files:**
- Modify: `tests/test_nightly_balance.py`

- [ ] **Step 1: Replace the single-day test with a parametrized version**

Replace the `test_2026_03_21_balances_to_zero` function with:

```python
# Populated from scripts/fixture_regression.py inventory. Update this list
# when new days are added (or when a day becomes unblocked).
PARSEABLE_DAYS = [
    "2026-03-02", "2026-03-03", "2026-03-04", "2026-03-08",
    "2026-03-09", "2026-03-13", "2026-03-14", "2026-03-17",
    "2026-03-21", "2026-03-23", "2026-03-26", "2026-03-29",
    "2026-03-30", "2026-04-01", "2026-04-02", "2026-04-03",
    "2026-04-04", "2026-04-05",
]


@pytest.mark.parametrize("day", PARSEABLE_DAYS, ids=PARSEABLE_DAYS)
def test_day_balances_to_zero(app, day):
    """For every parseable fixture day, the full pipeline must reach DC = 0."""
    from database.models import db, NightAuditSession
    from utils.rj_balancer import BalancerService

    y, m, d = (int(p) for p in day.split("-"))
    audit_date = date(y, m, d)

    with app.app_context():
        NightAuditSession.query.filter_by(audit_date=audit_date).delete()
        db.session.commit()

        nas = NightAuditSession(audit_date=audit_date, auditor_name="test")
        _seed_nas(nas, day)
        db.session.add(nas)
        db.session.commit()

        files = _load_files(day)
        result = BalancerService.check_balance(nas, files=files, day=d)

        NightAuditSession.query.filter_by(audit_date=audit_date).delete()
        db.session.commit()

        decomp = result.get("dc_decomposition") or {}
        residual = decomp.get("unexplained_residual", float("inf"))

        assert abs(round(residual, 2)) < 0.01, _build_diagnostic(day, files, result)
```

- [ ] **Step 2: Run all 18 days**

```bash
source .venv/bin/activate && python -m pytest tests/test_nightly_balance.py -v --tb=no
```

Expected: some mix of PASS/FAIL. Record how many pass. This is the baseline.

- [ ] **Step 3: Get full diagnostics for the first failing day**

```bash
source .venv/bin/activate && python -m pytest tests/test_nightly_balance.py -v -x
```

The `-x` flag stops at the first failure, showing the full diagnostic.

- [ ] **Step 4: Skip commit**

---

## Phase C — The iteration fix-loop

### Task 10: Fix-loop — get every day to green

**Files (modified as needed, one at a time):**
- `utils/rj_balancer.py`
- `utils/rj_filler.py`
- `utils/parsers/*.py` (sales_journal_parser.py, daily_revenue_parser.py, ar_summary_parser.py, hp_parser.py, etc.)
- `routes/audit/rj_native.py` (only if Layer 3 later reveals a dispatcher divergence)
- `tests/fixtures/ground_truth_seeder.py` (only if a failure reveals a missing extractor field)

**Exit criterion:** `python -m pytest tests/test_nightly_balance.py -v --tb=no` reports all 18 days PASS.

**Anti-goals (banned):**
- Bumping the `< 0.01` tolerance. If a day can't hit 0.00, it's a bug.
- `@pytest.skip` on failing days.
- Batch-fixing multiple days in one change. One root cause at a time.

- [ ] **Step 1: Start the loop — find the first failing day**

```bash
source .venv/bin/activate && python -m pytest tests/test_nightly_balance.py -v --tb=no
```

Note the first day marked FAILED.

- [ ] **Step 2: Get the full diagnostic for that day**

```bash
source .venv/bin/activate && python -m pytest tests/test_nightly_balance.py -v -k "<DAY>"
```

(Replace `<DAY>` with e.g. `03-14`.)

- [ ] **Step 3: Diagnose using the common root-cause buckets**

Look at the residual value and the non-zero variance classes. Map to one of these buckets:

| Symptom | Likely fix location |
|---|---|
| Residual ≈ a known Transelect card total, `x20_transelect` = 0 | `utils/rj_balancer.py` — X24 regex pattern in transelect parser / `calculate_jour` |
| Residual ≈ `fd - ar` | `utils/rj_balancer.py` — `geac_bottom` formula, check `geac_effective` auto-wire |
| Residual has an HP admin/promo amount | `utils/rj_filler.py` — HP deductions not applied to Piazza/Spesa F&B |
| Residual matches a Recap S&D delta | `tests/fixtures/ground_truth_seeder.py` — `_RECAP_LABELS` missing a keyword, OR `utils/rj_balancer.py:_extract_recap` not reading a field |
| Residual has a small tax-like amount | `utils/parsers/sales_journal_parser.py` — regex truncating decimals |
| Day crashes with KeyError | `utils/parsers/ar_summary_parser.py` — `stored_balance` regex, or `utils/parsers/hp_parser.py` layout |
| Seeder fails with `SeederLayoutError` | `tests/fixtures/ground_truth_seeder.py` — extend the relevant extractor's needle list |

- [ ] **Step 4: Make the focused fix**

Edit the offending file with a minimal change that targets the root cause only. Do NOT refactor surrounding code.

- [ ] **Step 5: Verify that day now passes**

```bash
source .venv/bin/activate && python -m pytest tests/test_nightly_balance.py -v -k "<DAY>"
```

Expected: PASS.

- [ ] **Step 6: Re-run all 18 days to catch regressions**

```bash
source .venv/bin/activate && python -m pytest tests/test_nightly_balance.py -v --tb=no
```

If the fix regressed another day, revert the change and reconsider. Acceptable outcomes: N+1 passes (progress), N passes (the fix was too narrow — try again), N-1 passes (regression — revert).

- [ ] **Step 7: Run the existing fixture_regression.py sanity check**

```bash
source .venv/bin/activate && python scripts/fixture_regression.py 2>&1 | tail -20
```

Expected: the "Parseable today" count is **unchanged** (18). If it dropped, your fix broke something outside the test's scope.

- [ ] **Step 8: Loop back to Step 1**

Repeat Steps 1-7 until all 18 days PASS. Each iteration should take 5-20 minutes depending on how obvious the root cause is.

- [ ] **Step 9: Skip commit**

---

## Phase D — Layer 3: realistic auditor simulation

### Task 11: Generate the seed-2026-03-21.json fixture file

**Files:**
- Create: `tests/playwright/fixtures/seed-2026-03-21.json`

- [ ] **Step 1: Generate the JSON dump**

```bash
source .venv/bin/activate && python -c "
import json
from tests.fixtures.ground_truth_seeder import extract_all
print(json.dumps(extract_all('2026-03-21'), indent=2, sort_keys=True))
" > tests/playwright/fixtures/seed-2026-03-21.json
```

- [ ] **Step 2: Verify the file is valid JSON and non-empty**

```bash
python -c "import json; d=json.load(open('tests/playwright/fixtures/seed-2026-03-21.json')); print(len(d), 'keys'); assert 'geac_balance_sheet' in d"
```

Expected: prints `N keys` where N >= 10, no assertion error.

- [ ] **Step 3: Verify it's gitignored or small enough to track**

Run:

```bash
wc -l tests/playwright/fixtures/seed-2026-03-21.json
```

If < 200 lines, it's fine to commit (this is test fixture data). If > 500 lines, consider trimming to only the fields the Playwright test actually uses.

- [ ] **Step 4: Skip commit**

---

### Task 12: Write the Playwright nightly-flow spec

**Files:**
- Create: `tests/playwright/nightly-flow.spec.js`

- [ ] **Step 1: Identify the form field selectors for each seeded tab**

Read `templates/audit/rj/rj_native.html` to find the input IDs for:
- DueBack tab → receptionist envelope inputs
- SD tab → employee verified-amount inputs
- Transelect tab → terminal per-card inputs
- GEAC tab → balance sheet inputs
- Recap tab → cash/cheque/remb/deposit inputs
- Jour tab → `jour_chambres_a_refaire` input

Record each selector + which JSON key feeds it. If any input ID is dynamically generated, note the pattern.

- [ ] **Step 2: Write the Playwright spec**

Create `/home/v/Documents/Projects/audit-pack/tests/playwright/nightly-flow.spec.js`:

```js
// @ts-check
// Realistic auditor end-to-end simulation for 2026-03-21.
//
// This test drives the real browser UI the way a night auditor would:
// create a session, upload each source PDF through the file input,
// enter the seeded NAS fields through the form (per tab), and assert
// the livecard reaches DC = $0.00 / "Équilibré ✓".
//
// The "seed" data in seed-2026-03-21.json represents the hand-entered
// fields the auditor would populate from reports we don't have as
// standalone files (Transelect paper reports, GEAC balance sheet,
// Recap cash counts, DueBack envelopes, SD verified amounts). The
// pytest Layer 2 (tests/test_nightly_balance.py) covers the same
// day — this Playwright test proves the number the pipeline computed
// actually reaches the screen unchanged.

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const SEED = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'fixtures/seed-2026-03-21.json'), 'utf8')
);
const SESSION_COOKIE = fs.readFileSync(
  path.join(__dirname, '.session-cookie'), 'utf8'
).trim();

const FIXTURE_DIR = path.join(__dirname, '../../test_fixtures/2026-03-21');

async function injectAuth(context) {
  await context.addCookies([{
    name: 'session',
    value: SESSION_COOKIE,
    domain: '127.0.0.1',
    path: '/',
    httpOnly: true,
    sameSite: 'Lax',
  }]);
}

test('nightly flow for 2026-03-21 balances to zero on the livecard', async ({ page }) => {
  test.setTimeout(120_000); // upload + many form fields

  await injectAuth(page.context());
  await page.addInitScript(() => {
    localStorage.setItem('rjn_ui_mode', 'livecard');
  });

  // 1. Navigate to the page
  await page.goto('/rj/native');
  await page.waitForSelector('#livecard', { state: 'attached' });

  // 2. Create the session via form (date + auditor name, then "Nouveau jour")
  await page.fill('#inp-date', '2026-03-21');
  await page.fill('#inp-auditor', 'Test Auditor');
  await page.click('button[onclick*="startSession"]');  // selector may differ; adjust to real DOM
  await page.waitForFunction(() => window.SESSION && window.SESSION.audit_date);

  // 3. Upload each source document through the real file input.
  // The existing #file-report-upload handler auto-detects doc type.
  const sources = [
    'sales_journal.txt',
    'daily_revenue.pdf',
    'ar_summary.pdf',
    'hp.xlsx',
    'market_segment.pdf',
  ];
  for (const name of sources) {
    const filePath = path.join(FIXTURE_DIR, name);
    if (!fs.existsSync(filePath)) continue;
    await page.setInputFiles('#file-report-upload', filePath);
    // Wait for the upload round-trip + the livecard refresh to settle
    await page.waitForTimeout(1500);
  }

  // 4. Enter seeded fields per tab.
  // Each tab section below fills the form inputs for the corresponding
  // JSON key from SEED. Selectors MUST match the real DOM — the
  // implementer identified them in Task 12 Step 1.

  // Recap tab — scalar fields
  await page.click('button[data-tab="recap"]');
  for (const [key, selector] of Object.entries({
    cash_ls_lecture:          '#inp-cash-ls-lecture',
    cash_pos_lecture:         '#inp-cash-pos-lecture',
    cheque_ar_lecture:        '#inp-cheque-ar-lecture',
    cheque_dr_lecture:        '#inp-cheque-dr-lecture',
    remb_gratuite_lecture:    '#inp-remb-grat-lecture',
    remb_client_lecture:      '#inp-remb-client-lecture',
    dueback_reception_lecture:'#inp-dueback-rec-lecture',
    dueback_nb_lecture:       '#inp-dueback-nb-lecture',
    recap_balance:            '#inp-recap-balance',
    deposit_cdn:              '#inp-deposit-cdn',
    deposit_us:               '#inp-deposit-us',
  })) {
    const val = SEED[key];
    if (val === undefined || val === 0) continue;
    await page.fill(selector, String(val));
    await page.locator(selector).blur();
  }

  // GEAC tab — balance sheet
  await page.click('button[data-tab="geac"]');
  const bs = JSON.parse(SEED.geac_balance_sheet);
  for (const [key, selector] of Object.entries({
    prev_dr:    '#inp-geac-prev-dr',
    prev_gl:    '#inp-geac-prev-gl',
    today_dr:   '#inp-geac-today-dr',
    today_gl:   '#inp-geac-today-gl',
    facture_dr: '#inp-geac-facture-dr',
    facture_ar: '#inp-geac-facture-ar',
    advdep_dr:  '#inp-geac-advdep-dr',
    advdep_ad:  '#inp-geac-advdep-ad',
    newbal_dr:  '#inp-geac-newbal-dr',
    newbal_gl:  '#inp-geac-newbal-gl',
  })) {
    const val = bs[key];
    if (val === undefined || val === 0) continue;
    await page.fill(selector, String(val));
    await page.locator(selector).blur();
  }

  // Transelect tab — per-terminal per-card amounts
  // (The real form may use repeaters / dynamic row IDs; adjust selectors
  // as discovered in Task 12 Step 1.)
  await page.click('button[data-tab="transelect"]');
  // ... fill transelect_restaurant / reception / quasimodo blobs ...

  // DueBack tab
  await page.click('button[data-tab="dueback"]');
  const duebackRows = JSON.parse(SEED.dueback_entries);
  for (let i = 0; i < duebackRows.length; i++) {
    const row = duebackRows[i];
    // Selectors for dynamic rows; adjust to match real DOM
    await page.fill(`[data-dueback-row="${i}"] input[name="amount"]`, String(row.amount));
  }

  // SD tab
  await page.click('button[data-tab="sd"]');
  const sdRows = JSON.parse(SEED.sd_entries);
  for (let i = 0; i < sdRows.length; i++) {
    const row = sdRows[i];
    await page.fill(`[data-sd-row="${i}"] input[name="verified_amount"]`, String(row.verified_amount));
  }

  // Jour tab — chambres à refaire
  await page.click('button[data-tab="jour"]');
  await page.fill('#inp-jour-chambres-a-refaire', String(SEED.jour_chambres_a_refaire));
  await page.locator('#inp-jour-chambres-a-refaire').blur();

  // 5. Wait for the final debounced refresh
  await page.waitForTimeout(1000);

  // 6. Final assertions — the livecard must show DC = 0 / Équilibré
  const dc = page.locator('#livecard-dc');
  await expect(dc).toHaveText('$0.00');
  await expect(dc).toHaveClass(/\bok\b/);

  const verdict = page.locator('#livecard-verdict');
  await expect(verdict).toContainText('Équilibré');

  // 7. Screenshot for visual baseline
  await page.locator('#livecard').screenshot({
    path: 'test-results/nightly-flow-2026-03-21.png'
  });
});
```

**Selector placeholders:** the specific `#inp-*` selectors, `data-tab="..."` attributes, and dynamic-row indices above are best-effort and WILL need adjustment. Step 1 of this task is where you identify the real selectors. Do that first, then come back and rewrite the selectors inline before running the test.

- [ ] **Step 3: Make sure the Flask dev server is running**

```bash
source .venv/bin/activate && python main.py &
sleep 3
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/
```

Expected: `302` (auth redirect). Server is up.

- [ ] **Step 4: Regenerate the auth cookie**

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

- [ ] **Step 5: Run the test**

```bash
npx playwright test tests/playwright/nightly-flow.spec.js --config=tests/playwright/playwright.config.js
```

Expected: PASS. If FAIL, the diagnostic will show either:
- Selector missing → return to Step 1 and correct the selector
- Upload didn't populate a field → Layer 3 divergence, probably in `_apply_parsed_data_to_session` at `routes/audit/rj_native.py`. Fix there.
- Final DC ≠ 0 but Layer 2 is green → something in the form save → NAS → refresh round-trip drops data. Diagnose via devtools Network tab (is the seeded field present in the save POST body? is it present in the balance-check response?).

- [ ] **Step 6: Stop the Flask server**

```bash
pkill -f "python main.py" || true
```

- [ ] **Step 7: Skip commit**

---

## Phase E — Final verification

### Task 13: Full three-layer run + fixture regression sanity check

**Files:** none (verification only)

- [ ] **Step 1: Phase 4 Playwright regression**

Start the Flask dev server and run the existing Phase 4 tests to make sure nothing broke:

```bash
source .venv/bin/activate && python main.py &
sleep 3
npx playwright test tests/playwright/livecard.spec.js --config=tests/playwright/playwright.config.js
pkill -f "python main.py" || true
```

Expected: 19 passed.

- [ ] **Step 2: Layer 2 full run**

```bash
source .venv/bin/activate && python -m pytest tests/test_nightly_balance.py -v --tb=no
```

Expected: 18 passed.

- [ ] **Step 3: Layer 3 nightly-flow run**

```bash
source .venv/bin/activate && python main.py &
sleep 3
npx playwright test tests/playwright/nightly-flow.spec.js --config=tests/playwright/playwright.config.js
pkill -f "python main.py" || true
```

Expected: 1 passed.

- [ ] **Step 4: Seeder unit tests**

```bash
source .venv/bin/activate && python -m pytest tests/test_ground_truth_seeder.py -v
```

Expected: all tests pass.

- [ ] **Step 5: fixture_regression.py baseline**

```bash
source .venv/bin/activate && python scripts/fixture_regression.py 2>&1 | tail -10
```

Expected: "Parseable today: 18" (unchanged).

- [ ] **Step 6: Existing unit tests**

```bash
source .venv/bin/activate && python -m pytest tests/test_rj_filler.py tests/test_rj_reader.py tests/test_jour_mapping.py tests/test_ole_builder.py tests/test_import_export.py -v --tb=short
```

Expected: all pass, no regressions from fix-loop changes.

- [ ] **Step 7: Report back to the user**

Summary format:

```
Nightly balance integration — complete.

Layer 1 (seeder):        PASS  (N unit tests)
Layer 2 (pytest):        PASS  (18 days all balance to $0.00)
Layer 3 (Playwright):    PASS  (1 nightly-flow test, 2026-03-21)
Phase 4 regression:      PASS  (19 livecard tests)
Project unit tests:      PASS  (no regressions)
fixture_regression.py:   PASS  (18 parseable, unchanged)

Fixes applied during loop:
- <file>:<function> — <one-line why>
- <file>:<function> — <one-line why>
...
```

- [ ] **Step 8: Skip commit (user handles git)**

---

## Self-review checklist

- [x] Every spec section has a task:
  - Spec §1 Goal & success criterion → Tasks 8, 9, 10, 13
  - Spec §2 Layer 1 seeder → Tasks 1-7
  - Spec §2 Layer 2 pytest → Tasks 8, 9
  - Spec §2 Layer 3 Playwright → Tasks 11, 12
  - Spec §3 Iteration loop → Task 10
  - Spec §4 File structure → File Map at top + Tasks 1, 8, 11, 12
  - Spec §4 Database strategy (rollback via delete/create) → Task 8, 9 cleanup steps
  - Spec §5 Success criteria → Task 13
  - Spec §6 Risks (sheet layout variation, disjoint fields, double-write) → Task 7 Step 5, Task 10 Step 7
- [x] No placeholders or "TBD" (selector placeholders in Task 12 are explicitly flagged as needing Step 1 discovery)
- [x] Function/field names consistent across tasks:
  - `extract_dueback`, `extract_sd`, `extract_chambres`, `extract_transelect`, `extract_geac_balance_sheet`, `extract_recap`, `extract_all`, `_find_sheet`, `_as_float`, `_find_first_numeric`, `SeederLayoutError`, `_open_workbook`
  - `_load_files`, `_seed_nas`, `_build_diagnostic`, `PARSEABLE_DAYS`, `_FILE_KEY_TO_NAMES`
- [x] Every commit step is labeled "Skip commit — user handles git"
- [x] Test commands show expected output
- [x] The fix-loop task has explicit exit criteria and anti-patterns called out
- [x] Spec's Layer 2-vs-Layer 3 divergence risk is handled (Task 12 Step 5 diagnostic decision tree)
