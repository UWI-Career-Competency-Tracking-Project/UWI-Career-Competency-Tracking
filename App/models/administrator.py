from App.database import db
from .user import User
from flask_login import UserMixin

class Administrator(User, UserMixin):
    __tablename__ = "administrators"

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    department = db.Column(db.String(100))

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def get_json(self):
        return super().get_json()
