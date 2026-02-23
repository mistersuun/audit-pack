// ============================================================================
// GEAC/UX AUTO-CALCULATIONS
// ============================================================================

// Section 1: Calculate TOTAL for each card type
function calculateGeacTotal(cardType) {
  const cashOutInput = document.querySelector(`[data-cell*="6"][data-card="${cardType}"]`);
  const totalInput = document.querySelector(`[data-cell*="10"][data-card="${cardType}"]`);

  if (cashOutInput && totalInput) {
    const cashOut = parseFloat(cashOutInput.value || 0);
    // For now, TOTAL = Daily Cash Out (may have other components in rows 7-9)
    totalInput.value = cashOut.toFixed(2);
  }
}

// Section 1: Calculate VARIANCE with visual validation (TOTAL vs Daily Revenue)
function calculateGeacVariance(cardType) {
  const totalInput = document.querySelector(`[data-cell*="10"][data-card="${cardType}"]`);
  const dailyRevInput = document.querySelector(`[data-cell*="12"][data-card="${cardType}"]`);
  const varianceInput = document.querySelector(`[data-cell*="13"][data-card="${cardType}"]`);

  if (totalInput && dailyRevInput && varianceInput) {
    const total = parseFloat(totalInput.value || 0);
    const dailyRev = parseFloat(dailyRevInput.value || 0);

    // VARIANCE = TOTAL - Daily Revenue (MUST be 0!)
    const variance = total - dailyRev;
    varianceInput.value = variance.toFixed(2);

    // Visual validation
    if (Math.abs(variance) < 0.01) {
      // Balance! Green
      varianceInput.style.backgroundColor = '#d4edda';
      varianceInput.style.color = '#155724';
    } else {
      // ERREUR! Red
      varianceInput.style.backgroundColor = '#f8d7da';
      varianceInput.style.color = '#721c24';
    }
  }
}

// Section 1: Recalculate all card types
function recalculateGeacReconciliation() {
  const cardTypes = ['amex', 'diners', 'master', 'visa', 'discover'];
  cardTypes.forEach(cardType => {
    calculateGeacTotal(cardType);
    calculateGeacVariance(cardType);
  });
}

// Section 2: Calculate Balance Sheet Variances
function calculateBalancePrevVariance() {
  const daily = parseFloat(document.querySelector('[data-cell="B32"]')?.value || 0);
  const ledger = parseFloat(document.querySelector('[data-cell="E32"]')?.value || 0);
  const varianceInput = document.querySelector('[data-cell="F32"]');

  if (varianceInput) {
    const variance = daily - ledger;
    varianceInput.value = variance.toFixed(2);

    if (Math.abs(variance) < 0.01) {
      varianceInput.style.backgroundColor = '#d4edda';
      varianceInput.style.color = '#155724';
    } else {
      varianceInput.style.backgroundColor = '#f8d7da';
      varianceInput.style.color = '#721c24';
    }
  }
}

function calculateBalanceTodayVariance() {
  const daily = parseFloat(document.querySelector('[data-cell="B37"]')?.value || 0);
  const ledger = parseFloat(document.querySelector('[data-cell="E37"]')?.value || 0);
  const varianceInput = document.querySelector('[data-cell="F37"]');

  if (varianceInput) {
    const variance = daily - ledger;
    varianceInput.value = variance.toFixed(2);

    if (Math.abs(variance) < 0.01) {
      varianceInput.style.backgroundColor = '#d4edda';
      varianceInput.style.color = '#155724';
    } else {
      varianceInput.style.backgroundColor = '#f8d7da';
      varianceInput.style.color = '#721c24';
    }
  }
}

function calculateFactureVariance() {
  const daily = parseFloat(document.querySelector('[data-cell="B41"]')?.value || 0);
  const ledger = parseFloat(document.querySelector('[data-cell="G41"]')?.value || 0);
  const varianceInput = document.querySelector('[data-cell="H41"]');

  if (varianceInput) {
    const variance = daily - ledger;
    varianceInput.value = variance.toFixed(2);

    if (Math.abs(variance) < 0.01) {
      varianceInput.style.backgroundColor = '#d4edda';
      varianceInput.style.color = '#155724';
    } else {
      varianceInput.style.backgroundColor = '#f8d7da';
      varianceInput.style.color = '#721c24';
    }
  }
}

function calculateAdvDepositVariance() {
  const daily = parseFloat(document.querySelector('[data-cell="B44"]')?.value || 0);
  const applied = parseFloat(document.querySelector('[data-cell="J44"]')?.value || 0);
  const varianceInput = document.querySelector('[data-cell="K44"]');

  if (varianceInput) {
    const variance = daily - applied;
    varianceInput.value = variance.toFixed(2);

    if (Math.abs(variance) < 0.01) {
      varianceInput.style.backgroundColor = '#d4edda';
      varianceInput.style.color = '#155724';
    } else {
      varianceInput.style.backgroundColor = '#f8d7da';
      varianceInput.style.color = '#721c24';
    }
  }
}

function calculateNewBalance() {
  // New Balance = Balance Previous + Balance Today + Facture Direct + Adv Deposit Applied
  const balPrevDaily = parseFloat(document.querySelector('[data-cell="B32"]')?.value || 0);
  const balTodayDaily = parseFloat(document.querySelector('[data-cell="B37"]')?.value || 0);
  const factureDaily = parseFloat(document.querySelector('[data-cell="B41"]')?.value || 0);
  const advDaily = parseFloat(document.querySelector('[data-cell="B44"]')?.value || 0);

  const balPrevLedger = parseFloat(document.querySelector('[data-cell="E32"]')?.value || 0);
  const balTodayLedger = parseFloat(document.querySelector('[data-cell="E37"]')?.value || 0);
  const factureLedger = parseFloat(document.querySelector('[data-cell="G41"]')?.value || 0);
  const advApplied = parseFloat(document.querySelector('[data-cell="J44"]')?.value || 0);

  const newBalDaily = balPrevDaily + balTodayDaily + factureDaily + advDaily;
  const newBalLedger = balPrevLedger + balTodayLedger + factureLedger + advApplied;

  const dailyInput = document.querySelector('[data-cell="B53"]');
  const ledgerInput = document.querySelector('[data-cell="E53"]');
  const varianceInput = document.querySelector('[data-cell="F53"]');

  if (dailyInput) dailyInput.value = newBalDaily.toFixed(2);
  if (ledgerInput) ledgerInput.value = newBalLedger.toFixed(2);

  if (varianceInput) {
    const variance = newBalDaily - newBalLedger;
    varianceInput.value = variance.toFixed(2);

    if (Math.abs(variance) < 0.01) {
      varianceInput.style.backgroundColor = '#d4edda';
      varianceInput.style.color = '#155724';
    } else {
      varianceInput.style.backgroundColor = '#f8d7da';
      varianceInput.style.color = '#721c24';
    }
  }
}

function recalculateBalanceSheet() {
  calculateBalancePrevVariance();
  calculateBalanceTodayVariance();
  calculateFactureVariance();
  calculateAdvDepositVariance();
  calculateNewBalance();
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  // Section 1: Cash Out and Daily Revenue inputs
  document.querySelectorAll('.geac-cash-out, .geac-daily-rev').forEach(input => {
    input.addEventListener('input', recalculateGeacReconciliation);
  });

  // Section 2: Balance Sheet inputs
  document.querySelectorAll('.geac-bal-prev-daily, .geac-bal-prev-ledger').forEach(input => {
    input.addEventListener('input', () => {
      calculateBalancePrevVariance();
      calculateNewBalance();
    });
  });

  document.querySelectorAll('.geac-bal-today-daily, .geac-bal-today-ledger').forEach(input => {
    input.addEventListener('input', () => {
      calculateBalanceTodayVariance();
      calculateNewBalance();
    });
  });

  document.querySelectorAll('.geac-facture-daily, .geac-facture-ledger').forEach(input => {
    input.addEventListener('input', () => {
      calculateFactureVariance();
      calculateNewBalance();
    });
  });

  document.querySelectorAll('.geac-adv-daily, .geac-adv-applied').forEach(input => {
    input.addEventListener('input', () => {
      calculateAdvDepositVariance();
      calculateNewBalance();
    });
  });

  // Excel-like navigation
  setTimeout(() => {
    setupExcelNavigation('#geac-reconciliation-table');
    setupExcelNavigation('#geac-balance-table');
  }, 100);
});
