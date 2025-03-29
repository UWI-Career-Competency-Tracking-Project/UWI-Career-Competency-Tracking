from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from ..models.workshop import Workshop
from ..models.enrollment import Enrollment
from ..models.student import Student
from .. import db
from sqlalchemy import or_
from .dashboard_common import allowed_file, format_time_ago
import os

dashboard_views = Blueprint('dashboard_views', __name__, template_folder='../templates')

@dashboard_views.route('/dashboard')
@login_required
def dashboard():
    # Redirect to appropriate dashboard based on user type
    if current_user.user_type == 'student':
        return redirect(url_for('student_views.student_profile'))
    elif current_user.user_type == 'admin':
        return redirect(url_for('admin_views.admin_dashboard'))
    elif current_user.user_type == 'employer':
        return redirect(url_for('employer_views.employer_dashboard'))
    
    return render_template('Html/dashboard.html', user=current_user)

@dashboard_views.route('/workshops')
@login_required
def workshops():
    search_query = request.args.get('search', '').strip().lower()
    print("Accessing workshops route with search query:", search_query)
    
    try:
        all_workshops = Workshop.query.all()
        print(f"Retrieved {len(all_workshops)} workshops from database")
        
        for workshop in all_workshops:
            if workshop._competencies is None:
                workshop._competencies = []
                db.session.add(workshop)
        
        # Filter out workshops the student is already enrolled in
        if current_user.user_type == 'student':
            enrolled_workshop_ids = [
                enrollment.workshop_id for enrollment in 
                Enrollment.query.filter_by(student_id=current_user.id).all()
            ]
            all_workshops = [
                workshop for workshop in all_workshops 
                if workshop.id not in enrolled_workshop_ids
            ]
            print(f"Filtered out enrolled workshops, {len(all_workshops)} remaining")
        
        if search_query:
            filtered_workshops = []
            for workshop in all_workshops:
                workshop_data = [
                    workshop.workshopName.lower(),
                    (workshop.workshopDescription or '').lower(),
                    (workshop.instructor or '').lower(),
                    (workshop.location or '').lower()
                ]
                workshop_competencies = [comp.lower() for comp in workshop.competencies]
                
                if any(search_query in data for data in workshop_data) or \
                   any(search_query in comp for comp in workshop_competencies):
                    filtered_workshops.append(workshop)
            all_workshops = filtered_workshops
        
        print(f"Returning {len(all_workshops)} workshops after filtering")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render_template('Html/workshops_list.html', 
                                workshops=all_workshops,
                                search_query=search_query)
        
        return render_template('Html/studentsAvailableWorkshops.html', 
                             workshops=all_workshops,
                             search_query=search_query,
                             user=current_user)
                             
    except Exception as e:
        print(f"Error in workshops route: {str(e)}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        db.session.rollback()
        flash('Error loading workshops. Please try again.', 'error')
        return redirect(url_for('dashboard_views.dashboard')) 