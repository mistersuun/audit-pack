# QA Report: routes/crm_tabs.py
## Last Updated: 2026-03-23
## Status: FAIL

---

### Test QA-CRM-001: DailyCashRecon AttributeError — RECHECK of prior finding

- **Prior finding:** "DailyCashRecon missing year/month columns → AttributeError in crm_tabs.py:728"
- **Recheck:** `DailyCashRecon` is defined in `database/models.py` at line 1045. It **does** have `year = db.Column(db.Integer, nullable=False)` at line 1050 and `month = db.Column(db.Integer, nullable=False)` at line 1051. The prior finding that these columns are missing appears to be **incorrect based on the current code**.
- **However**, `crm_tabs.py:728` accesses `r.year` and `r.month`. If older production databases were created before these columns were added (i.e., migrations were not run), the actual DB columns would be absent and SQLAlchemy would raise `OperationalError` rather than `AttributeError`. In that sense the concern is valid for deployed instances without migration.
- **Recheck Status:** The model is correct in source. The risk is migration-only (data integrity), not a code bug in the current source.
- **Severity:** P2 — HIGH in deployed environments without migration

---

### Test QA-CRM-002: `occ_budget` uses room count instead of occupancy percentage (NEW)

- **File:Line:** crm_tabs.py:198
- **Input:** `GET /api/crm/tabs/revenue-mgmt` when monthly budget data exists
- **Expected Output:** `occ_budget` field contains occupancy percentage (0–100%)
- **Actual Output:**

  ```python
  'occ_budget': _round2(budget.rooms_target if budget else 0),
  ```

  `MonthlyBudget.rooms_target` (models.py:565) is defined as `db.Column(db.Integer, default=0)` with the comment "Target rooms sold" — an integer count like `180`. The frontend presumably renders this as an occupancy percentage on a scatter plot labeled "Occupancy vs ADR". Displaying `180` as a percentage value on a 0–100 axis breaks the chart.

  The correct value would be `(budget.rooms_target / TOTAL_ROOMS * 100)` where `TOTAL_ROOMS = 252`.

- **Status:** FAIL
- **Severity:** P2 — HIGH (incorrect chart data, misleads management decisions)
- **Steps to reproduce:**
  1. Ensure a `MonthlyBudget` record exists with `rooms_target=180`
  2. Call `GET /api/crm/tabs/revenue-mgmt`
  3. Inspect response: `occ_budget` will be `180` instead of `71.4`
- **This is NEW** — not reported in prior reviews.

---

### Test QA-CRM-003: Tip trend key splitting fails for departments containing hyphens (NEW)

- **File:Line:** crm_tabs.py:316–320
- **Input:** `GET /api/crm/tabs/fb-intel` when `DailyTipMetrics` records exist for a department named `ROOM-SERVICE` or any hyphenated name
- **Expected Output:** Tips correctly grouped by period and department
- **Actual Output:**

  ```python
  # Line 308:
  key = f"{t.year}-{t.month:02d}-{t.department}"
  # Example key: "2026-02-ROOM-SERVICE"

  # Line 316-320:
  parts = key.split('-')
  period = f"{parts[0]}-{parts[1]}"   # "2026-02"  ← correct
  dept = parts[2]                      # "ROOM" ← WRONG, should be "ROOM-SERVICE"
  ```

  If a department name contains a hyphen, `parts[2]` captures only the first fragment. The actual `DailyTipMetrics` departments listed in the model are `CHAMBRE, PIAZZA, BANQUET, BAR, ROOM_SERVICE` — using underscores, not hyphens. So this is safe **for the currently defined departments**. But it is a fragile design that will break silently if any department name ever contains a hyphen (which is a common convention).

- **Status:** WARNING
- **Severity:** P3 — MEDIUM (works now, fragile for future data)
- **Recommended fix:** Use `rsplit('-', 2)` or better: store year, month, and department as separate dict keys rather than encoding them in a composite string key.
- **This is NEW** — not reported in prior reviews.

---

### Test QA-CRM-004: `cash_reconciliation` tab queries DailyCashRecon by date but uses `.year`/`.month` attributes that are stored as DB columns — requires recent migrations (NEW + Clarification)

- **File:Line:** crm_tabs.py:603–604, 728–733
- **Input:** `GET /api/crm/tabs/cash-recon`
- **Expected Output:** Deposit trend grouped by month
- **Actual Output (code path):**

  ```python
  # Line 603–604:
  recon = DailyCashRecon.query.filter(
      DailyCashRecon.date.between(start, end)
  ).order_by(DailyCashRecon.date).all()

  # Line 728:
  key = f"{r.year}-{r.month:02d}"
  ```

  As confirmed in QA-CRM-001, `.year` and `.month` exist on the model. However, `DailyCashRecon.date` is a `db.Date` column. If the DB has rows seeded by old demo code that set only `date` but not `year`/`month` (e.g., pre-migration `seed_crm_demo.py`), then `r.year` returns `None` and `f"{None}-{None:02d}"` raises `TypeError: unsupported format character` in the f-string.

  This is a real runtime crash path for any deployment where demo data was seeded before the `year`/`month` columns were added.

- **Status:** FAIL (for pre-migration deployments)
- **Severity:** P2 — HIGH
- **Suggested fix:** Add null guard: `key = f"{r.year or r.date.year}-{(r.month or r.date.month):02d}"`
- **This is NEW** — the prior review reported AttributeError on the model; the actual error is TypeError in the f-string on None values.

---

### Test QA-CRM-005: Annual P&L double-counts labor (NEW)

- **File:Line:** crm_tabs.py:1124–1143
- **Input:** `GET /api/crm/tabs/pnl-budget` when both `MonthlyExpense` and `DepartmentLabor` records exist for the same period
- **Expected Output:** Labor cost counted once in the P&L
- **Actual Output:**

  ```python
  # Line 1131–1137: labor added from MonthlyExpense.labor_total
  for exp in expenses:
      annual_pnl[year]['labor'] += exp.labor_total or 0

  # Line 1139–1143: labor ALSO added from DepartmentLabor.total_labor_cost
  for dl in dept_labor:
      annual_pnl[year]['labor'] += dl.total_labor_cost or 0
  ```

  Both `MonthlyExpense.labor_total` and `DepartmentLabor.total_labor_cost` represent labor costs. If both data sources are populated, labor is double-counted in the annual P&L summary `labor_pct` calculation. A hotel running at 35% labor ratio would show as 70%.

- **Status:** FAIL
- **Severity:** P2 — HIGH (incorrect P&L data, misleads GOPPAR and margin analysis)
- **This is NEW** — not reported in prior reviews.
