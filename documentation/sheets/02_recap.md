# Recap (Recap)

**Excel Sheet:** `Recap` | **UI Tab:** Recap | **Dimensions:** ~26 rows x 4 cols (A-D), summary area H-N
**Template:** `templates/audit/rj/tabs/recap.html`
**Mapper:** `utils/rj_mapper.py` -> `RECAP_MAPPING`
**API:** `POST /api/rj/fill/recap`

## 1. Purpose

The Recap sheet is the daily cash reconciliation summary. It collects cash and cheque totals from multiple POS systems (Lightspeed, Positouch), refunds, and due-back amounts, then calculates a net deposit figure. The final balance (D23) must equal exactly $0.00 -- any discrepancy indicates a reconciliation error. The macro `envoie_dans_jour()` copies the daily summary into the Jour sheet for month-end tracking.

## 2. Sheet Layout

```
     A                        B (Lecture)    C (Correction)  D (Net=B+C)    ...  H-N (Summary)
  +-------------------------+--------------+---------------+-------------+
1 |                         |              |               |             |  E1: [date]
2 |                         |              |               |             |
3 |                         |              |               |             |
4 |                         |              |               |             |
5 | (header)                | Lecture      | Correction    | Net         |
  +-------------------------+--------------+---------------+-------------+
6 | Comptant Lightspeed     | [B6]         | [C6]          | =B6+C6      |
7 | Comptant Positouch      | [B7]         | [C7]          | =B7+C7      |
8 | Cheque Payment Register | [B8]         | [C8]          | =B8+C8      |
9 | Cheque Daily Revenu     | [B9]         | [C9]          | =B9+C9      |
10| TOTAL ENCAISSEMENTS     | =SUM(B6:B9)  | =SUM(C6:C9)  | =SUM(D6:D9) |  <- FORMULA
  +-------------------------+--------------+---------------+-------------+
11| Remb. Gratuite          | [B11]        | [C11]         | =B11+C11    |  (negative)
12| Remb. Client            | [B12]        | [C12]         | =B12+C12    |  (negative)
13|                         |              |               |             |
14| TOTAL REMBOURSEMENTS    | =SUM(...)    | =SUM(...)     | =SUM(...)   |  <- FORMULA
  +-------------------------+--------------+---------------+-------------+
15|                         |              |               |             |
16| Due Back Reception      | [B16]*       | [C16]         | =B16+C16    |  *AUTO_FILL
17| Due Back N/B            | [B17]*       | [C17]         | =B17+C17    |  *AUTO_FILL
18| TOTAL A DEPOSER         | =FORMULA     | =FORMULA      | =FORMULA    |  <- FORMULA
  +-------------------------+--------------+---------------+-------------+
19| Surplus / Deficit       | [B19]        | [C19]         | =B19+C19    |
20| TOTAL DEPOT NET         | =FORMULA     | =FORMULA      | =FORMULA    |  <- FORMULA
21|                         |              |               |             |
22| Depot Canadien          | (EXTERNAL)   |               | (EXTERNAL)  |  <- from SD file
23| BALANCE FINALE          | =FORMULA     |               | =FORMULA    |  MUST = $0.00
  +-------------------------+--------------+---------------+-------------+
24| Argent Recu             | [B24]        |               |             |
25|                         |              |               |             |
26| Prepare par             | [B26]        |               |             |
  +-------------------------+--------------+---------------+-------------+

  H19:N19 = Daily summary row -> copied to Jour by macro
```

### Sections

- **Rows 6-10:** Cash receipts (Encaissements) from POS systems
- **Rows 11-14:** Refunds (Remboursements), entered as negative amounts
- **Rows 16-18:** Due-back amounts and total to deposit
- **Rows 19-20:** Surplus/deficit and net deposit
- **Row 22:** External link to SD file deposit
- **Row 23:** Final balance (must be zero)
- **Row 24, 26:** Administrative fields

## 3. Field Classification

| Cell | Field Name | Type | Source | Notes |
|------|-----------|------|--------|-------|
| E1 | date | USER_INPUT | Manual | Audit date for this recap |
| B6 | comptant_lightspeed_lecture | USER_INPUT | Manual | Cash from Lightspeed POS |
| C6 | comptant_lightspeed_corr | USER_INPUT | Manual | Correction to Lightspeed cash |
| D6 | (net) | FORMULA | =B6+C6 | Net Lightspeed cash |
| B7 | comptant_positouch_lecture | USER_INPUT | Manual | Cash from Positouch POS |
| C7 | comptant_positouch_corr | USER_INPUT | Manual | Correction to Positouch cash |
| D7 | (net) | FORMULA | =B7+C7 | Net Positouch cash |
| B8 | cheque_payment_register_lecture | USER_INPUT | Manual | Cheques from payment register |
| C8 | cheque_payment_register_corr | USER_INPUT | Manual | Correction to payment register cheques |
| D8 | (net) | FORMULA | =B8+C8 | Net payment register cheques |
| B9 | cheque_daily_revenu_lecture | USER_INPUT | Manual | Cheques from daily revenue |
| C9 | cheque_daily_revenu_corr | USER_INPUT | Manual | Correction to daily revenue cheques |
| D9 | (net) | FORMULA | =B9+C9 | Net daily revenue cheques |
| Row 10 | (total encaissements) | FORMULA | =SUM | Total cash receipts |
| B11 | remb_gratuite_lecture | USER_INPUT | Manual | Complimentary refunds (negative) |
| C11 | remb_gratuite_corr | USER_INPUT | Manual | Correction to comp refunds |
| D11 | (net) | FORMULA | =B11+C11 | Net comp refunds |
| B12 | remb_client_lecture | USER_INPUT | Manual | Client refunds (negative) |
| C12 | remb_client_corr | USER_INPUT | Manual | Correction to client refunds |
| D12 | (net) | FORMULA | =B12+C12 | Net client refunds |
| Row 14 | (total remboursements) | FORMULA | =SUM | Total refunds |
| B16 | due_back_reception_lecture | AUTO_FILL | DueBack tab | Due-back amount from reception |
| C16 | due_back_reception_corr | USER_INPUT | Manual | Correction to due-back reception |
| D16 | (net) | FORMULA | =B16+C16 | Net due-back reception |
| B17 | due_back_nb_lecture | AUTO_FILL | DueBack tab | Due-back N/B amount |
| C17 | due_back_nb_corr | USER_INPUT | Manual | Correction to due-back N/B |
| D17 | (net) | FORMULA | =B17+C17 | Net due-back N/B |
| Row 18 | (total a deposer) | FORMULA | Calculated | Total to deposit |
| B19 | surplus_deficit_lecture | USER_INPUT | Manual | Surplus or deficit amount |
| C19 | surplus_deficit_corr | USER_INPUT | Manual | Correction to surplus/deficit |
| D19 | (net) | FORMULA | =B19+C19 | Net surplus/deficit |
| Row 20 | (total depot net) | FORMULA | Calculated | Net deposit total |
| Row 22 | (depot canadien) | EXTERNAL_LINK | SD file | Canadian deposit -- NOT editable |
| Row 23 | (balance finale) | FORMULA | Calculated | Must equal $0.00 |
| B24 | argent_recu | USER_INPUT | Manual | Cash received |
| B26 | prepare_par | USER_INPUT | Manual | Prepared by (name) |

## 4. Cell Mappings (from rj_mapper.py)

```python
RECAP_MAPPING = {
    'date': 'E1',                                # Audit date
    'comptant_lightspeed_lecture': 'B6',          # Cash Lightspeed (lecture)
    'comptant_lightspeed_corr': 'C6',             # Cash Lightspeed (correction)
    'comptant_positouch_lecture': 'B7',            # Cash Positouch (lecture)
    'comptant_positouch_corr': 'C7',               # Cash Positouch (correction)
    'cheque_payment_register_lecture': 'B8',       # Cheque payment register (lecture)
    'cheque_payment_register_corr': 'C8',          # Cheque payment register (correction)
    'cheque_daily_revenu_lecture': 'B9',            # Cheque daily revenue (lecture)
    'cheque_daily_revenu_corr': 'C9',              # Cheque daily revenue (correction)
    'remb_gratuite_lecture': 'B11',                # Refund gratuite (lecture, negative)
    'remb_gratuite_corr': 'C11',                   # Refund gratuite (correction, negative)
    'remb_client_lecture': 'B12',                  # Refund client (lecture, negative)
    'remb_client_corr': 'C12',                     # Refund client (correction, negative)
    'due_back_reception_lecture': 'B16',            # Due back reception (auto-filled)
    'due_back_reception_corr': 'C16',              # Due back reception (correction)
    'due_back_nb_lecture': 'B17',                  # Due back N/B (auto-filled)
    'due_back_nb_corr': 'C17',                     # Due back N/B (correction)
    'surplus_deficit_lecture': 'B19',               # Surplus / deficit (lecture)
    'surplus_deficit_corr': 'C19',                 # Surplus / deficit (correction)
    # Row 22: Depot Canadien - NOT EDITABLE (calculated by Excel from SD file)
    'argent_recu': 'B24',                          # Cash received
    'prepare_par': 'B26',                          # Prepared by
}
```

## 5. Macros & Operations

### Reset Operation

The following cell ranges are cleared when resetting the Recap sheet for a new day:

```python
'Recap': [
    {'row_start': 5, 'row_end': 20, 'col_start': 1, 'col_end': 3},  # B6:C20 - all lecture/correction values
    {'row_start': 8, 'row_end': 10, 'col': 3},                       # D9:D10 - net values rows 9-10
    {'row_start': 11, 'row_end': 14, 'col': 3},                      # D12:D14 - net values rows 12-14
    {'row': 15, 'col': 3},                                            # D16 - net due back reception
    {'row': 17, 'col': 3},                                            # D18 - net total a deposer
]
```

**Note:** Reset ranges use 0-indexed rows internally, so `row_start: 5` corresponds to Excel row 6, etc.

### Sync Operations

- **`envoie_dans_jour()`**: Copies H19:N19 (daily summary row) into the Jour sheet at columns BU:CA (cols 72-78) for the corresponding day. This is the primary mechanism for populating the monthly Jour ledger.

### Validation Rules

- **Balance finale (D23) MUST equal $0.00.** A non-zero balance indicates a reconciliation error between the deposit amount and the POS totals.
- Refund fields (B11, C11, B12, C12) should contain **negative** amounts.
- Row 22 (Depot Canadien) must NOT be manually edited -- it is an external link to the SD file.

## 6. Data Flow

### Inputs

- User enters POS cash/cheque readings and corrections from daily reports
- Due-back values (B16, B17) are auto-filled from the DueBack tab
- Depot Canadien (row 22) is linked externally from the SD file

### Outputs

- Daily summary (H19:N19) is copied to the Jour sheet via `envoie_dans_jour()` macro
- Balance finale (D23) serves as the reconciliation check

```
  [Lightspeed]   [Positouch]   [Payment Reg]   [Daily Rev]
       |              |              |               |
       v              v              v               v
  +----------------------------------------------------------+
  |                    Recap (B6:C9)                          |
  |  Lecture (col B)  +  Correction (col C)  =  Net (col D)  |
  +----------------------------------------------------------+
       |                                          |
       |   [DueBack tab] ----> B16, B17           |
       |   [SD file] -------> Row 22              |
       |                                          |
       v                                          v
  +------------------+                  +-------------------+
  | D23: Balance     |                  | H19:N19: Summary  |
  | (must = $0.00)   |                  |                   |
  +------------------+                  +-------------------+
                                               |
                                               v
                                        envoie_dans_jour()
                                               |
                                               v
                                        +-------------+
                                        |  Jour sheet |
                                        |  BU:CA row  |
                                        +-------------+
```

## 7. UI Implementation

- **Template:** `templates/audit/rj/tabs/recap.html`
- **Form fields:**
  - Date field (E1) at top
  - Paired inputs for each row: Lecture (col B) and Correction (col C)
  - Due-back fields (B16, B17) displayed as read-only (auto-filled from DueBack)
  - Argent recu (B24) and Prepare par (B26) at bottom
- **Special behaviors:**
  - Column D values are formulas and should be displayed as computed read-only fields in the UI
  - Row 22 (Depot Canadien) is read-only -- sourced from SD file
  - Balance finale (D23) should be visually highlighted when non-zero to alert the user
  - The `envoie_dans_jour()` macro button copies the daily summary to the Jour sheet
  - Total rows (10, 14, 18, 20, 23) are formula-driven and not directly editable

## 8. Known Issues & Gotchas

- **Row 22 (Depot Canadien) is an EXTERNAL_LINK** to the SD file. If the SD file is not available or the link is broken, this cell will show an error and the balance finale will not reconcile.
- **B16 and B17 are AUTO_FILL** from the DueBack tab. If DueBack data has not been entered for the current day, these cells will be zero or stale, causing an incorrect balance.
- **Refund amounts must be negative.** Entering positive values in rows 11-12 will inflate the deposit total instead of reducing it.
- **The reset operation clears some D-column cells** (D9:D10, D12:D14, D16, D18) which are formulas. This may require recalculation or formula restoration after reset if openpyxl does not preserve them.
- **envoie_dans_jour() writes to fixed columns** (BU:CA = cols 72-78). If the Jour sheet structure changes, this macro mapping must be updated in sync.
- The correction column (C) is designed for small adjustments. Large corrections may indicate a data entry error in the lecture column rather than a legitimate correction.
