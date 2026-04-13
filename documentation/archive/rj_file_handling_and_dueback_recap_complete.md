# RJ File Handling & DueBack ↔ Recap Complete Documentation

**Date:** 2026-01-15
**Status:** Complete

---

## Part 1: RJ File Handling Behavior

### Current Application Behavior

**Question:** "When I put a RJ it copies it and changes the name and date without overwriting the current one?"

**Answer:** Yes, that is correct. Here's how it works:

1. **Upload** (`/api/rj/upload`):
   - The RJ file is loaded into **memory only** (BytesIO)
   - Stored in session dictionary `RJ_FILES[session_id]`
   - **Original file on disk is NOT modified**

2. **Modifications** (all API calls):
   - All changes (DueBack entries, Recap values, etc.) are made **in memory**
   - Each save operation updates the in-memory BytesIO buffer
   - **Original file remains untouched**

3. **Download** (`/api/rj/download`):
   - Generates a **new filename**: `RJ_{YYYY-MM-DD}_filled.xls`
   - Example: `RJ_2026-01-15_filled.xls`
   - User downloads a **new copy** with today's date
   - **Does NOT overwrite** the original uploaded file

### Why This Design?

This is standard web application behavior:
- **Safety**: Original file is never modified accidentally
- **Audit trail**: Each download is a new dated copy
- **Reversibility**: User can always re-upload the original if needed
- **Multi-session**: Different sessions can work on different files

### Code References

```python
# routes/rj.py

# Upload - stores in memory
@rj_bp.route('/api/rj/upload', methods=['POST'])
def upload_rj():
    file_bytes = io.BytesIO(file.read())
    RJ_FILES[session_id] = file_bytes  # Memory only

# Download - new filename with date
@rj_bp.route('/api/rj/download', methods=['GET'])
def download_rj():
    filename = f'RJ_{today.strftime("%Y-%m-%d")}_filled.xls'
    return send_file(file_bytes, download_name=filename)
```

---

## Part 2: DueBack ↔ Recap Complete Relationship

### Data Flow Diagram

```
                    ┌──────────────────────────────────────────┐
                    │          'jour' SHEET (MASTER)           │
                    │                                          │
                    │  BY (76): Due back reception → -653.10   │
                    │  BV (73): Remb. Serverveurs  → -1067.61  │
                    │  BW (74): Remb. Gratuite     → -2543.42  │
                    │  BU (72): Argent recu        → 4070.43   │
                    │  CA (78): Surplus/Def        → -1532.47  │
                    └────────────────┬─────────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           │                         │                         │
           ▼                         ▼                         ▼
┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
│    DUBACK# SHEET   │   │    RECAP SHEET     │   │  controle SHEET    │
│                    │   │                    │   │                    │
│ B = jour!BY[day+2] │   │ Row 11: jour!BW    │   │ Row 3: jour=23     │
│ Z = SUM(C:Y)+B     │   │ Row 12: jour!BV    │   │ Row 4: mois=12     │
│                    │   │ Row 16: ABS(jour!BY)│   │ Row 5: année=2025  │
│ Day23 B49=-653.10  │   │ Row 17: N/B (PDF)  │   │ Row 22: DueBack MTD│
│ Monthly B67=-22746 │   │ Row 19: jour!CA    │   │ Row 26: DueBack Exp│
└────────────────────┘   │ Row 24: jour!BU    │   └────────────────────┘
           │             └────────────────────┘
           │                       │
           └───────────────────────┘
                    │
                    ▼
          ┌────────────────────────────────────────┐
          │  RECAP Row 16: "Due Back Réception"    │
          │  Value = ABS(DUBACK# Column B)         │
          │  653.10 (positive in display)          │
          └────────────────────────────────────────┘
```

### Key Connections

| Source | Destination | Value (Day 23) | Notes |
|--------|-------------|----------------|-------|
| jour!BY25 | DUBACK#!B49 | -653.10 | Formula: `=+jour!BY25` |
| DUBACK#!B49 | Recap!B16 | 653.10 | ABS value for display |
| jour!BV25 | Recap!B12 | -1067.61 | "Moins Remb. Client" |
| jour!BW25 | Recap!B11 | -2543.42 | "Moins Remb. Gratuité" |
| jour!BU25 | Recap!B24 | 4070.43 | "Argent Reçu" |
| jour!CA25 | Recap!B19 | 1532.47 | "Surplus/déficit" (sign inverted) |

### DUBACK# Column Z Formula

**Correct Formula:**
```excel
=SUM(C45:Y46)+B45
```

**Breakdown:**
- `C45:Y46` = Sum of **both rows** (Previous + Current) for all receptionists
- `B45` = Column B value from **previous row** (R/J reference from jour sheet)

**JavaScript Implementation:**
```javascript
// Column Z = SUM(C:Y for both rows) + Column B (previous)
function updateColumnZ() {
  let totalPrevious = 0;
  let totalCurrent = 0;

  duebackEntries.forEach(entry => {
    totalPrevious += -Math.abs(entry.previous);  // Negative
    totalCurrent += entry.current;                // Positive
  });

  // Formula: =SUM(C45:Y46)+B45
  const columnZNet = totalPrevious + totalCurrent + columnBPrevious;
}
```

### RECAP Sheet Structure (Rows 10-20)

| Row | Label | Column B | Column E | Code |
|-----|-------|----------|----------|------|
| 10 | Total | 1217.25 | 1217.25 | |
| 11 | Moins Remb. Gratuité | -2543.42 | -2543.42 | |
| 12 | Moins Remb. Client | -1067.61 | -1067.61 | |
| 14 | Total | -2393.78 | -2393.78 | |
| 15 | Moins échange U.S. | | | EC |
| **16** | **Due Back Réception** | **653.10** | **653.10** | **WR** |
| **17** | **Due Back N/B** | **667.61** | **667.61** | **WN** |
| 18 | Total à déposer | -1073.07 | -1073.07 | |
| 19 | Surplus/déficit | 1532.47 | 1532.47 | WS |
| 20 | Total dépôt net | 459.40 | 459.40 | |

### Recap Row 19 Hidden Columns (H-N)

These columns contain the calculation breakdown:

| Column | Value | Source |
|--------|-------|--------|
| H | 4070.43 | jour!BU (Argent Reçu) |
| I | -1067.61 | jour!BV (Remb. Client) |
| J | -2543.42 | jour!BW (Remb. Gratuité) |
| K | 0.00 | (empty) |
| **L** | **-653.10** | **jour!BY (Due Back Réception)** |
| M | 0.00 | (empty) |
| N | -1532.47 | jour!CA (Surplus/Def) |

---

## Part 3: "Due Back N/B" Mystery Resolved

**Question:** Where does "Due Back N/B" (667.61) come from?

**Answer:** User confirmed: **"Due Back N/B comes from a PDF"**

- **NOT** from Excel sheets
- **Manual entry** in Recap Row 17
- **N/B** likely means "Nettoyeur/Banquet" or "Night Balance"
- Separate tracking system, not in RJ file

### Implementation

In the webapp:
- "Due Back Réception" (Row 16): **Auto-populated** from DUBACK# Column B
- "Due Back N/B" (Row 17): **Manual entry** field (user reads from PDF)

---

## Part 4: controle Sheet Configuration

The `controle` sheet stores date and audit settings:

| Row | Content | Example Value |
|-----|---------|---------------|
| 2 | R.J. Préparée par | Khalil Mouatarif |
| 3 | jour (day) | 23 |
| 4 | mois (month) | 12 |
| 5 | année (year) | 2025 |
| 22 | Due Back mois a date | -22745.81 |
| 26 | due back du jour devrait être | 22163.93 |

**Key Validation:**
- Row 22 value (-22745.81) = DUBACK# B67 (monthly total)
- Row 26 value (22163.93) = DUBACK# Z67 (expected total)

---

## Part 5: SD File G39 → Recap Connection

**SD File Structure:**
- Contains daily Sommaire Journalier data
- Row 39 contains TOTALS for each day

**SD G39 Value:** 643.99 (variance total)

**Row 39 breakdown:**
| Column | Value |
|--------|-------|
| D | -462.51 |
| E | 497.80 |
| F | 316.32 |
| **G** | **643.99** (variance) |

**Connection:** SD!G39 variance → Recap (specific cell TBD)

---

## Part 6: VBA Macros Summary

Key macros in RJ file:

| Macro | Function |
|-------|----------|
| `Imp_RJ()` | Print RJ sheet |
| `efface_recap()` | Clear Recap sheet |
| `envoie_dans_jour()` | Copy Recap H19:N19 → jour sheet |
| `calcul_carte()` | Calculate credit cards to jour |
| `eff_depot()` | Clear deposit sheet |
| `eff_trans()` | Clear transelect |
| `calcul_sal()` | Calculate salaries |

**Important:** `envoie_dans_jour()` copies Recap Row 19 columns H-N to the jour sheet for the current day. This is equivalent to our `/api/rj/recap/send-to-jour` endpoint.

---

## Part 7: Implementation Checklist

### Currently Implemented
- [x] RJ file upload/download (with new filename)
- [x] DueBack entries (C-Y columns)
- [x] DueBack Column B display (read-only from jour)
- [x] DueBack Column Z calculation (SUM(C:Y)+B)
- [x] DueBack live Excel preview
- [x] Recap → jour copy (`/api/rj/recap/send-to-jour`)
- [x] SD file upload/read

### Needs Implementation
- [ ] "Due Back N/B" manual entry field in Recap
- [ ] SD G39 variance → Recap connection
- [ ] Recap auto-fill from jour sheet values
- [ ] controle sheet day/month/year update

---

## Part 8: File Storage Summary

| File Type | Storage | Persistence |
|-----------|---------|-------------|
| RJ Upload | Memory (BytesIO) | Session only |
| RJ Download | New file | User's computer |
| SD Upload | Memory (BytesIO) | Session only |
| SD Download | New file | User's computer |

**Note:** All modifications happen in memory. Original files are never modified.
