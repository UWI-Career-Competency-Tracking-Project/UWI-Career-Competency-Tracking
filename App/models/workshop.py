from .. import db
from datetime import datetime
from .enrollment import Enrollment
from .competency import Competency, WorkshopCompetency

class Workshop(db.Model):
    __tablename__ = 'workshops'
    
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date)
    time = db.Column(db.String(20))
    instructor = db.Column(db.String(100))
    location = db.Column(db.String(100))
    image_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    enrollments = db.relationship('Enrollment', back_populates='workshop', lazy=True, cascade='all, delete-orphan')
    workshop_competencies = db.relationship('WorkshopCompetency', back_populates='workshop', lazy=True, cascade='all, delete-orphan')

    def __init__(self, workshopID, workshopName, workshopDescription, workshopDate, workshopTime, instructor, location, image_path=None):
        self.id = workshopID
        self.name = workshopName
        self.description = workshopDescription
        self.date = workshopDate
        self.time = workshopTime
        self.instructor = instructor
        self.location = location
        self.image_path = image_path

    @property
    def competencies(self):
        """Get all competencies associated with this workshop."""
        return [wc.competency.name for wc in self.workshop_competencies]

    def add_competencies(self, competency_names):
        """Add competencies to the workshop."""
        if isinstance(competency_names, str):
            competency_names = [competency_names]
        
        try:
            for comp_name in competency_names:
                competency = Competency.query.filter_by(name=comp_name).first()
                if not competency:
                    competency = Competency(name=comp_name)
                    db.session.add(competency)
                
                existing = WorkshopCompetency.query.filter_by(
                    workshop_id=self.id,
                    competency_id=competency.id
                ).first()
                
                if not existing:
                    workshop_comp = WorkshopCompetency(
                        workshop_id=self.id,
                        competency_id=competency.id
                    )
                    db.session.add(workshop_comp)
            
            db.session.commit()
            
        except Exception as e:
            print(f"Error adding competencies to workshop: {e}")
            db.session.rollback()
            raise

    def get_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'time': self.time,
            'instructor': self.instructor,
            'location': self.location,
            'image_path': self.image_path,
            'competencies': self.competencies,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Workshop {self.name}>' 