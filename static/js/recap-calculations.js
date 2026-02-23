/**
 * Recap Real-time Calculations
 * Recalculates all Net (D) columns and TOTAL rows when inputs change
 */

/**
 * Get value from input by cell reference
 * @param {string} cell - Cell reference (e.g., "B6")
 * @returns {number} Parsed float value or 0 if empty
 */
function getCellValue(cell) {
  const input = document.querySelector(`[data-cell="${cell}"]`);
  if (!input) return 0;

  const value = parseFloat(input.value) || 0;
  return value;
}

/**
 * Format number as currency
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
  const formatted = Math.abs(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return (amount < 0 ? '-$' : '$') + formatted;
}

/**
 * Update a calculated cell's display value
 * @param {string} cellId - ID of the span element to update
 * @param {number} value - Calculated value
 */
function updateCalculatedCell(cellId, value) {
  const span = document.getElementById(cellId);
  if (!span) return;

  span.textContent = formatCurrency(value);

  // Color coding for better visibility
  if (value < 0) {
    span.style.color = (cellId.includes('23') || cellId.includes('b23') || cellId.includes('c23') || cellId.includes('d23')) ? 'white' : '#dc3545'; // Red for negatives
  } else if (value > 0) {
    span.style.color = (cellId.includes('23') || cellId.includes('b23') || cellId.includes('c23') || cellId.includes('d23')) ? 'white' : '#198754'; // Green for positives
  } else {
    span.style.color = (cellId.includes('23') || cellId.includes('b23') || cellId.includes('c23') || cellId.includes('d23')) ? 'white' : '#495057'; // Gray for zero
  }
}

/**
 * Main recalculation function - runs on every input change
 */
function recalculateRecap() {
  // Get all B and C values from inputs
  const b6 = getCellValue('B6');
  const c6 = getCellValue('C6');
  const b7 = getCellValue('B7');
  const c7 = getCellValue('C7');
  const b8 = getCellValue('B8');
  const c8 = getCellValue('C8');
  const b9 = getCellValue('B9');
  const c9 = getCellValue('C9');
  const b11 = getCellValue('B11');
  const c11 = getCellValue('C11');
  const b12 = getCellValue('B12');
  const c12 = getCellValue('C12');
  const b16 = getCellValue('B16');
  const c16 = getCellValue('C16');
  const b17 = getCellValue('B17');
  const c17 = getCellValue('C17');
  const b19 = getCellValue('B19');
  const c19 = getCellValue('C19');

  // Calculate D (Net) = B + C for each row
  const d6 = b6 + c6;
  const d7 = b7 + c7;
  const d8 = b8 + c8;
  const d9 = b9 + c9;
  const d11 = b11 + c11;
  const d12 = b12 + c12;
  const d16 = b16 + c16;
  const d17 = b17 + c17;
  const d19 = b19 + c19;

  // Update all D column displays
  updateCalculatedCell('recap-d6', d6);
  updateCalculatedCell('recap-d7', d7);
  updateCalculatedCell('recap-d8', d8);
  updateCalculatedCell('recap-d9', d9);
  updateCalculatedCell('recap-d11', d11);
  updateCalculatedCell('recap-d12', d12);
  updateCalculatedCell('recap-d16', d16);
  updateCalculatedCell('recap-d17', d17);
  updateCalculatedCell('recap-d19', d19);

  // Row 10: TOTAL cash & checks
  // B10 = B6 + B7 + B8 + B9
  const b10 = b6 + b7 + b8 + b9;
  const c10 = c6 + c7 + c8 + c9;
  const d10 = d6 + d7 + d8 + d9;

  updateCalculatedCell('recap-b10', b10);
  updateCalculatedCell('recap-c10', c10);
  updateCalculatedCell('recap-d10', d10);

  // Row 14: TOTAL après remboursements
  // B14 = B10 - |B11| - |B12| (remboursements are always subtracted)
  // Use Math.abs() to ensure remboursements are always subtracted, regardless of sign entered
  const b14 = b10 - Math.abs(b11) - Math.abs(b12);
  const c14 = c10 - Math.abs(c11) - Math.abs(c12);
  const d14 = d10 - Math.abs(d11) - Math.abs(d12);

  updateCalculatedCell('recap-b14', b14);
  updateCalculatedCell('recap-c14', c14);
  updateCalculatedCell('recap-d14', d14);

  // Row 18: Total à déposer
  // B18 = B14 + B15 + B16 + B17 (B15 = 0, Exchange US not used for now)
  const b18 = b14 + b16 + b17;
  const c18 = c14 + c16 + c17;
  const d18 = d14 + d16 + d17;

  updateCalculatedCell('recap-b18', b18);
  updateCalculatedCell('recap-c18', c18);
  updateCalculatedCell('recap-d18', d18);

  // Row 20: Total dépôt net
  // B20 = B18 + B19
  const b20 = b18 + b19;
  const c20 = c18 + c19;
  const d20 = d18 + d19;

  updateCalculatedCell('recap-b20', b20);
  updateCalculatedCell('recap-c20', c20);
  updateCalculatedCell('recap-d20', d20);

  // Row 23: BALANCE FINALE
  // B23 = B20 - B21 - B22
  // B21 (Dépôt US) = 0 for now
  // B22 (Dépôt Canadien) = from SD file, for this calculation = 0
  // In practice, B22 comes from Excel formula linking to SD file
  const b23 = b20;
  const c23 = c20;
  const d23 = d20;

  updateCalculatedCell('recap-b23', b23);
  updateCalculatedCell('recap-c23', c23);
  updateCalculatedCell('recap-d23', d23);

  // Update the balance indicator at the top of the page
  updateBalanceIndicator(d23);
}

/**
 * Update the balance indicator panel at top of Recap form
 * @param {number} balance - The D23 balance value
 */
function updateBalanceIndicator(balance) {
  const balanceValue = document.getElementById('recap-balance-value');
  const balanceMessage = document.getElementById('recap-balance-message');

  if (!balanceValue) return;

  balanceValue.textContent = formatCurrency(balance);

  // Update color and message based on balance
  if (Math.abs(balance) < 0.01) {
    // Balanced!
    balanceValue.style.color = '#198754';
    if (balanceMessage) {
      balanceMessage.textContent = '✅ Parfait! Le RECAP balance.';
      balanceMessage.style.color = '#198754';
    }
  } else {
    // Not balanced
    balanceValue.style.color = '#dc3545';
    if (balanceMessage) {
      balanceMessage.textContent = `⚠️ Différence de ${formatCurrency(balance)}`;
      balanceMessage.style.color = '#dc3545';
    }
  }

  // Also update the old balance display if it exists
  const oldBalanceDisplay = document.getElementById('recap-balance');
  if (oldBalanceDisplay) {
    oldBalanceDisplay.textContent = formatCurrency(balance);
    oldBalanceDisplay.style.color = Math.abs(balance) < 0.01 ? '#198754' : '#dc3545';
  }

  // Update status message
  const statusDisplay = document.getElementById('recap-balance-status');
  if (statusDisplay) {
    if (Math.abs(balance) < 0.01) {
      statusDisplay.textContent = '✅ Le RECAP balance correctement';
      statusDisplay.style.color = '#198754';
    } else {
      statusDisplay.textContent = `⚠️ Attention: Différence de ${formatCurrency(balance)}`;
      statusDisplay.style.color = '#dc3545';
    }
  }
}

/**
 * Handle data-always-negative attribute
 * Automatically convert positive inputs to negative
 */
function handleAlwaysNegative() {
  const negativeInputs = document.querySelectorAll('[data-always-negative="true"]');
  negativeInputs.forEach(input => {
    input.addEventListener('input', function() {
      if (this.value && parseFloat(this.value) > 0) {
        this.value = -Math.abs(parseFloat(this.value));
      }
    });

    input.addEventListener('blur', function() {
      if (this.value && parseFloat(this.value) > 0) {
        this.value = -Math.abs(parseFloat(this.value));
      }
    });
  });
}

/**
 * Handle data-always-positive attribute
 * Automatically convert negative inputs to positive
 */
function handleAlwaysPositive() {
  const positiveInputs = document.querySelectorAll('[data-always-positive="true"]');
  positiveInputs.forEach(input => {
    input.addEventListener('input', function() {
      if (this.value && parseFloat(this.value) < 0) {
        this.value = Math.abs(parseFloat(this.value));
      }
    });

    input.addEventListener('blur', function() {
      if (this.value && parseFloat(this.value) < 0) {
        this.value = Math.abs(parseFloat(this.value));
      }
    });
  });
}

/**
 * Cross-check validation for recap calculations
 * Verifies that all formulas are correct after recalculation
 */
function validateRecapCrossChecks() {
  const warnings = [];
  const failedCells = [];

  // Get all calculated values
  const d6 = getCellValue('B6') + getCellValue('C6');
  const d7 = getCellValue('B7') + getCellValue('C7');
  const d8 = getCellValue('B8') + getCellValue('C8');
  const d9 = getCellValue('B9') + getCellValue('C9');
  const d11 = getCellValue('B11') + getCellValue('C11');
  const d12 = getCellValue('B12') + getCellValue('C12');
  const d16 = getCellValue('B16') + getCellValue('C16');
  const d17 = getCellValue('B17') + getCellValue('C17');
  const d19 = getCellValue('B19') + getCellValue('C19');

  const b6 = getCellValue('B6');
  const b7 = getCellValue('B7');
  const b8 = getCellValue('B8');
  const b9 = getCellValue('B9');
  const b11 = getCellValue('B11');
  const b12 = getCellValue('B12');
  const b16 = getCellValue('B16');
  const b17 = getCellValue('B17');
  const b19 = getCellValue('B19');

  const c6 = getCellValue('C6');
  const c7 = getCellValue('C7');
  const c8 = getCellValue('C8');
  const c9 = getCellValue('C9');
  const c11 = getCellValue('C11');
  const c12 = getCellValue('C12');
  const c16 = getCellValue('C16');
  const c17 = getCellValue('C17');
  const c19 = getCellValue('C19');

  // Check 1: D = B + C for detail rows (6-9, 11-12, 16-17, 19)
  const detailRows = [
    { row: 6, d: d6, b: b6, c: c6 },
    { row: 7, d: d7, b: b7, c: c7 },
    { row: 8, d: d8, b: b8, c: c8 },
    { row: 9, d: d9, b: b9, c: c9 },
    { row: 11, d: d11, b: b11, c: c11 },
    { row: 12, d: d12, b: b12, c: c12 },
    { row: 16, d: d16, b: b16, c: c16 },
    { row: 17, d: d17, b: b17, c: c17 },
    { row: 19, d: d19, b: b19, c: c19 }
  ];

  detailRows.forEach(({ row, d, b, c }) => {
    const expected = b + c;
    if (Math.abs(d - expected) > 0.001) {
      warnings.push(`Row ${row}: D should equal B + C (expected ${expected}, got ${d})`);
      failedCells.push(`recap-d${row}`);
    }
  });

  // Check 2: Row 10 (TOTAL) = sum of rows 6-9
  const b10_calculated = b6 + b7 + b8 + b9;
  const c10_calculated = c6 + c7 + c8 + c9;
  const d10_calculated = d6 + d7 + d8 + d9;

  const b10_span = document.getElementById('recap-b10');
  const c10_span = document.getElementById('recap-c10');
  const d10_span = document.getElementById('recap-d10');

  if (b10_span) {
    const b10_display = parseFloat(b10_span.textContent.replace(/[$,]/g, '')) || 0;
    if (Math.abs(b10_display - b10_calculated) > 0.001) {
      warnings.push(`Row 10 (B): Should be sum of rows 6-9 (expected ${b10_calculated})`);
      failedCells.push('recap-b10');
    }
  }

  if (c10_span) {
    const c10_display = parseFloat(c10_span.textContent.replace(/[$,]/g, '')) || 0;
    if (Math.abs(c10_display - c10_calculated) > 0.001) {
      warnings.push(`Row 10 (C): Should be sum of rows 6-9 (expected ${c10_calculated})`);
      failedCells.push('recap-c10');
    }
  }

  if (d10_span) {
    const d10_display = parseFloat(d10_span.textContent.replace(/[$,]/g, '')) || 0;
    if (Math.abs(d10_display - d10_calculated) > 0.001) {
      warnings.push(`Row 10 (D): Should be sum of rows 6-9 (expected ${d10_calculated})`);
      failedCells.push('recap-d10');
    }
  }

  // Check 3: Row 14 = Row 10 - |Row 11| - |Row 12|
  const b14_calculated = b10_calculated - Math.abs(b11) - Math.abs(b12);
  const c14_calculated = c10_calculated - Math.abs(c11) - Math.abs(c12);
  const d14_calculated = d10_calculated - Math.abs(d11) - Math.abs(d12);

  const b14_span = document.getElementById('recap-b14');
  const c14_span = document.getElementById('recap-c14');
  const d14_span = document.getElementById('recap-d14');

  if (b14_span) {
    const b14_display = parseFloat(b14_span.textContent.replace(/[$,]/g, '')) || 0;
    if (Math.abs(b14_display - b14_calculated) > 0.001) {
      warnings.push(`Row 14 (B): Should be Row 10 - |Row 11| - |Row 12| (expected ${b14_calculated})`);
      failedCells.push('recap-b14');
    }
  }

  if (c14_span) {
    const c14_display = parseFloat(c14_span.textContent.replace(/[$,]/g, '')) || 0;
    if (Math.abs(c14_display - c14_calculated) > 0.001) {
      warnings.push(`Row 14 (C): Should be Row 10 - |Row 11| - |Row 12| (expected ${c14_calculated})`);
      failedCells.push('recap-c14');
    }
  }

  if (d14_span) {
    const d14_display = parseFloat(d14_span.textContent.replace(/[$,]/g, '')) || 0;
    if (Math.abs(d14_display - d14_calculated) > 0.001) {
      warnings.push(`Row 14 (D): Should be Row 10 - |Row 11| - |Row 12| (expected ${d14_calculated})`);
      failedCells.push('recap-d14');
    }
  }

  // Check 4: Row 18 = Row 14 + Row 16 + Row 17
  const b18_calculated = b14_calculated + b16 + b17;
  const c18_calculated = c14_calculated + c16 + c17;
  const d18_calculated = d14_calculated + d16 + d17;

  const b18_span = document.getElementById('recap-b18');
  const c18_span = document.getElementById('recap-c18');
  const d18_span = document.getElementById('recap-d18');

  if (b18_span) {
    const b18_display = parseFloat(b18_span.textContent.replace(/[$,]/g, '')) || 0;
    if (Math.abs(b18_display - b18_calculated) > 0.001) {
      warnings.push(`Row 18 (B): Should be Row 14 + Row 16 + Row 17 (expected ${b18_calculated})`);
      failedCells.push('recap-b18');
    }
  }

  if (c18_span) {
    const c18_display = parseFloat(c18_span.textContent.replace(/[$,]/g, '')) || 0;
    if (Math.abs(c18_display - c18_calculated) > 0.001) {
      warnings.push(`Row 18 (C): Should be Row 14 + Row 16 + Row 17 (expected ${c18_calculated})`);
      failedCells.push('recap-c18');
    }
  }

  if (d18_span) {
    const d18_display = parseFloat(d18_span.textContent.replace(/[$,]/g, '')) || 0;
    if (Math.abs(d18_display - d18_calculated) > 0.001) {
      warnings.push(`Row 18 (D): Should be Row 14 + Row 16 + Row 17 (expected ${d18_calculated})`);
      failedCells.push('recap-d18');
    }
  }

  // Check 5: Row 20 = Row 18 + Row 19
  const b20_calculated = b18_calculated + b19;
  const c20_calculated = c18_calculated + c19;
  const d20_calculated = d18_calculated + d19;

  const b20_span = document.getElementById('recap-b20');
  const c20_span = document.getElementById('recap-c20');
  const d20_span = document.getElementById('recap-d20');

  if (b20_span) {
    const b20_display = parseFloat(b20_span.textContent.replace(/[$,]/g, '')) || 0;
    if (Math.abs(b20_display - b20_calculated) > 0.001) {
      warnings.push(`Row 20 (B): Should be Row 18 + Row 19 (expected ${b20_calculated})`);
      failedCells.push('recap-b20');
    }
  }

  if (c20_span) {
    const c20_display = parseFloat(c20_span.textContent.replace(/[$,]/g, '')) || 0;
    if (Math.abs(c20_display - c20_calculated) > 0.001) {
      warnings.push(`Row 20 (C): Should be Row 18 + Row 19 (expected ${c20_calculated})`);
      failedCells.push('recap-c20');
    }
  }

  if (d20_span) {
    const d20_display = parseFloat(d20_span.textContent.replace(/[$,]/g, '')) || 0;
    if (Math.abs(d20_display - d20_calculated) > 0.001) {
      warnings.push(`Row 20 (D): Should be Row 18 + Row 19 (expected ${d20_calculated})`);
      failedCells.push('recap-d20');
    }
  }

  // Display warnings or clear them
  displayRecapWarnings(warnings, failedCells);
}

/**
 * Display warnings in the recap-warnings element
 * @param {array} warnings - Array of warning messages
 * @param {array} failedCells - Array of cell IDs that failed validation
 */
function displayRecapWarnings(warnings, failedCells) {
  let warningContainer = document.getElementById('recap-warnings');

  // Create the warning container if it doesn't exist
  if (!warningContainer) {
    warningContainer = document.createElement('div');
    warningContainer.id = 'recap-warnings';
    warningContainer.style.cssText = `
      margin: 15px 0;
      padding: 12px 15px;
      border-radius: 4px;
      font-size: 14px;
      display: none;
    `;

    const recapForm = document.querySelector('[data-recap-form]') || document.querySelector('.recap-form');
    if (recapForm) {
      recapForm.insertBefore(warningContainer, recapForm.firstChild);
    }
  }

  // Remove previous highlighting
  document.querySelectorAll('.recap-check-failed').forEach(cell => {
    cell.classList.remove('recap-check-failed');
  });

  if (warnings.length === 0) {
    // All checks passed
    warningContainer.style.display = 'none';
    warningContainer.innerHTML = '';
    updateCheckIndicators(true);
  } else {
    // Show warnings
    warningContainer.style.display = 'block';
    warningContainer.style.backgroundColor = '#fff3cd';
    warningContainer.style.borderLeft = '4px solid #ffc107';
    warningContainer.innerHTML = '<strong>Validation Warnings:</strong><ul style="margin: 8px 0 0 20px; padding: 0;">' +
      warnings.map(w => `<li>${w}</li>`).join('') +
      '</ul>';

    // Highlight failed cells
    failedCells.forEach(cellId => {
      const cell = document.getElementById(cellId);
      if (cell) {
        cell.classList.add('recap-check-failed');
        cell.style.backgroundColor = '#ffcccc';
        cell.style.padding = '2px 4px';
        cell.style.borderRadius = '3px';
      }
    });

    updateCheckIndicators(false);
  }
}

/**
 * Update the checkmark/warning indicators for total rows
 * @param {boolean} allValid - Whether all validations passed
 */
function updateCheckIndicators(allValid) {
  const totalRows = [10, 14, 18, 20, 23];

  totalRows.forEach(row => {
    const indicator = document.getElementById(`recap-check-indicator-${row}`);
    if (indicator) {
      if (allValid) {
        indicator.innerHTML = '✓';
        indicator.style.color = '#198754';
        indicator.style.fontSize = '16px';
        indicator.style.fontWeight = 'bold';
      } else {
        indicator.innerHTML = '⚠';
        indicator.style.color = '#ffc107';
        indicator.style.fontSize = '16px';
        indicator.style.fontWeight = 'bold';
      }
    }
  });
}

/**
 * Show preview of values that will be sent to Jour
 * Maps Recap row 18 Net values (D14, D16, D17, D18, D19, D20, D23) to Jour columns (BU-CA)
 */
function showJourPreview() {
  // Get the values from Recap row 18 (which are the 7 values sent to Jour)
  const jourMapping = [
    { recapCell: 'D14', jourCol: 'BU', jourColNum: 72, label: 'Cash CDN (après remboursements)' },
    { recapCell: 'D16', jourCol: 'BV', jourColNum: 73, label: 'Exchange - EURO' },
    { recapCell: 'D17', jourCol: 'BW', jourColNum: 74, label: 'Exchange - USA' },
    { recapCell: 'D18', jourCol: 'BX', jourColNum: 75, label: 'Total à déposer' },
    { recapCell: 'D19', jourCol: 'BY', jourColNum: 76, label: 'Intérêt/Frais' },
    { recapCell: 'D20', jourCol: 'BZ', jourColNum: 77, label: 'Total dépôt net' },
    { recapCell: 'D23', jourCol: 'CA', jourColNum: 78, label: 'Balance finale' }
  ];

  // Create or get preview panel
  let previewPanel = document.getElementById('jour-preview-panel');
  if (!previewPanel) {
    previewPanel = document.createElement('div');
    previewPanel.id = 'jour-preview-panel';
    previewPanel.style.cssText = `
      margin: 20px 0;
      padding: 15px;
      border: 2px solid #007bff;
      border-radius: 4px;
      background-color: #f0f7ff;
      display: none;
    `;

    const recapForm = document.querySelector('[data-recap-form]') || document.querySelector('.recap-form');
    if (recapForm) {
      recapForm.appendChild(previewPanel);
    }
  }

  // Build the preview content
  let previewHTML = '<h4 style="margin-top: 0; color: #007bff;">Aperçu - Envoi dans Jour:</h4>';
  previewHTML += '<table style="width: 100%; border-collapse: collapse; font-size: 14px;">';
  previewHTML += '<tr style="background-color: #e3f2fd;"><th style="padding: 8px; text-align: left; border: 1px solid #90caf9;">Colonne Jour</th><th style="padding: 8px; text-align: left; border: 1px solid #90caf9;">Libellé</th><th style="padding: 8px; text-align: right; border: 1px solid #90caf9;">Montant</th></tr>';

  jourMapping.forEach(mapping => {
    const valueSpan = document.getElementById(`recap-${mapping.recapCell}`);
    let value = 0;

    if (valueSpan) {
      value = parseFloat(valueSpan.textContent.replace(/[$,]/g, '')) || 0;
    }

    const formattedValue = formatCurrency(value);
    previewHTML += `<tr style="border-bottom: 1px solid #90caf9;">
      <td style="padding: 8px; border: 1px solid #90caf9; font-weight: bold;">${mapping.jourCol} (col ${mapping.jourColNum})</td>
      <td style="padding: 8px; border: 1px solid #90caf9;">${mapping.label}</td>
      <td style="padding: 8px; text-align: right; border: 1px solid #90caf9;">${formattedValue}</td>
    </tr>`;
  });

  previewHTML += '</table>';
  previewHTML += '<div style="margin-top: 15px; display: flex; gap: 10px;">';
  previewHTML += '<button id="jour-send-button" style="padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold;">Envoie dans Jour ▶</button>';
  previewHTML += '<button id="jour-cancel-button" style="padding: 10px 20px; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">Annuler</button>';
  previewHTML += '</div>';

  previewPanel.innerHTML = previewHTML;
  previewPanel.style.display = 'block';

  // Attach event listeners to buttons
  const sendButton = document.getElementById('jour-send-button');
  const cancelButton = document.getElementById('jour-cancel-button');

  if (sendButton) {
    sendButton.addEventListener('click', confirmAndSendToJour);
  }

  if (cancelButton) {
    cancelButton.addEventListener('click', function() {
      previewPanel.style.display = 'none';
    });
  }
}

/**
 * Confirm and send to Jour with a confirmation dialog
 */
function confirmAndSendToJour() {
  const confirmed = confirm(
    'Êtes-vous sûr de vouloir envoyer ces valeurs au formulaire Jour?\n\n' +
    'Cette action enverra les montants calculés du RECAP vers les colonnes correspondantes du formulaire Jour.'
  );

  if (confirmed) {
    sendRecapToJour();
  }
}

/**
 * Send Recap values to Jour form
 * Maps Recap columns to Jour columns
 */
function sendRecapToJour() {
  const jourMapping = [
    { recapCell: 'D14', jourCell: 'BU19' },
    { recapCell: 'D16', jourCell: 'BV19' },
    { recapCell: 'D17', jourCell: 'BW19' },
    { recapCell: 'D18', jourCell: 'BX19' },
    { recapCell: 'D19', jourCell: 'BY19' },
    { recapCell: 'D20', jourCell: 'BZ19' },
    { recapCell: 'D23', jourCell: 'CA19' }
  ];

  try {
    jourMapping.forEach(mapping => {
      const recapSpan = document.getElementById(`recap-${mapping.recapCell}`);
      const jourInput = document.querySelector(`[data-cell="${mapping.jourCell}"]`);

      if (recapSpan && jourInput) {
        const value = parseFloat(recapSpan.textContent.replace(/[$,]/g, '')) || 0;
        jourInput.value = value;

        // Trigger change event so other calculations update
        const event = new Event('change', { bubbles: true });
        jourInput.dispatchEvent(event);
      }
    });

    // Hide the preview panel
    const previewPanel = document.getElementById('jour-preview-panel');
    if (previewPanel) {
      previewPanel.style.display = 'none';
    }

    // Show success message
    alert('✅ Les valeurs du RECAP ont été envoyées au formulaire Jour avec succès!');

    console.log('Recap values sent to Jour');
  } catch (error) {
    console.error('Error sending Recap to Jour:', error);
    alert('⚠️ Erreur lors de l\'envoi des valeurs. Veuillez vérifier la console.');
  }
}

/**
 * Initialize check indicators for total rows
 */
function initCheckIndicators() {
  const totalRows = [10, 14, 18, 20, 23];

  totalRows.forEach(row => {
    const cells = document.querySelectorAll(`#recap-d${row}, #recap-c${row}, #recap-b${row}`);
    cells.forEach(cell => {
      if (cell && !document.getElementById(`recap-check-indicator-${row}`)) {
        const indicator = document.createElement('span');
        indicator.id = `recap-check-indicator-${row}`;
        indicator.className = 'recap-check-indicator';
        indicator.style.cssText = `
          display: inline-block;
          margin-left: 8px;
          font-size: 16px;
          font-weight: bold;
          color: #198754;
        `;
        indicator.innerHTML = '✓';
        cell.parentElement.appendChild(indicator);
      }
    });
  });
}

/**
 * Initialize Recap calculations
 * Attach event listeners to all inputs and run initial calculation
 */
function initRecapCalculations() {
  // Find all recap inputs (those with data-cell attributes starting with B or C)
  const recapInputs = document.querySelectorAll('.recap-calc-input, [data-cell^="B"], [data-cell^="C"]');

  // Attach both 'input' and 'change' listeners for real-time updates
  recapInputs.forEach(input => {
    input.addEventListener('input', function() {
      recalculateRecap();
      validateRecapCrossChecks();
    });
    input.addEventListener('change', function() {
      recalculateRecap();
      validateRecapCrossChecks();
    });
  });

  // Handle always-negative and always-positive fields
  handleAlwaysNegative();
  handleAlwaysPositive();

  // Initialize check indicators
  initCheckIndicators();

  // Run initial calculation
  recalculateRecap();
  validateRecapCrossChecks();

  console.log('✅ Recap calculations initialized with validation and preview');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initRecapCalculations);
} else {
  // DOM already loaded
  initRecapCalculations();
}

// Also export for use in other scripts if needed
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    recalculateRecap,
    getCellValue,
    formatCurrency,
    updateCalculatedCell
  };
}
