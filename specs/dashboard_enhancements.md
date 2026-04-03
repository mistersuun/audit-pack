# Dashboard Enhancement Specifications
## Sheraton Laval Night Audit System — Implementation-Ready Specs
**Author:** Data Architect
**Date:** 2026-03-23
**Codebase:** Flask + SQLAlchemy + SQLite, 252 rooms (TOTAL_ROOMS constant)

---

## Preliminary Notes on Existing Models Used

The following models are referenced throughout. Field names are taken verbatim from `database/models.py`.

| Model | Table | Granularity | Key Fields |
|---|---|---|---|
| `DailyJourMetrics` | `daily_jour_metrics` | 1 row per calendar date | `date`, `year`, `month`, `occupancy_rate`, `adr`, `revpar`, `room_revenue`, `fb_revenue`, `total_revenue`, `rooms_comp`, `rooms_hors_usage`, `total_rooms_sold`, `rooms_available` |
| `NightAuditSession` | `night_audit_sessions` | 1 row per audit date | `audit_date`, `auditor_name`, `status`, `completed_at`, `is_recap_balanced`, `is_transelect_balanced`, `is_ar_balanced`, `is_fully_balanced`, `quasi_variance`, `recap_balance`, `jour_rooms_hors_usage`, `gl_101100_*`, `gl_100401_*` |
| `DailyCashRecon` | `daily_cash_recon` | 1 row per date | `date`, `quasimodo_variance`, `surplus_deficit`, `deposit_cdn`, `deposit_usd`, `auditor_name` |
| `MonthlyBudget` | `monthly_budget` | 1 row per year+month | `year`, `month`, `rooms_target`, `adr_target`, `room_revenue`, `total_revenue` |
| `DepartmentLabor` | `department_labor` | 1 row per year+month+department | `year`, `month`, `department`, `total_labor_cost`, `total_hours`, `budget_cost`, `budget_hours`, `regular_hours`, `overtime_hours` |
| `MonthlyExpense` | `monthly_expenses` | 1 row per year+month | `year`, `month`, `total_expenses`, `labor_total`, `utilities`, `franchise_fees` |
| `OTBForecast` | `otb_forecast` | 1 row per snapshot_date+target_date | `snapshot_date`, `target_date`, `rooms_otb`, `occ_otb`, `adr_otb`, `revenue_otb`, `group_rooms`, `transient_rooms`, `ly_rooms`, `ly_occ`, `ly_adr`, `ly_revenue` |
| `STRCompSet` | `str_comp_set` | 1 row per report_date+period_type | `report_date`, `period_type`, `my_occ`, `my_adr`, `my_revpar`, `comp_occ`, `comp_adr`, `comp_revpar`, `occ_index`, `adr_index`, `revpar_index`, `occ_rank`, `adr_rank`, `revpar_rank`, `comp_set_size` |
| `MonthEndChecklist` | `month_end_checklists` | 1 row per year+month+task_name | `year`, `month`, `task_name`, `completed`, `completed_at`, `completed_by` |
| `DepositVariance` | `deposit_variances` | 1 row per audit_date+employee_name | `audit_date`, `employee_name`, `department`, `amount_declared`, `amount_verified`, `variance` |
| `DailyCardMetrics` | `daily_card_metrics` | 1 row per date+card_type | `date`, `card_type`, `pos_total`, `discount_amount`, `discount_rate`, `net_amount`, `transaction_count` |
| `DailyReconciliation` | `daily_reconciliations` | 1 row per audit_date | `audit_date`, `auditor_name`, `surplus_deficit`, `card_total_variance`, `ar_variance`, `is_balanced`, `deposit_cdn`, `deposit_us` |

---

## Part 1: GM Morning Briefing Dashboard

### Endpoint Definition

```
GET /api/dashboard/gm-briefing
```

**Blueprint:** `dashboard_bp` in `routes/dashboard.py`
**Auth:** `@login_required` — additionally enforce `role_required('gm', 'gsm', 'admin')` (import from `utils/auth_decorators.py`)
**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `date` | `YYYY-MM-DD` | Yesterday (most recent audit date) | The night being briefed on |

---

### Panel 1: Last Night Performance

**Business purpose:** Give the GM five headline KPIs for last night with three layers of context — budget variance, LY same date, and 7-day rolling average.

#### SQLAlchemy Queries

```python
from datetime import date, timedelta
from database.models import (
    db, DailyJourMetrics, MonthlyBudget, NightAuditSession, TOTAL_ROOMS
)
from sqlalchemy import func, desc

# --- Resolve briefing date ---
# Use ?date= param if provided, else fall back to most recent DJM row
target_date = _parse_date(request.args.get('date'))
if not target_date:
    latest = DailyJourMetrics.query.order_by(
        desc(DailyJourMetrics.date)
    ).first()
    if not latest:
        return jsonify({'success': True, 'has_data': False})
    target_date = latest.date

# --- Last night actuals ---
night = DailyJourMetrics.query.filter_by(date=target_date).first()
# Fallback: if no DJM row for target_date, has_data = False

# --- Budget for same month (prorated to single day) ---
import calendar
budget = MonthlyBudget.query.filter_by(
    year=target_date.year, month=target_date.month
).first()
days_in_month = calendar.monthrange(target_date.year, target_date.month)[1]
# Daily budget = monthly target / days in month
budget_occ_daily  = (budget.rooms_target / TOTAL_ROOMS / days_in_month * 100) if budget else None
budget_adr_daily  = budget.adr_target if budget else None
budget_room_rev_d = (budget.room_revenue / days_in_month) if budget else None
budget_total_rev_d= (budget.total_revenue / days_in_month) if budget else None

# --- LY same calendar date (365 days back) ---
ly_date = target_date.replace(year=target_date.year - 1)
ly_night = DailyJourMetrics.query.filter_by(date=ly_date).first()
# Fallback: try target_date - 364 days (same DOW) if exact LY date is missing
if not ly_night:
    ly_night = DailyJourMetrics.query.filter_by(
        date=target_date - timedelta(days=364)
    ).first()

# --- 7-day average (days -8 through -2 relative to target_date, excluding target itself) ---
week_start = target_date - timedelta(days=8)
week_end   = target_date - timedelta(days=1)
avg7 = db.session.query(
    func.avg(DailyJourMetrics.occupancy_rate),
    func.avg(DailyJourMetrics.adr),
    func.avg(DailyJourMetrics.revpar),
    func.avg(DailyJourMetrics.room_revenue),
    func.avg(DailyJourMetrics.fb_revenue),
    func.avg(DailyJourMetrics.total_revenue),
).filter(
    DailyJourMetrics.date.between(week_start, week_end)
).first()
```

**Computed KPIs:**

```python
# OOS-adjusted occupancy: numerator = rooms_comp + rooms_simple + rooms_double + rooms_suite
# denominator = TOTAL_ROOMS - rooms_hors_usage
rooms_sold     = night.total_rooms_sold  # pre-computed, includes comp
oos_rooms      = night.rooms_hors_usage or 0
avail_adjusted = TOTAL_ROOMS - oos_rooms
occ_adjusted   = (rooms_sold / avail_adjusted * 100) if avail_adjusted > 0 else night.occupancy_rate

# Effective ADR (excluding comp rooms from both numerator and denominator)
rooms_paid     = rooms_sold - (night.rooms_comp or 0)
effective_adr  = (night.room_revenue / rooms_paid) if rooms_paid > 0 else night.adr

# Comp room percentage
comp_pct       = (night.rooms_comp / rooms_sold * 100) if rooms_sold > 0 else 0

# F&B revenue (from DJM — fb_revenue field)
fb_rev         = night.fb_revenue or 0

# Total revenue
total_rev      = night.total_revenue or 0

# Helper: build variance dict
def _variance(actual, reference):
    if reference is None or reference == 0:
        return {'value': None, 'pct': None, 'direction': 'unknown'}
    diff = actual - reference
    pct  = round(diff / abs(reference) * 100, 2)
    return {
        'value': round(diff, 2),
        'pct': pct,
        'direction': 'above' if diff >= 0 else 'below'
    }
```

#### JSON Response Schema — Panel 1

```json
{
  "last_night": {
    "date": "2026-03-22",
    "kpis": {
      "occupancy_pct":    78.2,
      "occupancy_adjusted_pct": 79.8,
      "adr":              187.45,
      "effective_adr":    193.10,
      "revpar":           146.55,
      "room_revenue":     36914.40,
      "fb_revenue":       12340.00,
      "total_revenue":    54210.00,
      "rooms_sold":       197,
      "rooms_comp":       4,
      "comp_pct":         2.03,
      "oos_rooms":        5
    },
    "vs_budget": {
      "occupancy":  { "value": 3.2,    "pct": 4.3,   "direction": "above" },
      "adr":        { "value": -5.55,  "pct": -2.88, "direction": "below" },
      "revpar":     { "value": 8.55,   "pct": 6.19,  "direction": "above" },
      "room_revenue": { "value": 1914.40, "pct": 5.46, "direction": "above" },
      "total_revenue": { "value": 4210.00, "pct": 8.42, "direction": "above" }
    },
    "vs_ly": {
      "date_used": "2025-03-22",
      "occupancy":    { "value": 5.1,  "pct": 6.98,  "direction": "above" },
      "adr":          { "value": 12.45,"pct": 7.12,  "direction": "above" },
      "revpar":       { "value": 14.20,"pct": 10.74, "direction": "above" },
      "room_revenue": { "value": 3200.00,"pct": 9.49,"direction": "above" },
      "total_revenue":{ "value": 5100.00,"pct": 10.39,"direction": "above" }
    },
    "vs_7day_avg": {
      "occupancy":    { "value": 2.3,  "pct": 3.03,  "direction": "above" },
      "adr":          { "value": -3.20,"pct": -1.68, "direction": "below" },
      "revpar":       { "value": 1.10, "pct": 0.76,  "direction": "above" },
      "room_revenue": { "value": 800.00,"pct": 2.22, "direction": "above" },
      "total_revenue":{ "value": 1300.00,"pct": 2.46,"direction": "above" }
    },
    "fallback_notes": {
      "budget_available": true,
      "ly_data_available": true,
      "ly_date_used": "2025-03-22",
      "ly_fallback_applied": false
    }
  }
}
```

**Fallback rules:**
- No DJM row for `target_date`: return `{"success": true, "has_data": false, "reason": "no_djm_for_date"}`.
- No `MonthlyBudget` for the month: all `vs_budget` values have `"value": null, "pct": null`.
- No LY exact date: try `target_date - 364` (same DOW). If still missing, `ly_data_available: false` and `vs_ly` keys all null.
- 7-day average with fewer than 3 days of data: return it with a `"low_sample": true` flag.

---

### Panel 2: Operational Status

**Business purpose:** Confirm the RJ was submitted, identify who did it, when, and whether all four balance checks passed. Surface the Quasimodo variance and OOS RevPAR impact.

#### SQLAlchemy Queries

```python
# --- RJ session for target_date ---
rj = NightAuditSession.query.filter_by(audit_date=target_date).first()

# --- Cash recon for same date ---
cash = DailyCashRecon.query.filter_by(date=target_date).first()

# --- OOS RevPAR impact ---
# Revenue lost = OOS rooms × last night's ADR
oos_rooms       = (rj.jour_rooms_hors_usage if rj else 0) or (night.rooms_hors_usage if night else 0)
revpar_impact   = round(oos_rooms * (night.adr if night else 0), 2)

# --- Consecutive balanced nights streak (last 30 days) ---
# A "balanced night" = NightAuditSession.is_fully_balanced = True
recent_sessions = NightAuditSession.query.filter(
    NightAuditSession.audit_date <= target_date,
    NightAuditSession.audit_date >= target_date - timedelta(days=30)
).order_by(desc(NightAuditSession.audit_date)).all()

streak = 0
for s in recent_sessions:
    if s.is_fully_balanced:
        streak += 1
    else:
        break  # first unbalanced night stops the count
```

#### JSON Response Schema — Panel 2

```json
{
  "operational_status": {
    "rj_session": {
      "exists":       true,
      "auditor":      "Jean-François Tremblay",
      "status":       "submitted",
      "submitted_at": "2026-03-23T05:47:32",
      "is_submitted": true
    },
    "balance_grid": {
      "recap":       { "balanced": true,  "value": 0.00,  "threshold": 0.02 },
      "transelect":  { "balanced": true,  "value": -0.50, "threshold": 1.00 },
      "ar":          { "balanced": false, "value": 12.30, "threshold": 0.02 },
      "is_fully_balanced": false
    },
    "quasimodo": {
      "variance":    -4.20,
      "threshold":   5.00,
      "status":      "ok",
      "surplus_deficit": 2.50
    },
    "oos_rooms": {
      "count":           5,
      "revpar_impact":   935.75,
      "note": "Revenue foregone if OOS rooms had been sold at last night's ADR"
    },
    "gl_suspense": {
      "gl_101100_balance": 340.00,
      "gl_101100_variance": 0.00,
      "gl_100401_balance": 0.00,
      "gl_100401_variance": 0.00,
      "notes": ""
    },
    "consecutive_balanced_streak": 12,
    "fallback_notes": {
      "rj_session_found": true,
      "cash_recon_found": true
    }
  }
}
```

**Balance grid logic:**
- `recap.balanced` = `NightAuditSession.is_recap_balanced`
- `transelect.balanced` = `NightAuditSession.is_transelect_balanced`
- `ar.balanced` = `NightAuditSession.is_ar_balanced`
- `is_fully_balanced` = `NightAuditSession.is_fully_balanced`
- If no `NightAuditSession` exists, all balanced fields return `null` and `rj_session.exists = false`.
- GL suspense from `NightAuditSession.gl_101100_new_balance`, `gl_101100_variance`, `gl_100401_new_balance`, `gl_100401_variance`.

---

### Panel 3: Forward Look (Next 7 Days OTB + Next 30 Days Pace)

**Business purpose:** Provide a demand forecast so the GM can act on pricing and staffing before problems arise.

#### SQLAlchemy Queries

```python
from database.models import OTBForecast

today = date.today()

# --- Most recent snapshot available ---
# OTBForecast stores one row per (snapshot_date, target_date).
# We want the latest snapshot that covers the target window.
latest_snap = db.session.query(
    func.max(OTBForecast.snapshot_date)
).scalar()
# Fallback: if no snapshot within 3 days of today, flag stale data

# --- Next 7 days OTB ---
next7_end = today + timedelta(days=7)
next7 = OTBForecast.query.filter(
    OTBForecast.snapshot_date == latest_snap,
    OTBForecast.target_date > today,
    OTBForecast.target_date <= next7_end
).order_by(OTBForecast.target_date).all()

# --- Next 30 days revenue pace ---
next30_end = today + timedelta(days=30)
next30 = OTBForecast.query.filter(
    OTBForecast.snapshot_date == latest_snap,
    OTBForecast.target_date > today,
    OTBForecast.target_date <= next30_end
).order_by(OTBForecast.target_date).all()

# Aggregate totals for next 30 days
next30_rooms_otb   = sum(r.rooms_otb or 0 for r in next30)
next30_revenue_otb = sum(r.revenue_otb or 0 for r in next30)
next30_ly_rooms    = sum(r.ly_rooms or 0 for r in next30 if r.ly_rooms is not None)
next30_ly_revenue  = sum(r.ly_revenue or 0 for r in next30 if r.ly_revenue is not None)
```

#### JSON Response Schema — Panel 3

```json
{
  "forward_look": {
    "snapshot_date":   "2026-03-23",
    "snapshot_age_days": 0,
    "data_is_stale":   false,
    "next_7_days": [
      {
        "target_date":    "2026-03-24",
        "day_of_week":    "Tuesday",
        "rooms_otb":      185,
        "occ_otb_pct":    73.4,
        "adr_otb":        179.50,
        "revenue_otb":    33207.50,
        "group_rooms":    45,
        "transient_rooms": 140,
        "ly_rooms":       172,
        "ly_occ_pct":     68.3,
        "ly_revenue":     29584.00,
        "vs_ly_rooms":    { "value": 13, "pct": 7.56,  "direction": "above" },
        "vs_ly_revenue":  { "value": 3623.50, "pct": 12.25, "direction": "above" }
      }
    ],
    "next_30_days_pace": {
      "total_rooms_otb":   5420,
      "total_revenue_otb": 972800.00,
      "total_ly_rooms":    5010,
      "total_ly_revenue":  881760.00,
      "vs_ly_rooms_pct":   8.18,
      "vs_ly_revenue_pct": 10.33,
      "avg_daily_occ_otb": 71.7,
      "avg_daily_adr_otb": 179.48
    },
    "fallback_notes": {
      "otb_data_available": true,
      "ly_comparison_coverage": "28 of 30 days have LY data"
    }
  }
}
```

**Fallback rules:**
- No OTB data at all: `otb_data_available: false`, `next_7_days: []`, `next_30_days_pace` all nulls.
- `snapshot_age_days > 3`: set `data_is_stale: true` and include a warning in the response.
- `ly_rooms` is nullable per OTBForecast model — count days with non-null LY data and report coverage %.

---

### Panel 4: Trend Context

**Business purpose:** Give the GM the three strategic ratios they need for a quick read on competitive position and cost discipline.

#### SQLAlchemy Queries

```python
from database.models import STRCompSet

# --- Latest STR RevPAR index (most recent daily record) ---
latest_str = STRCompSet.query.filter_by(
    period_type='daily'
).order_by(desc(STRCompSet.report_date)).first()

# --- Labor % of revenue — last 3 full months ---
three_months_ago = (target_date.replace(day=1) - timedelta(days=1)).replace(day=1)  # 3 months back
labor_months = DepartmentLabor.query.filter(
    db.or_(
        DepartmentLabor.year > three_months_ago.year,
        db.and_(
            DepartmentLabor.year == three_months_ago.year,
            DepartmentLabor.month >= three_months_ago.month
        )
    ),
    db.or_(
        DepartmentLabor.year < target_date.year,
        db.and_(
            DepartmentLabor.year == target_date.year,
            DepartmentLabor.month < target_date.month
        )
    )
).all()

# Group by period and sum
from collections import defaultdict
labor_by_period = defaultdict(float)
for dl in labor_months:
    labor_by_period[f"{dl.year}-{dl.month:02d}"] += dl.total_labor_cost or 0

# Revenue for those same months
rev_rows = db.session.query(
    DailyJourMetrics.year,
    DailyJourMetrics.month,
    func.sum(DailyJourMetrics.total_revenue).label('total_rev')
).filter(
    db.or_(
        DailyJourMetrics.year > three_months_ago.year,
        db.and_(
            DailyJourMetrics.year == three_months_ago.year,
            DailyJourMetrics.month >= three_months_ago.month
        )
    ),
    db.or_(
        DailyJourMetrics.year < target_date.year,
        db.and_(
            DailyJourMetrics.year == target_date.year,
            DailyJourMetrics.month < target_date.month
        )
    )
).group_by(DailyJourMetrics.year, DailyJourMetrics.month).all()

# --- Top active alert (from existing threshold engine in dashboard.py) ---
# Re-use evaluate_thresholds() — call it with the night's data
# Return only the first alert (highest severity after sort)
```

#### JSON Response Schema — Panel 4

```json
{
  "trend_context": {
    "str_index": {
      "report_date":   "2026-03-22",
      "my_revpar":     146.55,
      "comp_revpar":   138.20,
      "revpar_index":  106.0,
      "revpar_rank":   2,
      "comp_set_size": 6,
      "my_occ":        78.2,
      "comp_occ":      74.1,
      "occ_index":     105.5,
      "my_adr":        187.45,
      "comp_adr":      186.52,
      "adr_index":     100.5,
      "data_available": true
    },
    "labor_pct_trend": [
      {
        "period":      "2025-12",
        "labor_cost":  412000.00,
        "revenue":     1480000.00,
        "labor_pct":   27.84,
        "status":      "ok"
      },
      {
        "period":      "2026-01",
        "labor_cost":  398000.00,
        "revenue":     1320000.00,
        "labor_pct":   30.15,
        "status":      "warning"
      },
      {
        "period":      "2026-02",
        "labor_cost":  425000.00,
        "revenue":     1390000.00,
        "labor_pct":   30.58,
        "status":      "warning"
      }
    ],
    "top_alert": {
      "severity":  "warning",
      "category":  "labor",
      "message":   "Ratio main-d'oeuvre à 30.6% — au-dessus de la cible de 30%",
      "action":    "Surveiller les heures supplémentaires, ajuster les horaires pour les prochains jours",
      "metric":    "labor_pct",
      "value":     30.58
    }
  }
}
```

**Status thresholds for labor_pct:**
- `ok`: < 30%
- `warning`: 30–38%
- `critical`: > 38%

**Fallback rules:**
- No STR data: `str_index.data_available = false`, all STR fields null.
- No DepartmentLabor for the period: `labor_pct_trend: []`.
- No alerts triggered: `top_alert: null`.

---

### Complete GM Briefing JSON Envelope

```json
{
  "success":   true,
  "has_data":  true,
  "generated_at": "2026-03-23T07:02:15",
  "briefing_date": "2026-03-22",
  "last_night":        { ... },
  "operational_status": { ... },
  "forward_look":       { ... },
  "trend_context":      { ... }
}
```

**Route registration in `routes/dashboard.py`:**

```python
@dashboard_bp.route('/api/dashboard/gm-briefing')
@login_required
def gm_briefing():
    ...
```

---

## Part 2: OTB Pace Analysis

### Endpoint Definition

```
GET /api/compset/otb-pace
```

**Blueprint:** `compset_bp` in `routes/compset.py`
**Auth:** `@login_required`
**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `snapshot_date` | `YYYY-MM-DD` | Most recent snapshot date in DB | Base snapshot for current OTB |
| `days` | Integer | `60` | Number of days forward to cover |
| `compare_snapshot` | `YYYY-MM-DD` | `snapshot_date - 7 days` | Earlier snapshot for pick-up calculation |

---

### Query Logic

```python
from database.models import db, OTBForecast, TOTAL_ROOMS
from sqlalchemy import func, desc
from datetime import date, timedelta

# --- Resolve snapshot dates ---
snap_str = request.args.get('snapshot_date')
days     = request.args.get('days', 60, type=int)
comp_str = request.args.get('compare_snapshot')

# Current snapshot: use param or latest available
if snap_str:
    current_snap = _parse_date(snap_str)
else:
    current_snap = db.session.query(
        func.max(OTBForecast.snapshot_date)
    ).scalar()
    if not current_snap:
        return jsonify({'success': True, 'has_data': False, 'reason': 'no_otb_data'})

# Comparison snapshot for pick-up (7 days earlier by default)
if comp_str:
    compare_snap = _parse_date(comp_str)
else:
    compare_snap = current_snap - timedelta(days=7)

# --- Fetch current snapshot data ---
end_target = current_snap + timedelta(days=days)
current_rows = OTBForecast.query.filter(
    OTBForecast.snapshot_date == current_snap,
    OTBForecast.target_date > current_snap,
    OTBForecast.target_date <= end_target
).order_by(OTBForecast.target_date).all()

# --- Fetch comparison snapshot data for same target dates ---
compare_rows = OTBForecast.query.filter(
    OTBForecast.snapshot_date == compare_snap,
    OTBForecast.target_date > current_snap,
    OTBForecast.target_date <= end_target
).order_by(OTBForecast.target_date).all()

# Index comparison rows by target_date for O(1) lookup
compare_map = {r.target_date: r for r in compare_rows}

# --- Build per-day records ---
days_data = []
for row in current_rows:
    comp = compare_map.get(row.target_date)
    pickup_rooms   = (row.rooms_otb - comp.rooms_otb) if comp else None
    pickup_revenue = (row.revenue_otb - comp.revenue_otb) if comp else None

    days_data.append({
        'target_date':       row.target_date.isoformat(),
        'day_of_week':       row.target_date.strftime('%A'),
        'days_out':          (row.target_date - current_snap).days,
        # Current OTB
        'rooms_otb':         row.rooms_otb,
        'occ_otb_pct':       round(row.rooms_otb / TOTAL_ROOMS * 100, 1),
        'adr_otb':           round(row.adr_otb or 0, 2),
        'revenue_otb':       round(row.revenue_otb or 0, 2),
        # Segment split
        'group_rooms':       row.group_rooms or 0,
        'transient_rooms':   row.transient_rooms or 0,
        'group_pct':         round((row.group_rooms or 0) / row.rooms_otb * 100, 1) if row.rooms_otb else 0,
        # LY comparison (stored on current row)
        'ly_rooms':          row.ly_rooms,
        'ly_occ_pct':        round((row.ly_rooms / TOTAL_ROOMS * 100), 1) if row.ly_rooms else None,
        'ly_adr':            round(row.ly_adr or 0, 2) if row.ly_adr else None,
        'ly_revenue':        round(row.ly_revenue or 0, 2) if row.ly_revenue else None,
        'vs_ly_rooms':       (row.rooms_otb - row.ly_rooms) if row.ly_rooms is not None else None,
        'vs_ly_rooms_pct':   round((row.rooms_otb - row.ly_rooms) / row.ly_rooms * 100, 1)
                             if row.ly_rooms else None,
        'vs_ly_revenue_pct': round((row.revenue_otb - row.ly_revenue) / row.ly_revenue * 100, 1)
                             if row.ly_revenue else None,
        # Pick-up (change in OTB over last 7 days)
        'pickup_rooms':      pickup_rooms,
        'pickup_revenue':    round(pickup_revenue, 2) if pickup_revenue is not None else None,
        'compare_snapshot':  compare_snap.isoformat() if comp else None,
    })

# --- Summary aggregates ---
total_rooms_otb   = sum(r.rooms_otb or 0 for r in current_rows)
total_revenue_otb = sum(r.revenue_otb or 0 for r in current_rows)
total_group       = sum(r.group_rooms or 0 for r in current_rows)
total_transient   = sum(r.transient_rooms or 0 for r in current_rows)
total_ly_rooms    = sum(r.ly_rooms or 0 for r in current_rows if r.ly_rooms)
total_ly_revenue  = sum(r.ly_revenue or 0 for r in current_rows if r.ly_revenue)
avg_adr_otb       = total_revenue_otb / total_rooms_otb if total_rooms_otb > 0 else 0
```

#### JSON Response Schema

```json
{
  "success":         true,
  "has_data":        true,
  "snapshot_date":   "2026-03-23",
  "compare_snapshot":"2026-03-16",
  "days_requested":  60,
  "days_returned":   60,
  "summary": {
    "total_rooms_otb":    5420,
    "total_revenue_otb":  972800.00,
    "avg_occ_otb_pct":    71.7,
    "avg_adr_otb":        179.48,
    "total_group_rooms":  1240,
    "total_transient_rooms": 4180,
    "group_pct":          22.9,
    "vs_ly_rooms_pct":    8.18,
    "vs_ly_revenue_pct":  10.33,
    "pickup_rooms_7d":    312,
    "ly_coverage_pct":    93.3
  },
  "daily": [
    {
      "target_date":        "2026-03-24",
      "day_of_week":        "Tuesday",
      "days_out":           1,
      "rooms_otb":          185,
      "occ_otb_pct":        73.4,
      "adr_otb":            179.50,
      "revenue_otb":        33207.50,
      "group_rooms":        45,
      "transient_rooms":    140,
      "group_pct":          24.3,
      "ly_rooms":           172,
      "ly_occ_pct":         68.3,
      "ly_adr":             168.20,
      "ly_revenue":         28930.40,
      "vs_ly_rooms":        13,
      "vs_ly_rooms_pct":    7.56,
      "vs_ly_revenue_pct":  14.79,
      "pickup_rooms":       8,
      "pickup_revenue":     1436.00,
      "compare_snapshot":   "2026-03-16"
    }
  ]
}
```

**Edge cases:**
- No OTB data at all: `has_data: false`.
- `compare_snapshot` not found (no snapshot 7 days ago): `pickup_rooms` and `pickup_revenue` are null for all rows; note in response.
- Multiple snapshot_dates on the same day (import + manual): deduplicate by taking `source = 'import'` over `'snapshot'` over `'manual'`; apply filter `.filter(OTBForecast.source != 'seed')` if seed data is present.

---

## Part 3: STR Index Trends

### Endpoint Definition

```
GET /api/compset/str-trends
```

**Blueprint:** `compset_bp` in `routes/compset.py`
**Auth:** `@login_required`
**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `start_date` | `YYYY-MM-DD` | 12 months ago | Start of analysis window |
| `end_date` | `YYYY-MM-DD` | Today | End of analysis window |
| `period_type` | `daily` or `monthly` | `daily` | Filter on `STRCompSet.period_type` |

---

### Query Logic

```python
from database.models import db, STRCompSet, DailyJourMetrics, TOTAL_ROOMS
from sqlalchemy import func

# --- Date range ---
start_date, end_date = _get_date_range()

# --- Raw STR records ---
str_rows = STRCompSet.query.filter(
    STRCompSet.report_date.between(start_date, end_date),
    STRCompSet.period_type == period_type
).order_by(STRCompSet.report_date).all()

if not str_rows:
    return jsonify({'success': True, 'has_data': False})

# --- Monthly aggregation ---
monthly = {}
for r in str_rows:
    key = f"{r.report_date.year}-{r.report_date.month:02d}"
    if key not in monthly:
        monthly[key] = {
            'my_occ': [], 'my_adr': [], 'my_revpar': [],
            'comp_occ': [], 'comp_adr': [], 'comp_revpar': [],
            'occ_index': [], 'adr_index': [], 'revpar_index': [],
            'occ_rank': [], 'adr_rank': [], 'revpar_rank': [],
            'comp_set_size': r.comp_set_size or 6,
        }
    monthly[key]['my_occ'].append(r.my_occ or 0)
    monthly[key]['my_adr'].append(r.my_adr or 0)
    monthly[key]['my_revpar'].append(r.my_revpar or 0)
    monthly[key]['comp_occ'].append(r.comp_occ or 0)
    monthly[key]['comp_adr'].append(r.comp_adr or 0)
    monthly[key]['comp_revpar'].append(r.comp_revpar or 0)
    # Indices: calculate from my/comp — do NOT average stored index (averaging ratios is wrong)
    # Instead: index = mean(my) / mean(comp) * 100 at the month level
    if r.occ_rank:  monthly[key]['occ_rank'].append(r.occ_rank)
    if r.adr_rank:  monthly[key]['adr_rank'].append(r.adr_rank)
    if r.revpar_rank: monthly[key]['revpar_rank'].append(r.revpar_rank)

def _mean(lst): return round(sum(lst) / len(lst), 2) if lst else None
def _index(my, comp): return round(my / comp * 100, 1) if comp else None

monthly_trend = []
for key in sorted(monthly.keys()):
    m = monthly[key]
    my_occ     = _mean(m['my_occ'])
    comp_occ   = _mean(m['comp_occ'])
    my_adr     = _mean(m['my_adr'])
    comp_adr   = _mean(m['comp_adr'])
    my_revpar  = _mean(m['my_revpar'])
    comp_revpar= _mean(m['comp_revpar'])

    monthly_trend.append({
        'period':          key,
        'my_occ':          my_occ,
        'comp_occ':        comp_occ,
        'occ_index':       _index(my_occ, comp_occ),
        'my_adr':          my_adr,
        'comp_adr':        comp_adr,
        'adr_index':       _index(my_adr, comp_adr),
        'my_revpar':       my_revpar,
        'comp_revpar':     comp_revpar,
        'revpar_index':    _index(my_revpar, comp_revpar),
        'avg_occ_rank':    _mean(m['occ_rank']),
        'avg_adr_rank':    _mean(m['adr_rank']),
        'avg_revpar_rank': _mean(m['revpar_rank']),
        'comp_set_size':   m['comp_set_size'],
        'day_count':       len(m['my_occ']),
    })

# --- Fair share analysis ---
# Fair share % = my_rooms / total comp rooms
# "Total comp rooms" is not stored; derive as comp_occ implies a comp_set aggregate.
# Best available proxy: (comp_occ / 100) × TOTAL_ROOMS × comp_set_size
# This is an approximation — document the assumption explicitly.
# Fair share index = my_occ_index (already computed above as occ_index)
# Fair share % = 100 / comp_set_size (theoretical equal share)
fair_share_pct = round(100 / (str_rows[0].comp_set_size or 6), 1)

# --- Summary over full period ---
all_my_revpar    = [r.my_revpar for r in str_rows if r.my_revpar]
all_comp_revpar  = [r.comp_revpar for r in str_rows if r.comp_revpar]
all_revpar_ranks = [r.revpar_rank for r in str_rows if r.revpar_rank]
```

#### JSON Response Schema

```json
{
  "success":     true,
  "has_data":    true,
  "start_date":  "2025-03-01",
  "end_date":    "2026-03-23",
  "period_type": "daily",
  "fair_share": {
    "theoretical_pct": 16.7,
    "comp_set_size":   6,
    "note": "Theoretical equal share = 100 / comp_set_size. Compare vs avg occ_index to assess penetration."
  },
  "summary": {
    "avg_occ_index":    105.2,
    "avg_adr_index":    101.8,
    "avg_revpar_index": 107.1,
    "avg_revpar_rank":  2.3,
    "days_ranked_1st_revpar": 87,
    "data_days":        365
  },
  "monthly_trend": [
    {
      "period":           "2025-03",
      "my_occ":           76.4,
      "comp_occ":         72.1,
      "occ_index":        105.9,
      "my_adr":           184.20,
      "comp_adr":         181.10,
      "adr_index":        101.7,
      "my_revpar":        140.73,
      "comp_revpar":      130.57,
      "revpar_index":     107.8,
      "avg_occ_rank":     2.1,
      "avg_adr_rank":     2.8,
      "avg_revpar_rank":  2.0,
      "comp_set_size":    6,
      "day_count":        31
    }
  ]
}
```

**Methodological note on index calculation:** Computing `mean(my) / mean(comp) * 100` at the monthly level is more accurate than averaging daily indices. Daily indices are ratio data and their averages are not additive. Document this in a code comment.

**Edge cases:**
- `comp_occ = 0` for any month: `occ_index = null` for that month.
- `period_type = 'monthly'`: STRCompSet rows with `period_type = 'monthly'` may already be aggregated by the data provider — use them as-is without further aggregation.
- Fewer than 7 days of STR data for a month: include data but flag `"low_sample": true` on that month's record.

---

## Part 4: Accounting Month-End Dashboard

### Endpoint Definition

```
GET /api/dashboard/accounting
```

**Blueprint:** `dashboard_bp` in `routes/dashboard.py`
**Auth:** `@login_required` — enforce `role_required('accounting', 'gm', 'admin')`
**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `year` | Integer | Current year | Year of month-end period |
| `month` | Integer | Current month | Month of period (1-12) |

---

### Query Logic

```python
import calendar
from database.models import (
    db, MonthEndChecklist, DailyJourMetrics, NightAuditSession,
    DepositVariance, DailyCardMetrics, MonthlyExpense, DepartmentLabor,
    MonthlyBudget, DailyCashRecon
)
from sqlalchemy import func
from datetime import date

year  = request.args.get('year',  date.today().year,  type=int)
month = request.args.get('month', date.today().month, type=int)

days_in_month = calendar.monthrange(year, month)[1]
month_start   = date(year, month, 1)
month_end     = date(year, month, days_in_month)
```

#### Section A: MonthEndChecklist Progress

```python
tasks = MonthEndChecklist.query.filter_by(year=year, month=month).all()
total_tasks     = len(tasks)
completed_tasks = sum(1 for t in tasks if t.completed)
pending         = [t.task_name for t in tasks if not t.completed]
```

#### Section B: Revenue Verification

```python
# Sum of DailyJourMetrics.total_revenue for all days in month
djm_sum = db.session.query(
    func.sum(DailyJourMetrics.total_revenue),
    func.sum(DailyJourMetrics.room_revenue),
    func.sum(DailyJourMetrics.fb_revenue),
    func.count(DailyJourMetrics.id).label('days_with_data')
).filter(
    DailyJourMetrics.date.between(month_start, month_end)
).first()

days_with_data = djm_sum[3] or 0

# Budget for comparison
budget = MonthlyBudget.query.filter_by(year=year, month=month).first()
```

#### Section C: Missing Data Detection

```python
# All dates in the month that have no DJM row
all_dates = {month_start + timedelta(days=i) for i in range(days_in_month)}
present   = {r.date for r in DailyJourMetrics.query.filter(
    DailyJourMetrics.date.between(month_start, month_end)
).with_entities(DailyJourMetrics.date).all()}
missing_dates = sorted(all_dates - present)

# Also check for NightAuditSession gaps
nas_present = {r.audit_date for r in NightAuditSession.query.filter(
    NightAuditSession.audit_date.between(month_start, month_end)
).with_entities(NightAuditSession.audit_date).all()}
missing_rj = sorted(all_dates - nas_present)
```

#### Section D: GL Suspense Account Status

```python
# Latest NightAuditSession for the month (most recent date)
# GL 101100 = "Autres revenus" suspense; GL 100401 = cash/bank reconciliation
latest_nas = NightAuditSession.query.filter(
    NightAuditSession.audit_date.between(month_start, month_end)
).order_by(desc(NightAuditSession.audit_date)).first()

# If month is complete and latest NAS is last day of month
```

#### Section E: Deposit Variance Summary by Employee

```python
# All deposit variances for the month grouped by employee
dep_vars = db.session.query(
    DepositVariance.employee_name,
    DepositVariance.department,
    func.count(DepositVariance.id).label('occurrences'),
    func.sum(DepositVariance.variance).label('total_variance'),
    func.sum(func.abs(DepositVariance.variance)).label('abs_total'),
    func.avg(DepositVariance.variance).label('avg_variance')
).filter(
    DepositVariance.audit_date.between(month_start, month_end)
).group_by(
    DepositVariance.employee_name,
    DepositVariance.department
).order_by(
    func.sum(func.abs(DepositVariance.variance)).desc()
).all()
```

#### Section F: Card Discount Costs by Type

```python
# Monthly card cost summary
card_costs = db.session.query(
    DailyCardMetrics.card_type,
    func.sum(DailyCardMetrics.pos_total).label('total_volume'),
    func.sum(DailyCardMetrics.discount_amount).label('total_discount'),
    func.sum(DailyCardMetrics.net_amount).label('net_amount'),
    func.sum(DailyCardMetrics.transaction_count).label('total_txn')
).filter(
    DailyCardMetrics.date.between(month_start, month_end)
).group_by(DailyCardMetrics.card_type).all()

# Blended rate = total_discount / total_volume
```

#### Section G: Data Quality Warnings

```python
warnings = []

# 1. MonthlyExpense missing for this period
exp = MonthlyExpense.query.filter_by(year=year, month=month).first()
if not exp:
    warnings.append({
        'code':    'MISSING_MONTHLY_EXPENSE',
        'severity':'warning',
        'message': f'MonthlyExpense not entered for {year}-{month:02d}. P&L and GOPPAR calculations will be incomplete.',
        'action':  'Enter expenses in the P&L tab before closing the month.'
    })

# 2. MonthlyBudget missing
if not budget:
    warnings.append({
        'code':    'MISSING_MONTHLY_BUDGET',
        'severity':'warning',
        'message': f'No budget targets found for {year}-{month:02d}.',
        'action':  'Enter budget in the Revenue Management setup.'
    })

# 3. DJM gaps
if missing_dates:
    warnings.append({
        'code':    'MISSING_DJM_DATES',
        'severity':'critical' if len(missing_dates) > 3 else 'warning',
        'message': f'{len(missing_dates)} date(s) have no DailyJourMetrics row.',
        'dates':   [d.isoformat() for d in missing_dates],
        'action':  'Upload missing RJ files or verify parser output.'
    })

# 4. Missing RJ sessions
if missing_rj:
    warnings.append({
        'code':    'MISSING_RJ_SESSIONS',
        'severity':'warning',
        'message': f'{len(missing_rj)} date(s) have no NightAuditSession.',
        'dates':   [d.isoformat() for d in missing_rj],
        'action':  'Verify night audit submissions for these dates.'
    })

# 5. DepartmentLabor missing
dl_count = DepartmentLabor.query.filter_by(year=year, month=month).count()
if dl_count == 0:
    warnings.append({
        'code':    'MISSING_DEPARTMENT_LABOR',
        'severity':'warning',
        'message': 'No DepartmentLabor entries for this period. Labor ratios cannot be computed.',
        'action':  'Import payroll data or enter manually via Labor tab.'
    })
```

#### JSON Response Schema

```json
{
  "success": true,
  "period":  { "year": 2026, "month": 3, "label": "March 2026", "days_in_month": 31 },

  "checklist": {
    "total_tasks":     15,
    "completed_tasks": 11,
    "progress_pct":    73.3,
    "pending_tasks":   ["Reconcile AR accounts", "Verify franchise fee invoice", "Submit to Controller", "Sign off P&L"],
    "status":          "in_progress"
  },

  "revenue_verification": {
    "djm_total_revenue":  1524810.00,
    "djm_room_revenue":   1089230.00,
    "djm_fb_revenue":     312450.00,
    "days_with_djm":      22,
    "days_expected":      31,
    "days_missing":       9,
    "budget_total_revenue": 1847000.00,
    "vs_budget_pct":        -17.45,
    "note": "Only 22 of 31 days have data. Month not yet complete."
  },

  "missing_data": {
    "djm_missing_dates":  ["2026-03-23", "2026-03-24"],
    "rj_missing_dates":   ["2026-03-23", "2026-03-24"],
    "djm_coverage_pct":   71.0,
    "rj_coverage_pct":    71.0
  },

  "gl_suspense": {
    "as_of_date":          "2026-03-22",
    "gl_101100": {
      "previous_balance":  2340.00,
      "additions":         150.00,
      "deductions":        -2340.00,
      "new_balance":       150.00,
      "variance":          0.00,
      "notes":             "Pending credit card adjustment"
    },
    "gl_100401": {
      "previous_balance":  0.00,
      "additions":         0.00,
      "deductions":        0.00,
      "new_balance":       0.00,
      "variance":          0.00,
      "notes":             ""
    }
  },

  "deposit_variance_leaderboard": [
    {
      "employee":        "Marie Côté",
      "department":      "RECEPTION",
      "occurrences":     4,
      "total_variance":  -12.50,
      "abs_total":       18.75,
      "avg_variance":    -3.13,
      "flag":            "review"
    },
    {
      "employee":        "Pierre Gagnon",
      "department":      "RESTAURANT",
      "occurrences":     2,
      "total_variance":  -5.00,
      "abs_total":       7.50,
      "avg_variance":    -2.50,
      "flag":            "ok"
    }
  ],

  "card_discount_costs": {
    "by_type": [
      { "card_type": "AMEX",     "volume": 124500.00, "discount": 3298.25, "rate_pct": 2.65, "transactions": 412, "net": 121201.75 },
      { "card_type": "VISA",     "volume": 210400.00, "discount": 3156.00, "rate_pct": 1.50, "transactions": 890, "net": 207244.00 },
      { "card_type": "MC",       "volume": 98200.00,  "discount": 1473.00, "rate_pct": 1.50, "transactions": 340, "net": 96727.00 },
      { "card_type": "DEBIT",    "volume": 45100.00,  "discount": 225.50,  "rate_pct": 0.50, "transactions": 520, "net": 44874.50 },
      { "card_type": "DISCOVER", "volume": 8200.00,   "discount": 180.40,  "rate_pct": 2.20, "transactions": 28,  "net": 8019.60 }
    ],
    "totals": {
      "total_volume":   486400.00,
      "total_discount": 8333.15,
      "blended_rate_pct": 1.71,
      "total_net":      478066.85,
      "total_transactions": 2190
    }
  },

  "data_quality_warnings": [
    {
      "code":     "MISSING_DJM_DATES",
      "severity": "warning",
      "message":  "9 dates have no DailyJourMetrics row.",
      "dates":    ["2026-03-23", "..."],
      "action":   "Upload missing RJ files or verify parser output."
    }
  ]
}
```

**Flag logic for deposit variance leaderboard:**
- `abs_total >= 50.00` → `"flag": "critical"`
- `abs_total >= 20.00` → `"flag": "review"`
- Otherwise → `"flag": "ok"`

---

## Part 5: Enhanced Existing CRM Tabs

### 5.1 Cash Tab Enhancements

**Add to:** `GET /api/crm/tabs/cash-recon` response

#### A. DepositVariance Leaderboard (date range scoped)

```python
# Add to existing cash_reconciliation() function

from database.models import DepositVariance

dep_vars = db.session.query(
    DepositVariance.employee_name,
    DepositVariance.department,
    func.count(DepositVariance.id).label('occurrences'),
    func.sum(DepositVariance.variance).label('net_variance'),
    func.sum(func.abs(DepositVariance.variance)).label('abs_variance'),
    func.max(func.abs(DepositVariance.variance)).label('worst_single')
).filter(
    DepositVariance.audit_date.between(start, end)
).group_by(
    DepositVariance.employee_name,
    DepositVariance.department
).order_by(func.sum(func.abs(DepositVariance.variance)).desc()).limit(20).all()

deposit_leaderboard = [{
    'employee':     r.employee_name,
    'department':   r.department,
    'occurrences':  r.occurrences,
    'net_variance': round(r.net_variance or 0, 2),
    'abs_variance': round(r.abs_variance or 0, 2),
    'worst_single': round(r.worst_single or 0, 2),
    'flag': 'critical' if (r.abs_variance or 0) >= 50 else
            'review'   if (r.abs_variance or 0) >= 20 else 'ok'
} for r in dep_vars]
```

#### B. DailyReconciliation Card-Type Breakdown

```python
from database.models import DailyReconciliation

recon_recs = DailyReconciliation.query.filter(
    DailyReconciliation.audit_date.between(start, end)
).all()

# Monthly card terminal vs bank variance
card_variance_monthly = {}
for r in recon_recs:
    key = f"{r.audit_date.year}-{r.audit_date.month:02d}"
    if key not in card_variance_monthly:
        card_variance_monthly[key] = {
            'visa': 0, 'mc': 0, 'amex': 0, 'debit': 0, 'discover': 0,
            'total_variance': 0, 'days': 0, 'balanced_days': 0
        }
    card_variance_monthly[key]['visa']     += (r.card_visa_terminal - r.card_visa_bank)
    card_variance_monthly[key]['mc']       += (r.card_mc_terminal - r.card_mc_bank)
    card_variance_monthly[key]['amex']     += (r.card_amex_terminal - r.card_amex_bank)
    card_variance_monthly[key]['debit']    += (r.card_debit_terminal - r.card_debit_bank)
    card_variance_monthly[key]['discover'] += (r.card_discover_terminal - r.card_discover_bank)
    card_variance_monthly[key]['total_variance'] += r.card_total_variance or 0
    card_variance_monthly[key]['days']     += 1
    if r.is_balanced:
        card_variance_monthly[key]['balanced_days'] += 1
```

#### C. Consecutive Balanced Nights Streak

```python
# Query last 60 NightAuditSession records ordered most-recent first
recent_nas = NightAuditSession.query.filter(
    NightAuditSession.audit_date <= date.today()
).order_by(desc(NightAuditSession.audit_date)).limit(60).all()

current_streak = 0
best_streak    = 0
temp_streak    = 0

for s in recent_nas:
    if s.is_fully_balanced:
        current_streak += 1
        temp_streak    += 1
        best_streak     = max(best_streak, temp_streak)
    else:
        if current_streak == temp_streak:
            # First unbalanced night — stop current streak count
            pass
        temp_streak = 0
        # current_streak only counts from the most recent date
        if current_streak == (recent_nas.index(s)):
            current_streak = recent_nas.index(s)
            break

# Simpler correct algorithm:
current_streak = 0
for s in recent_nas:
    if s.is_fully_balanced:
        current_streak += 1
    else:
        break
```

**New fields added to cash-recon response:**

```json
{
  "deposit_variance_leaderboard": [ ... ],
  "card_type_breakdown_monthly": [
    {
      "period":         "2026-02",
      "visa_variance":  -1.20,
      "mc_variance":    0.00,
      "amex_variance":  -3.40,
      "debit_variance": 0.00,
      "discover_variance": 0.00,
      "total_variance": -4.60,
      "days":           28,
      "balanced_days":  25,
      "balance_pct":    89.3
    }
  ],
  "balanced_streak": {
    "current_streak_days": 12,
    "streak_started":      "2026-03-11",
    "note": "Consecutive nights where is_fully_balanced = True"
  }
}
```

---

### 5.2 Labor Tab Enhancements

**Add to:** `GET /api/crm/tabs/labor` response

#### Budget Variance by Department

```python
# DepartmentLabor already has budget_cost and budget_hours fields
# The existing endpoint loads dept_labor — add this computation

budget_variance_by_dept = []
dept_month_map = {}  # key: (dept, period)

for dl in dept_labor:
    key = (dl.department, f"{dl.year}-{dl.month:02d}")
    dept_month_map[key] = dl

# Build monthly budget variance table
dept_names = sorted({dl.department for dl in dept_labor})
periods    = sorted({f"{dl.year}-{dl.month:02d}" for dl in dept_labor})

for period in periods:
    row = {'period': period, 'departments': {}}
    for dept in dept_names:
        dl = dept_month_map.get((dept, period))
        if dl:
            actual_cost   = dl.total_labor_cost or 0
            budget_cost   = dl.budget_cost or 0
            actual_hours  = dl.total_hours or 0
            budget_hours  = dl.budget_hours or 0
            cost_variance = round(actual_cost - budget_cost, 2)
            hours_variance= round(actual_hours - budget_hours, 1)
            cost_var_pct  = round(cost_variance / budget_cost * 100, 1) if budget_cost else None
            row['departments'][dept] = {
                'actual_cost':    actual_cost,
                'budget_cost':    budget_cost,
                'cost_variance':  cost_variance,
                'cost_var_pct':   cost_var_pct,
                'actual_hours':   actual_hours,
                'budget_hours':   budget_hours,
                'hours_variance': hours_variance,
                'overtime_hours': dl.overtime_hours or 0,
                'flag': 'over' if cost_variance > 0 else 'under' if cost_variance < 0 else 'on_budget'
            }
    budget_variance_by_dept.append(row)
```

**New field added to labor response:**

```json
{
  "budget_variance_by_dept": [
    {
      "period": "2026-02",
      "departments": {
        "RECEPTION": {
          "actual_cost":    42000.00,
          "budget_cost":    39500.00,
          "cost_variance":  2500.00,
          "cost_var_pct":   6.3,
          "actual_hours":   1820.0,
          "budget_hours":   1750.0,
          "hours_variance": 70.0,
          "overtime_hours": 45.5,
          "flag": "over"
        },
        "KITCHEN": { "...": "..." }
      }
    }
  ]
}
```

---

### 5.3 P&L Tab Enhancements

**Add to:** `GET /api/crm/tabs/pnl-budget` response

#### A. GOPPAR Metric

GOPPAR = Gross Operating Profit Per Available Room
Formula: `(total_revenue - total_expenses) / (TOTAL_ROOMS × days_in_period)`

```python
from database.models import TOTAL_ROOMS

goppar_monthly = []
for key in sorted(set(list(revenue_by_period.keys()) + list(expense_map.keys()))):
    year, month = key
    import calendar
    days_in_mo = calendar.monthrange(year, month)[1]
    revenue    = revenue_by_period.get(key, 0)
    expense    = expense_map.get(key)
    exp_total  = expense.total_expenses if expense else 0
    gop        = revenue - exp_total
    # GOPPAR denominator: available room-nights in the month
    available_room_nights = TOTAL_ROOMS * days_in_mo
    goppar     = round(gop / available_room_nights, 2) if available_room_nights > 0 else None

    goppar_monthly.append({
        'year':         year,
        'month':        month,
        'revenue':      round(revenue, 2),
        'expenses':     round(exp_total, 2),
        'gop':          round(gop, 2),
        'goppar':       goppar,
        'days_in_month': days_in_mo,
        'expense_data_present': expense is not None,
    })
```

#### B. Data Quality Warning When MonthlyExpense Is Empty

```python
# Check which months in the range have no MonthlyExpense row
months_with_revenue = set(revenue_by_period.keys())
months_with_expense = {(e.year, e.month) for e in expenses}
months_missing_expense = sorted(months_with_revenue - months_with_expense)

pnl_data_warnings = []
if months_missing_expense:
    pnl_data_warnings.append({
        'code':    'MISSING_MONTHLY_EXPENSE',
        'severity': 'warning',
        'message': f'{len(months_missing_expense)} month(s) have revenue but no expense data.',
        'periods': [f"{y}-{m:02d}" for y, m in months_missing_expense],
        'action':  'Enter monthly expenses to enable GOPPAR and profit margin calculations.'
    })
```

**New fields added to pnl-budget response:**

```json
{
  "goppar_monthly": [
    {
      "year":    2026,
      "month":   2,
      "revenue": 1390000.00,
      "expenses": 980000.00,
      "gop":     410000.00,
      "goppar":  54.23,
      "days_in_month": 28,
      "expense_data_present": true
    }
  ],
  "pnl_data_warnings": [
    {
      "code":     "MISSING_MONTHLY_EXPENSE",
      "severity": "warning",
      "message":  "1 month has revenue but no expense data.",
      "periods":  ["2026-03"],
      "action":   "Enter monthly expenses to enable GOPPAR and profit margin calculations."
    }
  ]
}
```

---

### 5.4 Revenue Tab Enhancements

**Add to:** `GET /api/crm/tabs/revenue-mgmt` response

These three metrics require `DailyJourMetrics` which is already loaded in the existing endpoint.

```python
# --- OOS-Adjusted Occupancy ---
# For each day: avail_adjusted = TOTAL_ROOMS - rooms_hors_usage
# occ_adjusted = total_rooms_sold / avail_adjusted * 100
# Report monthly average

oos_adj_occ = {}
for m in metrics:
    key = f"{m.year}-{m.month:02d}"
    if key not in oos_adj_occ:
        oos_adj_occ[key] = {'adj_occ_sum': 0, 'std_occ_sum': 0, 'count': 0}
    avail_adj = (m.rooms_available or TOTAL_ROOMS) - (m.rooms_hors_usage or 0)
    adj_occ = (m.total_rooms_sold / avail_adj * 100) if avail_adj > 0 else m.occupancy_rate
    oos_adj_occ[key]['adj_occ_sum'] += adj_occ
    oos_adj_occ[key]['std_occ_sum'] += m.occupancy_rate or 0
    oos_adj_occ[key]['count'] += 1

oos_adjusted_monthly = []
for key in sorted(oos_adj_occ.keys()):
    d = oos_adj_occ[key]
    c = d['count']
    oos_adjusted_monthly.append({
        'period':       key,
        'avg_occ_standard':  round(d['std_occ_sum'] / c, 2) if c else 0,
        'avg_occ_oos_adjusted': round(d['adj_occ_sum'] / c, 2) if c else 0,
    })

# --- Effective ADR (excluding comp rooms) ---
# effective_adr = room_revenue / (total_rooms_sold - rooms_comp)
# rooms_comp already exists on DJM

effective_adr_monthly = {}
for m in metrics:
    key = f"{m.year}-{m.month:02d}"
    if key not in effective_adr_monthly:
        effective_adr_monthly[key] = {'rev': 0, 'paid_rooms': 0, 'comp_rooms': 0, 'total_rooms': 0}
    paid = (m.total_rooms_sold or 0) - (m.rooms_comp or 0)
    effective_adr_monthly[key]['rev']         += m.room_revenue or 0
    effective_adr_monthly[key]['paid_rooms']  += max(paid, 0)
    effective_adr_monthly[key]['comp_rooms']  += m.rooms_comp or 0
    effective_adr_monthly[key]['total_rooms'] += m.total_rooms_sold or 0

eff_adr_monthly = []
for key in sorted(effective_adr_monthly.keys()):
    d = effective_adr_monthly[key]
    eff_adr = round(d['rev'] / d['paid_rooms'], 2) if d['paid_rooms'] > 0 else 0
    std_adr = round(d['rev'] / d['total_rooms'], 2) if d['total_rooms'] > 0 else 0
    comp_pct= round(d['comp_rooms'] / d['total_rooms'] * 100, 1) if d['total_rooms'] > 0 else 0
    eff_adr_monthly.append({
        'period':        key,
        'standard_adr':  std_adr,
        'effective_adr': eff_adr,
        'comp_room_pct': comp_pct,
        'total_comp_rooms': d['comp_rooms'],
    })
```

**New fields added to revenue-mgmt response:**

```json
{
  "oos_adjusted_occ_monthly": [
    {
      "period":              "2026-02",
      "avg_occ_standard":    76.4,
      "avg_occ_oos_adjusted": 78.1
    }
  ],
  "effective_adr_monthly": [
    {
      "period":           "2026-02",
      "standard_adr":     184.20,
      "effective_adr":    188.40,
      "comp_room_pct":    2.23,
      "total_comp_rooms": 65
    }
  ]
}
```

---

## Part 6: Night Auditor Error Detection Panel

### Endpoint Definition

```
GET /api/dashboard/auditor-panel
```

**Blueprint:** `dashboard_bp` in `routes/dashboard.py`
**Auth:** `@login_required`
**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `date` | `YYYY-MM-DD` | Today | Audit date to inspect |

**Purpose:** Real-time error detection dashboard shown to the night auditor during their shift. All data sourced from the live `NightAuditSession` for the given date.

---

### Query Logic

```python
from datetime import date, timedelta
from database.models import NightAuditSession, DailyCashRecon, DailyJourMetrics
from sqlalchemy import desc

audit_date_str = request.args.get('date')
audit_date     = _parse_date(audit_date_str) or date.today()

nas = NightAuditSession.query.filter_by(audit_date=audit_date).first()

# Reference data for context: 7-day average variance
seven_days_back = audit_date - timedelta(days=7)
recent_cash = DailyCashRecon.query.filter(
    DailyCashRecon.date.between(seven_days_back, audit_date - timedelta(days=1))
).all()
avg_quasi_7d = sum(abs(r.quasimodo_variance or 0) for r in recent_cash) / len(recent_cash) \
               if recent_cash else None

# Prior night for comparison
prior_date = audit_date - timedelta(days=1)
prior_nas  = NightAuditSession.query.filter_by(audit_date=prior_date).first()
```

#### Balance Status Grid Logic

```python
# Each check produces a status object:
# { "status": "green"|"red"|"pending", "value": float, "threshold": float, "label": str }

def _balance_check(is_balanced, value, threshold, label):
    return {
        'label':     label,
        'status':    'green' if is_balanced else ('red' if value is not None else 'pending'),
        'value':     value,
        'threshold': threshold,
        'is_ok':     is_balanced,
    }

if nas:
    recap_check = _balance_check(
        nas.is_recap_balanced,
        abs(nas.recap_balance or 0),
        0.02,
        'Récap'
    )
    transelect_check = _balance_check(
        nas.is_transelect_balanced,
        abs(nas.transelect_variance or 0),
        1.00,
        'Transelect'
    )
    ar_check = _balance_check(
        nas.is_ar_balanced,
        abs(nas.geac_ar_variance or 0),
        0.02,
        'AR (GEAC)'
    )
    quasi_check = {
        'label':     'Quasimodo',
        'status':    'green' if abs(nas.quasi_variance or 0) <= 5.0 else 'red',
        'value':     round(nas.quasi_variance or 0, 2),
        'threshold': 5.00,
        'is_ok':     abs(nas.quasi_variance or 0) <= 5.00,
    }
    overall_balanced = nas.is_fully_balanced
else:
    # No session yet for today
    recap_check = transelect_check = ar_check = {'status': 'pending', 'value': None, 'is_ok': None}
    quasi_check = {'status': 'pending', 'value': None, 'is_ok': None}
    overall_balanced = None
```

#### Outstanding Items

```python
outstanding = []

if nas:
    # 1. Variance checks
    if not nas.is_recap_balanced:
        outstanding.append({
            'priority': 'high',
            'category': 'RECAP',
            'issue':    f"Récap non balancé — variance: {nas.recap_balance:+.2f}$",
            'action':   "Vérifier les lectures Lightspeed et POS, recompter les dépôts.",
            'value':    nas.recap_balance,
        })

    if not nas.is_transelect_balanced:
        outstanding.append({
            'priority': 'high',
            'category': 'TRANSELECT',
            'issue':    f"Transelect non balancé — variance: {nas.transelect_variance:+.2f}$",
            'action':   "Comparer terminaux restaurant vs réception, vérifier Daily Rev FreedomPay.",
            'value':    nas.transelect_variance,
        })

    if not nas.is_ar_balanced:
        outstanding.append({
            'priority': 'high',
            'category': 'AR_GEAC',
            'issue':    f"AR GEAC non balancé — variance: {nas.geac_ar_variance:+.2f}$",
            'action':   "Vérifier solde précédent, charges et paiements du jour.",
            'value':    nas.geac_ar_variance,
        })

    quasi_var = nas.quasi_variance or 0
    if abs(quasi_var) > 5.0:
        outstanding.append({
            'priority': 'critical' if abs(quasi_var) > 10 else 'high',
            'category': 'QUASIMODO',
            'issue':    f"Variance Quasimodo: {quasi_var:+.2f}$ (seuil ±5$)",
            'action':   "Revoir les cartes par terminal (Débit/Visa/MC/Amex), chercher transaction manquante.",
            'value':    quasi_var,
        })

    # 2. GL suspense
    if abs(nas.gl_101100_variance or 0) > 0.02:
        outstanding.append({
            'priority': 'medium',
            'category': 'GL_101100',
            'issue':    f"Compte GL 101100 — variance non résolue: {nas.gl_101100_variance:+.2f}$",
            'action':   "Vérifier les entrées du journal EJ et réconcilier le solde.",
            'value':    nas.gl_101100_variance,
        })

    if abs(nas.gl_100401_variance or 0) > 0.02:
        outstanding.append({
            'priority': 'medium',
            'category': 'GL_100401',
            'issue':    f"Compte GL 100401 — variance: {nas.gl_100401_variance:+.2f}$",
            'action':   "Vérifier le compte bancaire vs dépôt net Récap.",
            'value':    nas.gl_100401_variance,
        })

    # 3. Internet/Sonifi variances
    if abs(nas.internet_variance or 0) > 0.02:
        outstanding.append({
            'priority': 'medium',
            'category': 'INTERNET',
            'issue':    f"Variance Internet: {nas.internet_variance:+.2f}$ (LS 36.1 vs 36.5)",
            'action':   "Comparer Cashier Detail 36.1 et 36.5, ajuster si nécessaire.",
            'value':    nas.internet_variance,
        })

    if abs(nas.sonifi_variance or 0) > 0.02:
        outstanding.append({
            'priority': 'medium',
            'category': 'SONIFI',
            'issue':    f"Variance Sonifi: {nas.sonifi_variance:+.2f}$ (CD 35.2 vs courriel)",
            'action':   "Vérifier montant courriel Sonifi 03h00 vs Cashier Detail 35.2.",
            'value':    nas.sonifi_variance,
        })

    # 4. Session not yet submitted
    if nas.status in ('draft', 'in_progress'):
        outstanding.append({
            'priority': 'info',
            'category': 'SUBMISSION',
            'issue':    f"RJ en statut '{nas.status}' — non soumis",
            'action':   "Compléter toutes les sections et soumettre avant 06h00.",
            'value':    None,
        })

# Sort: critical > high > medium > info
priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'info': 3}
outstanding.sort(key=lambda x: priority_order.get(x['priority'], 9))
```

#### Variance Alert Context

```python
variance_alerts = []

if nas:
    quasi_var = nas.quasi_variance or 0

    # Quasimodo with 7-day context
    variance_alerts.append({
        'metric':      'quasimodo_variance',
        'label':       'Variance Quasimodo',
        'current':     round(quasi_var, 2),
        'threshold':   5.00,
        'threshold_critical': 10.00,
        'avg_7d':      round(avg_quasi_7d, 2) if avg_quasi_7d is not None else None,
        'status':      'ok'      if abs(quasi_var) <= 5.0 else
                       'warning' if abs(quasi_var) <= 10.0 else 'critical',
        'context':     f"Moy. 7 jours: ±{avg_quasi_7d:.2f}$" if avg_quasi_7d else "Pas de données de comparaison",
    })

    # Surplus/Deficit
    surplus = nas.recap_balance or 0  # recap_balance IS the surplus/deficit equivalent
    variance_alerts.append({
        'metric':    'surplus_deficit',
        'label':     'Surplus / Déficit caisse',
        'current':   round(surplus, 2),
        'threshold': 20.00,
        'threshold_critical': 50.00,
        'status':    'ok'      if abs(surplus) <= 20.0 else
                     'warning' if abs(surplus) <= 50.0 else 'critical',
        'context':   "Différence entre encaisse comptée et système",
    })

    # AR variance
    ar_var = nas.geac_ar_variance or 0
    variance_alerts.append({
        'metric':    'ar_variance',
        'label':     'Variance AR GEAC',
        'current':   round(ar_var, 2),
        'threshold': 0.02,
        'status':    'ok' if abs(ar_var) <= 0.02 else 'critical',
        'context':   "Doit être ±0.02$ pour fermeture propre",
    })
```

#### JSON Response Schema

```json
{
  "success":       true,
  "audit_date":    "2026-03-23",
  "session_exists": true,
  "session_status": "in_progress",
  "auditor":       "Jean-François Tremblay",
  "generated_at":  "2026-03-23T04:30:00",

  "balance_grid": {
    "overall_balanced": false,
    "checks": {
      "recap": {
        "label":     "Récap",
        "status":    "green",
        "value":     0.00,
        "threshold": 0.02,
        "is_ok":     true
      },
      "transelect": {
        "label":     "Transelect",
        "status":    "green",
        "value":     0.45,
        "threshold": 1.00,
        "is_ok":     true
      },
      "ar_geac": {
        "label":     "AR (GEAC)",
        "status":    "red",
        "value":     12.30,
        "threshold": 0.02,
        "is_ok":     false
      },
      "quasimodo": {
        "label":     "Quasimodo",
        "status":    "green",
        "value":     -3.20,
        "threshold": 5.00,
        "is_ok":     true
      }
    }
  },

  "outstanding_items": [
    {
      "priority": "high",
      "category": "AR_GEAC",
      "issue":    "AR GEAC non balancé — variance: +12.30$",
      "action":   "Vérifier solde précédent, charges et paiements du jour.",
      "value":    12.30
    }
  ],

  "variance_alerts": [
    {
      "metric":    "quasimodo_variance",
      "label":     "Variance Quasimodo",
      "current":   -3.20,
      "threshold": 5.00,
      "threshold_critical": 10.00,
      "avg_7d":    2.85,
      "status":    "ok",
      "context":   "Moy. 7 jours: ±2.85$"
    },
    {
      "metric":    "surplus_deficit",
      "label":     "Surplus / Déficit caisse",
      "current":   0.00,
      "threshold": 20.00,
      "threshold_critical": 50.00,
      "status":    "ok",
      "context":   "Différence entre encaisse comptée et système"
    },
    {
      "metric":    "ar_variance",
      "label":     "Variance AR GEAC",
      "current":   12.30,
      "threshold": 0.02,
      "status":    "critical",
      "context":   "Doit être ±0.02$ pour fermeture propre"
    }
  ],

  "fallback_notes": {
    "session_found":       true,
    "prior_night_found":   true,
    "avg_7d_data_points":  6
  }
}
```

**Fallback rules:**
- No `NightAuditSession` for `audit_date`: `session_exists: false`, all balance checks return `"status": "pending"`, `outstanding_items: []` with one info item: "Aucune session d'audit trouvée pour cette date."
- `status = 'locked'`: session is read-only — flag it in the response and disable actionable suggestions.

---

## Implementation Priority Ranking

| Priority | Endpoint | Effort | Business Impact |
|---|---|---|---|
| 1 | `GET /api/dashboard/auditor-panel` | Low — reuses NAS fields already populated | High — prevents errors going undetected during shift |
| 2 | `GET /api/dashboard/gm-briefing` | Medium — 4 independent query blocks | High — consolidates morning workflow into one call |
| 3 | Cash tab: balanced streak + leaderboard | Low — additive to existing endpoint | Medium — accountability and trend visibility |
| 4 | P&L tab: GOPPAR + data quality warnings | Low — additive computation | Medium — closes the GOPPAR gap that currently requires Excel |
| 5 | Revenue tab: OOS-adj occ + effective ADR | Low — reuses existing metrics loop | Medium — more accurate KPIs for Revenue Management |
| 6 | Labor tab: budget variance by dept | Low — fields already in DepartmentLabor | Medium — replaces manual payroll variance tracking |
| 7 | `GET /api/compset/otb-pace` | Medium — pick-up logic across snapshots | High once OTB data is actively maintained |
| 8 | `GET /api/dashboard/accounting` | Medium — 7 independent sections | High during month-end close |
| 9 | `GET /api/compset/str-trends` | Low — STRCompSet already seeded | Medium — requires consistent STR import discipline |

---

## Shared Utility Functions to Add

Add these to `routes/dashboard.py` or a new `utils/response_helpers.py`:

```python
def _variance_dict(actual, reference):
    """
    Compute variance between actual and reference values.
    Returns dict with absolute value, percentage, and direction.
    Returns all None if reference is None or zero.
    """
    if reference is None or reference == 0:
        return {'value': None, 'pct': None, 'direction': 'unknown'}
    diff = actual - reference
    pct  = round(diff / abs(reference) * 100, 2)
    return {
        'value':     round(diff, 2),
        'pct':       pct,
        'direction': 'above' if diff >= 0 else 'below'
    }


def _parse_date(s):
    """Parse YYYY-MM-DD string to date, or None."""
    if not s:
        return None
    try:
        from datetime import datetime
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _daily_budget(budget_model, days_in_month):
    """
    Prorate a MonthlyBudget record to a single day.
    Returns dict of daily budget values, or all None if budget_model is None.
    """
    if not budget_model:
        return {k: None for k in ['occupancy_pct', 'adr', 'room_revenue', 'total_revenue']}
    from database.models import TOTAL_ROOMS
    return {
        'occupancy_pct': round(budget_model.rooms_target / TOTAL_ROOMS / days_in_month * 100, 2),
        'adr':           budget_model.adr_target,
        'room_revenue':  round(budget_model.room_revenue / days_in_month, 2),
        'total_revenue': round(budget_model.total_revenue / days_in_month, 2),
    }
```

---

## Index Calculation Correctness Note

When computing STR indices from daily records aggregated to monthly, **always compute the index from aggregated numerator and denominator**, not by averaging daily indices:

```python
# CORRECT: index from aggregated means
monthly_occ_index = (mean_my_occ / mean_comp_occ) * 100

# WRONG: average of daily indices (Jensen's inequality makes this biased)
monthly_occ_index = mean([r.occ_index for r in daily_rows])
```

The same principle applies to GOPPAR — always divide the aggregated GOP by aggregated available room-nights, not average daily GOPPAR values.

---

## Data Integrity Assertions to Add as Code Comments

Place these as `assert`-style comments in every new route to document the assumptions developers must uphold:

1. `DailyJourMetrics.date` is `UNIQUE` — one row per calendar date. Never aggregate without grouping by date first.
2. `OTBForecast` has one row per `(snapshot_date, target_date)` pair — always filter by `snapshot_date` before aggregating.
3. `NightAuditSession.is_fully_balanced` is computed by `calculate_all()` — it is not authoritative until the session status is `submitted` or `locked`.
4. `DepartmentLabor.budget_cost` may be 0.0 (not NULL) when no budget was entered — treat 0.0 budget as "missing" in variance calculations to avoid division by zero masking.
5. `STRCompSet.occ_index`, `adr_index`, `revpar_index` are stored on the model but should be recomputed from `my_*` and `comp_*` fields when aggregating to avoid compounding rounding errors.
