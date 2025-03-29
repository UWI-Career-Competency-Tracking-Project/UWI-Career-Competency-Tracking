from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_from_directory
from flask_login import login_required, current_user
from ..models.workshop import Workshop
from ..models.enrollment import Enrollment
from ..models.student import Student
from ..models.notification import Notification
from ..models.certificate_request import CertificateRequest
from .. import db
from datetime import datetime
from sqlalchemy import or_, func, distinct
import os
from werkzeug.utils import secure_filename
from ..controllers import certificate_controller
from ..controllers import notification_controller
from ..models.job_roles import JobRole
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from PyPDF2 import PdfReader, PdfWriter
from .dashboard_common import allowed_file, format_time_ago
from ..models.job_competency import JobCompetency
from ..models.competency import Competency

student_views = Blueprint('student_views', __name__, template_folder='../templates')

@student_views.route('/student-dashboard')
@login_required
def student_dashboard():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    return render_template('Html/studentdashboard.html', user=current_user)

@student_views.route('/competencies')
@login_required
def competencies():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
        
    try:
        student = Student.get_by_id(current_user.id)
        if not student:
            flash('Student account not found.', 'error')
            return redirect(url_for('dashboard_views.dashboard'))
        
        # Format competencies data for display
        for comp_name, comp_data in student.competencies.items():
            # Ensure the certificate_status field exists
            if 'certificate_status' not in comp_data:
                student.competencies[comp_name]['certificate_status'] = None
            
            # Convert empty string to None for consistency
            if comp_data.get('certificate_status') == '':
                student.competencies[comp_name]['certificate_status'] = None
        
        return render_template('Html/competencies.html', user=student)
        
    except Exception as e:
        print(f"Error loading competencies: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading competencies.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))

@student_views.route('/my-workshops')
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

@student_views.route('/enroll-workshop/<workshop_id>')
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

@student_views.route('/request-certificate', methods=['POST'])
@login_required
def request_certificate():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        competency = request.form.get('competency')
        if not competency:
            flash('Invalid request.', 'error')
            return redirect(url_for('student_views.competencies'))
        
        student = Student.query.get(current_user.id)
        if not student:
            flash('Student not found.', 'error')
            return redirect(url_for('student_views.competencies'))
        
        if competency not in student.competencies:
            flash('Competency not found.', 'error')
            return redirect(url_for('student_views.competencies'))
            
        comp_data = student.competencies[competency]
        if comp_data.get('rank') != 3:
            flash('Certificate can only be requested for Advanced rank competencies.', 'error')
            return redirect(url_for('student_views.competencies'))
        
        success, message = certificate_controller.request_certificate(current_user.id, competency)
        
        if success:
            student.update_competency_certificate_status(competency, 'pending')
            flash('Certificate request submitted successfully.', 'success')
        else:
            flash(message, 'error')
            
        return redirect(url_for('student_views.competencies'))
        
    except Exception as e:
        print(f"Error in request_certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while processing your request.', 'error')
        return redirect(url_for('student_views.competencies'))

@student_views.route('/earned-badges')
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

@student_views.route('/view-certificate/<competency>')
@login_required
def view_certificate(competency):
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    certificate_data = certificate_controller.get_certificate_data(current_user.id, competency)
    if not certificate_data:
        flash('Certificate not found.', 'error')
        return redirect(url_for('student_views.competencies'))
    
    # Add user to certificate_data
    certificate_data['user'] = current_user
    
    return render_template('Html/studentCertificate.html', **certificate_data)

@student_views.route('/job-matches')
@login_required
def job_matches():
    if current_user.user_type != 'student':
        flash('Only students can view job matches.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
        
    try:
        # Import here to avoid circular imports
        from ..models.job_roles import JobRole
        
        # Create sample jobs
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

@student_views.route('/profile')
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
        # Create sample jobs
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

@student_views.route('/update-profile-pic', methods=['POST'])
@login_required
def update_profile_pic():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        if 'profile_pic' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('student_views.student_profile'))
        
        file = request.files['profile_pic']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('student_views.student_profile'))
        
        # Validate file type
        if not file or not allowed_file(file.filename):
            flash('Invalid file type. Please upload an image file (PNG, JPG, JPEG, GIF, WEBP, BMP, TIFF, or SVG).', 'error')
            return redirect(url_for('student_views.student_profile'))
            
        # Proceed with update if file is valid
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
                    except Exception as e:
                        print(f"Error removing old profile picture: {e}")
                        # Continue even if old file removal fails
            
            # Update with new profile pic
            student.profile_pic = filename
            db.session.commit()
            flash('Profile picture updated successfully!', 'success')
        else:
            flash('Student record not found', 'error')
    
    except Exception as e:
        print(f"Error updating profile picture: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        flash('An error occurred while updating profile picture.', 'error')
    
    return redirect(url_for('student_views.student_profile'))

@student_views.route('/update-resume', methods=['POST'])
@login_required
def update_resume():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        if 'resume' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('student_views.student_profile'))
        
        file = request.files['resume']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('student_views.student_profile'))
        
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
    
    return redirect(url_for('student_views.student_profile'))

@student_views.route('/download-resume')
@login_required
def download_resume():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        student = Student.get_by_id(current_user.id)
        if not student or not student.resume:
            flash('Resume not found', 'error')
            return redirect(url_for('student_views.student_profile'))
        
        # Prepare resume file path
        resumes_dir = 'App/static/resumes'
        file_path = os.path.join(resumes_dir, student.resume)
        
        if not os.path.exists(file_path):
            flash('Resume file not found', 'error')
            return redirect(url_for('student_views.student_profile'))
        
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
        return redirect(url_for('student_views.student_profile'))

@student_views.route('/remove-resume')
@login_required
def remove_resume():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        student = Student.get_by_id(current_user.id)
        if not student or not student.resume:
            flash('No resume to remove', 'error')
            return redirect(url_for('student_views.student_profile'))
        
        # Get resume file path
        resumes_dir = 'App/static/resumes'
        file_path = os.path.join(resumes_dir, student.resume)
        
        # Delete the file if it exists
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted resume file: {file_path}")
            except Exception as file_error:
                print(f"Error deleting resume file: {file_error}")
        
        # Update the student record
        student.resume = None
        db.session.commit()
        flash('Resume removed successfully', 'success')
        
    except Exception as e:
        print(f"Error removing resume: {e}")
        db.session.rollback()
        flash('An error occurred while removing the resume', 'error')
    
    return redirect(url_for('student_views.student_profile'))

@student_views.route('/generate-resume')
@login_required
def generate_resume():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        student = Student.get_by_id(current_user.id)
        if not student:
            flash('Student account not found.', 'error')
            return redirect(url_for('student_views.student_profile'))
        
        earned_competencies = []
        if student.competencies:
            for comp_name, comp_data in student.competencies.items():
                rank = comp_data.get('rank', 0)
                certificate_status = comp_data.get('certificate_status', None)
                
                if rank > 0:  
                    earned_competencies.append({
                        'name': comp_name,
                        'rank': rank,
                        'rank_name': ['Beginner', 'Intermediate', 'Advanced'][rank-1],
                        'certificate_status': certificate_status
                    })
        
        enrolled_workshops = Workshop.query.join(Enrollment).filter(
            Enrollment.student_id == student.id
        ).all()
        
        resumes_dir = 'App/static/resumes'
        if not os.path.exists(resumes_dir):
            os.makedirs(resumes_dir)
        
        timestamp = int(datetime.now().timestamp())
        filename = f"{student.id}_{timestamp}_generated_resume.pdf"
        file_path = os.path.join(resumes_dir, filename)
        
        try:
            doc = SimpleDocTemplate(
                file_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            heading_style = styles['Heading2']
            normal_style = styles['Normal']
            
            competency_style = ParagraphStyle(
                'CompetencyStyle',
                parent=styles['Normal'],
                spaceAfter=6,
                bulletIndent=0,
                leftIndent=0
            )
            
            story = []
            
            # Header
            story.append(Paragraph(f"{student.first_name} {student.last_name}", title_style))
            contact_info = f"{student.email}"
            if student.phone:
                contact_info += f" | {student.phone}"
            if student.location:
                contact_info += f" | {student.location}"
            story.append(Paragraph(contact_info, normal_style))
            story.append(Spacer(1, 12))
            
            # Summary
            story.append(Paragraph("SUMMARY", heading_style))
            story.append(Paragraph(
                "A highly skilled individual with a diverse set of competencies and certifications from the UWI Career Competency Tracking System. "
                "Experienced in multiple areas with a focus on continuous professional development.",
                normal_style
            ))
            story.append(Spacer(1, 12))
            
            # Competencies
            story.append(Paragraph("COMPETENCIES", heading_style))
            if earned_competencies:
                for comp in earned_competencies:
                    comp_text = f"<b>{comp['name']}</b>"
                    if comp.get('certificate_status') == 'approved':
                        comp_text += " (Certified)"
                    comp_text += f"<br/>Level: {comp['rank_name']}<br/>"
                    
                    if comp['rank'] == 1:
                        desc = f"Basic knowledge and understanding of {comp['name']} concepts."
                    elif comp['rank'] == 2:
                        desc = f"Practical application and intermediate knowledge of {comp['name']}."
                    else:
                        desc = f"Advanced expertise and comprehensive knowledge of {comp['name']} with demonstrated proficiency."
                    
                    comp_text += desc
                    story.append(Paragraph(comp_text, competency_style))
                    story.append(Spacer(1, 6))
            else:
                story.append(Paragraph("No competencies listed.", normal_style))
            
            story.append(Spacer(1, 12))
            
            # Workshops
            story.append(Paragraph("WORKSHOPS & TRAINING", heading_style))
            if enrolled_workshops:
                for workshop in enrolled_workshops:
                    workshop_text = f"<b>{workshop.workshopName}</b><br/>"
                    workshop_text += f"Date: {workshop.workshopDate.strftime('%B %d, %Y')} | "
                    workshop_text += f"Instructor: {workshop.instructor} | "
                    workshop_text += f"Location: {workshop.location}<br/>"
                    
                    if workshop.workshopDescription:
                        workshop_text += workshop.workshopDescription
                    
                    story.append(Paragraph(workshop_text, competency_style))
                    story.append(Spacer(1, 6))
            else:
                story.append(Paragraph("No workshops or training listed.", normal_style))
            
            story.append(Spacer(1, 12))
            
            # Education
            story.append(Paragraph("EDUCATION", heading_style))
            education_text = "<b>University of the West Indies</b><br/>"
            education_text += f"Degree Program: {student.degree or '[Student\'s Degree]'}<br/>"
            education_text += "Participated in the UWI Career Competency Tracking System to develop and validate professional skills."
            story.append(Paragraph(education_text, competency_style))
            
            story.append(Spacer(1, 12))
            
            # Additional Information
            story.append(Paragraph("ADDITIONAL INFORMATION", heading_style))
            story.append(Paragraph(
                "This resume was automatically generated based on verified competencies and completed workshops "
                "tracked through the UWI Career Competency Tracking System. All listed competencies have been "
                "validated by instructors and administrators.",
                normal_style
            ))
            
            # Build the PDF
            doc.build(story)
            
            # Update student record with generated resume
            student.resume = filename
            db.session.commit()
            flash('Resume generated successfully!', 'success')
            
            # Redirect to download the generated resume
            return redirect(url_for('student_views.download_resume'))
            
        except Exception as pdf_error:
            print(f"Error generating PDF: {pdf_error}")
            import traceback
            traceback.print_exc()
            flash('Error generating PDF resume.', 'error')
            return redirect(url_for('student_views.student_profile'))
        
    except Exception as e:
        print(f"Error generating resume: {e}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while generating resume.', 'error')
        return redirect(url_for('student_views.student_profile'))

@student_views.route('/merge-resume')
@login_required
def merge_resume():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        student = Student.get_by_id(current_user.id)
        if not student:
            flash('Student account not found.', 'error')
            return redirect(url_for('student_views.student_profile'))
        
        if not student.resume:
            flash('You need to upload a resume first before adding competencies to it.', 'error')
            return redirect(url_for('student_views.student_profile'))
        
        # Get earned competencies
        earned_competencies = []
        if student.competencies:
            for comp_name, comp_data in student.competencies.items():
                rank = comp_data.get('rank', 0)
                certificate_status = comp_data.get('certificate_status', None)
                
                if rank > 0:  
                    earned_competencies.append({
                        'name': comp_name,
                        'rank': rank,
                        'rank_name': ['Beginner', 'Intermediate', 'Advanced'][rank-1],
                        'certificate_status': certificate_status
                    })
        
        if not earned_competencies:
            flash('You do not have any competencies to add to your resume.', 'info')
            return redirect(url_for('student_views.student_profile'))
            
        # Get enrolled workshops
        enrolled_workshops = Workshop.query.join(Enrollment).filter(
            Enrollment.student_id == student.id
        ).all()
        
        # Resumes directory
        resumes_dir = 'App/static/resumes'
        
        # Get existing resume path
        existing_resume_path = os.path.join(resumes_dir, student.resume)
        
        if not os.path.exists(existing_resume_path):
            flash('Existing resume file not found', 'error')
            return redirect(url_for('student_views.student_profile'))
        
        # Generate unique filename for competency PDF and merged resume
        timestamp = int(datetime.now().timestamp())
        merged_filename = f"{student.id}_{timestamp}_enhanced_resume.pdf"
        competency_pdf_path = os.path.join(resumes_dir, f"temp_competency_{timestamp}.pdf")
        merged_file_path = os.path.join(resumes_dir, merged_filename)
        
        try:
            # 1. Generate PDF of just the competencies using ReportLab
            doc = SimpleDocTemplate(
                competency_pdf_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            heading_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # Custom styles
            competency_style = ParagraphStyle(
                'CompetencyStyle',
                parent=styles['Normal'],
                spaceAfter=6,
                bulletIndent=0,
                leftIndent=0
            )
            
            # Build PDF content
            story = []
            
            # Title
            story.append(Paragraph("COMPETENCY PROFILE", title_style))
            story.append(Paragraph(f"For {student.first_name} {student.last_name}", normal_style))
            story.append(Spacer(1, 12))
            
            # Competencies
            story.append(Paragraph("VERIFIED COMPETENCIES", heading_style))
            if earned_competencies:
                for comp in earned_competencies:
                    comp_text = f"<b>{comp['name']}</b>"
                    if comp.get('certificate_status') == 'approved':
                        comp_text += " (Certified)"
                    comp_text += f"<br/>Level: {comp['rank_name']}<br/>"
                    
                    if comp['rank'] == 1:
                        desc = f"Basic knowledge and understanding of {comp['name']} concepts."
                    elif comp['rank'] == 2:
                        desc = f"Practical application and intermediate knowledge of {comp['name']}."
                    else:
                        desc = f"Advanced expertise and comprehensive knowledge of {comp['name']} with demonstrated proficiency."
                    
                    comp_text += desc
                    story.append(Paragraph(comp_text, competency_style))
                    story.append(Spacer(1, 6))
            else:
                story.append(Paragraph("No competencies listed.", normal_style))
            
            story.append(Spacer(1, 12))
            
            # Workshops
            story.append(Paragraph("WORKSHOPS & TRAINING", heading_style))
            if enrolled_workshops:
                for workshop in enrolled_workshops:
                    workshop_text = f"<b>{workshop.workshopName}</b><br/>"
                    workshop_text += f"Date: {workshop.workshopDate.strftime('%B %d, %Y')} | "
                    workshop_text += f"Instructor: {workshop.instructor} | "
                    workshop_text += f"Location: {workshop.location}<br/>"
                    
                    if workshop.workshopDescription:
                        workshop_text += workshop.workshopDescription
                    
                    story.append(Paragraph(workshop_text, competency_style))
                    story.append(Spacer(1, 6))
            else:
                story.append(Paragraph("No workshops or training listed.", normal_style))
            
            story.append(Spacer(1, 12))
            
            # Certification
            story.append(Paragraph("CERTIFICATION", heading_style))
            story.append(Paragraph(
                "The above competencies have been verified by the UWI Career Competency Tracking System. "
                "This system tracks and validates skills acquired through formal workshops and training sessions.",
                normal_style
            ))
            
            # Build the PDF
            doc.build(story)
            
            # 2. Merge PDFs using PyPDF2
            with open(existing_resume_path, 'rb') as file_original:
                original_pdf = PdfReader(file_original)
                
                with open(competency_pdf_path, 'rb') as file_competency:
                    competency_pdf = PdfReader(file_competency)
                    
                    # Create a PDF writer
                    merger = PdfWriter()
                    
                    # Add all pages from both PDFs
                    for page in original_pdf.pages:
                        merger.add_page(page)
                    
                    for page in competency_pdf.pages:
                        merger.add_page(page)
                    
                    # Write the merged PDF to file
                    with open(merged_file_path, 'wb') as output_file:
                        merger.write(output_file)
            
            # Remove temporary competency PDF
            if os.path.exists(competency_pdf_path):
                os.remove(competency_pdf_path)
            
            # Save old resume path to delete it later
            old_resume_path = os.path.join(resumes_dir, student.resume)
            
            # Update student record with merged resume
            student.resume = merged_filename
            db.session.commit()
            
            # Delete old resume file if different from the new one
            if os.path.exists(old_resume_path) and old_resume_path != merged_file_path:
                try:
                    os.remove(old_resume_path)
                except Exception as file_error:
                    print(f"Warning: Could not delete old resume: {file_error}")
            
            flash('Your resume has been enhanced with your competencies and skills!', 'success')
            
            # Redirect to download the merged resume
            return redirect(url_for('student_views.download_resume'))
            
        except Exception as pdf_error:
            print(f"Error merging PDF: {pdf_error}")
            import traceback
            traceback.print_exc()
            flash('Error adding competencies to your resume.', 'error')
            return redirect(url_for('student_views.student_profile'))
        
    except Exception as e:
        print(f"Error merging resume: {e}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while enhancing your resume.', 'error')
        return redirect(url_for('student_views.student_profile'))

@student_views.route('/update-personal-info', methods=['POST'])
@login_required
def update_personal_info():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        phone = request.form.get('phone', '')
        location = request.form.get('location', '')
        degree = request.form.get('degree', '')
        
        student = Student.get_by_id(current_user.id)
        if student:
            student.phone = phone
            student.location = location
            student.degree = degree
            db.session.commit()
            flash('Personal information updated successfully!', 'success')
        else:
            flash('Student record not found', 'error')
            
    except Exception as e:
        print(f"Error updating personal information: {e}")
        db.session.rollback()
        flash('An error occurred while updating personal information.', 'error')
    
    return redirect(url_for('student_views.student_profile'))

@student_views.route('/get-notifications')
@login_required
def get_notifications():
    """
    Get notifications for the current user (API endpoint)
    """
    if current_user.user_type != 'student':
        return jsonify({'error': 'Access denied. Students only.'}), 403
    
    limit = request.args.get('limit', 10, type=int)
    unread_only = request.args.get('unread_only', False, type=bool)
    
    notifications = notification_controller.get_notifications(
        student_id=current_user.id,
        limit=limit,
        unread_only=unread_only
    )
    
    unread_count = notification_controller.get_unread_count(current_user.id)
    
    return jsonify({
        'notifications': [
            {
                'id': n.id,
                'message': n.message,
                'notification_type': n.notification_type,
                'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_read': n.is_read,
                'link': n.link
            } for n in notifications
        ],
        'unread_count': unread_count
    })

@student_views.route('/mark-notification-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """
    Mark a notification as read
    """
    if current_user.user_type != 'student':
        return jsonify({'error': 'Access denied. Students only.'}), 403
    
    # Ensure the notification belongs to the current user
    notification = Notification.query.get(notification_id)
    if not notification or notification.student_id != current_user.id:
        return jsonify({'error': 'Notification not found or unauthorized.'}), 404
    
    success = notification_controller.mark_as_read(notification_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Error marking notification as read.'}), 500

@student_views.route('/mark-all-notifications-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """
    Mark all notifications as read for the current user
    """
    if current_user.user_type != 'student':
        return jsonify({'error': 'Access denied. Students only.'}), 403
    
    count = notification_controller.mark_all_as_read(current_user.id)
    
    return jsonify({
        'success': True,
        'count': count
    })

@student_views.route('/unenroll-workshop/<workshop_id>', methods=['POST'])
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
                    from ..models.competency import Competency
                    from ..models.student_competency import StudentCompetency
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

def create_sample_jobs():
    """Create sample jobs if none exist"""
    from ..models.job_roles import JobRole
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

@student_views.route('/workshops')
@login_required
def workshops():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    # Redirect to the dashboard_views.workshops route
    return redirect(url_for('dashboard_views.workshops')) 