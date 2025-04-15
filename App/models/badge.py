from App.database import db
from datetime import datetime

# Not used anymore - This model has been deprecated

class Badge(db.Model):
    __tablename__ = 'badges'
    
    badgeID = db.Column(db.Integer, primary_key=True)
    badgeName = db.Column(db.String(100), nullable=False)
    issueDate = db.Column(db.String(50))
    
    # Update to reference the correct column in competencies
    competencyID = db.Column(db.Integer, db.ForeignKey('competencies.id'))
    competency = db.relationship('Competency', backref='badges')