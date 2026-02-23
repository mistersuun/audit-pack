"""
Audit blueprint package - registers all audit sub-blueprints.
"""

from flask import Blueprint

# Import all sub-blueprints
from .rj_core import rj_core_bp
from .rj_fill import rj_fill_bp
from .rj_macros import rj_macros_bp
from .rj_sd import rj_sd_bp
from .rj_quasimodo import rj_quasimodo_bp
from .rj_parsers import rj_parsers_bp

# Create master audit blueprint
audit_bp = Blueprint('audit', __name__)

# Register all sub-blueprints with their prefixes
audit_bp.register_blueprint(rj_core_bp, url_prefix='/')
audit_bp.register_blueprint(rj_fill_bp, url_prefix='/')
audit_bp.register_blueprint(rj_macros_bp, url_prefix='/')
audit_bp.register_blueprint(rj_sd_bp, url_prefix='/')
audit_bp.register_blueprint(rj_quasimodo_bp, url_prefix='/')
audit_bp.register_blueprint(rj_parsers_bp, url_prefix='/')

__all__ = ['audit_bp']
