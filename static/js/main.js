// === Main JavaScript for Camino ===

// Function to fetch data from an API endpoint
async function fetchData(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching data:', error);
        showAlert('error', 'Erreur lors du chargement des données.');
    }
}

// Function to show alert messages
document.showAlert = function (type, message) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;

    alertContainer.appendChild(alert);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertContainer.removeChild(alert);
    }, 5000);
};

// Function to update KPIs dynamically
async function updateKPIs(url) {
    const data = await fetchData(url);
    if (data) {
        document.getElementById('kpi-questions-value').textContent = data.questions || '--';
        document.getElementById('kpi-responses-value').textContent = data.responses || '--';
        document.getElementById('kpi-roadmaps-value').textContent = data.roadmaps || '--';
        document.getElementById('kpi-users-value').textContent = data.users || '--';
    }
}

// Function to initialize charts dynamically
function initializeChart(chartId, chartType, chartData) {
    const ctx = document.getElementById(chartId).getContext('2d');
    return new Chart(ctx, {
        type: chartType,
        data: {
            labels: chartData.labels,
            datasets: [{
                data: chartData.values,
                backgroundColor: chartData.colors,
                borderColor: chartData.borderColors || [],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const value = context.raw || 0;
                            return `${context.label}: ${value}`;
                        }
                    }
                }
            }
        }
    });
}

// Function to update recent activities
function updateRecentActivities(activities) {
    const activitiesList = document.getElementById('recent-activities-list');
    if (!activitiesList) return;

    activitiesList.innerHTML = '';

    if (activities && activities.length > 0) {
        activities.forEach(activity => {
            const listItem = document.createElement('li');
            listItem.className = 'py-2';
            listItem.textContent = `${activity.timestamp}: ${activity.description}`;
            activitiesList.appendChild(listItem);
        });
    } else {
        activitiesList.innerHTML = '<li class="py-2 text-gray-500">Aucune activité récente.</li>';
    }
}

// Document ready initialization
window.onload = function () {
    // Example: Load KPIs and recent activities on dashboard
    updateKPIs('/analytics/dashboard/');
    fetchData('/analytics/activities/').then(updateRecentActivities);
};
