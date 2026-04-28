"""Run the existing DBRSFiller for Apr 23, 2026.

Parses DAILY_REV.pdf + MARKET_SEGMENT.pdf, then calls DBRSFiller.fill_and_paste()
which:
  1. Fills K:\\DBRS\\DBRS_formule.2025_corriger.xlsm (DailyRev + Market Segment)
  2. Reads DBRS Insertion B2:B89
  3. Updates Setup!F8 with audit_date in the Master DBR workbook
  4. Pastes values into Apr tab, day 23 column (skipping formula cells)
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.parsers.daily_revenue_parser import DailyRevenueParser
from utils.parsers.market_segment_parser import MarketSegmentParser
from utils.dbrs_filler import DBRSFiller


AUDIT_DATE = date(2026, 4, 23)
G4_CLUB_LOUNGE = 40  # Apr 23 G4 forfait in dollars (same as balancer p-g4)

DR_PDF = r'K:\Audition\04 - April\23-04-2026\DAILY_REV.pdf'
MS_PDF = r'K:\Audition\04 - April\23-04-2026\MARKET_SEGMENT.pdf'


def extract_room_charges(dr_parser):
    """Build {label: today_value} dict for all 40 DailyRev template rows + special."""
    ch_text = dr_parser._get_between(dr_parser.raw_text, 'Chambres', 'TELEPHONES')
    if not ch_text:
        raise RuntimeError('Could not find Chambres section in DR PDF')

    labels = list(DBRSFiller.DAILYREV_ROWS.values()) + ['Room Charge + Allowa']
    result = {}
    for label in labels:
        try:
            result[label] = dr_parser._get_today(ch_text, label)
        except Exception as e:
            print(f'  [warn] {label}: {e}')
            result[label] = 0.0
    return result


def extract_rooms_by_segment(ms_parser):
    """Build {code: today_rooms} dict from parsed segments list."""
    return {seg['code']: seg['today_rooms'] for seg in ms_parser.segments}


def main():
    print(f'=== DBRS Fill + Master Paste for {AUDIT_DATE} ===\n')

    print(f'[1/3] Parsing DR: {DR_PDF}')
    with open(DR_PDF, 'rb') as f:
        dr_bytes = f.read()
    dr = DailyRevenueParser(dr_bytes, filename='DAILY_REV.pdf')
    dr.parse()
    room_charges = extract_room_charges(dr)
    nz = sum(1 for v in room_charges.values() if v)
    print(f'  {nz} non-zero room charge lines')
    total_2_41 = sum(v for lbl, v in room_charges.items() if lbl != 'Room Charge + Allowa')
    print(f'  SUM(B2:B41) = {total_2_41:.2f}')
    print(f'  Room Charge + Allowa = {room_charges.get("Room Charge + Allowa", 0):.2f}')
    print(f'  Grand Total du RJ = {total_2_41 + room_charges.get("Room Charge + Allowa", 0) - G4_CLUB_LOUNGE:.2f}')

    print(f'\n[2/3] Parsing MS: {MS_PDF}')
    with open(MS_PDF, 'rb') as f:
        ms_bytes = f.read()
    ms = MarketSegmentParser(ms_bytes, filename='MARKET_SEGMENT.pdf')
    ms.parse()
    rooms_by_seg = extract_rooms_by_segment(ms)
    print(f'  {len(rooms_by_seg)} segments found, total rooms today: {sum(rooms_by_seg.values())}')
    top = sorted(rooms_by_seg.items(), key=lambda x: -x[1])[:5]
    for code, rooms in top:
        print(f'    {code}: {rooms} rooms')

    # Show which template-expected codes are missing from today's PDF
    expected_codes = set(DBRSFiller.MARKET_SEGMENT_ROWS.values())
    parsed_codes = set(rooms_by_seg.keys())
    missing = expected_codes - parsed_codes
    extra = parsed_codes - expected_codes
    if missing:
        print(f'  Template codes NOT in today PDF ({len(missing)}): {sorted(missing)}')
    if extra:
        print(f'  PDF codes NOT in template ({len(extra)}): {sorted(extra)}')

    print(f'\n[3/3] Running DBRSFiller.fill_and_paste (G4={G4_CLUB_LOUNGE})...')
    filler = DBRSFiller()
    result = filler.fill_and_paste(
        audit_date=AUDIT_DATE,
        dr_room_charges=room_charges,
        ms_rooms_by_segment=rooms_by_seg,
        g4=G4_CLUB_LOUNGE,
    )

    ins = result['staging']['dbrs_insertion']
    pst = result['paste']
    print(f'\n=== DONE ===')
    print(f'DBRS Insertion rows filled (non-zero): {len(ins)}')
    print(f'Master tab:   {pst["month_tab"]}')
    print(f'Day column:   {pst["day_column"]}')
    print(f'Rows pasted:  {pst["rows_written"]}')
    print(f'\nFirst 15 insertion values:')
    for row in sorted(ins.keys())[:15]:
        print(f'  B{row:2} = {ins[row]}')

    # Print the DBRS Insertion rows the user cares about specifically
    print(f'\nDBRS R81 (ALLOWANCE)         = {ins.get(81, 0)}')
    print(f'DBRS R87 (TOTAL NET REVENUE) = {ins.get(87, 0)}')


if __name__ == '__main__':
    main()
