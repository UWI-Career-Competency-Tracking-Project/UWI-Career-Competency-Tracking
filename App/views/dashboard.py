from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
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

dashboard_views = Blueprint('dashboard_views', __name__, template_folder='../templates')

UPLOAD_FOLDER = 'App/static/workshop_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@dashboard_views.route('/dashboard')
@login_required
def dashboard():
    return render_template('Html/dashboard.html', user=current_user)

@dashboard_views.route('/workshops')
@login_required
def workshops():
    search_query = request.args.get('search', '').strip().lower()
    print("Accessing workshops route with search query:", search_query)
    
    try:
        all_workshops = Workshop.query.all()
        
        if search_query:
            filtered_workshops = []
            for workshop in all_workshops:
                # Check if search query matches name, description, instructor, location
                if (search_query in workshop.name.lower() or
                    search_query in workshop.description.lower() or
                    search_query in workshop.instructor.lower() or
                    search_query in workshop.location.lower() or
                    # Check if search query matches any competency
                    any(search_query in comp.lower() for comp in workshop.competencies)):
                    filtered_workshops.append(workshop)
            all_workshops = filtered_workshops
        
        print(f"Found {len(all_workshops)} workshops:")
        for workshop in all_workshops:
            print(f"- {workshop.name} (ID: {workshop.id})")
        
        return render_template('Html/studentsAvailableWorkshops.html', 
                             workshops=all_workshops,
                             search_query=search_query)
    except Exception as e:
        print(f"Error fetching workshops: {e}")
        import traceback
        print("Full traceback:", traceback.format_exc())
        flash('Error loading workshops.', 'error')
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
        
        enrollment.add_workshop_competencies()
        
        db.session.commit()
        flash('Successfully enrolled in workshop!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error enrolling in workshop: {e}")
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
            workshop.name = request.form['name']
            workshop.description = request.form['description']
            workshop.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            workshop.time = request.form['time']
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

def init_dashboard_routes(app):
    app.register_blueprint(dashboard_views) 