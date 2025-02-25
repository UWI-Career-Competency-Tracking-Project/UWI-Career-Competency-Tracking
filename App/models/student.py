from .user import User
from App.database import db
from datetime import datetime

class Student(User):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    registration_date = db.Column(db.Date, default=datetime.utcnow)
    student_username = db.Column(db.String(80))
    region = db.Column(db.String(100))
    
    __mapper_args__ = {
        'polymorphic_identity': 'student'
    }

    def get_json(self):
        data = super().get_json()
        data.update({
            'registration_date': self.registration_date.strftime('%Y-%m-%d')
        })
        return data
