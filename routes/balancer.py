"""
RJ Balancer — Standalone page for auto-balancing the RJ.
Upload source documents, calculate all jour columns, compare against actual RJ values.
"""

from flask import Blueprint, render_template, request, jsonify, session
from database.models import db, NightAuditSession
from utils.auth_decorators import login_required
from datetime import datetime
import json, io

balancer_bp = Blueprint('balancer', __name__)


@balancer_bp.route('/balancer')
@login_required
def balancer_page():
    """Standalone balancer page."""
    return render_template('balancer.html')


@balancer_bp.route('/api/balancer/run', methods=['POST'])
@login_required
def run_balancer():
    """
    Run the balancer with uploaded source documents.

    Accepts multipart form with:
        - sj: Sales Journal text file
        - dr: Daily Revenue PDF
        - hp: HP Excel file
        - ar: AR Summary PDF (optional)
        - adv: Advance Deposit PDF (optional)
        - rj: RJ Excel file (optional — if not provided, uses NAS)
        - day: Day number (1-31)
        - g4: G4 override
        - adj_piaz: Piazza adjustment
        - adj_mar: Marché adjustment
        - club_nourr: Club Lounge Nourriture
        - club_autres: Club Lounge Autres
        - audit_date: YYYY-MM-DD (for NAS lookup)
    """
    from utils.rj_balancer import (
        BalancerService, parse_sj, parse_dr_pdf, parse_hp,
        parse_ar_pdf, parse_adv_dep, parse_rj_transelect,
        parse_rj_geac, parse_rj_recap, parse_rj_jour, calculate_jour,
        SJData, DRData, ARData, HPData, AdvDepData, TranselectData, GeacData, RecapData, JourRow
    )

    try:
        day = int(request.form.get('day', 0))
        g4 = float(request.form.get('g4', 0))
        adj_piaz = float(request.form.get('adj_piaz', 0))
        adj_mar = float(request.form.get('adj_mar', 0))
        club_nourr = request.form.get('club_nourr')
        club_autres = request.form.get('club_autres')
        dep_on_hand = request.form.get('dep_on_hand')
        club_nourr = float(club_nourr) if club_nourr else None
        club_autres = float(club_autres) if club_autres else None

        # Parse uploaded files
        sj = SJData()
        dr = DRData()
        ar = ARData()
        hp = HPData()
        adv = AdvDepData()
        tr = TranselectData()
        geac = GeacData()
        recap = RecapData()
        jour = JourRow()

        parsed = []

        def to_bio(f):
            """Convert uploaded file to BytesIO"""
            return io.BytesIO(f.read())

        # Sales Journal
        sj_file = request.files.get('sj')
        if sj_file:
            sj = parse_sj(to_bio(sj_file))
            parsed.append(f"SJ: Piaz_N={sj.piaz_nourr} Admin={sj.admin} Promo={sj.promo}")

        # Daily Revenue
        dr_file = request.files.get('dr')
        if dr_file:
            dr = parse_dr_pdf(to_bio(dr_file))
            parsed.append(f"DR: Chambres={dr.chambres_total} Internet={dr.internet} FD={dr.facture_direct}")

        # HP Excel
        hp_file = request.files.get('hp')
        if hp_file and day:
            hp = parse_hp(to_bio(hp_file), day)
            parsed.append(f"HP: day {day}")

        # AR Summary
        ar_file = request.files.get('ar')
        if ar_file:
            ar = parse_ar_pdf(to_bio(ar_file))
            parsed.append(f"AR: GuestFolios={ar.guest_folios}")

        # Advance Deposit
        adv_file = request.files.get('adv')
        if adv_file:
            adv = parse_adv_dep(to_bio(adv_file))
            parsed.append(f"AdvDep: Today={adv.today:.2f}")

        # Manual deposit on hand override (when Adv Dep parser fails)
        if dep_on_hand and float(dep_on_hand) > 0:
            manual_dep = float(dep_on_hand)
            # Override adv.today with manual value
            adv = AdvDepData(yesterday=0, received=0, applied=0, cancelled=0, dna=0)
            # Set the _today property by reverse-engineering: today = yesterday + received - applied - cancelled - dna
            # Simplest: set yesterday = manual value (so today property = manual value)
            adv.yesterday = manual_dep
            parsed.append(f"AdvDep MANUAL: Dep on Hand={manual_dep:.2f}")

        # RJ file (for Transelect, GEAC, Recap, Jour)
        rj_file = request.files.get('rj')
        if rj_file and day:
            rj_bytes = rj_file.read()
            tr = parse_rj_transelect(io.BytesIO(rj_bytes))
            geac = parse_rj_geac(io.BytesIO(rj_bytes))
            recap = parse_rj_recap(io.BytesIO(rj_bytes))
            jour = parse_rj_jour(io.BytesIO(rj_bytes), day)
            parsed.append(f"RJ: BO={jour.bal_ouv:.2f} BF={jour.bal_ferm:.2f} DC={jour.dc:.2f}")
            parsed.append(f"Transelect: AX={tr.totaux_ax} MC={tr.totaux_mc} X24={tr.x24}")
        else:
            # Try to get from NAS
            audit_date = request.form.get('audit_date')
            if audit_date:
                try:
                    d = datetime.strptime(audit_date, '%Y-%m-%d').date()
                    nas = NightAuditSession.query.filter_by(audit_date=d).first()
                    if nas:
                        # Extract Transelect, GEAC, Recap, Jour from NAS
                        result = BalancerService.extract_from_nas(nas)
                        if result:
                            jour = result
                            parsed.append(f"NAS: loaded session for {audit_date}")
                except Exception as e:
                    parsed.append(f"NAS error: {e}")

        if not day:
            return jsonify({'success': False, 'error': 'Jour (day) requis'}), 400

        # Run the balancer
        results = calculate_jour(
            sj, dr, ar, hp, adv, tr, geac, recap, jour,
            g4=g4, adj_piaz=adj_piaz, adj_mar=adj_mar,
            club_nourr_override=club_nourr, club_autres_override=club_autres
        )

        results['parsed'] = parsed
        results['success'] = True

        return jsonify(results)

    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500
