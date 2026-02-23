# Plan d'implémentation - Pages Rapports & Balances

## Vue d'ensemble

Ce document décrit l'implémentation complète des pages **Rapports** et **Balances** pour l'application Night Audit du Sheraton Laval.

---

# PARTIE 1: PAGE RAPPORTS

## 1.1 Tableau de bord quotidien

### Description
Résumé visuel de l'audit du jour avec indicateurs clés et comparaison avec la veille.

### Source de données
- Fichier RJ uploadé (feuilles: Recap, transelect, DUBACK#, depot)
- Base de données SQLite (historique des shifts)

### Implémentation

#### Backend (routes/reports.py)
```python
from flask import Blueprint, jsonify, session
from utils.rj_reader import RJReader

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/api/reports/daily-summary')
def daily_summary():
    """Retourne le résumé du jour actuel."""
    # Lire depuis le RJ en mémoire
    rj_data = get_current_rj()

    return jsonify({
        'date': rj_data['controle']['date'],
        'revenue': {
            'comptant': rj_data['recap']['comptant_total'],
            'cartes': rj_data['transelect']['total'],
            'cheques': rj_data['recap']['cheque_total'],
        },
        'deposits': rj_data['depot']['total'],
        'variance': rj_data['recap']['surplus_deficit'],
        'dueback_total': rj_data['dueback']['total_z'],
    })

@reports_bp.route('/api/reports/daily-comparison')
def daily_comparison():
    """Compare aujourd'hui vs hier."""
    today = get_today_data()
    yesterday = get_yesterday_data()  # Depuis DB ou fichier précédent

    return jsonify({
        'today': today,
        'yesterday': yesterday,
        'changes': {
            'revenue': calculate_change(today['revenue'], yesterday['revenue']),
            'deposits': calculate_change(today['deposits'], yesterday['deposits']),
        }
    })
```

#### Frontend (templates/reports.html)
```html
<!-- Cartes de résumé -->
<div class="dashboard-grid">
    <div class="stat-card">
        <div class="stat-icon revenue"><i data-feather="dollar-sign"></i></div>
        <div class="stat-content">
            <div class="stat-label">Revenus Total</div>
            <div class="stat-value" id="total-revenue">$0.00</div>
            <div class="stat-change positive" id="revenue-change">+0%</div>
        </div>
    </div>

    <div class="stat-card">
        <div class="stat-icon deposits"><i data-feather="briefcase"></i></div>
        <div class="stat-content">
            <div class="stat-label">Dépôts</div>
            <div class="stat-value" id="total-deposits">$0.00</div>
        </div>
    </div>

    <div class="stat-card">
        <div class="stat-icon variance"><i data-feather="activity"></i></div>
        <div class="stat-content">
            <div class="stat-label">Variance</div>
            <div class="stat-value" id="variance">$0.00</div>
        </div>
    </div>

    <div class="stat-card">
        <div class="stat-icon dueback"><i data-feather="users"></i></div>
        <div class="stat-content">
            <div class="stat-label">DueBack Total</div>
            <div class="stat-value" id="dueback-total">$0.00</div>
        </div>
    </div>
</div>
```

#### Base de données (nouveau modèle)
```python
# database/models.py

class DailyReport(db.Model):
    """Stocke les données quotidiennes pour historique."""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)

    # Revenus
    revenue_comptant = db.Column(db.Float, default=0)
    revenue_cartes = db.Column(db.Float, default=0)
    revenue_cheques = db.Column(db.Float, default=0)
    revenue_total = db.Column(db.Float, default=0)

    # Dépôts
    deposit_cdn = db.Column(db.Float, default=0)
    deposit_us = db.Column(db.Float, default=0)

    # Variances
    variance = db.Column(db.Float, default=0)
    dueback_total = db.Column(db.Float, default=0)

    # Métadonnées
    auditor_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
```

---

## 1.2 Tendances mensuelles/hebdomadaires

### Description
Graphiques interactifs montrant l'évolution des métriques sur 7/30 jours.

### Librairie recommandée
**Chart.js** - Léger, facile à utiliser, bonne documentation.

### Implémentation

#### Backend
```python
@reports_bp.route('/api/reports/trends')
def get_trends():
    """Retourne les données pour graphiques de tendances."""
    period = request.args.get('period', '7')  # 7 ou 30 jours

    start_date = datetime.now() - timedelta(days=int(period))

    reports = DailyReport.query.filter(
        DailyReport.date >= start_date
    ).order_by(DailyReport.date).all()

    return jsonify({
        'labels': [r.date.strftime('%d/%m') for r in reports],
        'datasets': {
            'revenue': [r.revenue_total for r in reports],
            'deposits': [r.deposit_cdn + r.deposit_us for r in reports],
            'variance': [r.variance for r in reports],
            'dueback': [r.dueback_total for r in reports],
        }
    })
```

#### Frontend
```html
<!-- Inclure Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<!-- Sélecteur de période -->
<div class="period-selector">
    <button onclick="loadTrends(7)" class="active">7 jours</button>
    <button onclick="loadTrends(30)">30 jours</button>
</div>

<!-- Graphique -->
<canvas id="revenue-chart"></canvas>

<script>
async function loadTrends(days) {
    const res = await fetch(`/api/reports/trends?period=${days}`);
    const data = await res.json();

    new Chart(document.getElementById('revenue-chart'), {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Revenus',
                data: data.datasets.revenue,
                borderColor: '#3b82f6',
                tension: 0.3
            }, {
                label: 'Dépôts',
                data: data.datasets.deposits,
                borderColor: '#10b981',
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' }
            }
        }
    });
}
</script>
```

---

## 1.3 Rapport de variances

### Description
Suivi des écarts de caisse par réceptionniste avec alertes.

### Implémentation

#### Nouveau modèle DB
```python
class VarianceRecord(db.Model):
    """Historique des variances par réceptionniste."""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    receptionist = db.Column(db.String(100), nullable=False)
    expected = db.Column(db.Float, default=0)
    actual = db.Column(db.Float, default=0)
    variance = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)

    @property
    def is_alert(self):
        """Retourne True si variance > seuil (ex: 50$)."""
        return abs(self.variance) > 50
```

#### Backend
```python
@reports_bp.route('/api/reports/variances')
def get_variances():
    """Liste des variances avec filtres."""
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    receptionist = request.args.get('receptionist')

    query = VarianceRecord.query

    if start_date:
        query = query.filter(VarianceRecord.date >= start_date)
    if end_date:
        query = query.filter(VarianceRecord.date <= end_date)
    if receptionist:
        query = query.filter(VarianceRecord.receptionist == receptionist)

    records = query.order_by(VarianceRecord.date.desc()).all()

    return jsonify({
        'records': [r.to_dict() for r in records],
        'summary': {
            'total_variance': sum(r.variance for r in records),
            'alert_count': sum(1 for r in records if r.is_alert),
            'by_receptionist': get_variance_by_receptionist(records)
        }
    })

@reports_bp.route('/api/reports/variances/by-receptionist')
def variances_by_receptionist():
    """Résumé des variances par réceptionniste."""
    results = db.session.query(
        VarianceRecord.receptionist,
        func.count(VarianceRecord.id).label('count'),
        func.sum(VarianceRecord.variance).label('total'),
        func.avg(VarianceRecord.variance).label('average')
    ).group_by(VarianceRecord.receptionist).all()

    return jsonify([{
        'name': r.receptionist,
        'count': r.count,
        'total': r.total,
        'average': r.average
    } for r in results])
```

#### Frontend - Tableau avec alertes
```html
<div class="variance-filters">
    <input type="date" id="start-date">
    <input type="date" id="end-date">
    <select id="receptionist-filter">
        <option value="">Tous les réceptionnistes</option>
    </select>
    <button onclick="loadVariances()">Filtrer</button>
</div>

<table class="variance-table">
    <thead>
        <tr>
            <th>Date</th>
            <th>Réceptionniste</th>
            <th>Attendu</th>
            <th>Réel</th>
            <th>Variance</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody id="variance-body">
        <!-- Rempli par JS -->
    </tbody>
</table>

<script>
function renderVarianceRow(record) {
    const isAlert = Math.abs(record.variance) > 50;
    return `
        <tr class="${isAlert ? 'alert-row' : ''}">
            <td>${record.date}</td>
            <td>${record.receptionist}</td>
            <td>$${record.expected.toFixed(2)}</td>
            <td>$${record.actual.toFixed(2)}</td>
            <td class="${record.variance < 0 ? 'negative' : 'positive'}">
                $${record.variance.toFixed(2)}
            </td>
            <td>
                ${isAlert ? '<span class="badge alert">⚠️ Alerte</span>' : '<span class="badge ok">✓</span>'}
            </td>
        </tr>
    `;
}
</script>
```

---

## 1.4 Rapport cartes de crédit

### Description
Analyse détaillée des transactions par carte avec comparaisons.

### Implémentation

#### Backend
```python
@reports_bp.route('/api/reports/credit-cards')
def credit_card_report():
    """Rapport détaillé des cartes de crédit."""
    # Lire depuis RJ transelect
    rj_data = get_current_rj()
    transelect = rj_data.get('transelect', {})

    return jsonify({
        'by_type': {
            'visa': transelect.get('visa_total', 0),
            'mastercard': transelect.get('master_total', 0),
            'amex': transelect.get('amex_total', 0),
            'debit': transelect.get('debit_total', 0),
        },
        'by_source': {
            'terminal': transelect.get('terminal_total', 0),
            'fusebox': transelect.get('fusebox_total', 0),
            'positouch': transelect.get('positouch_total', 0),
        },
        'reconciliation': {
            'terminal_total': transelect.get('terminal_total', 0),
            'fusebox_total': transelect.get('fusebox_total', 0),
            'difference': transelect.get('terminal_total', 0) - transelect.get('fusebox_total', 0),
            'is_balanced': abs(transelect.get('terminal_total', 0) - transelect.get('fusebox_total', 0)) < 0.01
        }
    })
```

#### Frontend - Graphique en donut
```html
<div class="credit-card-report">
    <div class="chart-container">
        <canvas id="card-type-chart"></canvas>
    </div>

    <div class="reconciliation-status">
        <h4>Réconciliation Terminal vs Fusebox</h4>
        <div class="recon-row">
            <span>Terminal:</span>
            <span id="terminal-total">$0.00</span>
        </div>
        <div class="recon-row">
            <span>Fusebox:</span>
            <span id="fusebox-total">$0.00</span>
        </div>
        <div class="recon-row difference">
            <span>Différence:</span>
            <span id="difference">$0.00</span>
        </div>
        <div id="balance-status" class="status-indicator"></div>
    </div>
</div>

<script>
function renderCardChart(data) {
    new Chart(document.getElementById('card-type-chart'), {
        type: 'doughnut',
        data: {
            labels: ['Visa', 'Mastercard', 'Amex', 'Débit'],
            datasets: [{
                data: [
                    data.by_type.visa,
                    data.by_type.mastercard,
                    data.by_type.amex,
                    data.by_type.debit
                ],
                backgroundColor: ['#1a73e8', '#ff5722', '#00bcd4', '#4caf50']
            }]
        }
    });
}
</script>
```

---

## 1.5 Exports PDF/Excel

### Description
Générer des rapports téléchargeables.

### Librairies recommandées
- **PDF**: `reportlab` ou `weasyprint`
- **Excel**: `openpyxl` (déjà utilisé) ou `xlsxwriter`

### Implémentation

#### Backend
```python
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

@reports_bp.route('/api/reports/export/pdf')
def export_pdf():
    """Génère un PDF du rapport quotidien."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Titre
    elements.append(Paragraph(f"Rapport d'Audit - {datetime.now().strftime('%d/%m/%Y')}", styles['Title']))

    # Tableau des revenus
    data = get_daily_summary()
    table_data = [
        ['Catégorie', 'Montant'],
        ['Comptant', f"${data['revenue']['comptant']:.2f}"],
        ['Cartes', f"${data['revenue']['cartes']:.2f}"],
        ['Chèques', f"${data['revenue']['cheques']:.2f}"],
        ['Total', f"${data['revenue']['total']:.2f}"],
    ]

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'rapport_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

@reports_bp.route('/api/reports/export/excel')
def export_excel():
    """Génère un Excel du rapport mensuel."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Rapport Mensuel"

    # En-têtes
    headers = ['Date', 'Revenus', 'Dépôts', 'Variance', 'DueBack']
    ws.append(headers)

    # Données
    reports = DailyReport.query.filter(
        DailyReport.date >= datetime.now() - timedelta(days=30)
    ).all()

    for r in reports:
        ws.append([
            r.date.strftime('%Y-%m-%d'),
            r.revenue_total,
            r.deposit_cdn + r.deposit_us,
            r.variance,
            r.dueback_total
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'rapport_mensuel_{datetime.now().strftime("%Y%m")}.xlsx'
    )
```

---

# PARTIE 2: PAGE BALANCES

## 2.1 Balance journalière

### Description
Vue en temps réel des comptes avec vérification automatique.

### Implémentation

#### Backend
```python
from flask import Blueprint

balances_bp = Blueprint('balances', __name__)

@balances_bp.route('/api/balances/daily')
def daily_balance():
    """Retourne les balances du jour."""
    rj_data = get_current_rj()

    # Lire depuis feuille GEAC
    geac = rj_data.get('geac_ux', {})

    return jsonify({
        'accounts': {
            'ar_balance': geac.get('balance_today', 0),
            'ar_previous': geac.get('balance_previous', 0),
            'guest_ledger': geac.get('balance_today_guest', 0),
            'city_ledger': geac.get('city_ledger', 0),
        },
        'verification': {
            'expected': calculate_expected_balance(rj_data),
            'actual': geac.get('new_balance', 0),
            'difference': calculate_expected_balance(rj_data) - geac.get('new_balance', 0),
            'is_balanced': abs(calculate_expected_balance(rj_data) - geac.get('new_balance', 0)) < 0.01
        }
    })
```

#### Frontend
```html
<div class="balance-dashboard">
    <!-- Comptes principaux -->
    <div class="accounts-grid">
        <div class="account-card">
            <h4>AR Balance</h4>
            <div class="balance-value" id="ar-balance">$0.00</div>
            <div class="balance-change" id="ar-change">vs hier: $0.00</div>
        </div>

        <div class="account-card">
            <h4>Guest Ledger</h4>
            <div class="balance-value" id="guest-ledger">$0.00</div>
        </div>

        <div class="account-card">
            <h4>City Ledger</h4>
            <div class="balance-value" id="city-ledger">$0.00</div>
        </div>
    </div>

    <!-- Vérification -->
    <div class="verification-panel">
        <h3>Vérification de Balance</h3>
        <div class="verify-row">
            <span>Balance attendue:</span>
            <span id="expected-balance">$0.00</span>
        </div>
        <div class="verify-row">
            <span>Balance actuelle:</span>
            <span id="actual-balance">$0.00</span>
        </div>
        <div class="verify-row difference">
            <span>Différence:</span>
            <span id="balance-diff">$0.00</span>
        </div>

        <div id="balance-status" class="status-banner">
            <!-- Affiche ✓ Balancé ou ⚠️ Écart détecté -->
        </div>
    </div>
</div>
```

---

## 2.2 Réconciliation

### Description
Outils pour réconcilier différentes sources (banque, cartes, caisse).

### Implémentation

#### Backend
```python
@balances_bp.route('/api/balances/reconciliation/cash')
def cash_reconciliation():
    """Réconciliation de la caisse."""
    rj_data = get_current_rj()
    recap = rj_data.get('recap', {})

    return jsonify({
        'system': {
            'lightspeed': recap.get('comptant_lightspeed', 0),
            'positouch': recap.get('comptant_positouch', 0),
            'total': recap.get('comptant_total', 0),
        },
        'counted': None,  # À remplir par l'utilisateur
        'variance': None,
        'status': 'pending'  # pending, balanced, variance
    })

@balances_bp.route('/api/balances/reconciliation/cash', methods=['POST'])
def submit_cash_count():
    """Soumet le comptage de caisse."""
    data = request.get_json()
    counted = data.get('counted', 0)

    rj_data = get_current_rj()
    system_total = rj_data['recap']['comptant_total']

    variance = counted - system_total

    # Sauvegarder en DB
    record = CashReconciliation(
        date=datetime.now().date(),
        system_total=system_total,
        counted_total=counted,
        variance=variance,
        auditor=session.get('user_name')
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        'system': system_total,
        'counted': counted,
        'variance': variance,
        'is_balanced': abs(variance) < 0.01
    })
```

---

## 2.3 Calculatrice de caisse

### Description
Outil pour compter billets et pièces avec calcul automatique.

### Implémentation (Frontend uniquement)

```html
<div class="cash-calculator">
    <h3>Calculatrice de Caisse</h3>

    <div class="denomination-grid">
        <!-- Billets -->
        <div class="denom-section">
            <h4>Billets</h4>
            <div class="denom-row">
                <label>$100 ×</label>
                <input type="number" data-value="100" class="denom-input" min="0">
                <span class="denom-total">$0.00</span>
            </div>
            <div class="denom-row">
                <label>$50 ×</label>
                <input type="number" data-value="50" class="denom-input" min="0">
                <span class="denom-total">$0.00</span>
            </div>
            <div class="denom-row">
                <label>$20 ×</label>
                <input type="number" data-value="20" class="denom-input" min="0">
                <span class="denom-total">$0.00</span>
            </div>
            <div class="denom-row">
                <label>$10 ×</label>
                <input type="number" data-value="10" class="denom-input" min="0">
                <span class="denom-total">$0.00</span>
            </div>
            <div class="denom-row">
                <label>$5 ×</label>
                <input type="number" data-value="5" class="denom-input" min="0">
                <span class="denom-total">$0.00</span>
            </div>
        </div>

        <!-- Pièces -->
        <div class="denom-section">
            <h4>Pièces</h4>
            <div class="denom-row">
                <label>$2 ×</label>
                <input type="number" data-value="2" class="denom-input" min="0">
                <span class="denom-total">$0.00</span>
            </div>
            <div class="denom-row">
                <label>$1 ×</label>
                <input type="number" data-value="1" class="denom-input" min="0">
                <span class="denom-total">$0.00</span>
            </div>
            <div class="denom-row">
                <label>$0.25 ×</label>
                <input type="number" data-value="0.25" class="denom-input" min="0">
                <span class="denom-total">$0.00</span>
            </div>
            <div class="denom-row">
                <label>$0.10 ×</label>
                <input type="number" data-value="0.10" class="denom-input" min="0">
                <span class="denom-total">$0.00</span>
            </div>
            <div class="denom-row">
                <label>$0.05 ×</label>
                <input type="number" data-value="0.05" class="denom-input" min="0">
                <span class="denom-total">$0.00</span>
            </div>
        </div>
    </div>

    <div class="calculator-total">
        <span>TOTAL:</span>
        <span id="cash-total">$0.00</span>
    </div>

    <button onclick="applyCashCount()" class="btn-primary">
        Appliquer à la réconciliation
    </button>
</div>

<script>
document.querySelectorAll('.denom-input').forEach(input => {
    input.addEventListener('input', calculateCashTotal);
});

function calculateCashTotal() {
    let total = 0;
    document.querySelectorAll('.denom-input').forEach(input => {
        const value = parseFloat(input.dataset.value);
        const count = parseInt(input.value) || 0;
        const subtotal = value * count;

        input.nextElementSibling.textContent = `$${subtotal.toFixed(2)}`;
        total += subtotal;
    });

    document.getElementById('cash-total').textContent = `$${total.toFixed(2)}`;
}
</script>
```

---

## 2.4 Suivi X20 / Master Balance

### Description
Afficher et vérifier les balances depuis la feuille "jour" du RJ.

### Implémentation

#### Backend
```python
@balances_bp.route('/api/balances/x20')
def x20_balance():
    """Retourne les données X20 depuis la feuille jour."""
    rj_data = get_current_rj()
    jour = rj_data.get('jour', {})

    current_day = rj_data['controle']['vjour']

    # Lire la ligne du jour dans la feuille jour
    # X20 est généralement la colonne de balance finale

    return jsonify({
        'day': current_day,
        'master_balance': {
            'rooms': jour.get(f'day_{current_day}_rooms', 0),
            'fb': jour.get(f'day_{current_day}_fb', 0),
            'other': jour.get(f'day_{current_day}_other', 0),
            'total': jour.get(f'day_{current_day}_total', 0),
        },
        'x20': {
            'debit': jour.get(f'day_{current_day}_x20_debit', 0),
            'credit': jour.get(f'day_{current_day}_x20_credit', 0),
            'balance': jour.get(f'day_{current_day}_x20_balance', 0),
        },
        'is_balanced': abs(jour.get(f'day_{current_day}_x20_balance', 0)) < 0.01
    })
```

#### Frontend
```html
<div class="x20-panel">
    <h3>Master Balance (X20)</h3>

    <div class="x20-grid">
        <div class="x20-card">
            <h4>Rooms Revenue</h4>
            <div class="x20-value" id="x20-rooms">$0.00</div>
        </div>
        <div class="x20-card">
            <h4>F&B Revenue</h4>
            <div class="x20-value" id="x20-fb">$0.00</div>
        </div>
        <div class="x20-card">
            <h4>Other Revenue</h4>
            <div class="x20-value" id="x20-other">$0.00</div>
        </div>
    </div>

    <div class="x20-summary">
        <div class="summary-row">
            <span>Total Débits:</span>
            <span id="x20-debit">$0.00</span>
        </div>
        <div class="summary-row">
            <span>Total Crédits:</span>
            <span id="x20-credit">$0.00</span>
        </div>
        <div class="summary-row balance">
            <span>Balance:</span>
            <span id="x20-balance">$0.00</span>
        </div>
    </div>

    <div id="x20-status" class="balance-indicator">
        <!-- ✓ Balancé à zéro ou ⚠️ Déséquilibré -->
    </div>
</div>
```

---

## 2.5 Fin de mois

### Description
Checklist et outils pour la clôture mensuelle.

### Implémentation

#### Backend
```python
@balances_bp.route('/api/balances/month-end')
def month_end_summary():
    """Résumé de fin de mois."""
    # Obtenir le mois en cours
    today = datetime.now()
    first_day = today.replace(day=1)

    # Agréger les données du mois
    reports = DailyReport.query.filter(
        DailyReport.date >= first_day,
        DailyReport.date <= today
    ).all()

    return jsonify({
        'month': today.strftime('%B %Y'),
        'days_completed': len(reports),
        'days_remaining': (today.replace(month=today.month+1, day=1) - timedelta(days=1)).day - today.day,
        'totals': {
            'revenue': sum(r.revenue_total for r in reports),
            'deposits': sum(r.deposit_cdn + r.deposit_us for r in reports),
            'variance': sum(r.variance for r in reports),
        },
        'averages': {
            'daily_revenue': sum(r.revenue_total for r in reports) / len(reports) if reports else 0,
            'daily_deposits': sum(r.deposit_cdn + r.deposit_us for r in reports) / len(reports) if reports else 0,
        },
        'checklist': get_month_end_checklist()
    })

def get_month_end_checklist():
    """Retourne la checklist de fin de mois."""
    return [
        {'id': 1, 'task': 'Vérifier toutes les variances du mois', 'completed': False},
        {'id': 2, 'task': 'Réconcilier les dépôts bancaires', 'completed': False},
        {'id': 3, 'task': 'Vérifier les balances AR', 'completed': False},
        {'id': 4, 'task': 'Exporter le rapport mensuel', 'completed': False},
        {'id': 5, 'task': 'Archiver les fichiers RJ', 'completed': False},
    ]
```

---

# PARTIE 3: STRUCTURE DES FICHIERS

## Nouveaux fichiers à créer

```
audit-pack/
├── routes/
│   ├── reports.py          # Nouvelles routes rapports
│   └── balances.py         # Nouvelles routes balances
├── templates/
│   ├── reports.html        # Page rapports
│   └── balances.html       # Page balances
├── database/
│   └── models.py           # Ajouter DailyReport, VarianceRecord, etc.
└── static/
    └── js/
        ├── charts.js       # Fonctions Chart.js
        └── calculator.js   # Calculatrice de caisse
```

## Enregistrement des blueprints (main.py)

```python
from routes.reports import reports_bp
from routes.balances import balances_bp

app.register_blueprint(reports_bp)
app.register_blueprint(balances_bp)
```

## Mise à jour de la navigation (base.html)

```html
<a href="{{ url_for('reports.reports_page') }}" class="menu-item">
    <i data-feather="bar-chart-2"></i>
    <span>Rapports</span>
</a>
<a href="{{ url_for('balances.balances_page') }}" class="menu-item">
    <i data-feather="percent"></i>
    <span>Balances</span>
</a>
```

---

# PARTIE 4: PLAN DE DÉVELOPPEMENT

## Phase 1 - Fondations (Priorité haute)
1. Créer les modèles de base de données
2. Créer les routes de base pour rapports et balances
3. Créer les templates HTML de base
4. Implémenter le tableau de bord quotidien

## Phase 2 - Fonctionnalités principales
1. Implémenter les graphiques de tendances (Chart.js)
2. Ajouter le rapport de variances
3. Créer la calculatrice de caisse
4. Implémenter la réconciliation

## Phase 3 - Fonctionnalités avancées
1. Exports PDF/Excel
2. Suivi X20/Master Balance
3. Outils de fin de mois
4. Alertes automatiques

## Phase 4 - Polissage
1. Améliorer l'UI/UX
2. Ajouter des animations/transitions
3. Optimiser les performances
4. Tests et corrections de bugs

---

# PARTIE 5: DÉPENDANCES À AJOUTER

```
# requirements.txt additions
chart.js          # Via CDN, pas pip
reportlab>=4.0    # Pour génération PDF
openpyxl>=3.1     # Déjà présent pour Excel
```

---

*Document créé le 2026-01-18*
*À mettre à jour au fur et à mesure de l'implémentation*
