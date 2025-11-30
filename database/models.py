from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer, nullable=False)
    title_fr = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # pre_audit, part1, part2, end_shift
    is_active = db.Column(db.Boolean, default=True)

    # Phase 2: Detailed instructions
    description_fr = db.Column(db.Text, nullable=True)  # Why this task matters
    steps_json = db.Column(db.Text, nullable=True)  # JSON array of step-by-step instructions
    screenshots_json = db.Column(db.Text, nullable=True)  # JSON array of screenshot filenames
    tips_fr = db.Column(db.Text, nullable=True)  # Helpful tips or warnings
    system_used = db.Column(db.String(100), nullable=True)  # Lightspeed, GXP, Espresso, etc.
    estimated_minutes = db.Column(db.Integer, nullable=True)  # Estimated time to complete

    completions = db.relationship('TaskCompletion', backref='task', lazy=True)

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'order': self.order,
            'title_fr': self.title_fr,
            'category': self.category,
            'is_active': self.is_active,
            'description_fr': self.description_fr,
            'steps': json.loads(self.steps_json) if self.steps_json else [],
            'screenshots': json.loads(self.screenshots_json) if self.screenshots_json else [],
            'tips_fr': self.tips_fr,
            'system_used': self.system_used,
            'estimated_minutes': self.estimated_minutes,
            'has_details': bool(self.steps_json)
        }


class Shift(db.Model):
    __tablename__ = 'shifts'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    completions = db.relationship('TaskCompletion', backref='shift', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class TaskCompletion(db.Model):
    __tablename__ = 'task_completions'

    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'shift_id': self.shift_id,
            'task_id': self.task_id,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'notes': self.notes
        }
