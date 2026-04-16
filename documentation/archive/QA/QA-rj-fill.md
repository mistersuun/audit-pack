# QA Report: routes/audit/rj_fill.py
## Last Updated: 2026-03-23
## Status: FAIL

---

### Test QA-FILL-001: `save_dueback_simple` writes wrong values to column Z (NEW)

- **File:Line:** rj_fill.py:407–410
- **Input:** `POST /api/rj/dueback/save` with multiple receptionist entries containing both `previous` and `current` amounts
- **Expected Output:** Column Z (DueBack total) receives the sum of all `previous` values on the "previous" row, and the sum of all `current` values on the "current" row
- **Actual Output:** The code accumulates `total_previous` and `total_current` correctly (lines 398–405), then computes `total_z = total_previous + total_current` at line 408. But then at lines 409–410:

  ```python
  filler.fill_dueback_by_col(current_day, 'Z', total_previous, line_type='previous')
  filler.fill_dueback_by_col(current_day, 'Z', total_current, line_type='nouveau')
  ```

  This writes `total_previous` to column Z's "previous" row and `total_current` to column Z's "current" row. That is actually **correct behavior** for Z — each row of Z should equal the sum of that row across all receptionist columns. So `total_z` is computed but unused in the return value context (it's only in the response JSON), which is fine.

  **However**, the actual bug is more subtle: `total_previous` accumulates values that are "already negative from frontend" (comment at line 383). So `total_previous` is a negative number. The Z "previous" row will receive a negative number — which is correct for the Excel formula structure (previous balances are stored negative). This appears intentional.

  **The real fill bug**: When `prev_val == 0` (line 396), the "previous" fill for that receptionist is skipped. But the Z total at line 409 still uses `total_previous` which only accumulated non-zero prevs. This means if the user enters zero for some receptionists (meaning "no previous balance"), the Z total correctly reflects only the non-zero ones. This is correct behavior.

  **Revised finding:** The more serious issue is that `filled_count` at line 419 counts receptionist column fills only (lines 397–405), but the two Z-fills (lines 409–410) are NOT counted in `filled_count`. The response at line 419 reports `filled_count` that doesn't include the Z column writes. This is a data integrity reporting error, not a data corruption error.

- **Status:** WARNING (logic is correct, reporting is misleading)
- **Severity:** P3 — LOW
- **Comments:** Minor issue. The Z-column data is written correctly; only the count in the response is understated by 2.

---

### Test QA-FILL-002: `update_controle` formats date string incorrectly when only year is provided (NEW)

- **File:Line:** rj_fill.py:580–586
- **Input:** `POST /api/rj/controle` with body `{"vjour": 15, "annee": 2026}` (no mois)
- **Expected Output:** A sensible date string in the success message
- **Actual Output:** Execution trace through lines 580–586:

  ```python
  date_str = f"{vjour:02d}"          # "15"
  if mois:                             # mois is None/falsy, skipped
      date_str = f"{vjour:02d}/{mois:02d}"
  if annee:                            # annee=2026, truthy
      date_str = f"{vjour:02d}/{annee}"   # "15/2026"
  ```

  The result is `"Contrôle mis à jour: Jour 15/2026"` — missing the month entirely. The string is wrong: it looks like day/year without month. More importantly, the `annee` branch overwrites the `mois` branch result, making the `mois` branch unreachable when `annee` is also provided. When all three are present: `date_str` ends up as `"{vjour}/{annee}"` — the month is always dropped from the message.

  This is a string formatting bug in the user-facing message only; the actual cell writes (line 570) use `vjour`, `mois`, `annee` separately and are not affected.

- **Status:** WARNING
- **Severity:** P3 — LOW (cosmetic, message only)
- **This is NEW** — not reported in prior reviews.

---

### Test QA-FILL-003: `fill_rj_sheet` sheet mapping covers only 6 sheets, silently rejects valid sheet names

- **File:Line:** rj_fill.py:91–98
- **Input:** `POST /api/rj/fill/dueback` (the URL uses `dueback` not `dueback` — note the route is separate at line 128)
- **Note:** The `fill_rj_sheet` generic endpoint at line 62 accepts sheet names `recap`, `transelect`, `geac`, `controle`, `depot`, `daily`. Any other name returns 400. This is intentional design, not a bug.
- **Status:** PASS (by design)

---

### Test QA-FILL-004: `autofill_geac_cashout` passes wrong data dict to fill_sheet (NEW)

- **File:Line:** rj_fill.py:474–493
- **Input:** `POST /api/rj/autofill-cashout` with valid card amounts
- **Expected Output:** GEAC/UX Row 6, Row 12, and Transelect rows filled
- **Actual Output:** Three `fill_sheet` calls are made:

  ```python
  # Fill GEAC/UX Row 6
  cells_filled += rj_filler.fill_sheet('geac_ux', {
      k: v for k, v in result['data'].items()
      if k in parser.FIELD_MAPPINGS       # FIELD_MAPPINGS has keys like 'amex_cash_out'
  })

  # Fill GEAC/UX Row 12
  cells_filled += rj_filler.fill_sheet('geac_ux', {
      k: v for k, v in result['data'].items()
      if k in parser.DAILY_REV_MAPPINGS   # DAILY_REV_MAPPINGS has keys like 'amex_daily_revenue'
  })

  # Fill Transelect
  cells_filled += rj_filler.fill_sheet('transelect', {
      k: v for k, v in result['data'].items()
      if k in parser.TRANSELECT_MAPPINGS  # TRANSELECT_MAPPINGS has keys like 'fusebox_visa'
  })
  ```

  Each `fill_sheet` call passes logical key names to `rj_filler.fill_sheet()`. But `fill_sheet` internally resolves these names against `CELL_MAPPINGS[sheet_name]` in `rj_mapper.py`. Whether this works depends on whether `CELL_MAPPINGS['geac_ux']` contains keys like `'amex_cash_out'`.

  **This is the same structural problem as QA-PARSE-003**: the parser's FIELD_MAPPINGS values are cell references (e.g., `'B6'`), but `fill_sheet` expects logical names that map to cell references. If the CELL_MAPPINGS in rj_mapper.py happen to use the same key names as the parser (e.g., `'amex_cash_out'`), this works. If not, zero cells are filled.

  Without reading `utils/rj_mapper.py` in full, this cannot be confirmed as broken — but the pattern is identical to the confirmed QA-PARSE-003 bug and warrants verification.

- **Status:** WARNING — needs verification against rj_mapper.py CELL_MAPPINGS
- **Severity:** P2 — HIGH if CELL_MAPPINGS key names don't match
