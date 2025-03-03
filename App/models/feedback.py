from App.database import db
from datetime import datetime

class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    feedbackID = db.Column(db.Integer, primary_key=True)
    feedbackComment = db.Column(db.String(500))
    feedbackRating = db.Column(db.Integer)
    feedbackDate = db.Column(db.Date, default=datetime.utcnow)
    
    # Relationships
    studentID = db.Column(db.Integer, db.ForeignKey('students.id'))
    employerID = db.Column(db.Integer, db.ForeignKey('employers.id')) 