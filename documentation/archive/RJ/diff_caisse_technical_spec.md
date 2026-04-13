# Diff.Caisse Column Decomposition - Technical Specification

## 1. Current State (Excel RJ Workbook)

### Sheet: "Diff.Caisse#" (Index 4)

**Purpose**: Track individual adjustment entries that decompose the monthly cash discrepancy (Diff.Caisse from Jour sheet)

**Dimensions**: 33 rows × 39 columns
- Rows: Day 1-25, plus header and summary rows
- Columns: A-AM (Jour, Total, Adjustments 1-36, Remaining)

### Column Structure

| Excel Col | Index | Field Name | Type | Purpose |
|-----------|-------|------------|------|---------|
| A | 0 | Jour | Number | Day number (1-25) |
| B | 1 | [unlabeled] | Currency | Total Diff.Caisse for this day |
| C | 2 | geac ux | Currency | Adjustment slot 1 |
| D | 3 | geac ux | Currency | Adjustment slot 2 |
| E | 4 | geac ux | Currency | Adjustment slot 3 |
| ... | ... | geac ux | Currency | ... |
| AL | 37 | geac ux | Currency | Adjustment slot 36 |
| AM | 38 | [unlabeled] | Currency | Remaining (unallocated) balance |

**Key Notes:**
- Column B value links to Jour sheet Column C (Diff.Caisse calculation)
- Columns C-AL represent 36 adjustment slots (generic "geac ux" labels)
- Column AM automatically calculates: `AM = B - SUM(C:AL)`
- Currently, all adjustment slots (C-AL) are **EMPTY** on every day

### Example: Day 24 (Row 25)

```
A25: 24.0
B25: 385.56          ← Total from Jour!C25
C25:0 (empty)
D25:0 (empty)
...
AL25: 0 (empty)
AM25: 385.56         ← Remaining = 385.56 - SUM(0 values) = 385.56
```

### Current Month Status

| Metric | Value |
|--------|-------|
| Days analyzed | 25 |
| Days with non-zero Diff.Caisse | 23 (92%) |
| Days with allocations entered | 0 (0%) |
| Total unallocated variance | ±$854,837.54 |
| Largest variance | Day 25: +$866,165.21 |

---

## 2. Integration with Jour Sheet

The Jour sheet (Index 9) calculates Diff.Caisse in Column C:

```
Jour!C24 = 385.56
          ↓
Diff.Caisse#!B25 = 385.56  (linked or copied)
```

**Calculation Method** (reverse-engineered from Excel):
- Jour totals are computed from F&B revenue, room revenue, deposits, and card reconciliation
- Diff.Caisse = Actual cash position - Expected cash position
- Positive value = cash overage
- Negative value = cash shortage

---

## 3. Data Model for RJ Natif

### NightAuditSession (database/models.py)

Add the following fields:

```python
# Option A: JSON array (flexible, allows rich metadata)
diff_caisse_adjustments = db.Column(db.Text)  # JSON: [{slot, reason, amount, timestamp}, ...]
diff_caisse_total = db.Column(db.Float)       # Denormalized from jour calculations
diff_caisse_remaining = db.Column(db.Float)   # Calculated: total - SUM(adjustments)

# Option B: 36 scalar columns (simple, Excel-like)
diff_caisse_adj_01 through diff_caisse_adj_36 = db.Column(db.Float)
diff_caisse_total = db.Column(db.Float)
diff_caisse_remaining = db.Column(db.Float)
```

**Recommendation**: Use Option A (JSON array) because:
- Allows descriptive reasons for each adjustment
- Scalable if audit requirements change
- Easier to maintain history
- Maps directly to Excel "adjustment entry" concept

**JSON Schema**:
```json
{
  "adjustments": [
    {
      "slot": 1,
      "reason": "Rounding error in Transelect reconciliation",
      "amount": 150.00,
      "timestamp": "2026-02-27T14:32:15Z"
    },
    {
      "slot": 2,
      "reason": "Customer refund reversal (not applied)",
      "amount": 235.56,
      "timestamp": "2026-02-27T14:35:22Z"
    }
  ],
  "remaining": 0.00,
  "last_updated": "2026-02-27T14:35:22Z"
}
```

---

## 4. Frontend Architecture (rj_native.html)

### New Tab: "Diff.Caisse" (Tab 10, between Jour and Quasimodo)

**Key Components:**

1. **Header Section**
   ```html
   <div class="diff-caisse-header">
     <h3>Différence de Caisse</h3>
     <div class="total-display">
       <span class="label">Total Diff.Caisse:</span>
       <span class="amount" id="diffCaisseTotal">$385.56</span>
     </div>
     <div class="remaining-display">
       <span class="label">Remaining (Unallocated):</span>
       <span class="amount" id="diffCaisseRemaining">$385.56</span>
     </div>
   </div>
   ```

2. **Adjustment Entry Form**
   ```html
   <form id="diffCaisseForm">
     <input type="text" id="adjReason" placeholder="Reason for adjustment">
     <input type="number" id="adjAmount" placeholder="Amount" step="0.01">
     <select id="adjSlot">
       <option value="">Select slot (1-36)</option>
       <option value="1">Slot 1</option>
       ...
       <option value="36">Slot 36</option>
     </select>
     <button type="button" onclick="addAdjustment()">Add Entry</button>
   </form>
   ```

3. **Entries Table**
   ```html
   <table id="diffCaisseTable">
     <thead>
       <tr>
         <th>Slot</th><th>Reason</th><th>Amount</th><th>Actions</th>
       </tr>
     </thead>
     <tbody id="diffCaisseEntries"></tbody>
     <tfoot>
       <tr>
         <td colspan="2"><strong>Total Allocated:</strong></td>
         <td id="totalAllocated">$0.00</td>
       </tr>
       <tr>
         <td colspan="2"><strong>Remaining:</strong></td>
         <td id="displayRemaining">$385.56</td>
       </tr>
     </tfoot>
   </table>
   ```

---

## 5. JavaScript Functions (rj_native.html)

### Core Functions

```javascript
// Load adjustments from session into form
function loadDiffCaisse(session) {
  const dc = session.diff_caisse_adjustments || { adjustments: [], remaining: 0 };
  
  // Display total
  document.getElementById('diffCaisseTotal').textContent = 
    fmt(session.jour_total || 0);  // From Jour tab
  
  // Populate entries table
  dc.adjustments.forEach((adj, idx) => {
    addAdjustmentRow(adj, idx);
  });
  
  // Update remaining
  updateDiffCaisseRemaining();
}

// Add new adjustment entry
function addAdjustment() {
  const reason = document.getElementById('adjReason').value.trim();
  const amount = parseFloat(document.getElementById('adjAmount').value) || 0;
  const slot = parseInt(document.getElementById('adjSlot').value) || 0;
  
  if (!reason || !amount || !slot) {
    alert('Please fill all fields');
    return;
  }
  
  if (slot < 1 || slot > 36) {
    alert('Slot must be 1-36');
    return;
  }
  
  // Add to DOM table
  addAdjustmentRow({ slot, reason, amount }, document.querySelectorAll('#diffCaisseEntries tr').length);
  
  // Clear form
  document.getElementById('adjReason').value = '';
  document.getElementById('adjAmount').value = '';
  document.getElementById('adjSlot').value = '';
  
  // Recalculate
  updateDiffCaisseRemaining();
  
  // Auto-save
  debounceSave('diff_caisse');
}

// Remove adjustment entry
function removeAdjustment(idx) {
  document.querySelector(`#diffCaisseEntries tr[data-index="${idx}"]`).remove();
  updateDiffCaisseRemaining();
  debounceSave('diff_caisse');
}

// Add row to entries table
function addAdjustmentRow(adj, idx) {
  const row = document.createElement('tr');
  row.setAttribute('data-index', idx);
  row.innerHTML = `
    <td>${adj.slot}</td>
    <td>${adj.reason}</td>
    <td>${fmt(adj.amount)}</td>
    <td><button type="button" onclick="removeAdjustment(${idx})">Delete</button></td>
  `;
  document.getElementById('diffCaisseEntries').appendChild(row);
}

// Recalculate remaining balance
function updateDiffCaisseRemaining() {
  const total = parseFloat(
    document.getElementById('diffCaisseTotal').textContent.replace(/[\$,]/g, '')
  ) || 0;
  
  const allocated = Array.from(document.querySelectorAll('#diffCaisseEntries tr'))
    .reduce((sum, row) => sum + parseFloat(row.cells[2].textContent.replace(/[\$,]/g, '')) || 0, 0);
  
  const remaining = total - allocated;
  
  document.getElementById('diffCaisseRemaining').textContent = fmt(remaining);
  document.getElementById('totalAllocated').textContent = fmt(allocated);
  document.getElementById('displayRemaining').textContent = fmt(remaining);
  
  // Visual warning if not balanced
  if (Math.abs(remaining) > 0.01) {
    document.getElementById('diffCaisseRemaining').classList.add('warning');
  } else {
    document.getElementById('diffCaisseRemaining').classList.remove('warning');
  }
}

// Serialize adjustments for API
function getDiffCaisseData() {
  const adjustments = Array.from(document.querySelectorAll('#diffCaisseEntries tr'))
    .map((row, idx) => ({
      slot: parseInt(row.cells[0].textContent),
      reason: row.cells[1].textContent,
      amount: parseFloat(row.cells[2].textContent.replace(/[\$,]/g, '')),
      timestamp: new Date().toISOString()
    }));
  
  const total = parseFloat(
    document.getElementById('diffCaisseTotal').textContent.replace(/[\$,]/g, '')
  ) || 0;
  
  const allocated = adjustments.reduce((sum, a) => sum + a.amount, 0);
  
  return {
    adjustments,
    total,
    remaining: total - allocated
  };
}
```

---

## 6. API Endpoints (routes/audit/rj_native.py)

### Save Endpoint

```python
@rj_native.route('/save/diff_caisse', methods=['POST'])
def save_diff_caisse():
    """
    Save Diff.Caisse adjustment entries.
    
    Request JSON:
    {
      "date": "2026-02-24",
      "adjustments": [
        {"slot": 1, "reason": "...", "amount": 150.00},
        {"slot": 2, "reason": "...", "amount": 235.56}
      ],
      "total": 385.56,
      "remaining": 0.00
    }
    """
    data = request.get_json()
    date_str = data.get('date')
    adjustments_data = data.get('adjustments', [])
    total = data.get('total', 0)
    remaining = data.get('remaining', 0)
    
    session = NightAuditSession.query.filter_by(audit_date=date_str).first()
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Validate: sum of allocations + remaining = total
    allocated_sum = sum(adj['amount'] for adj in adjustments_data)
    expected_remaining = total - allocated_sum
    
    if abs(expected_remaining - remaining) > 0.01:
        return jsonify({
            'error': 'Calculation mismatch',
            'expected_remaining': expected_remaining,
            'provided_remaining': remaining
        }), 400
    
    # Store adjustments
    import json
    session.diff_caisse_adjustments = json.dumps({
        'adjustments': adjustments_data,
        'total': total,
        'remaining': remaining,
        'last_updated': datetime.utcnow().isoformat()
    })
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'remaining': remaining,
        'allocated': allocated_sum
    })
```

### Validation in Calculate Endpoint

```python
def validate_diff_caisse(session):
    """
    Validate Diff.Caisse decomposition.
    Returns list of validation messages.
    """
    import json
    
    warnings = []
    
    if not session.diff_caisse_adjustments:
        warnings.append('Diff.Caisse: No adjustments entered')
        return warnings
    
    dc_data = json.loads(session.diff_caisse_adjustments)
    remaining = dc_data.get('remaining', 0)
    
    if abs(remaining) > 0.01:
        warnings.append(
            f'Diff.Caisse: Unresolved balance of ${remaining:.2f} remains. '
            f'Adjustments: {", ".join(a["reason"] for a in dc_data["adjustments"])}'
        )
    else:
        warnings.append('Diff.Caisse: Fully decomposed and balanced')
    
    return warnings
```

---

## 7. Validation Rules

### In-Form Validation
- Slot: 1-36 (unique per session or allow multiples?)
- Amount: positive or negative decimal
- Reason: non-empty text (50-200 chars recommended)
- Total allocated + remaining must equal Diff.Caisse total

### Server-Side Validation
- Date must exist in NightAuditSession
- Diff.Caisse value from Jour tab must be present
- Sum check: allocated + remaining = total ± $0.01 tolerance
- No duplicate slot allocations (optional business rule)

### Submission Validation
- Flag warning if remaining ≠ 0
- Allow submission anyway (auditor may acknowledge)
- Store warning in session.validation_notes

---

## 8. Storage Strategy

### Option 1: JSON Column (Recommended)
```python
# Single column stores complete decomposition
diff_caisse_adjustments: str (JSON)

Schema:
{
  "adjustments": [
    {"slot": int, "reason": str, "amount": float, "timestamp": ISO8601},
    ...
  ],
  "total": float,
  "remaining": float,
  "last_updated": ISO8601
}
```

### Option 2: Scalar Columns
```python
# 36 individual columns + 3 meta columns
diff_caisse_adj_01 through diff_caisse_adj_36: float
diff_caisse_total: float
diff_caisse_remaining: float
diff_caisse_reasons: text (CSV or JSON list)
```

**Recommendation**: Use Option 1 for flexibility and maintainability.

---

## 9. Excel Export

When exporting completed RJ session to Excel, include Diff.Caisse# data:

```python
def export_diff_caisse_to_excel(session, worksheet):
    """
    Write Diff.Caisse decomposition to Excel worksheet.
    """
    import json
    
    dc_data = json.loads(session.diff_caisse_adjustments or '{}')
    adjustments = dc_data.get('adjustments', [])
    
    # Row 0: Headers
    worksheet['A1'] = 'Slot'
    worksheet['B1'] = 'Reason'
    worksheet['C1'] = 'Amount'
    
    # Rows 1+: Adjustments
    for idx, adj in enumerate(adjustments):
        worksheet[f'A{idx+2}'] = adj['slot']
        worksheet[f'B{idx+2}'] = adj['reason']
        worksheet[f'C{idx+2}'] = adj['amount']
    
    # Summary row
    row = len(adjustments) + 3
    worksheet[f'A{row}'] = 'TOTAL'
    worksheet[f'B{row}'] = 'Remaining'
    worksheet[f'C{row}'] = dc_data.get('remaining', 0)
```

---

## 10. Testing Scenarios

### Test Case 1: Add Two Adjustments
- Input: Total = $385.56, Adj1 = $150.00, Adj2 = $235.56
- Expected: Remaining = $0.00, Status = "Balanced"

### Test Case 2: Partial Allocation
- Input: Total = $385.56, Adj1 = $100.00
- Expected: Remaining = $285.56, Status = "Warning: unresolved balance"

### Test Case 3: Over-allocation
- Input: Total = $385.56, Adj1 = $500.00
- Expected: Error "Amount exceeds available balance"

### Test Case 4: Negative Variance
- Input: Total = -$314.26, Adj1 = -$314.26
- Expected: Remaining = $0.00, Status = "Balanced"

---

## References

- **Excel File**: `/sessions/laughing-sharp-johnson/mnt/uploads/Rj 24-02-2026.xls`
- **Jour Sheet**: Index 9, Column C (Diff.Caisse source)
- **Diff.Caisse# Sheet**: Index 4 (decomposition data)
- **Current Month Total Variance**: ±$854,837.54 (requires audit investigation)
