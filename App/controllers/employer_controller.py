from App.models import Employer, Student, Feedback, JobRole, JobCompetency, StudentCompetency
from App.database import db
from datetime import datetime

def search_candidates(employer_id, criteria):
    employer = Employer.query.get(employer_id)
    if not employer:
        return False, "Invalid employer ID"
    
    try:
        job_role = JobRole.query.filter_by(jobTitle=criteria['job_title']).first()
        if not job_role:
            return False, "Job role not found"
            
        job_competencies = JobCompetency.query.filter_by(jobID=job_role.jobID).all()
        competency_ids = [jc.competencyID for jc in job_competencies]
        
        matching_students = Student.query.join(StudentCompetency).filter(
            StudentCompetency.competencyID.in_(competency_ids)
        ).distinct().all()
        
        return True, [student.get_json() for student in matching_students]
    except Exception as e:
        return False, str(e)

def provide_feedback(employer_id, student_id, feedback_data):
    employer = Employer.query.get(employer_id)
    student = Student.query.get(student_id)
    
    if not employer or not student:
        return False, "Invalid employer or student ID"
    
    try:
        new_feedback = Feedback(
            feedbackComment=feedback_data['comment'],
            feedbackRating=feedback_data['rating'],
            studentID=student_id,
            employerID=employer_id,
            feedbackDate=datetime.now()
        )
        db.session.add(new_feedback)
        db.session.commit()
        return True, "Feedback submitted successfully"
    except Exception as e:
        db.session.rollback()
        return False, str(e) 