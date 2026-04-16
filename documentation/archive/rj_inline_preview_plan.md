# RJ Inline Live Preview - Implementation Plan

**Date:** 2025-12-25
**Goal:** Add real-time Excel preview INSIDE each tab that updates as user types

---

## CHANGES NEEDED

### 1. Remove Separate "Aperçu" Tab
- ❌ Delete "Aperçu" tab button from navigation (line 69-71)
- ❌ Delete Preview tab content (lines 1744-1765)

### 2. Add Inline Preview to Each Tab

Each tab will have this structure:
```html
<div id="tab-xxx" class="rj-tab-content">
  <!-- FORM SECTION -->
  <div class="form-tile">
    <!-- Existing form inputs -->
  </div>

  <!-- LIVE PREVIEW SECTION -->
  <div class="excel-preview-container">
    <h4>📊 Aperçu Excel en temps réel</h4>
    <div id="preview-xxx" class="excel-preview">
      <!-- Excel-like preview rendered here -->
    </div>
  </div>
</div>
```

### 3. Add Real-Time Event Listeners

For all input fields:
```javascript
// Listen to all inputs and trigger preview update
document.addEventListener('input', (e) => {
  if (e.target.matches('.sd-input')) {
    updateSDPreview();
  } else if (e.target.matches('.depot-input')) {
    updateDepotPreview();
  }
  // ... etc for each section
});
```

### 4. Preview Rendering Functions

Create specific preview functions for each section:
- `updateSDPreview()` - Shows SD table as it will appear in Excel
- `updateDepotPreview()` - Shows depot entries formatted
- `updateTranselectPreview()` - Shows transelect reconciliation
- etc.

---

## IMPLEMENTATION STEPS

### Step 1: Remove "Aperçu" Tab
- Remove tab button
- Remove tab content div

### Step 2: Add Inline Preview Containers
Start with high-priority tabs:
- SD tab (most important)
- Depot tab
- Transelect tab
- GEAC tab

### Step 3: Add CSS for Inline Previews
```css
.excel-preview-container {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 2px dashed var(--border);
}

.excel-preview {
  background: white;
  padding: 1rem;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  overflow-x: auto;
}
```

### Step 4: Implement Real-Time Updates
- Add class names to all inputs for easy targeting
- Add event listeners
- Create update functions
- Render Excel-like HTML

---

## EXAMPLE: SD Tab with Inline Preview

```html
<!-- SD TAB -->
<div id="tab-sd" class="rj-tab-content">
  <div class="form-tile">
    <h4>SD - Sommaire Journalier des Dépôts</h4>

    <!-- SD TABLE -->
    <table id="sd-table">
      <!-- inputs with class "sd-input" -->
    </table>
  </div>

  <!-- INLINE EXCEL PREVIEW -->
  <div class="excel-preview-container">
    <h4>📊 Aperçu Excel - SD</h4>
    <p style="font-size:0.875rem; color:var(--text-muted);">
      Mise à jour automatique en temps réel
    </p>
    <div id="preview-sd" class="excel-preview">
      <!-- Excel table preview renders here -->
    </div>
  </div>
</div>
```

---

## PRIORITY ORDER

1. **SD Tab** - Most complex, high priority
2. **Depot Tab** - High priority
3. **Recap Tab** - Medium priority
4. **Transelect Tab** - Medium priority
5. **GEAC Tab** - Medium priority
6. **DueBack Tab** - Lower priority (already exists in backend)

---

## BENEFITS

✅ **See changes immediately** as you type
✅ **No tab switching** needed
✅ **Visual confirmation** before saving
✅ **Catch errors** early (e.g., missing values)
✅ **Better UX** - everything in one place
