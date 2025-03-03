// Importing confetti.js
function startConfetti() {
    let duration = 3 * 1000; // Confetti lasts 3 seconds
    let end = Date.now() + duration;

    (function frame() {
        confetti({
            particleCount: 5,
            spread: 100,
            origin: { y: 0.6 } // Starts mid-screen
        });

        if (Date.now() < end) {
            requestAnimationFrame(frame);
        }
    })();
}

document.getElementById("download-btn").addEventListener("click", function() {
    // Start confetti effect
    startConfetti();

    // Capture certificate screenshot and download
    html2canvas(document.getElementById("certificate"), {
        scale: 3, // High-quality image
        useCORS: true // Fixes external image loading
    }).then(canvas => {
        let link = document.createElement("a");
        link.href = canvas.toDataURL("image/png");
        link.download = "certificate.png";
        link.click();
    });
});
