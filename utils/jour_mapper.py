"""
JourMapper — bridges parser output to jour sheet columns.

Takes parsed data from DailyRevenueParser, SalesJournalParser, ARSummaryParser,
HPExcelParser + manual values + adjustments, and produces a dict of
{column_index: final_value} ready to write to the jour sheet.

Uses the mapping configuration in daily_rev_jour_mapping.py to determine:
- Which parser field feeds which jour column
- What operation to apply (direct, subtract, accumulate, formula, combined)
- Sign handling (keep, negate, always_negative)

Usage:
    mapper = JourMapper(
        daily_rev_data=daily_revenue_parser.extracted_data,
        sales_journal_data=sales_journal_parser.extracted_data,
        ar_summary_data=ar_summary_parser.extracted_data,
        hp_data=hp_excel_parser.extracted_data,
        manual_values={'club_lounge': 30.0, 'deposit_on_hand': 328963.22},
        adjustments=[{'department': 'piazza_nourriture', 'amount': 15.50}]
    )
    jour_values = mapper.compute_all()
    # jour_values = {36: 50906.60, 37: 0.00, 49: 5457.94, ...}
"""

from utils.daily_rev_jour_mapping import DAILY_REV_TO_JOUR, ACCUMULATOR_COLUMNS
from utils.adjustment_handler import apply_adjustments, group_adjustments_by_column


class JourMapper:
    """Compute final jour sheet values from all parser outputs."""

    def __init__(self, daily_rev_data=None, sales_journal_data=None,
                 ar_summary_data=None, hp_data=None,
                 manual_values=None, adjustments=None):
        """
        Initialize with all data sources.

        Args:
            daily_rev_data: Nested dict from DailyRevenueParser
            sales_journal_data: Nested dict from SalesJournalParser
            ar_summary_data: Nested dict from ARSummaryParser
            hp_data: Nested dict from HPExcelParser
            manual_values: Dict with 'club_lounge', 'deposit_on_hand'
            adjustments: List of dicts with 'department' and 'amount'
        """
        self.daily_rev = daily_rev_data or {}
        self.sales_journal = sales_journal_data or {}
        self.ar_summary = ar_summary_data or {}
        self.hp_data = hp_data or {}
        self.manual = manual_values or {}
        self.adjustments = adjustments or []

        # Combined data for field resolution
        # Priority: daily_rev > sales_journal > ar_summary > manual
        self._all_data = {
            'daily_rev': self.daily_rev,
            'sales_journal': self.sales_journal,
            'ar_summary': self.ar_summary,
            'hp': self.hp_data,
            'manual': self.manual,
        }

        # Results tracking
        self.computed = {}       # {col_letter: value}
        self.warnings = []
        self.errors = []

    def compute_all(self):
        """
        Compute all jour column values based on mapping config.

        Returns:
            dict: {column_index: final_value} ready for fill_jour_day()
        """
        jour_values = {}

        for col_letter, config in DAILY_REV_TO_JOUR.items():
            try:
                value = self._compute_column(col_letter, config)
                if value is not None:
                    col_idx = config['column_index']
                    jour_values[col_idx] = value
                    self.computed[col_letter] = value
            except Exception as e:
                self.errors.append(f"Column {col_letter}: {str(e)}")

        # Apply HP deductions (for Sales Journal columns)
        self._apply_hp_deductions(jour_values)

        # Apply per-department adjustments
        if self.adjustments:
            apply_adjustments(jour_values, self.adjustments)

        return jour_values

    def _compute_column(self, col_letter, config):
        """
        Compute a single column value based on its config.

        Args:
            col_letter: Column letter (e.g., 'AK')
            config: Mapping config dict from DAILY_REV_TO_JOUR

        Returns:
            Computed value or None if no data available
        """
        operation = config.get('operation', 'direct')

        if operation == 'direct':
            value = self._process_direct(config)
        elif operation == 'subtract':
            value = self._process_subtract(config)
        elif operation == 'accumulate':
            value = self._process_accumulate(config)
        elif operation == 'formula':
            value = self._process_formula(col_letter, config)
        elif operation == 'combined':
            value = self._process_combined(col_letter, config)
        else:
            self.warnings.append(f"Column {col_letter}: unknown operation '{operation}'")
            return None

        if value is None:
            return None

        # Apply sign handling
        value = self._apply_sign_handling(value, config)

        return value

    def _process_direct(self, config):
        """Direct copy: value = base_field value."""
        base_field = config.get('base_field')
        if not base_field:
            return None
        return self._resolve_field(base_field)

    def _process_subtract(self, config):
        """Subtract: value = base_field - subtract_field."""
        base_field = config.get('base_field')
        subtract_field = config.get('subtract_field')

        if not base_field:
            return None

        base_value = self._resolve_field(base_field)
        if base_value is None:
            return None

        if subtract_field:
            subtract_value = self._resolve_field(subtract_field) or 0
            return float(base_value) - float(subtract_value)

        return float(base_value)

    def _process_accumulate(self, config):
        """Accumulate: value = sum of all accumulator_fields."""
        fields = config.get('accumulator_fields', [])
        if not fields:
            return None

        total = 0
        found_any = False

        for field_path in fields:
            value = self._resolve_field(field_path)
            if value is not None:
                total += float(value)
                found_any = True

        return total if found_any else None

    def _process_formula(self, col_letter, config):
        """
        Formula: evaluate a defined formula.

        Handles special columns:
        - D: -(balance.new_balance) - deposits.deposit_on_hand
        - BF: -forfait + club_lounge_value
        """
        if col_letter == 'D':
            return self._formula_column_d(config)
        elif col_letter == 'BF':
            return self._formula_column_bf(config)
        else:
            # Generic formula - try base_field
            base_value = self._resolve_field(config.get('base_field'))
            return float(base_value) if base_value is not None else None

    def _process_combined(self, col_letter, config):
        """
        Combined: chain multiple operations.

        Handles:
        - CF: -(total_transfers - payments) [always negative]
        """
        if col_letter == 'CF':
            return self._formula_column_cf(config)
        else:
            # Fallback: try accumulating fields
            fields = config.get('accumulator_fields', [])
            if fields:
                total = 0
                for field_path in fields:
                    value = self._resolve_field(field_path)
                    if value is not None:
                        total += float(value)
                return total
            return None

    def _formula_column_d(self, config):
        """
        Column D = -(New Balance) - Deposit on Hand.

        New Balance comes from Daily Revenue parser.
        Deposit on Hand comes from manual values (Advance Deposit Balance Sheet).
        """
        new_balance = self._resolve_field('balance.new_balance')
        if new_balance is None:
            return None

        new_balance = float(new_balance)

        # Deposit on Hand from manual values
        deposit_on_hand = float(self.manual.get('deposit_on_hand', 0))

        # Formula: negate new_balance, then subtract deposit
        # If new_balance is -3,871,908.19, then -(-3,871,908.19) = 3,871,908.19
        # Then subtract deposit_on_hand
        result = -new_balance - deposit_on_hand
        return result

    def _formula_column_bf(self, config):
        """
        Column BF = -Forfait + Club Lounge value.
        """
        # Forfait from HP data or Sales Journal
        forfait = self._resolve_field('adjustments.forfait')
        if forfait is None:
            forfait = 0
        forfait = float(forfait)

        # Club lounge from manual values
        club_lounge = float(self.manual.get('club_lounge', 0))

        return -forfait + club_lounge

    def _formula_column_cf(self, config):
        """
        Column CF = A/R Misc + Front Office Transfers.

        Sources: A/R Misc + Front Office Transfers.
        Note: CF column values retain their original sign from source data.
        Deductions and payments are already represented with appropriate signs in source data.
        """
        ar_misc = self._resolve_field('non_revenue.ar_activity.total')
        fo_transfers = self._resolve_field('balance.front_office_transfers')

        total = 0
        if ar_misc is not None:
            total += float(ar_misc)
        if fo_transfers is not None:
            total += float(fo_transfers)

        # Preserve the sign as provided by source data
        return total if total != 0 else 0

    def _apply_sign_handling(self, value, config):
        """Apply sign handling rules."""
        sign = config.get('sign_handling', 'keep_sign')

        if sign == 'negate_result':
            return -value
        elif sign == 'always_negative':
            return -abs(value) if value != 0 else 0
        else:  # 'keep_sign'
            return value

    def _apply_hp_deductions(self, jour_values):
        """
        Apply HP deductions from the HP Excel parser to Sales Journal columns.

        Supports two HP data formats:

        1. New format (from HPExcelParser with daily extraction):
           hp_data = {'jour_deductions': {'9': 36.25, '18': 96.80}, ...}
           — jour_deductions maps directly: {col_index_str: amount}

        2. Legacy format (from old mensuel-only extraction):
           hp_data = {'piazza_nourr': 100, 'tabagie_nourr': 50, ...}
           — flat keys matching mensuel sheet fields
        """
        if not self.hp_data:
            return

        # Format 1: Direct jour_deductions from HP parser (preferred)
        jour_deductions = self.hp_data.get('jour_deductions', {})
        if jour_deductions:
            for col_idx_str, hp_amount in jour_deductions.items():
                col_idx = int(col_idx_str)
                if hp_amount and col_idx in jour_values:
                    jour_values[col_idx] -= abs(float(hp_amount))
            return

        # Format 2: Legacy flat keys from mensuel sheet
        hp_flat_mapping = {
            # flat_key → jour_column_index
            'piazza_nourr': 9,       # J
            'piazza_boisson': 10,    # K
            'piazza_biere': 11,      # L
            'piazza_min': 12,        # M
            'piazza_vin': 13,        # N
            'banquet_nourr': 14,     # O
            'banquet_boisson': 15,   # P
            'link_nourr': 16,        # Q
            'link_boisson': 17,      # R
            'tabagie_nourr': 18,     # S
        }

        for flat_key, col_idx in hp_flat_mapping.items():
            hp_amount = self.hp_data.get(flat_key, 0)
            if hp_amount and col_idx in jour_values:
                jour_values[col_idx] -= abs(float(hp_amount))

    def _resolve_field(self, field_path):
        """
        Resolve a dot-path field from all available data sources.

        Tries to find the value in this order:
        1. Daily Revenue data (most fields come from here)
        2. Sales Journal data
        3. AR Summary data
        4. HP data
        5. Manual values

        Args:
            field_path: Dot-separated path, e.g., 'revenue.chambres.total'

        Returns:
            Value if found, None otherwise
        """
        if not field_path:
            return None

        parts = field_path.split('.')

        # Special prefix routing
        if parts[0] == 'sales_journal':
            # Route to sales_journal data directly
            return self._navigate_dict(self.sales_journal, parts[1:])
        elif parts[0] == 'ar_summary':
            return self._navigate_dict(self.ar_summary, parts[1:])
        elif parts[0] == 'derived':
            return self._resolve_derived(parts[1:])
        elif parts[0] == 'manual':
            return self.manual.get(parts[1]) if len(parts) > 1 else None

        # Try each data source in order
        for source_key in ['daily_rev', 'sales_journal', 'ar_summary', 'hp']:
            data = self._all_data.get(source_key, {})
            result = self._navigate_dict(data, parts)
            if result is not None:
                return result

        return None

    def _navigate_dict(self, data, parts):
        """
        Navigate a nested dict by path parts.

        Args:
            data: Root dict
            parts: List of keys, e.g., ['revenue', 'chambres', 'total']

        Returns:
            Value at the path, or None if path doesn't exist
        """
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _resolve_derived(self, parts):
        """Resolve derived/calculated fields."""
        if not parts:
            return None

        if parts[0] == 'diff_forfait':
            # diff_forfait = forfait value - club_lounge
            forfait = self._resolve_field('adjustments.forfait') or 0
            club_lounge = float(self.manual.get('club_lounge', 0))
            return float(forfait) - club_lounge

        return None

    def get_summary(self):
        """
        Return a summary of all computed values for display.

        Returns:
            dict with 'values', 'warnings', 'errors', 'column_count'
        """
        return {
            'values': self.computed,
            'warnings': self.warnings,
            'errors': self.errors,
            'column_count': len(self.computed),
        }


def compute_jour_from_parsed_data(parsed_results, manual_values=None, adjustments=None):
    """
    Convenience function: take raw parser results dict and compute jour values.

    Args:
        parsed_results: dict of {doc_type: parser_result_data}
            e.g., {'daily_revenue': {...}, 'sales_journal': {...}, ...}
        manual_values: dict with 'club_lounge', 'deposit_on_hand'
        adjustments: list of per-department adjustments

    Returns:
        tuple: (jour_values_dict, summary_dict)
    """
    mapper = JourMapper(
        daily_rev_data=parsed_results.get('daily_revenue', {}),
        sales_journal_data=parsed_results.get('sales_journal', {}),
        ar_summary_data=parsed_results.get('ar_summary', {}),
        hp_data=parsed_results.get('hp_excel', {}),
        manual_values=manual_values,
        adjustments=adjustments,
    )

    jour_values = mapper.compute_all()
    summary = mapper.get_summary()

    return jour_values, summary
