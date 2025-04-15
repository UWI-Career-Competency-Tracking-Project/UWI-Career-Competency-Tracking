from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    
def create_db():
    """Helper function for tests that creates all database tables"""
    db.create_all() 