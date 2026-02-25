"""
Property management blueprint for multi-property support.

Handles property CRUD operations and property selection via Flask session.
"""

from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from datetime import datetime
from database.models import db, Property, NightAuditSession, DailyJourMetrics
from utils.auth_decorators import role_required, get_current_user
from utils.property_context import set_current_property, get_current_property

properties_bp = Blueprint('properties', __name__, url_prefix='/properties')


@properties_bp.route('/', methods=['GET'])
@role_required('admin')
def properties_page():
    """Render the property management page."""
    properties = Property.query.order_by(Property.is_active.desc(), Property.name).all()
    return render_template('properties.html', properties=properties)


@properties_bp.route('/api/properties', methods=['GET'])
@role_required('admin')
def list_properties():
    """
    List all properties.

    Returns:
        JSON list of all properties with their details.
    """
    properties = Property.query.order_by(Property.name).all()
    return jsonify([prop.to_dict() for prop in properties])


@properties_bp.route('/api/properties', methods=['POST'])
@role_required('admin')
def create_property():
    """
    Create a new property.

    Expected JSON body:
        {
            'code': 'SHRLVL',
            'name': 'Sheraton Laval',
            'brand': 'Marriott',
            'total_rooms': 252,
            'address': '2440 Autoroute des Laurentides',
            'city': 'Laval',
            'province': 'Québec',
            'country': 'Canada',
            'timezone': 'America/Montreal',
            'currency': 'CAD',
            'pms_type': 'Galaxy Lightspeed',
            'pms_property_id': '...'
        }

    Returns:
        JSON with created property or error message.
    """
    data = request.get_json() or {}

    # Validate required fields
    required = ['code', 'name', 'brand', 'total_rooms']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Champs requis manquants: {", ".join(missing)}'}), 400

    # Check for duplicate code
    existing = Property.query.filter_by(code=data['code']).first()
    if existing:
        return jsonify({'error': f'Code de propriété "{data["code"]}" déjà utilisé.'}), 409

    try:
        prop = Property(
            code=data['code'],
            name=data['name'],
            brand=data.get('brand', 'Marriott'),
            total_rooms=int(data['total_rooms']),
            address=data.get('address', ''),
            city=data.get('city', ''),
            province=data.get('province', ''),
            country=data.get('country', 'Canada'),
            timezone=data.get('timezone', 'America/Montreal'),
            currency=data.get('currency', 'CAD'),
            pms_type=data.get('pms_type', 'Galaxy Lightspeed'),
            pms_property_id=data.get('pms_property_id', ''),
        )
        db.session.add(prop)
        db.session.commit()

        return jsonify(prop.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@properties_bp.route('/api/properties/<int:property_id>', methods=['PUT'])
@role_required('admin')
def update_property(property_id):
    """
    Update an existing property.

    Args:
        property_id (int): The property ID to update.

    Returns:
        JSON with updated property or error message.
    """
    prop = Property.query.get(property_id)
    if not prop:
        return jsonify({'error': 'Propriété non trouvée.'}), 404

    data = request.get_json() or {}

    try:
        # Allow updating most fields except ID and created_at
        for field in ['code', 'name', 'brand', 'total_rooms', 'address', 'city',
                      'province', 'country', 'timezone', 'currency', 'is_active',
                      'pms_type', 'pms_property_id']:
            if field in data:
                if field == 'total_rooms':
                    setattr(prop, field, int(data[field]))
                elif field == 'is_active':
                    setattr(prop, field, bool(data[field]))
                else:
                    setattr(prop, field, data[field])

        db.session.commit()
        return jsonify(prop.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@properties_bp.route('/api/properties/<int:property_id>', methods=['DELETE'])
@role_required('admin')
def delete_property(property_id):
    """
    Deactivate a property (soft delete).

    Args:
        property_id (int): The property ID to deactivate.

    Returns:
        JSON success message or error.
    """
    prop = Property.query.get(property_id)
    if not prop:
        return jsonify({'error': 'Propriété non trouvée.'}), 404

    # Prevent deleting the default property if it has active sessions
    if property_id == 1:
        active_sessions = NightAuditSession.query.filter(
            NightAuditSession.property_id == property_id,
            NightAuditSession.status != 'locked'
        ).count()
        if active_sessions > 0:
            return jsonify({
                'error': 'Impossible de désactiver cette propriété. Sessions actives en cours.'
            }), 409

    try:
        prop.is_active = False
        db.session.commit()
        return jsonify({'message': 'Propriété désactivée avec succès.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@properties_bp.route('/api/properties/switch/<int:property_id>', methods=['POST'])
def switch_property(property_id):
    """
    Switch the active property in the user's session.

    Args:
        property_id (int): The property ID to switch to.

    Returns:
        JSON success message or error.
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non authentifié.'}), 401

    if set_current_property(property_id):
        return jsonify({
            'message': 'Propriété changée avec succès.',
            'property_id': property_id,
            'property_name': session.get('property_name'),
        }), 200
    else:
        return jsonify({'error': 'Propriété introuvable ou inactive.'}), 404


@properties_bp.route('/api/properties/portfolio', methods=['GET'])
@role_required('admin')
def portfolio_summary():
    """
    Get a summary dashboard of all properties.

    Returns:
        JSON with portfolio KPIs across all active properties.
    """
    properties = Property.query.filter_by(is_active=True).all()

    portfolio_data = []
    for prop in properties:
        # Get latest metrics for this property
        latest_metrics = DailyJourMetrics.query.filter_by(
            property_id=prop.id
        ).order_by(DailyJourMetrics.date.desc()).first()

        # Get average occupancy and ADR for last 30 days
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)

        avg_metrics = db.session.query(
            db.func.avg(DailyJourMetrics.occupancy_rate).label('avg_occ'),
            db.func.avg(DailyJourMetrics.adr).label('avg_adr'),
            db.func.sum(DailyJourMetrics.total_revenue).label('total_rev'),
        ).filter(
            DailyJourMetrics.property_id == prop.id,
            DailyJourMetrics.date >= thirty_days_ago,
        ).first()

        # Count recent audits
        recent_audits = NightAuditSession.query.filter(
            NightAuditSession.property_id == prop.id,
            NightAuditSession.audit_date >= thirty_days_ago,
            NightAuditSession.status == 'locked',
        ).count()

        portfolio_data.append({
            'id': prop.id,
            'code': prop.code,
            'name': prop.name,
            'city': prop.city,
            'total_rooms': prop.total_rooms,
            'latest_occ_pct': latest_metrics.occupancy_rate if latest_metrics else 0,
            'latest_adr': latest_metrics.adr if latest_metrics else 0,
            'avg_occ_30d': round(avg_metrics.avg_occ or 0, 1),
            'avg_adr_30d': round(avg_metrics.avg_adr or 0, 2),
            'total_revenue_30d': round(avg_metrics.total_rev or 0, 2),
            'recent_audits': recent_audits,
            'is_active': prop.is_active,
        })

    return jsonify(portfolio_data), 200
