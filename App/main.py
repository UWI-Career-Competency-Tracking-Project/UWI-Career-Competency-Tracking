from flask import Flask
from flask_login import LoginManager
from flask_uploads import DOCUMENTS, IMAGES, TEXT, UploadSet, configure_uploads
from flask_cors import CORS
import os
from datetime import datetime

from .database import db
from .config import get_config

# Get the login manager from __init__.py
from . import login_manager

def create_app(config_name=None):
 # Setup paths
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    app = Flask(__name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static',
        instance_relative_config=True)
    
    try:
        os.makedirs(app.instance_path)
        print(f"Created instance folder at: {app.instance_path}")
    except OSError:
        print(f"Instance folder already exists at: {app.instance_path}")
    
    # Load configuration
    app_config = get_config(config_name)
    app.config.from_object(app_config)
    
    if not app.config.get('SQLALCHEMY_DATABASE_URI').startswith('postgresql'):
        db_path = os.path.join(app.instance_path, 'database.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        print(f"Database will be stored at: {db_path}")
    
    # Initialize
    db.init_app(app)
    
    photos = UploadSet('photos', TEXT + DOCUMENTS + IMAGES)
    configure_uploads(app, photos)
    
    CORS(app)
    
    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth_views.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Import models
    from .models.user import User
    from .models.workshop import Workshop
    from .models.student import Student
    from .models.administrator import Administrator
    from .models.enrollment import Enrollment
    from .models.employer import Employer
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            print(f"Error loading user: {e}")
            return None
    
    from .views import init_views
    init_views(app)
    
    # Setup JWT if needed
    from .controllers.auth import setup_jwt, add_auth_context
    jwt = setup_jwt(app)
    add_auth_context(app)
    
    # Initialize database with sample data if needed
    with app.app_context():
        try:
            db.create_all()
            print("Created database tables")

            # Create admin user if it doesn't exist
            admin = Administrator.query.filter_by(username="admin").first()
            if not admin:
                admin = Administrator(
                    username="admin",
                    email="admin@example.com",
                    password="admin123",
                    first_name="Admin",
                    last_name="User"
                )
                db.session.add(admin)

            # Create student user if it doesn't exist 
            student = Student.query.filter_by(username="student").first()
            if not student:
                student = Student(
                    username="student",
                    email="student@example.com",
                    password="student123",
                    first_name="Test",
                    last_name="Student",
                    student_id="12345"
                )
                db.session.add(student)

            # Create employer user if it doesn't exist
            employer = Employer.query.filter_by(username="employer").first()
            if not employer:
                employer = Employer(
                    username="employer",
                    email="employer@example.com",
                    password="employer123",
                    first_name="Test",
                    last_name="Employer"
                )
                db.session.add(employer)

            db.session.commit()
            print("Created test users")

            # Create sample workshop if none exist
            workshop_exists = Workshop.query.first() is not None
            if not workshop_exists:
                # Workshop 1: Introduction to Leadership
                workshop1 = Workshop(
                    workshopID="WS001",
                    workshopName="Introduction to Leadership",
                    workshopDescription="Learn the fundamentals of leadership and team management.",
                    workshopDate=datetime.strptime("2024-03-15", "%Y-%m-%d").date(),
                    workshopTime="14:00",
                    instructor="Dr. Jane Smith",
                    location="Room 101",
                    image_path="workshop_images/default.jpg"
                )
                db.session.add(workshop1)
                db.session.flush()
                
                workshop1_competencies = ["Leadership I", "Communication I", "Team Work I"]
                workshop1.add_competencies(workshop1_competencies)
                
                # Workshop 2: Advanced Programming
                workshop2 = Workshop(
                    workshopID="WS002",
                    workshopName="Advanced Programming Techniques",
                    workshopDescription="Master advanced programming concepts and design patterns.",
                    workshopDate=datetime.strptime("2024-04-10", "%Y-%m-%d").date(),
                    workshopTime="10:00",
                    instructor="Prof. John Doe",
                    location="Computer Lab 3",
                    image_path="workshop_images/programming.png"
                )
                db.session.add(workshop2)
                db.session.flush()
                
                workshop2_competencies = ["Programming III", "Problem Solving II", "Critical Thinking II"]
                workshop2.add_competencies(workshop2_competencies)
                
                # Workshop 3: Professional Communication
                workshop3 = Workshop(
                    workshopID="WS003",
                    workshopName="Professional Communication Skills",
                    workshopDescription="Develop effective communication skills for the workplace.",
                    workshopDate=datetime.strptime("2024-04-25", "%Y-%m-%d").date(),
                    workshopTime="13:30",
                    instructor="Dr. Maria Rodriguez",
                    location="Room 205",
                    image_path="workshop_images/communication.png"
                )
                db.session.add(workshop3)
                db.session.flush()
                
                workshop3_competencies = ["Communication II", "Public Speaking I", "Professional Etiquette I"]
                workshop3.add_competencies(workshop3_competencies)
                
                # Workshop 4: Project Management
                workshop4 = Workshop(
                    workshopID="WS004",
                    workshopName="Project Management Fundamentals",
                    workshopDescription="Learn essential project management methodologies and tools.",
                    workshopDate=datetime.strptime("2024-05-05", "%Y-%m-%d").date(),
                    workshopTime="09:00",
                    instructor="Mr. Robert Johnson",
                    location="Conference Room A",
                    image_path="workshop_images/project.jpg"
                )
                db.session.add(workshop4)
                db.session.flush()
                
                workshop4_competencies = ["Project Management II", "Team Work II", "Time Management I"]
                workshop4.add_competencies(workshop4_competencies)
                
                db.session.commit()
                print("Created sample workshops with competencies")
            
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            db.session.rollback()
    
    return app