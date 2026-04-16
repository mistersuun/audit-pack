# Audit-Pack Documentation

## System Overview

RJ (Rapport de Jour) is a night audit system for Sheraton Laval hotel. It provides a web-based interface for filling Excel workbook sheets used in daily financial reconciliation. The system replaces manual Excel entry with a structured web UI that validates data, auto-fills from parsed documents, and syncs data between sheets.

## Data Flow

```
  SOURCE DOCUMENTS                PROCESSING                    OUTPUT
  ================               ==========                    ======

  Daily Revenue PDF ──┐
  Sales Journal RTF ──┤
  FreedomPay XLSX  ───┼──> Parsers ──> JourMapper ──> RJFiller ──> Excel Workbook
  HP Excel         ───┤       |        .compute_all()  .fill_jour_day()    |
  Advance Dep. PDF ───┘       |                                            |
                              v                                            v
                        structured dict                              jour sheet
                        {field: value}                           (117 columns)

  WEB UI (manual entry)
  =====================
  Tab forms ──> /api/rj/save ──> RJFiller.fill_sheet() ──> Excel cells

  MACRO SYNC (inter-sheet)
  ========================
  Recap H19:N19 ──── envoie_dans_jour() ────> jour BU:CA
  transelect row 38 ── calcul_carte() ──────> jour BI:BN
  DueBack operations ── sync_duback_to_setd() ──> SetD
```

## All 38 Sheets in RJ Workbook

**Core Sheets (web app integrated):**

| # | Sheet | UI Tab | Purpose |
|---|-------|--------|---------|
| 1 | controle | Nouveau Jour | Audit date & metadata setup |
| 2 | Recap | Recap | Cash reconciliation (balance must = $0) |
| 3 | DUBACK# | DueBack | Receptionist cash floats (23 receptionists) |
| 4 | SetD | SD | Employee settlement journal (135 personnel) |
| 5 | depot | Depot | Bank deposit tracking (CDN + US) |
| 6 | transelect | Transelect | Credit card terminal reconciliation |
| 7 | geac_ux | GEAC/UX | PMS balance + card variance (must = $0) |
| 8 | jour | (computed) | Master daily output (117 columns) |
| 9 | rj | (summary) | Report summary with budget comparison |

**Financial & Analysis Sheets:**

| # | Sheet | Purpose |
|---|-------|---------|
| 10 | EJ | GL journal entries (233 rows) |
| 11 | salaires | Labor/payroll by department |
| 12 | Budget | Annual/monthly budget targets |
| 13 | Diff.Caisse# | Cash register variance by register |
| 14 | diff_forfait | Package/forfait reconciliation |
| 15 | AD | F&B departmental analysis (60 cols: all depts + room inventory) |
| 16 | Nettoyeur / somm_nettoyeur | Staff gratuity detail + summary |
| 17 | Massage | Massage service tracking |
| 18 | Vestiaire# | Coat check/wardrobe |
| 19 | SOCAN / résonne | Music royalty tracking |
| 20 | Sonifi / Internet | In-room entertainment & internet revenue |

**Management Reports:**

| # | Sheet | Purpose |
|---|-------|---------|
| 21 | Rapp_p1 | Director Report: Revenue summary vs budget |
| 22 | Rapp_p2 | Director Report: Hours & employees |
| 23 | Rapp_p3 | Director Report: Revenue vs labor by dept |
| 24 | Etat rev | Revenue statement |
| 25 | Ristourne (×2) | Corporate rebate/discount analysis |

**GL Analysis & Utility:** Analyse 101100, Analyse 100401, autre GL, Auditeur, Feuil1/6/7/8

## Documentation Index

### [sheets/](sheets/) — All 38 RJ Workbook Sheets

**Core Sheets (web app integrated):**
- [01_controle.md](sheets/01_controle.md) — Audit date & metadata setup
- [02_recap.md](sheets/02_recap.md) — Cash reconciliation
- [03_dueback.md](sheets/03_dueback.md) — Receptionist cash floats
- [04_sd.md](sheets/04_sd.md) — Employee settlement journal
- [05_depot.md](sheets/05_depot.md) — Bank deposit tracking
- [06_transelect.md](sheets/06_transelect.md) — Credit card terminal reconciliation
- [07_geac_ux.md](sheets/07_geac_ux.md) — PMS balance + card variance
- [08_jour.md](sheets/08_jour.md) — Master daily output overview
- [08_jour_columns.md](sheets/08_jour_columns.md) — Complete 117-column reference
- [09_nettoyeur.md](sheets/09_nettoyeur.md) — Staff gratuities

**Financial & Analysis Sheets:**
- [10_ej.md](sheets/10_ej.md) — GL journal entries (233 entries)
- [11_salaires.md](sheets/11_salaires.md) — Labor/payroll by department
- [12_budget.md](sheets/12_budget.md) — Annual/monthly budget targets
- [13_diff_caisse.md](sheets/13_diff_caisse.md) — Cash register variance
- [14_diff_forfait.md](sheets/14_diff_forfait.md) — Package/forfait tracking
- [15_ad.md](sheets/15_ad.md) — F&B departmental analysis (60 columns)
- [16_minor_sheets.md](sheets/16_minor_sheets.md) — Massage, Vestiaire, SOCAN, Resonne, Sonifi, Internet
- [17_management_reports.md](sheets/17_management_reports.md) — Director Reports (Rapp_p1/p2/p3), Etat rev, Ristourne
- [18_gl_analysis.md](sheets/18_gl_analysis.md) — GL account analysis, Auditeur, working sheets

### [guides/](guides/) — User & Management Guides
- [night_audit_procedure.md](guides/night_audit_procedure.md) — Step-by-step audit workflow
- [installation.md](guides/installation.md) — System setup
- [quickstart.md](guides/quickstart.md) — Get running in 10 minutes
- [revenue_insights.md](guides/revenue_insights.md) — Revenue optimization & profit levers for management

### [dev/](dev/) — Developer Reference
- [parsers.md](dev/parsers.md) — All 11 document parsers
- [mappers.md](dev/mappers.md) — Cell mappings & jour column mapping
- [macros.md](dev/macros.md) — VBA macro equivalents in Python
- [auth.md](dev/auth.md) — Authentication & roles
- [database.md](dev/database.md) — Database schema & models
- [api_reference.md](dev/api_reference.md) — Complete API endpoint reference
- [bi_crossref.md](dev/bi_crossref.md) — BI cross-reference: data sources → CRM analytics

### [architecture.md](architecture.md) — System Architecture

### archive/ — Historical documentation

## Webapp Dashboards

| Page | Route | For | Purpose |
|------|-------|-----|---------|
| Smart Dashboard | `/dashboard` | Auditors | Shift intelligence, KPIs, threshold alerts, recommendations |
| CRM Analytics | `/crm` | Auditors | 7-tab comprehensive BI (Revenue, F&B, Labour, Cash, Payments, P&L) |
| Auditor Panel | `/dashboard` (panel) | Auditors | Error detection: balance grid, outstanding items, variance alerts |
| Direction Portal | `/direction` | GM/Accounting | Executive strategy: Rapp_p1-p3, Etat rev, GL reconciliation, trends |
| GM Briefing | `/dashboard/gm` | GM | Morning briefing with previous night performance + OTB forward look |
| Accounting | `/dashboard/accounting` | Accounting | Month-end close: checklist, revenue verification, data gaps, GL suspense |
| Manager Analytics | `/manager` | Management | GOPPAR, expense tracking, labor efficiency, deep insights |
| STR/OTB | (data models) | Revenue Mgmt | Competitive set indexing (STRCompSet), on-the-books forecasting (OTBForecast) |
| Forecasting | (planned) | Revenue Mgmt | 30-day projected ADR, RevPAR, occupancy from trailing averages |
| Portfolio | (planned) | Corporate | Multi-property view (Property model supports it) |

See [dev/dashboards.md](dev/dashboards.md) for full reference.

## Night Audit Workflow

1. **Nouveau Jour** -- Set the audit date, auditor name, and daily metadata.
2. **Import Docs** -- Upload a ZIP or individual files (Daily Revenue PDF, Sales Journal RTF, FreedomPay XLSX, HP Excel, Advance Deposit PDF).
3. **SD** -- Enter employee settlements, verify deposit totals.
4. **Depot** -- Record bank deposits (auto-filled from SD data).
5. **DueBack** -- Enter receptionist cash balances for the day.
6. **Recap** -- Enter cash readings (lecture/correction pairs), verify balance = $0.
7. **Transelect** -- Verify credit card terminal totals across all card types.
8. **GEAC/UX** -- Final card variance check (cash out vs revenue, must = 0).
9. **Export** -- Download the completed RJ Excel file.
