"""
JourImporter — Extract Jour sheet data from RJ files and persist to database.

Bridges the RJ Excel file (in-memory) to the DailyJourMetrics table for
multi-year historical analytics. Reuses JOUR_COLS mapping from analytics.py.

Usage:
    from utils.jour_importer import JourImporter

    # From upload
    metrics, info = JourImporter.extract_from_rj(file_bytes, 'RJ_20260115.xls')
    count = JourImporter.persist_batch(metrics)

    # Check data range
    status = JourImporter.get_data_status()
"""

import xlrd
from io import BytesIO
from datetime import date, datetime
import logging
import re

from database.models import db, DailyJourMetrics
from utils.analytics import JOUR_COLS, FB_OUTLETS, TOTAL_ROOMS

logger = logging.getLogger(__name__)


# Map from JOUR_COLS keys → list of column indices to sum for each outlet
_OUTLET_COLS = {
    'cafe_link': [4, 5, 6, 7, 8],
    'piazza': [9, 10, 11, 12, 13],
    'spesa': [14, 15, 16, 17, 18],
    'room_svc': [19, 20, 21, 22, 23],
    'banquet': [24, 25, 26, 27, 28],
}

# F&B category column indices (sum across all outlets for each category)
_CATEGORY_COLS = {
    'nourriture': [4, 9, 14, 19, 24],   # nour cols across outlets
    'boisson': [5, 10, 15, 20, 25],      # boi cols
    'bieres': [6, 11, 16, 21, 26],       # bie cols
    'mineraux': [7, 12, 17, 22, 27],     # min cols
    'vins': [8, 13, 18, 23, 28],         # vin cols
}


class JourImporter:
    """Extract and persist Jour sheet data from RJ files."""

    @staticmethod
    def extract_from_rj(file_bytes, filename=None):
        """
        Extract daily metrics from an RJ file's Jour sheet.

        Args:
            file_bytes: BytesIO or bytes of the RJ .xls file
            filename: Original filename (for date inference + tracking)

        Returns:
            tuple: (list[DailyJourMetrics], info_dict)
                info_dict has: {month, year, days_extracted, filename}
        """
        # Read file
        if isinstance(file_bytes, BytesIO):
            file_bytes.seek(0)
            raw = file_bytes.read()
            file_bytes.seek(0)  # Reset for further use
        elif isinstance(file_bytes, bytes):
            raw = file_bytes
        else:
            raw = file_bytes.read()

        wb = xlrd.open_workbook(file_contents=raw, formatting_info=True)

        # Get Jour sheet
        jour_sheet = None
        for name in ['Jour', 'jour', 'JOUR']:
            try:
                jour_sheet = wb.sheet_by_name(name)
                break
            except xlrd.biffh.XLRDError:
                continue

        if jour_sheet is None:
            return [], {'error': 'No Jour sheet found', 'filename': filename}

        # Get month/year from controle sheet
        month, year = JourImporter._read_controle_date(wb)

        # Fallback: parse from filename
        if not month or not year:
            fname_date = JourImporter._parse_filename_date(filename)
            if fname_date:
                month = month or fname_date['mois']
                year = year or fname_date['annee']

        if not month or not year:
            return [], {'error': 'Cannot determine month/year from file', 'filename': filename}

        # Parse each day row
        metrics = []
        for row in range(1, min(33, jour_sheet.nrows)):
            jour_val = JourImporter._cell(jour_sheet, row, JOUR_COLS['jour'])
            if not jour_val or not isinstance(jour_val, (int, float)):
                continue

            day_num = int(jour_val)
            if day_num < 1 or day_num > 31:
                continue

            # Read all columns for this day
            day_data = {}
            for key, col_idx in JOUR_COLS.items():
                if col_idx < jour_sheet.ncols:
                    val = JourImporter._cell(jour_sheet, row, col_idx)
                    day_data[key] = float(val) if isinstance(val, (int, float)) else 0.0
                else:
                    day_data[key] = 0.0

            # Skip empty days
            if day_data.get('chambres', 0) == 0 and day_data.get('rooms_simple', 0) == 0:
                continue

            # Build the date
            try:
                day_date = date(year, month, day_num)
            except ValueError:
                logger.warning(f"Invalid date: {year}-{month}-{day_num}, skipping")
                continue

            # Create DailyJourMetrics object
            m = JourImporter._map_to_model(day_data, day_date, filename)
            metrics.append(m)

        info = {
            'month': month,
            'year': year,
            'days_extracted': len(metrics),
            'filename': filename,
        }

        return metrics, info

    @staticmethod
    def persist_batch(metrics, source='rj_upload'):
        """
        Upsert a batch of DailyJourMetrics into the database.
        Updates existing records (by date), inserts new ones.

        Args:
            metrics: list of DailyJourMetrics (unsaved ORM objects)
            source: 'rj_upload' or 'bulk_import'

        Returns:
            dict: {inserted: N, updated: N, total: N}
        """
        inserted = 0
        updated = 0

        for m in metrics:
            m.source = source
            existing = DailyJourMetrics.query.filter_by(date=m.date).first()

            if existing:
                # Update all fields
                JourImporter._update_existing(existing, m)
                updated += 1
            else:
                db.session.add(m)
                inserted += 1

        db.session.commit()

        return {'inserted': inserted, 'updated': updated, 'total': inserted + updated}

    @staticmethod
    def get_data_status():
        """
        Get summary of historical data in the database.

        Returns:
            dict: {total_days, date_range, years_covered, months_with_data}
        """
        total = DailyJourMetrics.query.count()

        if total == 0:
            return {
                'total_days': 0,
                'date_range': None,
                'years_covered': 0,
                'months_with_data': [],
            }

        min_date = db.session.query(db.func.min(DailyJourMetrics.date)).scalar()
        max_date = db.session.query(db.func.max(DailyJourMetrics.date)).scalar()

        # Get distinct year-month pairs
        months = db.session.query(
            DailyJourMetrics.year,
            DailyJourMetrics.month
        ).distinct().order_by(
            DailyJourMetrics.year,
            DailyJourMetrics.month
        ).all()

        years = set(m[0] for m in months)

        return {
            'total_days': total,
            'date_range': {
                'from': min_date.isoformat() if min_date else None,
                'to': max_date.isoformat() if max_date else None,
            },
            'years_covered': len(years),
            'months_with_data': [
                {'year': y, 'month': m} for y, m in months
            ],
        }

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    @staticmethod
    def _read_controle_date(wb):
        """Read month and year from the controle sheet."""
        month = year = None
        for name in ['controle', 'Controle', 'CONTROLE']:
            try:
                sheet = wb.sheet_by_name(name)
                # B4 = mois (row 3, col 1)
                try:
                    val = sheet.cell_value(3, 1)
                    if isinstance(val, (int, float)) and 1 <= val <= 12:
                        month = int(val)
                except (IndexError, ValueError):
                    pass
                # B5 = annee (row 4, col 1)
                try:
                    val = sheet.cell_value(4, 1)
                    if isinstance(val, (int, float)) and 2000 <= val <= 2099:
                        year = int(val)
                except (IndexError, ValueError):
                    pass
                break
            except xlrd.biffh.XLRDError:
                continue

        return month, year

    @staticmethod
    def _parse_filename_date(filename):
        """Extract date info from filename (reuses rj_core pattern)."""
        if not filename:
            return None

        name = filename.rsplit('.', 1)[0]

        # YYYYMMDD or YYYY-MM-DD
        m = re.search(r'(20\d{2})[-_]?(0[1-9]|1[0-2])[-_]?(0[1-9]|[12]\d|3[01])', name)
        if m:
            return {'jour': int(m.group(3)), 'mois': int(m.group(2)), 'annee': int(m.group(1))}

        # DD-MM-YYYY
        m = re.search(r'(0[1-9]|[12]\d|3[01])[-/_](0[1-9]|1[0-2])[-/_](20\d{2})', name)
        if m:
            return {'jour': int(m.group(1)), 'mois': int(m.group(2)), 'annee': int(m.group(3))}

        # French month names
        months_fr = {
            'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12
        }
        lower = name.lower()
        for mname, mnum in months_fr.items():
            if mname in lower:
                nums = re.findall(r'\d+', name)
                for n in nums:
                    v = int(n)
                    if 2020 <= v <= 2030:
                        return {'mois': mnum, 'annee': v}

        return None

    @staticmethod
    def _cell(sheet, row, col):
        """Safe cell read."""
        try:
            val = sheet.cell_value(row, col)
            return val if val != '' else 0.0
        except (IndexError, AttributeError):
            return 0.0

    @staticmethod
    def _map_to_model(day_data, day_date, filename=None):
        """
        Map a day_data dict (from Jour sheet) to a DailyJourMetrics ORM object.
        """
        # Outlet totals
        cafe_link = sum(day_data.get(k, 0) for k in
                        ['cafe_link_nour', 'cafe_link_boi', 'cafe_link_bie', 'cafe_link_min', 'cafe_link_vin'])
        piazza = sum(day_data.get(k, 0) for k in
                     ['piazza_nour', 'piazza_boi', 'piazza_bie', 'piazza_min', 'piazza_vin'])
        spesa = sum(day_data.get(k, 0) for k in
                    ['spesa_nour', 'spesa_boi', 'spesa_bie', 'spesa_min', 'spesa_vin'])
        room_svc = sum(day_data.get(k, 0) for k in
                       ['room_svc_nour', 'room_svc_boi', 'room_svc_bie', 'room_svc_min', 'room_svc_vin'])
        banquet = sum(day_data.get(k, 0) for k in
                      ['banquet_nour', 'banquet_boi', 'banquet_bie', 'banquet_min', 'banquet_vin'])

        fb_revenue = cafe_link + piazza + spesa + room_svc + banquet

        # F&B categories
        total_nour = sum(day_data.get(k, 0) for k in
                         ['cafe_link_nour', 'piazza_nour', 'spesa_nour', 'room_svc_nour', 'banquet_nour'])
        total_boi = sum(day_data.get(k, 0) for k in
                        ['cafe_link_boi', 'piazza_boi', 'spesa_boi', 'room_svc_boi', 'banquet_boi'])
        total_bie = sum(day_data.get(k, 0) for k in
                        ['cafe_link_bie', 'piazza_bie', 'spesa_bie', 'room_svc_bie', 'banquet_bie'])
        total_min = sum(day_data.get(k, 0) for k in
                        ['cafe_link_min', 'piazza_min', 'spesa_min', 'room_svc_min', 'banquet_min'])
        total_vin = sum(day_data.get(k, 0) for k in
                        ['cafe_link_vin', 'piazza_vin', 'spesa_vin', 'room_svc_vin', 'banquet_vin'])

        # Other revenue
        chambres = day_data.get('chambres', 0)
        tips = day_data.get('pourboires', 0)
        tabagie = day_data.get('tabagie', 0)
        other_rev = sum(day_data.get(k, 0) for k in [
            'equipement', 'divers', 'location_salles', 'socan', 'resonne',
            'tel_interurb', 'tel_local', 'tel_frais_serv', 'valet_buanderie',
            'mch_liqueur', 'st_martin_elec', 'buanderette', 'autres_gl',
            'sonifi', 'autre_rev', 'location_boutique', 'internet',
        ])

        total_revenue = chambres + fb_revenue + tips + tabagie + other_rev

        # Room stats
        rooms_simple = int(day_data.get('rooms_simple', 0))
        rooms_double = int(day_data.get('rooms_double', 0))
        rooms_suite = int(day_data.get('rooms_suite', 0))
        rooms_comp = int(day_data.get('rooms_comp', 0))
        total_sold = rooms_simple + rooms_double + rooms_suite + rooms_comp
        rooms_avail = int(day_data.get('disponible', 0)) or TOTAL_ROOMS
        nb_clients = int(day_data.get('nb_clients', 0))
        hors_usage = int(day_data.get('hors_usage', 0))
        ch_refaire = int(day_data.get('ch_refaire', 0))

        occ_rate = (total_sold / rooms_avail * 100) if rooms_avail > 0 else 0

        # Payments
        visa = day_data.get('visa', 0)
        mc = day_data.get('mastercard', 0)
        amex_e = day_data.get('amex_elavon', 0)
        amex_g = day_data.get('amex_global', 0)
        debit = day_data.get('debit', 0)
        discover = day_data.get('discover', 0)
        total_cards = visa + mc + amex_e + amex_g + debit + discover

        # Taxes
        tps = day_data.get('tps', 0)
        tvq = day_data.get('tvq', 0)
        tvh = day_data.get('tvh', 0)

        # Cash
        bal_ouv = day_data.get('bal_ouv', 0)
        diff_caisse = day_data.get('diff_caisse', 0)
        new_balance = day_data.get('new_balance', 0)

        # KPIs
        adr = (chambres / total_sold) if total_sold > 0 else 0
        revpar = (chambres / rooms_avail) if rooms_avail > 0 else 0
        trevpar = (total_revenue / rooms_avail) if rooms_avail > 0 else 0
        food_pct = (total_nour / fb_revenue * 100) if fb_revenue > 0 else 0
        bev_pct = ((total_boi + total_bie + total_vin + total_min) / fb_revenue * 100) if fb_revenue > 0 else 0

        return DailyJourMetrics(
            date=day_date,
            year=day_date.year,
            month=day_date.month,
            day_of_month=day_date.day,

            room_revenue=round(chambres, 2),
            fb_revenue=round(fb_revenue, 2),
            cafe_link_total=round(cafe_link, 2),
            piazza_total=round(piazza, 2),
            spesa_total=round(spesa, 2),
            room_svc_total=round(room_svc, 2),
            banquet_total=round(banquet, 2),
            tips_total=round(tips, 2),
            tabagie_total=round(tabagie, 2),
            other_revenue=round(other_rev, 2),
            total_revenue=round(total_revenue, 2),

            total_nourriture=round(total_nour, 2),
            total_boisson=round(total_boi, 2),
            total_bieres=round(total_bie, 2),
            total_vins=round(total_vin, 2),
            total_mineraux=round(total_min, 2),

            rooms_simple=rooms_simple,
            rooms_double=rooms_double,
            rooms_suite=rooms_suite,
            rooms_comp=rooms_comp,
            total_rooms_sold=total_sold,
            rooms_available=rooms_avail,
            occupancy_rate=round(occ_rate, 2),
            nb_clients=nb_clients,
            rooms_hors_usage=hors_usage,
            rooms_ch_refaire=ch_refaire,

            visa_total=round(visa, 2),
            mastercard_total=round(mc, 2),
            amex_elavon_total=round(amex_e, 2),
            amex_global_total=round(amex_g, 2),
            debit_total=round(debit, 2),
            discover_total=round(discover, 2),
            total_cards=round(total_cards, 2),

            tps_total=round(tps, 2),
            tvq_total=round(tvq, 2),
            tvh_total=round(tvh, 2),

            opening_balance=round(bal_ouv, 2),
            cash_difference=round(diff_caisse, 2),
            closing_balance=round(new_balance, 2),

            adr=round(adr, 2),
            revpar=round(revpar, 2),
            trevpar=round(trevpar, 2),
            food_pct=round(food_pct, 2),
            beverage_pct=round(bev_pct, 2),

            rj_filename=filename,
        )

    @staticmethod
    def _update_existing(existing, new_metrics):
        """Update an existing DailyJourMetrics record with new data."""
        fields = [
            'room_revenue', 'fb_revenue', 'cafe_link_total', 'piazza_total',
            'spesa_total', 'room_svc_total', 'banquet_total', 'tips_total',
            'tabagie_total', 'other_revenue', 'total_revenue',
            'total_nourriture', 'total_boisson', 'total_bieres', 'total_vins', 'total_mineraux',
            'rooms_simple', 'rooms_double', 'rooms_suite', 'rooms_comp',
            'total_rooms_sold', 'rooms_available', 'occupancy_rate', 'nb_clients',
            'rooms_hors_usage', 'rooms_ch_refaire',
            'visa_total', 'mastercard_total', 'amex_elavon_total', 'amex_global_total',
            'debit_total', 'discover_total', 'total_cards',
            'tps_total', 'tvq_total', 'tvh_total',
            'opening_balance', 'cash_difference', 'closing_balance',
            'adr', 'revpar', 'trevpar', 'food_pct', 'beverage_pct',
            'source', 'rj_filename',
        ]
        for field in fields:
            setattr(existing, field, getattr(new_metrics, field))
        existing.updated_at = datetime.utcnow()
