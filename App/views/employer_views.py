from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_from_directory
from flask_login import login_required, current_user
from ..models.workshop import Workshop
from ..models.enrollment import Enrollment
from ..models.student import Student
from ..models.employer import Employer
from .. import db
from sqlalchemy import or_, func, distinct
import os

employer_views = Blueprint('employer_views', __name__, template_folder='../templates')

@employer_views.route('/employer-dashboard')
@login_required
def employer_dashboard():
    if current_user.user_type != 'employer':
        flash('Access denied. Employers only.', 'error')
        return redirect(url_for('employer_views.employer_dashboard'))
    return render_template('Html/employerdashboard.html', user=current_user)

@employer_views.route('/search-candidates')
@login_required
def search_candidates():
    print(f"Current user type: {current_user.user_type}")  
    if not current_user.is_authenticated or current_user.user_type != 'employer':
        flash('Access Denied. This page is only accessible to employers.', 'error')
        return redirect(url_for('employer_views.employer_dashboard'))
    
    try:
        competency_filter = request.args.get('competency', '').strip().lower()
        rank_filter = request.args.get('rank', '').strip()
        
        # Get all students
        students = Student.query.all()
        filtered_students = []
        
        for student in students:
            if student.competencies:  
                student_data = {
                    'id': student.id,
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'email': student.email,
                    'competencies': []
                }
                
                # Process each competency
                for comp_name, comp_data in student.competencies.items():
                    rank = comp_data.get('rank', 0)
                    if rank > 0: 
                        rank_name = ['Beginner', 'Intermediate', 'Advanced'][rank-1]
                        
                        if rank_filter and str(rank) != rank_filter:
                            continue
                            
                        student_data['competencies'].append({
                            'name': comp_name,
                            'rank': rank,
                            'rank_name': rank_name
                        })
                
                if student_data['competencies'] and (
                    not competency_filter or 
                    any(competency_filter in comp['name'].lower() for comp in student_data['competencies'])
                ):
                    filtered_students.append(student_data)
        
        return render_template('Html/employerSearch.html', 
                             students=filtered_students,
                             search_query=competency_filter,
                             rank_filter=rank_filter)
                             
    except Exception as e:
        print(f"Error in candidate search: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading candidates.', 'error')
        return redirect(url_for('employer_views.employer_dashboard'))

@employer_views.route('/view-candidate-profile/<int:student_id>')
@login_required
def view_candidate_profile(student_id):
    if current_user.user_type != 'employer':
        flash('Access denied. Employers only.', 'error')
        return redirect(url_for('employer_views.employer_dashboard'))
    
    try:
        student = Student.query.get_or_404(student_id)
        
        # Get enrolled workshops
        enrolled_workshops = Workshop.query.join(Enrollment).filter(
            Enrollment.student_id == student.id
        ).all()
        
        # Get earned competencies
        earned_competencies = []
        if student.competencies:
            for comp_name, comp_data in student.competencies.items():
                rank = comp_data.get('rank', 0)
                certificate_status = comp_data.get('certificate_status', None)
                feedback = comp_data.get('feedback', '')
                
                if rank > 0:  
                    earned_competencies.append({
                        'name': comp_name,
                        'rank': rank,
                        'rank_name': ['Beginner', 'Intermediate', 'Advanced'][rank-1],
                        'certificate_status': certificate_status,
                        'feedback': feedback
                    })
        
        return render_template('Html/viewCandidateProfile.html', 
                              student=student,
                              earned_competencies=earned_competencies,
                              workshops=enrolled_workshops,
                              user=current_user)
                              
    except Exception as e:
        print(f"Error loading candidate profile: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading candidate profile.', 'error')
        return redirect(url_for('employer_views.search_candidates'))

@employer_views.route('/view-candidate-resume/<int:student_id>')
@login_required
def view_candidate_resume(student_id):
    if current_user.user_type != 'employer':
        flash('Access denied. Employers only.', 'error')
        return redirect(url_for('employer_views.employer_dashboard'))
    
    try:
        student = Student.query.get_or_404(student_id)
        if not student or not student.resume:
            flash('Resume not found', 'error')
            return redirect(url_for('employer_views.view_candidate_profile', student_id=student_id))
        
        # Prepare resume file path
        resumes_dir = 'App/static/resumes'
        file_path = os.path.join(resumes_dir, student.resume)
        
        if not os.path.exists(file_path):
            flash('Resume file not found', 'error')
            return redirect(url_for('employer_views.view_candidate_profile', student_id=student_id))
        
        # Extract original filename from stored filename
        original_filename = student.resume.split('_', 2)[2] if len(student.resume.split('_', 2)) > 2 else student.resume
        
        # Return file for viewing
        return send_from_directory(
            os.path.abspath(resumes_dir),
            student.resume,
            as_attachment=False,
            download_name=original_filename
        )
    
    except Exception as e:
        print(f"Error viewing candidate resume: {e}")
        flash('An error occurred while viewing resume.', 'error')
        return redirect(url_for('employer_views.view_candidate_profile', student_id=student_id)) 