document.addEventListener("DOMContentLoaded", function () {
    console.log("Career Competency Tracking System is ready!");

    // Button Hover Effect for Console Logging
    let buttons = document.querySelectorAll(".btn");
    buttons.forEach(button => {
        button.addEventListener("mouseover", () => {
            console.log(`Hovering over ${button.innerText} button`);
        });
    });

    // Background Video Fallback Check
    let video = document.getElementById("background-video");
    if (!video) {
        console.warn("Background video not found!");
    }
});

