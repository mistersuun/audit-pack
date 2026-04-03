"""
STR Competitive Set & OTB (On The Books) — Benchmarking & Forecasting.

Provides:
- STR competitive positioning (index, ranking vs comp set)
- OTB forecasts (future occupancy, ADR, revenue)
- Data import (CSV), seed, and visualization
"""

from flask import Blueprint, request, jsonify, render_template, session
from functools import wraps
from datetime import datetime, date as date_type, timedelta
from database.models import db, STRCompSet, OTBForecast, DailyJourMetrics, TOTAL_ROOMS
from utils.auth_decorators import login_required, role_required
from sqlalchemy import func
import csv
import io
import logging
import json

logger = logging.getLogger(__name__)

compset_bp = Blueprint('compset', __name__, url_prefix='/compset')


# ═══════════════════════════════════════════════════════════════════════════════
# OTB PROJECTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def _booking_curve_factor(days_out):
    """
    Booking curve ramp — models how occupancy fills as the stay date approaches.

    Returns a multiplier (0.0–1.0) representing what fraction of final
    occupancy is typically "on the books" at this lead time.

    Based on typical full-service hotel booking patterns:
    - 1 day out:  ~95% of final occ is already booked
    - 7 days out: ~85%
    - 30 days:    ~60%
    - 60 days:    ~40%
    - 90 days:    ~30%
    """
    if days_out <= 0:
        return 1.0
    if days_out <= 1:
        return 0.95
    if days_out <= 3:
        return 0.90
    if days_out <= 7:
        return 0.85
    if days_out <= 14:
        return 0.75
    if days_out <= 30:
        return 0.60
    if days_out <= 45:
        return 0.50
    if days_out <= 60:
        return 0.40
    if days_out <= 75:
        return 0.35
    return 0.30


def generate_otb_projections(snapshot_date=None, days_forward=90):
    """
    Generate OTB projections for `days_forward` days using historical DailyJourMetrics.

    For each future target day:
    1. SDLY (Same Day Last Year): direct lookup in DailyJourMetrics
    2. DOW average: average of same day-of-week over the last 52 weeks
    3. Blend: prefer SDLY if available, fall back to DOW average
    4. Apply booking curve ramp based on days-out
    5. Split into group (~35%) / transient (~65%)

    Returns: dict with 'created' count and 'summary' stats.
    Raises: ValueError if insufficient historical data.
    """
    if snapshot_date is None:
        snapshot_date = date_type.today()

    # ── Gather historical context ─────────────────────────────────────────
    # DOW averages over the last 52 weeks (364 days)
    dow_start = snapshot_date - timedelta(days=364)
    historical = DailyJourMetrics.query.filter(
        DailyJourMetrics.date >= dow_start,
        DailyJourMetrics.date < snapshot_date,
    ).all()

    if len(historical) < 30:
        raise ValueError(
            f"Donnees historiques insuffisantes: {len(historical)} jours "
            f"(minimum 30 requis)."
        )

    # Build DOW lookup: {0: Monday, ..., 6: Sunday} → list of metrics
    dow_data = {i: [] for i in range(7)}
    for m in historical:
        dow_data[m.date.weekday()].append(m)

    # Build date lookup for SDLY
    # Target dates range from snapshot+1 to snapshot+days_forward.
    # SDLY for each is target - 365, so the range is:
    #   earliest: (snapshot + 1) - 365 = snapshot - 364
    #   latest:   (snapshot + days_forward) - 365
    # Add +/-2 day buffer for leap-year fallback.
    sdly_lookup = {}
    sdly_range_start = snapshot_date - timedelta(days=366)
    sdly_range_end = snapshot_date + timedelta(days=days_forward) - timedelta(days=363)
    sdly_metrics = DailyJourMetrics.query.filter(
        DailyJourMetrics.date >= sdly_range_start,
        DailyJourMetrics.date <= sdly_range_end,
    ).all()
    for m in sdly_metrics:
        sdly_lookup[m.date] = m

    # ── Generate projections ──────────────────────────────────────────────
    created = 0
    total_rooms = 0
    total_revenue = 0.0

    for d in range(1, days_forward + 1):
        target = snapshot_date + timedelta(days=d)
        dow = target.weekday()

        # --- SDLY lookup ---
        sdly_date = target - timedelta(days=365)
        # Also check +/- 1 day to handle leap years
        sdly = sdly_lookup.get(sdly_date)
        if sdly is None:
            sdly = sdly_lookup.get(sdly_date - timedelta(days=1))
        if sdly is None:
            sdly = sdly_lookup.get(sdly_date + timedelta(days=1))

        # --- DOW average ---
        dow_entries = dow_data.get(dow, [])
        if dow_entries:
            dow_occ = sum(e.occupancy_rate or 0 for e in dow_entries) / len(dow_entries)
            dow_adr = sum(e.adr or 0 for e in dow_entries) / len(dow_entries)
        else:
            # Fallback: global average
            dow_occ = sum(e.occupancy_rate or 0 for e in historical) / len(historical)
            dow_adr = sum(e.adr or 0 for e in historical) / len(historical)

        # --- Blend SDLY and DOW: prefer SDLY when available ---
        if sdly and (sdly.occupancy_rate or 0) > 0:
            # 60% SDLY weight, 40% DOW average
            forecast_occ = 0.6 * (sdly.occupancy_rate or 0) + 0.4 * dow_occ
            forecast_adr = 0.6 * (sdly.adr or 0) + 0.4 * dow_adr
        else:
            # DOW average only
            forecast_occ = dow_occ
            forecast_adr = dow_adr

        # --- Apply booking curve ramp ---
        ramp = _booking_curve_factor(d)
        ramped_occ = forecast_occ * ramp

        # Clamp occupancy between 0 and 100
        ramped_occ = max(0.0, min(100.0, ramped_occ))

        rooms_otb = int(round(ramped_occ * TOTAL_ROOMS / 100))
        rooms_otb = max(0, min(TOTAL_ROOMS, rooms_otb))

        adr_otb = round(forecast_adr, 2) if forecast_adr > 0 else 0
        revenue_otb = round(rooms_otb * adr_otb, 2)

        # --- Group / Transient split (35/65 default) ---
        group_rooms = int(round(rooms_otb * 0.35))
        transient_rooms = rooms_otb - group_rooms

        # --- SDLY values for comparison columns ---
        ly_rooms = sdly.total_rooms_sold if sdly else None
        ly_occ = round(sdly.occupancy_rate, 1) if sdly and sdly.occupancy_rate else None
        ly_adr = round(sdly.adr, 2) if sdly and sdly.adr else None
        ly_revenue = round(sdly.room_revenue, 2) if sdly and sdly.room_revenue else None

        # --- Upsert ---
        existing = OTBForecast.query.filter_by(
            snapshot_date=snapshot_date,
            target_date=target,
        ).first()

        if existing:
            existing.rooms_otb = rooms_otb
            existing.occ_otb = round(ramped_occ, 1)
            existing.adr_otb = adr_otb
            existing.revenue_otb = revenue_otb
            existing.group_rooms = group_rooms
            existing.transient_rooms = transient_rooms
            existing.ly_rooms = ly_rooms
            existing.ly_occ = ly_occ
            existing.ly_adr = ly_adr
            existing.ly_revenue = ly_revenue
            existing.source = 'auto_forecast'
        else:
            record = OTBForecast(
                snapshot_date=snapshot_date,
                target_date=target,
                rooms_otb=rooms_otb,
                rooms_available=TOTAL_ROOMS,
                occ_otb=round(ramped_occ, 1),
                adr_otb=adr_otb,
                revenue_otb=revenue_otb,
                group_rooms=group_rooms,
                transient_rooms=transient_rooms,
                ly_rooms=ly_rooms,
                ly_occ=ly_occ,
                ly_adr=ly_adr,
                ly_revenue=ly_revenue,
                source='auto_forecast',
            )
            db.session.add(record)

        created += 1
        total_rooms += rooms_otb
        total_revenue += revenue_otb

    db.session.commit()

    avg_occ = round(total_rooms / (TOTAL_ROOMS * days_forward) * 100, 1) if days_forward > 0 else 0
    avg_adr = round(total_revenue / total_rooms, 2) if total_rooms > 0 else 0

    return {
        'created': created,
        'snapshot_date': snapshot_date.isoformat(),
        'days_forward': days_forward,
        'historical_days_used': len(historical),
        'summary': {
            'avg_occ_otb': avg_occ,
            'avg_adr_otb': avg_adr,
            'total_revenue': round(total_revenue, 2),
            'total_rooms': total_rooms,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTE
# ═══════════════════════════════════════════════════════════════════════════════

@compset_bp.route('/')
@login_required
def compset_page():
    """Main STR & OTB page."""
    return render_template('compset.html')


# ═══════════════════════════════════════════════════════════════════════════════
# STR COMPETITIVE SET API
# ═══════════════════════════════════════════════════════════════════════════════

@compset_bp.route('/api/str', methods=['GET'])
@login_required
def get_str_data():
    """
    Get STR data for date range.

    Query params:
    - start_date: YYYY-MM-DD (default: 90 days ago)
    - end_date: YYYY-MM-DD (default: today)
    """
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')

    # Parse dates with defaults
    try:
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date() if end_str else date_type.today()
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else end_date - timedelta(days=90)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Query data
    records = STRCompSet.query.filter(
        STRCompSet.report_date >= start_date,
        STRCompSet.report_date <= end_date
    ).order_by(STRCompSet.report_date).all()

    data = [r.to_dict() for r in records]

    return jsonify({
        'count': len(data),
        'data': data,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
    })


@compset_bp.route('/api/str/import', methods=['POST'])
@login_required
def import_str_data():
    """
    Import STR data from CSV upload.

    Expected CSV columns:
    report_date, period_type, my_occ, my_adr, my_revpar,
    comp_occ, comp_adr, comp_revpar, occ_rank, adr_rank, revpar_rank, comp_set_size
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni.'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'Fichier vide.'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Seuls les fichiers CSV sont acceptés.'}), 400

    try:
        stream = io.TextIOWrapper(file.stream, encoding='utf-8-sig')
        reader = csv.DictReader(stream)

        imported_count = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                report_date = datetime.strptime(row['report_date'], '%Y-%m-%d').date()

                # Check if record exists
                existing = STRCompSet.query.filter_by(
                    report_date=report_date,
                    period_type=row.get('period_type', 'daily')
                ).first()

                if existing:
                    # Update
                    existing.my_occ = float(row.get('my_occ', 0))
                    existing.my_adr = float(row.get('my_adr', 0))
                    existing.my_revpar = float(row.get('my_revpar', 0))
                    existing.comp_occ = float(row.get('comp_occ', 0))
                    existing.comp_adr = float(row.get('comp_adr', 0))
                    existing.comp_revpar = float(row.get('comp_revpar', 0))
                    existing.occ_rank = int(row.get('occ_rank', 0)) or None
                    existing.adr_rank = int(row.get('adr_rank', 0)) or None
                    existing.revpar_rank = int(row.get('revpar_rank', 0)) or None
                    existing.comp_set_size = int(row.get('comp_set_size', 5))
                    existing.source = 'import'
                else:
                    # Create new
                    record = STRCompSet(
                        report_date=report_date,
                        period_type=row.get('period_type', 'daily'),
                        my_occ=float(row.get('my_occ', 0)),
                        my_adr=float(row.get('my_adr', 0)),
                        my_revpar=float(row.get('my_revpar', 0)),
                        comp_occ=float(row.get('comp_occ', 0)),
                        comp_adr=float(row.get('comp_adr', 0)),
                        comp_revpar=float(row.get('comp_revpar', 0)),
                        occ_rank=int(row.get('occ_rank', 0)) or None,
                        adr_rank=int(row.get('adr_rank', 0)) or None,
                        revpar_rank=int(row.get('revpar_rank', 0)) or None,
                        comp_set_size=int(row.get('comp_set_size', 5)),
                        source='import',
                    )
                    db.session.add(record)

                imported_count += 1
            except (ValueError, KeyError) as e:
                errors.append(f'Ligne {row_num}: {str(e)}')

        db.session.commit()

        return jsonify({
            'success': True,
            'imported': imported_count,
            'errors': errors,
            'message': f'{imported_count} enregistrements importés.'
        })
    except Exception as e:
        logger.error(f'STR import error: {e}')
        return jsonify({'error': f'Erreur lors de l\'import: {str(e)}'}), 500


@compset_bp.route('/api/str/seed', methods=['GET'])
@login_required
def seed_str_data():
    """Generate realistic demo STR data for past 90 days."""
    import random

    end_date = date_type.today()
    start_date = end_date - timedelta(days=90)

    # Delete existing seed data
    STRCompSet.query.filter(STRCompSet.source == 'seed').delete()

    current = start_date
    created_count = 0

    while current <= end_date:
        # Realistic ranges for a Sheraton
        my_occ = random.uniform(70, 95)
        comp_occ = random.uniform(72, 88)
        my_adr = random.uniform(140, 220)
        comp_adr = random.uniform(130, 210)
        my_revpar = (my_occ / 100) * my_adr
        comp_revpar = (comp_occ / 100) * comp_adr

        # Index calculation
        occ_index = round((my_occ / comp_occ) * 100, 1) if comp_occ > 0 else 100
        adr_index = round((my_adr / comp_adr) * 100, 1) if comp_adr > 0 else 100
        revpar_index = round((my_revpar / comp_revpar) * 100, 1) if comp_revpar > 0 else 100

        # Rank (simulated 1-6 out of 6 comp set)
        occ_rank = random.randint(2, 5) if random.random() > 0.3 else None
        adr_rank = random.randint(2, 5) if random.random() > 0.3 else None
        revpar_rank = random.randint(2, 5) if random.random() > 0.3 else None

        record = STRCompSet(
            report_date=current,
            period_type='daily',
            my_occ=round(my_occ, 1),
            my_adr=round(my_adr, 2),
            my_revpar=round(my_revpar, 2),
            comp_occ=round(comp_occ, 1),
            comp_adr=round(comp_adr, 2),
            comp_revpar=round(comp_revpar, 2),
            occ_index=occ_index,
            adr_index=adr_index,
            revpar_index=revpar_index,
            occ_rank=occ_rank,
            adr_rank=adr_rank,
            revpar_rank=revpar_rank,
            comp_set_size=6,
            source='seed',
        )
        db.session.add(record)
        created_count += 1
        current += timedelta(days=1)

    db.session.commit()

    return jsonify({
        'success': True,
        'created': created_count,
        'message': f'{created_count} jours de données STR créés.'
    })


# ═══════════════════════════════════════════════════════════════════════════════
# OTB FORECAST API
# ═══════════════════════════════════════════════════════════════════════════════

@compset_bp.route('/api/otb', methods=['GET'])
@login_required
def get_otb_data():
    """
    Get OTB forecast data.

    Query params:
    - snapshot_date: YYYY-MM-DD (default: today)
    - days: number of days forward (default: 90)

    Auto-generates projections from historical data if no rows exist
    for the requested snapshot_date.
    """
    snapshot_str = request.args.get('snapshot_date')
    days = request.args.get('days', '90', type=int)

    # Parse date
    try:
        snapshot_date = datetime.strptime(snapshot_str, '%Y-%m-%d').date() if snapshot_str else date_type.today()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Query data
    end_date = snapshot_date + timedelta(days=days)
    records = OTBForecast.query.filter(
        OTBForecast.snapshot_date == snapshot_date,
        OTBForecast.target_date <= end_date
    ).order_by(OTBForecast.target_date).all()

    # Auto-generate if no data exists for this snapshot
    if not records:
        try:
            result = generate_otb_projections(snapshot_date, days)
            logger.info(
                "OTB auto-generation: %d jours crees pour snapshot %s",
                result['created'], snapshot_date.isoformat()
            )
            # Re-query after generation
            records = OTBForecast.query.filter(
                OTBForecast.snapshot_date == snapshot_date,
                OTBForecast.target_date <= end_date
            ).order_by(OTBForecast.target_date).all()
        except ValueError as e:
            logger.warning("OTB auto-generation impossible: %s", e)
            # Return empty — not enough historical data
        except Exception as e:
            logger.error("OTB auto-generation error: %s", e)
            db.session.rollback()

    data = [r.to_dict() for r in records]

    return jsonify({
        'count': len(data),
        'data': data,
        'snapshot_date': snapshot_date.isoformat(),
        'days': days,
    })


@compset_bp.route('/api/otb/generate', methods=['POST'])
@login_required
def generate_otb_endpoint():
    """
    Generate 90-day OTB projections from historical DailyJourMetrics.

    Optional JSON body:
    - snapshot_date: YYYY-MM-DD (default: today)
    - days: integer (default: 90)
    """
    data = request.get_json(silent=True) or {}
    try:
        snap_str = data.get('snapshot_date')
        snapshot_date = (
            datetime.strptime(snap_str, '%Y-%m-%d').date()
            if snap_str else date_type.today()
        )
        days_forward = int(data.get('days', 90))
    except (ValueError, TypeError):
        return jsonify({'error': 'Format de date invalide (YYYY-MM-DD).'}), 400

    try:
        result = generate_otb_projections(snapshot_date, days_forward)
        return jsonify({
            'success': True,
            'message': f"{result['created']} jours de projections OTB generes.",
            **result,
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error('OTB generate error: %s', e)
        db.session.rollback()
        return jsonify({'error': f'Erreur: {str(e)}'}), 500


@compset_bp.route('/api/otb/import', methods=['POST'])
@login_required
def import_otb_data():
    """
    Import OTB data from CSV upload.

    Expected CSV columns:
    snapshot_date, target_date, rooms_otb, occ_otb, adr_otb, revenue_otb,
    group_rooms, transient_rooms, ly_rooms, ly_occ, ly_adr, ly_revenue
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni.'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'Fichier vide.'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Seuls les fichiers CSV sont acceptés.'}), 400

    try:
        stream = io.TextIOWrapper(file.stream, encoding='utf-8-sig')
        reader = csv.DictReader(stream)

        imported_count = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                snapshot_date = datetime.strptime(row['snapshot_date'], '%Y-%m-%d').date()
                target_date = datetime.strptime(row['target_date'], '%Y-%m-%d').date()

                # Check if record exists
                existing = OTBForecast.query.filter_by(
                    snapshot_date=snapshot_date,
                    target_date=target_date
                ).first()

                if existing:
                    # Update
                    existing.rooms_otb = int(row.get('rooms_otb', 0))
                    existing.occ_otb = float(row.get('occ_otb', 0))
                    existing.adr_otb = float(row.get('adr_otb', 0))
                    existing.revenue_otb = float(row.get('revenue_otb', 0))
                    existing.group_rooms = int(row.get('group_rooms', 0))
                    existing.transient_rooms = int(row.get('transient_rooms', 0))
                    existing.ly_rooms = int(row.get('ly_rooms', 0)) or None
                    existing.ly_occ = float(row.get('ly_occ', 0)) or None
                    existing.ly_adr = float(row.get('ly_adr', 0)) or None
                    existing.ly_revenue = float(row.get('ly_revenue', 0)) or None
                    existing.source = 'import'
                else:
                    # Create new
                    record = OTBForecast(
                        snapshot_date=snapshot_date,
                        target_date=target_date,
                        rooms_otb=int(row.get('rooms_otb', 0)),
                        occ_otb=float(row.get('occ_otb', 0)),
                        adr_otb=float(row.get('adr_otb', 0)),
                        revenue_otb=float(row.get('revenue_otb', 0)),
                        group_rooms=int(row.get('group_rooms', 0)),
                        transient_rooms=int(row.get('transient_rooms', 0)),
                        ly_rooms=int(row.get('ly_rooms', 0)) or None,
                        ly_occ=float(row.get('ly_occ', 0)) or None,
                        ly_adr=float(row.get('ly_adr', 0)) or None,
                        ly_revenue=float(row.get('ly_revenue', 0)) or None,
                        source='import',
                    )
                    db.session.add(record)

                imported_count += 1
            except (ValueError, KeyError) as e:
                errors.append(f'Ligne {row_num}: {str(e)}')

        db.session.commit()

        return jsonify({
            'success': True,
            'imported': imported_count,
            'errors': errors,
            'message': f'{imported_count} enregistrements importés.'
        })
    except Exception as e:
        logger.error(f'OTB import error: {e}')
        return jsonify({'error': f'Erreur lors de l\'import: {str(e)}'}), 500


@compset_bp.route('/api/otb/manual', methods=['POST'])
@login_required
def save_otb_manual():
    """Save manual OTB entry."""
    data = request.get_json()

    try:
        snapshot_date = datetime.strptime(data['snapshot_date'], '%Y-%m-%d').date()
        target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()

        # Check if exists
        existing = OTBForecast.query.filter_by(
            snapshot_date=snapshot_date,
            target_date=target_date
        ).first()

        if existing:
            existing.rooms_otb = data.get('rooms_otb', 0)
            existing.occ_otb = data.get('occ_otb', 0)
            existing.adr_otb = data.get('adr_otb', 0)
            existing.revenue_otb = data.get('revenue_otb', 0)
            existing.group_rooms = data.get('group_rooms', 0)
            existing.transient_rooms = data.get('transient_rooms', 0)
            existing.ly_rooms = data.get('ly_rooms')
            existing.ly_occ = data.get('ly_occ')
            existing.ly_adr = data.get('ly_adr')
            existing.ly_revenue = data.get('ly_revenue')
            existing.source = 'manual'
        else:
            record = OTBForecast(
                snapshot_date=snapshot_date,
                target_date=target_date,
                rooms_otb=data.get('rooms_otb', 0),
                occ_otb=data.get('occ_otb', 0),
                adr_otb=data.get('adr_otb', 0),
                revenue_otb=data.get('revenue_otb', 0),
                group_rooms=data.get('group_rooms', 0),
                transient_rooms=data.get('transient_rooms', 0),
                ly_rooms=data.get('ly_rooms'),
                ly_occ=data.get('ly_occ'),
                ly_adr=data.get('ly_adr'),
                ly_revenue=data.get('ly_revenue'),
                source='manual',
            )
            db.session.add(record)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Entrée OTB sauvegardée.'
        })
    except Exception as e:
        logger.error(f'OTB save error: {e}')
        db.session.rollback()
        return jsonify({'error': f'Erreur: {str(e)}'}), 500


@compset_bp.route('/api/otb/snapshot', methods=['POST'])
@login_required
def create_otb_snapshot():
    """
    Create OTB snapshot for today from latest available data.
    Copies yesterday's snapshot forward (rolling forecast).
    """
    today = date_type.today()

    try:
        # Get yesterday's snapshot
        yesterday = today - timedelta(days=1)
        yesterday_records = OTBForecast.query.filter_by(snapshot_date=yesterday).all()

        created_count = 0

        if yesterday_records:
            for rec in yesterday_records:
                # Shift target_date forward by 1 day
                new_target = rec.target_date + timedelta(days=1)

                # Check if today's record for this target exists
                existing = OTBForecast.query.filter_by(
                    snapshot_date=today,
                    target_date=new_target
                ).first()

                if not existing:
                    new_record = OTBForecast(
                        snapshot_date=today,
                        target_date=new_target,
                        rooms_otb=rec.rooms_otb,
                        occ_otb=rec.occ_otb,
                        adr_otb=rec.adr_otb,
                        revenue_otb=rec.revenue_otb,
                        group_rooms=rec.group_rooms,
                        transient_rooms=rec.transient_rooms,
                        ly_rooms=rec.ly_rooms,
                        ly_occ=rec.ly_occ,
                        ly_adr=rec.ly_adr,
                        ly_revenue=rec.ly_revenue,
                        source='snapshot',
                    )
                    db.session.add(new_record)
                    created_count += 1

        # Also add one new day 90 days out
        far_future = today + timedelta(days=90)
        existing_far = OTBForecast.query.filter_by(
            snapshot_date=today,
            target_date=far_future
        ).first()

        if not existing_far:
            # Estimate for far future
            far_record = OTBForecast(
                snapshot_date=today,
                target_date=far_future,
                rooms_otb=180,
                occ_otb=71.4,
                adr_otb=170,
                revenue_otb=12138,
                group_rooms=80,
                transient_rooms=100,
                source='snapshot',
            )
            db.session.add(far_record)
            created_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'created': created_count,
            'message': f'Snapshot créé avec {created_count} jours.'
        })
    except Exception as e:
        logger.error(f'OTB snapshot error: {e}')
        db.session.rollback()
        return jsonify({'error': f'Erreur: {str(e)}'}), 500


@compset_bp.route('/api/otb/seed', methods=['GET'])
@login_required
def seed_otb_data():
    """
    Generate OTB projections from historical data (replaces dummy seed).

    Deletes any prior seed/auto_forecast rows for today's snapshot, then
    runs the projection engine.  Falls back to the old random approach
    only if historical data is insufficient (< 30 days).
    """
    today = date_type.today()

    # Clear previous auto-generated and seed data for today
    OTBForecast.query.filter(
        OTBForecast.snapshot_date == today,
        OTBForecast.source.in_(['seed', 'auto_forecast']),
    ).delete(synchronize_session='fetch')
    db.session.commit()

    try:
        result = generate_otb_projections(today, 90)
        return jsonify({
            'success': True,
            'created': result['created'],
            'message': (
                f"{result['created']} jours de projections OTB generes "
                f"a partir de {result['historical_days_used']} jours historiques."
            ),
        })
    except ValueError as e:
        # Not enough historical data — inform the user
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Impossible de generer les projections: donnees historiques insuffisantes.',
        }), 400
    except Exception as e:
        logger.error('OTB seed/generate error: %s', e)
        db.session.rollback()
        return jsonify({'error': f'Erreur: {str(e)}'}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_date(date_str):
    """
    Parse a YYYY-MM-DD string into a date object.
    Returns None if date_str is None.
    Raises ValueError for malformed strings (caller is responsible for the 400).
    """
    if date_str is None:
        return None
    return datetime.strptime(date_str, '%Y-%m-%d').date()


# ═══════════════════════════════════════════════════════════════════════════════
# OTB PACE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

@compset_bp.route('/api/otb-pace', methods=['GET'])
@login_required
def get_otb_pace():
    """
    OTB Pace Analysis — per-day on-the-books position with pick-up vs a prior snapshot.

    Query params:
    - snapshot_date: YYYY-MM-DD (default: most recent snapshot_date in DB)
    - days: integer, days forward to cover (default: 60)
    - compare_snapshot: YYYY-MM-DD (default: snapshot_date - 7 days)

    Pick-up is defined as the change in rooms_otb between the current snapshot and
    the comparison snapshot for the same target_date.  A positive number means
    reservations were added in that window.

    Seed data is excluded so live / imported / manual entries are not polluted.
    """
    try:
        snap_str = request.args.get('snapshot_date')
        days = request.args.get('days', 60, type=int)
        comp_str = request.args.get('compare_snapshot')

        current_snap = _parse_date(snap_str)
        compare_snap_override = _parse_date(comp_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Resolve current snapshot — use the latest date available if none provided.
    if current_snap is None:
        current_snap = db.session.query(
            func.max(OTBForecast.snapshot_date)
        ).filter(OTBForecast.source != 'seed').scalar()

        if current_snap is None:
            return jsonify({'success': True, 'has_data': False, 'reason': 'no_otb_data'})

    # Resolve comparison snapshot.
    compare_snap = compare_snap_override if compare_snap_override else current_snap - timedelta(days=7)

    # Fetch current snapshot rows for the next `days` calendar days after the snapshot.
    end_target = current_snap + timedelta(days=days)
    current_rows = OTBForecast.query.filter(
        OTBForecast.snapshot_date == current_snap,
        OTBForecast.target_date > current_snap,
        OTBForecast.target_date <= end_target,
        OTBForecast.source != 'seed',
    ).order_by(OTBForecast.target_date).all()

    if not current_rows:
        return jsonify({
            'success': True,
            'has_data': False,
            'reason': 'no_rows_for_snapshot',
            'snapshot_date': current_snap.isoformat(),
        })

    # Fetch comparison snapshot rows for the same target window.
    compare_rows = OTBForecast.query.filter(
        OTBForecast.snapshot_date == compare_snap,
        OTBForecast.target_date > current_snap,
        OTBForecast.target_date <= end_target,
        OTBForecast.source != 'seed',
    ).order_by(OTBForecast.target_date).all()

    # O(1) lookup by target_date.
    compare_map = {r.target_date: r for r in compare_rows}
    compare_found = len(compare_rows) > 0

    # ── Per-day records ──────────────────────────────────────────────────────
    days_data = []
    for row in current_rows:
        comp = compare_map.get(row.target_date)
        rooms_otb = row.rooms_otb or 0

        pickup_rooms = (rooms_otb - comp.rooms_otb) if comp and comp.rooms_otb is not None else None
        pickup_revenue = (
            (row.revenue_otb or 0) - (comp.revenue_otb or 0)
        ) if comp and comp.revenue_otb is not None else None

        days_data.append({
            'target_date':       row.target_date.isoformat(),
            'day_of_week':       row.target_date.strftime('%A'),
            'days_out':          (row.target_date - current_snap).days,
            # Current OTB
            'rooms_otb':         rooms_otb,
            'occ_otb_pct':       round(rooms_otb / TOTAL_ROOMS * 100, 1),
            'adr_otb':           round(row.adr_otb or 0, 2),
            'revenue_otb':       round(row.revenue_otb or 0, 2),
            # Segment split
            'group_rooms':       row.group_rooms or 0,
            'transient_rooms':   row.transient_rooms or 0,
            'group_pct':         round((row.group_rooms or 0) / rooms_otb * 100, 1) if rooms_otb else 0,
            # LY comparison (stored on the current row — same snapshot carries LY data)
            'ly_rooms':          row.ly_rooms,
            'ly_occ_pct':        round(row.ly_rooms / TOTAL_ROOMS * 100, 1) if row.ly_rooms is not None else None,
            'ly_adr':            round(row.ly_adr, 2) if row.ly_adr is not None else None,
            'ly_revenue':        round(row.ly_revenue, 2) if row.ly_revenue is not None else None,
            'vs_ly_rooms':       (rooms_otb - row.ly_rooms) if row.ly_rooms is not None else None,
            'vs_ly_rooms_pct':   round((rooms_otb - row.ly_rooms) / row.ly_rooms * 100, 1)
                                 if row.ly_rooms else None,
            'vs_ly_revenue_pct': round(((row.revenue_otb or 0) - row.ly_revenue) / row.ly_revenue * 100, 1)
                                 if row.ly_revenue else None,
            # Pick-up vs comparison snapshot
            'pickup_rooms':      pickup_rooms,
            'pickup_revenue':    round(pickup_revenue, 2) if pickup_revenue is not None else None,
            'compare_snapshot':  compare_snap.isoformat() if comp else None,
        })

    # ── Summary aggregates ───────────────────────────────────────────────────
    total_rooms_otb   = sum(r.rooms_otb or 0 for r in current_rows)
    total_revenue_otb = sum(r.revenue_otb or 0 for r in current_rows)
    total_group       = sum(r.group_rooms or 0 for r in current_rows)
    total_transient   = sum(r.transient_rooms or 0 for r in current_rows)

    # LY aggregates — only count rows that actually have LY data.
    ly_rows_with_data  = [r for r in current_rows if r.ly_rooms is not None]
    total_ly_rooms     = sum(r.ly_rooms for r in ly_rows_with_data)
    ly_rev_rows        = [r for r in current_rows if r.ly_revenue is not None]
    total_ly_revenue   = sum(r.ly_revenue for r in ly_rev_rows)

    avg_adr_otb = total_revenue_otb / total_rooms_otb if total_rooms_otb > 0 else 0
    avg_occ_otb_pct = round(total_rooms_otb / (TOTAL_ROOMS * len(current_rows)) * 100, 1) if current_rows else 0

    # vs-LY at aggregate level (avoids averaging per-row percentages, which is statistically wrong).
    vs_ly_rooms_pct = round(
        (total_rooms_otb - total_ly_rooms) / total_ly_rooms * 100, 2
    ) if total_ly_rooms else None

    vs_ly_revenue_pct = round(
        (total_revenue_otb - total_ly_revenue) / total_ly_revenue * 100, 2
    ) if total_ly_revenue else None

    pickup_rooms_7d = sum(
        d['pickup_rooms'] for d in days_data if d['pickup_rooms'] is not None
    )

    # Percentage of days for which we have LY occupancy data.
    ly_coverage_pct = round(len(ly_rows_with_data) / len(current_rows) * 100, 1) if current_rows else 0

    summary = {
        'total_rooms_otb':       total_rooms_otb,
        'total_revenue_otb':     round(total_revenue_otb, 2),
        'avg_occ_otb_pct':       avg_occ_otb_pct,
        'avg_adr_otb':           round(avg_adr_otb, 2),
        'total_group_rooms':     total_group,
        'total_transient_rooms': total_transient,
        'group_pct':             round(total_group / total_rooms_otb * 100, 1) if total_rooms_otb else 0,
        'vs_ly_rooms_pct':       vs_ly_rooms_pct,
        'vs_ly_revenue_pct':     vs_ly_revenue_pct,
        'pickup_rooms_7d':       pickup_rooms_7d,
        'ly_coverage_pct':       ly_coverage_pct,
    }

    return jsonify({
        'success':          True,
        'has_data':         True,
        'snapshot_date':    current_snap.isoformat(),
        'compare_snapshot': compare_snap.isoformat(),
        'compare_found':    compare_found,
        'days_requested':   days,
        'days_returned':    len(days_data),
        'summary':          summary,
        'daily':            days_data,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# STR INDEX TRENDS
# ═══════════════════════════════════════════════════════════════════════════════

@compset_bp.route('/api/str-trends', methods=['GET'])
@login_required
def get_str_trends():
    """
    STR Index Trends — monthly penetration indices and rank history.

    Query params:
    - start_date: YYYY-MM-DD (default: 12 months ago)
    - end_date: YYYY-MM-DD (default: today)
    - period_type: 'daily' or 'monthly' (default: 'daily')

    Index methodology: compute mean(my_metric) / mean(comp_metric) * 100 at the
    monthly bucket level.  Averaging the stored daily indices is statistically
    incorrect because ratio data is not additive.  This approach is consistent
    with STR's own published methodology for custom date ranges.

    When period_type='monthly', rows are already aggregated by the data provider
    and are used as-is without further re-aggregation.
    """
    try:
        end_date = _parse_date(request.args.get('end_date')) or date_type.today()
        start_date = _parse_date(request.args.get('start_date')) or (end_date - timedelta(days=365))
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    period_type = request.args.get('period_type', 'daily')
    if period_type not in ('daily', 'monthly'):
        return jsonify({'error': "period_type must be 'daily' or 'monthly'."}), 400

    # ── Raw STR records ──────────────────────────────────────────────────────
    str_rows = STRCompSet.query.filter(
        STRCompSet.report_date.between(start_date, end_date),
        STRCompSet.period_type == period_type,
    ).order_by(STRCompSet.report_date).all()

    if not str_rows:
        return jsonify({
            'success':    True,
            'has_data':   False,
            'start_date': start_date.isoformat(),
            'end_date':   end_date.isoformat(),
            'period_type': period_type,
        })

    # ── Local aggregation helpers ────────────────────────────────────────────
    def _mean(lst):
        return round(sum(lst) / len(lst), 2) if lst else None

    def _index(my, comp):
        """Compute an index = my/comp*100, returning None if comp is 0 or missing."""
        if not comp:
            return None
        return round(my / comp * 100, 1)

    # ── Monthly aggregation ──────────────────────────────────────────────────
    # For period_type='monthly': each row is already one month — still run
    # through the same bucketing to produce a uniform monthly_trend structure.
    monthly: dict = {}
    for r in str_rows:
        key = f"{r.report_date.year}-{r.report_date.month:02d}"
        if key not in monthly:
            monthly[key] = {
                'my_occ':      [], 'my_adr':      [], 'my_revpar':      [],
                'comp_occ':    [], 'comp_adr':    [], 'comp_revpar':    [],
                'occ_rank':    [], 'adr_rank':    [], 'revpar_rank':    [],
                # Take comp_set_size from first row of the bucket.
                'comp_set_size': r.comp_set_size or 6,
            }
        monthly[key]['my_occ'].append(r.my_occ or 0)
        monthly[key]['my_adr'].append(r.my_adr or 0)
        monthly[key]['my_revpar'].append(r.my_revpar or 0)
        monthly[key]['comp_occ'].append(r.comp_occ or 0)
        monthly[key]['comp_adr'].append(r.comp_adr or 0)
        monthly[key]['comp_revpar'].append(r.comp_revpar or 0)
        # Only append rank when present — None ranks are excluded from averages.
        if r.occ_rank:
            monthly[key]['occ_rank'].append(r.occ_rank)
        if r.adr_rank:
            monthly[key]['adr_rank'].append(r.adr_rank)
        if r.revpar_rank:
            monthly[key]['revpar_rank'].append(r.revpar_rank)

    # ── Build monthly trend list ─────────────────────────────────────────────
    LOW_SAMPLE_THRESHOLD = 7  # Flag months with fewer than 7 daily observations.

    monthly_trend = []
    for key in sorted(monthly.keys()):
        m = monthly[key]
        my_occ      = _mean(m['my_occ'])
        comp_occ    = _mean(m['comp_occ'])
        my_adr      = _mean(m['my_adr'])
        comp_adr    = _mean(m['comp_adr'])
        my_revpar   = _mean(m['my_revpar'])
        comp_revpar = _mean(m['comp_revpar'])
        day_count   = len(m['my_occ'])

        monthly_trend.append({
            'period':           key,
            'my_occ':           my_occ,
            'comp_occ':         comp_occ,
            'occ_index':        _index(my_occ, comp_occ),
            'my_adr':           my_adr,
            'comp_adr':         comp_adr,
            'adr_index':        _index(my_adr, comp_adr),
            'my_revpar':        my_revpar,
            'comp_revpar':      comp_revpar,
            'revpar_index':     _index(my_revpar, comp_revpar),
            'avg_occ_rank':     _mean(m['occ_rank']),
            'avg_adr_rank':     _mean(m['adr_rank']),
            'avg_revpar_rank':  _mean(m['revpar_rank']),
            'comp_set_size':    m['comp_set_size'],
            'day_count':        day_count,
            # Flag sparse months so the consumer can apply appropriate caution.
            # Only meaningful for period_type='daily'; pre-aggregated monthly rows
            # are never flagged as low-sample regardless of row count.
            'low_sample':       period_type == 'daily' and day_count < LOW_SAMPLE_THRESHOLD,
        })

    # ── Fair share ───────────────────────────────────────────────────────────
    # Theoretical equal share = one property out of comp_set_size properties.
    # This is the baseline against which occ_index is compared to determine
    # whether the hotel is over- or under-penetrating its fair share.
    comp_set_size = str_rows[0].comp_set_size or 6
    fair_share_pct = round(100 / comp_set_size, 1)

    # ── Summary over full period ─────────────────────────────────────────────
    # Use the same mean(my)/mean(comp) methodology at the full-period level for
    # consistency — do NOT average the monthly indices.
    all_my_occ      = [r.my_occ for r in str_rows if r.my_occ is not None]
    all_comp_occ    = [r.comp_occ for r in str_rows if r.comp_occ is not None]
    all_my_adr      = [r.my_adr for r in str_rows if r.my_adr is not None]
    all_comp_adr    = [r.comp_adr for r in str_rows if r.comp_adr is not None]
    all_my_revpar   = [r.my_revpar for r in str_rows if r.my_revpar is not None]
    all_comp_revpar = [r.comp_revpar for r in str_rows if r.comp_revpar is not None]
    all_revpar_ranks = [r.revpar_rank for r in str_rows if r.revpar_rank is not None]

    avg_occ_index    = _index(_mean(all_my_occ) or 0, _mean(all_comp_occ) or 0)
    avg_adr_index    = _index(_mean(all_my_adr) or 0, _mean(all_comp_adr) or 0)
    avg_revpar_index = _index(_mean(all_my_revpar) or 0, _mean(all_comp_revpar) or 0)
    avg_revpar_rank  = _mean(all_revpar_ranks)

    # Count days / rows where we ranked 1st in RevPAR.
    days_ranked_1st_revpar = sum(1 for r in str_rows if r.revpar_rank == 1)

    summary = {
        'avg_occ_index':          avg_occ_index,
        'avg_adr_index':          avg_adr_index,
        'avg_revpar_index':       avg_revpar_index,
        'avg_revpar_rank':        avg_revpar_rank,
        'days_ranked_1st_revpar': days_ranked_1st_revpar,
        'data_days':              len(str_rows),
    }

    return jsonify({
        'success':      True,
        'has_data':     True,
        'start_date':   start_date.isoformat(),
        'end_date':     end_date.isoformat(),
        'period_type':  period_type,
        'fair_share': {
            'theoretical_pct': fair_share_pct,
            'comp_set_size':   comp_set_size,
            'note': (
                'Theoretical equal share = 100 / comp_set_size. '
                'Compare vs avg occ_index to assess penetration.'
            ),
        },
        'summary':       summary,
        'monthly_trend': monthly_trend,
    })
