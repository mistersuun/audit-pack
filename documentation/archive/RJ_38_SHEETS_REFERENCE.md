# RJ (Rapport Journalier) - Complete 39-Sheet Reference

> Hotel Sheraton Laval - 252 rooms
> Updated: 2026-03-23
> Source: Rj 22-03-2026.xls analysis

## Overview

The RJ Excel workbook contains **39 sheets** (35 active + 4 empty placeholders).
Each sheet serves a specific role in the nightly audit reconciliation process.

**Critical sheets** (core data entry): `jour`, `Recap`, `transelect`, `geac_ux`, `DUBACK#`, `SetD`, `controle`
**Auto-calculated sheets** (formula-driven reports): `rj`, `Rapp_p1`, `Rapp_p2`, `Rapp_p3`, `Etat rev`
**Reconciliation sheets** (verify external data): `Sonifi`, `Internet`, `SOCAN`, `resonne`, `Vestiaire#`, `Massage`, `diff_forfait`, `201802 Ristourne`
**Reference/support sheets**: `EJ`, `salaires`, `Budget`, `depot`, `AD`, `Auditeur`, `autre GL`, `Diff.Caisse#`, `Nettoyeur`, `somm_nettoyeur`, `Analyse 101100 autre`, `Analyse 100401`, `Ristourne Analyse`
**Empty placeholders**: `Sheet1`, `Feuil8`, `Feuil6`, `Feuil2`

---

## Sheet Index

| # | Sheet Name | Rows x Cols | Category | Automated? |
|---|-----------|------------|----------|-----------|
| 0 | EJ | 233 x 8 | Reference | Partial (archive parser) |
| 1 | controle | 33 x 92 | Core | Read by system (date, auditor) |
| 2 | Sheet1 | 0 x 0 | Empty | N/A |
| 3 | Analyse 101100 autre | 60 x 92 | Reference | No |
| 4 | Analyse 100401 | 5 x 8 | Reference | No |
| 5 | Diff.Caisse# | 38 x 39 | Reference | No |
| 6 | Feuil8 | 0 x 0 | Empty | N/A |
| 7 | autre GL | 180 x 61 | Reference | No |
| 8 | salaires | 132 x 92 | Reference | Partial (archive parser) |
| 9 | rj | 69 x 95 | Report | Auto-calculated |
| 10 | jour | 233 x 117 | Core | Partial (11 parsers) |
| 11 | Feuil1 | 40 x 98 | Reference | No |
| 12 | depot | 54 x 16 | Support | No |
| 13 | diff_forfait | 44 x 92 | Reconciliation | No |
| 14 | Sonifi | 65 x 94 | Reconciliation | No |
| 15 | Internet | 41 x 94 | Reconciliation | No |
| 16 | SOCAN | 57 x 13 | Reconciliation | No |
| 17 | résonne | 57 x 13 | Reconciliation | No |
| 18 | Vestiaire# | 45 x 7 | Reconciliation | No |
| 19 | DUBACK# | 67 x 23 | Core | Yes (sync_dueback_to_setd) |
| 20 | somm_nettoyeur | 103 x 9 | Reconciliation | No |
| 21 | Nettoyeur | 358 x 36 | Reference | No |
| 22 | SetD | 44 x 167 | Core | Yes (SDParser) |
| 23 | Massage | 36 x 9 | Reconciliation | No |
| 24 | 201802 Ristourne | 34 x 41 | Reconciliation | No |
| 25 | transelect | 40 x 32 | Core | Yes (FreedomPay + TransactionSummary) |
| 26 | Recap | 26 x 14 | Core | Yes (DailyRevenue + SalesJournal + Cashier) |
| 27 | geac_ux | 58 x 20 | Core | Yes (DailyRevenue + FreedomPay + AR + AdvDeposit) |
| 28 | Auditeur | 5 x 2 | Reference | No |
| 29 | Ristourne Analyse | 34 x 7 | Reference | No |
| 30 | AD | 41 x 60 | Reference | No (prior year data) |
| 31 | Budget | 134 x 17 | Reference | Partial (archive parser) |
| 32 | Rapp_p1 | 53 x 9 | Report | Auto-calculated |
| 33 | Rapp_p2 | 33 x 8 | Report | Auto-calculated |
| 34 | Rapp_p3 | 57 x 25 | Report | Auto-calculated |
| 35 | Etat rev | 53 x 8 | Report | Auto-calculated |
| 36 | Feuil6 | 0 x 0 | Empty | N/A |
| 37 | Feuil7 | 28 x 20 | Scratch | No |
| 38 | Feuil2 | 0 x 0 | Empty | N/A |

---

## Detailed Sheet Descriptions

### Sheet 0: `EJ` (Journal Entries)
**Purpose:** General ledger journal entries from source s-ej10.
**Structure:** 236 rows x 14 cols. Each row = one GL posting.
**Columns:** A=GL code, B=CC1, C=CC2, D=Description, E=Date, F=Source, G=Amount
**Sample:** 075001=VENTES CHAMBRES $1,004,903.55
**Automation:** Parsed by `parse_ej_sheet()` in archive extraction, stored in JournalEntry model.

### Sheet 1: `controle` (Control Parameters)
**Purpose:** Master control sheet with audit date, auditor name, property settings.
**Key cells:**
- B2: Auditor name (e.g. "Souleymane Camara")
- B3: Day (DD), B4: Month (MM), B5: Year (YYYY)
- B6: Temperature, B7: Weather condition
- B20: "HOTEL SHERATON LAVAL", B21: 252 (room count)
- B27: Days in month, B28: Date
- H26: Due back du jour (calculated)
- Column C: Field codes (vchmp, vvad, vcie, v_nbch, idate, etc.)
**Automation:** Read by system for date detection and session metadata.

### Sheet 5: `Diff.Caisse#` (Cash Difference)
**Purpose:** Daily cash variance tracking.
**Structure:** Col A=Day (1-31), Col B=Cash difference amount.
**Sample:** Day 22 = -$7,492.88
**Formula:** Feeds jour!C (Diff.Caisse column).

### Sheet 7: `autre GL` (Other General Ledger)
**Purpose:** Daily GL transactions for non-standard accounts.
**Columns:** Abonnement, Transf Bank SCOTIA/BNC, CHQ NSF, Due Back, Mauvaises Creances, diff paiement
**Structure:** Rows 6-37 = daily entries (March 1-31).

### Sheet 8: `salaires` (Payroll)
**Purpose:** Department labor hours and costs.
**Structure:** 132 rows x 92 cols. ~30 departments with hours/rates/totals.
**Departments:** Reception, Reservation, Auditeur, Portier, Club Lounge, Chambre, Preposee, Equipiere, Cuisine, Bar, Buanderie, Maintenance
**Automation:** Parsed by `parse_salaires_sheet()` into DailyLaborMetrics.

### Sheet 9: `rj` (Main RJ Summary)
**Purpose:** Revenue summary report showing JOUR/MOIS A DATE/BUDGET/ECART.
**Structure:** 82 rows x 95 cols. Formula-driven from jour sheet.
**Key rows:**
- Row 5: Balance d'ouverture
- Row 6: Chambres ($29,190.02 today)
- Rows 7-11: F&B by outlet
- Row 12: Total Nourriture
- Row 34: Total Revenus
- Row 49: Total Credit
- Row 67: Balance Fermeture
- Right side (cols I-O): Room statistics (134 rooms, 53.17% occ, ADR $217.84)
- Credit card totals, escompte rates, depot section

### Sheet 10: `jour` (Daily Journal) -- CRITICAL
**Purpose:** Master daily revenue sheet. 117 columns tracking all revenue, payments, taxes, and room stats.
**Structure:** 233 rows x 117 cols.
- Row 0: Section headers
- Row 1: Column codes
- Rows 2-32: Daily data (day 1-31)
- Row 33: Monthly totals
- Rows 35-232: 178 named range mappings (DA-DB columns)

**Column Groups:**
| Cols | Range | Group |
|------|-------|-------|
| A (0) | JOUR | Day number |
| B (1) | bal.ouv | Balance d'ouverture |
| C (2) | Diff.Caisse | Cash difference |
| D (3) | | D formula value |
| E-I (4-8) | Nou/Boi/Bie/Min/Vin | Pause Spesa (Cafe Link) |
| J-N (9-13) | Nou/Boi/Bie/Min/Vin | Piazza/Cupola |
| O-S (14-18) | Nou/Boi/Bie/Min/Vin | Marche La Spesa |
| T-X (19-23) | Nou/Boi/Bie/Min/Vin | Service aux Chambres |
| Y-AC (24-28) | Nou/Boi/Bie/Min/Vin | Banquet |
| AD (29) | Pourboires | Tips |
| AE (30) | Equipement | Equipment |
| AF (31) | Divers | Miscellaneous |
| AG (32) | Location de Salles | Room rental |
| AH-AI (33-34) | SOCAN/Resonne | Music licensing |
| AJ (35) | Tabagie | Tobacco shop |
| AK (36) | Chambres | Room revenue |
| AL-AN (37-39) | Telephone | Inter/Local/Service |
| AO (40) | Valet/Buanderie | Laundry |
| AQ (42) | ST-MARTN ELECTRIQUE | |
| AS (44) | Autres G/L | Other GL |
| AT (45) | Sonifi Film | |
| AV (47) | Location Boutique | |
| AW (48) | Internet | |
| AX (49) | TVQ | Provincial tax |
| AY (50) | TPS | Federal tax |
| AZ (51) | TVH | Harmonized tax |
| BA (52) | Massage | |
| BB (53) | Vestiaire | Coat check |
| BC (54) | Ristournes | Rebates |
| BF (57) | Diff forfait | Package difference |
| BH (59) | TOTAL CREDIT | |
| BI-BN (60-65) | Amex/Disc/MC/Visa/Debit/AmexGlobal | Card payments |
| BQ-BR (68-69) | HP Admin/Hotel Promo | |
| BU (72) | Argent recu | Cash received |
| BV (73) | Remb Serveurs+Debourses | |
| BW (74) | Remb Gratuite | |
| BY (76) | Due back reception | |
| CA (78) | Surplus/Deficit | |
| CB (79) | Cert Cadx | Gift certificates |
| CF (83) | Transfer to A/R | |
| CG (84) | Transfert royal | |
| CH (85) | Tr bancaire | Bank transfer |
| CI (86) | Cash operation | |
| CK-CR (88-95) | Room stats | Simple/Double/Suite/Comp/Client/HU/refaire/Dispo |

**Master Formula:** `C = D - B - (SUM(E:BF) - SUM(BI:CI))`
**D Formula:** `-(DlyRev New Balance) - (Deposit on Hand)`

### Sheet 11: `Feuil1` (Hours by Department)
**Purpose:** Daily labor hours for ~98 department positions.
**Structure:** Rows 7-38 = daily entries, 98 department columns.
**Departments include:** REC_ADM, REC_AUDIT, PIAZZA_ADM, CUISINE, BAR, BUANDERIE, MAINTENANCE, etc.

### Sheet 12: `depot` (Bank Deposits)
**Purpose:** Cash deposit tracking for two Canadian bank accounts.
**Accounts:** Client 6 #1844-22, Client 8 #4743-66
**Structure:** Daily deposit amounts with signatures, organized in 4-week columns.

### Sheet 13: `diff_forfait` (Package Variance)
**Purpose:** Verify package/forfait pricing against invoiced amounts.
**Types tracked:** Club Level, Forfait $75/$63/$87/$90/$98, BRUNCH, ADPQ
**Structure:** Rows 4-34 = daily entries with variance calculation.

### Sheet 14: `Sonifi` (In-Room Entertainment)
**Purpose:** Reconcile in-room movie revenue vs InnVue reports.
**Structure:** Price tiers ($8.95-$32.99), daily entries, InnVue reporting section.

### Sheet 15: `Internet` (DataValet)
**Purpose:** Reconcile internet revenue (DataValet vs RJ).
**Columns:** Rapport LightSpeed, Ajustement, BANQUETS, SPESA, Forfait BNC, RJ, Variance

### Sheet 16: `SOCAN` (Music Rights)
**Purpose:** SOCAN music licensing fee tracking.
**Structure:** Date, $, Event name, Room, Capacity, Dance/No dance rates, RJ, Variance.
**Fee table:** 1-100 rooms: $9.25 no dance / $18.51 dance.

### Sheet 17: `resonne` (Music Rights)
**Purpose:** Re:sonne music rights (identical structure to SOCAN).

### Sheet 18: `Vestiaire#` (Coat Check)
**Purpose:** Coat check revenue reconciliation vs contractor (Interventions).

### Sheet 19: `DUBACK#` (Due Backs) -- CRITICAL
**Purpose:** Track cashier due backs by employee.
**Structure:** 2 rows per day (RJ amount + employee allocations).
**Employees:** ~20 receptionists (Araujo, Caron, THANKARAJAH, CINDY, etc.)
**Formula:** Column Z = SUM(C:Y) for employee total.
**Automation:** `sync_dueback_to_setd` macro syncs to SetD sheet.

### Sheet 20: `somm_nettoyeur` (Laundry Summary)
**Purpose:** Dry cleaning/valet reconciliation.
**Columns:** FACTURE TOTALE, CLIENT, RJ, S.V. (Service Valet), A PAYER, VARIANCE

### Sheet 21: `Nettoyeur` (Laundry Detail)
**Purpose:** Individual employee dry cleaning charges by day.
**Structure:** 378 rows x 39 cols. Organized by department sections.

### Sheet 22: `SetD` (Suivi des Depots) -- CRITICAL
**Purpose:** Core cashier settlement tracking. ~160 employee columns.
**Structure:** 44 rows x 167 cols.
**Headers:** Row 1=Date+departments, Row 2=First names, Row 3=Last names, Row 4=GL codes
**Data:** Rows 5-35 = daily entries, Row 36 = monthly totals.
**Automation:** SDParser with fuzzy name matching fills employee columns.

### Sheet 23: `Massage`
**Purpose:** Spa/massage revenue reconciliation.
**Columns:** MASSAGE RJ, SANS TAXES, FACTURE, VARIANCE

### Sheet 24: `201802 Ristourne` (Rebates)
**Purpose:** Group rebates by client code (~37 group accounts).
**Groups:** Hockey clubs, corporate accounts, wedding blocks, etc.

### Sheet 25: `transelect` (Credit Card Reconciliation) -- CRITICAL
**Purpose:** Reconcile card transactions: POS terminals vs bank reports.
**Section 1 (rows 7-14):** Restaurant/Banquet/Spesa by card type (DEBIT, VISA, MC, DISCOVER, AMEX)
**Section 2 (rows 18-25):** Reception from FreedomPay + Daily Revenue
**Section 3 (rows 27-40):** Summary totals
**Escompte rates:** VISA=1.75%, MC=1.40%, AMEX=2.65%, DISCOVER=2.80%
**Automation:** FreedomPayParser + TransactionSummaryParser fill GEAC row 6 + fusebox rows.

### Sheet 26: `Recap` (Cash Recap) -- CRITICAL
**Purpose:** Daily cash reconciliation.
**Structure:** 26 rows x 15 cols, 5 sections:
1. Comptant (Cash): LightSpeed + Positouch = Total
2. Remboursements: Gratuite + Client + Loterie
3. Due Back: Reception + N/B
4. Depot: US + Canadian + Net
5. Verification: Argent Recu
**Automation:** DailyRevenueParser + SalesJournalParser + CashierSummaryParser.

### Sheet 27: `geac_ux` (GEAC Balance) -- CRITICAL
**Purpose:** Two-part GEAC system reconciliation.
**Part 1 (rows 1-23):** Card balancing (Daily Cash Out vs Daily Revenue by card type)
**Part 2 (rows 25-58):** Guest Ledger / AR / Advance Deposit balance tracking.
**Key values:**
- Row 6: Daily Cash Out (Amex, MC, Visa)
- Row 12: Daily Revenue (should match row 6)
- Row 14: Variance (should be $0)
- Row 32: Balance Previous Day
- Row 44: Advance Deposit (Balance + Applied)
- Row 53: New Balance
**Automation:** DailyRevenueParser + FreedomPayParser + ARSummaryParser + AdvanceDepositParser.

### Sheet 28: `Auditeur` (Auditor Names)
**Purpose:** Dropdown source for auditor selection.
**Names:** Souleymane Camara, Sherley Derisca, Christian Nduwayezu, Taha Abdelmoumen

### Sheet 29: `Ristourne Analyse`
**Purpose:** Rebate journal with GL analysis (account 201802).

### Sheet 30: `AD` (An Dernier / Prior Year)
**Purpose:** Prior year comparison data. Same structure as jour (60 columns).

### Sheet 31: `Budget` (Annual Budget)
**Purpose:** Budget reference data by category.
**Key budgets:** Chambres=$1,396,542; Nour.Piazza=$218,000; Banquet=$125,000; Location=$317,000
**Room budget:** 76.16% occ, $234.71 ADR
**Automation:** Parsed by `parse_budget_sheet()` into MonthlyBudget model.

### Sheets 32-35: Report Sheets (Auto-Calculated)
- **`Rapp_p1`**: Revenue summary (Ce Jour / Ce Mois / Budget)
- **`Rapp_p2`**: Hours & employees by department
- **`Rapp_p3`**: Detailed labor by job position
- **`Etat rev`**: Full P&L income statement

### Sheets 36-38: Empty Placeholders
- `Feuil6`, `Feuil7` (scratch), `Feuil2`

---

## Parser Coverage Map

| Source Document | Parser | Target Sheet | Status |
|----------------|--------|-------------|--------|
| Daily Revenue PDF | DailyRevenueParser | Recap + GEAC + Jour | Active |
| FreedomPay Excel | FreedomPayParser | GEAC Row 6 | Active |
| Transaction Summary | TransactionSummaryParser | Transelect Reception | Active |
| Advance Deposit PDF | AdvanceDepositParser | GEAC Row 44 | Active |
| AR Summary PDF | ARSummaryParser | GEAC balance | Active |
| Cashier Cashout PDF | CashierSummaryParser | GEAC + Recap | Active |
| HP Admin Excel | HPExcelParser | Jour (cols J-S) | Active |
| Sales Journal RTF/TXT | SalesJournalParser | Recap + Transelect + Jour | Active |
| SD Excel | SDParser | SetD | Active |
| Market Segment PDF | MarketSegmentParser | DBRS | Active |
| Server Recap TXT | RecapTextParser | Recap + Transelect | Active |

### Sheets NOT Yet Automated
- Sonifi, Internet, SOCAN, resonne (reconciliation only)
- Vestiaire#, Massage, diff_forfait, Ristourne (manual entry)
- Nettoyeur, somm_nettoyeur (laundry - external vendor)
- depot (bank deposits - manual)
- autre GL, Diff.Caisse#, Analyse sheets (GL analysis)
- salaires, Feuil1 (payroll - from external HR system)

---

## Complete Macro Reference

All original Excel VBA macros have been replicated as Python functions. They are exposed via REST API endpoints and implemented in `utils/rj_filler.py` using cell mappings from `utils/rj_mapper.py`.

### 1. Reset Macros (Clear Sheets for New Day)

These macros clear specific cell ranges in preparation for a new audit day. Each replicates the original VBA `efface_*()` macro.

#### `efface_recap()` / Reset Recap
- **API:** `POST /api/rj/reset/recap`
- **Implementation:** `RJFiller.reset_single_tab('Recap')`
- **What it clears:**
  - B6:C20 (Lecture + Correction columns)
  - D9:D10 (Net column rows 9-10)
  - D12:D14 (Net column rows 12-14)
  - D16 (Net column row 16)
  - D18 (Net column row 18)
- **VBA:** `Range("B6:C20").ClearContents` + `Range("D9:D10,D12:D14,D16,D18").ClearContents`

#### `eff_trans()` / Reset Transelect
- **API:** `POST /api/rj/reset/transelect`
- **Implementation:** `RJFiller.reset_single_tab('transelect')`
- **What it clears:**
  - B9:U13 (POS credit card data — all terminals)
  - X9:X13 (Column X totals)
  - B20:H24 (Bank/FreedomPay report section)
  - J20:P24 (Additional reconciliation columns)
- **VBA:** `Range("B9:U13,X9:X13,B20:H24,J20:P24").ClearContents`

#### `efface_rapport_geac()` / Reset GEAC
- **API:** `POST /api/rj/reset/geac`
- **Implementation:** `RJFiller.reset_single_tab('geac_ux')`
- **What it clears:**
  - Row 6: B6:C6, E6, G6:H6, J6 (Daily Cash Out)
  - Row 8: B8:C8, E8, G8:H8, J8 (Adjustments)
  - Row 12: B12:C12, E12, G12:H12, J12 (Daily Revenue)
  - Row 32: B32:C32, E32 (Balance Previous Day)
  - Row 37: B37:C37, E37 (Balance Today)
  - Row 41: B41:C41, G41:H41 (Facture Direct)
  - Row 44: B44:C44, J44:K44 (Advance Deposit)
  - Row 47: B47:C47, E47 (Transfer to AR)
  - Row 50: B50:C50, E50 (Transfer)
  - Row 53: B53:C53, E53 (New Balance)
- **VBA:** `Range("B6:C6,E6,G6:H6,J6,...,B53:C53,E53").ClearContents`

#### `Eff_depot()` / Reset Depot
- **API:** `POST /api/rj/reset/depot`
- **Implementation:** `RJFiller.reset_single_tab('depot')`
- **What it clears:**
  - A10:K42 (All deposit entry rows)
- **VBA:** `Range("eff_depot").ClearContents` (named range = A10:K42)

#### `eff_daily()` / Reset Daily
- **API:** `POST /api/rj/reset/daily`
- **What it clears:**
  - B2:B41 (Main daily data column)
  - B44 (Single total cell)
  - B47 (Single total cell)

#### Reset All Tabs (Batch)
- **API:** `POST /api/rj/reset`
- **Implementation:** `RJFiller.reset_tabs()`
- **Clears:** Recap + Transelect + GEAC + Depot + Daily in one call
- **Returns:** Total cells cleared count

---

### 2. Data Copy Macros (Inter-Sheet Transfer)

#### `envoie_dans_jour()` — Copy Recap to Jour
- **API:** `POST /api/rj/macro/envoie-jour`
- **Implementation:** `RJFiller.envoie_dans_jour(day=None)`
- **Source:** Recap sheet, row 19 (0-indexed: 18), columns H through N (7-13)
  - H19 = Argent recu
  - I19 = Remb. Serveurs+Debourses
  - J19 = Remb. Gratuite Posi-touch
  - K19 = (unused)
  - L19 = Due back reception
  - M19 = (unused)
  - N19 = Surplus/Deficit
- **Target:** Jour sheet, row = `4 + day - 1`, columns BU through CA (72-78)
  - BU(72) = Argent recu
  - BV(73) = Remb. Serveurs+Debourses
  - BW(74) = Remb. Gratuite
  - BX(75) = (unused)
  - BY(76) = Due back reception
  - BZ(77) = (unused)
  - CA(78) = Surplus/Deficit
- **Day auto-detection:** Reads controle!B3 if `day` not provided
- **VBA equivalent:** `envoie_dans_jour()` in original VBA module

#### `calcul_carte()` — Copy Transelect Card Totals to Jour
- **API:** `POST /api/rj/macro/calcul-carte`
- **Implementation:** `RJFiller.calcul_carte(day=None)`
- **Source:** Transelect sheet, row 14 (0-indexed: 13), columns B through T (1-19)
  - These are the total credit card amounts by type (AMEX, MC, VISA, Debit, etc.)
- **Target:** Jour sheet, row = `4 + day - 1`, starting at column BF (57)
  - Writes up to 19 card total values sequentially
- **Day auto-detection:** Reads controle!B3 if `day` not provided
- **VBA equivalent:** `calcul_carte()` in original VBA module

#### `send_recap_to_jour()` — Alternative Recap Copy
- **API:** `POST /api/rj/recap/send-to-jour`
- **Implementation:** `utils/rj_writer.copy_recap_to_jour(rj_bytes, day)`
- **Alternative implementation** using `rj_writer.py` instead of `RJFiller`
- **Same logic** as `envoie_dans_jour` but operates on raw bytes

---

### 3. Sync Macro (Cross-Sheet Reconciliation)

#### `sync_duback_to_setd()` — Sync DueBack to SetD
- **API:** `POST /api/rj/sync`
- **Implementation:** `RJFiller.sync_duback_to_setd(current_day)`
- **Flow:**
  1. Read DUBACK# sheet header row (row 2 / index 1) to map employee names to columns
  2. Read DUBACK# operations row for the day: `row = 2 + (day * 2) + 1` (0-indexed)
  3. For each employee with a non-zero amount, find their column in SetD
  4. Write the amount to SetD at row `4 + day` in the matching column
- **Name mapping:** `DUBACK_TO_SETD_MAPPING` handles mismatched names between sheets (e.g., "Ramzi" in DUBACK# = "RAMZI" in SetD)
- **Day auto-detection:** Reads controle!B3 if not provided in request body
- **VBA equivalent:** Manual copy/paste in original workflow

---

### 4. Fill Macros (Data Entry)

#### Fill Sheet by Mapping
- **API:** `POST /api/rj/fill/<sheet_name>`
- **Implementation:** `RJFiller.fill_sheet(sheet_name, data_dict)`
- **Sheets supported:** Recap, transelect, geac_ux, controle
- **Uses:** `CELL_MAPPINGS` dict to map field names to Excel cell references
- **Example:** `fill_sheet('Recap', {'comptant_lightspeed_lecture': 1234.56})` writes to B6

#### Fill DueBack
- **API:** `POST /api/rj/fill/dueback`
- **Implementation:** `RJFiller.fill_dueback_day(day, receptionist, amount, line_type)`
- **Row layout:** Day X balance row = `2 + (X * 2)`, operations row = balance + 1
- **24 receptionist columns** (C through Z): Araujo, Latulippe, Caron, Nader, Mompremier, oppong, SEDDIK, Kimberly, AYA, Leo, THANKARAJAH, CINDY, Manolo, MOUATARIF, KRAY, NITHYA, DAMAL, MAUDE, OLGA, Sylvie, Emery, Ben mansour, ANNIE-LIS, Total

#### Fill SetD
- **API:** `POST /api/rj/fill/setd`
- **Implementation:** `RJFiller.fill_setd_day(day, amount, account_col)`
- **Row:** `4 + day` (Day 1 = row 5, Day 31 = row 35)
- **167 columns:** 135 personnel columns (C through EI) + system columns
- **Full personnel mapping** in `SETD_PERSONNEL_COLUMNS` (utils/rj_mapper.py)

#### Fill Jour Day (Computed Values)
- **API:** Called internally by parsers
- **Implementation:** `RJFiller.fill_jour_day(day, jour_values)`
- **Input:** dict of `{column_index: value}` from parser output
- **Target row:** `4 + day - 1` in jour sheet
- **Used by:** `JourMapper.compute_all()` output

#### Update Controle
- **API:** `POST /api/rj/fill/controle`
- **Implementation:** `RJFiller.update_controle(vjour, mois, annee, idate)`
- **Cells:**
  - B3 = Day (vjour)
  - B4 = Month (mois)
  - B5 = Year (annee)
  - B28 = Excel date serial (idate, auto-calculated if day/month/year provided)
- **Excel date serial:** Computed as days since 1899-12-30 (with Excel's leap year bug)

#### Update Deposit
- **API:** `POST /api/rj/deposit`
- **Implementation:** `RJFiller.update_deposit(date_str, amount)`
- **Target sheet:** depot
- **Logic:** Searches column A for matching date, writes amount to column B. If no matching row, appends to first empty row after headers.

---

### 5. Cell Mapping Reference

All mappings are defined in `utils/rj_mapper.py`.

#### Controle Sheet (14 fields)
| Field | Cell | Description |
|-------|------|-------------|
| jour | B3 | Day (DD) |
| mois | B4 | Month (MM) |
| annee | B5 | Year (YYYY) |
| temperature | B6 | Temperature |
| condition | B7 | Weather |
| chambres_refaire | B9 | Rooms to redo |
| prepare_par | B2 | Auditor name |
| dollar_sales_ytd | B10 | YTD dollar sales |
| dollar_sales_prev | B11 | Previous year sales |
| closing_balance | B18 | Closing balance |
| hotel_name | B20 | Property name |
| total_rooms | B21 | 252 |
| days_in_month | B27 | 28/30/31 |
| audit_date | B28 | Excel serial date |

#### Recap Sheet (16 fields)
| Field | Cell | Description |
|-------|------|-------------|
| comptant_lightspeed_lecture | B6 | LightSpeed cash reading |
| comptant_lightspeed_corr | C6 | LightSpeed cash correction |
| comptant_positouch_lecture | B7 | Positouch cash reading |
| comptant_positouch_corr | C7 | Positouch cash correction |
| cheque_payment_register_lecture | B8 | Cheque PR reading |
| cheque_daily_revenu_lecture | B9 | Cheque DR reading |
| remb_gratuite_lecture | B11 | Gratuite refund |
| remb_client_lecture | B12 | Client refund |
| due_back_reception_lecture | B16 | Due back reception |
| due_back_nb_lecture | B17 | Due back N&B |
| surplus_deficit_lecture | B19 | Surplus/deficit |
| argent_recu | B24 | Cash received |

#### Transelect Sheet (22 fields)
| Field | Cell | Description |
|-------|------|-------------|
| bar_701_debit | B9 | Bar 701 debit card |
| bar_701_visa | B10 | Bar 701 VISA |
| bar_701_master | B11 | Bar 701 MC |
| bar_701_amex | B13 | Bar 701 AMEX |
| bar_702_* | C9-C13 | Bar 702 by card |
| bar_703_* | D9-D13 | Bar 703 by card |
| spesa_704_* | E9-E13 | Spesa 704 by card |
| room_705_visa | F10 | Room 705 VISA |
| reception_debit | D20 | Reception debit |
| reception_visa_term | D21 | Reception VISA terminal |
| reception_master_term | D22 | Reception MC terminal |
| reception_amex_term | D24 | Reception AMEX terminal |
| fusebox_visa | B21 | FreedomPay VISA |
| fusebox_master | B22 | FreedomPay MC |
| fusebox_amex | B24 | FreedomPay AMEX |
| quasimodo_* | E20-E24 | Quasimodo reconciliation |

#### GEAC Sheet (18 fields)
| Field | Cell | Description |
|-------|------|-------------|
| amex_cash_out | B6 | AMEX Daily Cash Out |
| diners_cash_out | E6 | Diners Cash Out |
| master_cash_out | G6 | MC Cash Out |
| visa_cash_out | J6 | VISA Cash Out |
| discover_cash_out | K6 | Discover Cash Out |
| amex_daily_revenue | B12 | AMEX Daily Revenue |
| diners_daily_revenue | E12 | Diners Daily Revenue |
| master_daily_revenue | G12 | MC Daily Revenue |
| visa_daily_revenue | J12 | VISA Daily Revenue |
| discover_daily_revenue | K12 | Discover Daily Revenue |
| balance_previous | B32 | Prev day guest ledger |
| balance_today | B37 | Today guest ledger |
| facture_direct | B41 | Direct billing |
| adv_deposit | B44 | Advance deposit balance |
| adv_deposit_applied | J44 | Advance deposit applied |
| new_balance | B53 | Calculated new balance |

---

### 6. Jour Sheet Row/Column Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `JOUR_DAY_ROW_OFFSET` | 4 | Day 1 = row index 4 (Excel row 5) |
| `get_jour_row_for_day(day)` | `4 + day - 1` | 0-indexed row for any day |
| `JOUR_RECAP_COLS` | [72,73,74,75,76,77,78] | Columns BU-CA (envoie_dans_jour target) |
| `JOUR_RECAP_SOURCE` | Recap row 18, cols 7-13 | H19:N19 source range |
| `JOUR_CC_START_COL` | 57 | Column BF (calcul_carte start) |
| `JOUR_CC_SOURCE` | transelect row 13 | Row 14 card totals |
| `JOUR_TOTAL_COLUMNS` | 117 | Total columns in jour sheet |

### 7. DueBack Row Constants

| Function | Formula | Example |
|----------|---------|---------|
| `get_dueback_row_for_day(day)` | balance = `2 + (day * 2)`, ops = balance + 1 | Day 1: (4, 5), Day 22: (46, 47) |

### 8. SetD Row Constants

| Function | Formula | Example |
|----------|---------|---------|
| `get_setd_row_for_day(day)` | `4 + day` | Day 1: row 5, Day 22: row 26 |
