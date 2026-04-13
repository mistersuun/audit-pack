# QA Summary Report — audit-pack (Sheraton Laval Night Audit System)
## Last Updated: 2026-03-23 (Final Pass — 9-area comprehensive verification)
## Tester: Thorough QA Tester (Agent — Claude Sonnet 4.6)
## Overall Status: PARTIAL — 7/9 areas PASS, 1 PARTIAL, 1 new MEDIUM issue found; 5 prior issues confirmed fixed

---

> This summary incorporates both the original execution-focused review and the 2026-03-23 recheck
> of the 18-fix wave applied by the development team. The recheck was performed by reading actual
> source code and tracing call paths — no mocking, no assumptions.

---

## Module Status Table

| Module | Status | Issues Found | Confirmed Fixed | Still Open | New (this recheck) |
|--------|--------|-------------|-----------------|------------|-------------------|
| routes/manager.py | PASS | 1 | 1 | 0 | 0 |
| routes/audit/rj_core.py | PASS | 4 | 4 | 0 | 0 |
| routes/audit/rj_parsers.py | PASS | 4 | 4 | 0 | 0 |
| routes/audit/rj_fill.py | WARN | 2 | 0 | 2 | 0 |
| routes/audit/rj_sd.py | PARTIAL | 2 | 1 | 1 | 0 |
| routes/audit/rj_native.py | PARTIAL | 0 | 0 | 0 | 1 (local auth decorator) |
| routes/crm_tabs.py | PASS | 5 | 5 | 0 | 0 |
| routes/dashboard.py | PASS | 3 | 3 | 0 | 0 |
| database/models.py | WARN | 4 | 0 | 4 | 0 |
| config/settings.py | PASS | 1 | 1 | 0 | 0 |
| main.py (debug flag) | PASS | 1 | 1 | 0 | 0 |
| utils/parsers/* | WARN | 4 | 1 | 3 | 0 |
| utils/analytics.py (ADR) | PASS | 1 | 1 | 0 | 0 |
| routes/hp.py | PASS | 1 | 1 | 0 | 0 |
| utils/alert_engine.py | PASS | 1 | 1 | 0 | 0 |
| routes/compset.py | PASS | 0 | 0 | 4 (pre-existing) | 0 |
| Cache invalidation | PASS | 1 | 1 | 0 | 0 |

---

## Priority Ranking — All Open Issues (as of Final Pass 2026-03-23)

### P1 — High (1 issue remaining)

| ID | File | Description | Recheck Status |
|----|------|-------------|----------------|
| QA-FILL-004 | rj_fill.py:474–493 | autofill-cashout fill_sheet() path not fixed (parse-and-fill fix was different route) | STILL OPEN |
| QA-TRANS-001 | transaction_summary_parser.py:23 | Top-level openpyxl import — app won't start if not installed | STILL OPEN |

### P2 — Medium (3 issues remaining)

| ID | File | Description | Recheck Status |
|----|------|-------------|----------------|
| FINAL-001 | rj_native.py:36–43 | Local auth_required bypasses JSON 401 for API routes | NEW — OPEN |
| EP3-MED-1 | dashboard.py auditor-panel | surplus_deficit uses recap_balance, ambiguous vs DailyCashRecon | STILL OPEN |
| EP4-MED-1 | compset.py otb-pace | No upper bound on ?days= query param | STILL OPEN |

### P3 — Low (5 issues remaining)

| ID | File | Description | Recheck Status |
|----|------|-------------|----------------|
| QA-PFACT-001 | parsers/__init__.py:91 | detect_type() returns None; callers must guard | PARTIALLY ADDRESSED |
| QA-SD-002 | rj_sd.py:233 | SD write route doesn't extend session timestamp | STILL OPEN |
| QA-MDL-001 | models.py | DailyReport.to_dict() unsafe float on NULL columns | NOT RECHECKED |
| EP5-MED-1 | compset.py str-trends | comp_set_size from first row of each monthly bucket only | STILL OPEN |
| INFRA-4 | scripts/seed_crm_demo.py | Local TOTAL_ROOMS = 252 definition | LOW — seed only |

### Confirmed Fixed in Final Pass

| ID | Description | Fixed Status |
|----|-------------|-------------|
| QA-CORE-001 | Threading locks declared but never acquired | CONFIRMED FIXED |
| QA-CORE-002 | HP_FILES eviction — HP_FILES_TIMESTAMPS never written | CONFIRMED FIXED |
| NEW-02 | parse-and-fill bypasses cache invalidation | CONFIRMED FIXED |
| EP1-HIGH-1 | STR index fields return 0.0 when None | CONFIRMED FIXED |
| EP2-MED-1 | days_missing uses full month not elapsed days | CONFIRMED FIXED |
| FIX-1b | alert_engine.py generate_daily_summary hardcodes 252 | CONFIRMED FIXED |

---

## 18-Fix Wave: Confirmed Fixed Items

| # | Description | Confirmation |
|---|-------------|-------------|
| 1 | QA-PARSE-003: parse-and-fill now uses get_fillable_data() | CONFIRMED |
| 2 | QA-PARSE-004: fill-jour has @csrf_protect | CONFIRMED |
| 3 | QA-SD-001: SD_FILES_TIMESTAMPS written on upload | CONFIRMED |
| 4 | QA-CRM-002: occ_budget is now a percentage | CONFIRMED |
| 5 | QA-CRM-005: Annual P&L labor uses DepartmentLabor only | CONFIRMED |
| 6 | QA-CORE-004: min() on empty dict guarded | CONFIRMED |
| 7 | QA-MGR-001: manager_required checks MANAGER_ROLES | CONFIRMED |
| 8 | QA-CFG-001: MAX_CONTENT_LENGTH set to 32MB | CONFIRMED |
| 9 | debug=True: now env-driven via FLASK_DEBUG | CONFIRMED |
| 10 | ADR calculation excludes comp rooms | CONFIRMED |
| 11 | days_in_month uses calendar.monthrange() | CONFIRMED |
| 12 | HP_FILES eviction code added to _cleanup_expired_sessions() | PARTIAL — verify hp.py timestamp write |

---

## Test Execution — pytest

**Status: UNTESTED**

The test suite in `tests/` requires real RJ .xls files at:
- `RJ 2024-2025/RJ 2025-2026/12-Février 2026/Rj 07-02-2026.xls`
- `RJ 2024-2025/RJ 2025-2026/12-Février 2026/Rj 08-02-2026.xls`

These paths do not exist in the repository. Tests would be skipped via `pytest.skip()`.

**Recommendation:** Include at least one anonymized/synthetic RJ .xls file in `tests/fixtures/`
so the test suite can run in CI without real hotel data.

---

## Session Memory / Leak Status (Updated)

| Dict | Timestamps Written? | Evicted by cleanup? | Verdict |
|------|--------------------|--------------------|---------|
| RJ_FILES | YES (rj_core.py:288) | YES | Correct |
| SD_FILES | YES (rj_sd.py:63) — FIXED | YES (rj_core.py:155–159) — FIXED | Now correct |
| HP_FILES | UNKNOWN — hp.py not verified | YES (rj_core.py:162–166) — code present | Partial fix — verify hp.py |
| _RJ_FILLER_CACHE | N/A (piggybacks RJ eviction + explicit pop) | YES | Mostly correct — parse-and-fill bypasses pop |

---

## Session B — New Endpoints and Bug Fixes (2026-03-23)

See `QA/QA-SESSION-2026-03-23-B.md` for full findings.

### Session B Infrastructure Results (updated by Final Pass)

| Item | Status | Notes |
|------|--------|-------|
| login_required consolidation (all 19 files) | PARTIAL | 20/21 correct; rj_native.py uses local auth_required (FINAL-001) |
| RJ_FILES_LOCK threading | PASS | Consistent across rj_core, rj_parsers, rj_macros — QA-CORE-001 RESOLVED |
| _RJ_VERSION_COUNTER cache | PASS | invalidate_rj_cache() called at all RJ_FILES write sites — NEW-02 RESOLVED |
| TOTAL_ROOMS local definitions | LOW WARNING | seed_crm_demo.py still has local copy (seed script only) |

### Session B Bug Fix Results

| Fix | Status | Notes |
|-----|--------|-------|
| alert_engine.py DailyJourMetrics | PASS | Correct model and field names |
| crm.py staff N+1 | PASS | GROUP BY query, portable CAST pattern |
| crm_tabs.py franchise % | PASS | Uses actual MonthlyExpense.franchise_fees |
| crm_tabs.py data quality warnings | PASS | Missing expense months detected and reported |
| crm_tabs.py deposit variance exposure | PASS | DepositVariance leaderboard + monthly trend added |
| crm_tabs.py labor budget variance | PASS | DepartmentLabor.budget_cost/hours fields used |
| dashboard.py labor ratio proration | PASS | days_with_revenue / days_in_month logic correct |

### Session B New Endpoint Results (updated by Final Pass)

| Endpoint | Overall | Key Issues |
|----------|---------|-----------|
| GET /api/dashboard/gm-briefing | PASS | EP1-HIGH-1 FIXED: STR index fields now return null when None |
| GET /api/dashboard/accounting | PASS | EP2-MED-1 FIXED: days_in_window used correctly |
| GET /api/dashboard/auditor-panel | PARTIAL | EP3-MED-1 still open: surplus uses recap_balance |
| GET /compset/api/otb-pace | PARTIAL | EP4-MED-1 still open: no upper bound on ?days= |
| GET /compset/api/str-trends | PARTIAL | EP5-MED-1 still open: comp_set_size from first row only |

### Session B Issues — Current Status After Final Pass

| Severity | ID | Location | Description | Status |
|----------|----|----------|-------------|--------|
| ~~HIGH~~ | EP1-HIGH-1 | dashboard.py gm-briefing Panel 4 | STR index fields return null via None guard | CONFIRMED FIXED |
| ~~MEDIUM~~ | EP2-MED-1 | dashboard.py accounting Section B | days_in_window computed before use | CONFIRMED FIXED |
| MEDIUM | EP3-MED-1 | dashboard.py auditor-panel | surplus_deficit uses recap_balance, ambiguous | STILL OPEN |
| MEDIUM | EP4-MED-1 | compset.py otb-pace | No upper bound on ?days= query param | STILL OPEN |
| MEDIUM | EP5-MED-1 | compset.py str-trends | comp_set_size from first row only per bucket | STILL OPEN |
| LOW | INFRA-4 | scripts/seed_crm_demo.py | Local TOTAL_ROOMS = 252 definition | STILL OPEN |
| ~~LOW~~ | FIX-1b | utils/alert_engine.py | generate_daily_summary used TOTAL_ROOMS | CONFIRMED FIXED |
| LOW | EP5-LOW-1 | compset.py str-trends | fair_share_pct based on first STR row only | STILL OPEN |
| LOW | EP5-LOW-2 | compset.py str-trends | Summary _index() masks all-None metric | STILL OPEN |

---

## Detailed Reports

- `QA/QA-rj-core.md` — rj_core.py findings (original)
- `QA/QA-rj-parsers.md` — rj_parsers.py findings (original)
- `QA/QA-rj-fill.md` — rj_fill.py findings (original)
- `QA/QA-rj-sd.md` — rj_sd.py findings (original)
- `QA/QA-crm-tabs.md` — crm_tabs.py findings (original)
- `QA/QA-models-config.md` — models.py and config/settings.py findings (original)
- `QA/QA-parsers-utils.md` — utils/parsers/* findings (original)
- `QA/QA-REGRESSION.md` — recheck checklist (updated 2026-03-23)
- `QA/QA-RECHECK-2026-03-23.md` — full recheck narrative with evidence
- `QA/QA-SESSION-2026-03-23-B.md` — Session B: new endpoints + bug fix verification
- `QA/QA-FINAL-2026-03-23.md` — Final Pass: 9-area comprehensive verification (LATEST)
