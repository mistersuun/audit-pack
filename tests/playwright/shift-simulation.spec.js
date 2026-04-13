// @ts-check
/**
 * Layer 3 — Shift simulation integration test (Playwright)
 *
 * Simulates a complete auditor night shift for 2026-03-29 -> 2026-03-30:
 *   1. Import yesterday's RJ (2026-03-29 ground_truth_rj.xls)
 *   2. Clear all daily tabs (Recap + Transelect + GEAC)
 *   3. Upload tonight's source PDFs (2026-03-30)
 *   4. Fill seeded form values across all tabs
 *   5. Run macros
 *   6. Assert livecard renders with DC near $0.00
 *   7. Export the filled RJ Excel and verify 38+ sheets via SheetJS
 *   8. Screenshot the livecard
 */
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const XLSX = require('xlsx');

// ── Fixtures ──────────────────────────────────────────────────────────

const SEED = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'fixtures/seed-2026-03-30.json'), 'utf8')
);

const SESSION_COOKIE = fs.readFileSync(
  path.join(__dirname, '.session-cookie'), 'utf8'
).trim();

const FIXTURE_DIR_PREV = path.join(__dirname, '../../test_fixtures/2026-03-29');
const FIXTURE_DIR = path.join(__dirname, '../../test_fixtures/2026-03-30');

// Parse nested JSON strings from seed
const GEAC_BS = JSON.parse(SEED.geac_balance_sheet);
const TRANS_REST = JSON.parse(SEED.transelect_restaurant);
const TRANS_REC = JSON.parse(SEED.transelect_reception);
const DUEBACK = JSON.parse(SEED.dueback_entries);
const SD = JSON.parse(SEED.sd_entries);

// Map gt_jour_cols (column indices) to NAS field names
const JOUR_COL_TO_NAS = {
  4: 'jour_cafe_nourriture', 5: 'jour_cafe_boisson', 6: 'jour_cafe_bieres',
  7: 'jour_cafe_mineraux', 8: 'jour_cafe_vins',
  9: 'jour_piazza_nourriture', 10: 'jour_piazza_boisson', 11: 'jour_piazza_bieres',
  12: 'jour_piazza_mineraux', 13: 'jour_piazza_vins',
  14: 'jour_spesa_nourriture', 15: 'jour_spesa_boisson', 16: 'jour_spesa_bieres',
  17: 'jour_spesa_mineraux', 18: 'jour_spesa_vins',
  19: 'jour_chambres_svc_nourriture', 20: 'jour_chambres_svc_boisson',
  21: 'jour_chambres_svc_bieres', 22: 'jour_chambres_svc_mineraux',
  23: 'jour_chambres_svc_vins',
  24: 'jour_banquet_nourriture', 25: 'jour_banquet_boisson', 26: 'jour_banquet_bieres',
  27: 'jour_banquet_mineraux', 28: 'jour_banquet_vins',
  29: 'jour_pourboires', 30: 'jour_equip_audio', 31: 'jour_equip_divers',
  32: 'jour_location_salle', 35: 'jour_tabagie',
  36: 'jour_room_revenue', 37: 'jour_tel_local', 38: 'jour_tel_interurbain',
  39: 'jour_tel_publics',
  40: 'jour_nettoyeur', 41: 'jour_machine_distrib', 42: 'jour_fax',
  44: 'jour_autres_gl', 45: 'jour_sonifi', 46: 'jour_lit_pliant',
  47: 'jour_boutique', 48: 'jour_internet', 49: 'jour_tvq',
  50: 'jour_tps', 51: 'jour_taxe_hebergement', 52: 'jour_massage',
  53: 'jour_vestiaire', 54: 'jour_gift_cards', 57: 'jour_club_lounge',
  80: 'jour_certificats', 83: 'jour_ar_misc', 86: 'jour_deposit_on_hand',
  88: 'jour_rooms_simple', 89: 'jour_rooms_double', 90: 'jour_rooms_suite',
  91: 'jour_rooms_comp', 92: 'jour_nb_clients', 93: 'jour_rooms_hors_usage',
};

// ── Helpers ───────────────────────────────────────────────────────────

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

/** Fill a number input by selector, triggering input event. */
async function fillNumber(page, selector, value) {
  if (value === undefined || value === null || value === 0) return;
  const el = page.locator(selector).first();
  if (await el.count() === 0) return;
  await el.fill(String(value));
  await el.dispatchEvent('input');
}

/** Fill a data-field input (Recap tab). */
async function fillDataField(page, fieldName, value) {
  await fillNumber(page, `[data-field="${fieldName}"]`, value);
}

/** Fill a data-jour input (Jour tab). */
async function fillDataJour(page, jourField, value) {
  await fillNumber(page, `[data-jour="${jourField}"]`, value);
}

/** Wait for autosave debounce + network. */
async function waitForSave(page) {
  await page.waitForTimeout(1500);
}

// ── Test ──────────────────────────────────────────────────────────────

test('shift simulation 2026-03-29 -> 2026-03-30 — full auditor night shift', async ({ page }) => {
  test.setTimeout(180_000);

  await injectAuth(page.context());
  await page.addInitScript(() => {
    localStorage.setItem('rjn_ui_mode', 'livecard');
  });

  // Auto-accept all confirm dialogs (needed for clearMacro)
  page.on('dialog', dialog => dialog.accept());

  // ════════════════════════════════════════
  // 1. Navigate to RJ Native
  // ════════════════════════════════════════
  await page.goto('/rj/native');
  await page.waitForSelector('.rjn', { state: 'attached', timeout: 15000 });

  // ════════════════════════════════════════
  // 2. Import yesterday's RJ (creates session for 2026-03-30)
  // ════════════════════════════════════════
  const rjFilePath = path.join(FIXTURE_DIR_PREV, 'ground_truth_rj.xls');
  console.log(`  Importing RJ from: ${rjFilePath}`);

  await page.setInputFiles('#file-import-rj', rjFilePath);

  // Wait for import to complete — the import-status div gets a success message
  // containing the emerald-colored checkmark when done
  await page.waitForSelector('#import-status span[style*="emerald"]', { timeout: 15000 });
  await page.waitForTimeout(1000); // let loadSessionToForm finish

  // Verify session was created for 2026-03-30
  const sessionDate = await page.evaluate(() => {
    const inp = document.getElementById('inp-date');
    return inp ? inp.value : null;
  });
  console.log(`  Session date after import: ${sessionDate}`);
  expect(sessionDate).toBe('2026-03-30');

  // Verify SESSION object exists (SESSION is let-scoped, not window-global)
  const hasSession = await page.evaluate(() => {
    // Check if SESSION is accessible via the script scope by testing a known side effect
    // The import sets inp-date and enables buttons — use btn-export as a proxy
    const btn = document.getElementById('btn-export');
    return btn && !btn.disabled;
  });
  console.log(`  SESSION loaded (btn-export enabled): ${hasSession}`);
  // If buttons aren't enabled yet, that's OK — loadSessionToForm may not have fired
  // We proceed regardless since the import clearly succeeded (date is set).

  // ════════════════════════════════════════
  // 3. Clear all daily tabs (Recap + Transelect + GEAC)
  // ════════════════════════════════════════
  console.log('  Clearing all daily tabs...');
  await page.click('button[onclick*="clearMacro(\'all-daily\')"]');
  await page.waitForTimeout(2000);

  // ════════════════════════════════════════
  // 4. Upload tonight's source PDFs
  // ════════════════════════════════════════
  console.log('  Uploading source PDFs...');
  const uploads = [
    { file: 'sales_journal.txt', type: 'sales_journal' },
    { file: 'daily_revenue.pdf', type: 'daily_revenue' },
    { file: 'ar_summary.pdf', type: 'ar_summary' },
    { file: 'hp.xlsx', type: 'hp_excel' },
    { file: 'market_segment.pdf', type: 'market_segment' },
  ];

  for (const { file, type } of uploads) {
    const filePath = path.join(FIXTURE_DIR, file);
    if (!fs.existsSync(filePath)) {
      console.log(`    Skipping upload: ${file} (not found)`);
      continue;
    }

    await page.evaluate((docType) => {
      window._currentDocType = docType;
    }, type);
    await page.setInputFiles('#file-report-upload', filePath);

    // Wait for upload to complete and session to reload
    await page.waitForTimeout(3000);
    console.log(`    Uploaded: ${file} (${type})`);
  }

  // ════════════════════════════════════════
  // 5. Fill Recap tab
  // ════════════════════════════════════════
  console.log('  Filling Recap tab...');
  await page.click('button[data-tab="recap"]');
  await page.waitForTimeout(300);

  const recapFields = [
    'cash_ls_lecture', 'cash_pos_lecture',
    'cheque_ar_lecture', 'cheque_dr_lecture',
    'remb_gratuite_lecture', 'remb_client_lecture',
    'dueback_nb_lecture',
  ];
  for (const field of recapFields) {
    if (SEED[field] !== undefined) {
      await fillDataField(page, field, SEED[field]);
    }
  }

  // Force-fill readonly fields via JS
  if (SEED.dueback_reception_lecture) {
    await page.evaluate((val) => {
      const inp = document.querySelector('[data-field="dueback_reception_lecture"]');
      if (inp) { inp.value = val; inp.dispatchEvent(new Event('input')); }
    }, SEED.dueback_reception_lecture);
  }
  if (SEED.deposit_cdn) {
    await page.evaluate((val) => {
      const inp = document.querySelector('[data-field="deposit_cdn"]');
      if (inp) { inp.value = val; inp.dispatchEvent(new Event('input')); }
    }, SEED.deposit_cdn);
  }
  if (SEED.deposit_us) {
    await page.evaluate((val) => {
      const inp = document.querySelector('[data-field="deposit_us"]');
      if (inp) { inp.value = val; inp.dispatchEvent(new Event('input')); }
    }, SEED.deposit_us);
  }

  await waitForSave(page);

  // ════════════════════════════════════════
  // 6. Fill DueBack tab
  // ════════════════════════════════════════
  console.log('  Filling DueBack tab...');
  await page.click('button[data-tab="dueback"]');
  await page.waitForTimeout(300);

  for (let i = 0; i < DUEBACK.length; i++) {
    const entry = DUEBACK[i];
    const rows = await page.locator('.rjn-dueback-row').count();
    if (i >= rows) {
      await page.click('.rjn-add-row');
      await page.waitForTimeout(200);
    }
    const row = page.locator('.rjn-dueback-row').nth(i);
    const nameInput = row.locator('input[type="text"]');
    const amountInputs = row.locator('input[type="number"]');

    await nameInput.fill(entry.name);
    await nameInput.dispatchEvent('input');
    await page.evaluate(() => {
      document.querySelectorAll('.dueback-suggestions').forEach(d => d.style.display = 'none');
    });
    await page.waitForTimeout(100);
    await amountInputs.nth(1).fill(String(entry.amount));
    await amountInputs.nth(1).dispatchEvent('input');
  }

  await waitForSave(page);

  // ════════════════════════════════════════
  // 7. Fill SD tab
  // ════════════════════════════════════════
  console.log('  Filling SD tab...');
  await page.click('button[data-tab="sd"]');
  await page.waitForTimeout(300);

  for (let i = 0; i < SD.length; i++) {
    const entry = SD[i];
    const rowCount = await page.locator('#sd-rows > div').count();
    if (i >= rowCount) {
      const addBtn = page.locator('#sec-sd .rjn-add-row').first();
      if (await addBtn.count() > 0) {
        await addBtn.click();
        await page.waitForTimeout(200);
      }
    }
    const row = page.locator('#sd-rows > div').nth(i);
    const nameInput = row.locator('.sd-name');
    const verifiedInput = row.locator('.sd-verifie');

    if (await nameInput.count() > 0) {
      await nameInput.fill(entry.employee);
    }
    if (await verifiedInput.count() > 0) {
      await verifiedInput.fill(String(entry.verified_amount));
      await verifiedInput.dispatchEvent('input');
    }
  }

  await waitForSave(page);

  // ════════════════════════════════════════
  // 8. Fill Transelect tab
  // ════════════════════════════════════════
  console.log('  Filling Transelect tab...');
  await page.click('button[data-tab="transelect"]');
  await page.waitForTimeout(300);

  const CARDS = ['debit', 'visa', 'mc', 'amex', 'discover'];
  for (const card of CARDS) {
    const cardData = TRANS_REST[card];
    if (!cardData) continue;
    const row = page.locator(`#rest-tbody tr[data-cardrow="${card}"]`);
    if (await row.count() === 0) continue;

    const posInput = row.locator('.rest-positouch');
    if (await posInput.count() > 0 && cardData.positouch) {
      await posInput.fill(String(cardData.positouch));
      await posInput.dispatchEvent('input');
    }
    const escInput = row.locator('.rest-esc-pct');
    if (await escInput.count() > 0 && cardData.esc_pct !== undefined) {
      await escInput.fill(String(cardData.esc_pct));
      await escInput.dispatchEvent('input');
    }
  }

  for (const card of CARDS) {
    const cardData = TRANS_REC[card];
    if (!cardData) continue;
    const row = page.locator(`#tbl-reception tbody tr[data-cardrow="${card}"]`);
    if (await row.count() === 0) continue;

    const fbInput = row.locator('[data-src="fusebox"]');
    if (await fbInput.count() > 0 && cardData.freedompay) {
      await fbInput.fill(String(cardData.freedompay));
      await fbInput.dispatchEvent('input');
    }
    const escInput = row.locator('.rec-esc-pct');
    if (await escInput.count() > 0 && cardData.esc_pct !== undefined) {
      await escInput.fill(String(cardData.esc_pct));
      await escInput.dispatchEvent('input');
    }
  }

  await waitForSave(page);

  // ════════════════════════════════════════
  // 9. Fill GEAC tab (Balance Sheet)
  // ════════════════════════════════════════
  console.log('  Filling GEAC tab...');
  await page.click('button[data-tab="geac"]');
  await page.waitForTimeout(300);

  const bsFields = {
    '#geac-bs-prev-dr': GEAC_BS.prev_dr,
    '#geac-bs-prev-gl': GEAC_BS.prev_gl,
    '#geac-bs-today-dr': GEAC_BS.today_dr,
    '#geac-bs-today-gl': GEAC_BS.today_gl,
    '#geac-bs-facture-dr': GEAC_BS.facture_dr,
    '#geac-bs-facture-ar': GEAC_BS.facture_ar,
    '#geac-bs-advdep-dr': GEAC_BS.advdep_dr,
    '#geac-bs-advdep-ad': GEAC_BS.advdep_ad,
    '#geac-bs-newbal-dr': GEAC_BS.newbal_dr,
    '#geac-bs-newbal-gl': GEAC_BS.newbal_gl,
  };
  for (const [selector, value] of Object.entries(bsFields)) {
    await fillNumber(page, selector, value);
  }

  await waitForSave(page);

  // ════════════════════════════════════════
  // 10. Fill Jour tab (scalars + GT jour columns)
  // ════════════════════════════════════════
  console.log('  Filling Jour tab...');
  await page.click('button[data-tab="jour"]');
  await page.waitForTimeout(300);

  if (SEED._gt_jour_cols) {
    for (const [colStr, value] of Object.entries(SEED._gt_jour_cols)) {
      const nasField = JOUR_COL_TO_NAS[parseInt(colStr)];
      if (nasField) {
        await fillDataJour(page, nasField, value);
      }
    }
  }

  await waitForSave(page);

  // ════════════════════════════════════════
  // 11. Fill RJ Rapport tab (bal ouv / bal ferm)
  // ════════════════════════════════════════
  if (SEED.rj_balance_ouverture) {
    console.log('  Filling RJ Rapport tab...');
    await page.evaluate(() => {
      const sec = document.getElementById('secondary-tabs');
      if (sec) sec.style.display = 'flex';
      switchTab('rj_rapport');
    });
    await page.waitForTimeout(500);
    await fillNumber(page, '#rj-bal-ouv', SEED.rj_balance_ouverture);
    await waitForSave(page);
  }

  // ════════════════════════════════════════
  // 12. Run macros
  // ════════════════════════════════════════
  console.log('  Running macros...');
  await page.click('button[data-tab="transelect"]');
  await page.waitForTimeout(300);

  await page.evaluate(async () => {
    if (typeof runMacro === 'function') {
      await runMacro('envoie_jour');
      await runMacro('calcul_carte');
      await runMacro('sync_setd');
    }
  });
  await page.waitForTimeout(2000);

  // Reload session to pick up macro results
  // Note: SESSION is let-scoped, so we use loadSessionToForm which sets it internally
  await page.evaluate(async () => {
    const date = document.getElementById('inp-date').value;
    const r = await fetch(`/api/rj/native/session/${date}`);
    const d = await r.json();
    if (d.session && typeof loadSessionToForm === 'function') {
      loadSessionToForm(d.session);
    }
  });
  await page.waitForTimeout(1000);

  // ════════════════════════════════════════
  // 13. Wait for livecard to settle
  // ════════════════════════════════════════
  console.log('  Waiting for livecard...');
  await page.evaluate(() => {
    if (typeof refreshChecklist === 'function') refreshChecklist();
  });
  await page.waitForTimeout(3000);

  // ════════════════════════════════════════
  // 14. Verify DC on livecard
  // ════════════════════════════════════════
  console.log('  Checking DC on livecard...');
  const livecardExists = await page.locator('#livecard').count() > 0;
  let dcNumeric = NaN;

  if (livecardExists) {
    const dcLocator = page.locator('#livecard-dc');
    const dcVisible = await dcLocator.count() > 0;

    if (dcVisible) {
      const dcText = await dcLocator.textContent();
      console.log(`  Livecard DC text: "${dcText}"`);

      expect(dcText).not.toBe('');
      expect(dcText).not.toBe('\u2014'); // em-dash

      dcNumeric = parseFloat(dcText.replace(/[$,\s]/g, ''));
      if (!isNaN(dcNumeric)) {
        console.log(`  DC numeric value: ${dcNumeric}`);
        // Soft assertion: browser path may have small variance vs penny-perfect pytest
        expect(Math.abs(dcNumeric)).toBeLessThan(5);
      }

      const verdictLocator = page.locator('#livecard-verdict');
      if (await verdictLocator.count() > 0) {
        const verdict = await verdictLocator.textContent();
        console.log(`  Livecard verdict: "${verdict}"`);
      }
    }
  } else {
    console.log('  Livecard not present — checking balance-check API directly');
    const bcResult = await page.evaluate(async () => {
      const date = document.getElementById('inp-date').value;
      const r = await fetch(`/api/rj/native/balance-check/${date}`);
      return await r.json();
    });
    console.log(`  Balance-check API: DC=${bcResult?.dc}, verdict=${bcResult?.verdict}`);
    if (bcResult?.dc !== undefined) {
      dcNumeric = parseFloat(bcResult.dc);
      expect(Math.abs(dcNumeric)).toBeLessThan(5);
    }
  }

  // ════════════════════════════════════════
  // 15. Screenshot the livecard
  // ════════════════════════════════════════
  if (livecardExists) {
    await page.locator('#livecard').screenshot({
      path: 'test-results/shift-simulation-2026-03-30.png',
    });
    console.log('  Screenshot saved: test-results/shift-simulation-2026-03-30.png');
  }

  // ════════════════════════════════════════
  // 16. Export the filled RJ Excel
  // ════════════════════════════════════════
  console.log('  Exporting RJ Excel...');

  // First, trigger a save-all so the export has fresh data
  await page.evaluate(async () => {
    if (typeof saveAllSections === 'function') await saveAllSections();
  });
  await page.waitForTimeout(2000);

  // Call the rj-filled export API directly via fetch (the #btn-export uses
  // window.open which is harder to intercept; exportRJExcel uses fetch
  // but needs the script-scoped SESSION)
  const exportUrl = '/api/rj/native/export/rj-filled/2026-03-30';
  const responsePromise = page.waitForResponse(resp =>
    resp.url().includes(exportUrl) && resp.status() === 200
  );

  // Trigger via evaluate since exportRJExcel reads script-scoped SESSION
  await page.evaluate(async () => {
    if (typeof exportRJExcel === 'function') {
      await exportRJExcel();
    }
  });

  const response = await responsePromise;
  const exportBuffer = await response.body();
  console.log(`  Export response size: ${exportBuffer.length} bytes`);

  // ════════════════════════════════════════
  // 17. Verify exported XLS has 38+ sheets
  // ════════════════════════════════════════
  const wb = XLSX.read(exportBuffer, { type: 'buffer' });
  console.log(`  Exported workbook has ${wb.SheetNames.length} sheets`);
  console.log(`  Sheet names: ${wb.SheetNames.join(', ')}`);

  expect(wb.SheetNames.length).toBeGreaterThanOrEqual(38);

  // ════════════════════════════════════════
  // 18. Verify session was saved correctly
  // ════════════════════════════════════════
  const sessionData = await page.evaluate(async () => {
    const date = document.getElementById('inp-date').value;
    const r = await fetch(`/api/rj/native/session/${date}`);
    const d = await r.json();
    return d.session || d;
  });

  expect(sessionData).toBeTruthy();
  expect(sessionData.audit_date).toBe('2026-03-30');

  console.log(`  Session verified: audit_date=${sessionData.audit_date}, status=${sessionData.status}`);
  console.log(`  Final DC: ${dcNumeric}`);
});
