from flask import Flask
from flask_login import LoginManager
from .database import db
import os
from datetime import datetime

login_manager = LoginManager()

def create_app():
    # Get the base directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    # Create Flask app with proper template and static folders
    app = Flask(__name__,
        template_folder=template_dir,
        static_folder=static_dir)
    
    # Create instance folder for database
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Configure app
    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['EXPLAIN_TEMPLATE_LOADING'] = True
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth_views.login_action'
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
    
    # Register blueprints
    from .views.auth import auth
    from .views.dashboard import dashboard_views
    from .views.index import index_views
    from .views.main import main_views

    app.register_blueprint(auth)
    app.register_blueprint(dashboard_views)
    app.register_blueprint(index_views)
    app.register_blueprint(main_views)
    
    # Initialize database and create sample data
    with app.app_context():
        try:
            # Create database tables
            db.create_all()
            print("Created database tables")
            
            # Check if sample data exists
            admin_exists = Administrator.query.filter_by(username='admin').first() is not None
            student_exists = Student.query.filter_by(username='student').first() is not None
            workshop_exists = Workshop.query.first() is not None
            
            # Create sample users if they don't exist
            if not admin_exists and not student_exists:
                test_admin = Administrator(
                    username="admin",
                    email="admin@example.com",
                    first_name="Admin",
                    last_name="User",
                    password="admin123"
                )
                
                test_student = Student(
                    username="student",
                    email="student@example.com",
                    first_name="Student",
                    last_name="User",
                    password="student123"
                )
                
                db.session.add(test_admin)
                db.session.add(test_student)
                db.session.commit()
                print("Created test users")
            
            # Create sample workshop if it doesn't exist
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
            print(f"Error initializing database: {e}")
            if 'db' in locals():
                db.session.rollback()
            raise
    
    return app