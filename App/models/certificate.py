from App.database import db
from datetime import datetime

class Certificate(db.Model):
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    competency_name = db.Column(db.String(100), nullable=False)
    date_issued = db.Column(db.DateTime, default=datetime.utcnow)
    certificate_number = db.Column(db.String(50), unique=True)
    
    student = db.relationship('Student', backref=db.backref('certificates', lazy=True))
    
    def __init__(self, student_id, competency_name, certificate_number=None):
        self.student_id = student_id
        self.competency_name = competency_name
        self.certificate_number = certificate_number or f"CERT-{datetime.now().strftime('%Y%m%d')}-{student_id}"
        
    def __repr__(self):
        return f'<Certificate {self.certificate_number} - {self.competency_name}>' 