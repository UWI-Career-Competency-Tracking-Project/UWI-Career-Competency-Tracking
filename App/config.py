import os

class Config:
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '..', 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SECRET_KEY = 'your-secret-key-here' 
    
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'workshop_images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

def load_config(app, overrides):
    if os.path.exists(os.path.join('./App', 'custom_config.py')):
        app.config.from_object('App.custom_config')
    else:
        app.config.from_object('App.default_config')
    app.config.from_prefixed_env()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['UPLOADED_PHOTOS_DEST'] = "App/uploads"
    app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
    app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
    app.config["JWT_COOKIE_SECURE"] = True
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config['FLASK_ADMIN_SWATCH'] = 'darkly'
    for key in overrides:
        app.config[key] = overrides[key]