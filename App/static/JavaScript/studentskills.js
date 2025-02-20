document.addEventListener('DOMContentLoaded', () => {
    const profilePic = document.getElementById('profile-pic');

    profilePic.addEventListener('click', () => {
        window.location.href = '#dashboard';
    });

    const coreSkills = [
        { name: 'Python Programming', level: 'Beginner', img: 'python.png' },
        { name: 'JavaScript Programming', level: 'Intermediate', img: 'javascript.png' },
        { name: 'C++ Programming', level: 'Beginner', img: 'cpp.png' },
        { name: 'Debugging', level: 'Advanced', img: 'debug.png' }
    ];

    const jobRoles = [
        { title: 'Software Engineer', description: 'Design, develop, and maintain software applications and systems.' },
        { title: 'Data Scientist', description: 'Analyze complex datasets to derive actionable insights and solve business problems.' }
    ];

    const skillsContainer = document.getElementById('skills-container');
    coreSkills.forEach((skill) => {
        const card = document.createElement('div');
        card.classList.add('skill-card');
        card.innerHTML = `
            <h4>${skill.name}</h4>
            <img src="images/${skill.img}" alt="${skill.name}">
            <span class="badge ${skill.level.toLowerCase()}">${skill.level}</span>
        `;
        skillsContainer.appendChild(card);
    });

    const rolesContainer = document.getElementById('job-roles-container');
    jobRoles.forEach((role) => {
        const card = document.createElement('div');
        card.classList.add('job-card');
        card.innerHTML = `
            <h4>Job Title: ${role.title}</h4>
            <p>Description: ${role.description}</p>
        `;
        rolesContainer.appendChild(card);
    });
});