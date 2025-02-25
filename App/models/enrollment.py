from .. import db
from datetime import datetime

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshops.workshopID'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='enrollments')
    workshop = db.relationship('Workshop', backref='enrollments') 