from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_from_directory, send_file
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
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from PyPDF2 import PdfReader, PdfWriter
from .dashboard_common import allowed_file, format_time_ago
from ..models.job_competency import JobCompetency
from ..models.competency import Competency
from flask_jwt_extended import create_access_token, set_access_cookies
from flask import make_response

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
        
        for comp_name, comp_data in student.competencies.items():
            if 'certificate_status' not in comp_data:
                student.competencies[comp_name]['certificate_status'] = None
            
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
        
        active_workshops = []
        completed_workshops = []
        
        for workshop in enrolled_workshops:
            enrollment = next((e for e in workshop.enrollments if e.student_id == student.id), None)
            if enrollment:
                if enrollment.completed:
                    completed_workshops.append(workshop)
                else:
                    active_workshops.append(workshop)
        
        print(f"Found {len(enrolled_workshops)} total workshops for student {student.username}")
        print(f"Active workshops: {len(active_workshops)}")
        print(f"Completed workshops: {len(completed_workshops)}")
        
        return render_template('Html/myWorkshops.html', 
                             workshops=enrolled_workshops,
                             active_workshops=active_workshops,
                             completed_workshops=completed_workshops,
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
        
        print("Created enrollment")
        
        notification_controller.create_admin_notification(
            message=f"{current_user.first_name} {current_user.last_name} has enrolled in {workshop.workshopName}",
            notification_type='enrollment',
            link=f"/workshop-enrollments/{workshop.workshopID}"
        )
        
        create_student_notification(
            student_id=current_user.id,
            message=f"You have successfully enrolled in {workshop.workshopName}",
            notification_type='enrollment_confirmation',
            link=f"/my-workshops"
        )
        
        # Note: Competencies will be added only after the admin marks the workshop as completed
        
        db.session.commit()
        flash('Successfully enrolled in workshop! Competencies will be added after workshop completion.', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error enrolling in workshop: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        flash('An error occurred while enrolling in the workshop.', 'error')
    
    return redirect(url_for('dashboard_views.workshops'))

@student_views.route('/earned-badges')
@login_required
def earned_badges():
    if current_user.user_type != 'student':
        flash('Only students can view their certificates.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
        
    try:
        student = Student.get_by_id(current_user.id)
        if not student:
            flash('Student account not found.', 'error')
            return redirect(url_for('dashboard_views.dashboard'))
            
        completed_workshops = Workshop.query.join(Enrollment).filter(
            Enrollment.student_id == student.id,
            Enrollment.completed == True,
            Enrollment.certificate_status == 'approved'
        ).all()
        
        return render_template('Html/earnedBadges.html', 
                             user=student,
                             completed_workshops=completed_workshops)
                             
    except Exception as e:
        print(f"Error loading certificates: {e}")
        flash('Error loading certificates.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))

@student_views.route('/view-certificate/<competency>')
@login_required
def view_certificate(competency):
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    student = Student.get_by_id(current_user.id)
    if not student or not student.competencies or competency not in student.competencies:
        flash('You do not have this competency.', 'error')
        return redirect(url_for('student_views.competencies'))
    
    comp_data = student.competencies.get(competency, {})
    if comp_data.get('certificate_status') != 'approved':
        flash('You do not have an approved certificate for this competency.', 'error')
        return redirect(url_for('student_views.competencies'))
    
    certificate_data = {
        'student_name': f"{student.first_name} {student.last_name}",
        'competency': competency,
        'rank': comp_data.get('rank', 3),
        'rank_name': ['Beginner', 'Intermediate', 'Advanced'][comp_data.get('rank', 3) - 1],
        'date_issued': comp_data.get('certificate_date', 'Not Available'),
        'certificate_id': f"COMP-{student.id}-{competency.replace(' ', '')}"
    }
    
    buffer = io.BytesIO()
    
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    background_path = os.path.join(base_dir, 'static', 'Images', 'certificate.png')
    medal_path = os.path.join(base_dir, 'static', 'Images', 'medal.png')
    
    from reportlab.lib.units import inch
    from reportlab.platypus.frames import Frame
    from reportlab.platypus.doctemplate import PageTemplate
    
    frame = Frame(
        0.75*inch,
        0.75*inch,
        9.5*inch,
        7*inch,
        leftPadding=0,
        bottomPadding=0,
        rightPadding=0,
        topPadding=0,
    )
    
    def firstPageTemplate(canvas, doc):
        if os.path.exists(background_path):
            canvas.saveState()
            canvas.drawImage(background_path, 0, 0, width=11*inch, height=8.5*inch)
            
            canvas.setFont('Helvetica', 8)
            canvas.setFillColorRGB(0.5, 0.5, 0.5)
            canvas.drawCentredString(5.5*inch, 0.4*inch, f"Certificate ID: {certificate_data['certificate_id']}")
            canvas.drawCentredString(5.5*inch, 0.25*inch, "© 2025 Career Competency Tracking System. All Rights Reserved.")
            
            if os.path.exists(medal_path):
                canvas.drawImage(medal_path, 4.5*inch, 1.5*inch, width=2*inch, height=2*inch)
            
            canvas.restoreState()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    page_template = PageTemplate(id='First', frames=frame, onPage=firstPageTemplate)
    doc.addPageTemplates([page_template])
    
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    try:
        elegant_title_font = 'Times-Bold'
        elegant_heading_font = 'Times-Bold'
        elegant_text_font = 'Times-Roman'
        student_name_font = 'Times-Italic'
    except:
        elegant_title_font = 'Helvetica-Bold'
        elegant_heading_font = 'Helvetica-Bold'
        elegant_text_font = 'Helvetica'
        student_name_font = 'Helvetica-Bold'
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName=elegant_title_font,
        fontSize=22,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=2
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        fontName=elegant_heading_font,
        fontSize=18,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=2
    )
    
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontName=elegant_heading_font,
        fontSize=16,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=2
    )
    
    student_name_style = ParagraphStyle(
        'StudentNameStyle',
        parent=styles['Heading2'],
        fontName=student_name_font,
        fontSize=24,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=4
    )
    
    competency_name_style = ParagraphStyle(
        'CompetencyNameStyle',
        parent=styles['Heading2'],
        fontName=elegant_heading_font,
        fontSize=18,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=2
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontName=elegant_text_font,
        fontSize=12,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=2
    )
    
    level_style = ParagraphStyle(
        'LevelStyle',
        parent=styles['Normal'],
        fontName=elegant_text_font,
        fontSize=16,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=1
    )
    
    content = []
    
    logo_path = os.path.join(base_dir, 'static', 'Images', 'logo.png')
    if os.path.exists(logo_path):
        img = Image(logo_path, width=1.5*inch, height=0.8*inch)
        img.hAlign = 'CENTER'
        content.append(img)
    
    content.append(Paragraph("CAREER COMPETENCY TRACKER", title_style))
    content.append(Paragraph("CERTIFICATE", title_style))
    content.append(Paragraph("of Achievement", subtitle_style))
    content.append(Spacer(1, 5))
    
    content.append(Paragraph("This Certificate is Presented To", normal_style))
    content.append(Paragraph(f"{certificate_data['student_name']}", student_name_style))
    content.append(Spacer(1, 5))
    content.append(Paragraph(f"For demonstrating proficiency in", normal_style))
    content.append(Paragraph(f"{certificate_data['competency']}", competency_name_style))
    content.append(Spacer(1, 10))
    
    content.append(Paragraph(f"{certificate_data['rank_name']} Level", level_style))
    content.append(Spacer(1, 15))
    
    date_style = ParagraphStyle(
        'DateStyle',
        parent=normal_style,
        fontSize=14,
        textColor=colors.navy,
        alignment=1
    )
    content.append(Paragraph(f"Date Issued: {certificate_data['date_issued']}", date_style))
    
    director_style = ParagraphStyle(
        'DirectorStyle',
        parent=normal_style,
        fontSize=14,
        textColor=colors.navy,
        alignment=1
    )
    
    content.append(Spacer(1, 20))
    content.append(Paragraph("Program Director", director_style))
    
    doc.build(content)
    
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{student.first_name}_{student.last_name}_{competency}_Certificate.pdf",
        mimetype='application/pdf'
    )

@student_views.route('/view-workshop-certificate/<workshop_id>')
@login_required
def view_workshop_certificate(workshop_id):
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    workshop = Workshop.query.get(workshop_id)
    if not workshop:
        flash('Workshop not found.', 'error')
        return redirect(url_for('student_views.my_workshops'))
    
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        workshop_id=workshop_id,
        completed=True
    ).first()
    
    if not enrollment:
        flash('You have not completed this workshop.', 'error')
        return redirect(url_for('student_views.my_workshops'))
    
    certificate_data = {
        'student_name': f"{current_user.first_name} {current_user.last_name}",
        'workshop_name': workshop.workshopName,
        'competencies': workshop.competencies,
        'date_completed': enrollment.completion_date.strftime('%B %d, %Y') if enrollment.completion_date else datetime.now().strftime('%B %d, %Y'),
        'instructor': workshop.instructor,
        'certificate_id': f"WS-{current_user.id}-{workshop.id}"
    }
    
    buffer = io.BytesIO()
    
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    background_path = os.path.join(base_dir, 'static', 'Images', 'certificate.png')
    medal_path = os.path.join(base_dir, 'static', 'Images', 'medal.png')
    
    from reportlab.lib.units import inch
    from reportlab.platypus.frames import Frame
    from reportlab.platypus.doctemplate import PageTemplate
    
    frame = Frame(
        0.75*inch,
        0.75*inch,
        9.5*inch,
        7*inch,
        leftPadding=0,
        bottomPadding=0,
        rightPadding=0,
        topPadding=0,
    )
    
    def firstPageTemplate(canvas, doc):
        if os.path.exists(background_path):
            canvas.saveState()
            canvas.drawImage(background_path, 0, 0, width=11*inch, height=8.5*inch)
            
            canvas.setFont('Helvetica', 8)
            canvas.setFillColorRGB(0.5, 0.5, 0.5)
            canvas.drawCentredString(5.5*inch, 0.4*inch, f"Certificate ID: {certificate_data['certificate_id']}")
            canvas.drawCentredString(5.5*inch, 0.25*inch, "© 2025 Career Competency Tracking System. All Rights Reserved.")
            
            if os.path.exists(medal_path):
                canvas.drawImage(medal_path, 4.5*inch, 1.5*inch, width=2*inch, height=2*inch)
            
            canvas.restoreState()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    page_template = PageTemplate(id='First', frames=frame, onPage=firstPageTemplate)
    doc.addPageTemplates([page_template])
    
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    try:
        elegant_title_font = 'Times-Bold'
        elegant_heading_font = 'Times-Bold'
        elegant_text_font = 'Times-Roman'
        student_name_font = 'Times-Italic'
    except:
        elegant_title_font = 'Helvetica-Bold'
        elegant_heading_font = 'Helvetica-Bold'
        elegant_text_font = 'Helvetica'
        student_name_font = 'Helvetica-Bold'
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName=elegant_title_font,
        fontSize=22,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=2
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        fontName=elegant_heading_font,
        fontSize=18,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=2
    )
    
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontName=elegant_heading_font,
        fontSize=16,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=2
    )
    
    student_name_style = ParagraphStyle(
        'StudentNameStyle',
        parent=styles['Heading2'],
        fontName=student_name_font,
        fontSize=24,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=4
    )
    
    workshop_name_style = ParagraphStyle(
        'WorkshopNameStyle',
        parent=styles['Heading2'],
        fontName=elegant_heading_font,
        fontSize=18,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=2
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontName=elegant_text_font,
        fontSize=12,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=2
    )
    
    competency_style = ParagraphStyle(
        'CompetencyStyle',
        parent=styles['Normal'],
        fontName=elegant_text_font,
        fontSize=14,
        textColor=colors.navy,
        alignment=1,
        spaceAfter=1
    )
    
    content = []
    
    logo_path = os.path.join(base_dir, 'static', 'Images', 'logo.png')
    if os.path.exists(logo_path):
        img = Image(logo_path, width=1.5*inch, height=0.8*inch)
        img.hAlign = 'CENTER'
        content.append(img)
    
    content.append(Paragraph("CAREER COMPETENCY TRACKER", title_style))
    content.append(Paragraph("CERTIFICATE", title_style))
    content.append(Paragraph("of Achievement", subtitle_style))
    content.append(Spacer(1, 5))
    
    content.append(Paragraph("This Certificate is Presented To", normal_style))
    content.append(Paragraph(f"{certificate_data['student_name']}", student_name_style))
    content.append(Spacer(1, 5))
    content.append(Paragraph("For the completion of the Workshop", normal_style))
    content.append(Paragraph(f"{certificate_data['workshop_name']}", workshop_name_style))
    content.append(Spacer(1, 10))
    
    content.append(Paragraph("Competencies Earned:", heading_style))
    content.append(Spacer(1, 5))
    
    if certificate_data['competencies']:
        if isinstance(certificate_data['competencies'], str):
            for comp in certificate_data['competencies'].split(','):
                content.append(Paragraph(comp.strip(), competency_style))
        else:
            for comp in certificate_data['competencies']:
                content.append(Paragraph(comp, competency_style))
    else:
        content.append(Paragraph("Workshop completion", competency_style))
    
    content.append(Spacer(1, 15))
    
    date_style = ParagraphStyle(
        'DateStyle',
        parent=normal_style,
        fontSize=14,
        textColor=colors.navy,
        alignment=1
    )
    content.append(Paragraph(f"Date: {certificate_data['date_completed']}", date_style))
    
    instructor_style = ParagraphStyle(
        'InstructorStyle',
        parent=normal_style,
        fontSize=14,
        textColor=colors.navy,
        alignment=1
    )
    
    content.append(Spacer(1, 20))
    content.append(Paragraph(f"Instructor: {certificate_data['instructor']}", instructor_style))
    
    doc.build(content)
    
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{current_user.first_name}_{current_user.last_name}_{workshop.workshopName}_Certificate.pdf",
        mimetype='application/pdf'
    )

@student_views.route('/job-matches')
@login_required
def job_matches():
    if current_user.user_type != 'student':
        flash('Only students can view job matches.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
        
    try:
        from ..models.job_roles import JobRole
        
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
        
        enrolled_workshops = Workshop.query.join(Enrollment).filter(
            Enrollment.student_id == student.id
        ).all()
        
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
        
        if not file or not allowed_file(file.filename):
            flash('Invalid file type. Please upload an image file (PNG, JPG, JPEG, GIF, WEBP, BMP, TIFF, or SVG).', 'error')
            return redirect(url_for('student_views.student_profile'))
            
        profile_pics_dir = 'App/static/profile_pics'
        if not os.path.exists(profile_pics_dir):
            os.makedirs(profile_pics_dir)
        
        filename = secure_filename(file.filename)
        filename = f"{current_user.id}_{int(datetime.now().timestamp())}_{filename}"
        file_path = os.path.join(profile_pics_dir, filename)
        file.save(file_path)
        
        student = Student.get_by_id(current_user.id)
        if student:
            if student.profile_pic:
                old_pic_path = os.path.join(profile_pics_dir, student.profile_pic)
                if os.path.exists(old_pic_path):
                    try:
                        os.remove(old_pic_path)
                    except Exception as e:
                        print(f"Error removing old profile picture: {e}")
            
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
        
        resumes_dir = 'App/static/resumes'
        if not os.path.exists(resumes_dir):
            os.makedirs(resumes_dir)
        
        filename = secure_filename(file.filename)
        filename = f"{current_user.id}_{int(datetime.now().timestamp())}_{filename}"
        file_path = os.path.join(resumes_dir, filename)
        file.save(file_path)
        
        student = Student.get_by_id(current_user.id)
        if student:
            if student.resume:
                old_resume_path = os.path.join(resumes_dir, student.resume)
                if os.path.exists(old_resume_path):
                    try:
                        os.remove(old_resume_path)
                    except:
                        pass
            
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
        
        resumes_dir = 'App/static/resumes'
        file_path = os.path.join(resumes_dir, student.resume)
        
        if not os.path.exists(file_path):
            flash('Resume file not found', 'error')
            return redirect(url_for('student_views.student_profile'))
        
        original_filename = student.resume.split('_', 2)[2] if len(student.resume.split('_', 2)) > 2 else student.resume
        
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
        
        resumes_dir = 'App/static/resumes'
        file_path = os.path.join(resumes_dir, student.resume)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted resume file: {file_path}")
            except Exception as file_error:
                print(f"Error deleting resume file: {file_error}")
        
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
            
            story.append(Paragraph(f"{student.first_name} {student.last_name}", title_style))
            contact_info = f"{student.email}"
            if student.phone:
                contact_info += f" | {student.phone}"
            if student.location:
                contact_info += f" | {student.location}"
            story.append(Paragraph(contact_info, normal_style))
            story.append(Spacer(1, 12))
            
            story.append(Paragraph("SUMMARY", heading_style))
            story.append(Paragraph(
                "A highly skilled individual with a diverse set of competencies and certifications from the UWI Career Competency Tracking System. "
                "Experienced in multiple areas with a focus on continuous professional development.",
                normal_style
            ))
            story.append(Spacer(1, 12))
            
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
            
            story.append(Paragraph("WORKSHOPS & TRAINING", heading_style))
            if enrolled_workshops:
                for workshop in enrolled_workshops:
                    enrollment = Enrollment.query.filter_by(
                        student_id=student.id,
                        workshop_id=workshop.id
                    ).first()
                    
                    workshop_text = f"<b>{workshop.workshopName}</b>"
                    
                    if enrollment and enrollment.certificate_status == 'approved':
                        workshop_text += " <i>(Certified)</i>"
                    
                    workshop_text += "<br/>"
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
            
            story.append(Paragraph("EDUCATION", heading_style))
            education_text = "<b>University of the West Indies</b><br/>"
            education_text += f"Degree Program: {student.degree or '[Student\'s Degree]'}<br/>"
            education_text += "Participated in the UWI Career Competency Tracking System to develop and validate professional skills."
            story.append(Paragraph(education_text, competency_style))
            
            story.append(Spacer(1, 12))
            
            story.append(Paragraph("ADDITIONAL INFORMATION", heading_style))
            story.append(Paragraph(
                "This resume was automatically generated based on verified competencies and completed workshops "
                "tracked through the UWI Career Competency Tracking System. All listed competencies have been "
                "validated by instructors and administrators.",
                normal_style
            ))
            
            doc.build(story)
            
            student.resume = filename
            db.session.commit()
            flash('Resume generated successfully!', 'success')
            
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
            
        enrolled_workshops = Workshop.query.join(Enrollment).filter(
            Enrollment.student_id == student.id
        ).all()
        
        resumes_dir = 'App/static/resumes'
        
        existing_resume_path = os.path.join(resumes_dir, student.resume)
        
        if not os.path.exists(existing_resume_path):
            flash('Existing resume file not found', 'error')
            return redirect(url_for('student_views.student_profile'))
        
        timestamp = int(datetime.now().timestamp())
        merged_filename = f"{student.id}_{timestamp}_enhanced_resume.pdf"
        competency_pdf_path = os.path.join(resumes_dir, f"temp_competency_{timestamp}.pdf")
        merged_file_path = os.path.join(resumes_dir, merged_filename)
        
        try:
            doc = SimpleDocTemplate(
                competency_pdf_path,
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
            
            story.append(Paragraph("COMPETENCY PROFILE", title_style))
            story.append(Paragraph(f"For {student.first_name} {student.last_name}", normal_style))
            story.append(Spacer(1, 12))
            
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
            
            story.append(Paragraph("WORKSHOPS & TRAINING", heading_style))
            if enrolled_workshops:
                for workshop in enrolled_workshops:
                    enrollment = Enrollment.query.filter_by(
                        student_id=student.id,
                        workshop_id=workshop.id
                    ).first()
                    
                    workshop_text = f"<b>{workshop.workshopName}</b>"
                    
                    if enrollment and enrollment.certificate_status == 'approved':
                        workshop_text += " <i>(Certified)</i>"
                    
                    workshop_text += "<br/>"
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
            
            story.append(Paragraph("CERTIFICATION", heading_style))
            story.append(Paragraph(
                "The above competencies have been verified by the UWI Career Competency Tracking System. "
                "This system tracks and validates skills acquired through formal workshops and training sessions.",
                normal_style
            ))
            
            doc.build(story)
            
            with open(existing_resume_path, 'rb') as file_original:
                original_pdf = PdfReader(file_original)
                
                with open(competency_pdf_path, 'rb') as file_competency:
                    competency_pdf = PdfReader(file_competency)
                    
                    merger = PdfWriter()
                    
                    for page in original_pdf.pages:
                        merger.add_page(page)
                    
                    for page in competency_pdf.pages:
                        merger.add_page(page)
                    
                    with open(merged_file_path, 'wb') as output_file:
                        merger.write(output_file)
            
            if os.path.exists(competency_pdf_path):
                os.remove(competency_pdf_path)
            
            old_resume_path = os.path.join(resumes_dir, student.resume)
            
            student.resume = merged_filename
            db.session.commit()
            
            if os.path.exists(old_resume_path) and old_resume_path != merged_file_path:
                try:
                    os.remove(old_resume_path)
                except Exception as file_error:
                    print(f"Warning: Could not delete old resume: {file_error}")
            
            flash('Your resume has been enhanced with your competencies and skills!', 'success')
            
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
def get_notifications():
    if not current_user.is_authenticated:
        return jsonify({'notifications': [], 'unread_count': 0})
    
    try:
        student_id = current_user.id
        notifications = notification_controller.get_notifications(student_id, limit=20)
        unread_count = notification_controller.get_unread_count(student_id)
        
        formatted_notifications = []
        for notif in notifications:
            if isinstance(notif.created_at, str):
                try:
                    created_at = datetime.fromisoformat(notif.created_at)
                except ValueError:
                    created_at = datetime.now()
            else:
                created_at = notif.created_at or datetime.now()
                
            formatted_notifications.append({
                'id': notif.id,
                'message': notif.message,
                'notification_type': notif.notification_type,
                'is_read': notif.is_read,
                'created_at': created_at.isoformat(),
                'link': notif.link
            })
        
        formatted_notifications.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'notifications': formatted_notifications,
            'unread_count': unread_count
        })
    except Exception as e:
        print(f"Error getting notifications: {e}")
        return jsonify({'error': str(e)}), 500

@student_views.route('/mark-notification-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    if current_user.user_type != 'student':
        return jsonify({'error': 'Access denied. Students only.'}), 403
    
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
        workshop_name = workshop.workshopName if workshop else "Unknown Workshop"
        
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
        
        notification_controller.create_admin_notification(
            message=f"{student.first_name} {student.last_name} has unenrolled from {workshop_name}",
            notification_type='unenrollment',
            link=f"/admin/workshop-attendance?workshop_id={workshop_id}"
        )
        
        create_student_notification(
            student_id=student.id,
            message=f"You have successfully unenrolled from {workshop_name}",
            notification_type='unenrollment_confirmation',
            link="/my-workshops"
        )
        
        db.session.commit()
        
        return jsonify({'message': 'Successfully unenrolled from workshop.'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 

def create_sample_jobs():
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

@student_views.route('/workshops')
@login_required
def workshops():
    if current_user.user_type != 'student':
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    return redirect(url_for('dashboard_views.workshops')) 

@student_views.route('/request-certificate', methods=['POST'])
@login_required
def request_certificate():
    if current_user.user_type != 'student':
        flash('Only students can request certificates.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        competency = request.form.get('competency')
        if not competency:
            flash('Invalid request. Please specify a competency.', 'error')
            return redirect(url_for('student_views.earned_badges'))
        
        student = Student.get_by_id(current_user.id)
        if not student or not student.competencies or competency not in student.competencies:
            flash('Competency not found or not earned.', 'error')
            return redirect(url_for('student_views.earned_badges'))
        
        comp_data = student.competencies.get(competency, {})
        rank = comp_data.get('rank', 0)
        
        if rank < 3:
            flash('You need to reach Advanced level to request a certificate.', 'error')
            return redirect(url_for('student_views.earned_badges'))
        
        student.competencies[competency]['certificate_status'] = 'pending'
        db.session.commit()
        
        notification_controller.create_admin_notification(
            message=f"Certificate request from {student.first_name} {student.last_name} for competency: {competency}",
            notification_type='certificate_request',
            link="/validate-certificates",
            related_id=student.id
        )
        
        flash('Certificate request submitted successfully. You will be notified when it is approved.', 'success')
        return redirect(url_for('student_views.earned_badges'))
        
    except Exception as e:
        print(f"Error requesting certificate: {e}")
        db.session.rollback()
        flash('An error occurred while requesting the certificate. Please try again.', 'error')
        return redirect(url_for('student_views.earned_badges'))

@student_views.route('/request-workshop-certificate', methods=['POST'])
@login_required
def request_workshop_certificate():
    if current_user.user_type != 'student':
        flash('Only students can request certificates.', 'error')
        return redirect(url_for('dashboard_views.dashboard'))
    
    try:
        workshop_id = request.form.get('workshop_id')
        if not workshop_id:
            flash('Invalid request. Please specify a workshop.', 'error')
            return redirect(url_for('student_views.my_workshops'))
        
        workshop = Workshop.query.get(workshop_id)
        if not workshop:
            flash('Workshop not found.', 'error')
            return redirect(url_for('student_views.my_workshops'))
        
        enrollment = Enrollment.query.filter_by(
            workshop_id=workshop_id,
            student_id=current_user.id
        ).first()
        
        if not enrollment or not enrollment.completed:
            flash('You must complete this workshop before requesting a certificate.', 'error')
            return redirect(url_for('student_views.my_workshops'))
        
        if enrollment.certificate_status == 'pending':
            flash('You have already requested a certificate for this workshop.', 'info')
            return redirect(url_for('student_views.my_workshops', tab='completed'))
            
        enrollment.certificate_status = 'pending'
        db.session.commit()
        
        notification_controller.create_admin_notification(
            message=f"Certificate request from {current_user.first_name} {current_user.last_name} for workshop: {workshop.workshopName}",
            notification_type='certificate_request',
            link=f"/validate-certificates?workshop_id={workshop_id}"
        )
        
        flash('Certificate request submitted successfully. You will be notified when it is approved.', 'success')
        return redirect(url_for('student_views.my_workshops', tab='completed'))
        
    except Exception as e:
        print(f"Error requesting certificate: {e}")
        flash('An error occurred while requesting the certificate. Please try again.', 'error')
        return redirect(url_for('student_views.my_workshops'))

def create_student_notification(student_id, message, notification_type, link=None):
    return notification_controller.create_notification(
        student_id=student_id,
        message=message,
        notification_type=notification_type,
        link=link
    )

def notify_certificate_approval(student_id, certificate_type, certificate_name):
    try:
        link = "/earned-badges"
        message = f"Your certificate for {certificate_name} has been approved!"
        
        notification_controller.create_notification(
            student_id=student_id,
            message=message,
            notification_type='certificate_approved',
            link=link
        )
        return True
    except Exception as e:
        print(f"Error creating certificate approval notification: {e}")
        return False 