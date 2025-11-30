import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../database/audit.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUDIT_PIN = os.getenv('AUDIT_PIN', '1234')
