from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_from_directory, make_response, send_file
from flask_login import login_required, current_user
from ..models.workshop import Workshop
from ..models.enrollment import Enrollment
from ..models.student import Student
from ..models.employer import Employer
from .. import db
from sqlalchemy import or_, func, distinct
import os
import io
from flask_jwt_extended import create_access_token, set_access_cookies
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.platypus import Table, TableStyle
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate

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
        
        enrolled_workshops = Workshop.query.join(Enrollment).filter(
            Enrollment.student_id == student.id
        ).all()
        
        certified_workshops = Workshop.query.join(Enrollment).filter(
            Enrollment.student_id == student.id,
            Enrollment.completed == True,
            Enrollment.certificate_status == 'approved'
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
        
        return render_template('Html/viewCandidateProfile.html', 
                              student=student,
                              earned_competencies=earned_competencies,
                              workshops=enrolled_workshops,
                              certified_workshops=certified_workshops,
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
        
        resumes_dir = 'App/static/resumes'
        file_path = os.path.join(resumes_dir, student.resume)
        
        if not os.path.exists(file_path):
            flash('Resume file not found', 'error')
            return redirect(url_for('employer_views.view_candidate_profile', student_id=student_id))
        
        original_filename = student.resume.split('_', 2)[2] if len(student.resume.split('_', 2)) > 2 else student.resume
        
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

@employer_views.route('/view-student-certificate/<int:student_id>/<competency>')
@login_required
def view_student_certificate(student_id, competency):
    if current_user.user_type != 'employer':
        flash('Access denied. Employers only.', 'error')
        return redirect(url_for('employer_views.employer_dashboard'))
    
    try:
        student = Student.query.get_or_404(student_id)
        
        if not student.competencies or competency not in student.competencies:
            flash('Certificate not found for this student.', 'error')
            return redirect(url_for('employer_views.view_candidate_profile', student_id=student_id))
        
        comp_data = student.competencies.get(competency, {})
        if comp_data.get('certificate_status') != 'approved':
            flash('Certificate not available or not approved.', 'error')
            return redirect(url_for('employer_views.view_candidate_profile', student_id=student_id))
        
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
                              
    except Exception as e:
        print(f"Error generating competency certificate PDF: {e}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while generating the certificate.', 'error')
        return redirect(url_for('employer_views.view_candidate_profile', student_id=student_id))

@employer_views.route('/view-student-workshop-certificate/<int:student_id>/<int:workshop_id>')
@login_required
def view_student_workshop_certificate(student_id, workshop_id):
    if current_user.user_type != 'employer':
        flash('Access denied. Employers only.', 'error')
        return redirect(url_for('employer_views.employer_dashboard'))
    
    try:
        student = Student.query.get_or_404(student_id)
        workshop = Workshop.query.get_or_404(workshop_id)
        
        enrollment = Enrollment.query.filter_by(
            student_id=student_id,
            workshop_id=workshop_id,
            certificate_status='approved'
        ).first()
        
        if not enrollment:
            flash('Certificate not found or not approved for this workshop.', 'error')
            return redirect(url_for('employer_views.view_candidate_profile', student_id=student_id))
        
        certificate_data = {
            'student_name': f"{student.first_name} {student.last_name}",
            'workshop_name': workshop.workshopName,
            'competencies': workshop.competencies,
            'date_completed': enrollment.completion_date.strftime('%B %d, %Y') if enrollment.completion_date else workshop.workshopDate.strftime('%B %d, %Y'),
            'instructor': workshop.instructor,
            'certificate_id': f"WS-{student.id}-{workshop.id}"
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
            # Fall back to defaults
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
            download_name=f"{student.first_name}_{student.last_name}_{workshop.workshopName}_Certificate.pdf",
            mimetype='application/pdf'
        )
                              
    except Exception as e:
        print(f"Error generating workshop certificate PDF: {e}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while generating the workshop certificate.', 'error')
        return redirect(url_for('employer_views.view_candidate_profile', student_id=student_id)) 

@employer_views.route('/get-competencies')
@login_required
def get_competencies():
    """Returns a list of all competencies in the system for autocomplete"""
    if not current_user.is_authenticated or current_user.user_type != 'employer':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        students = Student.query.all()
        all_competencies = set()
        
        for student in students:
            if student.competencies:
                for comp_name in student.competencies:
                    all_competencies.add(comp_name)
        
        return jsonify({'competencies': sorted(list(all_competencies))})
    except Exception as e:
        print(f"Error getting competencies: {e}")
        return jsonify({'error': str(e)}), 500 