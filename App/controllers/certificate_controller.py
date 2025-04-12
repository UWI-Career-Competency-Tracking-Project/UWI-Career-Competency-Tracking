from ..models.certificate_request import CertificateRequest
from ..models.student import Student
from .. import db
from ..models.enrollment import Enrollment
from ..models.workshop import Workshop
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
        
        student = Student.query.get(student_id)
        if student and student.competencies.get(competency, {}).get('certificate_status') == 'denied':
            print(f"Resubmitting previously denied certificate request for {competency}")
            
        new_request = CertificateRequest(
            student_id=student_id,
            competency=competency
        )
        
        if student:
            student.update_competency_certificate_status(competency, 'pending')
        
        db.session.add(new_request)
        db.session.commit()
        
        return True, 'Certificate request submitted successfully.'
        
    except Exception as e:
        print(f"Error creating certificate request: {str(e)}")
        db.session.rollback()
        return False, 'An error occurred while processing your request.'

def get_pending_requests():
    """
    Get all pending certificate requests (both workshop and competency)
    """
    try:
        pending_workshop_requests = Enrollment.query.filter_by(certificate_status='pending').all()
        
        pending_competency_requests = CertificateRequest.query.filter_by(status='pending').all()
        
        formatted_requests = []
        
        for req in pending_workshop_requests:
            student = Student.query.get(req.student_id)
            workshop = Workshop.query.get(req.workshop_id)
            
            if student and workshop:
                formatted_requests.append({
                    'id': req.id,
                    'type': 'workshop',
                    'student': student,
                    'workshop': workshop,
                    'competency': ', '.join(workshop.competencies) if workshop.competencies else 'No competencies',
                    'request_date': req.created_at or datetime.now()
                })
        
        for req in pending_competency_requests:
            student = Student.query.get(req.student_id)
            
            if student:
                formatted_requests.append({
                    'id': req.id,
                    'type': 'competency',
                    'student': student,
                    'competency': req.competency,
                    'request_date': req.request_date
                })
        
        formatted_requests.sort(key=lambda x: x['request_date'], reverse=True)
        
        return formatted_requests
    except Exception as e:
        print(f"Error getting pending certificate requests: {e}")
        return []

def process_request(request_id, action):
    """
    Process a certificate request - either approve or deny
    """
    try:
        enrollment = Enrollment.query.get(request_id)
        
        if not enrollment:
            return False, "Certificate request not found."
        
        if action == 'approve':
            enrollment.certificate_status = 'approved'
            message = "Certificate request approved successfully."
        elif action == 'deny':
            enrollment.certificate_status = 'rejected'
            message = "Certificate request denied."
        else:
            return False, "Invalid action."
        
        db.session.commit()
        return True, message
    except Exception as e:
        print(f"Error processing certificate request: {e}")
        db.session.rollback()
        return False, f"Error processing request: {str(e)}"

def get_certificate_data(student_id, competency):
    """Get certificate data for viewing"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return None
            
        comp_data = student.competencies.get(competency)
        if not comp_data or comp_data.get('certificate_status') != 'approved':
            return None
        
        certificate_date = comp_data.get('certificate_date')
        if not certificate_date:
            certificate_date = datetime.now().strftime('%B %d, %Y')
            
        return {
            'student_name': f"{student.first_name} {student.last_name}",
            'competency': competency,
            'date': certificate_date,
            'student_id': student.student_id
        }
        
    except Exception as e:
        print(f"Error getting certificate data: {str(e)}")
        return None

def process_competency_request(request_id, action):
    """
    Process a competency certificate request 
    """
    try:
        certificate_request = CertificateRequest.query.get(request_id)
        
        if not certificate_request:
            return False, "Certificate request not found."
        
        # Get the student and update the competency
        student = Student.query.get(certificate_request.student_id)
        if not student:
            return False, "Student not found."
        
        competency = certificate_request.competency
        
        if action == 'approve':
            certificate_request.status = 'approved'
            certificate_request.approve()
            student.update_competency_certificate_status(competency, 'approved')
            message = "Certificate request approved successfully."
        elif action == 'deny':
            certificate_request.status = 'rejected'
            certificate_request.deny()
            student.update_competency_certificate_status(competency, 'rejected')
            message = "Certificate request denied."
        else:
            return False, "Invalid action."
        
        db.session.commit()
        return True, message
    except Exception as e:
        print(f"Error processing competency certificate request: {e}")
        db.session.rollback()
        return False, f"Error processing request: {str(e)}" 