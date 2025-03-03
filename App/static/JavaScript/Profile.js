document.addEventListener('DOMContentLoaded', () => {
    const profilePic = document.getElementById('profile-pic');

    profilePic.addEventListener('click', () => {
        window.location.href = '#dashboard';
    });

    const usernameInput = document.querySelector('.username-input');
    usernameInput.addEventListener('input', (event) => {
        console.log(`Username changed to: ${event.target.value}`);
    });

    const infoBtn = document.querySelector('.info-btn');
    const trackBtn = document.querySelector('.track-btn');

    infoBtn.addEventListener('click', () => {
        alert('Navigating to Personal Information Page...');
    });

    trackBtn.addEventListener('click', () => {
        alert('Navigating to Track Competencies Page...');
    });
});