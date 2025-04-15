from .. import db
from datetime import datetime
from .enrollment import Enrollment
from sqlalchemy.orm.attributes import flag_modified

class Workshop(db.Model):
    __tablename__ = 'workshops'
    
    id = db.Column(db.Integer, primary_key=True)
    workshopID = db.Column(db.String(20), unique=True)
    workshopName = db.Column(db.String(100))
    workshopDescription = db.Column(db.Text)
    workshopDate = db.Column(db.Date)
    workshopTime = db.Column(db.String(20))
    instructor = db.Column(db.String(100))
    location = db.Column(db.String(100))
    image_path = db.Column(db.String(255), nullable=True)
    _competencies = db.Column('competencies', db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attendance_count = db.Column(db.Integer, default=0)

    enrollments = db.relationship('Enrollment', back_populates='workshop', lazy=True, cascade='all, delete-orphan')

    def __init__(self, workshopID, workshopName, workshopDescription, workshopDate, workshopTime, instructor, location, image_path=None, competencies=None, created_at=None):
        self.workshopID = workshopID
        self.workshopName = workshopName
        self.workshopDescription = workshopDescription
        self.workshopDate = workshopDate
        self.workshopTime = workshopTime
        self.instructor = instructor
        self.location = location
        self.image_path = image_path
        self._competencies = competencies if competencies is not None else []
        self.created_at = created_at if created_at is not None else datetime.utcnow()

    @property
    def competencies(self):
        """Get list of competency names for this workshop"""
        try:
            if self._competencies is None:
                self._competencies = []
                flag_modified(self, '_competencies')
                db.session.add(self)
                db.session.commit()
            return self._competencies if isinstance(self._competencies, list) else []
        except Exception as e:
            print(f"Error accessing competencies: {str(e)}")
            return []

    def get_competency_names(self):
        """Get list of competency names from the workshop"""
        return self.competencies

    @competencies.setter
    def competencies(self, value):
        """Set the competencies list directly"""
        if value is None:
            self._competencies = []
        else:
            self._competencies = value
        flag_modified(self, '_competencies')

    def add_competencies(self, competency_names):
        """Add competencies to the workshop"""
        try:
            if isinstance(competency_names, str):
                competency_names = [competency_names]
                
            if self._competencies is None:
                self._competencies = []
            
            if not isinstance(self._competencies, list):
                self._competencies = []
            
            for name in competency_names:
                if name and name not in self._competencies:
                    self._competencies.append(name)
            
            flag_modified(self, '_competencies')
            db.session.add(self)
            
            return True
        except Exception as e:
            print(f"Error adding competencies: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_json(self):
        try:
            return {
                'id': self.workshopID,
                'name': self.workshopName,
                'description': self.workshopDescription,
                'date': self.workshopDate.strftime('%Y-%m-%d') if self.workshopDate else None,
                'time': self.workshopTime,
                'instructor': self.instructor,
                'location': self.location,
                'image_path': self.image_path,
                'competencies': self.competencies,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
        except Exception as e:
            print(f"Error serializing workshop: {str(e)}")
            return {}

    def __repr__(self):
        return f'<Workshop {self.workshopName}>' 