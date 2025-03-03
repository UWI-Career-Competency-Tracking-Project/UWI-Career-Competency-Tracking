from App.database import db
from datetime import datetime

class Competency(db.Model):
    __tablename__ = 'competencies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))

    workshop_competencies = db.relationship('WorkshopCompetency', back_populates='competency', lazy=True, cascade='all, delete-orphan')
    student_competencies = db.relationship('StudentCompetency', back_populates='competency', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Competency {self.name}>'

class WorkshopCompetency(db.Model):
    __tablename__ = 'workshop_competencies'
    
    id = db.Column(db.Integer, primary_key=True)
    workshop_id = db.Column(db.String(10), db.ForeignKey('workshops.id', ondelete='CASCADE'))
    competency_id = db.Column(db.Integer, db.ForeignKey('competencies.id', ondelete='CASCADE'))
    
    workshop = db.relationship('Workshop', back_populates='workshop_competencies')
    competency = db.relationship('Competency', back_populates='workshop_competencies')

    def __repr__(self):
        return f'<WorkshopCompetency {self.workshop_id}:{self.competency_id}>' 