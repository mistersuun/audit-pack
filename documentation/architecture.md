# Architecture

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 / Flask |
| Frontend | HTML/JS (Jinja2 templates), lazy-loaded tab fragments |
| Database | PostgreSQL (SQLAlchemy ORM) |
| Excel | xlrd (read) + xlutils/xlwt (write) for .xls format |
| Parsers | pdfplumber (PDF), openpyxl (XLSX), built-in (text/RTF) |

## File Layout

```
audit-pack/
  routes/audit/          Flask blueprints for RJ endpoints
  utils/
    rj_mapper.py         Cell mapping definitions (CELL_MAPPINGS)
    rj_filler.py         Excel write operations (RJFiller)
    jour_mapper.py       Jour column computation (JourMapper)
    daily_rev_jour_mapping.py  Daily revenue -> jour mappings
    parsers/             Parser modules per document type
  templates/audit/rj/
    rj_layout.html       Main layout with tab navigation
    tabs/                One template per sheet tab
  static/                JS, CSS, template assets
  database/
    models.py            SQLAlchemy models
    migrations/          Schema migrations
```

## Parser Pipeline

```
Upload (PDF/XLSX/TXT)
  |
  v
ParserFactory
  |
  v
Parser.parse() --> structured dict {field: value}
  |
  v
JourMapper.compute_all() --> {col_index: value}
  |
  v
RJFiller.fill_jour_day(day, values) --> Excel write
```

Each parser produces a flat dictionary of named fields. JourMapper translates those fields into jour sheet column indices. RJFiller writes the computed values into the correct cells for the given audit day.

## Excel Read/Write Flow

1. `xlrd` opens the .xls workbook (read-only).
2. `xlutils.copy` creates a writable copy of the workbook.
3. `RJFiller` writes to cells via `sheet.write(row, col, value)`.
4. The workbook is saved to a `BytesIO` buffer or file path for download.

The .xls format is required because the original hotel workbook uses legacy Excel format with VBA macros. The xlrd/xlutils/xlwt stack handles this format natively.

## Cell Mapping Architecture

`rj_mapper.py` defines a `CELL_MAPPINGS` dictionary that maps sheet names to field-cell pairs:

```python
CELL_MAPPINGS = {
    "controle": {
        "jour": "B6",
        "mois": "B7",
        "annee": "B8",
        ...
    },
    "Recap": {
        "lecture_1": "H5",
        "correction_1": "I5",
        ...
    },
    ...
}
```

The helper function `excel_cell_to_indices()` converts cell references like `'B6'` into zero-based `(row, col)` tuples -- `(5, 1)` in this case. `fill_sheet()` iterates over the mapping for a given sheet and writes each value to the corresponding cell.

## Tab Loading (Frontend)

The main layout is `templates/audit/rj/rj_layout.html`. Tabs are lazy-loaded to avoid rendering all sheets at once:

1. User clicks a tab in the navigation bar.
2. JavaScript calls `fetch(/api/rj/tab/{tab_id})` to retrieve the tab HTML fragment.
3. The response is cached in a `tabCache` object to avoid redundant requests.
4. The current tab ID is saved to `localStorage` so it persists across page reloads.

Each tab fragment is a self-contained Jinja2 template in `templates/audit/rj/tabs/` that includes its own form fields, validation logic, and save handlers.

## Macro System

Python equivalents of the original VBA macros that synchronize data between sheets:

| Function | Source | Destination | Purpose |
|----------|--------|-------------|---------|
| `reset_tabs()` | -- | All sheets | Clear cell ranges per `RESET_RANGES` |
| `reset_single_tab()` | -- | One sheet | Clear a single sheet's ranges |
| `envoie_dans_jour()` | Recap H19:N19 | jour BU:CA | Push cash reconciliation totals to jour |
| `calcul_carte()` | transelect row 38 | jour BI:BN | Push card totals to jour |
| `sync_duback_to_setd()` | DueBack operations | SetD | Sync receptionist operations to settlement journal |
| `fill_jour_day()` | JourMapper output | jour sheet | Write all parser-computed values for the day |

These functions are called during save operations and during the final export to ensure all inter-sheet dependencies are resolved before the workbook is downloaded.

## Role-Based Navigation

The application exposes different sidebar groups depending on the user's role. Each group surfaces dashboards and tools relevant to that persona.

| Group | Roles | Pages |
|-------|-------|-------|
| **DIRECTION** | `gm`, `gsm`, `accounting` | Direction Portal (`/direction`), GM Briefing (`/dashboard/gm`), Accounting (`/dashboard/accounting`), Manager Analytics (`/manager`) |
| **AUDITORS** | `night_auditor`, `front_desk_supervisor` | Smart Dashboard (`/dashboard`), RJ (`/rj/v2`), CRM Analytics (`/crm`), Auditor Panel (via `/api/dashboard/auditor-panel`) |
| **ADMIN** | `admin` | All of the above + User Management (`/auth/admin/users`) |

The **Direction Portal** provides executive strategy views: Rapp_p1/p2/p3/Etat_rev replication, multi-year trends, GL reconciliation, and labor analysis. The **Manager Analytics** dashboard focuses on GOPPAR, expense management, and labor efficiency. Both draw from `DailyJourMetrics`, `DepartmentLabor`, `MonthlyExpense`, and `MonthlyBudget`.
