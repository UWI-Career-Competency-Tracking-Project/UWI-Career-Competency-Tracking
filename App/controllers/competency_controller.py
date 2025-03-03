from App.models import Competency, StudentCompetency, Administrator
from App.database import db
from datetime import datetime

def validate_competency(competency_id, validator_id, student_id, tier='Basic'):
    competency = Competency.query.get(competency_id)
    validator = Administrator.query.get(validator_id)
    
    if not competency or not validator:
        return False, "Invalid competency or validator ID"
    
    try:
        existing = StudentCompetency.query.filter_by(
            studentID=student_id,
            competencyID=competency_id
        ).first()
        
        if existing:
            existing.Tiers = tier
            existing.earnedDate = datetime.now()
        else:
            new_student_competency = StudentCompetency(
                studentID=student_id,
                competencyID=competency_id,
                Tiers=tier,
                earnedDate=datetime.now()
            )
            db.session.add(new_student_competency)
            
        db.session.commit()
        return True, "Competency validated successfully"
    except Exception as e:
        db.session.rollback()
        return False, str(e) 