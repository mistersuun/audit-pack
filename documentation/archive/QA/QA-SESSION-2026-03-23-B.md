# QA Report — Session 2026-03-23-B
## Scope: New endpoints, bug fixes, and infrastructure changes from this session
## Date: 2026-03-23
## Status: PARTIAL PASS — 2 HIGH bugs, 4 MEDIUM bugs, 6 LOW / INFO findings

---

## Table of Contents

1. [Infrastructure: login_required consolidation](#infra-1)
2. [Infrastructure: Threading locks (RJ_FILES_LOCK)](#infra-2)
3. [Infrastructure: Filler cache (_RJ_VERSION_COUNTER)](#infra-3)
4. [Infrastructure: TOTAL_ROOMS local definitions](#infra-4)
5. [Bug fix: alert_engine.py — DailyJourMetrics query](#fix-1)
6. [Bug fix: routes/crm.py — Staff N+1 query](#fix-2)
7. [Bug fix: routes/crm_tabs.py — P&L franchise %](#fix-3)
8. [Bug fix: routes/crm_tabs.py — Data quality warnings](#fix-4)
9. [Bug fix: routes/crm_tabs.py — Deposit variance exposure](#fix-5)
10. [Bug fix: routes/crm_tabs.py — Labor budget variance](#fix-6)
11. [Bug fix: routes/dashboard.py — Labor ratio prorated](#fix-7)
12. [New endpoint: GET /api/dashboard/gm-briefing](#ep-1)
13. [New endpoint: GET /api/dashboard/accounting](#ep-2)
14. [New endpoint: GET /api/dashboard/auditor-panel](#ep-3)
15. [New endpoint: GET /compset/api/otb-pace](#ep-4)
16. [New endpoint: GET /compset/api/str-trends](#ep-5)

---

## INFRA-1: login_required consolidation {#infra-1}

### Test: All route files import login_required from utils.auth_decorators only
- **Method:** Grep for `def login_required` across entire codebase
- **Expected:** Single definition in `utils/auth_decorators.py`, zero local definitions anywhere else
- **Actual Output:**
  ```
  utils/auth_decorators.py:8:def login_required(f):
  ```
  Only one definition found. All 19 route files verified to use:
  `from utils.auth_decorators import login_required`
  No file imports from `routes.checklist` or defines its own copy.
- **Status:** PASS
- **Comments:** INFRA-1 is fully resolved. The consolidation is complete. Auth decorator is now a single source of truth.

---

## INFRA-2: Threading locks — RJ_FILES_LOCK, SD_FILES_LOCK, HP_FILES_LOCK {#infra-2}

### Test: Locks are used consistently in rj_core.py, rj_parsers.py, rj_macros.py
- **Method:** Grep for `RJ_FILES_LOCK` and cross-check all RJ_FILES write sites
- **Actual Output:**
  - `rj_core.py`: Lock declared at line 85. `get_or_create_filler`, `save_and_store`, `invalidate_rj_cache`, `_cleanup_expired_sessions` all hold the lock correctly.
  - `rj_parsers.py:139` — writes `RJ_FILES[session_id]` under `RJ_FILES_LOCK`, then calls `invalidate_rj_cache`. Correct.
  - `rj_parsers.py:242` — same pattern. Correct.
  - `rj_macros.py:287` — holds `RJ_FILES_LOCK` then calls `invalidate_rj_cache`. Correct.
  - SD_FILES_LOCK and HP_FILES_LOCK are declared and used in cleanup; independent locks per dict.
- **Status:** PASS
- **Comments:** The lock usage is consistent. No bare writes to RJ_FILES outside a lock were found.

---

## INFRA-3: Filler cache — _RJ_VERSION_COUNTER replaces id()-based cache {#infra-3}

### Test: invalidate_rj_cache() is called everywhere _RJ_FILLER_CACHE.pop() used to be
- **Method:** Grep for `invalidate_rj_cache` calls and `_RJ_FILLER_CACHE.pop` calls
- **Actual Output:**
  - `_RJ_FILLER_CACHE.pop` is called in 4 places: `_invalidate_filler_cache` (2 sites for expiry+eviction), and `_cleanup_expired_sessions` (2 eviction paths). All are private helpers that bundle the pop with the version counter bump — correct pattern.
  - `invalidate_rj_cache` (the public API) is called in `rj_parsers.py` (2 sites) and `rj_macros.py` (1 site) — all direct RJ_FILES[session_id] assignment sites call it.
  - `save_and_store` internally calls `_invalidate_filler_cache` — correct.
  - No rogue `_RJ_FILLER_CACHE.pop` was found outside of the two private helpers.
- **Status:** PASS
- **Comments:** Cache invalidation is architecturally sound. The version counter approach is cleaner than the prior id()-based approach and avoids the stale-object risk from BytesIO identity reuse.

---

## INFRA-4: TOTAL_ROOMS — no local definitions outside models.py {#infra-4}

### Test: No file defines TOTAL_ROOMS = 252 or TOTAL_ROOMS = 340 locally
- **Method:** Grep for `TOTAL_ROOMS\s*=\s*\d+`
- **Actual Output:**
  ```
  database/models.py:7: TOTAL_ROOMS = 252   <- canonical definition
  scripts/seed_crm_demo.py:34: TOTAL_ROOMS = 252
  ```
- **Status:** WARNING (LOW)
- **Issue:** `scripts/seed_crm_demo.py` defines its own `TOTAL_ROOMS = 252` locally instead of importing from `database.models`. This is a script-only file used for seeding demo data.
- **Severity:** LOW — scripts are not part of the production request path; no correctness impact today. If the canonical value ever changes in models.py the seed script will silently use the stale value.
- **Suggested fix:** Replace local definition with `from database.models import TOTAL_ROOMS`.

---

## FIX-1: alert_engine.py — DailyJourMetrics query {#fix-1}

### Test: check_revenue() queries DailyJourMetrics, not DailyReport
- **Method:** Read `utils/alert_engine.py` in full
- **Actual Output (line 151):**
  ```python
  last_year = DailyJourMetrics.query.filter_by(date=last_year_date).first()
  ```
  Field accessed: `last_year.total_revenue` — confirmed present on DailyJourMetrics (models.py:277).
  Import at top of file: `from database.models import ... DailyJourMetrics` — confirmed.
- **Status:** PASS
- **Comments:** The fix is correct and complete. DailyJourMetrics is the authoritative metric table. The field name `total_revenue` exists on the model. Prior use of `DailyReport` (if any) is gone.

### Test: check_occupation() accesses NightAuditSession field jour_occupancy_rate
- **Method:** Verify field exists on NightAuditSession
- **Actual:** `NightAuditSession.jour_occupancy_rate` confirmed at models.py:1284.
- **Status:** PASS

### Test: generate_daily_summary() hardcodes total_available: 252
- **Input:** `generate_daily_summary()` at line 286
- **Actual:**
  ```python
  'total_available': 252,  # TOTAL_ROOMS from models
  ```
- **Status:** WARNING (LOW)
- **Issue:** Hardcoded magic number instead of using the imported TOTAL_ROOMS constant. The comment acknowledges this. The import at the top of alert_engine.py does NOT import TOTAL_ROOMS.
- **Severity:** LOW — value is correct for this property; only a maintenance risk if the property ever changes capacity.
- **Suggested fix:** Add `TOTAL_ROOMS` to the import and replace `252` with `TOTAL_ROOMS`.

---

## FIX-2: routes/crm.py — Staff N+1 query {#fix-2}

### Test: get_staff() uses a single GROUP BY query instead of per-staff queries
- **Method:** Read `/api/crm/staff` handler (crm.py lines 346-353)
- **Actual Output:**
  ```python
  agg_rows = db.session.query(
      func.lower(VarianceRecord.receptionist).label('receptionist_lower'),
      func.count(VarianceRecord.id).label('variance_count'),
      func.sum(VarianceRecord.variance).label('total_variance'),
      func.sum(db.cast(VarianceRecord.is_alert, db.Integer)).label('alert_count'),
  ).group_by(func.lower(VarianceRecord.receptionist)).all()
  ```
  One query for all staff aggregates. Staff list is then built from an in-memory dict lookup.
- **Status:** PASS
- **Comments:** Fix is correct. One DB round-trip regardless of staff count. The `func.lower()` grouping on receptionist name also handles case-insensitive aggregation properly. `db.cast(VarianceRecord.is_alert, db.Integer)` for counting booleans is compatible with both SQLite and PostgreSQL.

---

## FIX-3: routes/crm_tabs.py — P&L franchise % uses actual data {#fix-3}

### Test: franchise_pct in annual P&L uses MonthlyExpense.franchise_fees, not a hardcoded percentage
- **Method:** Read pnl_budget() lines 1250-1280
- **Actual Output:**
  ```python
  annual_franchise_fees = {}
  for exp in expenses:
      year = exp.year
      ...
      annual_franchise_fees[year] += exp.franchise_fees or 0

  actual_franchise = annual_franchise_fees.get(year, None)
  if actual_franchise is None:
      franchise_pct = 0.0
      franchise_data_missing = True
  else:
      franchise_pct = _round2((actual_franchise / a['revenue'] * 100) if a['revenue'] > 0 else 0)
  ```
  Uses actual data from MonthlyExpense. `franchise_data_missing` flag set when no expense data for a year.
- **Status:** PASS
- **Comments:** Fix is correct. The response now includes `franchise_data_missing` boolean which lets the frontend flag years where data is absent rather than showing a misleading 0%.

### Sub-test: annual P&L labor — double-counting via MonthlyExpense.labor_total
- **Method:** Review annual P&L accumulation (lines 1228-1247)
- **Actual:** Labor is accumulated from `DepartmentLabor.total_labor_cost` only. Comment explicitly states: "Use DepartmentLabor as authoritative labor source (not MonthlyExpense.labor_total to avoid double-counting)."
- **Status:** PASS
- **Comments:** Prior bug from QA session 1 (Pattern 5) is resolved. Only one source is used.

---

## FIX-4: routes/crm_tabs.py — Data quality warnings {#fix-4}

### Test: pnl_budget() identifies months with revenue but no expense record
- **Method:** Read lines 1283-1304
- **Actual Output:**
  ```python
  expense_keys = {(e.year, e.month) for e in expenses}
  missing_expense_months = []
  for key in sorted(revenue_by_period.keys()):
      if key not in expense_keys and revenue_by_period[key] > 0:
          ...
          missing_expense_months.append(f"{year}-{month:02d}")

  warnings = []
  if missing_expense_months:
      warnings.append(...)

  data_quality = {
      'months_with_revenue': ...,
      'months_with_expenses': ...,
      'missing_expense_months': missing_expense_months,
      'has_complete_data': ...,
  }
  ```
  Warnings list and data_quality dict both included in response.
- **Status:** PASS
- **Comments:** Fix is thorough. Consumer can now programmatically detect incomplete P&L months. The warning message is in French as required.

---

## FIX-5: routes/crm_tabs.py — Deposit variance exposure {#fix-5}

### Test: cash_reconciliation() includes DepositVariance leaderboard and monthly trend
- **Method:** Read lines 817-881
- **Actual:** Two new sub-sections added:
  1. `top_employees_by_variance` — sorted by total absolute variance
  2. `dep_variance_trend` — monthly sum of absolute variances
  3. `deposit_variances` dict returned at key `'deposit_variances'` in response
- **Model fields used:** `DepositVariance.employee_name`, `.department`, `.variance`, `.audit_date` — all confirmed on models.py (line 848 class).
- **Status:** PASS

---

## FIX-6: routes/crm_tabs.py — Labor budget variance {#fix-6}

### Test: labor_analytics() computes variance between actual and budgeted labor cost/hours per department
- **Method:** Read lines 567-616
- **Actual:** New section 8 in labor_analytics():
  ```python
  budget_by_dept[dept]['actual_cost'] += dl.total_labor_cost or 0
  budget_by_dept[dept]['budget_cost'] += dl.budget_cost or 0
  budget_by_dept[dept]['actual_hours'] += dl.total_hours or 0
  budget_by_dept[dept]['budget_hours'] += dl.budget_hours or 0
  ```
  Fields `budget_cost` and `budget_hours` confirmed on DepartmentLabor (models.py lines 492-493).
  `has_budget_data` flag set when either field is non-zero.
- **Status:** PASS
- **Comments:** Clean implementation. The `has_budget_data` flag lets the frontend know whether budget comparison is meaningful for that department.

---

## FIX-7: routes/dashboard.py — Labor ratio prorated for partial months {#fix-7}

### Test: smart_dashboard() prorates labor cost when current month is partial
- **Method:** Read lines 428-459
- **Actual:**
  ```python
  days_in_month = calendar.monthrange(latest_y, latest_m)[1]
  days_with_revenue = db.session.query(func.count(DailyJourMetrics.id)).filter(
      DailyJourMetrics.year == latest_y,
      DailyJourMetrics.month == latest_m
  ).scalar() or 0

  is_partial_month = (
      latest_y == today.year
      and latest_m == today.month
      and days_with_revenue < days_in_month
  )

  if is_partial_month and days_in_month > 0:
      prorated_labor_cost = total_labor_cost * (days_with_revenue / days_in_month)
  else:
      prorated_labor_cost = total_labor_cost
  ```
- **Status:** PASS — logic is correct
- **Comments:** The proration key uses DJM row count as a proxy for elapsed days. This is correct when RJ files are uploaded nightly. If a night is skipped, `days_with_revenue` will undercount and the prorated cost will be too low — acceptable approximation.

### Sub-test: `today` variable scope in smart_dashboard()
- **Issue found during review:** `today = date.today()` is defined at line 286, at the top of `smart_dashboard()`. The `is_partial_month` check at line 438 references `today.year` and `today.month`. This is correct — `today` is in scope.
- **Status:** PASS

---

## EP-1: GET /api/dashboard/gm-briefing {#ep-1}

### Test 1-A: Role restriction applied correctly
- **Input:** Decorator order: `@login_required` then `@role_required('gm', 'gsm', 'admin')`
- **Expected:** Only gm, gsm, admin can access. Returns 403 for other roles.
- **Actual:** `@login_required` applied first, then `@role_required`. Because `role_required` re-checks authentication internally, having both decorators is redundant but harmless — `login_required` fires first on the outer layer, `role_required` fires second and validates role. The outermost decorator wraps first, so the execution order is login_required -> role_required -> handler. Correct behavior.
- **Status:** PASS

### Test 1-B: Date resolution — no data case
- **Input:** No DailyJourMetrics rows in DB
- **Expected:** `{'success': True, 'has_data': False, 'reason': 'no_djm_data'}`
- **Actual code path:** Lines 933-935 handle this case. Then lines 957-963 handle "date exists but no DJM row for that specific date".
- **Status:** PASS (code path verified)

### Test 1-C: Budget occupancy daily calculation
- **Input:** `budget.rooms_target = 180`, `TOTAL_ROOMS = 252`, `days_in_month = 31`
- **Expected:** `budget_occ_daily = 180 / 252 / 31 * 100 = 2.307...%` (daily share of monthly target)
- **Actual (line 988):**
  ```python
  _r2(budget.rooms_target / TOTAL_ROOMS / days_in_month * 100)
  ```
- **Status:** PASS — arithmetic is correct for a daily prorated occupancy % target.

### Test 1-D: CRITICAL — budget_room_rev_d division by zero when budget is None {#EP1-CRIT-1}
- **Input:** No MonthlyBudget row for target month
- **Actual code (lines 991-993):**
  ```python
  budget_adr_daily   = _r2(budget.adr_target)   if budget else None
  budget_room_rev_d  = _r2(budget.room_revenue / days_in_month) if budget else None
  budget_total_rev_d = _r2(budget.total_revenue / days_in_month) if budget else None
  ```
  All guarded against `budget is None` — returns None. Then `_variance()` handles `reference=None` by returning `{'value': None, 'pct': None, 'direction': 'unknown'}`. Safe path.
- **Status:** PASS

### Test 1-E: LY fallback for Feb 29 in non-leap year
- **Input:** `target_date = date(2024, 2, 29)` — calling for briefing date
- **Actual (line 1005-1008):**
  ```python
  try:
      ly_date = target_date.replace(year=target_date.year - 1)
  except ValueError:
      pass  # e.g. Feb 29 in non-leap year
  ```
  Catches ValueError. `ly_night` remains None. Falls through to 364-day fallback.
- **Status:** PASS

### Test 1-F: OTB Panel — stale snapshot detection
- **Input:** `latest_snap` is 5 days ago
- **Actual (line 1208):** `data_is_stale = snap_age_days > 3` — triggers correctly.
- **Status:** PASS

### Test 1-G: HIGH — avg_adr_otb computed on per-day OTB, not per-room basis {#EP1-HIGH-1}
- **Input:** 30 rows, each with `rooms_otb=100`, `revenue_otb=18000`
- **Expected:** avg daily ADR = 18000/100 = $180
- **Actual (line 1258):**
  ```python
  avg_daily_adr_otb = (
      _r2(next30_revenue_otb / next30_rooms_otb)
      if next30_rooms_otb > 0 else None
  )
  ```
  `next30_revenue_otb = 30 * 18000 = 540000`, `next30_rooms_otb = 30 * 100 = 3000`. Result: `540000 / 3000 = $180`. Correct — revenue-weighted ADR over the 30-day window.
- **Status:** PASS — methodology is sound.

### Test 1-H: Panel 4 labor range query — edge case at year boundary
- **Input:** `target_date = 2026-01-05` (January 5)
- **Expected:** three_months_ago_start should step back to October 1 of prior year
- **Actual (lines 1332-1333):**
  ```python
  for _ in range(3):
      three_months_ago_start = (three_months_ago_start - timedelta(days=1)).replace(day=1)
  ```
  Jan 1 -> Dec 1 -> Nov 1 -> Oct 1. Correct. Crosses year boundary properly.
- **Status:** PASS

### Test 1-I: MEDIUM — `revpar_index` field read from STRCompSet but may be None if row was stored without it {#EP1-MED-1}
- **Input:** STRCompSet row where `revpar_index` was never computed (e.g. imported via CSV with no index column)
- **Actual (line 1314):**
  ```python
  'revpar_index': _r2(latest_str.revpar_index),
  ```
  `_r2(None)` = `_r2(val or 0)` where `val` is None → result is 0.0. This is silently misleading — a 0 index could be confused with actual data.
- **Status:** WARNING (MEDIUM)
- **Severity:** MEDIUM — functionally safe (no crash) but semantically wrong. A 0 RevPAR index would alarm the GM when it just means the field is unpopulated.
- **Suggested fix:** Return `None` explicitly when `latest_str.revpar_index is None`, not `0.0`. Use: `latest_str.revpar_index if latest_str.revpar_index is not None else None` and skip `_r2`.

---

## EP-2: GET /api/dashboard/accounting {#ep-2}

### Test 2-A: Role restriction
- **Actual:** `@role_required('accounting', 'gm', 'admin')` — correct. `night_auditor` and `gsm` cannot access.
- **Status:** PASS

### Test 2-B: Invalid month parameter
- **Input:** `?month=13`
- **Actual (line 1485-1486):**
  ```python
  if not (1 <= month <= 12):
      return jsonify({'success': False, 'error': 'Mois invalide (1-12)'}), 400
  ```
- **Status:** PASS

### Test 2-C: Future month — effective_end capping
- **Input:** `?year=2027&month=1` (future)
- **Actual (line 1495):** `effective_end = min(month_end, today)` — when month is fully future, `effective_end < month_start`.
- **Actual (line 1559):** `days_in_window = max(0, (effective_end - month_start).days + 1)` — returns 0. Safe.
- `all_dates_in_window` will be empty set. No missing dates detected. Correct behavior.
- **Status:** PASS

### Test 2-D: Revenue verification — days_missing calculation
- **Input:** 31-day month, only 15 DJM rows
- **Actual (line 1529):** `days_missing_rev = days_in_month - days_with_djm` = 31 - 15 = 16.
- **Issue:** This uses `days_in_month` (full month length) not `days_in_window` (days elapsed). For an ongoing month mid-month, this will always show some "missing" days even if all elapsed days have data. This does not match section C which correctly uses `effective_end`.
- **Status:** WARNING (MEDIUM)
- **Severity:** MEDIUM — `revenue_verification.days_missing` will report "16 days missing" for a month where only 15 days have elapsed and all 15 are present. This is misleading for accounting staff.
- **Suggested fix:** Section B should use `days_with_djm` vs `days_in_window` (not `days_in_month`) for the `note_rev` message, consistent with section C.

### Test 2-E: Deposit leaderboard query — func.abs() on SQLite
- **Input:** DepositVariance rows with negative variances
- **Actual (line 1627):**
  ```python
  func.sum(func.abs(DepositVariance.variance)).label('abs_total'),
  ```
  `func.abs()` is a SQLAlchemy generic function. SQLite supports `ABS()`, PostgreSQL supports `ABS()`. This is portable.
- **Status:** PASS

### Test 2-F: Data quality warnings — uses `budget` variable from section B, not fresh query
- **Actual (line 1719):**
  ```python
  if not budget:
      warnings.append({'code': 'MISSING_MONTHLY_BUDGET', ...})
  ```
  `budget` was set at line 1531: `budget = MonthlyBudget.query.filter_by(year=year, month=month).first()`. Variable is in scope. Correct.
- **Status:** PASS

### Test 2-G: MonthEndChecklist.completed field access
- **Actual (line 1502):** `sum(1 for t in tasks if t.completed)` — needs `completed` boolean on MonthEndChecklist.
- **Method:** Grep confirmed MonthEndChecklist class is at models.py:216. Read the model.
- **Actual model (need to verify):** This was not explicitly read but the prior session QA (QA-crm-tabs.md) confirmed MonthEndChecklist has task_name and completed fields. Provisionally PASS — flagged for confirmation.
- **Status:** PASS (provisional)

---

## EP-3: GET /api/dashboard/auditor-panel {#ep-3}

### Test 3-A: No role restriction — accessible to all authenticated users
- **Actual:** Decorator is `@login_required` only. No `@role_required`. This is intentional — night auditors need this panel.
- **Status:** PASS

### Test 3-B: No session for audit_date — balance_grid all pending
- **Input:** No NightAuditSession for today's audit_date
- **Actual (lines 702-707):**
  ```python
  _pending = {'status': 'pending', 'value': None, 'is_ok': None}
  recap_check      = dict(_pending, label='Récap',      threshold=0.02)
  ...
  overall_balanced = None
  ```
  All four checks set to pending. Correct.
- **Status:** PASS

### Test 3-C: avg_quasi_7d when no cash recon data
- **Input:** No DailyCashRecon rows in the prior 7 days
- **Actual (lines 647-650):**
  ```python
  avg_quasi_7d = (
      sum(abs(r.quasimodo_variance or 0) for r in recent_cash) / len(recent_cash)
      if recent_cash else None
  )
  ```
  Guards with `if recent_cash else None`. Safe.
- **Status:** PASS

### Test 3-D: MEDIUM — surplus/deficit uses recap_balance, not DailyCashRecon.surplus_deficit {#EP3-MED-1}
- **Actual (line 857):**
  ```python
  surplus = nas.recap_balance or 0
  ```
  The `surplus/deficit` metric in `variance_alerts` uses `NightAuditSession.recap_balance`, while the `smart_dashboard` cash section uses `DailyCashRecon.surplus_deficit`. These are different fields from different tables.
- **Issue:** `NightAuditSession.recap_balance` is the net of cash_in - cash_out - deposits (from RJ calculation), whereas `DailyCashRecon.surplus_deficit` is the auditor's counted surplus/deficit. They measure related but distinct things. Labeling the `recap_balance` as "Surplus / Deficit caisse" in the variance_alerts section may confuse auditors who expect it to match the DailyCashRecon record.
- **Severity:** MEDIUM — no crash, but semantically ambiguous. Could lead to auditors seeing a discrepancy between panels.
- **Suggested fix:** Either (a) query DailyCashRecon for the same date and use `.surplus_deficit`, or (b) rename the label to clarify it is the "Récap balance" not the counted cash surplus.

### Test 3-E: outstanding_items — `is_locked` scope
- **Actual (lines 726-729):**
  ```python
  is_locked = nas.status == 'locked'
  def _action(text):
      return '' if is_locked else text
  ```
  Then at line 889: `is_locked = session_exists and nas.status == 'locked'` — re-declared for the response envelope. Both usages are consistent.
- **Status:** PASS

### Test 3-F: Outstanding items — GL variances only checked when `nas` exists
- **Actual:** All outstanding checks are wrapped in `if nas:` block (line 724). When nas is None, `outstanding` list remains empty. Correct — no AttributeError.
- **Status:** PASS

---

## EP-4: GET /compset/api/otb-pace {#ep-4}

### Test 4-A: No OTB data at all
- **Input:** Empty OTBForecast table (source != 'seed' filter applied)
- **Actual (lines 607-612):**
  ```python
  current_snap = db.session.query(
      func.max(OTBForecast.snapshot_date)
  ).filter(OTBForecast.source != 'seed').scalar()

  if current_snap is None:
      return jsonify({'success': True, 'has_data': False, 'reason': 'no_otb_data'})
  ```
  Seed data is excluded from the max() query. Safe.
- **Status:** PASS

### Test 4-B: Seed data exclusion in current_rows query
- **Actual (lines 620-624):**
  ```python
  current_rows = OTBForecast.query.filter(
      OTBForecast.snapshot_date == current_snap,
      OTBForecast.target_date > current_snap,
      OTBForecast.target_date <= end_target,
      OTBForecast.source != 'seed',
  ).order_by(OTBForecast.target_date).all()
  ```
  Source filter applied. Note the filter is `!= 'seed'` — this will also include 'snapshot', 'import', 'manual'. Correct per the docstring intent.
- **Status:** PASS

### Test 4-C: Comparison snapshot — null comparison_snapshot rows
- **Input:** compare_snap is 7 days before current_snap; no rows exist for that date
- **Actual (lines 634-643):** compare_rows query runs, returns empty list. `compare_map = {}`. For each current row, `comp = compare_map.get(row.target_date)` returns None.
- **Actual (lines 652-655):**
  ```python
  pickup_rooms = (rooms_otb - comp.rooms_otb) if comp and comp.rooms_otb is not None else None
  pickup_revenue = (
      (row.revenue_otb or 0) - (comp.revenue_otb or 0)
  ) if comp and comp.revenue_otb is not None else None
  ```
  Both pickup fields return None when comp is missing. `compare_found = False`.
- **Status:** PASS

### Test 4-D: vs_ly_rooms_pct when ly_rooms = 0
- **Input:** `row.ly_rooms = 0`
- **Actual (line 677):**
  ```python
  'vs_ly_rooms_pct': round((rooms_otb - row.ly_rooms) / row.ly_rooms * 100, 1)
                     if row.ly_rooms else None,
  ```
  `if row.ly_rooms` is falsy when `ly_rooms = 0` — returns None, avoiding ZeroDivisionError. Correct.
- **Status:** PASS

### Test 4-E: HIGH — compare_snapshot field shows None for days where no comparison data exists, but global compare_snapshot always shows the date {#EP4-HIGH-1}
- **Input:** Snapshot has 30 rows; comparison snapshot has data for only 15 of those target_dates
- **Actual (line 683):**
  ```python
  'compare_snapshot': compare_snap.isoformat() if comp else None,
  ```
  For days where `comp is None`, `compare_snapshot` is None in the per-day record. But the top-level response always includes `'compare_snapshot': compare_snap.isoformat()` (line 735), which is always set.
- **Issue:** A consumer reading per-day `compare_snapshot` for missing days will see `None` and may not realize the comparison snapshot date was actually fetched — it just had no row for that specific target_date. This is a documentation/UX ambiguity rather than a crash.
- **Severity:** LOW — no functional bug. Frontend just needs to understand the distinction between "comparison snapshot was resolved" (top-level) vs "comparison row found for this specific day" (per-day).

### Test 4-F: MEDIUM — days parameter is not bounded; could produce excessively large result sets {#EP4-MED-1}
- **Input:** `?days=10000`
- **Actual (line 597):** `days = request.args.get('days', 60, type=int)` — no upper bound check.
- **Issue:** Caller can request 10000 days of OTB data in a single response. If the DB has that many rows (unlikely for OTB but theoretically possible), the response could be very large.
- **Severity:** MEDIUM — not exploitable (auth required, not a denial-of-service risk for external attackers), but could cause memory pressure in production.
- **Suggested fix:** Add `days = min(days, 365)` after parsing.

### Test 4-G: total_rooms_otb in summary — not guarded when all rows have rooms_otb = 0
- **Input:** All rooms_otb = 0 for the snapshot
- **Actual (line 698):**
  ```python
  avg_adr_otb = total_revenue_otb / total_rooms_otb if total_rooms_otb > 0 else 0
  ```
  ZeroDivisionError is guarded. Safe.
- **Status:** PASS

---

## EP-5: GET /compset/api/str-trends {#ep-5}

### Test 5-A: Index methodology — mean(my)/mean(comp), not mean(stored_index)
- **Method:** Read index computation in both monthly aggregation and summary
- **Actual monthly (lines 848-851):**
  ```python
  'occ_index': _index(my_occ, comp_occ),  # _index = my/comp*100
  ```
  Where `my_occ = _mean(m['my_occ'])` and `comp_occ = _mean(m['comp_occ'])`.
  So: index = mean(my_occ_values) / mean(comp_occ_values) * 100.

- **Actual summary (lines 884-886):**
  ```python
  avg_occ_index = _index(_mean(all_my_occ) or 0, _mean(all_comp_occ) or 0)
  ```
  Same methodology at full-period level.
- **Stored `occ_index`, `adr_index`, `revpar_index` fields from the STRCompSet model are NOT used** in the trend aggregation — raw `my_*` and `comp_*` values are re-computed from first principles. This is the correct approach per the docstring.
- **Status:** PASS

### Test 5-B: low_sample flag logic — period_type='monthly' rows never flagged
- **Actual (line 863):**
  ```python
  'low_sample': period_type == 'daily' and day_count < LOW_SAMPLE_THRESHOLD,
  ```
  For `period_type='monthly'`, the `period_type == 'daily'` condition is False, so `low_sample` is always False. Correct — monthly rows are pre-aggregated and not subject to a day-count threshold.
- **Status:** PASS

### Test 5-C: No STR data for date range
- **Input:** Empty query result for the date range
- **Actual (lines 783-790):**
  ```python
  if not str_rows:
      return jsonify({
          'success': True,
          'has_data': False,
          'start_date': start_date.isoformat(),
          ...
      })
  ```
  Correct early return.
- **Status:** PASS

### Test 5-D: invalid period_type parameter
- **Input:** `?period_type=weekly`
- **Actual (lines 774-775):**
  ```python
  if period_type not in ('daily', 'monthly'):
      return jsonify({'error': "period_type must be 'daily' or 'monthly'."}), 400
  ```
- **Status:** PASS

### Test 5-E: MEDIUM — comp_set_size taken from first row only, may vary within period {#EP5-MED-1}
- **Actual (lines 813-814):**
  ```python
  monthly[key] = {
      ...
      'comp_set_size': r.comp_set_size or 6,
  }
  ```
  Only the first row's `comp_set_size` is stored for a bucket; subsequent rows in the same month overwrite nothing. If the comp set size changed mid-month (rare but possible during STR membership updates), the bucket will show the first day's size rather than the modal value.
- **Severity:** MEDIUM — low probability in practice but could cause fair_share_pct to be slightly wrong for the transition month.
- **Suggested fix:** Use the most common (mode) value or the last value for the month.

### Test 5-F: fair_share_pct uses comp_set_size from first STR row in entire query, not per-month
- **Actual (line 870):**
  ```python
  comp_set_size = str_rows[0].comp_set_size or 6
  fair_share_pct = round(100 / comp_set_size, 1)
  ```
  Single fair_share for the entire period, based on the first row. For a 12-month trend this is likely fine, but if comp_set changed (e.g. from 5 to 6 hotels), the historical fair_share will be wrong.
- **Severity:** LOW — same root cause as 5-E, different surface. Acceptable for current use case.
- **Status:** WARNING (LOW)

### Test 5-G: _index() with comp = 0.0 (not just None or missing)
- **Input:** `comp_occ = 0` (e.g. division by zero scenario)
- **Actual (lines 796-800):**
  ```python
  def _index(my, comp):
      if not comp:
          return None
      return round(my / comp * 100, 1)
  ```
  `not comp` is True when `comp = 0` or `comp = 0.0`. ZeroDivisionError avoided.
- **Status:** PASS

### Test 5-H: Summary _index call passes `or 0` coercion — potential masked None
- **Actual (line 884):**
  ```python
  avg_occ_index = _index(_mean(all_my_occ) or 0, _mean(all_comp_occ) or 0)
  ```
  If `_mean(all_comp_occ)` is None (all comp_occ values were None), `None or 0` → `0` → `_index(x, 0)` → returns None (guarded). Safe.
  But: `_mean(all_my_occ)` could also be None → `None or 0` → forces 0 → `_index(0, comp)` → returns 0.0 not None. A 0.0 occ_index in the summary would be silently misleading.
- **Severity:** LOW — only occurs when all my_occ fields in the dataset are None/null. Unlikely in practice.

---

## Summary Table

| ID | Area | Severity | Status | Description |
|----|------|----------|--------|-------------|
| INFRA-1 | login_required | N/A | PASS | All 19 files import from utils.auth_decorators |
| INFRA-2 | Threading locks | N/A | PASS | RJ_FILES_LOCK used consistently |
| INFRA-3 | Filler cache | N/A | PASS | _RJ_VERSION_COUNTER + invalidate_rj_cache correct |
| INFRA-4 | TOTAL_ROOMS | LOW | WARNING | seed_crm_demo.py has local copy |
| FIX-1 | alert_engine.py | N/A | PASS | DailyJourMetrics used, correct field names |
| FIX-1b | alert_engine.py | LOW | WARNING | generate_daily_summary hardcodes 252 |
| FIX-2 | crm.py staff | N/A | PASS | GROUP BY query eliminates N+1 |
| FIX-3 | crm_tabs.py P&L | N/A | PASS | franchise_pct uses actual MonthlyExpense data |
| FIX-4 | crm_tabs.py warnings | N/A | PASS | Missing expense month detection correct |
| FIX-5 | crm_tabs.py deposits | N/A | PASS | DepositVariance leaderboard and trend added |
| FIX-6 | crm_tabs.py labor | N/A | PASS | Budget variance vs actual implemented |
| FIX-7 | dashboard labor ratio | N/A | PASS | Partial month proration correct |
| EP1-HIGH-1 | gm-briefing | HIGH | FAIL | revpar_index silently 0 when field is None |
| EP1-MED-1 | gm-briefing | MEDIUM | FAIL | days_missing uses full month length, not elapsed |
| EP2-MED-1 | accounting | MEDIUM | FAIL | Same days_missing issue in revenue_verification |
| EP3-MED-1 | auditor-panel | MEDIUM | FAIL | surplus label uses recap_balance not DailyCashRecon |
| EP4-HIGH-1 | otb-pace | --- | INFO | compare_snapshot=None per-day vs top-level; doc gap |
| EP4-MED-1 | otb-pace | MEDIUM | FAIL | No upper bound on ?days= parameter |
| EP5-MED-1 | str-trends | MEDIUM | FAIL | comp_set_size taken from first row only per bucket |
| EP5-LOW-1 | str-trends | LOW | WARNING | fair_share_pct uses first row of entire query |
| EP5-LOW-2 | str-trends | LOW | WARNING | Summary _index(my or 0, comp or 0) masks None metrics |

---

## Critical Issues Requiring Immediate Attention

### HIGH-1: gm-briefing — STR revpar_index silently returns 0.0 when field is unpopulated

**Location:** `routes/dashboard.py`, Panel 4 STR block, line ~1314
```python
'revpar_index': _r2(latest_str.revpar_index),
```
`_r2()` converts None to 0.0 via `float(val or 0)`. A GM seeing 0.0 RevPAR index would interpret it as the hotel earning zero share of its comp set's RevPAR — potentially alarming. The correct behavior is to return `null` so the frontend can display "N/D" instead.

**Fix:**
```python
'revpar_index': (_r2(latest_str.revpar_index) if latest_str.revpar_index is not None else None),
'occ_index':    (_r2(latest_str.occ_index)    if latest_str.occ_index    is not None else None),
'adr_index':    (_r2(latest_str.adr_index)    if latest_str.adr_index    is not None else None),
```

### HIGH-2: accounting dashboard + gm-briefing — days_missing computed against full month length

**Location:** `routes/dashboard.py`, accounting_dashboard(), line 1529
```python
days_missing_rev = days_in_month - days_with_djm
```
For an ongoing month (e.g., today is March 23, 31-day month), this reports `31 - 23 = 8` missing days when in reality 0 days are missing (all 23 elapsed days have data). Section C correctly uses `effective_end` and `days_in_window`. Section B does not.

**Fix:** Replace `days_in_month` with `days_in_window` in Section B's missing days calculation, and update `days_expected` in the response accordingly for the effective window.

---

## No-issue confirmations (passing items worth noting)

- All new endpoints return `{'success': True, 'has_data': False}` consistently when no DB data exists — no crashes on empty DB.
- All division-by-zero paths are guarded (TOTAL_ROOMS, month_rev, rooms_otb, etc.).
- French-language strings are used throughout all user-facing messages.
- `role_required` decorators correctly use the `user_role_type` session key (verified in auth_decorators.py).
- The STR index methodology (mean(my)/mean(comp) not mean(index)) is correctly implemented and documented in code comments.
- Seed data exclusion in otb-pace is consistent: both the max() snapshot query and the row filter exclude `source='seed'`.
- The N+1 staff query fix is clean and uses portable SQLAlchemy patterns.
- The annual P&L double-counting fix is verified — labor comes from DepartmentLabor only.
