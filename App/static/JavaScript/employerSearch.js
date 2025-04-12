let timeoutId;
let competenciesList = [];
let dataContainer;
let competenciesUrl;
let searchUrl;

// Fetch competencies when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Get URLs from data attributes
    dataContainer = document.getElementById('data-container');
    if (dataContainer) {
        competenciesUrl = dataContainer.getAttribute('data-competencies-url');
        searchUrl = dataContainer.getAttribute('data-search-url');
    }
    
    fetchCompetencies();
    
    // Set up event listeners
    const input = document.getElementById('competency-search');
    const searchButton = document.getElementById('search-button');
    
    // Only update autocomplete as user types, not search
    input.addEventListener('input', function() {
        const query = this.value;
        showAutocomplete(query);
    });
    
    // Search only when button is clicked
    searchButton.addEventListener('click', performSearch);
    
    // Or when Enter key is pressed
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch();
        }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target.id !== 'competency-search') {
            closeAllLists();
        }
    });
    
    // Handle filter Enter key
    document.getElementById('rank-filter').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch();
        }
    });
});

// Fetch all competencies from the server
function fetchCompetencies() {
    if (!competenciesUrl) {
        console.error('Competencies URL not available');
        return;
    }
    
    fetch(competenciesUrl)
        .then(response => response.json())
        .then(data => {
            if (data.competencies) {
                competenciesList = data.competencies;
            }
        })
        .catch(error => console.error('Error fetching competencies:', error));
}

// Show autocomplete suggestions
function showAutocomplete(query) {
    closeAllLists();
    if (!query) return false;
    
    const list = document.getElementById('autocomplete-list');
    query = query.toLowerCase();
    
    // Find matching competencies
    const matches = competenciesList.filter(comp => 
        comp.toLowerCase().includes(query)
    );
    
    // Add up to 8 suggestions
    matches.slice(0, 8).forEach(comp => {
        const div = document.createElement('div');
        // Highlight the matching part
        const matchIndex = comp.toLowerCase().indexOf(query);
        div.innerHTML = comp.substring(0, matchIndex) + 
                        '<strong>' + comp.substring(matchIndex, matchIndex + query.length) + '</strong>' +
                        comp.substring(matchIndex + query.length);
        
        div.addEventListener('click', function() {
            document.getElementById('competency-search').value = comp;
            closeAllLists();
            // Don't auto-search when selecting - wait for button click
        });
        
        list.appendChild(div);
    });
}

// Close all autocomplete lists
function closeAllLists() {
    const list = document.getElementById('autocomplete-list');
    if (list) list.innerHTML = '';
}

// Perform the actual search
function performSearch() {
    if (!searchUrl) {
        console.error('Search URL not available');
        return;
    }
    
    const searchQuery = document.getElementById('competency-search').value;
    const rankFilter = document.getElementById('rank-filter').value;
    window.location.href = `${searchUrl}?competency=${encodeURIComponent(searchQuery)}&rank=${encodeURIComponent(rankFilter)}`;
}
