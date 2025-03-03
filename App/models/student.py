from .user import User
from .. import db
from datetime import datetime
from .enrollment import Enrollment
from .student_competency import StudentCompetency
from .competency import Competency

class Student(User):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    registration_date = db.Column(db.Date, default=datetime.utcnow)
    student_username = db.Column(db.String(80))
    region = db.Column(db.String(100))
    
    # Relationships
    enrollments = db.relationship('Enrollment', back_populates='student', lazy=True, cascade='all, delete-orphan')
    student_competencies = db.relationship('StudentCompetency', back_populates='student', lazy=True, cascade='all, delete-orphan')
    
    __mapper_args__ = {
        'polymorphic_identity': 'student',
        'inherit_condition': (id == User.id)
    }

    def __init__(self, username, email, password, first_name, last_name):
        super().__init__(username=username, email=email, password=password, first_name=first_name, last_name=last_name, user_type='student')
        self.student_username = username

    @classmethod
    def get_by_id(cls, student_id):
        """Get a student by ID with a fresh database session."""
        return db.session.query(cls).filter_by(id=student_id).first()

    @property
    def enrolled_workshops(self):
        """Get all workshops the student is enrolled in."""
        from .workshop import Workshop
        return Workshop.query.join(Enrollment).filter(
            Enrollment.student_id == self.id
        ).all()

    @property
    def competencies(self):
        """Get all competencies with their ranks and feedback."""
        student_competencies = StudentCompetency.query.filter_by(student_id=self.id).all()
        return {
            sc.competency.name: {
                "rank": sc.rank,
                "feedback": sc.feedback,
                "awarded_date": sc.awarded_date.isoformat() if sc.awarded_date else None
            }
            for sc in student_competencies
        }

    def add_competencies(self, new_competencies):
        """Add new competencies to the student's list."""
        if isinstance(new_competencies, str):
            new_competencies = [new_competencies]
        
        try:
            for comp_name in new_competencies:
                competency = Competency.query.filter_by(name=comp_name).first()
                if not competency:
                    competency = Competency(name=comp_name)
                    db.session.add(competency)
                
                existing = StudentCompetency.query.filter_by(
                    student_id=self.id,
                    competency_id=competency.id
                ).first()
                
                if not existing:
                    student_comp = StudentCompetency(
                        student_id=self.id,
                        competency_id=competency.id,
                        rank=0
                    )
                    db.session.add(student_comp)
            
            db.session.commit()
            print("Successfully added competencies")
            
        except Exception as e:
            print(f"Error adding competencies: {e}")
            db.session.rollback()
            raise

    def update_competency_rank(self, competency_name, rank, feedback):
        """Update the rank and feedback for a competency."""
        try:
            competency = Competency.query.filter_by(name=competency_name).first()
            if not competency:
                raise ValueError(f"Competency '{competency_name}' not found")
            
            student_comp = StudentCompetency.query.filter_by(
                student_id=self.id,
                competency_id=competency.id
            ).first()
            
            if not student_comp:
                student_comp = StudentCompetency(
                    student_id=self.id,
                    competency_id=competency.id
                )
                db.session.add(student_comp)
            
            student_comp.rank = rank
            student_comp.feedback = feedback
            student_comp.awarded_date = datetime.utcnow()
            
            db.session.commit()
            print("Successfully updated competency rank")
            
        except Exception as e:
            print(f"Error updating rank: {e}")
            db.session.rollback()
            raise

    def get_json(self):
        data = super().get_json()
        data.update({
            'registration_date': self.registration_date.strftime('%Y-%m-%d') if self.registration_date else None,
            'competencies': self.competencies
        })
        return data
