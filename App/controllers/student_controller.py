from App.models import Student, Workshop, Competency, StudentCompetency
from App.database import db
from datetime import datetime

def register_for_workshop(student_id, workshop_id):
    student = Student.query.get(student_id)
    workshop = Workshop.query.get(workshop_id)
    
    if not student or not workshop:
        return False, "Invalid student or workshop ID"
    
    try:
        return True, "Successfully registered for workshop"
    except Exception as e:
        return False, str(e)

def view_competencies(student_id):
    student = Student.query.get(student_id)
    if not student:
        return False, "Invalid student ID"
    
    try:
        student_competencies = StudentCompetency.query.filter_by(studentID=student_id).all()
        competencies_list = []
        
        for sc in student_competencies:
            competency = Competency.query.get(sc.competencyID)
            competencies_list.append({
                'competency_name': competency.competencyName,
                'tier': sc.Tiers,
                'earned_date': sc.earnedDate.strftime('%Y-%m-%d')
            })
            
        return True, competencies_list
    except Exception as e:
        return False, str(e)

def view_progress(student_id):
    student = Student.query.get(student_id)
    if not student:
        return False, "Invalid student ID"
    
    try:
        total_competencies = Competency.query.count()
        earned_competencies = StudentCompetency.query.filter_by(studentID=student_id).count()
        
        progress = {
            'total_competencies': total_competencies,
            'earned_competencies': earned_competencies,
            'progress_percentage': (earned_competencies / total_competencies * 100) if total_competencies > 0 else 0
        }
        
        return True, progress
    except Exception as e:
        return False, str(e) 