from App.database import db

class JobCompetency(db.Model):
    __tablename__ = 'job_competencies'
    
    jobCOMPID = db.Column(db.Integer, primary_key=True)
    jobID = db.Column(db.Integer, db.ForeignKey('job_roles.jobID'))
    competencyID = db.Column(db.Integer, db.ForeignKey('competencies.id'))
    requiredRank = db.Column(db.Integer, default=1)  
    
    competency = db.relationship('Competency', backref='job_competencies', lazy=True) 