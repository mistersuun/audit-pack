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
from datetime import date, datetime
from markupsafe import escape
from database import db, Task, Shift, TaskCompletion

checklist_bp = Blueprint('checklist', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@checklist_bp.route('/')
@login_required
def index():
    # Always show role selection menu (Dashboard)
    return render_template('select_role.html')

@checklist_bp.route('/checklist')
@login_required
def checklist_view():
    if not session.get('user_role'):
        return redirect(url_for('checklist.index'))
    return render_template('checklist.html')

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
    faqs = [
        {
            "q": "Front – Mise en place (23h-00h) : que préparer ?",
            "a": """
<ol>
  <li><strong>Séparateur daté :</strong> ouvrir le Word, changer la date du jour, imprimer, plier en deux, le garder à gauche (toutes les pièces comptables y vont).</li>
  <li><strong>Entretien + météo :</strong> Word J+1..J+4, MétéoMédia (prévisions 7j) via Snipping Tool, remplacer l’image dans Word, imprimer en recto-verso.</li>
  <li><strong>Feuille de tournée :</strong> Excel (date du jour), imprimer, signer, déposer à droite du comptoir (côté tabagie SPESA) pour l’équipe du matin.</li>
  <li><strong>Pilotes UPS/FedEx/Cargojet :</strong> UPS plugin (sign-in sheet, date demain), Excel FedEx/Cargojet (chambres du cahier, noms Lightspeed pour Cargojet), imprimer, plier en 3, bac réceptionnistes.</li>
  <li><strong>Clés banquets :</strong> cartable sous l’ordi de droite, Word “Clés Banquets” (affichage, salle, horaire, contact), imprimer, placer avec les feuilles pilotes.</li>
</ol>
""",
            "tags": ["Front", "Setup", "Papier"]
        },
        {
            "q": "Front – Pré-audit (00h-02h) : actions clés ?",
            "a": """
<ol>
  <li><strong>Lancer Pre-Audit :</strong> Night Audit &gt; Run Pre-Audit uniquement quand Arrivals = 0. Récupérer les rapports imprimés.</li>
  <li><strong>Solde “±1$” (Actual Departure) :</strong>
    <ol>
      <li>Ouvrir le folio, Modify &gt; Cashiering &gt; Post.</li>
      <li>Si solde positif (noir) : Dept 40 / Sub 60.</li>
      <li>Si solde négatif (rouge) : Dept 40 / Sub 10.</li>
      <li>Ref = CLOSE, Note = 1, Add to List &gt; Post (solde = 0.00).</li>
      <li>Agrafer le rapport Actual Departure et mettre au séparateur daté.</li>
    </ol>
  </li>
  <li><strong>Groupes / Wholesalers :</strong>
    <ol>
      <li>In-House List &gt; Group Delegate Guests : Page break ON, Room rates YES, Sort Group Code/Room.</li>
      <li>Wholesaler Delegates : Tour Code ALL, Sort Room Number.</li>
      <li>Classer dans une chemise bleue datée.</li>
    </ol>
  </li>
  <li><strong>Internet (membres) :</strong>
    <ol>
      <li>Rapport 36/36.1 pour identifier les chambres facturées.</li>
      <li>Standard : corriger à 4.95 (4.95 / 0.52 / 0.25).</li>
      <li>Élite/Pilote : gratuit (0$) + Transfer vers “Marriott Internet”.</li>
      <li>Imprimer 36.1 final, Settle Marriott Internet (0$) + imprimer folio, imprimer 36.5.</li>
      <li>Agrafer 36.1 + folio Marriott Internet + 36.5, remettre au Back.</li>
    </ol>
  </li>
</ol>
""",
            "tags": ["Front", "Pré-audit", "Internet"]
        },
        {
            "q": "Front – Post-audit : impressions essentielles ?",
            "a": """
<ol>
  <li><strong>No Posting Allowed :</strong> All guests, in-house, by room → pile Restaurant.</li>
  <li><strong>Guest List – Charge All :</strong> Registered, special service CA → pile Restaurant.</li>
  <li><strong>Allotment Overview :</strong> Today à Today+49 → pile DBRS.</li>
  <li><strong>In-House List G4 :</strong> 3x (DBRS, Auditeur, Restaurant).</li>
  <li><strong>In-House List G4+CL :</strong> 2x (Superviseur, Restaurant).</li>
</ol>
""",
            "tags": ["Front", "Post-audit", "Impressions"]
        },
        {
            "q": "No-show : normal vs groupe/RL ?",
            "a": """
<ol>
  <li><strong>Normal :</strong> Cashiering > Post Dept 1 / Sub 28, montant HT, Ref NO SHOW, Note = nom client; imprimer folio + feuille d’ajustement.</li>
  <li><strong>Groupe/RL :</strong> charger tout le séjour, imprimer, transférer vers compte maître; dupliquer résa pour nuits restantes (rate 0$) pour éviter double facturation.</li>
</ol>
""",
            "tags": ["Front", "No-show"]
        },
        {
            "q": "Tips (POD) : comment valider ?",
            "a": """
<ul>
  <li><strong>Saisie :</strong> ventes/tips par serveur dans POD.</li>
  <li><strong>Validation :</strong> Total ventes Back – (réception + Spesa) = total ventes POD.</li>
  <li><strong>Classement :</strong> Agrafer feuilles (Back + POD) au séparateur daté.</li>
</ul>
""",
            "tags": ["Front", "Tips"]
        },
        {
            "q": "VNC / POSitouch : ordre d’impression ?",
            "a": """
<ol>
  <li><strong>Daily Sales Report :</strong> 9p + page 1 (M. Pazzi).</li>
  <li><strong>Sales Journal Reports / Memo Listings :</strong> trier par mode.</li>
  <li><strong>Acheteur.bat :</strong> 2 copies (Christophe + Restaurant).</li>
  <li><strong>Audit.bat :</strong> retirer page “Server Sales and Tips” pour la paie.</li>
</ol>
""",
            "tags": ["Front", "VNC", "POSitouch"]
        },
        {
            "q": "Moneris / PART : timing ?",
            "a": """
<ol>
  <li><strong>Moneris :</strong> fermer terminaux avant PART (~03h) Réception/Bar/Room Service/Banquet; récupérer et encercler les batchs.</li>
  <li><strong>Pendant PART (LS indispo) :</strong> faire HP/Admin, impressions VNC, classement.</li>
</ol>
""",
            "tags": ["Front", "Moneris", "PART"]
        },
        {
            "q": "Back – Transelect / GEAC : tolérance et saisie ?",
            "a": """
<ul>
  <li><strong>Tolérance :</strong> 0.00$ (max ±0.01).</li>
  <li><strong>Transelect :</strong> POSitouch Établissement (col. N), batchs Moneris, FreedomPay Payment Breakdown (Fusebox).</li>
  <li><strong>GEAC/UX :</strong> Daily Cash Out + Daily Revenue p.6, doit finir à 0 (sinon mail à Roula/Mandy).</li>
</ul>
""",
            "tags": ["Back", "Cartes"]
        },
        {
            "q": "Back – DueBack / SD / RECAP / Dépôt : flux ?",
            "a": """
<ul>
  <li><strong>DueBack :</strong> ligne - (veille) + ligne + (jour) par employé depuis Cashier Details.</li>
  <li><strong>SD :</strong> comptage coffre + montants POSitouch employés; variances à noter.</li>
  <li><strong>RECAP :</strong> Daily Revenue p.5-6 + DueBack + variances SD; imprimer puis transfert (Contrôle).</li>
  <li><strong>Dépôt / SetD :</strong> copier Montant vérifié SD -> Dépôt; variances -> SetD.</li>
</ul>
""",
            "tags": ["Back", "Comptant"]
        },
        {
            "q": "Enveloppe blanche / dossier bleu : contenu ?",
            "a": """
<ul>
  <li><strong>Enveloppe compta :</strong> DSR 9p + Paiement par département, Cashier Details brochés, piles cartes, RECAP/SD signés, HP/Admin pack, Daily Cash Out, Guest Ledger, Detail Ticket, Room Post Audit, Availability Rebuild Exception, Sales Journal Payment Totals/Memo Listings par mode.</li>
  <li><strong>Dossier bleu daté :</strong> RJ vérif, Daily Revenue, Advance Deposit, Sales Journal Entire House, pile cartes, HP/Admin pack, Complimentary report, Room Type Production, Quasimodo, DBRS, caisses/dépôts.</li>
</ul>
""",
            "tags": ["Back", "Classement"]
        },
        {
            "q": "Pas de PDF qui s’affiche ?",
            "a": "Utilise le bouton Télécharger/Ouvrir brut. Les PDF scannés s’affichent inline; les DOCX sont convertis en PDF lorsque disponibles.",
            "tags": ["Support"]
        }
    ]
    tags = sorted({t for f in faqs for t in f.get("tags", [])})
    front_count = len([f for f in faqs if "Front" in f.get("tags", [])])
    back_count = len([f for f in faqs if "Back" in f.get("tags", [])])
    return render_template('faq.html', faqs=faqs, tags=tags, front_count=front_count, back_count=back_count)

@checklist_bp.route('/api/clear-role', methods=['POST'])
@login_required
def clear_role():
    session.pop('user_role', None)
    return jsonify({'success': True})

@checklist_bp.route('/api/set-role', methods=['POST'])
@login_required
def set_role():
    data = request.get_json()
    role = data.get('role')
    print(f"DEBUG: Setting role to {role}")
    if role in ['front', 'back']:
        session['user_role'] = role
        session.modified = True
        print(f"DEBUG: Session role is now {session.get('user_role')}")
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Invalid role'}), 400

@checklist_bp.route('/api/tasks')
@login_required
def get_tasks():
    role = session.get('user_role', 'front') # Default to front if missing
    print(f"DEBUG: get_tasks called. Role in session: {role}")
    tasks = Task.query.filter_by(is_active=True, role=role).order_by(Task.order).all()
    print(f"DEBUG: Found {len(tasks)} tasks for role {role}")
    return jsonify([t.to_dict() for t in tasks])

@checklist_bp.route('/api/shifts/current')
@login_required
def get_current_shift():
    today = date.today()
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
    today = date.today()
    shift = Shift.query.filter_by(date=today).first()
    if not shift:
        shift = Shift(date=today)
        db.session.add(shift)
        db.session.commit()
    return jsonify(shift.to_dict())

@checklist_bp.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    today = date.today()
    shift = Shift.query.filter_by(date=today).first()
    if not shift:
        shift = Shift(date=today)
        db.session.add(shift)
        db.session.commit()

    existing = TaskCompletion.query.filter_by(shift_id=shift.id, task_id=task_id).first()
    if existing:
        return jsonify(existing.to_dict())

    data = request.get_json() or {}
    completion = TaskCompletion(
        shift_id=shift.id,
        task_id=task_id,
        notes=data.get('notes')
    )
    db.session.add(completion)
    db.session.commit()
    return jsonify(completion.to_dict())

@checklist_bp.route('/api/tasks/<int:task_id>/uncomplete', methods=['POST'])
@login_required
def uncomplete_task(task_id):
    today = date.today()
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
    today = date.today()
    shift = Shift.query.filter_by(date=today).first()
    if shift:
        shift.completed_at = datetime.utcnow()
        db.session.commit()
        return jsonify(shift.to_dict())
    return jsonify({'error': 'No shift found'}), 404
