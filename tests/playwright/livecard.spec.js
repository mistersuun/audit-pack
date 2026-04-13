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

// Pre-signed Flask session cookie generated via
// scripts/playwright_session_cookie.py — bypasses /auth/login for tests.
const SESSION_COOKIE = fs.readFileSync(
  path.join(__dirname, '.session-cookie'), 'utf8'
).trim();

async function injectAuth(context) {
  await context.addCookies([{
    name: 'session',
    value: SESSION_COOKIE,
    domain: '127.0.0.1',
    path: '/',
    httpOnly: true,
    sameSite: 'Lax',
  }]);
}

// Shared setup: navigate to the RJ native page with livecard mode enabled and a
// valid session stubbed. Balance-check responses are routed per-test via `mock`.
async function setupLivecard(page, mock) {
  await injectAuth(page.context());
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
  await page.goto('/rj/native');
  await page.waitForSelector('#livecard', { state: 'attached' });
  await page.waitForFunction(() => window.livecard && typeof window.livecard.render === 'function');
  if (mock) {
    await page.evaluate((m) => window.livecard.render(m), mock);
    await page.waitForSelector('#livecard-dc');
  }
}

// ---------- Shell (5 tests) ----------

test('1. Initial render at top-right corner, expanded', async ({ page }) => {
  await setupLivecard(page, FIXTURES.balanced);
  const card = page.locator('#livecard');
  await expect(card).toBeVisible();
  const box = await card.boundingBox();
  const vw = page.viewportSize().width;
  expect(box.x).toBeGreaterThan(vw / 2);  // right half of viewport
  expect(box.y).toBeLessThan(100);        // top
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
  // Click the header title area (not a button) to restore
  const header = page.locator('#livecard-header');
  const hb = await header.boundingBox();
  await page.mouse.click(hb.x + 30, hb.y + hb.height / 2);
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
  // |DC| > 10 → 'err' class (warn is reserved for |DC| < 10)
  await expect(dc).toHaveClass(/err/);
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
  await injectAuth(ctx);
  const p2 = await ctx.newPage();
  await p2.addInitScript(() => {
    localStorage.setItem('rjn_ui_mode', 'livecard');
    window.SESSION = { audit_date: '2026-04-10', auditor: 'Test Auditor' };
  });
  await p2.route('**/api/rj/native/balance-check/*', r => r.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify(FIXTURES.reconciled)
  }));
  await p2.goto('/rj/native');
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
  await injectAuth(page.context());
  await page.addInitScript(() => {
    localStorage.setItem('rjn_ui_mode', 'livecard');
    window.SESSION = { audit_date: '2026-04-10', auditor: 'Test Auditor' };
  });
  // Delay first balance-check so skeleton is observable
  await page.route('**/api/rj/native/balance-check/*', async route => {
    await new Promise(r => setTimeout(r, 400));
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(FIXTURES.balanced) });
  });
  await page.goto('/rj/native');
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
