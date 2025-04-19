function initializeCharts(resultData) {
    // If Chart.js isn't loaded yet, add it dynamically
    if (typeof Chart === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.onload = function() {
            createCharts(resultData);
        };
        document.head.appendChild(script);
    } else {
        createCharts(resultData);
    }
}

function createCharts(resultData) {
    // Example velocity profile chart
    const velocityCtx = document.getElementById('velocityChart').getContext('2d');
    
    // Generate some sample data points for X-axis (position)
    const positions = Array.from({length: 10}, (_, i) => i * resultData.total_length / 10);
    
    // Calculate velocity at each position based on contraction
    const velocities = positions.map(pos => {
        // Simple model: velocity increases linearly through the contraction
        const progress = pos / resultData.total_length;
        const velocityRatio = resultData.velocity_ratio || 1;
        return 15 * (1 + progress * (velocityRatio - 1));
    });
    
    new Chart(velocityCtx, {
        type: 'line',
        data: {
            labels: positions.map(p => `${p.toFixed(0)} mm`),
            datasets: [{
                label: 'Flow Velocity (m/s)',
                data: velocities,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.3,
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Velocity (m/s)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Position'
                    }
                }
            }
        }
    });
}
