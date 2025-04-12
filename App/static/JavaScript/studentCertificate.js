document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    window.addEventListener('load', function() {
        document.getElementById('loader').style.display = 'none';
    });
    
    const video = document.getElementById('bg-video');
    if (video) {
        video.play().catch(e => {
            console.error('Video play error:', e);
            setTimeout(() => {
                video.load();
                video.play().catch(e => console.warn('Second video play attempt failed:', e));
            }, 1000);
        });
    }
    
    document.getElementById('download-btn').addEventListener('click', function() {
        triggerConfetti();
        
        html2canvas(document.getElementById('certificate')).then(function(canvas) {
            const link = document.createElement('a');
            link.download = 'certificate.png';
            link.href = canvas.toDataURL('image/png');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            showMessage('PNG certificate downloaded!');
        }).catch(function(error) {
            console.error('Error generating PNG:', error);
            showMessage('Error generating PNG. Please try again.', true);
        });
    });
    
    document.getElementById('download-pdf-btn').addEventListener('click', function() {
        triggerConfetti();
        
        if (typeof window.jspdf === 'undefined') {
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

function triggerConfetti() {
    if (window.confetti) {
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
}

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