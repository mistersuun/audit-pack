# controle Sheet Documentation

**Sheet Name:** `controle`
**Dimensions:** 33 rows x 92 columns
**Purpose:** Configuration and control settings for the entire RJ workbook

---

## Overview

The `controle` sheet is the **master configuration sheet** that stores:
- Auditor name and date settings
- Hotel property information
- Annual statistics and comparisons
- Named ranges referenced by other sheets
- Monthly totals and validation values

---

## Structure

### Date & Auditor Configuration (Rows 2-5)

| Row | Column A | Column B | Column C | Purpose |
|-----|----------|----------|----------|---------|
| 2 | R.J. Préparée par | Khalil Mouatarif | | Auditor name |
| 3 | (jour label) | **23** | | Day of month |
| 4 | Mois (MM) | **12** | | Month number |
| 5 | Année (AAAA) | **2025** | | Year |

**Named Ranges:**
- `vjour` - Day value (Row 3, Col B) - Referenced by macros
- `idate` - Full date (Row 28, Col B) - Excel serial date

### Weather Information (Rows 6-7)

| Row | Column A | Column D/E |
|-----|----------|------------|
| 6 | Température | (weather data) |
| 7 | Condition | (weather description) |

### Annual Statistics (Rows 9-19)

| Row | Label | Value | Named Range |
|-----|-------|-------|-------------|
| 9 | # chambre à refaire | | `vchmp` |
| 10 | Vente dollar an a date | 23,912,245.37 | `vvad` |
| 11 | Vente dollar An dernier | 22,678,435.05 | `vvaad` |
| 12 | Ch. disponible an a date | 68,544 | `disp_ac` |
| 13 | Ch. disponible an passé | 68,544 | |
| 14 | Ch. Occuppees an a date | 56,170 | |
| 15 | Ch. Occuppees an passé | 58,179 | |
| 16 | Revenu Chambre an a date | 12,709,579.78 | |
| 17 | Revenu Chambre an passé | 12,876,792.91 | `revc_ad` |
| 18 | Balance de fermeture | | `v_balferm` |

### Hotel Property Info (Rows 20-21)

| Row | Label | Value | Named Range |
|-----|-------|-------|-------------|
| 20 | Propriété | HÔTEL SHERATON LAVAL | `vcie` |
| 21 | Nombre de chambre | 252 | `v_nbch` |

### DueBack Totals (Rows 21-26)

| Row | Column H | Value | Description |
|-----|----------|-------|-------------|
| 21 | Due Back mois a date | | Header |
| 22 | | **-22,745.81** | Monthly DueBack total (matches DUEBACK# B67) |
| 26 | due back du jour devrait être | **22,163.93** | Expected DueBack (matches DUEBACK# Z67) |

### Provisions & Settings (Rows 22-30)

| Row | Label | Named Range | Purpose |
|-----|-------|-------------|---------|
| 22 | Provision lingerie neuve | `t_mauv_c` | |
| 23 | Provision lingerie | `t_prov_l` | |
| 24 | Provision Vais,cout, | `t_prov_v` | |
| 25 | Provision verrerie | `t_prov_ver` | |
| 27 | # de jour dans le mois | `vjmois` | Days in month (31) |
| 28 | Date | `idate` | Excel date serial |
| 29 | Répartition pourb Banquet | `REP_BQT` | |
| 30 | Répartition pourb SAC | `REP_SAC` | |

---

## Key Named Ranges

| Named Range | Location | Purpose | Used By |
|-------------|----------|---------|---------|
| `vjour` | Row 3, Col B | Current day number | VBA macros, formulas |
| `vjmois` | Row 27, Col B | Days in month | Date calculations |
| `idate` | Row 28, Col B | Excel date serial | Sheet headers |
| `vcie` | Row 20, Col B | Hotel name | Report headers |
| `v_nbch` | Row 21, Col B | Number of rooms | Statistics |

---

## VBA Macros Related to controle

### `calcul_sal()` - Module3
```vba
Sub calcul_sal()
    ' Uses vjour named range to calculate salaries
    vjour = Range("vjour").Value
    ' ... calculates salary data based on day
End Sub
```

### Navigation Macros
- Many macros reference `vjour` to determine the current day column
- Date displays pull from `idate` named range

---

## Connections to Other Sheets

### From controle:
| controle Value | Destination | Purpose |
|----------------|-------------|---------|
| Row 3 (jour) | All sheets | Day column selection |
| Row 4 (mois) | Headers | Month display |
| Row 5 (année) | Headers | Year display |
| Row 20 (Propriété) | Report headers | Hotel name |
| Row 22 (DueBack MTD) | Validation | Cross-check with DUEBACK# B67 |

### To controle:
| Source | controle Location | Purpose |
|--------|-------------------|---------|
| DUEBACK# B67 | Row 22 (H) | Monthly DueBack total |
| DUEBACK# Z67 | Row 26 (H) | Expected DueBack |

---

## Data Validation

The controle sheet contains validation values that should match other sheets:

| controle Value | Should Match | Sheet |
|----------------|--------------|-------|
| Row 22 Col H (-22,745.81) | B67 | DUEBACK# |
| Row 26 Col H (22,163.93) | Z67 | DUEBACK# |

---

## Implementation Notes

### For WebApp:
1. **Date Settings** - Could be editable or auto-set from system date
2. **Auditor Name** - Should be pulled from logged-in user
3. **DueBack Totals** - Should auto-calculate and validate
4. **Statistics** - Read-only, pulled from annual data

### Important:
- The `vjour` value controls which day column is active throughout the workbook
- Changing the date here affects all day-dependent calculations
- The DueBack validation values should match DUEBACK# totals exactly
