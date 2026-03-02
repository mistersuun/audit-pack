# RJ 24-02-2026 Reconciliation Analysis
## Night Audit Financial Discrepancy Report

**Date:** February 24, 2026  
**Auditor:** Souleymane Camara  
**File:** Rj 24-02-2026.xls

---

## EXECUTIVE SUMMARY

The RJ for 24-02-2026 has a **critical balancing failure of -$65,356.43** in the Quasimodo reconciliation. This represents a **HUGE gap** between:

- **Cards + Cash recorded:** $81,413.25
- **JOUR Daily Revenue reported:** $146,769.68
- **Variance:** -$65,356.43 (cards/cash are underrecorded vs JOUR)

This suggests either:
1. **JOUR tab has false/inflated revenue entries** (most likely)
2. **TRANSELECT tab is missing significant card sales**
3. **Major GL posting discrepancy between Lightspeed revenue and actual card settlements**

---

## DETAILED BREAKDOWN

### 1. RECAP TAB — Cash Reconciliation

| Line Item | Amount |
|-----------|--------|
| Cash LS (Comptant Positouch) | $262.59 |
| Cheque Daily Revenue | $23,251.79 |
| **Subtotal** | **$23,514.38** |
| Less: Remb. Gratuité | -$430.78 |
| Less: Remb. Client | -$1,859.86 |
| **Subtotal after reimbursements** | **$21,223.74** |
| Less: Due Back Réception | -$1,859.86 |
| Less: Due Back N/B | -$1,859.86 |
| **Total to Deposit (NET)** | **$24,943.46** |
| Surplus/Déficit | -$1,691.67 |
| **ACTUAL Deposit CDN** | **$23,251.79** |
| **Money Received** | **$25,542.43** |

**Status:** RECAP is internally consistent. Money received = Deposit + Reimbursements collected. ✓

---

### 2. TRANSELECT TAB — Card Sales by Terminal

#### Restaurant/Banquet/Spesa Sales (NET after escompte):
```
DÉBIT:          $    697.14
VISA:           $  3,696.58
MASTER:         $  2,581.38
DISCOVER:       $      0.00
AMEX (net):     $    566.79
RESTAURANT TOTAL:    $  7,541.89
```

#### Reception Sales (NET after escompte):
```
VISA:           $ 33,488.63
MASTER:         $ 12,538.92
DISCOVER:       $      0.00
AMEX (net):     $  4,592.02
RECEPTION TOTAL:     $ 50,619.57
```

**TRANSELECT TOTAL (NET):** $58,161.46

---

### 3. GEAC TAB — Terminal Settlement Report

| Card | Daily Cash Out | Daily Revenue |
|------|-----------------|----------------|
| AMEX | $3,854.62 | $4,717.02 |
| MASTER | $9,633.39 | $12,716.96 |
| VISA | $28,477.12 | $34,085.12 |
| **GEAC TOTAL** | **$41,965.13** | **$51,519.10** |

---

### 4. JOUR TAB — Daily Revenue Totals (from RJ Summary)

| Category | Amount |
|----------|--------|
| Nourriture | $33,753.38 |
| Boisson | $5,325.63 |
| N&B & Location Salle | $60,009.01 |
| Room Revenue | $53,962.39 |
| Other Revenues | $27,249.50 |
| **TOTAL JOUR REVENUE** | **$141,220.90** |
| Tips | $5,548.78 |
| **TOTAL JOUR CREDIT** | **$146,769.68** |

---

## RECONCILIATION ANALYSIS

### Quasimodo Check (Theoretical):
```
Card Sales (Transelect, NET):         $ 58,161.46
Cash (Recap, CDN):                    $ 23,251.79
TOTAL (Cards + Cash):                 $ 81,413.25

vs.

JOUR Daily Revenue:                   $141,220.90
Tips:                                 $  5,548.78
TOTAL (Jour Credit):                  $146,769.68

VARIANCE:                             -$ 65,356.43
```

### Problem Areas Identified

#### Problem #1: JOUR Revenue > Cards + Cash by $65,356.43

The **JOUR tab is reporting $146.8k in daily revenue**, but only **$81.4k is accounted for** in actual card + cash deposits. This is a **44% gap**.

The missing $65,356.43 should appear as:
- Additional card sales in TRANSELECT
- Additional cash in RECAP
- Journal entries/transfers not yet recorded
- **Most likely: FALSE GL postings in JOUR**

#### Problem #2: AMEX Discrepancy ($441.79)

| Source | AMEX Amount |
|--------|------------|
| Transelect Rest + Recept (NET) | $5,158.81 |
| GEAC Daily Revenue | $4,717.02 |
| **Difference** | **$441.79** |

This is suspicious. The 0.9735 AMEX factor should only apply in Quasimodo reconciliation (reducing GEAC AMEX by ~2.65%), not in Transelect. The $441.79 gap suggests:
- AMEX escompte (fees) are being double-applied
- AMEX corrections/chargebacks not recorded in GEAC
- Rounding errors in multiple terminations

#### Problem #3: Cash Reconcilement Oddity

- **Recap shows:** Deposit CDN = $23,251.79
- **Money Received:** $25,542.43
- **Difference:** $2,290.64 (exactly: Remb Client + Remb Gratuité = $1,859.86 + $430.78)

This is actually correct — the reimbursements are collected and added to the deposit amount. ✓

---

## ROOT CAUSE HYPOTHESIS

### Most Likely Scenario: JOUR GL is Inflated

The JOUR tab is posting **$141.2k in daily revenue**, but only $81.4k can be traced to actual card terminals (Transelect/GEAC) + cash (Recap). 

**The missing $65.4k appears to be:**

1. **Rooms revenue double-entry** — Possibly posted to both Jour tab AND Quasimodo, causing duplication
2. **F&B GL entries from Lightspeed** — Lightspeed may have GL-posted sales that haven't yet been settled on Transelect terminals
3. **Advance deposits/transfers** — Customer prepayments or inter-department transfers miscoded as revenue
4. **AR/Invoice revenue** — Direct billing (no cash/card at POS) mixed into daily revenue
5. **Reconciliation of previous day's unmatched transactions**

### Secondary Issue: AMEX Processing

The AMEX amounts are not reconciling between Transelect (terminal capture) and GEAC (settlement). This suggests:
- **Out-of-balance AMEX terminal** — Card is not being processed through the same gateway as others
- **Manual AMEX adjustments** in Transelect that haven't reached GEAC settlement yet
- **Batch settlement timing** — AMEX may settle on a different schedule

---

## WHAT NEEDS TO BE CHECKED

### Immediate Actions

1. **Verify JOUR Room Revenue ($53,962.39)**
   - Cross-check against GEAC Guest Ledger balance movements
   - Verify no double-posting with Recap deposit
   
2. **Audit F&B Postings in JOUR**
   - Compare Jour nourriture total ($33,753.38) vs. sum of all F&B departments
   - Check if Lightspeed GL posted to "daily revenue" GL accounts correctly
   
3. **Reconcile AMEX Terminals**
   - Pull the actual AMEX settlement report from payment processor
   - Compare against GEAC Daily Revenue AMEX amount ($4,717.02)
   - Identify any pending reversals or chargebacks
   
4. **Check Transelect Completeness**
   - Verify all POS terminals are represented in Transelect
   - Check for missing transaction batches from any terminal
   - Confirm Debit card terminal is functioning

### Detailed Analysis Needed

5. **DueBack Reconciliation**
   - The "Due Back" amounts ($1,859.86 × 2 for Recept & N/B) represent customer money held
   - Verify these are in-house accounts, not POS corrections
   
6. **Remboursement Tracking**
   - $430.78 refunds (gratuité/comps) — verify GL account 
   - $1,859.86 customer refunds — verify GL account
   - These should NOT appear in daily revenue if properly coded
   
7. **Cash Difference Correction**
   - Recap shows -$1,691.67 surplus/déficit
   - This is NOT being properly addressed in the deposit calculation

---

## QUANTIFIED ISSUES

| Issue | Amount | Status |
|-------|--------|--------|
| Quasimodo Variance | -$65,356.43 | CRITICAL |
| AMEX Terminal Gap | $441.79 | MAJOR |
| Cash Shortage (S&D) | -$1,691.67 | MODERATE |
| **TOTAL UNRECONCILED** | **-$67,489.89** | **FAIL** |

---

## RECOMMENDATION

**DO NOT SUBMIT THIS RJ UNTIL THE FOLLOWING ARE RESOLVED:**

1. ✗ Identify the $65.4k missing from Jour revenue
2. ✗ Reconcile AMEX payment terminal to GEAC settlement
3. ✗ Account for the $1,691.67 cash shortage
4. ✗ Verify all GL postings from Lightspeed match POS terminal settlements

**Action:**
- Run a **detailed GL reconciliation** comparing Lightspeed daily revenue GL posts vs. Transelect/GEAC terminal settlements
- Pull **individual POS transaction reports** for each department to compare against Jour entries
- Contact **payment processor** for complete settlement reports (may be timing issues with batch settlement)
- Conduct **physical cash count verification** against Recap recorded amount

---

**Report Generated:** 2026-02-27  
**Data Source:** Rj 24-02-2026.xls (Recap, Transelect, GEAC, Jour sheets)
