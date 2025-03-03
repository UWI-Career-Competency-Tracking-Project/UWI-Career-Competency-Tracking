from App.database import db
from datetime import datetime

class StudentCompetency(db.Model):
    __tablename__ = 'student_competencies'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'))
    competency_id = db.Column(db.Integer, db.ForeignKey('competencies.id', ondelete='CASCADE'))
    rank = db.Column(db.Integer, default=0) 
    feedback = db.Column(db.String(500))
    awarded_date = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', back_populates='student_competencies')
    competency = db.relationship('Competency', back_populates='student_competencies')

    def get_rank_name(self):
        ranks = {
            0: "Unranked",
            1: "Beginner",
            2: "Intermediate",
            3: "Advanced"
        }
        return ranks.get(self.rank, "Unranked") 