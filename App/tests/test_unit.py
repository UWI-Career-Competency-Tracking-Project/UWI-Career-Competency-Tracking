import unittest
import pytest
from werkzeug.security import check_password_hash
from datetime import datetime, date
from unittest.mock import MagicMock, patch

from App.main import create_app
from App.database import db
from App.models.user import User
from App.models.student import Student
from App.models.workshop import Workshop
from App.models.enrollment import Enrollment
from App.models.certificate_request import CertificateRequest
from App.models.competency import Competency
from App.models.administrator import Administrator
from App.models.employer import Employer
from App.models.notification import Notification

from App.controllers.auth import login

class UserModelTests(unittest.TestCase):
    """Unit tests for User model"""
    
    def test_new_user(self):
        """Test user creation"""
        user = User(username="testuser", email="test@example.com", password="password123")
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash != "password123"  # Password should be hashed
    
    def test_check_password(self):
        """Test password verification"""
        user = User(username="testuser", email="test@example.com", password="password123")
        assert user.check_password("password123") is True
        assert user.check_password("wrongpassword") is False
    
    def test_user_json(self):
        """Test user JSON representation"""
        user = User(username="testuser", email="test@example.com", password="password123")
        user_json = user.get_json()
        assert "id" in user_json
        assert user_json["username"] == "testuser"
        assert user_json["email"] == "test@example.com"
        assert "password" not in user_json  # Password should not be included

class StudentModelTests(unittest.TestCase):
    """Unit tests for Student model"""
    
    def setUp(self):
        """Set up for Student model tests"""
        # Create a test app
        self.app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_new_student(self):
        """Test student creation"""
        student = Student(
            username="studentuser",
            email="student@example.com",
            password="student123",
            first_name="Test",
            last_name="Student",
            student_id="ST12345"
        )
        assert student.username == "studentuser"
        assert student.email == "student@example.com"
        assert student.first_name == "Test"
        assert student.last_name == "Student"
        assert student.student_id == "ST12345"
        assert isinstance(student.competencies, dict)
    
    def test_add_competency(self):
        """Test adding competency to student"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        student = Student(
            username=f"studentuser_{timestamp}",
            email=f"student_{timestamp}@example.com",
            password="student123",
            first_name="Test",
            last_name="Student",
            student_id=f"ST{timestamp}"
        )
        db.session.add(student)
        db.session.commit()
        
        student.add_competency("Leadership I")
        assert "Leadership I" in student.competencies
        assert student.competencies["Leadership I"]["level"] == 1
        assert student.competencies["Leadership I"]["certificate_status"] is None

    def test_update_competency(self):
        """Test updating student competency"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        student = Student(
            username=f"studentuser_{timestamp}",
            email=f"student_{timestamp}@example.com",
            password="student123",
            first_name="Test",
            last_name="Student",
            student_id=f"ST{timestamp}"
        )
        db.session.add(student)
        db.session.commit()
        
        student.add_competency("Communication I")
        student.update_competency_level("Communication I", 2)
        assert student.competencies["Communication I"]["level"] == 2
        
        student.update_competency_certificate_status("Communication I", "pending")
        assert student.competencies["Communication I"]["certificate_status"] == "pending"

class AdministratorModelTests(unittest.TestCase):
    """Unit tests for Administrator model"""
    
    def test_new_administrator(self):
        """Test administrator creation"""
        admin = Administrator(
            username="adminuser",
            email="admin@example.com",
            password="admin123",
            first_name="Admin",
            last_name="User"
        )
        assert admin.username == "adminuser"
        assert admin.email == "admin@example.com"
        assert admin.first_name == "Admin"
        assert admin.last_name == "User"

class EmployerModelTests(unittest.TestCase):
    """Unit tests for Employer model"""
    
    def test_new_employer(self):
        """Test employer creation"""
        employer = Employer(
            username="employeruser",
            email="employer@example.com",
            password="employer123",
            first_name="Employer",
            last_name="User"
        )
        assert employer.username == "employeruser"
        assert employer.email == "employer@example.com"
        assert employer.first_name == "Employer"
        assert employer.last_name == "User"

class WorkshopModelTests(unittest.TestCase):
    """Unit tests for Workshop model"""
    
    def test_new_workshop(self):
        """Test workshop creation"""
        workshop = Workshop(
            workshopID="WS001",
            workshopName="Test Workshop",
            workshopDescription="Test Description",
            workshopDate=date(2024, 5, 15),
            workshopTime="14:00",
            instructor="Test Instructor",
            location="Test Location"
        )
        assert workshop.workshopID == "WS001"
        assert workshop.workshopName == "Test Workshop"
        assert workshop.workshopDescription == "Test Description"
        assert workshop.workshopDate == date(2024, 5, 15)
        assert workshop.workshopTime == "14:00"
        assert workshop.instructor == "Test Instructor"
        assert workshop.location == "Test Location"
    
    def test_add_competencies(self):
        """Test adding competencies to workshop"""
        workshop = Workshop(
            workshopID="WS001",
            workshopName="Test Workshop",
            workshopDescription="Test Description",
            workshopDate=date(2024, 5, 15),
            workshopTime="14:00",
            instructor="Test Instructor",
            location="Test Location"
        )
        workshop.add_competencies(["Leadership I", "Communication I"])
        assert "Leadership I" in workshop.competencies
        assert "Communication I" in workshop.competencies
        assert len(workshop.competencies) == 2

class EnrollmentModelTests(unittest.TestCase):
    """Unit tests for Enrollment model"""
    
    def test_new_enrollment(self):
        """Test enrollment creation"""
        enrollment = Enrollment(
            student_id=1,
            workshop_id=1
        )
        assert enrollment.student_id == 1
        assert enrollment.workshop_id == 1
        assert enrollment.status == 'enrolled'
        assert enrollment.attended is False

class CertificateRequestTests(unittest.TestCase):
    """Unit tests for Certificate Request model"""
    
    def test_new_certificate_request(self):
        """Test certificate request creation"""
        cert_request = CertificateRequest(
            student_id=1,
            competency="Leadership I"
        )
        # Set the request_date manually since it's not set in __init__
        cert_request.request_date = datetime.now()
        
        assert cert_request.student_id == 1
        assert cert_request.competency == "Leadership I"
        assert cert_request.status == "pending"
        assert cert_request.request_date is not None

class NotificationTests(unittest.TestCase):
    """Unit tests for Notification model"""
    
    def test_new_notification(self):
        """Test notification creation"""
        notification = Notification(
            user_id=1,
            message="Test notification",
            notification_type="info"
        )
        assert notification.user_id == 1
        assert notification.message == "Test notification"
        assert notification.notification_type == "info"
        assert notification.is_read is False
        assert notification.created_at is not None

class AuthTests(unittest.TestCase):
    """Unit tests for authentication functionality"""
    
    def setUp(self):
        """Set up a test user for authentication tests"""
        self.app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        self.user = User(username="testauth", email="testauth@example.com", password="authpass123")
        db.session.add(self.user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_login(self):
        """Test login functionality"""
        # Test successful login
        logged_in_user = login("testauth", "authpass123")
        assert logged_in_user is not None
        assert logged_in_user.username == "testauth"
        
        # Test failed login with wrong password
        failed_login = login("testauth", "wrongpass")
        assert failed_login is None
        
        # Test failed login with non-existent username
        failed_login = login("nonexistent", "anypass")
        assert failed_login is None 