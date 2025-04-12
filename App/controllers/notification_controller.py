from App.models.notification import Notification
from App.models.student import Student
from App import db
from datetime import datetime, timedelta
from sqlalchemy import desc
from flask import flash
from App.models.workshop import Workshop
from App.models.enrollment import Enrollment

def create_notification(student_id=None, message=None, notification_type=None, user_id=None, user_type=None, related_id=None, link=None):
    try:
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        if student_id:
            existing = Notification.query.filter_by(
                student_id=student_id,
                notification_type=notification_type,
                message=message
            ).filter(Notification.created_at > one_hour_ago).first()
        elif user_type:
            existing = Notification.query.filter_by(
                user_type=user_type,
                notification_type=notification_type,
                message=message
            ).filter(Notification.created_at > one_hour_ago).first()
        else:
            existing = None
            
        if existing:
            print(f"Skipping duplicate notification: {message}")
            return existing
            
        current_time = datetime.now()
        notification = Notification(
            message=message,
            notification_type=notification_type,
            student_id=student_id,
            user_id=user_id,
            user_type=user_type,
            related_id=related_id,
            link=link,
            created_at=current_time,
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        if student_id:
            print(f"Created notification for student {student_id}: {message} at {current_time}")
        elif user_type:
            print(f"Created notification for {user_type}: {message} at {current_time}")
        return notification
    except Exception as e:
        db.session.rollback()
        print(f"Error creating notification: {e}")
        flash(f"Error creating notification: {str(e)}", "error")
        return None

def create_admin_notification(message, notification_type, link=None, related_id=None):
    """Create a notification specifically for admin users"""
    return create_notification(
        message=message,
        notification_type=notification_type,
        user_type='admin',
        link=link,
        related_id=related_id
    )

def get_notifications(student_id, limit=10, unread_only=False):
    query = Notification.query.filter_by(student_id=student_id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    return query.order_by(desc(Notification.created_at), desc(Notification.id)).limit(limit).all()

def get_admin_notifications(limit=10, unread_only=False):
    """Get notifications for admin users"""
    query = Notification.query.filter_by(user_type='admin')
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    return query.order_by(desc(Notification.created_at), desc(Notification.id)).limit(limit).all()

def get_unread_count(student_id):
    return Notification.query.filter_by(student_id=student_id, is_read=False).count()

def get_admin_unread_count():
    """Get count of unread admin notifications"""
    return Notification.query.filter_by(user_type='admin', is_read=False).count()

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

def mark_all_as_read(student_id=None, user_type=None):
    try:
        if student_id:
            notifications = Notification.query.filter_by(student_id=student_id, is_read=False).all()
        elif user_type:
            notifications = Notification.query.filter_by(user_type=user_type, is_read=False).all()
        else:
            return 0
            
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
    """
    Create a notification for certificate approval/rejection
    """
    is_approved = status == 'approved' or status == 'approve'
    
    message = f"Your certificate request for {competency_name} has been approved." if is_approved else \
             f"Your certificate request for {competency_name} has been rejected."
    
    notification_type = 'certificate_approved' if is_approved else 'certificate_rejected'
    
    return create_notification(
        student_id=student_id,
        message=message,
        notification_type=notification_type,
        link=link
    )

def track_workshop_attendance(workshop_id, student_id, attended=True):
    try:
        enrollment = Enrollment.query.filter_by(
            workshop_id=workshop_id,
            student_id=student_id
        ).first()
        
        if not enrollment:
            print(f"No enrollment found for student {student_id} in workshop {workshop_id}")
            return None
            
        enrollment.attended = attended
        enrollment.attendance_date = datetime.now() if attended else None
        
        workshop = Workshop.query.get(workshop_id)
        if workshop and attended:
            if not hasattr(workshop, 'attendance_count') or workshop.attendance_count is None:
                workshop.attendance_count = 0
            workshop.attendance_count += 1
        
        db.session.commit()
        
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