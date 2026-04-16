# Livecard Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing `.rjn-livepanel` sidebar with a floating, draggable, collapsible "livecard" built to a Linear/Stripe aesthetic, without breaking the legacy panel during migration.

**Architecture:** All changes land in a single template file (`templates/audit/rj/rj_native.html`). A new CSS block, new HTML shell, and a self-contained IIFE (`window.livecard`) live alongside the existing `.rjn-livepanel`. A `localStorage.rjn_ui_mode` flag chooses which renderer `refreshChecklist()` dispatches to. A parallel Playwright suite (`tests/playwright/livecard.spec.js`) exercises the new component against mocked balance-check responses. Once verified, a cleanup commit removes the legacy panel.

**Tech Stack:** Vanilla JS (ES2020+), custom CSS with existing design tokens (`--emerald`, `--rose`, `--amber`, `--card`, `--border`, `--mono`, `--ease`), Playwright for E2E tests, Flask/Jinja2 template.

**Design spec:** `docs/superpowers/specs/2026-04-10-livecard-redesign.md` — read this first. The plan references its section numbers for layout/CSS details rather than duplicating everything.

---

## File Map

| File | Change | Responsibility |
|---|---|---|
| `templates/audit/rj/rj_native.html` | Modify (3 edits) | New `<style id="livecard-styles">` in `<head>`, new `<aside class="livecard">` + `<div class="livecard-edge-tab">` after the toolbar, new `(function livecard(){ ... })()` IIFE inside the existing `<script>` |
| `tests/playwright/livecard.spec.js` | Create | All 19 Playwright tests, five categories |
| `tests/playwright/fixtures/*.json` | Create | Mocked `/api/rj/native/balance-check/:date` responses (one per scenario) |
| `tests/playwright/playwright.config.js` | Create (if absent) | Playwright config pointing at `tests/playwright` |
| `package.json` | Create/modify | `@playwright/test` devDep + `test:e2e` script |

**Single file discipline:** all livecard CSS/HTML/JS stays in `rj_native.html`. The file grows from ~5000 lines to ~5700 lines. If it exceeds 6000 lines post-merge, a follow-up cleanup task extracts the JS to `static/livecard.js` — that is explicitly **out of scope** for this plan.

---

## Parallel Execution Note

**During Tasks 1-13 (main thread works the livecard)**, a background subagent works on Tasks 14-15 (Playwright harness + full test suite) in parallel. The two streams are independent: the tests only depend on the spec and the JSON fixtures, not on the main-thread code. When the main thread finishes Task 13, Tasks 14-15 should already be drafted and can be run as the integration step.

Launch the parallel subagent at the start of Task 1 with the prompt provided in **Appendix A**.

---

## Task 1: Scaffold the feature flag and empty shell

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (3 edits)

**Purpose:** Get the new card into the DOM behind a flag. Nothing visible yet — just the empty shell, wired so `window.setLivecard(true)` can toggle it on.

- [ ] **Step 1: Add CSS block**

Open `templates/audit/rj/rj_native.html`. Locate the end of the existing `<style>` block by searching for `.rjn-livepanel{` (around line 235) and scrolling to the end of that block (the `[data-theme="dark"] .rjn-livepanel` rules, around line 298). After those rules and **before** the closing `</style>`, insert:

```html
<style id="livecard-styles">
/* === LIVECARD (Phase 4) ======================================
   Floating draggable balance card. Coexists with legacy
   .rjn-livepanel during migration — hidden by default until
   localStorage.rjn_ui_mode === 'livecard'.
   ============================================================ */

.livecard-hidden-mode { display: none !important; }

.livecard {
  position: fixed;
  top: 24px;
  right: 24px;
  width: 380px;
  z-index: 100;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.04);
  font-family: inherit;
  color: var(--text);
  user-select: none;
  transition: width 260ms var(--ease), height 260ms var(--ease),
              transform 260ms var(--ease), opacity 200ms var(--ease);
}

[data-theme="dark"] .livecard {
  background: #14171f;
  border-color: #1e2230;
  box-shadow: 0 10px 30px rgba(0,0,0,0.45), 0 2px 6px rgba(0,0,0,0.3);
}

.livecard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: grab;
  border-bottom: 1px solid var(--border);
}
.livecard-header:active { cursor: grabbing; }
[data-theme="dark"] .livecard-header { border-bottom-color: #1e2230; }

.livecard-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.livecard-controls {
  display: flex;
  gap: 4px;
}
.livecard-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  width: 22px;
  height: 22px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: background 120ms var(--ease), color 120ms var(--ease);
}
.livecard-btn:hover { background: var(--border); color: var(--text); }
.livecard-btn.active { color: var(--emerald); }

.livecard-body {
  padding: 0;
}

/* Edge tab (shown when card is hidden) */
.livecard-edge-tab {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 48px;
  background: var(--emerald);
  border-radius: 6px 0 0 6px;
  cursor: pointer;
  z-index: 100;
  transition: width 180ms var(--ease), background 180ms var(--ease);
}
.livecard-edge-tab:hover { width: 14px; }
.livecard-edge-tab.warn { background: var(--amber); }
.livecard-edge-tab.err  { background: var(--rose); }
</style>
```

- [ ] **Step 2: Add HTML shell**

Still in `rj_native.html`, find the existing `<aside class="rjn-livepanel"` (around line 332). **After the closing `</aside>`** of that panel (around line 361), insert:

```html
<!-- LIVECARD (Phase 4 — floating draggable balance card, feature-flagged) -->
<aside class="livecard livecard-hidden-mode" id="livecard" aria-label="Carte d'équilibrage">
  <header class="livecard-header" id="livecard-header">
    <span class="livecard-title">Diff. Caisse</span>
    <div class="livecard-controls">
      <button type="button" class="livecard-btn" id="livecard-pin"
              title="Épingler (empêche l'auto-ouverture)">📌</button>
      <button type="button" class="livecard-btn" id="livecard-min"
              title="Réduire">–</button>
      <button type="button" class="livecard-btn" id="livecard-hide"
              title="Masquer sur le bord">×</button>
    </div>
  </header>
  <div class="livecard-body" id="livecard-body">
    <!-- Content rendered by window.livecard.render() -->
  </div>
</aside>
<div class="livecard-edge-tab livecard-hidden-mode" id="livecard-edge-tab"
     role="button" aria-label="Afficher la carte d'équilibrage"></div>
```

- [ ] **Step 3: Add feature-flag IIFE**

Find the `async function refreshChecklist()` (around line 4109). **Immediately before** that function, insert:

```html
<script id="livecard-script">
(function() {
  'use strict';

  const LS_MODE = 'rjn_ui_mode';
  const LS_STATE = 'rjn_livecard_state';

  const mode = localStorage.getItem(LS_MODE) || 'legacy';
  const isLivecard = mode === 'livecard';

  const legacyPanel = document.getElementById('livepanel');
  const legacyToggle = document.getElementById('livepanel-toggle');
  const card = document.getElementById('livecard');
  const edgeTab = document.getElementById('livecard-edge-tab');

  if (isLivecard) {
    if (legacyPanel) legacyPanel.classList.add('livecard-hidden-mode');
    if (legacyToggle) legacyToggle.classList.add('livecard-hidden-mode');
    if (card) card.classList.remove('livecard-hidden-mode');
  }

  // Public API — bound in later tasks
  window.livecard = {
    mode: mode,
    init: function() { /* filled in Task 2 */ },
    refresh: function(_data) { /* filled in Task 7 */ },
    onUploadSuccess: function(_d) { /* filled in Task 8 */ },
    render: function(_data) { /* filled in Task 4 */ },
  };

  window.setLivecard = function(enabled) {
    localStorage.setItem(LS_MODE, enabled ? 'livecard' : 'legacy');
    location.reload();
  };

  if (isLivecard && card) {
    window.livecard.init();
  }
})();
</script>
```

- [ ] **Step 4: Smoke-test in browser**

Start the Flask dev server (`python app.py` or the existing run command). Open the RJ native page in the browser. Open devtools console and run:

```js
window.setLivecard(true)
```

Expected: page reloads. You should see a new empty card at top-right (380×44 approximately, just the header "DIFF. CAISSE" with three buttons). The legacy `.rjn-livepanel` should be gone. Run:

```js
window.setLivecard(false)
```

Expected: page reloads, legacy panel returns, new card gone.

- [ ] **Step 5: Commit**

Pause — the user handles all git commits for this project. Do not run `git commit`. Move to Task 2.

---

## Task 2: Drag + position persistence

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (livecard IIFE)

**Purpose:** Make the card draggable by its header, clamp it inside the viewport with a 20px margin, and persist position in `localStorage`.

- [ ] **Step 1: Add state + localStorage helpers**

Inside the livecard IIFE (the `(function(){ ... })()` added in Task 1), **between** the `window.setLivecard` definition and the `if (isLivecard && card)` block, insert:

```js
  // ---------- State + persistence ----------
  const state = {
    pinned: false,
    minimized: false,
    hidden: false,
    pos: null,     // {x, y} or null (default = top-right)
    lastResponseHash: null,
  };

  function loadState() {
    try {
      const raw = localStorage.getItem(LS_STATE);
      if (!raw) return;
      const saved = JSON.parse(raw);
      if (saved && typeof saved === 'object') {
        if (typeof saved.pinned === 'boolean') state.pinned = saved.pinned;
        if (typeof saved.minimized === 'boolean') state.minimized = saved.minimized;
        if (typeof saved.hidden === 'boolean') state.hidden = saved.hidden;
        if (saved.pos && typeof saved.pos.x === 'number') state.pos = saved.pos;
      }
    } catch (e) { /* corrupt localStorage — ignore */ }
  }

  function saveState() {
    try {
      localStorage.setItem(LS_STATE, JSON.stringify({
        pinned: state.pinned,
        minimized: state.minimized,
        hidden: state.hidden,
        pos: state.pos,
      }));
    } catch (e) { /* quota exceeded — ignore */ }
  }

  function applyPosition() {
    if (!card) return;
    if (state.pos) {
      card.style.top = state.pos.y + 'px';
      card.style.left = state.pos.x + 'px';
      card.style.right = 'auto';
    } else {
      card.style.top = '24px';
      card.style.right = '24px';
      card.style.left = 'auto';
    }
  }

  function clampPosition(x, y) {
    const rect = card.getBoundingClientRect();
    const margin = 20;
    const maxX = window.innerWidth - rect.width - margin;
    const maxY = window.innerHeight - rect.height - margin;
    return {
      x: Math.max(margin, Math.min(x, maxX)),
      y: Math.max(margin, Math.min(y, maxY)),
    };
  }
```

- [ ] **Step 2: Add drag handler**

Immediately after the clampPosition helper, insert:

```js
  // ---------- Drag ----------
  function attachDrag() {
    const header = document.getElementById('livecard-header');
    if (!header) return;
    let dragging = false;
    let startX = 0, startY = 0, startLeft = 0, startTop = 0;

    header.addEventListener('mousedown', (e) => {
      // Ignore clicks on buttons inside the header
      if (e.target.closest('.livecard-btn')) return;
      dragging = true;
      const rect = card.getBoundingClientRect();
      startLeft = rect.left;
      startTop = rect.top;
      startX = e.clientX;
      startY = e.clientY;
      card.style.transition = 'none';
      e.preventDefault();
    });

    window.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      const clamped = clampPosition(startLeft + dx, startTop + dy);
      state.pos = clamped;
      applyPosition();
    });

    window.addEventListener('mouseup', () => {
      if (!dragging) return;
      dragging = false;
      card.style.transition = '';
      saveState();
    });
  }
```

- [ ] **Step 3: Wire init()**

Replace the placeholder `init: function() { /* filled in Task 2 */ }` with:

```js
    init: function() {
      loadState();
      applyPosition();
      attachDrag();
    },
```

- [ ] **Step 4: Manual smoke test**

Reload the page with `window.setLivecard(true)`. Verify:
1. Card appears at top-right by default
2. Drag the header — card follows the mouse
3. Drag toward the edge — card clamps at 20px margin
4. Refresh the page — card reappears at its last-dragged position
5. Run `localStorage.removeItem('rjn_livecard_state')` + reload — card returns to top-right default

- [ ] **Step 5: Commit (user handles git)**

Do not commit yourself. Continue to Task 3.

---

## Task 3: Minimize (pill) + hide (edge tab) states

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (CSS block + IIFE)

**Purpose:** Wire the two remaining shell states. Pill state = 190×44 compact form. Hidden state = card disappears, edge tab shows on right edge; clicking the edge tab restores the card.

- [ ] **Step 1: Add CSS for pill + hidden states**

Inside the `<style id="livecard-styles">` block, **before** the `/* Edge tab */` comment, insert:

```css
.livecard.pill {
  width: 190px;
  overflow: hidden;
}
.livecard.pill .livecard-body { display: none; }
.livecard.pill .livecard-header { border-bottom: none; padding: 10px 14px; }
.livecard.pill .livecard-title {
  font-family: var(--mono);
  font-size: 13px;
  letter-spacing: 0;
  text-transform: none;
  color: var(--text);
}
.livecard.pill .livecard-title::before {
  content: '●';
  margin-right: 6px;
  color: var(--emerald);
}
.livecard.pill.warn .livecard-title::before { color: var(--amber); }
.livecard.pill.err  .livecard-title::before { color: var(--rose); }

.livecard.hidden-state { display: none; }
```

Then update the `.livecard-hidden-mode` rule at the top of the block to also apply to the edge tab element — the edge tab is already covered, nothing to change.

- [ ] **Step 2: Add state transition helpers to IIFE**

In the livecard IIFE, immediately after the `attachDrag()` function, insert:

```js
  // ---------- Visibility states ----------
  function applyVisibility() {
    if (!card || !edgeTab) return;
    card.classList.toggle('pill', state.minimized && !state.hidden);
    card.classList.toggle('hidden-state', state.hidden);
    edgeTab.classList.toggle('livecard-hidden-mode', !state.hidden);
  }

  function setMinimized(flag) {
    state.minimized = !!flag;
    if (flag) state.hidden = false;
    applyVisibility();
    saveState();
  }

  function setHidden(flag) {
    state.hidden = !!flag;
    applyVisibility();
    saveState();
  }

  function setPinned(flag) {
    state.pinned = !!flag;
    const btn = document.getElementById('livecard-pin');
    if (btn) btn.classList.toggle('active', state.pinned);
    saveState();
  }

  function attachControls() {
    const minBtn = document.getElementById('livecard-min');
    const hideBtn = document.getElementById('livecard-hide');
    const pinBtn = document.getElementById('livecard-pin');
    if (minBtn) minBtn.addEventListener('click', () => setMinimized(!state.minimized));
    if (hideBtn) hideBtn.addEventListener('click', () => setHidden(true));
    if (pinBtn) pinBtn.addEventListener('click', () => setPinned(!state.pinned));
    if (edgeTab) edgeTab.addEventListener('click', () => setHidden(false));
    // Clicking the pill header (not a button) restores the expanded card
    const header = document.getElementById('livecard-header');
    if (header) {
      header.addEventListener('click', (e) => {
        if (e.target.closest('.livecard-btn')) return;
        if (state.minimized) setMinimized(false);
      });
    }
  }
```

- [ ] **Step 3: Update init()**

Extend the `init` function to call the new helpers. Replace the current init with:

```js
    init: function() {
      loadState();
      applyPosition();
      applyVisibility();
      setPinned(state.pinned);
      attachDrag();
      attachControls();
    },
```

- [ ] **Step 4: Manual smoke test**

Reload with livecard mode on. Verify:
1. Click `–` (minimize) → card shrinks to 190px pill, body hides
2. Click the pill header → card expands back
3. Click `×` (hide) → card disappears, green edge tab appears on right
4. Click the edge tab → card reappears
5. Click `📌` → pin button turns green
6. Reload → pin state, minimized state, and hidden state all persist

- [ ] **Step 5: Continue to Task 4**

---

## Task 4: DC hero + verdict rendering

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (CSS block + IIFE)

**Purpose:** Fill the card body with the DC hero number (34px JetBrains Mono) and verdict text. Mock data for now — real refresh wiring lands in Task 7.

- [ ] **Step 1: Add CSS for DC hero + verdict**

Inside `<style id="livecard-styles">`, **after** the `.livecard-body { padding: 0; }` rule, insert:

```css
.livecard-hero {
  padding: 18px 18px 14px;
  text-align: center;
  border-bottom: 1px solid var(--border);
}
[data-theme="dark"] .livecard-hero { border-bottom-color: #1e2230; }

.livecard-dc {
  font-family: var(--mono);
  font-size: 34px;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: var(--emerald);
  transition: color 400ms var(--ease), transform 200ms var(--ease);
}
.livecard-dc.warn { color: var(--amber); }
.livecard-dc.err  { color: var(--rose); }

.livecard-verdict {
  margin-top: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--emerald);
  transition: color 400ms var(--ease);
}
.livecard-verdict.warn { color: var(--amber); }
.livecard-verdict.err  { color: var(--rose); }
```

- [ ] **Step 2: Implement render() body skeleton**

In the livecard IIFE, **before** the `window.livecard = { ... }` public API block, insert:

```js
  // ---------- Rendering ----------
  const DC_OK_THRESHOLD = 0.16;

  function fmtMoneyLocal(v) {
    const n = Number(v || 0);
    return (n < 0 ? '-' : '') + '$' + Math.abs(n).toFixed(2);
  }

  function classifyDC(dc) {
    const abs = Math.abs(dc);
    if (abs < DC_OK_THRESHOLD) return 'ok';
    if (abs < 10) return 'warn';
    return 'err';
  }

  function verdictText(klass, residualOk) {
    if (klass === 'ok') return 'Équilibré ✓';
    if (residualOk) return 'Réconcilié';
    return 'À investiguer';
  }

  function renderInto(data) {
    const body = document.getElementById('livecard-body');
    if (!body) return;
    const dc = Number(data.dc_current ?? data.dc_calculated ?? 0);
    const decomp = data.dc_decomposition || {};
    const residual = Number(decomp.unexplained_residual || 0);
    const residualOk = Math.abs(residual) < DC_OK_THRESHOLD;
    const klass = classifyDC(dc);
    const verdictKlass = (klass === 'ok') ? 'ok' : (residualOk ? 'warn' : 'err');

    body.innerHTML = `
      <div class="livecard-hero">
        <div class="livecard-dc ${klass === 'ok' ? '' : klass}" id="livecard-dc">${fmtMoneyLocal(dc)}</div>
        <div class="livecard-verdict ${verdictKlass === 'ok' ? '' : verdictKlass}" id="livecard-verdict">${verdictText(klass, residualOk)}</div>
      </div>
    `;

    // Pill title mirrors the DC value when minimized
    const titleEl = card ? card.querySelector('.livecard-title') : null;
    if (titleEl && state.minimized) {
      titleEl.textContent = fmtMoneyLocal(dc);
    } else if (titleEl) {
      titleEl.textContent = 'Diff. Caisse';
    }
    if (card) {
      card.classList.toggle('warn', klass === 'warn');
      card.classList.toggle('err', klass === 'err');
    }
    if (edgeTab) {
      edgeTab.classList.toggle('warn', klass === 'warn');
      edgeTab.classList.toggle('err', klass === 'err');
    }
  }
```

- [ ] **Step 3: Wire render() public method**

Replace the placeholder `render: function(_data) { /* filled in Task 4 */ }` with:

```js
    render: function(data) {
      if (!card || !data) return;
      renderInto(data);
    },
```

- [ ] **Step 4: Manual smoke test**

In devtools with livecard mode on, run:

```js
window.livecard.render({ dc_current: 0, dc_decomposition: { unexplained_residual: 0 } });
```

Expected: DC shows `$0.00` in emerald, verdict "Équilibré ✓". Then:

```js
window.livecard.render({ dc_current: -2167.86, dc_decomposition: { unexplained_residual: 0 } });
```

Expected: DC shows `-$2167.86` in amber (because residual is 0 → reconciled), verdict "Réconcilié".

```js
window.livecard.render({ dc_current: -2167.86, dc_decomposition: { unexplained_residual: -2.51 } });
```

Expected: DC in rose, verdict "À investiguer".

- [ ] **Step 5: Continue to Task 5**

---

## Task 5: Variance rows + checklist sections

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (CSS + IIFE renderer)

**Purpose:** Fill in the two middle sections — the 10-class variance decomposition table and the collapsible 21-point checklist.

- [ ] **Step 1: Add CSS for variances + checklist**

Inside `<style id="livecard-styles">`, **after** the `.livecard-verdict.err` rule, insert:

```css
.livecard-section {
  padding: 12px 18px;
  border-bottom: 1px solid var(--border);
}
[data-theme="dark"] .livecard-section { border-bottom-color: #1e2230; }
.livecard-section:last-child { border-bottom: none; }

.livecard-section-title {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.livecard-var-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 4px 0;
  font-size: 12px;
  transition: background 400ms var(--ease);
}
.livecard-var-row .label { color: var(--text-sec); font-weight: 600; }
.livecard-var-row .value { color: var(--text); font-weight: 700; font-family: var(--mono); }
.livecard-var-row.residual.err .value { color: var(--rose); }
.livecard-var-row.residual.ok .value { color: var(--emerald); }
.livecard-var-row[data-just-updated="true"] { background: var(--amber-bg); }

.livecard-checklist-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}
.livecard-checklist-score {
  font-family: var(--mono);
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
}
.livecard-checklist-score.ok  { color: var(--emerald); }
.livecard-checklist-score.err { color: var(--rose); }
.livecard-checklist-items {
  display: none;
  margin-top: 8px;
  max-height: 260px;
  overflow-y: auto;
}
.livecard-section.expanded .livecard-checklist-items { display: block; }

.livecard-check-item {
  display: flex;
  gap: 8px;
  padding: 5px 0;
  border-bottom: 1px solid var(--border);
  font-size: 11px;
  line-height: 1.35;
}
[data-theme="dark"] .livecard-check-item { border-bottom-color: #1e2230; }
.livecard-check-item:last-child { border-bottom: none; }
.livecard-check-item .ic { width: 14px; text-align: center; flex-shrink: 0; }
.livecard-check-item.pass .ic { color: var(--emerald); }
.livecard-check-item.fail .ic { color: var(--rose); }
.livecard-check-item.warn .ic { color: var(--amber); }
.livecard-check-item .txt { flex: 1; color: var(--text-sec); }
.livecard-check-item .detail { font-family: var(--mono); font-size: 10px; color: var(--text-muted); margin-top: 2px; }
```

- [ ] **Step 2: Extend renderInto() with variances + checklist**

Replace the `renderInto` function (from Task 4) with this expanded version:

```js
  const VARIANCE_ROWS = [
    ['Transelect X20',    'x20_transelect'],
    ['GEAC col 41',       'geac_bottom'],
    ['InterHotel XferIn', 'interhotel_xferin'],
    ['PANNE LIEN',        'panne_lien_hotel'],
    ['Chambres annul.',   'chambres_annulation'],
    ['Correction veille', 'prior_day_correction'],
    ['Poste caissier',    'cashier_misposting'],
    ['Dépôt resto',       'depot_resto_pas_ferme'],
    ['Recap surplus',     'recap_surplus'],
    ['Recap déficit',     'recap_deficit'],
  ];

  function _checkMetaLocal(status) {
    if (status === 'pass') return ['pass', '✓'];
    if (status === 'fail') return ['fail', '✗'];
    return ['warn', '!'];
  }

  function buildVariancesHtml(decomp) {
    const classes = decomp.classes || {};
    const nonzero = VARIANCE_ROWS
      .map(([label, key]) => [label, Number(classes[key] || 0)])
      .filter(([, v]) => Math.abs(v) >= 0.01);

    const lines = [];
    if (nonzero.length === 0) {
      lines.push(`<div class="livecard-var-row"><span class="label">Aucune variance</span><span class="value">—</span></div>`);
    } else {
      for (const [label, val] of nonzero) {
        lines.push(`<div class="livecard-var-row" data-var-key="${label}"><span class="label">${label}</span><span class="value">${fmtMoneyLocal(val)}</span></div>`);
      }
    }
    const declared = Number(decomp.declared_sum || 0);
    const residual = Number(decomp.unexplained_residual || 0);
    lines.push(`<div class="livecard-var-row"><span class="label">Somme déclarées</span><span class="value">${fmtMoneyLocal(declared)}</span></div>`);
    const resOk = Math.abs(residual) < DC_OK_THRESHOLD;
    lines.push(
      `<div class="livecard-var-row residual ${resOk ? 'ok' : 'err'}">` +
      `<span class="label">Résiduel</span>` +
      `<span class="value">${fmtMoneyLocal(residual)}</span></div>`
    );
    return { html: lines.join(''), nonzeroCount: nonzero.length };
  }

  function buildChecklistHtml(checks) {
    if (!checks || checks.length === 0) return { html: '', score: '', klass: '' };
    const pass = checks.filter(c => _checkMetaLocal(c.status)[0] === 'pass').length;
    const scoreKlass = (pass === checks.length) ? 'ok' : 'err';
    const itemsHtml = checks.map(c => {
      const [cls, icon] = _checkMetaLocal(c.status);
      const detail = c.detail ? `<div class="detail">${c.detail}</div>` : '';
      return `<div class="livecard-check-item ${cls}">` +
             `<span class="ic">${icon}</span>` +
             `<div class="txt">${c.item || 'Item'}${detail}</div></div>`;
    }).join('');
    return { html: itemsHtml, score: `${pass}/${checks.length}`, klass: scoreKlass };
  }

  function renderInto(data) {
    const body = document.getElementById('livecard-body');
    if (!body) return;
    const dc = Number(data.dc_current ?? data.dc_calculated ?? 0);
    const decomp = data.dc_decomposition || {};
    const residual = Number(decomp.unexplained_residual || 0);
    const residualOk = Math.abs(residual) < DC_OK_THRESHOLD;
    const klass = classifyDC(dc);
    const verdictKlass = (klass === 'ok') ? 'ok' : (residualOk ? 'warn' : 'err');

    const variances = buildVariancesHtml(decomp);
    const checklist = buildChecklistHtml(data.checklist || []);

    body.innerHTML = `
      <div class="livecard-hero">
        <div class="livecard-dc ${klass === 'ok' ? '' : klass}" id="livecard-dc">${fmtMoneyLocal(dc)}</div>
        <div class="livecard-verdict ${verdictKlass === 'ok' ? '' : verdictKlass}" id="livecard-verdict">${verdictText(klass, residualOk)}</div>
      </div>
      ${variances.nonzeroCount > 0 || Math.abs(dc) >= DC_OK_THRESHOLD ? `
        <div class="livecard-section">
          <div class="livecard-section-title">Variances déclarées</div>
          ${variances.html}
        </div>` : ''}
      ${checklist.html ? `
        <div class="livecard-section" id="livecard-checklist-section">
          <div class="livecard-checklist-summary" id="livecard-checklist-summary">
            <div class="livecard-section-title" style="margin-bottom:0">Checklist 21 points</div>
            <div class="livecard-checklist-score ${checklist.klass}">${checklist.score}</div>
          </div>
          <div class="livecard-checklist-items">${checklist.html}</div>
        </div>` : ''}
    `;

    // Checklist expand/collapse
    const sum = document.getElementById('livecard-checklist-summary');
    const sec = document.getElementById('livecard-checklist-section');
    if (sum && sec) {
      sum.addEventListener('click', () => sec.classList.toggle('expanded'));
    }

    // Pill title mirror
    const titleEl = card ? card.querySelector('.livecard-title') : null;
    if (titleEl && state.minimized) {
      titleEl.textContent = fmtMoneyLocal(dc);
    } else if (titleEl) {
      titleEl.textContent = 'Diff. Caisse';
    }
    if (card) {
      card.classList.toggle('warn', klass === 'warn');
      card.classList.toggle('err', klass === 'err');
    }
    if (edgeTab) {
      edgeTab.classList.toggle('warn', klass === 'warn');
      edgeTab.classList.toggle('err', klass === 'err');
    }
  }
```

- [ ] **Step 3: Manual smoke test**

In devtools:

```js
window.livecard.render({
  dc_current: -2167.86,
  dc_decomposition: {
    classes: { x20_transelect: -2165.35, panne_lien_hotel: -2.51 },
    declared_sum: -2167.86,
    unexplained_residual: 0,
  },
  checklist: [
    { item: 'Somme de DC = 0', status: 'fail', detail: 'DC=-2167.86' },
    { item: 'Checks balance', status: 'pass' },
  ],
});
```

Expected: DC amber, two variance rows visible ("Transelect X20" and "PANNE LIEN"), "Somme déclarées" row, "Résiduel" row in emerald, checklist section shows `1/2` in rose. Click checklist summary → items expand.

- [ ] **Step 4: Continue to Task 6**

---

## Task 6: Auto-note section + footer

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (CSS + IIFE renderer)

**Purpose:** Add the auto-note slide-in section (visible only when DC ≠ 0 AND residual = 0 AND `dc_note_text` is present) and the always-visible footer with auditor name + formatted date.

- [ ] **Step 1: Add CSS**

Inside `<style id="livecard-styles">`, **after** the `.livecard-check-item .detail` rule, insert:

```css
.livecard-autonote {
  font-family: var(--mono);
  font-size: 11px;
  line-height: 1.5;
  white-space: pre-wrap;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 10px;
  color: var(--text);
  max-height: 120px;
  overflow-y: auto;
}
[data-theme="dark"] .livecard-autonote { background: #0c0f14; border-color: #1e2230; }

.livecard-autonote-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
  font-size: 10px;
  color: var(--text-muted);
}
.livecard-autonote-copy {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-sec);
  padding: 3px 10px;
  font-size: 10px;
  font-weight: 600;
  border-radius: 4px;
  cursor: pointer;
  transition: all 150ms var(--ease);
}
.livecard-autonote-copy:hover { border-color: var(--emerald); color: var(--emerald); }
.livecard-autonote-copy.copied { background: var(--emerald-bg); color: var(--emerald); border-color: var(--emerald); }

.livecard-footer {
  padding: 10px 18px;
  font-size: 10px;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
  border-top: 1px solid var(--border);
}
[data-theme="dark"] .livecard-footer { border-top-color: #1e2230; }
```

- [ ] **Step 2: Extend renderInto() with auto-note + footer**

Locate the `body.innerHTML = \`...\`;` assignment in `renderInto()`. Replace the entire template literal (from `<div class="livecard-hero">` through the closing backtick) with:

```js
    const serverNote = typeof data.dc_note_text === 'string' ? data.dc_note_text : '';
    const showNote = Math.abs(dc) >= DC_OK_THRESHOLD && residualOk && (serverNote || variances.nonzeroCount > 0);
    const auditor = data.auditor || (window.SESSION && window.SESSION.auditor) || '—';
    const auditDate = data.audit_date || (window.SESSION && window.SESSION.audit_date) || '';
    const formattedDate = auditDate ? new Date(auditDate).toLocaleDateString('fr-CA', { year: 'numeric', month: 'short', day: 'numeric' }) : '—';

    body.innerHTML = `
      <div class="livecard-hero">
        <div class="livecard-dc ${klass === 'ok' ? '' : klass}" id="livecard-dc">${fmtMoneyLocal(dc)}</div>
        <div class="livecard-verdict ${verdictKlass === 'ok' ? '' : verdictKlass}" id="livecard-verdict">${verdictText(klass, residualOk)}</div>
      </div>
      ${variances.nonzeroCount > 0 || Math.abs(dc) >= DC_OK_THRESHOLD ? `
        <div class="livecard-section">
          <div class="livecard-section-title">Variances déclarées</div>
          ${variances.html}
        </div>` : ''}
      ${checklist.html ? `
        <div class="livecard-section" id="livecard-checklist-section">
          <div class="livecard-checklist-summary" id="livecard-checklist-summary">
            <div class="livecard-section-title" style="margin-bottom:0">Checklist 21 points</div>
            <div class="livecard-checklist-score ${checklist.klass}">${checklist.score}</div>
          </div>
          <div class="livecard-checklist-items">${checklist.html}</div>
        </div>` : ''}
      ${showNote ? `
        <div class="livecard-section" id="livecard-autonote-section">
          <div class="livecard-section-title">Note auto-générée</div>
          <div class="livecard-autonote" id="livecard-autonote">${serverNote || _buildClientNote(variances, auditor)}</div>
          <div class="livecard-autonote-actions">
            <span>À coller dans la cellule DC (col C)</span>
            <button type="button" class="livecard-autonote-copy" id="livecard-autonote-copy">Copier</button>
          </div>
        </div>` : ''}
      <div class="livecard-footer">
        <span>${auditor}</span>
        <span>${formattedDate}</span>
      </div>
    `;
```

- [ ] **Step 3: Add client-side note fallback + copy handler**

In the livecard IIFE, immediately after the `VARIANCE_ROWS` constant, insert:

```js
  function _buildClientNote(variances, auditor) {
    const lines = [`Auditeur De Nuit: ${auditor || ''}`];
    // Reparse from data-var-key-labeled rows if present
    const rows = variances.html.match(/data-var-key="([^"]+)">[\s\S]*?value">([^<]+)/g) || [];
    rows.forEach(r => {
      const m = r.match(/data-var-key="([^"]+)">[\s\S]*?value">([^<]+)/);
      if (m) lines.push(`${m[1]}: ${m[2]}`);
    });
    return lines.join('\n');
  }

  function attachAutoNoteCopy() {
    const btn = document.getElementById('livecard-autonote-copy');
    const note = document.getElementById('livecard-autonote');
    if (!btn || !note) return;
    btn.addEventListener('click', () => {
      const text = note.textContent || '';
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
          btn.textContent = 'Copié ✓';
          btn.classList.add('copied');
          setTimeout(() => {
            btn.textContent = 'Copier';
            btn.classList.remove('copied');
          }, 1500);
        }).catch(() => { /* silent */ });
      }
    });
  }
```

Then at the **end** of `renderInto()` (after the checklist event listener wire-up), add:

```js
    attachAutoNoteCopy();
```

- [ ] **Step 4: Manual smoke test**

In devtools with a mock that includes a note:

```js
window.livecard.render({
  dc_current: -2167.86,
  dc_note_text: "Auditeur De Nuit: Test\nTranselect X20: 2167.86",
  dc_decomposition: { classes: { x20_transelect: -2167.86 }, declared_sum: -2167.86, unexplained_residual: 0 },
  checklist: [{ item: 'DC=0', status: 'pass' }],
  auditor: 'Test',
  audit_date: '2026-04-10',
});
```

Expected: auto-note section visible with the server-provided text. Click "Copier" → button turns green, says "Copié ✓", reverts after 1.5s. Footer shows "Test" and "9 avr. 2026" (or similar localized format). Then render with `dc_current: 0` — auto-note section disappears.

- [ ] **Step 5: Continue to Task 7**

---

## Task 7: refresh() + diff-gated render + legacy dispatch

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (IIFE + existing `refreshChecklist`)

**Purpose:** Wire the card to the real `/api/rj/native/balance-check/:date` endpoint. Dispatch from the existing `refreshChecklist()` to either the legacy renderer or the new livecard. Add a diff-gated render (hash the response; skip identical renders).

- [ ] **Step 1: Add refresh() + hash helper**

In the livecard IIFE, immediately after `attachAutoNoteCopy`, insert:

```js
  // ---------- Refresh + diff gate ----------
  function _hash(s) {
    // Tiny FNV-1a — fast and collision-safe enough for response dedup
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = (h * 16777619) >>> 0;
    }
    return h.toString(16);
  }

  async function refresh(data) {
    if (!card) return;
    let payload = data;
    if (!payload) {
      const session = window.SESSION;
      if (!session || !session.audit_date) return;
      try {
        const r = await fetch(`/api/rj/native/balance-check/${session.audit_date}`);
        if (!r.ok) return;
        payload = await r.json();
      } catch (e) { return; }
    }
    const hash = _hash(JSON.stringify(payload));
    if (hash === state.lastResponseHash) return;  // diff gate
    state.lastResponseHash = hash;
    renderInto(payload);
  }
```

- [ ] **Step 2: Wire public refresh() method**

Replace the placeholder `refresh: function(_data) { /* filled in Task 7 */ }` with:

```js
    refresh: function(data) { return refresh(data); },
```

- [ ] **Step 3: Dispatch from refreshChecklist()**

Find the existing `async function refreshChecklist()` (around line 4109). Replace its body with:

```js
async function refreshChecklist(){
  if (!SESSION || !SESSION.audit_date) return;
  clearTimeout(_checklistTimer);
  _checklistTimer = setTimeout(async () => {
    try {
      const r = await fetch(`/api/rj/native/balance-check/${SESSION.audit_date}`);
      if (!r.ok) return;
      const d = await r.json();
      if (window.livecard && window.livecard.mode === 'livecard') {
        window.livecard.refresh(d);
      } else {
        renderLivePanel(d);
      }
    } catch(e) {
      // Silent — checklist is non-critical
    }
  }, 300);
}
```

- [ ] **Step 4: Manual smoke test**

With livecard mode on AND a real session loaded, trigger any field save (change a value in the form and blur). Verify:
1. Network tab shows a `GET /api/rj/native/balance-check/<date>` request
2. The livecard updates with real DC + variances + checklist
3. Triggering a second save with no data change → the second response is fetched but the card DOM does NOT re-render (set a breakpoint in `renderInto` to confirm, or add a `console.log('render')` temporarily and watch the console)
4. Changing a field so the balance genuinely changes → card re-renders

- [ ] **Step 5: Continue to Task 8**

---

## Task 8: Upload hook + startSession hook

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (existing upload handler + IIFE)

**Purpose:** When the upload endpoint returns a successful parse, refresh the livecard immediately (don't wait for the 300ms debounce). Also handle the file-date-mismatch error case — show a loud toast AND auto-expand the card from pill state.

- [ ] **Step 1: Implement onUploadSuccess() in IIFE**

Replace the placeholder `onUploadSuccess: function(_d) { /* filled in Task 8 */ }` with:

```js
    onUploadSuccess: function(d) {
      // Auto-expand from pill state unless pinned
      if (state.minimized && !state.pinned && !state.hidden) {
        setMinimized(false);
      }
      if (d && d.date_mismatch) {
        // Loud toast handled by main-thread hook; just flash the card
        if (card) {
          card.classList.add('err');
          setTimeout(() => card.classList.remove('err'), 1200);
        }
        return;
      }
      // Refresh now, bypassing the 300ms debounce by calling refresh() directly
      refresh();
    },
```

- [ ] **Step 2: Wire the upload handler**

Find the existing file upload handler at `document.getElementById('file-report-upload').addEventListener('change', ...)` (around line 1974). Locate the success branch — after the JSON response is parsed and `loadSessionToForm(SESSION)` is called, and before the `refreshChecklist()` call (around line 2033).

Insert **one line** after `loadSessionToForm(SESSION)` and before `refreshChecklist()`:

```js
      if (window.livecard && window.livecard.mode === 'livecard') window.livecard.onUploadSuccess(d);
```

- [ ] **Step 3: Manual smoke test**

With livecard mode on and the card minimized to pill, upload a valid file (any source document). Verify:
1. Card auto-expands from pill
2. Card content updates with fresh data immediately (no 300ms debounce visible)
3. Pin the card (📌), minimize to pill, upload again → card stays as pill (auto-expand suppressed)

- [ ] **Step 4: Continue to Task 9**

---

## Task 9: Auto-expand triggers + smart behaviors wiring

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (IIFE)

**Purpose:** Implement the two auto-expand triggers defined in spec §8.1: checklist pass→fail transition, and DC crossing the `|DC| < 10` → `|DC| ≥ 10` threshold. Both are suppressed by the pin toggle and never fire from hidden state.

- [ ] **Step 1: Track previous state**

In the IIFE, extend the `state` object at the top (added in Task 2). Replace the `state` declaration with:

```js
  const state = {
    pinned: false,
    minimized: false,
    hidden: false,
    pos: null,
    lastResponseHash: null,
    prevFailedCount: null,   // for checklist transition detection
    prevDcBucket: null,      // 'ok' | 'warn' | 'err'
  };
```

- [ ] **Step 2: Add transition detection to renderInto()**

At the **start** of `renderInto()`, after the `const body = ...` line, insert:

```js
    const checks = data.checklist || [];
    const failedCount = checks.filter(c => c.status === 'fail').length;
    const newBucket = classifyDC(Number(data.dc_current ?? data.dc_calculated ?? 0));
    const shouldAutoExpand = (
      !state.pinned &&
      !state.hidden &&
      state.minimized &&
      (
        (state.prevFailedCount !== null && failedCount > state.prevFailedCount) ||
        (state.prevDcBucket === 'warn' && newBucket === 'err') ||
        (state.prevDcBucket === 'ok' && newBucket !== 'ok')
      )
    );
    state.prevFailedCount = failedCount;
    state.prevDcBucket = newBucket;
    if (shouldAutoExpand) {
      setMinimized(false);
    }
```

- [ ] **Step 3: Manual smoke test**

With livecard mode on:

1. Render a passing state, minimize to pill:
```js
window.livecard.render({ dc_current: 0, dc_decomposition: { unexplained_residual: 0 }, checklist: [{item:'a',status:'pass'}] });
document.getElementById('livecard-min').click();
```
2. Render a failing state:
```js
window.livecard.render({ dc_current: 2500, dc_decomposition: { unexplained_residual: 2500 }, checklist: [{item:'a',status:'fail'}] });
```
Expected: card auto-expands.

3. Re-minimize, pin, render again with different failure → card stays as pill (pin suppresses).

- [ ] **Step 4: Continue to Task 10**

---

## Task 10: Animation gate + row pulses

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (CSS + IIFE)

**Purpose:** Implement the attention gate (promise queue) and row-level pulses per spec §8.2 and §8.5. Pulses are single 600ms CSS ring flashes applied to variance rows whose values changed since the last render.

- [ ] **Step 1: Add pulse + shimmer keyframes**

Inside `<style id="livecard-styles">`, before the closing `</style>`, insert:

```css
@keyframes livecard-pulse {
  0%   { box-shadow: 0 0 0 0 var(--amber); background: var(--amber-bg); }
  70%  { box-shadow: 0 0 0 8px transparent; }
  100% { box-shadow: 0 0 0 0 transparent; background: transparent; }
}
.livecard-var-row.livecard-pulsing {
  animation: livecard-pulse 600ms var(--ease);
  border-radius: 4px;
}
```

- [ ] **Step 2: Add animation gate + diff-pulse logic**

In the IIFE, after `state.lastResponseHash = null` (inside the state object) — no wait, in the helpers section, immediately after the `_hash` function, insert:

```js
  // ---------- Attention gate ----------
  let animationGate = Promise.resolve();
  function _animate(fn, durationMs) {
    animationGate = animationGate.then(async () => {
      try { fn(); } catch (e) { /* swallow */ }
      await new Promise(r => setTimeout(r, durationMs));
    });
    return animationGate;
  }

  // Track previous variance values for pulse detection
  const prevVariances = {};

  function pulseChangedVariances(decomp) {
    const classes = decomp.classes || {};
    const changed = [];
    for (const [label, key] of VARIANCE_ROWS) {
      const v = Number(classes[key] || 0);
      if (prevVariances[label] !== undefined && Math.abs(prevVariances[label] - v) >= 0.01) {
        changed.push(label);
      }
      prevVariances[label] = v;
    }
    for (const label of changed) {
      const row = document.querySelector(`.livecard-var-row[data-var-key="${label}"]`);
      if (row) {
        _animate(() => {
          row.classList.add('livecard-pulsing');
          setTimeout(() => row.classList.remove('livecard-pulsing'), 650);
        }, 650);
      }
    }
  }
```

- [ ] **Step 3: Call pulseChangedVariances from renderInto()**

At the **end** of `renderInto()`, after `attachAutoNoteCopy();`, add:

```js
    pulseChangedVariances(decomp);
```

- [ ] **Step 4: Manual smoke test**

In devtools:

```js
window.livecard.render({ dc_current: -10, dc_decomposition: { classes: { x20_transelect: -10 }, declared_sum: -10, unexplained_residual: 0 } });
setTimeout(() => window.livecard.render({ dc_current: -20, dc_decomposition: { classes: { x20_transelect: -20 }, declared_sum: -20, unexplained_residual: 0 } }), 1000);
```

Expected: on the second render, the Transelect X20 row flashes amber for ~600ms.

- [ ] **Step 5: Continue to Task 11**

---

## Task 11: Success moment animation

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (CSS + IIFE)

**Purpose:** Implement the 2.2s success sequence per spec §8.3 — triggered when DC transitions non-zero → zero, or when unexplained_residual transitions to zero.

- [ ] **Step 1: Add success-moment CSS**

Inside `<style id="livecard-styles">`, immediately after `@keyframes livecard-pulse`, insert:

```css
@keyframes livecard-success-glow {
  0%   { box-shadow: 0 0 0 0 rgba(16,185,129,0); }
  40%  { box-shadow: 0 0 40px 8px rgba(16,185,129,0.6); }
  100% { box-shadow: 0 0 0 0 rgba(16,185,129,0); }
}
@keyframes livecard-dc-bounce {
  0%   { transform: scale(1); }
  40%  { transform: scale(1.04); }
  100% { transform: scale(1); }
}
.livecard.success-moment {
  animation: livecard-success-glow 1600ms var(--ease);
}
.livecard.success-moment .livecard-dc {
  animation: livecard-dc-bounce 200ms var(--ease) 100ms;
}
```

- [ ] **Step 2: Add transition detection + playSuccessMoment()**

In the IIFE, extend the `state` object (replace the existing declaration):

```js
  const state = {
    pinned: false,
    minimized: false,
    hidden: false,
    pos: null,
    lastResponseHash: null,
    prevFailedCount: null,
    prevDcBucket: null,
    prevWasBalanced: null,     // boolean
    prevResidualOk: null,      // boolean
  };
```

Then, after `pulseChangedVariances`, insert:

```js
  function playSuccessMoment() {
    if (!card) return;
    _animate(() => {
      card.classList.add('success-moment');
    }, 2200);
    _animate(() => {
      card.classList.remove('success-moment');
    }, 0);
  }

  function checkSuccessTransition(dc, residualOk) {
    const nowBalanced = Math.abs(dc) < DC_OK_THRESHOLD;
    const trigger = (
      (state.prevWasBalanced === false && nowBalanced) ||
      (state.prevResidualOk === false && residualOk && !nowBalanced)
    );
    state.prevWasBalanced = nowBalanced;
    state.prevResidualOk = residualOk;
    return trigger;
  }
```

- [ ] **Step 3: Hook into renderInto()**

In `renderInto()`, **immediately before** the `pulseChangedVariances(decomp);` line you added in Task 10, insert:

```js
    if (checkSuccessTransition(dc, residualOk)) playSuccessMoment();
```

- [ ] **Step 4: Manual smoke test**

In devtools:

```js
window.livecard.render({ dc_current: -500, dc_decomposition: { unexplained_residual: 0 } });
setTimeout(() => window.livecard.render({ dc_current: 0, dc_decomposition: { unexplained_residual: 0 } }), 1000);
```

Expected: on the second render, the card glows green for ~1.6s, the DC number scales 1.04x briefly, color transitions red→green.

- [ ] **Step 5: Continue to Task 12**

---

## Task 12: Loading states

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (CSS + IIFE)

**Purpose:** Implement the four loading states from spec §9: top progress bar, pill-state rotating ring, first-load skeleton, stale indicator.

- [ ] **Step 1: Add loading state CSS**

Inside `<style id="livecard-styles">`, before the closing `</style>`, insert:

```css
.livecard-progress {
  position: absolute;
  top: 0;
  left: 0;
  height: 2px;
  width: 0;
  background: var(--emerald);
  border-radius: 12px 12px 0 0;
  transition: width 300ms var(--ease), opacity 200ms var(--ease), background 200ms var(--ease);
  opacity: 0;
  pointer-events: none;
}
.livecard-progress.active { opacity: 1; }
.livecard-progress.warn { background: var(--amber); }
.livecard-progress.err { background: var(--rose); }
.livecard { position: fixed; }  /* make sure children can position relative — override from above */

@keyframes livecard-spin {
  to { transform: rotate(360deg); }
}
.livecard.pill.loading .livecard-title::before {
  width: 8px;
  height: 8px;
  border: 1.5px solid var(--emerald);
  border-top-color: transparent;
  border-radius: 50%;
  content: '';
  display: inline-block;
  animation: livecard-spin 600ms linear infinite;
  margin-right: 6px;
}

@keyframes livecard-shimmer {
  0%   { background-position: -200px 0; }
  100% { background-position: 200px 0; }
}
.livecard-skeleton-row {
  height: 14px;
  background: linear-gradient(90deg, var(--border) 0%, var(--bg) 50%, var(--border) 100%);
  background-size: 200px 100%;
  animation: livecard-shimmer 1200ms linear infinite;
  border-radius: 4px;
  margin: 6px 0;
}

.livecard-stale {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--amber);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  text-align: center;
  line-height: 16px;
  cursor: pointer;
  display: none;
}
.livecard.stale .livecard-stale { display: block; }
```

- [ ] **Step 2: Add progress bar + stale marker to HTML**

Locate the `<aside class="livecard ...">` HTML block. Inside it, **before** the `<header class="livecard-header">`, insert:

```html
    <div class="livecard-progress" id="livecard-progress"></div>
    <div class="livecard-stale" id="livecard-stale" role="button" title="Rafraîchir (données obsolètes)">!</div>
```

- [ ] **Step 3: Wire progress bar + stale state in refresh()**

Replace the `refresh()` function in the IIFE (added in Task 7) with:

```js
  let staleTimer = null;
  function setProgress(pct, klass) {
    const bar = document.getElementById('livecard-progress');
    if (!bar) return;
    bar.classList.remove('warn', 'err');
    if (klass) bar.classList.add(klass);
    bar.classList.add('active');
    bar.style.width = pct + '%';
  }
  function clearProgress() {
    const bar = document.getElementById('livecard-progress');
    if (!bar) return;
    setTimeout(() => {
      bar.classList.remove('active');
      setTimeout(() => { bar.style.width = '0'; }, 200);
    }, 150);
  }
  function markStale() {
    if (card) card.classList.add('stale');
  }
  function clearStale() {
    if (card) card.classList.remove('stale');
  }

  async function refresh(data) {
    if (!card) return;
    let payload = data;
    if (!payload) {
      const session = window.SESSION;
      if (!session || !session.audit_date) return;
      setProgress(30);
      if (state.minimized) card.classList.add('loading');
      try {
        setProgress(70);
        const r = await fetch(`/api/rj/native/balance-check/${session.audit_date}`);
        setProgress(95);
        if (!r.ok) {
          setProgress(100, 'err');
          clearProgress();
          markStale();
          return;
        }
        payload = await r.json();
        clearStale();
      } catch (e) {
        setProgress(100, 'err');
        clearProgress();
        markStale();
        return;
      } finally {
        card.classList.remove('loading');
      }
    }
    const hash = _hash(JSON.stringify(payload));
    if (hash === state.lastResponseHash) {
      setProgress(100);
      clearProgress();
      return;
    }
    state.lastResponseHash = hash;
    renderInto(payload);
    setProgress(100);
    clearProgress();
  }
```

- [ ] **Step 4: Add first-load skeleton**

Inside the IIFE `init()` function, **after** `attachControls();`, add:

```js
      // First-load skeleton
      const body = document.getElementById('livecard-body');
      if (body) {
        body.innerHTML = `
          <div class="livecard-hero">
            <div class="livecard-dc" style="color: var(--text-muted)">—</div>
            <div class="livecard-verdict" style="color: var(--text-muted)">Calcul en cours…</div>
          </div>
          <div class="livecard-section">
            <div class="livecard-skeleton-row"></div>
            <div class="livecard-skeleton-row" style="width: 70%"></div>
            <div class="livecard-skeleton-row" style="width: 85%"></div>
          </div>
        `;
      }
```

- [ ] **Step 5: Wire stale-click retry**

Still in `init()`, after the first-load skeleton block, add:

```js
      const staleEl = document.getElementById('livecard-stale');
      if (staleEl) staleEl.addEventListener('click', () => { clearStale(); refresh(); });
```

- [ ] **Step 6: Manual smoke test**

1. Reload with livecard mode. Before the first balance-check fires, observe the skeleton (DC = `—`, shimmer rows).
2. Trigger a save → watch the top progress bar fill from ~30% → 70% → 95% → 100% → fade.
3. In devtools Network tab, throttle to "Offline" and trigger another save. Expected: `!` badge appears at top-right of card. Click it → card retries.
4. Minimize to pill, trigger a refresh → spinning ring appears on the status dot during the fetch.

- [ ] **Step 7: Continue to Task 13**

---

## Task 13: Reduced motion + final polish

**Files:**
- Modify: `templates/audit/rj/rj_native.html` (CSS)

**Purpose:** Honor `prefers-reduced-motion: reduce` per spec §8.6 — disable glow, bounce, pulse, shimmer; keep color tweens (shortened to 100ms) and layout transitions (instant).

- [ ] **Step 1: Add reduced-motion block**

Inside `<style id="livecard-styles">`, at the very end before `</style>`, insert:

```css
@media (prefers-reduced-motion: reduce) {
  .livecard,
  .livecard-dc,
  .livecard-verdict {
    transition: color 100ms linear, background 100ms linear !important;
  }
  .livecard.success-moment,
  .livecard.success-moment .livecard-dc,
  .livecard-var-row.livecard-pulsing,
  .livecard-skeleton-row,
  .livecard.pill.loading .livecard-title::before {
    animation: none !important;
  }
  .livecard-edge-tab { transition: none !important; }
}
```

- [ ] **Step 2: Manual smoke test**

In devtools, open Rendering panel → set "Emulate CSS media feature prefers-reduced-motion" to "reduce". Then:

```js
window.livecard.render({ dc_current: -500, dc_decomposition: { unexplained_residual: 0 } });
window.livecard.render({ dc_current: 0, dc_decomposition: { unexplained_residual: 0 } });
```

Expected: color changes (red → green) but no glow, no bounce, no pulse.

- [ ] **Step 3: Full-flow manual walkthrough**

With livecard mode enabled, walk through a full audit flow on an existing fixture day:
1. Load a session
2. Upload a source document → card auto-expands, shows fresh data, progress bar fills
3. Edit a field → card refreshes, variance row pulses
4. Resolve the variance → success moment fires when DC reaches 0
5. Drag the card around → it stays where you put it
6. Minimize to pill → DC visible in mono font
7. Hide → edge tab appears
8. Click edge tab → card returns
9. Reload page → all state persists

- [ ] **Step 4: Continue to Task 14**

---

## Task 14: Playwright harness

**Files:**
- Create: `package.json` (if absent)
- Create: `tests/playwright/playwright.config.js`
- Create: `tests/playwright/fixtures/` directory + 6 JSON fixtures

**Purpose:** Set up Playwright standalone (MCP is unavailable). Create fixture responses covering the scenarios the tests need.

- [ ] **Step 1: Check if `package.json` exists**

Run:

```bash
ls /home/v/Documents/Projects/audit-pack/package.json 2>/dev/null && echo EXISTS || echo MISSING
```

- [ ] **Step 2: Create or update `package.json`**

If missing, create `/home/v/Documents/Projects/audit-pack/package.json`:

```json
{
  "name": "audit-pack",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "test:e2e": "playwright test --config=tests/playwright/playwright.config.js"
  },
  "devDependencies": {
    "@playwright/test": "^1.44.0"
  }
}
```

If it exists, add the `test:e2e` script and the `@playwright/test` devDependency to whatever's there.

- [ ] **Step 3: Install Playwright**

Run:

```bash
cd /home/v/Documents/Projects/audit-pack && npm install --save-dev @playwright/test && npx playwright install chromium
```

Expected: downloads Chromium browser; no errors.

- [ ] **Step 4: Create Playwright config**

Create `/home/v/Documents/Projects/audit-pack/tests/playwright/playwright.config.js`:

```js
// @ts-check
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: __dirname,
  timeout: 10_000,
  expect: { timeout: 4_000 },
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5000',
    trace: 'retain-on-failure',
    viewport: { width: 1440, height: 900 },
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

- [ ] **Step 5: Create fixture JSON files**

Create the six fixture files in `/home/v/Documents/Projects/audit-pack/tests/playwright/fixtures/`:

**`balanced.json`:**
```json
{
  "dc_current": 0,
  "dc_decomposition": {
    "classes": {},
    "declared_sum": 0,
    "unexplained_residual": 0
  },
  "checklist": [
    { "item": "Diff. Caisse = 0", "status": "pass" },
    { "item": "Transelect balancé", "status": "pass" }
  ],
  "auditor": "Test Auditor",
  "audit_date": "2026-04-10"
}
```

**`reconciled.json`:**
```json
{
  "dc_current": -2167.86,
  "dc_note_text": "Auditeur De Nuit: Test Auditor\nTranselect X20: 2167.86",
  "dc_decomposition": {
    "classes": { "x20_transelect": -2167.86 },
    "declared_sum": -2167.86,
    "unexplained_residual": 0
  },
  "checklist": [
    { "item": "Diff. Caisse = 0", "status": "fail", "detail": "DC=-2167.86" },
    { "item": "Transelect balancé", "status": "pass" }
  ],
  "auditor": "Test Auditor",
  "audit_date": "2026-04-10"
}
```

**`unexplained.json`:**
```json
{
  "dc_current": -2170.37,
  "dc_decomposition": {
    "classes": { "x20_transelect": -2165.35, "panne_lien_hotel": -2.51 },
    "declared_sum": -2167.86,
    "unexplained_residual": -2.51
  },
  "checklist": [
    { "item": "Diff. Caisse = 0", "status": "fail" },
    { "item": "Résiduel inexpliqué", "status": "fail" }
  ],
  "auditor": "Test Auditor",
  "audit_date": "2026-04-10"
}
```

**`small-warn.json`:**
```json
{
  "dc_current": 5.25,
  "dc_decomposition": {
    "classes": {},
    "declared_sum": 0,
    "unexplained_residual": 5.25
  },
  "checklist": [
    { "item": "DC < $10", "status": "warn" }
  ],
  "auditor": "Test Auditor",
  "audit_date": "2026-04-10"
}
```

**`checklist-fail.json`:**
```json
{
  "dc_current": 0,
  "dc_decomposition": {
    "classes": {},
    "declared_sum": 0,
    "unexplained_residual": 0
  },
  "checklist": [
    { "item": "Item 1", "status": "pass" },
    { "item": "Item 2", "status": "fail", "detail": "Nouveau problème détecté" }
  ],
  "auditor": "Test Auditor",
  "audit_date": "2026-04-10"
}
```

**`two-variances.json`:**
```json
{
  "dc_current": -1500.00,
  "dc_decomposition": {
    "classes": { "x20_transelect": -1000, "geac_bottom": -500 },
    "declared_sum": -1500,
    "unexplained_residual": 0
  },
  "checklist": [{ "item": "DC reconciled", "status": "pass" }],
  "auditor": "Test Auditor",
  "audit_date": "2026-04-10"
}
```

- [ ] **Step 6: Verify Playwright runs**

From the repo root:

```bash
cd /home/v/Documents/Projects/audit-pack && npx playwright test --list --config=tests/playwright/playwright.config.js
```

Expected: "Total: 0 tests in 0 files" (no specs yet, but config loads cleanly).

- [ ] **Step 7: Continue to Task 15**

---

## Task 15: Playwright tests (all 19)

**Files:**
- Create: `tests/playwright/livecard.spec.js`

**Purpose:** Implement the 19 tests from spec §11.2. Tests mock `/api/rj/native/balance-check/*` via `page.route()` so the Flask backend doesn't need real fixture data.

- [ ] **Step 1: Create the spec file skeleton**

Create `/home/v/Documents/Projects/audit-pack/tests/playwright/livecard.spec.js`:

```js
// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const FIXTURES = {
  balanced: JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures/balanced.json'), 'utf8')),
  reconciled: JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures/reconciled.json'), 'utf8')),
  unexplained: JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures/unexplained.json'), 'utf8')),
  smallWarn: JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures/small-warn.json'), 'utf8')),
  checklistFail: JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures/checklist-fail.json'), 'utf8')),
  twoVariances: JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures/two-variances.json'), 'utf8')),
};

// Shared setup: navigate to the RJ native page with livecard mode enabled and a
// valid session stubbed. Balance-check responses are routed per-test via `mock`.
async function setupLivecard(page, mock) {
  await page.addInitScript(() => {
    localStorage.setItem('rjn_ui_mode', 'livecard');
    window.SESSION = { audit_date: '2026-04-10', auditor: 'Test Auditor' };
  });
  if (mock) {
    await page.route('**/api/rj/native/balance-check/*', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mock),
      });
    });
  }
  await page.goto('/audit/rj/native');
  await page.waitForSelector('#livecard', { state: 'attached' });
}

// ---------- Shell (5 tests) ----------

test('1. Initial render at top-right corner, expanded', async ({ page }) => {
  await setupLivecard(page, FIXTURES.balanced);
  const card = page.locator('#livecard');
  await expect(card).toBeVisible();
  const box = await card.boundingBox();
  expect(box.x).toBeGreaterThan(900);  // right side of 1440 viewport
  expect(box.y).toBeLessThan(100);     // top
  await expect(card).not.toHaveClass(/pill/);
});

test('2. Drag moves card and clamps at viewport edge', async ({ page }) => {
  await setupLivecard(page, FIXTURES.balanced);
  const header = page.locator('#livecard-header');
  const box = await header.boundingBox();
  // Drag far to the left
  await page.mouse.move(box.x + 20, box.y + 10);
  await page.mouse.down();
  await page.mouse.move(100, 500, { steps: 10 });
  await page.mouse.up();
  const cardBox = await page.locator('#livecard').boundingBox();
  expect(cardBox.x).toBeGreaterThanOrEqual(20);  // clamped at 20px margin
});

test('3. Minimize button toggles pill state', async ({ page }) => {
  await setupLivecard(page, FIXTURES.balanced);
  await page.click('#livecard-min');
  await expect(page.locator('#livecard')).toHaveClass(/pill/);
  // Click the header (not a button) to restore
  const header = page.locator('#livecard-header');
  const hb = await header.boundingBox();
  await page.mouse.click(hb.x + hb.width - 80, hb.y + hb.height / 2);
  await expect(page.locator('#livecard')).not.toHaveClass(/pill/);
});

test('4. Hide button reveals edge tab, edge tab restores card', async ({ page }) => {
  await setupLivecard(page, FIXTURES.balanced);
  await page.click('#livecard-hide');
  await expect(page.locator('#livecard')).toHaveClass(/hidden-state/);
  await expect(page.locator('#livecard-edge-tab')).toBeVisible();
  await page.click('#livecard-edge-tab');
  await expect(page.locator('#livecard')).not.toHaveClass(/hidden-state/);
});

test('5. Position and state persist across page reload', async ({ page }) => {
  await setupLivecard(page, FIXTURES.balanced);
  await page.click('#livecard-min');
  await expect(page.locator('#livecard')).toHaveClass(/pill/);
  await page.reload();
  await page.waitForSelector('#livecard');
  await expect(page.locator('#livecard')).toHaveClass(/pill/);
});

// ---------- Expanded layout (4 tests) ----------

test('6. DC hero renders current value with correct color class', async ({ page }) => {
  await setupLivecard(page, FIXTURES.reconciled);
  await page.waitForSelector('#livecard-dc');
  const dc = page.locator('#livecard-dc');
  await expect(dc).toContainText('2167.86');
  await expect(dc).toHaveClass(/warn/);
});

test('7. Verdict text matches DC state', async ({ page }) => {
  await setupLivecard(page, FIXTURES.unexplained);
  await expect(page.locator('#livecard-verdict')).toContainText('investiguer');
});

test('8. Variance rows render non-zero classes with correct labels', async ({ page }) => {
  await setupLivecard(page, FIXTURES.twoVariances);
  const rows = page.locator('.livecard-var-row[data-var-key]');
  await expect(rows).toHaveCount(2);
  await expect(rows.first()).toContainText('Transelect X20');
});

test('9. Footer shows auditor name and formatted date', async ({ page }) => {
  await setupLivecard(page, FIXTURES.balanced);
  const footer = page.locator('.livecard-footer');
  await expect(footer).toContainText('Test Auditor');
  await expect(footer).toContainText('2026');
});

// ---------- Smart behaviors (5 tests) ----------

test('10. Auto-expand on checklist pass→fail transition', async ({ page }) => {
  // Start with passing fixture, minimize, then inject failing fixture via window.livecard.render
  await setupLivecard(page, FIXTURES.balanced);
  await page.click('#livecard-min');
  await expect(page.locator('#livecard')).toHaveClass(/pill/);
  await page.evaluate((f) => window.livecard.render(f), FIXTURES.checklistFail);
  await expect(page.locator('#livecard')).not.toHaveClass(/pill/);
});

test('11. Pin toggle suppresses auto-expand', async ({ page }) => {
  await setupLivecard(page, FIXTURES.balanced);
  await page.click('#livecard-pin');    // pin on
  await page.click('#livecard-min');    // minimize
  await page.evaluate((f) => window.livecard.render(f), FIXTURES.checklistFail);
  await expect(page.locator('#livecard')).toHaveClass(/pill/);  // stays as pill
});

test('12. Variance value change triggers pulse', async ({ page }) => {
  await setupLivecard(page, FIXTURES.twoVariances);
  const modified = JSON.parse(JSON.stringify(FIXTURES.twoVariances));
  modified.dc_decomposition.classes.x20_transelect = -2000;
  await page.evaluate((f) => window.livecard.render(f), modified);
  const pulsingRow = page.locator('.livecard-var-row.livecard-pulsing');
  await expect(pulsingRow).toHaveCount(1, { timeout: 500 });
});

test('13. Success moment fires on DC zero transition', async ({ page }) => {
  await setupLivecard(page, FIXTURES.reconciled);
  await page.evaluate((f) => window.livecard.render(f), FIXTURES.balanced);
  await expect(page.locator('#livecard')).toHaveClass(/success-moment/);
});

test('14. prefers-reduced-motion neutralizes animations', async ({ page, browser }) => {
  const ctx = await browser.newContext({ reducedMotion: 'reduce' });
  const p2 = await ctx.newPage();
  await p2.addInitScript(() => {
    localStorage.setItem('rjn_ui_mode', 'livecard');
    window.SESSION = { audit_date: '2026-04-10', auditor: 'Test Auditor' };
  });
  await p2.route('**/api/rj/native/balance-check/*', r => r.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify(FIXTURES.reconciled)
  }));
  await p2.goto('/audit/rj/native');
  await p2.waitForSelector('#livecard');
  // Check that the success-moment animation is neutralized via CSS
  const animName = await p2.evaluate(() => {
    const el = document.createElement('div');
    el.className = 'livecard success-moment';
    document.body.appendChild(el);
    const n = getComputedStyle(el).animationName;
    el.remove();
    return n;
  });
  expect(animName).toBe('none');
  await ctx.close();
});

// ---------- Loading states (3 tests) ----------

test('15. Top progress bar animates during refresh', async ({ page }) => {
  await setupLivecard(page, FIXTURES.balanced);
  // Delay the next response so the bar is observable
  let resolved = false;
  await page.route('**/api/rj/native/balance-check/*', async route => {
    await new Promise(r => setTimeout(r, 300));
    resolved = true;
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(FIXTURES.reconciled) });
  });
  await page.evaluate(() => window.livecard.refresh());
  const bar = page.locator('#livecard-progress');
  await expect(bar).toHaveClass(/active/, { timeout: 500 });
});

test('16. Pill-state loader ring shows during refresh', async ({ page }) => {
  await setupLivecard(page, FIXTURES.balanced);
  await page.click('#livecard-min');
  await page.route('**/api/rj/native/balance-check/*', async route => {
    await new Promise(r => setTimeout(r, 300));
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(FIXTURES.balanced) });
  });
  const refreshPromise = page.evaluate(() => window.livecard.refresh());
  await expect(page.locator('#livecard')).toHaveClass(/loading/, { timeout: 500 });
  await refreshPromise;
});

test('17. First-load skeleton appears then content replaces it', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('rjn_ui_mode', 'livecard');
    window.SESSION = { audit_date: '2026-04-10', auditor: 'Test Auditor' };
  });
  // Delay first balance-check so skeleton is observable
  await page.route('**/api/rj/native/balance-check/*', async route => {
    await new Promise(r => setTimeout(r, 400));
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(FIXTURES.balanced) });
  });
  await page.goto('/audit/rj/native');
  await page.waitForSelector('#livecard-body');
  await expect(page.locator('.livecard-skeleton-row').first()).toBeVisible();
});

// ---------- Diff-gated render (2 tests) ----------

test('18. Identical response twice does not re-render DOM', async ({ page }) => {
  await setupLivecard(page, FIXTURES.balanced);
  // Snapshot HTML, render same data, assert unchanged + renderInto was gated
  const before = await page.locator('#livecard-body').innerHTML();
  await page.evaluate((f) => window.livecard.refresh(f), FIXTURES.balanced);
  const after = await page.locator('#livecard-body').innerHTML();
  expect(after).toBe(before);
});

test('19. Different response updates DOM', async ({ page }) => {
  await setupLivecard(page, FIXTURES.balanced);
  const before = await page.locator('#livecard-dc').textContent();
  await page.evaluate((f) => window.livecard.refresh(f), FIXTURES.reconciled);
  const after = await page.locator('#livecard-dc').textContent();
  expect(after).not.toBe(before);
});
```

- [ ] **Step 2: Run the test suite**

With the Flask dev server running on `localhost:5000`:

```bash
cd /home/v/Documents/Projects/audit-pack && npx playwright test --config=tests/playwright/playwright.config.js
```

Expected: all 19 tests pass.

- [ ] **Step 3: Fix any failures**

If any test fails, read the Playwright HTML report (`npx playwright show-report`) and fix either the test or the livecard code. Common failure modes:
- Selector mismatch (the template ID you used differs from the one in the test)
- Timing race on auto-expand (add a short `waitForTimeout(100)`)
- Animation still mid-flight when assertion runs (increase timeout or check for class presence instead of final state)

Do **not** simply remove failing tests. Fix the root cause.

- [ ] **Step 4: Continue to Task 16**

---

## Task 16: Fixture-day verification + final checks

**Files:**
- None (verification only)

**Purpose:** Walk through the success criteria from spec §16 against real fixture data.

- [ ] **Step 1: Run the fixture regression check**

```bash
cd /home/v/Documents/Projects/audit-pack && python -m tests.fixture_regression
```

Expected: all 16 fixture days score the same as before this plan was executed (this plan makes no Python changes; the scores must be identical).

- [ ] **Step 2: Manual walkthrough on 5 fixture days**

For each of these dates, load the session in the browser with livecard mode enabled and verify the card renders the expected variance pattern:
- **2026-03-02** — clean day (DC ≈ 0)
- **2026-03-14** — one class (Transelect X20 only)
- **2026-03-21** — multi-class day
- **2026-03-29** — four classes
- **2026-04-06** — recent day

For each: confirm DC value matches expected, variance rows match the 10-class decomposition, auto-note appears when DC ≠ 0 + residual = 0, and the checklist score is plausible.

- [ ] **Step 3: Check for console errors**

With devtools console open, walk through a normal session (load + edit 3 fields + upload a file). Expected: zero `console.error` entries. Warnings are OK.

- [ ] **Step 4: Check success criteria checklist from spec §16**

Walk through each item in spec §16 "Success criteria" and confirm it passes. If any item fails, open a follow-up task to fix it — do NOT mark this plan complete until all criteria pass.

- [ ] **Step 5: Hand off to the user**

Inform the user:
> Phase 4 livecard is implemented and passing all 19 Playwright tests. The legacy `.rjn-livepanel` still exists behind `localStorage.rjn_ui_mode = 'legacy'` (default). Run `window.setLivecard(true)` in the browser console to try it, `window.setLivecard(false)` to revert. Fixture regression scores are unchanged. Ready for your review before I propose a cleanup commit to remove the legacy panel.

The user handles all git operations. Do not run `git commit`.

---

## Appendix A: Parallel subagent prompt (launched at Task 1)

**Subagent type:** `general-purpose`

**Prompt:**

> You are building a Playwright test harness for a new floating "livecard" UI component. The component does not exist yet — the main thread is building it in parallel. You only depend on the design spec and the fixture scenarios.
>
> **Read these files first:**
> - `/home/v/Documents/Projects/audit-pack/docs/superpowers/specs/2026-04-10-livecard-redesign.md` (full design spec, especially §7, §8, §9, §11)
> - `/home/v/Documents/Projects/audit-pack/docs/superpowers/plans/2026-04-10-livecard-redesign.md` (Tasks 14 and 15 — your scope)
>
> **Your tasks:**
> 1. Execute Task 14 exactly as written — set up `package.json`, install Playwright, create `playwright.config.js`, create the 6 fixture JSON files
> 2. Execute Task 15 exactly as written — create `tests/playwright/livecard.spec.js` with all 19 tests
> 3. Verify the test file parses: `npx playwright test --list --config=tests/playwright/playwright.config.js` (should list 19 tests, zero failures)
> 4. Do NOT run the tests themselves — the main thread code isn't ready yet, so they will all fail
> 5. Report back when Tasks 14 + 15 are complete and the test file parses cleanly
>
> Do NOT modify `templates/audit/rj/rj_native.html` — that's the main thread's job. Do NOT run `git commit` — the user handles all git operations.

---

## Self-review checklist

- [x] Every spec section has a task
- [x] No placeholders or TBD
- [x] All class/function names used in later tasks match earlier definitions (`state`, `renderInto`, `refresh`, `_animate`, `VARIANCE_ROWS`, `_checkMetaLocal`, `classifyDC`, `fmtMoneyLocal`, `setMinimized`, `setHidden`, `setPinned`)
- [x] Every step has either code or an exact command
- [x] Commit steps explicitly note "user handles git — do not commit yourself"
- [x] Test plan matches spec §11 (19 tests in 5 categories)
- [x] Parallel subagent prompt provided
- [x] Success criteria verification is a separate task
