# geac_ux Sheet Documentation

**Sheet Name:** `geac_ux`
**Dimensions:** 58 rows x 11 columns
**Purpose:** GEAC/UX system balancing report for room charges

---

## Overview

The `geac_ux` sheet contains:
- GEAC (Galaxy/Property Management System) daily cash out reports
- Room charge credit card transactions
- Guest ledger balancing
- System validation between Daily Revenue and Guest Ledger

**GEAC** = The hotel's Property Management System (PMS) for room reservations and charges.

---

## Structure

### Header Section (Rows 1-5)

| Row | Content |
|-----|---------|
| 2 | HÔTEL SHERATON LAVAL |
| 4 | Card type headers: amex | diners | master | visa |
| 5 | Daily Cash Out |

### Daily Cash Out Section (Rows 6-12)

**Credit Card Totals from GEAC:**

| Row | Description | AMEX (B) | MASTER (G) | VISA (J) |
|-----|-------------|----------|------------|----------|
| 6 | Cash Out 1 | 5,714.14 | 7,394.15 | 6,473.46 |
| 8 | Cash Out 2 | | 3,200.90 | 1,152.39 |
| 10 | **Total** | **5,714.14** | **10,595.05** | **7,625.85** |
| 12 | Daily Revenue | 5,714.14 | 10,595.05 | 7,625.85 |

### GEAC/UX System Balance Report (Rows 25-58)

**Header:**
| Row | Content |
|-----|---------|
| 25 | GEAC/UX System Balance |
| 26 | HÔTEL SHERATON LAVAL |
| 28 | Daily Revenue | Guest Ledger | A/R Summary | Advance Deposit Summary |

### Balance Components

**Daily Revenue Section:**
| Row | Field | Value |
|-----|-------|-------|
| 30-32 | Balance Previous Day (p.7) | 3,268,484.66 |
| 34-37 | Balance today (p.7) | 16,923.33 |

**Guest Ledger Section:**
| Row | Field | Value |
|-----|-------|-------|
| 32 | Yesterday's ending balance | 3,268,484.66 |
| 37 | Debit Activities - Credit Activities | -16,923.33 |

**Transfers:**
| Row | Field | Value |
|-----|-------|-------|
| 39-41 | Facture Direct (p.6) | 6,574.37 |
| 41 | Front Office Transfer | 6,574.37 |
| 43-44 | Adv deposit applied (p.7) | 1,743.69 |

**New Balance:**
| Row | Field | Value |
|-----|-------|-------|
| 52-53 | New Balance (p.7) | 3,285,407.99 |
| 53 | ending balance | 3,285,407.99 |

### Footer

| Row | Content |
|-----|---------|
| 57 | Night Audit Date: [date] |
| 58 | Hotel Contact: Geneviève |

---

## Key Calculations

### Balance Check
```
New Balance = Previous Balance + Balance Today + Facture Direct + Adv Deposit
            = 3,268,484.66 + 16,923.33 + ... = 3,285,407.99
```

### Credit Card Validation
```
GEAC Credit Card Totals should match:
- transelect GEAC section (Rows 33-35)
- rj credit card section
```

---

## Connections

### To transelect Sheet

| geac_ux | transelect | Description |
|---------|------------|-------------|
| Row 10 AMEX | Row 35 AMEX ELAVON | 5,714.14 → 5,562.72 (net) |
| Row 10 MASTER | Row 35 MASTER | 10,595.05 |
| Row 10 VISA | Row 35 VISA | 7,625.85 |

### To rj Sheet

| geac_ux | rj Row | Description |
|---------|--------|-------------|
| Credit totals | 32-38 | Credit card section |
| Balance | 68 | Balance Fermeture |

---

## VBA Macros

### `geac_ux_report()` - Module28
```vba
Sub geac_ux_report()
    ' Navigate to geac_ux sheet
    Application.Goto Reference:=Range("home_geac_ux")
End Sub
```

### `efface_rapport_geac()` - Module26
```vba
Sub efface_rapport_geac()
    ' Clear GEAC report data
    Range("eff_geac").ClearContents
End Sub
```

### `recherche_auto_geac()` - Module19
```vba
Sub recherche_auto_geac()
    ' Automation for GEAC reports
    ' Auto-searches and fills GEAC data
End Sub
```

---

## Named Ranges

| Named Range | Purpose |
|-------------|---------|
| `home_geac_ux` | Navigation to geac_ux |
| `eff_geac` | Clear range for GEAC data |

---

## GEAC Balance Validation

**Critical Check:**
- Daily Revenue Balance = Guest Ledger Balance
- Row 32: 3,268,484.66 (both columns)
- Row 53: 3,285,407.99 (both columns)

If these don't match, there's a posting error in GEAC.

---

## Implementation Notes

### For WebApp:

1. **Data Source:**
   - Values come from GEAC printed reports
   - Night auditor enters values from paper reports

2. **Input Fields:**
   - Credit card totals by type
   - Balance figures from GEAC report pages

3. **Validation:**
   - Daily Revenue = Guest Ledger (must match)
   - Credit card totals match transelect GEAC section
   - New Balance = Previous + Changes

4. **Buttons/Actions:**
   - Navigate to GEAC
   - Clear GEAC data
   - Auto-search (recherche_auto_geac)

### Report Pages Referenced:
- **p.6**: Facture Direct (Direct billing)
- **p.7**: Daily Revenue and Balance

### Critical Validation:
The GEAC balance must reconcile or the night audit cannot close. Discrepancies require:
1. Review of posted transactions
2. Check for missing or duplicate entries
3. Verification against GEAC status report
