function searchWorkshops(query) {
    const workshops = document.querySelectorAll('.workshop-card');
    
    query = query.toLowerCase();
    
    let visibleCount = 0;
    
    workshops.forEach(workshop => {
        const title = workshop.querySelector('h3').textContent.toLowerCase();
        const description = workshop.querySelector('.description').textContent.toLowerCase();
        const instructor = workshop.querySelector('.workshop-details').textContent.toLowerCase();
        const location = workshop.querySelector('.workshop-details').textContent.toLowerCase();
        
        if (title.includes(query) || 
            description.includes(query) || 
            instructor.includes(query) || 
            location.includes(query)) {
            workshop.style.display = ''; 
            visibleCount++;
        } else {
            workshop.style.display = 'none'; 
        }
    });
    
    const noWorkshops = document.querySelector('.no-workshops');
    if (noWorkshops) {
        if (visibleCount === 0) {
            noWorkshops.style.display = '';
            noWorkshops.textContent = 'No workshops match your search.';
        } else {
            noWorkshops.style.display = 'none';
        }
    }
} 