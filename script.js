document.addEventListener('DOMContentLoaded', () => {
    
    // --- Prediction Page Logic ---
    const predictionForm = document.getElementById('predictionForm');
    if (predictionForm) {
        predictionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('predictBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Predicting...';
            btn.disabled = true;

            const errorAlert = document.getElementById('errorAlert');
            errorAlert.classList.add('d-none');
            document.getElementById('resultSection').classList.add('d-none');

            const payload = {
                City: document.getElementById('city').value,
                Day_of_Week: document.getElementById('dayOfWeek').value,
                Ride_Distance_KM: document.getElementById('distance').value,
                Ride_Type: document.getElementById('rideType').value,
                Weather: document.getElementById('weather').value,
                Event: document.getElementById('event').value,
                Available_Drivers: document.getElementById('drivers').value,
                Hour_of_Day: document.getElementById('hour').value,
                Traffic_Delay_Min: document.getElementById('traffic').value
            };

            try {
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('resDemandLevel').innerText = data.predicted_demand_level;
                    document.getElementById('resDemandScore').innerText = data.demand_score;
                    document.getElementById('resSurge').innerText = data.surge_multiplier_suggestion + 'x';
                    document.getElementById('resultSection').classList.remove('d-none');
                } else {
                    errorAlert.innerText = data.error || 'Prediction failed.';
                    errorAlert.classList.remove('d-none');
                }
            } catch (err) {
                errorAlert.innerText = 'Network error. Please try again.';
                errorAlert.classList.remove('d-none');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    // --- Dashboard Page Logic ---
    const dashboardContainer = document.getElementById('chartsContainer');
    if (dashboardContainer) {
        let charts = {}; // To keep track of chart instances

        const loadDashboard = async () => {
            document.getElementById('dashboardLoader').classList.remove('d-none');
            dashboardContainer.classList.add('d-none');
            document.getElementById('dashboardError').classList.add('d-none');

            try {
                const res = await fetch('/api/dashboard-data');
                const data = await res.json();
                if (data.error) throw new Error(data.error);

                renderChart('cityChart', 'bar', data.city_demand, 'Ride Demand by City', '#3b82f6');
                renderChart('weatherChart', 'pie', data.weather_demand, 'Weather Impact', ['#f59e0b', '#3b82f6', '#10b981']);
                renderChart('hourlyChart', 'line', data.hourly_demand, 'Hourly Demand', '#8b5cf6');
                
                document.getElementById('dashboardLoader').classList.add('d-none');
                dashboardContainer.classList.remove('d-none');
            } catch (err) {
                document.getElementById('dashboardLoader').classList.add('d-none');
                document.getElementById('dashboardError').innerText = 'Failed to load dashboard: ' + err.message;
                document.getElementById('dashboardError').classList.remove('d-none');
            }
        };

        const renderChart = (canvasId, type, dataObj, label, colors) => {
            const ctx = document.getElementById(canvasId).getContext('2d');
            
            // Destroy existing chart if present
            if (charts[canvasId]) {
                charts[canvasId].destroy();
            }

            charts[canvasId] = new Chart(ctx, {
                type: type,
                data: {
                    labels: Object.keys(dataObj),
                    datasets: [{
                        label: label,
                        data: Object.values(dataObj),
                        backgroundColor: colors,
                        borderColor: type === 'line' ? colors : 'transparent',
                        tension: 0.3,
                        fill: type === 'line' ? {target: 'origin', above: 'rgba(139, 92, 246, 0.2)'} : false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#f8fafc' }
                        }
                    },
                    scales: type !== 'pie' ? {
                        x: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                        y: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(255,255,255,0.1)' } }
                    } : {}
                }
            });
        };

        loadDashboard();
        
        document.getElementById('refreshCharts').addEventListener('click', loadDashboard);
    }

    // --- Dataset Page Logic ---
    const datasetTable = document.getElementById('datasetTable');
    if (datasetTable) {
        const loadDataset = async () => {
            const tbody = document.getElementById('datasetBody');
            tbody.innerHTML = '<tr><td colspan="12" class="text-center py-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2 text-muted mb-0">Loading dataset...</p></td></tr>';
            
            try {
                const res = await fetch('/api/dataset');
                const data = await res.json();
                
                if (data.success) {
                    tbody.innerHTML = '';
                    data.data.forEach(row => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${row.City}</td>
                            <td>${row.Date}</td>
                            <td>${row.Day_of_Week}</td>
                            <td>${row.Hour_of_Day}:00</td>
                            <td>${row.Ride_Distance_KM}</td>
                            <td><span class="badge bg-secondary">${row.Ride_Type}</span></td>
                            <td>${row.Weather}</td>
                            <td>${row.Event}</td>
                            <td>${row.Available_Drivers}</td>
                            <td><span class="badge bg-${row.Demand_Level === 'High' ? 'danger' : row.Demand_Level === 'Medium' ? 'warning' : 'success'}">${row.Demand_Level}</span></td>
                            <td>${row.Surge_Multiplier}</td>
                            <td>${row.Demand_Score}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                } else {
                    tbody.innerHTML = `<tr><td colspan="12" class="text-danger text-center py-3">${data.error}</td></tr>`;
                }
            } catch(e) {
                tbody.innerHTML = `<tr><td colspan="12" class="text-danger text-center py-3">Error loading dataset. Please make sure dataset is generated.</td></tr>`;
            }
        };

        loadDataset();
        document.getElementById('refreshTableBtn').addEventListener('click', loadDataset);

        // Upload Form
        const uploadForm = document.getElementById('uploadForm');
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('uploadBtn');
            btn.innerHTML = 'Uploading...';
            btn.disabled = true;

            const fileInput = document.getElementById('datasetFile');
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            const alertBox = document.getElementById('uploadAlert');
            
            try {
                const res = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                
                alertBox.classList.remove('d-none', 'alert-danger', 'alert-success');
                if (data.success) {
                    alertBox.classList.add('alert-success');
                    alertBox.innerText = data.message;
                    loadDataset(); // reload table
                } else {
                    alertBox.classList.add('alert-danger');
                    alertBox.innerText = data.error;
                }
            } catch (err) {
                alertBox.classList.remove('d-none', 'alert-success');
                alertBox.classList.add('alert-danger');
                alertBox.innerText = 'Upload failed due to network error.';
            } finally {
                btn.innerHTML = 'Upload CSV';
                btn.disabled = false;
            }
        });
    }

});
