# QA Report: routes/audit/rj_core.py
## Last Updated: 2026-03-23
## Status: FAIL

---

### Test QA-CORE-001: Threading locks declared but never acquired

- **Input:** Any two concurrent POST requests to `/api/rj/upload` or `/api/rj/fill/*`
- **Expected Output:** Requests serialise access to `RJ_FILES`, `SD_FILES`, `HP_FILES` via the declared locks
- **Actual Output:** `RJ_FILES_LOCK`, `SD_FILES_LOCK`, `HP_FILES_LOCK` are created at lines 85, 93, 97. A full-text search of the entire `routes/audit/` package finds zero uses of `.acquire()`, `with RJ_FILES_LOCK:`, or any equivalent. The locks exist only as objects — they are never acquired anywhere in the codebase.
- **Status:** FAIL
- **Severity:** P1 — CRITICAL
- **Comments:** Under Werkzeug's threaded dev server and any production WSGI server, two simultaneous users can corrupt `RJ_FILES` dict during concurrent read-modify-write. This is a prior-review finding, now **execution-verified**: grepping `threading.Lock` shows the locks are declared; grepping `.acquire` in the same directory returns zero results. The bug is real.
- **Marks as confirmed prior finding:** Yes

---

### Test QA-CORE-002: HP_FILES dictionary never evicted

- **Input:** More than 10 HP file uploads across different sessions
- **Expected Output:** Old HP sessions cleaned up by `_cleanup_expired_sessions()`
- **Actual Output:** `_cleanup_expired_sessions()` (lines 142–171) cleans `RJ_FILES` and `SD_FILES`. The code has `HP_FILES`, `HP_FILES_LOCK`, and `HP_FILES_TIMESTAMPS` declared (lines 96–104), but `_cleanup_expired_sessions()` contains zero references to `HP_FILES`. It never ages out HP entries. `HP_FILES` grows unbounded for the lifetime of the process.
- **Status:** FAIL
- **Severity:** P1 — CRITICAL (memory leak)
- **Comments:** The fix pattern is clear: replicate the SD_FILES block for HP_FILES inside `_cleanup_expired_sessions`. This is a prior-review finding, **execution-verified**.
- **Marks as confirmed prior finding:** Yes

---

### Test QA-CORE-003: SD_FILES cleanup logic reads timestamps that are never written (NEW)

- **Input:** Upload an SD file via `POST /api/sd/upload`, wait for session expiry
- **Expected Output:** Old SD file session evicted from `SD_FILES` by `_cleanup_expired_sessions()`
- **Actual Output:** `_cleanup_expired_sessions()` iterates `SD_FILES_TIMESTAMPS` (line 155) looking for expired entries. However, `rj_sd.py:61` writes `SD_FILES[session_id] = file_bytes` but **never writes to `SD_FILES_TIMESTAMPS`**. A grep of the entire `routes/audit/rj_sd.py` confirms zero assignments to `SD_FILES_TIMESTAMPS`. Result: `SD_FILES_TIMESTAMPS` is always empty, so the expiry loop at line 155 never finds anything to expire. SD files accumulate in memory indefinitely, exactly like the HP_FILES problem — but through a different mechanism.
- **Status:** FAIL
- **Severity:** P1 — CRITICAL (memory leak)
- **Steps to reproduce:**
  1. Upload an SD file via `/api/sd/upload`
  2. Check `SD_FILES_TIMESTAMPS` — it is empty
  3. Call `_cleanup_expired_sessions()` — SD entry is never removed
- **Expected vs Actual:**
  - Expected: `SD_FILES_TIMESTAMPS[session_id] = time.time()` written in `upload_sd()`
  - Actual: Not present. `SD_FILES_TIMESTAMPS` is always `{}`
- **This is NEW** — not reported in any prior review.

---

### Test QA-CORE-004: `_cleanup_expired_sessions` can raise `ValueError` if RJ_FILES_TIMESTAMPS is empty (NEW)

- **Input:** Call `_cleanup_expired_sessions()` when `RJ_FILES` has entries but `RJ_FILES_TIMESTAMPS` is empty (e.g., first upload under a race condition that skips timestamp write)
- **Expected Output:** Safe cleanup, or no-op
- **Actual Output:** Line 163: `oldest = min(RJ_FILES_TIMESTAMPS, key=RJ_FILES_TIMESTAMPS.get)` — `min()` on an empty dict raises `ValueError: min() arg is an empty sequence`. This can crash the cleanup function inside an upload handler.
- **Status:** FAIL
- **Severity:** P2 — HIGH
- **Comments:** Defensive fix: guard with `if RJ_FILES_TIMESTAMPS:` before calling `min()`. Same pattern applies to the SD_FILES loop at line 170.

---

### Test QA-CORE-005: `parse_and_fill` does not invalidate `_RJ_FILLER_CACHE` after save

- **Note:** This bug is documented in detail in QA-rj-parsers.md (QA-PARSE-002). It involves `rj_parsers.py` calling `filler.save()` directly and replacing `RJ_FILES[session_id]` with a new BytesIO, but not popping `_RJ_FILLER_CACHE`. The stale cache then returns the old unfilled filler on the next request.
- **Cross-reference:** QA-PARSE-002
