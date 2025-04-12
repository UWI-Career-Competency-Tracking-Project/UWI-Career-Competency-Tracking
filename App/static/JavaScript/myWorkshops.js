function unenrollWorkshop(workshopId) {
    if (confirm('Are you sure you want to unenroll from this workshop? This will also remove any competencies gained from this workshop.')) {
        console.log('Starting unenroll process for workshop:', workshopId);
        
        fetch(`/unenroll-workshop/${workshopId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'  
        })
        .then(response => {
            console.log('Response status:', response.status);
            return response.json().then(data => {
                console.log('Response data:', data);
                return { status: response.status, data };
            });
        })
        .then(({ status, data }) => {
            console.log('Processing response - Status:', status);
            if (status === 200) {
                console.log('Unenroll successful, reloading page...');
                window.location.reload();
            } else {
                console.error('Error response:', data.error);
                alert(data.error || 'Error unenrolling from workshop. Please try again.');
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            alert('An error occurred while unenrolling. Please try again.');
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    
    function activateTab(tabId) {
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        
        const tabBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
        if (tabBtn) {
            tabBtn.classList.add('active');
            const tabContent = document.getElementById(`${tabId}-tab`);
            if (tabContent) {
                tabContent.classList.add('active');
            }
        }
    }
    
    if (tabParam && ['active', 'completed'].includes(tabParam)) {
        activateTab(tabParam);
    }
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            activateTab(tabId);
            
            const url = new URL(window.location);
            url.searchParams.set('tab', tabId);
            window.history.pushState({}, '', url);
        });
    });
});