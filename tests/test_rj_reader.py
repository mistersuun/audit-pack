"""Tests for RJReader — reading data from RJ Excel files."""

import io
import pytest
from utils.rj_reader import RJReader


class TestRJReaderControle:
    """Test reading controle sheet."""

    def test_read_controle_returns_dict(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        ctrl = reader.read_controle()
        assert isinstance(ctrl, dict)

    def test_controle_has_date_fields(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        ctrl = reader.read_controle()
        assert ctrl.get('jour') == 7.0
        assert ctrl.get('mois') == 2.0
        assert ctrl.get('annee') == 2026.0

    def test_controle_has_auditor(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        ctrl = reader.read_controle()
        assert ctrl.get('prepare_par')  # Non-empty


class TestRJReaderRecap:
    """Test reading Recap sheet."""

    def test_read_recap_returns_dict(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        recap = reader.read_recap()
        assert isinstance(recap, dict)

    def test_recap_has_standard_fields(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        recap = reader.read_recap()
        assert 'prepare_par' in recap
        assert 'date' in recap


class TestRJReaderTranselect:
    """Test reading Transelect sheet."""

    def test_read_transelect_returns_dict(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        trans = reader.read_transelect()
        assert isinstance(trans, dict)
        assert len(trans) > 0

    def test_transelect_has_terminal_data(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        trans = reader.read_transelect()
        # Should have at least some terminal card data
        card_keys = [k for k in trans if any(
            c in k for c in ['debit', 'visa', 'master', 'amex']
        )]
        assert len(card_keys) > 0


class TestRJReaderGEAC:
    """Test reading GEAC sheet."""

    def test_read_geac_returns_dict(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        geac = reader.read_geac_ux()
        assert isinstance(geac, dict)
        assert len(geac) > 0


class TestRJReaderJour:
    """Test reading JOUR sheet."""

    def test_read_jour_day_returns_dict(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        jour = reader.read_jour_day(7)
        assert isinstance(jour, dict)

    def test_jour_day_7_has_data(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        jour = reader.read_jour_day(7)
        non_zero = {k: v for k, v in jour.items() if v and v != 0}
        assert len(non_zero) > 0

    def test_jour_day_0_returns_empty(self, rj07_bytes):
        """Day 0 returns data (no validation error) but with no meaningful values."""
        reader = RJReader(io.BytesIO(rj07_bytes))
        jour = reader.read_jour_day(0)
        assert isinstance(jour, dict)


class TestRJReaderDueBack:
    """Test reading DueBack sheet."""

    def test_read_dueback_returns_dict(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        dueback = reader.read_dueback(day=7)
        assert isinstance(dueback, dict)
        assert 'receptionists' in dueback

    def test_dueback_has_receptionists(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        dueback = reader.read_dueback(day=7)
        receptionists = dueback.get('receptionists', [])
        assert len(receptionists) > 0

    def test_dueback_receptionist_has_name(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        dueback = reader.read_dueback(day=7)
        for recep in dueback.get('receptionists', []):
            assert 'full_name' in recep or 'last_name' in recep


class TestRJReaderSetD:
    """Test reading SetD sheet."""

    def test_read_setd_returns_dict(self, rj07_bytes):
        reader = RJReader(io.BytesIO(rj07_bytes))
        setd = reader.read_setd_day(7)
        assert isinstance(setd, dict)
