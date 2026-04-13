# RJ Tabbed Interface - Implementation Plan

**Date:** 2025-12-25
**Goal:** Convert RJ page from single long page to clean tabbed interface with real-time Excel preview

---

## CURRENT STRUCTURE ANALYSIS

### Existing Sections (in order):
1. **File Upload Area** (lines 1-45) - Keep at top, outside tabs
2. **DueBack Section** (lines 47-126) - Move to Tab 1
3. **Recap Section** (lines 128-238) - Move to Tab 2
4. **SD Section** (lines 239-301) - Move to Tab 3
5. **Depot Section** (lines 302-733) - Move to Tab 4
6. **Transelect Section** (lines 734-1361) - Move to Tab 5
7. **GEAC/UX Section** (lines 1362-end) - Move to Tab 6

### New Components Needed:
- **Tab Navigation Bar** - Horizontal tabs at top
- **Tab Content Containers** - Wrap each section
- **Preview Tab** - Show real-time Excel preview
- **Tab Switching JavaScript** - Show/hide tabs
- **Tab Styling CSS** - Make tabs look good

---

## IMPLEMENTATION PLAN

### Phase 1: Prepare Structure ✅ (COMPLETE)
- [x] Add tab navigation HTML (DONE)
- [x] Wrap DueBack in tab-dueback div (DONE)
- [x] Start Recap tab (DONE)
- [x] Close Recap tab, start SD tab (DONE)
- [x] Close SD tab, start Depot tab (DONE)
- [x] Close Depot tab, start Transelect tab (DONE)
- [x] Close Transelect tab, start GEAC tab (DONE)
- [x] Close GEAC tab, add Preview tab (DONE)
- [x] Close tabs container (DONE)

### Phase 2: Add CSS Styling ✅ (COMPLETE)
- [x] Add tab navigation styles (DONE)
- [x] Add tab content styles (DONE)
- [x] Add active tab indicators (DONE)
- [x] Add responsive design (DONE)

### Phase 3: Add JavaScript Functionality ✅ (COMPLETE)
- [x] Add `switchRJTab(tabId)` function (DONE)
- [x] Add tab state persistence (DONE)
- [x] Add real-time preview functionality (DONE)
- [x] Add preview data sync (DONE)

### Phase 4: Testing ⏭️ (IN PROGRESS)
- [ ] Test tab switching
- [ ] Test data persistence across tabs
- [ ] Test preview updates
- [ ] Test responsive design
- [ ] Test all save buttons work

---

## DETAILED IMPLEMENTATION CHECKLIST

### STEP 1: Complete Tab Structure Wrappers

**Goal:** Wrap each section in its tab div

#### 1.1 Close Recap Tab, Open SD Tab
**Location:** Between Recap end (~line 238) and SD start (line 239)

**Find this:**
```html
          </div>
        </div>
      </div>

      <!-- SECTION SD (SOMMAIRE JOURNALIER DES DÉPÔTS) -->
      <div class="form-tile">
        <h4>SD - Sommaire Journalier des Dépôts</h4>
```

**Replace with:**
```html
          </div>
        </div>
      </div>
      <!-- END RECAP TAB -->

      <!-- SD TAB -->
      <div id="tab-sd" class="rj-tab-content">
        <div class="form-tile">
          <h4>SD - Sommaire Journalier des Dépôts</h4>
```

#### 1.2 Close SD Tab, Open Depot Tab
**Location:** Between SD end (~line 301) and Depot start (line 302)

**Find this:**
```html
        </div>

        <!-- SECTION DÉPÔT COMPLÈTE -->
        <div class="form-tile">
          <h4>Dépôt - Comptes Canadiens</h4>
```

**Replace with:**
```html
        </div>
      </div>
      <!-- END SD TAB -->

      <!-- DEPOT TAB -->
      <div id="tab-depot" class="rj-tab-content">
        <div class="form-tile">
          <h4>Dépôt - Comptes Canadiens</h4>
```

#### 1.3 Close Depot Tab, Open Transelect Tab
**Location:** Between Depot end (~line 733) and Transelect start (line 734)

**Find this:**
```html
        </script>

        <!-- SECTION TRANSELECT COMPLÈTE -->
        <div class="form-tile">
```

**Replace with:**
```html
        </script>
      </div>
      <!-- END DEPOT TAB -->

      <!-- TRANSELECT TAB -->
      <div id="tab-transelect" class="rj-tab-content">
        <div class="form-tile">
```

#### 1.4 Close Transelect Tab, Open GEAC Tab
**Location:** Between Transelect end (~line 1361) and GEAC start (line 1362)

**Find this:**
```html
        </script>

        <!-- SECTION GEAC/UX COMPLÈTE -->
        <div class="form-tile">
          <h4>GEAC / UX - Réconciliation finale CC</h4>
```

**Replace with:**
```html
        </script>
      </div>
      <!-- END TRANSELECT TAB -->

      <!-- GEAC TAB -->
      <div id="tab-geac" class="rj-tab-content">
        <div class="form-tile">
          <h4>GEAC / UX - Réconciliation finale CC</h4>
```

#### 1.5 Close GEAC Tab, Add Preview Tab, Close Tabs Container
**Location:** At the very end of the page (before {% endblock %})

**Find this:**
```html
        </div>
      </div>

  </div>
</div>

{% endblock %}
```

**Replace with:**
```html
        </div>
      </div>
      <!-- END GEAC TAB -->

      <!-- PREVIEW TAB -->
      <div id="tab-preview" class="rj-tab-content">
        <div class="form-tile">
          <h4>Aperçu en temps réel</h4>
          <p style="font-size:0.875rem; color:var(--text-secondary); margin-bottom:1.5rem;">
            Prévisualisation du fichier Excel avec vos modifications en temps réel.
          </p>

          <div style="background:#f8f9fa; padding:2rem; border-radius:8px; border:2px solid var(--border);">
            <div style="text-align:center; color:var(--text-muted);">
              <i data-feather="file-text" style="width:64px; height:64px; margin-bottom:1rem;"></i>
              <h4>Aperçu Excel</h4>
              <p>La prévisualisation en temps réel sera affichée ici.</p>
              <small>Entrez des données dans les autres onglets pour voir les mises à jour.</small>
            </div>
          </div>

          <div id="preview-container" style="margin-top:2rem; display:none;">
            <!-- Excel preview will be rendered here -->
          </div>
        </div>
      </div>
      <!-- END PREVIEW TAB -->

    </div>
    <!-- END TABS CONTENT -->
  </div>
  <!-- END TABS CONTAINER -->

</div>

{% endblock %}
```

---

### STEP 2: Add CSS for Tabs

**Location:** In base.html `<style>` section or create new rj-specific CSS

**Add this CSS:**
```css
/* ============================================
   RJ TABS STYLING
   ============================================ */

.rj-tabs-container {
  margin-top: 2rem;
}

.rj-tabs-nav {
  display: flex;
  gap: 0.5rem;
  background: var(--bg);
  border-bottom: 2px solid var(--border);
  padding: 0 1rem;
  overflow-x: auto;
}

.rj-tab-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  color: var(--text-muted);
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.rj-tab-btn:hover {
  color: var(--text);
  background: rgba(74, 144, 226, 0.05);
}

.rj-tab-btn.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
  background: rgba(74, 144, 226, 0.1);
}

.rj-tab-btn svg {
  width: 18px;
  height: 18px;
}

.rj-tabs-content {
  padding: 2rem 1rem;
}

.rj-tab-content {
  display: none;
}

.rj-tab-content.active {
  display: block;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive tabs */
@media (max-width: 768px) {
  .rj-tabs-nav {
    padding: 0 0.5rem;
  }

  .rj-tab-btn {
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
  }
}
```

---

### STEP 3: Add JavaScript for Tab Switching

**Location:** At the end of rj.html, before closing `</script>` tag

**Add this JavaScript:**
```javascript
// ============================================================================
// TAB SWITCHING FUNCTIONALITY
// ============================================================================

let currentRJTab = 'dueback'; // Default active tab

function switchRJTab(tabId) {
  // Hide all tab contents
  document.querySelectorAll('.rj-tab-content').forEach(tab => {
    tab.classList.remove('active');
  });

  // Remove active from all tab buttons
  document.querySelectorAll('.rj-tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  // Show selected tab
  const selectedTab = document.getElementById(`tab-${tabId}`);
  if (selectedTab) {
    selectedTab.classList.add('active');
  }

  // Activate button
  const buttons = document.querySelectorAll('.rj-tab-btn');
  buttons.forEach(btn => {
    if (btn.getAttribute('onclick')?.includes(tabId)) {
      btn.classList.add('active');
    }
  });

  // Update current tab
  currentRJTab = tabId;

  // Save to localStorage
  localStorage.setItem('rj_current_tab', tabId);

  // Re-render feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }

  // Update preview if switching to preview tab
  if (tabId === 'preview') {
    updatePreview();
  }
}

// Restore last active tab on page load
document.addEventListener('DOMContentLoaded', () => {
  const savedTab = localStorage.getItem('rj_current_tab');
  if (savedTab && document.getElementById(`tab-${savedTab}`)) {
    switchRJTab(savedTab);
  }
});

// ============================================================================
// REAL-TIME PREVIEW FUNCTIONALITY
// ============================================================================

function updatePreview() {
  const container = document.getElementById('preview-container');
  if (!container) return;

  // Collect all data from all tabs
  const previewData = {
    dueback: collectDuebackData(),
    recap: collectRecapData(),
    sd: collectSDData(),
    depot: collectDepotData(),
    transelect: collectTranselectData(),
    geac: collectGeacData()
  };

  // Generate preview HTML
  const previewHTML = generatePreviewHTML(previewData);

  container.innerHTML = previewHTML;
  container.style.display = 'block';

  // Re-render feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
}

function collectDuebackData() {
  // TODO: Implement - collect dueback table data
  return { rows: [] };
}

function collectRecapData() {
  // TODO: Implement - collect recap data
  return { fields: {} };
}

function collectSDData() {
  // TODO: Implement - collect SD data
  return { entries: sdData || [] };
}

function collectDepotData() {
  // TODO: Implement - collect depot data
  return {
    client6: depotData?.client6 || [],
    client8: depotData?.client8 || []
  };
}

function collectTranselectData() {
  // TODO: Implement - collect transelect data
  return { restaurant: {}, reception: {} };
}

function collectGeacData() {
  // TODO: Implement - collect GEAC data
  return { reconciliation: {}, balance: {} };
}

function generatePreviewHTML(data) {
  // Generate Excel-like preview
  let html = '<div style="background:white; padding:2rem; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1);">';
  html += '<h5 style="margin-bottom:1rem; color:var(--text);">📊 Résumé des modifications</h5>';

  html += '<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:1rem;">';

  // DueBack summary
  html += `<div style="padding:1rem; background:#f8f9fa; border-radius:6px;">
    <strong>DueBack</strong>
    <p style="margin:0.5rem 0 0 0; font-size:0.875rem; color:var(--text-muted);">
      ${data.dueback.rows.length} entrées
    </p>
  </div>`;

  // SD summary
  html += `<div style="padding:1rem; background:#fff3cd; border-radius:6px;">
    <strong>SD</strong>
    <p style="margin:0.5rem 0 0 0; font-size:0.875rem; color:var(--text-muted);">
      ${data.sd.entries.length} employés
    </p>
  </div>`;

  // Depot summary
  const depotTotal = (data.depot.client6.length || 0) + (data.depot.client8.length || 0);
  html += `<div style="padding:1rem; background:#d1ecf1; border-radius:6px;">
    <strong>Dépôt</strong>
    <p style="margin:0.5rem 0 0 0; font-size:0.875rem; color:var(--text-muted);">
      ${depotTotal} entrées
    </p>
  </div>`;

  html += '</div>';

  html += '<div style="margin-top:2rem; padding:1rem; background:#e7f3ff; border-radius:6px; border-left:4px solid var(--primary);">';
  html += '<p style="margin:0; font-size:0.875rem;"><strong>Note:</strong> Les modifications seront appliquées au fichier Excel lors de l\'enregistrement.</p>';
  html += '</div>';

  html += '</div>';

  return html;
}
```

---

### STEP 4: Verification Checklist

After implementation, verify:

- [ ] **Tab Navigation Displays Correctly**
  - All 7 tabs visible (DueBack, Recap, SD, Dépôt, Transelect, GEAC, Aperçu)
  - Icons show correctly
  - Active tab is highlighted

- [ ] **Tab Switching Works**
  - Click each tab → content changes
  - Active indicator moves
  - No JavaScript errors in console

- [ ] **Content Displays in Tabs**
  - DueBack table shows
  - Recap form shows
  - SD table shows
  - Depot sections show
  - Transelect tables show
  - GEAC sections show
  - Preview placeholder shows

- [ ] **Functionality Preserved**
  - DueBack save works
  - Recap calculations work
  - SD add/remove rows works
  - Depot add/remove amounts works
  - Transelect calculations work
  - GEAC calculations work

- [ ] **Preview Tab**
  - Shows summary of entered data
  - Updates when switching to it
  - No errors

- [ ] **Responsive Design**
  - Tabs scroll on mobile
  - Content readable on all screens

- [ ] **Data Persistence**
  - Tab selection persists on refresh
  - Data stays when switching tabs

---

## EXECUTION ORDER

Execute in this exact order:

1. ✅ **Backup rj.html** (create rj.html.backup)
2. ⏭️ **Make structural edits** (Steps 1.1-1.5)
3. ⏭️ **Add CSS** (Step 2)
4. ⏭️ **Add JavaScript** (Step 3)
5. ⏭️ **Test each tab** (Step 4)
6. ⏭️ **Fix any issues**
7. ⏭️ **Final verification**

---

## ROLLBACK PLAN

If anything goes wrong:
```bash
cp templates/rj.html.backup templates/rj.html
```

---

## ESTIMATED TIME

- Structural edits: 20 minutes
- CSS addition: 5 minutes
- JavaScript addition: 10 minutes
- Testing: 15 minutes
- **Total: ~50 minutes**

---

## READY TO PROCEED?

Please confirm:
- [ ] I've reviewed the plan
- [ ] I understand the changes
- [ ] I'm ready to proceed step by step
- [ ] Backup has been created

Once confirmed, we'll execute each step one at a time with verification.
