import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from App.database import db
from App.models.user import User

from flask_login import LoginManager
from App.views.auth import init_auth_routes
from App.views.dashboard import init_dashboard_routes
from App.views.main import init_main_routes

base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'App', 'templates')
static_dir = os.path.join(base_dir, 'App', 'static')

app = Flask(__name__, 
    template_folder=template_dir,
    static_folder=static_dir)

app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['EXPLAIN_TEMPLATE_LOADING'] = True 

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth_views.login_action'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

init_auth_routes(app)
init_dashboard_routes(app)
init_main_routes(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Registered routes:")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint}: {rule.rule}")
    app.run(debug=True)
