
// GPS Tracker JavaScript
let updateInterval;
let map;
let marker;
let trailPolyline;
const CIRCUIT_DIGEST_KEY = '6iZT82ahiMTf';

// Accelerometer chart variables
let accelChart;
let accelData = {
  labels: [],
  x: [],
  y: [],
  z: []
};
const MAX_DATA_POINTS = 50;

// Initialize map
function initMap() {
  // Create map centered on default location
  map = L.map('map').setView([14.5995, 120.9842], 17);

  // Add OpenStreetMap tile layer (fallback as Circuit Digest may not be working)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map);

  // Create marker with custom blue icon
  marker = L.marker([14.5995, 120.9842], {
    icon: L.icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    })
  }).addTo(map);

  marker.bindPopup('<b>Waiting for GPS...</b>').openPopup();

  // Initialize trail polyline (red color for movement trail)
  trailPolyline = L.polyline([], {
    color: 'red',
    weight: 3,
    opacity: 0.7,
    smoothFactor: 1
  }).addTo(map);
}

// Update map with current location
function updateMap(latitude, longitude) {
  if (map && marker && latitude && longitude) {
    const position = [latitude, longitude];

    // Update marker position
    marker.setLatLng(position);
    marker.bindPopup(`<b>Current Location</b><br>Lat: ${latitude.toFixed(6)}°<br>Lon: ${longitude.toFixed(6)}°`);

    // Center map on location
    map.setView(position, 18);
  }
}

// Fetch current GPS data
async function fetchCurrentGPS() {
  try {
    const response = await fetch('/api/gps/current');
    const result = await response.json();

    if (result.success) {
      updateUI(result.data);
    } else {
      console.error('Error fetching GPS data:', result.error);
      updateStatus('Error fetching GPS data', 'error');
    }
  } catch (error) {
    console.error('Network error:', error);
    updateStatus('Network error', 'error');
  }
}

// Fetch GPS trail data
async function fetchGPSTrail() {
  try {
    const response = await fetch('/api/gps/trail');
    const result = await response.json();

    if (result.success && result.data.length > 0) {
      // Convert trail data to Leaflet format
      const trailCoords = result.data.map(point => [point.lat, point.lon]);
      trailPolyline.setLatLngs(trailCoords);
    }
  } catch (error) {
    console.error('Error fetching trail:', error);
  }
}

// Update UI with GPS data
function updateUI(data) {
  // Always update satellite count regardless of fix status
  const satelliteCount = data.satellites || 0;
  document.getElementById('satellites').textContent = satelliteCount;

  if (data.has_fix) {
    updateStatus('GPS LOCKED', 'success');

    const latitude = data.latitude ? data.latitude.toFixed(6) + '°' : '--°';
    const longitude = data.longitude ? data.longitude.toFixed(6) + '°' : '--°';

    document.getElementById('latitude').textContent = latitude;
    document.getElementById('longitude').textContent = longitude;
    const altitude = data.altitude ? data.altitude.toFixed(1) + ' m' : '--';
    document.getElementById('altitude').textContent = altitude;

    // Update map if we have valid coordinates
    if (data.latitude && data.longitude) {
      updateMap(data.latitude, data.longitude);
    }
  } else {
    // Show searching status with satellite info
    if (satelliteCount > 0) {
      updateStatus(`SEARCHING... (${satelliteCount} SAT)`, 'waiting');
    } else {
      updateStatus('SEARCHING...', 'waiting');
    }
    document.getElementById('latitude').textContent = '--°';
    document.getElementById('longitude').textContent = '--°';
    document.getElementById('altitude').textContent = '--';
  }
}

// Update status indicator
function updateStatus(message, type) {
  const statusElement = document.getElementById('gps-status');
  statusElement.textContent = message;
  statusElement.className = 'status-value status-' + type;
}

// Start periodic GPS updates
function startGPSUpdates() {
  fetchCurrentGPS(); // Initial fetch
  updateInterval = setInterval(fetchCurrentGPS, 1000); // Update every 1 second

  // Update trail every 2 seconds
  setInterval(fetchGPSTrail, 2000);
}

// Initialize accelerometer chart
function initAccelChart() {
  const ctx = document.getElementById('accelChart').getContext('2d');

  accelChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: accelData.labels,
      datasets: [
        {
          label: 'X-Axis',
          data: accelData.x,
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 0
        },
        {
          label: 'Y-Axis',
          data: accelData.y,
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 0
        },
        {
          label: 'Z-Axis',
          data: accelData.z,
          borderColor: 'rgb(54, 162, 235)',
          backgroundColor: 'rgba(54, 162, 235, 0.1)',
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      animation: {
        duration: 0
      },
      scales: {
        y: {
          beginAtZero: true,
          min: -2,
          max: 2,
          grid: {
            color: 'rgba(0, 162, 255, 0.1)',
            borderColor: 'rgba(0, 162, 255, 0.3)'
          },
          ticks: {
            color: '#7fa8d1',
            font: {
              family: 'Rajdhani',
              size: 12
            }
          },
          title: {
            display: true,
            text: 'Acceleration (g)',
            color: '#00d4ff',
            font: {
              family: 'Orbitron',
              size: 13,
              weight: 'bold'
            }
          }
        },
        x: {
          display: false
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: '#7fa8d1',
            font: {
              family: 'Rajdhani',
              size: 13
            },
            padding: 15,
            usePointStyle: true
          }
        },
        title: {
          display: true,
          text: 'REAL-TIME ACCELERATION',
          color: '#00d4ff',
          font: {
            family: 'Orbitron',
            size: 14,
            weight: 'bold'
          },
          padding: {
            top: 10,
            bottom: 20
          }
        }
      }
    }
  });
}

// Fetch current accelerometer data
async function fetchCurrentAccel() {
  try {
    const response = await fetch('/api/accelerometer/current');
    const result = await response.json();

    if (result.success) {
      updateAccelUI(result.data);
    } else {
      console.error('Error fetching accelerometer data:', result.error);
    }
  } catch (error) {
    console.error('Network error (accelerometer):', error);
  }
}

// Update accelerometer UI and chart
function updateAccelUI(data) {
  // Update text values
  document.getElementById('accel-x').textContent = data.acceleration.x.toFixed(3) + ' g';
  document.getElementById('accel-y').textContent = data.acceleration.y.toFixed(3) + ' g';
  document.getElementById('accel-z').textContent = data.acceleration.z.toFixed(3) + ' g';
  document.getElementById('accel-mag').textContent = data.acceleration.magnitude.toFixed(3) + ' g';
  document.getElementById('accel-pitch').textContent = data.tilt.pitch.toFixed(1) + '°';
  document.getElementById('accel-roll').textContent = data.tilt.roll.toFixed(1) + '°';

  // Update chart data
  const now = new Date().toLocaleTimeString();
  accelData.labels.push(now);
  accelData.x.push(data.acceleration.x);
  accelData.y.push(data.acceleration.y);
  accelData.z.push(data.acceleration.z);

  // Keep only last MAX_DATA_POINTS
  if (accelData.labels.length > MAX_DATA_POINTS) {
    accelData.labels.shift();
    accelData.x.shift();
    accelData.y.shift();
    accelData.z.shift();
  }

  // Update chart
  if (accelChart) {
    accelChart.update();
  }
}

// Start periodic accelerometer updates
function startAccelUpdates() {
  fetchCurrentAccel(); // Initial fetch
  setInterval(fetchCurrentAccel, 200); // Update every 200ms for smoother graph
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
  console.log('GPS Tracker initialized');
  initMap();
  initAccelChart();
  startGPSUpdates();
  startAccelUpdates();
});
