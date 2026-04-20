"""Excel COM-based RJ filler — preserves formulas, tab colors, macros.

REPLACES xlutils.copy which destroys formulas. See docs/XLUTILS_WARNING.md.
Uses pywin32 to drive Excel directly. Windows only.

Column indices throughout this module are 1-based (matching the COM
Cells(row, col) convention). Day-to-row: Day N → Excel row N+2.
"""

import os
import shutil
import time
import logging

logger = logging.getLogger(__name__)


class RJFillerCOM:
    """Write to RJ .xls files via Excel COM, preserving all formatting.

    Usage (context manager — preferred):

        with RJFillerCOM('/path/to/RJ.xls') as filler:
            filler.write_jour_cell(day=14, col=37, formula='=50695.88-40')
            filler.write_geac({(6, 2): '=5613.06', (12, 7): '=17789.51'})
            dc = filler.get_dc(day=14)

    A backup (.bak.xls) is created before any write. On exception, the
    workbook is closed without saving; the backup remains intact.
    """

    # Jour columns with built-in formulas — NEVER overwrite.
    # All values are 1-based (COM convention). Cross-reference: AUTOFILL_MASTER.md §11.
    #
    #   B  (col  2): =D[prev_row]           — Bal_Ouv chained from prior day
    #   C  (col  3): =D-B-(SUM(E:BF)-SUM(BI:CI)) — DC auto-computes
    #   BH (col 60): SUM formula            — TOTAL CREDIT
    #   CK (col 89): =<total_rooms>-CM      — Simple rooms = total - Suite
    #   CW (col101): =ROUND(+BI*CS,2)      — net AMEX escompte
    #   CX (col102): =ROUND(+BJ*CT,2)      — net Discover escompte
    #   CY (col103): =ROUND(+BK*CU,2)      — net Master escompte
    #   CZ (col104): =ROUND(+BL*CV,2)      — net Visa escompte
    #   DG (col111): =SUM(E+J+O+T+Y)       — Nourriture total
    #   DH (col112): =SUM(F+K+P+U+Z)       — Alcool total
    #   DI (col113): =SUM(G+L+Q+V+AA)      — Bières total
    #   DJ (col114): =SUM(H+M+R+W+AB)      — Minéraux total
    #   DK (col115): =SUM(I+N+S+X+AC)      — Vins total
    FORMULA_COLUMNS = frozenset({
        2,    # B  — Bal_Ouv
        3,    # C  — DC
        60,   # BH — TOTAL CREDIT
        # CK (89) removed — auditor overwrites formula with actual room count
        101,  # CW — escompte AMEX
        102,  # CX — escompte Discover
        103,  # CY — escompte Master
        104,  # CZ — escompte Visa
        111,  # DG — Nourriture total
        112,  # DH — Alcool total
        113,  # DI — Bières total
        114,  # DJ — Minéraux total
        115,  # DK — Vins total
    })

    # Formula prefixes that indicate a cell contains a computed reference formula
    # (not a simple literal like '=0'). Used as belt-and-suspenders guard in
    # write_sheet_cell() for non-Jour sheets where FORMULA_COLUMNS doesn't apply.
    _COMPUTED_FORMULA_PREFIXES = ('=D', '=B', '=SUM', '=ROUND', '=IF', '=+')

    def __init__(self, rj_path: str) -> None:
        """
        Args:
            rj_path: Absolute or relative path to the RJ .xls file.
        """
        self.rj_path = os.path.abspath(rj_path)
        self.backup_path = self.rj_path + '.bak.xls'
        self.excel = None
        self.wb = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> 'RJFillerCOM':
        """Create backup then open the RJ file via COM."""
        shutil.copy2(self.rj_path, self.backup_path)
        logger.debug('Backup created: %s', self.backup_path)

        # Import here so the module can be imported on non-Windows for testing
        import win32com.client as win32  # noqa: PLC0415

        self.excel = win32.Dispatch('Excel.Application')
        self.excel.Visible = False
        self.excel.DisplayAlerts = False
        self.excel.AskToUpdateLinks = False
        self.wb = self.excel.Workbooks.Open(self.rj_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Recalculate, save (on success only), close, and quit Excel."""
        try:
            if self.wb is not None:
                if exc_type is None:
                    # Trigger full recalculation before saving so formula
                    # cells (DC, escompte, totals) reflect the new data.
                    self.excel.Calculate()
                    time.sleep(0.2)
                    self.wb.Save()
                    logger.debug('Workbook saved: %s', self.rj_path)
                # Always close without re-saving — we either just saved or are
                # discarding on error.  SaveChanges=False is intentional.
                self.wb.Close(SaveChanges=False)
        except Exception:
            logger.exception('Error during COM cleanup for %s', self.rj_path)
        finally:
            if self.excel is not None:
                try:
                    self.excel.Quit()
                except Exception:
                    logger.exception('Failed to quit Excel')
                self.excel = None
            self.wb = None

        # Never suppress the original exception
        return False

    # ------------------------------------------------------------------
    # Jour sheet writers
    # ------------------------------------------------------------------

    def write_jour_cell(self, day: int, col: int, formula: str) -> None:
        """Write a formula to a single Jour cell.

        Guards applied (in order):
        1. Column is in FORMULA_COLUMNS → skip silently.
        2. Cell already has a non-trivial computed formula → skip silently.
        3. Otherwise write formula string (must start with '=').

        Args:
            day:     Day number 1-31.
            col:     1-based column number (e.g., 37 for AK).
            formula: Formula string, e.g. '=50695.88-40'.  Plain numbers are
                     also accepted and will be written as values.
        """
        if not 1 <= day <= 31:
            raise ValueError(f'day must be 1-31, got {day}')
        if col < 1:
            raise ValueError(f'col must be >= 1, got {col}')

        if col in self.FORMULA_COLUMNS:
            logger.debug('Skipping formula column %d (day %d) — protected', col, day)
            return

        row = day + 2  # Day 1 → row 3, Day N → row N+2
        ws = self.wb.Sheets('jour')
        cell = ws.Cells(row, col)

        if cell.HasFormula:
            existing = str(cell.Formula)
            if existing.startswith(self._COMPUTED_FORMULA_PREFIXES):
                logger.debug(
                    'Skipping jour row %d col %d — existing formula: %s',
                    row, col, existing,
                )
                return

        if isinstance(formula, str) and formula.startswith('='):
            cell.Formula = formula
        else:
            cell.Value = formula

    def write_jour_row(self, day: int, values: dict) -> None:
        """Write multiple columns for a single Jour day.

        Args:
            day:    Day number 1-31.
            values: Mapping of {1-based col number: formula_string}.
                    e.g. {4: '=-1476889.24-455273.04', 37: '=50695.88-40'}
        """
        for col, formula in values.items():
            self.write_jour_cell(day, col, formula)

    # ------------------------------------------------------------------
    # Generic sheet writer
    # ------------------------------------------------------------------

    def write_sheet_cell(
        self, sheet_name: str, row: int, col: int, value
    ) -> None:
        """Write a value or formula to any sheet cell.

        For non-Jour sheets this is the primary write path. The HasFormula
        guard protects existing computed formulas (SUM, ROUND, IF, etc.) from
        being overwritten. Simple value-placeholder formulas ('=0', '=123.45')
        are considered safe to overwrite.

        Args:
            sheet_name: Excel sheet name, case-sensitive (e.g., 'geac_ux').
            row:        1-based row number.
            col:        1-based column number.
            value:      Number, or formula string starting with '='.
        """
        ws = self.wb.Sheets(sheet_name)
        cell = ws.Cells(row, col)

        if cell.HasFormula:
            existing = str(cell.Formula)
            if existing.startswith(self._COMPUTED_FORMULA_PREFIXES):
                logger.warning(
                    'Skipping %s!R%dC%d — existing formula: %s (attempted value: %s)',
                    sheet_name, row, col, existing, value,
                )
                return

        if isinstance(value, str) and value.startswith('='):
            cell.Formula = value
        else:
            cell.Value = value

    # ------------------------------------------------------------------
    # Convenience writers for GEAC and Transelect
    # ------------------------------------------------------------------

    def write_geac(self, geac_data: dict) -> None:
        """Write GEAC_UX sheet cells.

        Args:
            geac_data: Mapping of {(row, col): value} where row/col are
                       1-based.  Values may be numbers or formula strings.

                       Example:
                           {(6, 2): '=5613.06',
                            (12, 7): '=17789.51',
                            (6, 7): '=17789.51-5953.94'}
        """
        for (row, col), value in geac_data.items():
            self.write_sheet_cell('geac_ux', row, col, value)

    def write_transelect(self, transelect_data: dict) -> None:
        """Write Transelect sheet cells.

        Args:
            transelect_data: Mapping of {(row, col): value} where row/col
                             are 1-based.

                             Note: Rows 27-40 contain summary formulas —
                             do not write into them.  The HasFormula guard
                             will catch most of these, but callers should
                             also validate row numbers before calling.

                             Example:
                                 {(9, 24): 1415.99, (21, 2): 15185.17}
        """
        for (row, col), value in transelect_data.items():
            self.write_sheet_cell('transelect', row, col, value)

    # ------------------------------------------------------------------
    # Read-back helper
    # ------------------------------------------------------------------

    def get_dc(self, day: int) -> float:
        """Read the DC (Diff. Caisse) value for a given day after recalculation.

        DC lives in column C (col 3) of the jour sheet and is a formula cell.
        A full Calculate() is triggered before reading to ensure the value
        reflects any writes made in this session.

        Args:
            day: Day number 1-31.

        Returns:
            float DC value (should be 0.00 on a balanced day).
        """
        if not 1 <= day <= 31:
            raise ValueError(f'day must be 1-31, got {day}')

        row = day + 2
        ws = self.wb.Sheets('jour')
        self.excel.Calculate()
        time.sleep(0.1)
        value = ws.Cells(row, 3).Value  # col C = col 3
        if value is None:
            raise ValueError(
                f'DC cell (jour row {row}, col C) returned None — possible formula error'
            )
        return float(value)
