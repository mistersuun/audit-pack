# QA Report: routes/audit/rj_sd.py
## Last Updated: 2026-03-23
## Status: FAIL

---

### Test QA-SD-001: SD file upload never writes to SD_FILES_TIMESTAMPS (NEW)

- **File:Line:** rj_sd.py:59–71
- **Input:** `POST /api/sd/upload` with a valid SD file
- **Expected Output:** `SD_FILES_TIMESTAMPS[session_id]` updated so that `_cleanup_expired_sessions()` can evict the file after 8 hours
- **Actual Output:**

  ```python
  # rj_sd.py:59-71
  session_id = get_session_id()
  file_bytes.seek(0)
  SD_FILES[session_id] = file_bytes
  # SD_FILES_TIMESTAMPS[session_id] = time.time()  ← THIS LINE IS MISSING
  ```

  `SD_FILES_TIMESTAMPS` is declared in `rj_core.py:103` and read by `_cleanup_expired_sessions()` at line 155, but `upload_sd()` in `rj_sd.py` never writes to it. As a result:
  - `SD_FILES_TIMESTAMPS` is always `{}` (empty)
  - `_cleanup_expired_sessions()` iterates the empty dict and removes nothing
  - SD files accumulate in memory for the lifetime of the process

- **Status:** FAIL
- **Severity:** P1 — CRITICAL (memory leak)
- **Steps to reproduce:**
  1. Upload an SD file → `SD_FILES[sid]` populated, `SD_FILES_TIMESTAMPS[sid]` NOT populated
  2. Wait 8 hours and trigger any upload (which calls `_cleanup_expired_sessions()`)
  3. SD file is still present in memory
- **Fix:** Add `from .rj_core import SD_FILES_TIMESTAMPS` to rj_sd.py imports, then add `SD_FILES_TIMESTAMPS[session_id] = time.time()` after `SD_FILES[session_id] = file_bytes` in `upload_sd()`.
- **Cross-reference:** This is the same bug documented in QA-CORE-003 from a different angle.
- **This is NEW** — not reported in prior reviews.

---

### Test QA-SD-002: SD write route returns the updated BytesIO without updating SD_FILES_TIMESTAMPS

- **File:Line:** rj_sd.py:231
- **Input:** `POST /api/sd/day/<day>/entries` to write entries back to the SD file
- **Expected Output:** Timestamp updated so session stays alive
- **Actual Output:** `SD_FILES[session_id] = updated_sd` at line 231 writes a new BytesIO. No timestamp update. The session's last-activity time is stuck at the upload time (which was never recorded anyway per QA-SD-001). If timestamps were ever fixed, the write operations would not extend the session lifetime.
- **Status:** WARNING (secondary to QA-SD-001)
- **Severity:** P3 — LOW (impact only after QA-SD-001 is fixed)
