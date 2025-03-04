import os
from flask import Flask, render_template
from flask_uploads import DOCUMENTS, IMAGES, TEXT, UploadSet, configure_uploads
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_login import LoginManager

from App.database import init_db
from App.config import load_config

from App.controllers import (
    setup_jwt,
    add_auth_context
)

from .database import db
from .models.user import User
from .views.auth import init_auth_routes
from .views.dashboard import init_dashboard_routes
from .views.main import init_main_routes

def create_app(overrides={}):
    app = Flask(__name__, static_url_path='/static')
    load_config(app, overrides)
    CORS(app)
    add_auth_context(app)
    photos = UploadSet('photos', TEXT + DOCUMENTS + IMAGES)
    configure_uploads(app, photos)
    init_db(app)
    jwt = setup_jwt(app)
    @jwt.invalid_token_loader
    @jwt.unauthorized_loader
    def custom_unauthorized_response(error):
        return render_template('401.html', error=error), 401

    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    app.static_folder = static_dir
    app.template_folder = template_dir

    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['EXPLAIN_TEMPLATE_LOADING'] = True

    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth_views.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    init_auth_routes(app)
    init_dashboard_routes(app)
    init_main_routes(app)

    app.app_context().push()
    return app