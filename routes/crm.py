"""
CRM Blueprint — Hotel Business Intelligence Dashboard.

Power BI-style analytics combining:
- RJ Jour sheet data (117 cols × 31 days) for revenue, F&B, rooms, payments, taxes
- Historical data from DailyJourMetrics (multi-year)
- Staff/personnel management from SETD
- Variance tracking per employee
- Anomaly detection and actionable insights
"""

from flask import Blueprint, request, jsonify, render_template, session
from datetime import datetime, timedelta, date
from database.models import (
    db, User, Shift, TaskCompletion, Task,
    DailyReport, VarianceRecord, CashReconciliation, MonthEndChecklist,
    DailyJourMetrics
)
from sqlalchemy import func, desc, or_
from utils.auth_decorators import login_required
from utils.csrf import csrf_protect
import json
import io
import os
import logging

logger = logging.getLogger(__name__)

crm_bp = Blueprint('crm', __name__)


def _parse_date(s):
    """Parse YYYY-MM-DD string to date, or None."""
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


# ==============================================================================
# MAIN PAGE
# ==============================================================================

@crm_bp.route('/crm')
@login_required
def crm_page():
    active_tab = request.args.get('tab', 'overview')
    valid_tabs = ['overview', 'revenue', 'fb', 'labor', 'cash', 'payments', 'pnl']
    if active_tab not in valid_tabs:
        active_tab = 'overview'
    return render_template('crm.html', active_tab=active_tab)


# ==============================================================================
# ANALYTICS ENGINE — Supports both in-memory RJ and historical DB
# ==============================================================================

def _get_analytics(allow_db=True):
    """
    Get analytics engine based on request parameters.

    Priority:
    1. If start_date & end_date params → HistoricalAnalytics (DB)
    2. If RJ file in memory → JourAnalytics (in-memory)
    3. If DB has data → HistoricalAnalytics (last 30 days)
    4. None
    """
    from utils.analytics import JourAnalytics, HistoricalAnalytics

    # Check for explicit date range params
    start = _parse_date(request.args.get('start_date'))
    end = _parse_date(request.args.get('end_date'))

    if start and end and allow_db:
        return HistoricalAnalytics(start, end), 'db'

    # Try in-memory RJ file
    session_id = session.get('user_session_id', 'default')
    try:
        from routes.audit.rj_core import RJ_FILES
        if session_id in RJ_FILES:
            file_bytes = RJ_FILES[session_id]
            file_bytes.seek(0)
            return JourAnalytics(file_bytes.read()), 'rj'
    except (ImportError, KeyError):
        pass

    # Fallback: DB data (last 30 days)
    if allow_db:
        total = DailyJourMetrics.query.count()
        if total > 0:
            max_date = db.session.query(func.max(DailyJourMetrics.date)).scalar()
            min_start = max_date - timedelta(days=30)
            return HistoricalAnalytics(min_start, max_date), 'db'

    return None, None


# ==============================================================================
# BI ANALYTICS ENDPOINTS — All support ?start_date=&end_date= params
# ==============================================================================

@crm_bp.route('/api/crm/dashboard')
@login_required
def dashboard_data():
    """Full BI dashboard data — single call."""
    analytics, source = _get_analytics()
    if analytics is None or not analytics.has_data():
        return jsonify({
            'success': True,
            'has_data': False,
            'message': 'Aucune donnée disponible. Uploadez un RJ ou importez des données historiques.'
        })

    result = analytics.get_full_dashboard()

    # Add comparison data if requested
    compare = request.args.get('compare')
    if compare == 'yoy' and source == 'db' and hasattr(analytics, 'get_yoy_comparison'):
        result['yoy'] = analytics.get_yoy_comparison()

    # Add monthly summary for multi-year view
    if source == 'db' and hasattr(analytics, 'get_monthly_summary'):
        result['monthly_summary'] = analytics.get_monthly_summary()

    # Add data status
    from utils.jour_importer import JourImporter
    result['data_status'] = JourImporter.get_data_status()

    return jsonify({
        'success': True,
        'has_data': True,
        'source': source,
        **result
    })


@crm_bp.route('/api/crm/kpis')
@login_required
def kpis():
    """Executive KPIs with optional YoY comparison."""
    analytics, source = _get_analytics()
    if not analytics or not analytics.has_data():
        return jsonify({'success': True, 'has_data': False})

    result = {'success': True, 'has_data': True, 'kpis': analytics.get_executive_kpis()}

    # Add YoY deltas if historical
    if request.args.get('compare') == 'yoy' and hasattr(analytics, 'get_yoy_comparison'):
        yoy = analytics.get_yoy_comparison()
        result['yoy_deltas'] = yoy.get('deltas', {})
        result['prior_kpis'] = yoy.get('prior', {})

    return jsonify(result)


@crm_bp.route('/api/crm/revenue-trend')
@login_required
def revenue_trend():
    analytics, _ = _get_analytics()
    if not analytics or not analytics.has_data():
        return jsonify({'success': True, 'has_data': False})
    return jsonify({'success': True, 'has_data': True, 'trend': analytics.get_revenue_trend()})


@crm_bp.route('/api/crm/fb-analytics')
@login_required
def fb_analytics():
    analytics, _ = _get_analytics()
    if not analytics or not analytics.has_data():
        return jsonify({'success': True, 'has_data': False})
    return jsonify({'success': True, 'has_data': True, 'fb': analytics.get_fb_analytics()})


@crm_bp.route('/api/crm/room-analytics')
@login_required
def room_analytics():
    analytics, _ = _get_analytics()
    if not analytics or not analytics.has_data():
        return jsonify({'success': True, 'has_data': False})
    return jsonify({'success': True, 'has_data': True, 'rooms': analytics.get_room_analytics()})


@crm_bp.route('/api/crm/payment-analytics')
@login_required
def payment_analytics():
    analytics, _ = _get_analytics()
    if not analytics or not analytics.has_data():
        return jsonify({'success': True, 'has_data': False})
    return jsonify({'success': True, 'has_data': True, 'payments': analytics.get_payment_analytics()})


@crm_bp.route('/api/crm/tax-analytics')
@login_required
def tax_analytics():
    analytics, _ = _get_analytics()
    if not analytics or not analytics.has_data():
        return jsonify({'success': True, 'has_data': False})
    return jsonify({'success': True, 'has_data': True, 'taxes': analytics.get_tax_analytics()})


@crm_bp.route('/api/crm/anomalies')
@login_required
def anomalies():
    analytics, _ = _get_analytics()
    if not analytics or not analytics.has_data():
        return jsonify({'success': True, 'has_data': False})
    return jsonify({'success': True, 'has_data': True, 'anomalies': analytics.get_anomalies()})


# ==============================================================================
# ADVANCED ANALYTICS ENDPOINTS
# ==============================================================================

@crm_bp.route('/api/crm/advanced-kpis')
@login_required
def advanced_kpis():
    """Advanced KPIs: effective ADR, F&B per guest, volatility, etc."""
    analytics, source = _get_analytics()
    if not analytics or not analytics.has_data():
        return jsonify({'success': True, 'has_data': False})
    return jsonify({'success': True, 'has_data': True, 'source': source,
                    'advanced': analytics.get_advanced_kpis()})


@crm_bp.route('/api/crm/dow-analysis')
@login_required
def dow_analysis():
    """Day-of-week performance analysis."""
    analytics, source = _get_analytics()
    if not analytics or not analytics.has_data():
        return jsonify({'success': True, 'has_data': False})
    return jsonify({'success': True, 'has_data': True, 'source': source,
                    'dow': analytics.get_dow_analysis()})


@crm_bp.route('/api/crm/revenue-opportunities')
@login_required
def revenue_opportunities():
    """Revenue opportunities with annualized $ projections."""
    analytics, source = _get_analytics()
    if not analytics or not analytics.has_data():
        return jsonify({'success': True, 'has_data': False})
    return jsonify({'success': True, 'has_data': True, 'source': source,
                    'opportunities': analytics.get_revenue_opportunities()})


# ==============================================================================
# HISTORICAL DATA — Import & Status
# ==============================================================================

@crm_bp.route('/api/crm/import-history', methods=['POST'])
@login_required
@csrf_protect
def import_history():
    """
    Bulk import historical RJ files.
    Accepts multiple .xls files via 'files[]'.
    """
    from utils.jour_importer import JourImporter

    if 'files[]' not in request.files and 'files' not in request.files:
        return jsonify({'success': False, 'error': 'Aucun fichier envoyé'}), 400

    files = request.files.getlist('files[]') or request.files.getlist('files')

    total_imported = 0
    total_updated = 0
    errors = []
    all_dates = []

    for f in files:
        if not f.filename:
            continue
        if not f.filename.endswith(('.xls', '.xlsx')):
            errors.append({'file': f.filename, 'reason': 'Format non supporté (doit être .xls ou .xlsx)'})
            continue

        try:
            file_bytes = io.BytesIO(f.read())
            metrics, info = JourImporter.extract_from_rj(file_bytes, f.filename)

            if not metrics:
                reason = info.get('error', 'Aucune donnée extraite')
                errors.append({'file': f.filename, 'reason': reason})
                continue

            result = JourImporter.persist_batch(metrics, source='bulk_import')
            total_imported += result['inserted']
            total_updated += result['updated']

            for m in metrics:
                all_dates.append(m.date)

        except Exception as e:
            errors.append({'file': f.filename, 'reason': str(e)})

    if all_dates:
        return jsonify({
            'success': True,
            'imported': total_imported,
            'updated': total_updated,
            'total_files': len(files),
            'errors': errors,
            'date_range': {
                'from': min(all_dates).isoformat(),
                'to': max(all_dates).isoformat(),
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Aucun fichier RJ valide importé',
            'errors': errors,
        }), 400


@crm_bp.route('/api/crm/import-from-dir', methods=['POST'])
@login_required
@csrf_protect
def import_from_directory():
    """
    Import RJ files from a server-side directory path (e.g. K: drive).
    Body: { "path": "K:\\RJ 2026-2027" }
    """
    data = request.get_json(silent=True) or {}
    dir_path = data.get('path', '').strip()

    if not dir_path or not os.path.isdir(dir_path):
        return jsonify({'success': False, 'error': f'Dossier introuvable: {dir_path}'}), 400

    try:
        from scripts.import_rj_archives import find_rj_files, extract_date_from_filename
        from utils.jour_importer import JourImporter

        files = find_rj_files(dir_path)
        if not files:
            return jsonify({'success': False, 'error': 'Aucun fichier RJ trouvé dans ce dossier'}), 400

        total_imported = 0
        total_updated = 0
        errors = []

        for audit_date, filepath, fname in files:
            try:
                with open(filepath, 'rb') as f:
                    file_bytes = io.BytesIO(f.read())
                metrics, info = JourImporter.extract_from_rj(file_bytes, fname)
                if metrics:
                    result = JourImporter.persist_batch(metrics, source='dir_import')
                    total_imported += result.get('inserted', 0)
                    total_updated += result.get('updated', 0)
            except Exception as e:
                errors.append({'file': fname, 'reason': str(e)})

        return jsonify({
            'success': True,
            'total_files': len(files),
            'imported': total_imported,
            'updated': total_updated,
            'errors': errors[:20],
            'date_range': {
                'from': files[0][0].isoformat(),
                'to': files[-1][0].isoformat(),
            }
        })
    except Exception as e:
        logger.exception('Import from directory failed')
        return jsonify({'success': False, 'error': str(e)}), 500


@crm_bp.route('/api/crm/sync-kdrive', methods=['POST'])
@login_required
@csrf_protect
def sync_kdrive():
    """
    Trigger K: drive sync manually.
    Body: { "mode": "full" | "daily" }
    """
    from utils.sync_engine import SyncEngine

    data = request.get_json(silent=True) or {}
    mode = data.get('mode', 'daily')

    try:
        from flask import current_app
        if mode == 'full':
            result = SyncEngine.full_sync(current_app._get_current_object())
        else:
            result = SyncEngine.daily_sync(current_app._get_current_object())

        return jsonify({'success': True, **result})
    except Exception as e:
        logger.exception('K: drive sync failed')
        return jsonify({'success': False, 'error': str(e)}), 500


@crm_bp.route('/api/crm/data-status')
@login_required
def data_status():
    """Get summary of historical data in the database."""
    from utils.jour_importer import JourImporter
    from utils.sync_engine import SyncEngine
    jour_status = JourImporter.get_data_status()
    sync_status = SyncEngine.get_sync_status()
    return jsonify({'success': True, **jour_status, **sync_status})


# ==============================================================================
# STAFF / PERSONNEL
# ==============================================================================

@crm_bp.route('/api/crm/staff')
@login_required
def get_staff():
    """Get all staff members with stats."""
    from utils.rj_mapper import SETD_PERSONNEL_COLUMNS

    search = request.args.get('search', '').lower()
    sort_by = request.args.get('sort', 'name')

    excluded = {'petite caisse', 'conc. banc.', 'corr. mois suivant',
                'mixologue', 'mixologue 2.0', 'mixologue 3.0'}

    # Build aggregated variance stats in a single GROUP BY query instead of
    # one query per staff member (avoids N+1 on large datasets).
    # Note: func.sum on a cast boolean avoids SQLAlchemy 1.x/2.x case() API differences.
    # SQLite and PostgreSQL both support CAST(is_alert AS INTEGER) for counting booleans.
    agg_rows = db.session.query(
        func.lower(VarianceRecord.receptionist).label('receptionist_lower'),
        func.count(VarianceRecord.id).label('variance_count'),
        func.sum(VarianceRecord.variance).label('total_variance'),
        func.sum(
            db.cast(VarianceRecord.is_alert, db.Integer)
        ).label('alert_count'),
    ).group_by(func.lower(VarianceRecord.receptionist)).all()

    variance_stats = {
        row.receptionist_lower: {
            'variance_count': row.variance_count or 0,
            'total_variance': round(float(row.total_variance or 0), 2),
            'alert_count': row.alert_count or 0,
        }
        for row in agg_rows
    }

    staff_list = []
    for name, col in SETD_PERSONNEL_COLUMNS.items():
        if name.lower() in excluded:
            continue
        if search and search not in name.lower():
            continue

        stats = variance_stats.get(name.lower(), {
            'variance_count': 0,
            'total_variance': 0.0,
            'alert_count': 0,
        })

        staff_list.append({
            'name': name,
            'column': col,
            'stats': stats,
        })

    if sort_by == 'name':
        staff_list.sort(key=lambda x: x['name'].lower())
    elif sort_by == 'total_variance':
        staff_list.sort(key=lambda x: abs(x['stats']['total_variance']), reverse=True)

    return jsonify({'success': True, 'staff': staff_list, 'total': len(staff_list)})


# ==============================================================================
# VARIANCES
# ==============================================================================

@crm_bp.route('/api/crm/variances')
@login_required
def get_variances():
    """Get variance records with filters."""
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    receptionist = request.args.get('receptionist', '')
    alerts_only = request.args.get('alerts_only', 'false') == 'true'

    query = VarianceRecord.query
    if start:
        query = query.filter(VarianceRecord.date >= datetime.strptime(start, '%Y-%m-%d').date())
    if end:
        query = query.filter(VarianceRecord.date <= datetime.strptime(end, '%Y-%m-%d').date())
    if receptionist:
        query = query.filter(func.lower(VarianceRecord.receptionist).contains(receptionist.lower()))
    if alerts_only:
        query = query.filter(or_(
            VarianceRecord.variance > VarianceRecord.ALERT_THRESHOLD,
            VarianceRecord.variance < -VarianceRecord.ALERT_THRESHOLD
        ))

    records = query.order_by(desc(VarianceRecord.date)).limit(200).all()
    return jsonify({'success': True, 'variances': [r.to_dict() for r in records], 'total': len(records)})


@crm_bp.route('/api/crm/variances', methods=['POST'])
@login_required
def add_variance():
    """Add a new variance record."""
    data = request.get_json()
    if not data or not data.get('receptionist') or not data.get('date'):
        return jsonify({'success': False, 'error': 'receptionist et date requis'}), 400

    record = VarianceRecord(
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        receptionist=data['receptionist'],
        expected=float(data.get('expected', 0)),
        actual=float(data.get('actual', 0)),
        variance=float(data.get('actual', 0)) - float(data.get('expected', 0)),
        notes=data.get('notes', ''),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({'success': True, 'variance': record.to_dict()})
