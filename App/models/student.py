from App.database import db
from models.user import User 

class Student(User):
    __tablename__ = "students"

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }

    def get_json(self):
        data = super().get_json()
        data.update({
            'registration_date': self.registration_date.strftime('%Y-%m-%d')
        })
        return data
