"""
Insights Engine — Deep statistical analysis from DailyJourMetrics.

Runs correlations, seasonality, pricing power, F&B elasticity,
and anomaly detection to surface actionable revenue insights.
"""

from datetime import date, timedelta
from collections import defaultdict
import logging
try:
    import numpy as np
    from sklearn.cluster import KMeans
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None
    KMeans = None

logger = logging.getLogger(__name__)


class InsightsEngine:
    """Compute deep analytics insights from historical hotel data."""

    def __init__(self, metrics):
        """
        Args:
            metrics: list of DailyJourMetrics ORM objects, ordered by date
        """
        self.metrics = [m for m in metrics if m.total_revenue > 0 and m.total_rooms_sold > 0]
        self.n = len(self.metrics)

    def get_all_insights(self):
        """Return all insights as a structured dict for the dashboard."""
        if not HAS_NUMPY:
            logger.warning("numpy/sklearn not installed — insights disabled")
            return {'has_insights': False, 'reason': 'numpy not installed'}
        if self.n < 30:
            return {'has_insights': False}

        return {
            'has_insights': True,
            'pricing_power': self._pricing_power(),
            'weekend_vs_weekday': self._weekend_weekday(),
            'seasonality': self._seasonality(),
            'fb_elasticity': self._fb_elasticity(),
            'outlet_performance': self._outlet_performance(),
            'oos_analysis': self._oos_analysis(),
            'anomalies': self._anomalies(),
            'yoy_growth': self._yoy_growth(),
            'cash_variance': self._cash_variance(),
            'revpor': self._revpor(),
            'fb_capture': self._fb_capture(),
            'suite_premium': self._suite_premium(),
            'guest_density': self._guest_density(),
            'banquet_impact': self._banquet_impact(),
            'revenue_concentration': self._revenue_concentration(),
            'moving_averages': self._moving_averages(),
            'demand_forecast': self._demand_forecast(),
            'comp_roi': self._comp_roi(),
            'tax_efficiency': self._tax_efficiency(),
            'price_elasticity': self._price_elasticity(),
            'day_of_week_revenue': self._day_of_week_revenue(),
            'operating_regimes': self._operating_regimes(),
            'variance_decomposition': self._variance_decomposition(),
            'fb_conversion_funnel': self._fb_conversion_funnel(),
            'marginal_room_revenue': self._marginal_room_revenue(),
            'adr_compression': self._adr_compression(),
            'pareto_analysis': self._pareto_analysis(),
            'staffing_optimization': self._staffing_optimization(),
            'narrative_story': self._narrative_story(),
        }

    # ==========================================================================
    # PRICING POWER
    # ==========================================================================
    def _pricing_power(self):
        bands = {
            'low': {'label': '<60%', 'min': 0, 'max': 60, 'days': [], 'adrs': []},
            'mid': {'label': '60-85%', 'min': 60, 'max': 85, 'days': [], 'adrs': []},
            'high': {'label': '>85%', 'min': 85, 'max': 200, 'days': [], 'adrs': []},
        }

        for m in self.metrics:
            occ = m.occupancy_rate
            adr = m.adr
            if adr <= 0:
                continue
            for band in bands.values():
                if band['min'] <= occ < band['max']:
                    band['days'].append(m)
                    band['adrs'].append(adr)
                    break

        result = {}
        for key, band in bands.items():
            n = len(band['adrs'])
            avg_adr = sum(band['adrs']) / n if n else 0
            avg_occ = sum(d.occupancy_rate for d in band['days']) / n if n else 0
            avg_rev = sum(d.total_revenue for d in band['days']) / n if n else 0
            result[key] = {
                'label': band['label'],
                'days': n,
                'avg_adr': round(avg_adr, 2),
                'avg_occ': round(avg_occ, 1),
                'avg_revenue': round(avg_rev, 0),
            }

        # Calculate the premium gap
        high_adr = result.get('high', {}).get('avg_adr', 0)
        mid_adr = result.get('mid', {}).get('avg_adr', 0)
        premium_pct = ((high_adr - mid_adr) / mid_adr * 100) if mid_adr > 0 else 0

        # What if we increased high-occ ADR by 10%?
        high_days = result.get('high', {}).get('days', 0)
        high_sold = sum(d.total_rooms_sold for d in bands['high']['days'])
        avg_sold_high = high_sold / high_days if high_days > 0 else 0
        uplift_10pct = high_adr * 0.10 * avg_sold_high * 365 * (high_days / self.n)

        result['premium_pct'] = round(premium_pct, 1)
        result['uplift_10pct_annual'] = round(uplift_10pct, 0)

        return result

    # ==========================================================================
    # WEEKEND vs WEEKDAY
    # ==========================================================================
    def _weekend_weekday(self):
        weekend = []  # Fri, Sat, Sun
        weekday = []

        for m in self.metrics:
            dow = m.date.weekday()
            if dow >= 4:  # Fri=4, Sat=5, Sun=6
                weekend.append(m)
            else:
                weekday.append(m)

        def avg_metrics(days):
            n = len(days)
            if n == 0:
                return {}
            return {
                'days': n,
                'avg_revenue': round(sum(d.total_revenue for d in days) / n, 0),
                'avg_room_rev': round(sum(d.room_revenue for d in days) / n, 0),
                'avg_fb_rev': round(sum(d.fb_revenue for d in days) / n, 0),
                'avg_occ': round(sum(d.occupancy_rate for d in days) / n, 1),
                'avg_adr': round(sum(d.adr for d in days) / n, 2),
                'avg_clients': round(sum(d.nb_clients for d in days) / n, 1),
                'avg_tips': round(sum(d.tips_total for d in days) / n, 0),
            }

        we = avg_metrics(weekend)
        wd = avg_metrics(weekday)

        rev_premium = ((we.get('avg_revenue', 0) - wd.get('avg_revenue', 0))
                       / wd.get('avg_revenue', 1) * 100)
        fb_premium = ((we.get('avg_fb_rev', 0) - wd.get('avg_fb_rev', 0))
                      / wd.get('avg_fb_rev', 1) * 100)

        return {
            'weekend': we,
            'weekday': wd,
            'revenue_premium_pct': round(rev_premium, 1),
            'fb_premium_pct': round(fb_premium, 1),
        }

    # ==========================================================================
    # SEASONALITY
    # ==========================================================================
    def _seasonality(self):
        by_month = defaultdict(list)
        for m in self.metrics:
            by_month[m.month].append(m)

        months_fr = {
            1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Aoû', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }

        monthly = []
        for mo in range(1, 13):
            days = by_month.get(mo, [])
            if not days:
                continue
            n = len(days)
            monthly.append({
                'month': mo,
                'label': months_fr.get(mo, str(mo)),
                'avg_revenue': round(sum(d.total_revenue for d in days) / n, 0),
                'avg_occ': round(sum(d.occupancy_rate for d in days) / n, 1),
                'avg_adr': round(sum(d.adr for d in days) / n, 2),
                'avg_fb': round(sum(d.fb_revenue for d in days) / n, 0),
                'avg_revpar': round(sum(d.revpar for d in days) / n, 2),
                'days': n,
            })

        # Sort by revenue to find best/worst
        sorted_by_rev = sorted(monthly, key=lambda x: x['avg_revenue'], reverse=True)
        best = sorted_by_rev[0] if sorted_by_rev else None
        worst = sorted_by_rev[-1] if sorted_by_rev else None

        gap = best['avg_revenue'] - worst['avg_revenue'] if best and worst else 0
        gap_pct = (gap / worst['avg_revenue'] * 100) if worst and worst['avg_revenue'] > 0 else 0

        return {
            'monthly': monthly,
            'best_month': best,
            'worst_month': worst,
            'daily_gap': round(gap, 0),
            'gap_pct': round(gap_pct, 1),
            'annual_gap': round(gap * 30, 0),  # Approximate monthly gap
        }

    # ==========================================================================
    # F&B ELASTICITY
    # ==========================================================================
    def _fb_elasticity(self):
        bands = [
            {'label': '<50%', 'min': 0, 'max': 50, 'days': []},
            {'label': '50-70%', 'min': 50, 'max': 70, 'days': []},
            {'label': '70-85%', 'min': 70, 'max': 85, 'days': []},
            {'label': '85-100%', 'min': 85, 'max': 200, 'days': []},
        ]

        for m in self.metrics:
            if m.nb_clients <= 0:
                continue
            for band in bands:
                if band['min'] <= m.occupancy_rate < band['max']:
                    band['days'].append(m)
                    break

        result = []
        for band in bands:
            days = band['days']
            n = len(days)
            if n == 0:
                continue
            fb_total = sum(d.fb_revenue for d in days)
            guests_total = sum(d.nb_clients for d in days)
            fb_per_guest = fb_total / guests_total if guests_total > 0 else 0
            avg_fb = fb_total / n

            result.append({
                'label': band['label'],
                'days': n,
                'fb_per_guest': round(fb_per_guest, 2),
                'avg_fb_revenue': round(avg_fb, 0),
                'avg_occ': round(sum(d.occupancy_rate for d in days) / n, 1),
            })

        # Elasticity: does FB/guest stay flat, grow, or shrink with occupancy?
        if len(result) >= 2:
            low_fb = result[0]['fb_per_guest']
            high_fb = result[-1]['fb_per_guest']
            elasticity = 'declining' if high_fb < low_fb else 'growing' if high_fb > low_fb * 1.05 else 'flat'
            change_pct = ((high_fb - low_fb) / low_fb * 100) if low_fb > 0 else 0
        else:
            elasticity = 'unknown'
            change_pct = 0

        return {
            'bands': result,
            'elasticity': elasticity,
            'change_pct': round(change_pct, 1),
        }

    # ==========================================================================
    # OUTLET PERFORMANCE
    # ==========================================================================
    def _outlet_performance(self):
        outlets = {
            'Café Link': {'attr': 'cafe_link_total', 'total': 0},
            'Piazza': {'attr': 'piazza_total', 'total': 0},
            'Spesa': {'attr': 'spesa_total', 'total': 0},
            'Room Service': {'attr': 'room_svc_total', 'total': 0},
            'Banquet': {'attr': 'banquet_total', 'total': 0},
        }

        for m in self.metrics:
            for name, info in outlets.items():
                info['total'] += getattr(m, info['attr'], 0)

        fb_total = sum(o['total'] for o in outlets.values())

        # Calculate correlation with occupancy for each outlet
        result = []
        for name, info in outlets.items():
            attr = info['attr']
            values = [getattr(m, attr, 0) for m in self.metrics]
            occs = [m.occupancy_rate for m in self.metrics]

            corr = self._pearson(values, occs)
            share = (info['total'] / fb_total * 100) if fb_total > 0 else 0
            daily_avg = info['total'] / self.n if self.n > 0 else 0

            result.append({
                'name': name,
                'total_revenue': round(info['total'], 0),
                'daily_avg': round(daily_avg, 0),
                'fb_share_pct': round(share, 1),
                'occ_correlation': round(corr, 3),
            })

        result.sort(key=lambda x: x['total_revenue'], reverse=True)
        return result

    # ==========================================================================
    # OOS ANALYSIS
    # ==========================================================================
    def _oos_analysis(self):
        oos_days = [m for m in self.metrics if m.rooms_hors_usage > 0]
        if not oos_days:
            return {'avg_oos': 0, 'total_impact': 0}

        total_oos = sum(m.rooms_hors_usage for m in self.metrics)
        avg_oos = total_oos / self.n
        avg_adr = sum(m.adr for m in self.metrics) / self.n

        # Impact by month
        by_month = defaultdict(list)
        for m in self.metrics:
            by_month[m.month].append(m.rooms_hors_usage)

        monthly_avg = {}
        months_fr = {1:'Jan',2:'Fév',3:'Mar',4:'Avr',5:'Mai',6:'Jun',
                     7:'Jul',8:'Aoû',9:'Sep',10:'Oct',11:'Nov',12:'Déc'}
        for mo, vals in by_month.items():
            monthly_avg[months_fr.get(mo, str(mo))] = round(sum(vals) / len(vals), 1)

        # Worst OOS months
        sorted_months = sorted(monthly_avg.items(), key=lambda x: x[1], reverse=True)

        return {
            'avg_oos_per_day': round(avg_oos, 1),
            'annual_cost': round(avg_oos * avg_adr * 365, 0),
            'reduction_30pct_saving': round(avg_oos * 0.3 * avg_adr * 365, 0),
            'worst_months': sorted_months[:3],
            'best_months': sorted_months[-3:],
        }

    # ==========================================================================
    # ANOMALIES
    # ==========================================================================
    def _anomalies(self):
        revs = [m.total_revenue for m in self.metrics]
        occs = [m.occupancy_rate for m in self.metrics]

        avg_rev = sum(revs) / len(revs)
        std_rev = (sum((r - avg_rev) ** 2 for r in revs) / len(revs)) ** 0.5

        avg_occ = sum(occs) / len(occs)
        std_occ = (sum((o - avg_occ) ** 2 for o in occs) / len(occs)) ** 0.5

        # Find days > 2 std devs from mean
        rev_outliers = []
        for m in self.metrics:
            z_rev = (m.total_revenue - avg_rev) / std_rev if std_rev > 0 else 0
            if abs(z_rev) > 2:
                rev_outliers.append({
                    'date': m.date.isoformat(),
                    'revenue': round(m.total_revenue, 0),
                    'z_score': round(z_rev, 2),
                    'occ': round(m.occupancy_rate, 1),
                    'adr': round(m.adr, 2),
                    'direction': 'high' if z_rev > 0 else 'low',
                })

        rev_outliers.sort(key=lambda x: abs(x['z_score']), reverse=True)

        return {
            'revenue_outliers': rev_outliers[:10],
            'total_outlier_days': len(rev_outliers),
            'avg_revenue': round(avg_rev, 0),
            'std_revenue': round(std_rev, 0),
        }

    # ==========================================================================
    # YOY GROWTH
    # ==========================================================================
    def _yoy_growth(self):
        by_year = defaultdict(list)
        for m in self.metrics:
            by_year[m.year].append(m)

        years = sorted(by_year.keys())
        result = []

        for i, year in enumerate(years):
            days = by_year[year]
            n = len(days)
            total_rev = sum(d.total_revenue for d in days)
            avg_adr = sum(d.adr for d in days) / n
            avg_occ = sum(d.occupancy_rate for d in days) / n
            avg_revpar = sum(d.revpar for d in days) / n
            total_fb = sum(d.fb_revenue for d in days)

            entry = {
                'year': year,
                'days': n,
                'total_revenue': round(total_rev, 0),
                'avg_adr': round(avg_adr, 2),
                'avg_occ': round(avg_occ, 1),
                'avg_revpar': round(avg_revpar, 2),
                'total_fb': round(total_fb, 0),
            }

            # Compute YoY deltas
            if i > 0:
                prev = by_year[years[i - 1]]
                prev_n = len(prev)
                prev_rev = sum(d.total_revenue for d in prev)
                prev_adr = sum(d.adr for d in prev) / prev_n
                prev_occ = sum(d.occupancy_rate for d in prev) / prev_n

                # Normalize to daily for fair comparison
                daily_now = total_rev / n
                daily_prev = prev_rev / prev_n
                entry['rev_growth_pct'] = round((daily_now - daily_prev) / daily_prev * 100, 1) if daily_prev > 0 else 0
                entry['adr_growth_pct'] = round((avg_adr - prev_adr) / prev_adr * 100, 1) if prev_adr > 0 else 0
                entry['occ_delta'] = round(avg_occ - prev_occ, 1)

            result.append(entry)

        return result

    # ==========================================================================
    # CASH VARIANCE
    # ==========================================================================
    def _cash_variance(self):
        diffs = [m.cash_difference for m in self.metrics if m.cash_difference != 0]
        all_diffs = [m.cash_difference for m in self.metrics]

        if not diffs:
            return {'has_data': False}

        positive = [d for d in diffs if d > 0]
        negative = [d for d in diffs if d < 0]

        # Days with >$100 variance
        big_variances = [d for d in all_diffs if abs(d) > 100]

        return {
            'has_data': True,
            'days_with_variance': len(diffs),
            'pct_days_with_variance': round(len(diffs) / self.n * 100, 1),
            'total_positive': round(sum(positive), 0),
            'total_negative': round(sum(negative), 0),
            'net_impact': round(sum(all_diffs), 0),
            'avg_variance': round(sum(abs(d) for d in diffs) / len(diffs), 2) if diffs else 0,
            'big_variance_days': len(big_variances),
            'big_variance_pct': round(len(big_variances) / self.n * 100, 1),
        }

    # ==========================================================================
    # REVPOR - Revenue Per Occupied Room
    # ==========================================================================
    def _revpor(self):
        """RevPOR: Total revenue per occupied room — shows actual guest value."""
        by_month = defaultdict(list)
        revpors = []
        room_only_revpors = []
        ancillary_revpors = []

        for m in self.metrics:
            revpor = m.total_revenue / m.total_rooms_sold if m.total_rooms_sold > 0 else 0
            room_only = m.room_revenue / m.total_rooms_sold if m.total_rooms_sold > 0 else 0
            ancillary = (m.total_revenue - m.room_revenue) / m.total_rooms_sold if m.total_rooms_sold > 0 else 0

            revpors.append(revpor)
            room_only_revpors.append(room_only)
            ancillary_revpors.append(ancillary)
            by_month[m.month].append((revpor, room_only, ancillary))

        avg_revpor = sum(revpors) / len(revpors) if revpors else 0
        avg_room_only = sum(room_only_revpors) / len(room_only_revpors) if room_only_revpors else 0
        avg_ancillary = sum(ancillary_revpors) / len(ancillary_revpors) if ancillary_revpors else 0

        # Monthly trend
        months_fr = {
            1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Aoû', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }

        monthly_trend = []
        for mo in range(1, 13):
            values = by_month.get(mo, [])
            if values:
                rev_avg = sum(v[0] for v in values) / len(values)
                room_avg = sum(v[1] for v in values) / len(values)
                monthly_trend.append({
                    'month': months_fr.get(mo, str(mo)),
                    'revpor': round(rev_avg, 2),
                    'room_only': round(room_avg, 2),
                })

        ancillary_pct = (avg_ancillary / avg_revpor * 100) if avg_revpor > 0 else 0

        return {
            'avg_revpor': round(avg_revpor, 2),
            'room_only_revpor': round(avg_room_only, 2),
            'ancillary_revpor': round(avg_ancillary, 2),
            'ancillary_pct_of_revpor': round(ancillary_pct, 1),
            'monthly_trend': monthly_trend,
        }

    # ==========================================================================
    # F&B CAPTURE RATE
    # ==========================================================================
    def _fb_capture(self):
        """F&B capture rate: FB revenue per occupied room. Shows if guests eat on-property."""
        by_month = defaultdict(list)
        fb_per_rooms = []
        fb_as_pct_room = []

        for m in self.metrics:
            fb_per_room = m.fb_revenue / m.total_rooms_sold if m.total_rooms_sold > 0 else 0
            pct = (m.fb_revenue / m.room_revenue * 100) if m.room_revenue > 0 else 0
            fb_per_rooms.append(fb_per_room)
            fb_as_pct_room.append(pct)
            by_month[m.month].append((fb_per_room, pct))

        avg_fb_per_room = sum(fb_per_rooms) / len(fb_per_rooms) if fb_per_rooms else 0
        avg_fb_pct = sum(fb_as_pct_room) / len(fb_as_pct_room) if fb_as_pct_room else 0

        # Industry benchmark (15-25% for full-service)
        benchmark_low = 15.0
        benchmark_high = 25.0
        vs_benchmark = 'above' if avg_fb_pct > benchmark_high else 'below' if avg_fb_pct < benchmark_low else 'within'

        # Monthly trend
        months_fr = {
            1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Aoû', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }

        monthly_trend = []
        high_capture_days = []
        low_capture_days = []

        sorted_by_fb = sorted(enumerate(self.metrics), key=lambda x: fb_per_rooms[x[0]], reverse=True)

        for mo in range(1, 13):
            values = by_month.get(mo, [])
            if values:
                fb_avg = sum(v[0] for v in values) / len(values)
                pct_avg = sum(v[1] for v in values) / len(values)
                monthly_trend.append({
                    'month': months_fr.get(mo, str(mo)),
                    'fb_per_room': round(fb_avg, 2),
                    'fb_pct_room_rev': round(pct_avg, 1),
                })

        # Top 5 high capture days
        for i in range(min(5, len(sorted_by_fb))):
            idx, m = sorted_by_fb[i]
            high_capture_days.append({
                'date': m.date.isoformat(),
                'fb_per_room': round(fb_per_rooms[idx], 2),
                'pct': round(fb_as_pct_room[idx], 1),
            })

        # Top 5 low capture days
        sorted_low = sorted(enumerate(self.metrics), key=lambda x: fb_per_rooms[x[0]])
        for i in range(min(5, len(sorted_low))):
            idx, m = sorted_low[i]
            low_capture_days.append({
                'date': m.date.isoformat(),
                'fb_per_room': round(fb_per_rooms[idx], 2),
                'pct': round(fb_as_pct_room[idx], 1),
            })

        return {
            'avg_fb_per_room': round(avg_fb_per_room, 2),
            'avg_fb_pct_of_room_rev': round(avg_fb_pct, 1),
            'benchmark_range': f'{benchmark_low:.0f}-{benchmark_high:.0f}%',
            'vs_benchmark': vs_benchmark,
            'monthly_trend': monthly_trend,
            'high_capture_days': high_capture_days,
            'low_capture_days': low_capture_days,
        }

    # ==========================================================================
    # SUITE PREMIUM ANALYSIS
    # ==========================================================================
    def _suite_premium(self):
        """Analyze revenue uplift when more suites are sold."""
        suite_counts = [m.rooms_suite for m in self.metrics]
        median_suites = sorted(suite_counts)[len(suite_counts) // 2] if suite_counts else 0

        high_suite_days = [m for m in self.metrics if m.rooms_suite > median_suites]
        low_suite_days = [m for m in self.metrics if m.rooms_suite <= median_suites]

        def metrics_for_group(days):
            if not days:
                return {}
            n = len(days)
            return {
                'days': n,
                'avg_adr': round(sum(d.adr for d in days) / n, 2),
                'avg_revenue': round(sum(d.total_revenue for d in days) / n, 0),
                'avg_fb_rev': round(sum(d.fb_revenue for d in days) / n, 0),
                'avg_occ': round(sum(d.occupancy_rate for d in days) / n, 1),
            }

        high = metrics_for_group(high_suite_days)
        low = metrics_for_group(low_suite_days)

        premium_adr_pct = ((high.get('avg_adr', 0) - low.get('avg_adr', 0)) / low.get('avg_adr', 1) * 100)
        premium_rev_pct = ((high.get('avg_revenue', 0) - low.get('avg_revenue', 0)) / low.get('avg_revenue', 1) * 100)

        # Estimate annual uplift if suite sales increased by 10%
        avg_suites_sold = sum(d.rooms_suite for d in self.metrics) / self.n if self.n > 0 else 0
        potential_additional_suites = avg_suites_sold * 0.10
        avg_suite_premium = (high.get('avg_adr', 0) - low.get('avg_adr', 0))
        estimated_uplift = potential_additional_suites * avg_suite_premium * 365 * (high.get('days', 0) / self.n) if self.n > 0 else 0

        return {
            'median_suite_count': round(median_suites, 1),
            'high_suite_days': high,
            'low_suite_days': low,
            'premium_adr_pct': round(premium_adr_pct, 1),
            'premium_revenue_pct': round(premium_rev_pct, 1),
            'estimated_uplift_10pct_annual': round(estimated_uplift, 0),
        }

    # ==========================================================================
    # GUEST DENSITY ANALYSIS
    # ==========================================================================
    def _guest_density(self):
        """Guest density (clients/room) and its impact on F&B."""
        densities = []
        for m in self.metrics:
            if m.total_rooms_sold > 0:
                d = m.nb_clients / m.total_rooms_sold
                densities.append((m, d))

        if not densities:
            return {}

        # Create density bands
        bands = {
            '<1.2': {'min': 0, 'max': 1.2, 'metrics': []},
            '1.2-1.5': {'min': 1.2, 'max': 1.5, 'metrics': []},
            '1.5-1.8': {'min': 1.5, 'max': 1.8, 'metrics': []},
            '>1.8': {'min': 1.8, 'max': 10, 'metrics': []},
        }

        for m, d in densities:
            for band_key, band in bands.items():
                if band['min'] <= d < band['max']:
                    band['metrics'].append(m)
                    break

        result = []
        for band_key, band in bands.items():
            days = band['metrics']
            n = len(days)
            if n == 0:
                continue
            fb_total = sum(d.fb_revenue for d in days)
            rooms_total = sum(d.total_rooms_sold for d in days)
            fb_per_room = fb_total / rooms_total if rooms_total > 0 else 0
            avg_revenue = sum(d.total_revenue for d in days) / n
            avg_tips = sum(d.tips_total for d in days) / n
            avg_density = sum(m.nb_clients / m.total_rooms_sold for m in days) / n if n > 0 else 0

            result.append({
                'band': band_key,
                'days': n,
                'avg_density': round(avg_density, 2),
                'fb_per_room': round(fb_per_room, 2),
                'avg_total_revenue': round(avg_revenue, 0),
                'avg_tips': round(avg_tips, 0),
            })

        # Correlation between density and FB spending
        dens_vals = [d for _, d in densities]
        fb_per_room_vals = [m.fb_revenue / m.total_rooms_sold for m, _ in densities]
        corr = self._pearson(dens_vals, fb_per_room_vals)

        # Estimate additional FB revenue if density increased by 0.1
        avg_density = sum(d for _, d in densities) / len(densities) if densities else 0
        avg_fb_per_room = sum(fb_per_room_vals) / len(fb_per_room_vals) if fb_per_room_vals else 0
        if corr > 0.3:  # Positive correlation
            density_impact_per_0_1 = (avg_fb_per_room * corr * 0.1) * sum(m.total_rooms_sold for m in self.metrics) / self.n
        else:
            density_impact_per_0_1 = 0

        return {
            'bands': result,
            'correlation_density_to_fb': round(corr, 3),
            'estimated_fb_gain_per_0_1_density': round(density_impact_per_0_1 * 365, 0),
        }

    # ==========================================================================
    # BANQUET IMPACT ANALYSIS
    # ==========================================================================
    def _banquet_impact(self):
        """Analyze banquet events' halo effect on total hotel revenue."""
        banquet_days = [m for m in self.metrics if m.banquet_total > 0]
        no_banquet_days = [m for m in self.metrics if m.banquet_total == 0]

        def metrics_for_group(days):
            if not days:
                return {}
            n = len(days)
            return {
                'days': n,
                'avg_total_revenue': round(sum(d.total_revenue for d in days) / n, 0),
                'avg_room_revenue': round(sum(d.room_revenue for d in days) / n, 0),
                'avg_fb_revenue_excl_banquet': round(sum(d.fb_revenue - d.banquet_total for d in days) / n, 0),
                'avg_occupancy': round(sum(d.occupancy_rate for d in days) / n, 1),
                'avg_adr': round(sum(d.adr for d in days) / n, 2),
                'avg_tips': round(sum(d.tips_total for d in days) / n, 0),
            }

        banquet = metrics_for_group(banquet_days)
        no_banquet = metrics_for_group(no_banquet_days)

        revenue_uplift = ((banquet.get('avg_total_revenue', 0) - no_banquet.get('avg_total_revenue', 0))
                         / no_banquet.get('avg_total_revenue', 1) * 100) if no_banquet.get('avg_total_revenue', 0) > 0 else 0

        # Correlation between banquet revenue and room revenue
        banquet_revs = [m.banquet_total for m in self.metrics]
        room_revs = [m.room_revenue for m in self.metrics]
        corr = self._pearson(banquet_revs, room_revs)

        avg_banquet_rev = sum(d.banquet_total for d in banquet_days) / len(banquet_days) if banquet_days else 0

        return {
            'banquet_days': banquet,
            'no_banquet_days': no_banquet,
            'total_revenue_uplift_pct': round(revenue_uplift, 1),
            'banquet_to_room_correlation': round(corr, 3),
            'avg_daily_banquet_revenue': round(avg_banquet_rev, 0),
        }

    # ==========================================================================
    # REVENUE CONCENTRATION & DIVERSIFICATION
    # ==========================================================================
    def _revenue_concentration(self):
        """Revenue diversification index — how dependent on room revenue."""
        by_month = defaultdict(list)

        for m in self.metrics:
            room_pct = (m.room_revenue / m.total_revenue * 100) if m.total_revenue > 0 else 0
            fb_pct = (m.fb_revenue / m.total_revenue * 100) if m.total_revenue > 0 else 0
            other_pct = 100 - room_pct - fb_pct

            # Herfindahl index = sum of squared shares
            herfindahl = (room_pct ** 2 + fb_pct ** 2 + other_pct ** 2) / 100

            by_month[m.month].append({
                'room_pct': room_pct,
                'fb_pct': fb_pct,
                'other_pct': other_pct,
                'herfindahl': herfindahl,
            })

        months_fr = {
            1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Aoû', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }

        monthly_trend = []
        herfindahls = []
        for mo in range(1, 13):
            values = by_month.get(mo, [])
            if values:
                n = len(values)
                room_avg = sum(v['room_pct'] for v in values) / n
                fb_avg = sum(v['fb_pct'] for v in values) / n
                other_avg = sum(v['other_pct'] for v in values) / n
                herf_avg = sum(v['herfindahl'] for v in values) / n
                herfindahls.append(herf_avg)
                monthly_trend.append({
                    'month': months_fr.get(mo, str(mo)),
                    'room_pct': round(room_avg, 1),
                    'fb_pct': round(fb_avg, 1),
                    'other_pct': round(other_avg, 1),
                    'herfindahl': round(herf_avg, 3),
                })

        overall_herfindahl = sum(herfindahls) / len(herfindahls) if herfindahls else 0

        # Current vs historical trend
        if len(monthly_trend) >= 2:
            trend = 'improving' if monthly_trend[-1]['herfindahl'] < monthly_trend[0]['herfindahl'] else 'declining' if monthly_trend[-1]['herfindahl'] > monthly_trend[0]['herfindahl'] else 'stable'
        else:
            trend = 'unknown'

        # Risk assessment: if room revenue drops 10%
        avg_room_pct = sum(v['room_pct'] for v in monthly_trend) / len(monthly_trend) if monthly_trend else 0
        risk_if_room_down_10 = -avg_room_pct * 0.10

        return {
            'monthly_trend': monthly_trend,
            'herfindahl_index': round(overall_herfindahl, 3),
            'diversification_trend': trend,
            'avg_room_pct': round(avg_room_pct, 1),
            'risk_total_rev_if_room_down_10pct': round(risk_if_room_down_10, 1),
        }

    # ==========================================================================
    # MOVING AVERAGES
    # ==========================================================================
    def _moving_averages(self):
        """7-day, 30-day, 90-day moving averages for key metrics."""
        adrs = [m.adr for m in self.metrics]
        revpars = [m.revpar for m in self.metrics]
        occs = [m.occupancy_rate for m in self.metrics]
        total_revs = [m.total_revenue for m in self.metrics]
        fb_revs = [m.fb_revenue for m in self.metrics]

        def compute_ma(values, window):
            """Compute moving average for given window size."""
            if len(values) < window:
                return []
            return [sum(values[i:i+window]) / window for i in range(len(values) - window + 1)]

        ma_7_adr = compute_ma(adrs, 7)
        ma_30_adr = compute_ma(adrs, 30)
        ma_90_adr = compute_ma(adrs, 90)

        ma_7_revpar = compute_ma(revpars, 7)
        ma_30_revpar = compute_ma(revpars, 30)
        ma_90_revpar = compute_ma(revpars, 90)

        ma_7_occ = compute_ma(occs, 7)
        ma_30_occ = compute_ma(occs, 30)
        ma_90_occ = compute_ma(occs, 90)

        ma_7_rev = compute_ma(total_revs, 7)
        ma_30_rev = compute_ma(total_revs, 30)
        ma_90_rev = compute_ma(total_revs, 90)

        ma_7_fb = compute_ma(fb_revs, 7)
        ma_30_fb = compute_ma(fb_revs, 30)
        ma_90_fb = compute_ma(fb_revs, 90)

        # Momentum: is the latest MA trending up, down, or flat?
        def get_momentum(ma_list):
            if len(ma_list) < 2:
                return 'flat'
            last = ma_list[-1]
            prev = ma_list[-2]
            if last > prev * 1.01:
                return 'up'
            elif last < prev * 0.99:
                return 'down'
            else:
                return 'flat'

        # Short-term vs long-term crossover signals
        def get_crossover_signal(ma_short, ma_long):
            """Golden cross (short above long) = bullish; Death cross = bearish"""
            if len(ma_short) < 1 or len(ma_long) < 1:
                return 'unknown'
            if ma_short[-1] > ma_long[-1]:
                return 'bullish'
            elif ma_short[-1] < ma_long[-1]:
                return 'bearish'
            else:
                return 'neutral'

        return {
            'adr': {
                'ma_7': round(ma_7_adr[-1], 2) if ma_7_adr else 0,
                'ma_30': round(ma_30_adr[-1], 2) if ma_30_adr else 0,
                'ma_90': round(ma_90_adr[-1], 2) if ma_90_adr else 0,
                'momentum_7': get_momentum(ma_7_adr),
                'crossover_7_90': get_crossover_signal(ma_7_adr, ma_90_adr),
            },
            'revpar': {
                'ma_7': round(ma_7_revpar[-1], 2) if ma_7_revpar else 0,
                'ma_30': round(ma_30_revpar[-1], 2) if ma_30_revpar else 0,
                'ma_90': round(ma_90_revpar[-1], 2) if ma_90_revpar else 0,
                'momentum_7': get_momentum(ma_7_revpar),
                'crossover_7_90': get_crossover_signal(ma_7_revpar, ma_90_revpar),
            },
            'occupancy': {
                'ma_7': round(ma_7_occ[-1], 1) if ma_7_occ else 0,
                'ma_30': round(ma_30_occ[-1], 1) if ma_30_occ else 0,
                'ma_90': round(ma_90_occ[-1], 1) if ma_90_occ else 0,
                'momentum_7': get_momentum(ma_7_occ),
                'crossover_7_90': get_crossover_signal(ma_7_occ, ma_90_occ),
            },
            'total_revenue': {
                'ma_7': round(ma_7_rev[-1], 0) if ma_7_rev else 0,
                'ma_30': round(ma_30_rev[-1], 0) if ma_30_rev else 0,
                'ma_90': round(ma_90_rev[-1], 0) if ma_90_rev else 0,
                'momentum_7': get_momentum(ma_7_rev),
                'crossover_7_90': get_crossover_signal(ma_7_rev, ma_90_rev),
            },
            'fb_revenue': {
                'ma_7': round(ma_7_fb[-1], 0) if ma_7_fb else 0,
                'ma_30': round(ma_30_fb[-1], 0) if ma_30_fb else 0,
                'ma_90': round(ma_90_fb[-1], 0) if ma_90_fb else 0,
                'momentum_7': get_momentum(ma_7_fb),
                'crossover_7_90': get_crossover_signal(ma_7_fb, ma_90_fb),
            },
        }

    # ==========================================================================
    # DEMAND FORECASTING
    # ==========================================================================
    def _demand_forecast(self):
        """Simple demand forecasting using seasonal decomposition."""
        by_month = defaultdict(list)

        for m in self.metrics:
            by_month[m.month].append(m)

        months_fr = {
            1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Aoû', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }

        seasonal_profile = {}
        for mo in range(1, 13):
            days = by_month.get(mo, [])
            if not days:
                continue
            n = len(days)
            avg_occ = sum(d.occupancy_rate for d in days) / n
            avg_adr = sum(d.adr for d in days) / n
            avg_rev = sum(d.total_revenue for d in days) / n
            std_occ = (sum((d.occupancy_rate - avg_occ) ** 2 for d in days) / n) ** 0.5
            std_adr = (sum((d.adr - avg_adr) ** 2 for d in days) / n) ** 0.5
            std_rev = (sum((d.total_revenue - avg_rev) ** 2 for d in days) / n) ** 0.5

            seasonal_profile[mo] = {
                'label': months_fr.get(mo, str(mo)),
                'avg_occ': avg_occ,
                'avg_adr': avg_adr,
                'avg_revenue': avg_rev,
                'std_occ': std_occ,
                'std_adr': std_adr,
                'std_revenue': std_rev,
                'n': n,
            }

        # Month-over-month growth trend
        ordered_months = sorted(seasonal_profile.keys())
        growth_trend = []
        for i, mo in enumerate(ordered_months):
            if i > 0:
                prev_mo = ordered_months[i - 1]
                curr_rev = seasonal_profile[mo]['avg_revenue']
                prev_rev = seasonal_profile[prev_mo]['avg_revenue']
                growth = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
                growth_trend.append(growth)

        avg_growth = sum(growth_trend) / len(growth_trend) if growth_trend else 0

        # Project next 3 months
        current_month = 12  # Assume end of year
        forecast = []
        for offset in range(1, 4):
            forecast_mo = ((current_month + offset - 1) % 12) + 1
            if forecast_mo in seasonal_profile:
                profile = seasonal_profile[forecast_mo]
                # Apply growth trend to base seasonal profile
                growth_factor = 1 + (avg_growth / 100)
                forecast.append({
                    'month': months_fr.get(forecast_mo, str(forecast_mo)),
                    'forecasted_occ': round(profile['avg_occ'] * growth_factor, 1),
                    'forecasted_adr': round(profile['avg_adr'] * growth_factor, 2),
                    'forecasted_revenue': round(profile['avg_revenue'] * growth_factor, 0),
                    'confidence_high': round(profile['avg_revenue'] * growth_factor + profile['std_revenue'], 0),
                    'confidence_low': round(profile['avg_revenue'] * growth_factor - profile['std_revenue'], 0),
                })

        # Historical summary
        historical = []
        for mo in ordered_months:
            profile = seasonal_profile[mo]
            historical.append({
                'month': profile['label'],
                'avg_occ': round(profile['avg_occ'], 1),
                'avg_adr': round(profile['avg_adr'], 2),
                'avg_revenue': round(profile['avg_revenue'], 0),
            })

        return {
            'historical_by_month': historical,
            'avg_monthly_growth_pct': round(avg_growth, 1),
            'next_3_months_forecast': forecast,
        }

    # ==========================================================================
    # COMP ROOM ROI
    # ==========================================================================
    def _comp_roi(self):
        """Comp room ROI: do comp rooms generate ancillary revenue?"""
        comp_counts = [m.rooms_comp for m in self.metrics]
        median_comps = sorted(comp_counts)[len(comp_counts) // 2] if comp_counts else 0

        high_comp_days = [m for m in self.metrics if m.rooms_comp > median_comps]
        low_comp_days = [m for m in self.metrics if m.rooms_comp <= median_comps]

        def metrics_for_group(days):
            if not days:
                return {}
            n = len(days)
            fb_total = sum(d.fb_revenue for d in days)
            rooms_total = sum(d.total_rooms_sold for d in days)
            other_rev = sum(d.total_revenue - d.room_revenue - d.fb_revenue for d in days)
            tips_total = sum(d.tips_total for d in days)

            fb_per_occupied = fb_total / rooms_total if rooms_total > 0 else 0
            other_per_occupied = other_rev / rooms_total if rooms_total > 0 else 0
            tips_per_occupied = tips_total / rooms_total if rooms_total > 0 else 0
            ancillary_per_occupied = (fb_per_occupied + other_per_occupied + tips_per_occupied)

            return {
                'days': n,
                'fb_per_occupied_room': round(fb_per_occupied, 2),
                'ancillary_per_room': round(ancillary_per_occupied, 2),
                'tips_per_room': round(tips_per_occupied, 2),
            }

        high_comp = metrics_for_group(high_comp_days)
        low_comp = metrics_for_group(low_comp_days)

        # Calculate comp count difference
        avg_high_comps = sum(d.rooms_comp for d in high_comp_days) / len(high_comp_days) if high_comp_days else 0
        avg_low_comps = sum(d.rooms_comp for d in low_comp_days) / len(low_comp_days) if low_comp_days else 0

        # Average ADR cost per comp room
        avg_adr = sum(m.adr for m in self.metrics) / self.n if self.n > 0 else 0

        # Ancillary generated by comp guests
        comp_diff = avg_high_comps - avg_low_comps
        ancillary_high = high_comp.get('ancillary_per_room', 0)
        ancillary_low = low_comp.get('ancillary_per_room', 0)
        ancillary_from_comps = (ancillary_high - ancillary_low) * comp_diff * 365

        # ROI calculation
        comp_cost = avg_adr * comp_diff * 365
        roi_pct = ((ancillary_from_comps - comp_cost) / comp_cost * 100) if comp_cost > 0 else 0

        return {
            'median_comp_count': round(median_comps, 1),
            'high_comp_days': high_comp,
            'low_comp_days': low_comp,
            'estimated_ancillary_from_comps_annual': round(ancillary_from_comps, 0),
            'estimated_comp_cost_annual': round(comp_cost, 0),
            'comp_roi_pct': round(roi_pct, 1),
        }

    # ==========================================================================
    # TAX EFFICIENCY & BILLING ERROR DETECTION
    # ==========================================================================
    def _tax_efficiency(self):
        """Tax efficiency tracking — flag billing errors through rate anomalies."""
        tax_records = []

        for m in self.metrics:
            if m.tps_total == 0 or m.tvq_total == 0:
                continue

            # Calculate effective rates
            taxable = m.tps_total / 0.05 if m.tps_total > 0 else 0  # TPS is 5%
            tps_rate = (m.tps_total / taxable * 100) if taxable > 0 else 0

            tvq_rate = (m.tvq_total / taxable * 100) if taxable > 0 else 0

            tvh_rate = (m.tvh_total / m.room_revenue * 100) if m.room_revenue > 0 else 0

            tax_records.append({
                'date': m.date,
                'tps_rate': tps_rate,
                'tvq_rate': tvq_rate,
                'tvh_rate': tvh_rate,
            })

        if not tax_records:
            return {'has_data': False}

        # Statutory rates (Quebec/Canada)
        statutory_tps = 5.0
        statutory_tvq = 9.975  # Approx
        statutory_tvh = 8.0  # Approx (varies by province)

        # Calculate deviations
        flagged = []
        for rec in tax_records:
            tps_dev = abs(rec['tps_rate'] - statutory_tps)
            tvq_dev = abs(rec['tvq_rate'] - statutory_tvq)
            tvh_dev = abs(rec['tvh_rate'] - statutory_tvh)

            # Flag if > 0.5% deviation
            if tps_dev > 0.5 or tvq_dev > 0.5 or tvh_dev > 0.5:
                flagged.append({
                    'date': rec['date'].isoformat(),
                    'tps_rate': round(rec['tps_rate'], 2),
                    'tps_deviation': round(tps_dev, 2),
                    'tvq_rate': round(rec['tvq_rate'], 2),
                    'tvq_deviation': round(tvq_dev, 2),
                    'tvh_rate': round(rec['tvh_rate'], 2),
                    'tvh_deviation': round(tvh_dev, 2),
                })

        # Monthly trend of effective rates
        by_month = defaultdict(list)
        for rec in tax_records:
            by_month[rec['date'].month].append(rec)

        months_fr = {
            1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Aoû', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }

        monthly_trend = []
        for mo in range(1, 13):
            recs = by_month.get(mo, [])
            if recs:
                n = len(recs)
                avg_tps = sum(r['tps_rate'] for r in recs) / n
                avg_tvq = sum(r['tvq_rate'] for r in recs) / n
                avg_tvh = sum(r['tvh_rate'] for r in recs) / n
                monthly_trend.append({
                    'month': months_fr.get(mo, str(mo)),
                    'avg_tps_rate': round(avg_tps, 2),
                    'avg_tvq_rate': round(avg_tvq, 2),
                    'avg_tvh_rate': round(avg_tvh, 2),
                })

        return {
            'has_data': True,
            'total_records': len(tax_records),
            'flagged_anomalies': len(flagged),
            'anomaly_pct': round(len(flagged) / len(tax_records) * 100, 1) if tax_records else 0,
            'flagged_dates': flagged[:10],  # Top 10 anomalies
            'monthly_trend': monthly_trend,
        }

    # ==========================================================================
    # PRICE ELASTICITY OF DEMAND
    # ==========================================================================
    def _price_elasticity(self):
        """Calculate price elasticity using ADR vs occupancy regression.

        Returns: elasticity coefficient, revenue-maximizing ADR, current vs optimal ADR gap,
        estimated revenue gain.
        """
        adrs = []
        occs = []

        for m in self.metrics:
            if m.adr > 0:
                adrs.append(m.adr)
                occs.append(m.occupancy_rate)

        if len(adrs) < 10:
            return {'sufficient_data': False}

        # Simple linear regression: occupancy = a + b*adr
        n = len(adrs)
        mean_adr = sum(adrs) / n
        mean_occ = sum(occs) / n

        numerator = sum((adrs[i] - mean_adr) * (occs[i] - mean_occ) for i in range(n))
        denominator = sum((adrs[i] - mean_adr) ** 2 for i in range(n))

        if denominator == 0:
            return {'sufficient_data': False}

        elasticity_coeff = numerator / denominator  # Change in occupancy per dollar ADR change
        intercept = mean_occ - elasticity_coeff * mean_adr

        # Find revenue-maximizing ADR using the regression
        # Revenue = ADR * Occupancy_Rate * Rooms_Available
        # Assume constant rooms (say 200 average)
        avg_rooms = sum(m.rooms_available for m in self.metrics) / self.n if self.n > 0 else 100

        # To maximize: d(Revenue)/d(ADR) = 0
        # Revenue = ADR * (intercept + elasticity_coeff * ADR) * rooms
        # d(Revenue)/d(ADR) = (intercept + elasticity_coeff * ADR) + elasticity_coeff * ADR
        #                   = intercept + 2*elasticity_coeff*ADR = 0
        # Optimal ADR = -intercept / (2 * elasticity_coeff)

        if elasticity_coeff >= 0:
            # No downward demand curve, use current ADR
            optimal_adr = mean_adr
        else:
            optimal_adr = -intercept / (2 * elasticity_coeff)

        # Current metrics
        current_adr = mean_adr
        current_occ = mean_occ
        current_revenue = current_adr * (current_occ / 100) * avg_rooms

        # Optimal metrics
        optimal_occ = max(0, min(100, intercept + elasticity_coeff * optimal_adr))
        optimal_revenue = optimal_adr * (optimal_occ / 100) * avg_rooms

        adr_gap = optimal_adr - current_adr
        estimated_daily_gain = optimal_revenue - current_revenue
        estimated_annual_gain = estimated_daily_gain * 365

        return {
            'sufficient_data': True,
            'elasticity_coefficient': round(elasticity_coeff, 4),
            'current_adr': round(current_adr, 2),
            'current_occupancy': round(current_occ, 1),
            'optimal_adr': round(optimal_adr, 2),
            'optimal_occupancy': round(optimal_occ, 1),
            'adr_gap': round(adr_gap, 2),
            'estimated_daily_revenue_gain': round(estimated_daily_gain, 0),
            'estimated_annual_revenue_gain': round(estimated_annual_gain, 0),
        }

    # ==========================================================================
    # DAY OF WEEK REVENUE ANALYSIS
    # ==========================================================================
    def _day_of_week_revenue(self):
        """Revenue breakdown by day of week (Mon-Sun).

        Returns: each day's avg revenue, avg occupancy, avg ADR, avg F&B. Identify best/worst days.
        """
        dow_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        by_dow = defaultdict(list)

        for m in self.metrics:
            dow = m.date.weekday()  # 0=Mon, 6=Sun
            by_dow[dow].append(m)

        result = []
        for dow in range(7):
            days = by_dow.get(dow, [])
            if not days:
                continue

            n = len(days)
            result.append({
                'day_name': dow_names[dow],
                'day_number': dow,
                'days_count': n,
                'avg_revenue': round(sum(d.total_revenue for d in days) / n, 0),
                'avg_occupancy': round(sum(d.occupancy_rate for d in days) / n, 1),
                'avg_adr': round(sum(d.adr for d in days) / n, 2),
                'avg_fb_revenue': round(sum(d.fb_revenue for d in days) / n, 0),
            })

        # Find best and worst
        sorted_by_revenue = sorted(result, key=lambda x: x['avg_revenue'], reverse=True)
        best_day = sorted_by_revenue[0] if sorted_by_revenue else None
        worst_day = sorted_by_revenue[-1] if sorted_by_revenue else None

        return {
            'by_day': result,
            'best_day': best_day,
            'worst_day': worst_day,
        }

    # ==========================================================================
    # OPERATING REGIMES (K-MEANS CLUSTERING)
    # ==========================================================================
    def _operating_regimes(self):
        """K-means clustering (3 clusters) on daily metrics.

        Returns: cluster profiles (mean metrics per cluster), day counts, characteristics.
        """
        if self.n < 15:
            return {'sufficient_data': False}

        # Prepare features for clustering
        features = []
        for m in self.metrics:
            features.append([
                m.occupancy_rate,
                m.adr,
                m.total_revenue,
                m.fb_revenue,
            ])

        features_array = np.array(features)

        try:
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            labels = kmeans.fit_predict(features_array)
        except Exception as e:
            logger.warning(f"K-means clustering failed: {e}")
            return {'sufficient_data': False}

        # Analyze clusters
        clusters = defaultdict(list)
        for i, label in enumerate(labels):
            clusters[label].append(self.metrics[i])

        result = []
        for cluster_id in sorted(clusters.keys()):
            days = clusters[cluster_id]
            n = len(days)

            result.append({
                'cluster_id': int(cluster_id),
                'days_count': n,
                'days_pct': round(n / self.n * 100, 1),
                'avg_occupancy': round(sum(d.occupancy_rate for d in days) / n, 1),
                'avg_adr': round(sum(d.adr for d in days) / n, 2),
                'avg_total_revenue': round(sum(d.total_revenue for d in days) / n, 0),
                'avg_fb_revenue': round(sum(d.fb_revenue for d in days) / n, 0),
            })

        # Characterize clusters by occupancy levels
        result.sort(key=lambda x: x['avg_occupancy'])
        characteristics = []
        for i, cluster in enumerate(result):
            if i == 0:
                char = 'Low-occupancy regime (weak demand)'
            elif i == 1:
                char = 'Mid-range operating regime (steady state)'
            else:
                char = 'High-occupancy regime (peak demand)'
            characteristics.append(char)

        return {
            'sufficient_data': True,
            'clusters': result,
            'characteristics': characteristics,
        }

    # ==========================================================================
    # VARIANCE DECOMPOSITION (Revenue Drivers)
    # ==========================================================================
    def _variance_decomposition(self):
        """Calculate what % of total revenue variance is explained by each factor.

        Uses correlation analysis. Returns: contribution percentages for occupancy, ADR,
        F&B per room, clients.
        """
        if self.n < 10:
            return {'sufficient_data': False}

        total_revenues = [m.total_revenue for m in self.metrics]
        occupancies = [m.occupancy_rate for m in self.metrics]
        adrs = [m.adr for m in self.metrics]
        fb_per_rooms = [m.fb_revenue / m.total_rooms_sold if m.total_rooms_sold > 0 else 0
                       for m in self.metrics]
        clients = [m.nb_clients for m in self.metrics]

        # Calculate variance of total revenue
        mean_rev = sum(total_revenues) / len(total_revenues)
        total_variance = sum((r - mean_rev) ** 2 for r in total_revenues) / len(total_revenues)

        if total_variance == 0:
            return {'sufficient_data': False}

        # Correlation with each factor
        corr_occ = self._pearson(occupancies, total_revenues)
        corr_adr = self._pearson(adrs, total_revenues)
        corr_fb_per_room = self._pearson(fb_per_rooms, total_revenues)
        corr_clients = self._pearson(clients, total_revenues)

        # R-squared (coefficient of determination)
        r2_occ = corr_occ ** 2 if corr_occ != 0 else 0
        r2_adr = corr_adr ** 2 if corr_adr != 0 else 0
        r2_fb = corr_fb_per_room ** 2 if corr_fb_per_room != 0 else 0
        r2_clients = corr_clients ** 2 if corr_clients != 0 else 0

        # Normalize to percentages (proportional contribution)
        total_r2 = r2_occ + r2_adr + r2_fb + r2_clients
        if total_r2 == 0:
            total_r2 = 1  # Avoid division by zero

        return {
            'sufficient_data': True,
            'occupancy_contribution_pct': round(r2_occ / total_r2 * 100, 1),
            'adr_contribution_pct': round(r2_adr / total_r2 * 100, 1),
            'fb_per_room_contribution_pct': round(r2_fb / total_r2 * 100, 1),
            'clients_contribution_pct': round(r2_clients / total_r2 * 100, 1),
            'occupancy_correlation': round(corr_occ, 3),
            'adr_correlation': round(corr_adr, 3),
            'fb_per_room_correlation': round(corr_fb_per_room, 3),
            'clients_correlation': round(corr_clients, 3),
        }

    # ==========================================================================
    # F&B CONVERSION FUNNEL (Piazza Revenue per Client)
    # ==========================================================================
    def _fb_conversion_funnel(self):
        """F&B capture metrics: Piazza revenue per client (dining conversion proxy).

        Returns: current rate, historical trend, comparison.
        """
        by_quarter = defaultdict(list)
        piazza_per_client_list = []

        for m in self.metrics:
            if m.nb_clients <= 0:
                continue

            piazza_per_client = m.piazza_total / m.nb_clients if m.nb_clients > 0 else 0
            piazza_per_client_list.append(piazza_per_client)

            # Determine quarter (simplified: Q1=1-3, Q2=4-6, Q3=7-9, Q4=10-12)
            quarter = (m.month - 1) // 3 + 1
            quarter_key = f"{m.year}Q{quarter}"
            by_quarter[quarter_key].append(piazza_per_client)

        if not piazza_per_client_list:
            return {'sufficient_data': False}

        # Current metrics
        current_rate = sum(piazza_per_client_list) / len(piazza_per_client_list)
        max_rate = max(piazza_per_client_list)
        min_rate = min(piazza_per_client_list)

        # Quarterly trend
        quarterly_trend = []
        for quarter_key in sorted(by_quarter.keys()):
            values = by_quarter[quarter_key]
            quarterly_trend.append({
                'period': quarter_key,
                'avg_piazza_per_client': round(sum(values) / len(values), 2),
                'days_count': len(values),
            })

        # Trend direction (comparing first vs last quarter)
        trend_direction = 'stable'
        if len(quarterly_trend) >= 2:
            first_q = quarterly_trend[0]['avg_piazza_per_client']
            last_q = quarterly_trend[-1]['avg_piazza_per_client']
            if last_q > first_q * 1.05:
                trend_direction = 'improving'
            elif last_q < first_q * 0.95:
                trend_direction = 'declining'

        return {
            'sufficient_data': True,
            'current_piazza_per_client': round(current_rate, 2),
            'best_period_rate': round(max_rate, 2),
            'worst_period_rate': round(min_rate, 2),
            'range': round(max_rate - min_rate, 2),
            'trend_direction': trend_direction,
            'quarterly_trend': quarterly_trend,
        }

    # ==========================================================================
    # MARGINAL ROOM REVENUE BY OCCUPANCY BAND
    # ==========================================================================
    def _marginal_room_revenue(self):
        """Total incremental revenue from selling one more room at different occupancy bands.

        Includes room + F&B + ancillary.
        Returns: per-band marginal revenue.
        """
        bands = {
            '50-60%': {'min': 50, 'max': 60, 'days': []},
            '60-70%': {'min': 60, 'max': 70, 'days': []},
            '70-80%': {'min': 70, 'max': 80, 'days': []},
            '80-90%': {'min': 80, 'max': 90, 'days': []},
            '90-100%': {'min': 90, 'max': 101, 'days': []},
        }

        for m in self.metrics:
            occ = m.occupancy_rate
            for band_key, band in bands.items():
                if band['min'] <= occ < band['max']:
                    band['days'].append(m)
                    break

        result = []
        for band_key, band in bands.items():
            days = band['days']
            if not days:
                continue

            n = len(days)

            # Calculate marginal revenue per additional room
            avg_adr = sum(d.adr for d in days) / n
            avg_fb_per_room = sum(d.fb_revenue / d.total_rooms_sold if d.total_rooms_sold > 0 else 0
                                 for d in days) / n
            avg_other_per_room = sum((d.total_revenue - d.room_revenue - d.fb_revenue) / d.total_rooms_sold
                                    if d.total_rooms_sold > 0 else 0 for d in days) / n

            marginal_revenue_per_room = avg_adr + avg_fb_per_room + avg_other_per_room
            annual_marginal_revenue = marginal_revenue_per_room * 365

            result.append({
                'occupancy_band': band_key,
                'days_count': n,
                'avg_adr': round(avg_adr, 2),
                'avg_fb_per_room': round(avg_fb_per_room, 2),
                'avg_ancillary_per_room': round(avg_other_per_room, 2),
                'marginal_revenue_per_room': round(marginal_revenue_per_room, 2),
                'estimated_annual_per_room': round(annual_marginal_revenue, 0),
            })

        return result

    # ==========================================================================
    # ADR COMPRESSION ANALYSIS (Yield Management)
    # ==========================================================================
    def _adr_compression(self):
        """Compare ADR on sold-out nights vs average vs weak nights.

        Measure yield management effectiveness.
        Returns: ADR by band, premium percentages, benchmark comparison.
        """
        high_occ = []  # >95% occupancy
        mid_occ = []   # 70-95%
        low_occ = []   # <70%

        for m in self.metrics:
            if m.occupancy_rate > 95:
                high_occ.append(m)
            elif m.occupancy_rate >= 70:
                mid_occ.append(m)
            else:
                low_occ.append(m)

        def calc_metrics(days):
            if not days:
                return {}
            n = len(days)
            return {
                'days': n,
                'avg_adr': round(sum(d.adr for d in days) / n, 2),
                'avg_occupancy': round(sum(d.occupancy_rate for d in days) / n, 1),
                'std_adr': round((sum((d.adr - sum(d.adr for d in days) / n) ** 2 for d in days) / n) ** 0.5, 2),
            }

        high = calc_metrics(high_occ)
        mid = calc_metrics(mid_occ)
        low = calc_metrics(low_occ)

        # Premium calculations
        high_premium_vs_mid = ((high.get('avg_adr', 0) - mid.get('avg_adr', 0)) / mid.get('avg_adr', 1) * 100) if mid.get('avg_adr', 0) > 0 else 0
        high_premium_vs_low = ((high.get('avg_adr', 0) - low.get('avg_adr', 0)) / low.get('avg_adr', 1) * 100) if low.get('avg_adr', 0) > 0 else 0

        return {
            'high_occupancy_95plus': high,
            'mid_occupancy_70_95': mid,
            'low_occupancy_below70': low,
            'premium_high_vs_mid_pct': round(high_premium_vs_mid, 1),
            'premium_high_vs_low_pct': round(high_premium_vs_low, 1),
            'yield_management_strength': 'strong' if high_premium_vs_mid > 10 else 'moderate' if high_premium_vs_mid > 5 else 'weak',
        }

    # ==========================================================================
    # PARETO ANALYSIS (Revenue Concentration)
    # ==========================================================================
    def _pareto_analysis(self):
        """What % of revenue comes from top 10%, 20%, 50% of days?

        Returns: cumulative percentages, Gini coefficient, characterization of top days.
        """
        if self.n < 10:
            return {'sufficient_data': False}

        # Sort by revenue descending
        sorted_by_revenue = sorted(self.metrics, key=lambda m: m.total_revenue, reverse=True)
        total_revenue = sum(m.total_revenue for m in self.metrics)

        if total_revenue == 0:
            return {'sufficient_data': False}

        # Cumulative analysis
        cumulative_pct = []
        cumulative_revenue = 0
        for i, m in enumerate(sorted_by_revenue):
            cumulative_revenue += m.total_revenue
            cumulative_pct.append(((i + 1) / self.n * 100, cumulative_revenue / total_revenue * 100))

        # Find key thresholds
        top_10_pct_days = max(1, self.n // 10)
        top_20_pct_days = max(1, self.n // 5)
        top_50_pct_days = max(1, self.n // 2)

        top_10_revenue_contrib = sum(sorted_by_revenue[i].total_revenue for i in range(top_10_pct_days)) / total_revenue * 100
        top_20_revenue_contrib = sum(sorted_by_revenue[i].total_revenue for i in range(top_20_pct_days)) / total_revenue * 100
        top_50_revenue_contrib = sum(sorted_by_revenue[i].total_revenue for i in range(top_50_pct_days)) / total_revenue * 100

        # Gini coefficient (measure of inequality)
        # G = (2 * sum(i * revenue_i)) / (n * sum(revenue_i)) - (n+1)/n
        sorted_revenues = [m.total_revenue for m in sorted_by_revenue]
        gini_numerator = sum((i + 1) * sorted_revenues[i] for i in range(len(sorted_revenues)))
        gini = (2 * gini_numerator) / (self.n * total_revenue) - (self.n + 1) / self.n

        # Characterize top days
        top_10_days = sorted_by_revenue[:top_10_pct_days]
        avg_occ_top = sum(d.occupancy_rate for d in top_10_days) / len(top_10_days) if top_10_days else 0
        avg_adr_top = sum(d.adr for d in top_10_days) / len(top_10_days) if top_10_days else 0

        return {
            'sufficient_data': True,
            'top_10_pct_days_count': top_10_pct_days,
            'top_10_pct_revenue_contrib': round(top_10_revenue_contrib, 1),
            'top_20_pct_days_count': top_20_pct_days,
            'top_20_pct_revenue_contrib': round(top_20_revenue_contrib, 1),
            'top_50_pct_days_count': top_50_pct_days,
            'top_50_pct_revenue_contrib': round(top_50_revenue_contrib, 1),
            'gini_coefficient': round(gini, 3),
            'top_10_avg_occupancy': round(avg_occ_top, 1),
            'top_10_avg_adr': round(avg_adr_top, 2),
            'concentration_level': 'high' if gini > 0.3 else 'moderate' if gini > 0.15 else 'low',
        }

    # ==========================================================================
    # STAFFING OPTIMIZATION
    # ==========================================================================
    def _staffing_optimization(self):
        """Analyze staffing levels by occupancy regime and estimate cost savings.

        Classifies days into 3 occupancy regimes (low <70%, normal 70-85%, peak >85%)
        and calculates optimal staffing for each based on industry ratios.
        Returns: regimes with staffing breakdown, actual vs optimal, annual savings potential.
        """
        if self.n < 30:
            return {'sufficient_data': False}

        # Classify days into regimes
        low_occ_days = [m for m in self.metrics if m.occupancy_rate < 70]
        normal_occ_days = [m for m in self.metrics if 70 <= m.occupancy_rate <= 85]
        peak_occ_days = [m for m in self.metrics if m.occupancy_rate > 85]

        def analyze_regime(days, regime_name):
            if not days:
                return None

            n = len(days)
            avg_rooms = sum(d.total_rooms_sold for d in days) / n
            avg_fb = sum(d.fb_revenue for d in days) / n
            avg_revenue = sum(d.total_revenue for d in days) / n
            avg_clients = sum(d.nb_clients for d in days) / n
            avg_banquet = sum(d.banquet_total for d in days) / n

            # Calculate optimal staffing per industry ratios
            housekeeping_hours = max(1, avg_rooms * 0.5)  # 0.5h per room sold
            reception_agents = max(1, int(avg_rooms / 50)) if avg_rooms > 0 else 1
            reception_hours = reception_agents * 8
            fb_service_hours = max(0, avg_fb / 100 * 1.2)  # fb_revenue/100 * 1.2 hours
            kitchen_hours = max(0, avg_fb / 150)  # fb_revenue/150 hours
            maintenance_hours = 16  # Fixed
            admin_hours = 16  # Fixed
            banquet_hours = max(0, avg_banquet / 200)  # banquet_revenue/200 hours
            laundry_hours = max(0, avg_rooms * 0.12)  # rooms * 0.12h

            total_daily_hours = (housekeeping_hours + reception_hours + fb_service_hours +
                                kitchen_hours + maintenance_hours + admin_hours +
                                banquet_hours + laundry_hours)

            return {
                'regime': regime_name,
                'days': n,
                'avg_occupancy': round(sum(d.occupancy_rate for d in days) / n, 1),
                'avg_revenue': round(avg_revenue, 0),
                'avg_rooms': round(avg_rooms, 1),
                'avg_clients': round(avg_clients, 1),
                'avg_fb_revenue': round(avg_fb, 0),
                'staffing': {
                    'housekeeping_hours': round(housekeeping_hours, 1),
                    'reception_hours': round(reception_hours, 1),
                    'fb_service_hours': round(fb_service_hours, 1),
                    'kitchen_hours': round(kitchen_hours, 1),
                    'maintenance_hours': round(maintenance_hours, 1),
                    'admin_hours': round(admin_hours, 1),
                    'banquet_hours': round(banquet_hours, 1),
                    'laundry_hours': round(laundry_hours, 1),
                    'total_daily_hours': round(total_daily_hours, 1),
                },
            }

        low_regime = analyze_regime(low_occ_days, 'low_occupancy')
        normal_regime = analyze_regime(normal_occ_days, 'normal_occupancy')
        peak_regime = analyze_regime(peak_occ_days, 'peak_occupancy')

        # Actual staffing: 667h/week = 95.3h/day average at $30.64/h
        weekly_actual_hours = 667
        daily_actual_hours = weekly_actual_hours / 7
        avg_hourly_rate = 30.64

        # Calculate savings potential for low-occupancy days
        savings_potential = 0
        low_optimal_hours = low_regime['staffing']['total_daily_hours'] if low_regime else daily_actual_hours
        if low_occ_days:
            hours_reduction = max(0, daily_actual_hours - low_optimal_hours)
            savings_potential = hours_reduction * avg_hourly_rate * len(low_occ_days)

        # Build recommendations
        recommendations = []
        if low_regime and low_regime['days'] > 0:
            savings_daily = (daily_actual_hours - low_optimal_hours) * avg_hourly_rate
            if savings_daily > 50:
                recommendations.append(
                    f"Les jours à faible taux d'occupation (<70%) peuvent réduire les heures de {daily_actual_hours:.1f}h à "
                    f"{low_optimal_hours:.1f}h par jour, économisant ${savings_daily:.0f}/jour ({low_regime['days']} jours)."
                )

        if peak_regime and peak_regime['days'] > 0:
            peak_hours = peak_regime['staffing']['total_daily_hours']
            if peak_hours > daily_actual_hours:
                additional_cost = (peak_hours - daily_actual_hours) * avg_hourly_rate * peak_regime['days']
                recommendations.append(
                    f"Les jours de pointe (>85% d'occupation) nécessitent {peak_hours:.1f}h/jour. "
                    f"Budgétisez {additional_cost:.0f}$ supplémentaires pour {peak_regime['days']} jours."
                )

        if normal_regime and normal_regime['days'] > 0:
            normal_hours = normal_regime['staffing']['total_daily_hours']
            if abs(normal_hours - daily_actual_hours) < 5:
                recommendations.append(
                    f"L'occupation normale (70-85%) aligne bien avec l'allocation actuelle de {daily_actual_hours:.1f}h/jour."
                )

        annual_savings = savings_potential * (365 / sum(1 for d in self.metrics if d.occupancy_rate < 70) * self.n / 365) if low_occ_days else 0

        return {
            'sufficient_data': True,
            'regimes': [r for r in [low_regime, normal_regime, peak_regime] if r],
            'weekly_actual_hours': round(weekly_actual_hours, 1),
            'daily_actual_hours': round(daily_actual_hours, 1),
            'avg_hourly_rate': round(avg_hourly_rate, 2),
            'estimated_annual_savings_potential': round(annual_savings, 0),
            'recommendations': recommendations,
        }

    # ==========================================================================
    # NARRATIVE STORY
    # ==========================================================================
    def _narrative_story(self):
        """Generate a comprehensive narrative "story" analyzing all key insights.

        Creates a structured narrative with headline, strengths, warnings, opportunities,
        staffing insights, and actionable recommendations. All text in French.
        """
        if self.n < 30:
            return {'has_insights': False}

        # Compute key metrics once
        avg_revenue = sum(m.total_revenue for m in self.metrics) / self.n
        avg_adr = sum(m.adr for m in self.metrics) / self.n
        avg_occ = sum(m.occupancy_rate for m in self.metrics) / self.n
        avg_revpor = sum(m.total_revenue / m.total_rooms_sold if m.total_rooms_sold > 0 else 0
                        for m in self.metrics) / self.n
        avg_fb_per_room = sum(m.fb_revenue / m.total_rooms_sold if m.total_rooms_sold > 0 else 0
                             for m in self.metrics) / self.n

        # Get insights for detailed analysis
        pricing = self._pricing_power()
        banquet = self._banquet_impact()
        elasticity = self._fb_elasticity()
        revpor_data = self._revpor()
        oos = self._oos_analysis()
        suite_premium = self._suite_premium()
        staffing = self._staffing_optimization()
        pareto = self._pareto_analysis()
        varcomp = self._variance_decomposition()
        adr_comp = self._adr_compression()

        # =====================================================================
        # 1. HEADLINE
        # =====================================================================
        headline = (
            f"Sheraton Laval génère {avg_revpor:.0f}$ par chambre occupée, "
            f"mais des opportunités clés pourraient ajouter {int(avg_revpor * 0.3)}$+ supplémentaires."
        )

        # =====================================================================
        # 2. STRENGTHS
        # =====================================================================
        strengths = []

        # Banquet effect
        if banquet.get('banquet_days', {}).get('days', 0) > 0:
            banquet_uplift = banquet.get('total_revenue_uplift_pct', 0)
            if banquet_uplift > 20:
                strengths.append({
                    'title': 'Effet Banquet Exceptionnel',
                    'detail': (
                        f"Les jours avec banquet génèrent +{banquet_uplift:.1f}% de revenus. "
                        f"Votre mix événementiel est un avantage compétitif majeur."
                    ),
                    'metric': f"+{banquet_uplift:.1f}%",
                    'type': 'positive',
                })

        # Pricing power
        if pricing.get('premium_pct', 0) > 5:
            strengths.append({
                'title': 'Levier de Prix en Haute Occupation',
                'detail': (
                    f"À forte occupation (>85%), vous commandez une prime de {pricing.get('premium_pct', 0):.1f}% "
                    f"vs occupation normale. Votre positionnement est valorisé."
                ),
                'metric': f"+{pricing.get('premium_pct', 0):.1f}%",
                'type': 'positive',
            })

        # F&B capture
        fb_cap = self._fb_capture()
        if fb_cap.get('vs_benchmark') == 'above':
            strengths.append({
                'title': 'Performance F&B au-dessus de la Moyenne',
                'detail': (
                    f"À {fb_cap.get('avg_fb_pct_of_room_rev', 0):.1f}% du revenu des chambres, "
                    f"votre capture F&B dépasse la norme {fb_cap.get('benchmark_range', '15-25%')}."
                ),
                'metric': f"{fb_cap.get('avg_fb_pct_of_room_rev', 0):.1f}%",
                'type': 'positive',
            })

        # Yield management
        if adr_comp.get('yield_management_strength') == 'strong':
            premium = adr_comp.get('premium_high_vs_low_pct', 0)
            strengths.append({
                'title': 'Yield Management Efficace',
                'detail': (
                    f"Votre ADR aux jours pleins dépasse les jours faibles de {premium:.1f}%. "
                    f"Votre stratégie de prix capture bien la demande."
                ),
                'metric': f"+{premium:.1f}%",
                'type': 'positive',
            })

        # =====================================================================
        # 3. WARNINGS
        # =====================================================================
        warnings = []

        # F&B elasticity
        if elasticity.get('elasticity') == 'declining':
            change = elasticity.get('change_pct', 0)
            warnings.append({
                'title': 'Élasticité F&B Négative',
                'detail': (
                    f"Quand l'hôtel est plein, les clients dépensent {change:.1f}% moins en F&B par personne. "
                    f"C'est un risque pour la marge brute à forte occupation."
                ),
                'metric': f"{change:.1f}%",
                'type': 'negative',
            })

        # OOS impact
        if oos.get('avg_oos_per_day', 0) > 1:
            oos_cost = oos.get('annual_cost', 0)
            if oos_cost > 50000:
                warnings.append({
                    'title': 'Impact Maintenance : Chambres Indisponibles',
                    'detail': (
                        f"En moyenne {oos.get('avg_oos_per_day', 0):.1f} chambres/jour hors service coûtent "
                        f"~{int(oos_cost):,}$ annuels en revenu perdu. Priorisez la maintenance préventive."
                    ),
                    'metric': f"-${int(oos_cost):,}",
                    'type': 'negative',
                })

        # Revenue concentration
        if pareto.get('concentration_level') == 'high':
            top_10_contrib = pareto.get('top_10_pct_revenue_contrib', 0)
            warnings.append({
                'title': 'Forte Concentration des Revenus',
                'detail': (
                    f"{top_10_contrib:.1f}% des revenus proviennent de 10% des jours. "
                    f"Réduisez cette dépendance aux pics saisonniers."
                ),
                'metric': f"{top_10_contrib:.1f}%",
                'type': 'negative',
            })

        # =====================================================================
        # 4. OPPORTUNITIES
        # =====================================================================
        opportunities = []

        # Pricing uplift
        uplift_10pct = pricing.get('uplift_10pct_annual', 0)
        if uplift_10pct > 50000:
            opportunities.append({
                'title': 'Augmentation ADR à Haute Occupation',
                'detail': (
                    f"Une augmentation de 10% du tarif les jours >85% occupation "
                    f"générerait ~{int(uplift_10pct):,}$ annuels supplémentaires."
                ),
                'value': int(uplift_10pct),
            })

        # F&B per guest
        low_fb = elasticity.get('bands', [{}])[0].get('fb_per_guest', 0)
        high_fb = elasticity.get('bands', [{}])[-1].get('fb_per_guest', 0) if len(elasticity.get('bands', [])) > 1 else low_fb
        if low_fb > 0:
            fb_uplift = (high_fb - low_fb) * sum(m.nb_clients for m in self.metrics) / self.n * 365
            if fb_uplift > 0:
                opportunities.append({
                    'title': 'Hausse F&B par Client',
                    'detail': (
                        f"Augmenter le F&B par client de {low_fb:.2f}$ à {high_fb:.2f}$ "
                        f"rapporterait ~{int(fb_uplift):,}$ annuels."
                    ),
                    'value': int(fb_uplift),
                })

        # Suite premium
        suite_uplift = suite_premium.get('estimated_uplift_10pct_annual', 0)
        if suite_uplift > 50000:
            opportunities.append({
                'title': 'Augmentation Suites de 10%',
                'detail': (
                    f"Vendre 10% plus de suites générerait ~{int(suite_uplift):,}$ annuels "
                    f"grâce à une prime ADR de {suite_premium.get('premium_adr_pct', 0):.1f}%."
                ),
                'value': int(suite_uplift),
            })

        # Occupancy improvement
        occ_gap = 100 - avg_occ
        if occ_gap > 5:
            occ_uplift = occ_gap * avg_revenue / 100 * 365
            opportunities.append({
                'title': 'Augmentation Occupation de 5%',
                'detail': (
                    f"Porter l'occupation de {avg_occ:.1f}% à {avg_occ + 5:.1f}% "
                    f"rapporterait ~{int(occ_uplift):,}$ annuels."
                ),
                'value': int(occ_uplift),
            })

        # Comp ROI
        comp_data = self._comp_roi()
        comp_uplift = comp_data.get('estimated_ancillary_from_comps_annual', 0)
        if comp_uplift > 20000:
            opportunities.append({
                'title': 'Optimisation Chambres Complimentaires',
                'detail': (
                    f"Les clients en comp génèrent {int(comp_data.get('estimated_ancillary_from_comps_annual', 0)):,}$ "
                    f"en revenus annexes. Utilisez les comps stratégiquement."
                ),
                'value': int(comp_uplift),
            })

        # =====================================================================
        # 5. STAFFING STORY
        # =====================================================================
        staffing_story = ""
        if staffing.get('sufficient_data'):
            regimes = staffing.get('regimes', [])
            if regimes:
                staffing_story = (
                    f"Votre allocation actuelle de {staffing.get('daily_actual_hours', 0):.1f}h/jour "
                    f"convient à l'occupation normale. Cependant, les jours faibles (<70%) pourraient "
                    f"réduire de {int((staffing.get('daily_actual_hours', 0) - regimes[0]['staffing']['total_daily_hours']) * 10) / 10:.1f}h/jour. "
                    f"Cela offre ~{int(staffing.get('estimated_annual_savings_potential', 0)):,}$ d'économies potentielles."
                )

        # =====================================================================
        # 6. TOMORROW ACTION
        # =====================================================================
        tomorrow_action = ""
        if avg_occ < 70:
            tomorrow_action = (
                "L'occupation est en baisse. Activez votre stratégie de distribution pour les OTA "
                "et vérifiez les taux concurrents."
            )
        elif avg_occ > 85:
            if avg_fb_per_room < 15:
                tomorrow_action = (
                    "L'hôtel est plein. Entraînez l'équipe F&B pour augmenter les ventes à chambre pleine "
                    "et contrer la baisse d'élasticité."
                )
            else:
                tomorrow_action = (
                    "Appliquez une augmentation ADR de 5-10% aux futures réservations de haute occupation."
                )
        else:
            tomorrow_action = (
                "Analysez les 10% des jours les plus rentables et répliquezz les conditions de succès."
            )

        # =====================================================================
        # 7. TOTAL OPPORTUNITY
        # =====================================================================
        total_opportunity = sum(opp.get('value', 0) for opp in opportunities)

        # =====================================================================
        # 8. KPI CONTEXT
        # =====================================================================
        kpi_context = {
            'RevPOR': (
                'Revenu total par chambre occupée. Cible: >370$. '
                f'Votre RevPOR: {avg_revpor:.0f}$. Inclut chambres + F&B + ancillaires.'
            ),
            'ADR': (
                'Prix moyen de la chambre. Cible: augmenter au-delà de la CPI. '
                f'Votre ADR: {avg_adr:.2f}$. Plus haut = levier de prix plus fort.'
            ),
            'Occupancy': (
                'Taux de remplissage. Cible: 75-85% pour stabilité. '
                f'Votre Occupancy: {avg_occ:.1f}%. Trop bas = appel marketing; trop haut = saturation.'
            ),
            'F&B per Room': (
                'Revenu F&B par chambre vendue. Cible: 15-25% du revenu-chambre. '
                f'Votre F&B per Room: {avg_fb_per_room:.2f}$. Reflète la capture du marché sur la propriété.'
            ),
            'Cash Variance': (
                'Écart entre caisse et système. Cible: <1%. '
                'Variances > 100$ suggèrent des erreurs de caisse ou oublis.'
            ),
        }

        return {
            'has_insights': True,
            'headline': headline,
            'strengths': strengths,
            'warnings': warnings,
            'opportunities': opportunities,
            'staffing_story': staffing_story,
            'tomorrow_action': tomorrow_action,
            'total_opportunity': round(total_opportunity, 0),
            'kpi_context': kpi_context,
        }

    # ==========================================================================
    # HELPERS
    # ==========================================================================
    @staticmethod
    def _pearson(x, y):
        """Simple Pearson correlation coefficient."""
        n = len(x)
        if n < 3:
            return 0
        mx = sum(x) / n
        my = sum(y) / n
        sx = (sum((xi - mx) ** 2 for xi in x) / n) ** 0.5
        sy = (sum((yi - my) ** 2 for yi in y) / n) ** 0.5
        if sx == 0 or sy == 0:
            return 0
        cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / n
        return cov / (sx * sy)
