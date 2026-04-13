# QA Regression Checklist — audit-pack
## Last Updated: 2026-03-23 (RECHECK after 18-fix wave)

This file lists all items that need to be rechecked after fixes are applied.
Items are ordered by priority (P0/P1 first).

---

## P1 — Must Fix Before Production

| ID | Description | File | Fixed By | Recheck Status |
|----|-------------|------|----------|----------------|
| QA-MGR-001 | manager_required checks only `authenticated`, not role | manager.py:22 | 18-fix wave | CONFIRMED FIXED 2026-03-23 |
| QA-CORE-001 | Locks declared but never acquired | rj_core.py:85–97 | — | STILL OPEN — locks declared, never acquired anywhere |
| QA-CORE-002 | HP_FILES never evicted from cleanup | rj_core.py:142–171 | 18-fix wave | PARTIALLY FIXED — eviction code added but HP_FILES_TIMESTAMPS may not be written by hp.py (VERIFY) |
| QA-CORE-003 | SD_FILES_TIMESTAMPS never written on SD upload | rj_sd.py:61 | 18-fix wave | CONFIRMED FIXED 2026-03-23 |
| QA-PARSE-001 | parse-and-fill missing @csrf_protect | rj_parsers.py:70 | 18-fix wave | CONFIRMED FIXED 2026-03-23 (decorator present on line 72) |
| QA-PARSE-004 | fill-jour missing @csrf_protect | rj_parsers.py:150 | 18-fix wave | CONFIRMED FIXED 2026-03-23 (decorator present on line 158) |
| QA-PARSE-003 | parse-and-fill fills zero cells (filter logic wrong) | rj_parsers.py:124–127 | 18-fix wave | CONFIRMED FIXED 2026-03-23 — now uses get_fillable_data() + direct cell writes |
| QA-CFG-001 | No MAX_CONTENT_LENGTH (unlimited upload DoS) | config/settings.py | 18-fix wave | CONFIRMED FIXED 2026-03-23 — 32MB limit + 413 handler |

---

## P2 — Fix Before Next Release

| ID | Description | File | Fixed By | Recheck Status |
|----|-------------|------|----------|----------------|
| QA-CORE-004 | min() on empty RJ_FILES_TIMESTAMPS dict → ValueError | rj_core.py:163 | 18-fix wave | CONFIRMED FIXED 2026-03-23 — guarded with `and RJ_FILES_TIMESTAMPS` |
| QA-CRM-002 | occ_budget uses room count not occupancy % | crm_tabs.py:198 | 18-fix wave | CONFIRMED FIXED 2026-03-23 — now `rooms_target / 252 * 100` |
| QA-CRM-004 | f-string TypeError when year/month are None in DailyCashRecon | crm_tabs.py:728 | 18-fix wave | CONFIRMED FIXED 2026-03-23 — `if not r.year or not r.month: continue` guard on line 728 |
| QA-CRM-005 | Annual P&L double-counts labor from both MonthlyExpense and DepartmentLabor | crm_tabs.py:1124–1143 | 18-fix wave | CONFIRMED FIXED 2026-03-23 — labor sourced exclusively from DepartmentLabor |
| QA-DASH-001 | days_in_month hardcoded as 30 | dashboard.py:536 | 18-fix wave | CONFIRMED FIXED 2026-03-23 — uses calendar.monthrange() |
| QA-TRANS-001 | openpyxl top-level import crashes app if not installed | transaction_summary_parser.py:23 | — | STILL OPEN — top-level import unchanged |
| QA-PFACT-001 | detect_type returns None (scalar) not tuple | parsers/__init__.py:91 | 18-fix wave (partial) | DOCSTRING FIXED — function still returns None for informational-only patterns; callers must guard. |
| QA-FILL-004 | autofill-cashout fill_sheet may fill zero cells (same issue as PARSE-003) | rj_fill.py:474–493 | — | STILL OPEN — autofill-cashout still passes result['data'] to fill_sheet(). Verify fill_sheet() accepts field-name keys. |

---

## P3 — Housekeeping / Low Risk

| ID | Description | File | Fixed By | Recheck Status |
|----|-------------|------|----------|----------------|
| QA-CRM-003 | Tip trend key splitting fragile for hyphenated department names | crm_tabs.py:316–320 | — | NOT RECHECKED (not in 18-fix scope) |
| QA-MDL-001 | DailyReport.to_dict() unsafe float addition with potential None | models.py:141–144 | — | NOT RECHECKED |
| QA-MDL-002 | TaskCompletion orphans possible (no cascade delete) | models.py:670 | — | NOT RECHECKED |
| QA-FILL-002 | update_controle date string formatting drops month | rj_fill.py:580–586 | — | NOT RECHECKED |
| QA-SD-002 | SD write route doesn't extend session timestamp | rj_sd.py:231 | — | CONFIRMED STILL OPEN |
| QA-FREE-001 | FreedomPay parser returns success=True with empty data | freedompay_parser.py:100–108 | — | NOT RECHECKED |

---

## New Items Found During 2026-03-23 Recheck

| ID | Description | File | Recheck Status |
|----|-------------|------|----------------|
| NEW-01 | HP_FILES_TIMESTAMPS may not be written by hp.py — verify | routes/hp.py | NEEDS VERIFICATION |
| NEW-02 | parse-and-fill bypasses save_and_store(), _RJ_FILLER_CACHE not invalidated | rj_parsers.py:139 | OPEN — one-line fix: add `_RJ_FILLER_CACHE.pop(session_id, None)` |

---

## How Other Agents Should Mark Fixes

When you fix an item, add an HTML comment to the corresponding QA file:

```html
<!-- FIXED by [agent-name] on [date]: [brief description of what you changed] -->
```

Then update this table: set "Fixed By" to your agent name and "Recheck Status" to "PENDING RECHECK".

The QA agent will then re-run the affected test and update "Recheck Status" to either "CONFIRMED FIXED" or "STILL BROKEN".

---

## Known Pre-Existing Confirmed Bugs (from prior reviews, now execution-verified)

These were reported by other reviewers and are confirmed by this agent's execution tracing:

1. `manager_required` role bypass — CONFIRMED FIXED (2026-03-23 recheck)
2. Threading locks never acquired — CONFIRMED STILL OPEN
3. HP_FILES never evicted — PARTIALLY FIXED (eviction code added; hp.py timestamp write unverified)
4. parse-and-fill missing CSRF — CONFIRMED FIXED
5. No MAX_CONTENT_LENGTH — CONFIRMED FIXED
6. DailyCashRecon year/month issue — CONFIRMED FIXED (guard added at crm_tabs.py:728)
7. days_in_month hardcoded as 30 — CONFIRMED FIXED
