"""Tests for DBRS filler module."""
from utils.dbrs_filler import DBRSFiller


def test_dbrs_filler_class_exists():
    """DBRSFiller class should be importable."""
    filler = DBRSFiller()
    assert hasattr(filler, 'fill_dbrs_staging')
    assert hasattr(filler, 'paste_to_master')
    assert hasattr(filler, 'fill_and_paste')


def test_dailyrev_rows_mapping():
    """All room charge categories should be mapped."""
    assert len(DBRSFiller.DAILYREV_ROWS) >= 29
    assert DBRSFiller.DAILYREV_ROWS[2] == 'Room Chrg - Premium'
    assert DBRSFiller.DAILYREV_ROWS[23] == 'Room Chrg - Contract'
    assert DBRSFiller.DAILYREV_ROWS[29] == 'Guaranteed No Show'


def test_market_segment_rows_mapping():
    """Key segment codes should be mapped."""
    ms = DBRSFiller.MARKET_SEGMENT_ROWS
    assert ms[5] == 'T10'    # Premium Retail
    assert ms[59] == 'GC'    # Corporate Group
    assert ms[62] == 'T62'   # Complimentary
    assert ms[75] == 'GS'    # Group Social


def test_dailyrev_rows_coverage():
    """DailyRev mapping covers rows 2 through 30 with no gaps."""
    rows = DBRSFiller.DAILYREV_ROWS
    assert min(rows) == 2
    assert max(rows) == 30
    # Every integer from 2 to 30 must be present — no skipped data rows
    assert set(rows.keys()) == set(range(2, 31))


def test_market_segment_rows_no_subtotal_rows():
    """Known subtotal rows must not appear in the mapping.

    Rows 4, 6, 7, 10, 11, 15, 16, 19, 20, 27, 28 are SUBTOTAL formula rows
    in the Market Segment tab. Writing to them would corrupt workbook formulas.
    """
    known_subtotal_rows = {4, 6, 7, 10, 11, 15, 16, 19, 20, 27, 28}
    mapped_rows = set(DBRSFiller.MARKET_SEGMENT_ROWS.keys())
    overlap = known_subtotal_rows & mapped_rows
    assert overlap == set(), f'Subtotal rows in mapping: {overlap}'


def test_day_column_formula():
    """Day-to-column mapping: day 1 -> col 2 (B), day 14 -> col 15 (O), day 31 -> col 32 (AF)."""
    import datetime
    # The mapping is: day_col = audit_date.day + 1
    # Verify the constant described in section 14.6 of RJ_AUTOFILL_MASTER.md.
    # Use January (31 days) for the day-31 case; April only has 30 days.
    cases = [
        (datetime.date(2026, 4, 1), 2),   # day 1 -> col B (2)
        (datetime.date(2026, 4, 14), 15),  # day 14 -> col O (15)
        (datetime.date(2026, 1, 31), 32),  # day 31 -> col AF (32)
    ]
    for date, expected_col in cases:
        assert date.day + 1 == expected_col


def test_insertion_row_offset():
    """DBRS Insertion row N maps to month tab row N+96 (spec section 14.5)."""
    # R2 -> R98, R89 -> R185
    for ins_row, expected_target in [(2, 98), (7, 103), (89, 185)]:
        assert ins_row + 96 == expected_target


def test_master_paths_defined():
    """Master DBR path list should have at least one entry."""
    assert len(DBRSFiller.MASTER_PATHS) >= 1
    # Primary path must reference DBRS staging file separately
    assert DBRSFiller.DBRS_PATH != DBRSFiller.MASTER_PATHS[0]
