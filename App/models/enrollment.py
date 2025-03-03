from .. import db
from datetime import datetime

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshops.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', back_populates='enrollments')
    workshop = db.relationship('Workshop', back_populates='enrollments')

    def __init__(self, student_id, workshop_id):
        self.student_id = student_id
        self.workshop_id = workshop_id

    def add_workshop_competencies(self):
        """Add workshop competencies to the student"""
        try:
            from .competency import Competency
            from .student_competency import StudentCompetency
            
            if not self.workshop or not self.student:
                print("Workshop or student not found")
                return False
                
            print(f"Adding competencies from workshop {self.workshop.workshopName} to student {self.student.username}")
            print(f"Workshop competencies: {self.workshop.competencies}")
            
            for comp_name in self.workshop.competencies:
                if self.student._competencies is None:
                    self.student._competencies = {}

                if comp_name not in self.student._competencies:
                    self.student._competencies[comp_name] = {
                        'rank': 0,
                        'feedback': '',
                        'updated_at': datetime.utcnow().isoformat()
                    }
                
                competency = Competency.query.filter_by(name=comp_name).first()
                if not competency:
                    competency = Competency(name=comp_name)
                    db.session.add(competency)
                    db.session.flush()
                
                existing = StudentCompetency.query.filter_by(
                    student_id=self.student_id,
                    competency_id=competency.id
                ).first()
                
                if not existing:
                    student_comp = StudentCompetency(
                        student_id=self.student_id,
                        competency_id=competency.id,
                        competency_name=comp_name,
                        rank=0  
                    )
                    db.session.add(student_comp)
                    print(f"Added competency {comp_name} to student")

            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(self.student, '_competencies')
            db.session.add(self.student)
            db.session.commit()
            print(f"Successfully added competencies to student. Current competencies: {self.student.competencies}")
            return True
            
        except Exception as e:
            print(f"Error adding workshop competencies: {str(e)}")
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            db.session.rollback()
            return False

    def __repr__(self):
        return f'<Enrollment {self.student_id} - {self.workshop_id}>' 