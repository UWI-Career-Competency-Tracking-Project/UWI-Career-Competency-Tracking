from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from ..models.workshop import Workshop
from ..models.enrollment import Enrollment
from ..models.student import Student
from ..models.notification import Notification
from ..models.certificate_request import CertificateRequest
from ..models.certificate import Certificate
from .. import db
from datetime import datetime
from sqlalchemy import or_, func, distinct
from sqlalchemy.orm.attributes import flag_modified
import os
from werkzeug.utils import secure_filename
from ..controllers import certificate_controller
from ..controllers import notification_controller
from ..models.job_roles import JobRole
from ..models.job_competency import JobCompetency
from ..models.competency import Competency
from dateutil.relativedelta import relativedelta
from .dashboard_common import allowed_file, format_time_ago
from ..models.student_competency import StudentCompetency

admin_views = Blueprint('admin_views', __name__, template_folder='../templates')

@admin_views.route('/admin-dashboard')
@login_required
def admin_dashboard():
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        workshop_count = db.session.query(Workshop).count()
        student_count = db.session.query(Student).count()
        
        badge_count = 0
        certificate_count = 0  
        competency_counts = {}
        
        students = Student.query.all()
        recent_activities = []
        
        all_workshops = Workshop.query.all()
        for workshop in all_workshops:
            if workshop.competencies:
                for comp_name in workshop.competencies:
                    if comp_name in competency_counts:
                        competency_counts[comp_name] += 1
                    else:
                        competency_counts[comp_name] = 1
        
        enrollments = db.session.query(Enrollment).filter_by(completed=True, certificate_status='approved').all()
        certificate_count = len(enrollments)
        
        for enrollment in enrollments[:5]:
            student = Student.query.get(enrollment.student_id)
            workshop = Workshop.query.get(enrollment.workshop_id)
            if student and workshop:
                recent_activities.append({
                    'type': 'certificate',
                    'icon': 'fas fa-certificate',
                    'title': f"Certificate issued to {student.first_name} for {workshop.workshopName}",
                    'time': format_time_ago(enrollment.completion_date or datetime.now())
                })
        
        for student in students:
            if student.competencies:
                for comp_name, comp_data in student.competencies.items():
                    rank = comp_data.get('rank', 0)
                    if rank > 0:
                        badge_count += 1
                        
                        rank_name = "Beginner" if rank == 1 else "Intermediate" if rank == 2 else "Advanced"
                        recent_activities.append({
                            'type': 'badge',
                            'icon': 'fas fa-award',
                            'title': f"{student.first_name} earned {comp_name} Badge ({rank_name})",
                            'time': format_time_ago(comp_data.get('updated_at', datetime.now()))
                        })
        
        recent_workshops = Workshop.query.order_by(Workshop.workshopDate.desc()).limit(5).all()
        for workshop in recent_workshops:
            recent_activities.append({
                'type': 'workshop',
                'icon': 'fas fa-chalkboard-teacher',
                'title': f"New Workshop: {workshop.workshopName}",
                'time': format_time_ago(workshop.created_at or datetime.now())
            })
        
        if recent_activities:
            try:
                def get_activity_time_weight(activity):
                    time_str = activity.get('time', '')
                    
                    weight = 1000
                    
                    if 'minute' in time_str or 'minutes' in time_str:
                        try:
                            minutes = int(time_str.split(' ')[0])
                            weight = minutes
                        except (ValueError, IndexError):
                            pass
                    elif 'hour' in time_str or 'hours' in time_str:
                        try:
                            hours = int(time_str.split(' ')[0])
                            weight = hours * 60
                        except (ValueError, IndexError):
                            pass
                    elif 'day' in time_str or 'days' in time_str:
                        try:
                            days = int(time_str.split(' ')[0])
                            weight = days * 24 * 60
                        except (ValueError, IndexError):
                            pass
                    
                    return weight
                
                recent_activities = sorted(recent_activities, key=get_activity_time_weight)[:5]
            except Exception as e:
                print(f"Error sorting activities: {e}")
                recent_activities = recent_activities[:5]
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        months = []
        for i in range(12):
            month_date = datetime.now() - relativedelta(months=11-i)
            months.append(month_date.strftime("%b"))
        
        workshop_creation_data = [0] * 12
        if workshop_count > 0:
            workshop_creation_data[-1] = workshop_count  
        
        competency_labels = list(competency_counts.keys())
        competency_data = list(competency_counts.values())
        
        badges_earned_data = [0] * 12
        if badge_count > 0:
            badges_earned_data[-1] = badge_count
        
        certificates_issued_data = [0] * 12
        if certificate_count > 0:
            certificates_issued_data[-1] = certificate_count
        
        print(f"Dashboard statistics: Workshops={workshop_count}, Students={student_count}, Badges={badge_count}, Certificates={certificate_count}")
        print(f"Competency distribution: {competency_counts}")
        
        return render_template(
            'Html/admindashboard.html', 
            user=current_user,
            workshop_count=workshop_count,
            student_count=student_count,
            badge_count=badge_count,
            certificate_count=certificate_count,
            recent_activities=recent_activities,
            workshop_trends_labels=months,
            workshop_creation_data=workshop_creation_data,
            workshop_attendance_data=[0] * 12,  
            competency_labels=competency_labels,
            competency_data=competency_data,
            progress_labels=months,
            badges_earned_data=badges_earned_data,
            certificates_issued_data=certificates_issued_data
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error loading dashboard data: {str(e)}', 'error')
        
        return render_template(
            'Html/admindashboard.html',
            user=current_user,
            workshop_count=0,
            student_count=0,
            badge_count=0,
            certificate_count=0,
            recent_activities=[],
            workshop_trends_labels=["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
            workshop_creation_data=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            workshop_attendance_data=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            competency_labels=[],
            competency_data=[],
            progress_labels=["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
            badges_earned_data=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            certificates_issued_data=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        )

@admin_views.route('/admin-workshop-creation/', methods=['GET', 'POST'])
@login_required
def admin_workshop_creation():
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    if request.method == 'POST':
        try:
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
                    else:
                        flash('Invalid file type. Please upload an image file.', 'error')
                        return redirect(request.url)

            competencies = []
            if 'competencies[]' in request.form:
                competencies = request.form.getlist('competencies[]')
            elif 'competencies' in request.form:
                competencies = request.form.getlist('competencies')
            else:
                for key in request.form:
                    if key.startswith('competencies'):
                        competencies = [request.form[key]]
                        break
            
            if len(competencies) == 1 and ',' in competencies[0]:
                competencies = [comp.strip() for comp in competencies[0].split(',') if comp.strip()]
                
            new_workshop = Workshop(
                workshopID=request.form['id'],
                workshopName=request.form['name'],
                workshopDescription=request.form['description'],
                workshopDate=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
                workshopTime=request.form['time'],
                instructor=request.form['instructor'],
                location=request.form['location'],
                image_path=image_path,
                competencies=competencies,
                created_at=datetime.now()
            )
            
            db.session.add(new_workshop)
            db.session.commit()
            
            students = Student.query.all()
            student_ids = [student.id for student in students]
            
            if student_ids:
                workshop_link = url_for('dashboard_views.workshops', _external=True)
                notification_controller.create_workshop_notification(
                    student_ids=student_ids,
                    workshop_name=new_workshop.workshopName,
                    action_type='created',
                    link=workshop_link
                )
            
            flash('Workshop created successfully!', 'success')
            return redirect(url_for('admin_views.manage_workshops'))
            
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            flash(f'Error creating workshop: {str(e)}', 'error')
            
    return render_template('Html/adminWorkshopCreation.html', user=current_user)

@admin_views.route('/manage-workshops')
@login_required
def manage_workshops():
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    workshops = Workshop.query.order_by(Workshop.workshopDate.desc()).all()
    return render_template('Html/manageWorkshops.html', workshops=workshops, user=current_user)

@admin_views.route('/workshop-enrollments/<workshop_id>')
@login_required
def workshop_enrollments(workshop_id):
    """View all students enrolled in a workshop"""
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
        
    workshop = Workshop.query.filter_by(workshopID=workshop_id).first_or_404()
    
    enrollments = Enrollment.query.filter_by(workshop_id=workshop.id).all()
    enrolled_students = []
    
    for enrollment in enrollments:
        student = Student.query.get(enrollment.student_id)
        if student:
            enrolled_students.append({
                'student': student,
                'enrollment': enrollment
            })
    
    months = []
    for i in range(12):
        month_date = datetime.now() - relativedelta(months=11-i)
        months.append(month_date.strftime("%b"))
    
    return render_template(
        'Html/workshop_enrollments.html',
        workshop=workshop,
        enrolled_students=enrolled_students,
        user=current_user,
        workshop_count=0,
        student_count=0,
        badge_count=0,
        certificate_count=0,
        recent_activities=[],
        workshop_trends_labels=months,
        workshop_creation_data=[0] * 12,
        workshop_attendance_data=[0] * 12,
        competency_labels=[],
        competency_data=[],
        progress_labels=months,
        badges_earned_data=[0] * 12,
        certificates_issued_data=[0] * 12
    )

@admin_views.route('/mark-workshop-completion/<int:enrollment_id>', methods=['POST'])
@login_required
def mark_workshop_completion(enrollment_id):
    """Mark a student as having completed a workshop"""
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    action = request.form.get('action')
    
    try:
        if action == 'complete':
            # Mark as completed and add competencies
            enrollment.mark_completed()
            
            # Send notification to student
            from ..controllers import notification_controller
            workshop = Workshop.query.get(enrollment.workshop_id)
            student = Student.query.get(enrollment.student_id)
            
            if workshop and student:
                badge_link = url_for('student_views.earned_badges', _external=True)
                notification_controller.create_notification(
                    student_id=enrollment.student_id,
                    message=f"Workshop Completed: {workshop.workshopName}. You have successfully completed the workshop '{workshop.workshopName}' and earned competencies.",
                    notification_type='workshop_completion',
                    link=badge_link
                )
            
            return jsonify({
                'success': True, 
                'message': 'Student marked as completed',
                'status': 'completed'
            })
            
        elif action == 'uncomplete':
            enrollment.mark_not_completed()
            return jsonify({
                'success': True, 
                'message': 'Completion status removed',
                'status': enrollment.status
            })
            
        else:
            return jsonify({'error': 'Invalid action'}), 400
            
    except Exception as e:
        db.session.rollback()
        print(f"Error marking completion: {e}")
        return jsonify({'error': str(e)}), 500

@admin_views.route('/mark-workshop-attendance/<int:enrollment_id>', methods=['POST'])
@login_required
def mark_workshop_attendance(enrollment_id):
    """Mark a student as having attended a workshop"""
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    action = request.form.get('action')
    
    try:
        if action == 'mark':
            # Mark as attended
            enrollment.mark_attended()
            
            # Send notification to student
            from ..controllers import notification_controller
            workshop = Workshop.query.get(enrollment.workshop_id)
            
            if workshop:
                notification_controller.track_workshop_attendance(
                    workshop_id=enrollment.workshop_id,
                    student_id=enrollment.student_id,
                    attended=True
                )
            
            return jsonify({
                'success': True, 
                'message': 'Student marked as attended',
                'status': enrollment.status
            })
            
        elif action == 'unmark':
            enrollment.mark_not_attended()
            return jsonify({
                'success': True, 
                'message': 'Attendance status removed',
                'status': enrollment.status
            })
            
        else:
            return jsonify({'error': 'Invalid action'}), 400
            
    except Exception as e:
        db.session.rollback()
        print(f"Error marking attendance: {e}")
        return jsonify({'error': str(e)}), 500

@admin_views.route('/edit-workshop/<workshop_id>', methods=['GET', 'POST'])
@login_required
def edit_workshop(workshop_id):
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
        
    workshop = Workshop.query.filter_by(workshopID=workshop_id).first_or_404()
    
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
            
            competencies = []
            if 'competencies[]' in request.form:
                competencies = request.form.getlist('competencies[]')
            elif 'competencies' in request.form:
                competencies = request.form.getlist('competencies')
            
            if not competencies and request.form.get('competencies'):
                competencies = [comp.strip() for comp in request.form.get('competencies').split(',') if comp.strip()]
            
            if competencies:
                workshop.competencies = competencies
            
            db.session.commit()
            
            students = Student.query.all()
            student_ids = [student.id for student in students]
            
            if student_ids:
                workshop_link = url_for('dashboard_views.workshops', _external=True)
                notification_controller.create_workshop_notification(
                    student_ids=student_ids,
                    workshop_name=workshop.workshopName,
                    action_type='updated',
                    link=workshop_link
                )
            
            flash('Workshop updated successfully!', 'success')
            return redirect(url_for('admin_views.manage_workshops'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error updating workshop: {e}")
            flash(f'Error updating workshop: {str(e)}', 'error')
            
    return render_template('Html/editWorkshop.html', workshop=workshop, user=current_user)

@admin_views.route('/delete-workshop/<workshop_id>', methods=['DELETE'])
@login_required
def delete_workshop(workshop_id):
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    workshop = Workshop.query.filter_by(workshopID=workshop_id).first_or_404()
    
    if workshop.enrollments:
        return jsonify({'error': 'Cannot delete workshop with enrolled students'}), 400
        
    try:
        db.session.delete(workshop)
        db.session.commit()
        return jsonify({'message': 'Workshop deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_views.route('/admin-badges', methods=['GET', 'POST'])
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
                return redirect(url_for('admin_views.admin_badges'))
            
            student = Student.query.get(student_id)
            if student:
                rank = int(rank)
                if rank not in [1, 2, 3]:
                    flash('Invalid rank selected', 'error')
                    return redirect(url_for('admin_views.admin_badges'))
                
                print(f"Updating student competency - Before update: {student.competencies.get(competency)}")
                student.update_competency_rank(competency, rank, feedback)
                print(f"After update: {student.competencies.get(competency)}")
                
                badge_link = url_for('student_views.earned_badges', _external=True)
                notification_controller.create_badge_notification(
                    student_id=student_id,
                    competency_name=competency,
                    rank=rank,
                    link=badge_link
                )
                
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
                         search_query=search_query,
                         user=current_user)

@admin_views.route('/validate-certificates')
@login_required
def validate_certificates():
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    pending_requests = certificate_controller.get_pending_requests()
    return render_template('Html/adminValidatecomp.html', pending_requests=pending_requests, user=current_user)

@admin_views.route('/process-certificate-request/<int:request_id>', methods=['POST'])
@login_required
def process_certificate_request(request_id):
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    action = request.form.get('action')
    if action not in ['approve', 'deny']:
        flash('Invalid action.', 'error')
        return redirect(url_for('admin_views.validate_certificates'))
    
    success, message = certificate_controller.process_request(request_id, action)
    
    if success:
        # Get the enrollment that was just processed
        enrollment = Enrollment.query.get(request_id)
        if enrollment:
            # Get the workshop details
            workshop = Workshop.query.get(enrollment.workshop_id)
            if workshop:
                # Create a notification for the student using controller
                certificate_link = url_for('student_views.earned_badges', _external=True)
                notification_controller.create_certificate_notification(
                    student_id=enrollment.student_id,
                    competency_name=workshop.workshopName,
                    status=action,  # This will be 'approve' or 'deny'
                    link=certificate_link
                )
        
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin_views.validate_certificates'))

@admin_views.route('/process-competency-certificate/<int:request_id>', methods=['POST'])
@login_required
def process_competency_certificate(request_id):
    if current_user.user_type != 'admin':
        flash('Access denied. Administrators only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    action = request.form.get('action')
    if action not in ['approve', 'deny']:
        flash('Invalid action.', 'error')
        return redirect(url_for('admin_views.validate_certificates'))
    
    success, message = certificate_controller.process_competency_request(request_id, action)
    
    if success:
        cert_request = CertificateRequest.query.get(request_id)
        if cert_request:
            certificate_link = url_for('student_views.earned_badges', _external=True)
            notification_controller.create_certificate_notification(
                student_id=cert_request.student_id,
                competency_name=cert_request.competency,
                status=action,  
                link=certificate_link
            )
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_views.validate_certificates'))

@admin_views.route('/test-notification/<int:student_id>/<notification_type>')
def test_notification(student_id, notification_type):
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': f'Student with ID {student_id} not found'}), 404
        
        if notification_type == 'workshop':
            notification = notification_controller.create_workshop_notification(
                student_id, 
                workshop_name="Test Workshop", 
                action_type="created", 
                link="/my-workshops"
            )
            return jsonify({'success': True, 'message': f'Created workshop notification for student {student_id}'})
            
        elif notification_type == 'badge':
            notification = notification_controller.create_badge_notification(
                student_id, 
                competency_name="Test Competency", 
                rank=2, 
                link="/earned-badges"
            )
            return jsonify({'success': True, 'message': f'Created badge notification for student {student_id}'})
            
        elif notification_type == 'certificate':
            notification = notification_controller.create_certificate_notification(
                student_id, 
                competency_name="Test Competency", 
                status="approved", 
                link="/earned-badges"
            )
            return jsonify({'success': True, 'message': f'Created certificate notification for student {student_id}'})
            
        else:
            notification = notification_controller.create_notification(
                student_id=student_id,
                message=f"This is a test {notification_type} notification",
                notification_type="general",
                link="/student-dashboard"
            )
            return jsonify({'success': True, 'message': f'Created generic notification for student {student_id}'})
            
    except Exception as e:
        return jsonify({'error': f'Error creating notification: {str(e)}'}), 500

def create_sample_jobs():
    """Create sample jobs if none exist"""
    if JobRole.query.count() == 0:
        jobs = [
            {
                'title': 'Software Developer',
                'description': 'Design and develop software applications using modern technologies.',
                'required_rank': 2,  
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
                'required_rank': 3,  
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

UPLOAD_FOLDER = 'App/static/workshop_images'

@admin_views.route('/get-admin-notifications')
def get_admin_notifications():
    try:
        if not current_user.is_authenticated:
            return jsonify({'notifications': [], 'unread_count': 0})
        
        if current_user.user_type != 'admin':
            return jsonify({'notifications': [], 'unread_count': 0})
        
        try:
            notifications = notification_controller.get_admin_notifications(limit=20)
            unread_count = notification_controller.get_admin_unread_count()
            
            formatted_notifications = []
            for notif in notifications:
                if not notif.created_at:
                    created_at = datetime.now().isoformat()
                elif isinstance(notif.created_at, str):
                    try:
                        created_at = datetime.fromisoformat(notif.created_at).isoformat()
                    except ValueError:
                        created_at = datetime.now().isoformat()
                else:
                    created_at = notif.created_at.isoformat()
                
                formatted_notifications.append({
                    'id': notif.id,
                    'message': notif.message,
                    'notification_type': notif.notification_type,
                    'is_read': notif.is_read,
                    'created_at': created_at,
                    'link': notif.link
                })
            
            return jsonify({
                'notifications': formatted_notifications,
                'unread_count': unread_count
            })
            
        except Exception as e:
            print(f"Error getting admin notifications: {e}")
            return jsonify({'notifications': [], 'unread_count': 0})
    except Exception as e:
        print(f"Critical error in get_admin_notifications: {e}")
        return jsonify({'notifications': [], 'unread_count': 0})

@admin_views.route('/mark-admin-notification-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_admin_notification_read(notification_id):
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Access denied. Administrators only.'}), 403
    
    try:
        success = notification_controller.mark_as_read(notification_id)
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return jsonify({'error': str(e)}), 500

@admin_views.route('/mark-all-admin-notifications-read', methods=['POST'])
@login_required
def mark_all_admin_notifications_read():
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Access denied. Administrators only.'}), 403
    
    try:
        count = notification_controller.mark_all_as_read(user_type='admin')
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        return jsonify({'error': str(e)}), 500 