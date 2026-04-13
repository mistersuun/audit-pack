# RJ Sheet Audit -- 38 Sheets (39 actual tabs in workbook)

Audit date: 2026-04-11
Source file: `test_fixtures/2026-03-21/ground_truth_rj.xls`
Webapp template: `templates/audit/rj/rj_native.html`

## Sheet Inventory

| # | Sheet Name | Purpose | Rows x Cols | Webapp Tab | Category | Status | Notes |
|---|---|---|---|---|---|---|---|
| 1 | EJ | Ecritures de Journal -- GL posting entries (code, cc, desc, source, montant). YTD accumulated journal entries for budget/P&L. | 233x8 | `ej` | Read-only | OK | Carried from previous days. Webapp tab shows it read-only. Not editable nightly. |
| 2 | controle | Master control sheet -- auditor name, date (DD/MM/YYYY), temperature, YTD stats (rooms sold, revenue, occupancy), hotel metadata. | 33x92 | `controle` | Semi-auto | OK | Date/auditor auto-set on RJ upload. YTD stats carried forward. Auditor enters temperature/condition. Export fills via `update_controle()`. |
| 3 | Sheet1 | Empty placeholder. | 0x0 | -- | Not needed | N/A | Empty sheet, no purpose. |
| 4 | Analyse 101100 autre | GL account 101100 (Compte Transitoire) analysis -- DT/CT/Solde/Correction columns for transit account reconciliation. | 60x92 | `analyse_101100` | Semi-auto | OK | Webapp has GL analysis tab. Previous balance auto-carried; auditor enters new entries. Variance auto-calculated. |
| 5 | Analyse 100401 | GL account 100401 (Transfer Bancaire) analysis -- same DT/CT/Solde layout as 101100. | 5x8 | `analyse_100401` | Semi-auto | OK | Same as 101100 but for bank transfer account. |
| 6 | Diff.Caisse# | Monthly cash difference tracking -- day 1-31 in rows, with GEAC UX card-type columns. Shows daily cash variance (= -GEAC_UX + Transelect_Restaurant). | 38x39 | `diff_caisse` | Formula | OK | Auto-calculated by `calculate_all()` from GEAC/Transelect. Webapp shows daily diff caisse with reconciliation entries. |
| 7 | Feuil8 | Empty placeholder. | 0x0 | -- | Not needed | N/A | Empty sheet. |
| 8 | autre GL | "Autres Grand Livre" -- monthly GL journal for misc accounts (Abonnement, Transf Bank, CHQ NSF, Due Back, etc.). ~60 columns of GL accounts, daily rows. | 180x61 | `autre_gl` | Read-only | OK | Historical accumulated data. Webapp has `autre_gl` tab (read-only display). Not edited nightly. |
| 9 | salaires | Payroll by department -- Reception, Auditeur, Portier, Commis, Piazza, Banquet, etc. Hours (regular, overtime, escalade), rates, totals. | 132x92 | `salaires` | Read-only | OK | Webapp has `salaires` tab. Data carried from HR/payroll, not night-audit entry. |
| 10 | rj | Main Rapport Journalier summary -- Revenue breakdown (Chambres, Nourriture, Boissons, Location), MTD, Budget, Ecart. Room stats (occupancy, ADR, REVPAR). Deposits. | 69x95 | `rj_rapport` | Formula | OK | Derived from Jour and other sheets via Excel formulas. Webapp tab shows summary from calculated NAS fields (jour_total_revenue, occupancy, etc.). |
| 11 | jour | Daily revenue matrix -- 233 rows (days 1-31 repeated for months), ~117 columns covering ALL F&B departments (Spesa, Piazza, Marche, Banquet, Service Chambres), room revenue, taxes, misc revenue. The core data sheet. | 233x117 | `jour` | Auto | OK | Primary data entry point. Parsers (Daily Revenue, Sales Journal, House Totals, Cashier Summary) auto-fill via `_fill_from_*` functions. Export writes via `fill_jour_day()`. |
| 12 | Feuil1 | Hours detail matrix -- department-level hours (REC_ADM, REC_PROM, REC_AUDIT, PIAZZA_ADM, etc.) per day. Feeds into salaires sheet. | 40x98 | -- | Not implemented | N/A | Supporting data for salaires. Not needed for nightly audit flow -- HR/admin enters this separately. |
| 13 | depot | Bank deposit slip -- Client 6 (compte 1844-22) and Client 8 (compte 4743-66) deposit amounts by date. | 54x16 | `sd` (integrated) | Semi-auto | OK | Webapp integrates depot within the SD tab. `update_deposit()` in filler. Deposit amounts from SD parser feed into Recap CDN/USD. |
| 14 | diff_forfait | Forfait (package) difference tracking -- monthly grid with ~92 columns for various forfait types (Club Level, BNC, ADPQ, etc.) by day. | 44x92 | -- | Not implemented | Missing | No dedicated webapp tab. The `jour_diff_forfait` field exists and is auto-calculated from `forfait_sj + g4_montant` in `calculate_all()`, but the full monthly tracking grid is not implemented. Should have a tab for monthly review. |
| 15 | Sonifi | Sonifi (in-room entertainment) revenue reconciliation -- daily sales by tariff, monthly accumulation. Variance = CD 35.2 - RJ column. | 65x94 | `socan`-area (inline) | Semi-auto | OK | Webapp has Sonifi fields in Jour (jour_sonifi). `calculate_all()` auto-pulls from jour_sonifi to sonifi_email, calculates variance. Monthly detail grid not fully replicated but daily variance tracked. |
| 16 | Internet | Internet/Datavalet revenue reconciliation -- LightSpeed report vs RJ, by day. Includes adjustments (chambre, banquets, forfaits). | 41x94 | -- (inline in Jour) | Semi-auto | OK | Webapp has internet fields in Jour (jour_internet). `calculate_all()` auto-pulls and calculates variance. Monthly detail grid not replicated but daily value tracked. |
| 17 | SOCAN | SOCAN music royalties -- monthly tracking with event name, salle, capacity, dance/no-dance, RJ vs actual variance. | 57x13 | `socan` | Manual | OK | Webapp has SOCAN tab with restaurant/bar/banquet fields and notes. Auditor enters manually when events occur. |
| 18 | resonne | Re:sonne (conference AV) -- same layout as SOCAN. Monthly event charges. | 57x13 | `resonne` | Manual | OK | Webapp has Resonne tab with department/event/hours/tarif/charge entry. |
| 19 | Vestiaire# | Coat check revenue -- monthly tracking by vendor (Interventions/Francois Dubuc). Revenue reconciliation. | 45x7 | `vestiaire` | Manual | OK | Webapp has Vestiaire tab with station/expected/actual/variance. |
| 20 | DUBACK# | DueBack tracking -- daily R/J amount vs receptionist allocation columns (~23 columns for individual receptionists). Two rows per day (previous/nouveau). | 67x23 | `dueback` | Semi-auto | OK | Webapp has DueBack tab. R/J column auto-filled from Recap. Receptionist allocations entered manually. Export fills via `fill_dueback_by_col()`. |
| 21 | somm_nettoyeur | Nettoyeur (dry cleaning) monthly summary -- facture totale, client portion, R/J, S.V., a payer, variance. | 103x9 | `somm_nettoyeur` | Formula | OK | Webapp has Somm.Nett. tab. Values derived from Nettoyeur detail sheet. |
| 22 | Nettoyeur | Nettoyeur detail -- employee-level dry cleaning charges by day (1-31 columns). ~355 rows of employees across departments. | 355x36 | `nettoyeur` | Manual | OK | Webapp has Nettoyeur tab. Employee charges entered manually from dry cleaning invoices. |
| 23 | SetD | SetD (Suivi des Debiteurs) -- daily balance tracking with ~165 columns for individual employee/department accounts. RJ balance, petite caisse, concessions, corrections. | 44x165 | `setd` | Semi-auto | OK | Webapp has SetD tab. RJ balance auto-set from recap_balance in `calculate_all()`. Individual columns are manual. |
| 24 | Massage | Spa/massage revenue -- monthly tracking by day with RJ amount, facture, invoice number. Variance. | 36x9 | `massage` | Manual | OK | Webapp has Massage tab with therapist/service/revenue/tips entry. |
| 25 | 201802 Ristourne | Ristourne (rebate/commission) tracking by client account -- ~41 columns for different client codes (CNAM, Hockey, Cumberland, etc.) by day. | 34x41 | `ristourne` | Manual | OK | Webapp has Ristourne tab. Auditor enters rebate amounts per client. |
| 26 | transelect | Card settlement reconciliation -- Bar (A/B/C), Spesa, Room terminals + Extra terminals. Debit/Visa/MC/Amex/Discover by terminal. Total row. | 40x32 | `transelect` | Auto | OK | Fully auto-filled from FreedomPay (Transaction Summary) parser + Daily Revenue parser. Export writes via `fill_sheet('transelect')`. |
| 27 | Recap | Cash reconciliation -- Comptant (LS/Positouch), Cheques, Remboursements, DueBack, Surplus/Deficit, Deposits. THE primary balancing sheet. | 26x14 | `recap` | Semi-auto | OK | Partially auto-filled (comptant from Daily Rev parser, deposits from SD). Auditor verifies/adjusts corrections. Balance auto-calculated. |
| 28 | geac_ux | GEAC UX card reconciliation -- Amex/Diners/MC/Visa columns. Daily Cash Out vs Daily Revenue comparison. Variance detection. | 58x20 | `geac` | Auto | OK | Auto-filled from Daily Revenue parser (daily_rev) and FreedomPay parser (cashout). Balance auto-calculated. |
| 29 | Auditeur | Auditor reference list -- 4 auditor names. | 5x2 | `auditeur_ref` | Read-only | OK | Reference data. Webapp has Auditeur tab showing list. |
| 30 | Ristourne Analyse | Ristourne analysis -- GL account 201802, daily entries with provenance, debit/credit/solde. | 34x7 | `ristourne` (shared) | Read-only | OK | Supplementary to Ristourne tab. Read-only historical entries. |
| 31 | AD | Administration detail -- daily F&B revenue by outlet (Giotto, Piazza, Marche, Spesa, Banquet, etc.) ~60 columns. Cross-reference for auditor. | 41x60 | `admin_ad` | Read-only | OK | Webapp has AD tab. Data derived from Jour/EJ. Reference only. |
| 32 | Budget | Annual budget reference -- department-level budget amounts, monthly allocations, budget codes (BU_VE_*). | 134x17 | `budget_rj` | Read-only | OK | Webapp has Budget tab. Static reference data loaded from budget CSV import. |
| 33 | Rapp_p1 | Print report page 1 -- "Sommaire des Revenus" formatted for printing. Rooms, Location, Restaurant details. Ce Jour / Ce Mois / Budget. | 53x9 | `rapp_p1` | Formula | OK | Webapp has P1 tab. Values derived from Jour/RJ calculations. Print layout. |
| 34 | Rapp_p2 | Print report page 2 -- "Sommaire Heures & Employes". Department hours (fixed/variable), employees/day. | 33x8 | `rapp_p2` | Formula | OK | Webapp has P2 tab. Values from salaires/Feuil1. Currently shows zeros for Ce Jour (no live salaires input). |
| 35 | Rapp_p3 | Print report page 3 -- Detailed revenue/hours/salaries by sub-department. Journalier + Mensuel + Budget columns. | 57x25 | `rapp_p3` | Formula | OK | Webapp has P3 tab. Computed from Jour + salaires data. |
| 36 | Etat rev | "Etat des Revenus et Depenses" -- P&L style statement. Room revenue/salaries/benefits/variable costs, F&B margins. | 53x8 | `etat_rev` | Formula | OK | Webapp has Etat Rev tab. Derived from EJ/Jour/Budget. |
| 37 | Feuil6 | Empty placeholder. | 0x0 | -- | Not needed | N/A | Empty sheet. |
| 38 | Feuil7 | Scratch/working sheet -- unlabeled numerical data, appears to be DueBack or SD working calculations. No headers. | 28x20 | -- | Not needed | N/A | Internal scratch sheet with no formal purpose. Not needed in webapp. |
| 39 | Feuil2 | Empty placeholder. | 0x0 | -- | Not needed | N/A | Empty sheet. |

## Webapp-Only Tabs (no Excel sheet equivalent)

| Webapp Tab | Purpose | Notes |
|---|---|---|
| `resume` | Session summary dashboard -- shows all balance checks (Recap, Transelect, GEAC, DueBack, SD, Depot, Jour, HP, Quasimodo, DBRS, Diff.Caisse) with pass/fail status. Export + Submit buttons. | Webapp-only. Essential for audit workflow. |
| `quasimodo` | Cross-check total: (Transelect cards + Recap cash) vs Jour total revenue. Amex net factor applied. | Webapp-only calculation. Excel does this via formulas across sheets. |
| `hpadmin` | HP/Admin (Hotel Promotions) -- BQ tips, complimentary meals, promo entries deducted from F&B revenue. | Webapp-only dedicated tab. Excel distributes HP entries across Jour columns. |
| `dbrs` | Daily Business Review Summary -- occupancy, ADR, RevPAR, market segment breakdown. | Webapp-only. Excel computes from rj/jour sheets. |
| `analyse_gl` | Combined GL analysis (101100 + 100401) in one interface. | Webapp combines two Excel sheets into one tab. |

## Priority Fixes

### Missing tabs that matter for nightly audit:

1. **diff_forfait** (Sheet 14) -- The monthly forfait difference grid is not implemented as a dedicated tab. Currently only `jour_diff_forfait` is auto-calculated as a single daily value. The Excel sheet tracks ~92 columns of forfait types (Club Level, BNC, ADPQ, various hotel packages) with daily rows -- this is needed when the auditor investigates forfait discrepancies. **Priority: Medium** -- the daily calculation works, but monthly review/drill-down is missing.

### Partially implemented / data gaps:

2. **Sonifi** (Sheet 15) -- Daily variance works (jour_sonifi field), but the full monthly reconciliation grid (65 rows x 94 cols with individual tariff breakdown: $8.95, $9.95, $10.95, etc.) is not replicated. The auditor cannot drill into which tariff caused a variance. **Priority: Low** -- rarely has issues.

3. **Internet** (Sheet 16) -- Same situation as Sonifi. Daily value tracked in Jour, but the monthly reconciliation with LightSpeed report / adjustment columns is not replicated. **Priority: Low** -- simple daily tracking suffices.

4. **Rapp_p2** (Sheet 34) -- Hours/employees report shows all zeros for "Ce Jour" because there is no live salaires input mechanism. The webapp has the tab but it is essentially empty for daily data. **Priority: Low** -- HR data, not night-audit critical.

5. **Feuil1** (Sheet 12) -- Hours detail matrix that feeds salaires. No webapp tab, but this is HR/admin data, not night-audit. **Priority: None**.

## Automation Opportunities

| Sheet | Current | Potential | How |
|---|---|---|---|
| SOCAN (#17) | Manual | Semi-auto | If banquet event system provides event data, could pre-populate event names/salles/capacities. Currently rare enough that manual entry is fine. |
| Nettoyeur (#22) | Manual | Semi-auto | If dry cleaning vendor provides electronic invoices (PDF/CSV), a parser could extract employee-level charges. Currently paper invoices. |
| Massage (#24) | Manual | Semi-auto | If spa booking system exports data, could auto-populate. Currently manual from paper receipts. |
| Vestiaire (#19) | Manual | Semi-auto | If coat check vendor provides electronic reports, could auto-fill. Currently manual. |
| Ristourne (#25) | Manual | Semi-auto | If Marriott commission reports are available electronically, could parse. Currently manual tracking. |
| Rapp_p2 (#34) | Formula (empty) | Auto | Could auto-fill from payroll system if hours data were imported. Currently no payroll integration. |

## Summary Statistics

- **Total sheets in workbook**: 39
- **Empty/placeholder sheets**: 4 (Sheet1, Feuil8, Feuil6, Feuil2)
- **Scratch sheets**: 1 (Feuil7)
- **Sheets with webapp tabs**: 34 (including webapp-only tabs)
- **Fully automated (parser-fed)**: 3 (jour, transelect, geac_ux)
- **Semi-automated (parser + manual verify)**: 7 (controle, Recap, DueBack, SetD, Analyse 101100, Analyse 100401, depot)
- **Formula/computed**: 6 (rj, Diff.Caisse, somm_nettoyeur, Rapp_p1, Rapp_p2, Rapp_p3, Etat rev)
- **Manual entry**: 5 (SOCAN, Resonne, Vestiaire, Nettoyeur, Massage, Ristourne)
- **Read-only/reference**: 5 (EJ, autre GL, salaires, Auditeur, AD, Budget, Ristourne Analyse)
- **Not implemented (no webapp tab)**: 1 (diff_forfait monthly grid)
- **Not needed in webapp**: 5 (Sheet1, Feuil8, Feuil6, Feuil7, Feuil2)

## STATUS: DONE
