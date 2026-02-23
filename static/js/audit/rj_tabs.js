// ============================================================================
// MAIN RJ TABS JAVASCRIPT - Shared functionality
// ============================================================================

/**
 * Tab Switching and Lazy Loading Logic
 * - Caches tab HTML after first load
 * - Handles tab switching via fetch API
 * - Manages localStorage persistence
 */

// ============================================================================
// DEBUG FLAG & LOGGING
// ============================================================================

// Debug flag — set to true during development
const RJ_DEBUG = false;

function rjLog(...args) {
  if (RJ_DEBUG) console.log('[RJ]', ...args);
}

function rjError(...args) {
  if (RJ_DEBUG) console.error('[RJ]', ...args);
}

// ============================================================================
// API ENDPOINT CONFIGURATION
// ============================================================================

const RJ_API = {
  upload: '/api/rj/upload',
  download: '/api/rj/download',
  status: '/api/rj/status',
  reset: '/api/rj/reset',
  resetSheet: (sheet) => `/api/rj/reset/${sheet}`,
  controle: '/api/rj/controle',
  validate: '/api/rj/validate',
  preview: (sheet, opts = {}) => {
    const p = new URLSearchParams({
      sheet,
      start_row: opts.startRow || 0,
      end_row: opts.endRow || 35,
      start_col: opts.startCol || 0,
      end_col: opts.endCol || 15
    });
    return `/api/rj/preview?${p}`;
  },
  fill: (sheet) => `/api/rj/fill/${sheet}`,
  deposit: '/api/rj/deposit',
  duebackSave: '/api/rj/dueback/save',
  duebackReception: '/api/rj/dueback/reception',
  sdEntries: (day) => `/api/sd/day/${day}/entries`,
  macroEnvoieJour: '/api/rj/macro/envoie-jour',
  macroCalculCarte: '/api/rj/macro/calcul-carte',
  macroSendRecap: '/api/rj/macro/send-recap-jour',
  weather: '/api/rj/weather',
  reportPdf: '/api/rj/report/pdf',
  quasimodoGenerate: '/api/rj/quasimodo/generate',
  quasimodoPreview: '/api/rj/quasimodo/preview',
  quasimodoAutofill: '/api/rj/quasimodo/autofill',
  downloadCheck: '/api/rj/download/check',
  progress: '/api/rj/progress',
  duebackReceptionists: '/api/rj/dueback/receptionists',
};

// ============================================================================
// CSRF PROTECTION
// ============================================================================

/**
 * Get CSRF token from meta tag.
 */
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

/**
 * Wrapper around fetch() that automatically includes CSRF token for POST requests.
 */
async function csrfFetch(url, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'DELETE'].includes(method)) {
    if (!options.headers) options.headers = {};
    options.headers['X-CSRF-Token'] = getCsrfToken();
  }
  return window.fetch(url, options);
}

// ============================================================================
// UTILITY FUNCTIONS (overrides inline stubs)
// ============================================================================

function formatCurrency(value) {
  const num = parseFloat(value) || 0;
  return '$' + num.toFixed(2);
}

/**
 * Convert 0-based column index to Excel letter(s).
 * 0→A, 1→B, ..., 25→Z, 26→AA, 27→AB, etc.
 */
function colIndexToLetter(idx) {
  let letters = '';
  let n = idx;
  while (n >= 0) {
    letters = String.fromCharCode(65 + (n % 26)) + letters;
    n = Math.floor(n / 26) - 1;
  }
  return letters;
}

/**
 * Wrapper for async button operations with spinner + disable.
 * Eliminates the repeated 8-line pattern across all handlers.
 *
 * @param {Event|null} evt - The DOM event (to find the button)
 * @param {Function} asyncFn - Async function to execute
 * @param {string} loadingText - Text shown during execution
 */
async function withSpinner(evt, asyncFn, loadingText = 'Exécution...') {
  const btn = evt?.target?.closest?.('button') || evt?.currentTarget;
  let orig;
  if (btn) {
    orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<div class="rj-spinner" style="width:16px;height:16px;border-width:2px;"></div> ${loadingText}`;
  }
  try {
    await asyncFn();
  } finally {
    if (btn) {
      btn.innerHTML = orig;
      btn.disabled = false;
      if (typeof feather !== 'undefined') feather.replace();
    }
  }
}

/**
 * Invalidate tab cache for specific tabs or all tabs.
 * Should be called after any save/macro that modifies RJ data.
 */
function invalidateTabCache(tabNames) {
  if (!window.tabCache) return;
  if (!tabNames) {
    // Clear all
    Object.keys(window.tabCache).forEach(k => delete window.tabCache[k]);
  } else {
    // Clear specific tabs
    (Array.isArray(tabNames) ? tabNames : [tabNames]).forEach(t => {
      delete window.tabCache[t];
    });
  }
}

// ============================================================================
// AUTO-SAVE SYSTEM — debounced save on input change
// ============================================================================

/** Per-sheet debounce timers */
const _autoSaveTimers = {};

/** Auto-save status indicator */
function showAutoSaveStatus(status, sheetName) {
  let indicator = document.getElementById('autosave-indicator');
  if (!indicator) {
    indicator = document.createElement('div');
    indicator.id = 'autosave-indicator';
    indicator.style.cssText = 'position:fixed; bottom:1rem; right:1rem; padding:0.5rem 1rem; border-radius:0.5rem; font-size:0.8rem; z-index:9999; transition:opacity 0.3s ease; pointer-events:none;';
    document.body.appendChild(indicator);
  }

  if (status === 'saving') {
    indicator.textContent = `⏳ Sauvegarde ${sheetName}...`;
    indicator.style.background = '#fef3c7';
    indicator.style.color = '#92400e';
    indicator.style.opacity = '1';
  } else if (status === 'saved') {
    indicator.textContent = `✓ ${sheetName} sauvegardé`;
    indicator.style.background = '#d1fae5';
    indicator.style.color = '#065f46';
    indicator.style.opacity = '1';
    setTimeout(() => { indicator.style.opacity = '0'; }, 2000);
  } else if (status === 'error') {
    indicator.textContent = `✗ Erreur: ${sheetName}`;
    indicator.style.background = '#fee2e2';
    indicator.style.color = '#991b1b';
    indicator.style.opacity = '1';
    setTimeout(() => { indicator.style.opacity = '0'; }, 4000);
  }
}

/**
 * Debounced auto-save for a sheet.
 * Collects all [data-field] inputs in the container and POSTs to the fill API.
 *
 * @param {string} sheetName - Sheet name for the API endpoint
 * @param {string} containerSelector - CSS selector for the form container (optional)
 * @param {number} delay - Debounce delay in ms (default 1500)
 */
function scheduleAutoSave(sheetName, containerSelector, delay = 1500) {
  // Clear existing timer for this sheet
  if (_autoSaveTimers[sheetName]) {
    clearTimeout(_autoSaveTimers[sheetName]);
  }

  _autoSaveTimers[sheetName] = setTimeout(async () => {
    const container = containerSelector
      ? document.querySelector(containerSelector)
      : document.getElementById('rj-tab-container');

    if (!container) return;

    const inputs = container.querySelectorAll('[data-field]');
    const data = {};
    let fieldCount = 0;

    inputs.forEach(input => {
      const field = input.getAttribute('data-field');
      if (!field) return;

      let value;
      if (input.type === 'number') {
        value = input.value !== '' ? parseFloat(input.value) : null;
      } else if (input.type === 'checkbox') {
        value = input.checked;
      } else {
        value = input.value || null;
      }

      if (value !== null && value !== '') {
        data[field] = value;
        fieldCount++;
      }
    });

    if (fieldCount === 0) return; // Nothing to save

    showAutoSaveStatus('saving', sheetName);

    try {
      const response = await csrfFetch(RJ_API.fill(sheetName), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        showAutoSaveStatus('error', sheetName);
        return;
      }

      const result = await response.json();
      if (result.success) {
        showAutoSaveStatus('saved', sheetName);
        invalidateTabCache([sheetName]);
        refreshValidation();
      } else {
        showAutoSaveStatus('error', sheetName);
      }
    } catch (e) {
      showAutoSaveStatus('error', sheetName);
      rjError('Auto-save failed:', e);
    }
  }, delay);
}

/**
 * Attach auto-save listeners to all [data-field] inputs in a container.
 * Should be called after a tab is loaded/rendered.
 *
 * @param {string} sheetName - Sheet name for the save API
 * @param {string} containerSelector - CSS selector for the container
 */
function attachAutoSave(sheetName, containerSelector) {
  const container = containerSelector
    ? document.querySelector(containerSelector)
    : document.getElementById('rj-tab-container');

  if (!container) return;

  const inputs = container.querySelectorAll('[data-field]');
  inputs.forEach(input => {
    // Use 'input' event for real-time, 'change' for selects/checkboxes
    const eventType = (input.tagName === 'SELECT' || input.type === 'checkbox') ? 'change' : 'input';

    // Avoid double-attaching
    if (input.dataset.autoSaveAttached) return;
    input.dataset.autoSaveAttached = 'true';

    input.addEventListener(eventType, () => {
      scheduleAutoSave(sheetName, containerSelector);
    });
  });
}

function notify(message, type = 'info') {
  const container = document.getElementById('notification-container');
  if (!container) return;

  const notification = document.createElement('div');
  notification.className = `rj-toast rj-toast-${type}`;

  // Use textContent to prevent XSS (never insert raw HTML from server messages)
  const msgSpan = document.createElement('span');
  msgSpan.textContent = message;

  const closeBtn = document.createElement('button');
  closeBtn.textContent = '\u00D7';
  closeBtn.style.cssText = 'background:none; border:none; cursor:pointer; opacity:0.6; font-size:1.2rem; padding:0 0 0 1rem;';
  closeBtn.addEventListener('click', () => notification.remove());

  notification.appendChild(msgSpan);
  notification.appendChild(closeBtn);

  container.appendChild(notification);
  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => notification.remove(), 300);
  }, 4000);
}

function setupExcelNavigation(tableSelector) {
  const table = document.querySelector(tableSelector);
  if (!table) return;

  const inputs = table.querySelectorAll('input[type="number"], input[type="text"], select');
  if (inputs.length === 0) return;

  // Calculate columns per row for vertical navigation
  const rows = table.querySelectorAll('tbody tr, tr');
  let colsPerRow = 1;
  if (rows.length > 0) {
    const firstRowInputs = rows[0].querySelectorAll('input[type="number"], input[type="text"], select');
    if (firstRowInputs.length > 0) colsPerRow = firstRowInputs.length;
  }

  inputs.forEach((input, index) => {
    input.addEventListener('keydown', (e) => {
      switch (e.key) {
        case 'ArrowRight':
          e.preventDefault();
          if (index + 1 < inputs.length) inputs[index + 1].focus();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          if (index - 1 >= 0) inputs[index - 1].focus();
          break;
        case 'ArrowDown':
          e.preventDefault();
          if (index + colsPerRow < inputs.length) inputs[index + colsPerRow].focus();
          break;
        case 'ArrowUp':
          e.preventDefault();
          if (index - colsPerRow >= 0) inputs[index - colsPerRow].focus();
          break;
        case 'Enter':
          e.preventDefault();
          if (index + 1 < inputs.length) inputs[index + 1].focus();
          break;
        case 'Tab':
          e.preventDefault();
          if (e.shiftKey) {
            if (index - 1 >= 0) inputs[index - 1].focus();
          } else {
            if (index + 1 < inputs.length) inputs[index + 1].focus();
          }
          break;
      }
    });
  });
}

// ============================================================================
// VALIDATION WIDGET
// ============================================================================

/**
 * Fetch validation results and update the floating widget.
 */
async function refreshValidation() {
  try {
    const res = await csrfFetch(RJ_API.validate);
    if (!res.ok) return;
    const data = await res.json();
    if (!data.success) return;

    let widget = document.getElementById('validation-widget');
    if (!widget) {
      widget = document.createElement('div');
      widget.id = 'validation-widget';
      widget.style.cssText = 'position:fixed; top:4.5rem; right:1rem; background:white; border-radius:0.75rem; box-shadow:0 4px 12px rgba(0,0,0,0.15); padding:0.75rem 1rem; z-index:9998; font-size:0.8rem; min-width:200px; max-width:280px; transition: all 0.3s ease;';
      document.body.appendChild(widget);
    }

    const icons = { ok: '✅', warning: '⚠️', error: '❌', info: 'ℹ️' };
    const colors = { ok: '#065f46', warning: '#92400e', error: '#991b1b', info: '#1e40af' };

    let html = `<div style="font-weight:600; margin-bottom:0.5rem; color:${colors[data.overall]};">${icons[data.overall]} Validation RJ</div>`;

    data.checks.forEach(c => {
      html += `<div style="display:flex; justify-content:space-between; padding:0.15rem 0; color:${colors[c.status]};">`;
      html += `<span>${icons[c.status]} ${c.name}</span>`;
      html += `<span style="font-size:0.75rem; opacity:0.8;">${c.detail}</span>`;
      html += '</div>';
    });

    widget.innerHTML = html;
  } catch (e) {
    rjError('Validation fetch failed:', e);
  }
}

// ============================================================================
// AUTO-FILL WEATHER
// ============================================================================

/**
 * Fetch current weather and auto-fill the temperature field.
 * Called when Nouveau Jour tab loads.
 */
async function autoFillWeather() {
  try {
    const res = await csrfFetch(RJ_API.weather);
    if (!res.ok) return;
    const data = await res.json();

    if (data.success && data.weather) {
      const w = data.weather;

      // Auto-fill temperature input if it exists and is empty
      const tempInput = document.getElementById('controle-temperature')
        || document.querySelector('[data-field="temperature"]');
      if (tempInput && !tempInput.value) {
        tempInput.value = w.temperature;
      }

      // Auto-fill condition if field exists and is empty
      const condInput = document.getElementById('controle-condition')
        || document.querySelector('[data-field="condition"]');
      if (condInput && !condInput.value) {
        condInput.value = w.description;
      }

      // Show weather badge
      const weatherBadge = document.getElementById('weather-badge');
      if (weatherBadge) {
        weatherBadge.textContent = `${w.temperature}°C — ${w.description}`;
        weatherBadge.style.display = 'inline-block';
      }
    }
  } catch (e) {
    rjError('Weather fetch failed:', e);
  }
}

// ============================================================================
// MAIN RJ FILE OPERATIONS
// ============================================================================

async function uploadRJFile() {
  const fileInput = document.getElementById('rj-file-input');
  const file = fileInput.files[0];

  if (!file) {
    notify('Veuillez sélectionner un fichier RJ', 'error');
    return;
  }

  // Show loading state on upload button
  const uploadBtn = document.getElementById('btn-upload-rj');
  const originalHTML = uploadBtn.innerHTML;
  uploadBtn.innerHTML = '<div class="rj-spinner" style="width:16px;height:16px;border-width:2px;"></div> <span>Chargement...</span>';
  uploadBtn.disabled = true;

  const formData = new FormData();
  formData.append('rj_file', file);

  try {
    const response = await csrfFetch(RJ_API.upload, {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (data.success) {
      updateFileStatus(data.file_info.filename, data.file_info.size);
      notify(`RJ chargé: ${data.file_info.filename}`, 'success');

      // Store audit info for auto-population
      if (data.audit_info) {
        window.rjAuditInfo = data.audit_info;
      }

      // Clear tab cache so data reloads fresh
      Object.keys(tabCache).forEach(k => delete tabCache[k]);

      // Auto-switch to nouveau-jour
      await switchRJTab('nouveau-jour');

      // Auto-populate date fields if audit info is available
      if (data.audit_info) {
        setTimeout(() => {
          const vjour = document.getElementById('controle-vjour');
          const mois = document.getElementById('controle-mois');
          const annee = document.getElementById('controle-annee');

          if (vjour && data.audit_info.jour) {
            vjour.value = String(Math.floor(data.audit_info.jour));
          }
          if (mois && data.audit_info.mois) {
            mois.value = String(Math.floor(data.audit_info.mois));
          }
          if (annee && data.audit_info.annee) {
            annee.value = String(Math.floor(data.audit_info.annee));
          }

          // Show what was detected
          const parts = [];
          if (data.audit_info.jour) parts.push(`Jour ${Math.floor(data.audit_info.jour)}`);
          if (data.audit_info.mois) parts.push(`Mois ${Math.floor(data.audit_info.mois)}`);
          if (data.audit_info.annee) parts.push(`Année ${Math.floor(data.audit_info.annee)}`);
          if (parts.length > 0) {
            notify(`Date détectée: ${parts.join(', ')}`, 'info');
          }
        }, 500); // Wait for tab to render
      }

      // Auto-fill weather
      autoFillWeather();

      // Refresh validation widget
      refreshValidation();
    } else {
      notify(`Erreur: ${data.error}`, 'error');
    }
  } catch (error) {
    rjError('Error uploading RJ file:', error);
    notify(`Erreur réseau: ${error.message}`, 'error');
  } finally {
    uploadBtn.innerHTML = originalHTML;
    uploadBtn.disabled = false;
    if (typeof feather !== 'undefined') feather.replace();
  }
}

async function resetRJ() {
  const confirmed = await showConfirmModal(
    'Réinitialiser le RJ',
    'Ceci va effacer toutes les modifications non sauvegardées dans le RJ en mémoire. Cette action est irréversible.',
    true
  );
  if (!confirmed) return;

  try {
    const response = await csrfFetch(RJ_API.reset, { method: 'POST' });
    const data = await response.json();

    if (data.success) {
      notify(data.message || 'RJ réinitialisé', 'success');
      // Clear tab cache
      Object.keys(tabCache).forEach(k => delete tabCache[k]);
      location.reload();
    } else {
      notify(`Erreur: ${data.error}`, 'error');
    }
  } catch (error) {
    rjError('Error resetting RJ:', error);
    notify(`Erreur réseau: ${error.message}`, 'error');
  }
}

async function downloadRJ() {
  const downloadBtn = document.getElementById('btn-download-rj');
  const originalHTML = downloadBtn.innerHTML;
  downloadBtn.innerHTML = '<div class="rj-spinner" style="width:16px;height:16px;border-width:2px;"></div> <span>...</span>';
  downloadBtn.disabled = true;

  try {
    const response = await csrfFetch(RJ_API.download);

    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      // Use server-provided filename if available, fall back to client date
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `RJ_${new Date().toISOString().split('T')[0]}.xls`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match && match[1]) {
          filename = match[1].replace(/['"]/g, '');
        }
      }
      a.download = filename;

      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      notify('Fichier téléchargé', 'success');
    } else {
      const data = await response.json();
      notify(`Erreur: ${data.error}`, 'error');
    }
  } catch (error) {
    rjError('Error downloading RJ file:', error);
    notify(`Erreur réseau: ${error.message}`, 'error');
  } finally {
    downloadBtn.innerHTML = originalHTML;
    downloadBtn.disabled = false;
    if (typeof feather !== 'undefined') feather.replace();
  }
}

async function checkRJStatus() {
  try {
    const response = await csrfFetch(RJ_API.status);
    const data = await response.json();

    if (data.file_loaded) {
      updateFileStatus(data.filename, data.file_size);
      notify(`Fichier: ${data.filename} (${(data.file_size / 1024).toFixed(0)} KB)`, 'info');
    } else {
      notify('Aucun fichier RJ chargé', 'warning');
    }
  } catch (error) {
    rjError('Error checking RJ status:', error);
    notify(`Erreur réseau: ${error.message}`, 'error');
  }
}

// ============================================================================
// SHEET OPERATIONS (with confirmation modals)
// ============================================================================

async function updateControle(evt) {
  const vjour = document.getElementById('controle-vjour')?.value;
  const mois = document.getElementById('controle-mois')?.value;
  const annee = document.getElementById('controle-annee')?.value;

  if (!vjour) {
    notify('Veuillez sélectionner un jour', 'error');
    return;
  }

  await withSpinner(evt, async () => {
    const response = await csrfFetch(RJ_API.controle, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        vjour: parseInt(vjour),
        mois: parseInt(mois),
        annee: parseInt(annee)
      })
    });
    if (!response.ok) { notify('Erreur serveur', 'error'); return; }
    const data = await response.json();

    if (data.success) {
      notify(`Date appliquée: jour ${vjour}/${mois}/${annee}`, 'success');
      invalidateTabCache(['nouveau-jour']);
      if (typeof refreshControlePreview === 'function') {
        refreshControlePreview();
      }
      refreshValidation();
    } else {
      notify(`Erreur: ${data.error}`, 'error');
    }
  }, 'Application...');
}

async function resetSheet(sheet) {
  const sheetNames = {
    recap: 'Recap',
    transelect: 'Transelect',
    geac: 'GEAC/UX',
    depot: 'Dépôt',
    daily: 'Daily'
  };
  const name = sheetNames[sheet] || sheet;

  const confirmed = await showConfirmModal(
    `Effacer ${name}`,
    `Ceci va effacer toutes les données de l'onglet ${name}. Voulez-vous continuer?`,
    true
  );
  if (!confirmed) return;

  try {
    const response = await csrfFetch(RJ_API.resetSheet(sheet), {
      method: 'POST'
    });
    const data = await response.json();

    if (data.success) {
      notify(`${name} effacé`, 'success');
      // Clear tab cache for this sheet
      delete tabCache[sheet];
    } else {
      notify(`Erreur: ${data.error}`, 'error');
    }
  } catch (error) {
    notify(`Erreur: ${error.message}`, 'error');
  }
}

async function resetAllSheets() {
  const confirmed = await showConfirmModal(
    'Effacer TOUS les onglets',
    'Ceci va effacer les données de Recap, Transelect, GEAC et Dépôt. Cette action est irréversible.',
    true
  );
  if (!confirmed) return;

  try {
    const response = await csrfFetch(RJ_API.reset, { method: 'POST' });
    if (!response.ok) { notify('Erreur serveur', 'error'); return; }
    const data = await response.json();

    if (data.success) {
      notify(`Tous les onglets effacés (${data.cleared_count || 0} cellules)`, 'success');
      invalidateTabCache();
    } else {
      notify(`Erreur: ${data.error}`, 'error');
    }
  } catch (error) {
    notify(`Erreur: ${error.message}`, 'error');
  }
}

// ============================================================================
// MACRO OPERATIONS
// ============================================================================

async function macroEnvoieDansJour(evt) {
  await withSpinner(evt, async () => {
    const response = await csrfFetch(RJ_API.macroEnvoieJour, { method: 'POST' });
    if (!response.ok) { notify('Erreur serveur', 'error'); return; }
    const data = await response.json();
    if (data.success) {
      notify(`Recap → Jour: ${data.filled_count || 0} cellules remplies`, 'success');
      invalidateTabCache();
    } else {
      notify(`Erreur: ${data.error}`, 'error');
    }
  }, 'Exécution...');
}

async function macroCalculCarte(evt) {
  await withSpinner(evt, async () => {
    const response = await csrfFetch(RJ_API.macroCalculCarte, { method: 'POST' });
    if (!response.ok) { notify('Erreur serveur', 'error'); return; }
    const data = await response.json();
    if (data.success) {
      notify(`Calcul Cartes → Jour: ${data.filled_count || 0} cellules`, 'success');
      invalidateTabCache();
    } else {
      notify(`Erreur: ${data.error}`, 'error');
    }
  }, 'Exécution...');
}

async function macroExecuteAll(evt) {
  const confirmed = await showConfirmModal(
    'Exécuter toutes les macros',
    'Ceci va exécuter Envoie Recap → Jour puis Calcul Cartes → Jour. Continuer?',
    false
  );
  if (!confirmed) return;

  await withSpinner(evt, async () => {
    // Execute both macros sequentially
    const r1 = await csrfFetch(RJ_API.macroEnvoieJour, { method: 'POST' });
    const d1 = await r1.json();
    if (!d1.success) {
      notify(`Erreur Envoie Jour: ${d1.error}`, 'error');
      return;  // Now safe: withSpinner's finally always runs
    }

    const r2 = await csrfFetch(RJ_API.macroCalculCarte, { method: 'POST' });
    const d2 = await r2.json();
    if (!d2.success) {
      notify(`Erreur Calcul Carte: ${d2.error}`, 'error');
      return;
    }

    notify(`Macros exécutées: ${(d1.filled_count || 0) + (d2.filled_count || 0)} cellules remplies`, 'success');
    invalidateTabCache();
  }, 'Exécution...');
}

// ============================================================================
// AUTO-FILL BETWEEN TABS
// ============================================================================

// Fill Due Back Réception (Row 16) from DueBack Column B
async function fillDueBackReception() {
  try {
    const statusRes = await csrfFetch(RJ_API.status);
    const status = await statusRes.json();

    if (!status.file_loaded) {
      notify('Veuillez charger un fichier RJ d\'abord', 'error');
      return;
    }

    const day = status.current_day;
    if (!day) {
      notify('Impossible de déterminer le jour courant. Configurez la date dans Nouveau Jour.', 'error');
      return;
    }

    const res = await csrfFetch(`/api/rj/dueback/column-b?day=${day}`);
    const result = await res.json();

    if (result.success && result.data) {
      // API returns { data: { previous, current, net }, day }
      const currentVal = result.data.current || result.data.net || 0;
      const absValue = Math.abs(currentVal);
      const input = document.querySelector('[data-cell="B16"]') ||
                    document.querySelector('[data-field="due_back_reception_lecture"]');
      if (input) {
        input.value = absValue.toFixed(2);
        input.dispatchEvent(new Event('input', { bubbles: true }));
        notify(`Due Back Réception: ${absValue.toFixed(2)} $`, 'success');
      }
    } else {
      notify('Valeur Due Back non trouvée pour ce jour', 'warning');
    }
  } catch (e) {
    notify('Erreur lors du remplissage automatique', 'error');
  }
}

// Fill Due Back N/B (Row 17) — manual entry, just focus the field
function fillDueBackNB() {
  notify('Due Back N/B provient du PDF — entrez la valeur manuellement', 'info');
  const input = document.querySelector('[data-cell="B17"]');
  if (input) {
    input.focus();
    input.select();
  }
}

// Calculate Surplus/Deficit automatically from Recap values
function fillSurplusDeficit() {
  const getNet = (lectureField, corrField) => {
    const lecture = parseFloat(document.querySelector(`[data-field="${lectureField}"]`)?.value || 0);
    const corr = parseFloat(document.querySelector(`[data-field="${corrField}"]`)?.value || 0);
    return lecture + corr;
  };

  // Cash total
  const comptantLS = getNet('comptant_lightspeed_lecture', 'comptant_lightspeed_corr');
  const comptantPosi = getNet('comptant_positouch_lecture', 'comptant_positouch_corr');
  let totalArgentRecu = comptantLS + comptantPosi;

  // Add cheques if checked
  const hasCheques = document.getElementById('recap-has-cheques');
  if (hasCheques && hasCheques.checked) {
    const chequePR = getNet('cheque_payment_register_lecture', 'cheque_payment_register_corr');
    const chequeDR = getNet('cheque_daily_revenu_lecture', 'cheque_daily_revenu_corr');
    totalArgentRecu += chequePR + chequeDR;
  }

  // Subtract reimbursements
  const rembGrat = getNet('remb_gratuite_lecture', 'remb_gratuite_corr');
  const rembClient = getNet('remb_client_lecture', 'remb_client_corr');
  totalArgentRecu -= (rembGrat + rembClient);

  // Subtract DueBack
  const duebackRecep = getNet('due_back_reception_lecture', 'due_back_reception_corr');
  const duebackNB = getNet('due_back_nb_lecture', 'due_back_nb_corr');
  totalArgentRecu -= (duebackRecep + duebackNB);

  // Surplus/deficit = total - depot
  const depot = getNet('depot_canadien_lecture', 'depot_canadien_corr');
  const surplusDeficit = totalArgentRecu - depot;

  const surplusInput = document.querySelector('[data-field="surplus_deficit_lecture"]');
  if (surplusInput) {
    surplusInput.value = surplusDeficit.toFixed(2);
    surplusInput.dispatchEvent(new Event('input', { bubbles: true }));
    notify(`Surplus/Déficit calculé: ${surplusDeficit.toFixed(2)} $`, 'success');
  }
}

// Fill Depot total from SD verified amounts
async function fillDepotFromSD() {
  try {
    const statusRes = await csrfFetch(RJ_API.status);
    const status = await statusRes.json();

    if (!status.file_loaded) {
      notify('Veuillez charger un fichier RJ d\'abord', 'error');
      return;
    }

    const day = status.current_day;
    if (!day) {
      notify('Jour courant non trouvé dans controle', 'error');
      return;
    }

    const res = await csrfFetch(RJ_API.sdEntries(day));
    const data = await res.json();

    if (data.success) {
      const total = data.total_verifie || data.total_montant || 0;
      // Try to fill the depot field
      const input = document.querySelector('[data-field="depot_total"]') ||
                    document.querySelector('#depot-sd-total');
      if (input) {
        input.value = total.toFixed(2);
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
      notify(`Dépôt rempli depuis SD: ${total.toFixed(2)} $`, 'success');
    } else {
      notify('Données SD non trouvées pour ce jour', 'warning');
    }
  } catch (e) {
    notify('Erreur lors du remplissage depuis SD', 'error');
  }
}

// ============================================================================
// EXCEL PREVIEW
// ============================================================================

async function refreshControlePreview() {
  await loadSheetPreview('controle');
}

async function loadSheetPreview(sheetOverride) {
  const selector = document.getElementById('preview-sheet-selector');
  const sheetName = sheetOverride || (selector ? selector.value : 'controle');

  const tableEl = document.getElementById('excel-preview-table');
  const headerEl = document.getElementById('excel-preview-header');
  const bodyEl = document.getElementById('excel-preview-body');
  const loadingEl = document.getElementById('excel-preview-loading');
  const infoEl = document.getElementById('excel-preview-info');

  if (!tableEl || !bodyEl) return;

  // Show loading
  if (loadingEl) {
    loadingEl.style.display = 'block';
    loadingEl.innerHTML = '<div class="rj-spinner" style="margin:1rem auto;"></div><p style="margin-top:0.5rem;">Chargement...</p>';
  }
  tableEl.style.display = 'none';

  try {
    const response = await csrfFetch(RJ_API.preview(sheetName));
    const result = await response.json();

    if (!result.success) {
      if (loadingEl) loadingEl.innerHTML = `<p style="color:#dc3545;">Erreur: ${result.error}</p>`;
      return;
    }

    const rows = result.data || [];
    if (rows.length === 0) {
      if (loadingEl) loadingEl.innerHTML = '<p>Aucune donnée trouvée</p>';
      return;
    }

    // Build header (column letters)
    if (headerEl) {
      headerEl.innerHTML = '';
      const headerRow = document.createElement('tr');
      // Row number column
      headerRow.innerHTML = '<th class="excel-header" style="min-width:35px;">#</th>';
      const maxCols = rows[0] ? rows[0].length : 10;
      for (let c = 0; c < maxCols; c++) {
        const letter = colIndexToLetter(c);
        headerRow.innerHTML += `<th class="excel-header">${letter}</th>`;
      }
      headerEl.appendChild(headerRow);
    }

    // Build body
    bodyEl.innerHTML = '';
    rows.forEach((row, rowIdx) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td class="excel-row-header">${rowIdx + 1}</td>`;
      row.forEach((cell) => {
        const val = cell !== null && cell !== undefined ? cell : '';
        const displayVal = typeof val === 'number' ? (Number.isInteger(val) ? val : val.toFixed(2)) : val;
        tr.innerHTML += `<td class="excel-cell" style="padding:0.25rem 0.5rem; font-size:0.75rem; white-space:nowrap; max-width:150px; overflow:hidden; text-overflow:ellipsis;">${displayVal}</td>`;
      });
      bodyEl.appendChild(tr);
    });

    // Show table, hide loading
    tableEl.style.display = 'table';
    if (loadingEl) loadingEl.style.display = 'none';

    // Update controle info if reading controle sheet
    if (sheetName === 'controle' && infoEl && rows.length > 4) {
      infoEl.style.display = 'block';
      const vjour = rows[2] && rows[2][1] !== undefined ? rows[2][1] : '-';
      const mois = rows[3] && rows[3][1] !== undefined ? rows[3][1] : '-';
      const annee = rows[4] && rows[4][1] !== undefined ? rows[4][1] : '-';
      const idate = rows[27] && rows[27][1] !== undefined ? rows[27][1] : '-';

      const vjEl = document.getElementById('preview-vjour');
      const moEl = document.getElementById('preview-mois');
      const anEl = document.getElementById('preview-annee');
      const idEl = document.getElementById('preview-idate');
      if (vjEl) vjEl.textContent = vjour;
      if (moEl) moEl.textContent = mois;
      if (anEl) anEl.textContent = annee;
      if (idEl) idEl.textContent = idate;
    }

  } catch (error) {
    if (loadingEl) {
      loadingEl.textContent = '';
      const errP = document.createElement('p');
      errP.style.color = '#dc3545';
      errP.textContent = `Erreur réseau: ${error.message}`;
      loadingEl.appendChild(errP);
      loadingEl.style.display = 'block';
    }
  }
}

// ============================================================================
// GENERIC SHEET SAVE — collects all data-field inputs and POSTs to fill API
// ============================================================================

async function saveSheetGeneric(sheetName, containerSelector, evt) {
  // Collect all inputs with data-field attribute
  const container = containerSelector
    ? document.querySelector(containerSelector)
    : document.getElementById('rj-tab-container');

  if (!container) {
    notify('Conteneur non trouvé', 'error');
    return;
  }

  const inputs = container.querySelectorAll('[data-field]');
  const data = {};
  let fieldCount = 0;

  inputs.forEach(input => {
    const field = input.getAttribute('data-field');
    if (!field) return;

    let value;
    if (input.type === 'number') {
      value = input.value !== '' ? parseFloat(input.value) : null;
    } else if (input.type === 'checkbox') {
      value = input.checked;
    } else {
      value = input.value || null;
    }

    // Only include non-null values
    if (value !== null && value !== '') {
      data[field] = value;
      fieldCount++;
    }
  });

  if (fieldCount === 0) {
    notify('Aucune donnée à sauvegarder', 'warning');
    return;
  }

  await withSpinner(evt, async () => {
    const response = await csrfFetch(RJ_API.fill(sheetName), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) { notify('Erreur serveur', 'error'); return; }
    const result = await response.json();

    if (result.success) {
      notify(`${sheetName}: ${result.cells_filled || fieldCount} cellules sauvegardées`, 'success');
      invalidateTabCache([sheetName]);
    } else {
      notify(`Erreur: ${result.error}`, 'error');
    }
  }, 'Sauvegarde...');
}

// ============================================================================
// SAVE FUNCTIONS — each tab calls the generic function with its sheet name
// ============================================================================

async function saveRecap(evt) {
  // Pre-save validation: check if balance is at $0.00
  const balanceEl = document.getElementById('recap-balance-value');
  if (balanceEl) {
    const balanceText = balanceEl.textContent.replace(/[$,\s]/g, '');
    const balance = parseFloat(balanceText) || 0;

    if (Math.abs(balance) > 0.01) {
      const confirmed = await showConfirmModal(
        'Balance non nulle',
        `La balance Recap est de $${balance.toFixed(2)} (devrait être $0.00). Voulez-vous sauvegarder quand même?`,
        true
      );
      if (!confirmed) return;
    }
  }

  await saveSheetGeneric('recap', null, evt);
}

async function saveTranselect(evt) {
  // Note: Transelect has normal variance from card rounding — no confirmation needed
  await saveSheetGeneric('transelect', null, evt);
}

async function saveGeac(evt) {
  await saveSheetGeneric('geac', null, evt);
}

async function saveDepot(evt) {
  await withSpinner(evt, async () => {
    const container = document.getElementById('rj-tab-container');
    const inputs = container?.querySelectorAll('[data-field]') || [];
    const data = {};

    inputs.forEach(input => {
      const field = input.getAttribute('data-field');
      if (field && input.value !== '') {
        data[field] = input.type === 'number' ? parseFloat(input.value) : input.value;
      }
    });

    const response = await csrfFetch(RJ_API.deposit, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) { notify('Erreur serveur', 'error'); return; }
    const result = await response.json();

    if (result.success) {
      notify('Dépôt sauvegardé', 'success');
      invalidateTabCache(['depot']);
    } else {
      notify(`Erreur: ${result.error}`, 'error');
    }
  }, 'Sauvegarde...');
}

async function saveDuebackData(evt) {
  // Collect data first (before spinner) to validate
  const container = document.getElementById('rj-tab-container');
  const entryRows = container?.querySelectorAll('.dueback-receptionist-entry') || [];
  const data = {};

  entryRows.forEach(row => {
    const select = row.querySelector('select');
    const prevInput = row.querySelector('.dueback-prev-input');
    const currInput = row.querySelector('.dueback-curr-input');

    if (select && select.value) {
      data[select.value] = {
        previous: prevInput ? parseFloat(prevInput.value) || 0 : 0,
        current: currInput ? parseFloat(currInput.value) || 0 : 0
      };
    }
  });

  if (Object.keys(data).length === 0) {
    notify('Aucune entrée DueBack à sauvegarder', 'warning');
    return;
  }

  await withSpinner(evt, async () => {
    const response = await csrfFetch(RJ_API.duebackSave, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({ error: 'Erreur serveur' }));
      notify(`Erreur: ${errData.error}`, 'error');
      return;
    }

    const result = await response.json();
    if (result.success) {
      notify(`DueBack: ${Object.keys(data).length} réceptionniste(s) sauvegardé(s)`, 'success');
      invalidateTabCache(['dueback']);
    } else {
      notify(`Erreur: ${result.error}`, 'error');
    }
  }, 'Sauvegarde...');
}

async function saveSD(evt) {
  const container = document.getElementById('rj-tab-container');
  const daySelect = container?.querySelector('#sd-day-select, [data-field="sd_day"]');
  const day = daySelect ? parseInt(daySelect.value) : null;

  if (!day) {
    notify('Veuillez sélectionner un jour pour le SD', 'error');
    return;
  }

  await withSpinner(evt, async () => {
    // Scope inputs to SD tab content only to avoid collecting fields from other tabs
    const sdContainer = container?.querySelector('#tab-sd, .sd-form, [data-tab="sd"]') || container;
    const inputs = sdContainer?.querySelectorAll('[data-field]') || [];
    const entries = [];

    inputs.forEach(input => {
      const field = input.getAttribute('data-field');
      // Skip fields that belong to other sheets
      if (field && field !== 'sd_day' && !field.startsWith('recap_') && !field.startsWith('transelect_') &&
          !field.startsWith('geac_') && !field.startsWith('dueback_') && input.value !== '') {
        entries.push({
          field: field,
          value: input.type === 'number' ? parseFloat(input.value) : input.value
        });
      }
    });

    const response = await csrfFetch(RJ_API.sdEntries(day), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entries })
    });
    if (!response.ok) { notify('Erreur serveur', 'error'); return; }
    const result = await response.json();

    if (result.success) {
      notify(`SD jour ${day}: sauvegardé`, 'success');
      invalidateTabCache(['sd']);
    } else {
      notify(`Erreur: ${result.error}`, 'error');
    }
  }, 'Sauvegarde...');
}

// ============================================================================
// PDF REPORT EXPORT
// ============================================================================

/**
 * Generate and download a Night Audit PDF report for the GM.
 * Triggers a GET request to /api/rj/report/pdf which returns a PDF file.
 */
async function exportPDFReport() {
  const pdfBtn = document.getElementById('btn-pdf-report');
  if (!pdfBtn) return;

  const originalHTML = pdfBtn.innerHTML;
  pdfBtn.innerHTML = '<div class="rj-spinner" style="width:16px;height:16px;border-width:2px;"></div> <span>Génération...</span>';
  pdfBtn.disabled = true;

  try {
    const response = await fetch(RJ_API.reportPdf);

    if (!response.ok) {
      let errMsg = 'Erreur lors de la génération du PDF';
      try {
        const errData = await response.json();
        errMsg = errData.error || errMsg;
      } catch (_) { /* response was not JSON */ }
      notify(errMsg, 'error');
      return;
    }

    // Download the PDF blob
    const blob = await response.blob();
    const filename = response.headers.get('Content-Disposition')
      ?.match(/filename="?([^"]+)"?/)?.[1]
      || `Rapport_Nuit_${new Date().toISOString().slice(0, 10)}.pdf`;

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    notify('Rapport PDF téléchargé', 'success');
  } catch (error) {
    rjError('PDF export error:', error);
    notify(`Erreur: ${error.message}`, 'error');
  } finally {
    pdfBtn.innerHTML = originalHTML;
    pdfBtn.disabled = false;
    if (typeof feather !== 'undefined') feather.replace();
  }
}


/**
 * Generate and download a Quasimodo .xls file from transelect data.
 * Posts to /api/rj/quasimodo/generate which returns an .xls file.
 */
async function generateQuasimodo() {
  const btn = document.getElementById('btn-quasimodo');
  if (!btn) return;

  const originalHTML = btn.innerHTML;
  btn.innerHTML = '<div class="rj-spinner" style="width:16px;height:16px;border-width:2px;"></div> <span>Génération...</span>';
  btn.disabled = true;

  try {
    const response = await csrfFetch(RJ_API.quasimodoGenerate, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });

    if (!response.ok) {
      let errMsg = 'Erreur lors de la génération du Quasimodo';
      try {
        const errData = await response.json();
        errMsg = errData.error || errMsg;
      } catch (_) { /* response was not JSON */ }
      notify(errMsg, 'error');
      return;
    }

    // Download the XLS blob
    const blob = await response.blob();
    const filename = response.headers.get('Content-Disposition')
      ?.match(/filename="?([^"]+)"?/)?.[1]
      || `Quasimodo_${new Date().toISOString().slice(0, 10)}.xls`;

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    notify('Quasimodo généré et téléchargé', 'success');

    // After successful generation, offer to auto-fill E20-E24
    const doAutofill = await showConfirmModal(
      'Auto-remplir Transelect?',
      'Voulez-vous aussi remplir automatiquement les champs Quasimodo (E20-E24) dans Transelect avec les totaux par carte?',
      false
    );
    if (doAutofill) {
      await autofillQuasimodo(null);
    }
  } catch (error) {
    rjError('Quasimodo generation error:', error);
    notify(`Erreur: ${error.message}`, 'error');
  } finally {
    btn.innerHTML = originalHTML;
    btn.disabled = false;
    if (typeof feather !== 'undefined') feather.replace();
  }
}


// ============================================================================
// QUASIMODO AUTO-FILL (E20-E24 in transelect)
// ============================================================================

/**
 * Auto-fill Quasimodo fields E20-E24 in the transelect sheet.
 * Computes card totals from MON+GLB and writes to the Quasimodo columns.
 */
async function autofillQuasimodo(evt) {
  await withSpinner(evt, async () => {
    const response = await csrfFetch(RJ_API.quasimodoAutofill, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ error: 'Erreur serveur' }));
      notify(`Erreur: ${err.error}`, 'error');
      return;
    }

    const data = await response.json();
    if (data.success) {
      const vals = data.values || {};
      const parts = [];
      if (vals.quasimodo_debit) parts.push(`DB: $${vals.quasimodo_debit}`);
      if (vals.quasimodo_visa) parts.push(`VI: $${vals.quasimodo_visa}`);
      if (vals.quasimodo_master) parts.push(`MC: $${vals.quasimodo_master}`);
      if (vals.quasimodo_amex) parts.push(`AX: $${vals.quasimodo_amex}`);

      notify(data.message || `Quasimodo E20-E24 remplis (${data.filled_count} cellules)`, 'success');

      // Update UI inputs if we're on the transelect tab
      Object.entries(vals).forEach(([field, value]) => {
        const input = document.querySelector(`[data-field="${field}"]`);
        if (input && value) {
          input.value = parseFloat(value).toFixed(2);
        }
      });

      invalidateTabCache(['transelect']);
    } else {
      notify(`Erreur: ${data.error}`, 'error');
    }
  }, 'Auto-remplissage...');
}


// ============================================================================
// PRE-DOWNLOAD VALIDATION CHECK
// ============================================================================

/**
 * Check RJ completeness before downloading.
 * Shows warnings/errors in a modal. If user confirms, proceeds to download.
 */
async function downloadWithCheck() {
  const downloadBtn = document.getElementById('btn-download-rj');
  if (!downloadBtn) return;

  const originalHTML = downloadBtn.innerHTML;
  downloadBtn.innerHTML = '<div class="rj-spinner" style="width:16px;height:16px;border-width:2px;"></div> <span>Vérification...</span>';
  downloadBtn.disabled = true;

  try {
    const checkRes = await csrfFetch(RJ_API.downloadCheck);
    if (!checkRes.ok) {
      // If check fails, fall through to normal download
      downloadBtn.innerHTML = originalHTML;
      downloadBtn.disabled = false;
      if (typeof feather !== 'undefined') feather.replace();
      return downloadRJ();
    }

    const check = await checkRes.json();

    // Restore button
    downloadBtn.innerHTML = originalHTML;
    downloadBtn.disabled = false;
    if (typeof feather !== 'undefined') feather.replace();

    if (check.status === 'ready') {
      // All good — download directly
      return downloadRJ();
    }

    if (check.errors && check.errors.length > 0) {
      // Has blocking errors
      const errorList = check.errors.map(e => `  \u2022 ${e}`).join('\n');
      const warnList = check.warnings?.length
        ? '\n\nAvertissements:\n' + check.warnings.map(w => `  \u2022 ${w}`).join('\n')
        : '';
      const confirmed = await showConfirmModal(
        'Erreurs détectées',
        `Le RJ a des erreurs bloquantes:\n${errorList}${warnList}\n\nTélécharger quand même?`,
        true
      );
      if (confirmed) return downloadRJ();
      return;
    }

    if (check.warnings && check.warnings.length > 0) {
      // Has warnings only
      const warnList = check.warnings.map(w => `  \u2022 ${w}`).join('\n');
      const confirmed = await showConfirmModal(
        'Avertissements',
        `Le RJ semble incomplet:\n${warnList}\n\nTélécharger quand même?`,
        false
      );
      if (confirmed) return downloadRJ();
      return;
    }

    // Fallback
    return downloadRJ();

  } catch (error) {
    rjError('Download check error:', error);
    // On error, fall through to normal download
    downloadBtn.innerHTML = originalHTML;
    downloadBtn.disabled = false;
    if (typeof feather !== 'undefined') feather.replace();
    return downloadRJ();
  }
}


// ============================================================================
// PROGRESS TRACKER
// ============================================================================

/**
 * Fetch and render the progress tracker bar.
 * Shows X/7 sections completed with a visual progress bar.
 */
async function refreshProgress() {
  try {
    const res = await csrfFetch(RJ_API.progress);
    if (!res.ok) return;
    const data = await res.json();
    if (!data.success) return;

    let bar = document.getElementById('rj-progress-bar');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'rj-progress-bar';
      bar.style.cssText = 'padding:0.4rem 1rem; background:#f8fafc; border-bottom:1px solid #e2e8f0; display:flex; align-items:center; gap:0.75rem; font-size:0.8rem;';

      // Insert after toolbar, before tabs
      const toolbar = document.querySelector('.rj-toolbar');
      if (toolbar && toolbar.nextSibling) {
        toolbar.parentNode.insertBefore(bar, toolbar.nextSibling);
      }
    }

    const pct = data.progress || 0;
    const done = data.done || 0;
    const total = data.total || 7;
    const sections = data.sections || [];

    // Color based on progress
    const barColor = pct === 100 ? '#10b981' : (pct >= 50 ? '#f59e0b' : '#ef4444');

    // Build section dots
    const dots = sections.map(s => {
      const color = s.done ? '#10b981' : '#d1d5db';
      const cursor = s.tab ? 'cursor:pointer' : '';
      const onclick = s.tab ? `onclick="switchRJTab('${s.tab}')"` : '';
      return `<span title="${s.name}: ${s.detail}" ${onclick} style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${color}; ${cursor}" aria-label="${s.name}"></span>`;
    }).join('');

    bar.innerHTML = `
      <span style="font-weight:600; color:#475569; min-width:75px;">${done}/${total} sections</span>
      <div style="flex:1; background:#e2e8f0; border-radius:999px; height:8px; overflow:hidden;">
        <div style="width:${pct}%; height:100%; background:${barColor}; border-radius:999px; transition:width 0.5s ease;"></div>
      </div>
      <span style="color:${barColor}; font-weight:600; min-width:35px;">${pct}%</span>
      <div style="display:flex; gap:4px; align-items:center;">${dots}</div>
    `;
  } catch (e) {
    rjError('Progress fetch failed:', e);
  }
}

/**
 * Initialize progress tracker — auto-refresh on tab switch and file upload.
 */
function initProgressTracker() {
  if (!rjFileLoaded) return;
  refreshProgress();
}
