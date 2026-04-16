# Database Models

Source: `database/models.py`

The application uses **Flask-SQLAlchemy** with SQLite. All models are defined in a single file.

---

## Schema Overview

### Property Management

**Property** (`properties`)

Multi-property support (currently single-property: Sheraton Laval).

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| code | String(10), unique | e.g. `'SHRLVL'` |
| name | String(200) | e.g. `'Sheraton Laval'` |
| brand | String(100) | Default `'Marriott'` |
| total_rooms | Integer | 252 for Sheraton Laval |
| pms_type | String(50) | Default `'Galaxy Lightspeed'` |
| pms_property_id | String(100) | |
| timezone | String(50) | Default `'America/Montreal'` |
| currency | String(3) | Default `'CAD'` |

### Authentication

**User** (`users`)

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| username | String(100), unique | Login identifier |
| email | String(120), unique, nullable | |
| password_hash | String(255) | Werkzeug hashed |
| role | String(50) | `night_auditor`, `gm`, `gsm`, `front_desk_supervisor`, `accounting`, `admin` |
| full_name_fr | String(200), nullable | Display name |
| is_active | Boolean | Default True |
| must_change_password | Boolean | Default True |
| last_login | DateTime, nullable | |
| default_property_id | FK -> properties.id | |

Methods: `set_password()`, `check_password()`, `has_role(*roles)`, `to_dict()`

**AuditSession** (`audit_sessions`)

Legacy session tracking. Links auditor to audit date and optional RJ file path.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| date | Date, indexed | Audit date |
| auditor_id | FK -> users.id | |
| started_at / completed_at | DateTime | |
| rj_file_path | String(500), nullable | |

### Daily Operations

**DailyReport** (`daily_reports`)

Consolidated daily revenue snapshot. One row per date (unique constraint on `date`).

| Column | Type | Notes |
|--------|------|-------|
| date | Date, unique, indexed | |
| revenue_comptant | Float | Cash |
| revenue_cartes | Float | Cards |
| revenue_cheques | Float | Cheques |
| revenue_total | Float | Total |
| deposit_cdn / deposit_us | Float | Deposits |
| variance | Float | Reconciliation variance |
| dueback_total | Float | |
| ar_balance / guest_ledger / city_ledger | Float | Ledger balances |
| auditor_name | String(100) | |

**VarianceRecord** (`variance_records`)

Per-receptionist daily variance tracking.

| Column | Type | Notes |
|--------|------|-------|
| date | Date, indexed | |
| receptionist | String(100), indexed | |
| expected / actual / variance | Float | |
| notes | Text, nullable | |

Class attribute `ALERT_THRESHOLD = 50.0` -- property `is_alert` returns True if abs(variance) > threshold.

**CashReconciliation** (`cash_reconciliations`)

Cash count reconciliation records.

| Column | Type | Notes |
|--------|------|-------|
| date | Date, indexed | |
| system_total / counted_total / variance | Float | |
| auditor | String(100) | |

**MonthEndChecklist** (`month_end_checklists`)

Task-based checklist for month-end procedures.

| Column | Type | Notes |
|--------|------|-------|
| year / month | Integer | |
| task_name | String(200) | |
| completed | Boolean | |
| completed_at | DateTime | |
| completed_by | String(100) | |

### Forecasting & Competitive Intelligence

**OTBForecast** (`otb_forecasts`)

On-The-Books forecast data -- future reservations snapshot. One row per (snapshot_date, target_date) pair.

| Column | Type | Notes |
|--------|------|-------|
| snapshot_date | Date, indexed | When this data was captured |
| target_date | Date, indexed | The future date being forecasted |
| rooms_otb | Integer | Rooms on the books |
| rooms_available | Integer | Default 252 |
| occ_otb | Float | OTB occupancy % |
| adr_otb | Float | OTB ADR |
| revenue_otb | Float | OTB room revenue |
| group_rooms | Integer | Group block rooms |
| transient_rooms | Integer | Individual reservations |
| ly_rooms / ly_occ / ly_adr / ly_revenue | Float/Integer | Same day last year comparison |
| source | String(50) | `manual`, `api`, `import` |

Unique constraint: `(snapshot_date, target_date)`.

**STRCompSet** (`str_comp_set`)

STR Competitive Set data -- weekly import from STR reports.

| Column | Type | Notes |
|--------|------|-------|
| report_date | Date, indexed | Report period date |
| period_type | String(20) | `daily`, `wtd`, `mtd`, `ytd` |
| my_occ / my_adr / my_revpar | Float | Hotel's own metrics |
| comp_occ / comp_adr / comp_revpar | Float | Comp set average |
| occ_index / adr_index / revpar_index | Float | Index = my / comp x 100 (RGI) |
| occ_rank / adr_rank / revpar_rank | Integer | Rank within comp set (1 = best) |
| comp_set_size | Integer | Default 5 |
| source | String(50) | `manual`, `api`, `import` |

### Historical Analytics

**DailyJourMetrics** (`daily_jour_metrics`)

Rich daily metrics extracted from jour sheets. One row per calendar day. Supports
multi-year historical analytics with approximately 45 columns covering:

- **Revenue**: room_revenue, fb_revenue, cafe_link_total, piazza_total, spesa_total, room_svc_total, banquet_total, tips_total, tabagie_total, other_revenue, total_revenue
- **F&B categories**: total_nourriture, total_boisson, total_bieres, total_vins, total_mineraux
- **Occupancy**: rooms_simple, rooms_double, rooms_suite, rooms_comp, total_rooms_sold, rooms_available, occupancy_rate, nb_clients
- **Payments**: visa_total, mastercard_total, amex_elavon_total, amex_global_total, debit_total, discover_total, total_cards
- **Taxes**: tps_total, tvq_total, tvh_total
- **Cash**: opening_balance, cash_difference, closing_balance
- **KPIs** (cached): adr, revpar, trevpar, food_pct, beverage_pct

**Indexes**: `ix_djm_year_month` on (year, month), `ix_djm_property_date` on (property_id, date).

**MonthlyExpense** (`monthly_expenses`)

Monthly operating expense data for profitability analysis (GOPPAR, break-even).

---

## NightAuditSession and Related Native Models

These models support the native (database-backed, no-Excel) audit workflow:

- **NightAuditSession** -- Stores all audit form fields for a single night
- **DailyReconciliation** -- Reconciliation data per session
- **DueBack** -- Per-receptionist DueBack entries
- **RJArchive** / **RJSheetData** -- Archived RJ data for historical access

(Defined in `database/models.py`; imported by `routes/audit/rj_native.py`)

---

## Migration Approach

- SQLAlchemy `db.create_all()` creates tables on application startup
- Schema changes are handled by adding columns with defaults (SQLite limitations)
- The `migrate_to_multiuser.py` script handles the auth migration and seeds initial users
- No formal migration framework (e.g. Alembic) is currently in use

---

## Global Constants

```python
TOTAL_ROOMS = 252  # Sheraton Laval property capacity
```

Used as default for `DailyJourMetrics.rooms_available` and occupancy calculations.
