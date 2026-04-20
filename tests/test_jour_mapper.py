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
                'revenue': {'comptabilite': {'facture_direct': 45000.0}},
            },
            ar_summary_data={'front_office_transfers': {'guest_folios': 45000.0}},
        )
        result = mapper.compute_all()
        assert result.get(41) == pytest.approx(0.0)

    def test_ar_greater_than_fd_positive(self):
        """When AR > FD, AP is positive."""
        mapper = make_mapper(
            daily_rev_data={
                'revenue': {'comptabilite': {'facture_direct': 45000.0}},
            },
            ar_summary_data={'front_office_transfers': {'guest_folios': 46000.0}},
        )
        result = mapper.compute_all()
        assert result.get(41) == pytest.approx(1000.0)

    def test_ar_less_than_fd_negative(self):
        """When AR < FD, AP is negative."""
        mapper = make_mapper(
            daily_rev_data={
                'revenue': {'comptabilite': {'facture_direct': 50000.0}},
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
                'revenue': {'comptabilite': {'facture_direct': 5000.0}},
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


# ============================================================================
# Test new operation: room_formula (column CK, index 88)
# ============================================================================

class TestRoomFormula:
    """
    CK = total_rooms_today (integer). RJFillerCOM writes the formula;
    JourMapper just provides the numeric value.
    """

    def test_returns_integer_value(self):
        mapper = make_mapper(daily_rev_data={
            'market_segment': {'total_rooms_today': 248},
        })
        result = mapper.compute_all()
        assert result.get(88) == 248
        assert isinstance(result.get(88), int)

    def test_float_input_truncated_to_int(self):
        mapper = make_mapper(daily_rev_data={
            'market_segment': {'total_rooms_today': 248.0},
        })
        result = mapper.compute_all()
        assert result.get(88) == 248
        assert isinstance(result.get(88), int)

    def test_no_market_segment_data_skipped(self):
        mapper = make_mapper(daily_rev_data={})
        result = mapper.compute_all()
        assert 88 not in result

    def test_zero_rooms(self):
        mapper = make_mapper(daily_rev_data={
            'market_segment': {'total_rooms_today': 0},
        })
        result = mapper.compute_all()
        assert result.get(88) == 0


# ============================================================================
# Test compute_all integration
# ============================================================================

class TestComputeAllIntegration:
    """Verify that all 3 new operations work together in compute_all()."""

    def test_all_three_new_operations_together(self):
        mapper = make_mapper(
            daily_rev_data={
                'revenue': {
                    'comptabilite': {'facture_direct': 45000.0},
                    'ar_activity': {'total': 200.0},
                },
                'market_segment': {'total_rooms_today': 180},
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
        # CK = 180
        assert result.get(88) == 180

    def test_summary_tracks_new_columns(self):
        mapper = make_mapper(
            daily_rev_data={
                'revenue': {'comptabilite': {'facture_direct': 1000.0}},
                'market_segment': {'total_rooms_today': 200},
            },
            ar_summary_data={'front_office_transfers': {'guest_folios': 1000.0}},
        )
        mapper.compute_all()
        summary = mapper.get_summary()
        assert 'AP' in summary['values']
        assert 'CK' in summary['values']

    def test_unknown_operation_generates_warning(self):
        """Ensure the fallback warning still works."""
        mapper = make_mapper()
        # Manually test _compute_column with a fake config
        result = mapper._compute_column('ZZ', {'operation': 'nonexistent'})
        assert result is None
        assert any('unknown operation' in w for w in mapper.warnings)
