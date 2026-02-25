"""
Forecasting Blueprint — InsightsEngine-powered demand, pricing, and revenue forecasts.

Exposes InsightsEngine ML capabilities to a user-facing dashboard with:
- Demand forecasting (30/60/90 day occupancy, ADR, RevPAR)
- Seasonal pattern analysis (by month, day of week)
- Anomaly detection
- Pricing power analysis
- Trend analysis (moving averages)
- Revenue concentration insights
"""

from flask import Blueprint, request, jsonify, render_template, session
from functools import wraps
from datetime import datetime, timedelta, date
from database.models import db, DailyJourMetrics
from utils.insights_engine import InsightsEngine, HAS_NUMPY
import logging

logger = logging.getLogger(__name__)

forecasting_bp = Blueprint('forecasting', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            from flask import redirect, url_for
            return redirect(url_for('auth_v2.login'))
        return f(*args, **kwargs)
    return decorated_function


def _load_metrics(days_back=365):
    """Load historical DailyJourMetrics from database."""
    cutoff_date = date.today() - timedelta(days=days_back)
    metrics = DailyJourMetrics.query.filter(
        DailyJourMetrics.date >= cutoff_date
    ).order_by(DailyJourMetrics.date).all()
    return metrics


# ==============================================================================
# MAIN PAGE
# ==============================================================================

@forecasting_bp.route('/previsions/')
@forecasting_bp.route('/previsions')
@login_required
def forecasting_page():
    """Main forecasting dashboard page."""
    return render_template('forecasting.html')


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@forecasting_bp.route('/api/previsions/forecast', methods=['GET'])
@login_required
def api_forecast():
    """
    30/60/90 day demand forecast: occupancy, ADR, RevPAR.
    Returns:
        {
            'success': bool,
            'has_insights': bool,
            'reason': str (if not has_insights),
            'forecast_30': {'occupancy_pct': float, 'adr': float, 'revpar': float, 'confidence': float},
            'forecast_60': {...},
            'forecast_90': {...},
            'historical_avg': {...}
        }
    """
    metrics = _load_metrics(days_back=365)

    if len(metrics) < 30:
        return jsonify({
            'success': False,
            'has_insights': False,
            'reason': 'Minimum 30 jours de données requis'
        }), 400

    try:
        engine = InsightsEngine(metrics)
        if not HAS_NUMPY:
            return jsonify({
                'success': False,
                'has_insights': False,
                'reason': 'Installez numpy pour activer les prévisions'
            }), 400

        # Get demand forecast from InsightsEngine
        forecast = engine._demand_forecast()

        # Historical average for comparison
        if metrics:
            hist_avg = {
                'occupancy_pct': round(sum(m.occupancy_rate for m in metrics) / len(metrics), 1),
                'adr': round(sum(m.adr for m in metrics) / len(metrics), 2),
                'revpar': round(sum(m.revpar for m in metrics) / len(metrics), 2),
            }
        else:
            hist_avg = {'occupancy_pct': 0, 'adr': 0, 'revpar': 0}

        return jsonify({
            'success': True,
            'has_insights': True,
            'forecast_30': forecast.get('forecast_30', {}),
            'forecast_60': forecast.get('forecast_60', {}),
            'forecast_90': forecast.get('forecast_90', {}),
            'historical_avg': hist_avg,
            'raw_forecast': forecast
        })
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return jsonify({
            'success': False,
            'has_insights': False,
            'reason': f'Erreur: {str(e)}'
        }), 500


@forecasting_bp.route('/api/previsions/seasonality', methods=['GET'])
@login_required
def api_seasonality():
    """
    Seasonal patterns: revenue by month, occupancy by day of week.
    Returns:
        {
            'success': bool,
            'monthly': [{month, label, avg_revenue, avg_occ, avg_adr, avg_revpar}],
            'day_of_week': [{dow, label, avg_revenue, avg_occ}],
            'best_month': {...},
            'worst_month': {...},
            'best_dow': {...},
            'worst_dow': {...}
        }
    """
    metrics = _load_metrics(days_back=365)

    if len(metrics) < 30:
        return jsonify({
            'success': False,
            'reason': 'Minimum 30 jours de données requis'
        }), 400

    try:
        engine = InsightsEngine(metrics)
        if not HAS_NUMPY:
            return jsonify({
                'success': False,
                'reason': 'Installez numpy pour activer les prévisions'
            }), 400

        seasonality = engine._seasonality()
        dow_revenue = engine._day_of_week_revenue()

        return jsonify({
            'success': True,
            'seasonality': seasonality,
            'day_of_week_revenue': dow_revenue
        })
    except Exception as e:
        logger.error(f"Seasonality error: {e}")
        return jsonify({
            'success': False,
            'reason': f'Erreur: {str(e)}'
        }), 500


@forecasting_bp.route('/api/previsions/anomalies', methods=['GET'])
@login_required
def api_anomalies():
    """
    Detected anomalies in revenue, occupancy, etc.
    Returns:
        {
            'success': bool,
            'anomalies': [
                {
                    'date': str,
                    'metric': str,
                    'value': float,
                    'expected': float,
                    'deviation_pct': float,
                    'severity': 'info'|'warning'|'critical'
                }
            ]
        }
    """
    metrics = _load_metrics(days_back=365)

    if len(metrics) < 30:
        return jsonify({
            'success': False,
            'anomalies': [],
            'reason': 'Minimum 30 jours de données requis'
        }), 400

    try:
        engine = InsightsEngine(metrics)
        if not HAS_NUMPY:
            return jsonify({
                'success': False,
                'anomalies': [],
                'reason': 'Installez numpy pour activer les prévisions'
            }), 400

        anomalies = engine._anomalies()

        return jsonify({
            'success': True,
            'anomalies': anomalies.get('anomalies', []),
            'raw': anomalies
        })
    except Exception as e:
        logger.error(f"Anomalies error: {e}")
        return jsonify({
            'success': False,
            'anomalies': [],
            'reason': f'Erreur: {str(e)}'
        }), 500


@forecasting_bp.route('/api/previsions/pricing', methods=['GET'])
@login_required
def api_pricing():
    """
    Pricing power analysis: occupancy bands vs ADR.
    Returns:
        {
            'success': bool,
            'pricing_power': {
                'low': {'label': '<60%', 'days': int, 'avg_adr': float, 'avg_occ': float, 'avg_revenue': float},
                'mid': {...},
                'high': {...},
                'premium_pct': float,
                'uplift_10pct_annual': float
            }
        }
    """
    metrics = _load_metrics(days_back=365)

    if len(metrics) < 30:
        return jsonify({
            'success': False,
            'reason': 'Minimum 30 jours de données requis'
        }), 400

    try:
        engine = InsightsEngine(metrics)
        if not HAS_NUMPY:
            return jsonify({
                'success': False,
                'reason': 'Installez numpy pour activer les prévisions'
            }), 400

        pricing = engine._pricing_power()

        return jsonify({
            'success': True,
            'pricing_power': pricing
        })
    except Exception as e:
        logger.error(f"Pricing error: {e}")
        return jsonify({
            'success': False,
            'reason': f'Erreur: {str(e)}'
        }), 500


@forecasting_bp.route('/api/previsions/trends', methods=['GET'])
@login_required
def api_trends():
    """
    Trend analysis: 7/30/90-day moving averages + trend direction.
    Returns:
        {
            'success': bool,
            'moving_averages': {
                'ma7': [{'date': str, 'revpar': float}],
                'ma30': [...],
                'ma90': [...]
            },
            'trend': {
                'direction': 'up'|'down'|'stable',
                'pct_change_30d': float,
                'momentum': 'accelerating'|'decelerating'|'stable'
            }
        }
    """
    metrics = _load_metrics(days_back=365)

    if len(metrics) < 90:
        return jsonify({
            'success': False,
            'reason': 'Minimum 90 jours de données requis'
        }), 400

    try:
        engine = InsightsEngine(metrics)
        if not HAS_NUMPY:
            return jsonify({
                'success': False,
                'reason': 'Installez numpy pour activer les prévisions'
            }), 400

        ma_data = engine._moving_averages()

        # Calculate trend direction
        if len(metrics) >= 60:
            last_30_avg = sum(m.revpar for m in metrics[-30:]) / 30
            prev_30_avg = sum(m.revpar for m in metrics[-60:-30]) / 30
            pct_change = ((last_30_avg - prev_30_avg) / prev_30_avg * 100) if prev_30_avg > 0 else 0
            if abs(pct_change) < 2:
                direction = 'stable'
            elif pct_change > 0:
                direction = 'up'
            else:
                direction = 'down'
        else:
            pct_change = 0
            direction = 'unknown'

        # Momentum (acceleration)
        if len(metrics) >= 90:
            ma30_now = sum(m.revpar for m in metrics[-30:]) / 30
            ma30_mid = sum(m.revpar for m in metrics[-60:-30]) / 30
            ma30_old = sum(m.revpar for m in metrics[-90:-60]) / 30

            accel_now = ma30_now - ma30_mid
            accel_mid = ma30_mid - ma30_old

            if accel_now > accel_mid * 1.1:
                momentum = 'accelerating'
            elif accel_now < accel_mid * 0.9:
                momentum = 'decelerating'
            else:
                momentum = 'stable'
        else:
            momentum = 'unknown'

        return jsonify({
            'success': True,
            'moving_averages': ma_data.get('moving_averages', {}),
            'trend': {
                'direction': direction,
                'pct_change_30d': round(pct_change, 1),
                'momentum': momentum
            },
            'raw': ma_data
        })
    except Exception as e:
        logger.error(f"Trends error: {e}")
        return jsonify({
            'success': False,
            'reason': f'Erreur: {str(e)}'
        }), 500


@forecasting_bp.route('/api/previsions/insights', methods=['GET'])
@login_required
def api_all_insights():
    """
    All InsightsEngine insights combined (used for narrative).
    Returns all insights as a single JSON object.
    """
    metrics = _load_metrics(days_back=365)

    if len(metrics) < 30:
        return jsonify({
            'success': False,
            'reason': 'Minimum 30 jours de données requis',
            'has_insights': False
        }), 400

    try:
        engine = InsightsEngine(metrics)
        if not HAS_NUMPY:
            return jsonify({
                'success': False,
                'reason': 'Installez numpy pour activer les prévisions',
                'has_insights': False
            }), 400

        all_insights = engine.get_all_insights()

        return jsonify({
            'success': True,
            'insights': all_insights
        })
    except Exception as e:
        logger.error(f"All insights error: {e}")
        return jsonify({
            'success': False,
            'reason': f'Erreur: {str(e)}',
            'has_insights': False
        }), 500
