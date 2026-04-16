# Livecard redesign — Phase 4 design spec

**Date**: 2026-04-10
**Author**: night-audit webapp team
**Status**: Design approved, awaiting writing-plans handoff
**Parent**: `docs/WIRING_PLAN.md` §8 (Phase 4 frontend polish)

---

## 1. Purpose

Replace the Phase 1 `.rjn-livepanel` static sidebar with a floating, draggable "livecard" that serves as the night auditor's always-visible status companion. The card must feel fast, authoritative, and calm at 3am.

This is frontend polish only. No backend changes. No new Python modules. No new data contracts. The `check_balance` API response shape (Phase 1-3) is exactly what the new card consumes.

## 2. Goals

1. **Beautiful and information-dense without feeling busy** — Linear/Stripe dashboard aesthetic.
2. **Floating + draggable** — auditor controls where the card lives on screen.
3. **Three states** — expanded, pill, hidden (edge tab), with smart transitions between them.
4. **Instant visual answer** to "am I done?" via a dominant DC hero + verdict text.
5. **Safe migration** — new card and old panel coexist behind a localStorage toggle until verified.
6. **Comprehensive Playwright test coverage** — ~19 tests for shell, layout, behaviors, loading, diff-gated render.

## 3. Non-goals

- No backend changes
- No new fonts beyond the already-loaded Inter + JetBrains Mono
- No tabbed content in the expanded state (sections are always visible or auto-hidden)
- No keyboard shortcuts for minimize/expand (can add later if requested)
- No drag-to-snap-to-corner (free-form drag only)
- No multiple floating cards (single instance only)
- No sound effects
- No confetti, no decorative gradients, no purple anywhere

## 4. Brainstorm decisions (locked)

| Decision | Choice |
|---|---|
| Scope | C — focused live-panel redesign, everything else stays |
| Aesthetic lineage | 2 — Linear/Stripe (modern SaaS, whitespace, elegant sans-serif) |
| Visual hierarchy | A+B — DC number dominates, verdict text below |
| Shell | D — floating draggable card with minimized pill + hidden edge tab |
| Transition triggers | C — smart reactions (no auto-hide on idle) |
| Pill content | B+D — DC + verdict icon base state + success morph on day balanced |
| Expanded density | B — smart sections that auto-expand based on state |
| Hide behavior | A — full hide with always-visible 8px right-edge tab |
| Migration | Safe coexistence — old panel + new card both in DOM, toggled via localStorage |

## 5. Architecture

### 5.1 DOM structure

Single `<aside class="livecard" id="livecard">` placed right after the toolbar in `templates/audit/rj/rj_native.html`. Sibling: `<div class="livecard-edge-tab" id="livecard-edge-tab">` for the hidden state.

Three mutually-exclusive modes via class on the root element:
- `.livecard.mode-expanded` (default)
- `.livecard.mode-pill`
- `.livecard.mode-hidden` (shows edge tab, hides main card)

### 5.2 State shape

```js
state = {
  el, pillEl, edgeTabEl,        // DOM refs
  mode: 'expanded',              // 'expanded' | 'pill' | 'hidden'
  pinned: false,                 // prevents auto-expand on variance changes
  position: {x: null, y: null},  // null = default (top-right)
  lastResponseHash: null,        // for diff-gated render
  animationGate: Promise.resolve(),  // serializes animation sequences
  refreshTimer: null,            // debounce handle
  lastBalanceCheck: null,        // latest response cached for re-render
}
```

Persisted in `localStorage.rjn_livecard_state` as `{mode, pinned, position}`. Restored on init; clamped to viewport if the saved position is off-screen.

### 5.3 Public API

```js
window.livecard = {
  init(),                    // mounts the card, wires handlers, restores state
  refresh(),                 // fetches /api/rj/native/balance-check and re-renders (debounced 300ms)
  onUploadSuccess(result),   // hook called from upload handler — triggers cascade animation
  setMode('expanded' | 'pill' | 'hidden'),
}
```

No other exports. Implementation is a single IIFE with all helpers in closure.

### 5.4 Integration with existing code

- Replace the 4 call sites of `refreshChecklist()` with `window.livecard.refresh()`
- Upload handler calls `window.livecard.onUploadSuccess(result)` after a successful `/api/rj/native/upload-file` response
- No other changes to existing JS

## 6. The shell

### 6.1 Expanded card

- **Dimensions**: 380px wide, content-sized height, min 320px, max 80vh (scrollable on overflow)
- **Border radius**: 14px
- **Shadow**: `0 20px 50px -12px rgba(0,0,0,0.25), 0 8px 16px -8px rgba(0,0,0,0.15)` (Linear/Stripe floating-surface style)
- **Border**: 1px subtle in light, slightly stronger in dark
- **Position**: `fixed`, top-right corner by default (top: 20px, right: 20px)
- **z-index**: 60 (above page, below modals at 100)

### 6.2 Header / drag handle

- 40px tall row at the top of the expanded card
- Cursor: `grab` → `grabbing` during drag
- Contents (left to right): drag dots icon · pin toggle · minimize button · hide button
- Pin toggle icon filled when pinned (auto-expand suppressed)

### 6.3 Drag behavior

- Free-form, no snapping
- Edge-clamped: 20px minimum margin from any viewport edge
- Drag state stored in `state.position` and persisted on drag end
- Click (no movement) on drag handle does nothing; click on minimize/hide buttons triggers transitions
- When in pill state, the entire pill is the drag handle

### 6.4 Pill (minimized state)

- **Dimensions**: 190×44px, 18px border-radius
- **Contents** (left to right): status dot (8px) · DC value (JetBrains Mono 16px 700) · verdict icon (13px `✓` / `!` / `?`)
- **Background**: color-coded (`--emerald-bg` / `--amber-bg` / `--rose-bg`)
- **Hover**: `translateY(-1px)` + deeper shadow
- **Click**: expand to last known position

### 6.5 Hidden state + edge tab

- Card fully removed from visible flow
- `<div class="livecard-edge-tab">` appears: 8px wide, 48px tall, glued to right edge of viewport at 50% vertical
- Color-coded by current DC status
- Click → card reappears at last-known position, state becomes whatever it was before hiding (pill or expanded)

## 7. Expanded layout

### 7.1 Typography scale (all px)

| Element | Size | Weight | Family | Notes |
|---|---|---|---|---|
| DC hero | 34 | 700 | JetBrains Mono | `tabular-nums`, color-animated |
| Verdict text | 13 | 600 | Inter | Letter-spacing +0.5 |
| Section header | 10.5 | 700 | Inter | Uppercase, letter-spacing +0.8, `--text-muted` |
| Variance label | 12.5 | 500 | Inter | |
| Variance value | 13 | 700 | JetBrains Mono | `tabular-nums` |
| Checklist item | 11.5 | 500 | Inter | line-height 1.35 |
| Auto-note body | 10.5 | 400 | JetBrains Mono | line-height 1.4, `--text-sec` |
| Footer metadata | 10 | 500 | Inter | `--text-muted` |

### 7.2 Visual hierarchy (ASCII mockup)

```
┌──────────────────────────────────────────────┐
│ ⋮⋮⋮           📌 PIN         −   ×          │ ← 40px drag header
├──────────────────────────────────────────────┤
│                                              │
│        DIFFÉRENCE DE CAISSE                  │ ← section header, centered
│             −1 694,15 $                      │ ← DC hero, 34px mono, color-tweened
│          À réconcilier  !                    │ ← verdict, 13px
│                                              │
├──────────────────────────────────────────────┤
│  VARIANCES DÉCLARÉES              3 actives  │
│  Transelect X20            −82,46 $          │
│  GEAC col 41            −1 577,95 $          │
│  Chambres annuler          −33,74 $          │
│                            ────────          │
│  Somme expliquée        −1 694,15 $          │
│  Résiduel                    0,00 $  ✓       │ ← green if matches
│                                              │
├──────────────────────────────────────────────┤
│  CHECKLIST 21 POINTS              18/21 ✓    │
│  ✓ 17 réussis  !  3 échecs  ⊘  1 N/A         │
│  [ Voir détails ↓ ]                          │
│                                              │
├──────────────────────────────────────────────┤
│  NOTE AUTO-GÉNÉRÉE        📋 Copier          │ ← only shown when note exists
│  ┌────────────────────────────────────────┐ │
│  │ Souleymane Camara:                     │ │
│  │ TRANSELECT: 82.46                      │ │
│  │ GEAC: 1577.95                          │ │
│  │ CHAMBRES ANNULER: 33.74                │ │
│  └────────────────────────────────────────┘ │
│  À coller dans le commentaire col C          │
│  après l'export Excel.                       │
│                                              │
├──────────────────────────────────────────────┤
│  Souleymane Camara  ·  6 avr. 2026           │ ← footer, 10px muted
└──────────────────────────────────────────────┘
```

### 7.3 Spacing rhythm

- Outer padding: 16px horizontal, 14px vertical
- Section gap: 18px between sections
- Section inner gap: 10px between header and content
- Variance/checklist row gap: 6px
- 1px `--border` dividers between sections (barely-visible in dark)

### 7.4 Color semantics

- **Balanced** (DC = 0): DC in `--emerald`, verdict "Équilibré ✓" in emerald
- **Reconcilable** (DC ≠ 0 but residual = 0): DC in `--amber`, verdict "Réconcilié" in amber
- **Unexplained** (residual ≠ 0): DC in `--rose`, verdict "À investiguer" in rose, Résiduel row highlighted
- All transitions are color tweens (not instant swaps)
- Zero gradients, zero purple

### 7.5 Section auto-hide rules

- **Variances section**: hidden when no non-zero classes exist
- **Checklist section**: always visible (default collapsed summary)
- **Auto-note section**: shown only when `DC ≥ 0.16` AND `residual < 0.16` AND variance list is non-empty
- **Footer**: always visible

## 8. Smart behaviors

### 8.1 Auto-expand triggers (from pill → expanded)

- Checklist item flips from pass → fail (new problem)
- DC magnitude crosses the `|DC| < 10` → `|DC| ≥ 10` threshold (meaningful change, only the first crossing)
- Upload rejected with date-mismatch error
- Success moment (special case — may animate from pill state)

Auto-expand is **suppressed by the pin toggle** (except for success moment).

Auto-expand is **never triggered from hidden state**. The edge tab changes color instead.

### 8.2 Pulse for attention (pill stays pill, but draws the eye)

- Variance row value changed → single 600ms CSS ring pulse
- Checklist score dropped by 1+ → single pulse
- Pulses are color-coded (amber for new variance, red for unexplained residual)

### 8.3 The success moment

Trigger: DC transitions from non-zero to zero, OR unexplained_residual transitions to zero.

Total duration: 2.2s (panel) + 1.5s (pill morph if applicable).

Sequence:
1. **0ms** — color tween red/amber → green, 400ms ease-out
2. **100ms** — DC number 1.04x scale bounce, 200ms spring, back to 1x
3. **200ms** — radial green glow fades in, peaks at 400ms (0.6 opacity)
4. **400ms** — verdict text slides up + fades out, 200ms
5. **500ms** — new "Équilibré ✓" slides up + fades in, 300ms
6. **800ms** — glow fades out, 800ms
7. **1.0s** — if card is in pill state, pill morphs to 240×48 "✓ Équilibré" chip
8. **2.5s** — pill reverts to normal DC display

Implementation: single CSS class `.success-moment` applied to root; all timing encoded in CSS animations. One `setTimeout(2500)` to remove the class.

### 8.4 Row-level micro-animations

- Variance row value change → `data-just-updated="true"` attribute for 400ms, CSS flashes background + scales value
- Checklist item pass → fail → red left-border slides in over 300ms
- Checklist item fail → pass → green left-border appears, holds 1s, fades

### 8.5 Attention gate

A single promise-queue serializes animations to enforce "at most one element moves at a time":

```js
state.animationGate = Promise.resolve();
function _animate(fn, durationMs) {
  state.animationGate = state.animationGate.then(async () => {
    fn();
    await new Promise(r => setTimeout(r, durationMs));
  });
}
```

Priority (higher blocks lower):
1. Success moment (blocks all for 2.5s)
2. Auto-expand from pill (blocks row pulses for 400ms)
3. Row-level pulse
4. Checklist item transition

### 8.6 Reduced motion

`@media (prefers-reduced-motion: reduce)`:
- Disables: success glow, scale bounce, row flash, pulse rings
- Keeps: color tweens (but 100ms instead of 400ms), auto-expand (instant, no slide)
- Keeps: all toasts and notifications

## 9. Loading states

### 9.1 Top progress bar

2px line inside the card's top border-radius. States:

| State | Width | Behavior |
|---|---|---|
| Idle | 0 | Hidden |
| Pending save (debounce) | 30% | Slides in from left |
| Save in flight | 70% | Grows |
| Balance-check in flight | 95% | Grows |
| Done | 100% | Holds 150ms then fades 200ms |
| Error | — | Flashes `--rose` before fading |

Color matches DC status (green/amber/rose).

### 9.2 Pill-state loader

When card is in pill state and a refresh is in flight:
- Status dot on the left gains a 1px outline ring that rotates once (600ms/rev)
- Stops when the refresh completes

### 9.3 First-load skeleton

Before the first `balance-check` response arrives:
- DC hero shows `—`
- 3 greyed placeholder variance rows with CSS shimmer (gradient sweep, 1.2s loop)
- Verdict text shows "Calcul en cours…" in `--text-muted`
- Real content fades in when the response arrives

### 9.4 Stale indicator

If the balance-check request fails or times out:
- `!` badge in the top-right corner of the DC hero
- Tooltip: "Dernière mise à jour: il y a 12s"
- Previous numeric values retained (not cleared)
- Click the badge → manual retry

## 10. Technical implementation

### 10.1 File layout

All changes in a single file: **`templates/audit/rj/rj_native.html`**.

- New CSS block `<style id="livecard-styles">` added inside `{% block head %}` (~200-260 lines)
- New HTML `<aside class="livecard">` + `<div class="livecard-edge-tab">` added after the toolbar (~60 lines)
- New JS block inside `<script>` near the other refresh helpers (~400-500 lines)

### 10.2 CSS architecture

- All class names prefixed with `.livecard` (no clashes with existing `.rjn-*`)
- Uses existing CSS variables (`--emerald`, `--rose`, `--amber`, `--card`, `--border`, `--mono`, `--ease`, etc.)
- No new design tokens
- Three `@keyframes` sets: `livecard-success-glow`, `livecard-pulse`, `livecard-shimmer`
- `@media (prefers-reduced-motion: reduce)` block at the end disables motion

### 10.3 JS architecture

Single IIFE, closure-scoped state, 5 public methods (`init`, `refresh`, `onUploadSuccess`, `setMode`, `render`).

Private helpers: `_attachDrag`, `_loadState`, `_saveState`, `_hash`, `_animate`, `_diffRender`, `_playSuccessMoment`.

### 10.4 Diff-gated render

Before rewriting the DOM, compute a lightweight hash of the new response (`JSON.stringify(response)` then FNV-1a hash or similar). If identical to `state.lastResponseHash`, skip the render entirely. Eliminates no-op DOM churn (the Phase 1 simplify agent flagged this as "defer until we see jank" — Phase 4 addresses it).

### 10.5 Safe migration strategy

**Both panels exist in the DOM simultaneously.**

- Old `.rjn-livepanel` kept as-is (hidden via `.livecard-legacy--hidden` when `localStorage.rjn_ui_mode === 'livecard'`)
- New `.livecard` hidden by default (`.livecard--hidden-by-default` removed when mode is 'livecard')
- Toggle via a small helper exposed on `window`:

```js
window.setLivecard = function(enabled) {
  localStorage.setItem('rjn_ui_mode', enabled ? 'livecard' : 'legacy');
  location.reload();
}
```

- During development: `window.setLivecard(true)` to preview, `window.setLivecard(false)` to revert
- Refresh hook: `refreshChecklist()` checks the mode and dispatches to either the old renderer or `window.livecard.refresh()`
- Once verified against all fixture days + approved, a follow-up commit removes the old panel and the toggle

### 10.6 Integration hooks

Modified in the existing template JS (minimal edits):

1. Upload handler (`file-report-upload` change event): after `loadSessionToForm(SESSION)`, call `window.livecard.onUploadSuccess(d)` in addition to `refreshChecklist()`
2. `saveSection()` completion: call `refreshChecklist()` as before — internally this dispatches to `window.livecard.refresh()` when mode is `livecard`
3. `startSession()` after session created: call `refreshChecklist()` as before (same dispatch)

No other integration work. The existing code paths remain intact.

## 11. Testing plan

### 11.1 Test coverage target

~19 Playwright tests covering five categories. Test file location: **`tests/playwright/livecard.spec.js`**.

### 11.2 Test categories

**Shell (5 tests)**
1. Initial load renders card in top-right corner at default position, expanded
2. Drag moves card to arbitrary position; edge clamping enforces 20px margin
3. Minimize button → pill state; click pill → expanded at last position
4. Hide button → edge tab appears on right edge; click edge tab → card reappears
5. `localStorage` persistence: position + mode survive `page.reload()`

**Expanded layout (4 tests)**
6. DC hero renders current value with correct color class
7. Verdict text matches DC state (balanced / reconcilable / unexplained)
8. Variance rows render one-per-non-zero-class with correct labels + values
9. Footer metadata shows auditor name + formatted date

**Smart behaviors (5 tests)**
10. Auto-expand on checklist pass→fail transition
11. Pin toggle on → auto-expand suppressed
12. Pill pulse on variance value change (`.pulse` class applied briefly)
13. Success moment: mocked DC=0 transition, verify `.success-moment` class for ~2.2s
14. `prefers-reduced-motion` → motion classes neutralized

**Loading states (3 tests)**
15. Top progress bar appears during `refresh()`, fills, fades
16. Pill-state loader ring rotates during refresh
17. First-load skeleton → real content fade-in

**Diff-gated render (2 tests)**
18. Identical response twice → no DOM mutation (MutationObserver or innerHTML fingerprint)
19. Different response → DOM updated

### 11.3 Test implementation notes

- Tests mock `/api/rj/native/balance-check/*` via `page.route()`
- Fixtures: one response per scenario stored as JSON in `tests/playwright/fixtures/`
- Tests run headless via `npx playwright test`
- The Playwright MCP is currently `✘ failed`; tests are written as standalone `.spec.js` files that can run via `npx playwright test` directly, independent of the MCP
- No Flask backend required during test runs

### 11.4 Parallel execution plan

During implementation:

- **Main thread**: writes `livecard` CSS + HTML + JS via the `frontend-design` skill
- **Background subagent**: writes the Playwright test suite (all 19 tests) using mocked responses
- **Final step**: main thread integrates, runs `npx playwright test`, fixes any failures

The two streams are fully independent — tests only depend on the design spec, not on the main-thread code.

## 12. Files touched

| File | Scope | Lines est. |
|---|---|---|
| `templates/audit/rj/rj_native.html` | Add new CSS + HTML + JS for livecard, add localStorage toggle helper | +700 |
| `tests/playwright/livecard.spec.js` | New test suite | +600 |
| `tests/playwright/fixtures/*.json` | Mocked balance-check responses | ~10 files, 200 total |
| `package.json` (if absent) | Add `@playwright/test` as devDep | +5 |

Existing `.rjn-livepanel` code remains untouched until post-verification cleanup commit.

## 13. YAGNI — explicit exclusions

- Keyboard shortcuts for mode toggle (can add later on request)
- Drag-to-snap-to-corner (user chose free-form)
- Multiple floating cards
- Sound effects
- Custom animation library (pure CSS transitions + small `animationGate`)
- New web fonts (Inter + JetBrains Mono already loaded)
- Any redesign of tabs, forms, or non-livecard chrome
- i18n abstraction (app is French-only)
- Unit tests for JS (no JS test framework in project; only E2E tests added)
- Removing the legacy `.rjn-livepanel` (deferred to a separate cleanup commit)

## 14. Risks + mitigations

| Risk | Mitigation |
|---|---|
| Livecard covers important page content at certain positions | Default position is top-right (clear of tabs); drag is free-form; hide-to-edge-tab always available |
| 400-500 lines of new JS increases template file to ~5800 lines | Acceptable; still one file. If it exceeds 6000 lines post-merge, consider extracting to `static/livecard.js` in a follow-up |
| `xlwt` limitation from Phase 3 still prevents writing cell notes on export | Unchanged from Phase 3 — "Copier" button + paste-in-Excel flow remains the workaround |
| Playwright MCP is failed — may delay test runs | Tests are standalone `.spec.js` files runnable via `npx playwright test`; MCP is not required |
| Legacy `.rjn-livepanel` and new `.livecard` both in DOM could double-render balance check | Dispatch via `refreshChecklist()` checks `rjn_ui_mode` and calls exactly one of the two renderers |
| Reduced-motion preference not honored = accessibility regression | `@media (prefers-reduced-motion: reduce)` block at end of CSS neutralizes all animation classes; tested explicitly |
| Animation gate adds complexity for marginal benefit | Accepted — enforces "one thing at a time" rule; <30 lines of JS |
| First-load skeleton fires too briefly to be useful (<200ms) | Acceptable — skeleton covers the fetch time; if the fetch is fast enough that skeleton isn't seen, there's no problem to solve |

## 15. Open questions

None. All brainstorming decisions are locked.

## 16. Success criteria

- [ ] `window.setLivecard(true)` swaps to the new card with zero visual regressions in surrounding tabs
- [ ] Default position, drag, minimize, hide, edge-tab-reveal all work on first try
- [ ] Success moment fires on real DC=0 transitions (verified via fixture day Mar 09)
- [ ] `prefers-reduced-motion` neutralizes all animations (verified via devtools toggle)
- [ ] Persistence survives `page.reload()` (verified via Playwright test)
- [ ] `npx playwright test` runs green on all 19 tests
- [ ] `fixture_regression.py` scores preserved (no Python changes, should be identical)
- [ ] Manual review on fixture days Mar 02, Mar 14, Mar 21, Mar 29, Apr 06 confirms the card renders correctly for each variance pattern (one class, two classes, four classes, clean day, Recap-only day)
- [ ] No `console.error` during normal usage
- [ ] No animation jank during rapid field editing

## 17. Handoff

Next step: invoke the `superpowers:writing-plans` skill to produce an implementation plan. The plan will split the work across the main thread (CSS/HTML/JS via `frontend-design` skill) and a background agent (Playwright tests).

No git commits are made by Claude for this work — the user handles all git operations.
