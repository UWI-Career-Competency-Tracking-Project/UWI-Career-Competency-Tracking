from App.database import db
from models.user import User 

class Administrator(User):
    __tablename__ = "administrators"

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

    def get_json(self):
        return super().get_json()
