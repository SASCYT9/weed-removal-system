// WebSocket connection
const socket = io();

// Connection status
socket.on('connect', () => {
    console.log('Connected to server');
    updateConnectionStatus(true);
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    updateConnectionStatus(false);
});

// Update connection status indicator
function updateConnectionStatus(connected) {
    const indicator = document.getElementById('connection-status');
    if (connected) {
        indicator.textContent = 'Online';
        indicator.className = 'status-indicator online';
    } else {
        indicator.textContent = 'Offline';
        indicator.className = 'status-indicator offline';
    }
}

// Robot state updates
socket.on('robot_state', (data) => {
    console.log('Robot state:', data);
    updateRobotState(data);
});

socket.on('state_update', (data) => {
    console.log('State update:', data);
    updateRobotState(data);
});

socket.on('position_update', (data) => {
    updatePosition(data);
});

socket.on('gps_update', (data) => {
    updateGPS(data);
});

socket.on('detections_update', (data) => {
    updateDetections(data);
});

socket.on('telemetry_update', (data) => {
    updateTelemetry(data);
});

socket.on('statistics_update', (data) => {
    updateStatistics(data);
});

// Update functions
function updateRobotState(state) {
    if (state.status) {
        document.getElementById('robot-status').textContent = state.status;
    }
    if (state.position) {
        updatePosition(state.position);
    }
    if (state.gps) {
        updateGPS(state.gps);
    }
    if (state.statistics) {
        updateStatistics(state.statistics);
    }
}

function updatePosition(position) {
    if (position.heading !== undefined) {
        document.getElementById('heading').textContent =
            position.heading.toFixed(1) + '°';
    }
}

function updateGPS(gps) {
    if (gps.latitude) {
        document.getElementById('latitude').textContent =
            gps.latitude.toFixed(6);
    }
    if (gps.longitude) {
        document.getElementById('longitude').textContent =
            gps.longitude.toFixed(6);
    }
    if (gps.fix_quality !== undefined) {
        const fixText = gps.fix_quality === 4 ? 'RTK Fixed' :
                       gps.fix_quality === 5 ? 'RTK Float' :
                       gps.fix_quality === 2 ? 'DGPS' :
                       gps.fix_quality === 1 ? 'GPS' : 'No Fix';
        document.getElementById('gps-fix').textContent = fixText;
    }
}

function updateDetections(detections) {
    const feed = document.getElementById('detection-feed');

    if (detections.length === 0) {
        feed.innerHTML = '<p>No recent detections</p>';
        return;
    }

    feed.innerHTML = '';
    detections.forEach(detection => {
        const item = document.createElement('div');
        item.className = 'feed-item';
        item.innerHTML = `
            <strong>${detection.class_name || 'Unknown'}</strong>
            - Confidence: ${((detection.confidence || 0) * 100).toFixed(1)}%
            <br>
            <small>Position: (${detection.center ? detection.center[0].toFixed(1) : '--'},
                           ${detection.center ? detection.center[1].toFixed(1) : '--'})</small>
        `;
        feed.appendChild(item);
    });
}

function updateTelemetry(telemetry) {
    const container = document.getElementById('telemetry-data');
    container.innerHTML = '';

    for (const [key, value] of Object.entries(telemetry)) {
        const item = document.createElement('div');
        item.className = 'telemetry-item';
        item.innerHTML = `
            <span class="label">${formatKey(key)}:</span>
            <span class="value">${formatValue(value)}</span>
        `;
        container.appendChild(item);
    }
}

function updateStatistics(stats) {
    if (stats.weeds_detected !== undefined) {
        document.getElementById('weeds-detected').textContent = stats.weeds_detected;
    }
    if (stats.weeds_removed !== undefined) {
        document.getElementById('weeds-removed').textContent = stats.weeds_removed;
    }
    if (stats.distance_traveled !== undefined) {
        document.getElementById('distance-traveled').textContent =
            stats.distance_traveled.toFixed(1);
    }
}

// Send command to robot
function sendCommand(command) {
    console.log('Sending command:', command);
    fetch('/api/command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ command: command })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Command response:', data);
    })
    .catch(error => {
        console.error('Error sending command:', error);
    });
}

// Helper functions
function formatKey(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatValue(value) {
    if (typeof value === 'number') {
        return value.toFixed(2);
    }
    return value;
}

// Fetch initial status
fetch('/api/status')
    .then(response => response.json())
    .then(data => {
        updateRobotState(data);
    })
    .catch(error => {
        console.error('Error fetching status:', error);
    });
