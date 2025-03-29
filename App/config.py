import os

class Config:
    # Paths
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(os.path.dirname(basedir), 'instance')
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    
    # File uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'workshop_images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # JWT settings
    JWT_ACCESS_COOKIE_NAME = 'access_token'
    JWT_TOKEN_LOCATION = ["cookies", "headers"]
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_CSRF_PROTECT = False
    
    # Templates
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = True
    
    # Misc
    PREFERRED_URL_SCHEME = 'https'
    FLASK_ADMIN_SWATCH = 'darkly'
    
    # Create upload folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # Create instance folder if it doesn't exist
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    # Flask-Uploads config
    UPLOADED_PHOTOS_DEST = os.path.join(basedir, 'uploads')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(Config.instance_path, 'database.db')
    JWT_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///:memory:'


class ProductionConfig(Config):
    """Production configuration"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(Config.instance_path, 'database.db')
    
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://')


# Configuration dictionary mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration class based on environment"""
    if not config_name:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    return config.get(config_name, config['default'])


# For backward compatibility
def load_config(app, overrides={}):
    """Legacy configuration loader for backward compatibility"""
    import warnings
    warnings.warn(
        "load_config is deprecated. Use get_config() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Get default configuration
    config_obj = get_config('default')
    app.config.from_object(config_obj)
    
    # Override with custom settings
    for key, value in overrides.items():
        app.config[key] = value
        
    # Load environment variables
    app.config.from_prefixed_env()
    
    return app