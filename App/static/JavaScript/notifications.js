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
  
  loadNotifications();
  
  setInterval(loadNotifications, 30000);
  
  if (markAllReadBtn) {
    markAllReadBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      markAllNotificationsAsRead();
    });
  }
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
  
  let html = '';
  
  notifications.forEach(notification => {
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
    default: return '';
  }
}

function getIconForType(type) {
  switch (type) {
    case 'workshop': return '<i class="fas fa-chalkboard-teacher"></i>';
    case 'badge': return '<i class="fas fa-award"></i>';
    case 'certificate': return '<i class="fas fa-certificate"></i>';
    default: return '<i class="fas fa-bell"></i>';
  }
}

function formatTimeAgo(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffSeconds = Math.floor((now - date) / 1000);
  
  if (diffSeconds < 60) {
    return 'just now';
  }
  
  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
  }
  
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  }
  
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) {
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  }
  
  return date.toLocaleDateString();
}

function handleNotificationClick(event, notificationId, link) {
  markNotificationAsRead(notificationId);
  
  if (link && link !== 'null' && link !== 'undefined') {
    window.location.href = link;
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