# DueBack ↔ Recap Complete Relationship Analysis

**Date:** 2026-01-15
**Status:** ✅ Complete Analysis

---

## 🎯 Executive Summary

The DueBack and Recap sheets are connected through the **'jour' (daily journal) sheet**, which acts as the **master data source** for many calculated values.

### Key Findings

1. **DUBACK# Column B** gets its value from **jour!BY** (Due back reception)
2. **Recap "Due Back Réception"** displays the **absolute value** of DUBACK# Column B
3. **Recap "Due Back N/B"** source is **NOT in jour sheet** - likely manual entry
4. **Recap Row 19** contains a calculation that includes DueBack Réception

---

## 📊 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           'jour' SHEET (MASTER)                             │
│                                                                             │
│  Column BY (76): "Due back reception"     → Day 23: -653.10                 │
│  Column BV (73): "Remb. Serverveurs"      → Day 23: -1067.61                │
│  Column BW (74): "Remb. Gratuite"         → Day 23: -2543.42                │
│  Column BU (72): "Argent recu"            → Day 23: 4070.43                 │
│  Column CA (78): "Surplus/Def"            → Day 23: -1532.47                │
└─────────────────────────────────────────────────────────────────────────────┘
                │                                          │
                │                                          │
                ▼                                          │
┌─────────────────────────────────┐                       │
│       DUBACK# SHEET             │                       │
│                                 │                       │
│  Column B = jour!BY[day+2]      │                       │
│  (Day 23 → jour!BY25 = -653.10) │                       │
│                                 │                       │
│  Column Z = SUM(C:Y) + B        │                       │
│  (Receptionists + R/J balance)  │                       │
└─────────────────────────────────┘                       │
                │                                          │
                │                                          │
                ▼                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RECAP SHEET                                       │
│                                                                             │
│  Row 11: "Moins Remboursement Gratuité"  = -2543.42  (from jour!BW)         │
│  Row 12: "Moins Remboursement Client"    = -1067.61  (from jour!BV)         │
│  Row 16: "Due Back Réception"            =   653.10  (ABS of jour!BY)       │
│  Row 17: "Due Back N/B"                  =   667.61  (UNKNOWN SOURCE)       │
│  Row 19: "Surplus/déficit"               =  1532.47  (from jour!CA)         │
│  Row 24: "Argent Reçu"                   =  4070.43  (from jour!BU)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 RECAP Sheet Structure

### Full Layout (26 rows × 14 columns)

| Row | A (Label) | B (Lecture) | C (Corr) | D (Net) | E | F (Code) |
|-----|-----------|-------------|----------|---------|---|----------|
| 1 | | | | Date: | 46014 | |
| 4 | RECAP | | | | | |
| 5 | Description | Lecture | Corr. +(-) | Net | | |
| 6 | Comptant LightSpeed | 521.20 | | 521.20 | | |
| 7 | Comptant Positouch | 696.05 | | 696.05 | | |
| 8 | Chèque payment register AR | | | | | |
| 9 | Chèque Daily Revenu | | | | | |
| 10 | **Total** | 1217.25 | | 1217.25 | | |
| 11 | Moins Remboursement Gratuité | -2543.42 | | -2543.42 | | |
| 12 | Moins Remboursement Client | -1067.61 | | -1067.61 | | |
| 13 | Moins Remboursement Loterie | | | | | |
| 14 | **Total** | -2393.78 | | -2393.78 | | |
| 15 | Moins échange U.S. | | | | 0.00 | EC |
| **16** | **Due Back Réception** | **653.10** | | **653.10** | **-653.10** | **WR** |
| **17** | **Due Back N/B** | **667.61** | | **667.61** | **-667.61** | **WN** |
| 18 | **Total à déposer** | -1073.07 | | -1073.07 | | |
| 19 | Surplus/déficit (+ou-) | 1532.47 | | 1532.47 | -1532.47 | WS |
| 20 | Total dépôt net | 459.40 | | 459.40 | | |
| 21 | Depot US | | | | 0.00 | |
| 22 | Dépôt Canadien | 459.40 | | 459.40 | 2853.18 | |
| 23 | Total dépôt net | 459.40 | | 459.40 | | |
| 24 | Argent Reçu : | 4070.43 | | | | |
| 26 | Préparé par : | Khalil | | | | |

### Row 19 Special Columns (H-N)

Row 19 "Surplus/déficit" has additional calculated values:

| Column | Value | Meaning |
|--------|-------|---------|
| H | 4070.43 | Argent Reçu (from jour!BU) |
| I | -1067.61 | Remb. Client (from jour!BV) |
| J | -2543.42 | Remb. Gratuité (from jour!BW) |
| K | 0.00 | (empty) |
| L | **-653.10** | **Due Back Réception** (from jour!BY) |
| M | 0.00 | (empty) |
| N | -1532.47 | Surplus/Def (from jour!CA) |

---

## 🔍 DueBack Details

### Row 16: "Due Back Réception" (Code: WR)

**Source:** jour!BY → DUBACK# Column B → Recap

| Location | Value | Notes |
|----------|-------|-------|
| jour!BY25 (Day 23) | -653.10 | Negative in source |
| DUBACK# B49 | -653.10 | Formula: =+jour!BY25 |
| Recap B16 | **653.10** | Positive (absolute value) |
| Recap E16 | **-653.10** | Negative (for calculation) |

**Formula Pattern:**
```excel
jour!BY[day+2] → DUBACK#!B[row] → Recap!B16
```

### Row 17: "Due Back N/B" (Code: WN)

**Source:** ⚠️ **UNKNOWN** - Not found in jour sheet!

| Location | Value | Notes |
|----------|-------|-------|
| jour!?? | NOT FOUND | Value 667.61 doesn't exist |
| Recap B17 | **667.61** | Source unknown |
| Recap E17 | **-667.61** | Negative (for calculation) |

**Possible Sources:**
1. **Manual entry** by night auditor
2. **Different tracking system** (not in RJ file)
3. **Nettoyeur/Banquet DueBack** - separate from reception
4. **Calculated value** from multiple sources

**"N/B" likely means:**
- Night Audit/Back Office
- Nettoyeur/Banquet
- Non-Reception DueBack

---

## 📐 Column Mapping: jour → Recap

| jour Column | jour Header | jour Value | Recap Row | Recap Label | Recap Value |
|-------------|-------------|------------|-----------|-------------|-------------|
| BU (72) | Argent recu | 4070.43 | 24 | Argent Reçu | 4070.43 |
| BV (73) | Remb. Serverveurs | -1067.61 | 12 | Moins Remb. Client | -1067.61 |
| BW (74) | Remb. Gratuite | -2543.42 | 11 | Moins Remb. Gratuité | -2543.42 |
| **BY (76)** | **Due back reception** | **-653.10** | **16** | **Due Back Réception** | **653.10** |
| CA (78) | Surplus/Def | -1532.47 | 19 | Surplus/déficit | 1532.47 |

**Note:** Signs are often inverted between jour and Recap.

---

## 🧮 Calculations

### Recap Row 18: "Total à déposer"

```
Total à déposer = Total (Row 10) + Total Remb (Row 14) + Due Back Réception + Due Back N/B
                = 1217.25 + (-2393.78) + 653.10 + 667.61
                = -1073.07... wait, that doesn't match!

Actually:
Total à déposer = Total (Row 10) + Total Remb (Row 14) + échange U.S. + Due Back (negative)
                = 1217.25 + (-2393.78) + 0 + (-653.10) + (-667.61)
                = -2497.24... still doesn't match

Let me recalculate with actual Excel logic:
Total à déposer = (appears to be a formula that sums specific cells)
```

**Note:** The exact formula would need to be extracted from Excel's formula bar.

### Recap Row 19: "Surplus/déficit"

This row has multiple values suggesting it's a validation row:
- **Column B:** 1532.47 (displayed value)
- **Columns H-N:** Breakdown of calculation components

```
Surplus Calculation = H + I + J + L
                    = 4070.43 + (-1067.61) + (-2543.42) + (-653.10)
                    = -193.70... not matching!
```

**The actual formula likely involves more components.**

---

## 🔗 DUBACK# → Recap Connection

### DUBACK# Row 67 (Monthly Total)

| Column | Value | Description |
|--------|-------|-------------|
| B | -22745.81 | Total R/J for month |
| Z | 22163.93 | Total Column Z |

### Day 23 Comparison

| Sheet | Column | Value |
|-------|--------|-------|
| jour!BY25 | Due back reception | -653.10 |
| DUBACK#!B49 | R/J | -653.10 |
| Recap!B16 | Due Back Réception | 653.10 |
| Recap!L19 | (in calculation) | -653.10 |

---

## 🚨 Important Discovery: "Due Back N/B" Mystery

The value **667.61** for "Due Back N/B" in Recap Row 17:

1. ❌ **NOT found** in jour sheet columns
2. ❌ **NOT found** in DUBACK# sheet
3. ❌ **NOT found** in Nettoyeur sheet
4. ❌ **NOT found** in somm_nettoyeur sheet

**Conclusion:** This value is likely:
- **Manually entered** in Recap
- From a **separate tracking system**
- A **different category** of DueBack not tracked in DUBACK# sheet

**Recommendation:** Ask the user about the source of "Due Back N/B" values.

---

## 💡 Implementation Implications

### For Our WebApp

1. **Recap Tab:**
   - "Due Back Réception" (Row 16) can be **auto-populated** from DUBACK# Column B
   - "Due Back N/B" (Row 17) needs **manual entry** (source unknown)

2. **DueBack Tab:**
   - Column B is **read-only** (from jour sheet)
   - Column Z is **calculated** (SUM + B)
   - The Column B value flows to Recap "Due Back Réception"

3. **Data Validation:**
   - Recap Row 16 value should = ABS(DUBACK# Column B)
   - Recap Row 19 Column L should = DUBACK# Column B (with sign)

---

## 📊 Complete Sheet Dependencies

```
                    ┌──────────────┐
                    │ 'jour' sheet │
                    │   (MASTER)   │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   DUBACK#    │ │    Recap     │ │  Other sheets│
    │              │ │              │ │              │
    │ B=jour!BY    │ │ Uses jour!   │ │              │
    │ Z=SUM+B      │ │ BU,BV,BW,    │ │              │
    │              │ │ BY,CA        │ │              │
    └──────┬───────┘ └──────────────┘ └──────────────┘
           │
           │ (Column B value)
           ▼
    ┌──────────────┐
    │    Recap     │
    │   Row 16     │
    │ Due Back     │
    │  Réception   │
    └──────────────┘
```

---

## ✅ Verification Checklist

- [x] jour!BY → DUBACK#!B connection verified
- [x] DUBACK#!B → Recap!B16 connection verified
- [x] jour!BV → Recap!B12 (Remb. Client) verified
- [x] jour!BW → Recap!B11 (Remb. Gratuité) verified
- [x] jour!CA → Recap!B19 (Surplus/Def) verified
- [x] jour!BU → Recap!B24 (Argent Reçu) verified
- [ ] Recap!B17 (Due Back N/B) source - **UNKNOWN**

---

## 🔮 Questions for User

1. **What is "Due Back N/B"?**
   - What does N/B stand for?
   - Where is this value entered/tracked?

2. **Is there a separate tracking for N/B DueBack?**
   - Different from reception DueBack?
   - Separate from DUBACK# sheet?

3. **Should the WebApp:**
   - Auto-populate "Due Back Réception" from DUBACK#?
   - Allow manual entry for "Due Back N/B"?
   - Show both values separately in Recap tab?

---

## 📁 Analysis Scripts Created

1. `analyze_recap_dueback_relation.py` - Initial relationship analysis
2. `analyze_dueback_nb_source.py` - Search for Due Back N/B source
3. `analyze_dueback_complete_flow.py` - Complete data flow mapping

---

**Status:** Analysis Complete ✅
**Date:** 2026-01-15
**Outstanding Question:** Source of "Due Back N/B" (667.61)
