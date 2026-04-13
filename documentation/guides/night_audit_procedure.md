# Night Audit Procedure

Step-by-step guide for completing the nightly audit using the audit-pack web interface.

---

## Pre-Audit Preparation

1. **Exchange information** with the evening supervisor -- note any outstanding issues, late checkouts, or special instructions.
2. **Check emails** for notices from accounting (Roula, Mandy) or management.
3. **Verify the fire panel** -- confirm no active alarms.
4. **Organize your workspace** -- clear desk, gather pens, calculator.
5. **Open the audit-pack web app** in your browser (`http://localhost:5000` or the server URL). Enter the audit PIN when prompted.
6. **Start a new audit date** -- the app defaults to today's date. Confirm it is correct.

---

## Audit Workflow Overview

The audit follows a strict order. Each sheet feeds data into the next.

```
DueBack --> SD --> Recap --> Depot --> SetD --> Transelect --> GEAC --> Nouveau Jour
```

Complete each sheet before moving to the next. The app shows validation status (green = balanced, red = variance) on each tab.

---

## Sheet-by-Sheet Instructions

### 1. Nouveau Jour (Opening the New Day)

- Open yesterday's RJ file and save a copy with today's date.
- In the web app, go to the **Controle** tab and update the date and auditor name.
- Clear the contents of RECAP, TRANSELECT, and GEAC tabs (the app may do this automatically).

### 2. SD (Sommaire Journalier des Depots)

The SD reconciles what each employee should have deposited (from Positouch) against what they actually deposited (physical count from the safe).

| Column | Description | Source |
|--------|-------------|--------|
| Montant (Positouch) | Expected deposit amount | Positouch system report |
| Montant Verifie | Actual amount deposited | Physical deposit slip from safe |
| Variance | Difference (auto-calculated) | Montant - Verifie |

**Steps:**
1. Collect all deposit envelopes from the safe.
2. Count each envelope and record the verified amount.
3. Enter values in the SD sheet. The app calculates variance automatically.
4. **Do not print the SD until the Recap balances.**

### 3. Depot

The Depot tab records deposits going to bank accounts (Client 6 and Client 8).

**Steps:**
1. Copy the "Montant Verifie" totals from the SD into the Depot tab.
2. The app provides an **auto-fill from SD** button -- use it to avoid manual copy errors.
3. Enter dates and amounts for each bank client account.
4. Verify the grand total matches the SD verified total.

### 4. DueBack

The DueBack tracks cash owed by or owed to each receptionist.

| Line | Value | Sign |
|------|-------|------|
| Previous (Line 1) | DueBack from yesterday | Negative (-) |
| Current (Line 2) | DueBack from today | Positive (+) |

**Steps:**
1. For each receptionist, enter yesterday's dueback as a negative number.
2. Enter today's dueback as a positive number.
3. Column Z auto-calculates the total. This total feeds into the Recap.

### 5. Recap (Balance Comptant)

The Recap is the central balancing sheet. It must balance to **$0.00**.

**Data sources:**
- Pages 5-6 of the Daily Revenue report (from LightSpeed)
- SD variance total
- DueBack total (Column Z)

**Steps:**
1. Enter Daily Revenue figures from the LightSpeed report.
2. The app auto-pulls the DueBack total and SD variance.
3. Check the balance. If it is not $0.00, review your SD and DueBack entries.

### 6. Transelect (Credit Card Reconciliation)

Transelect reconciles credit card transactions between POS terminals and payment processors.

| Section | Source |
|---------|--------|
| Restaurant | Moneris terminals + Positouch batch reports |
| Reception | FreedomPay / FuseBox reports |

**Steps:**
1. Enter terminal batch totals from Moneris.
2. Enter Positouch credit card totals (Interac, Visa, MC, Amex).
3. Enter FreedomPay settlement totals for reception.
4. Variance must be **$0.00**. If not, recheck terminal batch amounts.

### 7. GEAC (Final Credit Card Balance)

GEAC compares the Daily Cash Out report against the Daily Revenue report.

**Steps:**
1. Enter Daily Cash Out totals.
2. Enter Daily Revenue page 6 totals.
3. Variance must be **$0.00**.
4. **If variance persists:** you cannot correct it yourself. Send an email to accounting (Roula and Mandy) noting the date and variance amount.

### 8. Export / Nouveau Jour (Final Consolidation)

The Jour tab is the master consolidation of the entire audit.

**Data sources:**
- Departures / Arrivals / Stayovers report
- Complimentary Rooms Report
- A/R Summary Report
- Advance Deposit Balance
- Sales Journal for Entire House
- Daily Revenue

**Steps:**
1. Enter occupancy figures (departures, arrivals, stayovers, complimentary rooms).
2. Enter revenue figures from the Sales Journal.
3. Enter Daily Revenue detail columns.
4. Check **Column C (Diff. Caisse)** -- it must be **$0.00**.

---

## Verification Checkpoints

Before submitting, confirm all of the following:

| Checkpoint | Expected Value | Where to Check |
|------------|---------------|----------------|
| SD Variance total | Noted and explained | SD tab, bottom row |
| Recap balance | $0.00 | Recap tab, balance cell |
| Transelect variance | $0.00 | Transelect tab, variance cell |
| GEAC variance | $0.00 | GEAC tab, variance cell |
| Jour Diff. Caisse | $0.00 | Jour tab, Column C |
| Depot grand total | Matches SD verified total | Depot tab, grand total |

The web app highlights each checkpoint in green (pass) or red (fail).

---

## What To Do If Variances Are Found

### SD Variance (Positouch vs. Verified)
- Recount the physical deposit.
- Check if an envelope was missed or double-counted.
- If the variance is confirmed, note the employee name and amount. It carries forward to the Recap.

### Recap Does Not Balance
- Recheck Daily Revenue figures (pages 5-6).
- Verify the DueBack total is correct.
- Confirm SD variance was entered correctly.
- The SD can be adjusted to make the Recap balance -- but only if you find a legitimate counting error.

### Transelect Variance
- Verify each terminal batch total against the physical batch slip.
- Check for duplicate or missed transactions.
- Confirm the Positouch "Etablissement" report matches.

### GEAC Variance
- Do **not** attempt to correct it.
- Send an email to accounting with the date, the Daily Cash Out total, the Daily Revenue total, and the difference.

### Jour Column C Not Zero
- This usually traces back to a GEAC variance or a credit card difference.
- Review Transelect and GEAC first.

---

## Final Submission Steps

1. **Print the SD** (only after the Recap balances).
2. **Prepare the white envelope** for accounting with all required documents.
3. **Prepare the dated blue folder** with all daily reports in the correct order.
4. **Complete the DBRS** (Daily Business Review Summary) as a separate file.
5. **Export the completed RJ** from the web app (PDF or Excel).
6. **File all physical documents** in the appropriate locations.
7. **Log out** of the web app.
