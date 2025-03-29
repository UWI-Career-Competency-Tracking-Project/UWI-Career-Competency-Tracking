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

            db.session.commit()
            print("Created test users")

            # Create sample workshop if none exist
            workshop_exists = Workshop.query.first() is not None
            if not workshop_exists:
                sample_workshop = Workshop(
                    workshopID="WS001",
                    workshopName="Introduction to Leadership",
                    workshopDescription="Learn the fundamentals of leadership and team management.",
                    workshopDate=datetime.strptime("2024-03-15", "%Y-%m-%d").date(),
                    workshopTime="14:00",
                    instructor="Dr. Jane Smith",
                    location="Room 101",
                    image_path="workshop_images/default.jpg"
                )
                db.session.add(sample_workshop)
                db.session.flush()
                
                workshop_competencies = ["Leadership", "Communication", "Team Management"]
                sample_workshop.add_competencies(workshop_competencies)
                
                db.session.commit()
                print("Created sample workshop with competencies")
            
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            db.session.rollback()
    
    return app