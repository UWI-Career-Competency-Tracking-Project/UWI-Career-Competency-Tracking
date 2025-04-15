from .. import db
from .user import User
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime
from .enrollment import Enrollment
from .student_competency import StudentCompetency
from .competency import Competency

class Student(User):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    student_id = db.Column(db.String(20), unique=True)
    _competencies = db.Column('competencies', db.JSON, default=dict)
    profile_pic = db.Column(db.String(255))
    resume = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    degree = db.Column(db.String(100))
    
    enrollments = db.relationship('Enrollment', back_populates='student', lazy=True, cascade='all, delete-orphan')
    student_competencies = db.relationship('StudentCompetency', back_populates='student', lazy=True, cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }
    
    __table_args__ = {
        'extend_existing': True
    }

    def __init__(self, username, password, email, first_name, last_name, student_id):
        super().__init__(username=username, password=password, email=email, first_name=first_name, last_name=last_name, user_type='student')
        self.student_id = student_id
        self._competencies = {}
        self.profile_pic = None
        self.resume = None
        self.phone = None
        self.location = None
        self.degree = None

    @property
    def competencies(self):
        """Get student's competencies"""
        if self._competencies is None:
            self._competencies = {}
            flag_modified(self, '_competencies')
            db.session.add(self)
            try:
                db.session.commit()
            except:
                db.session.rollback()
        return self._competencies

    def get_competency_names(self):
        """Get a list of competency names for this student"""
        if self._competencies is None:
            return []
        return list(self.competencies.keys())
        
    def get_competency_data(self, competency_name):
        """Get competency data for a specific competency"""
        competencies = self.competencies
        if competency_name in competencies:
            return competencies[competency_name]
        return {}

    def update_competency_rank(self, competency_name, rank, feedback=None):
        """Update a competency's rank and feedback"""
        try:
            if self._competencies is None:
                self._competencies = {}
            
            existing_status = None
            existing_date = None
            if competency_name in self._competencies:
                existing_status = self._competencies[competency_name].get('certificate_status')
                existing_date = self._competencies[competency_name].get('certificate_date')
            
            self._competencies[competency_name] = {
                'rank': rank,
                'feedback': feedback,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if existing_status:
                self._competencies[competency_name]['certificate_status'] = existing_status
            if existing_date:
                self._competencies[competency_name]['certificate_date'] = existing_date
            
            flag_modified(self, '_competencies')
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error updating competency rank: {str(e)}")
            db.session.rollback()
            return False

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get(id)

    def __repr__(self):
        return f'<Student {self.username}>'

    def update_competency_certificate_status(self, competency_name, status):
        """Update the certificate status for a competency"""
        try:
            if self._competencies is None:
                self._competencies = {}
            
            if competency_name not in self._competencies:
                self._competencies[competency_name] = {
                    'rank': 0,
                    'feedback': '',
                    'updated_at': datetime.utcnow().isoformat()
                }
            
            self._competencies[competency_name]['certificate_status'] = status
            if status == 'approved':
                self._competencies[competency_name]['certificate_date'] = datetime.utcnow().strftime('%Y-%m-%d')
            
            flag_modified(self, '_competencies')
            db.session.add(self)
            db.session.commit()
            print(f"Successfully updated certificate status for {competency_name} to {status}")
            return True
        except Exception as e:
            print(f"Error updating certificate status: {str(e)}")
            db.session.rollback()
            return False

    @property
    def enrolled_workshops(self):
        """Get all workshops the student is enrolled in."""
        from .workshop import Workshop
        return Workshop.query.join(Enrollment).filter(
            Enrollment.student_id == self.id
        ).all()

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
                        competency_name=comp_name,
                        rank=0  
                    )
                    db.session.add(student_comp)
            
            db.session.commit()
            print("Successfully added competencies")
            
        except Exception as e:
            print(f"Error adding competencies: {e}")
            db.session.rollback()
            raise

    def get_json(self):
        data = super().get_json()
        data.update({
            'student_id': self.student_id,
            'competencies': self.competencies,
            'profile_pic': self.profile_pic,
            'resume': self.resume,
            'phone': self.phone,
            'location': self.location,
            'degree': self.degree
        })
        return data

    def add_competency(self, competency_name):
        """Add a single competency to the student with level 1"""
        try:
            if self._competencies is None:
                self._competencies = {}
            
            self._competencies[competency_name] = {
                'level': 1,
                'feedback': '',
                'updated_at': datetime.utcnow().isoformat(),
                'certificate_status': None
            }
            
            flag_modified(self, '_competencies')
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error adding competency: {str(e)}")
            db.session.rollback()
            return False

    def update_competency_level(self, competency_name, level):
        """Update a competency's level"""
        try:
            if self._competencies is None:
                self._competencies = {}
            
            if competency_name not in self._competencies:
                self._competencies[competency_name] = {
                    'level': level,
                    'feedback': '',
                    'updated_at': datetime.utcnow().isoformat(),
                    'certificate_status': None
                }
            else:
                self._competencies[competency_name]['level'] = level
                self._competencies[competency_name]['updated_at'] = datetime.utcnow().isoformat()
            
            flag_modified(self, '_competencies')
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error updating competency level: {str(e)}")
            db.session.rollback()
            return False
