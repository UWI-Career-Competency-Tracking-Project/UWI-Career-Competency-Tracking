document.addEventListener('DOMContentLoaded', function() {
  initNotifications();
  
  setupDropdowns();
});

function initNotifications() {
  const notificationCount = document.getElementById('notification-count');
  const notificationsList = document.getElementById('notifications-list');
  const markAllReadBtn = document.getElementById('mark-all-read');
  
  if (!notificationCount || !notificationsList) {
    return; 
  }
  
  window.adminRoutes = [
    '/admin-', 
    '/validate-certificates', 
    '/manage-workshops',
    '/edit-workshop',
    '/workshop-enrollments',
    '/admin-badges'
  ];
  
  const currentPath = window.location.pathname;
  const isAdminPage = window.adminRoutes.some(route => currentPath.includes(route));
  
  console.log('Current path:', currentPath, 'Is admin page:', isAdminPage);
  
  if (isAdminPage) {
    console.log('Loading admin notifications for path:', currentPath);
    loadAdminNotifications();
    setInterval(loadAdminNotifications, 30000);
  } else {
    loadNotifications();
    setInterval(loadNotifications, 30000);
  }
  
  if (markAllReadBtn) {
    markAllReadBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      if (isAdminPage) {
        markAllAdminNotificationsAsRead();
      } else {
        markAllNotificationsAsRead();
      }
    });
  }
}

function loadAdminNotifications() {
  console.log('Loading admin notifications...');
  fetch('/get-admin-notifications')
    .then(response => {
      console.log('Admin notifications response status:', response.status);
      if (!response.ok) {
        throw new Error(`Failed to load admin notifications: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Admin notifications data:', data);
      updateNotificationCount(data.unread_count || 0);
      renderNotifications(data.notifications || []);
    })
    .catch(error => {
      console.error('Error loading admin notifications:', error);
      document.getElementById('notifications-list').innerHTML = `
        <div class="notification-empty">Error loading notifications: ${error.message}</div>
      `;
    });
}

function loadNotifications() {
  fetch('/get-notifications')
    .then(response => {
      if (!response.ok) {
        throw new Error(`Failed to load notifications: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      updateNotificationCount(data.unread_count || 0);
      renderNotifications(data.notifications || []);
    })
    .catch(error => {
      console.error('Error loading notifications:', error);
      document.getElementById('notifications-list').innerHTML = `
        <div class="notification-empty">Error loading notifications: ${error.message}</div>
      `;
    });
}

function updateNotificationCount(count) {
  const badge = document.getElementById('notification-count');
  if (badge) {
    badge.textContent = count;
    badge.style.display = count > 0 ? 'flex' : 'none';
  }
}

function renderNotifications(notifications) {
  const container = document.getElementById('notifications-list');
  
  if (!notifications || notifications.length === 0) {
    container.innerHTML = `
      <div class="notification-empty">No notifications</div>
    `;
    return;
  }
  
  console.log('Rendering notifications:', notifications);
  
  notifications.sort((a, b) => {
    console.log(`Comparing: a.id=${a.id}, a.created_at=${a.created_at}, b.id=${b.id}, b.created_at=${b.created_at}`);
    
    const dateA = new Date(a.created_at || 0);
    const dateB = new Date(b.created_at || 0);
    
    if (dateB.getTime() !== dateA.getTime()) {
      return dateB.getTime() - dateA.getTime();
    }
    
    return b.id - a.id;
  });
  
  let html = '';
  
  const shownMessages = new Set();
  
  notifications.forEach(notification => {
    const messageKey = `${notification.notification_type}:${notification.message}`;
    if (shownMessages.has(messageKey)) {
      return;
    }
    shownMessages.add(messageKey);
    
    const notificationClass = notification.is_read ? 'notification-item' : 'notification-item unread';
    const iconClass = getIconClass(notification.notification_type);
    const icon = getIconForType(notification.notification_type);
    const timeAgo = formatTimeAgo(notification.created_at);
    
    html += `
      <div class="${notificationClass}" data-id="${notification.id}" onclick="handleNotificationClick(event, ${notification.id}, '${notification.link || ''}')">
        <div class="notification-content">
          <div class="notification-icon ${iconClass}">
            ${icon}
          </div>
          <div class="notification-text">
            ${notification.message}
            <span class="notification-time">${timeAgo}</span>
          </div>
        </div>
      </div>
    `;
  });
  
  container.innerHTML = html;
}

function getIconClass(type) {
  switch (type) {
    case 'workshop': return 'workshop';
    case 'badge': return 'badge';
    case 'certificate': return 'certificate';
    case 'certificate_request': return 'certificate-request';
    case 'certificate_approved': return 'certificate-approved';
    case 'enrollment_confirmation': return 'enrollment';
    case 'unenrollment_confirmation': return 'unenrollment';
    default: return '';
  }
}

function getIconForType(type) {
  switch (type) {
    case 'workshop': return '<i class="fas fa-chalkboard-teacher"></i>';
    case 'badge': return '<i class="fas fa-award"></i>';
    case 'certificate': return '<i class="fas fa-certificate"></i>';
    case 'certificate_request': return '<i class="fas fa-file-signature"></i>';
    case 'certificate_approved': return '<i class="fas fa-check-circle"></i>';
    case 'enrollment_confirmation': return '<i class="fas fa-user-plus"></i>';
    case 'unenrollment_confirmation': return '<i class="fas fa-user-minus"></i>';
    default: return '<i class="fas fa-bell"></i>';
  }
}

function formatTimeAgo(dateString) {
  if (!dateString) return 'just now';
  
  try {
    const date = new Date(dateString);
    
    if (isNaN(date.getTime())) {
      return 'unknown time';
    }
    
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.round(diffMs / 1000);
    const diffMin = Math.round(diffSec / 60);
    const diffHour = Math.round(diffMin / 60);
    const diffDay = Math.round(diffHour / 24);
    
    if (diffSec < 60) {
      return 'just now';
    } else if (diffMin < 60) {
      return `${diffMin} ${diffMin === 1 ? 'minute' : 'minutes'} ago`;
    } else if (diffHour < 24) {
      return `${diffHour} ${diffHour === 1 ? 'hour' : 'hours'} ago`;
    } else if (diffDay < 7) {
      return `${diffDay} ${diffDay === 1 ? 'day' : 'days'} ago`;
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
      });
    }
  } catch (e) {
    console.error('Error formatting date:', e);
    return 'unknown time';
  }
}

function handleNotificationClick(event, notificationId, link) {
  const isAdminPage = window.adminRoutes.some(route => window.location.pathname.includes(route));
  console.log('Notification clicked:', notificationId, 'Link:', link, 'Is admin page:', isAdminPage);
  
  if (isAdminPage) {
    markAdminNotificationAsRead(notificationId);
  } else {
    markNotificationAsRead(notificationId);
  }
  
  if (link && link !== 'null' && link !== 'undefined' && link !== '') {
    if (!link.startsWith('http') && !link.startsWith('/')) {
      link = '/' + link;
    }
    
    if (isAdminPage && link.includes('workshop_id=')) {
      const params = new URLSearchParams(link.split('?')[1]);
      const workshopId = params.get('workshop_id');
      
      if (link.includes('validate-certificates')) {
        console.log('Navigating to validate certificates for workshop:', workshopId);
        window.location.href = `/validate-certificates?workshop_id=${workshopId}`;
        return;
      } else if (workshopId) {
        console.log('Navigating to workshop enrollments:', workshopId);
        window.location.href = `/workshop-enrollments/${workshopId}`;
        return;
      }
    }
    
    if (link === '/undefined' || link === '/null') {
      console.log('Invalid link, not navigating');
      return;
    }
    
    console.log('Navigating to:', link);
    window.location.href = link;
  } else {
    console.log('No link provided or link is empty, not navigating');
  }
}

function markNotificationAsRead(notificationId) {
  fetch(`/mark-notification-read/${notificationId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(response => {
    if (response.ok) {
      const notificationElement = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
      if (notificationElement) {
        notificationElement.classList.remove('unread');
      }
      
      const badge = document.getElementById('notification-count');
      if (badge) {
        const currentCount = parseInt(badge.textContent);
        if (currentCount > 0) {
          updateNotificationCount(currentCount - 1);
        }
      }
    }
  })
  .catch(error => {
    console.error('Error marking notification as read:', error);
  });
}

function markAdminNotificationAsRead(notificationId) {
  fetch(`/mark-admin-notification-read/${notificationId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(response => {
    if (response.ok) {
      const notificationElement = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
      if (notificationElement) {
        notificationElement.classList.remove('unread');
      }
      
      const badge = document.getElementById('notification-count');
      if (badge) {
        const currentCount = parseInt(badge.textContent);
        if (currentCount > 0) {
          updateNotificationCount(currentCount - 1);
        }
      }
    }
  })
  .catch(error => {
    console.error('Error marking admin notification as read:', error);
  });
}

function markAllNotificationsAsRead() {
  fetch('/mark-all-notifications-read', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(response => {
    if (response.ok) {
      return response.json();
    }
    throw new Error('Failed to mark all notifications as read');
  })
  .then(data => {
    const unreadNotifications = document.querySelectorAll('.notification-item.unread');
    unreadNotifications.forEach(notification => {
      notification.classList.remove('unread');
    });
    
    updateNotificationCount(0);
  })
  .catch(error => {
    console.error('Error marking all notifications as read:', error);
  });
}

function markAllAdminNotificationsAsRead() {
  fetch('/mark-all-admin-notifications-read', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(response => {
    if (response.ok) {
      return response.json();
    }
    throw new Error('Failed to mark all admin notifications as read');
  })
  .then(data => {
    const unreadNotifications = document.querySelectorAll('.notification-item.unread');
    unreadNotifications.forEach(notification => {
      notification.classList.remove('unread');
    });
    
    updateNotificationCount(0);
  })
  .catch(error => {
    console.error('Error marking all admin notifications as read:', error);
  });
}

function setupDropdowns() {
  const notificationsTrigger = document.querySelector('.notifications-trigger');
  const profileTrigger = document.querySelector('.profile-trigger');
  
  if (notificationsTrigger) {
    notificationsTrigger.addEventListener('click', function(e) {
      e.stopPropagation();
      const dropdown = this.closest('.notifications-dropdown');
      dropdown.classList.toggle('active');
      
      const profileDropdown = document.querySelector('.profile-dropdown');
      if (profileDropdown) {
        profileDropdown.classList.remove('active');
      }
    });
  }
  
  if (profileTrigger) {
    profileTrigger.addEventListener('click', function(e) {
      e.stopPropagation();
      const dropdown = this.closest('.profile-dropdown');
      dropdown.classList.toggle('active');
      
      const notificationsDropdown = document.querySelector('.notifications-dropdown');
      if (notificationsDropdown) {
        notificationsDropdown.classList.remove('active');
      }
    });
  }
  
  document.addEventListener('click', function(e) {
    const notificationsDropdown = document.querySelector('.notifications-dropdown');
    const profileDropdown = document.querySelector('.profile-dropdown');
    
    if (notificationsDropdown && !notificationsDropdown.contains(e.target)) {
      notificationsDropdown.classList.remove('active');
    }
    
    if (profileDropdown && !profileDropdown.contains(e.target)) {
      profileDropdown.classList.remove('active');
    }
  });
} 