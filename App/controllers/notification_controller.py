from App.models.notification import Notification
from App.models.student import Student
from App import db
from datetime import datetime
from sqlalchemy import desc
from flask import flash
from App.models.workshop import Workshop
from App.models.enrollment import Enrollment

def create_notification(student_id, message, notification_type, link=None):
    try:
        notification = Notification(
            student_id=student_id,
            message=message,
            notification_type=notification_type,
            link=link,
            created_at=datetime.now(),
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        print(f"Created notification for student {student_id}: {message}")
        return notification
    except Exception as e:
        db.session.rollback()
        print(f"Error creating notification: {e}")
        flash(f"Error creating notification: {str(e)}", "error")
        return None

def get_notifications(student_id, limit=10, unread_only=False):
    query = Notification.query.filter_by(student_id=student_id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    return query.order_by(desc(Notification.created_at)).limit(limit).all()

def get_unread_count(student_id):
    return Notification.query.filter_by(student_id=student_id, is_read=False).count()

def mark_as_read(notification_id):
    try:
        notification = Notification.query.get(notification_id)
        if notification:
            notification.is_read = True
            db.session.add(notification)
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"Error marking notification as read: {str(e)}")
        db.session.rollback()
        return False

def mark_all_as_read(student_id):
    try:
        notifications = Notification.query.filter_by(student_id=student_id, is_read=False).all()
        count = 0
        for notification in notifications:
            notification.is_read = True
            db.session.add(notification)
            count += 1
        
        db.session.commit()
        return count
    except Exception as e:
        print(f"Error marking all notifications as read: {str(e)}")
        db.session.rollback()
        return 0

def create_workshop_notification(student_ids, workshop_name, action_type, link=None):
    if not isinstance(student_ids, list):
        student_ids = [student_ids]
    
    notifications = []
    
    for student_id in student_ids:
        message = f"A new workshop '{workshop_name}' has been created." if action_type == 'created' else \
                 f"Workshop '{workshop_name}' has been updated." if action_type == 'updated' else \
                 f"Workshop '{workshop_name}' has been cancelled."
        
        notification = create_notification(
            student_id=student_id,
            message=message,
            notification_type='workshop',
            link=link
        )
        
        if notification:
            notifications.append(notification)
    
    return notifications

def create_badge_notification(student_id, competency_name, rank, link=None):
    rank_name = "Beginner" if rank == 1 else "Intermediate" if rank == 2 else "Advanced"
    message = f"You have earned a {rank_name} badge in {competency_name}."
    
    return create_notification(
        student_id=student_id,
        message=message,
        notification_type='badge',
        link=link
    )

def create_certificate_notification(student_id, competency_name, status, link=None):
    message = f"Your certificate request for {competency_name} has been approved." if status == 'approved' else \
             f"Your certificate request for {competency_name} has been rejected."
    
    return create_notification(
        student_id=student_id,
        message=message,
        notification_type='certificate',
        link=link
    )

def track_workshop_attendance(workshop_id, student_id, attended=True):
    try:
        # Find the enrollment
        enrollment = Enrollment.query.filter_by(
            workshop_id=workshop_id,
            student_id=student_id
        ).first()
        
        if not enrollment:
            print(f"No enrollment found for student {student_id} in workshop {workshop_id}")
            return None
            
        # Update attendance
        enrollment.attended = attended
        enrollment.attendance_date = datetime.now() if attended else None
        
        # If attended, update workshop attendance count
        workshop = Workshop.query.get(workshop_id)
        if workshop and attended:
            if not hasattr(workshop, 'attendance_count') or workshop.attendance_count is None:
                workshop.attendance_count = 0
            workshop.attendance_count += 1
        
        db.session.commit()
        
        # If attended, create notification
        if attended:
            workshop_name = workshop.workshopName if workshop else "Workshop"
            create_notification(
                student_id=student_id,
                message=f"Your attendance has been recorded for {workshop_name}.",
                notification_type='attendance',
                link=None
            )
            
        return enrollment
        
    except Exception as e:
        db.session.rollback()
        print(f"Error tracking attendance: {e}")
        return None

def mark_notifications_as_read(student_id, notification_ids=None):
    try:
        query = Notification.query.filter_by(student_id=student_id, is_read=False)
        
        if notification_ids:
            query = query.filter(Notification.id.in_(notification_ids))
            
        notifications = query.all()
        
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.now()
            
        db.session.commit()
        return len(notifications)
        
    except Exception as e:
        db.session.rollback()
        print(f"Error marking notifications as read: {e}")
        return 0 