from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import date, datetime
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
    return render_template('checklist.html')

@checklist_bp.route('/api/tasks')
@login_required
def get_tasks():
    tasks = Task.query.filter_by(is_active=True).order_by(Task.order).all()
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
