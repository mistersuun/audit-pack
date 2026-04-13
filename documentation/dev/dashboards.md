# Webapp Dashboards Reference

Complete reference for all dashboard pages in the Night Audit webapp.
Each entry documents the page route, role access, template, API endpoints, and data sources.

---

## Navigation Structure

The sidebar navigation in `templates/base.html` is role-based, controlled by `session.user_role_type`.

### Auditor + Admin Sidebar (`night_auditor`, `front_desk_supervisor`, `admin`)

| Section       | Label              | Route                  |
|---------------|--------------------|------------------------|
| --            | Dashboard          | `/dashboard`           |
| Outils        | Checklist (Front)  | `/checklist?role=front` |
| Outils        | Checklist (Back)   | `/checklist?role=back`  |
| Outils        | Documentation      | `/documentation`       |
| Outils        | Rapport Journalier | `/rj/native`           |
| Outils        | CRM (7 tabs)       | `/crm`                 |
| Outils        | Previsions         | `/previsions`          |
| Outils        | STR & OTB          | `/compset`             |
| Outils        | Generateurs        | `/generators`          |

### Direction Sidebar (`gm`, `gsm`, `accounting`)

| Section       | Label              | Route                  |
|---------------|--------------------|------------------------|
| --            | Tableau de bord    | `/direction`           |
| Rapports      | Rapport Journalier | `/direction#rj`        |
| Rapports      | Rapports Direction | `/direction#reports`   |
| Rapports      | Tendances          | `/direction#trends`    |
| Rapports      | Budget & Ecarts    | `/budget`              |
| Analyse       | Portfolio          | `/portfolio`           |
| Analyse       | Analytics          | `/manager`             |
| Analyse       | STR & OTB          | `/compset`             |
| Ressources    | Documentation      | `/documentation`       |

### Admin-Only Extras (appended after auditor sidebar)

| Section       | Label              | Route                  |
|---------------|--------------------|------------------------|
| Direction     | Analytics          | `/manager`             |
| Direction     | Portail Direction  | `/direction`           |
| Direction     | Portfolio          | `/portfolio`           |
| Direction     | Proprietes         | `/properties`          |

### Shared (all authenticated users)

| Section       | Label              | Route                  |
|---------------|--------------------|------------------------|
| Support       | FAQ                | `/faq`                 |
| Support       | Notifications      | `/notifications` (direction/admin only) |

---

## Auditor Dashboards

### Smart Dashboard (`/dashboard`)

- **Route:** `GET /dashboard`
- **Blueprint:** `dashboard_bp` (`routes/dashboard.py`)
- **Decorator:** `@login_required` (all authenticated users)
- **Template:** `dashboard.html`
- **API:** `GET /api/dashboard/smart`

#### Sections returned by `/api/dashboard/smart`

| Section       | Key              | Description                                                     |
|---------------|------------------|-----------------------------------------------------------------|
| Tonight KPIs  | `today`          | Occupancy, ADR, RevPAR, room/FB/total revenue, rooms sold, comp, OOS |
| Comparisons   | `comparisons`    | vs Yesterday, vs Same DOW last week, vs 30-day average (with delta %) |
| Sparklines    | `sparklines`     | Last 7 days of occupancy, ADR, RevPAR, revenue                 |
| Cash Recon    | `cash`           | Quasimodo variance, surplus/deficit, deposits, auditor name     |
| Labor         | `labor`          | Month total/prorated labor cost, revenue, labor %, partial-month flag |
| Card Mix      | `card_data`      | Total card volume, AMEX % (embedded in threshold alerts)        |
| Alerts        | `alerts`         | Threshold-based alerts (critical/warning/info/success) across occupation, ADR, RevPAR, F&B, cash, labor, cards, trends |
| Shift Progress| `shift`          | Current shift task completion count and % progress              |
| RJ Status     | `rj`             | Tonight's NightAuditSession status (draft/in_progress/locked)   |
| Weather       | `weather`        | Temperature + condition from latest NightAuditSession           |
| MTD Summary   | `mtd`            | Month-to-date avg occupancy, ADR, total revenue                 |
| Budget        | `budget`         | Prorated monthly budget vs actual variance                      |
| Meta          | `meta`           | Total days in DB, date range from/to                            |

#### Threshold Engine

Defined in `THRESHOLDS` dict at top of `routes/dashboard.py`. Categories:
- `occupation` -- critical < 45%, warning < 60%, success > 90%
- `adr` -- below/above 15% of 30-day average
- `revpar` -- below 20% of average
- `fb` -- F&B per client < $12 warning, > $25 success
- `cash` -- Quasimodo abs > $5/$10, surplus/deficit abs > $20/$50
- `labor` -- labor % > 32% warning, > 38% critical
- `cards` -- AMEX % > 30% info
- `trends` -- 3-day occ drop > 10pts, 7-day ADR drop > $8, 7-day F&B drop > 15%

#### Data Sources

`DailyJourMetrics`, `DailyCashRecon`, `DailyCardMetrics`, `DepartmentLabor`, `MonthlyBudget`, `NightAuditSession`, `Shift`, `Task`, `TaskCompletion`

---

### Auditor Panel Widget

- **API:** `GET /api/dashboard/auditor-panel`
- **Decorator:** `@login_required`
- **Query param:** `?date=YYYY-MM-DD` (defaults to tonight's audit date, yesterday if before 07:00)

Embedded within the auditor dashboard. Returns three sections:

| Section              | Key                  | Description                                                   |
|----------------------|----------------------|---------------------------------------------------------------|
| Balance Grid         | `balance_grid`       | 4 balance checks: Recap (0.02$), Transelect (1.00$), AR GEAC (0.02$), Quasimodo (5.00$). Each has status green/red/pending |
| Outstanding Items    | `outstanding_items`  | Priority-sorted issues: RECAP, TRANSELECT, AR_GEAC, QUASIMODO, GL_101100, GL_100401, INTERNET, SONIFI, SUBMISSION |
| Variance Alerts      | `variance_alerts`    | Quasimodo variance with 7-day rolling avg context, surplus/deficit, AR variance |

#### Data Sources

`NightAuditSession` (current + prior night), `DailyCashRecon` (7-day rolling)

---

### CRM Analytics (`/crm`)

- **Route:** `GET /crm`
- **Blueprint:** `crm_bp` (`routes/crm.py`)
- **Decorator:** `@login_required`
- **Template:** `crm.html`
- **Query param:** `?tab=overview|revenue|fb|labor|cash|payments|pnl`

7-tab BI analytics dashboard. See `bi_crossref.md` for detailed per-tab column mappings.

| Tab          | Label           | Key API Endpoints                                          |
|--------------|-----------------|------------------------------------------------------------|
| `overview`   | Vue d'ensemble  | `/api/crm/dashboard`, `/api/crm/kpis`, `/api/crm/data-status` |
| `revenue`    | Revenue Mgmt    | `/api/crm/revenue-trend`, `/api/crm/revenue-opportunities`, `/api/crm/advanced-kpis` |
| `fb`         | F&B Intelligence| `/api/crm/fb-analytics`                                    |
| `labor`      | Main-d'oeuvre   | `/api/crm/staff`                                           |
| `cash`       | Cash & Recon    | `/api/crm/variances` (GET + POST), `/api/crm/anomalies`   |
| `payments`   | Paiements       | `/api/crm/payment-analytics`, `/api/crm/dow-analysis`     |
| `pnl`        | P&L & Budget    | `/api/crm/dashboard` (combined)                            |

Additional CRM endpoints:
- `POST /api/crm/import-history` -- import historical RJ Excel files
- `POST /api/crm/import-from-dir` -- import from directory
- `POST /api/crm/sync-kdrive` -- sync from kDrive
- `GET /api/crm/data-status` -- data source status

#### Analytics Engine

CRM uses a dual-source analytics engine (`_get_analytics()`):
1. Explicit `?start_date=&end_date=` -> `HistoricalAnalytics` (DB)
2. In-memory RJ file -> `JourAnalytics`
3. Fallback: DB last 30 days -> `HistoricalAnalytics`

#### Data Sources

`DailyJourMetrics`, `DailyReport`, `VarianceRecord`, `CashReconciliation`, `MonthEndChecklist`, `User`, `Shift`, `TaskCompletion`

---

## Direction Dashboards

### Direction Portal (`/direction`)

- **Route:** `GET /direction`
- **Blueprint:** `direction_bp` (`routes/direction.py`)
- **Decorator:** `@direction_required` -- roles: `admin`, `gm`, `gsm`, `accounting`
- **Template:** `direction_portal.html`

The Direction portal is a single-page app with multiple sections toggled via sidebar links (`#rj`, `#reports`, `#trends`).

#### API Endpoints

| Endpoint                                     | Method | Description                                          |
|----------------------------------------------|--------|------------------------------------------------------|
| `/api/direction/dashboard`                   | GET    | KPI summary (RevPAR, ADR, Occ, Revenue) + budget variance + recent audits list |
| `/api/direction/rj-summary/<date>`           | GET    | Complete read-only NightAuditSession (all 155 columns) |
| `/api/direction/rj-sessions`                 | GET    | List all NightAuditSession records for RJ viewer     |
| `/api/direction/dates`                       | GET    | Available dates (last 90) for date picker            |
| `/api/direction/all-dates`                   | GET    | Full date history grouped by year-month              |
| `/api/direction/daily-report/<date>`         | GET    | 4 Direction reports: Rapp_p1, Rapp_p2, Rapp_p3, Etat_rev |
| `/api/direction/trends`                      | GET    | Configurable trend data (default 30 days, max 365). Revenue, occ, ADR, RevPAR, F&B, room revenue series |
| `/api/direction/overview`                    | GET    | Full executive overview: KPIs, advanced KPIs, DOW analysis, trends, F&B, rooms, payments, monthly summary |
| `/api/direction/yearly-comparison`           | GET    | Year-over-year comparison for all available years    |
| `/api/direction/monthly-summary`             | GET    | Monthly aggregated revenue/occ/ADR for bar charts    |
| `/api/direction/labor-analysis`              | GET    | Labor cost % by department (JOIN DailyLaborMetrics x DailyJourMetrics) |
| `/api/direction/gl-reconciliation`           | GET    | GL journal entries vs RJ data (JOIN JournalEntry x NightAuditSession) |
| `/api/direction/labor-by-department`         | GET    | Department-level labor breakdown                     |
| `/api/direction/gl-top-accounts`             | GET    | Top GL accounts by volume                            |
| `/api/direction/cross-analysis`              | GET    | Cross-analysis across all 38 data sheets             |

#### Section Groups

- **RJ Reports:** RJ viewer with full 155-column NightAuditSession, session list, date picker
- **Direction Overview:** Dashboard KPIs with budget variance, executive overview with DOW/trend/F&B/rooms/payments
- **Trends:** 30-365 day trend charts (revenue, occ, ADR, RevPAR, F&B)
- **Daily Reports:** 4-part Direction reports (Rapp_p1 Revenue Summary, Rapp_p2 Hours & Staff, Rapp_p3 Revenue Statement, Etat_rev Full P&L)
- **GL & Labor:** GL reconciliation, labor cost analysis by department, cross-analysis

#### Data Sources

`DailyJourMetrics`, `NightAuditSession`, `DepartmentLabor`, `MonthlyExpense`, `MonthlyBudget`, `JournalEntry`, `DailyLaborMetrics`

---

### GM Morning Briefing (`/dashboard/gm`)

- **Route:** `GET /dashboard/gm`
- **Blueprint:** `dashboard_bp` (`routes/dashboard.py`)
- **Decorators:** `@login_required`, `@role_required('gm', 'gsm', 'admin')`
- **Template:** `dashboard/gm_briefing.html`
- **API:** `GET /api/dashboard/gm-briefing`
- **Query param:** `?date=YYYY-MM-DD` (defaults to most recent DJM row)

#### 4 Panels

| Panel                | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| Last Night           | KPIs (occ, ADR, RevPAR, revenue, F&B, rooms sold, comp %, OOS), vs Budget (prorated daily), vs Last Year (same date or -364 days for same DOW), vs 7-day rolling average |
| Operational Status   | Balance checks from NightAuditSession, audit submission status, auditor name |
| Forward Look         | OTB forecast (next 7/14/30 days occupancy + ADR), STR competitive position  |
| Trend Context        | 7-day rolling averages, MTD performance vs budget, DOW patterns             |

#### Data Sources

`DailyJourMetrics`, `NightAuditSession`, `MonthlyBudget`, `OTBForecast`, `STRCompSet`, `DailyCashRecon`, `DepositVariance`

---

### Accounting Month-End (`/dashboard/accounting`)

- **Route:** `GET /dashboard/accounting`
- **Blueprint:** `dashboard_bp` (`routes/dashboard.py`)
- **Decorators:** `@login_required`, `@role_required('accounting', 'gm', 'admin')`
- **Template:** `dashboard/accounting.html`
- **API:** `GET /api/dashboard/accounting`
- **Query params:** `?year=YYYY&month=MM`

#### 7 Sections

| Section                 | Description                                                           |
|-------------------------|-----------------------------------------------------------------------|
| A. Checklist Progress   | MonthEndChecklist task completion count, %, pending task names         |
| B. Revenue Verification | DJM total/room/FB revenue vs budget, days with data vs expected       |
| C. Missing Data         | Dates in the month window with no DJM data (only past dates)          |
| D. GL Suspense          | GL account variances from JournalEntry (101100, 100401, etc.)         |
| E. Deposit Variances    | DepositVariance records for the month                                 |
| F. Card Discount Costs  | Card processing fee analysis from DailyCardMetrics                    |
| G. Data Quality         | Warnings about incomplete or suspicious data                          |

#### Data Sources

`MonthEndChecklist`, `DailyJourMetrics`, `MonthlyBudget`, `NightAuditSession`, `DepositVariance`, `DailyCardMetrics`, `JournalEntry`

---

### Manager / Executive Intelligence (`/manager`)

- **Route:** `GET /manager`
- **Blueprint:** `manager_bp` (`routes/manager.py`)
- **Decorator:** `@manager_required` -- roles: `admin`, `gm`, `gsm`, `accounting`
- **Template:** `manager.html`

#### API Endpoints

| Endpoint                             | Method | Description                                                  |
|--------------------------------------|--------|--------------------------------------------------------------|
| `/api/manager/overview`              | GET    | Complete executive overview: KPIs, advanced KPIs, DOW analysis, opportunities, trend, F&B, rooms, payments, monthly summary, YoY, data status, deep insights |
| `/api/manager/yearly-comparison`     | GET    | Year-over-year all metrics for all available years           |
| `/api/manager/expenses`              | GET    | All MonthlyExpense records                                   |
| `/api/manager/expenses`              | POST   | Upsert a monthly expense record                             |
| `/api/manager/goppar`                | GET    | GOPPAR and profitability: GOP, margin %, LCPOR, break-even occ per month |
| `/api/manager/labor`                 | GET    | Department labor data with monthly summaries and LCPOR       |
| `/api/manager/labor`                 | POST   | Upsert a department labor record                             |
| `/api/manager/labor-analytics`       | GET    | Deep labor analytics: department efficiency, overtime, budget variance, staffing patterns |
| `/api/manager/labor/efficiency`      | GET    | Labor intensity, productivity, seasonal patterns, staffing status |
| `/api/manager/automation-stats`      | GET    | Import stats for all data sources, automation % coverage     |

#### Dashboard Sections

- **Executive KPIs:** ADR, occupancy, RevPAR, TRevPAR, revenue totals, guest counts
- **Yearly Comparison:** Multi-year side-by-side with deltas
- **Expenses & GOPPAR:** Monthly P&L, gross operating profit per available room, margin %
- **Labor Analytics:** Department efficiency ranking, overtime analysis, tips, budget variance, seasonal staffing
- **Automation Stats:** Data source coverage and import counts

#### Data Sources

`DailyJourMetrics`, `DailyReconciliation`, `JournalEntry`, `DepositVariance`, `TipDistribution`, `HPDepartmentSales`, `DueBack`, `DepartmentLabor`, `MonthlyExpense`

---

## Shared Dashboards

### Budget & Ecarts (`/budget`)

- **Route:** `GET /budget/`
- **Blueprint:** `budget_bp` (`routes/budget.py`, `url_prefix='/budget'`)
- **Decorator:** `@budget_required` -- roles: `admin`, `gm`, `gsm`, `accounting`
- **Template:** `budget.html`

| Endpoint                                  | Method | Description                              |
|-------------------------------------------|--------|------------------------------------------|
| `/api/budget/<year>/<month>`              | GET    | Get budget for a specific month          |
| `/api/budget/save`                        | POST   | Save/update budget data                  |
| `/api/budget/import`                      | POST   | Import budget from file                  |
| `/api/budget/variance/<year>/<month>`     | GET    | Budget vs actual variance for a month    |
| `/api/budget/ytd/<year>`                  | GET    | Year-to-date budget analysis             |
| `/api/budget/<year>/<month>`              | DELETE | Delete a monthly budget record           |

**Data Sources:** `MonthlyBudget`, `DailyJourMetrics`

---

### STR & OTB (`/compset`)

- **Route:** `GET /compset/`
- **Blueprint:** `compset_bp` (`routes/compset.py`, `url_prefix='/compset'`)
- **Decorator:** `@login_required` (visible to auditors and direction)
- **Template:** `compset.html`

| Endpoint                        | Method | Description                                    |
|---------------------------------|--------|------------------------------------------------|
| `/compset/api/str`              | GET    | STR competitive set data                       |
| `/compset/api/str/import`       | POST   | Import STR data from CSV                       |
| `/compset/api/str/seed`         | GET    | Seed STR sample data                           |
| `/compset/api/str-trends`       | GET    | STR trend analysis                             |
| `/compset/api/otb`              | GET    | OTB forecast data                              |
| `/compset/api/otb/generate`     | POST   | Generate OTB projections (booking curve engine)|
| `/compset/api/otb/import`       | POST   | Import OTB data from file                      |
| `/compset/api/otb/manual`       | POST   | Manual OTB entry                               |
| `/compset/api/otb/snapshot`     | POST   | Save OTB snapshot                              |
| `/compset/api/otb/seed`         | GET    | Seed OTB sample data                           |
| `/compset/api/otb-pace`         | GET    | OTB pace analysis (pickup trends)              |

**Data Sources:** `STRCompSet`, `OTBForecast`, `DailyJourMetrics`

---

### Forecasting (`/previsions`)

- **Route:** `GET /previsions`
- **Blueprint:** `forecasting_bp` (`routes/forecasting.py`)
- **Decorator:** `@login_required`
- **Template:** `forecasting.html`

InsightsEngine-powered ML forecasting dashboard.

| Endpoint                             | Method | Description                                  |
|--------------------------------------|--------|----------------------------------------------|
| `/api/previsions/forecast`           | GET    | 30/60/90-day demand forecast (occ, ADR, RevPAR) |
| `/api/previsions/seasonality`        | GET    | Seasonal patterns by month and DOW           |
| `/api/previsions/anomalies`          | GET    | Statistical anomaly detection                |
| `/api/previsions/pricing`            | GET    | Pricing power analysis                       |
| `/api/previsions/trends`             | GET    | Moving average trend analysis                |
| `/api/previsions/insights`           | GET    | Revenue concentration insights               |

**Data Sources:** `DailyJourMetrics` (via `InsightsEngine`)

---

### Portfolio (`/portfolio`)

- **Route:** `GET /portfolio/`
- **Blueprint:** `portfolio_bp` (`routes/portfolio.py`, `url_prefix='/portfolio'`)
- **Decorator:** `@role_required('admin', 'gm', 'gsm', 'accounting')`
- **Template:** `portfolio.html`

Multi-property consolidated dashboard.

| Endpoint                              | Method | Description                                |
|---------------------------------------|--------|--------------------------------------------|
| `/portfolio/api/portfolio/summary`    | GET    | Consolidated KPIs across all properties    |
| `/portfolio/api/portfolio/comparison` | GET    | Property-to-property comparison            |
| `/portfolio/api/portfolio/property-list` | GET | List of all properties with metadata       |

**Data Sources:** `Property`, `NightAuditSession`, `DailyJourMetrics`

---

### Reports (`/reports`)

- **Route:** `GET /reports`
- **Blueprint:** `reports_bp` (`routes/reports.py`)
- **Decorator:** `@login_required`
- **Template:** `reports.html`

Auditor-facing analytics and daily reporting.

| Endpoint                              | Method | Description                                    |
|---------------------------------------|--------|------------------------------------------------|
| `/api/reports/daily-summary`          | GET    | Daily summary from RJ or database              |
| `/api/reports/daily-comparison`       | GET    | Day-over-day comparison                        |
| `/api/reports/trends`                 | GET    | Trend charts                                   |
| `/api/reports/variances`              | GET    | Variance tracking                              |
| `/api/reports/variances/by-receptionist` | GET | Variances grouped by receptionist              |
| `/api/reports/credit-cards`           | GET    | Credit card breakdown                          |
| `/api/reports/save-daily`             | POST   | Save a daily report entry                      |
| `/api/reports/receptionists`          | GET    | Receptionist list                              |

**Data Sources:** `DailyReport`, `VarianceRecord`, `DailyJourMetrics`, `NightAuditSession`

---

## Dashboard Summary Table

| #  | Page                    | Route                  | Roles                              | Purpose                                          | Key API                            |
|----|-------------------------|------------------------|------------------------------------|--------------------------------------------------|------------------------------------|
| 1  | Smart Dashboard         | `/dashboard`           | All authenticated                  | Auditor landing: KPIs, alerts, shift progress    | `/api/dashboard/smart`             |
| 2  | Auditor Panel           | (widget)               | All authenticated                  | Real-time balance checks + error detection       | `/api/dashboard/auditor-panel`     |
| 3  | CRM Analytics           | `/crm`                 | All authenticated                  | 7-tab BI: revenue, F&B, labor, cash, payments    | `/api/crm/dashboard`               |
| 4  | Direction Portal        | `/direction`            | gm, gsm, accounting, admin        | RJ viewer, Direction reports, trends, GL, labor  | `/api/direction/dashboard`         |
| 5  | GM Morning Briefing     | `/dashboard/gm`        | gm, gsm, admin                    | 4-panel last-night summary for GM                | `/api/dashboard/gm-briefing`       |
| 6  | Accounting Month-End    | `/dashboard/accounting` | accounting, gm, admin             | Checklist, revenue verification, GL, deposits    | `/api/dashboard/accounting`        |
| 7  | Manager Intelligence    | `/manager`             | gm, gsm, accounting, admin        | Executive KPIs, YoY, GOPPAR, labor, automation   | `/api/manager/overview`            |
| 8  | Budget & Ecarts         | `/budget`              | gm, gsm, accounting, admin        | Budget management and variance analysis          | `/api/budget/<y>/<m>`              |
| 9  | STR & OTB               | `/compset`             | All authenticated                  | Competitive benchmarking + OTB forecasts         | `/compset/api/str`, `/compset/api/otb` |
| 10 | Forecasting             | `/previsions`          | All authenticated                  | ML demand/pricing/anomaly forecasts              | `/api/previsions/forecast`         |
| 11 | Portfolio               | `/portfolio`           | gm, gsm, accounting, admin        | Multi-property consolidated view                 | `/portfolio/api/portfolio/summary` |
| 12 | Reports                 | `/reports`             | All authenticated                  | Daily summaries, variance tracking, cards         | `/api/reports/daily-summary`       |
