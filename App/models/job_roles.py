from App.database import db

class JobRole(db.Model):
    __tablename__ = 'job_roles'
    
    jobID = db.Column(db.Integer, primary_key=True)
    jobTitle = db.Column(db.String(100), nullable=False)
    jobDescription = db.Column(db.String(500)) 