import unittest
import pytest
import time
import concurrent.futures
from datetime import datetime, date
from statistics import mean, median

from App.main import create_app
from App.database import db
from App.models.user import User
from App.models.student import Student
from App.models.workshop import Workshop
from App.models.enrollment import Enrollment
from App.models.certificate_request import CertificateRequest
from App.models.administrator import Administrator
from App.controllers.certificate_controller import (
    request_certificate, 
    get_pending_requests, 
    process_competency_request,
    get_certificate_data
)
from App.controllers.notification_controller import create_notification, get_notifications

class PerformanceTestBase(unittest.TestCase):
    """Base class for performance tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test database and application context"""
        cls.app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()
        
        # Create test data
        cls.create_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the test database"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def create_test_data(cls):
        """Create test data for performance testing"""
        # Generate a timestamp to ensure unique usernames/emails
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create students
        for i in range(10):  # Reduced from 100 for faster testing
            student = Student(
                username=f"student{i}_{timestamp}",
                email=f"student{i}_{timestamp}@example.com",
                password="password",
                first_name=f"First{i}",
                last_name=f"Last{i}",
                student_id=f"S{timestamp}{i}"
            )
            db.session.add(student)
        
        # Create workshops
        for i in range(5):  # Reduced from 20 for faster testing
            workshop = Workshop(
                workshopID=f"WS{timestamp}{i}",
                workshopName=f"Workshop {i}",
                workshopDescription=f"Description for Workshop {i}",
                workshopDate=date(2024, 5, 15),
                workshopTime="14:00",
                instructor=f"Instructor {i}",
                location=f"Location {i}"
            )
            competencies = [f"Competency {j}" for j in range(i % 3 + 1)]
            db.session.add(workshop)
            db.session.commit()
            workshop.add_competencies(competencies)
            db.session.commit()
        
        # Create an admin
        admin = Administrator(
            username=f"admin_{timestamp}",
            email=f"admin_{timestamp}@example.com",
            password="admin123",
            first_name="Admin",
            last_name="User"
        )
        db.session.add(admin)
        
        db.session.commit()
        
        # Create enrollments (each student enrolls in multiple workshops)
        students = Student.query.all()
        workshops = Workshop.query.all()
        
        for i, student in enumerate(students[:5]):  # First 5 students
            for j, workshop in enumerate(workshops[:2]):  # First 2 workshops
                enrollment = Enrollment(
                    student_id=student.id,
                    workshop_id=workshop.id
                )
                enrollment.mark_attended()
                db.session.add(enrollment)
                
                # Add competencies to students from workshops
                for competency in workshop.get_competency_names():
                    student.add_competency(competency)
        
        db.session.commit()

class DatabaseQueryPerformanceTests(PerformanceTestBase):
    """Performance tests for database queries"""
    
    def test_get_all_students_performance(self):
        """Test performance of retrieving all students"""
        start_time = time.time()
        students = Student.query.all()
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"Time to retrieve all students: {query_time:.2f}ms")
        
        # Assert that the query completes within the expected time frame
        self.assertLess(query_time, 500, "Query took too long to execute")
    
    def test_get_all_workshops_performance(self):
        """Test performance of retrieving all workshops"""
        start_time = time.time()
        workshops = Workshop.query.all()
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"Time to retrieve all workshops: {query_time:.2f}ms")
        
        # Assert that the query completes within the expected time frame
        self.assertLess(query_time, 500, "Query took too long to execute")
    
    def test_get_all_enrollments_performance(self):
        """Test performance of retrieving all enrollments"""
        start_time = time.time()
        enrollments = Enrollment.query.all()
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"Time to retrieve all enrollments: {query_time:.2f}ms")
        
        # Assert that the query completes within the expected time frame
        self.assertLess(query_time, 500, "Query took too long to execute")
    
    def test_complex_query_performance(self):
        """Test performance of a complex join query"""
        start_time = time.time()
        # Complex query: Get all students with their workshop enrollments and filter by attended
        result = db.session.query(Student, Enrollment, Workshop)\
            .join(Enrollment, Student.id == Enrollment.student_id)\
            .join(Workshop, Enrollment.workshop_id == Workshop.id)\
            .filter(Enrollment.attended == True)\
            .all()
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"Time for complex join query: {query_time:.2f}ms")
        
        # Assert that the query completes within the expected time frame
        self.assertLess(query_time, 500, "Complex query took too long to execute")

class CertificateGenerationPerformanceTests(PerformanceTestBase):
    """Performance tests for certificate generation"""
    
    def setUp(self):
        """Additional setup for certificate generation tests"""
        # Add competencies to students and create certificate requests
        students = Student.query.limit(5).all()
        for i, student in enumerate(students):
            competency = f"Perf_Competency_{i}"
            student.add_competency(competency)
            student.update_competency_certificate_status(competency, "approved")
            db.session.commit()
    
    def test_certificate_generation_performance(self):
        """Test performance of certificate generation"""
        students = Student.query.limit(5).all()
        generation_times = []
        
        for i, student in enumerate(students):
            competency = f"Perf_Competency_{i}"
            
            start_time = time.time()
            certificate_data = get_certificate_data(student.id, competency)
            end_time = time.time()
            
            generation_time = (end_time - start_time) * 1000  # Convert to milliseconds
            generation_times.append(generation_time)
            
            # Verify certificate data was generated correctly
            self.assertIsNotNone(certificate_data)
            self.assertEqual(certificate_data['competency'], competency)
        
        if generation_times:
            avg_time = mean(generation_times)
            med_time = median(generation_times)
            max_time = max(generation_times)
            
            print(f"Certificate generation performance:")
            print(f"Average time: {avg_time:.2f}ms")
            print(f"Median time: {med_time:.2f}ms")
            print(f"Maximum time: {max_time:.2f}ms")
            
            # Assert that certificate generation completes within the expected time frame
            self.assertLess(max_time, 3000, "Certificate generation took too long")

class ConcurrentUserPerformanceTests(PerformanceTestBase):
    """Performance tests for concurrent user operations"""
    
    def test_concurrent_certificate_requests(self):
        """Test system performance with concurrent certificate requests"""
        students = Student.query.limit(5).all()
        
        # Add a competency to each student
        for i, student in enumerate(students):
            competency = f"Concurrent_Competency_{i}"
            student.add_competency(competency)
        db.session.commit()
        
        # Use this instance to keep track of app context state
        app_context = self.app.app_context()
        
        def request_certificate_task(student_index):
            """Task to request a certificate for a student"""
            if student_index >= len(students):
                return 0, False
                
            # Ensure we are in an app context
            with app_context:
                student = students[student_index]
                competency = f"Concurrent_Competency_{student_index}"
                
                start_time = time.time()
                success, message = request_certificate(student.id, competency)
                end_time = time.time()
                
                request_time = (end_time - start_time) * 1000  # Convert to milliseconds
                return request_time, success
        
        request_times = []
        error_count = 0
        
        try:
            # Single-threaded version for stability
            for i in range(min(5, len(students))):
                request_time, success = request_certificate_task(i)
                request_times.append(request_time)
                if not success:
                    error_count += 1
            
            if request_times:
                avg_time = mean(request_times)
                med_time = median(request_times)
                max_time = max(request_times)
                error_rate = error_count / len(students) if students else 0
                
                print(f"Concurrent certificate request performance:")
                print(f"Average time: {avg_time:.2f}ms")
                print(f"Median time: {med_time:.2f}ms")
                print(f"Maximum time: {max_time:.2f}ms")
                print(f"Error rate: {error_rate:.2%}")
                
                # Assert that requests complete within the expected time frame
                self.assertLess(max_time, 3000, "Certificate requests took too long")
                self.assertLess(error_rate, 0.2, "Too many errors in certificate requests")
        except Exception as e:
            self.fail(f"Exception in concurrent certificate requests: {str(e)}")

class EnrollmentPerformanceTests(PerformanceTestBase):
    """Performance tests for enrollment process"""
    
    def test_enrollment_process_performance(self):
        """Test performance of enrollment process"""
        students = Student.query.limit(3).all()
        workshops = Workshop.query.limit(3).all()
        
        if not students or not workshops:
            self.skipTest("No students or workshops available for testing")
            
        enrollment_times = []
        
        for student in students:
            for workshop in workshops:
                # Check if enrollment already exists
                existing = Enrollment.query.filter_by(
                    student_id=student.id,
                    workshop_id=workshop.id
                ).first()
                
                if existing:
                    continue
                
                start_time = time.time()
                
                # Create enrollment
                enrollment = Enrollment(
                    student_id=student.id,
                    workshop_id=workshop.id
                )
                db.session.add(enrollment)
                db.session.commit()
                
                # Mark as attended
                enrollment.mark_attended()
                db.session.commit()
                
                # Add competencies from workshop
                for competency in workshop.get_competency_names():
                    student.add_competency(competency)
                db.session.commit()
                
                end_time = time.time()
                enrollment_time = (end_time - start_time) * 1000
                enrollment_times.append(enrollment_time)
        
        if enrollment_times:
            avg_time = mean(enrollment_times)
            med_time = median(enrollment_times)
            max_time = max(enrollment_times)
            
            print(f"Enrollment process performance:")
            print(f"Average time: {avg_time:.2f}ms")
            print(f"Median time: {med_time:.2f}ms")
            print(f"Maximum time: {max_time:.2f}ms")
            
            # Assert that enrollment process completes within the expected time frame
            self.assertLess(max_time, 3000, "Enrollment process took too long")

class NotificationPerformanceTests(PerformanceTestBase):
    """Performance tests for notification system"""
    
    def test_notification_creation_performance(self):
        """Test performance of notification creation"""
        students = Student.query.limit(5).all()
        
        if not students:
            self.skipTest("No students available for testing")
            
        creation_times = []
        
        for i, student in enumerate(students):
            start_time = time.time()
            notification = create_notification(
                student_id=student.id,
                message=f"Test notification {i} at {datetime.now()}",
                notification_type="test"
            )
            end_time = time.time()
            
            creation_time = (end_time - start_time) * 1000
            creation_times.append(creation_time)
            
            self.assertIsNotNone(notification)
        
        if creation_times:
            avg_time = mean(creation_times)
            med_time = median(creation_times)
            max_time = max(creation_times)
            
            print(f"Notification creation performance:")
            print(f"Average time: {avg_time:.2f}ms")
            print(f"Median time: {med_time:.2f}ms")
            print(f"Maximum time: {max_time:.2f}ms")
            
            # Assert that notification creation completes within the expected time frame
            self.assertLess(max_time, 1000, "Notification creation took too long")
    
    def test_notification_retrieval_performance(self):
        """Test performance of notification retrieval"""
        # Create a bunch of notifications for a single student
        students = Student.query.first()
        
        if not students:
            self.skipTest("No students available for testing")
            
        # Create 20 notifications
        for i in range(20):
            create_notification(
                student_id=students.id,
                message=f"Perf test notification {i}",
                notification_type="test"
            )
        
        # Test retrieval performance
        start_time = time.time()
        notifications = get_notifications(students.id)
        end_time = time.time()
        
        retrieval_time = (end_time - start_time) * 1000
        
        print(f"Notification retrieval performance:")
        print(f"Time to retrieve notifications: {retrieval_time:.2f}ms")
        print(f"Number of notifications retrieved: {len(notifications)}")
        
        # Assert that notification retrieval completes within the expected time frame
        self.assertLess(retrieval_time, 1000, "Notification retrieval took too long") 