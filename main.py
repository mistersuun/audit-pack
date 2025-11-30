import os
from flask import Flask, redirect, url_for
from config.settings import Config
from database import db
from routes import auth_bp, checklist_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Fix database path for absolute reference
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database", "audit.db")}'

    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(checklist_bp)

    # Create tables
    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return redirect(url_for('checklist.index'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)
