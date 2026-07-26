/* Smart Traffic Management System — Chart.js Analytics Script */

document.addEventListener('DOMContentLoaded', () => {
  initCharts();
});

function initCharts() {
  // 1. Vehicle Count Line Chart
  const ctxVehicles = document.getElementById('chart-vehicles');
  if (ctxVehicles) {
    new Chart(ctxVehicles, {
      type: 'line',
      data: {
        labels: ['13:00', '13:05', '13:10', '13:15', '13:20', '13:25', '13:30'],
        datasets: [
          { label: 'North', data: [12, 18, 15, 22, 25, 19, 14], borderColor: '#00e5ff', tension: 0.3 },
          { label: 'South', data: [8, 11, 14, 10, 16, 12, 9], borderColor: '#00e676', tension: 0.3 },
          { label: 'East', data: [5, 9, 7, 12, 8, 10, 6], borderColor: '#ffab00', tension: 0.3 },
          { label: 'West', data: [9, 14, 11, 18, 15, 16, 11], borderColor: '#ff5252', tension: 0.3 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#8ca0ba' } } },
        scales: {
          x: { ticks: { color: '#8ca0ba' }, grid: { color: '#2a3756' } },
          y: { ticks: { color: '#8ca0ba' }, grid: { color: '#2a3756' } }
        }
      }
    });
  }

  // 2. Queue Length Bar Chart
  const ctxQueue = document.getElementById('chart-queue');
  if (ctxQueue) {
    new Chart(ctxQueue, {
      type: 'bar',
      data: {
        labels: ['North', 'South', 'East', 'West'],
        datasets: [{
          label: 'Est Queue (Meters)',
          data: [45, 28, 18, 35],
          backgroundColor: ['rgba(0, 229, 255, 0.7)', 'rgba(0, 230, 118, 0.7)', 'rgba(255, 171, 0, 0.7)', 'rgba(255, 82, 82, 0.7)']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: '#8ca0ba' }, grid: { color: '#2a3756' } },
          y: { ticks: { color: '#8ca0ba' }, grid: { color: '#2a3756' } }
        }
      }
    });
  }

  // 3. Signal Phase Breakdown Doughnut Chart
  const ctxPhases = document.getElementById('chart-phases');
  if (ctxPhases) {
    new Chart(ctxPhases, {
      type: 'doughnut',
      data: {
        labels: ['North', 'South', 'East', 'West'],
        datasets: [{
          data: [35, 25, 20, 20],
          backgroundColor: ['#00e5ff', '#00e676', '#ffab00', '#ff5252']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#8ca0ba' } } }
      }
    });
  }

  // 4. PCE Score vs Congestion Radar Chart
  const ctxCongestion = document.getElementById('chart-congestion');
  if (ctxCongestion) {
    new Chart(ctxCongestion, {
      type: 'radar',
      data: {
        labels: ['PCE Score', 'Queue Sec', 'Density', 'Waiting Cycles', 'Emergencies'],
        datasets: [
          { label: 'North Lane', data: [80, 65, 75, 40, 20], borderColor: '#00e5ff', backgroundColor: 'rgba(0, 229, 255, 0.2)' },
          { label: 'South Lane', data: [50, 45, 60, 30, 10], borderColor: '#00e676', backgroundColor: 'rgba(0, 230, 118, 0.2)' }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#8ca0ba' } } },
        scales: {
          r: { ticks: { display: false }, grid: { color: '#2a3756' }, pointLabels: { color: '#8ca0ba' } }
        }
      }
    });
  }
}
