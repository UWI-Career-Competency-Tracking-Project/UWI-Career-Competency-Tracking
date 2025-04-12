from .. import db
from datetime import datetime

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshops.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='enrolled')  
    attended = db.Column(db.Boolean, default=False)
    attendance_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    certificate_status = db.Column(db.String(50), nullable=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', back_populates='enrollments')
    workshop = db.relationship('Workshop', back_populates='enrollments')

    def __init__(self, student_id, workshop_id):
        self.student_id = student_id
        self.workshop_id = workshop_id
        self.enrollment_date = datetime.now()
        self.status = 'enrolled'
        self.attended = False
        self.attendance_date = None
        self.completed = False
        self.completion_date = None

    def add_workshop_competencies(self):
        """Add workshop competencies to the student after workshop completion"""
        try:
            if not self.completed:
                print("Workshop not marked as completed. Competencies won't be added.")
                return False
                
            from .competency import Competency
            from .student_competency import StudentCompetency
            
            if not self.workshop or not self.student:
                print("Workshop or student not found")
                return False
                
            print(f"Adding competencies from workshop {self.workshop.workshopName} to student {self.student.username}")
            print(f"Workshop competencies: {self.workshop.competencies}")
            
            for comp_name in self.workshop.competencies:
                rank = 1 
                if " III" in comp_name or comp_name.endswith(" III"):
                    rank = 3
                elif " II" in comp_name or comp_name.endswith(" II"):
                    rank = 2  
                elif " I" in comp_name or comp_name.endswith(" I"):
                    rank = 1 
                
                print(f"Determined rank {rank} for competency {comp_name}")
                
                if self.student._competencies is None:
                    self.student._competencies = {}

                if comp_name not in self.student._competencies:
                    self.student._competencies[comp_name] = {
                        'rank': rank,  
                        'feedback': f'Earned through {self.workshop.workshopName} workshop',
                        'updated_at': datetime.utcnow().isoformat()
                    }
                else:
                    current_rank = self.student._competencies[comp_name].get('rank', 0)
                    if rank > current_rank:
                        self.student._competencies[comp_name]['rank'] = rank
                        print(f"Upgraded rank from {current_rank} to {rank} for {comp_name}")
                    
                    existing_feedback = self.student._competencies[comp_name].get('feedback', '')
                    workshop_feedback = f'Earned through {self.workshop.workshopName} workshop'
                    
                    if workshop_feedback not in existing_feedback:
                        new_feedback = existing_feedback + "; " + workshop_feedback if existing_feedback else workshop_feedback
                        self.student._competencies[comp_name]['feedback'] = new_feedback
                        self.student._competencies[comp_name]['updated_at'] = datetime.utcnow().isoformat()
                
                competency = Competency.query.filter_by(name=comp_name).first()
                if not competency:
                    level = rank  
                    
                    competency = Competency(name=comp_name, level=level)
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
                        rank=rank, 
                        feedback="Completed via workshop: " + self.workshop.workshopName
                    )
                    db.session.add(student_comp)
                    print(f"Added competency {comp_name} with rank {rank} to student")
                else:
                    if rank > existing.rank:
                        existing.rank = rank
                        print(f"Updated competency {comp_name} rank from {existing.rank} to {rank}")
                    
                    existing_feedback = existing.feedback or ""
                    workshop_feedback = f'Earned through {self.workshop.workshopName} workshop'
                    
                    if workshop_feedback not in existing_feedback:
                        new_feedback = existing_feedback + "; " + workshop_feedback if existing_feedback else workshop_feedback
                        existing.feedback = new_feedback
                        db.session.add(existing)
                    
                    print(f"Updated existing competency {comp_name} for student")

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

    def mark_attended(self):
        self.attended = True
        self.attendance_date = datetime.now()
        db.session.commit()
    
    def mark_not_attended(self):
        self.attended = False
        self.attendance_date = None
        db.session.commit()
    
    def mark_completed(self):
        """Mark the workshop as completed and add competencies to student"""
        self.completed = True
        self.completion_date = datetime.now()
        self.status = 'completed'
        db.session.commit()
        
        return self.add_workshop_competencies()
    
    def mark_not_completed(self):
        """Remove completed status"""
        self.completed = False
        self.completion_date = None
        if self.attended:
            self.status = 'attended'
        else:
            self.status = 'enrolled'
        db.session.commit()
    
    def cancel(self):
        self.status = 'cancelled'
        db.session.commit()

    def __repr__(self):
        return f'<Enrollment {self.id}: Student {self.student_id} in Workshop {self.workshop_id}>' 