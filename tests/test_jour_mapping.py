"""Tests for jour_mapping — bidirectional NAS ↔ Excel mapping."""

import pytest
from utils.jour_mapping import (
    JOUR_NAS_TO_COL, JOUR_COL_TO_NAS, JOUR_MACRO_COLS,
    nas_jour_to_excel_dict, excel_jour_to_nas_dict,
)


class TestJourMappingConstants:
    """Test mapping constants."""

    def test_nas_to_col_has_entries(self):
        assert len(JOUR_NAS_TO_COL) == 54

    def test_col_to_nas_is_reverse(self):
        """Every NAS→COL entry should have a reverse COL→NAS entry."""
        for nas_field, col_idx in JOUR_NAS_TO_COL.items():
            assert col_idx in JOUR_COL_TO_NAS
            assert JOUR_COL_TO_NAS[col_idx] == nas_field

    def test_macro_cols_excluded(self):
        """Macro columns should NOT appear in the NAS mapping."""
        mapped_cols = set(JOUR_NAS_TO_COL.values())
        for macro_col in JOUR_MACRO_COLS:
            assert macro_col not in mapped_cols

    def test_all_fields_start_with_jour(self):
        for field in JOUR_NAS_TO_COL:
            assert field.startswith('jour_')

    def test_occupation_fields_present(self):
        assert 'jour_rooms_simple' in JOUR_NAS_TO_COL
        assert 'jour_rooms_double' in JOUR_NAS_TO_COL
        assert 'jour_rooms_suite' in JOUR_NAS_TO_COL
        assert 'jour_rooms_comp' in JOUR_NAS_TO_COL
        assert 'jour_nb_clients' in JOUR_NAS_TO_COL
        assert 'jour_rooms_hors_usage' in JOUR_NAS_TO_COL


class TestNasJourToExcelDict:
    """Test NAS → Excel conversion."""

    def test_returns_dict(self):
        # Create a mock NAS-like object
        class MockNAS:
            jour_cafe_nourriture = 500.0
            jour_cafe_boisson = 100.0
            jour_rooms_simple = 50

        result = nas_jour_to_excel_dict(MockNAS())
        assert isinstance(result, dict)
        assert 4 in result  # jour_cafe_nourriture → col 4
        assert result[4] == 500.0

    def test_skips_none_values(self):
        class MockNAS:
            jour_cafe_nourriture = None
            jour_cafe_boisson = 100.0

        result = nas_jour_to_excel_dict(MockNAS())
        assert 4 not in result  # None skipped
        assert 5 in result

    def test_includes_zero_values(self):
        """Zero values are included in the mapping (not filtered out)."""
        class MockNAS:
            jour_cafe_nourriture = 0
            jour_cafe_boisson = 0.0

        result = nas_jour_to_excel_dict(MockNAS())
        assert 4 in result  # jour_cafe_nourriture → col 4
        assert 5 in result  # jour_cafe_boisson → col 5


class TestExcelJourToNasDict:
    """Test Excel → NAS conversion."""

    def test_converts_known_columns(self):
        excel_data = {4: 500.0, 5: 100.0, 9: 800.0}
        result = excel_jour_to_nas_dict(excel_data)
        assert result['jour_cafe_nourriture'] == 500.0
        assert result['jour_cafe_boisson'] == 100.0
        assert result['jour_piazza_nourriture'] == 800.0

    def test_skips_unknown_columns(self):
        excel_data = {999: 123.0}  # No mapping for col 999
        result = excel_jour_to_nas_dict(excel_data)
        assert len(result) == 0

    def test_skips_macro_columns(self):
        excel_data = {72: 100.0, 73: 200.0}  # Macro cols
        result = excel_jour_to_nas_dict(excel_data)
        assert len(result) == 0

    def test_includes_zero_values(self):
        """Zero values are included in the mapping (not filtered out)."""
        excel_data = {4: 0, 5: 0.0, 9: 800.0}
        result = excel_jour_to_nas_dict(excel_data)
        assert 'jour_cafe_nourriture' in result
        assert 'jour_cafe_boisson' in result
        assert 'jour_piazza_nourriture' in result

    def test_roundtrip(self):
        """NAS → Excel → NAS should preserve data."""
        class MockNAS:
            jour_cafe_nourriture = 500.0
            jour_piazza_nourriture = 800.0
            jour_rooms_simple = 120

        excel_dict = nas_jour_to_excel_dict(MockNAS())
        nas_dict = excel_jour_to_nas_dict(excel_dict)
        assert nas_dict['jour_cafe_nourriture'] == 500.0
        assert nas_dict['jour_piazza_nourriture'] == 800.0
        assert nas_dict['jour_rooms_simple'] == 120
