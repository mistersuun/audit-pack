"""Tests for JourMapper — bridges parser output to jour sheet columns.

Covers existing operations (direct, subtract, accumulate) and the 3 new
operations added for Phase 2: geac_compensation, cf_transfer, room_formula.
"""

import pytest
from utils.jour_mapper import JourMapper


# ============================================================================
# Helpers
# ============================================================================

def make_mapper(**kwargs):
    """Shortcut to build a JourMapper with only the data sources needed."""
    return JourMapper(**kwargs)


# ============================================================================
# Test existing operations (baseline coverage)
# ============================================================================

class TestDirectOperation:
    """Operation 'direct': value = base_field value."""

    def test_direct_from_daily_rev(self):
        mapper = make_mapper(daily_rev_data={
            'revenue': {'telephones': {'local': 42.0}}
        })
        result = mapper.compute_all()
        # AL (col 37) = revenue.telephones.local
        assert result.get(37) == 42.0

    def test_direct_missing_field_skipped(self):
        mapper = make_mapper(daily_rev_data={})
        result = mapper.compute_all()
        assert 37 not in result  # AL not produced when no data

    def test_direct_zero_is_kept(self):
        mapper = make_mapper(daily_rev_data={
            'revenue': {'telephones': {'local': 0.0}}
        })
        result = mapper.compute_all()
        assert result.get(37) == 0.0


class TestSubtractOperation:
    """Operation 'subtract': value = base - subtract_field."""

    def test_subtract_chambres_minus_club_lounge(self):
        mapper = make_mapper(daily_rev_data={
            'revenue': {'chambres': {'total': 50000.0}},
            'non_revenue': {'club_lounge': {'total': 200.0}},
        })
        result = mapper.compute_all()
        # AK (col 36) = chambres.total - club_lounge.total
        assert result.get(36) == pytest.approx(49800.0)

    def test_subtract_with_no_subtract_field(self):
        """When subtract_field resolves to None, treat as 0."""
        mapper = make_mapper(daily_rev_data={
            'revenue': {'chambres': {'total': 50000.0}},
        })
        result = mapper.compute_all()
        assert result.get(36) == pytest.approx(50000.0)


class TestAccumulateOperation:
    """Operation 'accumulate': value = sum of all accumulator_fields."""

    def test_accumulate_tps(self):
        mapper = make_mapper(
            daily_rev_data={
                'non_revenue': {
                    'chambres_tax': {'tps': 100.0},
                    'telephones_tax': {'tps_local': 5.0, 'tps_interurbain': 3.0},
                    'autres_tax': {'tps_autres': 2.0},
                    'internet_nonrev': {'tps': 1.0},
                },
            },
            sales_journal_data={
                'taxes': {'tps': 50.0},
            },
        )
        result = mapper.compute_all()
        # AY (col 50) = sum of all TPS sources
        assert result.get(50) == pytest.approx(161.0)

    def test_accumulate_no_data_skipped(self):
        mapper = make_mapper(daily_rev_data={})
        result = mapper.compute_all()
        assert 50 not in result  # AY not produced


# ============================================================================
# Test new operation: geac_compensation (column AP, index 41)
# ============================================================================

class TestGeacCompensation:
    """
    AP = -(facture_direct - ar_guest_folios) = guest_folios - facture_direct.
    """

    def test_equal_fd_and_ar_returns_zero(self):
        """When FD = AR Guest Folios, AP = 0."""
        mapper = make_mapper(
            daily_rev_data={
                'settlements': {'facture_direct': -45000.0},
            },
            ar_summary_data={'front_office_transfers': {'guest_folios': 45000.0}},
        )
        result = mapper.compute_all()
        assert result.get(41) == pytest.approx(0.0)

    def test_ar_greater_than_fd_positive(self):
        """When AR > FD, AP is positive."""
        mapper = make_mapper(
            daily_rev_data={
                'settlements': {'facture_direct': -45000.0},
            },
            ar_summary_data={'front_office_transfers': {'guest_folios': 46000.0}},
        )
        result = mapper.compute_all()
        assert result.get(41) == pytest.approx(1000.0)

    def test_ar_less_than_fd_negative(self):
        """When AR < FD, AP is negative."""
        mapper = make_mapper(
            daily_rev_data={
                'settlements': {'facture_direct': -50000.0},
            },
            ar_summary_data={'front_office_transfers': {'guest_folios': 49000.0}},
        )
        result = mapper.compute_all()
        assert result.get(41) == pytest.approx(-1000.0)

    def test_no_fd_returns_none(self):
        """If facture_direct is missing, AP cannot be computed."""
        mapper = make_mapper(
            daily_rev_data={},
            ar_summary_data={'front_office_transfers': {'guest_folios': 46000.0}},
        )
        result = mapper.compute_all()
        assert 41 not in result

    def test_no_ar_treats_as_zero(self):
        """If AR Guest Folios is missing, treat as 0."""
        mapper = make_mapper(
            daily_rev_data={
                'settlements': {'facture_direct': -5000.0},
            },
            ar_summary_data={},
        )
        result = mapper.compute_all()
        # AP = 0 - 5000 = -5000
        assert result.get(41) == pytest.approx(-5000.0)


# ============================================================================
# Test new operation: cf_transfer (column CF, index 83)
# ============================================================================

class TestCfTransfer:
    """
    CF = AR Guest Folios - AR Payments - DR AR Misc.
    Uses accumulator_fields with '-' prefix for subtracted fields.
    Fields route through ar_summary_data and daily_rev_data.
    """

    def test_basic_cf_formula(self):
        """CF = 5000 - 1000 - 200 = 3800."""
        mapper = make_mapper(
            ar_summary_data={
                'front_office_transfers': {'guest_folios': 5000.0},
                'payments': 1000.0,
            },
            daily_rev_data={
                'revenue': {'ar_activity': {'total': 200.0}},
            },
        )
        result = mapper.compute_all()
        assert result.get(83) == pytest.approx(3800.0)

    def test_cf_only_transfers(self):
        """When only guest_folios is present."""
        mapper = make_mapper(
            ar_summary_data={
                'front_office_transfers': {'guest_folios': 5000.0},
            },
        )
        result = mapper.compute_all()
        assert result.get(83) == pytest.approx(5000.0)

    def test_cf_negative_result(self):
        """CF can be negative when subtractions exceed additions."""
        mapper = make_mapper(
            ar_summary_data={
                'front_office_transfers': {'guest_folios': 1000.0},
                'payments': 3000.0,
            },
            daily_rev_data={
                'revenue': {'ar_activity': {'total': 500.0}},
            },
        )
        result = mapper.compute_all()
        # 1000 - 3000 - 500 = -2500
        assert result.get(83) == pytest.approx(-2500.0)

    def test_cf_no_data_skipped(self):
        """CF returns None when no fields resolve."""
        mapper = make_mapper(daily_rev_data={})
        result = mapper.compute_all()
        assert 83 not in result

    def test_cf_zero_result(self):
        """CF = 0 when all components cancel out."""
        mapper = make_mapper(
            ar_summary_data={
                'front_office_transfers': {'guest_folios': 1200.0},
                'payments': 1000.0,
            },
            daily_rev_data={
                'revenue': {'ar_activity': {'total': 200.0}},
            },
        )
        result = mapper.compute_all()
        assert result.get(83) == pytest.approx(0.0)


# CK (col 88) is now a direct-write column sourced from market_segment.total_rooms_today.
# The auditor overwrites the default Excel formula (=total_rooms-CM) with the actual count.
# See TestSalesJournalSourcedColumns below for market_segment test coverage.


class TestSalesJournalSourcedColumns:
    """Verify SJ-sourced columns resolve through the 'departments' wrapper."""

    def test_ad_banquet_pourboire(self):
        """AD (col 29) reads from sales_journal.banquet.pourboire_a_payer."""
        mapper = make_mapper(sales_journal_data={
            'departments': {'banquet': {'pourboire_a_payer': 1822.50}},
        })
        result = mapper.compute_all()
        assert result.get(29) == pytest.approx(1822.50)

    def test_ag_accumulates_sj_and_dr(self):
        """AG (col 32) = SJ banquet.location_salle + DR location_salle_forfait."""
        mapper = make_mapper(
            sales_journal_data={
                'departments': {'banquet': {'location_salle': 15300.0}},
            },
            daily_rev_data={
                'revenue': {'autres_revenus': {'location_salle_forfait': 40.0}},
            },
        )
        result = mapper.compute_all()
        assert result.get(32) == pytest.approx(15340.0)

    def test_au_accumulates_dr_and_sj(self):
        """AU (col 46) = DR lit_pliant + SJ chambres.fr_etage."""
        mapper = make_mapper(
            daily_rev_data={
                'revenue': {'autres_revenus': {'lit_pliant': 20.0}},
            },
            sales_journal_data={
                'departments': {'chambres': {'fr_etage': 21.0}},
            },
        )
        result = mapper.compute_all()
        assert result.get(46) == pytest.approx(41.0)


class TestMarketSegmentColumns:
    """Verify CK/CN/CO resolve from market_segment_data."""

    def test_ck_total_rooms(self):
        """CK (col 88) reads from market_segment.total_rooms_today."""
        mapper = make_mapper(market_segment_data={'total_rooms_today': 168})
        result = mapper.compute_all()
        assert result.get(88) == 168

    def test_cn_complimentary_rooms(self):
        """CN (col 91) reads from market_segment.complimentary_rooms_today."""
        mapper = make_mapper(market_segment_data={'complimentary_rooms_today': 3})
        result = mapper.compute_all()
        assert result.get(91) == 3

    def test_co_total_guests(self):
        """CO (col 92) reads from market_segment.total_guests_today."""
        mapper = make_mapper(market_segment_data={'total_guests_today': 198})
        result = mapper.compute_all()
        assert result.get(92) == 198

    def test_cp_dbrs_ooo_rooms(self):
        """CP (col 93) reads from dbrs.ooo_rooms."""
        mapper = make_mapper(dbrs_data={'ooo_rooms': 33})
        result = mapper.compute_all()
        assert result.get(93) == 33


# ============================================================================
# Test compute_all integration
# ============================================================================

class TestComputeAllIntegration:
    """Verify that geac_compensation + cf_transfer work together."""

    def test_geac_compensation_and_cf_together(self):
        mapper = make_mapper(
            daily_rev_data={
                'settlements': {'facture_direct': -45000.0},
                'revenue': {'ar_activity': {'total': 200.0}},
            },
            ar_summary_data={
                'front_office_transfers': {'guest_folios': 46000.0},
                'payments': 1000.0,
            },
        )
        result = mapper.compute_all()

        # AP = 46000 - 45000 = 1000
        assert result.get(41) == pytest.approx(1000.0)
        # CF = 46000 - 1000 - 200 = 44800
        assert result.get(83) == pytest.approx(44800.0)

    def test_summary_tracks_computed_columns(self):
        mapper = make_mapper(
            daily_rev_data={
                'settlements': {'facture_direct': -1000.0},
            },
            ar_summary_data={'front_office_transfers': {'guest_folios': 1000.0}},
        )
        mapper.compute_all()
        summary = mapper.get_summary()
        assert 'AP' in summary['values']
        assert 'CF' in summary['values']

    def test_unknown_operation_generates_warning(self):
        """Ensure the fallback warning still works."""
        mapper = make_mapper()
        # Manually test _compute_column with a fake config
        result = mapper._compute_column('ZZ', {'operation': 'nonexistent'})
        assert result is None
        assert any('unknown operation' in w for w in mapper.warnings)
