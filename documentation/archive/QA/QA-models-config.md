# QA Report: database/models.py and config/settings.py
## Last Updated: 2026-03-23
## Status: FAIL

---

## config/settings.py

### Test QA-CFG-001: No MAX_CONTENT_LENGTH (Confirmed Prior)

- **File:Line:** config/settings.py (entire file)
- **Input:** Any file upload endpoint (`/api/rj/upload`, `/api/sd/upload`, `/api/rj/parse`)
- **Expected Output:** Flask rejects files larger than a configured maximum
- **Actual Output:** `Config` class has no `MAX_CONTENT_LENGTH` attribute. Flask defaults to unlimited upload size. A malicious or accidental 2 GB upload will be read entirely into memory via `io.BytesIO(file.read())` before any processing.
- **Status:** FAIL
- **Severity:** P1 — CRITICAL (DoS)
- **Fix:** Add `MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB` to Config. Flask will then automatically return 413 for oversized requests.
- **Marks as confirmed prior finding:** Yes

---

## database/models.py

### Test QA-MDL-001: `DailyReport.to_dict()` silently adds USD and CDN deposits without null guards

- **File:Line:** models.py:141–144
- **Input:** Any code path that calls `.to_dict()` on a `DailyReport` where `deposit_cdn` or `deposit_us` is NULL in the database (possible for old records)
- **Expected Output:** Safe fallback to 0.0
- **Actual Output:**

  ```python
  'total': self.deposit_cdn + self.deposit_us,
  ```

  Both columns have `default=0`, so new records are safe. However, SQLAlchemy `default` only applies at Python ORM insertion time, not at the DB level (no `server_default`). If rows were inserted via raw SQL or migration scripts without these values, `deposit_cdn` could be `None`. `None + float` raises `TypeError`.

- **Status:** WARNING
- **Severity:** P3 — LOW (only affects legacy rows or raw SQL inserts)
- **Fix:** Use `(self.deposit_cdn or 0) + (self.deposit_us or 0)`

---

### Test QA-MDL-002: Orphan records possible — TaskCompletion has no cascade delete from Task

- **File:Line:** models.py:670 (Task model), 713 (TaskCompletion model)
- **Input:** Delete a Task record via `Task.query.filter_by(id=X).delete()`
- **Expected Output:** Associated TaskCompletion records deleted (cascade)
- **Actual Output:** `Task` has `completions = db.relationship('TaskCompletion', backref='task', lazy=True)` but no `cascade='all, delete-orphan'`. Deleting a task leaves orphan `TaskCompletion` rows with dangling `task_id` foreign keys. SQLite's default behavior allows this without error (no FK enforcement unless `PRAGMA foreign_keys = ON`). The orphans will be invisible to the application but consume space.
- **Status:** WARNING
- **Severity:** P3 — LOW (SQLite FK not enforced by default)
- **Fix:** Add `cascade='all, delete-orphan'` to the `completions` relationship.

---

### Test QA-MDL-003: `MonthlyExpense` and `MonthlyBudget` share similar table-constraint naming — unique constraint names may conflict on PostgreSQL migration

- **File:Line:** models.py:422–424, 611–613
- **Input:** Migrating schema to PostgreSQL
- **Actual Output:** Both tables use `db.UniqueConstraint('year', 'month', name='uq_monthly_...')`. Names are distinct (`uq_monthly_expense_period` vs `uq_monthly_budget_period`) so no immediate conflict.
- **Status:** PASS

---

### Test QA-MDL-004: `NightAuditSession.status` has no database-level CHECK constraint

- **File:Line:** models.py:1115
- **Input:** INSERT via direct SQL: `status = 'invalid_status'`
- **Expected Output:** DB rejects invalid status
- **Actual Output:** `status = db.Column(db.String(20), default='draft')` — no SQLAlchemy `CheckConstraint`. Application code must enforce valid values. SQLite will accept any string.
- **Status:** WARNING
- **Severity:** P3 — LOW (application-level validation exists in routes, but no DB-level guard)

---

## manager.py

### Test QA-MGR-001: `manager_required` checks authenticated but not role (Confirmed Prior)

- **File:Line:** manager.py:22–29
- **Input:** Any authenticated user (including `night_auditor` role) accessing `/manager` or any `/api/manager/*` endpoint
- **Expected Output:** Only users with `gm`, `gsm`, or `admin` roles can access manager portal
- **Actual Output:**

  ```python
  def manager_required(f):
      @wraps(f)
      def decorated_function(*args, **kwargs):
          if not session.get('authenticated'):
              return redirect(url_for('auth_v2.login'))
          return f(*args, **kwargs)   # ← any authenticated user passes
      return decorated_function
  ```

  A night auditor can view executive KPIs, GOPPAR data, labor analytics, and all management-only financial data by simply navigating to `/manager` or calling `/api/manager/overview`. The decorator name implies manager-only access, but the implementation is identical to a plain `login_required`.

- **Status:** FAIL
- **Severity:** P1 — CRITICAL (authorization bypass)
- **Fix:** Add `user_role = session.get('user_role_type'); if user_role not in ('gm', 'gsm', 'admin'): return redirect(...)` or use the existing `role_required('gm', 'gsm', 'admin')` decorator from `utils/auth_decorators.py`.
- **Marks as confirmed prior finding:** Yes
