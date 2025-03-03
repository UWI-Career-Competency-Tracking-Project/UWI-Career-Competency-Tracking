from .. import db
from .user import User

class Administrator(User):
    __tablename__ = 'administrators'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

    def __init__(self, username, password, email, first_name=None, last_name=None):
        super().__init__(username=username, password=password, email=email, 
                        first_name=first_name, last_name=last_name, user_type='admin')

    def __repr__(self):
        return f'<Administrator {self.username}>'

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
