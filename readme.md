# UWI Career Competency Tracking

A comprehensive web application for tracking, developing, and certifying career competencies for UWI students.

## Overview
The UWI Career Competency Tracking application provides a centralized platform where:
- Students can track their competency development and receive certifications
- Administrators can create workshops and verify student competencies
- Employers can view verified student competencies for hiring decisions

## Features
- **User Authentication**: Role-based login system for students, administrators, and employers
- **Workshop Management**: Create, schedule, and manage workshops with associated competencies
- **Competency Tracking**: Record and track student competencies gained through workshops
- **Certificate Generation**: Generate certificates for verified competencies
- **Profile Management**: Complete user profiles for students and employers
- **Responsive Design**: Modern UI that works across desktop and mobile devices

## User Roles and Capabilities
### Students
- Register and create profiles with personal/academic information
- Browse and enroll in competency-building workshops
- Track acquired competencies and their levels
- Request certificates for verified competencies
- Manage personal profiles and upload resumes
- View their workshop history and certificate status

### Administrators
- Create and manage workshops with specific competencies
- Review and verify student competencies
- Approve certificate requests
- Manage all users in the system
- Generate reports on student participation and competency development

### Employers
- Create employer profiles
- Browse student profiles with verified competencies
- Filter students by competencies and qualifications
- View verified certificates and student achievements

## Application Architecture
### MVC Structure
The application follows the Model-View-Controller (MVC) architectural pattern:
- **Models**: Database entities and business logic
- **Views**: User interface templates and routes
- **Controllers**: Business logic that connects models and views

### Key Components

#### Views
The application has several view modules:
- `views/auth.py`: Authentication views (login, registration, password reset)
- `views/student_views.py`: Student dashboard, workshop enrollment, competency tracking
- `views/admin_views.py`: Admin dashboard, workshop management, certificate approval
- `views/employer_views.py`: Employer dashboard, student browsing, competency search
- `views/dashboard_views.py`: Dashboard views for all user types
- `views/index.py`: Main landing page and public views

#### Models
- `models/user.py`: Base user class with authentication
- `models/student.py`: Student user type with competency tracking
- `models/administrator.py`: Admin user type
- `models/employer.py`: Employer user type
- `models/workshop.py`: Workshop scheduling and management
- `models/enrollment.py`: Student workshop enrollments
- `models/competency.py`: Competency definitions
- `models/student_competency.py`: Tracks student competency levels
- `models/certificate.py`: Certificate generation and verification
- `models/certificate_request.py`: Student requests for certificates
- `models/notification.py`: System notifications
- `models/feedback.py`: Workshop and competency feedback

#### Controllers
- `controllers/auth.py`: Authentication logic and JWT setup
- Other controller files handle business logic for core functionality

## Tech Stack
- **Backend**: Flask framework (Python)
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Frontend**: HTML, CSS, JavaScript with Bootstrap
- **Authentication**: Flask-Login and JWT
- **ORM**: SQLAlchemy
- **Testing**: Pytest

## Installation and Setup

### Prerequisites
* Python 3.7+
* Pip package manager

### Installation Steps

1. Clone the repository:
```bash
$ git clone https://github.com/UWI-Career-Competency-Tracking-Project/UWI-Career-Competency-Tracking.git
$ cd UWI-Career-Competency-Tracking
```

2. Install dependencies:
```bash
$ pip install -r requirements.txt
```

### Environment Setup

Create a `.flaskenv` file in the root directory with the following content:
```
FLASK_APP=wsgi.py
FLASK_ENV=development
```

## Configuration Management

Configuration information such as database credentials and API keys are managed through environment variables or config files.

### Development Configuration

When running the project in a development environment, the app is configured via `default_config.py` file in the App folder:

```python
SQLALCHEMY_DATABASE_URI = "sqlite:///temp-database.db"
SECRET_KEY = "secret key"
JWT_ACCESS_TOKEN_EXPIRES = 7
ENV = "DEVELOPMENT"
```

### Production Configuration

For production deployment on Render, set environment variables in your project dashboard:
- DATABASE_URL (automatically provided by Render's PostgreSQL service)
- SECRET_KEY
- ENV=production

## Running the Project

### Development Server
```bash
$ flask run
```

### Production Server
```bash
$ gunicorn wsgi:app
```

## Database Management

### Database Initialization
The database is automatically initialized when the application starts. The initialization code can be found in `App/main.py` which:
- Creates all necessary database tables
- Sets up sample users (admin, student, employer)
- Creates sample workshops with competencies

## Testing

### Running Tests
Unit and integration tests are in the App/tests directory:

```bash
# Run all tests
$ pytest

# Run specific test categories
$ flask test user
```

### Test Coverage
Generate a test coverage report:
```bash
$ coverage report
$ coverage html   
```

## Project Structure
```
UWI-Career-Competency-Tracking/
├── App/                    # Main application package
│   ├── controllers/        # Business logic
│   ├── models/             # Database models
│   ├── static/             # Static assets (CSS, JS, images)
│   ├── templates/          # HTML templates
│   ├── tests/              # Test cases
│   ├── views/              # Route handlers
│   ├── __init__.py         # App initialization
│   ├── config.py           # Configuration handling
│   ├── database.py         # Database setup
│   ├── default_config.py   # Default configuration
│   └── main.py             # App factory and initialization
├── instance/               # Instance-specific data
├── __pycache__/            # Compiled Python files
├── e2e/                    # End-to-end tests
├── .flaskenv               # Flask environment variables
├── app.py                  # Application entry point
├── gunicorn_config.py      # Gunicorn configuration
├── package.json            # Node.js dependencies
├── pytest.ini              # Pytest configuration
├── requirements.txt        # Python dependencies
├── setup.cfg               # Setup configuration
└── wsgi.py                 # WSGI entry point
```

## Data Flow

1. **User Registration and Authentication**:
   - Users register with email/password
   - Authentication handled via Flask-Login
   - Role-based access control for different user types

2. **Workshop Management**:
   - Administrators create workshops with specific competencies
   - Workshops are stored with dates, times, locations, and instructors
   - Competencies associated with workshops are tracked

3. **Student Enrollment**:
   - Students browse available workshops
   - Students enroll in workshops
   - System tracks enrollment and attendance

4. **Competency Acquisition**:
   - Students gain competencies from workshop attendance
   - Competency levels are tracked (from beginner to advanced)
   - Students can see their competency growth over time

5. **Certificate Generation**:
   - Students request certificates for specific competencies
   - Administrators review and approve certificates
   - System generates downloadable certificates

## Security Considerations

- Passwords are hashed using bcrypt
- Role-based access control for protected routes
- CSRF protection for form submissions
- Input validation on all user inputs

## Troubleshooting

### Database Issues
If you experience database issues, you may need to run migrations or recreate the database:
```bash
$ flask db upgrade 
```

## Deployment

### Deployed to Render

## Link: https://uwi-career-competency-tracker.onrender.com


## Future Development Plans
- Mobile application for on-the-go competency tracking
- Advanced analytics dashboard for institutional insights
- Integration with job boards and hiring platforms
- Blockchain-based certification verification
- Expanded employer engagement features
- Integration with university systems for automatic enrollment

## Contributors
- Ijaaz Sisarran (@IjaazSisarran)
- Varune Rampersad (@VaruneRampersad)
- Josiah Phillip (@Josiah-Phillip)