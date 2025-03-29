"""
Views package for the application.
This module registers all blueprints with the application.
"""

from .index import index_views
from .auth import auth as auth_views
from .dashboard_views import dashboard_views
from .student_views import student_views
from .admin_views import admin_views
from .employer_views import employer_views
from .main import main_views

# List of all blueprints for easier registration
views = [
    index_views, 
    auth_views, 
    dashboard_views, 
    student_views, 
    admin_views, 
    employer_views, 
    main_views
]

def init_views(app):
    """
    Register all blueprints with the application.
    
    Args:
        app: Flask application instance
    """
    for blueprint in views:
        app.register_blueprint(blueprint) 