# Nightly Balance Integration Test — Design

**Date:** 2026-04-10
**Author:** brainstormed with Claude
**Status:** approved, ready for implementation plan

## 1. Goal & Success Criterion

**Goal:** Prove that for every fixture day with sufficient source documents, the pipeline can reduce DC to zero using only the inputs that were available that night (parseable PDFs/XLS + manually-counted cash envelopes from the ground-truth RJ).

**The single pass/fail assertion per day:**

```
abs(round(balance_check(nas, source_files).dc_decomposition.unexplained_residual, 2)) < 0.01
```

Penny-perfect. Bit-perfect float comparison is unachievable due to accumulated parser arithmetic, but rounded to two decimals the residual must read `$0.00`.

The NightAuditSession is pre-seeded from:

1. **Source PDFs/XLS in the fixture** — parsed and applied via `BalancerService.check_balance(files=...)`. Covers the parseable portion of each day (Sales Journal, Daily Revenue, AR Summary, HP admin, Advance Deposit).
2. **Ground-truth seeder** — fills every NAS field the auditor had in front of them that we don't have as a standalone source file. This includes both purely manual entries (DueBack, SD, Chambres à refaire) and values the auditor hand-entered from reports that aren't in the fixture (Transelect card reports, GEAC balance sheet, Recap values).
3. Nothing else.

**Why the seeder is broader than "manual" fields:** the test goal is "given the same inputs the auditor had that night, can we reach DC = 0?" The auditor had Transelect paper reports + a GEAC balance sheet in addition to the PDFs. We don't have those reports as separate files in the fixture — they only survive inside the completed `ground_truth_rj.xls`. Pulling them from the ground-truth RJ is how we reconstruct "the auditor's input state" for a Layer 2 replay.

**Skipped:** temperature (not needed, not tested).

**Why this is the right bar:**

- A balanced RJ has residual = 0 by definition. An auditor who left work at 3am with residual ≠ 0 was still owed an explanation.
- If the pipeline can't reach 0 on a historical day that the auditor *did* balance, the gap is in our code — a missing column, wrong sign, unapplied compensation, parser dropping a value.
- It's a ratchet: whatever passes today is the floor. Every fix only increases the number of green days.

**Initial state (from today's code):** unknown. First run will reveal which days pass. The iteration loop is: run → `N` fail → diagnose first failure → fix parser/balancer/filler/seeder → re-run → `N-1` fail → repeat until all 18 green.

**Out of scope for the first pass:**

- Days flagged as "unparseable" in `fixture_regression.py` (missing required docs — 6 days)
- Temperature field (skipped entirely)
- Comparing per-class variance values to historical (optional Phase 2 if the residual test isn't sensitive enough)

## 2. Architecture

Three layers, each independently runnable.

### Layer 1 — Ground-truth seeder (pure Python, no Flask)

**File:** `tests/fixtures/ground_truth_seeder.py`

A set of helpers that read `test_fixtures/<day>/ground_truth_rj.xls` and return plain dicts shaped for `NightAuditSession` assignment. No DB, no Flask, no side effects — just xlrd reads.

Each extractor reads one logical group by **sheet name + column labels**, not hardcoded row indices, so small layout variations across days don't break it.

```python
# Purely manual fields (counted cash envelopes, observation)
def extract_dueback(day: str) -> list[dict]:
    """DueBack sheet → per-receptionist cash envelope amounts for col 78 + friends."""

def extract_sd(day: str) -> list[dict]:
    """S&D sheet → per-employee verified amounts."""

def extract_chambres(day: str) -> int:
    """Jour sheet → chambres à refaire count."""

# Fields the auditor hand-entered from paper reports we don't have as files
def extract_transelect(day: str) -> dict:
    """Transelect sheets (Restaurant, Reception, Banquet, FreedomPay) → per-terminal card totals + X20/X24 compensation."""

def extract_geac_balance_sheet(day: str) -> dict:
    """GEAC balance sheet → prev_balance, new_balance, cc_variance, fd, ar, col 41 bottom line."""

def extract_recap(day: str) -> dict:
    """Recap sheet → H19:N19 totals, surplus/deficit, S&D carry-forward values."""

def extract_all(day: str) -> dict:
    """Convenience: bundle every extractor above into one dict keyed by NAS attribute name."""
```

**Output shape:** `extract_all(day)` returns a flat dict of `{nas_attribute_name: value}` that can be applied to a NAS via a simple loop: `for k, v in extract_all(day).items(): setattr(nas, k, v)`. No field ever overlaps a value the balancer would derive from a fixture file (seeder and files write to disjoint sets of NAS fields).

**Reusable outside tests** — any debugging session can import this to replay a historical day's full input state.

### Layer 2 — Pipeline correctness test (pytest, no browser)

**File:** `tests/test_nightly_balance.py`

Parametrized pytest over all parseable fixture days. Per day:

1. Create a fresh NightAuditSession inside a rollback transaction
2. Load source files from `test_fixtures/<day>/` into a `files` dict of `BytesIO` streams (same shape the `/api/rj/native/balance-check` endpoint accepts)
3. Apply seeded fields from Layer 1: `for k, v in extract_all(day).items(): setattr(nas, k, v)` — writes DueBack, SD, Chambres, Transelect rows, GEAC balance sheet, and Recap values directly onto the NAS object (disjoint from what the fixture files will populate)
4. Call `BalancerService.check_balance(nas, files=files, day=d.day)` — this parses the source documents, fills the NAS, and returns the decomposition
5. Assert `abs(round(result["dc_decomposition"]["unexplained_residual"], 2)) < 0.01`
6. On failure, format a rich diagnostic and `pytest.fail(diagnostic)`

**Runtime target:** < 30 seconds for all 18 days.

### Layer 3 — Realistic auditor simulation (Playwright, real Flask server)

**File:** `tests/playwright/nightly-flow.spec.js`

One end-to-end test for **2026-03-21** (has the full set of six source documents), simulating the night auditor's actual workflow:

1. `page.goto('/rj/native')` with auth cookie injected (same pattern as Phase 4 tests)
2. Flip to livecard mode via `localStorage.setItem('rjn_ui_mode', 'livecard')` then reload
3. Create the session via the form UI (`#inp-date`, `#inp-auditor`, startSession trigger)
4. Upload each PDF through the real file input — one at a time, like drag-and-drop:
   - `sales_journal.txt`
   - `daily_revenue.pdf`
   - `ar_summary.pdf`
   - `hp.xlsx`
   - `market_segment.pdf`
   - After each upload: wait for livecard refresh, observe DC shifting
5. Enter the seeded fields through the form UI (not DB write) — every tab the auditor would normally touch:
   - DueBack tab → cash envelope amounts per receptionist
   - SD tab → verified amounts per employee
   - Transelect tab → Restaurant/Reception/Banquet/FreedomPay terminal totals, X20/X24 compensation
   - GEAC tab → balance sheet (prev/new/cc_variance/fd/ar), col 41 bottom line
   - Recap tab → H19:N19 totals, surplus/déficit values
   - Jour tab → chambres à refaire
   - Blur each field to trigger debounced save; observe the DC shrinking after each blur
6. Wait for final `refreshChecklist` debounce
7. Final assertions:
   - `#livecard-dc` text === `'$0.00'`
   - `#livecard-dc` has class `.ok`
   - `#livecard-verdict` text === `'Équilibré ✓'`
   - Screenshot the card for visual regression baseline

**Seeded field values:** hardcoded JSON constants in `tests/playwright/fixtures/seed-2026-03-21.json`, generated once via `python -c "from tests.fixtures.ground_truth_seeder import extract_all, json; print(json.dumps(extract_all('2026-03-21'), indent=2))"` and pasted. No file I/O during the Playwright run.

**Test length reality check:** entering ~25-40 fields via form UI is a lot of Playwright clicks. If this balloons past 200 lines, split the seeded fields into a data-driven loop (`for (const [tab, fields] of seedData.entries())`) rather than hand-writing each input's `.fill()` call.

**Runtime estimate:** ~30 seconds for this one test. Runs after Layer 2 is green — it's the "yes, reaches the screen" gate, not the fix-loop.

### Why three layers

- Layer 1 is reusable for manual debugging, not just tests
- Layer 2 is the ratchet — ~30 second run, tight fix-loop
- Layer 3 proves the number the pipeline computed reaches the screen unchanged

**Why not one big Playwright test per day:** too slow (~15 s × 18 days = 4.5 min/iteration), and failures are harder to diagnose through traces than pytest stacktraces. Pytest is the right tool for the fix-loop.

### Possible divergence between layers

Layer 2 calls `BalancerService.check_balance(files=...)` directly. Layer 3 routes through HTTP upload endpoint + `_apply_parsed_data_to_session`. If these diverge, Layer 2 can pass while Layer 3 fails — useful information (it means the dispatcher is dropping something the direct balancer handles), but worth being aware of.

## 3. The iteration loop

The whole point is the fix-loop. When a day fails Layer 2, the test output must tell you *why* without making you open xlrd and grep the fixture manually.

### Diagnostic output on failure

```
FAILED tests/test_nightly_balance.py::test_day_balances[2026-03-14]

Day: 2026-03-14
─────────────────────────────────────────────────────
SOURCE DOCUMENTS APPLIED:
  ✓ sales_journal.txt       (parsed)
  ✓ daily_revenue.pdf       (parsed)
  ✓ ar_summary.pdf          (parsed)
  ✗ hp.xlsx                 (MISSING from fixture)
  ✓ market_segment.pdf      (parsed)

MANUAL FIELDS SEEDED FROM GROUND TRUTH:
  dueback_reception_lecture = 1234.56    (from ground_truth_rj.xls sheet 'DueBack' row 19)
  sd_petite_caisse_verifie   = 500.00
  jour_chambres_a_refaire    = 3

BALANCE CHECK RESULT:
  dc_calculated        = -2167.86
  declared_sum         = -2165.35
  unexplained_residual = -2.51       ← FAILING (expected 0.00)

VARIANCE CLASSES (10):
  x20_transelect       = -2165.35   [source: transelect.X24]
  geac_bottom          =     0.00
  interhotel_xferin    =     0.00
  panne_lien_hotel     =     0.00   ← expected -2.51 here?
  chambres_annulation  =     0.00
  prior_day_correction =     0.00
  cashier_misposting   =     0.00
  depot_resto_pas_ferme=     0.00
  recap_surplus        =     0.00
  recap_deficit        =     0.00

HYPOTHESIS:
  Residual of -2.51 is unexplained. Check:
  - Is PANNE LIEN HÔTEL column populated in the ground-truth RJ for this day?
  - Is there a balancer class that should catch this value but isn't wired?

BalancerService warnings (if any):
  [warn] AR end_of_day missing, stored_variance defaulted to 0
─────────────────────────────────────────────────────
```

The diagnostic is built by a helper inside `tests/test_nightly_balance.py` — no extra logging infrastructure, just a formatted string passed to `pytest.fail(msg)`.

### Running subsets during fix-loop

```bash
pytest tests/test_nightly_balance.py -v                  # all 18 days
pytest tests/test_nightly_balance.py -v -k "03-14"       # just the broken day
pytest tests/test_nightly_balance.py --tb=no             # summary only
pytest tests/test_nightly_balance.py -x                  # stop at first red
```

### Typical session

```
$ pytest -v --tb=no
  2026-03-02 PASS
  2026-03-03 PASS
  2026-03-14 FAIL  (residual -2.51)
  2026-03-16 FAIL  (residual +18.02)
  ...

$ pytest -v -k "03-14"
  [read diagnostic, identify: PANNE LIEN HÔTEL not wired]
  [fix utils/rj_balancer.py]

$ pytest -v -k "03-14"
  PASS

$ pytest -v --tb=no
  [confirm no regressions, see next failing day]
```

### Common root-cause buckets

| Symptom | Likely fix location |
|---|---|
| Residual matches a known Transelect value but x20_transelect class is 0 | `utils/rj_balancer.py` — X24 pattern matching |
| Residual ≈ GEAC fd − ar | `utils/rj_balancer.py` — geac_bottom formula |
| Residual has HP admin/promo amount | `utils/rj_filler.py` — HP deductions not applied |
| Residual matches a Recap S&D value | `utils/rj_filler.py` — col 78 not fed from ground-truth DueBack |
| Residual has a small tax-like amount | `utils/parsers/sales_journal_parser.py` — truncated decimal |
| Day crashes with KeyError | `utils/parsers/ar_summary_parser.py` — stored_balance regex, etc. |

### Anti-patterns (explicitly banned)

- Automatically "fixing" a failing day by bumping the tolerance. If it doesn't balance to 0, it's a bug.
- `@pytest.skip` on failing days. Every red stays red until fixed.
- Batch-fixing across multiple days at once. One day at a time. Each fix should be a focused commit that explains the root cause.

## 4. File structure & scope boundaries

### New files

| File | Lines (est.) | Responsibility |
|---|---|---|
| `tests/fixtures/ground_truth_seeder.py` | ~350 | Extract manual + hand-entered fields from `ground_truth_rj.xls`: DueBack, SD, Chambres, Transelect rows, GEAC balance sheet, Recap values. Pure Python, no Flask. |
| `tests/test_nightly_balance.py` | ~250 | Parametrized pytest. Includes `apply_parsed_sources`, `apply_manual_fields`, `build_diagnostic`, and `test_day_balances_to_zero`. |
| `tests/playwright/nightly-flow.spec.js` | ~180 | One realistic end-to-end UI test for 2026-03-21. |
| `tests/playwright/fixtures/seed-2026-03-21.json` | ~80 | Hardcoded seeded field values (DueBack + SD + Transelect + GEAC + Recap + Chambres) for the Playwright test. |

### Modified files (bug fixes only, discovered during iteration)

| File | When |
|---|---|
| `utils/rj_balancer.py` | Any missing variance class, sign error, or formula gap |
| `utils/rj_filler.py` | Any dispatcher forgetting a parser or manual field |
| `utils/parsers/*.py` | Any regex dropping a value, wrong decimal handling, missing section |
| `routes/audit/rj_native.py` | Only if `_apply_parsed_data_to_session` is the divergence point between Layer 2 and Layer 3 |

### Not modified in this work (scope boundaries)

- `templates/audit/rj/rj_native.html` — the livecard is already shipped. Rendering fixes go here but should be rare.
- `database/models.py` — no schema changes. All test data transient.
- `scripts/fixture_regression.py` — unchanged; stays as inventory report.
- Any other frontend code — not touched.

### Database strategy

**Layer 2 (pytest):**

- Each test runs inside `app.app_context()` with a transaction rolled back after the test
- Session rows created fresh and never persisted
- No separate test DB required — reuses `database/audit.db` with transaction isolation
- Fallback if rollback is awkward with SQLAlchemy's default session behavior: initialize a `:memory:` SQLite from the production schema

**Layer 3 (Playwright):**

- Existing Phase 4 auth cookie approach still works
- Session is created via the form UI and left in the real DB
- The session creation endpoint should use upsert semantics so the `2026-03-21` session is overwritten on re-runs. **To verify during implementation.** If it doesn't, the test setup must `DELETE FROM night_audit_sessions WHERE audit_date = '2026-03-21'` first.

### Explicit YAGNI exclusions

- No new CI pipeline config (add to existing pytest invocation)
- No test report HTML generator (pytest's built-in output is fine)
- No baseline snapshot files (`residual = 0` is its own spec)
- No parametrized per-class decomposition comparison (Phase 2)
- No temperature field handling
- No Quasimodo parser work (known gap, not in this scope)

## 5. Success criteria

1. `pytest tests/test_nightly_balance.py` runs without errors (infrastructure correct)
2. Every parseable fixture day lands at residual = 0.00 (eventually — may take multiple fix iterations)
3. `npx playwright test nightly-flow.spec.js` passes against a live Flask server
4. `scripts/fixture_regression.py` scores are unchanged or improved (never regressed)
5. Every fix commit has a one-line "why" in the message pointing at the root cause

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Ground-truth XLS layout varies across fixture days | Seeder reads by sheet name + column labels, not hardcoded row indices. Defensive lookup with warnings on missing fields. |
| Seeder has to cover Transelect/GEAC/Recap sheets with varied layouts across days (different terminal lists, different tax accumulators, different Recap row counts) | Write each extractor against 2-3 fixture days during development. Each extractor has its own unit test asserting it returns the expected NAS dict for a known day. If a day has a sheet layout the extractor can't handle, it raises a clear `SeederLayoutError(day, sheet)` the pytest diagnostic surfaces directly. |
| Seeder and fixture files both try to populate the same NAS field (double-write conflict) | The seeder and the balancer's fixture-file path must write to disjoint NAS fields. Enforced by a unit test: `test_seeder_fields_disjoint_from_balancer_fields` asserts the key sets don't overlap for any day. |
| Transaction rollback breaks SQLAlchemy session state in unexpected ways | Fallback to `:memory:` SQLite in the pytest conftest. |
| Layer 2 and Layer 3 diverge (parser path differences) | Both failure modes surface as test failures. Divergence is information, not a blocker. |
| Days that cannot balance to 0 reveal they need inputs we don't have access to | The seeder is extended to extract additional manual fields. If that's still not enough, the day becomes "blocked" in `fixture_regression.py` and excluded. Requires explicit user approval per-day. |
| Manual fields in ground-truth RJ are themselves wrong (auditor error) | Out of scope. If the historical RJ is wrong, we can't match it. Document which days this applies to and exclude them with a note. |
| The `_apply_parsed_data_to_session` path drops fields the direct balancer handles | Fix the dispatcher in `routes/audit/rj_native.py`. This is an expected class of bug the test surfaces. |

## 7. Open questions

None — all design decisions are locked.

## 8. Handoff

Next step: invoke `superpowers:writing-plans` to produce the implementation plan. The plan will split the work into:

1. Layer 1 — seeder implementation (standalone, testable with a throwaway script)
2. Layer 2 — pytest infrastructure + first parametrized run, capturing the initial "how many days fail" baseline
3. Iteration loop — one sub-task per failing day, each a fix + re-run cycle
4. Layer 3 — Playwright end-to-end test once Layer 2 is all green

No git commits are made by Claude for this work — the user handles all git operations.
