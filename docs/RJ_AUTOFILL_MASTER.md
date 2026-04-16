# RJ Auto-Fill Master Reference

**Purpose:** Complete authoritative spec for auto-filling a daily RJ.xls workbook from uploaded source documents. Captures every rule, exception, and gotcha learned through direct user correction sessions.

**Hotel:** Sheraton Laval (252 rooms). RJ = Rapport Journalier (daily night-audit workbook).

**Last updated:** 2026-04-15 after extensive user correction.

---

## 1. Required source documents (per day)

| Document | Format | Used for |
|---|---|---|
| Daily Revenue (DR) | PDF, 7 pages | Chambres, Autres revenus, Taxes, Settlements, Adv Dep, New Balance |
| Sales Journal (SJ) | TXT | F&B by department, payment modes, HP totals, Pourboires, DEPOT UTIL |
| AR Summary | PDF/XLS | Guest Folios (= FD), AR adjustments, AR Misc |
| Cashier Cashout | TXT | Daily Cash Out per card per cashier |
| Advance Deposit | XLS | Deposits on Hand Today (for Bal_Ferm) |
| HP file | XLSX | HP deductions per F&B category, Pourboires Admin/Promo |
| Market Segment | PDF/XLS | Occupancy/ADR by segment |
| DBRS | XLS | Arrivals/Departures/Stayovers, room counts |
| GLedger | XLS | Guest Ledger detail (cross-reference) |
| COMP_ROOM | TXT | Complimentary rooms (CN col) |

## 1b. CRITICAL: Daily Revenue must be POST-AUDIT

The DR PDF must be run **AFTER the night audit posting** (typically 3:00-5:00 AM). A pre-audit DR (e.g., timestamped 12:59 AM) will be **missing most room charges, taxes, and settlement adjustments**.

**How to verify:** Check the DR header timestamp. If it says anything before ~3:00 AM, it's likely pre-audit and missing:
- Room charges ($50,000+ typically missing)
- Taxe Hébergement / TPS Chambres / TVQ Chambres (proportionally missing)
- Facture Direct (may show a partial amount)
- Advance Deposit DNA (may show 0)
- InterHotel XferIn (may show 0)
- Balance Today / New Balance (will be wrong)
- Autre A Payer Taxable (may show 0)

**Impact of using pre-audit DR:** Chambres (AK) will be off by ~$50K+, taxes (AX/AY/AZ) off by ~$10K+, Bal_Ferm (D) completely wrong. DC will be off by $60K+ — impossible to diagnose.

**Real example (April 15, 2026):**
| Item | Pre-audit (12:59 AM) | Post-audit (correct) |
|---|---|---|
| Chambres Total | $499.01 | **$55,052.42** |
| TVH | $17.50 | **$1,927.72** |
| TPS Chambres | $25.81 | **$2,849.00** |
| New Balance | -$1,543,520.25 | **-$1,482,382.27** |
| InterHotel XferIn | $0 | **$19.98** |

**Rule:** If DR timestamp is before 3:00 AM, REJECT the file and ask for the post-audit version. The webapp should validate this automatically.

## 2. User-provided manual inputs

These cannot be derived from the documents and must be supplied by the auditor:
- **G4** — Club Lounge / accommodation production deduction for Chambres
- **F&B adjustments** — minor correction amounts (e.g., Piazza adj 2.96, Spesa adj 4.05)
- **X24 compensation strategy** — usually NONE (leave DC = X24, document in comment)

## 3. Tools

| Tool | Purpose |
|---|---|
| `pdfplumber` | PDF parsing (DR, AR Summary, Market Segment) |
| `xlrd` | Read .xls (read-only, has cached values not formulas) |
| `openpyxl` | Read .xlsx (HP file) |
| `pywin32` (`win32com.client`) | **Write .xls** via Excel COM (preserves formulas/colors/macros) |
| `python-docx` | Read reference .docx files |

## 4. CRITICAL: Write-back via Excel COM only

**NEVER use `xlutils.copy`** — it silently destroys all formulas, tab colors, and embedded macros (file shrinks ~470 KB). The audit-pack project's `RJFiller` currently uses xlutils — this is a bug.

**Correct write pattern:**
```python
import win32com.client as win32

excel = win32.Dispatch('Excel.Application')
excel.Visible = False
excel.DisplayAlerts = False
excel.AskToUpdateLinks = False

wb = excel.Workbooks.Open(r'K:\path\to\Rj DD-MM-YYYY.xls')
ws = wb.Sheets('jour')

# 1-indexed rows/cols
cell = ws.Cells(row, col)
if cell.HasFormula and cell.Formula != f'={cell.Value}':
    pass  # SKIP — existing computed formula
else:
    cell.Formula = '=2384.64-7061'  # write as audit-trail formula

wb.Save()
wb.Close()
excel.Quit()
```

**Always backup first:** `shutil.copy2(src, src + '.bak.xls')` before any COM write.

## 5. Write formulas, not values

The auditor must SEE where each number came from. Past auditors write decomposed formulas:
- `CF16 = =2384.64-7061` (FD - AR Misc), not `-4676.36`
- `AY16 = =2623.45+1528.09+12.9` (TPS chamb + SJ + Autres), not `4164.44`
- `J16 = =3585-612-2.96` (SJ - HP - adj), not `2970.04`
- `AK16 = =50695.88-40` (DR - G4), not `50655.88`
- `BF16 = =-(170.16-40)`, not `-130.16`
- `D16 = =-1476889.24-455273.04`, not `-1932162.28`

## 6. Fill order (per day)

1. **Backup** the .xls
2. **Read all source documents** into a unified dict
3. **Transelect**: fill POSITOUCH (col X) for restaurant + Reception cols B and P (col I auto)
4. **GEAC_UX**: fill top (card variance R6/R8/R12) + bottom (R32/R37/R41/R44/R53)
5. **Recap macro**: confirm BU/BV/BW/BY/CA already filled (envoie_dans_jour macro)
6. **JOUR row**: fill all manual cells with `=formula` decompositions
7. **Verify DC** in C[row]: should be 0 OR equal to Transelect X24 (+/- GEAC AP + Recap)
8. **Document DC source** in C[row] cell comment

## 7. Sheet-by-sheet fill rules

### 7.1 TRANSELECT

**Restaurant section (rows 9-14)** — POS terminal totals vs Positouch:

| Cell | Fill from | Notes |
|---|---|---|
| X9 (POSITOUCH DEBIT) | SJ INTERAC **+ SJ PANNE INTERACT** | Add panne to card total |
| X10 (POSITOUCH VISA) | SJ VISA **+ SJ PANNE VISA** | Add panne to card total |
| X11 (POSITOUCH MASTER) | SJ MASTERCARD **+ SJ PANNE MASTER** | Add panne to card total |
| X13 (POSITOUCH AMEX) | SJ AMEX **+ SJ PANNE AMEX** | Add panne to card total |
| Y9-Y14 (VARIANCE) | FORMULA — auto | X24 = TOTAL1 - POSITOUCH |
| Cols B-U | (already filled per terminal) | Don't touch |

**Reception section (rows 21-25)** — bank-side reconciliation:

| Cell | Fill from | Notes |
|---|---|---|
| B21 (Bank Report VISA) | DR Settlements VISA (abs) | FreedomPay = DR |
| P21 (Daily Revenue VISA) | Same as B21 | |
| I21 (TOTAL VISA) | FORMULA — DO NOT WRITE | |
| B22 (Bank Report MASTER) | DR Settlements MC (abs) | |
| P22 (Daily Revenue MASTER) | Same as B22 | |
| B24 (Bank Report AMEX) | DR Settlements AMEX (abs) | |
| P24 (Daily Revenue AMEX) | Same as B24 | |
| X20 (DEBIT col 23) | X24 carry-down (= Y14 value) | |

### 7.2 GEAC_UX

**Top — Card Variance section (rows 6-12):**

| Cell | Fill from | Formula |
|---|---|---|
| B6 (AMEX Cash Out) | DR Settlement AMEX abs - DR Dep Rcvd AMEX | `=5613.06-0` |
| G6 (MASTER Cash Out) | DR Settlement MC abs - DR Dep Rcvd MC | `=17789.51-5953.94` |
| J6 (VISA Cash Out) | DR Settlement VISA abs - DR Dep Rcvd VISA | `=15185.17-3127.87` |
| B8 (AMEX Dep Rcvd) | DR p.6 Dep Recvd AMEX | `=0` |
| G8 (MASTER Dep Rcvd) | DR p.6 Dep Recvd MC | `=5953.94` |
| J8 (VISA Dep Rcvd) | DR p.6 Dep Recvd VISA | `=3127.87` |
| B10/G10/J10 (Total) | FORMULA — auto = R6+R8 | (don't write) |
| B12 (AMEX Daily Revenue) | DR Settlement AMEX abs | `=5613.06` |
| G12 (MASTER Daily Revenue) | DR Settlement MC abs | `=17789.51` |
| J12 (VISA Daily Revenue) | DR Settlement VISA abs | `=15185.17` |

Variance check: J14 (formula) = total - daily revenue → should be ~0.

**Bottom — GEAC Balance Sheet (rows 32-53):**

| Cell | Fill from | Notes |
|---|---|---|
| B32 | DR p.7 Balance Prev Day (abs) | |
| E32 | Same value | mirror |
| B37 | DR p.7 Balance Today (abs) | |
| E37 | -B37 (signed negative) | |
| B41 | DR p.6 Facture Direct (abs) | |
| G41 | AR Summary Guest Folios | should = B41 |
| B44 | DR p.7 Adv Dep Applied (abs) | |
| J44 | Same value | mirror |
| B53 | DR p.7 New Balance (abs) | |
| E53 | Same value | mirror |

### 7.3 JOUR — column-by-column fill

**Row offset:** Day N = Excel row N+2 (e.g., Day 14 = row 16).

**Cells with built-in formulas — DO NOT OVERWRITE:**
- A: day number (might be value)
- **B (Bal_Ouv)** = `=D[prev_row]` — chained from prior day
- **C (DC)** = `=D[r]-B[r]-(SUM(E[r]:BF[r])-SUM(BI[r]:CI[r]))` — auto-computes
- **BH (TOTAL CREDIT)** — auto-sum
- **CW-CZ (escompte calcs)** = `=ROUND(+BI[r]*CS[r],2)` etc.
- **DG-DK (category totals)** = `=SUM(E[r]+J[r]+O[r]+T[r]+Y[r])` etc.

**Manual fill cells (formulas with audit trail):**

| Col | Letter | Header | Source rule | Formula example |
|---|---|---|---|---|
| 4 | D | bal.ferm | -|DR p.7 New Balance| - Adv Dep on Hand | `=-1476889.24-455273.04` |
| 5 | E | Nou_Link / Pause Spesa | SJ Bqt PAUSE SPESA + Piazza PAUSE SPESA | `=2626` |
| 10 | J | Nou_piazza | SJ Piazza NOURRITURE - HP Piazza Nour - adj | `=3585-612-2.96` |
| 11 | K | Boi_piazza | SJ Piazza ALCOOL - HP Piazza Boisson | `=1550-47` |
| 12 | L | Bie_piazza | SJ Piazza BIERES - HP Bières | `=539.5` |
| 13 | M | Min_piazza | SJ Piazza NAB - HP Piazza Min | `=156.5-65.5` |
| 14 | N | Vin_piazza | SJ Piazza VINS - HP Piazza Vin | `=539-84` |
| 15 | O | Nou_mar | SJ SPESA NOURRITURE - HP Tabagie Nour - adj | `=1223.89-7-4.05` |
| 20 | T | Nou_schbr | SJ CHAMBRES NOURRITURE | `=226` |
| 22 | V | Bie_schbr | SJ CHAMBRES BIERES | `=11` |
| 23 | W | Min_schbr | SJ CHAMBRES NAB | `=4.25` |
| 24 | X | Vin_schbr | SJ CHAMBRES VINS | `=28` |
| 25 | Y | Nou_bqt | SJ BANQUET NOURRITURE - HP Bqt | `=8410` |
| 26 | Z | Boi_bqt | SJ BANQUET ALCOOL (signed) | |
| 27 | AA | Biere Banquet | SJ BANQUET BIERES (signed) | |
| 28 | AB | Min_bqt | SJ BANQUET NAB | |
| 29 | AC | Vin_bqt | SJ BANQUET VINS | |
| 30 | AD | Pourboires | SJ Pourb à Payer (sum across all depts) | `=1986.48` |
| 31 | AE | Equipement | SJ Banquet EQUIP AUDIO VISUEL (signed) | |
| 32 | AF | Divers Bqt | SJ Banquet EQ. DIVERS (signed) | `=80` |
| 33 | AG | Location de Salles | SJ Bqt LOC SALLE + Piazza LOC SALLE | `=9300` |
| 34 | AH | SOCAN | SJ Banquet SOCAM | |
| 36 | AJ | Tabagie | SJ Spesa TABAGIE - HP Tabagie Tab | `=1021.03-245.44` |
| 37 | AK | Chambres | DR p.1 Chambres Total - **G4** | `=50695.88-40` |
| 38 | AL | Tel.Interurb | DR Telephone Interurbain | |
| 39 | AM | Tel.Local | DR Telephone Local | |
| 40 | AN | Tel.Frais.Serv. | DR Frais De Service | |
| 41 | AO | Valet/Buanderie / Nettoyeur | DR p.2 Nettoyeur | `=257.8` |
| 42 | AP | Mch/Liqueur | -(FD - AR Guest Folios), 0 if FD=AR | `=0` |
| 45 | AS | Autres G/L | DR p.2 Autres GL Total - SJ DEPOT UTIL | `=-157384.06` |
| 46 | AT | Sonifi Film | DR p.2 Sonifi | |
| 47 | AU | Autre Rev. | SJ FR/Étage + DR Lit Pliant + DR Non-Tax + DR p.7 InterHotel XferIn | `=18` |
| 48 | AV | Location Boutique | DR p.2 Location de Boutique | |
| 49 | AW | Internet | **DR Internet (signed, often negative!)** + SJ Bqt INTERNET + **DR InterHotel XferIn (p.7)** — ALL THREE components every time | `=-17.38+460+19.98` |
| 50 | AX | TVQ | DR TVQ Chambres + SJ TVQ + DR TVQ Autres + DR TVQ Internet + DR TVQ Tel. **NO F&B OPERA TAXES** | `=5231.01+3047.97+25.71` |
| 51 | AY | TPS | DR TPS Chambres + SJ TPS + DR TPS Autres + DR TPS Internet + DR TPS Tel + DR TPS Compt. **NO F&B OPERA TAXES** | `=2623.45+1528.09+12.9` |
| 52 | AZ | TVH | DR Taxe Hebergement | `=1775.29` |
| 53 | BA | Massage | DR p.2 Massage | |
| 54 | BB | Vestiaire | SJ Banquet VESTIAIRE | |
| 55 | BC | Ristournes | DR p.2 Autre A Payer Taxable | |
| 58 | BF | Difference forfait | -(SJ FORFAIT - G4) | `=-(170.16-40)` |
| 61 | BI | Amex ELAVON | (auto from calcul_carte macro = Transelect TOTAUX) | |
| 62 | BJ | Discover | **0** unless explicit X24 compensation | `=0` |
| 63 | BK | Master Charge | (auto from calcul_carte macro) | |
| 64 | BL | Visa | (auto) | |
| 65 | BM | Carte Debit | (auto) | |
| 66 | BN | Amex GLOBAL | (auto) | |
| 69 | BQ | H/P Administration 14 | HP file Journalier row 32 col Admin Pourb (POSITIVE) | `=36.99` |
| 70 | BR | Hotel Promotion 15 | HP file Journalier row 32 col Promo Pourb (POSITIVE) | `=76.35` |
| 73 | BU | Argent recu | (auto from envoie_dans_jour macro = Recap Argent Reçu) | |
| 74 | BV | Remb. Serveurs + Déboursés | (auto from macro = -DR Remb Serveur) | |
| 75 | BW | Remb. Gratuité Posi-touch | (auto = -SJ Pourboire Charge) | |
| 77 | BY | Due back reception | (auto = -Recap Due Back Réception) | |
| 79 | CA | Surplus/Def | (auto = Recap Surplus/Déficit) | |
| 80 | CB | Cert Cadx | DR Certificat Cadeaux + others | |
| 81 | CC | Bon D'achat | DR Bon D'Achat | |
| 84 | CF | transfer to A/R | **DR Facture Direct - DR AR Misc** (AR Misc as NEGATIVE) | `=2384.64-7061` |
| 89 | CK | SIMPLE | **FORMULA: =TotalRoomsSold-CM** — do NOT overwrite | |
| 91 | CM | SUITE | **Unknown source — do not auto-fill** (user enters manually) | |
| 92 | CN | COMP. | Market Segment T62 Complimentary Rooms today | |
| 93 | CO | # CLIENT | Market Segment TOTAL Guests today | |
| 94 | CP | HORS D'USAGE | DBRS OOO (out of order) rooms | |
| 95 | CQ | CH. a refaire | **Unknown source — do not auto-fill** (user enters manually) | |
| 95 | CR | DISPONIBLE | typically 252 (total rooms) | |
| 96-99 | CS-CV | escompte rates | constants: AMEX 0.0265, Discover 0.028, MC 0.014, Visa 0.017 | |

## 8. The 3 acceptable DC variance sources

DC must equal one of (or sum of) these — anything else is an error:

| Source | Where | Acceptance |
|---|---|---|
| **Transelect X24** | Col Y14 (POSITOUCH vs Bank) | DC = X24 OK; document in comment "Transelect: ${X24}" |
| **GEAC AP** | Col 41 (FD vs AR variance) | If FD ≠ AR, AP = -(FD - AR) compensates |
| **Recap I10** | Surplus/Déficit, already in CA | Auto-handled |
| **PANNE LIEN** | When a card terminal failed and posted to suspense | Document in comment |

**Rule:** If DC ≠ 0 with attribution to one of these 3 sources, the day is VALID. Document the attribution as a cell comment on C[row]:
- Single source: `"TRANSELECT: 685.66"`
- Multi-source: `"transelect: 880.62 + geac: -423.73 + débalancement: -242.22"`
- With panne lien: `"TRANSELECT: 14.22 + 12.93 Discover was posted as a panne lien"`

**DC = 0 with auditor notes** (e.g., "désbalancement autre: 1476.06 + deb chbre: 138.42") = **balanced day with documentation of items that were properly classified**, NOT hidden imbalance.

## 9. Common DC errors and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| DC = + AR Misc amount | AR Misc not entered as negative in CF | CF = FD - AR Misc |
| DC = sum of F&B OPERA TPS+TVQ | F&B OPERA taxes wrongly added to AY/AX | Remove them; AY/AX use only Chamb+SJ+Autres |
| DC ≈ ±9.99 / 19.98 / 49.95 | InterHotel XferIn missing from AW | Add DR p.7 InterHotel to AW |
| DC ≈ ±small amount matching DR Internet value | DR Internet (negative) not included in AW | AW = DR Internet (signed!) + SJ Bqt Internet + InterHotel. DR Internet is often negative — don't assume 0 |
| DC ≈ 2× DR Internet magnitude | Sign flip on AW Internet | Negate (DR Internet is often negative) |
| DC = total HP Promo | HP Promo not deducted from F&B credits | Deduct Admin+Promo from J/O/AJ |
| DC = HP pourboires sum (~$113) | BQ/BR not entered | Fill BQ=Admin pourb, BR=Promo pourb (positive) |
| DC = DEPOT UTIL amount | DEPOT UTIL handled wrong | AS = DR Autres GL - DEPOT UTIL; CF = FD only (don't subtract DEPOT UTIL from CF) |
| DC matches a specific DR Today value | That DR item not in any Jour column | Find the column (Nettoyeur AO, Sonifi AT, Massage BA, etc.) |
| Tab colors gone, formulas broken, file shrunk | xlutils.copy was used | RESTORE FROM BACKUP, never use xlutils on .xls |

## 10. Special-case rules

### 10.1 AW (Internet) — THREE components, never skip any
AW = DR Internet (signed) + SJ Bqt INTERNET + DR InterHotel XferIn (p.7)

**DR Internet** is often NEGATIVE (corrections, adjustments). Never assume 0 — always check DR p.2 Internet Today value and preserve the sign.

**InterHotel XferIn** goes to AW, NOT AU. Often $9.99 weekday, $49.95 Sunday (5-day accumulation). Check DR p.7 every time.

**Real example (April 15, 2026):** AW = -17.38 + 460 + 19.98 = 462.60. Missing the -17.38 caused DC to be off by exactly $17.38.

### 10.2 AR Misc
Goes to **CF as negative**. CF = DR FD - DR AR Misc. So if AR Misc = +7,061, CF = FD - 7,061.

### 10.3 DEPOT UTIL
- Goes to **AS** as deduction: AS = DR Autres GL - SJ DEPOT UTIL
- Does NOT go to CF. Common error: subtracting DEPOT UTIL from CF too.

### 10.4 Club Lounge (G4)
- AK = DR Chambres Total - G4 (where G4 = SJ Forfait amount that's actually Club Lounge accommodation)
- BF = -(SJ Forfait - G4)
- User must provide G4 value (can't be derived)

### 10.5 Sunday batch
- Sat+Sun bank deposits arrive together Monday → Sunday X24 is POSITIVE (bank > Positouch)
- Sunday BJ would be NEGATIVE if compensating
- Sunday InterHotel often $49.95 (5-day accumulation)

### 10.6 X24 compensation strategy
**Default: don't compensate.** Leave BJ = 0, accept DC = X24 as Transelect variance. Document in C cell comment.

If explicitly compensating (rare):
- Enter -X24 in Transelect Discover row 11 col 24, OR
- Enter -X24 directly in Jour BJ

## 11. JOUR cell formula reference (Day 13 pattern)

These formula patterns will exist in your template — DO NOT overwrite them:

```
B[r] = =D[r-1]                                          (Bal_Ouv chains from prev day)
C[r] = =D[r]-B[r]-(SUM(E[r]:BF[r])-SUM(BI[r]:CI[r]))   (DC formula)
CW[r] = =ROUND(+BI[r]*CS[r],2)                          (net AMEX)
CX[r] = =ROUND(+BJ[r]*CT[r],2)                          (net Discover)
CY[r] = =ROUND(+BK[r]*CU[r],2)                          (net Master)
CZ[r] = =ROUND(+BL[r]*CV[r],2)                          (net Visa)
DG[r] = =SUM(E[r]+J[r]+O[r]+T[r]+Y[r])                  (Nourriture total)
DH[r] = =SUM(F[r]+K[r]+P[r]+U[r]+Z[r])                  (Alcool total)
DI[r] = =SUM(G[r]+L[r]+Q[r]+V[r]+AA[r])                 (Bières total)
DJ[r] = =SUM(H[r]+M[r]+R[r]+W[r]+AB[r])                 (Minéraux total)
DK[r] = =SUM(I[r]+N[r]+S[r]+X[r]+AC[r])                 (Vins total)
CK[r] = =243-CM[r]                                      (Simple rooms = 243-Comp)
```

## 12. Verification checklist (after fill)

- [ ] File still 2.27 MB (or original size) — formulas/macros intact
- [ ] Tab colors preserved
- [ ] BU/BV/BW/BY/CA filled by Recap macro
- [ ] BI-BN filled by calcul_carte macro from Transelect TOTAUX
- [ ] GEAC card variance row 14 = 0 (or near-zero floating-point)
- [ ] Transelect Restaurant Y14 = X24 variance (often non-zero, that's OK)
- [ ] Recap Total dépôt net = Dépôt Canadien (internally consistent)
- [ ] Jour C[r] (DC) = 0 OR = sum of (X24 + GEAC + Recap I10 + manual)
- [ ] DC source documented in C[r] cell comment
- [ ] B[r+1] auto-references D[r] (chain unbroken)

## 13. Webapp implementation notes

For the audit-pack Flask app to do this end-to-end:

1. **Replace `RJFiller` (currently uses xlutils)** with `RJFillerCOM` using pywin32 + Excel.
2. **Parser updates needed:**
   - `DailyRevenueParser`: extract pp.1-7 fully (Chambres, Autres, Taxes, Settlements, Adv Dep, New Balance)
   - `SalesJournalParser`: extract F&B by dept + payment modes + DEPOT UTIL + HP totals + PANNE amounts
   - `ARSummaryParser`: extract Guest Folios + AR Misc adjustments
   - `AdvanceDepositParser`: extract Deposits on Hand Today
   - `HPExcelParser`: read Journalier sheet rows 7-33 by Aera/Paiement
3. **JourMapper.compute_all() rewrite** per Section 7.3 above (use the column rules table).
4. **Validation step** per Section 12 checklist.
5. **DC attribution UI**: present non-zero DC + ask user to confirm source (Transelect/GEAC/Recap/Other).
6. **Cell comment writer**: prepend C[r] cell comment with source breakdown.

## 14. DBRS workflow (separate from RJ)

The DBRS (Daily Business Review Sheet) is a SEPARATE workbook used to feed the corporate "2023 DBR MasterSheraton" tracker. It's not part of the RJ but the night auditor fills it from the same source documents.

**File:** `K:\DBRS\DBRS_formule.2025_corriger.xlsm`

**Sheets:**
| Sheet | Purpose |
|---|---|
| Explications | French instructions (8 steps) |
| **DailyRev** | Manual entry of Room Charge categories from DR |
| **Market Segment** | Manual entry of Rooms by segment from MS report |
| DBRS | Computed (formulas) — categorizes for DBRS standard |
| DBRS Insertion | Output: B2:B89 cells (formulas referencing DBRS sheet) |

### 14.1 DailyRev tab fill (col B, rows 2-30)

Each row has a Room Charge label in col A; fill col B with the **Today** value from Daily Revenue PDF page 1:

| Row | Label | Source (DR p.1) |
|---|---|---|
| 2 | Room Chrg - Premium | Today value |
| 3 | Room Chrg - Standard | |
| 4 | Room Chrg - eChannel | |
| 5 | Room Chrg - Special | |
| 6 | Room Chrg - Wholesal | |
| 7 | Room Chrg - Govt./Mi | |
| 8 | Room Chrg - Weekend | |
| 9 | Room Chrg - AAA | |
| 10 | Room Chrg - Packages | |
| 11 | Room Chrg - Advance | |
| 12 | Room Chrg - Senior D | |
| 13 | Room Chrg - Associat | |
| 14 | Rm Chrg - Reward Red | |
| 15 | Room Chrg - Other Di | |
| 16 | Room Chrg - Complime | |
| 17 | Room Chrg - GRP OTH | |
| 18 | Room Chrg - GRP - Co | |
| 19 | Room Chrg - GRP - As | |
| 20 | Room Chrg - GRP Tour | |
| 21 | Room Chrg - GRP - Go | |
| 22 | Room Charge OPEN | |
| 23 | Room Chrg - Contract | |
| 24-30 | Other room charges (Opaque, SVO, Late Fee, Cancellation, GNS, etc.) | |
| 38 | (used in DBRS calc B83 No Shows) | |
| 44, 47 | (used in DBRS B81 Allowance) | |

### 14.2 Market Segment tab fill (col B, rows 3-91)

Use the **Rooms** column (3rd col on PDF) for TODAY (not MTD) per market segment:

The structure mirrors the Market Segment PDF segment-by-segment with SUBTOTAL formulas like `=SUM(B8:B9)`.

Examples for Apr 14:
- B3: NOT SPECIFIED rooms = 0
- B5: T10 Premium Reta rooms = 5
- B8: T11 Airline = 0
- B9: T12 Standard Ret = 22
- B12-14: T14, T15, T16 (Govt) — use T16 = 1 today
- B17: T17 Special Corp = 29
- ...
- B59: GC Corporate Group = 100
- B72: GN Association = 39
- B62: T62 Complimentary = (number of comp rooms)
- B89: W58 KDT MiniHotel
- B90: GG Government Group
- B91: GO Other Groups
- B94 grand total = formula sum of all subtotals

### 14.3 DBRS computed sheet (auto)

The DBRS sheet aggregates DailyRev + Market Segment into standard segment groups (Retail, Special Corporate, Government, Premium, Packages, FIT/Wholesale, Discounts, SPG/Marriott Rewards, Discount Total, Transient Total, Groups by type, Contract, Perm, etc.) with rooms/ADR/revenue per segment.

Key formulas (auto):
- B11 TOTAL PREMIUM = B5+B2+B8 (rooms)
- B13 TOTAL PREMIUM REVENUE = B7+B4+B10
- B12 TOTAL PREMIUM ADR = B13/B11
- B38 TOTAL DISCOUNTS, B40 TOTAL DISCOUNT REVENUE
- B42 TOTAL TRANSIENT, B44 TOTAL REVENUE
- B65 TOTAL GROUP, B67 TOTAL GROUP REV
- B77 DAILY PAID OCC RMS, B79 DAILY REVENUE
- B81 ALLOWANCE = DailyRev!B44 - DailyRev!B47
- B82 OTHER = DailyRev!B28 + DailyRev!B31
- B83 NO SHOWS = DailyRev!B29 + DailyRev!B38
- B84 EARLY DEP/LATE DEP = DailyRev!B27 + DailyRev!B26
- B86 TOTAL NET ADR, B87 TOTAL NET REVENUE
- B89 Complimentary Rooms = Market Segment!B62

### 14.4 DBRS Insertion (paste-target output)

Cells B2:B89 contain `=DBRS!B[r]` formulas — they auto-mirror the DBRS sheet for paste-friendly extraction.

### 14.5 Manual paste step into 2026DBR MasterSheraton.xls

The corporate master is `K:\Audition\04 - April\2026DBR MasterSheraton.xls` (year-specific name, e.g., `2026DBR MasterSheraton.xls`, also mirrored at `Y:\2026DBR MasterSheraton.xls`).

**Master workbook structure:**
| Tab | Purpose |
|---|---|
| Instruction | French instructions for the full DBR process |
| DBR Cover | Summary cover page (7-day forecast, OTB updates) |
| **Setup** | Config: hotel name, rooms (252), SAP (858), and **Date of Update** in cell **F8** |
| **Jan-Dec** | 12 monthly tabs (490r × 256c each) |

**Month tab layout (all same pattern, e.g., `Apr`):**
- **B2** = `=+Setup!F8` — pulls the current date from Setup
- **Rows 4-95** = Summary section with SUMIF formulas that read "last night's actual" based on `DAY($B$2)` vs the day-header row
- **Row 96** = ACTUAL flags (0/1 marking which days are final)
- **Row 97** = Day numbers: B97=1, C97=2, ..., O97=**14**, AF97=31, AG97=TOTAL
- **Rows 98-185+** = Daily data per segment:
  - R98 Retail rooms / R99 ADR formula / R100 Retail Rev
  - R101 Special Corp rooms / R102 ADR / R103 Special Corp Rev
  - R104 Gov rooms / R105 ADR / R106 Gov Rev
  - R107-R109 TOTAL PREMIUM formulas
  - R110-R112 Packages, R113-R115 FIT/Wholesale, R116-R118 Qualified Discounts, R119-R121 Marriott Bonvoy
  - R134 TOTAL DISCOUNTS, then Groups (Corporate/Association/Gov/SMERF/T&T/Other), Contract, Perm
  - Final rows: Allowance, Other, No Shows, Early/Late Dep, Complimentary

**DBRS Insertion → Month tab row mapping:** `DBRS Insertion B[N]` → `Month tab [DayCol][N+96]`
- DBRS Insertion R2 → Apr R98 (Retail rooms)
- DBRS Insertion R4 → Apr R100 (Retail revenue)
- DBRS Insertion R7 → Apr R103 (Special Corp rev)
- DBRS Insertion R89 → Apr R185 (Complimentary rooms)

Blank rows in DBRS Insertion (e.g., R3, R6, R9) correspond to rows with existing formulas in the month tab (ADR formulas, SUBTOTAL formulas) — the "Skip blanks" paste preserves them.

### 14.6 Full paste procedure

1. Open `DBRS_formule.2025_corriger.xlsm` (the staging workbook)
2. Fill **DailyRev** tab from DR PDF (Today values per Room Chrg category, col B rows 2-30+)
3. Fill **Market Segment** tab from MS PDF (Rooms per segment Today, col B rows 3-91)
4. Verify DBRS sheet auto-computed correctly
5. Go to **DBRS Insertion** tab, select **B2:B89**, Ctrl+C
6. Open `2026DBR MasterSheraton.xls` (corporate master)
7. **Setup tab → cell F8 = audit date** (e.g., `2026-04-14`)
8. Go to the month tab matching the audit month (e.g., `Apr`)
9. Click the cell at **column [day_letter]98** — day→column map:
   - Day 1 → B, Day 2 → C, Day 3 → D, ..., Day 14 → **O**, ..., Day 31 → AF
   - General: Excel column number = day + 1 (since day 1 is col 2/B)
10. Right-click → **Collage Spécial...** (Paste Special)
11. Check **Valeurs** (Values) + **Blanc non compris** (Skip blanks)
12. Click OK

**At end of month:** Month tab B2 currently has formula `=+Setup!F8` (follows Setup date). To lock the month's final state, replace B2 formula with the last date of that month (hardcoded) so the summary formulas keep showing that month's end-of-month snapshot.

### 14.7 Auto-fill spec for the DBR Master

For the webapp end-to-end:
1. Parse DR PDF → extract Today values for all Room Chrg lines (rows 2-48 of DR p.1) + adjustments (Allowance, GNS, etc.)
2. Parse Market Segment PDF → extract Rooms count per segment for TODAY column (3rd col)
3. Open `DBRS_formule.2025_corriger.xlsm` via COM, fill both tabs
4. Save it
5. Open `2026DBR MasterSheraton.xls` via COM
6. Set `Setup!F8` = audit date
7. Compute day column from audit date: col = day + 1 (Excel number) → letter via `col_letter(day+1)`
8. Read DBRS Insertion B2:B89 values
9. Write each non-blank value to the corresponding month tab cell at `[day_col][98+offset]` where offset matches the DBRS Insertion row offset
10. Save `2026DBR MasterSheraton.xls`

**Implementation:** `utils/dbrs_filler.py` — `DBRSFiller` class implements this full spec.

- `DBRSFiller.fill_dbrs_staging(dr_room_charges, ms_rooms_by_segment)` — steps 3-8 above; returns `{'dbrs_insertion': {row: value}}`
- `DBRSFiller.paste_to_master(audit_date, insertion_values, master_path=None)` — steps 5-10 above; auto-detects master path from `MASTER_PATHS` list
- `DBRSFiller.fill_and_paste(audit_date, dr_room_charges, ms_rooms_by_segment)` — single-call full workflow
- Both methods use `HasFormula` guards to replicate "Paste Special → Values + Skip blanks" behaviour
- Tests: `tests/test_dbrs_filler.py` (8 tests, no Excel required — covers mappings, row/column arithmetic, subtotal row exclusion)

### 14.6 Auto-fill spec for the DBRS

For the webapp:
1. Parse DR PDF → extract Today values for all Room Chrg lines (rows 2-48 of DR p.1) + room rate adjustments (Allowance, GNS, etc.)
2. Parse Market Segment PDF → extract Rooms count per segment for TODAY column (3rd column)
3. Use Excel COM to open `DBRS_formule.2025_corriger.xlsm`
4. Fill DailyRev!B2:B... with the room charge values (write as `=value` for audit trail)
5. Fill Market Segment!B3:B91 with the room counts (skip rows with SUBTOTAL formulas)
6. Save the workbook
7. (Optional) Auto-paste B2:B89 from DBRS Insertion into the master DBR file

The DBRS macros and formulas auto-compute everything else.

## 15. Reference files in this project

- `/RJ_Audit_Methodology.docx` — Detective process for finding DC errors
- `/RJ_Balancing_Guide_Sheraton.docx` — Authoritative column rules
- `/RJ_Balancing_Complete_Guide.docx` — Overview + formulas
- `/RJ_AUDIT_CHECKLIST.md` — Reference checklist
- Reference good fills: `K:\RJ 2026-2027\02-AVRIL 2026\Rj 13-04-2026.xls`, `Rj 14-04-2026.xls`
