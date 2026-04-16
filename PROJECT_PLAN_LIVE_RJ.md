# RJ Webapp — "Fill 100% from Webapp + Live 38-Sheet Preview" Plan

_Last updated: 2026-04-07_
_Status: Planning_
_Scope: ONLY the path to (1) finishing the RJ entirely from the webapp, (2) seeing
each of the 38 sheets update live as fields change, (3) knowing in real-time that
the audit is correct, and (4) exporting a drop-in `.xlsm`. Everything outside that
loop is out of scope._

---

## 1. Executive Summary

The webapp is ~80% of the way to letting an auditor finish a Rapport Journalier
without ever opening the real Excel. Parsers fill ~58 fields automatically,
`calculate_all()` already computes Bal_Ferm + DC + most jour totals, all 38 tabs
have UI surfaces, and a JSON "preview" endpoint exists. What is blocking the
end-state is **four concrete things**:

1. **The export does not write the full template.** `/api/rj/native/export/rj/<date>`
   loads `Rj Vierge.xls` but writes only Recap + Transelect + GEAC + DUBACK + depot
   header cells. **Jour, SetD, all 25+ secondary sheets are skipped** (literally
   `# For now, skip individual jour entries.` in the code at line 5884).
2. **The preview is decoupled from the real template.** `/api/rj/native/preview/<date>`
   returns hand-curated cell lists for ~9 sheets and `{filled_count}` blobs for the
   other ~25. It does NOT show what will actually be written to each of the 38
   sheets, so "live preview" today is a checkbox tracker, not a sheet preview.
3. **`calculate_all()` is missing the column-level credit/debit math from
   `calculate_jour()` in `rj_balancer.py`.** It now computes bal_ferm, total_fb,
   total_revenue, and a *simplified* DC, but it does NOT populate the 86 jour
   columns the export needs (cols 4-86), nor does it produce the per-column diff
   that powers the "is it correct?" feedback.
4. **Several tabs collect data the auditor still has to type into Excel manually**
   (or that the save endpoints store but never export): SetD personnel rows,
   somm_nettoyeur, salaires, EJ, ristourne, rapp_p1/p2/p3, etat_rev, budget, autre_gl,
   analyse_101100/100401, vestiaire entries, massage entries, auditeur signatures.
   The save endpoints exist; the writers don't.

The fix is **not** more parsers or more UI. It is wiring the calculation engine
into the template writer so a single endpoint emits the same bytes that go to the
K: drive — and then making the preview a read-only render of that exact in-memory
workbook.

---

## 2. Goal-State Architecture (one-paragraph version)

A single server-side function `build_rj_workbook(nas) -> openpyxl.Workbook` loads
`Rj Vierge.xlsm` (we need an `.xlsm` template, not `.xls` — see Risk R-1) and
writes every cell that depends on `nas`. **Both** the export endpoint and the
preview endpoint call this function. The preview endpoint serializes the
post-write workbook to a structured JSON (`{sheet: [{cell, value, formula?,
status}]}`) which the front-end renders as a 38-card grid. Saves are debounced
on the client; after each successful save the client refetches the preview JSON
(small payload, no websockets needed). The "is it correct?" panel is the existing
21-point checklist from `_build_checklist()` in rj_balancer.py, also surfaced
through the same endpoint.

---

## 3. The 38 Sheets — Coverage Matrix

Status legend:
- **AUTO** = parser fills it from a source doc, save endpoint round-trips, included in current export writer.
- **MANUAL** = UI tab exists, save endpoint exists, but EXPORT WRITER does NOT write to the real template (auditor still must touch Excel).
- **CALC** = derived from other fields by `calculate_all()` or formulas in the template.
- **PARTIAL** = some cells written, others not.
- **MISSING** = no UI / no save / no writer.

Sheet names are taken from `Rj 12-23-2025-Copie.xls` and the `RESET_RANGES` /
`CELL_MAPPINGS` constants in `utils/rj_mapper.py`.

| # | Sheet | Source | Parser | Save Endpoint | Calc in `calculate_all()` | Export Writer | Preview Renders | Status |
|---|-------|--------|--------|---------------|---------------------------|---------------|-----------------|--------|
| 1 | controle | manual + auto-date | — | save_controle (L2669) | partial (jours_dans_mois) | yes (date + name only) | yes (7 cells) | **PARTIAL** |
| 2 | Recap | manual + Cashier Summary + SJ | cashier_summary, sales_journal | save_recap (L2696) | yes (recap_balance) | yes (B6:C17,B22:B26) | yes (16 cells) | **AUTO** |
| 3 | transelect | TransactionSummary + Sales Journal | transaction_summary, sales_journal | save_transelect (L2737) | yes (transelect_variance, quasimodo) | partial (rest+rec, no X20/X24/totaux) | yes (per-card) | **PARTIAL** |
| 4 | geac_ux | TransactionSummary + Daily Revenue + Adv Dep | transaction_summary, daily_revenue, advance_deposit | save_geac (L2768) | yes (ar_variance) | partial (B6/G6/J6 + B8/G8/J8 only — no balance sheet rows 32/37/41/44/53) | yes (cashout/dailyrev/balance) | **PARTIAL** |
| 5 | jour | DR + SJ + HP + AdvDep + Transelect + Recap | calculate_jour() exists in rj_balancer, NOT used by save | partial (totals, KPIs, bal_ferm, simplified DC) | calculate_all writes only ~10 of 86 cols | **NO** (line 5884: "skip individual jour entries") | yes (~33 jour fields, no row mapping) | **MISSING — biggest gap** |
| 6 | DUBACK# | manual entry | — | save_dueback (L2809) | dueback_total | partial (col A name + col B prev/new for first ~30 entries — header row only, no day row math) | yes (entry list) | **PARTIAL** |
| 7 | SetD | derived from DUBACK# + sd_entries + manual | sd_parser exists | save_sd (L2851), save_setd (L2988) | yes (setd_rj_balance) | **NO** (line 5876: `pass`) | yes (entry list) | **MISSING** |
| 8 | depot | Sommaire dépôts + manual | sd_parser (depot subset) | save_depot (L2954) | yes (depot_total) | partial (col B/F amounts only — no date col, no totals) | yes | **PARTIAL** |
| 9 | DBRS | Market Segment | market_segment_parser | save_dbrs (L3189) | yes (dbrs_*) | NO | yes (entries count) | **MISSING** |
| 10 | HP | HP Excel upload | hp_excel_parser | save_hp_admin (L3096) | yes (hp_admin_total + jour deductions) | NO | yes (entries count) | **MISSING** |
| 11 | Sonifi | DR (jour_sonifi) + manual email | daily_revenue (jour_sonifi only) | save_sonifi (L3148) | yes (sonifi_variance) | NO | partial (sonifi total only) | **MISSING** |
| 12 | Internet | DR (jour_internet) + manual | daily_revenue | save_internet (L3130) | yes (internet_variance) | NO | partial | **MISSING** |
| 13 | Quasimodo | derived from Transelect + Recap | — | save_quasimodo (L3166) | yes (quasi_*) | NO | NO (no preview entry) | **MISSING** |
| 14 | Diff.Caisse# | manual + diff_caisse_formula | — | save_diff_caisse (L3257) | yes (diff_caisse_total + diff_caisse_formula) | NO | yes (entries count) | **MISSING** |
| 15 | SOCAN | manual | — | save_socan (L3275) | yes (socan_charge) | NO | yes | **MISSING** |
| 16 | Résonne | manual | — | save_resonne (L3294) | yes (resonne_total) | NO | yes | **MISSING** |
| 17 | Vestiaire# | manual entries | — | save_vestiaire (L3311) | yes (vestiaire_total_*) | NO | yes | **MISSING** |
| 18 | AD (Admin) | manual | — | save_admin (L3330) | yes (admin_total) | NO | yes | **MISSING** |
| 19 | Massage | manual | — | save_massage (L3347) | yes (massage_*) | NO | yes | **MISSING** |
| 20 | Ristourne | manual | — | save_ristourne (L3366) | yes (ristourne_*) | NO | yes | **MISSING** |
| 21 | EJ | manual | — | save_ej (L3386) | yes (ej_total) | NO | yes | **MISSING** |
| 22 | Salaires | manual | — | save_salaires (L3409) | yes (salaires_total_*) | NO | yes | **MISSING** |
| 23 | Nettoyeur | manual | — | save_nettoyeur (L3437) | yes (nettoyeur_total) | NO | yes | **MISSING** |
| 24 | Somm.Nettoyeur | manual | — | save_somm_nettoyeur (L3460) | nothing to compute | NO | yes | **MISSING** |
| 25 | Auditeur | manual signatures | — | save_auditeur (L3480) | nothing to compute | NO | yes | **MISSING** |
| 26 | rj | derived stats | — | save_rj_rapport (L3498) | nothing | NO | yes | **MISSING** |
| 27 | Rapp_p1 | manual | — | save_rapp_reports (L3533) | nothing | NO | yes (filled count) | **MISSING** |
| 28 | Rapp_p2 | manual | — | save_rapp_reports | nothing | NO | yes | **MISSING** |
| 29 | Rapp_p3 | manual | — | save_rapp_reports | nothing | NO | yes | **MISSING** |
| 30 | Etat rev | manual | — | save_etat_rev (L3555) | nothing | NO | yes | **MISSING** |
| 31 | Budget | manual | — | save_budget_rj (L3573) | nothing | NO | yes | **MISSING** |
| 32 | Analyse 101100 | manual | — | save_analyse_gl_101100 (L3215) | yes (gl_101100_variance) | NO | yes | **MISSING** |
| 33 | Analyse 100401 | manual | — | save_analyse_gl_100401 (L3236) | yes (gl_100401_variance) | NO | yes | **MISSING** |
| 34 | Autre GL | manual | — | save_analyse_gl (L3591) | nothing | NO | yes | **MISSING** |
| 35 | diff_forfait | derived (jour_diff_forfait) | — | (calc only) | yes (jour_diff_forfait) | NO | partial | **CALC** |
| 36 | daily | derived from jour | — | (no save) | nothing | NO | NO | **MISSING** |
| 37 | rj_stats | derived | — | (in save_rj_rapport) | nothing | NO | yes | **MISSING** |
| 38 | print sheets / VNC | derived | — | — | nothing | NO | NO | **MISSING** |

**Summary:** Of the 38 sheets, **4 are AUTO**, **5 are PARTIAL**, **~28 are MISSING**
on the export side. Only 1 (jour) is missing on the calculation side. All 38 have
SOMETHING in the JSON preview, but the preview is a hand-built mock of `nas`
fields, not a render of the workbook the export will produce. Confirm exact sheet
list against the live `Rj Vierge.xls` template before implementation (see Q-001).

---

## 4. Gap Analysis — What Specifically Blocks the Goal

### GAP-A. `calculate_all()` does NOT populate the 86 jour columns

- **File:** `database/models.py` lines 1447-1822 (`NightAuditSession.calculate_all`).
- **Problem:** It computes `jour_total_fb`, `jour_total_revenue`, `jour_adr`, `jour_revpar`,
  `rj_balance_fermeture`, `diff_caisse_formula` (simplified), and stores
  `rj_cards_summary` JSON. It does **not** compute the 86 individual jour columns
  (col 4 through col 86) that `calculate_jour()` in `rj_balancer.py` lines 595-793
  produces — Pause Spesa, every F&B sub-line with HP deductions applied, Pourboires
  with HP_pourb removed, the per-card debits at cols 60-65, the GEAC col41 comp,
  the col5 residual compensation, the Recap-derived debits at cols 72-78, the
  col57 diff_forfait, etc.
- **Impact:** Without these 86 columns the export writer can't fill the jour row
  for the day, the live preview can't show "DC will be $0 once you save", and the
  21-point checklist can only be run by the standalone balancer (not the per-save
  recompute loop).
- **Fix:** Move `calculate_jour()` into a service that operates on `nas` (no need
  for it to keep parsing files — `nas` already has the parsed data) and call it
  from `calculate_all()`. Persist the result as a new JSON column
  `jour_columns_calc` on `NightAuditSession` so the writer + preview both read it.
  The 21-point checklist becomes a pure function of `jour_columns_calc` plus the
  scalar fields.
- **Concretely:**
  - New file: `utils/rj_jour_calculator.py` exposing `compute_jour_columns(nas) -> dict[int, float]`.
    Copy the math from `rj_balancer.calculate_jour()` lines 621-694 verbatim,
    sourcing inputs from `nas` fields and JSON blobs (`hp_admin_entries`,
    `transelect_restaurant`, `transelect_reception`, `geac_balance_sheet`, etc.)
    instead of from parser dataclasses. Preserve the column numbering 4-86.
  - New column: `jour_columns_calc db.Column(db.Text)` on `NightAuditSession`
    + a migration in `migrate_db.py`.
  - In `models.py:calculate_all()` after the existing bal_ferm computation, call
    `from utils.rj_jour_calculator import compute_jour_columns; cols = compute_jour_columns(self); self.set_json('jour_columns_calc', cols)`.
  - Replace the simplified DC computation at line 1817 with the real one:
    `dc = bal_ferm - bal_ouv - sum(cols[k] for k in cols if 4<=k<=57) + sum(cols[k] for k in cols if 60<=k<=86)`.

### GAP-B. The export writer skips jour + 28 secondary sheets

- **File:** `routes/audit/rj_native.py` lines 5694-5910 (`export_rj_excel`).
- **Problem:** Lines 5876 (`# For now, skip individual personnel entries`) and 5884
  (`# For now, skip individual jour entries`) are blockers. The writer also stops
  at GEAC row 8 — never writes balance sheet (rows 32, 37, 41, 44, 53), never
  writes any of the 28 secondary sheets.
- **Fix:** Replace the inline writer with a `RJWorkbookBuilder` class that has one
  method per sheet. Most are mechanical: read `nas.get_json(field)` →
  iterate → write. Use `utils/rj_filler.py:RJFiller` (already exists, already does
  Recap/Transelect/GEAC/DUBACK#/depot/SetD/jour via `CELL_MAPPINGS`/`get_*_row_for_day`)
  as the foundation. **Key insight: most of the writing logic already exists in
  `utils/rj_filler.py`**; it just isn't called from the export endpoint, which
  reimplemented half of it inline. Switch the export endpoint to use `RJFiller`.
- **Concretely:**
  - Audit `utils/rj_filler.py` (762 lines) — it already has `update_controle`,
    `update_deposit`, `sync_duback_to_setd`, etc. Read its full surface (only
    looked at 0-440 in research) and inventory which sheets it covers.
  - Add missing methods: `write_jour_row(day, jour_columns_calc)`,
    `write_setd_personnel(setd_personnel_json)`, `write_geac_balance_sheet`,
    `write_secondary_sheet(sheet_name, json_blob)` (generic JSON-to-table writer
    for the 20+ list-shaped sheets like ej_entries, salaires, ristourne,
    nettoyeur, vestiaire, massage, admin, somm_nettoyeur, etc).
  - For each secondary sheet, build a small mapping config:
    `SECONDARY_SHEET_LAYOUTS = {'EJ': {'start_row': 4, 'cols': {'date':'A', 'description':'B', 'montant':'C'}}, ...}`.
    This is the only new "schema work" required — and it can be derived in 2-3
    hours from inspecting the template.
  - Rewrite `export_rj_excel` to: load template → instantiate `RJFiller` → call
    every writer method → save. Target: <100 lines of orchestration.

### GAP-C. The preview endpoint isn't a render of the actual export

- **File:** `routes/audit/rj_native.py` lines 960-1209 (`preview_rj`).
- **Problem:** Hand-curated `cell` dicts. If the export writer writes `B6=4070.43`,
  the preview will say `B6=4070.43` only because the same value is hardcoded into
  both routes. The two will drift the moment one is changed.
- **Fix:** Make the preview a read-only side-effect of the build:
  ```python
  wb = build_rj_workbook(nas)             # same call as export
  return jsonify(serialize_workbook_for_preview(wb, nas))
  ```
  Where `serialize_workbook_for_preview()` walks every sheet, reads every cell
  that isn't blank, and emits `{sheet: {name, cells: [{ref, value, formula, status}]}}`.
  Status = `'ok' | 'warn' | 'error' | 'empty' | 'calculated'` based on the
  21-point checklist results merged in.
- **Concretely:**
  - New file: `utils/rj_preview_serializer.py` with `serialize(wb, nas, checklist) -> dict`.
  - Add `wb_to_preview` switch to `build_rj_workbook` so the same builder can be
    called once per save without disk I/O (everything stays in BytesIO).
  - **Performance:** A full 38-sheet template is ~1-3 MB. Reading every cell on
    every keystroke is too slow. Mitigations:
    1. Debounce client saves to ≥250 ms (already done via `debounceSave`).
    2. Only return cells that **changed** since the last preview (server keeps
       a per-session hash of the previous serialization in `instance/preview_cache/`,
       diffs against the new one). Return `{sheets: [...all sheets metadata...],
       changed_cells: [...]}` so the client can patch.
    3. For the first request, return everything; for subsequent ones, return diffs.

### GAP-D. The template is `.xls`, but the user wants `.xlsm`

- **File:** `routes/audit/rj_native.py` line 5715, also `documentation/back/Rj-19-12-2024.xls`.
- **Problem:** `xlrd`/`xlutils` only handle the legacy binary `.xls` format and
  cannot preserve macros or write `.xlsm`. The dashboard `.xlsm` files exist
  (`DBRS_formule.2023_corriger copie.xlsm`) but the active template `Rj Vierge.xls`
  is the legacy format. The user's stated goal is "byte-for-byte ready to drop
  into K: drive." If the K: drive workflow uses `.xlsm` with macros, we **cannot**
  use xlrd/xlutils — we must switch to `openpyxl` (which preserves macros if loaded
  with `keep_vba=True`).
- **Fix:**
  - Confirm with user: is the production template `.xls` or `.xlsm`? (Q-002)
  - If `.xlsm`: rebuild the writer on `openpyxl.load_workbook(path, keep_vba=True)`.
    Note: openpyxl can write `.xlsm` and preserve VBA but **does not preserve the
    formatting of cells with formulas the same way xlwt does**. Validate by
    round-tripping the template once and diffing.
  - If `.xls`: stay on xlutils, accept that macros must be re-attached or that
    the template has the macros pre-baked.
  - Impact: this decision drives the entire writer choice. Resolve before GAP-B.

### GAP-E. Save → recompute → re-render loop is incomplete

- **Files:** all `save_*` endpoints in `rj_native.py`, `templates/audit/rj/rj_native.html`
  (`debounceSave` JS function — not yet read but referenced 30+ times).
- **Problem:** Today's flow: keystroke → debounceSave → POST `/save/<section>` →
  endpoint commits → returns. But the response does NOT include recomputed
  preview data. The client must separately call `/calculate` and `/preview` to
  refresh — and in the current HTML, neither call is made automatically after
  saves (only on tab switch / manual button click).
- **Fix:** Make every save endpoint call `nas.calculate_all()` before commit
  (most don't currently — verify each one) and return the **new preview diff** in
  the response payload. Client patches the preview UI from the response without
  a second roundtrip.
- **Concretely:**
  - Add a helper `_save_response(nas)` in `rj_native.py` that runs
    `nas.calculate_all()`, commits, builds a small preview-diff, runs the
    21-point check, and returns
    `{success, balance_status, dc, jour_diffs, sheet_changes}`.
  - Replace the bespoke return at the end of every `save_*` endpoint with
    `return _save_response(nas)`.
  - In `rj_native.html`, change `debounceSave()` to apply the response payload
    to the preview pane and the persistent balance bar.

---

## 5. Recommended Implementation Order

Each phase ships independently and produces visible value.

### Phase 0 — Decisions (½ day, blocks everything)

- [ ] Q-001: Confirm exact list of 38 sheet names + which template file is
      authoritative. Open `Rj Vierge.xls` (or `.xlsm`) and dump sheet names + max
      row/col per sheet. Update Section 3 table.
- [ ] Q-002: `.xls` vs `.xlsm` for production drop. Drives writer library choice.
- [ ] Q-003: Are there VBA macros in the production template that must run after
      the file is opened? If yes, the export must trigger them on first open OR
      we must reproduce their effects in Python. The four known macros
      (`envoie_dans_jour`, `calcul_carte`, `eff_*`) are already reproduced in
      `rj_filler.py`/`rj_writer.py` — verify completeness.
- [ ] Q-004: Performance budget for live preview. Acceptable latency from
      keystroke → preview update? (Suggest: ≤500 ms for non-jour sheets, ≤1.5 s
      after a jour-affecting field.)

### Phase 1 — Calculation Engine Completion (1-2 days) — **GAP-A**

- [ ] P1.1 Create `utils/rj_jour_calculator.py` with `compute_jour_columns(nas)`.
      Copy math from `utils/rj_balancer.py:calculate_jour` lines 621-694 verbatim,
      replacing `sj.x` / `dr.x` / etc with `nas.field` reads.
- [ ] P1.2 Add `jour_columns_calc` Text column on `NightAuditSession` in
      `database/models.py`. Add migration step in `migrate_db.py`.
- [ ] P1.3 Wire `compute_jour_columns(self)` into `NightAuditSession.calculate_all()`
      after the existing card_debit_totals block (line 1788).
- [ ] P1.4 Replace simplified DC at line 1817 with real DC formula using the
      computed columns.
- [ ] P1.5 Move 21-point checklist (`_build_checklist` from rj_balancer.py L800-964)
      into a method on NightAuditSession: `nas.run_checklist() -> list[dict]`.
      It should consume `jour_columns_calc` instead of parser dataclasses.
- [ ] P1.6 Unit test against the validated 2026-02-16 test session (the one
      where 22/23 jour columns matched ground truth). Target: **all 23 columns
      match**, DC = 0 ± 0.02.
- [ ] P1.7 Add `/api/rj/native/jour-debug/<date>` returning the 86 column values
      side-by-side with the legacy parser-based balancer for fast regression.

### Phase 2 — Single Workbook Builder (2-3 days) — **GAP-B + GAP-D**

- [ ] P2.1 Resolve Q-002 (.xls vs .xlsm). If `.xlsm`: add `openpyxl` dependency,
      build a thin compatibility shim that exposes the same API as `RJFiller`
      methods.
- [ ] P2.2 Read the FULL `utils/rj_filler.py` (the research only sampled L1-440
      of 762) and inventory which sheets/methods already exist.
- [ ] P2.3 Create `utils/rj_workbook_builder.py:build_rj_workbook(nas) -> Workbook`.
      Single entry point that:
      - Loads `Rj Vierge.{xls|xlsm}`
      - Instantiates the filler
      - For each of the 38 sheets, calls a dedicated `_write_<sheet>(nas, ws)` method
      - Returns the in-memory workbook
- [ ] P2.4 Implement `_write_jour(nas, ws)` reading from `jour_columns_calc` JSON
      and writing to the day's row using `get_jour_row_for_day(day)`. This is the
      single most important writer.
- [ ] P2.5 Implement `_write_setd(nas, ws)` using `setd_personnel` JSON and the
      135-column `SETD_PERSONNEL_COLUMNS` map already in `rj_mapper.py`.
- [ ] P2.6 Implement `_write_geac_full(nas, ws)` covering rows 32, 37, 41, 44,
      53 from `geac_balance_sheet` JSON.
- [ ] P2.7 Build `SECONDARY_SHEET_LAYOUTS` dict (single mapping config) and a
      generic `_write_secondary_sheet(layout, list_data, ws)` method that
      handles all 20+ list-shaped sheets (EJ, salaires, ristourne, nettoyeur,
      vestiaire, massage, admin, ej, somm_nettoyeur, ristourne, resonne, autre_gl,
      analyse_101100, analyse_100401, rapp_p1/p2/p3, etat_rev, budget, auditeur).
- [ ] P2.8 Replace the inline writer in `routes/audit/rj_native.py:export_rj_excel`
      (L5694-5910) with `wb = build_rj_workbook(nas); wb.save(buf); send_file(buf)`.
- [ ] P2.9 Decommission the parallel `routes/audit/rj_export_excel.py` (the 14-sheet
      `openpyxl` reimplementation) — or repurpose it as a "summary export" only.
      It is a confusing second source of truth today.
- [ ] P2.10 Round-trip test: export, open in Excel, verify formulas still
      compute, verify it can replace a real K: drive RJ.

### Phase 3 — Preview = Workbook Render (1-2 days) — **GAP-C**

- [ ] P3.1 Create `utils/rj_preview_serializer.py:serialize(wb, nas, checklist) -> dict`.
      Walk every sheet, emit `{name, cells: [{ref, value, formula?, status, label?}], stats: {filled, total, balanced}}`.
      Mark cells as `'error'` if they appear in `checklist` failures.
- [ ] P3.2 Replace the body of `preview_rj` (L962) with:
      `wb = build_rj_workbook(nas); checklist = nas.run_checklist(); return jsonify(serialize(wb, nas, checklist))`.
- [ ] P3.3 Add a server-side preview cache keyed by `(audit_date, nas.updated_at)`.
      Same input → same bytes → return cached JSON. Avoid rebuilding the workbook
      if nothing changed. Store in `instance/preview_cache/`.
- [ ] P3.4 Add diff support: if client passes `?since=<hash>`, return only the
      cells that changed since that hash. Otherwise return everything.
- [ ] P3.5 Update `templates/audit/rj/tabs/preview.html` to render a 38-card
      grid: each card shows sheet name, fill %, balance status, click to expand
      and see the actual cell list. Highlight error cells in red.
- [ ] P3.6 Verify the preview is the SAME data as the export (write a test that
      builds a workbook, exports it, parses it back, builds preview from the same
      session, and asserts equality).

### Phase 4 — Save → Recompute → Live Preview Loop (1 day) — **GAP-E**

- [ ] P4.1 Add helper `_save_response(nas)` in `rj_native.py` (next to `_get_session`).
      Runs `calculate_all()`, commits, runs checklist, returns small payload:
      `{success, balance: {dc, recap, transelect, ar, fully_balanced},
      checklist_failures: [...], changed_sheets: [...], jour_diffs: [...]}`.
- [ ] P4.2 Refactor every `save_*` endpoint (≈30 of them, all between L2667 and
      L3614) to end with `return _save_response(nas)`. Audit each one to ensure
      it doesn't have section-specific return data the client depends on; if it
      does, merge it into `_save_response` payload.
- [ ] P4.3 In `rj_native.html`, change `debounceSave` to:
      1. POST → save endpoint
      2. Parse response
      3. Update persistent balance bar (DC pill, 4 balance pills)
      4. Update the preview pane via `applyPreviewDiff(response.changed_sheets)`
      5. If the user is currently viewing the preview tab, refetch full preview
         (else mark dirty and refetch on tab switch).
- [ ] P4.4 Add a persistent top-bar to `rj_layout.html` (already proposed in the
      old plan as Phase 5). It shows: `DC: $0 ✓ | Recap ✓ | Transelect ✓ | GEAC ✓`
      and updates from the `_save_response` payload. This becomes the auditor's
      "am I correct?" answer.
- [ ] P4.5 When `dc != 0`, the bar expands to show the top 3 checklist failures
      and a "Voir Préview" button. No other UI changes needed — the existing
      preview tab now contains the truth.

### Phase 5 — Polish & Acceptance (½-1 day)

- [ ] P5.1 Acceptance test: take the 2026-02-16 fixture, upload its 6 source
      docs, fill 6 manual fields, click Export, byte-compare the resulting
      `.xlsm` against the manually-completed K: drive RJ. Target: zero
      meaningful differences (formula recalc cells may differ until Excel
      reopens).
- [ ] P5.2 Smoke test: complete a brand-new RJ from scratch in <30 minutes
      using only the webapp.
- [ ] P5.3 Document the new flow in `documentation/RJ_NATIVE_WORKFLOW.md` (1 page).
- [ ] P5.4 Update `routes/audit/README.md`.

**Total: ~6-9 working days end-to-end. Phase 1 + Phase 2 + Phase 4 unblock the
core "fill from webapp" goal in ~5 days even without the polished preview.**

---

## 6. Live-Preview Architecture — The Choice

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **A. Client-side JS model of 38 sheets** | Zero server roundtrip per keystroke. Instant. | Have to reimplement `calculate_jour`, `calculate_all`, AND every cell-write rule in JavaScript. ~3000 lines. Two sources of truth = drift = bugs. **Hard veto.** |
| **B. WebSocket push from server** | Real-time. Server stays source of truth. | New infra (websockets, server state). The save→recompute is already async — push is overkill for one user per session. |
| **C. Debounced fetch after save** | Server is single source of truth. Reuses existing `/save/<section>` infra. Cache + diff makes it cheap. | One ~250 ms latency per save. Requires the export builder to be fast enough to run on every save. |
| **D. Server-render-on-save, client polls** | Simplest. | Wasteful polling. |

### Pick: Option C — Debounced fetch after save, with diff caching.

**Justification:**
- The server is already the source of truth for every calculation; rebuilding
  that in JS is the single biggest risk to correctness in this whole project.
- The save endpoints already exist and are debounced (≥250 ms) on the client.
- A single auditor sits at this for one nightly session — there's no fan-out
  problem that would justify websockets.
- The export builder MUST be fast enough to run per-save anyway, because that's
  exactly what the user wants: "see what will be written as I type." If
  `build_rj_workbook(nas)` takes >500 ms, the live preview is broken regardless
  of transport.
- Diff caching (Phase 3.3 and 3.4) handles the payload-size concern: the first
  preview load returns ~1 MB of structured cell data; every subsequent save
  returns only the cells that changed since the previous hash, typically a few
  dozen.

### Concrete Data Flow

```
[user types in jour_piazza_nourriture field]
           │
           ▼ (250 ms debounce)
POST /api/rj/native/save/jour { jour_piazza_nourriture: 1234.56 }
           │
           ▼
save_jour():
   nas.jour_piazza_nourriture = 1234.56
   nas.calculate_all()                      ← runs compute_jour_columns + DC + checklist
   db.session.commit()
   wb = build_rj_workbook(nas)              ← in-memory, no disk
   diff = serialize_diff(wb, nas, last_hash_for(nas.id))
   return { success, balance, diff }
           │
           ▼
client.applyPreviewDiff(response.diff)
client.updateBalanceBar(response.balance)
```

**Performance budget:**
- `compute_jour_columns`: ≤10 ms (pure Python arithmetic on ~50 numbers)
- `calculate_all`: ≤50 ms (already runs today; mostly JSON unmarshalling)
- `build_rj_workbook`: target ≤300 ms. Cache the loaded template (`functools.lru_cache`
  on the bytes), only the writes are per-session. openpyxl + ~80 cell writes
  should be <200 ms.
- `serialize_diff`: ≤50 ms with hash-based shortcut.
- Total per-save: ≤500 ms. ✓

If P2.10 testing shows openpyxl is slower than this, fall back to:
- Compute jour_columns_calc + checklist on every save (cheap)
- Only run `build_rj_workbook` on tab-switch to preview tab + on explicit "Refresh
  Preview" click.
- The balance bar still updates per save (cheap).

This degraded mode is still a major improvement over today.

---

## 7. Risks & Mitigations

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| R-1 | `.xls` vs `.xlsm` template mismatch breaks export | High | Critical | Resolve Q-002 in Phase 0. Decision blocks Phase 2. |
| R-2 | Rewriting `calculate_jour` for `nas` introduces sign/HP-deduction bugs that the validated 2026-02-16 fixture doesn't catch | Medium | High | Run the legacy `rj_balancer.calculate_jour` (parser-based) and the new `compute_jour_columns(nas)` side-by-side on N=10 historical sessions. Diff every column. |
| R-3 | openpyxl breaks formulas or formatting in the round-trip | Medium | Critical | Round-trip test in P2.10 *before* writing any new code. If broken, stay on xlutils + accept `.xls` output, or use `xlwings`/COM (Mac/Windows only). |
| R-4 | The 28 secondary sheet layouts are not consistent across templates | Medium | Medium | Inventory all 38 sheet layouts in Phase 0 against the actual template. Build SECONDARY_SHEET_LAYOUTS as data, not code. |
| R-5 | Live preview is too slow per-save | Medium | Medium | Phase 3 has the degraded fallback (preview only on tab switch). Profile in Phase 2. |
| R-6 | `_save_response` response shape change breaks current `debounceSave` callers | High | Low | Add a feature flag `?v=2` to opt-in incrementally. Old endpoints keep their current shape until callers are migrated. |
| R-7 | Macro-driven cells (formulas that depend on Excel recalc) read as 0 in openpyxl until Excel reopens the file | Medium | Medium | Use `data_only=False` when loading, accept that the preview shows formula strings for those cells, and label them `'formula'` in the preview status. |
| R-8 | Drift between `_apply_parsed_data_to_session` and `compute_jour_columns` (parser writes a field, calculator reads a different field) | Medium | High | Add an integration test that runs both for each fixture and asserts every column matches. |

---

## 8. Open Questions

- [ ] Q-001: Confirm the actual 38 sheet names by dumping
      `xlrd.open_workbook('Rj Vierge.xls').sheet_names()`. Update Section 3 table.
- [ ] Q-002: Is the production template `.xls` or `.xlsm`? (Drives writer library.)
- [ ] Q-003: Does the current K: drive workflow rely on macros running on file
      open? If yes, list them and decide: reproduce in Python or trigger via
      Excel COM.
- [ ] Q-004: Live-preview latency budget — confirm ≤500 ms is acceptable.
- [ ] Q-005: Are sheets `daily`, `print_VNC`, `Quasimodo` separate physical sheets
      in the template or generated views? (Affects sheet count.)
- [ ] Q-006: Should the export be `.xlsm` (with macros) or `.xlsx` (no macros)?
      The K: drive previous-day file is `.xlsm`.
- [ ] Q-007: When the user drops an existing previous-day `.xlsm` into the
      webapp, is the goal to (a) extract data and start fresh on Vierge, or
      (b) overwrite the previous-day file in place? Affects whether the writer
      uses Vierge or merges into uploaded file.

---

## 9. Decision Log

| Date | Decision | Rationale | Alternatives |
|------|----------|-----------|--------------|
| 2026-04-07 | Single source of truth = server-side `build_rj_workbook(nas)` | Avoids JS reimplementation of 86-column math; preview = export by construction | Client-side JS model rejected (R-2 risk); websocket push rejected (overkill) |
| 2026-04-07 | Phase 1 (jour calc) before Phase 2 (writer) | Writer needs `jour_columns_calc` data to write the jour row | — |
| 2026-04-07 | Use existing `utils/rj_filler.py` as foundation, do not rewrite | 762 lines of working filler logic already exists; the export endpoint just doesn't call it | Greenfield rewrite rejected as wasteful |
| 2026-04-07 | Deprecate `routes/audit/rj_export_excel.py` (the 14-sheet openpyxl path) | Two parallel exports = drift; the template-based path is the only one that matches the K: drive format | Keep both rejected |

---

## 10. Files That Will Change

| File | Change | Phase |
|------|--------|-------|
| `database/models.py` | Add `jour_columns_calc` column; wire `compute_jour_columns` into `calculate_all`; replace simplified DC with real DC; add `run_checklist` method | P1 |
| `migrate_db.py` | Add migration for `jour_columns_calc` column | P1 |
| `utils/rj_jour_calculator.py` | **NEW** — `compute_jour_columns(nas)` ported from `rj_balancer.calculate_jour` | P1 |
| `utils/rj_workbook_builder.py` | **NEW** — `build_rj_workbook(nas) -> Workbook` orchestrator | P2 |
| `utils/rj_filler.py` | Add `write_jour_row`, `write_setd_personnel`, `write_geac_balance_sheet`, `write_secondary_sheet`; expose layouts | P2 |
| `utils/rj_mapper.py` | Add `SECONDARY_SHEET_LAYOUTS` dict for 20+ secondary sheets | P2 |
| `utils/rj_preview_serializer.py` | **NEW** — `serialize(wb, nas, checklist)` + diff support | P3 |
| `routes/audit/rj_native.py` | Replace `export_rj_excel` body (L5694-5910) with `build_rj_workbook` call; replace `preview_rj` body (L960-1209) with serializer call; add `_save_response` helper; refactor all 30 `save_*` endpoints to use it | P2, P3, P4 |
| `routes/audit/rj_export_excel.py` | Deprecate or repurpose | P2.9 |
| `templates/audit/rj/rj_layout.html` | Add persistent balance bar at top | P4 |
| `templates/audit/rj/rj_native.html` | Update `debounceSave` to apply preview diff from save response | P4 |
| `templates/audit/rj/tabs/preview.html` | Render 38-card grid with expandable cell views | P3 |
| `documentation/RJ_NATIVE_WORKFLOW.md` | **NEW** — auditor-facing workflow doc | P5 |

---

## 11. Success Criteria

- [ ] An auditor opens the webapp, drops 6 source docs, types ≤15 manual values,
      clicks Export, and gets an `.xlsm` byte-equivalent (modulo formula recalc)
      to a manually-completed K: drive file.
- [ ] At any moment during data entry, the preview tab shows what each of the
      38 sheets currently contains, updated within ≤500 ms of a save.
- [ ] DC, Recap balance, Transelect variance, GEAC variance are visible at the
      top of every tab, updated live.
- [ ] When DC ≠ 0, the system tells the auditor which checklist item failed and
      which jour column has the wrong value.
- [ ] The 86 jour columns computed by `compute_jour_columns(nas)` match the
      ground-truth file for the 2026-02-16 fixture (and ideally N=10 historical
      fixtures).
- [ ] No code path requires the auditor to open the real Excel file.

---

## 12. Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-04-07 | Initial plan | Replace the broad "RJ Gestion Overhaul" plan with a sharper plan focused only on fill-from-webapp + live preview + correctness |
