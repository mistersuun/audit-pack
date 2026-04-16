"""Tests for parser extraction fixes."""


def test_interhotel_extracted():
    from utils.parsers.daily_revenue_parser import DailyRevenueParser
    parser = DailyRevenueParser(b'', filename='test.pdf')
    text = "InterHotel XferIn 19.98 329.65 0.00 549.45"
    val = parser._get_today(text, 'InterHotel XferIn')
    assert val == 19.98


def test_interhotel_zero_when_missing():
    from utils.parsers.daily_revenue_parser import DailyRevenueParser
    parser = DailyRevenueParser(b'', filename='test.pdf')
    text = "Some other line 100.00"
    val = parser._get_today(text, 'InterHotel XferIn')
    assert val == 0.0


def test_pre_audit_timestamp_warning():
    from utils.parsers.daily_revenue_parser import DailyRevenueParser
    parser = DailyRevenueParser(b'', filename='test.pdf')
    parser.extracted_data = {}

    # Pre-audit should warn
    parser._check_timestamp_validity("15-APR-2026 12:59 AM")
    assert any('pre-audit' in w.lower() for w in parser.validation_warnings)

    # Post-audit should not warn
    parser.validation_warnings = []
    parser._check_timestamp_validity("15-APR-2026 03:28 AM")
    assert not any('pre-audit' in w.lower() for w in parser.validation_warnings)
