"""
Lightspeed Galaxy PMS Integration Blueprint.

Handles configuration, authentication, and synchronization of PMS data
into the RJ Natif night audit system.

Routes:
- GET /lightspeed/ - Configuration page
- GET /api/lightspeed/status - Connection status JSON
- POST /api/lightspeed/connect - Test connection with credentials
- POST /api/lightspeed/sync/<date> - Sync data for a specific date
- GET /api/lightspeed/sync/status/<date> - Get sync status for a date
- POST /api/lightspeed/disconnect - Clear stored credentials
"""

from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from datetime import datetime, timedelta
import logging
from functools import wraps

from routes.checklist import login_required
from utils.lightspeed_client import LightspeedClient, LightspeedAPIError, LightspeedConfigError
from utils.lightspeed_sync import LightspeedSync
from utils.csrf import csrf_protect

logger = logging.getLogger(__name__)

lightspeed_bp = Blueprint(
    'lightspeed',
    __name__,
    url_prefix='/lightspeed',
    template_folder='../templates'
)

# Module-level client instance (shared across requests)
_lightspeed_client = None


def get_lightspeed_client() -> LightspeedClient:
    """Get or create the Lightspeed client singleton."""
    global _lightspeed_client
    if _lightspeed_client is None:
        _lightspeed_client = LightspeedClient()
    return _lightspeed_client


def get_sync_service() -> LightspeedSync:
    """Get a Lightspeed sync service instance."""
    return LightspeedSync(get_lightspeed_client())


def require_gm_or_admin(f):
    """Decorator: Require GM or Admin role to access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_role = session.get('user_role_type')
        if user_role not in ['gm', 'admin']:
            flash("Accès réservé aux Directeurs Généraux et Administrateurs.", "error")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@lightspeed_bp.route('/', methods=['GET'])
@login_required
@require_gm_or_admin
def configuration_page():
    """
    Configuration page for Lightspeed integration.

    Displays:
    1. Connection status indicator
    2. Configuration form
    3. Sync status by date
    4. Recent sync history
    """
    client = get_lightspeed_client()
    status = client.get_connection_status()

    # Get recent sessions with sync info
    from database.models import NightAuditSession
    recent_sessions = NightAuditSession.query.order_by(
        NightAuditSession.audit_date.desc()
    ).limit(30).all()

    sync_service = get_sync_service()
    sync_statuses = [
        {
            'date': s.audit_date.isoformat(),
            'auditor': s.auditor_name or 'Non assigné',
            'status': s.status,
            'sync_info': sync_service.get_sync_status(s.audit_date.isoformat()),
        }
        for s in recent_sessions
    ]

    return render_template(
        'lightspeed.html',
        connection_status=status,
        is_configured=client.is_configured(),
        is_connected=client.is_connected(),
        sync_statuses=sync_statuses,
    )


@lightspeed_bp.route('/api/status', methods=['GET'])
@login_required
def api_status():
    """
    Get connection status.

    Returns JSON with current connection state, property info, last sync time.
    """
    client = get_lightspeed_client()
    return jsonify(client.get_connection_status())


@lightspeed_bp.route('/api/connect', methods=['POST'])
@login_required
@require_gm_or_admin
@csrf_protect
def api_connect():
    """
    Test connection with provided credentials.

    Expects JSON:
    {
        "client_id": "...",
        "client_secret": "...",
        "property_id": "...",
        "base_url": "..." (optional)
    }

    Returns:
    {
        "success": bool,
        "message": str,
        "connection_status": dict
    }
    """
    data = request.get_json() or {}

    try:
        # Create temporary client with provided credentials
        test_client = LightspeedClient(config={
            'LIGHTSPEED_CLIENT_ID': data.get('client_id'),
            'LIGHTSPEED_CLIENT_SECRET': data.get('client_secret'),
            'LIGHTSPEED_PROPERTY_ID': data.get('property_id'),
            'LIGHTSPEED_BASE_URL': data.get('base_url', 'https://api.lsk.lightspeed.app'),
        })

        # Test connection
        if test_client.test_connection():
            # Update global client with new credentials
            global _lightspeed_client
            _lightspeed_client = test_client

            logger.info(f"Successfully connected to Lightspeed API")
            return jsonify({
                'success': True,
                'message': 'Connexion réussie à Lightspeed Galaxy PMS',
                'connection_status': test_client.get_connection_status(),
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Test de connexion échoué. Vérifiez les identifiants.',
                'connection_status': test_client.get_connection_status(),
            }), 400

    except LightspeedConfigError as e:
        logger.warning(f"Config error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Erreur de configuration: {str(e)}",
        }), 400

    except LightspeedAPIError as e:
        logger.warning(f"API error during connection test: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Erreur API: {str(e)}",
        }), 400

    except Exception as e:
        logger.error(f"Unexpected error during connection: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Erreur inattendue: {str(e)}",
        }), 500


@lightspeed_bp.route('/api/sync/<date_str>', methods=['POST'])
@login_required
@require_gm_or_admin
@csrf_protect
def api_sync(date_str):
    """
    Sync data for a specific date.

    Syncs all available tabs from Lightspeed API into NightAuditSession.

    Args:
        date_str: Date string (YYYY-MM-DD)

    Returns:
    {
        "success": bool,
        "message": str,
        "synced_tabs": [list],
        "errors": [list],
        "warnings": [list],
    }
    """
    try:
        # Validate date format
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Format de date invalide. Utilisez YYYY-MM-DD.',
            }), 400

        client = get_lightspeed_client()

        if not client.is_configured():
            return jsonify({
                'success': False,
                'message': 'Lightspeed non configuré. Entrez les identifiants d\'abord.',
            }), 400

        # Perform sync
        sync_service = get_sync_service()
        result = sync_service.sync_session(date_str)

        if result['errors']:
            return jsonify({
                'success': False,
                'message': f"Sync partielle: {len(result['synced_tabs'])} onglets synchronisés",
                'synced_tabs': result['synced_tabs'],
                'errors': result['errors'],
                'warnings': result['warnings'],
            }), 400
        else:
            logger.info(f"Successfully synced {date_str}")
            return jsonify({
                'success': True,
                'message': f"{len(result['synced_tabs'])} onglets synchronisés avec succès",
                'synced_tabs': result['synced_tabs'],
                'errors': result['errors'],
                'warnings': result['warnings'],
            })

    except Exception as e:
        logger.error(f"Sync failed for {date_str}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Erreur lors de la synchronisation: {str(e)}",
        }), 500


@lightspeed_bp.route('/api/sync/status/<date_str>', methods=['GET'])
@login_required
def api_sync_status(date_str):
    """
    Get sync status for a date.

    Shows which tabs are synced, which are manual, completeness percentage.

    Args:
        date_str: Date string (YYYY-MM-DD)

    Returns:
    {
        "date": date_str,
        "session_found": bool,
        "synced_tabs": [list],
        "manual_tabs": [list],
        "sync_completeness": float (0-1),
    }
    """
    try:
        sync_service = get_sync_service()
        status = sync_service.get_sync_status(date_str)
        return jsonify(status)

    except Exception as e:
        logger.error(f"Status check failed for {date_str}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Erreur: {str(e)}",
        }), 500


@lightspeed_bp.route('/api/disconnect', methods=['POST'])
@login_required
@require_gm_or_admin
@csrf_protect
def api_disconnect():
    """
    Clear stored authentication and disconnect from Lightspeed.

    Returns:
    {
        "success": bool,
        "message": str,
    }
    """
    try:
        client = get_lightspeed_client()
        client.disconnect()

        # Reset global client
        global _lightspeed_client
        _lightspeed_client = None

        logger.info("Disconnected from Lightspeed API")
        return jsonify({
            'success': True,
            'message': 'Déconnecté de Lightspeed Galaxy PMS',
        })

    except Exception as e:
        logger.error(f"Disconnect failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Erreur: {str(e)}",
        }), 500
