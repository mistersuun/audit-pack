# RJ Auto-Fill Phase 2: End-to-End Write Pipeline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the auto-fill pipeline so uploading source documents produces a fully balanced RJ.xls with all formulas preserved, GEAC/Transelect sheets filled, and audit-trail formulas (=a+b-c) in Jour cells.

**Architecture:** Replace xlutils.copy with Excel COM (pywin32) for all .xls writes. Add GEAC and Transelect fill logic. Update JourMapper to handle corrected operation types. Add G4/adjustments input UI.

**Tech Stack:** Python 3, pywin32 (Excel COM), Flask, Jinja2, existing parser framework

---

## File Map

| File | Changes | Responsibility |
|---|---|---|
| `utils/rj_filler_com.py` | NEW: Excel COM-based RJ filler (replaces xlutils for writes) | Core |
| `utils/jour_mapper.py` | Update compute_all() for new operation types | Core |
| `utils/geac_filler.py` | NEW: Auto-fill GEAC_UX sheet (top + bottom) from parsed DR/AR data | Core |
| `utils/transelect_filler.py` | NEW: Auto-fill Transelect (POSITOUCH, Reception, X24) from SJ/DR | Core |
| `routes/audit/rj_fill.py` | Wire new fillers into existing endpoints | Integration |
| `templates/audit/rj/tabs/import_docs.html` | Add G4, Piazza adj, Spesa adj input fields | UI |
| `tests/test_rj_filler_com.py` | Tests for COM filler | Tests |
| `tests/test_geac_filler.py` | Tests for GEAC fill logic | Tests |
| `tests/test_transelect_filler.py` | Tests for Transelect fill logic | Tests |

---

## Task 1: Build RJFillerCOM (Excel COM writer)

**Files:**
- Create: `utils/rj_filler_com.py`

The core class that replaces xlutils.copy for .xls writes. Uses pywin32 to drive Excel directly, preserving all formulas, tab colors, macros.

Key features:
- Opens .xls via COM, writes formulas (=a+b-c style), saves, closes
- HasFormula guard: skips cells with existing formulas (B, C, BH, CW-CZ, DG-DK)
- Backup before write
- Methods: `write_jour_row(day, values)`, `write_geac(data)`, `write_transelect(data)`

---

## Task 2: Build GEAC auto-filler

**Files:**
- Create: `utils/geac_filler.py`

Fills GEAC_UX sheet from parsed DR + AR data per docs/RJ_AUTOFILL_MASTER.md section 7.2:

**Top (card variance R6/R8/R12):**
- R6: Cash Out = DR Settlement abs - DR Dep Rcvd per card (AMEX/MC/VISA)
- R8: Deposits Received per card
- R12: Daily Revenue per card (= R6+R8 should match)

**Bottom (balance sheet R32-R53):**
- R32/E32: DR p.7 Balance Prev Day (abs)
- R37: DR p.7 Balance Today (abs) / E37 negative
- R41: AR Guest Folios / G41: same (when FD=AR)
- R44/J44: DR p.7 Adv Dep Applied (abs)
- R53/E53: DR p.7 New Balance (abs)

---

## Task 3: Build Transelect auto-filler

**Files:**
- Create: `utils/transelect_filler.py`

Fills Transelect sheet per docs/RJ_AUTOFILL_MASTER.md section 7.1:

**Restaurant POSITOUCH (col X):**
- DEBIT = SJ INTERAC + SJ PANNE INTERACT
- VISA = SJ VISA + SJ PANNE VISA
- MASTER = SJ MC + SJ PANNE MASTER
- AMEX = SJ AMEX + SJ PANNE AMEX

**Reception (cols B and P, col I is formula):**
- B/P per card = DR Settlement amount per card (abs)

---

## Task 4: Update JourMapper for new operation types

**Files:**
- Modify: `utils/jour_mapper.py`

The mapping config now has these operation types that `compute_all()` must handle:
- `geac_compensation`: AP = -(FD - AR Guest Folios)
- `cf_transfer`: CF = AR Guest Folios - AR Payments - DR AR Misc
- `accumulate` with 3 fields: AW = DR Internet + SJ Bqt Internet + InterHotel
- `room_formula`: CK = total_rooms - CM (write as Excel formula)
- Negative accumulator fields: CF has `-balance.ar_payments` (subtract)

---

## Task 5: Add G4/adjustments input UI

**Files:**
- Modify: `templates/audit/rj/tabs/import_docs.html`
- Modify: `routes/audit/rj_fill.py`

Add input fields:
- G4 (Club Lounge deduction): number input, required
- Piazza Nour adjustment: number input, default 0
- Spesa Nour adjustment: number input, default 0
- Advance Deposit on Hand: number input, required

These values feed into the fill pipeline alongside parsed document data.

---

## Task 6: Wire everything into the fill endpoint

**Files:**
- Modify: `routes/audit/rj_fill.py`

Update the parse-and-fill endpoint to:
1. Parse all uploaded docs (DR, SJ, AR, HP, MS, Adv Dep)
2. Validate DR timestamp (reject pre-3AM)
3. Compute GEAC values → write to GEAC sheet via RJFillerCOM
4. Compute Transelect values → write to Transelect sheet via RJFillerCOM
5. Run envoie_dans_jour + calcul_carte macros (or compute equivalent)
6. Compute Jour row → write formulas via RJFillerCOM
7. Verify DC = 0 or DC = X24 (Transelect variance)
8. Return result with DC decomposition

---

## Task 7: Integration testing

End-to-end test with real April 15 documents:
- Upload DR, SJ, AR, HP, MS, Adv Dep for April 15
- Provide G4=60, Piazza adj=0, Spesa adj=3.4
- Verify all 3 sheets filled correctly (GEAC, Transelect, Jour)
- Verify DC = expected Transelect X24 variance
- Verify file size unchanged (formulas preserved)
