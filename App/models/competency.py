from App.database import db
from datetime import datetime

class Competency(db.Model):
    __tablename__ = 'competencies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    level = db.Column(db.Integer, default=1)  # 1 = Level I, 2 = Level II, 3 = Level III
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student_competencies = db.relationship('StudentCompetency', back_populates='competency', lazy=True, cascade='all, delete-orphan')

    def __init__(self, name, description=None, level=1):
        self.name = name
        self.description = description
        self.level = level

    def get_level_display(self):
        """Returns a display representation of the competency with level"""
        if self.level > 1:
            return f"{self.name} {self.get_roman_level()}"
        return self.name
    
    def get_roman_level(self):
        """Convert level to Roman numerals"""
        romans = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
        return romans.get(self.level, str(self.level))

    def __repr__(self):
        return f'<Competency {self.name} Level {self.level}>' 