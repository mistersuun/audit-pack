"""Tests for RJFiller — writing data to RJ Excel files."""

import io
import xlrd
import pytest
from utils.rj_filler import RJFiller


class TestRJFillerControle:
    """Test updating controle sheet."""

    def test_update_controle_day(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        result = filler.update_controle(vjour=15, mois=3, annee=2026)
        assert result['vjour'] == 15
        assert result['mois'] == 3
        assert result['annee'] == 2026

    def test_controle_persists_after_save(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        filler.update_controle(vjour=20, mois=4, annee=2026)
        output = filler.save_to_bytes()

        rb = xlrd.open_workbook(file_contents=output.getvalue(), formatting_info=True)
        ctrl = rb.sheet_by_name('controle')
        assert ctrl.cell_value(2, 1) == 20  # B3 = vjour
        assert ctrl.cell_value(3, 1) == 4   # B4 = mois

    def test_controle_calculates_idate(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        result = filler.update_controle(vjour=8, mois=2, annee=2026)
        assert 'idate' in result
        assert result['idate'] > 0


class TestRJFillerRecap:
    """Test filling Recap sheet."""

    def test_fill_recap(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        count = filler.fill_sheet('Recap', {
            'comptant_lightspeed_lecture': 5000.50,
            'comptant_lightspeed_corr': 100.00,
        })
        assert count == 2

    def test_fill_recap_skip_empty(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        count = filler.fill_sheet('Recap', {
            'comptant_lightspeed_lecture': 5000.50,
            'prepare_par': '',  # empty string should be skipped
        })
        assert count == 1


class TestRJFillerTranselect:
    """Test filling Transelect sheet."""

    def test_fill_transelect(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        count = filler.fill_sheet('transelect', {
            'bar_701_debit': 150.00,
            'bar_701_visa': 300.00,
        })
        assert count == 2


class TestRJFillerJour:
    """Test filling JOUR sheet."""

    def test_fill_jour_day(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        result = filler.fill_jour_day(8, {4: 1500.00, 5: 200.00, 9: 800.00})
        assert result['day'] == 8
        assert result['filled_count'] == 3

    def test_fill_jour_persists(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        filler.fill_jour_day(8, {4: 1234.56})
        output = filler.save_to_bytes()

        rb = xlrd.open_workbook(file_contents=output.getvalue(), formatting_info=True)
        jour = rb.sheet_by_name('jour')
        # Day 8 row = 4 + 8 - 1 = 11 (JOUR_DAY_ROW_OFFSET=4)
        assert jour.cell_value(11, 4) == 1234.56

    def test_fill_jour_invalid_day(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        with pytest.raises(ValueError):
            filler.fill_jour_day(0, {4: 100})

    def test_fill_jour_empty_dict(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        result = filler.fill_jour_day(8, {})
        assert result['filled_count'] == 0


class TestRJFillerMacros:
    """Test macro equivalents."""

    def test_envoie_dans_jour(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        result = filler.envoie_dans_jour(7)
        assert result['day'] == 7
        assert 'recap_values' in result
        assert len(result['recap_values']) == 7

    def test_calcul_carte(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        result = filler.calcul_carte(7)
        assert result['day'] == 7
        assert 'card_totals' in result

    def test_reset_tabs(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        cleared = filler.reset_tabs()
        assert cleared > 0


class TestRJFillerSave:
    """Test save operations."""

    def test_save_to_bytes(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        output = filler.save_to_bytes()
        assert len(output.getvalue()) > 100000  # Should be > 100KB

    def test_save_readable_by_xlrd(self, rj07_bytes):
        filler = RJFiller(io.BytesIO(rj07_bytes))
        output = filler.save_to_bytes()
        rb = xlrd.open_workbook(file_contents=output.getvalue(), formatting_info=True)
        assert len(rb.sheet_names()) == 38
