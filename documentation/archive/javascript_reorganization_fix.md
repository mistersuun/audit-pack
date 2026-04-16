# JavaScript Reorganization Fix

**Date:** 2025-12-25
**Issue:** SD, Depot, Transelect, and GEAC tabs showing blank screens
**Root Cause:** JavaScript code was placed INSIDE tab divs that become hidden (`display: none`) when not active

---

## Problem

The SD, Depot, Transelect, and GEAC JavaScript was incorrectly placed inside their respective tab `<div>` elements:

**Before:**
```
<div id="tab-sd" class="rj-tab-content">
  <!-- SD form content -->
</div>

<div id="tab-depot" class="rj-tab-content">
  <!-- Depot form content -->
  <script>
    // SD JavaScript (lines 440-907) - WRONG LOCATION!
    // This is inside Depot tab, gets hidden when SD tab is active
  </script>
</div>

<div id="tab-transelect" class="rj-tab-content">
  <!-- Transelect form content -->
  <script>
    // Transelect JavaScript (lines 842-1222)
  </script>
</div>

<div id="tab-geac" class="rj-tab-content">
  <!-- GEAC form content -->
  <script>
    // GEAC JavaScript (lines 1008-1339)
  </script>
</div>
```

When a tab has `display: none`, the JavaScript inside it may not execute properly or be accessible to other parts of the page.

---

## Solution

Moved ALL tab-specific JavaScript to the global `{% block scripts %}` section at the end of the template:

**After:**
```
<div id="tab-sd" class="rj-tab-content">
  <!-- SD form content ONLY -->
</div>

<div id="tab-depot" class="rj-tab-content">
  <!-- Depot form content ONLY -->
</div>

<div id="tab-transelect" class="rj-tab-content">
  <!-- Transelect form content ONLY -->
</div>

<div id="tab-geac" class="rj-tab-content">
  <!-- GEAC form content ONLY -->
</div>

<!-- All tabs end here -->

{% block scripts %}
<script>
  feather.replace();

  // SD JavaScript (468 lines)
  let sdData = [];
  function initializeSD() { ... }
  function updateSDPreview() { ... }

  // Depot JavaScript
  let depotData = { client6: [], client8: [] };
  function initializeDepot() { ... }
  function updateDepotPreview() { ... }

  // Transelect JavaScript (381 lines)
  function recalculateRestaurantRow() { ... }
  function updateTranselectPreview() { ... }

  // GEAC JavaScript (332 lines)
  function recalculateGeacReconciliation() { ... }
  function updateGeacPreview() { ... }

  // Main tab switching logic
  function switchRJTab(tabId) { ... }
</script>
{% endblock %}
```

---

## Changes Made

### Files Modified:
- `/templates/rj.html`

### Script Movements:
1. **SD/Depot JavaScript** - Moved from line 440-907 (inside Depot tab) to global scripts section
2. **Transelect JavaScript** - Moved from line 842-1222 (inside Transelect tab) to global scripts section
3. **GEAC JavaScript** - Moved from line 1008-1339 (inside GEAC tab) to global scripts section

### Total Lines Reorganized:
- SD/Depot: 468 lines
- Transelect: 381 lines
- GEAC: 332 lines
- **Total: 1,181 lines of JavaScript moved**

---

## Benefits

1. **Scripts always accessible** - JavaScript functions are now in global scope regardless of which tab is active
2. **No display issues** - Scripts are outside hidden tab divs, so they always load and execute
3. **Better organization** - All JavaScript is in one centralized location
4. **Easier debugging** - No need to search through tab divs to find JavaScript code

---

## Verification

After reorganization:

```bash
grep -n "<script>" templates/rj.html
# Shows only 4 script tags, all in global section (lines 1037-1888)

grep -n 'id="tab-' templates/rj.html
# Shows all tabs are before line 859 (before scripts section)
```

Structure verified:
- ✅ All tab divs: lines 237-859 (contain ONLY HTML content)
- ✅ All scripts: lines 1037-1888 (in global `{% block scripts %}`)
- ✅ Scripts are AFTER tabs (correct)
- ✅ No scripts inside tab divs (correct)

---

## Testing

1. Refresh the page at `http://127.0.0.1:5000/rj`
2. Click on each tab: SD, Depot, Transelect, GEAC
3. **Expected:** All tabs now display their content correctly
4. **Expected:** Inline live previews work in real-time as you type

---

## Backup

A timestamped backup was created before making changes:
```bash
templates/rj.html.backup-20251225-HHMMSS
```

To restore if needed:
```bash
cp templates/rj.html.backup-20251225-HHMMSS templates/rj.html
```
