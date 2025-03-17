from App.database import db
from datetime import datetime

class Competency(db.Model):
    __tablename__ = 'competencies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student_competencies = db.relationship('StudentCompetency', back_populates='competency', lazy=True, cascade='all, delete-orphan')

    def __init__(self, name, description=None):
        self.name = name
        self.description = description

    def __repr__(self):
        return f'<Competency {self.name}>' 