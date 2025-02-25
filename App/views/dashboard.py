from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from ..models.workshop import Workshop
from ..models.enrollment import Enrollment
from .. import db
from datetime import datetime
from sqlalchemy import or_

dashboard_views = Blueprint('dashboard_views', __name__, template_folder='../templates')

@dashboard_views.route('/dashboard')
@login_required
def dashboard():
    return render_template('Html/dashboard.html', user=current_user)

@dashboard_views.route('/workshops')
@login_required
def workshops():
    search_query = request.args.get('search', '')
    
    if search_query:
        all_workshops = Workshop.query.filter(
            or_(
                Workshop.workshopName.ilike(f'%{search_query}%'),
                Workshop.workshopDescription.ilike(f'%{search_query}%'),
                Workshop.instructor.ilike(f'%{search_query}%'),
                Workshop.location.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        all_workshops = Workshop.query.all()
    
    return render_template('Html/studentsAvailableWorkshops.html', 
                         workshops=all_workshops,
                         search_query=search_query)

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

@dashboard_views.route('/enroll-workshop/<workshop_id>')
@login_required
def enroll_workshop(workshop_id):
    workshop = Workshop.query.get_or_404(workshop_id)
    
    existing_enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        workshop_id=workshop_id
    ).first()
    
    if existing_enrollment:
        flash('You are already enrolled in this workshop!', 'warning')
        return redirect(url_for('dashboard_views.workshops'))
    
    # Create new enrollment
    enrollment = Enrollment(
        student_id=current_user.id,
        workshop_id=workshop_id,
        enrollment_date=datetime.now()
    )
    
    try:
        db.session.add(enrollment)
        db.session.commit()
        flash('Successfully enrolled in workshop!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error enrolling in workshop.', 'error')
    
    return redirect(url_for('dashboard_views.workshops'))

@dashboard_views.route('/my-workshops')
@login_required
def my_workshops():
    enrolled_workshops = Workshop.query.join(Enrollment).filter(
        Enrollment.student_id == current_user.id
    ).all()
    return render_template('Html/myWorkshops.html', workshops=enrolled_workshops)

@dashboard_views.route('/manage-workshops')
@login_required
def manage_workshops():
    print("Accessing manage_workshops route") 
    print(f"Current user type: {current_user.user_type}") 
    
    if current_user.user_type != 'admin':
        print(f"Access denied for user: {current_user.username}, type: {current_user.user_type}") 
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    workshops = Workshop.query.all()
    print(f"Found {len(workshops)} workshops") 
    return render_template('Html/manageWorkshops.html', workshops=workshops)

@dashboard_views.route('/edit-workshop/<workshop_id>', methods=['GET', 'POST'])
@login_required
def edit_workshop(workshop_id):
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
        
    workshop = Workshop.query.get_or_404(workshop_id)
    
    if request.method == 'POST':
        workshop.workshopName = request.form['workshopName']
        workshop.workshopDescription = request.form['workshopDescription']
        workshop.workshopDate = datetime.strptime(request.form['workshopDate'], '%Y-%m-%d').date()
        workshop.workshopTime = datetime.strptime(request.form['workshopTime'], '%H:%M').time()
        workshop.instructor = request.form['instructor']
        workshop.location = request.form['location']
        
        try:
            db.session.commit()
            flash('Workshop updated successfully!', 'success')
            return redirect(url_for('dashboard_views.manage_workshops'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating workshop: {str(e)}', 'error')
            
    return render_template('Html/editWorkshop.html', workshop=workshop)

@dashboard_views.route('/delete-workshop/<workshop_id>', methods=['DELETE'])
@login_required
def delete_workshop(workshop_id):
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    workshop = Workshop.query.get_or_404(workshop_id)
    
    if workshop.enrollments:
        return jsonify({'error': 'Cannot delete workshop with enrolled students'}), 400
        
    try:
        db.session.delete(workshop)
        db.session.commit()
        return jsonify({'message': 'Workshop deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def init_dashboard_routes(app):
    app.register_blueprint(dashboard_views) 