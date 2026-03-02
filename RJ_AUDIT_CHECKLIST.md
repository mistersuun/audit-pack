# RJ 24-02-2026 Audit Remediation Checklist

**File:** Rj 24-02-2026.xls  
**Date:** February 24, 2026  
**Auditor:** Souleymane Camara  
**Critical Variance:** -$65,356.43 (MUST RESOLVE)

---

## EXECUTIVE STATUS

**SUBMISSION STATUS:** ❌ BLOCKED — DO NOT SUBMIT UNTIL ITEMS BELOW ARE COMPLETED

**Key Issues:**
1. **Quasimodo variance of -$65,356.43** (Cards + Cash don't match JOUR revenue)
2. **AMEX terminal settlement mismatch ($441.79)**
3. **Cash shortage of -$1,691.67** (recorded in Recap S&D field)
4. **Transelect vs GEAC variance ($6,642.36 unexplained)**

---

## IMMEDIATE ACTIONS (Complete Today)

### ❌ ACTION #1: Verify JOUR Room Revenue ($53,962.39)

**What:** The Jour tab shows room revenue of $53,962.39 (38% of daily total). This is suspicious because:
- Rooms revenue should appear in GEAC Guest Ledger, not directly as cash
- Cannot be traced to any card/cash settlement in this audit

**Steps:**
1. [ ] Pull GEAC Guest Ledger balance report for Feb 24
   - Check "Balance Previous Day" vs "Balance Today"
   - Expected movement: should match room revenue
2. [ ] Cross-reference room sales in Lightspeed
   - Pull daily room revenue report from Lightspeed GUI
   - Compare against JOUR value of $53,962.39
3. [ ] Check if rooms are duplicated
   - Is this amount appearing BOTH in Jour AND in Guest Ledger?
   - If yes, remove from one location
4. [ ] Verify no advance deposits/prepayments
   - Check if customer deposits are coded as room revenue
   - These should be LIABILITY, not revenue

**Expected Outcome:** Either:
- Confirm room revenue is correct and appears once
- Or identify the overstatement and correct

---

### ❌ ACTION #2: Reconcile F&B Sales (Nourriture + Boisson + Location Salle)

**What:** JOUR shows:
- Nourriture: $33,753.38
- Boisson: $5,325.63
- Location de Salles: $20,930.00
- **Total F&B: $60,009.01**

But Transelect (actual card settlements) shows only **$7,541.89** for restaurants. Where is the other $52,467.12?

**Steps:**
1. [ ] Pull individual F&B department reports from Lightspeed
   - Café: _________
   - Piazza/Bar: _________
   - Marché/Spesa: _________
   - Banquet: _________
   - Room Service: _________
   - **Total:** _________
   
2. [ ] Compare Lightspeed department totals to JOUR entries
   - Do the numbers match exactly?
   - If not, identify which department(s) are wrong

3. [ ] Check POS terminal batches
   - Pull transaction report from each F&B terminal
   - Verify all transactions are included in Transelect
   - Look for batches not closed (pending settlements)

4. [ ] Identify non-POS F&B revenue
   - Room service (cash, not terminal)?
   - Invoice/catering (direct billing)?
   - Staff meals (comps, not cash)?
   - These would NOT appear in card/cash reconciliation

5. [ ] Reconciliation table:

   | Department | Lightspeed GL | POS Terminal | Variance | Notes |
   |-----------|---------------|--------------|----------|-------|
   | Café      | $           | $           | $        |       |
   | Piazza    | $           | $           | $        |       |
   | Marché    | $           | $           | $        |       |
   | Banquet   | $           | $           | $        |       |
   | Room Svc  | $           | $           | $        |       |
   | Location Salle | $      | $           | $        |       |
   | **TOTAL** | **$60,009** | **$7,542**  | **-$52,467** |  |

---

### ❌ ACTION #3: Audit the "Other Revenues" Category ($27,249.50)

**What:** JOUR shows "Other Revenues" of $27,249.50 (19% of total). These include:
- Audio-Visual: $25,194.43
- Tabagie/Shop: $764.24
- Internet: $166.83
- Massage, Buanderie, Nettoyage, etc.

**Problem:** These are showing as daily REVENUE but don't match any POS/cash settlement.

**Steps:**
1. [ ] Verify Audio-Visual revenue ($25,194.43)
   - [ ] Is this one-time invoice or actual daily revenue?
   - [ ] Is it being billed directly (AR) or collected in cash?
   - [ ] Should this even be in daily revenue?

2. [ ] Check Internet charges ($166.83)
   - [ ] Verify against actual guest internet charges
   - [ ] Is this POS-captured or manually invoiced?

3. [ ] Review Other categories
   - [ ] Tabagie/Shop: Is this a retail vending machine? Where's the cash?
   - [ ] Massage: Who paid? Cash tip or card?
   - [ ] Buanderie: Laundry service charges

4. [ ] Determine which are TRUE revenue vs prepayments/deposits
   - Separate into:
     - **Collected Revenue** (should appear in deposits)
     - **Accounts Receivable** (customer invoiced, not yet paid)
     - **Customer Deposits** (prepayments, not revenue)

---

### ❌ ACTION #4: Reconcile AMEX Terminal Settlement

**What:** AMEX amounts don't match:
- Transelect shows: $5,158.81 (net after escompte of $140.43)
- GEAC Daily Revenue shows: $4,717.02
- **Difference: $441.79**

This suggests AMEX is either:
- Not settling through GEAC (different processor?)
- Being charged additional fees not in GEAC
- Having transactions manually adjusted in Transelect

**Steps:**
1. [ ] Contact payment processor for AMEX settlement report
   - Request: Daily settlement report for Feb 24, 2026
   - Compare "gross sales" vs "settlement amount"
   - Identify all fees, chargebacks, reversals

2. [ ] Verify GEAC shows all AMEX settlements
   - [ ] Is AMEX Elavon the same as GEAC AMEX?
   - [ ] Check GEAC report for any pending/held amounts
   - [ ] Look for any "adjustment" or "correction" entries

3. [ ] Audit Transelect AMEX entries
   - [ ] Are escompte amounts correct?
   - [ ] Are any reversals/chargebacks missing?
   - [ ] Is AMEX factor (0.9735) being applied twice?

4. [ ] Resolution:
   - [ ] GEAC AMEX amount: $________
   - [ ] Processor settlement: $________
   - [ ] Transelect amount: $________
   - [ ] Explained variance: $________

---

### ❌ ACTION #5: Account for the Cash Shortage (-$1,691.67)

**What:** The Recap tab shows "Surplus/déficit" of -$1,691.67. This means:
- Physical cash count was **$1,691.67 LESS** than what the books said should be there
- This has NOT been properly accounted for in the deposit

**Steps:**
1. [ ] Retrieve cash count worksheet from Feb 24 audit
   - Books balance (per Recap before S&D): $________
   - Physical count (per cash counter): $________
   - Difference: $________
   - Sign-off: ________

2. [ ] Determine reason for shortage
   - [ ] Cashier error/float imbalance?
   - [ ] Unrecorded refunds/voids?
   - [ ] Cash register overages/underages?
   - [ ] Theft/loss?
   - [ ] Deposit envelope error?

3. [ ] Decide treatment:
   - **If minor/explainable:** Adjust to specific GL account (e.g., "Cash Over/Short")
   - **If theft suspected:** Escalate to management, file incident report
   - **If rounding error:** Leave as-is with note

4. [ ] Update Recap
   - [ ] Ensure -$1,691.67 is properly documented
   - [ ] GL posting to correct account
   - [ ] Manager sign-off

---

### ❌ ACTION #6: Verify Transelect vs GEAC Completeness

**What:** Transelect shows higher card totals ($58,161.46) than GEAC settled ($51,519.10), a difference of $6,642.36.

This could be:
- Pending transactions captured but not yet settled
- Terminal batches not closed
- Timing difference (expected)
- OR missing GEAC batches (not expected)

**Steps:**
1. [ ] Pull transaction count from Transelect
   - How many transactions total? _________
   - Date range covered: _________

2. [ ] Pull settlement report from GEAC
   - How many batches closed? _________
   - Final settlement amount: $________
   - Date/time of final close: _________

3. [ ] Compare daily batch reports
   - [ ] Are all terminal IDs represented in both?
   - [ ] Are batch numbers matching?
   - [ ] Any pending/held transactions in either system?

4. [ ] Assess if variance is acceptable
   - If Transelect > GEAC by <$100: Likely pending, OK to proceed
   - If Transelect > GEAC by >$100: Investigate missing batches
   - If GEAC > Transelect: Serious error, must correct

---

## SUPPORTING RECONCILIATION WORKSHEETS

### Worksheet A: JOUR Revenue Breakdown
```
Category                    GL Amount       POS Amount      Variance
===========================================================================
Nourriture                  $33,753.38      $________       $________
Boisson                     $5,325.63       $________       $________
Location de Salles          $20,930.00      $________       $________
Room Revenue                $53,962.39      $________       $________
Other Revenues              $27,249.50      $________       $________
===========================================================================
TOTAL                       $141,220.90     $________       $________
```

### Worksheet B: Card Settlement Reconciliation
```
Card Type       Transelect      GEAC Daily      Variance        Notes
                (Terminal Calc) (Settlement)    
===========================================================================
VISA            $37,185.21      $34,085.12      +$3,100.09      
MASTER          $15,120.30      $12,716.96      +$2,403.34      
AMEX            $5,158.81       $4,717.02       +$441.79        **PROBLEM
DEBIT           $697.14         $0.00           +$697.14        
DISCOVER        $0.00           $0.00           $0.00           
===========================================================================
TOTAL           $58,161.46      $51,519.10      +$6,642.36      
```

### Worksheet C: Cash Flow Verification
```
Recap Deposit CDN:          $23,251.79
Actual deposit receipt:     $________
Remittance note from bank:  $________

Money Received (per Recap): $25,542.43
  = Deposit + Remb Client + Remb Gratuité
  = $23,251.79 + $1,859.86 + $430.78
  = $________

Notes/Discrepancies:
_______________________________________________________________________________
_______________________________________________________________________________
```

---

## SIGN-OFF & APPROVAL

Once all actions above are complete:

**Auditor Verification:**
- [ ] All variances identified and explained
- [ ] GL postings verified
- [ ] POS/terminal batches reconciled
- [ ] Cash count documented
- [ ] Management review completed

**Auditor Name:** _________________________  
**Auditor Signature:** ____________________  **Date:** __________

**Manager Approval:**
- [ ] All issues resolved
- [ ] Documentation complete
- [ ] Ready for submission

**Manager Name:** _________________________  
**Manager Signature:** ____________________  **Date:** __________

---

## FINAL SUBMISSION CHECKLIST

Before submitting RJ to corporate:

- [ ] Quasimodo variance within ±$0.01
- [ ] All 14 tabs completed and internally reconciled
- [ ] Cash count verified and signed
- [ ] AMEX settlement confirmed
- [ ] F&B revenue cross-checked to terminals
- [ ] Room revenue verified to Guest Ledger
- [ ] No unexplained variances >$10
- [ ] Manager sign-off obtained
- [ ] RJ locked and submitted

---

**Report Generated:** February 27, 2026  
**Source Data:** Rj 24-02-2026.xls (Recap, Transelect, GEAC, Jour sheets)  
**Reference:** rj_reconciliation_analysis.md, rj_summary_tables.txt
