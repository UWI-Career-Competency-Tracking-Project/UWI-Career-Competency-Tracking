from App.models import Badge, Student, Competency
from App.database import db
from datetime import datetime
import os
from PIL import Image, ImageDraw, ImageFont

def generate_certificate(badge_id, student_id):
    badge = Badge.query.get(badge_id)
    student = Student.query.get(student_id)
    
    if not badge or not student:
        return False, "Invalid badge or student ID"
    
    try:
        certificate_data = {
            'student_name': f"{student.first_name} {student.last_name}",
            'badge_name': badge.badgeName,
            'issue_date': datetime.now().strftime('%Y-%m-%d'),
            'competency': Competency.query.get(badge.competencyID).competencyName
        }
        
        return True, certificate_data
    except Exception as e:
        return False, str(e) 