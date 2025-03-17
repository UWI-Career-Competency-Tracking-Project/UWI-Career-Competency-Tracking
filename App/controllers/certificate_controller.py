from ..models.certificate_request import CertificateRequest
from ..models.student import Student
from .. import db
from datetime import datetime

def request_certificate(student_id, competency):
    """Create a new certificate request"""
    try:
        existing_request = CertificateRequest.query.filter_by(
            student_id=student_id,
            competency=competency,
            status='pending'
        ).first()
        
        if existing_request:
            return False, 'A request for this competency is already pending.'
        
        new_request = CertificateRequest(
            student_id=student_id,
            competency=competency
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        return True, 'Certificate request submitted successfully.'
        
    except Exception as e:
        print(f"Error creating certificate request: {str(e)}")
        db.session.rollback()
        return False, 'An error occurred while processing your request.'

def get_pending_requests():
    """Get all pending certificate requests"""
    try:
        return CertificateRequest.query.filter_by(status='pending').all()
    except Exception as e:
        print(f"Error getting pending requests: {str(e)}")
        return []

def process_request(request_id, action):
    """Process a certificate request (approve/deny)"""
    try:
        request = CertificateRequest.query.get(request_id)
        if not request:
            return False, 'Request not found.'
            
        if action not in ['approve', 'deny']:
            return False, 'Invalid action.'
            
        request.status = action + 'd'  
        
        if action == 'approve':
            student = Student.query.get(request.student_id)
            if student:
                student.update_competency_certificate_status(request.competency, 'approved')
        
        db.session.commit()
        return True, f'Certificate request {action}d successfully.'
        
    except Exception as e:
        print(f"Error processing certificate request: {str(e)}")
        db.session.rollback()
        return False, 'An error occurred while processing the request.'

def get_certificate_data(student_id, competency):
    """Get certificate data for viewing"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return None
            
        comp_data = student.competencies.get(competency)
        if not comp_data or comp_data.get('certificate_status') != 'approved':
            return None
            
        return {
            'student_name': f"{student.first_name} {student.last_name}",
            'competency': competency,
            'issue_date': comp_data.get('certificate_date'),
            'student_id': student.student_id
        }
        
    except Exception as e:
        print(f"Error getting certificate data: {str(e)}")
        return None 