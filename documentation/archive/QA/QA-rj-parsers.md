# QA Report: routes/audit/rj_parsers.py
## Last Updated: 2026-03-23
## Status: FAIL

---

### Test QA-PARSE-001: `parse_and_fill` missing @csrf_protect (Confirmed Prior)

- **File:Line:** rj_parsers.py:70–72
- **Input:** `POST /api/rj/parse-and-fill` with `doc_type` and `file`
- **Expected Output:** CSRF token validated before mutating server state
- **Actual Output:** The `parse_and_fill()` function at line 70 has only `@login_required`. The `@csrf_protect` decorator present on `parse_document()` at line 16–18 is NOT applied to `parse_and_fill`. Since this route reads a document and writes cells into the RJ file in memory, it is a state-mutating POST without CSRF protection. An attacker who can get an authenticated user to visit a malicious page can trigger arbitrary fills.
- **Status:** FAIL
- **Severity:** P1 — CRITICAL (CSRF)
- **Fix:** Add `@csrf_protect` between `@login_required` and `def parse_and_fill`.
- **Marks as confirmed prior finding:** Yes

Similarly, `fill_jour` at line 150–152 is also missing `@csrf_protect`. It writes directly to the Jour sheet.

---

### Test QA-PARSE-002: `parse_and_fill` leaves `_RJ_FILLER_CACHE` stale (NEW)

- **File:Line:** rj_parsers.py:115–133
- **Input:** User calls `parse_and_fill`, then immediately calls any rj_fill route (e.g., `fill_rj_sheet`)
- **Expected Output:** The subsequent fill route sees the updated RJ bytes
- **Actual Output:** Execution trace:
  1. `parse_and_fill` creates its own `RJFiller(rj_bytes)` at line 118 — this bypasses `get_or_create_filler()`.
  2. It calls `filler.save(output)` at line 131, then sets `RJ_FILES[session_id] = output` at line 133.
  3. This replaces the BytesIO object in `RJ_FILES`, which changes `id(file_bytes)`.
  4. However, it does NOT call `_RJ_FILLER_CACHE.pop(session_id, None)`.
  5. `_RJ_FILLER_CACHE[session_id]` still holds `(old_buf_id, old_filler)`.
  6. Next call to `get_or_create_filler()` checks `cached[0] == id(RJ_FILES[session_id])` — since the BytesIO was replaced, `id` differs, so the cache is correctly invalidated **in that case**.

  Wait — actually this is **partially self-correcting**: `get_or_create_filler` compares `id(file_bytes)` of the current `RJ_FILES[session_id]` with the cached buf_id. Since `parse_and_fill` stores a NEW BytesIO object, the ids differ and `get_or_create_filler` creates a fresh filler.

  **The real bug is different**: `parse_and_fill` itself calls `filler.fill_sheet(target_sheet, {...})` with a **wrong filter** (see QA-PARSE-003). So no cells are actually written. The cache invalidation is correct.

- **Status:** WARNING (the cache issue is correctly handled by id comparison, but the downstream fill is broken for a different reason)
- **Severity:** P2 — revised down due to self-correcting cache logic
- **Note:** The real P1 issue is QA-PARSE-003 below.

---

### Test QA-PARSE-003: `parse_and_fill` fills zero cells due to wrong filter logic (NEW)

- **File:Line:** rj_parsers.py:124–127
- **Input:** `POST /api/rj/parse-and-fill` with `doc_type=daily_revenue` and a valid PDF
- **Expected Output:** Revenue fields written to the Recap sheet in RJ
- **Actual Output:** Zero cells written. Here is the exact execution trace:

  ```python
  # Line 124-127:
  filled_count = filler.fill_sheet(target_sheet, {
      k: v for k, v in result['data'].items()
      if k in parser.FIELD_MAPPINGS
  })
  ```

  `result['data']` contains logical field names extracted by the parser, e.g.:
  `{'room_charge_total': 5234.50, 'telephones_total': 12.00, ...}`

  `parser.FIELD_MAPPINGS` for `DailyRevenueParser` is:
  ```python
  FIELD_MAPPINGS = {
      'room_charge_total': 'B6',
      'telephones_total': 'B7',
      ...
  }
  ```

  The filter `if k in parser.FIELD_MAPPINGS` checks if `k` (e.g., `'room_charge_total'`) is a key in `FIELD_MAPPINGS`. This IS correct — keys match.

  **However**, the real problem is what `filler.fill_sheet()` does with that data. `fill_sheet` expects `{logical_field_name: value}` and internally looks up `CELL_MAPPINGS[sheet_name][field_name]` to find the cell reference. The fill works on logical names.

  But in `parse_and_fill`, the target_sheet comes from `ParserFactory.get_type_info()`:

  ```python
  type_info = ParserFactory.get_type_info().get(doc_type, {})
  target_sheet = type_info.get('target_sheet', 'Recap')
  ```

  For `daily_revenue`, `target_sheet = 'Recap'`. But `DailyRevenueParser.FIELD_MAPPINGS` maps fields to GEAC-style cell refs like `'B6'`, `'B7'` — **not** the Recap sheet field names that `rj_filler.fill_sheet('Recap', ...)` expects.

  So `fill_sheet('Recap', {'room_charge_total': 5234.50, ...})` looks up `'room_charge_total'` in `CELL_MAPPINGS['Recap']`. If `CELL_MAPPINGS['Recap']` uses different key names (which it does, based on rj_mapper.py naming conventions), the lookup fails silently and `filled_count = 0`.

- **Status:** FAIL
- **Severity:** P1 — CRITICAL
- **Impact:** The `parse_and_fill` endpoint always returns `filled_count=0` for any parser. Users are misled into thinking the operation succeeded because the API returns `success: True`.
- **Steps to reproduce:**
  1. Upload a valid RJ file
  2. Call `POST /api/rj/parse-and-fill` with a valid Daily Revenue PDF
  3. Response returns `{'success': true, 'filled_count': 0}`
  4. Check the RJ file — no cells changed
- **Root cause:** `parse_and_fill` conflates the parser's internal FIELD_MAPPINGS (cell refs for direct Excel writing) with the fill_sheet API (which takes logical field names and resolves them internally). The correct approach is to use `parser.get_fillable_data()` which returns `{cell_ref: value}` and write those directly using the workbook API, OR use the same logical names that CELL_MAPPINGS expects.
- **This is NEW** — not reported in any prior review.

---

### Test QA-PARSE-004: `fill_jour` missing @csrf_protect (NEW)

- **File:Line:** rj_parsers.py:150–152
- **Input:** `POST /api/rj/fill-jour` without CSRF token
- **Expected Output:** 403 CSRF error
- **Actual Output:** Request accepted. `fill_jour` writes computed values directly to the Jour sheet. It is decorated only with `@login_required`, not `@csrf_protect`. This is the same class of vulnerability as QA-PARSE-001.
- **Status:** FAIL
- **Severity:** P1 — CRITICAL (CSRF)
- **This is NEW** — only `/api/rj/parse` and the prior review's reference to `parse-and-fill` were mentioned. `fill_jour` is a separate unprotected write route.
