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


def test_panne_extraction():
    from utils.parsers.sales_journal_parser import SalesJournalParser
    sj_text = b"""HOTEL SHERATON LAVAL                                                   PAGE:   1
REPORT DATE: 04/15/2026                                 REPORT TIME:  1:07:16.86
--------------------------------------------------------------------------------
                      SALES JOURNAL REPORT FOR 04/15/2026
                         SALES JOURNAL for Entire house
Account #         Account Name               Debits      Credits
--------------------------------------------------------------------------------
                 PIAZZA
                  NOURRITURE                             2828.50
                  TPS                                    1950.85
                  TVQ                                    3891.46
                                               0.00
                  COMPTANT                                640.92
                  VISA                      1782.26
                  MASTERCARD                 912.63
                  AMEX                       310.23
                  INTERAC                    568.08
                  CHAMBRE                  41791.03
                  PANNE VISA                  62.50
                  PANNE INTERACT              17.49
                  ADMINISTRATION             348.58
                  HOTEL PROMOTION            101.50
                  FORFAIT                    142.60
                  PANNE LIEN HOTEL             9.00
                  POURBOIRE CHARGE           817.97       817.97
                                         ----------   ----------
                                           53392.62 *   53392.62 *
"""
    parser = SalesJournalParser(sj_text, filename='test.txt')
    parser.parse()
    result = parser.get_result()
    data = result['data']

    # Check pannes extracted
    assert data.get('pannes', {}).get('visa') == 62.50
    assert data.get('pannes', {}).get('interac') == 17.49
    assert data.get('pannes', {}).get('lien_hotel') == 9.00

    # Check positouch totals include pannes
    pos = data.get('positouch_totals', {})
    assert pos.get('visa') == 1782.26 + 62.50
    assert pos.get('interac') == 568.08 + 17.49
    assert pos.get('mastercard') == 912.63  # no panne
    assert pos.get('amex') == 310.23  # no panne
