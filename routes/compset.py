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
from database.models import db, STRCompSet, OTBForecast
from utils.auth_decorators import login_required, role_required
import csv
import io
import logging
import json

logger = logging.getLogger(__name__)

compset_bp = Blueprint('compset', __name__, url_prefix='/compset')

TOTAL_ROOMS = 252


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

    data = [r.to_dict() for r in records]

    return jsonify({
        'count': len(data),
        'data': data,
        'snapshot_date': snapshot_date.isoformat(),
        'days': days,
    })


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
    """Generate realistic demo OTB data for next 90 days."""
    import random

    today = date_type.today()

    # Delete existing seed data
    OTBForecast.query.filter(OTBForecast.source == 'seed').delete()

    created_count = 0

    for days_forward in range(1, 91):
        target_date = today + timedelta(days=days_forward)

        # Realistic OTB ramp: starts at 45%, peaks at 85% on weekends
        day_of_week = target_date.weekday()
        base_occ = 45 + (days_forward / 90) * 35  # Ramp from 45% to 80%

        # Weekend peaks
        if day_of_week in [4, 5]:  # Friday, Saturday
            base_occ += random.uniform(5, 15)

        rooms_otb = int(TOTAL_ROOMS * (base_occ / 100))
        group_rooms = random.randint(10, 60) if random.random() > 0.5 else random.randint(0, 20)
        transient_rooms = max(0, rooms_otb - group_rooms)

        adr_otb = random.uniform(140, 190)
        revenue_otb = rooms_otb * adr_otb

        # Last year comparison (slightly lower)
        ly_rooms = max(0, rooms_otb - random.randint(5, 25))
        ly_occ = round((ly_rooms / TOTAL_ROOMS) * 100, 1)
        ly_adr = adr_otb * random.uniform(0.92, 1.08)
        ly_revenue = ly_rooms * ly_adr

        record = OTBForecast(
            snapshot_date=today,
            target_date=target_date,
            rooms_otb=rooms_otb,
            occ_otb=round(base_occ, 1),
            adr_otb=round(adr_otb, 2),
            revenue_otb=round(revenue_otb, 2),
            group_rooms=group_rooms,
            transient_rooms=transient_rooms,
            ly_rooms=ly_rooms,
            ly_occ=round(ly_occ, 1),
            ly_adr=round(ly_adr, 2),
            ly_revenue=round(ly_revenue, 2),
            source='seed',
        )
        db.session.add(record)
        created_count += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'created': created_count,
        'message': f'{created_count} jours de données OTB créés.'
    })
