
function startConfetti() {
    let duration = 3 * 1000; 
    let end = Date.now() + duration;

    (function frame() {
        confetti({
            particleCount: 5,
            spread: 100,
            origin: { y: 0.6 } 
        });

        if (Date.now() < end) {
            requestAnimationFrame(frame);
        }
    })();
}

document.getElementById("download-btn").addEventListener("click", function() {
    
    startConfetti();

    
    html2canvas(document.getElementById("certificate"), {
        scale: 3, 
        useCORS: true 
    }).then(canvas => {
        let link = document.createElement("a");
        link.href = canvas.toDataURL("image/png");
        link.download = "certificate.png";
        link.click();
    });
});
