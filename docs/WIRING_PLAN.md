# RJ Webapp — Extensive Wiring Plan

**Audience**: developer implementing the "upload → auto-fill → manual complete → live DC → export .xls" workflow
**Anchored to**: `docs/BALANCING_RULES_MASTER.md` + 20-day fixture forensics (Mar 01 – Apr 06 2026)
**Authored**: 2026-04-09

---

## 0. TL;DR

> **The app is ~80% wired already.** The goal is NOT to rebuild anything — it's to (a) fix 5 real bugs in the balancer, (b) wire 3 missing upload handlers, (c) trigger the existing auto-fill path from the existing upload endpoint, (d) surface the existing `_build_checklist` 21-point output in the UI, and (e) add a simple manual-input form for the 9 truly non-derivable fields. All the heavy machinery (parsers, `calculate_jour`, 66 routes, 222-column NAS model, RJFiller export) exists and works.

---

## 1. Current state snapshot (what the 4 agents found)

### 1.1 Frontend — `templates/audit/rj/rj_native.html` (4,705 lines)
- **Framework**: vanilla ES6 + custom CSS (no React/Vue/jQuery/Tailwind). Dark-mode capable.
- **Upload infrastructure**: ✅ complete — ZIP dropzone, 11 per-doc upload buttons, `POST /api/rj/native/upload-file`, `POST /api/rj/native/upload-zip`.
- **Tabs**: Setup, DueBack, SD, Recap, Transelect, GEAC, Jour, Quasimodo, SetD, HP/Admin, Summary + 28 secondary tabs (hidden behind "⋯ Plus").
- **Auto-save**: ✅ `debounceSave(tabName)` per section on every field change.
- **Live DC widget**: ✅ exists (lines 1039-1086 + toolbar badge 241), `recalcDC()` JS function sums jour cols, color-coded green/red/amber.
- **Export button**: ✅ `exportExcel()` → `GET /api/rj/native/export/rj-filled/<date>`.

**The one critical gap**: after upload, parsed values are returned as JSON but **not automatically populated into the form**. The auditor has to click fields to trigger `debounceSave()`. This is a ~50-line JS fix.

### 1.2 Backend — 66 routes, 12,882 lines across 10 `routes/audit/rj_*.py` files
- **Upload/parse**: `POST /api/rj/native/parse-and-fill` (line 1499), `POST /api/rj/native/upload-file`, `POST /api/rj/native/upload-zip`, `POST /api/rj/native/import/excel` (line 559).
- **Per-tab save**: ~30 save endpoints (`save/recap`, `save/jour`, `save/transelect`, `save/geac`, `save/dueback`, `save/sd`, `save/hp_admin`, etc.)
- **Balance check**: `GET/POST /api/rj/native/balance-check/<audit_date>` (line 1218) — ✅ already calls `BalancerService.check_balance` which runs `_build_checklist` and returns the full 21-point diagnostic + DC decomposition.
- **Auto-fix**: `POST /api/rj/native/auto-fix/<audit_date>` (line 1249) — partial.
- **Export**: `GET /api/rj/native/export/rj-filled/<audit_date>` (line 1281) — uses `RJFiller` (xlutils.copy) to inject NAS data into archived RJ template.

### 1.3 NAS model — `database/models.py` `NightAuditSession`
- **~222 columns/fields** covering everything in the 38-sheet RJ workbook.
- **All 9 manual auditor inputs exist as fields**: `g4_montant`, `jour_adj_piazza`, `jour_adj_spesa`, `jour_adj_cafe`, `jour_adj_chambres_svc`, `jour_adj_banquet`, `jour_adj_tabagie`, `jour_adj_notes` (JSON), `recap_balance` (S&D).
- **All jour columns 4-86** have corresponding `jour_*` fields.
- **JSON fields** for nested data: `transelect_restaurant`, `transelect_reception`, `geac_cashout`, `geac_daily_rev`, `geac_balance_sheet`, `hp_admin_entries`, `sd_entries`, `dueback_entries`, `setd_personnel`, `depot_data`.
- **No missing fields** for the manual inputs we identified.

### 1.4 Parsers — TWO parallel layers
- **Balancer-layer** (`utils/rj_balancer.py` inline): `parse_sj`, `parse_dr_pdf`, `parse_ar_pdf`, `parse_hp`, `parse_adv_dep`, `parse_rj_transelect`, `parse_rj_geac`, `parse_rj_recap`, `parse_rj_jour`. **This is the canonical path** — used by `BalancerService.check_balance`, `fixture_regression.py`, and `calculate_jour`.
- **Class-layer** (`utils/parsers/*.py`): `DailyRevenueParser`, `SalesJournalParser`, `ARSummaryParser`, `HPExcelParser`, `AdvanceDepositParser`, `FreedomPayParser`, `SDParser`, `MarketSegmentParser`, `CashierSummaryParser`, `TransactionSummaryParser`, `RecapTextParser`. **This is the webapp's path** — used by `ParserFactory.create()` inside `parse-and-fill` route.

**⚠️ The two layers have DIVERGENT logic.** Fixes to the balancer layer don't propagate to the webapp's auto-fill path, and vice versa. Current bugs (col 29 pourb, col 36 chambres filter, col 46 InterHotel) exist ONLY in the balancer layer. The class-layer is richer but less battle-tested.

### 1.5 Formula coverage — `calculate_jour()` in `utils/rj_balancer.py:595-793`
- **36 of 37 documented formulas implemented** (only col 6 `Bie_Link` unimplemented — that's the "HP fallback when no detailed HP" column, rarely used).
- **Variance classes auto-detected**: X24 (Transelect), GEAC col 41 (bottom), PANNE TPS (but buggy — see §2.3).
- **Variance classes NOT auto-detected** (by design, require auditor input): InterHotel XferIn routing, Chambres annulation, prior-day corrections, cashier misposting, depot resto pas ferme, operational notes.

---

## 2. Bugs to fix — prioritized

Every bug is in `utils/rj_balancer.py`. Do NOT touch `utils/parsers/*` yet — those are used by the webapp's auto-fill and fixing them requires separate regression.

### 2.1 🔴 P0 — Col 29 `Pourb` double-deduction (line 642)

```python
# CURRENT
calc[29] = max(0, sj.piaz_pourb + sj.bqt_pourb + sj.spesa_pourb - hp_pourb_admin - hp_pourb_promo)

# CORRECT
calc[29] = sj.piaz_pourb + sj.bqt_pourb + sj.spesa_pourb
```

**Why**: HP pourb is already in col 68 (HPAdmP) and col 69 (HPProP) as separate debits. Subtracting it from col 29 double-counts the deduction. Mar 02 forensic: raw SJ pourb = 1780.89 = RJ truth col 29 exactly, no HP deduction.

**Test**: fixture regression on Mar 02 — col 29 diff should drop to 0.

### 2.2 🔴 P0 — Col 46 `AutRev` missing `dr.interhotel_xferin` (line 655)

```python
# CURRENT
calc[46] = sj.piaz_fretage + sj.ch_fretage + dr.lit_pliant

# CORRECT
calc[46] = sj.piaz_fretage + sj.ch_fretage + dr.lit_pliant + dr.interhotel_xferin
```

**Why**: The Guide calls col 46 "MOST-FORGOTTEN" and says the #1 most common error is leaving InterHotel out. Mar 14, 17, 23, 26, 29, 30, Apr 03, 04, 05 all had DC variances equal to the missing XferIn value. Also update the misleading warning at line 723-724 (remove or change to "InterHotel XferIn routed to col 46 automatically").

**Test**: Mar 14 DC drops from +9.99 to 0 after this fix.

### 2.3 🔴 P0 — `dc_after_comp` hardcoded to 0.00 (line 782)

```python
# CURRENT (line 782 in the return dict)
'dc_after_comp': 0.00,  # With all compensations applied

# CORRECT
'dc_after_comp': dc_after_comp,   # use the variable computed at line 771-772
```

**Why**: The variable `dc_after_comp` is correctly computed on lines 771-772 but then discarded by the hardcoded 0.00 on line 782. Any consumer of this field (balance-check endpoint response, live DC widget) sees the wrong value.

**Test**: any day with non-zero compensation — the API response's `dc_after_comp` should match the mathematically-computed value, not 0.

### 2.4 🟡 P1 — Col 36 `Chamb` row filter misses 2 patterns (line 367 inside `parse_dr_pdf`)

```python
# CURRENT
if in_chambres and 'Room Chr' in line:

# CORRECT
if in_chambres and ('Room Chr' in line or 'Rm Chrg' in line or 'Room Charge' in line):
```

**Why**: Misses `"Rm Chrg - Reward Red"` and `"Room Charge + Allowa"` on most fixture days. Mar 02 missed 170 + 228.40 = 398.40 of chambres total.

**Test**: Mar 02 DR chambres_total should match DR Total line exactly.

### 2.5 🟡 P1 — GEAC AR fallback zeroes col 41 silently (line 1002)

```python
# CURRENT
g.ar = ar_val if ar_val > 0 else g.fd

# CORRECT
g.ar = ar_val if ar_val > 0 else 0
```

**Why**: When the geac_ux AR cell is blank/0, the code fakes `g.ar = g.fd` which makes `col41 = -(fd - ar) = 0`. On a legitimate AR=0 day, col 41 should be `-fd` (possibly large). Silently wrong.

### 2.6 🟡 P1 — Club Lounge override branch is a no-op (lines 1106-1110)

```python
# CURRENT
if hasattr(nas, 'jour_club_lounge') and nas.jour_club_lounge:
    pass  # let calculate_jour use DR values by default

# CORRECT: wire the override
if hasattr(nas, 'jour_club_lounge') and nas.jour_club_lounge:
    club_nourr_override = float(nas.jour_club_lounge)
    # then pass club_nourr_override=club_nourr_override to calculate_jour
```

**Why**: Manual CL overrides stored in NAS are silently ignored. The `calculate_jour` signature already has `club_nourr_override` and `club_autres_override` parameters.

### 2.7 🟢 P2 — `parse_rj_jour` doesn't read cell notes (line 1028)

Add `formatting_info=True` to `xlrd.open_workbook` and read `cell_note_map[(row, 2)]` — the DC cell notes are the ground-truth variance documentation (Transelect / InterHotel / Chambres annul / etc.). Without them the regression can't tell an "explained declared variance" day from a real error.

### 2.8 🟢 P2 — No file-date validation (all parsers)

Add to each parser: extract the report date from the PDF/xls header, compare to the session audit_date, raise a warning if they differ by more than 1 day. This would have caught the 5 stale February files in our March fixture immediately.

### 2.9 ⏸ DEFERRED — TPS on pannes deduction (lines 660-663)

User-flagged as "wait for more data." Do NOT fix. Document in comments only. Our forensic found Mar 02, Mar 13, Mar 29, Mar 30, and others where the deduction produced a wrong answer, but the user may have context we don't.

### 2.10 🟢 P2 — Add `ARData.stored_variance` property

The master doc's hidden GEAC AR formula:
```
GEAC AR side = AR Total Transfers + (AR stored balance − AR computed end of day)
```

Empirically verified on Mar 21, 23, 29, 30, Apr 03, 04. Add to `utils/rj_balancer.py` `ARData` dataclass:

```python
@dataclass
class ARData:
    # ... existing fields
    total_transfers: float = 0
    stored_balance: float = 0
    computed_end_of_day: float = 0

    @property
    def stored_variance(self):
        return self.stored_balance - self.computed_end_of_day

    @property
    def geac_ar_side(self):
        return self.total_transfers + self.stored_variance
```

Then update `parse_ar_pdf` to extract the "Ending balance does not agree with stored balance for today of XXX" warning line. Update `GeacData.col41` formula to use `ar.geac_ar_side` instead of just `ar.total_transfers`.

---

## 3. What we can wire TODAY without new code

These are the "connect 2 pieces that already exist" wins. Each should take < 1 hour.

### 3.1 🎯 Trigger auto-fill automatically after upload

**Current**: `upload-file` returns JSON → JS receives it → user must click each field to fire save.

**Fix**: After successful `upload-file` response, JS should iterate the returned field map and populate + save each tab automatically.

**Files**: `templates/audit/rj/rj_native.html` — inside the existing `file-report-upload` change handler (around line 1860), add:

```javascript
// After successful upload
if (result.filled && result.sections) {
    // Populate all form fields from result.details
    populateFormFromParse(result.details);
    // Trigger recalc + DC update
    recalcDC();
    // Save each affected tab
    for (const section of result.sections) {
        await fetch(`/api/rj/native/save/${section}`, { method: 'POST', ... });
    }
    // Show toast: "N fields auto-filled from <doc_type>"
}
```

The backend already returns `result.sections` and `result.details`. Just need to consume them.

### 3.2 🎯 Surface the 21-point checklist in the UI

**Current**: `balance-check` endpoint already returns a full `checklist` array with 21 items + status. UI doesn't render it.

**Fix**: Add a sidebar panel to `rj_native.html` that calls `GET /api/rj/native/balance-check/<audit_date>` after every save and renders the checklist items as a scannable list:

```
✅ 1. BF = -(DR NB) - AdvDep
✅ 2. F&B credits (cols 9-35) from SJ − HP − adj
🟡 3. Col 36 Chambres = DR - G4 (G4 missing — enter manually)
✅ 4. Col 44 Autres GL
...
🔴 19. DR InterHotel XferIn accounted ← FAILS (9.99 in DR, not in col 46)
```

Each FAIL item should have a clickable "Fix" button that either:
- Scrolls to the relevant field, OR
- Opens a modal with the auto-fix suggestion (e.g. "Add 9.99 to col 46")

**Files**: `templates/audit/rj/rj_native.html` — new `<aside>` section. JS function `refreshChecklist()` to call the API and render.

### 3.3 🎯 Surface the 10-variance-class DC breakdown

**Current**: `balance-check` response has `dc_decomposition` but only 4 buckets.

**Fix (prerequisite)**: Expand `utils/rj_balancer.py` `check_balance` return to include all 10 classes:

```python
return {
    ...
    'dc_decomposition': {
        'x20_transelect': tr.x20_value,   # from transelect sheet
        'geac_bottom': geac.col41,        # FD vs AR
        'geac_top_per_card': {...},       # top section per-card variances
        'recap_surplus_deficit': -recap.surplus_deficit,
        'interhotel_xferin': dr.interhotel_xferin,   # if not in col 46
        'chambres_annulation': 0,         # from cell note parsing
        'prior_day_correction': 0,        # from cell note parsing
        'cashier_misposting': 0,          # from cell note parsing
        'depot_resto_pas_ferme': 0,       # from cell note parsing
        'panne_lien_hotel': sj.panne_lien,
        'sum_explained': total,
        'unexplained_residual': dc - total,
    }
}
```

Then render in the UI as a breakdown below the DC widget:

```
DC = −1,694.15

Declared variances:
  Transelect X20           −82.46  [✓ in note]
  GEAC col 41            −1,577.95  [✓ in note]
  Chambres annul            −33.74  [✓ in note]
  ─────────────────────────────────
  Sum                   −1,694.15
  Unexplained                0.00  ✓
```

### 3.4 🎯 File-header date validation at upload time

**Current**: Feb files in March folders go undetected.

**Fix**: After parse, extract the report date from the parser output (most parsers already have `report_date` field) and compare to `nas.audit_date`. If differ by > 1 day, return HTTP 400 with:

```json
{
    "success": false,
    "error": "Date mismatch",
    "detail": "Daily Revenue PDF is dated 2026-02-18 but you are auditing 2026-03-18. Please upload the correct file."
}
```

The UI should show this as a bright red toast and REJECT the upload.

### 3.5 🎯 Fix `dc_after_comp` return (already in §2.3 but worth calling out)

One-line change, unblocks the correct DC display in the webapp.

---

## 4. Missing source parsers — NEW code needed

Three new parsers, all simple. Based on Apr 06 fixture analysis.

### 4.1 `utils/parsers/house_totals_parser.py` — P0 NEW

**Input**: `house_totals.txt` — Sales Journal Report for Entire House (Lightspeed POS output)

**Extracts**:
- `tips_to_servers` (PAIDOUTS section: `TIPS TO SERVERS -763.98`)
- `expected_deposit` (payment totals section: `EXPECTED DEPOSIT -534.64`)
- `paidouts` (gross paidouts: `PAIDOUTS 763.98`)
- `payment_totals_per_card` (VISA, MASTERCARD, AMEX, INTERAC, CHAMBRE — feeds Transelect POSITOUCH column)
- `pannes_per_card` (PANNE VISA, PANNE MASTER counts & totals)
- `total_sales_tax` (TOTAL SALES+TAX)
- `period` / `beginning` / `ending` (non-resetable totals — for audit trail)

**Feeds**:
- `recap.comptant_positouch` = `|paidouts| + expected_deposit` (signed)  [**proven on Apr 06**: 763.98 − 534.64 = 229.34 = actual Recap value]
- `recap.remb_gratuite` = `-|paidouts|`  [= −763.98]
- `transelect.positouch_*` per card
- Cross-check: `panne_*` counts vs SJ panne lines

**Effort**: ~2-4 hours. Text parsing with regex. No PDF.

**Master doc impact**: this is the missing POS-side piece. Once wired, Recap Comptant Positouch and Remb Gratuité stop being manual and become auto-filled.

### 4.2 `utils/parsers/debourse_parser.py` — P1 NEW

**Input**: `house_90_2.dat` (actually a PDF — file extension is wrong; starts with `%PDF-1.5`). Cashier Detail Report for Dept 90 (Debourse) / Sub-dept 90.2.

**Extracts**:
- `tickets` — list of `{cashier_initials, amount, description, time}` entries
- `dept_90_total` (= Remboursement Serveur total, e.g. `505.61`)

**Feeds**:
- `recap.remb_client` = `−dept_90_total`  [= −505.61, feeds jour col 73]
- `recap.due_back_reception` = `dept_90_total`  [= 505.61, feeds jour col 76]
- `DUBACK#` sheet per-cashier rows (indirectly via `all_cashier_details`)

**Effort**: ~4-6 hours. PDF text parsing with `pdfplumber`, similar pattern to `parse_dr_pdf`.

**Note**: Also extends `CashierSummaryParser` which already has a skeleton. Can either complete that or write from scratch.

### 4.3 Extend `utils/parsers/cashier_summary_parser.py` — P1 (skeleton exists)

**Input**: `all_cashier_details.pdf` — full cashier detail, 25 pages on Apr 06.

**Currently extracts**: Grand totals by department, per-card-type totals.

**Add**: Per-cashier breakdown, per-dept totals per cashier. Feeds `DUBACK#` sheet `dueback_entries` JSON and `SetD` `setd_personnel` JSON.

**Effort**: ~2-3 hours. Extension of existing parser.

---

## 5. Parser dispatch table (the complete auto-fill surface)

For every source doc the webapp should accept, map to the fields it fills:

| Source file | Parser | Fills NAS fields | Feeds jour cols | Feeds Recap | Feeds Transelect | Feeds GEAC |
|---|---|---|---|---|---|---|
| **Previous day RJ.xls** | `import_excel` | Bal_Ouv carryover, controle, DUBACK rotation | col 1 (Bal_Ouv) | — | — | — |
| **daily_revenue.pdf** | `DailyRevenueParser` + `parse_dr_pdf` | `jour_room_revenue`, `jour_tel_*`, `jour_nettoyeur`, `jour_sonifi`, `jour_lit_pliant`, `jour_internet`, `jour_massage`, `jour_fax`, `jour_tvq`, `jour_tps`, `jour_taxe_hebergement`, `jour_transfer_cr`, `jour_autres_gl`, `geac_balance_sheet`, `jour_deposit_on_hand` | 36, 37, 38, 40, 44, 45, 46, 47, 48, 49, 50, 51, 52, 54, 55, 73, 83 | ALL settlements rows | reception totals per card | FD side + CC top section |
| **sales_journal.txt** | `SalesJournalParser` + `parse_sj` | `jour_piazza_*`, `jour_banquet_*`, `jour_spesa_*`, `jour_chambres_svc_*`, `jour_pourboires`, `jour_forfait_sj`, `jour_equip_audio`, `jour_vestiaire`, `jour_tabagie`, SJ panne fields | 4, 9-14, 19-28, 29, 30, 31, 32, 33, 35, 53, 57, 74 | Cheque AR/DR lines | — | — |
| **ar_summary.pdf** | `ARSummaryParser` + `parse_ar_pdf` | `geac_ar_previous`, `geac_ar_*`, new `stored_variance` field | — (flows into col 41 calc) | — | — | AR side + stored variance |
| **hp.xlsx** | `HPExcelParser` + `parse_hp` | `hp_admin_entries` JSON, HP admin/promo totals | 9-14, 24-28 (deductions), 68, 69 | — | — | — |
| **advance_deposit.pdf** | `AdvanceDepositParser` + `parse_adv_dep` | `jour_deposit_on_hand` (today formula) | 3 (Bal_Ferm input) | — | — | AdvDep applied |
| **transaction_summary.xlsx** (FreedomPay) | `TransactionSummaryParser` | `transelect_reception` per card | 60-65 | — | reception bank totals | CC top section |
| **house_totals.txt** ⭐ NEW | `HouseTotalsParser` 🆕 | `recap_comptant_positouch`, `recap_remb_gratuite`, POS panne counts, POS per-card totals | — (fills Recap only) | ✅ Comptant, Remb Gratuité | POSITOUCH column | — |
| **house_90_2.dat** (PDF) ⭐ NEW | `DebourseParser` 🆕 | `recap_remb_client`, `recap_due_back_reception` | 73, 76 | ✅ Remb Client, Due Back | — | — |
| **all_cashier_details.pdf** ⭐ EXTEND | `CashierSummaryParser` | `dueback_entries`, `setd_personnel` per-cashier | — | Due Back distribution | — | — |
| **market_segment.pdf** | `MarketSegmentParser` | `dbrs_*` segment revenue | 88-95 (room counts) | — | — | — |
| **sd_deposit.xlsx** | `SDParser` | `sd_entries`, `setd_personnel` | — | — | — | — |
| **recap_text.txt** (per-server) | `RecapTextParser` | Server-level breakdown | — | Per-server detail | Restaurant POS totals | — |

---

## 6. Manual input fields — the "the auditor still types these" list

These 9 fields **cannot** be derived from any source doc (verified across 20 days of forensics). They must be captured in the UI as simple form inputs.

### 6.1 Absolutely required (blocks balancing)

| Field | NAS column | Used by | Why manual | UI form location |
|---|---|---|---|---|
| **`g4_montant`** | `nas.g4_montant` | col 36 Chambres + col 57 DifForf | Not in any source doc. Auditor judgment: = Club Lounge total when CL active, else = forfait manual input. Mar 02 = 80.00, Mar 21 = 380.00, Mar 29 = 0. | Controle tab, single number field |
| **`jour_adj_piazza`** | `nas.jour_adj_piazza` | col 9 Nou_Piaz | Code 50 correction entries — auditor review of SJ postings. Mar 02 = 16.06, Mar 04 = 6.08. | Jour tab, near col 9 |
| **`jour_adj_spesa`** | `nas.jour_adj_spesa` | col 14 Nou_Mar | Same as above for Spesa. Mar 02 = 8.65, Mar 04 = 8.65. | Jour tab, near col 14 |
| **Recap physical cash count** | `nas.recap_balance` (inverted) | col 78 S&D | Physical count of cash envelope by auditor. Not in any file. Apr 06 = +79.38 surplus. | Recap tab, single number field ("cash counted") |
| **Transelect terminal totals** (per terminal) | `nas.transelect_restaurant` JSON | cols 60-65 (indirectly via macro) | Read from physical bank settlement reports. Until we get `transaction_summary.xlsx` every day, this is manual. | Transelect tab, per-terminal grid |

### 6.2 Conditionally required (only when variance occurs)

| Field | NAS column | Used by | When | UI form location |
|---|---|---|---|---|
| **Chambres annulation** | `nas.jour_adj_notes` (JSON) | col 36 reduction | Free-text note: "CHAMBRES: 33.74 ANNULER". Forensic Mar 21. | Jour tab, cell-note free text |
| **Prior-day correction** | `nas.jour_adj_notes` (JSON) | col 5 or col 41 | Manual carry-over from yesterday's unresolved variance. Mar 25. | Jour tab, cell-note free text |
| **Cashier misposting** | `nas.jour_adj_*` department | col 9/14/24/etc. | "Nicoletta a mal poster un debourser". Mar 29. | Free text + numeric amount |
| **Operational notes** | `nas.jour_adj_notes` (JSON) | auditor record | "depot resto pas ferme", etc. Mar 30. | Cell-note free text |

### 6.3 Cell note auto-generation

For DC ≠ 0 with declared variances matching, **the webapp generates the cell note text** (saves auditor typing):

```
Input state:
  DC = -1,694.15
  Declared: X20 = -82.46, GEAC = -1,577.95, Chambres annul = -33.74

Auto-generated note text:
  Auditeur De Nuit:
  GEAC: 1577.95$
  TRANSELECT: 82.46$
  CHAMBRES: 33.74 ANNULER
```

On export, `RJFiller` writes this into `ws.write_comment(jour_row, 2, note_text)` — the cell note on the DC column.

---

## 7. Live DC panel — the UX spec

**Location**: right sidebar of `rj_native.html`, always visible. 260px wide.

**Sections**:

```
┌─ RJ 2026-04-06 ───────────────────┐
│                                    │
│  DC                      −18.66    │  ← big number, color-coded
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                    │
│  Declared variances                │
│                                    │
│  ✓ Transelect X20       −28.65    │
│  ✓ GEAC col 41 compensé          │  ← pre-compensated, not in DC
│  ✓ InterHotel XferIn      +9.99    │
│                          ──────    │
│  Somme des déclarées    −18.66    │
│  Résiduel inexpliqué      0.00    │  ← GREEN if zero
│                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  21-point checklist        18/21  │
│  ↓ Voir détails                    │
│                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Note auto-générée                 │
│  ┌──────────────────────────────┐ │
│  │ GEAC: 59.78                  │ │
│  │ TRANSELECT: 28.65            │ │
│  │ InterHotel XferIn: 9.99      │ │
│  └──────────────────────────────┘ │
│  [Appliquer à la cellule C21]     │
│                                    │
└────────────────────────────────────┘
```

**States**:

1. **DC = 0 outright** → green "✓ Équilibré" banner, no note needed
2. **DC ≠ 0, residual = 0** (all variances declared) → green "✓ Réconcilié — X variances documentées", show the auto-generated note with one-click "Apply" button
3. **DC ≠ 0, residual ≠ 0** → red "⚠ Résiduel inexpliqué de $X" with a diagnostic hint pointing at the most likely class (e.g. "Vérifiez: InterHotel XferIn sur DR p.7")

**API**: `GET /api/rj/native/balance-check/<date>` — already exists, returns the data. Just need a polling JS function that calls it on every form change (debounced 500ms).

---

## 8. Implementation sequence (the concrete roadmap)

### Phase 1 — Quick wins (1 day, no new parsers)

**Goal**: current code works correctly end-to-end with existing inputs.

1. **Fix balancer bugs** §2.1, §2.2, §2.3 (Col 29, Col 46 InterHotel, dc_after_comp) — 30 min
2. **Run fixture regression** — confirm Mar 02/14/17/Apr 04 scores improve
3. **Fix P1 bugs** §2.4, §2.5, §2.6 — 45 min
4. **Auto-fill on upload** §3.1 — wire the JS callback — 1 hour
5. **File-date validation** §3.4 — add to `parse-and-fill` endpoint — 1 hour
6. **DC breakdown in response** §3.3 — expand `check_balance` return, 10-class — 2 hours
7. **21-point checklist panel** §3.2 — add sidebar, call API, render — 2 hours

**End of day 1 result**: auditor uploads files → all fields fill automatically → DC widget shows 10-class breakdown → 21-point checklist visible in sidebar → stale files rejected at upload time → Mar 14 / Apr 03 etc. balance correctly.

### Phase 2 — Recap side (2 days)

**Goal**: Recap / S&D / Due Back become auto-fillable from `house_totals.txt` + `house_90_2.pdf` + `all_cashier_details.pdf`.

1. **Write `HouseTotalsParser`** — 3h
2. **Write `DebourseParser`** — 4h
3. **Extend `CashierSummaryParser`** for per-cashier breakdown — 3h
4. **Add 3 upload buttons to `rj_native.html`** — 30 min
5. **Add `_fill_from_house_totals`, `_fill_from_debourse`, `_fill_from_cashier_details`** dispatchers in `rj_native.py` — 2h
6. **Comptant Positouch formula**: wire `|paidouts| + expected_deposit` into Recap save path — 1h
7. **Recap live computation**: when `actual_cash_counted` entered, auto-compute S&D — 1h
8. **Test Apr 06 fixture end-to-end**: upload 3 new file types + DR + AR + SJ + HP → Recap fully populated → Enter cash count → DC balances

**End of Phase 2**: auditor uploads 8-9 files + 1 cash count field → Recap is 100% auto-filled → DC balances in real time.

### Phase 3 — GEAC stored variance + cell note reading (1 day)

1. **Extract stored variance from AR PDF** (§2.10) — add to `parse_ar_pdf` — 1h
2. **Wire stored variance into GEAC col 41 formula** — 30 min
3. **Read cell notes from previous day RJ** (§2.7) — `parse_rj_jour` with `formatting_info=True` — 30 min
4. **Write cell notes on export** — `RJFiller.add_jour_note(row, col, text)` using `xlwt ws.write_comment` — 1h
5. **Cell note generator** — Python function that builds the French note text from declared variances — 1h
6. **Wire auto-note into the Live DC panel** (§7, UI already designed) — 2h

**End of Phase 3**: days like Mar 21 / Mar 29 (multi-variance days) auto-generate their cell note text and auto-apply on export.

### Phase 4 — Front-end polish (open-ended)

Once everything is wired correctly, iterate on the UX. Use the frontend-design skill. Priorities (in order):

1. **Upload zone feedback** — clear progress, success toasts naming each field that got filled
2. **Live DC sidebar** aesthetic refinement (see §7 mockup)
3. **Cell-note preview modal** with side-by-side "current" vs "auto-generated"
4. **Mobile responsiveness** — auditors may use tablets
5. **Dark-mode parity** — existing dark mode is already good, make sure new panels match
6. **Keyboard shortcuts** — `Ctrl+S` to save current tab, `Ctrl+B` to run balance check, etc.
7. **Error-first navigation** — click a failed checklist item to jump to the relevant field

---

## 9. Testing strategy

For every change, run the fixture regression:

```bash
python -m scripts.fixture_regression inventory
python -m scripts.fixture_regression regression
```

**Acceptance criteria for each phase**:

- **Phase 1**: Mar 02/14/17/Apr 03/Apr 04 score improves; Mar 16 stops being 0/48; new DC decomposition appears in API response.
- **Phase 2**: Apr 06 fully reconciled from source files + 1 manual input (cash count).
- **Phase 3**: Mar 21 exports with the correct auto-generated cell note.
- **Phase 4**: user sign-off on UX.

Add a per-day `balance_score` to fixture regression output: `(match_count, total_count, dc_residual_after_declared_variances)`. The goal is match ≥95% and residual ≤$0.15 on every scoreable day.

---

## 10. Risks + mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **Two parallel parser layers** diverging further | Fixes to one don't propagate; users see different answers between "balance check" (balancer layer) and "parse and fill" (class layer) | Declare balancer layer canonical. Make class-layer parsers internally call balancer-layer `parse_*` functions and wrap the result. Do this as a separate phase AFTER all bugs are fixed. |
| **TPS panne deduction (§2.9)** may or may not be correct | Days where fixture shows it over-correcting might actually be undercounting a non-panne source | Leave alone until user provides more data. Do NOT include in Phase 1 fixes. |
| **VBA macros in the export template** break if opened in LibreOffice | `xlutils.copy` + `rebuild_xls_with_vba` is fragile | Test every export path on LibreOffice headless and on actual Excel. Keep the `ole_builder.py` path, but add a fallback that rebuilds without VBA if corruption detected. |
| **Cell notes on .xls vs .xlsx** | `xlwt` supports comments differently than `openpyxl`; the legacy format may truncate | Test note round-trip (write → read → write) early in Phase 3. |
| **Stored variance formula (§2.10)** may have edge cases we didn't see | Our forensic had 5 non-trivial GEAC days, not 50 | Add a flag `use_stored_variance_formula` defaulting to True. Keep the old `col41 = -(FD - AR_raw)` accessible via the old path if needed. |
| **Manual auditor inputs not mirrored in cell-note autofill** | User expects the webapp to "know" about prior-day corrections but there's no source | Clear UI messaging: "These fields come from your judgment — the webapp cannot derive them." |

---

## 11. Hand-off to the frontend iteration phase

Once Phases 1-3 are done, the app is functionally complete. The frontend-design skill then takes over for polish:

- **Brief**: "A night auditor's RJ filling workspace. French, restaurant/hotel context. Needs to feel fast, authoritative, and calm at 3am. Style reference: old-school accounting ledger meets modern fintech dashboard. Dark mode is the default."
- **Constraints**: vanilla JS + custom CSS (no new frameworks). Use existing CSS variables for color palette.
- **Key moments**: upload success → values cascading into the form (animation), DC transitioning red → yellow → green as the auditor resolves variances (micro-interaction), the auto-generated cell note sliding in from the right.

---

## 12. Summary — what the user cares about

> **Quote**: "my goal is for people to be able to fill in the webapp but still get the complete excel at the end and make it easier for them to develop and complete the rj when they are not perfect at understanding excel"

**How this plan meets it**:

1. **Upload = done for you.** Upload prev day RJ + today's 8 source docs → 95% of the jour + Recap auto-fills. No Excel cell navigation required.
2. **Manual input is minimal.** Only 9 fields require typing, and they're in plain-language forms (not spreadsheet cells). "Combien d'argent comptant avez-vous compté dans l'enveloppe?" not "Enter value in CA78".
3. **Live validation catches errors.** 21-point checklist + 10-variance-class DC panel runs on every change. Auditor sees "Transelect X20 = $82.46 — add to note?" not an Excel formula error.
4. **Cell notes write themselves.** Auto-generated French variance declarations. Auditor clicks "Apply" and it's done.
5. **Export = complete .xls.** `RJFiller` injects every field + note into the previous day's template. The output is indistinguishable from what the auditor would produce manually — same 38 sheets, same formulas, same cell notes.
6. **For auditors not great with Excel**: they never see a column letter. They see labeled forms. The Excel knowledge stays with the webapp.

---

**End of plan.** Ready to execute Phase 1 when you give the word.
