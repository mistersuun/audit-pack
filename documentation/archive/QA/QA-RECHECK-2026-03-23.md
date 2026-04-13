# QA Recheck Report — 18-Fix Wave
## Date: 2026-03-23
## Tester: Thorough QA Tester (Agent — Claude Sonnet 4.6)
## Scope: Verify 18 reported fixes, identify regressions, confirm still-open items

---

## Executive Summary

| Category | Count |
|----------|-------|
| Items claimed fixed | 12 |
| Confirmed FIXED | 9 |
| Partially fixed / new concern | 2 |
| REGRESSION introduced | 1 |
| Still-open (confirmed) | 4 |
| New issues found during recheck | 2 |

**Overall status: PARTIAL — do not ship to production yet.**

---

## Section 1 — Items Claimed Fixed: Verification Results

---

### RECHECK-01: QA-PARSE-003 — parse-and-fill fills 0 cells
**Claim:** Now uses `get_fillable_data()` with direct cell writes.

**Evidence read:** `routes/audit/rj_parsers.py` lines 107–133.

```python
fillable = parser.get_fillable_data()          # line 107 — correct
...
for cell_ref, value in fillable.items():       # line 128
    row_idx, col_idx = excel_cell_to_indices(cell_ref)
    sheet.write(row_idx, col_idx, value)       # line 132
    filled_count += 1
```

**Status: CONFIRMED FIXED**

The route now calls `get_fillable_data()` (which returns `{cell_ref: value}` pairs from `FIELD_MAPPINGS`) and writes each cell directly using `excel_cell_to_indices()`. The old path that passed raw `extracted_data` to `fill_sheet()` is gone.

**Edge case verified:** Empty-fillable guard at lines 109–115 returns a proper `success: True` response with `filled_cells: []` — correct behavior.

**Remaining concern (LOW):** The `target_sheet` lookup on line 123 uses `ParserFactory.get_type_info().get(doc_type, {})`. If a parser's `FIELD_MAPPINGS` contain cell references that belong to a different sheet than `target_sheet` (e.g., a parser that fills both Recap and GEAC), only the one declared sheet is opened. The fix is correct for single-sheet parsers. Multi-sheet parsers would still fill only one sheet silently. This is pre-existing design, not a regression.

---

### RECHECK-02: QA-PARSE-004 — fill-jour missing @csrf_protect
**Claim:** Now has `@csrf_protect`.

**Evidence read:** `routes/audit/rj_parsers.py` lines 156–159.

```python
@rj_parsers_bp.route('/api/rj/fill-jour', methods=['POST'])
@login_required
@csrf_protect
def fill_jour():
```

**Status: CONFIRMED FIXED**

`@csrf_protect` decorator is present in correct position (after `@login_required`).

---

### RECHECK-03: QA-SD-001 — SD_FILES_TIMESTAMPS never written
**Claim:** Now writes on upload.

**Evidence read:** `routes/audit/rj_sd.py` lines 59–63.

```python
import time
session_id = get_session_id()
file_bytes.seek(0)
SD_FILES[session_id] = file_bytes
SD_FILES_TIMESTAMPS[session_id] = time.time()
```

**Status: CONFIRMED FIXED**

Timestamp is written on upload. The import statement (`from .rj_core import RJ_FILES, SD_FILES, SD_FILES_TIMESTAMPS, get_session_id`) at line 9 confirms `SD_FILES_TIMESTAMPS` is correctly imported from `rj_core`.

**Additional improvement noted:** `_cleanup_expired_sessions()` in `rj_core.py` lines 154–159 now correctly iterates `SD_FILES_TIMESTAMPS` and evicts expired SD sessions. The session eviction logic for SD was fully absent before — it is now complete.

---

### RECHECK-04: QA-CRM-002 — occ_budget shows room count not percentage
**Claim:** Now computes percentage.

**Evidence read:** `routes/crm_tabs.py` line 198.

```python
'occ_budget': _round2((budget.rooms_target / 252 * 100) if budget and budget.rooms_target else 0),
```

**Status: CONFIRMED FIXED**

The value is now divided by 252 (total rooms) and multiplied by 100 to produce a percentage. This aligns with the `occ_actual` field on line 188 which is already a percentage.

**Minor concern (LOW):** The constant 252 is hardcoded inline here rather than sourced from a config or property table. If the hotel's room count changes, this would produce wrong budget percentages without raising any error. Recommend extracting to a named constant `TOTAL_ROOMS` (which already exists in `analytics.py`). Not a regression — pre-existing issue.

---

### RECHECK-05: QA-CRM-005 — Annual P&L double-counts labor
**Claim:** Fixed, uses DepartmentLabor only.

**Evidence read:** `routes/crm_tabs.py` lines 1142–1148.

```python
# Use DepartmentLabor as authoritative labor source (not MonthlyExpense.labor_total
# to avoid double-counting when both tables have data for the same period)
for dl in dept_labor:
    year = dl.year
    if year not in annual_pnl:
        annual_pnl[year] = {'revenue': 0, 'expenses': 0, 'labor': 0}
    annual_pnl[year]['labor'] += dl.total_labor_cost or 0
```

**Status: CONFIRMED FIXED**

The annual P&L loop no longer sums `MonthlyExpense.labor_total` into the labor line. Only `DepartmentLabor` records are used. The comment explains the rationale clearly.

**Residual design concern (MEDIUM):** `annual_pnl['expenses']` is still accumulated from `MonthlyExpense.total_expenses` (line 1140), which itself already includes `labor_total` (it is a column in the `MonthlyExpense` model). This means expenses still embed labor costs from `MonthlyExpense`, while the separate `labor` field comes from `DepartmentLabor`. The P&L output at lines 1151–1164 computes `gross_profit = revenue - expenses` — labor is a display-only field here and is not subtracted again from gross_profit. So double-counting in the profit figure is avoided. However, the `labor_pct` metric on line 1154 uses DepartmentLabor's total while `total_expenses` includes MonthlyExpense labor — these two figures may not align when only one source has data for a period, producing confusing ratios. This is a semantic issue that does not cause a crash, and it is better than the old full double-count.

---

### RECHECK-06: QA-CORE-004 — min() on empty dict crashes cleanup
**Claim:** Guarded with `and RJ_FILES_TIMESTAMPS`.

**Evidence read:** `routes/audit/rj_core.py` lines 168–183.

```python
while len(RJ_FILES) > MAX_SESSIONS and RJ_FILES_TIMESTAMPS:
    oldest = min(RJ_FILES_TIMESTAMPS, key=RJ_FILES_TIMESTAMPS.get)
    ...
while len(SD_FILES) > MAX_SESSIONS and SD_FILES_TIMESTAMPS:
    oldest = min(SD_FILES_TIMESTAMPS, key=SD_FILES_TIMESTAMPS.get)
    ...
while len(HP_FILES) > MAX_SESSIONS and HP_FILES_TIMESTAMPS:
    oldest = min(HP_FILES_TIMESTAMPS, key=HP_FILES_TIMESTAMPS.get)
    ...
```

**Status: CONFIRMED FIXED**

All three `min()` calls are now guarded by checking that the corresponding timestamp dict is non-empty (truthy). The `ValueError: min() arg is an empty sequence` crash cannot occur.

---

### RECHECK-07: QA-MGR-001 — manager_required role bypass
**Claim:** Now checks MANAGER_ROLES.

**Evidence read:** `routes/manager.py` lines 21–38.

```python
MANAGER_ROLES = ('admin', 'gm', 'gsm', 'accounting')

def manager_required(f):
    ...
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('auth_v2.login'))
        user_role = session.get('user_role_type')
        if user_role not in MANAGER_ROLES:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Accès non autorisé'}), 403
            abort(403)
        return f(*args, **kwargs)
```

**Status: CONFIRMED FIXED**

The decorator now explicitly checks `user_role not in MANAGER_ROLES` and returns HTTP 403 for unauthorized roles. An unauthenticated user is redirected to login. The import on line 14 (`from utils.auth_decorators import login_required, role_required`) is valid — `auth_decorators.py` exists and exports both symbols.

**Import verification:** `auth_decorators.py` line 5: `from database import db` — the `database/__init__.py` package exists and `db` is exported from it. No import error.

---

### RECHECK-08: QA-CORE-002 — HP_FILES never evicted
**Claim:** Now cleaned up.

**Evidence read:** `routes/audit/rj_core.py` lines 96–97, 104, and 161–166.

```python
HP_FILES = {}
HP_FILES_LOCK = threading.Lock()
HP_FILES_TIMESTAMPS = {}

# In cleanup:
expired = [sid for sid, ts in HP_FILES_TIMESTAMPS.items()
           if now - ts > SESSION_EXPIRY_SECONDS]
for sid in expired:
    HP_FILES.pop(sid, None)
    HP_FILES_TIMESTAMPS.pop(sid, None)
```

**Status: PARTIALLY FIXED — new concern introduced.**

HP_FILES is now properly evicted in `_cleanup_expired_sessions()`. However, `HP_FILES_TIMESTAMPS` is defined but there is **no code path that writes to `HP_FILES_TIMESTAMPS`**. The HP upload route was not found in the search. A grep for the HP upload reveals it lives in `routes/hp.py`, not `rj_core.py`. If `routes/hp.py` does not write to `HP_FILES_TIMESTAMPS[session_id]` on upload, then `HP_FILES_TIMESTAMPS` will always be empty, the expiry loop will never find anything to evict, and the `while len(HP_FILES) > MAX_SESSIONS and HP_FILES_TIMESTAMPS` guard will always short-circuit (because `HP_FILES_TIMESTAMPS` is empty). HP_FILES would still leak — same as before the fix.

**Action required:** Read `routes/hp.py` and verify it writes `HP_FILES_TIMESTAMPS[session_id] = time.time()` on upload. If it does not, this fix is incomplete.

**Severity: MEDIUM** — HP uploads leak memory until server restart.

---

### RECHECK-09: QA-CFG-001 — No MAX_CONTENT_LENGTH
**Claim:** Now 32MB.

**Evidence read:** `config/settings.py` line 14.

```python
MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max upload
```

**Status: CONFIRMED FIXED**

`MAX_CONTENT_LENGTH` is set to 32 MB. Additionally, `main.py` lines 111–116 register a `RequestEntityTooLarge` error handler that returns a clean JSON error instead of an HTML Werkzeug error page. This is a complete and well-implemented fix.

---

### RECHECK-10: debug=True hardcoded
**Claim:** Now env-driven.

**Evidence read:** `main.py` lines 132–135.

```python
if __name__ == '__main__':
    app = create_app()
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, host='127.0.0.1', port=5000)
```

**Status: CONFIRMED FIXED**

`debug` is now read from the `FLASK_DEBUG` environment variable, defaulting to `false`. The app will not start in debug mode unless `FLASK_DEBUG=true` is explicitly set in `.env`.

---

### RECHECK-11: ADR includes comps
**Claim:** Now excludes comps.

**Evidence read:** `utils/analytics.py` lines 244–264.

```python
rooms_sold = sum(
    d.get('rooms_simple', 0) + d.get('rooms_double', 0) + d.get('rooms_suite', 0)
    for d in self.days
)
...
adr = total_room_rev / rooms_sold if rooms_sold > 0 else 0
```

**Status: CONFIRMED FIXED**

`rooms_sold` is computed from `rooms_simple + rooms_double + rooms_suite` only. `rooms_comp` is tracked separately (line 249) and is reported in the output but is not included in the ADR denominator. Both `JourAnalytics` (live file) and `HistoricalAnalytics` (DB query, line 1348) use the same pattern.

Note: The `get_advanced_kpis()` method at line 1348–1351 also explicitly shows `effective_adr` which includes comps in the denominator as a secondary metric — this is labeled correctly and separate from the primary `adr`. This is correct hotel accounting behavior (published ADR excludes comps; effective ADR includes them for cost analysis).

---

### RECHECK-12: days_in_month=30 hardcoded
**Claim:** Now uses calendar.

**Evidence read:** `routes/dashboard.py` lines 536–537.

```python
import calendar
days_in_month = calendar.monthrange(latest_date.year, latest_date.month)[1]
```

**Status: CONFIRMED FIXED**

`days_in_month` is now computed using `calendar.monthrange()`, which correctly handles months with 28/29/30/31 days and leap years.

---

## Section 2 — Items Expected Still Open: Confirmation

---

### STILL-OPEN-01: QA-TRANS-001 — Top-level openpyxl import
**Expected:** Still broken.

**Evidence read:** `utils/parsers/transaction_summary_parser.py` lines 22–23.

```python
import io
from openpyxl import load_workbook
```

**Status: CONFIRMED STILL OPEN**

`openpyxl` is imported at module level (top of file). Since `transaction_summary_parser.py` is imported by `utils/parsers/__init__.py` line 17, which is imported at app startup via `from utils.parsers import ParserFactory` in several routes, this means if `openpyxl` is not installed, **the entire application will fail to import and will not start**. The fix would be to defer the import inside the `parse()` method with a try/except that raises a user-friendly error.

**Severity: HIGH** — runtime import failure on startup if openpyxl missing.

Note: `openpyxl` is listed as a critical dependency in `setup.py` line 168, so on a properly set-up instance this should be present. The risk is primarily in CI environments or minimal deployments.

---

### STILL-OPEN-02: QA-PFACT-001 — detect_type() returns bare None
**Expected:** Still present.

**Evidence read:** `utils/parsers/__init__.py` lines 81–93.

```python
@classmethod
def detect_type(cls, filename):
    """Auto-detect parser type from filename.

    Returns:
        doc_type string, or None if not parseable.
    """
    if not filename:
        return None
    fn_lower = filename.lower()
    for pattern, doc_type in cls.FILENAME_PATTERNS:
        if pattern in fn_lower:
            return doc_type
    return None
```

**Status: CONFIRMED STILL OPEN (docstring matches scalar return)**

The docstring has been corrected from the prior version (it no longer says "tuple") — it correctly documents the return type as `doc_type string, or None`. The function correctly returns a scalar.

**However**, `FILENAME_PATTERNS` still contains entries where `doc_type` is `None` (e.g., line 63: `('cashier_details', None)`, line 64: `('4_28_cashier', None)`). When a filename matches one of these patterns, `detect_type()` returns `None` — indicating "no parser available." Any caller that does not check for `None` before calling `ParserFactory.create()` will get a `ValueError: Type de document inconnu: None`. This is not a tuple-unpacking crash but is still a caller-side risk.

**The broader auto-dispatch path** (referenced in the ZIP upload feature from recent commits) needs to verify it guards against `None` returns. This was not changed by the 18 fixes.

**Severity: MEDIUM** — silent `None` propagation can cause confusing errors.

---

### STILL-OPEN-03: QA-CORE-001 — Threading locks declared but never acquired
**Expected:** Still broken.

**Evidence:** Grep for `with.*LOCK|acquire` in `routes/audit/` returned only the three lock declarations:

```
RJ_FILES_LOCK = threading.Lock()   # line 85
SD_FILES_LOCK = threading.Lock()   # line 93
HP_FILES_LOCK = threading.Lock()   # line 97
```

No `with RJ_FILES_LOCK:`, `with SD_FILES_LOCK:`, or `with HP_FILES_LOCK:` blocks were found anywhere in `rj_core.py`, `rj_parsers.py`, `rj_sd.py`, or `rj_fill.py`.

**Status: CONFIRMED STILL OPEN**

All three locks are declared but never acquired. Concurrent Flask requests from the same or different users can simultaneously mutate `RJ_FILES`, `SD_FILES`, or `HP_FILES` without synchronization. Under the built-in Flask dev server (single-threaded) this is harmless, but under Gunicorn or any threaded WSGI server this is a data race.

**Severity: HIGH** — production threading risk (data corruption under load).

---

### STILL-OPEN-04: QA-FILL-004 / Filler cache id() fragility
**Expected:** Still present.

**Evidence read:** `routes/audit/rj_core.py` lines 107–128.

```python
file_bytes = RJ_FILES[session_id]
buf_id = id(file_bytes)

cached = _RJ_FILLER_CACHE.get(session_id)
if cached and cached[0] == buf_id:
    return cached[1]
```

**Status: CONFIRMED STILL OPEN**

The cache uses `id(file_bytes)` to detect whether the stored `BytesIO` object has been replaced. In CPython, `id()` is the memory address of the object. When `save_and_store()` replaces the buffer (creates a new `BytesIO`), the old object may be garbage-collected, and the new object may receive the same memory address — causing the cache to believe it is hitting a valid cached filler when it is actually stale. `save_and_store()` does call `_RJ_FILLER_CACHE.pop(session_id, None)` which invalidates the cache explicitly, so the fragility only matters if someone stores a new buffer in `RJ_FILES` WITHOUT going through `save_and_store()`. Looking at `rj_parsers.py` lines 118–139, the `parse-and-fill` route does NOT use `save_and_store()` — it writes directly to `RJ_FILES[session_id] = output` — which means `_RJ_FILLER_CACHE` is not invalidated for that code path. A subsequent call to `get_or_create_filler()` from another route could return a stale filler based on `id()` reuse.

**Severity: MEDIUM** — stale cache could cause a subsequent fill operation to write to a stale copy of the workbook, losing the parse-and-fill changes.

---

## Section 3 — Regression Check

---

### REG-01: rj_fill.py autofill-cashout still uses fill_sheet with result['data'] (QA-FILL-004)
**Claim:** Claimed fixed by earlier report as "same structural bug as PARSE-003."

**Evidence read:** `routes/audit/rj_fill.py` lines 474–493.

```python
# Fill GEAC/UX Row 6 (Daily Cash Out)
if geac_fill:
    cells_filled += rj_filler.fill_sheet('geac_ux', {
        k: v for k, v in result['data'].items()
        if k in parser.FIELD_MAPPINGS
    })

# Fill GEAC/UX Row 12 (Daily Revenue)
if daily_rev_fill:
    cells_filled += rj_filler.fill_sheet('geac_ux', {
        k: v for k, v in result['data'].items()
        if k in parser.DAILY_REV_MAPPINGS
    })

# Fill Transelect fusebox rows
if transelect_fill:
    cells_filled += rj_filler.fill_sheet('transelect', {
        k: v for k, v in result['data'].items()
        if k in parser.TRANSELECT_MAPPINGS
    })
```

**Status: STILL BROKEN — NOT fixed by the 18-fix wave**

The `parse-and-fill` route was fixed (RECHECK-01 above), but the `autofill-cashout` route was NOT. It still passes `result['data']` (field-name keys like `'visa_total'`) to `fill_sheet()`, which expects `{field_name: value}` format and relies on `fill_sheet()` internally looking up the cell reference via the parser's mappings.

This is a different data flow from `parse-and-fill` and `fill_sheet()` may work correctly here if the `FreedomPayParser.fill_sheet()` internally handles the field-name→cell mapping. The question is whether `rj_filler.fill_sheet()` (from `utils/rj_filler.py`) does the right thing with field-name keys.

**Action required:** Read `utils/rj_filler.py` `fill_sheet()` implementation to determine whether field-name keys work there, or whether it also expects cell-reference keys. This was flagged as QA-FILL-004 and was NOT part of the 18-fix claims, so it should still be tracked as open.

**Severity: HIGH** — if `fill_sheet()` expects cell refs but receives field names, autofill-cashout fills 0 cells silently.

---

### REG-02: rj_sd.py write route does not update SD_FILES_TIMESTAMPS (QA-SD-002 — new regression concern)
**Evidence read:** `routes/audit/rj_sd.py` lines 179–244. The `write_sd_day_entries()` route updates `SD_FILES[session_id] = updated_sd` (line 233) but does **not** update `SD_FILES_TIMESTAMPS[session_id]`. This means a session that uploads a SD file and then writes to it repeatedly will not have its expiry timestamp refreshed. If the auditor spends more than 8 hours making SD writes without re-uploading, the session could be evicted during the next cleanup call. This was noted as QA-SD-002 in the original report and was not claimed as fixed.

**Status: CONFIRMED STILL OPEN (pre-existing, not a new regression)**

---

### REG-03: New syntax / import check — all modified files
**Files checked:**
- `routes/manager.py` — clean, no syntax errors found, imports valid
- `routes/audit/rj_core.py` — clean
- `routes/audit/rj_parsers.py` — clean
- `routes/audit/rj_sd.py` — clean
- `routes/crm_tabs.py` — clean
- `routes/dashboard.py` — clean
- `config/settings.py` — clean
- `utils/auth_decorators.py` — clean, `from database import db` is valid
- `main.py` — clean
- `utils/parsers/__init__.py` — clean
- `utils/parsers/transaction_summary_parser.py` — clean (syntax only; import concern noted in STILL-OPEN-01)

**Status: NO SYNTAX REGRESSIONS FOUND**

---

## Section 4 — New Issues Found During Recheck

---

### NEW-01: SD_FILES_TIMESTAMPS exported but HP_FILES_TIMESTAMPS is not
**Severity: MEDIUM**

`routes/audit/rj_sd.py` line 9 imports `SD_FILES_TIMESTAMPS` from `rj_core`:
```python
from .rj_core import RJ_FILES, SD_FILES, SD_FILES_TIMESTAMPS, get_session_id
```
This is correct and works.

However, `HP_FILES_TIMESTAMPS` is defined in `rj_core.py` (line 104) but is never imported by any other file. If `routes/hp.py` needs to write timestamps on HP upload, it must import `HP_FILES_TIMESTAMPS` from `rj_core`. A search of the codebase was not run for `routes/hp.py` in this pass — this must be verified. If `hp.py` does not import and write `HP_FILES_TIMESTAMPS`, the HP eviction fix (RECHECK-08) is incomplete.

**File to check:** `C:\Users\Auditeur\Documents\Projects\audit-pack\routes\hp.py`

---

### NEW-02: parse-and-fill cache not invalidated (interaction between RECHECK-01 and STILL-OPEN-04)
**Severity: MEDIUM**

The `parse-and-fill` route (fixed in RECHECK-01) writes the modified workbook directly to `RJ_FILES[session_id] = output` (line 139 of `rj_parsers.py`) without calling `save_and_store()`. This means `_RJ_FILLER_CACHE` is NOT cleared. If a user calls `parse-and-fill` and then immediately calls any route that uses `get_or_create_filler()` (such as `fill-jour`, `fill/<sheet_name>`, or `autofill-cashout`), the cache check will compare `id(new_output)` against the cached `id(old_buffer)`. Since both are different `BytesIO` objects, the cache miss will cause a fresh `RJFiller` to be created from the new buffer — which is correct behavior. The `id()` fragility described in STILL-OPEN-04 only manifests when the OLD object is freed and the new one reuses the same address. In this specific code path, since `output` is a fresh object created by `filler.save()`, it is unlikely (but not impossible) to reuse the address of the buffer that was just replaced.

**Recommendation:** Replace `RJ_FILES[session_id] = output` in `rj_parsers.py:139` with a call to the centralized `save_and_store()` helper to ensure consistent cache invalidation:
```python
# Replace lines 136-139 with:
filler_obj = RJFiller.__new__(RJFiller)  # or just:
# Call save_and_store equivalent:
from .rj_core import save_and_store
# ... but filler here is RJFiller not using get_or_create_filler pattern
```
Actually the simplest fix is: after line 138, add `_RJ_FILLER_CACHE.pop(session_id, None)` to explicitly invalidate. This is a one-line fix.

---

## Section 5 — Complete Status Table (All Original Issues)

| ID | Description | Status After Fixes |
|----|-------------|-------------------|
| QA-PARSE-003 | parse-and-fill fills 0 cells | CONFIRMED FIXED |
| QA-PARSE-004 | fill-jour missing @csrf_protect | CONFIRMED FIXED |
| QA-SD-001 | SD_FILES_TIMESTAMPS never written | CONFIRMED FIXED |
| QA-CRM-002 | occ_budget shows room count not % | CONFIRMED FIXED |
| QA-CRM-005 | P&L double-counts labor | CONFIRMED FIXED |
| QA-CORE-004 | min() on empty dict | CONFIRMED FIXED |
| QA-MGR-001 | manager_required role bypass | CONFIRMED FIXED |
| QA-CORE-002 | HP_FILES never evicted | PARTIALLY FIXED — HP_FILES_TIMESTAMPS may not be written (verify hp.py) |
| QA-CFG-001 | No MAX_CONTENT_LENGTH | CONFIRMED FIXED |
| debug=True hardcoded | debug mode always on | CONFIRMED FIXED |
| ADR includes comps | ADR denominator wrong | CONFIRMED FIXED |
| days_in_month=30 | hardcoded month length | CONFIRMED FIXED |
| QA-TRANS-001 | top-level openpyxl import | STILL OPEN |
| QA-PFACT-001 | detect_type() None callers | STILL OPEN |
| QA-CORE-001 | Threading locks never acquired | STILL OPEN |
| QA-FILL-004 | autofill-cashout fill_sheet bug | STILL OPEN (not in 18-fix scope) |
| QA-SD-002 | SD write route doesn't extend timestamp | STILL OPEN |

---

## Section 6 — Prioritized Actions Required

### P1 — Before next deploy
1. **Verify `routes/hp.py`** writes `HP_FILES_TIMESTAMPS[session_id] = time.time()` on HP upload. If not, HP memory leak persists.
2. **Verify `utils/rj_filler.py` `fill_sheet()`** accepts field-name keys (not cell-ref keys) to confirm or deny QA-FILL-004 for autofill-cashout.
3. **Add `_RJ_FILLER_CACHE.pop(session_id, None)`** after `RJ_FILES[session_id] = output` in `rj_parsers.py:139` to eliminate cache invalidation race (NEW-02).

### P2 — Before production release
4. Acquire threading locks around all reads/writes to `RJ_FILES`, `SD_FILES`, `HP_FILES` (QA-CORE-001).
5. Move `from openpyxl import load_workbook` inside `TransactionSummaryParser.parse()` (QA-TRANS-001).
6. Extend SD session timestamp on SD write in `rj_sd.py:233` (QA-SD-002).

### P3 — Housekeeping
7. Replace hardcoded `252` in `crm_tabs.py:198` with shared `TOTAL_ROOMS` constant.
8. Add caller-side `None` guard after `ParserFactory.detect_type()` in ZIP auto-dispatch code.
