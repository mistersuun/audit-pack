"""
Budget Analyzer — Variance analysis and budget import utilities.
Analyzes MonthlyBudget vs DailyJourMetrics for variance reports.
"""

from datetime import datetime, date
from decimal import Decimal
import calendar
import csv
import io
from database.models import db, MonthlyBudget, DailyJourMetrics


class BudgetAnalyzer:
    """Analyzer for budget vs actual data."""

    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.budget = None
        self.daily_metrics = []
        self._load_data()

    def _load_data(self):
        """Load budget and actual data from database."""
        self.budget = MonthlyBudget.query.filter_by(
            year=self.year, month=self.month
        ).first()

        self.daily_metrics = DailyJourMetrics.query.filter(
            DailyJourMetrics.year == self.year,
            DailyJourMetrics.month == self.month
        ).all()

    def get_budget_dict(self):
        """Return budget as dictionary, or empty dict if no budget exists."""
        if not self.budget:
            return None

        return {
            'year': self.budget.year,
            'month': self.budget.month,
            'rooms_target': self.budget.rooms_target,
            'adr_target': self.budget.adr_target,
            'room_revenue': self.budget.room_revenue,
            'location_salle': self.budget.location_salle,
            'giotto': self.budget.giotto,
            'piazza': self.budget.piazza,
            'cupola': self.budget.cupola,
            'banquet': self.budget.banquet,
            'spesa': self.budget.spesa,
            'total_revenue': self.budget.total_revenue,
            'labor_reception': self.budget.labor_reception,
            'labor_femme_chambre': self.budget.labor_femme_chambre,
            'labor_equipier': self.budget.labor_equipier,
            'labor_gouvernante': self.budget.labor_gouvernante,
            'labor_buanderie': self.budget.labor_buanderie,
            'labor_cuisine': self.budget.labor_cuisine,
            'labor_piazza': self.budget.labor_piazza,
            'labor_cupola': self.budget.labor_cupola,
            'labor_banquet': self.budget.labor_banquet,
            'labor_banquet_ii': self.budget.labor_banquet_ii,
            'labor_adm': self.budget.labor_adm,
            'labor_marketing': self.budget.labor_marketing,
            'labor_entretien': self.budget.labor_entretien,
            'marketing': self.budget.marketing,
            'admin': self.budget.admin,
            'entretien': self.budget.entretien,
            'energie': self.budget.energie,
            'taxes_assurances': self.budget.taxes_assurances,
            'amortissement': self.budget.amortissement,
            'interet': self.budget.interet,
            'loyer': self.budget.loyer,
            'cost_variable_chambres': self.budget.cost_variable_chambres,
            'cost_variable_banquet': self.budget.cost_variable_banquet,
            'cost_variable_resto': self.budget.cost_variable_resto,
            'benefits_hebergement': self.budget.benefits_hebergement,
            'benefits_restauration': self.budget.benefits_restauration,
        }

    def get_actual_data(self):
        """Calculate actuals from daily metrics for the month."""
        if not self.daily_metrics:
            return {
                'days': 0,
                'rooms_sold': 0,
                'adr': 0,
                'room_revenue': 0,
                'location_salle': 0,
                'giotto': 0,
                'piazza': 0,
                'cupola': 0,
                'banquet': 0,
                'spesa': 0,
                'total_revenue': 0,
                'occupancy_rate': 0,
                'total_nourriture': 0,
                'total_boisson': 0,
                'total_bieres': 0,
                'total_vins': 0,
                'total_mineraux': 0,
            }

        days = len(self.daily_metrics)
        total_rooms_sold = sum(m.total_rooms_sold or 0 for m in self.daily_metrics)
        total_room_revenue = sum(m.room_revenue or 0 for m in self.daily_metrics)
        total_location = sum(m.other_revenue or 0 for m in self.daily_metrics)  # placeholder
        total_piazza = sum(m.piazza_total or 0 for m in self.daily_metrics)
        total_banquet = sum(m.banquet_total or 0 for m in self.daily_metrics)
        total_spesa = sum(m.spesa_total or 0 for m in self.daily_metrics)
        total_revenue = sum(m.total_revenue or 0 for m in self.daily_metrics)
        avg_occupancy = sum(m.occupancy_rate or 0 for m in self.daily_metrics) / days if days > 0 else 0
        total_nourriture = sum(m.total_nourriture or 0 for m in self.daily_metrics)
        total_boisson = sum(m.total_boisson or 0 for m in self.daily_metrics)
        total_bieres = sum(m.total_bieres or 0 for m in self.daily_metrics)
        total_vins = sum(m.total_vins or 0 for m in self.daily_metrics)
        total_mineraux = sum(m.total_mineraux or 0 for m in self.daily_metrics)

        adr = (total_room_revenue / total_rooms_sold) if total_rooms_sold > 0 else 0

        return {
            'days': days,
            'rooms_sold': total_rooms_sold,
            'adr': round(adr, 2),
            'room_revenue': round(total_room_revenue, 2),
            'location_salle': round(total_location, 2),
            'giotto': 0,  # Not tracked in DailyJourMetrics
            'piazza': round(total_piazza, 2),
            'cupola': 0,  # Not tracked separately
            'banquet': round(total_banquet, 2),
            'spesa': round(total_spesa, 2),
            'total_revenue': round(total_revenue, 2),
            'occupancy_rate': round(avg_occupancy, 2),
            'total_nourriture': round(total_nourriture, 2),
            'total_boisson': round(total_boisson, 2),
            'total_bieres': round(total_bieres, 2),
            'total_vins': round(total_vins, 2),
            'total_mineraux': round(total_mineraux, 2),
        }

    def get_variance_report(self):
        """
        Calculate full variance analysis.
        Returns: {
            'budget': {...},
            'actual': {...},
            'variance_items': [
                {'category', 'budget', 'actual', 'variance', 'variance_pct', 'favorable'}
            ],
            'month_label': 'janvier 2026',
            'has_budget': True/False,
            'has_actuals': True/False,
        }
        """
        month_names = [
            'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
        ]
        month_label = f"{month_names[self.month - 1]} {self.year}"

        budget_data = self.get_budget_dict()
        actual_data = self.get_actual_data()

        if not budget_data:
            return {
                'budget': None,
                'actual': actual_data,
                'variance_items': [],
                'month_label': month_label,
                'has_budget': False,
                'has_actuals': len(self.daily_metrics) > 0,
                'error': 'Aucun budget saisi pour ce mois',
            }

        if not actual_data or actual_data['days'] == 0:
            return {
                'budget': budget_data,
                'actual': actual_data,
                'variance_items': [],
                'month_label': month_label,
                'has_budget': True,
                'has_actuals': False,
                'error': 'Aucune donnée réelle pour ce mois',
            }

        # Build variance items
        variance_items = []

        # Revenue variances
        categories = [
            ('Chambres', budget_data['room_revenue'], actual_data['room_revenue']),
            ('Piazza', budget_data['piazza'], actual_data['piazza']),
            ('Banquet', budget_data['banquet'], actual_data['banquet']),
            ('Spesa', budget_data['spesa'], actual_data['spesa']),
            ('Giotto', budget_data['giotto'], actual_data['giotto']),
            ('Location Salle', budget_data['location_salle'], actual_data['location_salle']),
        ]

        for category, budget, actual in categories:
            if budget != 0 or actual != 0:
                variance = actual - budget
                variance_pct = (variance / budget * 100) if budget != 0 else (100 if actual > 0 else 0)
                favorable = variance >= 0  # Revenue: positive is favorable
                variance_items.append({
                    'category': category,
                    'budget': round(budget, 2),
                    'actual': round(actual, 2),
                    'variance': round(variance, 2),
                    'variance_pct': round(variance_pct, 2),
                    'favorable': favorable,
                })

        # Total Revenue
        variance = actual_data['total_revenue'] - budget_data['total_revenue']
        variance_pct = (variance / budget_data['total_revenue'] * 100) if budget_data['total_revenue'] != 0 else 0
        variance_items.append({
            'category': 'Revenu Total',
            'budget': round(budget_data['total_revenue'], 2),
            'actual': round(actual_data['total_revenue'], 2),
            'variance': round(variance, 2),
            'variance_pct': round(variance_pct, 2),
            'favorable': variance >= 0,
            'total': True,
        })

        # Occupancy (as KPI)
        rooms_variance = actual_data['rooms_sold'] - budget_data['rooms_target']
        rooms_variance_pct = (rooms_variance / budget_data['rooms_target'] * 100) if budget_data['rooms_target'] != 0 else 0
        variance_items.append({
            'category': 'Chambres Vendues',
            'budget': budget_data['rooms_target'],
            'actual': actual_data['rooms_sold'],
            'variance': rooms_variance,
            'variance_pct': round(rooms_variance_pct, 2),
            'favorable': rooms_variance >= 0,
        })

        # ADR
        adr_variance = actual_data['adr'] - budget_data['adr_target']
        adr_variance_pct = (adr_variance / budget_data['adr_target'] * 100) if budget_data['adr_target'] != 0 else 0
        variance_items.append({
            'category': 'Tarif Moyen (ADR)',
            'budget': round(budget_data['adr_target'], 2),
            'actual': round(actual_data['adr'], 2),
            'variance': round(adr_variance, 2),
            'variance_pct': round(adr_variance_pct, 2),
            'favorable': adr_variance >= 0,
        })

        return {
            'budget': budget_data,
            'actual': actual_data,
            'variance_items': variance_items,
            'month_label': month_label,
            'has_budget': True,
            'has_actuals': True,
        }

    def get_ytd_summary(self):
        """Get year-to-date variance summary."""
        ytd_variance = []

        month_names = [
            'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
        ]

        for m in range(1, 13):
            analyzer = BudgetAnalyzer(self.year, m)
            report = analyzer.get_variance_report()

            if report['has_budget'] and report['has_actuals']:
                # Find revenue total item
                rev_item = next((v for v in report['variance_items'] if v.get('total')), None)
                if rev_item:
                    ytd_variance.append({
                        'month': m,
                        'month_label': month_names[m - 1],
                        'budget': rev_item['budget'],
                        'actual': rev_item['actual'],
                        'variance': rev_item['variance'],
                        'variance_pct': rev_item['variance_pct'],
                    })
                else:
                    ytd_variance.append({
                        'month': m,
                        'month_label': month_names[m - 1],
                        'budget': report['budget']['total_revenue'],
                        'actual': report['actual']['total_revenue'],
                        'variance': report['actual']['total_revenue'] - report['budget']['total_revenue'],
                        'variance_pct': ((report['actual']['total_revenue'] - report['budget']['total_revenue']) / report['budget']['total_revenue'] * 100) if report['budget']['total_revenue'] != 0 else 0,
                    })

        # Calculate YTD totals
        ytd_budget_sum = sum(item['budget'] for item in ytd_variance)
        ytd_actual_sum = sum(item['actual'] for item in ytd_variance)
        ytd_variance_sum = ytd_actual_sum - ytd_budget_sum
        ytd_variance_pct = (ytd_variance_sum / ytd_budget_sum * 100) if ytd_budget_sum != 0 else 0

        return {
            'year': self.year,
            'monthly': ytd_variance,
            'ytd_budget': round(ytd_budget_sum, 2),
            'ytd_actual': round(ytd_actual_sum, 2),
            'ytd_variance': round(ytd_variance_sum, 2),
            'ytd_variance_pct': round(ytd_variance_pct, 2),
        }

    @staticmethod
    def parse_budget_csv(file_content):
        """
        Parse CSV budget import.
        Expected format: first column = field name, subsequent columns = months (Jan-Dec)
        Returns: list of {month: 1-12, data: {...fields}}
        """
        try:
            text = file_content.decode('utf-8') if isinstance(file_content, bytes) else file_content
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)

            if not rows or len(rows) < 2:
                return {'error': 'Fichier CSV vide'}

            # First row = headers (skip first column which is field names)
            headers = rows[0][1:]  # Skip first column
            month_count = len(headers)

            if month_count < 1:
                return {'error': 'Aucune colonne de mois trouvée'}

            budget_by_month = {}
            for m in range(1, month_count + 1):
                budget_by_month[m] = {}

            # Parse rows (each row is a field with values for each month)
            for row in rows[1:]:
                if not row or len(row) < 2:
                    continue

                field_name = row[0].strip().lower()
                if not field_name:
                    continue

                # Map CSV field names to MonthlyBudget columns
                db_field = _map_csv_field_to_db(field_name)
                if not db_field:
                    continue

                for idx, value in enumerate(row[1:]):
                    if idx + 1 <= month_count:
                        try:
                            parsed_val = float(value) if value.strip() else 0
                            budget_by_month[idx + 1][db_field] = parsed_val
                        except (ValueError, AttributeError):
                            pass

            return {'success': True, 'months': budget_by_month}

        except Exception as e:
            return {'error': f'Erreur lors du parsing CSV: {str(e)}'}

    @staticmethod
    def parse_budget_excel(file_content):
        """
        Parse Excel budget import (simplified - uses openpyxl if available).
        Returns same format as parse_budget_csv.
        """
        try:
            import openpyxl
        except ImportError:
            return {
                'error': 'openpyxl non installé. Veuillez importer un fichier CSV à la place.'
            }

        try:
            from io import BytesIO
            wb = openpyxl.load_workbook(BytesIO(file_content))
            ws = wb.active

            if not ws:
                return {'error': 'Classeur Excel vide'}

            # Read all rows
            rows = []
            for row in ws.iter_rows(values_only=True):
                rows.append([str(v) if v is not None else '' for v in row])

            if len(rows) < 2:
                return {'error': 'Fichier Excel insuffisant'}

            # Process like CSV
            headers = rows[0][1:]
            month_count = len(headers)

            if month_count < 1:
                return {'error': 'Aucune colonne de mois trouvée'}

            budget_by_month = {}
            for m in range(1, month_count + 1):
                budget_by_month[m] = {}

            for row in rows[1:]:
                if not row or len(row) < 2:
                    continue

                field_name = str(row[0]).strip().lower()
                if not field_name:
                    continue

                db_field = _map_csv_field_to_db(field_name)
                if not db_field:
                    continue

                for idx, value in enumerate(row[1:]):
                    if idx + 1 <= month_count:
                        try:
                            parsed_val = float(value) if value and str(value).strip() else 0
                            budget_by_month[idx + 1][db_field] = parsed_val
                        except (ValueError, TypeError):
                            pass

            return {'success': True, 'months': budget_by_month}

        except Exception as e:
            return {'error': f'Erreur lors du parsing Excel: {str(e)}'}


def _map_csv_field_to_db(csv_field):
    """Map CSV field names to MonthlyBudget columns."""
    mapping = {
        'rooms_target': 'rooms_target',
        'chambres_target': 'rooms_target',
        'adr_target': 'adr_target',
        'tarif_moyen': 'adr_target',
        'room_revenue': 'room_revenue',
        'revenu_chambres': 'room_revenue',
        'location_salle': 'location_salle',
        'location': 'location_salle',
        'giotto': 'giotto',
        'piazza': 'piazza',
        'cupola': 'cupola',
        'banquet': 'banquet',
        'spesa': 'spesa',
        'total_revenue': 'total_revenue',
        'revenu_total': 'total_revenue',
        'labor_reception': 'labor_reception',
        'labor_femme_chambre': 'labor_femme_chambre',
        'labor_equipier': 'labor_equipier',
        'labor_gouvernante': 'labor_gouvernante',
        'labor_buanderie': 'labor_buanderie',
        'labor_cuisine': 'labor_cuisine',
        'labor_piazza': 'labor_piazza',
        'labor_cupola': 'labor_cupola',
        'labor_banquet': 'labor_banquet',
        'labor_banquet_ii': 'labor_banquet_ii',
        'labor_adm': 'labor_adm',
        'labor_marketing': 'labor_marketing',
        'labor_entretien': 'labor_entretien',
        'marketing': 'marketing',
        'admin': 'admin',
        'entretien': 'entretien',
        'energie': 'energie',
        'taxes_assurances': 'taxes_assurances',
        'amortissement': 'amortissement',
        'interet': 'interet',
        'loyer': 'loyer',
        'cost_variable_chambres': 'cost_variable_chambres',
        'cost_variable_banquet': 'cost_variable_banquet',
        'cost_variable_resto': 'cost_variable_resto',
        'benefits_hebergement': 'benefits_hebergement',
        'benefits_restauration': 'benefits_restauration',
    }

    return mapping.get(csv_field, None)
