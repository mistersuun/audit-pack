"""Tests for column mapping fixes per docs/RJ_AUTOFILL_MASTER.md."""
from utils.daily_rev_jour_mapping import DAILY_REV_TO_JOUR


def test_ap_is_geac_compensation_not_machine_distributrice():
    ap = DAILY_REV_TO_JOUR['AP']
    assert ap['column_index'] == 41
    assert 'machine_distributrice' not in str(ap.get('base_field', ''))
    desc = ap.get('description', '').lower()
    assert 'geac' in desc or 'facture direct' in desc


def test_ax_ay_exclude_fb_opera_taxes():
    ay = DAILY_REV_TO_JOUR['AY']
    ax = DAILY_REV_TO_JOUR['AX']
    fb_tps = ['non_revenue.restaurant_piazza.tps', 'non_revenue.banquet.tps',
              'non_revenue.la_spesa.tps', 'non_revenue.services_chambres.tps']
    fb_tvq = ['non_revenue.restaurant_piazza.tvq', 'non_revenue.banquet.tvq',
              'non_revenue.la_spesa.tvq', 'non_revenue.services_chambres.tvq']
    for field in fb_tps:
        assert field not in ay.get('accumulator_fields', [])
    for field in fb_tvq:
        assert field not in ax.get('accumulator_fields', [])


def test_cf_uses_ar_formula():
    cf = DAILY_REV_TO_JOUR['CF']
    assert cf['column_index'] == 83
    assert 'payment' in (cf.get('description', '') + cf.get('formula', '')).lower()


def test_aw_has_three_components():
    aw = DAILY_REV_TO_JOUR['AW']
    assert aw['column_index'] == 48
    assert aw['operation'] == 'accumulate'
    fields = aw.get('accumulator_fields', [])
    assert len(fields) == 3
