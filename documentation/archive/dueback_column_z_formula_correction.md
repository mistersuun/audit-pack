# DueBack Column Z Formula Correction

**Date:** 2026-01-02
**Status:** ✅ Fixed

---

## 🔴 Correction

### Initial Understanding (INCORRECT)
```excel
Column Z = SUM(C:Y)
```
Sum of receptionist columns only.

### Actual Formula (CORRECT)
```excel
Column Z = SUM(C45:Y46)+B45
```

**For Day N:**
```excel
=SUM(C[balance_row]:Y[operations_row])+B[balance_row]
```

---

## 📊 What This Means

### Column Z Calculation

**Components:**
1. **SUM(C45:Y46)**: Sum of all 23 receptionist columns for BOTH rows
   - Row 45 (balance_row): Previous DueBack values
   - Row 46 (operations_row): Current DueBack values

2. **+B45**: Add Column B (previous row)
   - Column B contains reference to jour sheet: `=+jour!BY[row]`
   - This is the R/J balance

**Total Formula:**
```
Column Z = (Receptionist Previous + Receptionist Current) + Column B Previous
```

---

## 💻 Implementation Fix

### JavaScript Changes (`templates/rj.html`)

#### Before (Incorrect)
```javascript
const totalNet = totalPrevious + totalCurrent;
document.getElementById('dueback-total-net').textContent = formatCurrency(totalNet);
```

#### After (Correct)
```javascript
// Column Z formula: =SUM(C45:Y46)+B45
const columnZNet = totalPrevious + totalCurrent + columnBPrevious;
document.getElementById('dueback-total-net').textContent = formatCurrency(columnZNet);
```

### New Global Variable
```javascript
let columnBPrevious = 0;  // Stores Column B previous value for Column Z calculation
```

### Updated Flow
```
1. fetchDuebackColumnB()
   ↓
2. Store columnBPrevious
   ↓
3. updateColumnZ()
   ↓
4. Calculate: columnZNet = totalPrevious + totalCurrent + columnBPrevious
```

---

## 🎯 Example Calculation

### Day 23 (rows 49-50)

**Given:**
- Column B (from jour!BY25): **-$653.10**
- Receptionist Previous (sum of C49:Y49): **-$350.00**
- Receptionist Current (sum of C50:Y50): **$375.00**

**Calculation:**
```
Column Z Net = SUM(C49:Y50) + B49
             = (Previous + Current) + Column B
             = (-$350.00 + $375.00) + (-$653.10)
             = $25.00 + (-$653.10)
             = -$628.10
```

**Display:**
- **Column B:**
  - Previous: -$653.10
  - Current: $0.00
  - Net: -$653.10

- **Column Z:**
  - Previous: -$350.00 (receptionists only)
  - Current: $375.00 (receptionists only)
  - Net: **-$628.10** (includes Column B)

---

## 🔧 Files Modified

1. **`templates/rj.html`**
   - Added `columnBPrevious` global variable
   - Modified `fetchDuebackColumnB()` to store and trigger update
   - Created `updateColumnZ()` function with correct formula
   - Simplified `calculateDuebackTotals()` to orchestrate updates

2. **`documentation/dueback_column_b_vs_z_analysis.md`**
   - Updated Column Z formula documentation
   - Added breakdown of formula components

---

## ✅ Verification

### Formula Pattern
```
For any day N with balance_row R and operations_row R+1:

Column Z = SUM(C[R]:Y[R+1]) + B[R]
```

**Example mapping:**
| Day | Balance Row | Operations Row | Column Z Formula |
|-----|-------------|----------------|------------------|
| 1   | 5           | 6              | =SUM(C5:Y6)+B5   |
| 23  | 49          | 50             | =SUM(C49:Y50)+B49|

---

## 🎨 UI Impact

### What User Sees

**Column B (Read-Only):**
- Shows R/J balance from jour sheet
- Lock icon indicates read-only
- Values fetched from RJ file

**Column Z (Calculated):**
- Shows total including R/J balance
- Calculator icon indicates calculation
- **Now correctly includes Column B in the net total**

### Visual Relationship

```
┌──────────────────────────────────┐
│ Column B (R/J from jour sheet)   │
│ Previous: -$653.10 🔒            │
│ Current:  $0.00                  │
│ Net:      -$653.10               │
└──────────────────────────────────┘
              │
              │ (added to Column Z net)
              ↓
┌──────────────────────────────────┐
│ Column Z (Receptionists + B)     │
│ Previous: -$350.00 🧮            │
│ Current:  $375.00                │
│ Net:      -$628.10               │
│           (includes B: -$653.10) │
└──────────────────────────────────┘
```

---

## 📝 Key Takeaways

1. **Column Z is NOT just receptionists** - it includes Column B
2. **Column B appears twice** in the calculation:
   - Once in its own display (read-only from jour sheet)
   - Once added to Column Z net
3. **Formula is consistent** across all days: `=SUM(C:Y for 2 rows) + B`
4. **This makes sense** - Column Z shows the complete DueBack picture including R/J

---

**Correction Applied:** 2026-01-02
**Status:** ✅ Complete
**Testing:** Ready for validation
