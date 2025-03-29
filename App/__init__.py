from .database import db

from flask_login import LoginManager
login_manager = LoginManager()

from .main import create_app

__version__ = '1.0.0'