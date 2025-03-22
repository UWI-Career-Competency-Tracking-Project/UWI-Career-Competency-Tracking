from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_from_directory
from flask_login import login_required, current_user
from ..models.workshop import Workshop
from ..models.enrollment import Enrollment
from ..models.student import Student
from .. import db
from datetime import datetime
from sqlalchemy import or_
import os
from werkzeug.utils import secure_filename
from ..models.user import User
from ..models.student_competency import StudentCompetency
from ..models.competency import Competency
from ..controllers import certificate_controller
from ..models.job_roles import JobRole
from ..models.job_competency import JobCompetency

dashboard_views = Blueprint('dashboard_views', __name__, template_folder='../templates')

UPLOAD_FOLDER = 'App/static/workshop_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@dashboard_views.route('/student-dashboard')
@login_required
def student_dashboard():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    return render_template('Html/studentdashboard.html', user=current_user)

@dashboard_views.route('/admin-dashboard')
@login_required
def admin_dashboard():
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    return render_template('Html/admindashboard.html', user=current_user)

@dashboard_views.route('/employer-dashboard')
@login_required
def employer_dashboard():
    if current_user.user_type != 'employer':
        flash('Access denied. Employers only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    return render_template('Html/employerdashboard.html', user=current_user)

@dashboard_views.route('/dashboard')
@login_required
def dashboard():
    # Redirect to appropriate dashboard based on user type
    if current_user.user_type == 'student':
        return redirect(url_for('dashboard_views.student_dashboard'))
    elif current_user.user_type == 'admin':
        return redirect(url_for('dashboard_views.admin_dashboard'))
    elif current_user.user_type == 'employer':
        return redirect(url_for('dashboard_views.employer_dashboard'))
    
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

@dashboard_views.route('/admin-workshop-creation/', methods=['GET', 'POST'])
@login_required
def admin_workshop_creation():
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    if request.method == 'POST':
        try:
            print("\n=== Workshop Creation Process Started ===")
            print("1. Form Data Received:", {k: v for k, v in request.form.items()})
            
            image_path = None
            if 'workshop_image' in request.files:
                file = request.files['workshop_image']
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        if not os.path.exists(UPLOAD_FOLDER):
                            os.makedirs(UPLOAD_FOLDER)
                        
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(UPLOAD_FOLDER, filename)
                        file.save(file_path)
                        image_path = f'workshop_images/{filename}'
                        print("2. Image saved successfully:", image_path)
                    else:
                        flash('Invalid file type. Please upload an image file.', 'error')
                        return redirect(request.url)

            competencies = [comp.strip() for comp in request.form.get('competencies', '').split(',') if comp.strip()]
            print("3. Parsed competencies:", competencies)
            
            try:
                new_workshop = Workshop(
                    workshopID=request.form.get('id'),
                    workshopName=request.form.get('name'),
                    workshopDescription=request.form.get('description'),
                    workshopDate=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
                    workshopTime=request.form.get('time'),
                    instructor=request.form.get('instructor'),
                    location=request.form.get('location'),
                    image_path=image_path
                )
                print("5. Workshop object created successfully")
                
                if competencies:
                    new_workshop.add_competencies(competencies)
                    print("5a. Added competencies:", competencies)
                
            except Exception as model_error:
                print("ERROR creating Workshop object:", str(model_error))
                print("Workshop model attributes:", dir(Workshop))
                raise
            
            try:
                db.session.add(new_workshop)
                print("6. Workshop added to session")
                db.session.flush()
                print("7. Session flushed successfully")
            except Exception as db_error:
                print("ERROR adding to session:", str(db_error))
                raise
            
            try:
                db.session.commit()
                print("8. Changes committed to database")
            except Exception as commit_error:
                print("ERROR during commit:", str(commit_error))
                raise
            
            try:
                created_workshop = Workshop.query.get(new_workshop.id)
                if created_workshop:
                    print("9. Workshop creation verified:", vars(created_workshop))
                else:
                    print("WARNING: Workshop not found after creation!")
            except Exception as verify_error:
                print("ERROR during verification:", str(verify_error))
            
            flash('Workshop created successfully!', 'success')
            return redirect(url_for('dashboard_views.workshops'))
            
        except Exception as e:
            print("\n=== Workshop Creation Failed ===")
            print("Error type:", type(e).__name__)
            print("Error message:", str(e))
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            db.session.rollback()
            flash(f'Error creating workshop: {str(e)}', 'error')
            return redirect(url_for('dashboard_views.admin_workshop_creation'))

    return render_template('Html/adminWorkshopCreation.html')

@dashboard_views.route('/enroll-workshop/<workshop_id>')
@login_required
def enroll_workshop(workshop_id):
    if not isinstance(current_user, Student):
        flash('Only students can enroll in workshops.', 'error')
        return redirect(url_for('dashboard_views.workshops'))
    
    try:
        workshop = Workshop.query.get(workshop_id)
        if not workshop:
            flash('Workshop not found.', 'error')
            return redirect(url_for('dashboard_views.workshops'))
        
        print(f"Found workshop: {workshop.workshopName}")
        print(f"Workshop competencies: {workshop.competencies}")
        
        existing_enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            workshop_id=workshop_id
        ).first()
        
        if existing_enrollment:
            flash('You are already enrolled in this workshop.', 'info')
            return redirect(url_for('dashboard_views.workshops'))
        
        enrollment = Enrollment(
            student_id=current_user.id,
            workshop_id=workshop_id
        )
        db.session.add(enrollment)
        db.session.flush()  
        
        print("Created enrollment, adding competencies...")
        
        enrollment.add_workshop_competencies()
        
        student = Student.query.get(current_user.id)
        print(f"Student competencies after enrollment: {student.competencies}")
        
        db.session.commit()
        flash('Successfully enrolled in workshop!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error enrolling in workshop: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        flash('An error occurred while enrolling in the workshop.', 'error')
    
    return redirect(url_for('dashboard_views.workshops'))

@dashboard_views.route('/competencies')
@login_required
def competencies():
    if current_user.user_type != 'student':
        flash('Only students can view competencies.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
        
    try:
        student = Student.get_by_id(current_user.id)
        if not student:
            flash('Student account not found.', 'error')
            return redirect(url_for('dashboard_views.dashboard'))
            
        return render_template('Html/competencies.html', user=student)
        
    except Exception as e:
        print(f"Error loading competencies: {e}")
        flash('Error loading competencies.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))

@dashboard_views.route('/my-workshops')
@login_required
def my_workshops():
    if current_user.user_type != 'student':
        flash('Only students can view their workshops.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
        
    try:
        student = Student.get_by_id(current_user.id)
        if not student:
            flash('Student account not found.', 'error')
            return redirect(url_for('dashboard_views.dashboard'))
        
        enrolled_workshops = Workshop.query.join(Enrollment).filter(
            Enrollment.student_id == student.id
        ).all()
        
        print(f"Found {len(enrolled_workshops)} enrolled workshops for student {student.username}")
        
        return render_template('Html/myWorkshops.html', 
                             workshops=enrolled_workshops,
                             user=student)
                             
    except Exception as e:
        print(f"Error fetching workshops: {e}")
        db.session.rollback()
        flash('Error loading workshops.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))

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
        try:
            workshop.workshopName = request.form['name']
            workshop.workshopDescription = request.form['description']
            workshop.workshopDate = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            workshop.workshopTime = request.form['time']
            workshop.instructor = request.form['instructor']
            workshop.location = request.form['location']
            
            if 'workshop_image' in request.files:
                file = request.files['workshop_image']
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        if not os.path.exists(UPLOAD_FOLDER):
                            os.makedirs(UPLOAD_FOLDER)
                        
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(UPLOAD_FOLDER, filename)
                        file.save(file_path)
                        workshop.image_path = f'workshop_images/{filename}'
                    else:
                        flash('Invalid file type. Please upload an image file.', 'error')
                        return redirect(request.url)
            
            competencies = [comp.strip() for comp in request.form.get('competencies', '').split(',') if comp.strip()]
            if competencies:
                workshop.add_competencies(competencies)
            
            db.session.commit()
            flash('Workshop updated successfully!', 'success')
            return redirect(url_for('dashboard_views.manage_workshops'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error updating workshop: {e}")
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

@dashboard_views.route('/admin-badges', methods=['GET', 'POST'])
@login_required
def admin_badges():
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    search_query = request.args.get('search', '')
    
    students_query = Student.query
    
    if search_query:
        students_query = students_query.filter(
            or_(
                Student.first_name.ilike(f'%{search_query}%'),
                Student.last_name.ilike(f'%{search_query}%'),
                Student.username.ilike(f'%{search_query}%')
            )
        )
    
    students = students_query.all()
    
    student_competencies = []
    for student in students:
        if student.competencies:
            for comp_name in student.competencies:
                student_competencies.append({
                    'student': student,
                    'competency': comp_name,
                    'data': student.competencies[comp_name]
                })
    
    if request.method == 'POST':
        try:
            student_id = request.form.get('student_id')
            competency = request.form.get('competency')
            rank = request.form.get('rank')
            feedback = request.form.get('feedback', '')
            
            print(f"Received update request - Student ID: {student_id}, Competency: {competency}, Rank: {rank}, Feedback: {feedback}")
            
            if not rank:
                flash('Please select a rank', 'error')
                return redirect(url_for('dashboard_views.admin_badges'))
            
            student = Student.query.get(student_id)
            if student:
                rank = int(rank)
                if rank not in [1, 2, 3]:
                    flash('Invalid rank selected', 'error')
                    return redirect(url_for('dashboard_views.admin_badges'))
                
                print(f"Updating student competency - Before update: {student.competencies.get(competency)}")
                student.update_competency_rank(competency, rank, feedback)
                print(f"After update: {student.competencies.get(competency)}")
                
                db.session.commit()
                flash('Student competency updated successfully!', 'success')
            else:
                flash('Student not found', 'error')
            
        except Exception as e:
            print(f"Error updating competency: {e}")
            db.session.rollback()
            flash('Error updating student competency.', 'error')
    
    return render_template('Html/adminbadges.html', 
                         student_competencies=student_competencies,
                         search_query=search_query)

@dashboard_views.route('/unenroll-workshop/<workshop_id>', methods=['POST'])
@login_required
def unenroll_workshop(workshop_id):
    if not isinstance(current_user, Student):
        return jsonify({'error': 'Only students can unenroll from workshops.'}), 403
    
    try:
        student = Student.query.get(current_user.id)
        if not student:
            return jsonify({'error': 'Student not found.'}), 404

        enrollment = Enrollment.query.filter_by(
            student_id=student.id,
            workshop_id=workshop_id
        ).first()
        
        if not enrollment:
            return jsonify({'error': 'You are not enrolled in this workshop.'}), 404
        
        workshop = Workshop.query.get(workshop_id)
        
        if workshop and workshop.competencies:
            other_workshops = Workshop.query.join(Enrollment).filter(
                Enrollment.student_id == student.id,
                Workshop.id != workshop_id
            ).all()
            
            for comp_name in workshop.competencies:
                competency_in_other_workshop = False
                for other_workshop in other_workshops:
                    if comp_name in other_workshop.competencies:
                        competency_in_other_workshop = True
                        break
                
                if not competency_in_other_workshop:
                    competency = Competency.query.filter_by(name=comp_name).first()
                    if competency:
                        StudentCompetency.query.filter_by(
                            student_id=student.id,
                            competency_id=competency.id
                        ).delete()
        
        db.session.delete(enrollment)
        db.session.commit()
        
        return jsonify({'message': 'Successfully unenrolled from workshop.'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@dashboard_views.route('/request-certificate', methods=['POST'])
@login_required
def request_certificate():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        competency = request.form.get('competency')
        if not competency:
            flash('Invalid request.', 'error')
            return redirect(url_for('dashboard_views.competencies'))
        
        student = Student.query.get(current_user.id)
        if not student:
            flash('Student not found.', 'error')
            return redirect(url_for('dashboard_views.competencies'))
        
        if competency not in student.competencies:
            flash('Competency not found.', 'error')
            return redirect(url_for('dashboard_views.competencies'))
            
        comp_data = student.competencies[competency]
        if comp_data.get('rank') != 3:
            flash('Certificate can only be requested for Advanced rank competencies.', 'error')
            return redirect(url_for('dashboard_views.competencies'))
        
        success, message = certificate_controller.request_certificate(current_user.id, competency)
        
        if success:
            student.update_competency_certificate_status(competency, 'pending')
            flash('Certificate request submitted successfully.', 'success')
        else:
            flash(message, 'error')
            
        return redirect(url_for('dashboard_views.competencies'))
        
    except Exception as e:
        print(f"Error in request_certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while processing your request.', 'error')
        return redirect(url_for('dashboard_views.competencies'))

@dashboard_views.route('/validate-certificates')
@login_required
def validate_certificates():
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    pending_requests = certificate_controller.get_pending_requests()
    return render_template('Html/adminValidatecomp.html', pending_requests=pending_requests)

@dashboard_views.route('/process-certificate-request/<int:request_id>', methods=['POST'])
@login_required
def process_certificate_request(request_id):
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    action = request.form.get('action')
    if action not in ['approve', 'deny']:
        flash('Invalid action.', 'error')
        return redirect(url_for('dashboard_views.validate_certificates'))
    
    success, message = certificate_controller.process_request(request_id, action)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('dashboard_views.validate_certificates'))

@dashboard_views.route('/view-certificate/<competency>')
@login_required
def view_certificate(competency):
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    certificate_data = certificate_controller.get_certificate_data(current_user.id, competency)
    if not certificate_data:
        flash('Certificate not found.', 'error')
        return redirect(url_for('dashboard_views.competencies'))
    
    # Add user to certificate_data
    certificate_data['user'] = current_user
    
    return render_template('Html/studentCertificate.html', **certificate_data)

@dashboard_views.route('/earned-badges')
@login_required
def earned_badges():
    if current_user.user_type != 'student':
        flash('Only students can view their badges and certificates.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
        
    try:
        student = Student.get_by_id(current_user.id)
        if not student:
            flash('Student account not found.', 'error')
            return redirect(url_for('dashboard_views.dashboard'))
            
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
        
        return render_template('Html/earnedBadges.html', 
                             user=student,
                             earned_competencies=earned_competencies)
                             
    except Exception as e:
        print(f"Error loading badges: {e}")
        flash('Error loading badges and certificates.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))

@dashboard_views.route('/search-candidates')
@login_required
def search_candidates():
    print(f"Current user type: {current_user.user_type}")  
    if not current_user.is_authenticated or current_user.user_type != 'employer':
        flash('Access Denied. This page is only accessible to employers.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
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
        return redirect(url_for('dashboard_views.dashboard'))

def create_sample_jobs():
    """Create sample jobs if none exist"""
    if JobRole.query.count() == 0:
        jobs = [
            {
                'title': 'Software Developer',
                'description': 'Design and develop software applications using modern technologies.',
                'required_rank': 2,  # Intermediate
                'competencies': [
                    ('Programming', 2),
                    ('Problem Solving', 2),
                    ('Team Work', 1)
                ]
            },
            {
                'title': 'Data Analyst',
                'description': 'Analyze complex data sets to identify trends and patterns.',
                'required_rank': 2,
                'competencies': [
                    ('Data Analysis', 2),
                    ('Problem Solving', 2),
                    ('Communication', 1)
                ]
            },
            {
                'title': 'Project Manager',
                'description': 'Lead and coordinate software development projects.',
                'required_rank': 3,  # Advanced
                'competencies': [
                    ('Leadership', 3),
                    ('Communication', 2),
                    ('Team Work', 2)
                ]
            },
            {
                'title': 'UI/UX Designer',
                'description': 'Create intuitive and visually appealing user interfaces for web and mobile applications.',
                'required_rank': 2,
                'competencies': [
                    ('Design Thinking', 2),
                    ('Communication', 2),
                    ('Creativity', 2)
                ]
            },
            {
                'title': 'DevOps Engineer',
                'description': 'Implement and maintain CI/CD pipelines and cloud infrastructure.',
                'required_rank': 3,
                'competencies': [
                    ('Cloud Computing', 3),
                    ('Problem Solving', 2),
                    ('System Administration', 2)
                ]
            },
            {
                'title': 'Business Analyst',
                'description': 'Bridge the gap between business needs and technical solutions.',
                'required_rank': 2,
                'competencies': [
                    ('Business Analysis', 2),
                    ('Communication', 2),
                    ('Problem Solving', 2)
                ]
            },
            {
                'title': 'Quality Assurance Engineer',
                'description': 'Ensure software quality through comprehensive testing and automation.',
                'required_rank': 2,
                'competencies': [
                    ('Testing', 2),
                    ('Attention to Detail', 2),
                    ('Problem Solving', 1)
                ]
            },
            {
                'title': 'Database Administrator',
                'description': 'Manage and optimize database systems and ensure data security.',
                'required_rank': 3,
                'competencies': [
                    ('Database Management', 3),
                    ('Security', 2),
                    ('Problem Solving', 2)
                ]
            },
            {
                'title': 'Technical Writer',
                'description': 'Create clear and comprehensive technical documentation and user guides.',
                'required_rank': 2,
                'competencies': [
                    ('Technical Writing', 2),
                    ('Communication', 3),
                    ('Documentation', 2)
                ]
            },
            {
                'title': 'Cybersecurity Analyst',
                'description': 'Protect systems and networks from security threats and vulnerabilities.',
                'required_rank': 3,
                'competencies': [
                    ('Security', 3),
                    ('Problem Solving', 2),
                    ('Risk Assessment', 2)
                ]
            }
        ]

        try:
            for job in jobs:
                new_job = JobRole(
                    jobTitle=job['title'],
                    jobDescription=job['description'],
                    requiredRank=job['required_rank']
                )
                db.session.add(new_job)
                db.session.flush()  

                for comp_name, rank in job['competencies']:
                    comp = Competency.query.filter_by(name=comp_name).first()
                    if not comp:
                        comp = Competency(name=comp_name)
                        db.session.add(comp)
                        db.session.flush()

                    job_comp = JobCompetency(
                        jobID=new_job.jobID,
                        competencyID=comp.id,
                        requiredRank=rank
                    )
                    db.session.add(job_comp)

            db.session.commit()
            print("Sample jobs created successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating sample jobs: {str(e)}")

@dashboard_views.route('/job-matches')
@login_required
def job_matches():
    if current_user.user_type != 'student':
        flash('Only students can view job matches.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
        
    try:
        create_sample_jobs()
        
        student = Student.get_by_id(current_user.id)
        if not student:
            flash('Student account not found.', 'error')
            return redirect(url_for('dashboard_views.dashboard'))
        
        job_matches = JobRole.get_matching_jobs(student)
        
        return render_template('Html/jobMatches.html', 
                             job_matches=job_matches,
                             user=student)
                             
    except Exception as e:
        print(f"Error loading job matches: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading job matches.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))

@dashboard_views.route('/profile')
@login_required
def student_profile():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
        
    try:
        student = Student.get_by_id(current_user.id)
        if not student:
            flash('Student account not found.', 'error')
            return redirect(url_for('dashboard_views.dashboard'))
        
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
        
        # Get job matches (limited to top 3)
        create_sample_jobs()
        job_matches = JobRole.get_matching_jobs(student)[:3]
        
        return render_template('Html/studentProfile.html', 
                             user=student,
                             earned_competencies=earned_competencies,
                             workshops=enrolled_workshops,
                             job_matches=job_matches)
                             
    except Exception as e:
        print(f"Error loading profile: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading profile.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))

@dashboard_views.route('/update-profile-pic', methods=['POST'])
@login_required
def update_profile_pic():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        if 'profile_pic' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('dashboard_views.student_profile'))
        
        file = request.files['profile_pic']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('dashboard_views.student_profile'))
        
        if file and allowed_file(file.filename):
            # Create profile pics directory if it doesn't exist
            profile_pics_dir = 'App/static/profile_pics'
            if not os.path.exists(profile_pics_dir):
                os.makedirs(profile_pics_dir)
            
            # Generate unique filename
            filename = secure_filename(file.filename)
            # Add timestamp to prevent caching issues
            filename = f"{current_user.id}_{int(datetime.now().timestamp())}_{filename}"
            file_path = os.path.join(profile_pics_dir, filename)
            file.save(file_path)
            
            # Update student record
            student = Student.get_by_id(current_user.id)
            if student:
                # Delete old profile pic if exists
                if student.profile_pic:
                    old_pic_path = os.path.join(profile_pics_dir, student.profile_pic)
                    if os.path.exists(old_pic_path):
                        try:
                            os.remove(old_pic_path)
                        except:
                            pass
                
                # Update with new profile pic
                student.profile_pic = filename
                db.session.commit()
                flash('Profile picture updated successfully!', 'success')
            else:
                flash('Student record not found', 'error')
        else:
            flash('Invalid file type. Please upload an image file.', 'error')
    
    except Exception as e:
        print(f"Error updating profile picture: {e}")
        db.session.rollback()
        flash('An error occurred while updating profile picture.', 'error')
    
    return redirect(url_for('dashboard_views.student_profile'))

@dashboard_views.route('/update-resume', methods=['POST'])
@login_required
def update_resume():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        if 'resume' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('dashboard_views.student_profile'))
        
        file = request.files['resume']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('dashboard_views.student_profile'))
        
        # Create resumes directory if it doesn't exist
        resumes_dir = 'App/static/resumes'
        if not os.path.exists(resumes_dir):
            os.makedirs(resumes_dir)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        # Add timestamp to prevent caching issues
        filename = f"{current_user.id}_{int(datetime.now().timestamp())}_{filename}"
        file_path = os.path.join(resumes_dir, filename)
        file.save(file_path)
        
        # Update student record
        student = Student.get_by_id(current_user.id)
        if student:
            # Delete old resume if exists
            if student.resume:
                old_resume_path = os.path.join(resumes_dir, student.resume)
                if os.path.exists(old_resume_path):
                    try:
                        os.remove(old_resume_path)
                    except:
                        pass
            
            # Update with new resume
            student.resume = filename
            db.session.commit()
            flash('Resume updated successfully!', 'success')
        else:
            flash('Student record not found', 'error')
    
    except Exception as e:
        print(f"Error updating resume: {e}")
        db.session.rollback()
        flash('An error occurred while updating resume.', 'error')
    
    return redirect(url_for('dashboard_views.student_profile'))

@dashboard_views.route('/download-resume')
@login_required
def download_resume():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        student = Student.get_by_id(current_user.id)
        if not student or not student.resume:
            flash('Resume not found', 'error')
            return redirect(url_for('dashboard_views.student_profile'))
        
        # Prepare resume file path
        resumes_dir = 'App/static/resumes'
        file_path = os.path.join(resumes_dir, student.resume)
        
        if not os.path.exists(file_path):
            flash('Resume file not found', 'error')
            return redirect(url_for('dashboard_views.student_profile'))
        
        # Extract original filename from stored filename
        original_filename = student.resume.split('_', 2)[2] if len(student.resume.split('_', 2)) > 2 else student.resume
        
        # Return file for download
        return send_from_directory(
            os.path.abspath(resumes_dir),
            student.resume,
            as_attachment=True,
            download_name=original_filename
        )
    
    except Exception as e:
        print(f"Error downloading resume: {e}")
        flash('An error occurred while downloading resume.', 'error')
        return redirect(url_for('dashboard_views.student_profile'))

@dashboard_views.route('/update-personal-info', methods=['POST'])
@login_required
def update_personal_info():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        phone = request.form.get('phone', '')
        location = request.form.get('location', '')
        
        student = Student.get_by_id(current_user.id)
        if student:
            student.phone = phone
            student.location = location
            db.session.commit()
            flash('Personal information updated successfully!', 'success')
        else:
            flash('Student record not found', 'error')
            
    except Exception as e:
        print(f"Error updating personal information: {e}")
        db.session.rollback()
        flash('An error occurred while updating personal information.', 'error')
    
    return redirect(url_for('dashboard_views.student_profile'))

@dashboard_views.route('/view-candidate-profile/<int:student_id>')
@login_required
def view_candidate_profile(student_id):
    if current_user.user_type != 'employer':
        flash('Access denied. Employers only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
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
        return redirect(url_for('dashboard_views.search_candidates'))

def init_dashboard_routes(app):
    app.register_blueprint(dashboard_views) 