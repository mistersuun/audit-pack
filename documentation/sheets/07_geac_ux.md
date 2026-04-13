# GEAC/UX (PMS Balance + Card Variance)

**Excel Sheet:** `geac_ux` | **UI Tab:** GEAC | **Dimensions:** ~53 R x 11 C
**Template:** templates/audit/rj/tabs/geac.html
**Mapper:** utils/rj_mapper.py -> `GEAC_UX_MAPPING`
**API:** POST /api/rj/fill/geac_ux, POST /api/rj/autofill-cashout

## 1. Purpose

The GEAC/UX sheet reconciles two critical aspects of the night audit:

1. **Card Variance** (top section): Compares daily cash-out totals from FreedomPay against daily revenue per card type. Each card type variance must equal $0.00.
2. **GEAC Balance Sheet** (bottom section): Reconciles the PMS (Property Management System) balances -- previous day, today, direct invoices, advance deposits -- to arrive at a new balance figure.

## 2. Sheet Layout

The sheet is divided into two distinct sections:

### Section 1: Card Variance (Rows 4-13)

| Row | Content | Type |
|-----|---------|------|
| 4-5 | Headers / card type labels | STATIC |
| 6 | Daily Cash Out | USER_INPUT |
| 8 | Additional cash out amounts | USER_INPUT |
| 10 | TOTAL (cash out) | FORMULA |
| 12 | Daily Revenue | USER_INPUT |
| 13-14 | VARIANCE (Total - Daily Revenue) | FORMULA |

Card types are laid out across columns: AMEX (B), DINERS (E), MASTER (G), VISA (J), DISCOVER (K).

### Section 2: GEAC Balance Sheet (Rows 30-53)

| Row | Content | Type |
|-----|---------|------|
| 30-31 | Headers | STATIC |
| 32 | Balance Previous Day | USER_INPUT |
| 37 | Balance Today | USER_INPUT |
| 41 | Facture Direct / FO Transfers | USER_INPUT |
| 44 | Advance Deposit Applied | USER_INPUT / PARSED |
| 47-50 | Additional entries | USER_INPUT |
| 53 | New Balance | FORMULA |

The balance section uses two sub-columns: a dollar amount (B) and a guest-count or secondary value (E or G/J depending on row).

## 3. Field Classification

| Field | Cell(s) | Type | Source |
|-------|---------|------|--------|
| Date | E22 | USER_INPUT | Date picker |
| AMEX Cash Out | B6 | USER_INPUT | FreedomPay Transaction Summary |
| DINERS Cash Out | E6 | USER_INPUT | FreedomPay Transaction Summary |
| MASTER Cash Out | G6 | USER_INPUT | FreedomPay Transaction Summary |
| VISA Cash Out | J6 | USER_INPUT | FreedomPay Transaction Summary |
| DISCOVER Cash Out | K6 | USER_INPUT | FreedomPay Transaction Summary |
| AMEX Total | B10 | FORMULA | Auto-calculated |
| DINERS Total | E10 | FORMULA | Auto-calculated |
| MASTER Total | G10 | FORMULA | Auto-calculated |
| VISA Total | J10 | FORMULA | Auto-calculated |
| DISCOVER Total | K10 | FORMULA | Auto-calculated |
| AMEX Daily Revenue | B12 | USER_INPUT | Daily Revenue report |
| DINERS Daily Revenue | E12 | USER_INPUT | Daily Revenue report |
| MASTER Daily Revenue | G12 | USER_INPUT | Daily Revenue report |
| VISA Daily Revenue | J12 | USER_INPUT | Daily Revenue report |
| DISCOVER Daily Revenue | K12 | USER_INPUT | Daily Revenue report |
| Balance Previous Day | B32, E32 | USER_INPUT | PMS / prior day |
| Balance Today | B37, E37 | USER_INPUT | PMS |
| Facture Direct | B41, G41 | USER_INPUT | Front Office |
| Advance Deposit | B44 | USER_INPUT | Manual |
| Adv Deposit Applied | J44 | USER_INPUT / PARSED | PDF parse |
| New Balance | B53, E53 | FORMULA | Auto-calculated |

## 4. Cell Mappings (from rj_mapper.py)

```python
GEAC_UX_MAPPING = {
    'date': 'E22',
    # Daily Cash Out (Row 6)
    'amex_cash_out': 'B6', 'diners_cash_out': 'E6', 'master_cash_out': 'G6',
    'visa_cash_out': 'J6', 'discover_cash_out': 'K6',
    # Total (Row 10) - auto-calculated
    'amex_total': 'B10', 'diners_total': 'E10', 'master_total': 'G10',
    'visa_total': 'J10', 'discover_total': 'K10',
    # Daily Revenue (Row 12)
    'amex_daily_revenue': 'B12', 'diners_daily_revenue': 'E12',
    'master_daily_revenue': 'G12', 'visa_daily_revenue': 'J12', 'discover_daily_revenue': 'K12',
    # Balance Previous Day (Row 32)
    'balance_previous': 'B32', 'balance_previous_guest': 'E32',
    # Balance Today (Row 37)
    'balance_today': 'B37', 'balance_today_guest': 'E37',
    # Facture Direct (Row 41)
    'facture_direct': 'B41', 'facture_direct_guest': 'G41',
    # Adv deposit applied (Row 44)
    'adv_deposit': 'B44', 'adv_deposit_applied': 'J44',
    # New Balance (Row 53) - auto-calculated
    'new_balance': 'B53', 'new_balance_guest': 'E53',
}
```

## 5. Macros & Operations

### Reset Ranges

The `geac_ux` reset clears the following cell ranges before filling new data:

| Row | Ranges Cleared |
|-----|---------------|
| 6 | B6:C6, E6, G6:H6, J6 |
| 8 | B8:C8, E8, G8:H8, J8 |
| 12 | B12:C12, E12, G12:H12, J12 |
| 32 | B32:C32, E32 |
| 37 | B37:C37, E37 |
| 41 | B41:C41, G41:H41 |
| 44 | B44:C44, J44:K44 |
| 47 | B47:C47, E47 |
| 50 | B50:C50, E50 |
| 53 | B53:C53, E53 |

Note: Reset ranges span wider than the mapping targets (e.g., B6:C6 vs just B6) to clear adjacent helper cells.

### Autofill Cash Out

The `/api/rj/autofill-cashout` endpoint populates Row 6 cash-out values from a parsed FreedomPay Transaction Summary. This is a convenience operation that maps parsed card-type totals directly to the cash-out row.

### Formulas

- **Row 10 (Total):** Sums Row 6 + Row 8 per card column. Must not be overwritten.
- **Row 13/14 (Variance):** Row 10 - Row 12 per card column. Target: $0.00 each.
- **Row 53 (New Balance):** Computed from balance rows (32, 37, 41, 44, 47, 50). Must not be overwritten.

## 6. Data Flow

```
FreedomPay Transaction Summary (PDF)
    |
    v
  Parser --> autofill-cashout --> Row 6 (Cash Out per card type)
                                      |
Daily Revenue Report (PDF)            |
    |                                 v
    v                          Row 10: TOTAL (formula)
  Parser --> fill/geac_ux --> Row 12 (Daily Revenue per card type)
                                      |
                                      v
                               Row 13/14: VARIANCE (must = $0.00)

PMS Reports (manual / PDF)
    |
    v
  fill/geac_ux --> Rows 32, 37, 41, 44 (Balance sheet inputs)
                        |
                        v
                  Row 53: NEW BALANCE (formula)
```

## 7. UI Implementation

**Template:** `templates/audit/rj/tabs/geac.html`

The GEAC tab in the web UI provides:
- Card variance section with inputs for cash-out and daily revenue per card type
- Visual variance indicators (should show $0.00 when balanced)
- GEAC balance section with inputs for PMS balance figures
- Autofill button for cash-out values (triggers `/api/rj/autofill-cashout`)
- Standard fill button for all other fields (triggers `/api/rj/fill/geac_ux`)

## 8. Known Issues & Gotchas

- **Column layout is irregular:** Card types do not occupy consecutive columns (B, E, G, J, K). This is because some card types span multiple columns in the Excel template (e.g., MASTER uses G:H).
- **Reset ranges are wider than mappings:** The reset clears adjacent cells (e.g., C column) that may contain helper formulas or labels. Ensure the reset runs before fill to avoid stale data.
- **Two API endpoints:** Cash-out has its own dedicated autofill endpoint separate from the general fill. Both must target the same sheet but write to different rows.
- **Row 10 and Row 53 are formulas:** Writing values to these cells will break the spreadsheet. The mapper includes them for reference but they should only be read, never written.
- **Variance must be zero:** A non-zero variance in Row 13/14 indicates a discrepancy between FreedomPay settlements and PMS daily revenue -- this is the primary audit check for this sheet.
