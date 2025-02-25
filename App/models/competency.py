from App.database import db

class Competency(db.Model):
    __tablename__ = 'competencies'
    
    competencyID = db.Column(db.Integer, primary_key=True)
    competencyName = db.Column(db.String(100), nullable=False)
    competencyDescription = db.Column(db.String(500))
    
    # Relationships
    workshops = db.relationship('Workshop', secondary='workshop_competencies', backref='competencies')
    
    def validate(self):
        pass 