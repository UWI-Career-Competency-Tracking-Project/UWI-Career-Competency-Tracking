from .. import db
from datetime import datetime

class StudentCompetency(db.Model):
    __tablename__ = 'student_competencies'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    competency_id = db.Column(db.Integer, db.ForeignKey('competencies.id'), nullable=False)
    competency_name = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.Integer, default=0)  
    feedback = db.Column(db.Text)
    certificate_status = db.Column(db.String(20), default=None)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship('Student', back_populates='student_competencies')
    competency = db.relationship('Competency', back_populates='student_competencies')

    def __init__(self, student_id, competency_id, competency_name, rank=1, feedback=None):
        self.student_id = student_id
        self.competency_id = competency_id
        self.competency_name = competency_name
        self.rank = rank
        self.feedback = feedback

    def update_rank(self, new_rank, feedback=None):
        """Update the competency rank and feedback"""
        try:
            self.rank = new_rank
            if feedback:
                self.feedback = feedback
            self.updated_at = datetime.utcnow()
            return True
        except Exception as e:
            print(f"Error updating rank: {str(e)}")
            return False

    def __repr__(self):
        return f'<StudentCompetency {self.student_id} - {self.competency_name}>'

    def get_rank_name(self):
        ranks = {
            1: "Beginner",
            2: "Intermediate",
            3: "Advanced"
        }
        return ranks.get(self.rank, "Unranked") 