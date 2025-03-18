let timeoutId;
        
        function debounceSearch(value) {
            clearTimeout(timeoutId);
            
            timeoutId = setTimeout(() => {
                performSearch(value);
            }, 300); 
        }
        
        function performSearch(query) {
            let baseUrl = window.location.pathname;
            
            let url = baseUrl + (query ? `?search=${encodeURIComponent(query)}` : '');
            
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    let temp = document.createElement('div');
                    temp.innerHTML = html;
                    
                    let newWorkshops = temp.querySelector('.workshops-container');
                    let currentWorkshops = document.querySelector('.workshops-container');
                    if (newWorkshops && currentWorkshops) {
                        currentWorkshops.innerHTML = newWorkshops.innerHTML;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        }