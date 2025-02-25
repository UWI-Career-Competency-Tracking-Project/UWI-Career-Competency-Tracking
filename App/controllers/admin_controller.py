from App.models import Administrator, Student, Badge, Workshop, Competency, Feedback
from App.database import db
from datetime import datetime

def disperse_certificate(admin_id, student_id, certificate_data):
    admin = Administrator.query.get(admin_id)
    student = Student.query.get(student_id)
    if not admin or not student:
        return False, "Invalid admin or student ID"
    
    try:
        new_badge = Badge(
            badgeName=certificate_data['name'],
            issueDate=datetime.now().strftime('%Y-%m-%d'),
            competencyID=certificate_data['competency_id']
        )
        db.session.add(new_badge)
        db.session.commit()
        return True, "Certificate dispersed successfully"
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def manage_workshop(admin_id, workshop_data):
    admin = Administrator.query.get(admin_id)
    if not admin:
        return False, "Invalid admin ID"
    
    try:
        new_workshop = Workshop(
            workshopID=workshop_data['workshop_id'],
            workshopName=workshop_data['name'],
            workshopDescription=workshop_data['description'],
            workshopDate=datetime.strptime(workshop_data['date'], '%Y-%m-%d').date(),
            workshopTime=datetime.strptime(workshop_data['time'], '%H:%M').time(),
            instructor=workshop_data['instructor'],
            location=workshop_data['location']
        )
        db.session.add(new_workshop)
        db.session.commit()
        return True, "Workshop created successfully"
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def manage_competency(admin_id, competency_data):
    admin = Administrator.query.get(admin_id)
    if not admin:
        return False, "Invalid admin ID"
    
    try:
        new_competency = Competency(
            competencyName=competency_data['name'],
            competencyDescription=competency_data['description']
        )
        db.session.add(new_competency)
        db.session.commit()
        return True, "Competency created successfully"
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def validate_student_competency(admin_id, student_id, competency_id):
    admin = Administrator.query.get(admin_id)
    student = Student.query.get(student_id)
    competency = Competency.query.get(competency_id)
    
    if not all([admin, student, competency]):
        return False, "Invalid admin, student, or competency ID"
    
    try:
        return True, "Competency validated successfully"
    except Exception as e:
        return False, str(e)

def give_feedback(admin_id, student_id, feedback_data):
    admin = Administrator.query.get(admin_id)
    student = Student.query.get(student_id)
    
    if not admin or not student:
        return False, "Invalid admin or student ID"
    
    try:
        new_feedback = Feedback(
            feedbackComment=feedback_data['comment'],
            feedbackRating=feedback_data['rating'],
            studentID=student_id,
            employerID=admin_id
        )
        db.session.add(new_feedback)
        db.session.commit()
        return True, "Feedback submitted successfully"
    except Exception as e:
        db.session.rollback()
        return False, str(e) 