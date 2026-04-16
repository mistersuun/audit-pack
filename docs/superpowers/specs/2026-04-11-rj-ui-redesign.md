# RJ Native UI Redesign — Design

**Date:** 2026-04-11
**Status:** approved

## Goal

Replace the dated grey-background aesthetic of `templates/audit/rj/rj_native.html` with a dark-first Linear/Notion-inspired design, plus a proper light mode alternative. CSS-only change — zero JS modifications.

## Approach

- Replace the CSS design tokens (lines 9-23) with a dark-first palette
- Restyle every component: toolbar, tabs, cards, tables, inputs, buttons, badges, checks, upload zone, dueback rows
- The existing `[data-theme="dark"]` override block (lines 198-208) becomes the DEFAULT; light mode becomes the override
- Add a theme toggle button (sun/moon) in the toolbar, persisted via `localStorage.rjn_theme`
- All existing HTML IDs, form fields, JS functions, tab structure remain untouched

## Dark palette (default)

- Background: `#0a0a0f`
- Card/surface: `rgba(255,255,255,0.03)` with `border: 1px solid rgba(255,255,255,0.06)`
- Text primary: `#e5e7eb`, secondary: `#9ca3af`, muted: `#4b5563`
- Inputs: `rgba(255,255,255,0.04)` bg, `rgba(255,255,255,0.08)` border
- Active tab: `rgba(99,102,241,0.15)` bg, `#a5b4fc` text
- Accent: `#6366f1` (indigo), emerald/rose/amber unchanged

## Light palette (toggle)

- Background: `#fafafa`
- Card/surface: `#fff` with `border: 1px solid #e5e7eb`
- Text primary: `#1a1a2e`, secondary: `#6b7280`, muted: `#9ca3af`
- Inputs: `#fff` bg, `#e5e7eb` border
- Active tab: `#6366f1` bg, `#fff` text
- Same accent colors

## Success criteria

- All 21 Playwright tests pass unchanged
- Shift simulation test passes unchanged
- Dark mode is default, light mode via toggle
- No grey zones visible in either mode
- Every form field, button, macro trigger works identically
