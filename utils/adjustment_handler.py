"""
Multi-department adjustment handler for night audit.

Adjustments are per-department deductions (HP promotions, admin credits, etc.)
that must be subtracted from Sales Journal values before writing to the jour sheet.

Each department maps to a specific jour column:
- Piazza: J(9), K(10), L(11), M(12), N(13)
- Banquet: O(14), P(15)
- Spesa: Q(16), R(17)
- Tabagie: S(18)
"""

import logging

logger = logging.getLogger(__name__)


# Department key → jour column index (0-based)
DEPARTMENT_COLUMNS = {
    'piazza_nourriture': 9,     # J
    'piazza_alcool': 10,        # K
    'piazza_bieres': 11,        # L
    'piazza_non_alcool': 12,    # M
    'piazza_vins': 13,          # N
    'banquet_nourriture': 14,   # O
    'banquet_boissons': 15,     # P
    'spesa_nourriture': 16,     # Q
    'spesa_boissons': 17,       # R
    'tabagie': 18,              # S
}

# French labels for UI display
DEPARTMENT_LABELS = {
    'piazza_nourriture': 'Piazza Nourriture',
    'piazza_alcool': 'Piazza Alcool',
    'piazza_bieres': 'Piazza Bières',
    'piazza_non_alcool': 'Piazza Non-Alcool (Minéraux)',
    'piazza_vins': 'Piazza Vins',
    'banquet_nourriture': 'Banquet Nourriture',
    'banquet_boissons': 'Banquet Boissons',
    'spesa_nourriture': 'Marché Spesa Nourriture',
    'spesa_boissons': 'Marché Spesa Boissons',
    'tabagie': 'Tabagie',
}


def get_departments():
    """Return list of departments with their column indices and labels."""
    return [
        {
            'key': key,
            'label': DEPARTMENT_LABELS[key],
            'column_index': DEPARTMENT_COLUMNS[key],
        }
        for key in DEPARTMENT_COLUMNS
    ]


def group_adjustments_by_column(adjustments):
    """
    Group adjustments by target column index, summing amounts.

    Args:
        adjustments: list of dicts with 'department' and 'amount' keys
            e.g., [{'department': 'piazza_nourriture', 'amount': 15.50}, ...]

    Returns:
        dict: {column_index: total_adjustment_amount}
    """
    grouped = {}
    for adj in adjustments:
        dept = adj.get('department', '')
        amount = float(adj.get('amount', 0))
        if dept in DEPARTMENT_COLUMNS and amount != 0:
            col = DEPARTMENT_COLUMNS[dept]
            grouped[col] = grouped.get(col, 0) + amount
    return grouped


def apply_adjustments(jour_values, adjustments):
    """
    Subtract per-department adjustments from jour column values.

    Args:
        jour_values: dict {column_index: value} — will be modified in place
        adjustments: list of dicts with 'department' and 'amount' keys

    Returns:
        dict: same jour_values dict with adjustments applied
    """
    grouped = group_adjustments_by_column(adjustments)

    for col_idx, adj_amount in grouped.items():
        if col_idx in jour_values:
            jour_values[col_idx] -= adj_amount
        else:
            # Skip: no base value exists for this department column.
            # Applying an adjustment without a base would create misleading negative values.
            logger.info(f"Skipping adjustment for column {col_idx} — no base value in jour sheet.")

    return jour_values
