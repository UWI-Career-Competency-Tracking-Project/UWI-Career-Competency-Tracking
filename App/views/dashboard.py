from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from ..models.workshop import Workshop
from .. import db
from datetime import datetime

dashboard_views = Blueprint('dashboard_views', __name__, template_folder='../templates')

@dashboard_views.route('/dashboard')
@login_required
def dashboard():
    return render_template('Html/dashboard.html', user=current_user)

@dashboard_views.route('/workshops')
@login_required
def workshops():
    all_workshops = Workshop.query.all()
    return render_template('Html/studentsAvailableWorkshops.html', workshops=all_workshops)

@dashboard_views.route('/admin-workshop-creation/', methods=['GET', 'POST'])
@login_required
def admin_workshop_creation():
    print("Accessing admin_workshop_creation route")  
    print(f"Current user type: {current_user.user_type}") 
    
    if current_user.user_type != 'admin':
        print(f"Access denied for user: {current_user.username}, type: {current_user.user_type}")
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    if request.method == 'POST':
        try:
            new_workshop = Workshop(
                workshopID=request.form.get('workshopID'),
                workshopName=request.form.get('workshopName'),
                workshopDescription=request.form.get('workshopDescription'),
                workshopDate=datetime.strptime(request.form.get('workshopDate'), '%Y-%m-%d').date(),
                workshopTime=datetime.strptime(request.form.get('workshopTime'), '%H:%M').time(),
                instructor=request.form.get('instructor'),
                location=request.form.get('location')
            )
            db.session.add(new_workshop)
            db.session.commit()
            flash('Workshop created successfully!', 'success')
            return redirect(url_for('dashboard_views.dashboard'))
        except Exception as e:
            print(f"Error creating workshop: {e}") 
            db.session.rollback()
            flash(f'Error creating workshop: {str(e)}', 'error')

    try:
        print("Attempting to render template")  
        return render_template('Html/adminWorkshopCreation.html')
    except Exception as e:
        print(f"Error rendering template: {e}") 
        return str(e), 500

def init_dashboard_routes(app):
    app.register_blueprint(dashboard_views) 