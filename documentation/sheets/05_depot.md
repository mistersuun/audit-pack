# Depot - Bank Deposit Tracking (`Depot`)

**Excel Sheet:** `Depot` | **UI Tab:** Depot | **Dimensions:** 42 x 14
**Template:** templates/audit/rj/tabs/depot.html
**Mapper:** utils/rj_mapper.py -> reset ranges
**API:** POST /api/rj/deposit

## 1. Purpose

The Depot sheet tracks physical bank deposits for two accounts: a Canadian (CDN) account and a US account. It records deposit dates, amounts, and signatures, serving as the bridge between the daily SetD verified totals and the Recap sheet's Row 22 (Depot Canadien). The sheet is structured as two parallel sections side by side.

## 2. Sheet Layout

The sheet contains two parallel deposit tracking sections:

| Section   | Columns | Account            | Currency |
|-----------|---------|--------------------|----------|
| CLIENT 6  | A-G     | #1844-22 (Canadian)| CDN      |
| CLIENT 8  | H-N     | #4743-66 (US)      | US       |

**Per section structure:**

| Column (CDN/US) | Content    |
|------------------|------------|
| A / H            | DATE       |
| B / I            | MONTANT (amount) entries |
| C-F / J-M        | Additional MONTANT entries |
| G / N            | SIGNATURE / TOTAL |

| Row(s)  | Content                        |
|---------|--------------------------------|
| 1-9     | Headers and account info       |
| 10-42   | Data range (deposits)          |

**Reset range:**
```python
'depot': [
    {'row_start': 9, 'row_end': 42, 'col_start': 0, 'col_end': 11},  # A10:K42
]
```

## 3. Field Classification

| Field              | Cell/Range  | Type    | Notes                                    |
|--------------------|-------------|---------|------------------------------------------|
| Headers            | A1:N9       | STATIC  | Account numbers, section titles          |
| CDN deposit date   | A10:A42     | INPUT   | Date of each Canadian deposit            |
| CDN amounts        | B10:F42     | INPUT   | Deposit amount entries (CDN)             |
| CDN signature/total| G10:G42     | MIXED   | Signature or row total                   |
| US deposit date    | H10:H42     | INPUT   | Date of each US deposit                  |
| US amounts         | I10:M42     | INPUT   | Deposit amount entries (US)              |
| US signature/total | N10:N42     | MIXED   | Signature or row total                   |

## 4. Cell Mappings (from rj_mapper.py)

The Depot sheet uses a range-based reset rather than individual cell mappings:

```python
'depot': [
    {'row_start': 9, 'row_end': 42, 'col_start': 0, 'col_end': 11},  # A10:K42
]
```

Data is written dynamically via the `update_deposit()` function rather than through a static mapping dictionary. The function locates the next available row in the appropriate section based on the deposit date.

## 5. Macros & Operations

| Operation        | Function                          | Description                              |
|------------------|-----------------------------------|------------------------------------------|
| Add deposit      | `update_deposit(date_str, amount)`| Insert a deposit record at next free row |
| Reset sheet      | Standard range reset              | Clears A10:K42 for new month             |

**update_deposit(date_str, amount):** Inserts a new deposit entry with the given date and amount into the next available row in the CDN section. The function auto-detects the insertion point.

## 6. Data Flow

```
SetD (verified amounts) ──auto-fill──> Depot (CDN section)
                                           │
                                           ▼
                              Depot amount totals
                                           │
                                    (Excel formula)
                                           ▼
                                  Recap Row 22 (Depot Canadien)
```

- **Upstream:** SetD verified daily amounts auto-fill into Depot entries.
- **Downstream:** Depot totals feed back to Recap Row 22 (Depot Canadien) via Excel formula. This is a formula-based link -- the Depot sheet does not programmatically write to Recap.

## 7. UI Implementation

**Template:** `templates/audit/rj/tabs/depot.html`

The UI provides:
- Side-by-side view of CDN and US deposit sections
- Date picker and amount input for adding new deposits
- POST to `/api/rj/deposit` with `date_str` and `amount` parameters
- Visual alignment with the two-account layout of the Excel sheet

## 8. Known Issues & Gotchas

- **Reset range only covers A10:K42:** Columns L-N (part of the US section) are outside the reset range. Verify whether US-side data is fully cleared on month reset.
- **Auto-fill direction:** Depot is populated from SetD verified amounts. Manual entries should be flagged to avoid double-counting.
- **Row capacity:** The data range supports rows 10-42 (33 rows). Months with daily deposits will fit, but multiple deposits per day could exhaust available rows.
- **Formula link to Recap:** The Depot-to-Recap connection is an Excel formula, not a Python write. Changing the Depot sheet structure may break the formula reference at Recap Row 22.
- **Two currencies:** CDN and US sections are independent. Ensure the API does not accidentally write US amounts into the CDN section or vice versa.
