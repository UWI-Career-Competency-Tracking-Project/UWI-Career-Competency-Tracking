from App.database import db
from datetime import datetime

class StudentCompetency(db.Model):
    __tablename__ = 'student_competencies'
    
    studentCOMPID = db.Column(db.Integer, primary_key=True)
    studentID = db.Column(db.Integer, db.ForeignKey('students.id'))
    competencyID = db.Column(db.Integer, db.ForeignKey('competencies.competencyID'))
    Tiers = db.Column(db.String(50))
    earnedDate = db.Column(db.Date, default=datetime.utcnow) 