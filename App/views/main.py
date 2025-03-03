from flask import Blueprint, render_template, session

main_views = Blueprint('main_views', __name__, template_folder='../templates')

@main_views.route('/')
def home():
    session.pop('_flashes', None)
    return render_template('Html/home.html')

def init_main_routes(app):
    app.register_blueprint(main_views) 