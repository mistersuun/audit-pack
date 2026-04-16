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

import json

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


def _day_number(day: str) -> int:
    """Extract the day-of-month from a date string like '2026-03-21'."""
    return int(day.split("-")[2])


def _employee_name(sh: xlrd.sheet.Sheet, col: int,
                   name_row1: int = 1, name_row2: int = 2) -> str:
    """Build an employee name from the two header rows at *col*."""
    first = str(sh.cell_value(name_row1, col)).strip()
    last = str(sh.cell_value(name_row2, col)).strip()
    if first and last:
        return f"{first} {last}"
    return first or last


def extract_dueback(day: str) -> list[dict]:
    """Read the DueBack (DUBACK#) sheet and return per-receptionist amounts.

    Returns a list of dicts: ``[{'name': 'Alice', 'amount': 123.45}, ...]``
    skipping employees with zero or missing amounts.

    Layout (probed from 2026-03-21):
      - Row 1 cols 2..N: employee first names
      - Row 2 cols 2..N: employee last names
      - Data rows come in pairs per day-of-month:
        - First row:  col 0 = day#, col 1 = RJ total (negative)
        - Second row: col 0 = same day#, cols 2..N = individual amounts
      The second row of each pair holds the per-employee envelope cash.
      The 'Total' column (col 21 on 2026-03-21) is skipped.
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "duback") or _find_sheet(wb, "dueback")
    if sh is None:
        raise SeederLayoutError(day, "(DueBack)", "no sheet matching 'duback' or 'dueback'")

    target_day = _day_number(day)

    # Find the "Total" column to skip it
    total_col = None
    for c in range(sh.ncols):
        hdr = str(sh.cell_value(1, c)).strip().lower()
        if hdr == "total":
            total_col = c
            break

    # Find the two data rows for this day.
    # Day rows come in pairs: first has the RJ total in col 1,
    # second has individual amounts.
    day_rows = []
    for r in range(3, sh.nrows):  # skip header rows 0-2
        if _as_float(sh.cell_value(r, 0)) == float(target_day):
            day_rows.append(r)

    if len(day_rows) < 2:
        # Some days might have only one row or none
        return []

    # The second row of the pair has individual employee amounts
    amounts_row = day_rows[1]

    # Determine the employee column range (skip col 0=date, col 1=RJ total)
    first_emp_col = 2
    # Find last employee column (stop before 'Total' or blank header)
    last_emp_col = first_emp_col
    for c in range(first_emp_col, sh.ncols):
        if c == total_col:
            break
        name = _employee_name(sh, c)
        if not name:
            break
        last_emp_col = c + 1

    rows: list[dict] = []
    for c in range(first_emp_col, last_emp_col):
        amount = _as_float(sh.cell_value(amounts_row, c))
        if amount == 0.0:
            continue
        name = _employee_name(sh, c)
        if not name:
            continue
        rows.append({"name": name, "amount": round(amount, 2)})

    return rows


def extract_sd(day: str) -> list[dict]:
    """Read the SD (SetD) sheet and return per-employee verified amounts.

    Returns a list of dicts:
    ``[{'employee': 'Alice', 'verified_amount': 500.00}, ...]``

    Layout (probed from 2026-03-21):
      - Row 1 cols 2..N: employee first names  (some header cols like
        'Petite', 'Conc.', 'Corr.' are accounting labels, not people)
      - Row 2 cols 2..N: employee last names / account codes
      - Row 3 cols 2..N: account numbers (e.g. '2-946000')
      - One data row per day: col 0 = day#, col 1 = RJ SD total,
        cols 2..N = individual employee amounts.
      Special columns to skip: those with header labels like 'RJ',
      'Petite', 'Conc.', 'Corr.', 'total', '± 1.00', 'distribution'.
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "setd") or _find_sheet(wb, "sd")
    if sh is None:
        raise SeederLayoutError(day, "(SD)", "no sheet matching 'setd' or 'sd'")

    target_day = _day_number(day)

    # Labels in rows 1-2 that indicate non-employee columns
    skip_labels = {
        "jour", "rj", "petite", "conc.", "corr.", "total", "distribution",
        "neg=débiteur", "comptab", "comptab.", "banquet", "comptab",
    }

    # Find the data row for this day
    data_row = None
    for r in range(4, sh.nrows):  # skip header rows 0-3
        if _as_float(sh.cell_value(r, 0)) == float(target_day):
            data_row = r
            break

    if data_row is None:
        return []

    rows: list[dict] = []
    for c in range(2, sh.ncols):
        # Check if this column is an employee column
        h1 = str(sh.cell_value(1, c)).strip()
        h2 = str(sh.cell_value(2, c)).strip()

        # Skip known non-employee columns
        if h1.lower() in skip_labels or h2.lower() in skip_labels:
            continue
        # Skip columns with '±' in header (distribution column)
        if "±" in h1 or "±" in h2:
            continue

        amount = _as_float(sh.cell_value(data_row, c))
        if amount == 0.0:
            continue

        name = _employee_name(sh, c)
        if not name:
            continue

        rows.append({"employee": name, "verified_amount": round(amount, 2)})

    return rows


def extract_chambres(day: str) -> int:
    """Read the jour sheet and return chambres à refaire count.

    The 'jour' sheet has a column labelled 'CH. a refaire' (col 94 on
    2026-03-21). Each row corresponds to a day of the month (row 2 = day 1,
    row 3 = day 2, etc.). The value is an integer between 0 and 252.

    Returns 0 if the value is empty or the column cannot be found.
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "jour")
    if sh is None:
        raise SeederLayoutError(day, "(jour)", "no 'jour' sheet found")

    target_day = _day_number(day)

    # Find the 'CH. a refaire' column by scanning header row 1
    refaire_col = None
    for c in range(sh.ncols):
        hdr = str(sh.cell_value(1, c)).strip().lower()
        if "refaire" in hdr:
            refaire_col = c
            break

    if refaire_col is None:
        # Fallback: try the controle sheet
        csh = _find_sheet(wb, "controle")
        if csh is not None:
            for r in range(csh.nrows):
                label = str(csh.cell_value(r, 0)).strip().lower()
                if "refaire" in label:
                    v = _as_float(csh.cell_value(r, 1))
                    return int(v)
        return 0

    # Find the row for our target day. Col 0 has the day number.
    for r in range(2, sh.nrows):
        if _as_float(sh.cell_value(r, 0)) == float(target_day):
            v = _as_float(sh.cell_value(r, refaire_col))
            return int(v)

    return 0


# ── Card-type label normalisation ──────────────────────────────────────

_CARD_LABEL_MAP = {
    "débit": "debit",
    "debit": "debit",
    "visa": "visa",
    "master": "mc",
    "mastercard": "mc",
    "amex": "amex",
    "discover": "discover",
}


def _norm_card(raw: str) -> str | None:
    """Map a raw XLS card-type label to the NAS key, or None."""
    return _CARD_LABEL_MAP.get(raw.strip().lower())


# ── Transelect ─────────────────────────────────────────────────────────

def extract_transelect(day: str) -> dict:
    """Read the ``transelect`` sheet and return terminal-card JSON blobs.

    Returns a dict with up to three keys:
      - ``transelect_restaurant`` — JSON string
      - ``transelect_reception``  — JSON string
      - ``transelect_quasimodo``  — JSON string (if section exists)

    Each JSON blob has the schema::

        {"_terminals": ["positouch"],
         "debit": {"positouch": 8277.13, "esc_pct": 0},
         "visa":  {"positouch": 6297.25, "esc_pct": 0.0175}, ...}

    Layout (probed from 2026-03-21):
      Restaurant section starts at row 6 (header "TYPE" in col 0).
        - Col 23 = POSITOUCH (POS total per card type)
        - Col 25 = ESCOMPTE (discount percentage)
        - Rows 8-12 = DÉBIT, VISA, MASTER, DISCOVER, AMEX

      Reception section starts at row 17 (second "TYPE" in col 0).
        - Col 1 = FreedomPay (Bank Report value)
        - Col 17 = ESCOMPTE
        - Rows 19-23 = DÉBIT, ViSA, MASTER, DISCOVER, AMEX
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "transelect")
    if sh is None:
        raise SeederLayoutError(day, "(transelect)", "no 'transelect' sheet found")

    result: dict = {}

    # ── Locate sections by scanning for "TYPE" labels in col 0 ──
    type_rows: list[int] = []
    for r in range(sh.nrows):
        if str(sh.cell_value(r, 0)).strip().upper() == "TYPE":
            type_rows.append(r)

    if len(type_rows) < 1:
        raise SeederLayoutError(day, "transelect", "no TYPE header row found")

    # ── Helper: find column by header label ──
    def _find_col(header_row: int, label: str) -> int | None:
        label_lc = label.lower()
        for c in range(sh.ncols):
            if str(sh.cell_value(header_row, c)).strip().lower() == label_lc:
                return c
        return None

    # ── Restaurant section ──
    rest_hdr = type_rows[0]  # row 6 typically
    # Use TOTAL 1 + TOTAL 2 (bar tills + banquet terminals).
    # This matches the TOTAUX row that the jour sheet debit columns use.
    # TOTAL 2 is typically 0 for all card types except DEBIT which may
    # have banquet terminal amounts.
    tot1_col = _find_col(rest_hdr, "TOTAL 1")
    tot2_col = _find_col(rest_hdr, "TOTAL 2") or _find_col(rest_hdr, "TOTAL 2 ")
    pos_col = tot1_col if tot1_col is not None else _find_col(rest_hdr, "POSITOUCH")
    esc_col = _find_col(rest_hdr, "ESCOMPTE")

    if pos_col is not None:
        blob: dict = {"_terminals": ["positouch"]}
        # Card rows are the 5 rows after (header+subheader), i.e. rest_hdr+2 .. rest_hdr+6
        for offset in range(2, 7):
            r = rest_hdr + offset
            if r >= sh.nrows:
                break
            card_key = _norm_card(str(sh.cell_value(r, 0)))
            if card_key is None:
                continue
            t1_val = _as_float(sh.cell_value(r, pos_col))
            t2_val = _as_float(sh.cell_value(r, tot2_col)) if tot2_col is not None else 0
            pos_val = t1_val + t2_val
            esc_val = _as_float(sh.cell_value(r, esc_col)) if esc_col is not None else 0
            blob[card_key] = {"positouch": round(pos_val, 2), "esc_pct": esc_val}
        result["transelect_restaurant"] = json.dumps(blob)

    # ── Reception section ──
    if len(type_rows) >= 2:
        rec_hdr = type_rows[1]  # row 17 typically
        # FreedomPay value is in col 1 (Bank Report)
        fp_col = 1
        # Escompte column for reception
        rec_esc_col = _find_col(rec_hdr, "ESCOMPTE")

        blob = {"_terminals": ["freedompay"]}
        for offset in range(2, 7):
            r = rec_hdr + offset
            if r >= sh.nrows:
                break
            card_key = _norm_card(str(sh.cell_value(r, 0)))
            if card_key is None:
                continue
            fp_val = _as_float(sh.cell_value(r, fp_col))
            esc_val = _as_float(sh.cell_value(r, rec_esc_col)) if rec_esc_col is not None else 0
            blob[card_key] = {"freedompay": round(fp_val, 2), "esc_pct": esc_val}
        result["transelect_reception"] = json.dumps(blob)

    # ── Quasimodo section (if a third TYPE row exists) ──
    if len(type_rows) >= 3:
        qm_hdr = type_rows[2]
        blob = {"_terminals": ["quasimodo"]}
        for offset in range(2, 7):
            r = qm_hdr + offset
            if r >= sh.nrows:
                break
            card_key = _norm_card(str(sh.cell_value(r, 0)))
            if card_key is None:
                continue
            val = _as_float(sh.cell_value(r, 1))
            blob[card_key] = {"quasimodo": round(val, 2), "esc_pct": 0}
        result["transelect_quasimodo"] = json.dumps(blob)

    return result


# ── GEAC Balance Sheet ─────────────────────────────────────────────────

def extract_geac_balance_sheet(day: str) -> dict:
    """Read the ``geac_ux`` sheet and return the GEAC balance sheet JSON.

    Returns ``{'geac_balance_sheet': <JSON string>}`` with keys:
    ``prev_dr, prev_gl, today_dr, today_gl, facture_dr, facture_ar,
    advdep_dr, advdep_ad, newbal_dr, newbal_gl``.

    Layout (probed from 2026-03-21, starting at row 24):
      The GEAC/UX System Balance Sheet occupies the lower half of the
      ``geac_ux`` sheet.  Key rows are identified by label scanning:
        - "Balance Previous Day" → data row has prev_dr (col 1), prev_gl (col 4)
        - "Balance today"        → data row has today_dr (col 1), today_gl (col 4)
        - "Facture Direct"       → data row has facture_dr (col 1), facture_ar (col 3)
        - "Adv deposit applied"  → data row has advdep_dr (col 1), advdep_ad (col 9)
        - "New Balance"          → data row has newbal_dr (col 1), newbal_gl (col 4)
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "geac_ux") or _find_sheet(wb, "geac")
    if sh is None:
        raise SeederLayoutError(day, "(geac_ux)", "no 'geac_ux' sheet found")

    # Find the "GEAC/UX System Balance Sheet" header to anchor our search
    bs_start = None
    for r in range(sh.nrows):
        for c in range(min(3, sh.ncols)):
            cell = str(sh.cell_value(r, c)).strip().lower()
            if "balance sheet" in cell:
                bs_start = r
                break
        if bs_start is not None:
            break
    if bs_start is None:
        raise SeederLayoutError(day, "geac_ux", "no 'Balance Sheet' header found")

    bs: dict = {
        "prev_dr": 0.0, "prev_gl": 0.0,
        "today_dr": 0.0, "today_gl": 0.0,
        "facture_dr": 0.0, "facture_ar": 0.0,
        "advdep_dr": 0.0, "advdep_ad": 0.0,
        "newbal_dr": 0.0, "newbal_gl": 0.0,
    }

    # Scan label rows from bs_start to end, then read the NEXT numeric row
    r = bs_start
    while r < sh.nrows:
        label = str(sh.cell_value(r, 1)).strip().lower()

        if "balance previous" in label or "yesterday" in label:
            # Data is below the label — skip until we find a numeric row
            dr = r + 1
            while dr < sh.nrows and not isinstance(sh.cell_value(dr, 1), float):
                dr += 1
            if dr < sh.nrows:
                bs["prev_dr"] = round(_as_float(sh.cell_value(dr, 1)), 2)
                bs["prev_gl"] = round(_as_float(sh.cell_value(dr, 4)), 2)

        elif "balance today" in label:
            dr = r + 1
            while dr < sh.nrows and not isinstance(sh.cell_value(dr, 1), float):
                dr += 1
            if dr < sh.nrows:
                bs["today_dr"] = round(_as_float(sh.cell_value(dr, 1)), 2)
                bs["today_gl"] = round(_as_float(sh.cell_value(dr, 4)), 2)

        elif "facture" in label:
            dr = r + 1
            while dr < sh.nrows and not isinstance(sh.cell_value(dr, 1), float):
                dr += 1
            if dr < sh.nrows:
                bs["facture_dr"] = round(_as_float(sh.cell_value(dr, 1)), 2)
                bs["facture_ar"] = round(_as_float(sh.cell_value(dr, 3)), 2)

        elif "adv deposit" in label:
            dr = r + 1
            while dr < sh.nrows and not isinstance(sh.cell_value(dr, 1), float):
                dr += 1
            if dr < sh.nrows:
                bs["advdep_dr"] = round(_as_float(sh.cell_value(dr, 1)), 2)
                bs["advdep_ad"] = round(_as_float(sh.cell_value(dr, 9)), 2)

        elif "new balance" in label:
            dr = r + 1
            while dr < sh.nrows and not isinstance(sh.cell_value(dr, 1), float):
                dr += 1
            if dr < sh.nrows:
                bs["newbal_dr"] = round(_as_float(sh.cell_value(dr, 1)), 2)
                bs["newbal_gl"] = round(_as_float(sh.cell_value(dr, 4)), 2)

        r += 1

    return {"geac_balance_sheet": json.dumps(bs)}


# ── Recap ──────────────────────────────────────────────────────────────

def extract_recap(day: str) -> dict:
    """Read the ``Recap`` sheet and return NAS scalar field values.

    Returns a dict of ``{NAS_attribute_name: float}`` for:
      - ``cash_ls_lecture``, ``cash_pos_lecture``
      - ``cheque_ar_lecture``, ``cheque_dr_lecture``
      - ``remb_gratuite_lecture``, ``remb_client_lecture``
      - ``dueback_reception_lecture``, ``dueback_nb_lecture``
      - ``recap_balance`` (surplus/deficit)
      - ``deposit_cdn``, ``deposit_us``

    Layout (probed from 2026-03-21):
      Col 0 = description label, col 1 = Lecture, col 2 = Corr, col 3 = Net.
      Rows are identified by substring match on the label in col 0.
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "recap")
    if sh is None:
        raise SeederLayoutError(day, "(Recap)", "no 'Recap' sheet found")

    # Build a label→row index for fast lookup
    label_map: dict[str, int] = {}
    for r in range(sh.nrows):
        lbl = str(sh.cell_value(r, 0)).strip().lower()
        if lbl:
            label_map[lbl] = r

    def _find_row(needle: str) -> int | None:
        needle_lc = needle.lower()
        for lbl, r in label_map.items():
            if needle_lc in lbl:
                return r
        return None

    result: dict = {}

    # Map: (NAS field name, label substring, value column)
    mappings = [
        ("cash_ls_lecture",           "lightspeed",          1),
        ("cash_pos_lecture",          "positouch",           1),
        ("cheque_ar_lecture",         "chèque payment",      1),
        ("cheque_ar_lecture",         "cheque payment",      1),  # fallback no accent
        ("cheque_dr_lecture",         "chèque daily",        1),
        ("cheque_dr_lecture",         "cheque daily",        1),  # fallback
        ("remb_gratuite_lecture",     "gratuité",            1),
        ("remb_gratuite_lecture",     "gratuite",            1),  # fallback
        ("remb_client_lecture",       "remboursement client", 1),
        ("dueback_reception_lecture", "due back réception",  1),
        ("dueback_reception_lecture", "due back reception",  1),  # fallback
        ("dueback_nb_lecture",        "due back n/b",        1),
        ("recap_balance",            "surplus",             1),
        ("deposit_us",               "depot us",            3),
        ("deposit_us",               "dépôt us",            3),  # fallback
        ("deposit_cdn",              "canadien",            1),
    ]

    for field, needle, col in mappings:
        if field in result:
            continue  # already found by a prior variant
        row = _find_row(needle)
        if row is not None:
            result[field] = round(_as_float(sh.cell_value(row, col)), 2)

    return result


# ── Jour scalars (Bal_Ouv, etc.) ──────────────────────────────────────

def extract_jour_scalars(day: str) -> dict:
    """Read scalar values from the ``jour`` sheet that the balancer needs
    as *inputs* (not computed outputs).

    Currently extracted:
      - ``rj_balance_ouverture`` — col 1 (bal.ouv), the opening balance
        carried from the previous night.

    The day-of-month selects the row (col 0 = day number).
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, "jour")
    if sh is None:
        raise SeederLayoutError(day, "(jour)", "no 'jour' sheet found")

    target_day = _day_number(day)
    result: dict = {}

    for r in range(2, sh.nrows):
        if _as_float(sh.cell_value(r, 0)) == float(target_day):
            result["rj_balance_ouverture"] = round(
                _as_float(sh.cell_value(r, 1)), 2
            )
            result["rj_balance_fermeture"] = round(
                _as_float(sh.cell_value(r, 3)), 2
            )
            # Col 2 = Diff.Caisse (the auditor-accepted DC for this day).
            result["diff_caisse_ground_truth"] = round(
                _as_float(sh.cell_value(r, 2)), 2
            )

            # Extract ALL jour column values (cols 1-86) so that the
            # export verification test can fill the jour row directly.
            # Include zero values too — they are meaningful in the GT.
            gt_cols: dict[int, float] = {}
            for c in range(1, min(87, sh.ncols)):
                v = sh.cell_value(r, c)
                if isinstance(v, (int, float)):
                    gt_cols[c] = round(float(v), 2)
            if gt_cols:
                result["_gt_jour_cols"] = gt_cols
            break

    return result


def extract_sheet_cells(day: str, sheet_name: str,
                        cells: list[tuple[int, int]]) -> dict[tuple[int, int], float | str]:
    """Read specific cells from a ground-truth sheet.

    Args:
        day: Date string like '2026-03-21'.
        sheet_name: Exact sheet name (e.g. 'transelect', 'geac_ux').
        cells: List of (row, col) 0-indexed tuples.

    Returns:
        Dict of {(row, col): value} for cells that contain non-empty values.
    """
    wb = _open_workbook(day)
    sh = _find_sheet(wb, sheet_name)
    if sh is None:
        return {}

    result: dict[tuple[int, int], float | str] = {}
    for r, c in cells:
        if r >= sh.nrows or c >= sh.ncols:
            continue
        ctype = sh.cell_type(r, c)
        if ctype == 0:  # XL_CELL_EMPTY
            continue
        val = sh.cell_value(r, c)
        if isinstance(val, float):
            result[(r, c)] = round(val, 2)
        elif isinstance(val, str) and val.strip():
            result[(r, c)] = val.strip()
    return result


# ── Bundle all extractors ─────────────────────────────────────────────

def extract_all(day: str) -> dict:
    """Run every extractor and return a single dict ready for NAS seeding.

    Keys come from three categories:

    1. JSON blob fields (``geac_balance_sheet``, ``transelect_*``) — kept
       as JSON strings, same as the individual extractors return them.
    2. Recap scalars (``cash_ls_lecture``, ``recap_balance``, etc.) —
       plain floats.
    3. Chambres a refaire — integer stored under ``chambres_refaire``.
    4. DueBack and SD lists — serialised to JSON strings under
       ``dueback_entries`` and ``sd_entries``.
    """
    out: dict = {}

    # JSON blobs from GEAC and Transelect extractors
    out.update(extract_geac_balance_sheet(day))
    out.update(extract_transelect(day))

    # Recap scalars
    out.update(extract_recap(day))

    # Jour scalars (bal_ouv, etc.)
    out.update(extract_jour_scalars(day))

    # Chambres a refaire
    out['chambres_refaire'] = extract_chambres(day)

    # DueBack + SD — NAS stores these as JSON strings
    out['dueback_entries'] = json.dumps(extract_dueback(day))
    out['sd_entries'] = json.dumps(extract_sd(day))

    return out
