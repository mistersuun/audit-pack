// ============================================================================
// TRANSELECT AUTO-CALCULATIONS
// ============================================================================

// Section 1: Restaurant - Calculate TOTAL 1 (sum of terminals)
function calculateRestaurantTotal1(row) {
  const terminalCols = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U'];
  let sum = 0;

  terminalCols.forEach(col => {
    const val = parseFloat(document.querySelector(`[data-cell="${col}${row}"]`)?.value || 0);
    sum += val;
  });

  const total1Input = document.querySelector(`[data-cell="V${row}"]`);
  if (total1Input) {
    total1Input.value = sum.toFixed(2);
  }

  return sum;
}

// Section 1: Restaurant - Calculate VARIANCE with visual validation
function calculateRestaurantVariance(row) {
  const total1 = parseFloat(document.querySelector(`[data-cell="V${row}"]`)?.value || 0);
  const total2 = parseFloat(document.querySelector(`[data-cell="W${row}"]`)?.value || 0);
  const positouch = parseFloat(document.querySelector(`[data-cell="X${row}"]`)?.value || 0);

  // VARIANCE = (TOTAL1 + TOTAL2) - POSITOUCH
  const variance = (total1 + total2) - positouch;

  const varianceInput = document.querySelector(`[data-cell="Y${row}"]`);
  if (varianceInput) {
    varianceInput.value = variance.toFixed(2);

    // Visual validation
    if (Math.abs(variance) < 0.01) {
      // Balance! Green
      varianceInput.style.backgroundColor = '#d4edda';
      varianceInput.style.color = '#155724';
      varianceInput.style.fontWeight = '600';
    } else {
      // Ne balance pas! Red
      varianceInput.style.backgroundColor = '#f8d7da';
      varianceInput.style.color = '#721c24';
      varianceInput.style.fontWeight = '600';
    }
  }

  return variance;
}

// Section 1: Restaurant - Calculate $ Escompte and NET
function calculateRestaurantEscompteAndNet(row) {
  const total1 = parseFloat(document.querySelector(`[data-cell="V${row}"]`)?.value || 0);
  const total2 = parseFloat(document.querySelector(`[data-cell="W${row}"]`)?.value || 0);
  const totalAmount = total1 + total2;

  const escomptePct = parseFloat(document.querySelector(`[data-cell="Z${row}"]`)?.value || 0);

  // $ escompte = Total × (Taux / 100)
  const escompteAmt = totalAmount * (escomptePct / 100);

  const escompteInput = document.querySelector(`[data-cell="AA${row}"]`);
  if (escompteInput) {
    escompteInput.value = escompteAmt.toFixed(2);
  }

  // NET = Total - $ escompte
  const net = totalAmount - escompteAmt;

  const netInput = document.querySelector(`[data-cell="AB${row}"]`);
  if (netInput) {
    netInput.value = net.toFixed(2);
  }
}

// Section 1: Restaurant - Recalculate all for one row
function recalculateRestaurantRow(row) {
  calculateRestaurantTotal1(row);
  calculateRestaurantVariance(row);
  calculateRestaurantEscompteAndNet(row);
  calculateRestaurantTotals(); // Update row 14 totals
}

// Section 1: Restaurant - Calculate row 14 totals
function calculateRestaurantTotals() {
  const rows = [9, 10, 11, 12, 13];
  const cols = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'AA', 'AB'];

  cols.forEach(col => {
    if (col === 'Z') return; // Skip escompte %

    let sum = 0;
    rows.forEach(row => {
      const val = parseFloat(document.querySelector(`[data-cell="${col}${row}"]`)?.value || 0);
      sum += val;
    });

    const totalInput = document.querySelector(`[data-cell="${col}14"]`);
    if (totalInput) {
      totalInput.value = sum.toFixed(2);
    }
  });

  // After updating Y14, recalculate master balance
  calculateMasterBalance();
}

// Section 2: Reception - Calculate TOTAL (sum of terminals)
function calculateReceptionTotal(row) {
  const b = parseFloat(document.querySelector(`[data-cell="B${row}"]`)?.value || 0);
  const c = parseFloat(document.querySelector(`[data-cell="C${row}"]`)?.value || 0);
  const d = parseFloat(document.querySelector(`[data-cell="D${row}"]`)?.value || 0);

  const total = b + c + d;

  const totalInput = document.querySelector(`[data-cell="I${row}"]`);
  if (totalInput) {
    totalInput.value = total.toFixed(2);
  }

  return total;
}

// Section 2: Reception - Calculate VARIANCE with visual validation
function calculateReceptionVariance(row) {
  const total = parseFloat(document.querySelector(`[data-cell="I${row}"]`)?.value || 0);
  const dailyRev = parseFloat(document.querySelector(`[data-cell="P${row}"]`)?.value || 0);

  // VARIANCE = TOTAL - Daily Revenue (MUST be 0!)
  const variance = total - dailyRev;

  const varianceInput = document.querySelector(`[data-cell="Q${row}"]`);
  if (varianceInput) {
    varianceInput.value = variance.toFixed(2);

    // Visual validation
    if (Math.abs(variance) < 0.01) {
      // Balance! Green
      varianceInput.style.backgroundColor = '#d4edda';
      varianceInput.style.color = '#155724';
      varianceInput.style.fontWeight = '600';
    } else {
      // ERREUR! Red
      varianceInput.style.backgroundColor = '#f8d7da';
      varianceInput.style.color = '#721c24';
      varianceInput.style.fontWeight = '600';
    }
  }

  return variance;
}

// Section 2: Reception - Calculate $ Escompte and NET GEAC
function calculateReceptionEscompteAndNet(row) {
  const total = parseFloat(document.querySelector(`[data-cell="I${row}"]`)?.value || 0);
  const escomptePct = parseFloat(document.querySelector(`[data-cell="R${row}"]`)?.value || 0);

  // $ escompte = Total × (Taux / 100)
  const escompteAmt = total * (escomptePct / 100);

  const escompteInput = document.querySelector(`[data-cell="S${row}"]`);
  if (escompteInput) {
    escompteInput.value = escompteAmt.toFixed(2);
  }

  // NET GEAC = Total - $ escompte
  const net = total - escompteAmt;

  const netInput = document.querySelector(`[data-cell="T${row}"]`);
  if (netInput) {
    netInput.value = net.toFixed(2);
  }
}

// Section 2: Reception - Recalculate all for one row
function recalculateReceptionRow(row) {
  calculateReceptionTotal(row);
  calculateReceptionVariance(row);
  calculateReceptionEscompteAndNet(row);
  calculateReceptionTotals(); // Update row 25 totals
}

// Section 2: Reception - Calculate row 25 totals
function calculateReceptionTotals() {
  const rows = [20, 21, 22, 24]; // Note: no row 23
  const cols = ['B', 'C', 'D', 'I', 'P', 'Q', 'S', 'T'];

  cols.forEach(col => {
    let sum = 0;
    rows.forEach(row => {
      const val = parseFloat(document.querySelector(`[data-cell="${col}${row}"]`)?.value || 0);
      sum += val;
    });

    const totalInput = document.querySelector(`[data-cell="${col}25"]`);
    if (totalInput) {
      totalInput.value = sum.toFixed(2);
    }
  });

  // After updating Q25, recalculate master balance
  calculateMasterBalance();
}

// MASTER BALANCE: X20 = Q25 + Y14 (Restaurant VARIANCE + Réception VARIANCE)
function calculateMasterBalance() {
  const y14 = parseFloat(document.querySelector('[data-cell="Y14"]')?.value || 0);  // Restaurant TOTAL VARIANCE
  const q25 = parseFloat(document.querySelector('[data-cell="Q25"]')?.value || 0);  // Réception TOTAL VARIANCE

  // MASTER BALANCE = Restaurant VARIANCE + Réception VARIANCE
  const masterBalance = q25 + y14;

  // Update X20 cell in the table
  const masterBalanceInput = document.querySelector('[data-cell="X20"]');
  if (masterBalanceInput) {
    masterBalanceInput.value = masterBalance.toFixed(2);

    // Visual feedback - CRITICAL BALANCING INDICATOR
    if (Math.abs(masterBalance) < 0.01) {
      // PERFECT BALANCE! Green
      masterBalanceInput.style.backgroundColor = '#d4edda';
      masterBalanceInput.style.color = '#155724';
      masterBalanceInput.style.fontWeight = '700';
      masterBalanceInput.style.border = '2px solid #28a745';
    } else if (Math.abs(masterBalance) < 10) {
      // Small variance - Yellow
      masterBalanceInput.style.backgroundColor = '#fff3cd';
      masterBalanceInput.style.color = '#856404';
      masterBalanceInput.style.fontWeight = '700';
      masterBalanceInput.style.border = '2px solid #ffc107';
    } else {
      // Large variance - Red
      masterBalanceInput.style.backgroundColor = '#f8d7da';
      masterBalanceInput.style.color = '#721c24';
      masterBalanceInput.style.fontWeight = '700';
      masterBalanceInput.style.border = '2px solid #dc3545';
    }
  }

  // UPDATE PROMINENT DISPLAY AT TOP
  const displayBox = document.getElementById('master-balance-display');
  const valueDisplay = document.getElementById('master-balance-value');
  const messageDisplay = document.getElementById('master-balance-message');
  const restaurantDisplay = document.getElementById('restaurant-variance-display');
  const receptionDisplay = document.getElementById('reception-variance-display');

  if (valueDisplay) {
    valueDisplay.textContent = '$' + masterBalance.toFixed(2);
  }

  if (restaurantDisplay) {
    restaurantDisplay.textContent = '$' + y14.toFixed(2);
    restaurantDisplay.style.color = Math.abs(y14) < 0.01 ? '#28a745' : '#dc3545';
  }

  if (receptionDisplay) {
    receptionDisplay.textContent = '$' + q25.toFixed(2);
    receptionDisplay.style.color = Math.abs(q25) < 0.01 ? '#28a745' : '#dc3545';
  }

  // Color-code the entire display box
  if (displayBox && valueDisplay && messageDisplay) {
    if (Math.abs(masterBalance) < 0.01) {
      // PERFECT BALANCE! Green
      displayBox.style.background = 'linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%)';
      displayBox.style.borderColor = '#28a745';
      valueDisplay.style.color = '#155724';
      messageDisplay.textContent = '✅ TRANSELECT PARFAITEMENT BALANCÉ!';
      messageDisplay.style.color = '#155724';
    } else if (Math.abs(masterBalance) < 10) {
      // Small variance - Yellow
      displayBox.style.background = 'linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%)';
      displayBox.style.borderColor = '#ffc107';
      valueDisplay.style.color = '#856404';
      messageDisplay.textContent = '⚠️ Petite variance - Vérifier les entrées';
      messageDisplay.style.color = '#856404';
    } else {
      // Large variance - Red
      displayBox.style.background = 'linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%)';
      displayBox.style.borderColor = '#dc3545';
      valueDisplay.style.color = '#721c24';
      messageDisplay.textContent = '❌ VARIANCE IMPORTANTE - Révision requise!';
      messageDisplay.style.color = '#721c24';
    }
  }

  return masterBalance;
}

// Event Listeners - Restaurant Section
document.addEventListener('DOMContentLoaded', () => {
  // Restaurant terminal inputs
  document.querySelectorAll('.transelect-terminal').forEach(input => {
    input.addEventListener('input', function() {
      const row = parseInt(this.dataset.row);
      recalculateRestaurantRow(row);
    });
  });

  // Restaurant total2, positouch, escompte% inputs
  document.querySelectorAll('.transelect-total2, .transelect-positouch, .transelect-escompte-pct').forEach(input => {
    input.addEventListener('input', function() {
      const row = parseInt(this.dataset.row);
      recalculateRestaurantRow(row);
    });
  });

  // Reception terminal inputs
  document.querySelectorAll('.reception-terminal').forEach(input => {
    input.addEventListener('input', function() {
      const row = parseInt(this.dataset.row);
      recalculateReceptionRow(row);
    });
  });

  // Reception daily revenue and escompte% inputs
  document.querySelectorAll('.reception-daily-rev, .reception-escompte-pct').forEach(input => {
    input.addEventListener('input', function() {
      const row = parseInt(this.dataset.row);
      recalculateReceptionRow(row);
    });
  });

  // Excel-like navigation
  setTimeout(() => {
    setupExcelNavigation('#transelect-restaurant-table');
    setupExcelNavigation('#transelect-reception-table');
  }, 100);
});
