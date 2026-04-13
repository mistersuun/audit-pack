# Export Verification & Full Shift Simulation — Design

**Date:** 2026-04-10
**Author:** brainstormed with Claude
**Status:** approved, ready for implementation plan

## 1. Goal

Two test suites that prove the auditor's complete nightly workflow produces a correct, complete Excel RJ file:

**Sub-project A (pytest):** For every consecutive fixture day pair, import yesterday's ground-truth RJ as the base template, seed today's data, run the export pipeline (`RJFiller`), and compare the exported `.xls` cell-by-cell against today's ground-truth RJ. Verifies all 38 sheets exist with correct names. Cell-level comparison on the ~8 filled sheets (jour, Recap, transelect, geac_ux, DUBACK#, SetD, controle, depot). Sheet-count + name check on the remaining ~30 untouched sheets.

**Sub-project B (Playwright):** One realistic end-to-end "shift simulation" for the 2026-03-29 → 2026-03-30 pair. Drives the real browser UI through the complete auditor journey: import yesterday's RJ → click "Tout effacer (Recap+Trans+GEAC)" → upload tonight's PDFs → fill manual/seeded fields → verify DC=$0.00 on livecard → click Export → download the `.xls` → verify it has 38 sheets, correct date, and correct jour row.

## 2. Sub-project A: Export cell-level verification

### Architecture

```
test_fixtures/2026-03-29/ground_truth_rj.xls  ← base template (yesterday)
                    │
                    ▼
         RJFiller(base_bytes)
                    │
         ├── fill_sheet('controle', {date fields for day 30})
         ├── fill_sheet('Recap', {seeded recap values})
         ├── fill_sheet('transelect', {seeded card totals})
         ├── fill_sheet('geac_ux', {seeded balance sheet})
         ├── fill_dueback_day(30)
         ├── fill_setd_day(30)
         ├── fill_jour_day(30, {computed jour values})
         ├── envoie_dans_jour(30)   ← macro equivalent
         ├── calcul_carte(30)       ← macro equivalent
         └── save_to_bytes()
                    │
                    ▼
         exported_bytes  ← open with xlrd
                    │
                    ▼
         Compare cell-by-cell against:
         test_fixtures/2026-03-30/ground_truth_rj.xls
```

### Cell comparison scope

| Sheet | What's compared | Cells (est.) |
|---|---|---|
| `jour` | Day N's row only (cols 1-86) | ~86 |
| `Recap` | Filled cells from `CELL_MAPPINGS['Recap']` | ~20 |
| `transelect` | Card totals per section (restaurant/reception) | ~30 |
| `geac_ux` | Balance sheet 10 values | ~10 |
| `DUBACK#` | Day N's column of receptionist amounts | ~15 |
| `SetD` | Day N's column of employee SD amounts | ~15 |
| `controle` | Date fields (vjour, vmois, vannee) | ~3 |
| `depot` | Deposit amounts | ~5 |
| All 38 sheets | Exist with correct names | names only |

### Tolerance

Penny-perfect: `abs(exported_value - ground_truth_value) < 0.01` on every compared cell. Any drift is a bug.

### Diagnostic on failure

Reports the sheet name, cell address (e.g., `Recap!C6`), exported value, expected value, and the NAS field name that maps to that cell (reverse lookup from `CELL_MAPPINGS`).

### Test structure

```python
CONSECUTIVE_PAIRS = [
    ("2026-03-02", "2026-03-03"),
    ("2026-03-03", "2026-03-04"),
    ("2026-03-29", "2026-03-30"),
    ("2026-04-03", "2026-04-04"),
    ("2026-04-04", "2026-04-05"),
]

@pytest.mark.parametrize("base_day,target_day", CONSECUTIVE_PAIRS)
def test_export_matches_ground_truth(app, base_day, target_day):
    # 1. Load base (yesterday's ground truth) as template bytes
    # 2. Create NAS for target_day, seed via extract_all(target_day)
    # 3. Create RJFiller(base_bytes), fill all sheets from NAS
    # 4. Run envoie_dans_jour + calcul_carte (macro equivalents)
    # 5. save_to_bytes() → exported_bytes
    # 6. Open both exported + ground truth with xlrd
    # 7. Assert 38 sheet names match
    # 8. For each filled sheet: compare cells via CELL_MAPPINGS
    # 9. For jour: compare day row cols 1-86
```

The test uses `CELL_MAPPINGS` from `utils/rj_mapper.py` to know which cells to compare — so it tests "did the filler write the correct value into the correct cell" end-to-end.

### Consecutive pairs available

| Base (day N-1) | Target (day N) | Source docs on target day |
|---|---|---|
| 2026-03-02 | 2026-03-03 | sales_journal, daily_revenue |
| 2026-03-03 | 2026-03-04 | sales_journal, daily_revenue, hp |
| 2026-03-29 | 2026-03-30 | sales_journal, daily_revenue, ar_summary, hp, market_segment |
| 2026-04-03 | 2026-04-04 | sales_journal, daily_revenue, ar_summary, hp, market_segment |
| 2026-04-04 | 2026-04-05 | sales_journal, daily_revenue, ar_summary, hp, market_segment |

### Iteration approach

Same fix-loop as the nightly-balance integration: run → N fail → diagnose first failure → fix the filler/mapper/macro → re-run → repeat until all 5 green.

## 3. Sub-project B: Full shift simulation

### The test flow

One Playwright test using the 2026-03-29 → 2026-03-30 consecutive pair:

**Step 1 — Navigate**
- `page.goto('/rj/native')` with auth cookie + livecard mode enabled

**Step 2 — Import yesterday's RJ**
- Find the import UI element (file input or button)
- Upload `test_fixtures/2026-03-29/ground_truth_rj.xls`
- Wait for session creation confirmation
- Verify `SESSION.audit_date === '2026-03-30'`

**Step 3 — Clear daily tabs**
- Click "Tout effacer (Recap+Trans+GEAC)" button
- Accept the confirmation dialog
- Wait for the clear to complete

**Step 4 — Upload tonight's PDFs**
- Upload each source doc from `test_fixtures/2026-03-30/` through the file input, one at a time
- After each upload: wait for livecard refresh, observe DC shifting

**Step 5 — Fill seeded fields per tab**
- Same approach as the existing `nightly-flow.spec.js`
- Values from `tests/playwright/fixtures/seed-2026-03-30.json`
- Recap, Transelect, GEAC, DueBack, SD, Jour tabs
- Blur each field to trigger debounced save

**Step 6 — Verify DC = $0.00**
- `#livecard-dc` text === `'$0.00'`
- `#livecard-dc` has class `.ok`
- `#livecard-verdict` contains `'Équilibré'`

**Step 7 — Export the completed RJ**
- Click the export button
- Capture the download via `page.waitForEvent('download')`

```js
const [download] = await Promise.all([
  page.waitForEvent('download'),
  page.click('#btn-export-rj'),
]);
const filePath = await download.path();
```

**Step 8 — Verify the downloaded .xls**
- Read with SheetJS (`xlsx` npm package) in Node.js
- Assert 38 sheets exist with correct names
- Assert controle date fields show 2026-03-30
- Assert jour row 30 has DC ≈ 0
- Screenshot the livecard for visual baseline

### Why SheetJS

Playwright runs in Node.js. SheetJS (`xlsx` npm package) reads `.xls` files natively in Node. No Python subprocess needed. Added as a devDep alongside `@playwright/test`.

### What this test proves that no other test does

- Import → clear → fill → export round-trip works through real HTTP
- The download produces a valid .xls the auditor can open
- The exported file has all 38 sheets intact
- VBA preservation (OLEBuilder) didn't corrupt the file
- The controle date is correct (auditor's first sanity check)
- The jour row for day 30 matches what the livecard showed

### Runtime estimate

~90 seconds. Runs after Sub-project A is green.

## 4. File structure

### New files

| File | Lines (est.) | Responsibility |
|---|---|---|
| `tests/test_export_verification.py` | ~300 | Sub-project A: parametrized pytest over 5 consecutive pairs, cell-level comparison |
| `tests/playwright/shift-simulation.spec.js` | ~250 | Sub-project B: full shift simulation for 2026-03-29 → 2026-03-30 |
| `tests/playwright/fixtures/seed-2026-03-30.json` | ~80 | Seeded field values for the shift simulation |

### New devDep

- `xlsx` npm package (SheetJS) for reading `.xls` in Node.js inside the Playwright test

### Modified files (only if bugs discovered during iteration)

| File | When |
|---|---|
| `utils/rj_filler.py` | Cell written to wrong address or missing |
| `utils/rj_mapper.py` | `CELL_MAPPINGS` has wrong mapping |
| `utils/ole_builder.py` | VBA preservation corrupts sheets |
| `routes/audit/rj_native.py` | Export endpoint drops data |

### Not touched

- `templates/audit/rj/rj_native.html` — no UI changes
- `database/models.py` — no schema changes
- Existing tests — no modifications

## 5. Success criteria

1. `pytest tests/test_export_verification.py -v --tb=no` → all 5 consecutive pairs PASS (cell-level match, 38 sheets present)
2. `npx playwright test shift-simulation.spec.js` → PASS (DC=$0.00, download verified, 38 sheets, correct date)
3. All existing tests still pass (no regressions)
4. Every compared cell is penny-perfect (`abs(diff) < 0.01`)
5. Exported `.xls` is openable by xlrd (Python) and SheetJS (Node) without corruption errors

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| `RJFiller` needs a valid base template; `Rj Vierge.xls` isn't on disk | Use day N-1's `ground_truth_rj.xls` as the base — mirrors the real auditor flow |
| `CELL_MAPPINGS` may not cover every cell the auditor's ground truth has | The comparison only checks cells in `CELL_MAPPINGS`. Un-mapped cells are ignored. If a comparison fails because the expected cell isn't in the mapping, extend the mapping. |
| xlutils subtly alters formatting during `copy()`, causing spurious cell diffs | Compare numeric values only, skip text/formatting cells. Use `_as_float` with tolerance. |
| SheetJS reads `.xls` differently than xlrd (decimal precision, date encoding) | The Playwright test checks structural facts (sheet count, sheet names, date fields) and one DC value — not full cell-level comparison (Sub-project A covers that in Python). |
| The "Tout effacer" dialog blocks Playwright | Use `page.on('dialog', d => d.accept())` to auto-accept confirmation dialogs. |
| Export endpoint requires a base file in the DB archive or memory cache | The import step (step 2) stores the uploaded file via `_persist_rj()` + `_archive_rj_to_db()`, which the export endpoint reads back. The import-before-export test flow matches real usage. |
| `envoie_dans_jour()` or `calcul_carte()` write to wrong row for the target day | The filler methods take `day` as an argument. Verify the day number is correct (day of month, not day index). |

## 7. YAGNI exclusions

- No VBA execution testing (verify streams are preserved, not that they run)
- No formatting/style comparison (fonts, colors, cell borders)
- No formula evaluation (xlrd/SheetJS read cached values, not live formula results)
- No multi-month boundary testing (all fixture days are within March-April 2026)
- No concurrent session testing
- No mobile/responsive testing
- No PDF export testing (only Excel)

## 8. Open questions

None — all design decisions are locked.

## 9. Handoff

Next step: invoke `superpowers:writing-plans` to produce the implementation plan. The plan will split into:

1. Sub-project A infrastructure (test skeleton, cell comparison helpers)
2. Sub-project A iteration loop (fix export bugs until all 5 pairs green)
3. Sub-project B (generate seed JSON, write Playwright spec, run)
4. Final verification (all layers)

No git commits are made by Claude — the user handles all git operations.
