# BI Cross-Reference: Data Sources to Analytics

This document maps the full data pipeline from RJ Excel sheets through parsers, into the database, and out to CRM analytics tabs. Use it to understand which source feeds which metric, and to identify gaps where untapped data could yield new insights.

---

## 1. Sheet to CRM Tab Mapping

| CRM Tab | Endpoint | Primary Data Source | Sheets Used | Key Metrics |
|---------|----------|---------------------|-------------|-------------|
| **Overview** | `/api/crm/dashboard` | `DailyJourMetrics` or in-memory Jour | jour | Total revenue, ADR, RevPAR, TRevPAR, occupancy, F&B total, anomalies |
| **Revenue** | `/api/crm/tabs/revenue-mgmt` | `DailyJourMetrics` + `MonthlyBudget` | jour, controle, Budget | ADR by DoW, ADR by month, RevPAR trend, occupancy vs ADR scatter, budget vs actual, yearly summary |
| **F&B** | `/api/crm/tabs/fb-intel` | `DailyJourMetrics` + `DailyTipMetrics` | jour, AD (HP sales), Nettoyeur | Outlet trend monthly, F&B per client, tips by department, food vs beverage evolution |
| **Labour** | `/api/crm/tabs/labor` | `DepartmentLabor` + `DailyLaborMetrics` + `DailyJourMetrics` | salaires, Feuil1 | Labor by dept, hours, labor % of revenue, revenue per labor hour, overtime trend, headcount, budget variance |
| **Cash** | `/api/crm/tabs/cash-recon` | `DailyCashRecon` + `DepositVariance` | Recap, Diff.Caisse#, DUEBACK#, SetD | Surplus/deficit trend, Quasimodo variance, diff caisse, auditor stats, deposit trend, recon quality, employee variances |
| **Payments** | `/api/crm/tabs/payments` | `DailyCardMetrics` | transelect, geac_ux | Card mix %, card volume, discount costs, blended rate, net vs gross, transaction counts, average ticket |
| **P&L** | `/api/crm/tabs/pnl-budget` | `MonthlyBudget` + `MonthlyExpense` + `DailyJourMetrics` | Budget, jour, salaires | Revenue variance, expense breakdown, profit margin, labour ratio, franchise fees, annual P&L |

### Direction Portal Data Flows

| Direction Tab | Endpoint | Primary Models | Key Metrics |
|---------------|----------|----------------|-------------|
| **Dashboard KPIs** | `/api/direction/dashboard` | `DailyJourMetrics`, `NightAuditSession`, `MonthlyBudget` | RevPAR, ADR, occupancy vs budget, MTD revenue, recent audits |
| **Daily Report** (Rapp_p1/p2/p3/Etat rev) | `/api/direction/daily-report/<date>` | `DailyJourMetrics`, `NightAuditSession`, `DepartmentLabor`, `MonthlyExpense`, `MonthlyBudget` | Revenue vs budget, hours & headcount, revenue vs labor by dept, full P&L |
| **Trends** | `/api/direction/trends` | `DailyJourMetrics` | 30-365 day revenue, occupancy, ADR, RevPAR, F&B, room revenue trends |
| **Labor Analysis** | `/api/direction/labor-analysis` | `DailyLaborMetrics`, `DailyJourMetrics` | Labour cost % by department, daily cost/revenue ratio |
| **GL Reconciliation** | `/api/direction/gl-reconciliation` | `JournalEntry`, `NightAuditSession` | GL entries vs RJ data, account-level reconciliation |
| **Cross Analysis** | `/api/direction/cross-analysis` | `DailyJourMetrics`, `DailyLaborMetrics`, `JournalEntry`, `DepositVariance` | Multi-source cross-sheet analysis |

### Manager Dashboard Data Flows

| Manager Section | Endpoint | Primary Models | Key Metrics |
|-----------------|----------|----------------|-------------|
| **Executive Overview** | `/api/manager/overview` | `DailyJourMetrics`, `DepartmentLabor` | KPIs, advanced KPIs, DOW, opportunities, F&B, rooms, payments, insights |
| **GOPPAR** | `/api/manager/goppar` | `MonthlyExpense`, `DailyJourMetrics` | GOP, GOPPAR, margin %, LCPOR, break-even occupancy |
| **Expenses** | `/api/manager/expenses` | `MonthlyExpense` | Monthly operating expenses by category |
| **Labor Analytics** | `/api/manager/labor-analytics` | `DepartmentLabor`, `DailyJourMetrics` | Department efficiency, monthly trends, staffing patterns |
| **Labor Efficiency** | `/api/manager/labor/efficiency` | `DepartmentLabor` | Labor intensity, productivity metrics, seasonal patterns |

**Additional standalone endpoints:**

| Endpoint | Source | Metrics |
|----------|--------|---------|
| `/api/crm/kpis` | `JourAnalytics` / `HistoricalAnalytics` | Executive KPIs with optional YoY comparison |
| `/api/crm/revenue-trend` | `JourAnalytics` / `HistoricalAnalytics` | Daily revenue trend (room, F&B, other, total) |
| `/api/crm/fb-analytics` | `JourAnalytics` | F&B by outlet and category, food/bev mix, tips |
| `/api/crm/room-analytics` | `JourAnalytics` | Room type mix, occupancy trend, comp rooms |
| `/api/crm/payment-analytics` | `JourAnalytics` | Card breakdown, escrow fees, daily card trend |
| `/api/crm/tax-analytics` | `JourAnalytics` | TPS/TVQ/TVH totals and daily trend |
| `/api/crm/anomalies` | `JourAnalytics` | Low occupancy, ADR drops, F&B drops, cash variances |
| `/api/crm/advanced-kpis` | `JourAnalytics` / `HistoricalAnalytics` | Effective ADR, pricing power, volatility, F&B per guest, comp loss, OOS cost, card processing |
| `/api/crm/dow-analysis` | `JourAnalytics` / `HistoricalAnalytics` | Day-of-week performance, weekend vs weekday |
| `/api/crm/revenue-opportunities` | `JourAnalytics` / `HistoricalAnalytics` | Opportunity days, potential revenue, annualized projections |

---

## 2. Jour Column to DailyJourMetrics Field Mapping

### Revenue Fields

| DB Field | Jour Col(s) | Letter(s) | Description |
|----------|-------------|-----------|-------------|
| `room_revenue` | 36 | AK | Chambres minus Club Lounge |
| `fb_revenue` | 4-28 (sum) | E-AC | Sum of all F&B outlet columns |
| `cafe_link_total` | 4-8 (sum) | E-I | Cafe Link: nour + boi + bie + min + vin |
| `piazza_total` | 9-13 (sum) | J-N | Piazza/Cupola: nour + boi + bie + min + vin |
| `spesa_total` | 14-18 (sum) | O-S | Marche La Spesa: nour + boi + bie + min + vin |
| `room_svc_total` | 19-23 (sum) | T-X | Room Service: nour + boi + bie + min + vin |
| `banquet_total` | 24-28 (sum) | Y-AC | Banquet: nour + boi + bie + min + vin |
| `tips_total` | 29 | AD | Pourboires |
| `tabagie_total` | 35 | AJ | Tabagie |
| `other_revenue` | 30,31,48 etc | AE,AF,AW | Equipment, divers, internet, misc |
| `total_revenue` | computed | -- | room_revenue + fb_revenue + other_revenue |

### F&B Category Fields

| DB Field | Jour Col | Letter | Description |
|----------|----------|--------|-------------|
| `total_nourriture` | 110 | DG | Sum of all food columns across outlets |
| `total_boisson` | 116 | DM | Sum of all beverage categories |
| `total_bieres` | 112 | DI | Sum of all beer columns |
| `total_vins` | 114 | DK | Sum of all wine columns |
| `total_mineraux` | 113 | DJ | Sum of all non-alcoholic columns |

### Occupancy & Room Fields

| DB Field | Jour Col | Letter | Description |
|----------|----------|--------|-------------|
| `rooms_simple` | 88 | CK | Simple room count |
| `rooms_double` | 89 | CL | Double room count |
| `rooms_suite` | 90 | CM | Suite room count |
| `rooms_comp` | 91 | CN | Complimentary room count |
| `total_rooms_sold` | computed | -- | simple + double + suite |
| `rooms_available` | 95 | CR | Available rooms (default 252) |
| `occupancy_rate` | computed | -- | total_rooms_sold / rooms_available * 100 |
| `nb_clients` | 92 | CO | Guest count |
| `rooms_hors_usage` | 93 | CP | Out of service rooms |
| `rooms_ch_refaire` | 94 | CQ | Rooms to redo |

### Payment Fields

| DB Field | Jour Col | Letter | Description |
|----------|----------|--------|-------------|
| `visa_total` | 63 | BL | Visa card total |
| `mastercard_total` | 62 | BK | MasterCard total |
| `amex_elavon_total` | 60 | BI | Amex ELAVON total |
| `amex_global_total` | 65 | BN | Amex GLOBAL total |
| `debit_total` | 64 | BM | Debit card total |
| `discover_total` | 61 | BJ | Discover total |
| `total_cards` | computed | -- | Sum of all 6 card types |

### Tax Fields

| DB Field | Jour Col | Letter | Description |
|----------|----------|--------|-------------|
| `tps_total` | 50 | AY | Federal TPS (GST) accumulator |
| `tvq_total` | 49 | AX | Provincial TVQ (QST) accumulator |
| `tvh_total` | 51 | AZ | Accommodation tax (Taxe Hebergement) |

### Cash & Balance Fields

| DB Field | Jour Col | Letter | Description |
|----------|----------|--------|-------------|
| `opening_balance` | 1 | B | Opening balance |
| `cash_difference` | 2 | C | Cash difference |
| `closing_balance` | 3 | D | Closing/new balance |

### Computed KPI Fields (cached in DB)

| DB Field | Formula | Fed By |
|----------|---------|--------|
| `adr` | room_revenue / total_rooms_sold | cols 36, 88-90 |
| `revpar` | room_revenue / rooms_available | cols 36, 95 |
| `trevpar` | total_revenue / rooms_available | all revenue cols, col 95 |
| `food_pct` | total_nourriture / fb_revenue * 100 | cols 110, 4-28 |
| `beverage_pct` | total_boisson / fb_revenue * 100 | cols 116, 4-28 |

---

## 3. Data Gaps & Untapped Sources

The following RJ sheets contain data that is NOT currently flowing into CRM analytics. Each represents an opportunity for richer BI.

| Sheet | Columns | Current Status | Potential CRM Value |
|-------|---------|----------------|---------------------|
| **AD** (HP Departmental Sales) | ~60 cols of F&B detail by department | Partially imported via `HPDepartmentSales` model but not exposed in CRM tabs | Much richer than jour for department-level food cost % and beverage category mix |
| **diff_forfait** | Package/forfait revenue detail | Not parsed | Package revenue analysis, forfait utilization rates |
| **Ristourne** | Corporate account rebate tracking | Not parsed | Corporate account profitability, client-level revenue analysis |
| **Sonifi / Internet** | Ancillary service detail | Col 45 (AT) and 48 (AW) capture totals only | Per-room ancillary revenue, adoption rates, upsell opportunity sizing |
| **autre GL** | General Ledger line items | Col 44 (AS) captures total only | GL-level expense tracking, anomaly detection on individual GL codes |
| **Massage** | Spa/massage service detail | Col 52 (BA) captures total only | Service revenue per available room, spa utilization, seasonal patterns |
| **SOCAN / Resonne** | Music royalty costs | Cols 33-34 (AH-AI) captured but not in CRM | Royalty cost tracking, compliance monitoring |
| **Nettoyeur / somm_nettoyeur** | Tip distribution detail by employee | `TipDistribution` model exists but not in CRM tabs | Gratuity distribution fairness analysis, tip-to-sales ratios by employee |
| **Diff.Caisse#** | Register-level cash detail | `DailyCashRecon` captures aggregate; individual register data not broken out | Register-level cash accountability, identify problem registers |
| **Feuil1** (labor hours detail) | Sub-department staffing by shift | `DailyLaborMetrics` captures department level | Sub-department staffing optimization, shift-level labor efficiency |
| **Rapp_p1 / Rapp_p2 / Rapp_p3** | Pre-built management reports | Not parsed | Already-computed KPIs from Excel -- could validate or supplement CRM calculations |
| **Etat rev** | Revenue state/status report | Not parsed | Month-end revenue reconciliation, department-level actual vs budget |
| **EJ** (Journal Entries) | GL journal entries | `JournalEntry` model exists | Full GL audit trail, expense categorization, anomaly detection |
| **Budget** | Monthly budget targets | `MonthlyBudget` model exists and IS used in Revenue and P&L tabs | Already connected -- consider expanding to per-department granularity |

---

## 4. Analytics Opportunities

### High-Value Expansions (using existing parsed data)

| Opportunity | Data Source | Implementation | Expected Impact |
|-------------|------------|----------------|-----------------|
| **Department-level food cost %** | `HPDepartmentSales` (already in DB) | Add F&B Intelligence sub-charts showing food/bev/beer/wine/mineral by department with cost ratios | Identify which outlet has margin problems |
| **Beverage category mix trends** | `HPDepartmentSales` | Track beer vs wine vs spirits vs non-alc ratios over time per outlet | Optimize inventory purchasing, identify consumer preference shifts |
| **Corporate account profitability** | Ristourne sheet (needs parser) | Parse rebate data, cross-reference with room revenue by account | Prioritize high-margin corporate accounts, renegotiate unprofitable ones |
| **Gratuity distribution fairness** | `TipDistribution` + `DailyTipMetrics` (both in DB) | Add tip equity dashboard: tip-to-sales ratio per employee, variance from department average | Labor relations, compliance, identify training needs |
| **Register-level cash accountability** | Diff.Caisse# (needs detail parsing) | Break out cash variance by register/station, not just daily total | Pinpoint shrinkage to specific registers or shifts |
| **Sub-department staffing optimization** | Feuil1 (needs detail parsing) | Parse individual department rows (RECEPTION, RESERVATION, AUDIT, PORTIER, etc.) at daily granularity | Right-size staffing by sub-department, optimize scheduling |

### Medium-Value Additions (new parsers needed)

| Opportunity | Data Source | Implementation | Expected Impact |
|-------------|------------|----------------|-----------------|
| **Pre-built management reports** | Rapp_p1/p2/p3 | Parse already-computed Excel KPIs, use as validation/supplement | Cross-check CRM calculations, add management-specific views |
| **Package revenue analysis** | diff_forfait | New parser for forfait detail | Understand package contribution, optimize pricing |
| **GL-level expense tracking** | autre GL detail | Expand col AS parsing to capture individual GL lines | Automated expense categorization, anomaly alerts |
| **Ancillary revenue optimization** | Sonifi, Internet, Massage detail | Parse per-room/per-day detail beyond totals | Size upsell opportunities, track adoption curves |

### Analytics Engine Enhancements (code-level)

| Enhancement | Current State | Proposed | Benefit |
|-------------|---------------|----------|---------|
| **YoY comparison** | Available via `HistoricalAnalytics.get_yoy_comparison()` | Extend to all tabs (currently only Overview) | Year-over-year delta on every metric |
| **Forecasting** | Not implemented | Use 90-day trailing average + seasonal adjustment | Projected ADR, RevPAR, occupancy for next 30 days |
| **Anomaly scoring** | Basic threshold alerts in `get_anomalies()` | Statistical z-score across all metrics, severity weighting | Automated daily briefing for GM |
| **Break-even analysis** | `MonthlyExpense` model exists | Calculate daily break-even occupancy from fixed + variable costs | "You need X rooms/night to cover costs" |
| **GOPPAR** | Not implemented | Gross Operating Profit per Available Room from expense + revenue data | True profitability metric (industry standard) |

---

## 5. Data Flow Diagram

```
RJ Excel File (.xls)
    |
    +-- Daily Revenue Parser (7 pages)
    |       |-- revenue.chambres.total --> jour col AK (36) --> DailyJourMetrics.room_revenue
    |       |-- revenue.telephones.* --> jour cols AL-AN (37-39)
    |       |-- revenue.autres_revenus.* --> jour cols AO-AW (40-48)
    |       |-- non_revenue.*.tps/tvq --> jour cols AX-AY (49-50) [accumulated]
    |       |-- non_revenue.chambres_tax.taxe_hebergement --> jour col AZ (51)
    |       |-- settlements.* --> jour cols BC, CC (54, 80)
    |       |-- balance.new_balance --> jour col D (3)
    |       +-- balance.front_office_transfers --> jour col CF (83)
    |
    +-- Sales Journal Parser (POS)
    |       |-- cafe_link.* --> jour cols E-I (4-8) --> DailyJourMetrics.cafe_link_total
    |       |-- piazza.* --> jour cols J-N (9-13) --> DailyJourMetrics.piazza_total
    |       |-- spesa.* --> jour cols O-S (14-18) --> DailyJourMetrics.spesa_total
    |       |-- chambres.* --> jour cols T-X (19-23) --> DailyJourMetrics.room_svc_total
    |       |-- banquet.* --> jour cols Y-AC (24-28) --> DailyJourMetrics.banquet_total
    |       |-- adjustments.pourboire_charge --> jour col AD (29) --> DailyJourMetrics.tips_total
    |       |-- adjustments.administration --> jour col BQ (68)
    |       |-- adjustments.hotel_promotion --> jour col BR (69)
    |       +-- taxes.tps/tvq --> added to accumulators AX-AY
    |
    +-- Transelect Parser (Card Settlements)
    |       |-- amex_total --> jour col BI (60) --> DailyJourMetrics.amex_elavon_total
    |       |-- discover_total --> jour col BJ (61) --> DailyJourMetrics.discover_total
    |       |-- master_total --> jour col BK (62) --> DailyJourMetrics.mastercard_total
    |       |-- visa_total --> jour col BL (63) --> DailyJourMetrics.visa_total
    |       |-- debit_total --> jour col BM (64) --> DailyJourMetrics.debit_total
    |       +-- amex_global_total --> jour col BN (65) --> DailyJourMetrics.amex_global_total
    |
    +-- Recap Parser (Cash Reconciliation)
    |       +-- H19:N19 --> jour cols BU-CA (72-78) via envoie_dans_jour macro
    |
    +-- Jour Sheet (read by JourAnalytics)
            |-- 117 cols x 31 rows --> JourAnalytics (in-memory)
            +-- 45 key metrics --> DailyJourMetrics (persisted to DB)
                    |
                    +-- CRM Overview Tab (dashboard_data)
                    +-- CRM Revenue Tab (revenue_management)
                    +-- CRM F&B Tab (fb_intelligence)
                    +-- CRM Labour Tab (labor_analytics)
                    +-- CRM Cash Tab (cash_reconciliation)
                    +-- CRM Payments Tab (payment_analytics)
                    +-- CRM P&L Tab (pnl_budget)
```

---

## 6. Database Model Index

| Model | Table | Source Sheet(s) | CRM Tab(s) |
|-------|-------|-----------------|-------------|
| `DailyJourMetrics` | `daily_jour_metrics` | jour | Overview, Revenue, F&B, Labour (for revenue ratios), P&L |
| `DailyLaborMetrics` | `daily_labor_metrics` | salaires, Feuil1 | Labour |
| `DepartmentLabor` | `department_labor` | salaires (monthly aggregation) | Labour |
| `DailyTipMetrics` | `daily_tip_metrics` | Nettoyeur, somm_nettoyeur | F&B |
| `DailyCashRecon` | `daily_cash_recon` | Diff.Caisse#, Recap | Cash |
| `DailyCardMetrics` | `daily_card_metrics` | transelect | Payments |
| `DepositVariance` | `deposit_variances` | SetD files | Cash |
| `MonthlyBudget` | `monthly_budget` | Budget sheet | Revenue, P&L |
| `MonthlyExpense` | `monthly_expenses` | Manual entry / Budget | P&L |
| `DailyReconciliation` | `daily_reconciliations` | Recap + GEAC + transelect | (available, not yet in tabs) |
| `JournalEntry` | `journal_entries` | EJ sheet | (available, not yet in tabs) |
| `TipDistribution` | `tip_distributions` | POURBOIRE files | (available, not yet in tabs) |
| `HPDepartmentSales` | `hp_department_sales` | AD (HP) files | (available, not yet in tabs) |
| `DueBack` | `due_backs` | DUEBACK# sheet | (available, not yet in tabs) |
| `MonthlyBudgetLegacy` | `monthly_budgets` | Budget (simplified) | (legacy) |
| `VarianceRecord` | `variance_records` | Manual entry | Staff management (CRM staff endpoint) |
| `CashReconciliation` | `cash_reconciliations` | Manual entry | (legacy) |

---

## 7. Analytics Engine Classes

### JourAnalytics (in-memory, single RJ file)

Reads an RJ `.xls` file directly into memory and computes all metrics from the Jour sheet. Used when a user has uploaded an RJ file in the current session.

**Methods:**
- `get_executive_kpis()` -- ADR, RevPAR, TRevPAR, occupancy, total revenue, rooms sold, guest count, card totals, taxes
- `get_revenue_trend()` -- Daily line chart data (room, F&B, other, total, occupancy, ADR, RevPAR)
- `get_fb_analytics()` -- Outlet breakdown, category totals, food/bev %, daily F&B trend
- `get_room_analytics()` -- Room type mix, occupancy trend, comp rooms, OOS, ADR by day
- `get_payment_analytics()` -- Card breakdown by type, daily trend, escrow fees
- `get_tax_analytics()` -- TPS/TVQ/TVH totals and daily trend
- `get_anomalies()` -- Low occupancy, ADR drops, F&B drops, cash variance alerts
- `get_advanced_kpis()` -- Effective ADR, pricing power, volatility, F&B per guest, comp loss, OOS cost, card processing cost, opportunity revenue, tax efficiency
- `get_dow_analysis()` -- Day-of-week performance, weekend vs weekday comparison
- `get_revenue_opportunities()` -- Opportunity days, potential revenue with annualized projections
- `get_full_dashboard()` -- Calls all of the above in a single response

### HistoricalAnalytics (database, multi-year)

Queries `DailyJourMetrics` table for a date range and computes the same metrics from persisted historical data. Used when date range params are provided or when no RJ file is in memory.

**Additional methods:**
- `get_yoy_comparison()` -- Year-over-year deltas for all KPIs
- `get_monthly_summary()` -- Aggregated monthly view across multiple years

**Priority logic** (in `_get_analytics()`):
1. Explicit `start_date` + `end_date` params --> `HistoricalAnalytics` (DB)
2. RJ file in memory (current session) --> `JourAnalytics` (in-memory)
3. DB has data --> `HistoricalAnalytics` (last 30 days)
4. No data available
