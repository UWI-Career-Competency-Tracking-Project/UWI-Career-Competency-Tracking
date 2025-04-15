import unittest
import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch

from App.main import create_app
from App.database import db
from App.models.user import User
from App.models.student import Student
from App.models.workshop import Workshop
from App.models.enrollment import Enrollment
from App.models.certificate_request import CertificateRequest
from App.models.administrator import Administrator
from App.models.employer import Employer
from App.models.notification import Notification
from App.models.competency import Competency
from App.models.job_competency import JobCompetency

from App.controllers.auth import login
from App.controllers.certificate_controller import (
    request_certificate, 
    get_pending_requests, 
    process_competency_request,
    get_certificate_data
)
from App.controllers.notification_controller import create_notification, get_notifications

# This fixture creates an empty database for the test and deletes it after the test
@pytest.fixture(autouse=True, scope="function")
def empty_db():
    # Use in-memory database for testing
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Initialize database with base tables if needed
        from App.models.competency import Competency
        from App.models.job_competency import JobCompetency
        
        # Push app context so controllers can work properly
        ctx = app.app_context()
        ctx.push()
        
        # Return test client for tests that need it
        yield app.test_client()
        
        # Clean up
        ctx.pop()
        db.session.remove()
        db.drop_all()

@pytest.mark.usefixtures("empty_db")
class UserRegistrationIntegrationTests(unittest.TestCase):
    """Integration tests for user registration flow"""
    
    def test_student_registration(self):
        """Test student registration by creating directly in the database"""
        # Create student directly
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        student = Student(
            username=f"teststudent_{timestamp}",
            email=f"teststudent_{timestamp}@example.com",
            password="student123",
            first_name="Test",
            last_name="Student",
            student_id=f"ST{timestamp}"
        )
        db.session.add(student)
        db.session.commit()
        
        # Verify student was created
        retrieved_student = Student.query.filter_by(student_id=f"ST{timestamp}").first()
        assert retrieved_student is not None
        assert retrieved_student.username == f"teststudent_{timestamp}"
        assert retrieved_student.email == f"teststudent_{timestamp}@example.com"
    
    def test_admin_registration(self):
        """Test admin registration by creating directly in the database"""
        # Create admin directly
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        admin = Administrator(
            username=f"testadmin_{timestamp}",
            email=f"testadmin_{timestamp}@example.com",
            password="admin123",
            first_name="Test",
            last_name="Admin"
        )
        db.session.add(admin)
        db.session.commit()
        
        # Verify admin was created
        retrieved_admin = Administrator.query.filter_by(username=f"testadmin_{timestamp}").first()
        assert retrieved_admin is not None
        assert retrieved_admin.username == f"testadmin_{timestamp}"
        assert retrieved_admin.email == f"testadmin_{timestamp}@example.com"
    
    def test_employer_registration(self):
        """Test employer registration by creating directly in the database"""
        # Create employer directly
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        employer = Employer(
            username=f"testemployer_{timestamp}",
            email=f"testemployer_{timestamp}@example.com",
            password="employer123",
            first_name="Test",
            last_name="Employer"
        )
        db.session.add(employer)
        db.session.commit()
        
        # Verify employer was created
        retrieved_employer = Employer.query.filter_by(username=f"testemployer_{timestamp}").first()
        assert retrieved_employer is not None
        assert retrieved_employer.username == f"testemployer_{timestamp}"
        assert retrieved_employer.email == f"testemployer_{timestamp}@example.com"
    
    def test_login(self):
        """Test user login functionality"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user = User(
            username=f"logintest_{timestamp}",
            email=f"login_{timestamp}@example.com",
            password="loginpass123"
        )
        db.session.add(user)
        db.session.commit()
        
        # Test login with correct credentials
        logged_in_user = login(f"logintest_{timestamp}", "loginpass123")
        assert logged_in_user is not None
        assert logged_in_user.username == f"logintest_{timestamp}"
        
        # Test login with incorrect credentials
        failed_login = login(f"logintest_{timestamp}", "wrongpassword")
        assert failed_login is None

@pytest.mark.usefixtures("empty_db")
class WorkshopEnrollmentIntegrationTests(unittest.TestCase):
    """Integration tests for workshop enrollment flow"""
    
    def setUp(self):
        # Create a student
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.student = Student(
            username=f"enrollstudent_{timestamp}",
            email=f"enroll_{timestamp}@example.com",
            password="enroll123",
            first_name="Enroll",
            last_name="Student",
            student_id=f"EN{timestamp}"
        )
        
        # Create a workshop
        self.workshop = Workshop(
            workshopID=f"WS{timestamp}",
            workshopName="Test Workshop",
            workshopDescription="Test Description",
            workshopDate=date(2024, 5, 15),
            workshopTime="14:00",
            instructor="Test Instructor",
            location="Test Location"
        )
        
        db.session.add(self.student)
        db.session.add(self.workshop)
        db.session.commit()
        
        # Add competencies after commit to ensure workshop has an ID
        self.workshop.add_competencies(["Leadership I", "Communication I"])
        db.session.commit()
    
    def test_workshop_enrollment(self):
        """Test student enrollment in workshop"""
        # Enroll student in workshop
        enrollment = Enrollment(
            student_id=self.student.id,
            workshop_id=self.workshop.id
        )
        db.session.add(enrollment)
        db.session.commit()
        
        # Verify enrollment was created
        retrieved_enrollment = Enrollment.query.filter_by(
            student_id=self.student.id,
            workshop_id=self.workshop.id
        ).first()
        
        assert retrieved_enrollment is not None
        assert retrieved_enrollment.student_id == self.student.id
        assert retrieved_enrollment.workshop_id == self.workshop.id
        assert retrieved_enrollment.attended is False
        
    def test_competency_tracking(self):
        """Test competency tracking after workshop enrollment"""
        # Enroll student in workshop
        enrollment = Enrollment(
            student_id=self.student.id,
            workshop_id=self.workshop.id
        )
        # Mark as attended
        enrollment.mark_attended()
        
        db.session.add(enrollment)
        db.session.commit()
        
        # Add competencies to student based on workshop
        for competency_name in self.workshop.get_competency_names():
            self.student.add_competency(competency_name)
        
        db.session.commit()
        
        # Verify student has the competencies
        student = Student.query.get(self.student.id)
        competency_names = student.get_competency_names()
        assert "Leadership I" in competency_names
        assert "Communication I" in competency_names

@pytest.mark.usefixtures("empty_db")
class CertificateRequestIntegrationTests(unittest.TestCase):
    """Integration tests for certificate request flow"""
    
    def setUp(self):
        # Create a student
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.student = Student(
            username=f"certstudent_{timestamp}",
            email=f"cert_{timestamp}@example.com",
            password="cert123",
            first_name="Cert",
            last_name="Student",
            student_id=f"CT{timestamp}"
        )
        
        # Add a competency to the student
        db.session.add(self.student)
        db.session.commit()
        
        self.student.add_competency("Leadership I")
        self.student.add_competency("Communication I")
        db.session.commit()
        
        # Create an admin
        self.admin = Administrator(
            username=f"certadmin_{timestamp}",
            email=f"certadmin_{timestamp}@example.com",
            password="admin123",
            first_name="Cert",
            last_name="Admin"
        )
        
        db.session.add(self.admin)
        db.session.commit()
    
    def test_certificate_request_flow(self):
        """Test certificate request and approval flow"""
        # Student requests a certificate
        success, message = request_certificate(self.student.id, "Leadership I")
        assert success is True
        assert "submitted successfully" in message
        
        # Check that the request was created
        pending_requests = get_pending_requests()
        assert len(pending_requests) > 0
        
        # Find the certificate request
        cert_request = CertificateRequest.query.filter_by(
            student_id=self.student.id,
            competency="Leadership I"
        ).first()
        
        assert cert_request is not None
        assert cert_request.status == "pending"
        
        # Admin approves the certificate
        success, message = process_competency_request(cert_request.id, "approve")
        assert success is True
        assert "approved successfully" in message
        
        # Verify certificate status was updated
        updated_student = Student.query.get(self.student.id)
        competency_data = updated_student.get_competency_data("Leadership I")
        assert competency_data.get("certificate_status") == "approved"
        
        # Get certificate data
        cert_data = get_certificate_data(self.student.id, "Leadership I")
        assert cert_data is not None
        assert cert_data["student_name"] == "Cert Student"
        assert cert_data["competency"] == "Leadership I"
    
    def test_duplicate_certificate_request(self):
        """Test duplicate certificate request handling"""
        # Submit first request
        success, message = request_certificate(self.student.id, "Communication I")
        assert success is True
        
        # Submit duplicate request
        success, message = request_certificate(self.student.id, "Communication I")
        assert success is False
        assert "already pending" in message

@pytest.mark.usefixtures("empty_db")
class NotificationIntegrationTests(unittest.TestCase):
    """Integration tests for notification system"""
    
    def setUp(self):
        # Create a student
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.student = Student(
            username=f"notifystudent_{timestamp}",
            email=f"notify_{timestamp}@example.com",
            password="notify123",
            first_name="Notify",
            last_name="Student",
            student_id=f"NT{timestamp}"
        )
        db.session.add(self.student)
        db.session.commit()
    
    def test_notification_creation_and_retrieval(self):
        """Test creating and retrieving notifications"""
        # Create a notification
        notification = create_notification(
            student_id=self.student.id,
            message="Test notification message",
            notification_type="info"
        )
        
        assert notification is not None
        assert notification.student_id == self.student.id
        assert notification.message == "Test notification message" 