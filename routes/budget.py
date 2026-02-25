"""
Budget Management & Variance Analysis — Management portal for budget import and variance reporting.
"""

from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from functools import wraps
from datetime import datetime, date
from database.models import db, MonthlyBudget
from utils.budget_analyzer import BudgetAnalyzer
import logging

logger = logging.getLogger(__name__)

budget_bp = Blueprint('budget', __name__, url_prefix='/budget')

from database.models import TOTAL_ROOMS  # 252, from models.py


def budget_required(f):
    """Access control for budget management (Direction portal roles)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('auth_v2.login'))
        role = session.get('user_role_type', '')
        if role not in ('admin', 'gm', 'gsm', 'accounting'):
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# PAGE
# ==============================================================================

@budget_bp.route('/')
@budget_required
def budget_page():
    """Budget management page."""
    return render_template('budget.html')


# ==============================================================================
# API — Budget Management
# ==============================================================================

@budget_bp.route('/api/budget/<int:year>/<int:month>')
@budget_required
def get_budget(year, month):
    """Get budget for a specific month."""
    if month < 1 or month > 12:
        return jsonify({'error': 'Mois invalide'}), 400

    budget = MonthlyBudget.query.filter_by(year=year, month=month).first()

    if not budget:
        return jsonify({'data': None, 'message': 'Aucun budget saisi'}), 200

    return jsonify({
        'data': {
            'id': budget.id,
            'year': budget.year,
            'month': budget.month,
            'rooms_target': budget.rooms_target,
            'adr_target': budget.adr_target,
            'room_revenue': budget.room_revenue,
            'location_salle': budget.location_salle,
            'giotto': budget.giotto,
            'piazza': budget.piazza,
            'cupola': budget.cupola,
            'banquet': budget.banquet,
            'spesa': budget.spesa,
            'total_revenue': budget.total_revenue,
            'labor_reception': budget.labor_reception,
            'labor_femme_chambre': budget.labor_femme_chambre,
            'labor_equipier': budget.labor_equipier,
            'labor_gouvernante': budget.labor_gouvernante,
            'labor_buanderie': budget.labor_buanderie,
            'labor_cuisine': budget.labor_cuisine,
            'labor_piazza': budget.labor_piazza,
            'labor_cupola': budget.labor_cupola,
            'labor_banquet': budget.labor_banquet,
            'labor_banquet_ii': budget.labor_banquet_ii,
            'labor_adm': budget.labor_adm,
            'labor_marketing': budget.labor_marketing,
            'labor_entretien': budget.labor_entretien,
            'marketing': budget.marketing,
            'admin': budget.admin,
            'entretien': budget.entretien,
            'energie': budget.energie,
            'taxes_assurances': budget.taxes_assurances,
            'amortissement': budget.amortissement,
            'interet': budget.interet,
            'loyer': budget.loyer,
            'cost_variable_chambres': budget.cost_variable_chambres,
            'cost_variable_banquet': budget.cost_variable_banquet,
            'cost_variable_resto': budget.cost_variable_resto,
            'benefits_hebergement': budget.benefits_hebergement,
            'benefits_restauration': budget.benefits_restauration,
        }
    })


@budget_bp.route('/api/budget/save', methods=['POST'])
@budget_required
def save_budget():
    """Save or update budget data (manual entry)."""
    data = request.get_json()

    if not data or 'year' not in data or 'month' not in data:
        return jsonify({'error': 'Année et mois requis'}), 400

    year = data.get('year')
    month = data.get('month')

    if month < 1 or month > 12:
        return jsonify({'error': 'Mois invalide'}), 400

    try:
        # Get or create budget record
        budget = MonthlyBudget.query.filter_by(year=year, month=month).first()

        if not budget:
            budget = MonthlyBudget(year=year, month=month)

        # Update fields
        budget.rooms_target = data.get('rooms_target', budget.rooms_target)
        budget.adr_target = data.get('adr_target', budget.adr_target)
        budget.room_revenue = data.get('room_revenue', budget.room_revenue)
        budget.location_salle = data.get('location_salle', budget.location_salle)
        budget.giotto = data.get('giotto', budget.giotto)
        budget.piazza = data.get('piazza', budget.piazza)
        budget.cupola = data.get('cupola', budget.cupola)
        budget.banquet = data.get('banquet', budget.banquet)
        budget.spesa = data.get('spesa', budget.spesa)
        budget.total_revenue = data.get('total_revenue', budget.total_revenue)

        # Labor fields
        budget.labor_reception = data.get('labor_reception', budget.labor_reception)
        budget.labor_femme_chambre = data.get('labor_femme_chambre', budget.labor_femme_chambre)
        budget.labor_equipier = data.get('labor_equipier', budget.labor_equipier)
        budget.labor_gouvernante = data.get('labor_gouvernante', budget.labor_gouvernante)
        budget.labor_buanderie = data.get('labor_buanderie', budget.labor_buanderie)
        budget.labor_cuisine = data.get('labor_cuisine', budget.labor_cuisine)
        budget.labor_piazza = data.get('labor_piazza', budget.labor_piazza)
        budget.labor_cupola = data.get('labor_cupola', budget.labor_cupola)
        budget.labor_banquet = data.get('labor_banquet', budget.labor_banquet)
        budget.labor_banquet_ii = data.get('labor_banquet_ii', budget.labor_banquet_ii)
        budget.labor_adm = data.get('labor_adm', budget.labor_adm)
        budget.labor_marketing = data.get('labor_marketing', budget.labor_marketing)
        budget.labor_entretien = data.get('labor_entretien', budget.labor_entretien)

        # Fixed costs
        budget.marketing = data.get('marketing', budget.marketing)
        budget.admin = data.get('admin', budget.admin)
        budget.entretien = data.get('entretien', budget.entretien)
        budget.energie = data.get('energie', budget.energie)
        budget.taxes_assurances = data.get('taxes_assurances', budget.taxes_assurances)
        budget.amortissement = data.get('amortissement', budget.amortissement)
        budget.interet = data.get('interet', budget.interet)
        budget.loyer = data.get('loyer', budget.loyer)

        # Cost ratios
        budget.cost_variable_chambres = data.get('cost_variable_chambres', budget.cost_variable_chambres)
        budget.cost_variable_banquet = data.get('cost_variable_banquet', budget.cost_variable_banquet)
        budget.cost_variable_resto = data.get('cost_variable_resto', budget.cost_variable_resto)
        budget.benefits_hebergement = data.get('benefits_hebergement', budget.benefits_hebergement)
        budget.benefits_restauration = data.get('benefits_restauration', budget.benefits_restauration)

        db.session.add(budget)
        db.session.commit()

        return jsonify({
            'message': f'Budget pour {month}/{year} enregistré',
            'data': {
                'id': budget.id,
                'year': budget.year,
                'month': budget.month,
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f'Budget save error: {str(e)}')
        return jsonify({'error': f'Erreur lors de l\'enregistrement: {str(e)}'}), 500


@budget_bp.route('/api/budget/import', methods=['POST'])
@budget_required
def import_budget():
    """Import budget from CSV/Excel upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'Fichier vide'}), 400

    try:
        year = int(request.form.get('year', 0))
        file_content = file.read()

        # Try CSV first, then Excel
        if file.filename.endswith('.csv'):
            result = BudgetAnalyzer.parse_budget_csv(file_content)
        elif file.filename.endswith(('.xlsx', '.xls')):
            result = BudgetAnalyzer.parse_budget_excel(file_content)
        else:
            return jsonify({'error': 'Format de fichier non supporté (CSV ou Excel requis)'}), 400

        if 'error' in result:
            return jsonify({'error': result['error']}), 400

        # Insert/update budgets for each month
        month_budgets = result.get('months', {})
        saved_months = []

        for month, fields in month_budgets.items():
            if not fields:
                continue

            budget = MonthlyBudget.query.filter_by(year=year, month=month).first()
            if not budget:
                budget = MonthlyBudget(year=year, month=month)

            # Update all provided fields
            for field_name, value in fields.items():
                if hasattr(budget, field_name):
                    setattr(budget, field_name, value)

            db.session.add(budget)
            saved_months.append(month)

        db.session.commit()

        return jsonify({
            'message': f'Budget importé pour {len(saved_months)} mois',
            'months_saved': saved_months,
            'year': year,
        })

    except ValueError as e:
        return jsonify({'error': f'Année invalide: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Budget import error: {str(e)}')
        return jsonify({'error': f'Erreur lors de l\'import: {str(e)}'}), 500


@budget_bp.route('/api/budget/variance/<int:year>/<int:month>')
@budget_required
def get_variance(year, month):
    """Get variance analysis for a month (budget vs actual)."""
    if month < 1 or month > 12:
        return jsonify({'error': 'Mois invalide'}), 400

    try:
        analyzer = BudgetAnalyzer(year, month)
        report = analyzer.get_variance_report()
        return jsonify(report)
    except Exception as e:
        logger.error(f'Variance analysis error: {str(e)}')
        return jsonify({'error': f'Erreur: {str(e)}'}), 500


@budget_bp.route('/api/budget/ytd/<int:year>')
@budget_required
def get_ytd_summary(year):
    """Get year-to-date variance summary."""
    try:
        analyzer = BudgetAnalyzer(year, 1)  # Month doesn't matter for YTD
        summary = analyzer.get_ytd_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f'YTD summary error: {str(e)}')
        return jsonify({'error': f'Erreur: {str(e)}'}), 500


@budget_bp.route('/api/budget/<int:year>/<int:month>', methods=['DELETE'])
@budget_required
def delete_budget(year, month):
    """Delete a month's budget."""
    if month < 1 or month > 12:
        return jsonify({'error': 'Mois invalide'}), 400

    try:
        budget = MonthlyBudget.query.filter_by(year=year, month=month).first()

        if not budget:
            return jsonify({'error': 'Budget non trouvé'}), 404

        db.session.delete(budget)
        db.session.commit()

        return jsonify({'message': f'Budget pour {month}/{year} supprimé'})

    except Exception as e:
        db.session.rollback()
        logger.error(f'Budget delete error: {str(e)}')
        return jsonify({'error': f'Erreur lors de la suppression: {str(e)}'}), 500
