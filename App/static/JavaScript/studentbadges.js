document.addEventListener('DOMContentLoaded', () => {
    const profilePic = document.getElementById('profile-pic');

    profilePic.addEventListener('click', () => {
        window.location.href = '#dashboard';
    });

    const dynamicCategories = [
        { name: 'Coding', progress: 90, img: 'badge1.png' },
        { name: 'Problem Solving', progress: 70, img: 'badge2.png' },
        { name: 'Leadership', progress: 50, img: 'badge3.png' },
        { name: 'Teamwork', progress: 80, img: 'badge1.png' },
        { name: 'Communication', progress: 60, img: 'badge2.png' },
        { name: 'Critical Thinking', progress: 95, img: 'badge3.png' }
    ];

    const achievementsContainer = document.getElementById('achievements-container');
    dynamicCategories.forEach((category) => {
        const card = document.createElement('div');
        card.classList.add('achievement-card');
        card.innerHTML = `
            <h3>${category.name}</h3>
            <img src="images/${category.img}" alt="${category.name}">
            <div class="progress-bar">
                <div class="progress" style="width: ${category.progress}%"></div>
            </div>
            <p>Progress: ${category.progress}%</p>
        `;
        achievementsContainer.appendChild(card);
    });
});