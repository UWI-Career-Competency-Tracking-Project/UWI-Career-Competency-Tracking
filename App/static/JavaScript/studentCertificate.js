// Wait for DOM to fully load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // Hide loader when page is fully loaded
    window.addEventListener('load', function() {
        document.getElementById('loader').style.display = 'none';
    });
    
    // Check if video plays
    const video = document.getElementById('bg-video');
    if (video) {
        video.play().catch(e => {
            console.error('Video play error:', e);
            // Try to force load the video if autoplay fails
            setTimeout(() => {
                video.load();
                video.play().catch(e => console.warn('Second video play attempt failed:', e));
            }, 1000);
        });
    }
    
    // PNG download functionality
    document.getElementById('download-btn').addEventListener('click', function() {
        // Show confetti
        triggerConfetti();
        
        // Capture certificate as PNG
        html2canvas(document.getElementById('certificate')).then(function(canvas) {
            // Create download link
            const link = document.createElement('a');
            link.download = 'certificate.png';
            link.href = canvas.toDataURL('image/png');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Show success message
            showMessage('PNG certificate downloaded!');
        }).catch(function(error) {
            console.error('Error generating PNG:', error);
            showMessage('Error generating PNG. Please try again.', true);
        });
    });
    
    // PDF download functionality
    document.getElementById('download-pdf-btn').addEventListener('click', function() {
        // Show confetti
        triggerConfetti();
        
        // Check if jsPDF is available
        if (typeof window.jspdf === 'undefined') {
            // Load jsPDF if not available
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
            script.onload = function() {
                generatePDF();
            };
            script.onerror = function() {
                showMessage('Failed to load PDF library. Please try again later.', true);
            };
            document.head.appendChild(script);
        } else {
            generatePDF();
        }
    });
});

// Function to trigger confetti animation
function triggerConfetti() {
    if (window.confetti) {
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
}

// Function to generate PDF
function generatePDF() {
    html2canvas(document.getElementById('certificate')).then(function(canvas) {
        if (window.jspdf && window.jspdf.jsPDF) {
            const pdf = new window.jspdf.jsPDF({
                orientation: 'landscape',
                unit: 'px'
            });
            
            const imgData = canvas.toDataURL('image/png');
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
            
            pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
            pdf.save('certificate.pdf');
            
            showMessage('PDF certificate downloaded!');
        } else {
            showMessage('PDF library not loaded correctly. Please try again.', true);
        }
    }).catch(function(error) {
        console.error('Error generating PDF:', error);
        showMessage('Error generating PDF. Please try again.', true);
    });
}

// Function to show message
function showMessage(text, isError = false) {
    const message = document.createElement('div');
    message.className = 'success-message';
    if (isError) message.className += ' error-message';
    message.textContent = text;
    document.body.appendChild(message);
    
    setTimeout(function() {
        message.style.opacity = '0';
        setTimeout(function() {
            if (document.body.contains(message)) {
                document.body.removeChild(message);
            }
        }, 500);
    }, 3000);
}