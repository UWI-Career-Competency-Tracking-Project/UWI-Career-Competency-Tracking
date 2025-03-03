from flask import Flask
from flask_login import LoginManager
from .database import db, init_db
import os
from datetime import datetime

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    app.config['SECRET_KEY'] = 'dev'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_action'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    from .models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            print(f"Error loading user: {e}")
            return None
    
    from .views.auth import auth
    from .views.dashboard import dashboard_views
    from .views.index import index_views
    from .views.main import main_views

    app.register_blueprint(auth)
    app.register_blueprint(dashboard_views)
    app.register_blueprint(index_views)
    app.register_blueprint(main_views)
    
    with app.app_context():
        try:
            db.create_all()
            print("Created database tables")
            
            # Import models needed for sample data
            from .models.workshop import Workshop
            from .models.student import Student
            from .models.administrator import Administrator
            
            admin_exists = Administrator.query.filter_by(username='admin').first() is not None
            student_exists = Student.query.filter_by(username='student').first() is not None
            workshop_exists = Workshop.query.first() is not None
            
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
                db.session.flush()  # Ensure workshop has an ID before adding competencies
                
                # Add competencies to the workshop
                workshop_competencies = ["Leadership", "Communication", "Team Management"]
                sample_workshop.add_competencies(workshop_competencies)
                
                db.session.commit()
                print("Created sample workshop with competencies")
            
            create_sample_data()  # Create sample data after initializing database
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            if 'db' in locals():
                db.session.rollback()
    
    return app

def create_sample_data():
    """Create sample data for testing if no data exists."""
    from .models.workshop import Workshop
    from .models.administrator import Administrator
    from .models.student import Student
    from datetime import datetime
    
    # Check if any workshops exist
    if Workshop.query.first() is None:
        try:
            # Create sample admin
            admin = Administrator(
                username="admin",
                email="admin@uwi.edu",
                password="admin123",
                first_name="Admin",
                last_name="User"
            )
            db.session.add(admin)

            # Create sample student
            student = Student(
                username="student",
                email="student@my.uwi.edu",
                password="student123",
                first_name="Student",
                last_name="User"
            )
            db.session.add(student)

            # Create sample workshop
            workshop = Workshop(
                workshopID="WS001",
                workshopName="Introduction to Leadership",
                workshopDescription="Learn the fundamentals of leadership and team management",
                workshopDate=datetime.strptime("2024-03-15", "%Y-%m-%d").date(),
                workshopTime="14:00",
                instructor="Dr. Jane Smith",
                location="Room 101",
                image_path="/static/images/leadership.jpg"
            )
            db.session.add(workshop)
            db.session.flush()  # Ensure workshop has an ID before adding competencies

            # Add competencies to workshop
            workshop_competencies = ["Leadership", "Communication", "Team Management"]
            workshop.add_competencies(workshop_competencies)

            db.session.commit()
            print("Sample data created successfully")
            
        except Exception as e:
            print(f"Error creating sample data: {e}")
            db.session.rollback()
            raise