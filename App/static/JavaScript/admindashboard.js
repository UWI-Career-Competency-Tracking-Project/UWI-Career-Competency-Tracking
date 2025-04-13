document.addEventListener('DOMContentLoaded', function () {
    function safeGetVariable(variable, defaultValue) {
        return typeof window[variable] !== 'undefined' ? window[variable] : defaultValue;
    }

    window.addEventListener('load', function () {
        setTimeout(function () {
            const loader = document.getElementById('loader');
            if (loader) {
                loader.style.display = 'none';
            }
        }, 500);

        initCharts();
    });

    function initCharts() {
        try {
            const counters = document.querySelectorAll('.stat-value');

            counters.forEach(counter => {
                const target = parseInt(counter.getAttribute('data-target')) || 0;
                const duration = 1500;
                const frameDuration = 1000 / 60;
                const totalFrames = Math.round(duration / frameDuration);
                const easeOutQuad = t => t * (2 - t);

                let frame = 0;
                const countTo = target;
                const counter_val = { val: 0 };

                const animate = () => {
                    frame++;
                    const progress = easeOutQuad(frame / totalFrames);
                    const currentCount = Math.round(countTo * progress);

                    if (counter_val.val !== currentCount) {
                        counter_val.val = currentCount;
                        counter.textContent = currentCount;
                    }

                    if (frame < totalFrames) {
                        requestAnimationFrame(animate);
                    }
                };

                animate();
            });

            const workshopTrendsChart = document.getElementById('workshopTrendsChart');
            if (workshopTrendsChart && typeof window.workshopCreationData !== 'undefined' && window.workshopCreationData && window.workshopCreationData.some(value => value > 0)) {
                const workshopCtx = workshopTrendsChart.getContext('2d');
                new Chart(workshopCtx, {
                    type: 'line',
                    data: {
                        labels: window.workshopTrendsLabels || [],
                        datasets: [{
                            label: 'Workshops Created',
                            data: window.workshopCreationData || [],
                            borderColor: 'rgba(6, 182, 212, 1)',
                            backgroundColor: 'rgba(6, 182, 212, 0.2)',
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: '#dee2e6'
                                },
                                ticks: {
                                    color: '#212529'
                                }
                            },
                            x: {
                                grid: {
                                    color: '#dee2e6'
                                },
                                ticks: {
                                    color: '#212529'
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                labels: {
                                    color: '#212529'
                                }
                            }
                        }
                    }
                });
            }

            const competenciesChart = document.getElementById('competenciesChart');
            if (competenciesChart && typeof window.competencyLabels !== 'undefined' && window.competencyLabels && window.competencyLabels.length > 0) {
                const competenciesCtx = competenciesChart.getContext('2d');
                new Chart(competenciesCtx, {
                    type: 'doughnut',
                    data: {
                        labels: window.competencyLabels || [],
                        datasets: [{
                            data: window.competencyData || [],
                            backgroundColor: [
                                'rgba(6, 182, 212, 0.8)',
                                'rgba(245, 158, 11, 0.8)',
                                'rgba(124, 58, 237, 0.8)',
                                'rgba(16, 185, 129, 0.8)',
                                'rgba(239, 68, 68, 0.8)',
                                'rgba(59, 130, 246, 0.8)'
                            ],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: {
                                    color: '#212529',
                                    boxWidth: 15,
                                    padding: 15
                                }
                            }
                        },
                        cutout: '50%'
                    }
                });
            }

            const studentProgressChart = document.getElementById('studentProgressChart');
            if (studentProgressChart && typeof window.badgesEarnedData !== 'undefined' && window.badgesEarnedData && window.badgesEarnedData.some(value => value > 0)) {
                const progressCtx = studentProgressChart.getContext('2d');
                new Chart(progressCtx, {
                    type: 'bar',
                    data: {
                        labels: window.progressLabels || [],
                        datasets: [
                            {
                                label: 'Badges Earned',
                                data: window.badgesEarnedData || [],
                                backgroundColor: 'rgba(6, 182, 212, 0.7)',
                                borderWidth: 0
                            },
                            {
                                label: 'Certificates Issued',
                                data: window.certificatesIssuedData || [],
                                backgroundColor: 'rgba(124, 58, 237, 0.7)',
                                borderWidth: 0
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: '#dee2e6'
                                },
                                ticks: {
                                    stepSize: 1,
                                    color: '#212529'
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    color: '#212529'
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                labels: {
                                    color: '#212529'
                                }
                            }
                        }
                    }
                });
            }

            const loadingBar = document.querySelector('.loading-bar');
            if (loadingBar) {
                loadingBar.style.width = '100%';
            }

        } catch (e) {
            console.error("Error initializing dashboard:", e);
        }
    }
});
