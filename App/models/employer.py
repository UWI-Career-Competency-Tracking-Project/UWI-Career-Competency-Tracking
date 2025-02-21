from App.database import db
from .user import User 

class Employer(User):
    __tablename__ = "employers"

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'employer',
    }

    def get_json(self):
        return super().get_json()
