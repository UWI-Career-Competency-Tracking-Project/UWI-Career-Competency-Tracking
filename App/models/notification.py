from App.database import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    user_id = db.Column(db.Integer)  
    user_type = db.Column(db.String(20))  
    related_id = db.Column(db.Integer)  
    message = db.Column(db.String(500), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(200)) 
    
    student = db.relationship('Student', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))
    
    def __init__(self, message, notification_type, student_id=None, user_id=None, user_type=None, 
                 related_id=None, link=None, created_at=None, is_read=False):
        self.student_id = student_id
        self.user_id = user_id
        self.user_type = user_type
        self.related_id = related_id
        self.message = message
        self.notification_type = notification_type
        self.link = link
        self.created_at = created_at if created_at else datetime.utcnow()
        self.is_read = is_read
    
    def mark_as_read(self):
        self.is_read = True
        db.session.add(self)
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'user_id': self.user_id,
            'user_type': self.user_type,
            'related_id': self.related_id,
            'message': self.message,
            'notification_type': self.notification_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_read': self.is_read,
            'link': self.link
        } 