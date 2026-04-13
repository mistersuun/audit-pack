# QA Report: utils/parsers/* and utils/
## Last Updated: 2026-03-23
## Status: PARTIAL

---

## utils/parsers/__init__.py — ParserFactory

### Test QA-PFACT-001: `detect_type` returns None for unknown files with no explanation

- **File:Line:** parsers/__init__.py:87–91
- **Input:** `ParserFactory.detect_type('randomfile.pdf')`
- **Expected Output:** `(None, 'No matching parser')` — docstring says returns `(doc_type, label) or (None, reason)`
- **Actual Output:** Function returns just `None` (line 91), not a tuple. The docstring says it returns `(doc_type, label)` for known types and `(None, reason)` for unknown. But the actual return is a scalar `None` — no reason string. Callers that expect a tuple will get `TypeError: cannot unpack non-iterable NoneType object`.
- **Status:** FAIL
- **Severity:** P2 — HIGH if callers unpack the result
- **Verification needed:** Check all callers of `ParserFactory.detect_type()` to see if they unpack as a tuple.
- **This is NEW** — not reported in prior reviews.

---

### Test QA-PFACT-002: ZIP upload auto-dispatch (referenced in git log) not visible in parsers/__init__.py

- **Git commit:** `f06bf71 feat: ZIP upload avec auto-dispatch + 4 nouveaux parsers`
- **Check:** The `ParserFactory` has no ZIP handling. Searching for ZIP upload logic — this appears to be in a separate route not yet traced. The auto-dispatch likely lives in a route that calls `detect_type` per file in a ZIP. If `detect_type` returns `None` (scalar) for unrecognized files and the ZIP handler tries to unpack it as a tuple, it crashes.
- **Status:** WARNING — needs ZIP route identification
- **Severity:** P2 — HIGH if confirmed

---

## utils/parsers/transaction_summary_parser.py

### Test QA-TRANS-001: Hard import of openpyxl at module level — crash if not installed

- **File:Line:** transaction_summary_parser.py:23
- **Input:** `from utils.parsers import TransactionSummaryParser` when `openpyxl` is not installed
- **Expected Output:** Graceful ImportError with helpful message
- **Actual Output:** `from openpyxl import load_workbook` at line 23 is a top-level import. If openpyxl is missing, the entire `utils/parsers/__init__.py` import fails because it imports `TransactionSummaryParser` unconditionally. This would prevent the entire app from starting.

  By contrast, `DailyRevenueParser` wraps the `pdfplumber` import in a try/except inside `parse()`, providing a graceful failure. `TransactionSummaryParser` does not use this defensive pattern.

- **Status:** WARNING
- **Severity:** P2 — HIGH (can prevent app startup)
- **Fix:** Move the import inside `parse()` with a try/except, similar to `DailyRevenueParser.parse()`.
- **This is NEW** — not reported in prior reviews.

---

## utils/parsers/freedompay_parser.py

### Test QA-FREE-001: Parser in auto-fill mode always sets `confidence=0.0` when no cards dict given, then `validate()` may approve it

- **File:Line:** freedompay_parser.py:100–108
- **Input:** `FreedomPayParser(file_bytes=b'', daily_revenue_cards={})` — empty cards dict
- **Expected Output:** Parser reports failure
- **Actual Output:** `parse()` reaches the else branch (line 102–108), appends a warning, sets `confidence=0.0`, sets `_parsed=True`. Then `validate()` is called by `get_result()`. If `validate()` only checks for errors (not confidence), it returns `True` and `get_result()` returns `{'success': True, ...}` with confidence=0.0 and empty data. The caller in `autofill_geac_cashout` checks `if not result['success']` — since it's True, it proceeds to fill zero cells.
- **Status:** WARNING (silent no-op, not a crash)
- **Severity:** P3 — LOW
- **This is NEW** — not reported in prior reviews.

---

## utils/parsers/base_parser.py

### Test QA-BASE-001: `get_fillable_data()` called before `parse()` silently triggers re-parse

- **File:Line:** base_parser.py:73–79
- **Input:** Call `parser.get_fillable_data()` without calling `parse()` first
- **Expected Output:** `parse()` called automatically (this is the intended behavior per the guard at line 72)
- **Actual Output:** Correct. The guard `if not self._parsed: self.parse()` ensures parsing happens. This is intentional design, not a bug.
- **Status:** PASS

---

## utils/csrf.py

### Test QA-CSRF-001: CSRF token popped from JSON body — modifies request data

- **File:Line:** csrf.py:36
- **Input:** `POST /api/rj/fill/recap` with JSON body `{"_csrf_token": "abc123", "amount": 500}`
- **Expected Output:** Token validated, body available with `_csrf_token` removed or still present
- **Actual Output:** `data.pop('_csrf_token', '')` at line 36 **mutates** the dict returned by `request.get_json()`. Flask caches the parsed JSON body and returns the same dict object on subsequent calls to `request.get_json()`. So if the route handler also calls `request.get_json()`, it will receive the dict **with `_csrf_token` already removed**. This is by design (token consumed after validation) but could cause confusion if a developer checks `request.get_json()` in a route after the decorator runs and doesn't find the token.

  More importantly: if `data.get_json(silent=True)` returns the same cached dict across the decorator and the route, the route handler will see the body without `_csrf_token` — which is correct expected behavior. No functional bug here.

- **Status:** PASS (behavior is correct, just subtle)

---

## routes/auth_v2.py / auth.py

### Test QA-AUTH-001: Dual auth blueprints — potential route name collision

- **File:Line:** main.py:50–51
- **Input:** `app.register_blueprint(auth_bp); app.register_blueprint(auth_v2)`
- **Expected Output:** Both blueprints register successfully
- **Actual Output:** `auth_bp` is imported from `routes/auth.py` and `auth_v2` from `routes/auth_v2.py`. If both define a route named `login`, Flask's `url_for('auth_v2.login')` used throughout the codebase would resolve correctly only if `auth_v2` is the authoritative login blueprint. The `login_required` decorators in `rj_core.py`, `crm_tabs.py`, `dashboard.py`, `manager.py` all redirect to `url_for('auth_v2.login')`. This is consistent — no collision detected.
- **Status:** PASS
