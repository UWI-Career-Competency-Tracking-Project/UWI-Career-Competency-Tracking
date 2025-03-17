from .. import db
from datetime import datetime

class CertificateRequest(db.Model):
    __tablename__ = 'certificate_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    competency = db.Column(db.String(100), nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  
    
    student = db.relationship('Student', backref=db.backref('certificate_requests', lazy=True))
    
    def __init__(self, student_id, competency):
        self.student_id = student_id
        self.competency = competency
        
    def __repr__(self):
        return f'<CertificateRequest {self.student_id} - {self.competency}>'

    def approve(self):
        self.status = 'approved'
        self.response_date = datetime.utcnow()
    
    def deny(self):
        self.status = 'denied'
        self.response_date = datetime.utcnow() 