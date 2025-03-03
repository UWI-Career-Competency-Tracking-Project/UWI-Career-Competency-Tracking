from .. import db
from datetime import datetime
from .student_competency import StudentCompetency
from .competency import Competency

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'))
    workshop_id = db.Column(db.String(10), db.ForeignKey('workshops.id', ondelete='CASCADE'))
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', back_populates='enrollments')
    workshop = db.relationship('Workshop', back_populates='enrollments')

    def __init__(self, student_id, workshop_id):
        self.student_id = student_id
        self.workshop_id = workshop_id

    def add_workshop_competencies(self):
        """Add workshop's competencies to the enrolled student."""
        try:
            workshop_competencies = [wc.competency for wc in self.workshop.workshop_competencies]
            
            for competency in workshop_competencies:
                existing = StudentCompetency.query.filter_by(
                    student_id=self.student_id,
                    competency_id=competency.id
                ).first()
                
                if not existing:
                    student_comp = StudentCompetency(
                        student_id=self.student_id,
                        competency_id=competency.id,
                        rank=0  
                    )
                    db.session.add(student_comp)
            
            db.session.commit()
            print(f"Added {len(workshop_competencies)} competencies to student {self.student_id}")
            
        except Exception as e:
            print(f"Error adding workshop competencies to student: {e}")
            db.session.rollback()
            raise

    def __repr__(self):
        return f'<Enrollment {self.student_id}:{self.workshop_id}>' 