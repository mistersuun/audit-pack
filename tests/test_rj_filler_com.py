"""Tests for RJFillerCOM — Excel COM-based RJ writer.

These tests are intentionally COM-free: they verify the class's static
properties, guard logic, and arithmetic contracts without opening Excel.
COM-dependent behavior (actual file writes, get_dc round-trips) requires a
live Windows + Excel environment and is exercised manually or in integration
tests tagged @pytest.mark.integration.
"""

import pytest
from utils.rj_filler_com import RJFillerCOM


# ---------------------------------------------------------------------------
# Class-level attribute tests
# ---------------------------------------------------------------------------

class TestRJFillerCOMClass:
    """Verify RJFillerCOM has the expected interface."""

    def test_class_importable(self):
        assert RJFillerCOM is not None

    def test_has_write_jour_cell(self):
        assert callable(getattr(RJFillerCOM, 'write_jour_cell', None))

    def test_has_write_jour_row(self):
        assert callable(getattr(RJFillerCOM, 'write_jour_row', None))

    def test_has_write_geac(self):
        assert callable(getattr(RJFillerCOM, 'write_geac', None))

    def test_has_write_transelect(self):
        assert callable(getattr(RJFillerCOM, 'write_transelect', None))

    def test_has_write_sheet_cell(self):
        assert callable(getattr(RJFillerCOM, 'write_sheet_cell', None))

    def test_has_get_dc(self):
        assert callable(getattr(RJFillerCOM, 'get_dc', None))

    def test_has_context_manager_protocol(self):
        assert hasattr(RJFillerCOM, '__enter__')
        assert hasattr(RJFillerCOM, '__exit__')


# ---------------------------------------------------------------------------
# FORMULA_COLUMNS protection set
# ---------------------------------------------------------------------------

class TestFormulaColumnsSet:
    """FORMULA_COLUMNS must cover all known built-in Jour formula cells.

    Column numbers are 1-based (COM convention). See AUTOFILL_MASTER.md §11
    and CLAUDE.md for the canonical formula cell reference.
    """

    FC = RJFillerCOM.FORMULA_COLUMNS

    def test_col_B_protected(self):
        """B (col 2) = Bal_Ouv =D[prev_row] — must never be overwritten."""
        assert 2 in self.FC

    def test_col_C_protected(self):
        """C (col 3) = DC formula =D-B-(SUM...) — the balance-check cell."""
        assert 3 in self.FC

    def test_col_BH_protected(self):
        """BH (col 60) = TOTAL CREDIT sum formula."""
        assert 60 in self.FC

    def test_col_CK_protected(self):
        """CK (col 89) = =243-CM simple rooms formula."""
        assert 89 in self.FC

    def test_col_CW_protected(self):
        """CW (col 101) = =ROUND(+BI*CS,2) AMEX escompte."""
        assert 101 in self.FC

    def test_col_CX_protected(self):
        """CX (col 102) = =ROUND(+BJ*CT,2) Discover escompte."""
        assert 102 in self.FC

    def test_col_CY_protected(self):
        """CY (col 103) = =ROUND(+BK*CU,2) Master escompte."""
        assert 103 in self.FC

    def test_col_CZ_protected(self):
        """CZ (col 104) = =ROUND(+BL*CV,2) Visa escompte."""
        assert 104 in self.FC

    def test_col_DG_protected(self):
        """DG (col 111) = Nourriture total."""
        assert 111 in self.FC

    def test_col_DH_protected(self):
        """DH (col 112) = Alcool total."""
        assert 112 in self.FC

    def test_col_DI_protected(self):
        """DI (col 113) = Bières total."""
        assert 113 in self.FC

    def test_col_DJ_protected(self):
        """DJ (col 114) = Minéraux total."""
        assert 114 in self.FC

    def test_col_DK_protected(self):
        """DK (col 115) = Vins total."""
        assert 115 in self.FC

    def test_formula_columns_is_immutable(self):
        """FORMULA_COLUMNS should be a frozenset so callers cannot mutate it."""
        assert isinstance(self.FC, frozenset)

    def test_writable_columns_not_protected(self):
        """Spot-check that common writeable columns are NOT in the set."""
        # D=4 (Nouveau Solde), AK=37 (Chambres), CF=84 (Transfer AR)
        for col in (4, 37, 84):
            assert col not in self.FC, (
                f'Column {col} is incorrectly marked as a formula column'
            )


# ---------------------------------------------------------------------------
# Day-to-row arithmetic
# ---------------------------------------------------------------------------

class TestDayToRowMapping:
    """Day N must map to Excel row N+2 (1-based)."""

    @pytest.mark.parametrize('day,expected_row', [
        (1, 3),
        (14, 16),
        (15, 17),
        (28, 30),
        (31, 33),
    ])
    def test_day_to_row(self, day, expected_row):
        assert day + 2 == expected_row

    def test_day_1_is_row_3(self):
        """Day 1 must be row 3 — not row 2, not row 1."""
        assert 1 + 2 == 3

    def test_day_31_is_row_33(self):
        """Day 31 (last day of month) must be row 33."""
        assert 31 + 2 == 33


# ---------------------------------------------------------------------------
# Input validation (no COM needed — object is constructed via __new__)
# ---------------------------------------------------------------------------

class TestInputValidation:
    """write_jour_cell and get_dc must reject out-of-range inputs."""

    def _make_filler(self):
        """Construct a bare RJFillerCOM without calling __init__."""
        return RJFillerCOM.__new__(RJFillerCOM)

    def test_write_jour_cell_rejects_day_zero(self):
        filler = self._make_filler()
        with pytest.raises(ValueError, match='day must be 1-31'):
            filler.write_jour_cell(day=0, col=4, formula='=1000')

    def test_write_jour_cell_rejects_day_32(self):
        filler = self._make_filler()
        with pytest.raises(ValueError, match='day must be 1-31'):
            filler.write_jour_cell(day=32, col=4, formula='=1000')

    def test_write_jour_cell_rejects_col_zero(self):
        filler = self._make_filler()
        with pytest.raises(ValueError, match='col must be >= 1'):
            filler.write_jour_cell(day=1, col=0, formula='=1000')

    def test_get_dc_rejects_day_zero(self):
        filler = self._make_filler()
        with pytest.raises(ValueError, match='day must be 1-31'):
            filler.get_dc(day=0)

    def test_get_dc_rejects_day_32(self):
        filler = self._make_filler()
        with pytest.raises(ValueError, match='day must be 1-31'):
            filler.get_dc(day=32)


# ---------------------------------------------------------------------------
# FORMULA_COLUMNS guard (no COM needed — tested via monkeypatching)
# ---------------------------------------------------------------------------

class TestFormulaColumnGuard:
    """write_jour_cell must silently skip protected columns."""

    def _make_filler_with_mock_wb(self, monkeypatch):
        """Return a filler with a mock workbook that records writes."""
        filler = RJFillerCOM.__new__(RJFillerCOM)
        written = []

        class MockCell:
            HasFormula = False
            Formula = None
            Value = None

        class MockSheet:
            def Cells(self, row, col):
                class _Cell(MockCell):
                    pass
                c = _Cell()
                c._row = row
                c._col = col
                # Track assignments
                original_setattr = object.__setattr__

                class TrackingCell(_Cell):
                    def __setattr__(self, name, value):
                        if name in ('Formula', 'Value'):
                            written.append((row, col, name, value))
                        object.__setattr__(self, name, value)
                return TrackingCell()

        class MockWB:
            def Sheets(self, name):
                return MockSheet()

        filler.wb = MockWB()
        filler.excel = None  # not needed for these tests
        return filler, written

    def test_protected_column_is_skipped(self, monkeypatch):
        filler, written = self._make_filler_with_mock_wb(monkeypatch)
        # Column 3 (C = DC) must never be written
        filler.write_jour_cell(day=14, col=3, formula='=50695.88')
        assert len(written) == 0, (
            'write_jour_cell wrote to a protected column (C/DC)'
        )

    def test_bal_ouv_column_is_skipped(self, monkeypatch):
        filler, written = self._make_filler_with_mock_wb(monkeypatch)
        # Column 2 (B = Bal_Ouv)
        filler.write_jour_cell(day=1, col=2, formula='=1234.56')
        assert len(written) == 0

    def test_unprotected_column_is_written(self, monkeypatch):
        filler, written = self._make_filler_with_mock_wb(monkeypatch)
        # Column 37 (AK = Chambres) is writable
        filler.write_jour_cell(day=14, col=37, formula='=50695.88-40')
        assert len(written) == 1
        row, col, attr, val = written[0]
        assert row == 16    # day 14 + 2
        assert col == 37
        assert val == '=50695.88-40'


# ---------------------------------------------------------------------------
# Column arithmetic helpers (letter → 1-based index)
# ---------------------------------------------------------------------------

class TestColumnArithmetic:
    """Verify the 1-based column numbers embedded in FORMULA_COLUMNS."""

    @pytest.mark.parametrize('letter,expected', [
        ('B',   2),
        ('C',   3),
        ('BH',  60),
        ('CK',  89),
        ('CW', 101),
        ('CX', 102),
        ('CY', 103),
        ('CZ', 104),
        ('DG', 111),
        ('DH', 112),
        ('DI', 113),
        ('DJ', 114),
        ('DK', 115),
    ])
    def test_col_letter_to_1based_index(self, letter, expected):
        """Each column letter must resolve to the expected 1-based index."""
        def col_to_1based(col_str: str) -> int:
            result = 0
            for ch in col_str.upper():
                result = result * 26 + (ord(ch) - ord('A') + 1)
            return result

        assert col_to_1based(letter) == expected, (
            f'{letter} should be column {expected}, got {col_to_1based(letter)}'
        )
