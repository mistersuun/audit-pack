"""Unit tests for tests/fixtures/ground_truth_seeder.py.

Each extractor is tested against one well-known fixture day to catch
layout drift early. These tests do NOT depend on Flask or the DB —
they are pure xlrd reads.
"""
import pytest

import json

from tests.fixtures.ground_truth_seeder import (
    extract_all,
    extract_chambres,
    extract_dueback,
    extract_geac_balance_sheet,
    extract_recap,
    extract_sd,
    extract_transelect,
)


# ---------------------------------------------------------------------------
# DueBack
# ---------------------------------------------------------------------------

def test_extract_dueback_returns_list_of_dicts():
    result = extract_dueback('2026-03-21')
    assert isinstance(result, list)
    assert len(result) > 0
    for row in result:
        assert isinstance(row, dict)
        assert 'name' in row
        assert 'amount' in row
        assert isinstance(row['amount'], (int, float))


def test_extract_dueback_skips_blank_rows():
    result = extract_dueback('2026-03-21')
    for row in result:
        assert row['name'].strip() != ''


def test_extract_dueback_known_value():
    """Day 21 has Nikoletta with 1231.64 in col 11."""
    result = extract_dueback('2026-03-21')
    names = {r['name'] for r in result}
    # Nikoletta should be in the results (no last name in row 2 for that col)
    assert any('Nikoletta' in n for n in names), f"Expected Nikoletta in {names}"
    nikoletta = [r for r in result if 'Nikoletta' in r['name']][0]
    assert nikoletta['amount'] == 1231.64


# ---------------------------------------------------------------------------
# SD
# ---------------------------------------------------------------------------

def test_extract_sd_returns_list_of_dicts():
    result = extract_sd('2026-03-21')
    assert isinstance(result, list)
    assert len(result) > 0
    for row in result:
        assert 'employee' in row
        assert 'verified_amount' in row
        assert isinstance(row['verified_amount'], (int, float))


def test_extract_sd_skips_accounting_columns():
    """SD results should not include 'Petite Caisse', 'Conc. Banc.', etc."""
    result = extract_sd('2026-03-21')
    for row in result:
        emp = row['employee'].lower()
        assert 'petite' not in emp, f"Accounting column leaked: {row}"
        assert 'conc.' not in emp, f"Accounting column leaked: {row}"
        assert 'corr.' not in emp, f"Accounting column leaked: {row}"


def test_extract_sd_known_value():
    """Day 21 has VICTOR GUEFAELLY with 110.52."""
    result = extract_sd('2026-03-21')
    names = {r['employee'] for r in result}
    assert any('VICTOR' in n for n in names), f"Expected VICTOR in {names}"
    victor = [r for r in result if 'VICTOR' in r['employee']][0]
    assert victor['verified_amount'] == 110.52


# ---------------------------------------------------------------------------
# Chambres à refaire
# ---------------------------------------------------------------------------

def test_extract_chambres_returns_integer():
    result = extract_chambres('2026-03-21')
    assert isinstance(result, int)
    assert 0 <= result <= 252  # Sheraton Laval has 252 rooms


def test_extract_chambres_day_with_value():
    """Day 4 (2026-03-04) has 210 chambres à refaire."""
    result = extract_chambres('2026-03-04')
    assert isinstance(result, int)
    assert result == 210


def test_extract_chambres_day_21_empty():
    """Day 21 has no chambres à refaire value (empty cell), so returns 0."""
    result = extract_chambres('2026-03-21')
    assert result == 0


# ---------------------------------------------------------------------------
# Transelect
# ---------------------------------------------------------------------------

def test_extract_transelect_returns_dict_with_sections():
    result = extract_transelect('2026-03-21')
    assert isinstance(result, dict)
    assert 'transelect_restaurant' in result or 'transelect_reception' in result


def test_extract_transelect_restaurant_valid_json():
    result = extract_transelect('2026-03-21')
    assert 'transelect_restaurant' in result
    blob = json.loads(result['transelect_restaurant'])
    assert '_terminals' in blob
    for card in ['debit', 'visa', 'mc', 'amex', 'discover']:
        assert card in blob, f"Missing card type {card}"
        assert 'esc_pct' in blob[card]


def test_extract_transelect_reception_valid_json():
    result = extract_transelect('2026-03-21')
    assert 'transelect_reception' in result
    blob = json.loads(result['transelect_reception'])
    assert '_terminals' in blob
    for card in ['debit', 'visa', 'mc', 'amex', 'discover']:
        assert card in blob, f"Missing card type {card}"


def test_extract_transelect_restaurant_known_values():
    """Verify TOTAL values from 2026-03-21 (uses TOTAUX columns, not raw POSITOUCH)."""
    result = extract_transelect('2026-03-21')
    blob = json.loads(result['transelect_restaurant'])
    assert blob['debit']['positouch'] == 8315.18
    assert blob['visa']['positouch'] == 6216.14
    assert blob['amex']['positouch'] == 520.6


def test_extract_transelect_reception_known_values():
    """Verify FreedomPay values from 2026-03-21."""
    result = extract_transelect('2026-03-21')
    blob = json.loads(result['transelect_reception'])
    assert blob['visa']['freedompay'] == 11170.4
    assert blob['mc']['freedompay'] == 11625.82
    assert blob['amex']['freedompay'] == 5107.58


# ---------------------------------------------------------------------------
# GEAC Balance Sheet
# ---------------------------------------------------------------------------

def test_extract_geac_balance_sheet_returns_json():
    result = extract_geac_balance_sheet('2026-03-21')
    assert isinstance(result, dict)
    assert 'geac_balance_sheet' in result


def test_extract_geac_balance_sheet_has_all_keys():
    result = extract_geac_balance_sheet('2026-03-21')
    blob = json.loads(result['geac_balance_sheet'])
    expected_keys = {
        'prev_dr', 'prev_gl', 'today_dr', 'today_gl',
        'facture_dr', 'facture_ar', 'advdep_dr', 'advdep_ad',
        'newbal_dr', 'newbal_gl',
    }
    assert set(blob.keys()) == expected_keys


def test_extract_geac_balance_sheet_nonzero_values():
    """The GEAC sheet always has data on 2026-03-21."""
    result = extract_geac_balance_sheet('2026-03-21')
    blob = json.loads(result['geac_balance_sheet'])
    # At least prev_dr and newbal_dr should be non-zero
    assert blob['prev_dr'] > 0, f"prev_dr should be > 0, got {blob['prev_dr']}"
    assert blob['newbal_dr'] > 0, f"newbal_dr should be > 0, got {blob['newbal_dr']}"


def test_extract_geac_balance_sheet_known_values():
    """Verify specific values from 2026-03-21."""
    result = extract_geac_balance_sheet('2026-03-21')
    blob = json.loads(result['geac_balance_sheet'])
    assert blob['prev_dr'] == 916907.17
    assert blob['prev_gl'] == 916907.17
    assert blob['today_dr'] == 30767.66
    assert blob['newbal_dr'] == 886139.51
    assert blob['newbal_gl'] == 886139.51


# ---------------------------------------------------------------------------
# Recap
# ---------------------------------------------------------------------------

def test_extract_recap_returns_dict_of_floats():
    result = extract_recap('2026-03-21')
    assert isinstance(result, dict)
    for k, v in result.items():
        assert isinstance(v, float), f"{k} should be float, got {type(v)}"


def test_extract_recap_has_expected_keys():
    result = extract_recap('2026-03-21')
    expected_keys = {
        'cash_ls_lecture', 'cash_pos_lecture',
        'cheque_ar_lecture', 'cheque_dr_lecture',
        'remb_gratuite_lecture', 'remb_client_lecture',
        'dueback_reception_lecture', 'dueback_nb_lecture',
        'recap_balance', 'deposit_cdn', 'deposit_us',
    }
    assert expected_keys.issubset(set(result.keys())), \
        f"Missing keys: {expected_keys - set(result.keys())}"


def test_extract_recap_known_values():
    """Verify specific values from 2026-03-21."""
    result = extract_recap('2026-03-21')
    assert result['cash_pos_lecture'] == 1947.46
    assert result['remb_gratuite_lecture'] == -2467.49
    assert result['remb_client_lecture'] == -1231.64
    assert result['dueback_reception_lecture'] == 1231.64
    assert result['dueback_nb_lecture'] == 1232.21
    assert result['recap_balance'] == 15.09


# ---------------------------------------------------------------------------
# extract_all
# ---------------------------------------------------------------------------

def test_extract_all_bundles_every_extractor():
    result = extract_all('2026-03-21')
    assert isinstance(result, dict)
    # JSON blobs
    assert 'geac_balance_sheet' in result
    assert 'transelect_restaurant' in result
    # Scalar fields from recap
    assert 'cash_ls_lecture' in result
    # Chambres
    assert 'chambres_refaire' in result
    # List-of-dicts as JSON strings
    assert 'dueback_entries' in result
    assert 'sd_entries' in result


def test_extract_all_dueback_entries_is_json_string():
    result = extract_all('2026-03-21')
    parsed = json.loads(result['dueback_entries'])
    assert isinstance(parsed, list)
    assert len(parsed) > 0
    assert 'name' in parsed[0]
    assert 'amount' in parsed[0]


def test_extract_all_sd_entries_is_json_string():
    result = extract_all('2026-03-21')
    parsed = json.loads(result['sd_entries'])
    assert isinstance(parsed, list)
    assert len(parsed) > 0
    assert 'employee' in parsed[0]


def test_extract_all_chambres_is_int():
    result = extract_all('2026-03-21')
    assert isinstance(result['chambres_refaire'], int)


def test_extract_all_matches_individual_extractors():
    """extract_all must return the same values as calling each extractor."""
    day = '2026-03-21'
    bundled = extract_all(day)

    # GEAC
    geac = extract_geac_balance_sheet(day)
    assert bundled['geac_balance_sheet'] == geac['geac_balance_sheet']

    # Transelect
    ts = extract_transelect(day)
    for key in ts:
        assert bundled[key] == ts[key], f"Mismatch on {key}"

    # Recap
    recap = extract_recap(day)
    for key in recap:
        assert bundled[key] == recap[key], f"Mismatch on recap {key}"

    # Chambres
    assert bundled['chambres_refaire'] == extract_chambres(day)

    # DueBack + SD (compare parsed)
    assert json.loads(bundled['dueback_entries']) == extract_dueback(day)
    assert json.loads(bundled['sd_entries']) == extract_sd(day)
