from App.database import db
from datetime import datetime

class JobRole(db.Model):
    __tablename__ = 'job_roles'
    
    jobID = db.Column(db.Integer, primary_key=True)
    jobTitle = db.Column(db.String(100), nullable=False)
    jobDescription = db.Column(db.String(500))
    requiredRank = db.Column(db.Integer, default=1)  
    dateAdded = db.Column(db.DateTime, default=datetime.utcnow)
    isActive = db.Column(db.Boolean, default=True)
    
    competencies = db.relationship('JobCompetency', backref='job_role', lazy=True, cascade='all, delete-orphan')
    
    def get_required_competencies(self):
        """Get list of competency names and required ranks for this job"""
        return [(jc.competency.name, jc.requiredRank) for jc in self.competencies if jc.competency]
    
    def calculate_match_score(self, student_competencies):
        """Calculate how well a student's competencies match this job's requirements"""
        if not student_competencies:
            return 0
            
        total_matches = 0
        required_competencies = self.get_required_competencies()
        
        for comp_name, required_rank in required_competencies:
            if comp_name in student_competencies:
                student_rank = student_competencies[comp_name].get('rank', 0)
                if student_rank >= required_rank:
                    total_matches += 1
        
        if not required_competencies:
            return 0
            
        return (total_matches / len(required_competencies)) * 100
    
    @staticmethod
    def get_matching_jobs(student):
        """Get all jobs with their match scores for a student"""
        all_jobs = JobRole.query.filter_by(isActive=True).all()
        job_matches = []
        
        for job in all_jobs:
            match_score = job.calculate_match_score(student.competencies)
            if match_score > 0:  # Only include jobs with some match
                job_matches.append({
                    'job': job,
                    'score': match_score,
                    'matching_competencies': [
                        comp for comp, rank in job.get_required_competencies()
                        if comp in student.competencies and 
                        student.competencies[comp].get('rank', 0) >= rank
                    ]
                })
        
        # Sort by match score, highest first
        return sorted(job_matches, key=lambda x: x['score'], reverse=True) 