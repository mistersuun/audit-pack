# API Reference

All endpoints require authentication (`@login_required`) unless noted otherwise.
Mutating endpoints (`POST`) also require CSRF protection (`@csrf_protect`).

Base URL: all paths are relative to the application root.

---

## RJ Core (`routes/audit/rj_core.py`)

### Pages

| Method | Path | Description |
|--------|------|-------------|
| GET | `/rj` | Original monolithic RJ page |
| GET | `/rj/v2` | Modular RJ page with lazy-loaded tabs |

### Tab Fragments

**GET** `/api/rj/tab/<tab_id>`

Returns HTML fragment for lazy-loaded tab. Valid tab_ids: `nouveau-jour`, `sd`, `depot`, `dueback`, `recap`, `transelect`, `geac`, `import-docs`.

### Upload / Download

**POST** `/api/rj/upload`

Upload RJ Excel file for the current session.

- **Form data**: `rj_file` (file, `.xls` or `.xlsx`)
- **Response**: `{ success, message, file_info: { filename, size, sheets } }`
- **Side effects**: Stores file in session-scoped memory (`RJ_FILES`), auto-extracts date from filename

**GET** `/api/rj/download`

Download the current (modified) RJ file.

- **Response**: Excel file attachment

### Status / Reading

**GET** `/api/rj/status`

Returns current RJ file status and basic info (loaded, filename, current day).

**GET** `/api/rj/read/<sheet_name>`

Read current values from a specific sheet. Returns JSON with cell values.

---

## RJ Fill (`routes/audit/rj_fill.py`)

### Sheet Fill

**POST** `/api/rj/fill/<sheet_name>`

Fill a sheet with form data using CELL_MAPPINGS.

- **Path param**: `sheet_name` -- `recap`, `transelect`, `geac`, `controle`, `depot`, `daily`
- **Body**: JSON dict with field names matching the sheet's mapping
- **Response**: `{ success, message, cells_filled }`

### Controle

**POST** `/api/rj/controle`

Update controle sheet with day/date values.

- **Body**: `{ vjour: int, mois: int, annee: int, prepare_par: string }`
- **Response**: `{ success, message, updated: { vjour, mois, annee, idate } }`

**POST** `/api/rj/autofill-controle`

Auto-fill controle with session auditor name and provided or current date.

- **Body** (optional): `{ vjour, mois, annee }`

### Recap

**POST** `/api/rj/autofill-recap`

Auto-fill Recap fields from Daily Revenue data.

- **Body**: `{ daily_revenue_data: { settlements: { cheque: float }, ... } }`

### GEAC Cashout

**POST** `/api/rj/autofill-cashout`

Auto-fill GEAC/UX Rows 6 and 12 + Transelect fusebox from card totals.

- **Body**: `{ cards: { visa: float, mastercard: float, amex: float, diners: float, discover: float } }`
- **Fills**: geac_ux B6/E6/G6/J6/K6 (cash out), B12/E12/G12/J12/K12 (daily rev), transelect B21/B22/B24 (fusebox)

### DueBack

**POST** `/api/rj/fill/dueback`

Fill single DueBack entry.

- **Body**: `{ day: int, receptionist: string, amount: float, line: "previous"|"nouveau" }`

**GET** `/api/rj/dueback/names?day=N`

Get receptionist columns and values for a given day.

**GET** `/api/rj/dueback/total?day=N`

Get column Z total for a day.

**GET** `/api/rj/dueback/column-b?day=N`

Get column B (R/J reference from jour sheet) values for a day.

- **Response**: `{ data: { previous, current, net }, day }`

**POST** `/api/rj/dueback/bulk`

Fill multiple DueBack entries at once.

- **Body**: `{ day: int, items: [ { col_letter, line_type, amount } ] }`

**POST** `/api/rj/dueback/save`

Save all DueBack data for current audit day using simplified workflow.

- **Body**: `{ "C": { previous: float, current: float }, "D": { ... }, ... }`
- Previous values stored as negative, current as positive. Also computes Total Z.

### Deposit

**POST** `/api/rj/deposit`

Update depot tab with verified amount.

- **Body**: `{ amount: float, date: "YYYY-MM-DD" (optional) }`

---

## RJ Macros (`routes/audit/rj_macros.py`)

**POST** `/api/rj/reset`

Reset (clear) all tabs: Recap, transelect, geac_ux.

- **Response**: `{ success, cleared_count }`

**POST** `/api/rj/reset/<sheet_name>`

Reset single tab. Valid names: `recap`, `transelect`, `geac`, `geac_ux`, `depot`, `daily`.

**POST** `/api/rj/sync`

Sync DUBACK# to SetD for current day.

- **Body** (optional): `{ day: int }`

**POST** `/api/rj/macro/envoie-jour`

Copy Recap H19:N19 to jour columns BU:CA for the given day.

- **Body** (optional): `{ day: int }`

**POST** `/api/rj/macro/calcul-carte`

Copy transelect card totals to jour columns BI:BN for the given day.

- **Body** (optional): `{ day: int }`

**POST** `/api/rj/recap/send-to-jour`

Alternative endpoint for copying Recap summary to jour (uses `rj_writer` module).

- **Body**: `{ day: int }`

---

## RJ Parsers (`routes/audit/rj_parsers.py`)

**POST** `/api/rj/parse`

Parse an uploaded document and return extracted data (preview only, does not fill RJ).

- **Form data**: `doc_type` (string), `file` (uploaded file), `day` (optional, for hp_excel)
- **Response**: `{ success, data, field_mappings, confidence, warnings, errors }`

**POST** `/api/rj/parse-and-fill`

Parse document AND auto-fill the corresponding RJ sheet.

- **Form data**: `doc_type`, `file`
- **Response**: `{ success, data, filled_cells, filled_count, confidence, warnings }`

**POST** `/api/rj/fill-jour`

Compute all jour values from parsed data and write to jour sheet.

- **Body**: `{ day, parsed_data: { daily_revenue: {}, sales_journal: {}, hp_excel: {} }, manual_values: {}, adjustments: [] }`
- **Response**: `{ success, filled_count, day, target_row, values: { col_letter: value }, summary }`

**GET** `/api/rj/departments`

Get available departments for adjustment entries.

**GET** `/api/rj/parser-types`

Get all available parser types with labels and descriptions.

---

## SD Operations (`routes/audit/rj_sd.py`)

**POST** `/api/sd/upload`

Upload SD (Suivi des Depots) Excel file.

- **Form data**: `sd_file` (`.xls` or `.xlsx`)
- **Response**: `{ success, message, file_info: { filename, size, available_days } }`

---

## Authentication (`routes/auth_v2.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET/POST | `/auth/login` | No | Login page and handler |
| GET | `/auth/logout` | No | Clear session |
| GET | `/auth/profile` | Yes | User profile |
| GET/POST | `/auth/change-password` | Yes | Change password |
| GET | `/auth/admin/users` | Admin | User management page |
| POST | `/auth/api/admin/users` | Admin | Create user |
| POST | `/auth/api/admin/users/<id>/toggle` | Admin | Toggle user active state |

---

## Direction Portal (`routes/direction.py`)

All endpoints require `direction_required` decorator (roles: `admin`, `gm`, `gsm`, `accounting`).

### Page

| Method | Path | Description |
|--------|------|-------------|
| GET | `/direction` | Direction Portal SPA page |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/direction/dashboard` | KPI summary (RevPAR, ADR, occupancy, revenue vs budget, recent audits). Requires `?date=YYYY-MM-DD` |
| GET | `/api/direction/rj-summary/<date>` | Complete read-only NightAuditSession for a date (all 155 columns) |
| GET | `/api/direction/trends` | Configurable trend data for charts (revenue, occ, ADR, RevPAR, F&B, room rev). `?days=N` (default 30, max 365) |
| GET | `/api/direction/overview` | Full executive overview: KPIs, advanced KPIs, DOW analysis, trend, F&B, rooms, payments, monthly. Optional `?start_date=&end_date=` |
| GET | `/api/direction/yearly-comparison` | Year-over-year comparison for all available years with delta computation |
| GET | `/api/direction/all-dates` | All available dates grouped by year-month for the date picker |
| GET | `/api/direction/rj-sessions` | List all NightAuditSession records for the RJ viewer |
| GET | `/api/direction/monthly-summary` | Monthly aggregated revenue/occ/ADR for historical bar charts |
| GET | `/api/direction/daily-report/<date>` | All 4 Direction reports (Rapp_p1, Rapp_p2, Rapp_p3, Etat_rev) for a given date with MTD + budget |
| GET | `/api/direction/dates` | List of dates with data (last 90) for the date picker |
| GET | `/api/direction/labor-analysis` | Labour cost % by department (DailyLaborMetrics x DailyJourMetrics). `?days=N` |
| GET | `/api/direction/gl-reconciliation` | GL journal entries vs RJ data (JournalEntry x NightAuditSession). `?date=` or `?days=N` |
| GET | `/api/direction/labor-by-department` | Detailed labor breakdown by department. `?days=N` |
| GET | `/api/direction/gl-top-accounts` | Top 20 GL accounts by total amount. `?date=YYYY-MM-DD` (optional) |
| GET | `/api/direction/cross-analysis` | Cross-sheet analysis combining revenue, labor, GL, and deposits. `?days=N` |

---

## Manager Portal (`routes/manager.py`)

All endpoints require `manager_required` decorator (roles: `admin`, `gm`, `gsm`, `accounting`).

### Page

| Method | Path | Description |
|--------|------|-------------|
| GET | `/manager` | Manager Analytics SPA page |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/manager/overview` | Complete executive overview: KPIs, advanced KPIs, DOW, opportunities, trend, F&B, rooms, payments, monthly, YoY, data status, insights. Optional `?start_date=&end_date=` |
| GET | `/api/manager/yearly-comparison` | Year-over-year comparison for all years (ADR, occ, RevPAR, TRevPAR, F&B/guest, card payments, OOS, comp rooms) |
| GET | `/api/manager/expenses` | Get all monthly expense records |
| POST | `/api/manager/expenses` | Save/update a monthly expense record. Body: `{ year, month, labor_rooms, labor_fb, ... }` |
| GET | `/api/manager/goppar` | GOPPAR and profitability metrics: GOP, margin %, LCPOR, break-even occupancy by month |
| GET | `/api/manager/labor` | Get department-level labor data with budget analysis. `?year=N` |
| POST | `/api/manager/labor` | Upsert a department labor record. Body: `{ year, month, department, regular_hours, ... }` |
| GET | `/api/manager/labor-analytics` | Comprehensive labor analytics: department efficiency, monthly trends, staffing patterns |
| GET | `/api/manager/labor/efficiency` | Deep efficiency analysis: labor intensity, productivity metrics, seasonal patterns |
| GET | `/api/manager/automation-stats` | Stats on all imported data sources and automation percentage |

---

## Dashboard Sub-Endpoints (`routes/dashboard.py`)

### Pages

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/dashboard` | `@login_required` | Smart Dashboard (auditor landing page) |
| GET | `/dashboard/gm` | `gm`, `gsm`, `admin` | GM Morning Briefing page |
| GET | `/dashboard/accounting` | `accounting`, `gm`, `admin` | Accounting month-end page |

### API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/dashboard/smart` | `@login_required` | Smart dashboard: KPIs, alerts, shift progress, weather. `?date=` |
| GET | `/api/dashboard/auditor-panel` | `@login_required` | Auditor error detection panel: balance grid, outstanding items, variance alerts. `?date=` |
| GET | `/api/dashboard/gm-briefing` | `gm`, `gsm`, `admin` | GM morning briefing: last night performance, operational status, OTB look, trend context. `?date=` |
| GET | `/api/dashboard/accounting` | `accounting`, `gm`, `admin` | Accounting month-end: checklist progress, revenue verification, data gaps, GL suspense, deposit variances, card discount costs, data quality. `?year=&month=` |

---

## Common Response Patterns

### Success
```json
{
    "success": true,
    "message": "Human-readable status (French)",
    "data": { ... }
}
```

### Error
```json
{
    "success": false,
    "error": "Error description"
}
```

HTTP status codes: 200 (success), 400 (bad request / validation), 500 (server error).

### Amount Validation

All financial amount fields are validated with `validate_amount()`:
- Must be a valid number (not NaN, not Infinity)
- Absolute value must not exceed 10,000,000
- Returns `(float_value, None)` on success or `(None, error_message)` on failure
