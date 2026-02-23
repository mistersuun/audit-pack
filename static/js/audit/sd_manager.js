// ============================================================================
// SD (SOMMAIRE JOURNALIER) - GESTION MULTI-ENTRÉES ET AUTO-CALCULS
// ============================================================================

// Storage for SD entries
let sdData = [];

// Initialize with one empty row
function initializeSD() {
  if (sdData.length === 0) {
    addSDRow();
  }
}

// Add a new SD row
function addSDRow() {
  const entry = {
    id: Date.now() + Math.random(),
    departement: '',
    nom: '',
    devise: 'CDN',
    montant: 0,
    montant_verifie: 0,
    remboursement: 0,
    variance: 0
  };

  sdData.push(entry);
  renderSDTable();

  // Focus on the new departement input
  setTimeout(() => {
    const tbody = document.getElementById('sd-body');
    const lastRow = tbody.lastElementChild;
    if (lastRow) {
      const deptInput = lastRow.querySelector('.sd-departement');
      if (deptInput) deptInput.focus();
    }
  }, 100);
}

// Remove an SD row
function removeSDRow(entryId) {
  sdData = sdData.filter(e => e.id !== entryId);
  renderSDTable();
}

// Render the SD table
function renderSDTable() {
  const tbody = document.getElementById('sd-body');
  tbody.innerHTML = '';

  sdData.forEach((entry, index) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td class="excel-cell">
        <select class="excel-input sd-departement" data-entry-id="${entry.id}"
                onchange="updateSDEntry(${entry.id}, 'departement', this.value)">
          <option value="">Sélectionner...</option>
          <option value="RÉCEPTION" ${entry.departement === 'RÉCEPTION' ? 'selected' : ''}>RÉCEPTION</option>
          <option value="SPESA" ${entry.departement === 'SPESA' ? 'selected' : ''}>SPESA</option>
          <option value="RESTAURANT" ${entry.departement === 'RESTAURANT' ? 'selected' : ''}>RESTAURANT</option>
          <option value="BANQUET" ${entry.departement === 'BANQUET' ? 'selected' : ''}>BANQUET</option>
          <option value="COMPTABILITÉ" ${entry.departement === 'COMPTABILITÉ' ? 'selected' : ''}>COMPTABILITÉ</option>
        </select>
      </td>
      <td class="excel-cell" style="position: relative;">
        <input type="text" class="excel-input sd-nom" data-entry-id="${entry.id}"
               list="setd-names-datalist"
               value="${entry.nom || ''}"
               placeholder="Taper un nom..."
               style="min-width: 180px;"
               oninput="filterSDName(${entry.id}, this)"
               onchange="validateSDName(${entry.id}, this)"
               autocomplete="off">
        <span class="sd-nom-status" data-entry-id="${entry.id}" style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%); font-size: 0.75rem;"></span>
      </td>
      <td class="excel-cell">
        <select class="excel-input sd-devise" data-entry-id="${entry.id}"
                onchange="updateSDEntry(${entry.id}, 'devise', this.value)">
          <option value="CDN" ${entry.devise === 'CDN' ? 'selected' : ''}>CDN</option>
          <option value="US" ${entry.devise === 'US' ? 'selected' : ''}>US</option>
        </select>
      </td>
      <td class="excel-cell">
        <input type="number" step="0.01" class="excel-input sd-montant" data-entry-id="${entry.id}"
               value="${entry.montant || ''}" placeholder="0.00"
               onchange="updateSDEntry(${entry.id}, 'montant', this.value)">
      </td>
      <td class="excel-cell" style="background:#fff3cd;">
        <input type="number" step="0.01" class="excel-input sd-verifie" data-entry-id="${entry.id}"
               value="${entry.montant_verifie || ''}" placeholder="0.00"
               style="background:#ffedd5; font-weight:600;"
               onchange="updateSDEntry(${entry.id}, 'montant_verifie', this.value)">
      </td>
      <td class="excel-cell">
        <input type="number" step="0.01" class="excel-input sd-remboursement" data-entry-id="${entry.id}"
               value="${entry.remboursement || ''}" placeholder="0.00"
               onchange="updateSDEntry(${entry.id}, 'remboursement', this.value)">
      </td>
      <td class="excel-cell">
        <input type="number" step="0.01" class="excel-input sd-variance" data-entry-id="${entry.id}"
               value="${entry.variance || ''}" placeholder="0.00" readonly
               style="background:#f0f0f0;">
      </td>
      <td class="excel-cell" style="text-align:center;">
        <button onclick="removeSDRow(${entry.id})"
                style="background:#dc3545; color:white; border:none; padding:0.25rem 0.5rem; border-radius:4px; cursor:pointer; font-size:0.75rem;"
                title="Supprimer cette ligne">
          <i data-feather="trash-2" style="width:14px; height:14px;"></i>
        </button>
      </td>
    `;
    tbody.appendChild(row);
  });

  // Re-render feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }

  calculateSDTotals();
}

// Update a specific SD entry field
function updateSDEntry(entryId, field, value) {
  const entry = sdData.find(e => e.id === entryId);
  if (entry) {
    if (['montant', 'montant_verifie', 'remboursement', 'variance'].includes(field)) {
      entry[field] = parseFloat(value) || 0;
    } else {
      entry[field] = value;
    }

    // Auto-calculate variance
    if (field === 'montant' || field === 'montant_verifie' || field === 'remboursement') {
      entry.variance = entry.montant - entry.montant_verifie + entry.remboursement;
    }

    calculateSDTotals();
  }
}

// Calculate SD totals
function calculateSDTotals() {
  const totalMontant = sdData.reduce((sum, entry) => sum + (parseFloat(entry.montant) || 0), 0);
  const totalVerifie = sdData.reduce((sum, entry) => sum + (parseFloat(entry.montant_verifie) || 0), 0);
  const totalRemboursement = sdData.reduce((sum, entry) => sum + (parseFloat(entry.remboursement) || 0), 0);
  const totalVariance = sdData.reduce((sum, entry) => sum + (parseFloat(entry.variance) || 0), 0);

  document.getElementById('sd-total-montant').value = totalMontant.toFixed(2);
  document.getElementById('sd-total-verifie').value = totalVerifie.toFixed(2);
  document.getElementById('sd-total-remboursement').value = totalRemboursement.toFixed(2);
  document.getElementById('sd-total-variance').value = totalVariance.toFixed(2);

  // Update depot SD preview if function exists
  if (typeof updateDepotSDPreview === 'function') {
    updateDepotSDPreview();
  }

  // Update SetD export count
  updateSDSetDCount();

  // Update live validation dashboard
  updateLiveValidationDashboard();
}

// Update live validation dashboard in SD tab
function updateLiveValidationDashboard() {
  // 1. Update Depot preview (Montant Vérifié total)
  const totalVerifie = parseFloat(document.getElementById('sd-total-verifie')?.value) || 0;
  const depotAmountEl = document.getElementById('live-depot-amount');
  if (depotAmountEl) {
    depotAmountEl.textContent = '$' + totalVerifie.toFixed(2);
    depotAmountEl.style.color = totalVerifie > 0 ? '#007bff' : '#6c757d';
  }

  // 1b. Update Depot account details
  updateLiveDepotPreview();

  // 2. Update SetD preview (variances by employee)
  const { variances, unmatched } = getSDVariancesForSetD();
  const setdListEl = document.getElementById('live-setd-list');
  const setdTotalEl = document.getElementById('live-setd-total');

  if (setdListEl) {
    if (variances.length === 0) {
      setdListEl.innerHTML = '<div style="color: #999; font-style: italic; text-align: center; padding: 0.5rem;">Aucune variance</div>';
    } else {
      setdListEl.innerHTML = variances.map(v => {
        const color = v.variance > 0 ? '#dc3545' : '#28a745';
        const sign = v.variance > 0 ? '+' : '';
        return `<div style="display: flex; justify-content: space-between; padding: 0.25rem 0.5rem; border-bottom: 1px solid #f0f0f0;">
          <span style="color: #333;">${v.nom}</span>
          <span style="color: ${color}; font-weight: 600;">${sign}$${v.variance.toFixed(2)}</span>
        </div>`;
      }).join('');
    }
  }

  // Calculate SetD total
  const setdTotal = variances.reduce((sum, v) => sum + v.variance, 0);
  if (setdTotalEl) {
    const color = setdTotal > 0 ? '#dc3545' : setdTotal < 0 ? '#28a745' : '#6c757d';
    const sign = setdTotal > 0 ? '+' : '';
    setdTotalEl.textContent = sign + '$' + setdTotal.toFixed(2);
    setdTotalEl.style.color = color;
  }

  // 3. Update Balance indicator
  const totalVarianceSD = parseFloat(document.getElementById('sd-total-variance')?.value) || 0;
  const balanceCardEl = document.getElementById('live-balance-card');
  const balanceIconEl = document.getElementById('live-balance-icon');
  const balanceStatusEl = document.getElementById('live-balance-status');
  const varianceSDEl = document.getElementById('live-variance-sd');
  const varianceDiffEl = document.getElementById('live-variance-diff');

  // Variance SD = what's in the SD total
  // SetD total = sum of variances that have employee mapping
  // Difference = what's unaccounted for (employees not in SetD or no variance)
  const difference = totalVarianceSD - setdTotal;

  if (varianceSDEl) {
    const color = totalVarianceSD > 0 ? '#dc3545' : totalVarianceSD < 0 ? '#28a745' : '#6c757d';
    const sign = totalVarianceSD > 0 ? '+' : '';
    varianceSDEl.textContent = sign + '$' + totalVarianceSD.toFixed(2);
    varianceSDEl.style.color = color;
  }

  if (varianceDiffEl) {
    const sign = difference > 0 ? '+' : '';
    varianceDiffEl.textContent = sign + '$' + difference.toFixed(2);
  }

  // Update balance status
  const hasData = sdData.some(e => e.nom || e.montant || e.montant_verifie);

  if (!hasData) {
    // No data yet
    if (balanceCardEl) balanceCardEl.style.borderLeftColor = '#6c757d';
    if (balanceIconEl) balanceIconEl.textContent = '⚪';
    if (balanceStatusEl) {
      balanceStatusEl.textContent = 'En attente...';
      balanceStatusEl.style.color = '#6c757d';
    }
    if (varianceDiffEl) varianceDiffEl.style.color = '#6c757d';
  } else if (Math.abs(difference) < 0.01 && Math.abs(totalVarianceSD) < 0.01) {
    // Perfect balance - no variance at all
    if (balanceCardEl) balanceCardEl.style.borderLeftColor = '#28a745';
    if (balanceIconEl) balanceIconEl.textContent = '✅';
    if (balanceStatusEl) {
      balanceStatusEl.textContent = 'Équilibré!';
      balanceStatusEl.style.color = '#28a745';
    }
    if (varianceDiffEl) varianceDiffEl.style.color = '#28a745';
  } else if (Math.abs(difference) < 0.01) {
    // All variances assigned to employees
    if (balanceCardEl) balanceCardEl.style.borderLeftColor = '#28a745';
    if (balanceIconEl) balanceIconEl.textContent = '✅';
    if (balanceStatusEl) {
      balanceStatusEl.textContent = 'Variances assignées';
      balanceStatusEl.style.color = '#28a745';
    }
    if (varianceDiffEl) varianceDiffEl.style.color = '#28a745';
  } else {
    // Unbalanced - some variance not assigned
    if (balanceCardEl) balanceCardEl.style.borderLeftColor = '#dc3545';
    if (balanceIconEl) balanceIconEl.textContent = '❌';
    if (balanceStatusEl) {
      balanceStatusEl.textContent = 'Non assigné!';
      balanceStatusEl.style.color = '#dc3545';
    }
    if (varianceDiffEl) varianceDiffEl.style.color = '#dc3545';
  }

  // Show warning for unmatched names
  if (unmatched.length > 0) {
    console.warn('Noms SD non reconnus dans SetD:', unmatched);
  }
}

// Generate dropdown options for SetD names, grouped by first letter
function getSetDNamesOptions(selectedNom) {
  const names = Object.keys(SETD_PERSONNEL_COLUMNS).sort((a, b) =>
    a.toLowerCase().localeCompare(b.toLowerCase())
  );

  let html = '';
  let currentLetter = '';

  names.forEach(name => {
    const firstLetter = name.charAt(0).toUpperCase();
    if (firstLetter !== currentLetter) {
      if (currentLetter !== '') {
        html += '</optgroup>';
      }
      currentLetter = firstLetter;
      html += `<optgroup label="— ${firstLetter} —">`;
    }
    const selected = name === selectedNom ? 'selected' : '';
    html += `<option value="${name}" ${selected}>${name}</option>`;
  });

  if (currentLetter !== '') {
    html += '</optgroup>';
  }

  return html;
}

// Populate the datalist with all SetD names
function populateSetDNamesDatalist() {
  const datalist = document.getElementById('setd-names-datalist');
  if (!datalist) return;

  const names = Object.keys(SETD_PERSONNEL_COLUMNS).sort((a, b) =>
    a.toLowerCase().localeCompare(b.toLowerCase())
  );

  datalist.innerHTML = names.map(name => `<option value="${name}">`).join('');
}

// Filter and highlight as user types a name
function filterSDName(entryId, input) {
  const value = input.value.trim();
  const statusEl = input.parentElement.querySelector('.sd-nom-status');

  if (!value) {
    if (statusEl) statusEl.innerHTML = '';
    input.style.borderColor = '';
    return;
  }

  // Check for exact match
  const names = Object.keys(SETD_PERSONNEL_COLUMNS);
  const exactMatch = names.find(n => n.toLowerCase() === value.toLowerCase());
  const partialMatches = names.filter(n => n.toLowerCase().includes(value.toLowerCase()));

  if (exactMatch) {
    // Exact match found
    if (statusEl) statusEl.innerHTML = '<span style="color: #28a745;">✓</span>';
    input.style.borderColor = '#28a745';
    // Auto-correct case if needed
    if (input.value !== exactMatch) {
      input.value = exactMatch;
    }
    updateSDEntry(entryId, 'nom', exactMatch);
  } else if (partialMatches.length > 0) {
    // Partial matches - show count
    if (statusEl) statusEl.innerHTML = `<span style="color: #ffc107; font-size: 0.65rem;">${partialMatches.length}</span>`;
    input.style.borderColor = '#ffc107';
  } else {
    // No match
    if (statusEl) statusEl.innerHTML = '<span style="color: #dc3545;">✗</span>';
    input.style.borderColor = '#dc3545';
  }
}

// Validate name when user leaves the field
function validateSDName(entryId, input) {
  const value = input.value.trim();
  const statusEl = input.parentElement.querySelector('.sd-nom-status');

  if (!value) {
    updateSDEntry(entryId, 'nom', '');
    if (statusEl) statusEl.innerHTML = '';
    input.style.borderColor = '';
    return;
  }

  // Check for exact match (case-insensitive)
  const names = Object.keys(SETD_PERSONNEL_COLUMNS);
  const exactMatch = names.find(n => n.toLowerCase() === value.toLowerCase());

  if (exactMatch) {
    input.value = exactMatch;
    updateSDEntry(entryId, 'nom', exactMatch);
    if (statusEl) statusEl.innerHTML = '<span style="color: #28a745;">✓</span>';
    input.style.borderColor = '#28a745';
  } else {
    // Try to find closest match
    const closestMatches = names.filter(n =>
      n.toLowerCase().startsWith(value.toLowerCase()) ||
      n.toLowerCase().includes(value.toLowerCase())
    );

    if (closestMatches.length === 1) {
      // Only one match, auto-select it
      input.value = closestMatches[0];
      updateSDEntry(entryId, 'nom', closestMatches[0]);
      if (statusEl) statusEl.innerHTML = '<span style="color: #28a745;">✓</span>';
      input.style.borderColor = '#28a745';
    } else if (closestMatches.length > 1) {
      // Multiple matches - keep value but mark as warning
      updateSDEntry(entryId, 'nom', value);
      if (statusEl) statusEl.innerHTML = `<span style="color: #ffc107;" title="${closestMatches.slice(0,3).join(', ')}...">?</span>`;
      input.style.borderColor = '#ffc107';
    } else {
      // No match at all
      updateSDEntry(entryId, 'nom', value);
      if (statusEl) statusEl.innerHTML = '<span style="color: #dc3545;" title="Nom non reconnu dans SetD">✗</span>';
      input.style.borderColor = '#dc3545';
    }
  }
}

// Mapping of SD names to SetD columns (from SETD_PERSONNEL_COLUMNS)
const SETD_PERSONNEL_COLUMNS = {
  'Martine Breton': 'C', 'Petite Caisse': 'E', 'Conc. Banc.': 'F', 'Corr. Mois suivant': 'G',
  'JEAN PHILIPPE': 'H', 'Tristan Tremblay': 'I', 'Mandy Le': 'J', 'Frederic Dupont': 'K',
  'Florence Roy': 'L', 'Marie Carlesso': 'M', 'Patrick Caron': 'N', 'KARL LECLERC': 'O',
  'Stéphane Latulippe': 'P', 'natalie rousseau': 'Q', 'DAVID GIORGI': 'R', 'YOUSSIF GANNI': 'S',
  'MYRLENE BELIVEAU': 'T', 'EMMANUELLE LUSSIER': 'U', 'DANIELLE BELANGER': 'V', 'VALERIE GUERIN': 'W',
  'Youri Georges': 'X', 'Alexandre Thifault': 'Y', 'Julie Dagenais': 'Z', 'PATRICK MARTEL': 'AA',
  'Nelson Dacosta': 'AB', 'NAOMIE COLIN': 'AC', 'SOPHIE CHIARUCCI': 'AD', 'CHRISTOS MORENTZOS': 'AE',
  'WOODS John': 'AF', 'MARCO Sabourin': 'AG', 'sachetti francois': 'AH', 'caouette Phillipe': 'AI',
  'Caron Patrick': 'AJ', 'MIXOLOGUE': 'AK', 'GIOVANNI TOMANELLI': 'AL', 'Mathieu Guerit': 'AN',
  'Marie Eve': 'AO', 'CARL Tourangeau': 'AP', 'MAUDE GAUTHIER': 'AQ', 'Stephane Bernachez': 'AR',
  'Jonathan Samedy': 'AS', 'NICOLAS Bernatchez': 'AT', 'JULIEN BAZAGLE': 'AU', 'Panayota Lappas': 'AV',
  'PLINIO TESTA Campos': 'AW', 'spiro Katsenis': 'AX', 'Isabelle Leclair': 'AY', 'ANAIS BESETTE': 'AZ',
  'DRAGAN MILOVIC': 'BA', 'LIDA RAMASAN': 'BB', 'RAFFI OYAN': 'BC', 'CECIL PATRICIA': 'BD',
  'QUENTIN BRUNET': 'BE', 'Sabrina Gagnon': 'BF', 'NOEMY ROY': 'BG', 'Melanie Guilemette': 'BH',
  'Pierre-luc Lapointe': 'BI', 'Adelaide Rancourt': 'BJ', 'theriault emilie': 'BK', 'Sandra Tremblay': 'BL',
  'DAVID DFAUCHER': 'BM', 'LINDA': 'BN', 'olivier lamothe': 'BO', 'gozzi alexandra': 'BP',
  'Sarah Vesnaver': 'BQ', 'Forget Caroline': 'BR', 'ANDREW STEPHANE': 'BS', 'Tremblay Caroline': 'BT',
  'jessica simon': 'BU', 'Francis Latour': 'BV', 'Constantino Difruschia': 'BW', 'Cuong Tran': 'BX',
  'MATHIEU GUERIT': 'BY', 'Youri George': 'BZ', 'Arnaud Duguay': 'CA', 'JOSE LATUPLIPPE': 'CB',
  'Mixologue 2.0': 'CC', 'MIXOLOGUE 3.0': 'CE', 'Dany Prouxl-Rivard': 'CF', 'JONNI LANGLOIS': 'CG',
  'Laurence': 'CH', 'Morgane Muffait': 'CI', 'NICOLE': 'CJ', 'VICTOR GUEFAELLY': 'CK',
  'Emma Heguy': 'CL', 'MANON RINGROSE': 'CM', 'lethicia heinmeyer': 'CN', 'Stephanie desjardins': 'CO',
  'Elisabetta Lungarini': 'CP', 'France bergeron': 'CR', 'kalena Caticchio': 'CS', 'Nicolle Blanchard': 'CT',
  'DRAGANA RADOVANOVIC': 'CU', 'elena kaltsoudas': 'CV', 'Jean-Seb. Pitre': 'CW', 'CHARLES R': 'CX',
  'Pier Audrey Belanger': 'CY', 'GINO MOURIN': 'CZ', 'Sophie c': 'DA', 'Philippe Caouette': 'DB',
  'Marly Innocent': 'DC', 'MOHAMED ELSABER': 'DD', 'SOULEYMANE CAMARA': 'DE', 'KHALIL MOUATARIF': 'DF',
  'MANOLO C': 'DG', 'Laeticia Nader': 'DH', 'Sylvie Pierre': 'DI', 'Debbie Fleurant-Rioux': 'DJ',
  'Debby Araujo': 'DK', 'Isabelle Caron': 'DL', 'Rose-Delande Mompremier': 'DM', 'ANGELO JOSEPH': 'DN',
  'ANNIE': 'DO', 'JEAN-MICHEL CYR': 'DP', 'damal Kelly': 'DQ', 'JESSICA SIMON': 'DR',
  'levesque MAUDE': 'DS', 'Josée Latulippe': 'DT', 'SARAH MADITUKA': 'DU', 'LEO SCARPA': 'DV',
  'Schneidine': 'DX', 'thaneekan': 'DY', 'AYA BACHARI': 'DZ', 'SEDDIK ZAYEN': 'EA',
  'VALERIE KRAY': 'EB', 'sarah': 'EC', 'OPPONG ZANETA': 'ED', 'guylaine': 'EE',
  'pierre cindy': 'EF', 'Cristancho Natalia': 'EH', 'Durocher Stéphanie': 'EI'
};

// Get SD entries with non-zero variances for SetD export
function getSDVariancesForSetD() {
  const variances = [];
  const unmatched = [];

  sdData.forEach(entry => {
    if (entry.nom && entry.variance !== 0) {
      const nom = entry.nom.trim();
      if (SETD_PERSONNEL_COLUMNS[nom]) {
        variances.push({
          nom: nom,
          variance: entry.variance,
          column: SETD_PERSONNEL_COLUMNS[nom]
        });
      } else {
        unmatched.push(nom);
      }
    }
  });

  return { variances, unmatched };
}

// Update SetD export count indicator
function updateSDSetDCount() {
  const { variances } = getSDVariancesForSetD();
  const countEl = document.getElementById('sd-setd-preview-count');
  if (countEl) {
    countEl.textContent = variances.length;
  }
}

// Show preview of variances to export to SetD
function showSDSetDPreview() {
  const previewEl = document.getElementById('sd-setd-preview');
  const listEl = document.getElementById('sd-setd-preview-list');
  const unmatchedEl = document.getElementById('sd-setd-unmatched');
  const unmatchedNamesEl = document.getElementById('sd-setd-unmatched-names');

  const { variances, unmatched } = getSDVariancesForSetD();

  if (variances.length === 0 && unmatched.length === 0) {
    previewEl.style.display = 'block';
    listEl.innerHTML = '<div style="color: #6c757d; font-style: italic;">Aucune variance à exporter (toutes les variances sont à 0)</div>';
    unmatchedEl.style.display = 'none';
    return;
  }

  // Build preview list
  listEl.innerHTML = variances.map(v => {
    const color = v.variance > 0 ? '#dc3545' : '#28a745';
    const sign = v.variance > 0 ? '+' : '';
    return `
      <div style="background: white; padding: 0.5rem 0.75rem; border-radius: 4px; border-left: 3px solid ${color}; display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: 500; font-size: 0.85rem;">${v.nom}</span>
        <span style="font-weight: 700; color: ${color}; font-size: 0.9rem;">${sign}$${v.variance.toFixed(2)}</span>
      </div>
    `;
  }).join('');

  // Show unmatched names if any
  if (unmatched.length > 0) {
    unmatchedNamesEl.textContent = unmatched.join(', ');
    unmatchedEl.style.display = 'block';
  } else {
    unmatchedEl.style.display = 'none';
  }

  previewEl.style.display = 'block';

  // Re-render feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
}

// Export SD variances to SetD in RJ file
async function exportSDToSetD() {
  const { variances, unmatched } = getSDVariancesForSetD();

  if (variances.length === 0) {
    notify('Aucune variance à exporter vers SetD (toutes les variances sont à 0 ou les noms ne correspondent pas)', 'warning');
    return;
  }

  // Get current day from SD day selector or DueBack day
  const sdDayInput = document.getElementById('sd-current-day');
  const duebackDay = document.getElementById('dueback-current-day');
  let day = sdDayInput ? parseInt(sdDayInput.value) : null;

  if (!day && duebackDay) {
    day = parseInt(duebackDay.textContent);
  }

  if (!day || day < 1 || day > 31) {
    notify('Impossible de déterminer le jour. Veuillez charger un jour SD d\'abord.', 'error');
    return;
  }

  // Confirm with user
  const variancesList = variances.map(v => `${v.nom}: ${v.variance > 0 ? '+' : ''}$${v.variance.toFixed(2)}`).join('\n');
  const confirmMsg = `Exporter ${variances.length} variance(s) vers SetD pour le jour ${day}?\n\n${variancesList}`;

  if (!confirm(confirmMsg)) {
    return;
  }

  try {
    const res = await fetch('/api/sd/export_setd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        day: day,
        variances: variances.map(v => ({ nom: v.nom, variance: v.variance }))
      })
    });

    const data = await res.json();

    if (data.success) {
      notify(data.message, 'success');

      // Show unmatched warning if any
      if (data.unmatched && data.unmatched.length > 0) {
        notify(`Noms non reconnus dans SetD: ${data.unmatched.join(', ')}`, 'warning');
      }
    } else {
      notify(`Erreur: ${data.error}`, 'error');
    }
  } catch (error) {
    console.error('Error exporting to SetD:', error);
    notify(`Erreur réseau: ${error.message}`, 'error');
  }
}

// Upload SD file
async function uploadSDFile() {
  const fileInput = document.getElementById('sd-file-input');
  const file = fileInput.files[0];

  if (!file) {
    alert('Veuillez sélectionner un fichier SD');
    return;
  }

  const formData = new FormData();
  formData.append('sd_file', file);

  try {
    const res = await fetch('/api/sd/upload', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();

    if (data.success) {
      // Show file info
      document.getElementById('sd-filename').textContent = data.file_info.filename;
      document.getElementById('sd-file-size').textContent = `Taille: ${(data.file_info.size / 1024).toFixed(2)} KB`;
      document.getElementById('sd-available-days').textContent = `Jours disponibles: ${data.file_info.available_days.join(', ')}`;
      document.getElementById('sd-file-info').style.display = 'block';
      document.getElementById('sd-day-selector').style.display = 'block';

      // Auto-load day 1
      document.getElementById('sd-current-day').value = 1;
      await loadSDDay();

      alert(data.message);
    } else {
      alert(`Erreur: ${data.error}`);
    }
  } catch (error) {
    console.error('Error uploading SD file:', error);
    alert(`Erreur réseau: ${error.message}`);
  }
}

// Load SD day data
async function loadSDDay() {
  const dayInput = document.getElementById('sd-current-day');
  const day = parseInt(dayInput.value);

  if (!day || day < 1 || day > 31) {
    alert('Le jour doit être entre 1 et 31');
    return;
  }

  try {
    const res = await fetch(`/api/sd/day/${day}`);
    const data = await res.json();

    if (data.success) {
      // Update day info
      document.getElementById('sd-day-date').textContent = data.data.date || '-';
      document.getElementById('sd-day-entries-count').textContent = data.data.entries.length;
      document.getElementById('sd-day-info').style.display = 'block';

      // Load entries into the table
      sdData = data.data.entries.map(entry => ({
        id: Date.now() + Math.random(),
        departement: entry.departement || '',
        nom: entry.nom || '',
        devise: entry.cdn_us || 'CDN',
        montant: entry.montant || 0,
        montant_verifie: entry.montant_verifie || 0,
        remboursement: entry.remboursement || 0,
        variance: entry.variance || 0
      }));

      renderSDTable();

      // Also fetch totals
      const totalsRes = await fetch(`/api/sd/day/${day}/totals`);
      const totalsData = await totalsRes.json();

      if (totalsData.success) {
        console.log('Totals for day', day, ':', totalsData.totals);
      }
    } else {
      alert(`Erreur: ${data.error}`);
    }
  } catch (error) {
    console.error('Error loading SD day:', error);
    alert(`Erreur réseau: ${error.message}`);
  }
}

// Download SD file
async function downloadSDFile() {
  try {
    const res = await fetch('/api/sd/download');

    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SD_${new Date().toISOString().split('T')[0]}.xls`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } else {
      const data = await res.json();
      alert(`Erreur: ${data.error}`);
    }
  } catch (error) {
    console.error('Error downloading SD file:', error);
    alert(`Erreur réseau: ${error.message}`);
  }
}

// Save SD data
async function saveSD() {
  const dayInput = document.getElementById('sd-current-day');
  const day = parseInt(dayInput.value);

  if (!day || day < 1 || day > 31) {
    alert('Veuillez charger un jour avant de sauvegarder');
    return;
  }

  // Convert sdData to API format
  const entries = sdData.map(entry => ({
    departement: entry.departement || '',
    nom: entry.nom || '',
    cdn_us: entry.devise || 'CDN',
    montant: parseFloat(entry.montant) || 0,
    montant_verifie: parseFloat(entry.montant_verifie) || 0,
    remboursement: parseFloat(entry.remboursement) || 0,
    variance: parseFloat(entry.variance) || 0
  }));

  try {
    const res = await fetch(`/api/sd/day/${day}/entries`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entries: entries })
    });

    const data = await res.json();

    if (data.success) {
      alert(data.message);
      // Reload the day to confirm the save
      await loadSDDay();
    } else {
      alert(`Erreur: ${data.error}`);
    }
  } catch (error) {
    console.error('Error saving SD data:', error);
    alert(`Erreur réseau: ${error.message}`);
  }
}

// ============================================================================
// DÉPÔT - GESTION MULTI-ENTRÉES ET AUTO-CALCULS
// ============================================================================

// Storage for depot entries - each entry now has a date
let depotData = {
  client6: [],  // { id, amount, date: "23 DECEMBRE" }
  client8: []
};

const DEPOT_MAX_DAYS = 7;  // Keep only 7 days of entries

// Initialize with one empty row for each client
function initializeDepot() {
  if (depotData.client6.length === 0) {
    addDepotRow('client6');
  }
  if (depotData.client8.length === 0) {
    addDepotRow('client8');
  }
}

// Get current date in format "DD MOIS"
function getDepotDateString(date = new Date()) {
  const months = ['JANVIER', 'FÉVRIER', 'MARS', 'AVRIL', 'MAI', 'JUIN',
                  'JUILLET', 'AOÛT', 'SEPTEMBRE', 'OCTOBRE', 'NOVEMBRE', 'DÉCEMBRE'];
  return `${date.getDate()} ${months[date.getMonth()]}`;
}

// Parse a date string like "23 DECEMBRE" to a Date object (current year)
function parseDepotDate(dateStr) {
  if (!dateStr) return null;
  const months = {
    'JANVIER': 0, 'FÉVRIER': 1, 'MARS': 2, 'AVRIL': 3, 'MAI': 4, 'JUIN': 5,
    'JUILLET': 6, 'AOÛT': 7, 'SEPTEMBRE': 8, 'OCTOBRE': 9, 'NOVEMBRE': 10, 'DÉCEMBRE': 11,
    'FEVRIER': 1, 'AOUT': 7, 'DECEMBRE': 11  // Without accents
  };
  const parts = dateStr.trim().toUpperCase().split(' ');
  if (parts.length < 2) return null;
  const day = parseInt(parts[0]);
  const month = months[parts[1]];
  if (isNaN(day) || month === undefined) return null;
  return new Date(new Date().getFullYear(), month, day);
}

// Get unique dates from a client's entries
function getUniqueDatesForClient(clientId) {
  const dates = new Set();
  depotData[clientId].forEach(entry => {
    if (entry.date) dates.add(entry.date);
  });
  return Array.from(dates);
}

// Count unique days in a client
function countUniqueDays(clientId) {
  return getUniqueDatesForClient(clientId).length;
}

// Get the client with more space (fewer unique days)
function getClientWithMoreSpace() {
  const client6Days = countUniqueDays('client6');
  const client8Days = countUniqueDays('client8');

  // Return the one with fewer days, or client6 if equal
  return client6Days <= client8Days ? 'client6' : 'client8';
}

// Remove entries older than 7 days from a client
function rotateOldEntries(clientId) {
  const uniqueDates = getUniqueDatesForClient(clientId);

  if (uniqueDates.length <= DEPOT_MAX_DAYS) {
    return 0;  // No rotation needed
  }

  // Sort dates (oldest first)
  const sortedDates = uniqueDates.sort((a, b) => {
    const dateA = parseDepotDate(a);
    const dateB = parseDepotDate(b);
    if (!dateA || !dateB) return 0;
    return dateA - dateB;
  });

  // Find dates to remove (oldest ones beyond 7 days)
  const datesToRemove = sortedDates.slice(0, sortedDates.length - DEPOT_MAX_DAYS);

  // Remove entries with those dates
  const originalCount = depotData[clientId].length;
  depotData[clientId] = depotData[clientId].filter(entry =>
    !datesToRemove.includes(entry.date)
  );

  const removedCount = originalCount - depotData[clientId].length;

  if (removedCount > 0) {
    console.log(`Rotation Depot: ${removedCount} entrées supprimées (dates: ${datesToRemove.join(', ')})`);
  }

  return removedCount;
}

// Rotate old entries from both clients
function rotateAllOldEntries() {
  const removed6 = rotateOldEntries('client6');
  const removed8 = rotateOldEntries('client8');

  if (removed6 > 0) renderDepotTable('client6');
  if (removed8 > 0) renderDepotTable('client8');

  return removed6 + removed8;
}

// Update the live Depot preview in SD tab dashboard
function updateLiveDepotPreview() {
  // Get current space for each client
  const client6Days = countUniqueDays('client6');
  const client8Days = countUniqueDays('client8');

  // Determine target client
  const targetClient = getClientWithMoreSpace();
  const targetLabel = targetClient === 'client6' ? 'Client 6' : 'Client 8';

  // Update target indicator
  const targetEl = document.getElementById('live-depot-target');
  if (targetEl) {
    targetEl.textContent = targetLabel;
    targetEl.style.color = targetClient === 'client6' ? '#007bff' : '#17a2b8';
  }

  // Update Client 6 progress bar
  const c6CountEl = document.getElementById('live-depot-c6-count');
  const c6BarEl = document.getElementById('live-depot-c6-bar');
  if (c6CountEl) {
    c6CountEl.textContent = `${client6Days}/7`;
    c6CountEl.style.color = client6Days >= 7 ? '#dc3545' : '#6c757d';
  }
  if (c6BarEl) {
    const c6Percent = Math.min((client6Days / 7) * 100, 100);
    c6BarEl.style.width = c6Percent + '%';
    c6BarEl.style.background = client6Days >= 7 ? '#dc3545' : '#007bff';
  }

  // Update Client 8 progress bar
  const c8CountEl = document.getElementById('live-depot-c8-count');
  const c8BarEl = document.getElementById('live-depot-c8-bar');
  if (c8CountEl) {
    c8CountEl.textContent = `${client8Days}/7`;
    c8CountEl.style.color = client8Days >= 7 ? '#dc3545' : '#6c757d';
  }
  if (c8BarEl) {
    const c8Percent = Math.min((client8Days / 7) * 100, 100);
    c8BarEl.style.width = c8Percent + '%';
    c8BarEl.style.background = client8Days >= 7 ? '#dc3545' : '#17a2b8';
  }

  // Update Client 6 entries list (Excel-style: DATE | MONTANTS | TOTAL)
  const c6EntriesEl = document.getElementById('live-depot-c6-entries');
  const c6TotalEl = document.getElementById('live-depot-c6-total');
  if (c6EntriesEl) {
    const c6Entries = depotData.client6.filter(e => e.amount > 0);
    if (c6Entries.length === 0) {
      c6EntriesEl.innerHTML = '<div style="color: #999; font-style: italic; text-align: center; font-size: 0.65rem;">Vide</div>';
    } else {
      // Group by date (Excel structure: Date once, then amounts, then total)
      const byDate = {};
      c6Entries.forEach(e => {
        const date = e.date || 'Sans date';
        if (!byDate[date]) byDate[date] = [];
        byDate[date].push(e.amount);
      });
      // Render Excel-style
      let html = '';
      Object.entries(byDate).forEach(([date, amounts]) => {
        const dayTotal = amounts.reduce((s, a) => s + a, 0);
        // Date row with first amount
        html += `<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; font-size: 0.6rem; background: #e3f2fd; padding: 0.1rem 0.2rem;">
          <span style="color: #1565c0; font-weight: 600;">${date}</span>
          <span style="text-align: right;">${amounts[0] ? '$' + amounts[0].toFixed(2) : ''}</span>
          <span></span>
        </div>`;
        // Additional amounts (no date)
        for (let i = 1; i < amounts.length; i++) {
          html += `<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; font-size: 0.6rem; padding: 0.1rem 0.2rem;">
            <span></span>
            <span style="text-align: right;">$${amounts[i].toFixed(2)}</span>
            <span></span>
          </div>`;
        }
        // Total row (in SIGNATURE column)
        html += `<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; font-size: 0.6rem; background: #fff8e1; padding: 0.1rem 0.2rem; border-bottom: 1px solid #ddd;">
          <span></span>
          <span></span>
          <span style="text-align: right; font-weight: 700; color: #007bff;">$${dayTotal.toFixed(2)}</span>
        </div>`;
      });
      c6EntriesEl.innerHTML = html;
    }
    const c6Total = c6Entries.reduce((s, e) => s + e.amount, 0);
    if (c6TotalEl) c6TotalEl.textContent = '$' + c6Total.toFixed(2);
  }

  // Update Client 8 entries list (Excel-style)
  const c8EntriesEl = document.getElementById('live-depot-c8-entries');
  const c8TotalEl = document.getElementById('live-depot-c8-total');
  if (c8EntriesEl) {
    const c8Entries = depotData.client8.filter(e => e.amount > 0);
    if (c8Entries.length === 0) {
      c8EntriesEl.innerHTML = '<div style="color: #999; font-style: italic; text-align: center; font-size: 0.65rem;">Vide</div>';
    } else {
      // Group by date
      const byDate = {};
      c8Entries.forEach(e => {
        const date = e.date || 'Sans date';
        if (!byDate[date]) byDate[date] = [];
        byDate[date].push(e.amount);
      });
      // Render Excel-style
      let html = '';
      Object.entries(byDate).forEach(([date, amounts]) => {
        const dayTotal = amounts.reduce((s, a) => s + a, 0);
        // Date row with first amount
        html += `<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; font-size: 0.6rem; background: #e0f7fa; padding: 0.1rem 0.2rem;">
          <span style="color: #00838f; font-weight: 600;">${date}</span>
          <span style="text-align: right;">${amounts[0] ? '$' + amounts[0].toFixed(2) : ''}</span>
          <span></span>
        </div>`;
        // Additional amounts
        for (let i = 1; i < amounts.length; i++) {
          html += `<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; font-size: 0.6rem; padding: 0.1rem 0.2rem;">
            <span></span>
            <span style="text-align: right;">$${amounts[i].toFixed(2)}</span>
            <span></span>
          </div>`;
        }
        // Total row
        html += `<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; font-size: 0.6rem; background: #fff8e1; padding: 0.1rem 0.2rem; border-bottom: 1px solid #ddd;">
          <span></span>
          <span></span>
          <span style="text-align: right; font-weight: 700; color: #17a2b8;">$${dayTotal.toFixed(2)}</span>
        </div>`;
      });
      c8EntriesEl.innerHTML = html;
    }
    const c8Total = c8Entries.reduce((s, e) => s + e.amount, 0);
    if (c8TotalEl) c8TotalEl.textContent = '$' + c8Total.toFixed(2);
  }

  // Show rotation warning if needed
  const rotationEl = document.getElementById('live-depot-rotation');
  if (rotationEl) {
    const targetDays = targetClient === 'client6' ? client6Days : client8Days;
    if (targetDays >= 7) {
      rotationEl.style.display = 'block';
    } else {
      rotationEl.style.display = 'none';
    }
  }
}

// Add a new deposit row for a specific client
function addDepotRow(clientId) {
  const todayStr = getDepotDateString();
  const entry = {
    id: Date.now() + Math.random(),
    amount: 0,
    date: todayStr  // Track date for rotation
  };

  depotData[clientId].push(entry);
  renderDepotTable(clientId);

  // Focus on the new amount input
  setTimeout(() => {
    const tbody = document.getElementById(`depot-${clientId}-body`);
    const lastRow = tbody.lastElementChild;
    if (lastRow) {
      const amountInput = lastRow.querySelector('.depot-amount');
      if (amountInput) amountInput.focus();
    }
  }, 100);
}

// Remove a deposit row
function removeDepotRow(clientId, entryId) {
  depotData[clientId] = depotData[clientId].filter(e => e.id !== entryId);
  renderDepotTable(clientId);
}

// Render the table for a specific client
function renderDepotTable(clientId) {
  const tbody = document.getElementById(`depot-${clientId}-body`);
  const entries = depotData[clientId];

  tbody.innerHTML = '';

  entries.forEach((entry, index) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td class="excel-row-header">${index + 1}</td>
      <td class="excel-cell">
        <input type="number" step="0.01" class="excel-input depot-amount"
               data-client="${clientId}" data-entry-id="${entry.id}"
               value="${entry.amount || ''}" placeholder="0.00"
               onchange="updateDepotEntry('${clientId}', ${entry.id}, 'amount', this.value)">
      </td>
      <td class="excel-cell" style="text-align:center;">
        <button onclick="removeDepotRow('${clientId}', ${entry.id})"
                style="background:#dc3545; color:white; border:none; padding:0.25rem 0.5rem; border-radius:4px; cursor:pointer; font-size:0.75rem;"
                title="Supprimer cette ligne">
          <i data-feather="trash-2" style="width:14px; height:14px;"></i>
        </button>
      </td>
    `;
    tbody.appendChild(row);
  });

  // Re-render feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }

  calculateDepotTotals();
}

// Update a specific entry field
function updateDepotEntry(clientId, entryId, field, value) {
  const entry = depotData[clientId].find(e => e.id === entryId);
  if (entry) {
    if (field === 'amount') {
      entry.amount = parseFloat(value) || 0;
    } else {
      entry[field] = value;
    }
    calculateDepotTotals();
  }
}

// Calculate totals for all clients
function calculateDepotTotals() {
  // Calculate CLIENT 6 total
  const client6Total = depotData.client6.reduce((sum, entry) => sum + (parseFloat(entry.amount) || 0), 0);
  document.getElementById('depot-client6-total').value = client6Total.toFixed(2);

  // Calculate CLIENT 8 total
  const client8Total = depotData.client8.reduce((sum, entry) => sum + (parseFloat(entry.amount) || 0), 0);
  document.getElementById('depot-client8-total').value = client8Total.toFixed(2);

  // Calculate general total
  const generalTotal = client6Total + client8Total;
  document.getElementById('depot-total-general').value = generalTotal.toFixed(2);

  // Update validation indicator
  updateDepotSDValidation();

  // Update live preview in SD tab (if visible)
  if (typeof updateLiveDepotPreview === 'function') {
    updateLiveDepotPreview();
  }
}

// Update the SD preview in Depot tab
function updateDepotSDPreview() {
  const sdTotalVerifie = parseFloat(document.getElementById('sd-total-verifie')?.value) || 0;
  const previewEl = document.getElementById('depot-sd-preview');
  if (previewEl) {
    previewEl.textContent = '$' + sdTotalVerifie.toFixed(2);
  }
}

// Update validation indicator comparing SD and Depot totals
function updateDepotSDValidation() {
  const sdTotal = parseFloat(document.getElementById('sd-total-verifie')?.value) || 0;
  const depotTotal = parseFloat(document.getElementById('depot-total-general')?.value) || 0;
  const validationEl = document.getElementById('depot-sd-validation');

  if (!validationEl) return;

  const diff = Math.abs(sdTotal - depotTotal);

  if (sdTotal === 0 && depotTotal === 0) {
    validationEl.style.display = 'none';
    return;
  }

  validationEl.style.display = 'block';

  if (diff < 0.01) {
    validationEl.innerHTML = `
      <span style="color: #155724;">
        <i data-feather="check-circle" style="width:16px; height:16px; vertical-align:middle;"></i>
        Parfait! SD ($${sdTotal.toFixed(2)}) = Dépôt ($${depotTotal.toFixed(2)})
      </span>`;
  } else {
    validationEl.innerHTML = `
      <span style="color: #721c24;">
        <i data-feather="alert-triangle" style="width:16px; height:16px; vertical-align:middle;"></i>
        Attention: SD ($${sdTotal.toFixed(2)}) ≠ Dépôt ($${depotTotal.toFixed(2)}) - Différence: $${diff.toFixed(2)}
      </span>`;
  }

  // Re-render feather icons
  if (typeof feather !== 'undefined') feather.replace();
}

// Fill Depot from SD "Montant Vérifié" total
function fillDepotFromSD() {
  const sdTotalVerifie = parseFloat(document.getElementById('sd-total-verifie')?.value) || 0;

  if (sdTotalVerifie <= 0) {
    notify('Le SD n\'a pas de Montant Vérifié à importer (total = $0.00)', 'error');
    return;
  }

  // Get today's date string
  const todayStr = getDepotDateString();

  // Choose the client with more space automatically
  const targetClient = getClientWithMoreSpace();
  const clientLabel = targetClient === 'client6' ? 'Client 6' : 'Client 8';

  // Perform rotation to ensure we stay within 7 days limit
  const rotatedCount = rotateOldEntries(targetClient);
  if (rotatedCount > 0) {
    notify(`Rotation automatique: ${rotatedCount} ancienne(s) entrée(s) supprimée(s) de ${clientLabel}`, 'info');
  }

  // Check if there's already an entry for today
  const todayEntries = depotData[targetClient].filter(e => e.date === todayStr);
  if (todayEntries.length > 0) {
    // Add to existing day
    const entry = {
      id: Date.now() + Math.random(),
      amount: sdTotalVerifie,
      date: todayStr
    };
    depotData[targetClient].push(entry);
  } else {
    // New day entry
    const entry = {
      id: Date.now() + Math.random(),
      amount: sdTotalVerifie,
      date: todayStr
    };
    depotData[targetClient].push(entry);
  }

  renderDepotTable(targetClient);

  // Auto-fill date field for this client
  const dateInput = document.getElementById(`depot-${targetClient}-date`);
  if (dateInput) {
    dateInput.value = todayStr;
  }

  // Show space status
  const client6Days = countUniqueDays('client6');
  const client8Days = countUniqueDays('client8');

  notify(`$${sdTotalVerifie.toFixed(2)} importé vers ${clientLabel} (${todayStr}). Espace: Client 6 = ${client6Days}/7 jours, Client 8 = ${client8Days}/7 jours`, 'success');

  // Update validation
  updateDepotSDValidation();
}

// Save depot data
async function saveDepot() {
  // Prepare data for backend
  const depotPayload = {
    date: document.getElementById('selected-date')?.textContent || new Date().toLocaleDateString('fr-CA'),
    client6: depotData.client6.filter(e => e.amount > 0),
    client8: depotData.client8.filter(e => e.amount > 0),
    totals: {
      client6: parseFloat(document.getElementById('depot-client6-total').value || 0),
      client8: parseFloat(document.getElementById('depot-client8-total').value || 0),
      general: parseFloat(document.getElementById('depot-total-general').value || 0)
    }
  };

  console.log('Saving depot data:', depotPayload);

  try {
    const res = await fetch('/api/rj/deposit', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(depotPayload)
    });

    const json = await res.json();
    if (json.success) {
      notify('Dépôt enregistré avec succès!', 'success');
    } else {
      notify(json.error || 'Erreur lors de l\'enregistrement du dépôt', 'error');
    }
  } catch (e) {
    console.error('Error saving depot:', e);
    notify('Erreur réseau lors de l\'enregistrement', 'error');
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  populateSetDNamesDatalist();
  initializeSD();
  initializeDepot();
});
