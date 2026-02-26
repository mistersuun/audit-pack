import os
from pathlib import Path
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    abort,
    send_file
)
from functools import wraps
from datetime import date, datetime, timedelta

def _audit_date():
    """
    Get the current audit date.
    Night auditors work from ~11 PM to ~7 AM. If the current time is between
    midnight and 6:59 AM, the audit date is yesterday (the night they started).
    This ensures checklist progress persists across the midnight boundary.
    """
    now = datetime.now()
    if now.hour < 7:
        return (now - timedelta(days=1)).date()
    return now.date()
from markupsafe import escape
from database import db, Task, Shift, TaskCompletion

checklist_bp = Blueprint('checklist', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('auth_v2.login'))
        return f(*args, **kwargs)
    return decorated_function

@checklist_bp.route('/')
@login_required
def index():
    # Everyone lands on the smart dashboard
    return redirect(url_for('dashboard.dashboard_page'))

@checklist_bp.route('/checklist')
@login_required
def checklist_view():
    # Accept role from URL param and set in session
    role_param = request.args.get('role')
    if role_param in ('front', 'back'):
        session['user_role'] = role_param
        session.modified = True
    elif not session.get('user_role'):
        # No role set — default to front
        session['user_role'] = 'front'
        session.modified = True
    return render_template('checklist.html', active_role=session.get('user_role', 'front'))

@checklist_bp.route('/documentation')
@login_required
def documentation():
    docs = [
        {
            "title": "Formation Auditeurs Back (PDF)",
            "path": "back/Formation Auditeurs Back.pdf",
            "description": "Guide de formation Back (PDF scanné)."
        },
        {
            "title": "print_VNC (PDF converti)",
            "path": "back/print_VNC.pdf",
            "description": "Guides rapports POSitouch/VNC."
        },
        {
            "title": "print_VNC_SHORT (PDF converti)",
            "path": "back/print_VNC_SHORT.pdf",
            "description": "Version courte rapports POSitouch/VNC."
        },
        {
            "title": "Quasimodo (PDF converti)",
            "path": "back/QUASIMODO.pdf",
            "description": "Guide Quasimodo (réconciliation cartes)."
        },
        {
            "title": "HP explication (PDF converti)",
            "path": "back/HP explication.pdf",
            "description": "Guide saisie Hotel Promotion / Admin."
        },
        {
            "title": "Procédure Complète Front (PDF)",
            "path": "front/2024-12 - Procédure Complète Front.pdf",
            "description": "Procédure détaillée Front desk (version PDF)."
        }
    ]
    return render_template('documentation.html', docs=docs)

@checklist_bp.route('/documentation/file/<path:filename>')
@login_required
def documentation_file(filename):
    docs_base = Path(__file__).resolve().parent.parent / "documentation"
    full_path = (docs_base / filename).resolve()
    if docs_base not in full_path.parents and docs_base != full_path.parent:
        abort(404)
    if not full_path.exists():
        abort(404)
    mimetype = None
    if full_path.suffix.lower() == '.pdf':
        mimetype = 'application/pdf'
    elif full_path.suffix.lower() == '.docx':
        mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    return send_file(full_path, as_attachment=False, mimetype=mimetype)

@checklist_bp.route('/documentation/view/<path:filename>')
@login_required
def documentation_view(filename):
    docs_base = Path(__file__).resolve().parent.parent / "documentation"
    full_path = (docs_base / filename).resolve()
    if docs_base not in full_path.parents and docs_base != full_path.parent:
        abort(404)
    if not full_path.exists():
        abort(404)

    ext = full_path.suffix.lower()
    is_pdf = filename.lower().endswith('.pdf')
    content_html = None
    parsed = True

    try:
        if ext == '.md':
            text = full_path.read_text(encoding='utf-8', errors='ignore')
            content_html = f"<pre>{escape(text)}</pre>"
        elif ext == '.docx':
            from docx import Document
            doc = Document(str(full_path))
            text = "\n\n".join([p.text for p in doc.paragraphs])
            content_html = f"<pre>{escape(text)}</pre>"
        elif ext == '.pdf':
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(str(full_path))
                text = "\n".join([page.extract_text() or '' for page in reader.pages])
                content_html = f"<pre>{escape(text)}</pre>"
            except Exception:
                parsed = False
        else:
            parsed = False
    except Exception:
        parsed = False

    return render_template(
        'doc_viewer.html',
        filename=filename,
        parsed=parsed,
        content_html=content_html,
        is_pdf=is_pdf,
        download_url=url_for('checklist.documentation_file', filename=filename)
    )


@checklist_bp.route('/faq')
@login_required
def faq():
    glossary = {
        "Glossaire des termes": [
            {
                "term": "PART",
                "english": "Night Audit Run",
                "definition": "Processus automatique LightSpeed qui ferme la journee et lance tous les calculs comptables. Se lance generalement vers 03h00.",
                "context": "Exemple: PART doit etre lance apres que les terminaux Moneris soient fermes et apres l'export des rapports VNC."
            },
            {
                "term": "ADR",
                "english": "Average Daily Rate",
                "definition": "Tarif moyen par chambre vendue. Calcule comme: Revenus Hebergement / Nombre de chambres vendues.",
                "context": "L'ADR est affiche dans le rapport Jour et dans DBRS pour analyser la strategie tarifaire."
            },
            {
                "term": "RevPAR",
                "english": "Revenue Per Available Room",
                "definition": "Revenu par chambre disponible. Combinaison de l'ADR et du taux d'occupation (Revenus Hebergement / Total chambres disponibles).",
                "context": "Metrique cle pour evaluer la performance hoteliere dans DBRS."
            },
            {
                "term": "OCC%",
                "english": "Occupancy Rate",
                "definition": "Taux d'occupation: (chambres vendues) / (chambres disponibles) x 100%. Exemple: 280/340 = 82.35%.",
                "context": "Calcule dans l'onglet Jour et reporte dans DBRS pour l'analyse Marriott."
            },
            {
                "term": "ARR / DEP",
                "english": "Arrivals / Departures",
                "definition": "Nombre d'arrivees et de departs clients pour la journee dans LightSpeed.",
                "context": "ARR doit etre = 0 avant de lancer Pre-Audit. DEP affecte les chemises bleues."
            },
            {
                "term": "Folio",
                "english": "Guest Folio",
                "definition": "Compte client dans LightSpeed contenant toutes les charges et paiements du sejour.",
                "context": "Exemple: modifier le folio pour corriger une charge ou poster un credit; imprimer le folio pour les dossiers."
            },
            {
                "term": "DueBack",
                "english": "Cash Due Back",
                "definition": "Remboursement a la reception: montant du jour moins montant de veille pour chaque employe.",
                "context": "DueBack = solde + (nouveau) - solde - (veille). Saisi depuis Cashier Details dans RJ Natif."
            },
            {
                "term": "No-show",
                "english": "No-show",
                "definition": "Reservation non honoree. Client ne se presente pas a l'hotel.",
                "context": "Procedure: poster Dept 1 / Sub 28 dans le folio, note 'NO SHOW' + nom client."
            },
            {
                "term": "Walk-in",
                "english": "Walk-in",
                "definition": "Client sans reservation prealable qui arrive a la reception.",
                "context": "S'oppose a une arrivee prevue (reservation). Traite comme un client regulier dans LightSpeed."
            },
            {
                "term": "PM / Mode de paiement",
                "english": "Payment Method",
                "definition": "Methode de paiement (Credit, Debit, Comptant, Cheque, etc.).",
                "context": "Saisi dans Transelect par terminal et par type de carte. Reconciliation Moneris vs POSitouch."
            },
            {
                "term": "Cashiering",
                "english": "Cashiering Module",
                "definition": "Module de caisse dans LightSpeed pour poster les charges et paiements.",
                "context": "Utilise pour corriger les soldes clients, poster les no-shows, crediter les cheques sans provision."
            },
            {
                "term": "GEAC / UX",
                "english": "GEAC / UX",
                "definition": "Systeme de comptabilite cartes hotel. Affiche le Daily Cash Out et Daily Revenue par type de carte.",
                "context": "GEAC balance DOIT etre = 0 a la fin du cycle. Si variance, contacter Roula ou Mandy."
            },
            {
                "term": "Transelect",
                "english": "Transelect Card Reconciliation",
                "definition": "Rapprochement des terminaux de paiement (Moneris vs POSitouch vs FreedomPay).",
                "context": "Tolerance max +/-0.01. Reconcilie Etablissement POSitouch + batchs Moneris + FreedomPay Fusebox."
            },
            {
                "term": "Quasimodo",
                "english": "Quasimodo Global Reconciliation",
                "definition": "Reconciliation globale: montants totals des cartes + comptant vs revenus Jour total.",
                "context": "AMEX multiplie par facteur 0.9735 (frais commerciaux). Variance doit etre +/-0.01$."
            },
            {
                "term": "DBRS",
                "english": "Daily Business Review Summary",
                "definition": "Rapport pour siege Marriott. Contient resume revenus, ADR, occupancy, market segments, no-shows.",
                "context": "Genere dans RJ Natif a partir des donnees Jour. Inclus dans dossier bleu."
            },
            {
                "term": "SetD",
                "english": "Personnel Set-Dejeuner",
                "definition": "Allocations repas accordees aux employes (petit-dejeuner gratuit).",
                "context": "Saisi dans SetD si variance SD. Transfere a Depot pour ajustement comptable."
            },
            {
                "term": "SD",
                "english": "Safe Deposit / Surplus-Deficit",
                "definition": "Comptage physique de la caisse coffre-fort vs montants POSitouch des employes.",
                "context": "Variance SD = comptage - POSitouch. Reportee dans RECAP et SetD."
            },
            {
                "term": "HP / Admin",
                "english": "Hotel Promotion & Administration",
                "definition": "Factures F&B gratuites pour hotes, evenements, marketing, etc.",
                "context": "Saisi manuellement ou par scanning; poste dans LightSpeed Dept 50."
            },
            {
                "term": "RJ",
                "english": "Rapport Journalier",
                "definition": "Rapport complet quotidien (Excel traditionnel ou RJ Natif web app).",
                "context": "Contient 14 onglets: Controle, DueBack, Recap, Transelect, GEAC, SD, SetD, HP, Internet, Sonifi, Jour, Quasimodo, DBRS, Sommaire."
            },
            {
                "term": "POD",
                "english": "Payment on Departure / Tip Register",
                "definition": "Registre des pourboires: saisie rapide des ventes et tips par serveur.",
                "context": "Validation: Total ventes Back - (reception + Spesa) = total ventes POD."
            },
            {
                "term": "OTB",
                "english": "On The Books",
                "definition": "Reservations futures. Donnees de pick-up et revenus projetes.",
                "context": "Affiche dans DBRS pour l'analyse Marriott. Donnees du module Reservations LightSpeed."
            },
            {
                "term": "Pre-Audit",
                "english": "Pre-Audit",
                "definition": "Verifications avant PART: soldes clients a +/-1$, printings, travail Internet.",
                "context": "Lance depuis LightSpeed > Night Audit > Run Pre-Audit (ARR doit etre = 0)."
            },
            {
                "term": "Post-Audit",
                "english": "Post-Audit",
                "definition": "Verifications apres PART: impressions completes, rapports finaux, classement.",
                "context": "Effectue quand PART est termine et LightSpeed est a nouveau disponible."
            },
            {
                "term": "Galaxy Lightspeed",
                "english": "Galaxy Lightspeed PMS",
                "definition": "Property Management System (PMS) de l'hotel. Gere reservations, folios, rapports.",
                "context": "Systeme source pour: revenus, occupancy, guest data, cashiering, night audit."
            },
            {
                "term": "VNC / POSitouch",
                "english": "VNC / POSitouch",
                "definition": "Systeme de point de vente pour restaurants et services (Bar, Room Service, Banquet).",
                "context": "Fournit rapports: Daily Sales Report, Sales Journal, Memo Listings, Acheteur/Audit batch."
            },
            {
                "term": "Moneris",
                "english": "Moneris Payment Terminals",
                "definition": "Fournisseur des terminaux de paiement par carte (Reception, Bar, Room Service, Banquet).",
                "context": "Batchs fermes avant PART (~03h). Totaux reconcilies dans Transelect."
            },
            {
                "term": "FreedomPay",
                "english": "FreedomPay Payment Gateway",
                "definition": "Passerelle de paiement integree au PMS. Collecte transactions cartes de tous les modules.",
                "context": "Donnees disponibles dans Fusebox. Utilisee pour Transelect + Quasimodo."
            },
            {
                "term": "Fusebox",
                "english": "FreedomPay Fusebox Portal",
                "definition": "Portail de rapports FreedomPay. Affiche Payment Breakdown par type de carte et terminal.",
                "context": "Accede via navigateur pour recuperer les totaux Transelect par card type."
            },
            {
                "term": "Separateur date",
                "english": "Dated Separator Sheet",
                "definition": "Feuille pliee en deux qui separe les documents comptables par date.",
                "context": "Prepare en mise en place (23h) avec date du jour. Toutes pieces comptables y vont."
            },
            {
                "term": "Feuille de tournee",
                "english": "Morning Inspection Checklist",
                "definition": "Checklist d'inspection hotel pour l'equipe du matin (proprete, maintenance, etc.).",
                "context": "Imprimee depuis Excel avec date du jour. Signee et deposee a droite du comptoir."
            },
            {
                "term": "Chemise bleue",
                "english": "Blue Binder",
                "definition": "Dossier de classement journalier pour la direction. Contient rapports cles et analyses.",
                "context": "Contenu: RJ, Daily Revenue, Sales Journal, cartes, HP/Admin, Quasimodo, DBRS, caisses."
            },
            {
                "term": "Enveloppe comptabilite",
                "english": "Accounting Envelope",
                "definition": "Enveloppe blanche contenant tous les documents comptables pour transmission a la direction.",
                "context": "Contenu: DSR 9p, Cashier Details, piles cartes, RECAP/SD signes, HP, Daily Cash Out, rapports."
            }
        ],
        "Procedures Front Desk": [
            {
                "title": "Timeline complete 23h-07h",
                "content": "23h00-00h00: Mise en place. 00h00-02h00: Pre-audit. 02h00-03h00: Finalisations. 03h00: PART lance. 03h00-04h00: Post-PART. 04h00-07h00: Impressions finales."
            },
            {
                "title": "Quand lancer Pre-Audit",
                "content": "Pre-Audit ne doit etre lance que lorsque Arrivals = 0 dans LightSpeed. Chemin: Night Audit > Run Pre-Audit."
            },
            {
                "title": "Procedure No-show normal",
                "content": "1. Ouvrir le folio client. 2. Cashiering > Post. 3. Dept 1 / Sub 28. 4. Montant HT. 5. Ref = 'NO SHOW'. 6. Imprimer folio + ajustement."
            },
            {
                "title": "Procedure No-show groupe/RL",
                "content": "1. Charger tout le sejour au compte maitre. 2. Imprimer folio. 3. Transferer vers compte maitre. 4. Dupliquer resa pour nuits restantes (rate 0$)."
            },
            {
                "title": "Ajustement Internet Standard",
                "content": "Standard (acces Internet facture): 1. Identifier chambres depuis rapport 36. 2. Corriger montant a 4.95. 3. Imprimer 36.1 final. 4. Imprimer folio. 5. Agrafer au separateur."
            },
            {
                "title": "Internet Elite/Pilote (gratuit)",
                "content": "Elite/Pilote (Internet gratuit): 1. Identifier depuis rapport 36. 2. Transfer vers Marriott Internet (0$). 3. Settle. 4. Imprimer folio. 5. Imprimer 36.5. 6. Agrafer 36.1 + folio + 36.5."
            },
            {
                "title": "Impressions essentielles Post-Audit",
                "content": "1. No Posting Allowed (All guests). 2. Guest List - Charge All. 3. Allotment Overview (Today a Today+49). 4. In-House List G4 (3 copies). 5. In-House List G4+CL (2 copies)."
            },
            {
                "title": "VNC / POSitouch - ordre d'impression",
                "content": "1. Daily Sales Report (9 pages + page 1). 2. Sales Journal Reports par mode. 3. Memo Listings. 4. Acheteur.bat (2 copies). 5. Audit.bat (sans page Server Sales and Tips)."
            },
            {
                "title": "Timing Moneris / PART",
                "content": "~02h30: Fermer tous les terminaux Moneris. Recuperer batchs. ~03h00: Lancer PART. 03h00-04h00: Faire HP/Admin, impressions VNC, classement."
            }
        ],
        "Procedures Back Office": [
            {
                "title": "Transelect - sources donnees et tolerance",
                "content": "Sources: POSitouch col. N, batchs Moneris, FreedomPay Fusebox. Tolerance: 0.00$ (max +/-0.01$). Reconcilie: Restaurant + Reception = total net par card type."
            },
            {
                "title": "GEAC balance",
                "content": "GEAC/UX doit afficher balance = 0.00$. Sources: Daily Cash Out vs Daily Revenue. Si variance: contacter Roula ou Mandy. Rapport d'exception au siege."
            },
            {
                "title": "DueBack - saisi depuis Cashier Details",
                "content": "DueBack = (solde nouveau - solde veille) par employe. Ligne negative (-): remboursement veille. Ligne positive (+): montant jour. Source: Cashier Details LightSpeed."
            },
            {
                "title": "SD - Comptage vs POSitouch",
                "content": "1. Compter physiquement le coffre-fort. 2. Obtenir totaux POSitouch (Acheteur.bat). 3. Calculer variance. 4. Saisir dans RJ Natif > SD. 5. Si variance: creer entree SetD."
            },
            {
                "title": "RECAP - entrees et calculs",
                "content": "Entrees: Daily Revenue lectures + DueBack + variances SD. Calcul: (Lecture Cash + Lecture Cheque) + (Correction) = NET. Imprimer RECAP + signer."
            },
            {
                "title": "Depot - enveloppes physiques",
                "content": "1. Copier Montant verifie SD vers Depot (client 6: Caisse, client 8: Cheques). 2. Preparer enveloppes physiques. 3. Agrafer depot bancaire. 4. Classer."
            },
            {
                "title": "Quasimodo - facteur AMEX et variance",
                "content": "Quasimodo reconcilie: Transelect (cartes) + Recap (comptant) vs Jour total. AMEX x 0.9735 (frais). Variance doit etre +/-0.01$. Si > 0.01$: deboguer sources."
            },
            {
                "title": "DBRS - source donnees et mapping",
                "content": "Sources: Jour total, occupation, ADR, OTB, market segments, no-shows. Genere dans RJ Natif > DBRS. Inclus dans chemise bleue + rapport siege Marriott."
            }
        ],
        "Classement & Documents": [
            {
                "title": "Enveloppe comptabilite - contenu exact",
                "content": "1. Daily Sales Report (9p + p1). 2. Paiement par departement. 3. Cashier Details broch. 4. Pile cartes. 5. RECAP signe. 6. SD signe. 7. HP/Admin. 8. Daily Cash Out. 9. Guest Ledger. 10. Detail Ticket. 11. Room Post Audit. 12. Availability Rebuild Exception. 13. Sales Journal Payment Totals. 14. Memo Listings."
            },
            {
                "title": "Chemise bleue datee - contenu exact",
                "content": "1. RJ verifie. 2. Daily Revenue. 3. Advance Deposit. 4. Sales Journal Entire House. 5. Pile cartes. 6. HP/Admin. 7. Complimentary report. 8. Room Type Production. 9. Quasimodo. 10. DBRS. 11. Rapports caisses/depots."
            },
            {
                "title": "Piles restaurant - rapport et documents",
                "content": "Pile 1: Daily Sales Report (DSR) 9 pages. Pile 2: No Posting Allowed. Pile 3: Guest List - Charge All. Pile 4: Sales Journal Reports par mode. Pile 5: Memo Listings. Pile 6: In-House List G4."
            },
            {
                "title": "Piles DBRS - rapport et documents",
                "content": "Pile 1: Allotment Overview (Today a Today+49). Pile 2: In-House List G4. Pile 3: Daily Revenue. Pile 4: DBRS web. Pile 5: OTB. Pile 6: Room Type Production si needed."
            }
        ],
        "Raccourcis App Web": [
            {
                "title": "Navigation rapide RJ Natif",
                "content": "Accueil > RJ Natif > Selectionner date > 14 onglets. Barre de status affiche: statut session, heure derniere sauvegarde, bouton Calculer, bouton Soumettre."
            },
            {
                "title": "Auto-save dans RJ Natif",
                "content": "Chaque champ auto-save apres 500ms d'inactivite (debounce). Indicateur de sauvegarde affiche. Pas besoin de cliquer Enregistrer. Lors du submit, tous les 14 onglets sont sauvegardes."
            },
            {
                "title": "Generateurs de documents",
                "content": "Menu principal > options: Generer POD, Generer Depot, Generer Rapport Jour (PDF), Generer Quasimodo (PDF). Chaque generateur pre-remplit depuis RJ Natif."
            },
            {
                "title": "POD - entree rapide batch",
                "content": "Bouton Nouveau POD > selectionner serveur > saisir ventes + tips. Sauvegarde instantanee. Validation automatique vs Back total. Historique POD affiche tous les entrees."
            },
            {
                "title": "Tab order dans RJ Natif",
                "content": "Important: Internet/Sonifi AVANT Jour (necessaire pour revenus). Quasimodo/DBRS APRES Jour (utilisent totaux Jour). Controle en premier. Sommaire en dernier."
            }
        ],
        "Numeros & Contacts": [
            {
                "title": "Contacts cles",
                "content": "Roula (Comptabilite): variance GEAC > 0.01$. Mandy (Finance): rapports siege, DBRS. M. Pazzi (Directeur): DSR daily, signature RECAP. Superviseur nuit: questions, escalade clients."
            }
        ]
    }

    glossary_count = len(glossary.get("Glossaire des termes", []))
    categories = list(glossary.keys())

    return render_template('faq.html', glossary=glossary, glossary_count=glossary_count, categories=categories)


# ── API: Liste des tâches ──────────────────────────────────────
@checklist_bp.route('/api/tasks')
@login_required
def get_tasks():
    """Retourne les tâches actives pour le rôle courant (front/back)."""
    role = session.get('user_role', 'front')
    tasks = Task.query.filter_by(role=role, is_active=True).order_by(Task.order).all()
    return jsonify([t.to_dict() for t in tasks])


@checklist_bp.route('/api/set-role', methods=['POST'])
@login_required
def set_role():
    """Change le rôle actif (front/back) en session."""
    data = request.get_json() or {}
    role = data.get('role', 'front')
    if role in ('front', 'back'):
        session['user_role'] = role
        session.modified = True
    return jsonify({'role': session.get('user_role', 'front')})


@checklist_bp.route('/api/shifts/current')
@login_required
def get_current_shift():
    today = _audit_date()
    shift = Shift.query.filter_by(date=today).first()
    if not shift:
        return jsonify({'shift': None, 'completions': []})

    completions = TaskCompletion.query.filter_by(shift_id=shift.id).all()
    return jsonify({
        'shift': shift.to_dict(),
        'completions': [c.to_dict() for c in completions]
    })

@checklist_bp.route('/api/shifts', methods=['POST'])
@login_required
def start_shift():
    today = _audit_date()
    user_name = session.get('user_name', 'Inconnu')
    shift = Shift.query.filter_by(date=today).first()
    if not shift:
        shift = Shift(date=today, user_name=user_name)
        db.session.add(shift)
        db.session.commit()
    return jsonify(shift.to_dict())

@checklist_bp.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    today = _audit_date()
    user_name = session.get('user_name', 'Inconnu')
    shift = Shift.query.filter_by(date=today).first()
    if not shift:
        shift = Shift(date=today, user_name=user_name)
        db.session.add(shift)
        db.session.commit()

    existing = TaskCompletion.query.filter_by(shift_id=shift.id, task_id=task_id).first()
    if existing:
        return jsonify(existing.to_dict())

    data = request.get_json() or {}
    completion = TaskCompletion(
        shift_id=shift.id,
        task_id=task_id,
        completed_by=user_name,
        notes=data.get('notes')
    )
    db.session.add(completion)
    db.session.commit()
    return jsonify(completion.to_dict())

@checklist_bp.route('/api/tasks/<int:task_id>/uncomplete', methods=['POST'])
@login_required
def uncomplete_task(task_id):
    today = _audit_date()
    shift = Shift.query.filter_by(date=today).first()
    if not shift:
        return jsonify({'success': True})

    completion = TaskCompletion.query.filter_by(shift_id=shift.id, task_id=task_id).first()
    if completion:
        db.session.delete(completion)
        db.session.commit()
    return jsonify({'success': True})

@checklist_bp.route('/api/shifts/complete', methods=['POST'])
@login_required
def complete_shift():
    today = _audit_date()
    shift = Shift.query.filter_by(date=today).first()
    if shift:
        shift.completed_at = datetime.utcnow()
        db.session.commit()
        return jsonify(shift.to_dict())
    return jsonify({'error': 'No shift found'}), 404


# ── ETL / Historique ──────────────────────────────────────────────
@checklist_bp.route('/api/history')
@login_required
def get_history():
    """ETL endpoint: retourne l'historique complet des shifts et complétions.
    Params: ?days=30 (défaut), ?role=front|back, ?format=json|csv
    """
    from sqlalchemy import desc
    days = request.args.get('days', 30, type=int)
    role_filter = request.args.get('role', None)
    output_format = request.args.get('format', 'json')

    cutoff = date.today() - timedelta(days=days)
    shifts = Shift.query.filter(Shift.date >= cutoff).order_by(desc(Shift.date)).all()

    # Pre-load all tasks into a lookup dict (eliminates N+1 queries)
    all_tasks = {t.id: t for t in Task.query.filter_by(is_active=True).all()}
    total_front = sum(1 for t in all_tasks.values() if t.role == 'front')
    total_back = sum(1 for t in all_tasks.values() if t.role == 'back')

    # Pre-load all completions for these shifts in one query
    shift_ids = [s.id for s in shifts]
    all_completions = TaskCompletion.query.filter(
        TaskCompletion.shift_id.in_(shift_ids)
    ).all() if shift_ids else []
    completions_by_shift = {}
    for c in all_completions:
        completions_by_shift.setdefault(c.shift_id, []).append(c)

    history = []
    for s in shifts:
        for c in completions_by_shift.get(s.id, []):
            task = all_tasks.get(c.task_id)
            if not task:
                continue
            if role_filter and task.role != role_filter:
                continue
            history.append({
                'date': s.date.isoformat(),
                'shift_id': s.id,
                'shift_user': s.user_name or '',
                'task_id': c.task_id,
                'task_order': task.order,
                'task_title': task.title_fr,
                'task_category': task.category,
                'task_role': task.role,
                'completed_at': c.completed_at.isoformat() if c.completed_at else '',
                'completed_by': c.completed_by or '',
                'notes': c.notes or '',
            })

    if output_format == 'csv':
        import io, csv
        output = io.StringIO()
        if history:
            writer = csv.DictWriter(output, fieldnames=history[0].keys())
            writer.writeheader()
            writer.writerows(history)
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=checklist_history_{days}j.csv'
        }

    # Résumé par date (uses pre-loaded data, no extra queries)
    summary_by_date = {}
    for s in shifts:
        shift_comps = completions_by_shift.get(s.id, [])
        done_front = sum(1 for c in shift_comps if all_tasks.get(c.task_id) and all_tasks[c.task_id].role == 'front')
        done_back = sum(1 for c in shift_comps if all_tasks.get(c.task_id) and all_tasks[c.task_id].role == 'back')

        summary_by_date[s.date.isoformat()] = {
            'shift': s.to_dict(),
            'front': {'done': done_front, 'total': total_front, 'pct': round(done_front / max(total_front, 1) * 100)},
            'back': {'done': done_back, 'total': total_back, 'pct': round(done_back / max(total_back, 1) * 100)},
        }

    return jsonify({
        'period_days': days,
        'total_records': len(history),
        'summary': summary_by_date,
        'records': history
    })


@checklist_bp.route('/api/history/export')
@login_required
def export_history_csv():
    """Export CSV direct pour ETL externe."""
    from sqlalchemy import desc
    import io, csv

    days = request.args.get('days', 90, type=int)
    cutoff = date.today() - timedelta(days=days)
    shifts = Shift.query.filter(Shift.date >= cutoff).order_by(desc(Shift.date)).all()

    output = io.StringIO()
    fields = ['date', 'shift_user', 'task_order', 'task_title', 'task_category',
              'task_role', 'completed_at', 'completed_by', 'duration_min', 'notes']
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()

    # Pre-load tasks and completions to avoid N+1 queries
    all_tasks = {t.id: t for t in Task.query.all()}
    shift_ids = [s.id for s in shifts]
    all_comps = TaskCompletion.query.filter(TaskCompletion.shift_id.in_(shift_ids)).all() if shift_ids else []
    comps_by_shift = {}
    for c in all_comps:
        comps_by_shift.setdefault(c.shift_id, []).append(c)

    for s in shifts:
        for c in comps_by_shift.get(s.id, []):
            task = all_tasks.get(c.task_id)
            if not task:
                continue
            writer.writerow({
                'date': s.date.isoformat(),
                'shift_user': s.user_name or '',
                'task_order': task.order,
                'task_title': task.title_fr,
                'task_category': task.category,
                'task_role': task.role,
                'completed_at': c.completed_at.isoformat() if c.completed_at else '',
                'completed_by': c.completed_by or '',
                'duration_min': task.estimated_minutes or '',
                'notes': c.notes or '',
            })

    return output.getvalue(), 200, {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': f'attachment; filename=audit_checklist_etl_{date.today().isoformat()}.csv'
    }
