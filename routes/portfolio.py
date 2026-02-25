"""
Portfolio management blueprint for multi-property dashboard.

Provides consolidated views and analytics across all properties.
"""

from flask import Blueprint, render_template, jsonify, session
from datetime import datetime, timedelta
from database.models import db, Property, NightAuditSession, DailyJourMetrics
from utils.auth_decorators import role_required

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/portfolio')


@portfolio_bp.route('/', methods=['GET'])
@role_required('admin', 'gm', 'gsm', 'accounting')
def portfolio_page():
    """Render the portfolio dashboard page."""
    return render_template('portfolio.html')


@portfolio_bp.route('/api/portfolio/summary', methods=['GET'])
@role_required('admin', 'gm', 'gsm', 'accounting')
def portfolio_summary():
    """
    Get consolidated KPI summary across all active properties.

    Returns:
        JSON with:
            - total_rooms: sum of all property rooms
            - avg_occupancy: average occupancy across all properties
            - total_revenue_30d: total revenue last 30 days
            - avg_adr_30d: average ADR last 30 days
            - property_count: number of active properties
            - recent_audits: count of locked audits in last 30 days
    """
    properties = Property.query.filter_by(is_active=True).all()
    if not properties:
        return jsonify({
            'total_rooms': 0,
            'avg_occupancy': 0,
            'total_revenue_30d': 0,
            'avg_adr_30d': 0,
            'property_count': 0,
            'recent_audits': 0,
        }), 200

    thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
    property_ids = [p.id for p in properties]

    # Get aggregated metrics
    metrics = db.session.query(
        db.func.sum(Property.total_rooms).label('total_rooms'),
        db.func.avg(DailyJourMetrics.occupancy_rate).label('avg_occ'),
        db.func.sum(DailyJourMetrics.total_revenue).label('total_rev'),
        db.func.avg(DailyJourMetrics.adr).label('avg_adr'),
    ).outerjoin(
        DailyJourMetrics,
        db.and_(
            Property.id == DailyJourMetrics.property_id,
            DailyJourMetrics.date >= thirty_days_ago
        )
    ).filter(
        Property.id.in_(property_ids)
    ).first()

    # Count recent audits
    recent_audits = NightAuditSession.query.filter(
        NightAuditSession.property_id.in_(property_ids),
        NightAuditSession.audit_date >= thirty_days_ago,
        NightAuditSession.status == 'locked',
    ).count()

    return jsonify({
        'total_rooms': metrics.total_rooms or 0,
        'avg_occupancy': round(metrics.avg_occ or 0, 1),
        'total_revenue_30d': round(metrics.total_rev or 0, 2),
        'avg_adr_30d': round(metrics.avg_adr or 0, 2),
        'property_count': len(properties),
        'recent_audits': recent_audits,
    }), 200


@portfolio_bp.route('/api/portfolio/comparison', methods=['GET'])
@role_required('admin', 'gm', 'gsm', 'accounting')
def portfolio_comparison():
    """
    Get property-to-property comparison data.

    Returns:
        JSON with comparison metrics for each active property:
            - occupancy trend (last 30 days, by property)
            - ADR trend (last 30 days, by property)
            - RevPAR by property
            - total revenue by property
    """
    properties = Property.query.filter_by(is_active=True).order_by(Property.name).all()
    thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)

    comparison_data = []
    for prop in properties:
        # Get daily metrics for last 30 days
        daily_data = DailyJourMetrics.query.filter(
            DailyJourMetrics.property_id == prop.id,
            DailyJourMetrics.date >= thirty_days_ago,
        ).order_by(DailyJourMetrics.date).all()

        if not daily_data:
            # No data yet for this property
            comparison_data.append({
                'property_id': prop.id,
                'property_name': prop.name,
                'property_code': prop.code,
                'total_rooms': prop.total_rooms,
                'dates': [],
                'occupancy': [],
                'adr': [],
                'revpar': [],
                'revenue': [],
                'avg_occupancy': 0,
                'avg_adr': 0,
                'avg_revpar': 0,
                'total_revenue': 0,
            })
            continue

        dates = [d.date.isoformat() for d in daily_data]
        occupancy = [round(d.occupancy_rate or 0, 1) for d in daily_data]
        adr = [round(d.adr or 0, 2) for d in daily_data]
        revpar = [round((d.adr or 0) * (d.occupancy_rate or 0) / 100, 2) for d in daily_data]
        revenue = [round(d.total_revenue or 0, 2) for d in daily_data]

        avg_occ = sum(occupancy) / len(occupancy) if occupancy else 0
        avg_adr = sum(adr) / len(adr) if adr else 0
        avg_revpar = sum(revpar) / len(revpar) if revpar else 0
        total_rev = sum(revenue)

        comparison_data.append({
            'property_id': prop.id,
            'property_name': prop.name,
            'property_code': prop.code,
            'total_rooms': prop.total_rooms,
            'dates': dates,
            'occupancy': occupancy,
            'adr': adr,
            'revpar': revpar,
            'revenue': revenue,
            'avg_occupancy': round(avg_occ, 1),
            'avg_adr': round(avg_adr, 2),
            'avg_revpar': round(avg_revpar, 2),
            'total_revenue': round(total_rev, 2),
        })

    return jsonify(comparison_data), 200


@portfolio_bp.route('/api/portfolio/property-list', methods=['GET'])
@role_required('admin', 'gm', 'gsm', 'accounting')
def portfolio_property_list():
    """
    Get a simple list of active properties for selection.

    Returns:
        JSON array of properties with id, code, name.
    """
    properties = Property.query.filter_by(is_active=True).order_by(Property.name).all()
    return jsonify([{
        'id': p.id,
        'code': p.code,
        'name': p.name,
        'city': p.city,
    } for p in properties]), 200
