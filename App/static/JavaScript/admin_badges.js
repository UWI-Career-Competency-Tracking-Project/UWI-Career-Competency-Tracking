function updateRankDisplay(radio, rankText) {
    const form = radio.closest('form');
    const rankDisplay = form.querySelector('.rank-text');
    rankDisplay.textContent = rankText;
}

function submitForm(event, button) {
    event.preventDefault();
    const form = button.closest('form');
    const rank = form.querySelector('input[name="rank"]:checked');
    
    if (!rank) {
        alert('Please select a rank before updating.');
        return;
    }
    
    const formData = new FormData(form);
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.text())
    .then(data => {
        window.location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating. Please try again.');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.badge').forEach(badge => {
        badge.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                const rankText = this.querySelector('label').textContent;
                updateRankDisplay(radio, rankText);
            }
        });
    });

    document.querySelectorAll('input[name="rank"]:checked').forEach(radio => {
        const rankText = radio.closest('.badge').querySelector('label').textContent;
        updateRankDisplay(radio, rankText);
    });
}); 