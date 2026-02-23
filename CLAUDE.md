# CLAUDE.md

This file provides guidance to Claude Code when working with this repository. Read it entirely before making changes.

## Project Overview

Sheraton Laval Night Audit WebApp — a local Flask application for night audit employees. Two main modules:
1. **Front Desk Checklist** — 46 step-by-step tasks for the nightly audit procedure
2. **RJ Natif** — Digital replacement of the Excel "Rapport Journalier" (RJ) workbook with 14 interactive tabs

The UI is entirely in **French**. The hotel uses **Galaxy Lightspeed** as their PMS.

## Development Commands

```bash
pip install -r requirements.txt        # Install dependencies
python seed_tasks.py                    # Seed front checklist tasks (run once or to reset)
python main.py                          # Run dev server on http://127.0.0.1:5000
```

## Architecture

- **Framework**: Flask + Jinja2 + SQLAlchemy
- **Database**: SQLite (`database/audit.db`)
- **Auth**: PIN-based (`AUDIT_PIN` in `.env`) + multi-user with roles (v2)
- **Frontend**: Vanilla JS, no framework. CSS variables for theming. Feather Icons.

### Directory Structure (core files only)

```
main.py                              # App entry point, registers all blueprints
config/settings.py                   # Flask configuration
database/models.py                   # ALL SQLAlchemy models (~1200 lines)
database/audit.db                    # SQLite database (auto-created)

routes/
  auth.py, auth_v2.py                # Authentication (PIN + multi-user)
  checklist.py                       # Front desk 46-task checklist
  audit/
    rj_native.py                     # ★ RJ Natif — main API (14 save endpoints + session mgmt)
    rj_core.py                       # RJ legacy tab-based routes
    rj_fill.py                       # Auto-fill from uploaded reports
    rj_parsers.py                    # PDF/text parsers for Lightspeed reports
    rj_macros.py                     # Excel macro emulation
    rj_sd.py                         # SD-specific endpoints
    rj_quasimodo.py                  # Quasimodo reconciliation logic

templates/
  audit/rj/rj_native.html            # ★ RJ Natif single-page app (~1800 lines, HTML+JS)
  audit/rj/rj_layout.html            # Legacy RJ layout
  audit/rj/tabs/                     # Legacy individual tab templates

documentation/
  front/                             # Front desk checklist source (46 tasks)
  back/README.md                     # Back audit procedures (19 phases)
  RJ/                                # RJ workbook analysis docs
    00_INDEX.md                      # Index of all 38 RJ Excel sheets
    12_procedure_back_complete.md    # Complete back audit workflow
```

### Utility scripts (root level)
There are many `analyze_*.py`, `debug_*.py`, `test_*.py` scripts at the root. These were used during development to reverse-engineer the original Excel RJ workbook. They are NOT part of the running app. Don't modify them unless asked.

## Key Models (database/models.py)

### NightAuditSession (★ main model, ~150 columns)
One row per audit night. Stores ALL data from the 14 RJ tabs.

**Core fields**: `audit_date` (PK-like, unique), `auditor_name`, `status` (draft/in_progress/submitted/locked), `temperature`, `weather_condition`, `chambres_refaire`

**Recap fields** (8 pairs lecture+correction): `cash_ls_*`, `cash_pos_*`, `cheque_ar_*`, `cheque_dr_*`, `remb_gratuite_*`, `remb_client_*`, `dueback_reception_*`, `dueback_nb_*`, plus `deposit_cdn`, `deposit_us`

**JSON columns** (stored as db.Text, parsed as JSON):
- `dueback_entries` — array of {name, previous, nouveau}
- `transelect_restaurant` — nested dict by terminal then card type
- `transelect_reception` — nested dict by card type then terminal
- `geac_cashout`, `geac_daily_rev` — dict by card type
- `sd_entries` — array of {department, name, currency, amount, verified, reimbursement}
- `depot_data` — {client6: {date, amounts[]}, client8: {date, amounts[]}}
- `setd_personnel` — array of {name, amount}
- `hp_admin_entries` — array of {area, nourriture, boisson, biere, vin, mineraux, autre, pourboire, raison, autorise_par}
- `dbrs_market_segments` — {transient, group, contract, other}
- `dbrs_otb_data` — JSON for On-The-Books data

**Scalar fields for new modules**:
- Internet: `internet_ls_361`, `internet_ls_365`, `internet_variance`
- Sonifi: `sonifi_cd_352`, `sonifi_email`, `sonifi_variance`
- Quasimodo (16 cols): `quasi_fb_{debit/visa/mc/amex/discover}`, `quasi_rec_{debit/visa/mc/amex/discover}`, `quasi_amex_factor` (default 0.9735), `quasi_cash_cdn`, `quasi_cash_usd`, `quasi_total`, `quasi_rj_total`, `quasi_variance`
- DBRS: `dbrs_daily_rev_today`, `dbrs_adr`, `dbrs_house_count`, `dbrs_noshow_count`, `dbrs_noshow_revenue`

**Jour fields** (~40 columns): All prefixed `jour_*` — F&B by department (cafe, piazza, spesa, chambres_svc, banquet × nourriture/boisson/bieres/mineraux/vins), room revenue, telephones, taxes (TVQ/TPS/taxe_hebergement), occupation (rooms_simple/double/suite/comp/hors_usage, nb_clients), and "autres revenus" (nettoyeur, machine_distrib, autres_gl, sonifi, lit_pliant, boutique, internet, massage).

**`calculate_all()` method**: Server-side recalculation of all computed fields (13 sections). Called on submit.

**`to_dict()` method**: Serializes session to JSON for the frontend. Handles JSON column parsing.

### Other models
- **Shift**: Legacy nightly audit session (date, start/end times)
- **Task**: 46 front desk checklist items (title_fr, description_fr, steps_json, screenshots_json, tips_fr, system_used, estimated_minutes)
- **TaskCompletion**: Tracks which front tasks are done per shift
- **User**: Multi-user auth (username, password_hash, role, pin)
- **HPDepartmentSales**: Monthly HP department sales (separate from daily RJ)

## RJ Natif — The Main Feature

### 14 Tabs (in order)
| # | Tab ID | Name | Description |
|---|--------|------|-------------|
| 1 | controle | Contrôle | Date, auditor, weather, chambres à refaire |
| 2 | dueback | DueBack | Dynamic rows: receptionist name + previous + nouveau |
| 3 | recap | Recap | 8 lines (lecture + correction = NET), deposits CDN/USD |
| 4 | transelect | Transelect | Restaurant (rows=terminals, cols=cards) + Reception (rows=cards, cols=terminals) |
| 5 | geac | GEAC | Cashout vs Daily Revenue by card + AR balance |
| 6 | sd | SD/Dépôt | SD expense entries + Depot envelopes (client 6 & 8) |
| 7 | setd | SetD | Personnel set-déjeuner entries |
| 8 | hpadmin | HP/Admin | Hotel Promotion & Administration F&B invoices |
| 9 | internet | Internet | CD 36.1 vs CD 36.5 variance |
| 10 | sonifi | Sonifi | CD 35.2 vs email PDF variance |
| 11 | jour | Jour | F&B revenue, hébergement, taxes, occupation, KPIs |
| 12 | quasimodo | Quasimodo | Global reconciliation: Transelect cards + Cash vs Jour total |
| 13 | dbrs | DBRS | Daily Business Review Summary (Marriott corporate) |
| 14 | resume | Sommaire | Validation checks + submit/lock |

### API Endpoints (routes/audit/rj_native.py)
All endpoints are under `/api/rj/native/`:

- `GET /session/<date>` — Create or load session for date
- `POST /save/controle` — Save control info
- `POST /save/dueback` — Save dueback entries
- `POST /save/recap` — Save recap fields
- `POST /save/transelect` — Save restaurant + reception data
- `POST /save/geac` — Save GEAC cashout + daily rev + AR
- `POST /save/sd` — Save SD entries
- `POST /save/depot` — Save depot data
- `POST /save/setd` — Save SetD personnel
- `POST /save/hp_admin` — Save HP/Admin entries
- `POST /save/internet` — Save internet fields
- `POST /save/sonifi` — Save sonifi fields
- `POST /save/jour` — Save all jour_* fields
- `POST /save/quasimodo` — Save quasimodo fields
- `POST /save/dbrs` — Save DBRS segments + noshow
- `POST /calculate` — Server-side recalc all computed fields
- `POST /submit/<date>` — Lock session, run final validation

### Frontend JS Architecture (in rj_native.html)
- **Auto-save**: Every input triggers `debounceSave(section)` with 500ms debounce
- **`saveSection(section)`**: Switch statement with 14 cases, POSTs to corresponding API
- **`loadSessionToForm(s)`**: Populates all 14 tabs from session JSON
- **`submitSession()`**: Saves all 14 sections sequentially, then locks
- **`refreshSummary()`**: Updates 12 validation checks in Sommaire tab
- **Recalc functions**: `recalcRecap()`, `recalcTranselect()`, `recalcGeac()`, `recalcDueback()`, `recalcSD()`, `recalcDepot()`, `recalcSetD()`, `recalcHP()`, `recalcInternet()`, `recalcSonifi()`, `recalcJour()`, `recalcQuasimodo()`, `recalcDBRS()`
- **Helper**: `fv(el)` = parse float from input, `fmt(n)` = format as $X,XXX.XX, `round2(n)` = round to 2 decimals
- **Constants**: `TOTAL_ROOMS = 340` (for occupation % calculation)

## Critical Business Rules

1. **Transelect NEVER balances to $0** — The X20 cell (Quasimodo) always shows a variance. The real check is Quasimodo variance (cards + cash vs Jour total) which should be ±$0.01.
2. **AMEX factor = 0.9735** — AMEX amounts in Quasimodo are multiplied by this factor (merchant fee adjustment).
3. **Occupation calculation**: Available rooms = TOTAL_ROOMS (340) − hors_usage. Rooms sold = simple + double + suite + comp.
4. **Internet must be checked BEFORE Part** (03h00). CD 35.2 (Sonifi) also printed before Part.
5. **Jour "Autres revenus"** section is collapsible (toggle) to reduce clutter — auto-opens if any field has a value.
6. **Tab order matters**: Internet/Sonifi come BEFORE Jour (need their data). Quasimodo/DBRS come AFTER Jour (need Jour totals).
7. **Auto-fill Quasimodo**: Pulls card totals from Transelect DOM + cash from Recap deposit fields.
8. **Auto-fill DBRS**: Pulls revenue/ADR/occ%/house count from Jour KPIs.

## Documentation References

- `documentation/back/README.md` — Complete back audit procedure (19 phases with timing)
- `documentation/RJ/00_INDEX.md` — All 38 sheets in the original Excel RJ workbook
- `documentation/RJ/12_procedure_back_complete.md` — Step-by-step back audit workflow
- `documentation/front/sheraton_laval_night_audit_checklist.md` — 46 front desk tasks

## Environment Variables

Copy `env.example` to `.env`:
- `SECRET_KEY` — Flask session secret
- `AUDIT_PIN` — PIN for webapp access

## What's NOT Yet Implemented

From the back audit 19-phase checklist, these are still manual:
- Phase 1-3: Physical setup (printing reports, stapling documents)
- Phase 5: Lightspeed "Part" execution (PMS-side, can't automate)
- Phase 14: HP/Admin is built but doesn't auto-import from scanned invoices
- Phase 17: Cash deposit envelope physical preparation
- Phase 19: Document assembly and filing (physical)
- OTB (On The Books) section in DBRS is defined but not wired to a data source
- Excel export of completed RJ sessions (for archival compatibility)
