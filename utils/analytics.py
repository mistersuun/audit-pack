"""
Analytics Engine — Reads RJ Jour sheet and computes hotel BI metrics.

Extracts 31 days of data from the Jour sheet (117 columns) and computes:
- Revenue KPIs: ADR, RevPAR, TRevPAR, total revenue
- F&B Analytics: revenue by outlet, food/beverage mix
- Room Analytics: occupancy rate, room type mix, guest counts
- Payment Analysis: credit card breakdown, trends
- Tax Analytics: TPS, TVQ, TVH breakdown
- Trend Analysis: daily/weekly comparisons, anomaly detection
"""

import xlrd
from io import BytesIO
from statistics import stdev, mean as stats_mean
from collections import defaultdict
from datetime import date as date_type, timedelta


# =============================================================================
# JOUR SHEET COLUMN MAP (0-indexed)
# =============================================================================
JOUR_COLS = {
    # Core
    'jour': 0,           # Day number
    'bal_ouv': 1,        # Opening balance
    'diff_caisse': 2,    # Cash difference
    'new_balance': 3,    # New/Closing balance

    # F&B — Café Link / Pause Spesa (cols E-I = 4-8)
    'cafe_link_nour': 4,
    'cafe_link_boi': 5,
    'cafe_link_bie': 6,
    'cafe_link_min': 7,
    'cafe_link_vin': 8,

    # F&B — Piazza / Cupola (cols J-N = 9-13)
    'piazza_nour': 9,
    'piazza_boi': 10,
    'piazza_bie': 11,
    'piazza_min': 12,
    'piazza_vin': 13,

    # F&B — Marché La Spesa (cols O-S = 14-18)
    'spesa_nour': 14,
    'spesa_boi': 15,
    'spesa_bie': 16,
    'spesa_min': 17,
    'spesa_vin': 18,

    # F&B — Service aux Chambres (cols T-X = 19-23)
    'room_svc_nour': 19,
    'room_svc_boi': 20,
    'room_svc_bie': 21,
    'room_svc_min': 22,
    'room_svc_vin': 23,

    # F&B — Banquet (cols Y-AC = 24-28)
    'banquet_nour': 24,
    'banquet_boi': 25,
    'banquet_bie': 26,
    'banquet_min': 27,
    'banquet_vin': 28,

    # Other Revenue
    'pourboires': 29,       # AD - Tips
    'equipement': 30,       # AE
    'divers': 31,           # AF
    'location_salles': 32,  # AG - Hall rental
    'socan': 33,            # AH - SOCAN
    'resonne': 34,          # AI - Ré:sonne
    'tabagie': 35,          # AJ - Tobacco/Convenience
    'chambres': 36,         # AK - Room revenue (KEY!)
    'tel_interurb': 37,     # AL
    'tel_local': 38,        # AM
    'tel_frais_serv': 39,   # AN
    'valet_buanderie': 40,  # AO
    'mch_liqueur': 41,      # AP
    'st_martin_elec': 42,   # AQ
    'buanderette': 43,      # AR
    'autres_gl': 44,        # AS
    'sonifi': 45,           # AT
    'autre_rev': 46,        # AU
    'location_boutique': 47, # AV
    'internet': 48,         # AW

    # Taxes
    'tvq': 49,              # AX - TVQ Provinciale
    'tps': 50,              # AY - TPS Fédérale
    'tvh': 51,              # AZ - Taxe Hébergement

    # Other non-revenue
    'massage': 52,          # BA
    'vestiaire': 53,        # BB
    'ristournes': 54,       # BC
    'fax_photo': 55,        # BD
    'billet_promo': 56,     # BE
    'diff_forfait': 57,     # BF
    'fin_des': 58,          # BG
    'total_credit': 59,     # BH

    # Credit Cards
    'amex_elavon': 60,      # BI
    'discover': 61,         # BJ
    'mastercard': 62,       # BK
    'visa': 63,             # BL
    'debit': 64,            # BM
    'amex_global': 65,      # BN

    # Other
    'repas_nb': 66,         # BO
    'star_hot_50': 67,      # BP
    'hp_admin': 68,         # BQ
    'hotel_promo': 69,      # BR

    # Recap area
    'argent_recu': 72,       # BU
    'remb_serveurs': 73,     # BV
    'remb_gratuite': 74,     # BW
    'due_back_recep': 76,    # BY
    'surplus_deficit': 78,   # CA

    # Transfers
    'transfert_royal': 84,   # CG
    'tr_bancaire': 85,       # CH
    'cash_operation': 86,    # CI
    'transfer_ar': 83,       # CF

    # Room Statistics
    'rooms_simple': 88,      # CK
    'rooms_double': 89,      # CL (header may say empty but has data)
    'rooms_suite': 90,       # CM
    'rooms_comp': 91,        # CN
    'nb_clients': 92,        # CO
    'hors_usage': 93,        # CP
    'ch_refaire': 94,        # CQ
    'disponible': 95,        # CR

    # Escrow percentages
    'esc_amex': 96,          # CS
    'esc_diners': 97,        # CT
    'esc_master': 98,        # CU
    'esc_visa': 99,          # CV

    # Net card amounts
    'net_amex': 100,         # CW
    'net_diners': 101,       # CX
    'net_master': 102,       # CY
    'net_visa': 103,         # CZ

    # POS Totals (summary across all outlets)
    'total_nourriture': 110, # DG (or nearby)
    'total_alcool': 111,     # DH
    'total_bieres': 112,     # DI
    'total_mineraux': 113,   # DJ
    'total_vins': 114,       # DK
    'total_boisson': 116,    # DM
}

# Restaurant outlet groupings for F&B analysis
FB_OUTLETS = {
    'Café Link': {'nour': 4, 'boi': 5, 'bie': 6, 'min': 7, 'vin': 8},
    'Piazza/Cupola': {'nour': 9, 'boi': 10, 'bie': 11, 'min': 12, 'vin': 13},
    'Marché Spesa': {'nour': 14, 'boi': 15, 'bie': 16, 'min': 17, 'vin': 18},
    'Room Service': {'nour': 19, 'boi': 20, 'bie': 21, 'min': 22, 'vin': 23},
    'Banquet': {'nour': 24, 'boi': 25, 'bie': 26, 'min': 27, 'vin': 28},
}

from database.models import TOTAL_ROOMS  # 252, Sheraton Laval


class JourAnalytics:
    """
    Reads the Jour sheet from an RJ file and computes analytics.
    """

    def __init__(self, file_bytes):
        """Initialize with RJ file bytes."""
        if isinstance(file_bytes, BytesIO):
            file_bytes.seek(0)
            raw = file_bytes.read()
        elif isinstance(file_bytes, bytes):
            raw = file_bytes
        else:
            raw = file_bytes.read()

        self.wb = xlrd.open_workbook(file_contents=raw, formatting_info=True)
        self.jour = None
        self.days = []
        self._load()

    def _load(self):
        """Load and parse the Jour sheet into structured daily records."""
        # Try both 'Jour' and 'jour'
        for name in ['Jour', 'jour', 'JOUR']:
            try:
                self.jour = self.wb.sheet_by_name(name)
                break
            except xlrd.biffh.XLRDError:
                continue

        if self.jour is None:
            return

        self.days = []
        for row in range(1, min(33, self.jour.nrows)):
            jour_val = self._cell(row, JOUR_COLS['jour'])
            if not jour_val or not isinstance(jour_val, (int, float)):
                continue

            day_data = {'day': int(jour_val)}
            for key, col_idx in JOUR_COLS.items():
                if col_idx < self.jour.ncols:
                    val = self._cell(row, col_idx)
                    day_data[key] = float(val) if isinstance(val, (int, float)) else 0.0
                else:
                    day_data[key] = 0.0

            # Only include days with actual data (room revenue or room stats)
            if day_data.get('chambres', 0) != 0 or day_data.get('rooms_simple', 0) != 0:
                self.days.append(day_data)

    def _cell(self, row, col):
        """Safe cell read."""
        try:
            val = self.jour.cell_value(row, col)
            return val if val != '' else 0.0
        except (IndexError, AttributeError):
            return 0.0

    def has_data(self):
        return len(self.days) > 0

    # =========================================================================
    # KPI COMPUTATIONS
    # =========================================================================

    def get_executive_kpis(self):
        """Compute top-level hotel KPIs."""
        if not self.days:
            return self._empty_kpis()

        total_room_rev = sum(d.get('chambres', 0) for d in self.days)
        rooms_sold = sum(
            d.get('rooms_simple', 0) + d.get('rooms_double', 0) + d.get('rooms_suite', 0)
            for d in self.days
        )
        rooms_available = sum(d.get('disponible', 0) or TOTAL_ROOMS for d in self.days)
        rooms_comp = sum(d.get('rooms_comp', 0) for d in self.days)
        total_clients = sum(d.get('nb_clients', 0) for d in self.days)
        total_fb = sum(self._day_fb_total(d) for d in self.days)
        total_other = sum(self._day_other_revenue(d) for d in self.days)
        total_revenue = total_room_rev + total_fb + total_other

        # Card totals
        total_cards = sum(self._day_cards_total(d) for d in self.days)

        # Taxes
        total_tps = sum(d.get('tps', 0) for d in self.days)
        total_tvq = sum(d.get('tvq', 0) for d in self.days)
        total_tvh = sum(d.get('tvh', 0) for d in self.days)

        n = len(self.days)
        adr = total_room_rev / rooms_sold if rooms_sold > 0 else 0
        occ_rate = rooms_sold / rooms_available * 100 if rooms_available > 0 else 0
        revpar = total_room_rev / rooms_available if rooms_available > 0 else 0
        trevpar = total_revenue / rooms_available if rooms_available > 0 else 0

        return {
            'days_count': n,
            'total_revenue': round(total_revenue, 2),
            'avg_daily_revenue': round(total_revenue / n, 2) if n else 0,
            'room_revenue': round(total_room_rev, 2),
            'fb_revenue': round(total_fb, 2),
            'other_revenue': round(total_other, 2),
            'adr': round(adr, 2),
            'revpar': round(revpar, 2),
            'trevpar': round(trevpar, 2),
            'occupancy_rate': round(occ_rate, 1),
            'rooms_sold': int(rooms_sold),
            'rooms_available': int(rooms_available),
            'rooms_comp': int(rooms_comp),
            'total_clients': int(total_clients),
            'avg_clients_per_day': round(total_clients / n, 1) if n else 0,
            'total_cards': round(total_cards, 2),
            'total_taxes': round(total_tps + total_tvq + total_tvh, 2),
            'total_tps': round(total_tps, 2),
            'total_tvq': round(total_tvq, 2),
            'total_tvh': round(total_tvh, 2),
        }

    def get_revenue_trend(self):
        """Daily revenue trend for line chart."""
        return [{
            'day': d['day'],
            'room_revenue': round(d.get('chambres', 0), 2),
            'fb_revenue': round(self._day_fb_total(d), 2),
            'other_revenue': round(self._day_other_revenue(d), 2),
            'total': round(d.get('chambres', 0) + self._day_fb_total(d) + self._day_other_revenue(d), 2),
            'occupancy': round(self._day_occupancy(d), 1),
            'adr': round(self._day_adr(d), 2),
            'revpar': round(self._day_revpar(d), 2),
        } for d in self.days]

    def get_fb_analytics(self):
        """F&B analytics — breakdown by outlet and category."""
        outlet_totals = {}
        for outlet_name, cols in FB_OUTLETS.items():
            total = 0
            categories = {}
            for cat, col_idx in cols.items():
                cat_total = sum(d.get(list(JOUR_COLS.keys())[
                    list(JOUR_COLS.values()).index(col_idx)
                ], 0) for d in self.days)
                # Map short keys to full names
                cat_names = {'nour': 'Nourriture', 'boi': 'Boisson', 'bie': 'Bières',
                            'min': 'Minéraux', 'vin': 'Vins'}
                categories[cat_names.get(cat, cat)] = round(cat_total, 2)
                total += cat_total
            outlet_totals[outlet_name] = {
                'total': round(total, 2),
                'categories': categories,
            }

        # Category totals across all outlets
        cat_totals = {
            'Nourriture': round(sum(d.get('total_nourriture', 0) for d in self.days), 2),
            'Alcool': round(sum(d.get('total_alcool', 0) for d in self.days), 2),
            'Bières': round(sum(d.get('total_bieres', 0) for d in self.days), 2),
            'Minéraux': round(sum(d.get('total_mineraux', 0) for d in self.days), 2),
            'Vins': round(sum(d.get('total_vins', 0) for d in self.days), 2),
        }

        total_fb = sum(v for v in cat_totals.values())
        food_pct = round(cat_totals['Nourriture'] / total_fb * 100, 1) if total_fb else 0
        bev_pct = round(100 - food_pct, 1)

        # Daily trend by outlet
        fb_trend = []
        for d in self.days:
            entry = {'day': d['day']}
            for outlet_name, cols in FB_OUTLETS.items():
                day_total = 0
                for cat, col_idx in cols.items():
                    key = [k for k, v in JOUR_COLS.items() if v == col_idx][0]
                    day_total += d.get(key, 0)
                entry[outlet_name] = round(day_total, 2)
            fb_trend.append(entry)

        return {
            'outlets': outlet_totals,
            'category_totals': cat_totals,
            'total_fb': round(total_fb, 2),
            'food_pct': food_pct,
            'beverage_pct': bev_pct,
            'trend': fb_trend,
            'other': {
                'pourboires': round(sum(d.get('pourboires', 0) for d in self.days), 2),
                'tabagie': round(sum(d.get('tabagie', 0) for d in self.days), 2),
            }
        }

    def get_room_analytics(self):
        """Room/occupancy analytics."""
        trend = []
        for d in self.days:
            simple = d.get('rooms_simple', 0)
            double = d.get('rooms_double', 0)
            suite = d.get('rooms_suite', 0)
            comp = d.get('rooms_comp', 0)
            dispo = d.get('disponible', 0) or TOTAL_ROOMS
            sold = simple + double + suite
            occ = sold / dispo * 100 if dispo > 0 else 0

            trend.append({
                'day': d['day'],
                'simple': int(simple),
                'double': int(double),
                'suite': int(suite),
                'comp': int(comp),
                'sold': int(sold),
                'available': int(dispo),
                'occupancy': round(occ, 1),
                'clients': int(d.get('nb_clients', 0)),
                'hors_usage': int(d.get('hors_usage', 0)),
                'ch_refaire': int(d.get('ch_refaire', 0)),
                'adr': round(d.get('chambres', 0) / sold, 2) if sold > 0 else 0,
                'room_revenue': round(d.get('chambres', 0), 2),
            })

        # Aggregates
        total_sold = sum(t['sold'] for t in trend)
        total_avail = sum(t['available'] for t in trend)
        total_simple = sum(t['simple'] for t in trend)
        total_double = sum(t['double'] for t in trend)
        total_suite = sum(t['suite'] for t in trend)
        total_comp = sum(t['comp'] for t in trend)

        return {
            'trend': trend,
            'summary': {
                'avg_occupancy': round(total_sold / total_avail * 100, 1) if total_avail else 0,
                'total_rooms_sold': total_sold,
                'room_mix': {
                    'simple': total_simple,
                    'double': total_double,
                    'suite': total_suite,
                    'comp': total_comp,
                },
                'room_mix_pct': {
                    'simple': round(total_simple / total_sold * 100, 1) if total_sold else 0,
                    'double': round(total_double / total_sold * 100, 1) if total_sold else 0,
                    'suite': round(total_suite / total_sold * 100, 1) if total_sold else 0,
                    'comp': round(total_comp / total_sold * 100, 1) if total_sold else 0,
                },
                'avg_clients': round(sum(t['clients'] for t in trend) / len(trend), 1) if trend else 0,
                'avg_hors_usage': round(sum(t['hors_usage'] for t in trend) / len(trend), 1) if trend else 0,
            }
        }

    def get_payment_analytics(self):
        """Payment method breakdown."""
        cards = {
            'Amex ELAVON': sum(d.get('amex_elavon', 0) for d in self.days),
            'Discover': sum(d.get('discover', 0) for d in self.days),
            'Mastercard': sum(d.get('mastercard', 0) for d in self.days),
            'Visa': sum(d.get('visa', 0) for d in self.days),
            'Débit': sum(d.get('debit', 0) for d in self.days),
            'Amex GLOBAL': sum(d.get('amex_global', 0) for d in self.days),
        }

        total = sum(v for v in cards.values() if v > 0)
        breakdown = {k: {
            'amount': round(v, 2),
            'pct': round(abs(v) / total * 100, 1) if total else 0,
        } for k, v in cards.items()}

        # Daily trend
        trend = [{
            'day': d['day'],
            'visa': round(d.get('visa', 0), 2),
            'mastercard': round(d.get('mastercard', 0), 2),
            'amex': round(d.get('amex_elavon', 0) + d.get('amex_global', 0), 2),
            'debit': round(d.get('debit', 0), 2),
        } for d in self.days]

        # Escrow fees
        avg_esc = {
            'amex': round(sum(d.get('esc_amex', 0) for d in self.days) / len(self.days), 3) if self.days else 0,
            'master': round(sum(d.get('esc_master', 0) for d in self.days) / len(self.days), 3) if self.days else 0,
            'visa': round(sum(d.get('esc_visa', 0) for d in self.days) / len(self.days), 3) if self.days else 0,
        }

        return {
            'breakdown': breakdown,
            'total': round(total, 2),
            'trend': trend,
            'avg_escrow_pct': avg_esc,
        }

    def get_tax_analytics(self):
        """Tax breakdown and trends."""
        trend = [{
            'day': d['day'],
            'tps': round(d.get('tps', 0), 2),
            'tvq': round(d.get('tvq', 0), 2),
            'tvh': round(d.get('tvh', 0), 2),
            'total': round(d.get('tps', 0) + d.get('tvq', 0) + d.get('tvh', 0), 2),
        } for d in self.days]

        totals = {
            'tps': round(sum(d.get('tps', 0) for d in self.days), 2),
            'tvq': round(sum(d.get('tvq', 0) for d in self.days), 2),
            'tvh': round(sum(d.get('tvh', 0) for d in self.days), 2),
        }
        totals['total'] = round(sum(totals.values()), 2)

        return {
            'totals': totals,
            'trend': trend,
            'avg_daily': {k: round(v / len(self.days), 2) for k, v in totals.items()} if self.days else totals,
        }

    def get_anomalies(self):
        """Detect anomalies and provide actionable insights."""
        if len(self.days) < 3:
            return {'alerts': [], 'insights': []}

        alerts = []
        insights = []

        # Compute averages
        avg_occ = sum(self._day_occupancy(d) for d in self.days) / len(self.days)
        avg_adr = sum(self._day_adr(d) for d in self.days) / len(self.days)
        avg_fb = sum(self._day_fb_total(d) for d in self.days) / len(self.days)
        avg_rev = sum(d.get('chambres', 0) for d in self.days) / len(self.days)

        for d in self.days:
            day = d['day']
            occ = self._day_occupancy(d)
            adr = self._day_adr(d)
            fb = self._day_fb_total(d)
            rev = d.get('chambres', 0)

            # Low occupancy alert
            if occ < avg_occ * 0.7 and occ > 0:
                alerts.append({
                    'day': day, 'type': 'low_occupancy', 'severity': 'warning',
                    'message': f'Jour {day}: Occupation {occ:.0f}% vs moyenne {avg_occ:.0f}%',
                    'delta': round(occ - avg_occ, 1),
                })

            # High occupancy opportunity
            if occ > 95:
                insights.append({
                    'day': day, 'type': 'high_occupancy',
                    'message': f'Jour {day}: Occupation {occ:.0f}% — opportunité de pricing dynamique',
                })

            # ADR drop
            if adr < avg_adr * 0.8 and adr > 0:
                alerts.append({
                    'day': day, 'type': 'low_adr', 'severity': 'warning',
                    'message': f'Jour {day}: ADR ${adr:.2f} vs moyenne ${avg_adr:.2f}',
                    'delta': round(adr - avg_adr, 2),
                })

            # F&B drop
            if fb < avg_fb * 0.5 and avg_fb > 100:
                alerts.append({
                    'day': day, 'type': 'low_fb', 'severity': 'info',
                    'message': f'Jour {day}: F&B ${fb:.0f} vs moyenne ${avg_fb:.0f}',
                    'delta': round(fb - avg_fb, 2),
                })

            # Cash variance
            diff = d.get('diff_caisse', 0)
            if abs(diff) > 50:
                alerts.append({
                    'day': day, 'type': 'cash_variance', 'severity': 'danger',
                    'message': f'Jour {day}: Différence caisse ${diff:.2f}',
                    'delta': round(diff, 2),
                })

        # Revenue mix insights
        total_rev = sum(d.get('chambres', 0) for d in self.days)
        total_fb = sum(self._day_fb_total(d) for d in self.days)
        if total_rev > 0:
            fb_ratio = total_fb / total_rev * 100
            if fb_ratio < 15:
                insights.append({
                    'type': 'low_fb_ratio',
                    'message': f'Ratio F&B/Chambres à {fb_ratio:.1f}% — potentiel d\'amélioration des revenus F&B',
                })

        # Out of service rooms
        avg_oos = sum(d.get('hors_usage', 0) for d in self.days) / len(self.days)
        if avg_oos > 5:
            insights.append({
                'type': 'high_oos',
                'message': f'Moyenne de {avg_oos:.0f} chambres hors service — impact sur RevPAR',
            })

        return {
            'alerts': sorted(alerts, key=lambda x: {'danger': 0, 'warning': 1, 'info': 2}.get(x.get('severity', 'info'), 3)),
            'insights': insights,
        }

    # =========================================================================
    # ADVANCED ANALYTICS — Revenue Management, Efficiency, Opportunities
    # =========================================================================

    def get_advanced_kpis(self):
        """
        Compute advanced hotel KPIs not in the basic set.
        Designed to impress a GM / VP Ops / Owner.
        """
        if not self.days:
            return {}

        n = len(self.days)
        total_room_rev = sum(d.get('chambres', 0) for d in self.days)
        total_fb = sum(self._day_fb_total(d) for d in self.days)
        total_other = sum(self._day_other_revenue(d) for d in self.days)
        total_revenue = total_room_rev + total_fb + total_other
        rooms_sold = sum(
            d.get('rooms_simple', 0) + d.get('rooms_double', 0) + d.get('rooms_suite', 0)
            for d in self.days
        )
        rooms_comp = sum(d.get('rooms_comp', 0) for d in self.days)
        rooms_available = sum(d.get('disponible', 0) or TOTAL_ROOMS for d in self.days)
        total_clients = sum(d.get('nb_clients', 0) for d in self.days)
        total_oos = sum(d.get('hors_usage', 0) for d in self.days)
        tips = sum(d.get('pourboires', 0) for d in self.days)

        # --- Effective ADR (includes comp rooms in the denominator) ---
        total_rooms_incl_comp = rooms_sold + rooms_comp
        effective_adr = total_room_rev / total_rooms_incl_comp if total_rooms_incl_comp > 0 else 0

        # --- Comp Rate % ---
        comp_rate_pct = rooms_comp / total_rooms_incl_comp * 100 if total_rooms_incl_comp > 0 else 0

        # --- Comp Revenue Loss (comps × ADR = what we "gave away") ---
        adr = total_room_rev / rooms_sold if rooms_sold > 0 else 0
        comp_revenue_loss = rooms_comp * adr

        # --- Double Occupancy Factor (avg guests per room) ---
        double_occ_factor = total_clients / rooms_sold if rooms_sold > 0 else 0

        # --- F&B RevPAR (F&B per available room) ---
        fb_revpar = total_fb / rooms_available if rooms_available > 0 else 0

        # --- F&B per Guest ---
        fb_per_guest = total_fb / total_clients if total_clients > 0 else 0

        # --- Ancillary RevPAR ---
        ancillary_revpar = total_other / rooms_available if rooms_available > 0 else 0

        # --- Ancillary per Guest ---
        ancillary_per_guest = total_other / total_clients if total_clients > 0 else 0

        # --- Revenue per Guest (total) ---
        rev_per_guest = total_revenue / total_clients if total_clients > 0 else 0

        # --- OOS Cost Impact (lost revenue from out-of-service rooms) ---
        oos_cost = total_oos * adr  # each OOS room = 1 lost ADR

        # --- Tip Ratio (tips / F&B) ---
        tip_ratio = tips / total_fb * 100 if total_fb > 0 else 0

        # --- Card Processing Cost (estimated using escrow %) ---
        processing_cost = self._calc_processing_cost()

        # --- Volatility metrics (std dev) ---
        daily_revpar = [self._day_revpar(d) for d in self.days]
        daily_adr = [self._day_adr(d) for d in self.days if self._day_adr(d) > 0]
        daily_occ = [self._day_occupancy(d) for d in self.days]
        revpar_volatility = stdev(daily_revpar) if len(daily_revpar) >= 2 else 0
        adr_volatility = stdev(daily_adr) if len(daily_adr) >= 2 else 0
        occ_volatility = stdev(daily_occ) if len(daily_occ) >= 2 else 0

        # --- Opportunity Days (occ < 70%) and potential revenue ---
        opportunity_days = [d for d in self.days if self._day_occupancy(d) < 70 and self._day_occupancy(d) > 0]
        opp_rooms = sum(
            (d.get('disponible', 0) or TOTAL_ROOMS) * 0.70 -
            (d.get('rooms_simple', 0) + d.get('rooms_double', 0) + d.get('rooms_suite', 0))
            for d in opportunity_days
        )
        opp_revenue = max(opp_rooms, 0) * adr  # revenue if those days hit 70% occ

        # --- Pricing Power Score (correlation: high occ days vs ADR) ---
        high_occ_adrs = [self._day_adr(d) for d in self.days if self._day_occupancy(d) > 85]
        low_occ_adrs = [self._day_adr(d) for d in self.days if self._day_occupancy(d) < 60 and self._day_adr(d) > 0]
        pricing_power = 0
        if high_occ_adrs and low_occ_adrs:
            avg_high = stats_mean(high_occ_adrs)
            avg_low = stats_mean(low_occ_adrs)
            if avg_low > 0:
                pricing_power = round((avg_high - avg_low) / avg_low * 100, 1)

        # --- Tax Efficiency (actual effective tax rate vs expected) ---
        total_tps = sum(d.get('tps', 0) for d in self.days)
        total_tvq = sum(d.get('tvq', 0) for d in self.days)
        total_tvh = sum(d.get('tvh', 0) for d in self.days)
        taxable_rev = total_revenue - tips  # tips aren't taxable
        effective_tps_rate = total_tps / taxable_rev * 100 if taxable_rev > 0 else 0
        effective_tvq_rate = total_tvq / taxable_rev * 100 if taxable_rev > 0 else 0
        effective_tvh_rate = total_tvh / total_room_rev * 100 if total_room_rev > 0 else 0

        return {
            # Pricing & Revenue
            'effective_adr': round(effective_adr, 2),
            'pricing_power_pct': pricing_power,
            'revpar_volatility': round(revpar_volatility, 2),
            'adr_volatility': round(adr_volatility, 2),
            'occ_volatility': round(occ_volatility, 2),

            # Guest Metrics
            'double_occ_factor': round(double_occ_factor, 2),
            'fb_per_guest': round(fb_per_guest, 2),
            'ancillary_per_guest': round(ancillary_per_guest, 2),
            'rev_per_guest': round(rev_per_guest, 2),

            # F&B Performance
            'fb_revpar': round(fb_revpar, 2),
            'ancillary_revpar': round(ancillary_revpar, 2),
            'tip_ratio_pct': round(tip_ratio, 2),

            # Comp & OOS Impact
            'comp_rate_pct': round(comp_rate_pct, 1),
            'comp_revenue_loss': round(comp_revenue_loss, 2),
            'oos_rooms_avg': round(total_oos / n, 1),
            'oos_cost_impact': round(oos_cost, 2),

            # Processing Costs
            'card_processing_cost': round(processing_cost.get('total_cost', 0), 2),
            'card_processing_detail': processing_cost,

            # Opportunities
            'opportunity_days_count': len(opportunity_days),
            'opportunity_rooms': int(max(opp_rooms, 0)),
            'opportunity_revenue': round(opp_revenue, 2),

            # Tax Efficiency
            'effective_tps_rate': round(effective_tps_rate, 3),
            'effective_tvq_rate': round(effective_tvq_rate, 3),
            'effective_tvh_rate': round(effective_tvh_rate, 3),

            # Annualized projections (extrapolate from current data)
            'annual_oos_cost': round(oos_cost / n * 365, 0) if n else 0,
            'annual_comp_loss': round(comp_revenue_loss / n * 365, 0) if n else 0,
            'annual_processing_cost': round(processing_cost.get('total_cost', 0) / n * 365, 0) if n else 0,
            'annual_opp_revenue': round(opp_revenue / n * 365, 0) if n else 0,
        }

    def get_dow_analysis(self):
        """
        Day-of-week performance analysis.
        Requires a date reference; for single-month RJ we infer from day number.
        Returns performance by DOW (0=lundi to 6=dimanche).
        """
        DOW_NAMES = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

        dow_data = defaultdict(lambda: {
            'count': 0, 'room_rev': 0, 'fb_rev': 0, 'total_rev': 0,
            'rooms_sold': 0, 'clients': 0, 'occ_sum': 0, 'adr_sum': 0,
        })

        for d in self.days:
            # Try to infer DOW from date if available, else skip
            day_date = d.get('_date')
            if not day_date:
                # For single-month RJ without dates, we can't do DOW
                continue
            dow = day_date.weekday()  # 0=Monday
            fb = self._day_fb_total(d)
            other = self._day_other_revenue(d)
            sold = d.get('rooms_simple', 0) + d.get('rooms_double', 0) + d.get('rooms_suite', 0)

            dow_data[dow]['count'] += 1
            dow_data[dow]['room_rev'] += d.get('chambres', 0)
            dow_data[dow]['fb_rev'] += fb
            dow_data[dow]['total_rev'] += d.get('chambres', 0) + fb + other
            dow_data[dow]['rooms_sold'] += sold
            dow_data[dow]['clients'] += d.get('nb_clients', 0)
            dow_data[dow]['occ_sum'] += self._day_occupancy(d)
            dow_data[dow]['adr_sum'] += self._day_adr(d)

        result = []
        for dow in range(7):
            info = dow_data[dow]
            n = info['count']
            if n == 0:
                result.append({
                    'dow': dow, 'name': DOW_NAMES[dow], 'count': 0,
                    'avg_room_rev': 0, 'avg_fb_rev': 0, 'avg_total_rev': 0,
                    'avg_occ': 0, 'avg_adr': 0, 'avg_rooms_sold': 0, 'avg_clients': 0,
                })
                continue

            result.append({
                'dow': dow,
                'name': DOW_NAMES[dow],
                'count': n,
                'avg_room_rev': round(info['room_rev'] / n, 2),
                'avg_fb_rev': round(info['fb_rev'] / n, 2),
                'avg_total_rev': round(info['total_rev'] / n, 2),
                'avg_occ': round(info['occ_sum'] / n, 1),
                'avg_adr': round(info['adr_sum'] / n, 2),
                'avg_rooms_sold': round(info['rooms_sold'] / n, 0),
                'avg_clients': round(info['clients'] / n, 0),
            })

        # Weekend vs Weekday comparison
        weekday = [r for r in result if r['dow'] < 4 and r['count'] > 0]
        weekend = [r for r in result if r['dow'] >= 4 and r['count'] > 0]  # Fri-Sun for hotel industry

        wd_occ = stats_mean([r['avg_occ'] for r in weekday]) if weekday else 0
        we_occ = stats_mean([r['avg_occ'] for r in weekend]) if weekend else 0
        wd_adr = stats_mean([r['avg_adr'] for r in weekday]) if weekday else 0
        we_adr = stats_mean([r['avg_adr'] for r in weekend]) if weekend else 0
        wd_rev = stats_mean([r['avg_total_rev'] for r in weekday]) if weekday else 0
        we_rev = stats_mean([r['avg_total_rev'] for r in weekend]) if weekend else 0

        return {
            'by_dow': result,
            'weekend_vs_weekday': {
                'weekday_avg_occ': round(wd_occ, 1),
                'weekend_avg_occ': round(we_occ, 1),
                'weekday_avg_adr': round(wd_adr, 2),
                'weekend_avg_adr': round(we_adr, 2),
                'weekday_avg_rev': round(wd_rev, 2),
                'weekend_avg_rev': round(we_rev, 2),
                'occ_gap': round(we_occ - wd_occ, 1),
                'adr_gap': round(we_adr - wd_adr, 2),
            },
            'best_day': max(result, key=lambda r: r['avg_total_rev'])['name'] if result else '—',
            'worst_day': min([r for r in result if r['count'] > 0], key=lambda r: r['avg_total_rev'])['name'] if result else '—',
        }

    def get_revenue_opportunities(self):
        """
        Identify concrete revenue opportunities with $ amounts.
        This is the "money slide" for executive presentations.
        """
        if not self.days:
            return {'opportunities': [], 'total_annual_potential': 0}

        n = len(self.days)
        opportunities = []
        total_potential = 0
        adr = sum(self._day_adr(d) for d in self.days if self._day_adr(d) > 0) / max(len([d for d in self.days if self._day_adr(d) > 0]), 1)
        avg_occ = sum(self._day_occupancy(d) for d in self.days) / n

        # 1. OOS Room Recovery
        avg_oos = sum(d.get('hors_usage', 0) for d in self.days) / n
        if avg_oos > 2:
            recoverable = max(avg_oos - 2, 0)  # Target: max 2 OOS rooms
            daily_recovery = recoverable * adr * (avg_occ / 100)
            annual = daily_recovery * 365
            total_potential += annual
            opportunities.append({
                'id': 'oos_recovery',
                'title': 'Réduction chambres hors-service',
                'description': f'{avg_oos:.0f} chambres OOS/jour en moyenne. Réduire à 2 max → {recoverable:.0f} chambres récupérées/jour × ${adr:.0f} ADR × {avg_occ:.0f}% occ',
                'daily_impact': round(daily_recovery, 0),
                'annual_impact': round(annual, 0),
                'difficulty': 'moyen',
                'category': 'operations',
            })

        # 2. Comp Room Optimization
        rooms_comp = sum(d.get('rooms_comp', 0) for d in self.days)
        avg_comp = rooms_comp / n
        if avg_comp > 1:
            reducible = max(avg_comp - 1, 0)  # Target: max 1 comp/day
            daily_comp = reducible * adr
            annual = daily_comp * 365
            total_potential += annual
            opportunities.append({
                'id': 'comp_optimization',
                'title': 'Optimisation chambres gratuites',
                'description': f'{avg_comp:.1f} comps/jour. Réduire de {reducible:.1f} chambre(s) → économie de ${adr:.0f}/jour',
                'daily_impact': round(daily_comp, 0),
                'annual_impact': round(annual, 0),
                'difficulty': 'facile',
                'category': 'revenue',
            })

        # 3. F&B Per Guest Uplift
        total_fb = sum(self._day_fb_total(d) for d in self.days)
        total_clients = sum(d.get('nb_clients', 0) for d in self.days)
        fb_per_guest = total_fb / total_clients if total_clients > 0 else 0
        if fb_per_guest < 25 and total_clients > 0:  # Sheraton benchmark ~$25-35/guest
            target = 25
            uplift = target - fb_per_guest
            daily_fb_gain = uplift * (total_clients / n)
            annual = daily_fb_gain * 365
            total_potential += annual
            opportunities.append({
                'id': 'fb_uplift',
                'title': 'Augmentation dépense F&B par client',
                'description': f'${fb_per_guest:.2f}/client actuellement. Objectif ${target}/client → +${uplift:.2f}/client × {total_clients/n:.0f} clients/jour',
                'daily_impact': round(daily_fb_gain, 0),
                'annual_impact': round(annual, 0),
                'difficulty': 'moyen',
                'category': 'fb',
            })

        # 4. Dynamic Pricing on High-Demand Days
        high_occ_days = [d for d in self.days if self._day_occupancy(d) > 90]
        if high_occ_days:
            avg_high_adr = stats_mean([self._day_adr(d) for d in high_occ_days if self._day_adr(d) > 0]) if high_occ_days else 0
            if avg_high_adr > 0 and avg_high_adr < adr * 1.15:  # Not charging enough on high days
                suggested_increase = adr * 0.15  # 15% premium
                avg_high_rooms = stats_mean([d.get('rooms_simple', 0) + d.get('rooms_double', 0) + d.get('rooms_suite', 0) for d in high_occ_days])
                daily_gain = suggested_increase * avg_high_rooms
                annual = daily_gain * len(high_occ_days) / n * 365
                total_potential += annual
                opportunities.append({
                    'id': 'dynamic_pricing',
                    'title': 'Pricing dynamique jours forte demande',
                    'description': f'{len(high_occ_days)} jours à >90% occ. ADR moyen ces jours: ${avg_high_adr:.0f}. Avec +15% → +${suggested_increase:.0f}/chambre',
                    'daily_impact': round(daily_gain, 0),
                    'annual_impact': round(annual, 0),
                    'difficulty': 'facile',
                    'category': 'pricing',
                })

        # 5. Low Occupancy Day Strategy
        low_occ_days = [d for d in self.days if self._day_occupancy(d) < 60 and self._day_occupancy(d) > 0]
        if low_occ_days:
            avg_low_sold = stats_mean([d.get('rooms_simple', 0) + d.get('rooms_double', 0) + d.get('rooms_suite', 0) for d in low_occ_days])
            target_sold = TOTAL_ROOMS * 0.65  # Get to 65%
            gap = target_sold - avg_low_sold
            if gap > 0:
                discounted_rate = adr * 0.80  # 20% discount to fill
                daily_gain = gap * discounted_rate
                annual = daily_gain * len(low_occ_days) / n * 365
                total_potential += annual
                opportunities.append({
                    'id': 'low_occ_fill',
                    'title': 'Stratégie remplissage jours faibles',
                    'description': f'{len(low_occ_days)} jours à <60% occ. Gain moyen de {gap:.0f} chambres à ${discounted_rate:.0f} (tarif réduit -20%)',
                    'daily_impact': round(daily_gain, 0),
                    'annual_impact': round(annual, 0),
                    'difficulty': 'moyen',
                    'category': 'pricing',
                })

        # 6. Card Processing Cost Reduction
        proc = self._calc_processing_cost()
        if proc.get('total_cost', 0) > 0:
            annual_proc = proc['total_cost'] / n * 365
            # Assume 15% reduction possible via negotiation
            savings = annual_proc * 0.15
            if savings > 5000:
                total_potential += savings
                opportunities.append({
                    'id': 'processing_reduction',
                    'title': 'Renégociation frais de traitement cartes',
                    'description': f'Frais estimés: ${annual_proc:,.0f}/an. Réduction de 15% via renégociation processeurs (Elavon, Global)',
                    'daily_impact': round(savings / 365, 0),
                    'annual_impact': round(savings, 0),
                    'difficulty': 'facile',
                    'category': 'costs',
                })

        # Sort by annual impact
        opportunities.sort(key=lambda x: x['annual_impact'], reverse=True)

        return {
            'opportunities': opportunities,
            'total_annual_potential': round(total_potential, 0),
            'data_period_days': n,
        }

    def _calc_processing_cost(self):
        """Calculate estimated card processing costs using escrow %."""
        if not self.days:
            return {'total_cost': 0}

        # Use escrow percentages or fallback to industry rates
        avg_esc = {}
        for card, key in [('amex', 'esc_amex'), ('master', 'esc_master'), ('visa', 'esc_visa')]:
            vals = [d.get(key, 0) for d in self.days if d.get(key, 0) > 0]
            if vals:
                avg_esc[card] = stats_mean(vals)
            else:
                # Industry fallback rates (QC rates)
                avg_esc[card] = {'amex': 0.025, 'master': 0.017, 'visa': 0.017}[card]

        # Debit typically 0.5-0.8% or flat fee
        avg_esc['debit'] = 0.005

        total_visa = sum(abs(d.get('visa', 0)) for d in self.days)
        total_mc = sum(abs(d.get('mastercard', 0)) for d in self.days)
        total_amex = sum(abs(d.get('amex_elavon', 0)) + abs(d.get('amex_global', 0)) for d in self.days)
        total_debit = sum(abs(d.get('debit', 0)) for d in self.days)

        cost_visa = total_visa * avg_esc.get('visa', 0.017)
        cost_mc = total_mc * avg_esc.get('master', 0.017)
        cost_amex = total_amex * avg_esc.get('amex', 0.025)
        cost_debit = total_debit * avg_esc.get('debit', 0.005)

        total = cost_visa + cost_mc + cost_amex + cost_debit

        return {
            'total_cost': round(total, 2),
            'by_card': {
                'Visa': {'volume': round(total_visa, 2), 'rate_pct': round(avg_esc.get('visa', 0) * 100, 2), 'cost': round(cost_visa, 2)},
                'Mastercard': {'volume': round(total_mc, 2), 'rate_pct': round(avg_esc.get('master', 0) * 100, 2), 'cost': round(cost_mc, 2)},
                'Amex': {'volume': round(total_amex, 2), 'rate_pct': round(avg_esc.get('amex', 0) * 100, 2), 'cost': round(cost_amex, 2)},
                'Débit': {'volume': round(total_debit, 2), 'rate_pct': round(avg_esc.get('debit', 0) * 100, 2), 'cost': round(cost_debit, 2)},
            },
            'cheapest_method': 'Débit',
            'most_expensive_method': 'Amex',
        }

    def get_full_dashboard(self):
        """Return everything in a single call for the dashboard."""
        return {
            'has_data': self.has_data(),
            'kpis': self.get_executive_kpis(),
            'revenue_trend': self.get_revenue_trend(),
            'fb': self.get_fb_analytics(),
            'rooms': self.get_room_analytics(),
            'payments': self.get_payment_analytics(),
            'taxes': self.get_tax_analytics(),
            'anomalies': self.get_anomalies(),
            'advanced': self.get_advanced_kpis(),
            'dow': self.get_dow_analysis(),
            'opportunities': self.get_revenue_opportunities(),
        }

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _day_fb_total(self, d):
        """Total F&B revenue for a day."""
        total = 0
        for outlet_name, cols in FB_OUTLETS.items():
            for cat, col_idx in cols.items():
                key = [k for k, v in JOUR_COLS.items() if v == col_idx][0]
                total += d.get(key, 0)
        total += d.get('pourboires', 0)
        total += d.get('tabagie', 0)
        return total

    def _day_other_revenue(self, d):
        """Other revenue (non-room, non-F&B)."""
        keys = ['equipement', 'divers', 'location_salles', 'socan', 'resonne',
                'tel_interurb', 'tel_local', 'valet_buanderie', 'internet',
                'autre_rev', 'location_boutique', 'sonifi', 'massage']
        return sum(d.get(k, 0) for k in keys)

    def _day_cards_total(self, d):
        """Total credit/debit card payments for a day."""
        return abs(d.get('amex_elavon', 0)) + abs(d.get('discover', 0)) + \
               abs(d.get('mastercard', 0)) + abs(d.get('visa', 0)) + \
               abs(d.get('debit', 0)) + abs(d.get('amex_global', 0))

    def _day_occupancy(self, d):
        """Occupancy rate for a day."""
        sold = d.get('rooms_simple', 0) + d.get('rooms_double', 0) + d.get('rooms_suite', 0)
        avail = d.get('disponible', 0) or TOTAL_ROOMS
        return sold / avail * 100 if avail > 0 else 0

    def _day_adr(self, d):
        """Average Daily Rate for a day."""
        sold = d.get('rooms_simple', 0) + d.get('rooms_double', 0) + d.get('rooms_suite', 0)
        return d.get('chambres', 0) / sold if sold > 0 else 0

    def _day_revpar(self, d):
        """RevPAR for a day."""
        avail = d.get('disponible', 0) or TOTAL_ROOMS
        return d.get('chambres', 0) / avail if avail > 0 else 0

    def _empty_kpis(self):
        return {
            'days_count': 0, 'total_revenue': 0, 'avg_daily_revenue': 0,
            'room_revenue': 0, 'fb_revenue': 0, 'other_revenue': 0,
            'adr': 0, 'revpar': 0, 'trevpar': 0, 'occupancy_rate': 0,
            'rooms_sold': 0, 'rooms_available': 0, 'rooms_comp': 0,
            'total_clients': 0, 'avg_clients_per_day': 0,
            'total_cards': 0, 'total_taxes': 0,
            'total_tps': 0, 'total_tvq': 0, 'total_tvh': 0,
        }


# =============================================================================
# HISTORICAL ANALYTICS — Database-backed multi-year analytics
# =============================================================================

class HistoricalAnalytics:
    """
    Query DailyJourMetrics for multi-month/multi-year trend analysis.
    Returns same output format as JourAnalytics so the dashboard is compatible.
    """

    def __init__(self, start_date, end_date):
        from database.models import DailyJourMetrics
        self.start_date = start_date
        self.end_date = end_date
        self.metrics = DailyJourMetrics.query.filter(
            DailyJourMetrics.date >= start_date,
            DailyJourMetrics.date <= end_date
        ).order_by(DailyJourMetrics.date).all()

    def has_data(self):
        return len(self.metrics) > 0

    def get_executive_kpis(self):
        """Same output format as JourAnalytics.get_executive_kpis()."""
        if not self.metrics:
            return _empty_kpis_static()

        n = len(self.metrics)
        total_room_rev = sum(m.room_revenue for m in self.metrics)
        total_fb = sum(m.fb_revenue for m in self.metrics)
        total_other = sum(m.other_revenue for m in self.metrics)
        total_revenue = sum(m.total_revenue for m in self.metrics)
        rooms_sold = sum(m.total_rooms_sold for m in self.metrics)
        rooms_available = sum(m.rooms_available for m in self.metrics)
        rooms_comp = sum(m.rooms_comp for m in self.metrics)
        total_clients = sum(m.nb_clients for m in self.metrics)
        total_cards = sum(m.total_cards for m in self.metrics)
        total_tps = sum(m.tps_total for m in self.metrics)
        total_tvq = sum(m.tvq_total for m in self.metrics)
        total_tvh = sum(m.tvh_total for m in self.metrics)

        adr = total_room_rev / rooms_sold if rooms_sold > 0 else 0
        occ_rate = rooms_sold / rooms_available * 100 if rooms_available > 0 else 0
        revpar = total_room_rev / rooms_available if rooms_available > 0 else 0
        trevpar = total_revenue / rooms_available if rooms_available > 0 else 0

        return {
            'days_count': n,
            'total_revenue': round(total_revenue, 2),
            'avg_daily_revenue': round(total_revenue / n, 2) if n else 0,
            'room_revenue': round(total_room_rev, 2),
            'fb_revenue': round(total_fb, 2),
            'other_revenue': round(total_other, 2),
            'adr': round(adr, 2),
            'revpar': round(revpar, 2),
            'trevpar': round(trevpar, 2),
            'occupancy_rate': round(occ_rate, 1),
            'rooms_sold': int(rooms_sold),
            'rooms_available': int(rooms_available),
            'rooms_comp': int(rooms_comp),
            'total_clients': int(total_clients),
            'avg_clients_per_day': round(total_clients / n, 1) if n else 0,
            'total_cards': round(total_cards, 2),
            'total_taxes': round(total_tps + total_tvq + total_tvh, 2),
            'total_tps': round(total_tps, 2),
            'total_tvq': round(total_tvq, 2),
            'total_tvh': round(total_tvh, 2),
        }

    def get_revenue_trend(self):
        """Daily revenue trend — same format as JourAnalytics but with date."""
        result = []
        for m in self.metrics:
            total = m.room_revenue + m.fb_revenue + m.other_revenue
            result.append({
                'day': m.day_of_month,
                'date': m.date.isoformat(),
                'room_revenue': round(m.room_revenue, 2),
                'fb_revenue': round(m.fb_revenue, 2),
                'other_revenue': round(m.other_revenue, 2),
                'total': round(total, 2),
                'occupancy': round(m.occupancy_rate, 1),
                'adr': round(m.adr, 2),
                'revpar': round(m.revpar, 2),
            })
        return result

    def get_fb_analytics(self):
        """F&B analytics from DB."""
        # Calculate category totals
        total_nour = sum(m.total_nourriture for m in self.metrics)
        total_boi = sum(m.total_boisson for m in self.metrics)
        total_bie = sum(m.total_bieres for m in self.metrics)
        total_min = sum(m.total_mineraux for m in self.metrics)
        total_vin = sum(m.total_vins for m in self.metrics)

        # Calculate outlet totals
        outlet_sums = {
            'Café Link': sum(m.cafe_link_total for m in self.metrics),
            'Piazza/Cupola': sum(m.piazza_total for m in self.metrics),
            'Marché Spesa': sum(m.spesa_total for m in self.metrics),
            'Room Service': sum(m.room_svc_total for m in self.metrics),
            'Banquet': sum(m.banquet_total for m in self.metrics),
        }
        total_fb = sum(outlet_sums.values())

        # Distribute category totals proportionally to each outlet
        outlets = {}
        for name, outlet_total in outlet_sums.items():
            pct = (outlet_total / total_fb) if total_fb > 0 else 0
            outlets[name] = {
                'total': round(outlet_total, 2),
                'categories': {
                    'Nourriture': round(total_nour * pct, 2),
                    'Boisson': round(total_boi * pct, 2),
                    'Bières': round(total_bie * pct, 2),
                    'Vins': round(total_vin * pct, 2),
                    'Minéraux': round(total_min * pct, 2),
                }
            }

        cat_totals = {
            'Nourriture': round(total_nour, 2),
            'Boisson': round(total_boi, 2),
            'Bières': round(total_bie, 2),
            'Minéraux': round(total_min, 2),
            'Vins': round(total_vin, 2),
        }

        food_pct = round(total_nour / total_fb * 100, 1) if total_fb else 0

        tips = sum(m.tips_total for m in self.metrics)
        tabagie = sum(m.tabagie_total for m in self.metrics)

        return {
            'outlets': outlets,
            'category_totals': cat_totals,
            'total_fb': round(total_fb, 2),
            'food_pct': food_pct,
            'beverage_pct': round(100 - food_pct, 1),
            'trend': [],
            'other': {
                'pourboires': round(tips, 2),
                'tabagie': round(tabagie, 2),
            }
        }

    def get_room_analytics(self):
        """Room analytics from DB."""
        trend = []
        for m in self.metrics:
            sold = m.total_rooms_sold
            trend.append({
                'day': m.day_of_month,
                'date': m.date.isoformat(),
                'simple': m.rooms_simple,
                'double': m.rooms_double,
                'suite': m.rooms_suite,
                'comp': m.rooms_comp,
                'sold': sold,
                'available': m.rooms_available,
                'occupancy': round(m.occupancy_rate, 1),
                'clients': m.nb_clients,
                'hors_usage': m.rooms_hors_usage,
                'ch_refaire': m.rooms_ch_refaire,
                'adr': round(m.adr, 2),
                'room_revenue': round(m.room_revenue, 2),
            })

        total_sold = sum(m.total_rooms_sold for m in self.metrics)
        total_avail = sum(m.rooms_available for m in self.metrics)
        total_simple = sum(m.rooms_simple for m in self.metrics)
        total_double = sum(m.rooms_double for m in self.metrics)
        total_suite = sum(m.rooms_suite for m in self.metrics)
        total_comp = sum(m.rooms_comp for m in self.metrics)

        return {
            'trend': trend,
            'summary': {
                'avg_occupancy': round(total_sold / total_avail * 100, 1) if total_avail else 0,
                'total_rooms_sold': total_sold,
                'room_mix': {
                    'simple': total_simple, 'double': total_double,
                    'suite': total_suite, 'comp': total_comp,
                },
                'room_mix_pct': {
                    'simple': round(total_simple / total_sold * 100, 1) if total_sold else 0,
                    'double': round(total_double / total_sold * 100, 1) if total_sold else 0,
                    'suite': round(total_suite / total_sold * 100, 1) if total_sold else 0,
                    'comp': round(total_comp / total_sold * 100, 1) if total_sold else 0,
                },
                'avg_clients': round(sum(m.nb_clients for m in self.metrics) / len(self.metrics), 1) if self.metrics else 0,
                'avg_hors_usage': round(sum(m.rooms_hors_usage for m in self.metrics) / len(self.metrics), 1) if self.metrics else 0,
            }
        }

    def get_payment_analytics(self):
        """Payment breakdown from DB."""
        cards = {
            'Visa': sum(m.visa_total for m in self.metrics),
            'Mastercard': sum(m.mastercard_total for m in self.metrics),
            'Amex ELAVON': sum(m.amex_elavon_total for m in self.metrics),
            'Amex GLOBAL': sum(m.amex_global_total for m in self.metrics),
            'Débit': sum(m.debit_total for m in self.metrics),
            'Discover': sum(m.discover_total for m in self.metrics),
        }
        total = sum(abs(v) for v in cards.values())
        breakdown = {k: {
            'amount': round(v, 2),
            'pct': round(abs(v) / total * 100, 1) if total else 0,
        } for k, v in cards.items()}

        return {
            'breakdown': breakdown,
            'total': round(total, 2),
            'trend': [],
            'avg_escrow_pct': {},
        }

    def get_tax_analytics(self):
        """Tax analytics from DB."""
        totals = {
            'tps': round(sum(m.tps_total for m in self.metrics), 2),
            'tvq': round(sum(m.tvq_total for m in self.metrics), 2),
            'tvh': round(sum(m.tvh_total for m in self.metrics), 2),
        }
        totals['total'] = round(sum(totals.values()), 2)
        n = len(self.metrics) or 1

        return {
            'totals': totals,
            'trend': [],
            'avg_daily': {k: round(v / n, 2) for k, v in totals.items()},
        }

    def get_anomalies(self):
        """Anomaly detection from DB data."""
        if len(self.metrics) < 3:
            return {'alerts': [], 'insights': []}

        alerts = []
        insights = []

        avg_occ = sum(m.occupancy_rate for m in self.metrics) / len(self.metrics)
        avg_adr = sum(m.adr for m in self.metrics) / len(self.metrics)
        avg_fb = sum(m.fb_revenue for m in self.metrics) / len(self.metrics)

        for m in self.metrics:
            if m.occupancy_rate < avg_occ * 0.7 and m.occupancy_rate > 0:
                alerts.append({
                    'day': m.day_of_month, 'date': m.date.isoformat(),
                    'type': 'low_occupancy', 'severity': 'warning',
                    'message': f'{m.date.strftime("%d %b %Y")}: Occ {m.occupancy_rate:.0f}% vs moy {avg_occ:.0f}%',
                })
            if abs(m.cash_difference) > 50:
                alerts.append({
                    'day': m.day_of_month, 'date': m.date.isoformat(),
                    'type': 'cash_variance', 'severity': 'danger',
                    'message': f'{m.date.strftime("%d %b %Y")}: Diff caisse ${m.cash_difference:.2f}',
                })

        # Revenue mix insight
        total_rev = sum(m.room_revenue for m in self.metrics)
        total_fb = sum(m.fb_revenue for m in self.metrics)
        if total_rev > 0:
            fb_ratio = total_fb / total_rev * 100
            if fb_ratio < 15:
                insights.append({
                    'type': 'low_fb_ratio',
                    'message': f'Ratio F&B/Chambres à {fb_ratio:.1f}% — potentiel d\'amélioration',
                })

        return {
            'alerts': sorted(alerts, key=lambda x: {'danger': 0, 'warning': 1, 'info': 2}.get(x.get('severity', 'info'), 3))[:50],
            'insights': insights,
        }

    # ── Advanced Analytics (Historical) ────────────────────────────────

    def get_advanced_kpis(self):
        """Advanced KPIs computed from historical DB data."""
        if not self.metrics:
            return {}

        n = len(self.metrics)
        total_room_rev = sum(m.room_revenue for m in self.metrics)
        total_fb = sum(m.fb_revenue for m in self.metrics)
        total_other = sum(m.other_revenue for m in self.metrics)
        total_revenue = sum(m.total_revenue for m in self.metrics)
        rooms_sold = sum(m.total_rooms_sold for m in self.metrics)
        rooms_comp = sum(m.rooms_comp for m in self.metrics)
        rooms_available = sum(m.rooms_available for m in self.metrics)
        total_clients = sum(m.nb_clients for m in self.metrics)
        total_oos = sum(m.rooms_hors_usage for m in self.metrics)
        tips = sum(m.tips_total for m in self.metrics)

        adr = total_room_rev / rooms_sold if rooms_sold > 0 else 0
        total_rooms_incl_comp = rooms_sold + rooms_comp
        effective_adr = total_room_rev / total_rooms_incl_comp if total_rooms_incl_comp > 0 else 0
        comp_rate_pct = rooms_comp / total_rooms_incl_comp * 100 if total_rooms_incl_comp > 0 else 0
        comp_revenue_loss = rooms_comp * adr
        double_occ = total_clients / rooms_sold if rooms_sold > 0 else 0
        fb_revpar = total_fb / rooms_available if rooms_available > 0 else 0
        fb_per_guest = total_fb / total_clients if total_clients > 0 else 0
        anc_revpar = total_other / rooms_available if rooms_available > 0 else 0
        anc_per_guest = total_other / total_clients if total_clients > 0 else 0
        rev_per_guest = total_revenue / total_clients if total_clients > 0 else 0
        oos_cost = total_oos * adr
        tip_ratio = tips / total_fb * 100 if total_fb > 0 else 0
        avg_occ = sum(m.occupancy_rate for m in self.metrics) / n

        # Volatility
        daily_revpar = [m.revpar for m in self.metrics]
        daily_adr = [m.adr for m in self.metrics if m.adr > 0]
        daily_occ = [m.occupancy_rate for m in self.metrics]
        revpar_vol = stdev(daily_revpar) if len(daily_revpar) >= 2 else 0
        adr_vol = stdev(daily_adr) if len(daily_adr) >= 2 else 0
        occ_vol = stdev(daily_occ) if len(daily_occ) >= 2 else 0

        # Opportunity days
        opp_days = [m for m in self.metrics if m.occupancy_rate < 70 and m.occupancy_rate > 0]
        opp_rooms = sum(max(m.rooms_available * 0.70 - m.total_rooms_sold, 0) for m in opp_days)
        opp_revenue = opp_rooms * adr

        # Pricing power
        high_adrs = [m.adr for m in self.metrics if m.occupancy_rate > 85 and m.adr > 0]
        low_adrs = [m.adr for m in self.metrics if m.occupancy_rate < 60 and m.adr > 0]
        pricing_power = 0
        if high_adrs and low_adrs:
            avg_h = stats_mean(high_adrs)
            avg_l = stats_mean(low_adrs)
            if avg_l > 0:
                pricing_power = round((avg_h - avg_l) / avg_l * 100, 1)

        # Tax efficiency
        total_tps = sum(m.tps_total for m in self.metrics)
        total_tvq = sum(m.tvq_total for m in self.metrics)
        total_tvh = sum(m.tvh_total for m in self.metrics)
        taxable = total_revenue - tips
        eff_tps = total_tps / taxable * 100 if taxable > 0 else 0
        eff_tvq = total_tvq / taxable * 100 if taxable > 0 else 0
        eff_tvh = total_tvh / total_room_rev * 100 if total_room_rev > 0 else 0

        # Card processing
        total_visa = sum(m.visa_total for m in self.metrics)
        total_mc = sum(m.mastercard_total for m in self.metrics)
        total_amex = sum(m.amex_elavon_total + m.amex_global_total for m in self.metrics)
        total_debit = sum(m.debit_total for m in self.metrics)
        proc_cost = abs(total_visa)*0.017 + abs(total_mc)*0.017 + abs(total_amex)*0.025 + abs(total_debit)*0.005

        return {
            'effective_adr': round(effective_adr, 2),
            'pricing_power_pct': pricing_power,
            'revpar_volatility': round(revpar_vol, 2),
            'adr_volatility': round(adr_vol, 2),
            'occ_volatility': round(occ_vol, 2),
            'double_occ_factor': round(double_occ, 2),
            'fb_per_guest': round(fb_per_guest, 2),
            'ancillary_per_guest': round(anc_per_guest, 2),
            'rev_per_guest': round(rev_per_guest, 2),
            'fb_revpar': round(fb_revpar, 2),
            'ancillary_revpar': round(anc_revpar, 2),
            'tip_ratio_pct': round(tip_ratio, 2),
            'comp_rate_pct': round(comp_rate_pct, 1),
            'comp_revenue_loss': round(comp_revenue_loss, 2),
            'oos_rooms_avg': round(total_oos / n, 1),
            'oos_cost_impact': round(oos_cost, 2),
            'card_processing_cost': round(proc_cost, 2),
            'card_processing_detail': {
                'total_cost': round(proc_cost, 2),
                'by_card': {
                    'Visa': {'volume': round(abs(total_visa), 2), 'rate_pct': 1.7, 'cost': round(abs(total_visa)*0.017, 2)},
                    'Mastercard': {'volume': round(abs(total_mc), 2), 'rate_pct': 1.7, 'cost': round(abs(total_mc)*0.017, 2)},
                    'Amex': {'volume': round(abs(total_amex), 2), 'rate_pct': 2.5, 'cost': round(abs(total_amex)*0.025, 2)},
                    'Débit': {'volume': round(abs(total_debit), 2), 'rate_pct': 0.5, 'cost': round(abs(total_debit)*0.005, 2)},
                },
            },
            'opportunity_days_count': len(opp_days),
            'opportunity_rooms': int(max(opp_rooms, 0)),
            'opportunity_revenue': round(opp_revenue, 2),
            'effective_tps_rate': round(eff_tps, 3),
            'effective_tvq_rate': round(eff_tvq, 3),
            'effective_tvh_rate': round(eff_tvh, 3),
            'annual_oos_cost': round(oos_cost / n * 365, 0) if n else 0,
            'annual_comp_loss': round(comp_revenue_loss / n * 365, 0) if n else 0,
            'annual_processing_cost': round(proc_cost / n * 365, 0) if n else 0,
            'annual_opp_revenue': round(opp_revenue / n * 365, 0) if n else 0,
        }

    def get_dow_analysis(self):
        """Day-of-week analysis from historical DB data."""
        DOW_NAMES = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        dow_data = defaultdict(lambda: {
            'count': 0, 'room_rev': 0, 'fb_rev': 0, 'total_rev': 0,
            'rooms_sold': 0, 'clients': 0, 'occ_sum': 0, 'adr_sum': 0,
        })

        for m in self.metrics:
            dow = m.date.weekday()
            dow_data[dow]['count'] += 1
            dow_data[dow]['room_rev'] += m.room_revenue
            dow_data[dow]['fb_rev'] += m.fb_revenue
            dow_data[dow]['total_rev'] += m.total_revenue
            dow_data[dow]['rooms_sold'] += m.total_rooms_sold
            dow_data[dow]['clients'] += m.nb_clients
            dow_data[dow]['occ_sum'] += m.occupancy_rate
            dow_data[dow]['adr_sum'] += m.adr

        result = []
        for dow in range(7):
            info = dow_data[dow]
            nc = info['count']
            if nc == 0:
                result.append({'dow': dow, 'name': DOW_NAMES[dow], 'count': 0,
                    'avg_room_rev': 0, 'avg_fb_rev': 0, 'avg_total_rev': 0,
                    'avg_occ': 0, 'avg_adr': 0, 'avg_rooms_sold': 0, 'avg_clients': 0})
                continue
            result.append({
                'dow': dow, 'name': DOW_NAMES[dow], 'count': nc,
                'avg_room_rev': round(info['room_rev'] / nc, 2),
                'avg_fb_rev': round(info['fb_rev'] / nc, 2),
                'avg_total_rev': round(info['total_rev'] / nc, 2),
                'avg_occ': round(info['occ_sum'] / nc, 1),
                'avg_adr': round(info['adr_sum'] / nc, 2),
                'avg_rooms_sold': round(info['rooms_sold'] / nc, 0),
                'avg_clients': round(info['clients'] / nc, 0),
            })

        weekday = [r for r in result if r['dow'] < 4 and r['count'] > 0]
        weekend = [r for r in result if r['dow'] >= 4 and r['count'] > 0]  # Fri-Sun for hotel industry
        wd_occ = stats_mean([r['avg_occ'] for r in weekday]) if weekday else 0
        we_occ = stats_mean([r['avg_occ'] for r in weekend]) if weekend else 0
        wd_adr = stats_mean([r['avg_adr'] for r in weekday]) if weekday else 0
        we_adr = stats_mean([r['avg_adr'] for r in weekend]) if weekend else 0
        wd_rev = stats_mean([r['avg_total_rev'] for r in weekday]) if weekday else 0
        we_rev = stats_mean([r['avg_total_rev'] for r in weekend]) if weekend else 0

        return {
            'by_dow': result,
            'weekend_vs_weekday': {
                'weekday_avg_occ': round(wd_occ, 1), 'weekend_avg_occ': round(we_occ, 1),
                'weekday_avg_adr': round(wd_adr, 2), 'weekend_avg_adr': round(we_adr, 2),
                'weekday_avg_rev': round(wd_rev, 2), 'weekend_avg_rev': round(we_rev, 2),
                'occ_gap': round(we_occ - wd_occ, 1), 'adr_gap': round(we_adr - wd_adr, 2),
            },
            'best_day': max(result, key=lambda r: r['avg_total_rev'])['name'] if result else '—',
            'worst_day': min([r for r in result if r['count'] > 0], key=lambda r: r['avg_total_rev'])['name'] if result else '—',
        }

    def get_revenue_opportunities(self):
        """Revenue opportunities from historical data."""
        if not self.metrics:
            return {'opportunities': [], 'total_annual_potential': 0}

        n = len(self.metrics)
        opportunities = []
        total_potential = 0
        adrs = [m.adr for m in self.metrics if m.adr > 0]
        adr = stats_mean(adrs) if adrs else 0
        avg_occ = sum(m.occupancy_rate for m in self.metrics) / n

        # 1. OOS
        avg_oos = sum(m.rooms_hors_usage for m in self.metrics) / n
        if avg_oos > 2:
            recoverable = max(avg_oos - 2, 0)
            daily = recoverable * adr * (avg_occ / 100)
            annual = daily * 365
            total_potential += annual
            opportunities.append({
                'id': 'oos_recovery', 'title': 'Réduction chambres hors-service',
                'description': f'{avg_oos:.0f} OOS/jour moy. → réduire à 2 max = {recoverable:.0f} chambres × ${adr:.0f} ADR',
                'daily_impact': round(daily, 0), 'annual_impact': round(annual, 0),
                'difficulty': 'moyen', 'category': 'operations',
            })

        # 2. Comps
        avg_comp = sum(m.rooms_comp for m in self.metrics) / n
        if avg_comp > 1:
            reducible = max(avg_comp - 1, 0)
            daily = reducible * adr
            annual = daily * 365
            total_potential += annual
            opportunities.append({
                'id': 'comp_optimization', 'title': 'Optimisation chambres gratuites',
                'description': f'{avg_comp:.1f} comps/jour → réduire de {reducible:.1f} = ${adr:.0f}/jour',
                'daily_impact': round(daily, 0), 'annual_impact': round(annual, 0),
                'difficulty': 'facile', 'category': 'revenue',
            })

        # 3. F&B uplift
        total_fb = sum(m.fb_revenue for m in self.metrics)
        total_clients = sum(m.nb_clients for m in self.metrics)
        fb_pg = total_fb / total_clients if total_clients > 0 else 0
        if fb_pg < 25 and total_clients > 0:
            uplift = 25 - fb_pg
            daily = uplift * (total_clients / n)
            annual = daily * 365
            total_potential += annual
            opportunities.append({
                'id': 'fb_uplift', 'title': 'Augmentation F&B par client',
                'description': f'${fb_pg:.2f}/client actuel → objectif $25 = +${uplift:.2f} × {total_clients/n:.0f} clients/jour',
                'daily_impact': round(daily, 0), 'annual_impact': round(annual, 0),
                'difficulty': 'moyen', 'category': 'fb',
            })

        # 4. Dynamic pricing
        high_days = [m for m in self.metrics if m.occupancy_rate > 90]
        if high_days:
            avg_h_adr = stats_mean([m.adr for m in high_days if m.adr > 0]) if high_days else 0
            if avg_h_adr > 0 and avg_h_adr < adr * 1.15:
                increase = adr * 0.15
                avg_h_rooms = stats_mean([m.total_rooms_sold for m in high_days])
                daily = increase * avg_h_rooms
                annual = daily * len(high_days) / n * 365
                total_potential += annual
                opportunities.append({
                    'id': 'dynamic_pricing', 'title': 'Pricing dynamique haute demande',
                    'description': f'{len(high_days)} jours >90% occ. +15% ADR = +${increase:.0f}/chambre × {avg_h_rooms:.0f} ch.',
                    'daily_impact': round(daily, 0), 'annual_impact': round(annual, 0),
                    'difficulty': 'facile', 'category': 'pricing',
                })

        # 5. Low occ fill
        low_days = [m for m in self.metrics if m.occupancy_rate < 60 and m.occupancy_rate > 0]
        if low_days:
            avg_low_sold = stats_mean([m.total_rooms_sold for m in low_days])
            gap = TOTAL_ROOMS * 0.65 - avg_low_sold
            if gap > 0:
                rate = adr * 0.80
                daily = gap * rate
                annual = daily * len(low_days) / n * 365
                total_potential += annual
                opportunities.append({
                    'id': 'low_occ_fill', 'title': 'Remplissage jours faibles',
                    'description': f'{len(low_days)} jours <60% occ. +{gap:.0f} chambres à ${rate:.0f} (tarif -20%)',
                    'daily_impact': round(daily, 0), 'annual_impact': round(annual, 0),
                    'difficulty': 'moyen', 'category': 'pricing',
                })

        # 6. Card processing
        total_cards = sum(abs(m.visa_total) + abs(m.mastercard_total) + abs(m.amex_elavon_total) + abs(m.amex_global_total) + abs(m.debit_total) for m in self.metrics)
        annual_proc = total_cards * 0.019 / n * 365  # Blended ~1.9% rate
        savings = annual_proc * 0.15
        if savings > 5000:
            total_potential += savings
            opportunities.append({
                'id': 'processing_reduction', 'title': 'Renégociation frais cartes',
                'description': f'Frais estimés: ${annual_proc:,.0f}/an. Économie de 15% = ${savings:,.0f}',
                'daily_impact': round(savings / 365, 0), 'annual_impact': round(savings, 0),
                'difficulty': 'facile', 'category': 'costs',
            })

        opportunities.sort(key=lambda x: x['annual_impact'], reverse=True)
        return {
            'opportunities': opportunities,
            'total_annual_potential': round(total_potential, 0),
            'data_period_days': n,
        }

    def get_full_dashboard(self):
        """Return all analytics in a single call."""
        return {
            'has_data': self.has_data(),
            'kpis': self.get_executive_kpis(),
            'revenue_trend': self.get_revenue_trend(),
            'fb': self.get_fb_analytics(),
            'rooms': self.get_room_analytics(),
            'payments': self.get_payment_analytics(),
            'taxes': self.get_tax_analytics(),
            'anomalies': self.get_anomalies(),
            'advanced': self.get_advanced_kpis(),
            'dow': self.get_dow_analysis(),
            'opportunities': self.get_revenue_opportunities(),
        }

    # ── Historical-specific methods ──────────────────────────────────────

    def get_yoy_comparison(self):
        """Year-over-year KPI comparison for the same period one year ago."""
        from datetime import timedelta
        delta = timedelta(days=365)
        prior_start = self.start_date - delta
        prior_end = self.end_date - delta

        prior = HistoricalAnalytics(prior_start, prior_end)
        current_kpis = self.get_executive_kpis()
        prior_kpis = prior.get_executive_kpis()

        def pct_change(current, previous):
            if previous and previous != 0:
                return round((current - previous) / abs(previous) * 100, 1)
            return None

        return {
            'current': current_kpis,
            'prior': prior_kpis,
            'deltas': {
                'adr': pct_change(current_kpis['adr'], prior_kpis['adr']),
                'revpar': pct_change(current_kpis['revpar'], prior_kpis['revpar']),
                'occupancy_rate': pct_change(current_kpis['occupancy_rate'], prior_kpis['occupancy_rate']),
                'room_revenue': pct_change(current_kpis['room_revenue'], prior_kpis['room_revenue']),
                'fb_revenue': pct_change(current_kpis['fb_revenue'], prior_kpis['fb_revenue']),
                'total_revenue': pct_change(current_kpis['total_revenue'], prior_kpis['total_revenue']),
                'avg_clients_per_day': pct_change(current_kpis['avg_clients_per_day'], prior_kpis['avg_clients_per_day']),
            }
        }

    def get_monthly_summary(self):
        """Monthly aggregates for multi-year trending."""
        from database.models import DailyJourMetrics, db
        from sqlalchemy import func

        rows = db.session.query(
            DailyJourMetrics.year,
            DailyJourMetrics.month,
            func.count(DailyJourMetrics.id).label('days'),
            func.avg(DailyJourMetrics.adr).label('avg_adr'),
            func.avg(DailyJourMetrics.revpar).label('avg_revpar'),
            func.avg(DailyJourMetrics.occupancy_rate).label('avg_occ'),
            func.sum(DailyJourMetrics.total_revenue).label('total_rev'),
            func.sum(DailyJourMetrics.room_revenue).label('room_rev'),
            func.sum(DailyJourMetrics.fb_revenue).label('fb_rev'),
            func.avg(DailyJourMetrics.nb_clients).label('avg_clients'),
        ).filter(
            DailyJourMetrics.date >= self.start_date,
            DailyJourMetrics.date <= self.end_date
        ).group_by(
            DailyJourMetrics.year,
            DailyJourMetrics.month
        ).order_by(
            DailyJourMetrics.year,
            DailyJourMetrics.month
        ).all()

        return [{
            'year': r.year,
            'month': r.month,
            'days': r.days,
            'avg_adr': round(r.avg_adr or 0, 2),
            'avg_revpar': round(r.avg_revpar or 0, 2),
            'avg_occupancy': round(r.avg_occ or 0, 1),
            'total_revenue': round(r.total_rev or 0, 2),
            'room_revenue': round(r.room_rev or 0, 2),
            'fb_revenue': round(r.fb_rev or 0, 2),
            'avg_clients': round(r.avg_clients or 0, 1),
        } for r in rows]


def _empty_kpis_static():
    """Empty KPIs dict (for use outside JourAnalytics)."""
    return {
        'days_count': 0, 'total_revenue': 0, 'avg_daily_revenue': 0,
        'room_revenue': 0, 'fb_revenue': 0, 'other_revenue': 0,
        'adr': 0, 'revpar': 0, 'trevpar': 0, 'occupancy_rate': 0,
        'rooms_sold': 0, 'rooms_available': 0, 'rooms_comp': 0,
        'total_clients': 0, 'avg_clients_per_day': 0,
        'total_cards': 0, 'total_taxes': 0,
        'total_tps': 0, 'total_tvq': 0, 'total_tvh': 0,
    }


# =============================================================================
# DAY-OF-WEEK BASELINES — computes historical averages per weekday
# =============================================================================

def get_dow_baselines(lookback_weeks=12):
    """
    Compute day-of-week baselines from the last `lookback_weeks` weeks of data.

    Returns a dict keyed by weekday (0=Monday..6=Sunday), each containing:
      - occupancy_rate: avg occupancy for that DoW
      - adr: avg ADR
      - revpar: avg RevPAR
      - room_revenue: avg room revenue
      - fb_revenue: avg F&B revenue
      - fb_per_client: avg F&B per client
      - total_revenue: avg total revenue
      - nb_clients: avg guest count
      - sample_count: number of data points used
    """
    from database.models import DailyJourMetrics, db
    from sqlalchemy import func, extract
    from datetime import date as date_cls, timedelta

    cutoff = date_cls.today() - timedelta(weeks=lookback_weeks)

    rows = db.session.query(
        extract('dow', DailyJourMetrics.date).label('dow'),
        func.avg(DailyJourMetrics.occupancy_rate).label('avg_occ'),
        func.avg(DailyJourMetrics.adr).label('avg_adr'),
        func.avg(DailyJourMetrics.revpar).label('avg_revpar'),
        func.avg(DailyJourMetrics.room_revenue).label('avg_room_rev'),
        func.avg(DailyJourMetrics.fb_revenue).label('avg_fb_rev'),
        func.avg(DailyJourMetrics.total_revenue).label('avg_total_rev'),
        func.avg(DailyJourMetrics.nb_clients).label('avg_clients'),
        func.count(DailyJourMetrics.id).label('cnt'),
    ).filter(
        DailyJourMetrics.date >= cutoff,
        DailyJourMetrics.occupancy_rate > 0,
    ).group_by('dow').all()

    baselines = {}
    for r in rows:
        dow = int(r.dow)
        avg_clients = r.avg_clients or 0
        avg_fb = r.avg_fb_rev or 0
        baselines[dow] = {
            'occupancy_rate': round(r.avg_occ or 0, 1),
            'adr': round(r.avg_adr or 0, 2),
            'revpar': round(r.avg_revpar or 0, 2),
            'room_revenue': round(r.avg_room_rev or 0, 2),
            'fb_revenue': round(avg_fb, 2),
            'fb_per_client': round(avg_fb / avg_clients, 2) if avg_clients > 0 else 0,
            'total_revenue': round(r.avg_total_rev or 0, 2),
            'nb_clients': round(avg_clients, 1),
            'sample_count': r.cnt,
        }

    # SQLite: strftime('%w', date) -> 0=Sun, 1=Mon, ... 6=Sat
    # Python: date.weekday() -> 0=Mon, 1=Tue, ... 6=Sun
    # Remap: DB_dow -> python_dow = (DB_dow - 1) % 7
    remapped = {}
    for db_dow, data in baselines.items():
        py_dow = (db_dow - 1) % 7
        remapped[py_dow] = data
    return remapped

# =============================================================================
# ACTIONABLE INTELLIGENCE — Data-driven recommendations
# =============================================================================

def get_dow_baselines(lookback_days=90):
    """
    Calculate day-of-week baselines from actual hotel data.
    Returns dict keyed by weekday (0=Mon, 6=Sun) with avg metrics.
    Used to replace hardcoded thresholds with data-driven ones.
    """
    from database.models import DailyJourMetrics
    from datetime import date, timedelta
    from sqlalchemy import func

    end = DailyJourMetrics.query.order_by(DailyJourMetrics.date.desc()).first()
    if not end:
        return {}

    start = end.date - timedelta(days=lookback_days)
    metrics = DailyJourMetrics.query.filter(
        DailyJourMetrics.date.between(start, end.date)
    ).all()

    if not metrics:
        return {}

    from collections import defaultdict
    by_dow = defaultdict(list)
    DOW_NAMES = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

    for m in metrics:
        dow = m.date.weekday()  # 0=Mon, 6=Sun
        by_dow[dow].append(m)

    baselines = {}
    for dow in range(7):
        days = by_dow.get(dow, [])
        if not days:
            continue
        n = len(days)
        avg_occ = sum(d.occupancy_rate or 0 for d in days) / n
        avg_adr = sum(d.adr or 0 for d in days) / n
        avg_revpar = sum(d.revpar or 0 for d in days) / n
        avg_revenue = sum(d.total_revenue or 0 for d in days) / n
        avg_fb = sum(d.fb_revenue or 0 for d in days) / n
        avg_rooms = sum(d.total_rooms_sold or 0 for d in days) / n
        avg_clients = sum(d.nb_clients or 0 for d in days) / n
        fb_per_client = avg_fb / avg_clients if avg_clients > 0 else 0

        baselines[dow] = {
            'day_name': DOW_NAMES[dow],
            'days_sampled': n,
            'avg_occupancy': round(avg_occ, 1),
            'avg_adr': round(avg_adr, 2),
            'avg_revpar': round(avg_revpar, 2),
            'avg_revenue': round(avg_revenue, 2),
            'avg_fb_revenue': round(avg_fb, 2),
            'avg_rooms_sold': round(avg_rooms, 0),
            'avg_clients': round(avg_clients, 0),
            'avg_fb_per_client': round(fb_per_client, 2),
        }

    return baselines


def get_staffing_guide():
    """
    Generate staffing recommendations by day-of-week based on actual occupancy patterns.
    Returns a list of 7 entries with recommended staffing levels relative to baseline.
    """
    from database.models import TOTAL_ROOMS

    baselines = get_dow_baselines()
    if not baselines:
        return {'has_data': False}

    # Calculate overall average occupancy as baseline reference
    all_occ = [b['avg_occupancy'] for b in baselines.values()]
    overall_avg_occ = sum(all_occ) / len(all_occ) if all_occ else 70

    guide = []
    for dow in range(7):
        b = baselines.get(dow)
        if not b:
            continue

        occ = b['avg_occupancy']
        ratio = occ / overall_avg_occ if overall_avg_occ > 0 else 1.0

        # Staffing level determination
        if occ < 45:
            level = 'Minimum'
            level_fr = 'Minimum'
            adjust_pct = round((1 - ratio) * -100)
            color = 'red'
        elif occ < 65:
            level = 'Reduced'
            level_fr = 'Réduit'
            adjust_pct = round((1 - ratio) * -100)
            color = 'orange'
        elif occ < 80:
            level = 'Normal'
            level_fr = 'Normal'
            adjust_pct = 0
            color = 'blue'
        elif occ < 90:
            level = 'Normal+'
            level_fr = 'Normal+'
            adjust_pct = round((ratio - 1) * 100)
            color = 'green'
        else:
            level = 'Full + Events'
            level_fr = 'Complet + Événements'
            adjust_pct = round((ratio - 1) * 100)
            color = 'green'

        # Estimate housekeeping needs (roughly 1 housekeeper per 14 rooms)
        est_rooms = round(TOTAL_ROOMS * occ / 100)
        est_housekeepers = max(2, round(est_rooms / 14))
        # Front desk: 1 agent per ~80 rooms occupied, min 1
        est_front_desk = max(1, round(est_rooms / 80))

        guide.append({
            'dow': dow,
            'day_name': b['day_name'],
            'avg_occupancy': occ,
            'avg_rooms': est_rooms,
            'level': level,
            'level_fr': level_fr,
            'adjust_pct': adjust_pct,
            'color': color,
            'est_housekeepers': est_housekeepers,
            'est_front_desk': est_front_desk,
            'avg_revenue': b['avg_revenue'],
        })

    # Find best/worst days
    best = max(guide, key=lambda x: x['avg_occupancy'])
    worst = min(guide, key=lambda x: x['avg_occupancy'])

    return {
        'has_data': True,
        'guide': guide,
        'overall_avg_occupancy': round(overall_avg_occ, 1),
        'best_day': best['day_name'],
        'worst_day': worst['day_name'],
        'occ_swing': round(best['avg_occupancy'] - worst['avg_occupancy'], 1),
        'insight': f"Écart de {round(best['avg_occupancy'] - worst['avg_occupancy'], 0)}pts entre {best['day_name']} ({best['avg_occupancy']:.0f}%) et {worst['day_name']} ({worst['avg_occupancy']:.0f}%). Ajuster effectifs en conséquence.",
    }


def get_pricing_guide():
    """
    Generate pricing recommendations by day-of-week based on occupancy vs ADR patterns.
    Identifies days where you're leaving money on the table.
    """
    from database.models import TOTAL_ROOMS

    baselines = get_dow_baselines()
    if not baselines:
        return {'has_data': False}

    all_adr = [b['avg_adr'] for b in baselines.values() if b['avg_adr'] > 0]
    overall_avg_adr = sum(all_adr) / len(all_adr) if all_adr else 200

    guide = []
    total_annual_opportunity = 0

    for dow in range(7):
        b = baselines.get(dow)
        if not b:
            continue

        occ = b['avg_occupancy']
        adr = b['avg_adr']

        # Pricing logic based on demand (occupancy) patterns
        if occ >= 90:
            # High demand — should charge premium
            suggested_adr = round(overall_avg_adr * 1.15, 2)  # +15%
            if adr < suggested_adr:
                strategy = 'Augmenter'
                strategy_detail = f"Forte demande ({occ:.0f}% occ) → augmenter à ${suggested_adr:.0f}"
                annual_opp = round((suggested_adr - adr) * b['avg_rooms_sold'] * 52, 2)
            else:
                strategy = 'Maintenir'
                strategy_detail = f"Bon positionnement à ${adr:.0f} avec {occ:.0f}% occ"
                annual_opp = 0
                suggested_adr = adr
        elif occ >= 75:
            # Solid demand — hold price
            strategy = 'Maintenir'
            strategy_detail = f"Demande solide ({occ:.0f}% occ) — maintenir ${adr:.0f}"
            suggested_adr = adr
            annual_opp = 0
        elif occ >= 55:
            # Moderate — slight discount to drive volume
            suggested_adr = round(overall_avg_adr * 0.92, 2)  # -8%
            strategy = 'Léger rabais'
            rooms_gap = round(TOTAL_ROOMS * 0.75 - TOTAL_ROOMS * occ / 100)
            strategy_detail = f"Demande modérée ({occ:.0f}%) — rabais léger à ${suggested_adr:.0f} pour remplir {rooms_gap} chambres de plus"
            annual_opp = round(rooms_gap * suggested_adr * 52, 2) if rooms_gap > 0 else 0
        else:
            # Low demand — aggressive discount + promotions
            suggested_adr = round(overall_avg_adr * 0.80, 2)  # -20%
            rooms_gap = round(TOTAL_ROOMS * 0.55 - TOTAL_ROOMS * occ / 100)
            strategy = 'Rabais agressif'
            strategy_detail = f"Faible demande ({occ:.0f}%) — tarif promotionnel ${suggested_adr:.0f}, activer OTAs, packages"
            annual_opp = round(rooms_gap * suggested_adr * 52, 2) if rooms_gap > 0 else 0

        total_annual_opportunity += max(0, annual_opp)

        guide.append({
            'dow': dow,
            'day_name': b['day_name'],
            'avg_occupancy': occ,
            'current_adr': adr,
            'suggested_adr': round(suggested_adr, 2),
            'adr_delta': round(suggested_adr - adr, 2),
            'strategy': strategy,
            'strategy_detail': strategy_detail,
            'annual_opportunity': max(0, round(annual_opp)),
        })

    # Key insight: find the biggest money-on-table day
    biggest_opp = max(guide, key=lambda x: x['annual_opportunity'])

    return {
        'has_data': True,
        'guide': guide,
        'overall_avg_adr': round(overall_avg_adr, 2),
        'total_annual_opportunity': round(total_annual_opportunity),
        'biggest_opportunity': biggest_opp['day_name'],
        'insight': f"Opportunité annuelle estimée: ${total_annual_opportunity:,.0f}. Plus gros levier: {biggest_opp['day_name']} ({biggest_opp['strategy_detail']})",
    }


def get_savings_calculator():
    """
    Calculate concrete dollar savings from 5 optimization levers using actual hotel data.
    Each lever shows current state, target, and annualized savings.
    """
    from database.models import DailyJourMetrics, DailyCardMetrics, TOTAL_ROOMS
    from sqlalchemy import func

    end_row = DailyJourMetrics.query.order_by(DailyJourMetrics.date.desc()).first()
    if not end_row:
        return {'has_data': False}

    end_date = end_row.date
    from datetime import timedelta
    start_date = end_date - timedelta(days=90)

    metrics = DailyJourMetrics.query.filter(
        DailyJourMetrics.date.between(start_date, end_date)
    ).all()

    if len(metrics) < 7:
        return {'has_data': False}

    n = len(metrics)
    avg_adr = sum(m.adr or 0 for m in metrics) / n
    avg_occ = sum(m.occupancy_rate or 0 for m in metrics) / n
    avg_rooms = sum(m.total_rooms_sold or 0 for m in metrics) / n
    avg_clients = sum(m.nb_clients or 0 for m in metrics) / n
    avg_fb = sum(m.fb_revenue or 0 for m in metrics) / n
    avg_fb_per_client = avg_fb / avg_clients if avg_clients > 0 else 0
    avg_comp = sum(m.rooms_comp or 0 for m in metrics) / n
    avg_oos = sum(m.rooms_hors_usage or 0 for m in metrics) / n

    levers = []
    total_savings = 0

    # --- LEVER 1: Sunday fill strategy ---
    baselines = get_dow_baselines()
    if baselines:
        sunday = baselines.get(6)  # 6 = Sunday
        if sunday and sunday['avg_occupancy'] < avg_occ - 15:
            current_rooms = round(TOTAL_ROOMS * sunday['avg_occupancy'] / 100)
            target_occ = min(sunday['avg_occupancy'] + 15, avg_occ)
            target_rooms = round(TOTAL_ROOMS * target_occ / 100)
            gap = target_rooms - current_rooms
            discount_adr = round(avg_adr * 0.80, 2)
            annual = round(gap * discount_adr * 52)
            levers.append({
                'name': 'Remplissage dimanche',
                'name_en': 'Sunday Fill Strategy',
                'current': f"{sunday['avg_occupancy']:.0f}% occ ({current_rooms} chambres)",
                'target': f"{target_occ:.0f}% occ ({target_rooms} chambres)",
                'action': f"Tarif promotionnel ${discount_adr:.0f} (-20%), packages weekend, OTA push",
                'annual_savings': annual,
                'category': 'revenue',
            })
            total_savings += annual

    # --- LEVER 2: Card fee optimization ---
    # Get card volume breakdown
    cards = DailyCardMetrics.query.filter(
        DailyCardMetrics.date.between(start_date, end_date)
    ).all()
    if cards:
        by_type = {}
        for c in cards:
            by_type.setdefault(c.card_type, 0)
            by_type[c.card_type] = by_type[c.card_type] + (c.pos_total or 0)

        total_vol = sum(by_type.values())
        amex_vol = by_type.get('AMEX', 0)
        amex_pct = amex_vol / total_vol * 100 if total_vol > 0 else 0

        if amex_pct > 10:
            # If 5% of AMEX shifts to Visa/Debit
            shift_amount = amex_vol * 0.30  # 30% of AMEX could shift
            fee_diff = 0.01  # 1% fee difference (AMEX 2.5% vs Visa 1.5%)
            annual_savings = round(shift_amount / n * 365 * fee_diff)
            levers.append({
                'name': 'Optimisation frais cartes',
                'name_en': 'Card Fee Optimization',
                'current': f"AMEX = {amex_pct:.0f}% du volume (${amex_vol/n*365:,.0f}/an)",
                'target': f"Réduire AMEX de 30% → shift vers Visa/Débit",
                'action': "Encourager Visa/MC/Débit au check-in, signalétique aux caisses",
                'annual_savings': annual_savings,
                'category': 'cost',
            })
            total_savings += annual_savings

    # --- LEVER 3: Comp room policy ---
    if avg_comp > 0.5:
        target_comp = 0.5  # Max 0.5/day average
        saved_rooms = (avg_comp - target_comp)
        annual = round(saved_rooms * avg_adr * 365)
        levers.append({
            'name': 'Politique chambres gratuites',
            'name_en': 'Comp Room Policy',
            'current': f"{avg_comp:.1f} chambres comp/jour (${avg_comp * avg_adr * 365:,.0f}/an perdu)",
            'target': f"Max {target_comp:.1f} comp/jour",
            'action': "Politique d'approbation GM pour comps, suivi mensuel par département",
            'annual_savings': annual,
            'category': 'revenue',
        })
        total_savings += annual

    # --- LEVER 4: OOS room recovery ---
    # Cap OOS at realistic max (>15 likely includes rooms-to-clean, not true OOS)
    realistic_oos = min(avg_oos, 10)  # Cap at 10 — beyond that it's data quality
    target_oos = 2
    if realistic_oos > target_oos:
        recovered = realistic_oos - target_oos
        annual = round(recovered * avg_adr * (avg_occ / 100) * 365)
        levers.append({
            'name': 'Réduction chambres hors service',
            'name_en': 'OOS Room Recovery',
            'current': f"{realistic_oos:.0f} chambres OOS/jour" + (" (données indiquent {:.0f}, probablement inclut ch. à refaire)".format(avg_oos) if avg_oos > 10 else ""),
            'target': f"Max {target_oos} chambres OOS/jour",
            'action': "Accélérer les réparations, prioriser la maintenance préventive, vérifier données OOS vs ch. à refaire",
            'annual_savings': annual,
            'category': 'revenue',
        })
        total_savings += annual

    # --- LEVER 5: F&B upsell on low-F&B days ---
    if baselines and avg_fb_per_client > 0:
        # Identify days with genuinely LOW F&B per client (exclude banquet-heavy days)
        # Banquet days have F&B/client >$150 — those aren't upsell opportunities
        low_fb_days = [b for b in baselines.values()
                       if b['avg_fb_per_client'] < 80 and b['avg_fb_per_client'] > 0]
        if low_fb_days:
            avg_low_fb_pc = sum(b['avg_fb_per_client'] for b in low_fb_days) / len(low_fb_days)
            # Realistic target: +$15/client through menu upsell, combos, happy hour
            target_fb_pc = avg_low_fb_pc + 15
            uplift = 15.0  # $15/client is achievable via training + promotions
            avg_low_clients = sum(b['avg_clients'] for b in low_fb_days) / len(low_fb_days)
            annual = round(uplift * avg_low_clients * len(low_fb_days) * 52)
            low_day_names = ', '.join(b['day_name'] for b in low_fb_days)
            levers.append({
                'name': 'Upsell F&B jours faibles',
                'name_en': 'F&B Upsell Low-Spend Days',
                'current': f"${avg_low_fb_pc:.0f}/client les {low_day_names}",
                'target': f"${target_fb_pc:.0f}/client (+$15 via upsell)",
                'action': "Happy hour, combos repas+boisson, formation upsell serveurs, menu du jour",
                'annual_savings': annual,
                'category': 'revenue',
            })
            total_savings += annual

    # --- LEVER 6: High-demand day pricing premium ---
    if baselines:
        high_occ_days = [b for b in baselines.values() if b['avg_occupancy'] >= 88]
        if high_occ_days:
            underpriced = [b for b in high_occ_days if b['avg_adr'] < avg_adr * 1.10]
            if underpriced:
                premium = avg_adr * 0.12  # 12% premium
                rooms_affected = sum(b['avg_rooms_sold'] for b in underpriced) / len(underpriced)
                # Only ~40% of rooms are at BAR (rest are corporate/group/OTA contracted)
                bar_rooms = rooms_affected * 0.40
                annual = round(premium * bar_rooms * len(underpriced) * 52)
                day_names = ', '.join(b['day_name'] for b in underpriced)
                levers.append({
                    'name': 'Premium jours forte demande',
                    'name_en': 'High-Demand Pricing Premium',
                    'current': f"ADR moyen ${avg_adr:.0f} même les jours à >88% occ ({day_names})",
                    'target': f"ADR +12% (${avg_adr * 1.12:.0f}) les jours de forte demande",
                    'action': f"Pricing dynamique: augmenter tarif {day_names} de ${premium:.0f}",
                    'annual_savings': annual,
                    'category': 'revenue',
                })
                total_savings += annual

    # Sort by biggest impact
    levers.sort(key=lambda x: x['annual_savings'], reverse=True)

    return {
        'has_data': True,
        'levers': levers,
        'total_annual_savings': round(total_savings),
        'data_period_days': n,
        'insight': f"{len(levers)} leviers identifiés pour ${total_savings:,.0f}/an d'économies et revenus additionnels.",
    }
