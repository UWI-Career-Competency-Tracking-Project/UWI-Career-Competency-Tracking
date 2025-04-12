document.addEventListener('DOMContentLoaded', function() {
    const attendanceButtons = document.querySelectorAll('.btn-attendance, .btn-attendance-remove');
    const completionButtons = document.querySelectorAll('.btn-completion, .btn-completion-remove');

    // Add event listeners to initial buttons
    attendanceButtons.forEach(button => {
        button.addEventListener('click', attendanceHandler);
    });

    completionButtons.forEach(button => {
        button.addEventListener('click', completionHandler);
    });

    // Main attendance handler function
    async function attendanceHandler() {
        const row = this.closest('tr');
        const enrollmentId = row.dataset.enrollmentId;
        const action = this.dataset.action;
        
        try {
            const response = await fetch(`/mark-workshop-attendance/${enrollmentId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `action=${action}`
            });
            
            const data = await response.json();
            
            if (response.ok) {
                const statusCell = row.querySelector('.status-cell');
                const actionsCell = row.querySelector('.action-buttons');
                
                if (action === 'mark') {
                    statusCell.innerHTML = '<span class="status attended">Attended</span>';
                    
                    // Replace this button with "Remove Attendance"
                    this.outerHTML = `
                        <button class="btn btn-attendance-remove" data-action="unmark">
                            <i class="fas fa-times"></i> Remove Attendance
                        </button>
                    `;
                    
                    // Add completion button if it doesn't exist
                    if (!row.querySelector('.btn-completion')) {
                        const completionButton = document.createElement('button');
                        completionButton.className = 'btn btn-completion';
                        completionButton.dataset.action = 'complete';
                        completionButton.innerHTML = '<i class="fas fa-certificate"></i> Mark Complete';
                        actionsCell.appendChild(completionButton);
                        
                        // Add event listener to the new completion button
                        completionButton.addEventListener('click', completionHandler);
                    }
                } else if (action === 'unmark') {
                    statusCell.innerHTML = '<span class="status enrolled">Enrolled</span>';
                    
                    this.outerHTML = `
                        <button class="btn btn-attendance" data-action="mark">
                            <i class="fas fa-check"></i> Mark Attended
                        </button>
                    `;
                    
                    const completionButton = row.querySelector('.btn-completion, .btn-completion-remove');
                    if (completionButton) {
                        completionButton.remove();
                    }
                }
                
                // Re-attach event listener to the updated attendance button
                const newAttendanceButton = row.querySelector('.btn-attendance, .btn-attendance-remove');
                if (newAttendanceButton) {
                    newAttendanceButton.addEventListener('click', attendanceHandler);
                }
                
                showNotification(data.message, 'success');
            } else {
                showNotification(data.error || 'An error occurred', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('An error occurred while updating attendance', 'error');
        }
    }

    // Main completion handler function
    async function completionHandler() {
        const row = this.closest('tr');
        const enrollmentId = row.dataset.enrollmentId;
        const action = this.dataset.action;
        
        try {
            const response = await fetch(`/mark-workshop-completion/${enrollmentId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `action=${action}`
            });
            
            const data = await response.json();
            
            if (response.ok) {
                const statusCell = row.querySelector('.status-cell');
                
                if (action === 'complete') {
                    statusCell.innerHTML = '<span class="status completed">Completed</span>';
                    this.outerHTML = `
                        <button class="btn btn-completion-remove" data-action="uncomplete">
                            <i class="fas fa-times"></i> Remove Completion
                        </button>
                    `;
                } else if (action === 'uncomplete') {
                    statusCell.innerHTML = '<span class="status attended">Attended</span>';
                    this.outerHTML = `
                        <button class="btn btn-completion" data-action="complete">
                            <i class="fas fa-certificate"></i> Mark Complete
                        </button>
                    `;
                }
                
                // Re-attach event listener to the updated completion button
                const newCompletionButton = row.querySelector('.btn-completion, .btn-completion-remove');
                if (newCompletionButton) {
                    newCompletionButton.addEventListener('click', completionHandler);
                }
                
                showNotification(data.message, 'success');
            } else {
                showNotification(data.error || 'An error occurred', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('An error occurred while updating completion status', 'error');
        }
    }

    function showNotification(message, type) {
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            alert(message);
        }
    }
}); 