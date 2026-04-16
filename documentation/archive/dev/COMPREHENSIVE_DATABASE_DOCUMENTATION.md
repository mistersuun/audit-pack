# Comprehensive Database Models & Analytics Documentation

**Last Updated:** February 22, 2026
**Scope:** Complete database schema, analytics queries, and data flow analysis

---

## TABLE OF CONTENTS

1. [All Database Models](#all-database-models)
2. [NightAuditSession Model — Detailed Column Reference](#nightauditsession-model--detailed-column-reference)
3. [DailyJourMetrics Model — Historical Analytics](#dailyjourmetrics-model--historical-analytics)
4. [Analytics Engine](#analytics-engine)
5. [Jour Sheet Importer](#jour-sheet-importer)
6. [Data Flow & Integration](#data-flow--integration)

---

## ALL DATABASE MODELS

### **User** (`users` table)
Authentication and multi-user role management.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `username` | String(100), unique | Login identifier |
| `email` | String(120), unique, nullable | Email address |
| `password_hash` | String(255) | Hashed password (werkzeug) |
| `role` | String(50), default='night_auditor' | Role: night_auditor, gm, gsm, front_desk_supervisor, accounting, admin |
| `full_name_fr` | String(200), nullable | Full name in French |
| `is_active` | Boolean, default=True | Account active status |
| `must_change_password` | Boolean, default=True | Password change required on next login |
| `last_login` | DateTime, nullable | Timestamp of last login |
| `created_at` | DateTime | Account creation timestamp |

**Methods:**
- `set_password(password)` — Hash and store password
- `check_password(password)` — Verify password hash
- `has_role(*roles)` — Check if user has any of specified roles
- `to_dict()` — Serialize to JSON

---

### **AuditSession** (`audit_sessions` table)
Legacy audit session tracking (minimal use in v2).

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `date` | Date, indexed | Audit date |
| `auditor_id` | Integer FK→users | Auditor user reference |
| `started_at` | DateTime | Session start time |
| `completed_at` | DateTime, nullable | Session completion time |
| `notes` | Text, nullable | Session notes |
| `rj_file_path` | String(500), nullable | Path to RJ file (if uploaded) |

---

### **DailyReport** (`daily_reports` table)
Consolidated daily revenue snapshot.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `date` | Date, unique, indexed | Report date (unique per day) |
| `revenue_comptant` | Float, default=0 | Cash revenue |
| `revenue_cartes` | Float, default=0 | Card revenue |
| `revenue_cheques` | Float, default=0 | Check revenue |
| `revenue_total` | Float, default=0 | Total revenue (computed) |
| `deposit_cdn` | Float, default=0 | CDN deposit amount |
| `deposit_us` | Float, default=0 | USD deposit amount |
| `variance` | Float, default=0 | Reconciliation variance |
| `dueback_total` | Float, default=0 | DueBack total (per receptionist) |
| `ar_balance` | Float, default=0 | Accounts receivable balance |
| `guest_ledger` | Float, default=0 | Guest ledger balance |
| `city_ledger` | Float, default=0 | City ledger balance |
| `auditor_name` | String(100), nullable | Auditor name |
| `created_at` | DateTime | Record creation timestamp |
| `updated_at` | DateTime | Record last update |
| `notes` | Text, nullable | Notes |

---

### **VarianceRecord** (`variance_records` table)
Per-receptionist daily variance tracking with alerts.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `date` | Date, indexed | Variance date |
| `receptionist` | String(100), indexed | Receptionist name |
| `expected` | Float, default=0 | Expected cash amount |
| `actual` | Float, default=0 | Actual cash counted |
| `variance` | Float, default=0 | Difference (actual - expected) |
| `notes` | Text, nullable | Variance explanation |
| `created_at` | DateTime | Record creation timestamp |

**Class Attributes:**
- `ALERT_THRESHOLD = 50.0` — Alert if variance exceeds ±$50

**Properties:**
- `is_alert` — Boolean: true if abs(variance) > $50

---

### **CashReconciliation** (`cash_reconciliations` table)
Daily cash drawer reconciliation.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `date` | Date, indexed | Reconciliation date |
| `system_total` | Float, default=0 | PMS system total |
| `counted_total` | Float, default=0 | Physical count total |
| `variance` | Float, default=0 | Difference |
| `auditor` | String(100), nullable | Auditor name |
| `notes` | Text, nullable | Notes |
| `created_at` | DateTime | Record creation timestamp |

**Methods:**
- `to_dict()` — Returns dict with `is_balanced` (true if variance < $0.01)

---

### **MonthEndChecklist** (`month_end_checklists` table)
Month-end closing tasks.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `year` | Integer | Year of month |
| `month` | Integer | Month (1-12) |
| `task_name` | String(200) | Task description |
| `completed` | Boolean, default=False | Completion status |
| `completed_at` | DateTime, nullable | Completion timestamp |
| `completed_by` | String(100), nullable | User who completed |
| `notes` | Text, nullable | Notes |

---

### **DailyJourMetrics** (`daily_jour_metrics` table)
**Historical daily metrics from RJ Jour sheet — 45+ KPIs, multi-year BI.**

One row per calendar day. Designed for historical analytics and dashboards spanning years.

#### Revenue Fields (11 columns)
| Column | Type | RJ Source | Description |
|--------|------|-----------|-------------|
| `room_revenue` | Float | Jour col 36 (AK) | Chambres (room revenue) |
| `fb_revenue` | Float | Computed | Sum of all F&B outlets |
| `cafe_link_total` | Float | Jour cols 4-8 | Café Link (pause/spesa) food+drink |
| `piazza_total` | Float | Jour cols 9-13 | Piazza/Cupola outlet |
| `spesa_total` | Float | Jour cols 14-18 | Marché Spesa marketplace |
| `room_svc_total` | Float | Jour cols 19-23 | Service aux Chambres (room service) |
| `banquet_total` | Float | Jour cols 24-28 | Banquet/events |
| `tips_total` | Float | Jour col 29 (AD) | Pourboires (tips) |
| `tabagie_total` | Float | Jour col 35 (AJ) | Tobacco/convenience shop |
| `other_revenue` | Float | Jour cols 30-48 | Equipment, internet, misc |
| `total_revenue` | Float | Computed | Room + F&B + other |

#### F&B Category Breakdown (5 columns)
| Column | Type | Description |
|--------|------|-------------|
| `total_nourriture` | Float | Food (across all outlets) |
| `total_boisson` | Float | Beverages (non-alcoholic + alcoholic) |
| `total_bieres` | Float | Beer |
| `total_vins` | Float | Wine |
| `total_mineraux` | Float | Mineral water/soft drinks |

#### Occupancy & Room Statistics (8 columns)
| Column | Type | RJ Source | Description |
|--------|------|-----------|-------------|
| `rooms_simple` | Integer | Jour col 88 (CK) | Single rooms sold |
| `rooms_double` | Integer | Jour col 89 (CL) | Double rooms sold |
| `rooms_suite` | Integer | Jour col 90 (CM) | Suite rooms sold |
| `rooms_comp` | Integer | Jour col 91 (CN) | Complimentary rooms |
| `total_rooms_sold` | Integer | Computed | simple + double + suite + comp |
| `rooms_available` | Integer | Jour col 95 (CR) or default=252 | Available rooms for sale |
| `occupancy_rate` | Float | Computed | % (0-100) |
| `nb_clients` | Integer | Jour col 92 (CO) | Guest count |
| `rooms_hors_usage` | Integer | Jour col 93 (CP) | Out of service |
| `rooms_ch_refaire` | Integer | Jour col 94 (CQ) | Rooms needing remake |

#### Payment Methods (7 columns)
| Column | Type | RJ Source | Description |
|--------|------|-----------|-------------|
| `visa_total` | Float | Jour col 63 (BL) | Visa volume |
| `mastercard_total` | Float | Jour col 62 (BK) | Mastercard volume |
| `amex_elavon_total` | Float | Jour col 60 (BI) | Amex ELAVON processor |
| `amex_global_total` | Float | Jour col 65 (BN) | Amex GLOBAL processor |
| `debit_total` | Float | Jour col 64 (BM) | Debit card volume |
| `discover_total` | Float | Jour col 61 (BJ) | Discover card volume |
| `total_cards` | Float | Computed | Sum of all card types |

#### Tax Fields (3 columns)
| Column | Type | RJ Source | Description |
|--------|------|-----------|-------------|
| `tps_total` | Float | Jour col 50 (AY) | Federal TPS (Canada) |
| `tvq_total` | Float | Jour col 49 (AX) | Provincial TVQ (Quebec) |
| `tvh_total` | Float | Jour col 51 (AZ) | Accommodation tax TVH |

#### Cash & Reconciliation (3 columns)
| Column | Type | RJ Source | Description |
|--------|------|-----------|-------------|
| `opening_balance` | Float | Jour col 1 | Cash opening balance |
| `cash_difference` | Float | Jour col 2 | Difference (counted - system) |
| `closing_balance` | Float | Jour col 3 | Ending cash balance |

#### Computed KPIs (5 columns)
| Column | Type | Formula | Description |
|--------|------|---------|-------------|
| `adr` | Float | room_revenue / rooms_sold | Average Daily Rate |
| `revpar` | Float | room_revenue / rooms_available | Revenue per Available Room |
| `trevpar` | Float | total_revenue / rooms_available | Total Revenue per Available Room |
| `food_pct` | Float | (total_nourriture / fb_revenue) × 100 | Food as % of F&B |
| `beverage_pct` | Float | (100 - food_pct) | Beverage as % of F&B |

#### Metadata (4 columns)
| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `date` | Date, unique, indexed | Calendar date |
| `year` | Integer, indexed | Year (for year-over-year queries) |
| `month` | Integer | Month (1-12) |
| `day_of_month` | Integer | Day of month (1-31) |
| `source` | String(20), default='rj_upload' | 'rj_upload' or 'bulk_import' |
| `rj_filename` | String(255), nullable | Original RJ filename for traceability |
| `created_at` | DateTime | Import timestamp |
| `updated_at` | DateTime | Last update timestamp |

**Methods:**
- `to_dict()` — Serialize to nested JSON with sections: date/time, revenue, fb_categories, occupancy, payments, taxes, kpis

---

### **MonthlyExpense** (`monthly_expenses` table)
Monthly operating expenses for GOPPAR/break-even analysis.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `year` | Integer | Year |
| `month` | Integer | Month (1-12) |
| `labor_rooms` | Float | Front office + housekeeping labor |
| `labor_fb` | Float | F&B staff labor |
| `labor_admin` | Float | Admin/management labor |
| `labor_maintenance` | Float | Engineering/maintenance labor |
| `labor_other` | Float | Other department labor |
| `labor_total` | Float | Auto-calculated |
| `utilities` | Float | Electricity, gas, water |
| `supplies` | Float | Amenities, cleaning, office supplies |
| `maintenance_costs` | Float | Repairs and preventive maintenance |
| `marketing` | Float | Marketing and sales expenses |
| `insurance` | Float | Property insurance |
| `franchise_fees` | Float | Marriott/Sheraton franchise fees |
| `technology` | Float | PMS, IT, telecom |
| `other_expenses` | Float | Miscellaneous |
| `total_expenses` | Float | Auto-calculated |
| `notes` | Text, nullable | Notes |
| `created_at` | DateTime | Record creation timestamp |
| `updated_at` | DateTime | Record last update |

**Unique Constraint:** `year + month`

**Methods:**
- `calculate_totals()` — Auto-sum labor and total expenses
- `to_dict()` — Serialize all fields to dict

---

### **DepartmentLabor** (`department_labor` table)
Monthly labor analytics by department with budget variance.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `year` | Integer | Year |
| `month` | Integer | Month |
| `department` | String(50) | Department: RECEPTION, KITCHEN, BANQUET, RESTAURANT, ADMINISTRATION, SALES, ROOMS, MAINTENANCE, BAR, OTHER |
| `regular_hours` | Float | Regular (non-OT) hours |
| `overtime_hours` | Float | Overtime hours |
| `total_hours` | Float | Regular + overtime |
| `regular_wages` | Float | Regular wage cost |
| `overtime_wages` | Float | OT wage cost (typically 1.5x) |
| `benefits` | Float | Benefits cost |
| `total_labor_cost` | Float | Wages + benefits |
| `headcount` | Integer | Number of employees |
| `avg_hourly_rate` | Float | total_labor_cost / total_hours |
| `tips_collected` | Float | Tips from POURBOIRE data |
| `tips_distributed` | Float | Tips paid to staff |
| `budget_hours` | Float | Budgeted hours |
| `budget_cost` | Float | Budgeted cost |
| `created_at` | DateTime | Record creation timestamp |
| `updated_at` | DateTime | Record last update |
| `notes` | Text, nullable | Notes |

**Unique Constraint:** `year + month + department`

**Methods:**
- `calculate_totals()` — Auto-sum hours and costs, calculate avg_hourly_rate
- `get_budget_variance()` — Returns actual_cost - budget_cost
- `get_budget_variance_pct()` — Variance as % of budget
- `get_hours_variance()` — Returns actual_hours - budget_hours
- `get_total_compensation()` — Returns labor_cost + tips_distributed
- `to_dict()` — Serialize with all computed variance fields

---

### **Task** (`tasks` table)
Front desk 46-step checklist items.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `order` | Integer | Task display order |
| `title_fr` | String(500) | Task title in French |
| `category` | String(100) | Category: pre_audit, part1, part2, end_shift |
| `role` | String(20), default='front' | Role: front, back |
| `is_active` | Boolean, default=True | Active/inactive status |
| `description_fr` | Text, nullable | Detailed description (why matters) |
| `steps_json` | Text, nullable | JSON array of step-by-step instructions |
| `screenshots_json` | Text, nullable | JSON array of screenshot filenames |
| `tips_fr` | Text, nullable | Helpful tips or warnings |
| `system_used` | String(100), nullable | System: Lightspeed, GXP, Espresso, etc. |
| `estimated_minutes` | Integer, nullable | Time estimate to complete |

**Methods:**
- `to_dict()` — Serialize with JSON parsing: steps array, screenshots array

---

### **Shift** (`shifts` table)
Nightly audit session metadata.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `date` | Date | Shift date |
| `started_at` | DateTime | Shift start time |
| `completed_at` | DateTime, nullable | Shift completion time |

**Relationships:**
- `completions` → TaskCompletion (one-to-many)

---

### **TaskCompletion** (`task_completions` table)
Tracks which front desk tasks are completed per shift.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `shift_id` | Integer FK→shifts | Shift reference |
| `task_id` | Integer FK→tasks | Task reference |
| `completed_at` | DateTime | Completion timestamp |
| `notes` | Text, nullable | Task notes |

**Unique Constraint:** `shift_id + task_id`

---

### **DailyReconciliation** (`daily_reconciliations` table)
Full daily reconciliation snapshot from RJ (Recap + GEAC + Transelect).

#### Recap Cash Section (16 columns)
| Column | Type | RJ Tab | Description |
|--------|------|--------|-------------|
| `audit_date` | Date, unique, indexed | — | Audit date |
| `auditor_name` | String(100) | Contrôle | Auditor name |
| `cash_lightspeed` | Float | Recap | Lightspeed cash lecture |
| `cash_positouch` | Float | Recap | POS Lightspeed cash lecture |
| `cash_correction` | Float | Recap | Cash correction amount |
| `cheque_ar` | Float | Recap | Check (accounts receivable) |
| `cheque_daily_rev` | Float | Recap | Check (daily revenue) |
| `remb_gratuite` | Float | Recap | Complimentary reimbursement |
| `remb_client` | Float | Recap | Client reimbursement |
| `remb_loterie` | Float | Recap | Lottery reimbursement |
| `exchange_us` | Float | Recap | USD exchange amount |
| `dueback_reception` | Float | Recap | DueBack reception line |
| `dueback_nb` | Float | Recap | DueBack night manager line |
| `surplus_deficit` | Float | Recap | Surplus/deficit line |
| `total_deposit_net` | Float | Recap | Net deposit total |
| `deposit_us` | Float | Recap | USD deposit |
| `deposit_cdn` | Float | Recap | CDN deposit |

#### Card Totals Section (10 columns)
| Column | Type | RJ Tab | Description |
|--------|------|--------|-------------|
| `card_visa_terminal` | Float | Transelect | Visa terminal total |
| `card_mc_terminal` | Float | Transelect | Mastercard terminal total |
| `card_amex_terminal` | Float | Transelect | Amex terminal total |
| `card_debit_terminal` | Float | Transelect | Debit terminal total |
| `card_discover_terminal` | Float | Transelect | Discover terminal total |
| `card_visa_bank` | Float | Transelect | Visa bank total |
| `card_mc_bank` | Float | Transelect | Mastercard bank total |
| `card_amex_bank` | Float | Transelect | Amex bank total |
| `card_debit_bank` | Float | Transelect | Debit bank total |
| `card_discover_bank` | Float | Transelect | Discover bank total |

**Properties:**
- `total_card_terminal` — Sum of all terminal cards
- `total_card_bank` — Sum of all bank cards

#### AR Balance Section (4 columns)
| Column | Type | RJ Tab | Description |
|--------|------|--------|-------------|
| `ar_previous` | Float | GEAC | Previous AR balance |
| `ar_charges` | Float | GEAC | Charges to AR |
| `ar_payments` | Float | GEAC | Payments from AR |
| `ar_new_balance` | Float | GEAC | New AR balance |

#### Variance Section (3 columns)
| Column | Type | Description |
|--------|------|-------------|
| `card_total_variance` | Float | Terminal - Bank card variance |
| `ar_variance` | Float | Expected AR - Actual AR |
| `is_balanced` | Boolean | True if all variances < $0.02 |

**Methods:**
- `calculate_variances()` — Compute card and AR variance, set is_balanced flag
- `to_dict()` — Serialize all columns to dict

---

### **JournalEntry** (`journal_entries` table)
Daily GL journal entries from RJ EJ sheet.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `audit_date` | Date, indexed | Entry date |
| `gl_code` | String(10), indexed | GL account code |
| `cost_center_1` | Float, nullable | Cost center 1 amount |
| `cost_center_2` | String(10), nullable | Cost center 2 code |
| `description_1` | String(200), nullable | Description line 1 |
| `description_2` | String(200), nullable | Description line 2 |
| `source` | String(20), nullable | Source system |
| `amount` | Float, default=0 | Entry amount |
| `created_at` | DateTime | Record creation timestamp |

**Unique Constraint:** `audit_date + gl_code`

---

### **DepositVariance** (`deposit_variances` table)
Daily deposit variance by employee from SD files.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `audit_date` | Date, indexed | Variance date |
| `department` | String(50), nullable | Department |
| `employee_name` | String(100) | Employee name |
| `currency` | String(5), default='CDN' | CDN or USD |
| `amount_declared` | Float | Employee declared amount |
| `amount_verified` | Float | Auditor verified amount |
| `reimbursement` | Float, default=0 | Reimbursement due to employee |
| `variance` | Float | Difference (declared - verified) |
| `created_at` | DateTime | Record creation timestamp |

**Unique Constraint:** `audit_date + employee_name`

**Methods:**
- `calculate_variance()` — Set variance = declared - verified

---

### **TipDistribution** (`tip_distributions` table)
Tip distribution per employee per pay period from POURBOIRE files.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `company_code` | Integer, nullable | Company/location code |
| `employee_id` | String(10), indexed | Employee ID |
| `employee_name` | String(100) | Employee name |
| `period_start` | Date, indexed | Pay period start date |
| `total_sales` | Float, default=0 | Total sales for period |
| `tip_amount` | Float, default=0 | Total tips distributed |
| `work_period_1` | Float | Period 1 tips (bi-weekly breakdown) |
| `work_period_2` | Float | Period 2 tips |
| `work_period_3` | Float | Period 3 tips |
| `work_period_4` | Float | Period 4 tips |
| `work_period_5` | Float | Period 5 tips |
| `work_period_6` | Float | Period 6 tips |
| `created_at` | DateTime | Record creation timestamp |

**Unique Constraint:** `period_start + employee_id`

---

### **HPDepartmentSales** (`hp_department_sales` table)
Monthly F&B sales breakdown by department from HP (Hotel Promotion) files.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `year` | Integer, indexed | Year |
| `month` | Integer, indexed | Month |
| `department` | String(50) | Department name |
| `food_sales` | Float | Food (NOURR) revenue |
| `beverage_sales` | Float | Beverage (BOISSON) revenue |
| `beer_sales` | Float | Beer (BIERE) revenue |
| `wine_sales` | Float | Wine (VIN) revenue |
| `mineral_sales` | Float | Mineral/soft drinks (MIN) revenue |
| `tips` | Float | Tips (POURB) collected |
| `tobacco_sales` | Float | Tobacco/convenience (TABAGIE) |
| `total_sales` | Float | Total sales |
| `admin_payment` | Float | Administration (14) payment |
| `hp_payment` | Float | Hotel Promotion (15) payment |
| `created_at` | DateTime | Record creation timestamp |

**Unique Constraint:** `year + month + department`

**Properties:**
- `calculated_total` — Sum of all category sales for validation

---

### **DueBack** (`due_backs` table)
Daily due-back balance per receptionist.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `audit_date` | Date, indexed | Audit date |
| `receptionist_name` | String(100) | Receptionist name |
| `balance` | Float, default=0 | DueBack balance (running total) |
| `entry_count` | Integer, default=0 | Number of DueBack entries |
| `created_at` | DateTime | Record creation timestamp |

**Unique Constraint:** `audit_date + receptionist_name`

---

## NIGHTAUDITSESSION MODEL — Detailed Column Reference

**Table:** `night_audit_sessions`
**Primary Key:** `id` (Integer)
**Unique Key:** `audit_date` (Date)

The NightAuditSession is the central model that captures all night audit data in a single database row, replacing the in-memory Excel RJ workbook. It has ~150 columns organized into 14 tabs matching the RJ native web app.

### Tab 1: Contrôle (4 columns)

| Column | Type | RJ Source | Description |
|--------|------|-----------|-------------|
| `audit_date` | Date, unique | Contrôle!B1 | Date of the audit (primary identifier) |
| `auditor_name` | String(100) | Contrôle!B2 | Name of night auditor |
| `temperature` | String(20) | Contrôle!B3 | Indoor temperature (manual entry) |
| `weather_condition` | String(50) | Contrôle!B4 | Weather description (manual entry) |
| `chambres_refaire` | Integer | Contrôle!B5 | Rooms needing remake (count) |
| `jours_dans_mois` | Integer | Contrôle!B6 | Days in month (auto-calculated from audit_date) |

### Recap Tab (18 columns: 8 pairs + 2 deposits)

**Structure:** Each recap line has LECTURE (read from system) + CORRECTION (auditor adjustment) → NET = LECTURE + CORRECTION

| Column | Type | Purpose |
|--------|------|---------|
| `cash_ls_lecture` | Float | Lightspeed cash — system reading |
| `cash_ls_corr` | Float | Lightspeed cash — auditor correction |
| `cash_pos_lecture` | Float | POS Lightspeed cash — system reading |
| `cash_pos_corr` | Float | POS Lightspeed cash — auditor correction |
| `cheque_ar_lecture` | Float | Check (AR) — system reading |
| `cheque_ar_corr` | Float | Check (AR) — auditor correction |
| `cheque_dr_lecture` | Float | Check (Daily Rev) — system reading |
| `cheque_dr_corr` | Float | Check (Daily Rev) — auditor correction |
| `remb_gratuite_lecture` | Float | Complimentary reimb — system reading |
| `remb_gratuite_corr` | Float | Complimentary reimb — auditor correction |
| `remb_client_lecture` | Float | Client reimbursement — system reading |
| `remb_client_corr` | Float | Client reimbursement — auditor correction |
| `dueback_reception_lecture` | Float | DueBack reception — system reading |
| `dueback_reception_corr` | Float | DueBack reception — auditor correction |
| `dueback_nb_lecture` | Float | DueBack night manager — system reading |
| `dueback_nb_corr` | Float | DueBack night manager — auditor correction |
| `deposit_cdn` | Float | CDN currency deposit envelope amount |
| `deposit_us` | Float | USD currency deposit envelope amount |
| `recap_balance` | Float | **COMPUTED:** Net (all corrections) - deposits |

**Computation Logic (in `calculate_all()`):**
```
recap_rows = [cash_ls_net, cash_pos_net, cheque_ar_net, cheque_dr_net]
recap_remb = [remb_gratuite_net, remb_client_net]
recap_dueback = [dueback_reception_net, dueback_nb_net]
cash_in = sum(recap_rows)
cash_out = sum(recap_remb) + sum(recap_dueback)
deposits = deposit_cdn + deposit_us
recap_balance = cash_in - cash_out - deposits
is_recap_balanced = abs(recap_balance) < 0.02
```

### DueBack Tab (JSON array + 1 scalar)

| Column | Type | Structure | Purpose |
|--------|------|-----------|---------|
| `dueback_entries` | Text (JSON) | Array of objects | Dynamic list of receptionists |
| `dueback_total` | Float | — | **COMPUTED:** Sum of nouveau values |

**JSON Structure:**
```json
[
  {
    "name": "Jean Dupont",
    "previous": 150.00,
    "nouveau": 145.00
  },
  {
    "name": "Marie Leblanc",
    "previous": 200.00,
    "nouveau": 190.00
  }
]
```

### Transelect Tab (4 columns + JSON structures)

| Column | Type | Structure | Purpose |
|--------|------|-----------|---------|
| `transelect_restaurant` | Text (JSON) | Nested dict | Restaurant terminal breakdown |
| `transelect_reception` | Text (JSON) | Nested dict | Reception card processor breakdown |
| `transelect_quasimodo` | Text (JSON) | Dict {card_type → total} | **AUTO-FILLED:** Card totals for Quasimodo |
| `transelect_variance` | Float | — | **COMPUTED:** Terminal variance |

**Restaurant JSON Structure:**
```json
{
  "fusebox": {
    "debit": 100.00,
    "visa": 500.00,
    "mc": 300.00,
    "amex": 200.00,
    "discover": 50.00,
    "total2": 1000.00,
    "positouch": 950.00,
    "esc_pct": 2.5
  },
  "term8": { ... },
  "k053": { ... }
}
```

**Reception JSON Structure:**
```json
{
  "debit": {
    "fusebox": 50.00,
    "term8": 30.00,
    "k053": 20.00,
    "daily_rev": 100.00,
    "esc_pct": 0.5
  },
  "visa": { ... },
  "mc": { ... },
  "amex": { ... },
  "discover": { ... }
}
```

**Transelect Quasimodo (auto-computed):**
```json
{
  "debit": 250.00,
  "visa": 1200.00,
  "mc": 800.00,
  "amex": 500.00,
  "discover": 150.00
}
```

### GEAC/UX Tab (7 columns + JSON structures)

| Column | Type | Structure | Purpose |
|--------|------|-----------|---------|
| `geac_cashout` | Text (JSON) | Dict {card_type → amount} | GEAC Cashout report by card |
| `geac_daily_rev` | Text (JSON) | Dict {card_type → amount} | GEAC Daily Revenue report by card |
| `geac_balance_sheet` | Text (JSON) | Complex dict | Full balance sheet snapshot |
| `geac_ar_previous` | Float | — | AR balance from yesterday |
| `geac_ar_charges` | Float | — | New AR charges today |
| `geac_ar_payments` | Float | — | AR payments received today |
| `geac_ar_new_balance` | Float | — | Expected AR balance today |
| `geac_ar_variance` | Float | — | **COMPUTED:** Expected - Actual |

**Computation Logic:**
```
ar_expected = ar_previous + ar_charges - ar_payments
geac_ar_variance = ar_expected - ar_new_balance
is_ar_balanced = abs(geac_ar_variance) < 0.02
```

### SD Tab (2 columns + JSON array)

| Column | Type | Structure | Purpose |
|--------|------|-----------|---------|
| `sd_entries` | Text (JSON) | Array of objects | Sommaire Journalier des Dépôts (daily deposit summary) |
| `sd_total_verified` | Float | — | **COMPUTED:** Sum of verified amounts |

**JSON Structure:**
```json
[
  {
    "department": "Restaurant",
    "name": "Chef",
    "currency": "CDN",
    "amount": 500.00,
    "verified": 495.00,
    "reimbursement": 5.00
  }
]
```

### Depot Tab (2 columns)

| Column | Type | Structure | Purpose |
|--------|------|-----------|---------|
| `depot_data` | Text (JSON) | Nested dict | Client envelope data (6 & 8) |
| `depot_total` | Float | — | **COMPUTED:** Sum of all envelope amounts |

**JSON Structure:**
```json
{
  "client6": {
    "date": "2026-02-22",
    "amounts": [100.00, 200.00, 150.00]
  },
  "client8": {
    "date": "2026-02-22",
    "amounts": [250.00, 300.00]
  }
}
```

### SetD Tab (2 columns + JSON array)

| Column | Type | Structure | Purpose |
|--------|------|-----------|---------|
| `setd_rj_balance` | Float | — | **AUTO-SET:** = recap_balance (for set-déjeuner reconciliation) |
| `setd_personnel` | Text (JSON) | Array of objects | Personnel set-déjeuner entries |

**JSON Structure:**
```json
[
  {
    "name": "Jean Dupont",
    "column_letter": "C",
    "amount": 25.00
  }
]
```

### HP/Admin Tab (2 columns + JSON array)

| Column | Type | Structure | Purpose |
|--------|------|-----------|---------|
| `hp_admin_entries` | Text (JSON) | Array of objects | Hotel Promotion & Admin F&B invoices |
| `hp_admin_total` | Float | — | **COMPUTED:** Sum of all categories across entries |

**JSON Structure:**
```json
[
  {
    "area": "Café Link",
    "nourriture": 100.00,
    "boisson": 50.00,
    "biere": 30.00,
    "vin": 40.00,
    "mineraux": 20.00,
    "autre": 10.00,
    "pourboire": 25.00,
    "raison": "Morning setup inventory",
    "autorise_par": "Manager Name"
  }
]
```

### Internet Tab (3 columns)

| Column | Type | Purpose |
|--------|------|---------|
| `internet_ls_361` | Float | CD 36.1 (Cashier Detail) from Lightspeed |
| `internet_ls_365` | Float | CD 36.5 (internet revenue) — **AUTO-PULLED** from jour_internet |
| `internet_variance` | Float | **COMPUTED:** 36.1 - 36.5 (should be ~0) |

### Sonifi Tab (3 columns)

| Column | Type | Purpose |
|--------|------|---------|
| `sonifi_cd_352` | Float | CD 35.2 (Cashier Detail) from Lightspeed |
| `sonifi_email` | Float | Email PDF amount from Sonifi — **AUTO-PULLED** from jour_sonifi |
| `sonifi_variance` | Float | **COMPUTED:** CD 35.2 - email amount (should be ~0) |

### Jour Tab (45+ columns organized by category)

#### F&B Revenue by Department × Category (25 columns)
5 departments (Café, Piazza, Spesa, Room Service, Banquet) × 5 categories (Food, Drink, Beer, Wine, Mineral)

```
jour_cafe_{nourriture,boisson,bieres,mineraux,vins}
jour_piazza_{nourriture,boisson,bieres,mineraux,vins}
jour_spesa_{nourriture,boisson,bieres,mineraux,vins}
jour_chambres_svc_{nourriture,boisson,bieres,mineraux,vins}
jour_banquet_{nourriture,boisson,bieres,mineraux,vins}
```

#### F&B Extra (3 columns)

| Column | Type | Description |
|--------|------|-------------|
| `jour_pourboires` | Float | Tips (Pourboires) |
| `jour_tabagie` | Float | Tobacco/convenience store |
| `jour_location_salle` | Float | Hall/room rental |

#### Hébergement/Room Section (4 columns)

| Column | Type | Description |
|--------|------|-------------|
| `jour_room_revenue` | Float | Room revenue from Daily Revenue report |
| `jour_tel_local` | Float | Local telephone revenue |
| `jour_tel_interurbain` | Float | Long distance telephone |
| `jour_tel_publics` | Float | Public phone revenue |

#### G4 Forfait Section (3 columns)
Special handling for "Forfait" (package rate adjustment).

| Column | Type | Purpose |
|--------|------|---------|
| `jour_forfait_sj` | Float | Forfait amount from Sales Journal (negative) |
| `g4_montant` | Float | G4 adjustment (manual entry, propagates to room revenue) |
| `jour_diff_forfait` | Float | **COMPUTED:** forfait_sj + g4_montant |

#### Autres Revenus (9 columns)
Other/miscellaneous revenue.

```
jour_nettoyeur        # Housekeeping extra
jour_machine_distrib  # Vending machines
jour_autres_gl        # Other GL entries
jour_sonifi          # Sonifi in-room entertainment
jour_lit_pliant      # Rollaway bed rental
jour_boutique        # Gift shop
jour_internet        # Internet revenue
jour_massage         # Spa/massage revenue
jour_diff_forfait    # Forfait difference (computed)
```

#### Taxes (3 columns)

| Column | Type | Description |
|--------|------|-------------|
| `jour_tvq` | Float | Provincial TVQ tax |
| `jour_tps` | Float | Federal TPS tax |
| `jour_taxe_hebergement` | Float | Accommodation tax (TVH) |

#### Règlements/Payment Methods (2 columns)

| Column | Type | Description |
|--------|------|-------------|
| `jour_gift_cards` | Float | Gift card redemptions |
| `jour_certificats` | Float | Certificate redemptions |

#### Occupation (6 columns)

| Column | Type | Description |
|--------|------|-------------|
| `jour_rooms_simple` | Integer | Single rooms sold |
| `jour_rooms_double` | Integer | Double rooms sold |
| `jour_rooms_suite` | Integer | Suite rooms sold |
| `jour_rooms_comp` | Integer | Complimentary rooms |
| `jour_nb_clients` | Integer | Guest count |
| `jour_rooms_hors_usage` | Integer | Rooms out of service |

#### Special Values (3 columns)

| Column | Type | Description |
|--------|------|-------------|
| `jour_club_lounge` | Float | Club lounge revenue |
| `jour_deposit_on_hand` | Float | Deposits on hand |
| `jour_ar_misc` | Float | A/R miscellaneous |

#### Computed Totals (4 columns)

| Column | Type | Formula |
|--------|------|---------|
| `jour_total_fb` | Float | Sum of all F&B + tips + tabagie + hall rental |
| `jour_total_revenue` | Float | F&B + room (with G4) + telephones + autres + taxes + reglements + special |
| `jour_adr` | Float | (room_rev + g4) / rooms_sold |
| `jour_revpar` | Float | (room_rev + g4) / (252 - hors_usage) |
| `jour_occupancy_rate` | Float | rooms_sold / (252 - hors_usage) × 100 |

### Quasimodo Tab (11 columns + 1 JSON)

**Global reconciliation: all card types (restaurant + reception) + cash vs Jour total revenue**

| Column | Type | Purpose |
|--------|------|---------|
| `quasi_fb_debit` | Float | Debit cards from restaurant (Transelect) |
| `quasi_fb_visa` | Float | Visa cards from restaurant |
| `quasi_fb_mc` | Float | Mastercard from restaurant |
| `quasi_fb_amex` | Float | Amex from restaurant |
| `quasi_fb_discover` | Float | Discover from restaurant |
| `quasi_rec_debit` | Float | Debit cards from reception (Transelect) |
| `quasi_rec_visa` | Float | Visa cards from reception |
| `quasi_rec_mc` | Float | Mastercard from reception |
| `quasi_rec_amex` | Float | Amex from reception |
| `quasi_rec_discover` | Float | Discover from reception |
| `quasi_amex_factor` | Float | AMEX fee factor (default 0.9735) |
| `quasi_cash_cdn` | Float | **AUTO-FILLED:** = deposit_cdn |
| `quasi_cash_usd` | Float | **AUTO-FILLED:** = deposit_us |
| `quasi_total` | Float | **COMPUTED:** All cards (with AMEX factor) + cash |
| `quasi_rj_total` | Float | **AUTO-SET:** = jour_total_revenue |
| `quasi_variance` | Float | **COMPUTED:** quasi_total - quasi_rj_total (should be ±$0.01) |

**Computation Logic:**
```
for each card_type in [debit, visa, mc, amex, discover]:
  quasi[card] = rest_total[card] + rec_total[card]

amex_net = (quasi_fb_amex + quasi_rec_amex) × quasi_amex_factor
amex_gross = quasi_fb_amex + quasi_rec_amex
non_amex = (sum all cards) - amex_gross
quasi_total = non_amex + amex_net + quasi_cash_cdn + quasi_cash_usd
quasi_variance = quasi_total - jour_total_revenue
```

### DBRS Tab (4 columns + 1 JSON)

**Daily Business Review Summary for Marriott corporate reporting**

| Column | Type | Purpose |
|--------|------|---------|
| `dbrs_market_segments` | Text (JSON) | Dict {transient, group, contract, other} |
| `dbrs_daily_rev_today` | Float | **AUTO-FILLED:** = jour_room_revenue |
| `dbrs_adr` | Float | **AUTO-FILLED:** = jour_adr |
| `dbrs_house_count` | Integer | **AUTO-FILLED:** = rooms_sold |
| `dbrs_otb_data` | Text (JSON) | On-The-Books future data (not yet wired) |
| `dbrs_noshow_count` | Integer | No-show room count |
| `dbrs_noshow_revenue` | Float | Revenue lost to no-shows |

### Balance Flags (3 columns)

| Column | Type | Description |
|--------|------|-------------|
| `is_recap_balanced` | Boolean | True if abs(recap_balance) < $0.02 |
| `is_transelect_balanced` | Boolean | True if abs(transelect_variance) < $1.00 |
| `is_ar_balanced` | Boolean | True if abs(geac_ar_variance) < $0.02 |
| `is_fully_balanced` | Boolean | True if all three above are true |

### Metadata (5 columns)

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `status` | String(20), default='draft' | draft, in_progress, submitted, locked |
| `started_at` | DateTime | Session start time |
| `completed_at` | DateTime, nullable | Session completion time |
| `notes` | Text | Auditor notes |
| `created_at` | DateTime | Record creation timestamp |

### Methods

**`get_json(field)`** — Safe JSON parse
- Returns parsed dict/list or empty {} / []
- Handles JSONDecodeError gracefully

**`set_json(field, data)`** — Safe JSON serialize
- Uses ensure_ascii=False for French characters

**`calculate_all()`** — Run all 13 balance calculations
1. Auto-set `jours_dans_mois` from audit_date
2. Calculate G4 propagation: `jour_diff_forfait = jour_forfait_sj + g4_montant`
3. **Recap balance**: cash_in - cash_out - deposits
4. **Transelect variance**: Terminal vs Bank per card type
5. **GEAC AR variance**: Expected vs Actual AR
6. **DueBack total**: Sum of nouvelles
7. **SD total verified**: Sum of verified amounts
8. **Depot total**: Sum of envelope amounts
9. **SetD RJ balance**: Auto-set = recap_balance
10. **Jour totals**: Total F&B, total revenue, occupancy %, ADR, RevPAR
11. **HP/Admin total**: Sum of all expense categories
12. **Internet variance**: CD 36.1 - 36.5
13. **Sonifi variance**: CD 35.2 - email amount
14. **Quasimodo**: Auto-fill from Transelect + Recap, compute with AMEX factor
15. **DBRS**: Auto-fill from Jour
16. **Overall balance flags**: Set is_fully_balanced

**`to_dict()`** — Serialize to JSON
- All scalar columns as-is
- All JSON columns parsed to dict/list
- DateTime fields as isoformat strings

---

## DAILYJOURMETRICS MODEL — HISTORICAL ANALYTICS

See [DailyJourMetrics section above](#dailyjourmetrics--daily_jour_metrics-table) for complete column reference.

### Key Points
- **~45 metrics per day** covering revenue, occupancy, payments, taxes
- **Multi-year queryable** via date range filters
- **Pre-computed KPIs** (ADR, RevPAR, TRevPAR, food%, beverage%)
- **Designed for BI dashboards** and historical trend analysis
- **Updated via JourImporter** when RJ files are uploaded

---

## ANALYTICS ENGINE

### HistoricalAnalytics Class

**Location:** `/utils/analytics.py` lines 1056–1299

Multi-month/multi-year analytics on DailyJourMetrics table. Returns same format as JourAnalytics for dashboard compatibility.

#### Constructor
```python
HistoricalAnalytics(start_date, end_date)
```
Queries DailyJourMetrics for date range, returns ordered list.

#### Methods

**`has_data()`**
Returns boolean if any metrics in range.

**`get_executive_kpis()`**
Returns dict with:
- `days_count`, `total_revenue`, `avg_daily_revenue`
- `room_revenue`, `fb_revenue`, `other_revenue`
- `adr`, `revpar`, `trevpar`, `occupancy_rate`
- `rooms_sold`, `rooms_available`, `rooms_comp`, `total_clients`, `avg_clients_per_day`
- `total_cards`, `total_taxes`, `total_tps`, `total_tvq`, `total_tvh`

**Queries:**
- `m.room_revenue` — Direct column query
- `m.total_rooms_sold` — Direct column query
- `m.rooms_available` — Direct column query
- `m.nb_clients` — Direct column query
- `m.total_cards` — Direct column query
- `m.tps_total`, `m.tvq_total`, `m.tvh_total` — Tax totals

**`get_revenue_trend()`**
Daily revenue line with date. Returns array of:
- `day`, `date`, `room_revenue`, `fb_revenue`, `other_revenue`, `total`
- `occupancy`, `adr`, `revpar`

**Queries:**
- `m.day_of_month` — Direct column
- `m.date` — Direct column
- `m.room_revenue`, `m.fb_revenue`, `m.other_revenue` — Direct columns

**`get_fb_analytics()`**
F&B breakdown by outlet + category totals.

**Queries:**
```python
outlets['Café Link']['total'] += m.cafe_link_total
outlets['Piazza/Cupola']['total'] += m.piazza_total
outlets['Marché Spesa']['total'] += m.spesa_total
outlets['Room Service']['total'] += m.room_svc_total
outlets['Banquet']['total'] += m.banquet_total

total_nour = sum(m.total_nourriture for m in self.metrics)
total_boi = sum(m.total_boisson ...)
total_bie = sum(m.total_bieres ...)
total_min = sum(m.total_mineraux ...)
total_vin = sum(m.total_vins ...)
```

**Returns:**
```python
{
  'outlets': {
    'Café Link': {'total': X, 'categories': {}},
    'Piazza/Cupola': {...},
    ...
  },
  'category_totals': {
    'Nourriture': X, 'Alcool': Y, 'Bières': Z, 'Minéraux': W, 'Vins': V
  },
  'total_fb': sum_of_categories,
  'food_pct': (nourriture / total_fb) * 100,
  'beverage_pct': 100 - food_pct,
  'trend': [],  # Simplified for large ranges
  'other': {'pourboires': X, 'tabagie': Y}
}
```

**`get_room_analytics()`**
Room mix, occupancy, ADR trends.

**Queries:**
```python
total_sold = sum(m.total_rooms_sold for m in self.metrics)
total_avail = sum(m.rooms_available ...)
total_simple = sum(m.rooms_simple ...)
total_double = sum(m.rooms_double ...)
total_suite = sum(m.rooms_suite ...)
total_comp = sum(m.rooms_comp ...)
```

**Returns:**
```python
{
  'trend': [
    {
      'day': day_num, 'date': iso_date,
      'simple': int, 'double': int, 'suite': int, 'comp': int,
      'sold': int, 'available': int, 'occupancy': pct, 'adr': float
    }
  ],
  'summary': {
    'avg_occupancy': pct,
    'total_rooms_sold': int,
    'room_mix': {'simple': int, 'double': int, 'suite': int, 'comp': int},
    'room_mix_pct': {...},
    'avg_clients': float,
    'avg_hors_usage': float
  }
}
```

**`get_payment_analytics()`**
Payment method breakdown.

**Queries:**
```python
cards = {
  'Visa': sum(m.visa_total for m in self.metrics),
  'Mastercard': sum(m.mastercard_total ...),
  'Amex ELAVON': sum(m.amex_elavon_total ...),
  'Amex GLOBAL': sum(m.amex_global_total ...),
  'Débit': sum(m.debit_total ...),
  'Discover': sum(m.discover_total ...)
}
```

**Returns:**
```python
{
  'breakdown': {
    'Visa': {'amount': float, 'pct': float},
    'Mastercard': {...},
    ...
  },
  'total': float,
  'trend': [],  # Empty for multi-month ranges
  'avg_escrow_pct': {}  # Not available in DB
}
```

**`get_tax_analytics()`**
Tax totals and daily averages.

**Queries:**
```python
totals = {
  'tps': sum(m.tps_total ...),
  'tvq': sum(m.tvq_total ...),
  'tvh': sum(m.tvh_total ...)
}
```

**Returns:**
```python
{
  'totals': {'tps': float, 'tvq': float, 'tvh': float, 'total': float},
  'trend': [],  # Empty
  'avg_daily': {'tps': float, 'tvq': float, 'tvh': float, 'total': float}
}
```

**`get_anomalies()`**
Alert detection (low occupancy, high cash variance).

**Queries:**
```python
avg_occ = sum(m.occupancy_rate ...) / len(self.metrics)
avg_adr = sum(m.adr ...) / len(self.metrics)
avg_fb = sum(m.fb_revenue ...) / len(self.metrics)

for m in self.metrics:
  if m.occupancy_rate < avg_occ * 0.7:
    alerts.append(...)
  if abs(m.cash_difference) > 50:
    alerts.append(...)
```

---

## JOUR SHEET IMPORTER

### JourImporter Class

**Location:** `/utils/jour_importer.py` lines 49–461

Extract daily metrics from RJ Jour sheet and persist to DailyJourMetrics.

#### Static Methods

**`extract_from_rj(file_bytes, filename=None)`**
Read Jour sheet from RJ file.

**Returns:** `(list[DailyJourMetrics], info_dict)`

**Process:**
1. Open XLS file (tries Jour, jour, JOUR sheet names)
2. Read month/year from Contrôle sheet (rows B4, B5)
3. Parse filename for date if needed (supports YYYYMMDD, DD-MM-YYYY, French month names)
4. Loop through rows 1–32 (days)
5. For each day with data, read all JOUR_COLS into dict
6. Call `_map_to_model(day_data, date, filename)` to create DailyJourMetrics
7. Return list of metrics + metadata

**`persist_batch(metrics, source='rj_upload')`**
Upsert metrics to database.

**Returns:** `{'inserted': N, 'updated': N, 'total': N}`

**Logic:**
- For each metric, check if DailyJourMetrics with same date exists
- If exists: update all fields via `_update_existing()`
- If new: insert via `db.session.add()`
- Commit once

**`get_data_status()`**
Get summary of historical data range.

**Returns:**
```python
{
  'total_days': int,
  'date_range': {'from': iso_date, 'to': iso_date},
  'years_covered': int,
  'months_with_data': [{'year': int, 'month': int}, ...]
}
```

**Queries:**
```python
total = DailyJourMetrics.query.count()
min_date = db.session.query(db.func.min(DailyJourMetrics.date)).scalar()
max_date = db.session.query(db.func.max(DailyJourMetrics.date)).scalar()
months = db.session.query(DailyJourMetrics.year, DailyJourMetrics.month).distinct().all()
```

#### Private Helpers

**`_read_controle_date(wb)`**
Extract month/year from Contrôle sheet.

**Returns:** `(month, year)` tuple or (None, None)

**`_parse_filename_date(filename)`**
Parse date from filename patterns.

**Supports:**
- YYYYMMDD, YYYY-MM-DD, YYYY_MM_DD
- DD-MM-YYYY, DD/MM/YYYY, DD_MM_YYYY
- French month names: janvier, février, mars, ... décembre

**`_cell(sheet, row, col)`**
Safe cell read from xlrd sheet.

**`_map_to_model(day_data, day_date, filename=None)`**
Map parsed day_data dict to DailyJourMetrics ORM object.

**Process:**
1. Sum outlet columns per F&B outlet (Café Link, Piazza, Spesa, Room Service, Banquet)
2. Sum category columns (Food, Boisson, Bières, Vins, Minéraux across all outlets)
3. Calculate room stats: simple + double + suite + comp = total sold
4. Calculate occupancy: sold / available × 100
5. Sum payment columns by type (Visa, MC, Amex, Debit, Discover)
6. Calculate KPIs: ADR = room_rev / sold, RevPAR = room_rev / avail, TRevPAR = total_rev / avail

**Fields Mapped:**
```python
return DailyJourMetrics(
  date=day_date, year=..., month=..., day_of_month=...,
  room_revenue=chambres,
  fb_revenue=sum_of_outlets,
  cafe_link_total=sum(cafe_link_cols),
  piazza_total=sum(piazza_cols),
  spesa_total=sum(spesa_cols),
  room_svc_total=sum(room_svc_cols),
  banquet_total=sum(banquet_cols),
  tips_total=pourboires,
  tabagie_total=tabagie,
  other_revenue=sum(misc_cols),
  total_revenue=room_rev + fb_rev + tips + tabagie + other,
  total_nourriture=sum_food,
  total_boisson=sum_drink,
  total_bieres=sum_beer,
  total_vins=sum_wine,
  total_mineraux=sum_mineral,
  rooms_simple=int(rooms_simple),
  rooms_double=int(rooms_double),
  rooms_suite=int(rooms_suite),
  rooms_comp=int(rooms_comp),
  total_rooms_sold=sum_sold,
  rooms_available=disponible or 252,
  occupancy_rate=pct,
  nb_clients=int(nb_clients),
  rooms_hors_usage=hors_usage,
  rooms_ch_refaire=ch_refaire,
  # Payments...
  visa_total=visa,
  mastercard_total=mc,
  amex_elavon_total=amex_elavon,
  amex_global_total=amex_global,
  debit_total=debit,
  discover_total=discover,
  total_cards=sum_cards,
  # Taxes...
  tps_total=tps,
  tvq_total=tvq,
  tvh_total=tvh,
  # Cash...
  opening_balance=bal_ouv,
  cash_difference=diff_caisse,
  closing_balance=new_balance,
  # KPIs...
  adr=room_rev / sold,
  revpar=room_rev / avail,
  trevpar=total_rev / avail,
  food_pct=(nourriture / fb_revenue) × 100,
  beverage_pct=(boisson+bie+vin+min / fb_revenue) × 100,
  rj_filename=filename
)
```

**`_update_existing(existing, new_metrics)`**
Update existing DailyJourMetrics record.

**Fields Updated:**
- All revenue fields
- All occupancy/room fields
- All payment fields
- All tax fields
- All cash fields
- All KPI fields
- source, rj_filename, updated_at

---

## DATA FLOW & INTEGRATION

### Import Flow: RJ File → Database

```
RJ File (Excel .xls)
    ↓
[JourImporter.extract_from_rj()]
    ↓
- Reads Jour sheet (117 columns)
- Parses 31 days of data
- Maps to ~45 daily metrics
    ↓
[JourImporter.persist_batch()]
    ↓
DailyJourMetrics table
    ↓
```

### Native Web Form Flow: Frontend → NightAuditSession

```
Frontend (rj_native.html)
    ↓
[autoSave → debounceSave(section)]
    ↓
[POST /api/rj/native/save/{section}]
    ↓
NightAuditSession (14 endpoints, one per tab)
    ↓
- Tab 1: save/controle
- Tab 2: save/dueback
- Tab 3: save/recap
- Tab 4: save/transelect
- Tab 5: save/geac
- Tab 6: save/sd
- Tab 7: save/depot
- Tab 8: save/setd
- Tab 9: save/hp_admin
- Tab 10: save/internet
- Tab 11: save/sonifi
- Tab 12: save/jour
- Tab 13: save/quasimodo
- Tab 14: save/dbrs
    ↓
[POST /api/rj/native/calculate]
    ↓
NightAuditSession.calculate_all()
    ↓
- Computes all 13 balance checks
- Sets computed fields
- Updates balance flags
    ↓
[POST /api/rj/native/submit/<date>]
    ↓
- Locks session (status='locked')
- Final validation
    ↓
```

### Historical Analytics Flow

```
DailyJourMetrics table (many dates)
    ↓
[HistoricalAnalytics(start_date, end_date)]
    ↓
[Query range filter + grouping]
    ↓
[get_executive_kpis(), get_fb_analytics(), get_room_analytics(), etc.]
    ↓
Dashboard API response (same format as JourAnalytics)
    ↓
```

### What Data is LOST in Import Process

The jour_importer.py has some limitations:

1. **Escrow percentages (escrow_* fields in Jour)** — Not imported to DailyJourMetrics
   - Escrow pct is in Jour columns 96–99 (esc_amex, esc_diners, esc_master, esc_visa)
   - These are computed in JourAnalytics but NOT stored in DB
   - HistoricalAnalytics has no escrow data, so `avg_escrow_pct` returns empty {}

2. **Net card amounts (net_* fields)** — Not imported
   - Jour columns 100–103 have net card amounts after fees
   - Not mapped to DailyJourMetrics

3. **Detailed POS totals** — Only aggregated
   - Jour columns 110–116 have detailed food/beverage/beer/wine totals by outlet
   - JourImporter recalculates from outlet cols (4–28), doesn't use these direct totals
   - Could cause minor discrepancies if calculations differ

4. **HP/Admin, SetD data** — Not imported
   - These are entered in the native web form, not in the Jour sheet
   - No historical tracking of HP invoices or personnel set-déjeuner

5. **SD (Sommaire Journalier)** — Not imported
   - Employee deposit data from SD files
   - No daily historical tracking

6. **DBRS data** — Partially imported
   - Only market segments and OTB (on-the-books) are stored as JSON
   - No historical tracking of no-show counts/revenue

7. **DateTime data** — Not stored in DailyJourMetrics
   - The Jour sheet may have time stamps (e.g., Part execution time)
   - Only date is stored, not time-of-day

### Missing Data in DailyJourMetrics

**Fields NOT stored but queried in JourAnalytics:**
- Cash balance fields (bal_ouv, diff_caisse, new_balance) — ARE stored ✓
- Escrow percentages — NOT stored ✗
- Net card amounts — NOT stored ✗
- Detailed terminal breakdowns — NOT stored (only aggregated) ✗
- Historical escrow rate trends — Cannot compute ✗

**Impact:**
- HistoricalAnalytics cannot return `avg_escrow_pct` (returns empty dict)
- HistoricalAnalytics cannot compute processing cost detail
- Historical variance in card processing rates is lost

---

## SUMMARY TABLE: Field Sources

| Model | Source | Fields | Volume |
|-------|--------|--------|--------|
| **NightAuditSession** | Native web form | 150 columns across 14 tabs | Per audit night |
| **DailyJourMetrics** | RJ Jour sheet import | 45 metrics | Per calendar day, multi-year |
| **DailyReport** | Manual/automated | Revenue summary | Per day |
| **VarianceRecord** | Manual entry | Receptionist variance | Per receptionist per day |
| **CashReconciliation** | Manual entry | Cash count vs PMS | Per day |
| **DailyReconciliation** | RJ file (Recap, GEAC, Transelect) | 30+ reconciliation fields | Per audit night |
| **JournalEntry** | RJ EJ sheet | GL entries | Per audit night |
| **DepositVariance** | RJ SD sheet | Employee deposits | Per employee per day |
| **TipDistribution** | POURBOIRE file | Employee tips | Per employee per pay period |
| **HPDepartmentSales** | RJ HP sheet | Department F&B | Per department per month |
| **DueBack** | RJ DueBack sheet | Receptionist balances | Per receptionist per day |

---

## References

- **Models Definition:** `/database/models.py` (1265 lines)
- **Analytics Engine:** `/utils/analytics.py` (1299 lines)
- **Jour Importer:** `/utils/jour_importer.py` (461 lines)
- **RJ Native Frontend:** `/templates/audit/rj/rj_native.html` (~1800 lines)
- **Backend Routes:** `/routes/audit/rj_native.py` (REST API endpoints)
