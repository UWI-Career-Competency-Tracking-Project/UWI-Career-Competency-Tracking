function unenrollWorkshop(workshopId) {
    if (confirm('Are you sure you want to unenroll from this workshop? This will also remove any competencies gained from this workshop.')) {
        console.log('Starting unenroll process for workshop:', workshopId);
        
        fetch(`/unenroll-workshop/${workshopId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'  // Include cookies in the request
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