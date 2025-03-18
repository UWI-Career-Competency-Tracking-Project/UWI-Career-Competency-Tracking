document.getElementById('download-btn').addEventListener('click', function() {
    html2canvas(document.getElementById('certificate')).then(function(canvas) {
        // Trigger confetti
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
        
        // Create download link
        const link = document.createElement('a');
        link.download = 'certificate.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
    });
});