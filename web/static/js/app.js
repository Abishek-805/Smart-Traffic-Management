/* Smart Traffic Management System — Control Room App JS */

// Global state
window.systemState = {
  aiRunning: true,
  wsOnline: true,
  esp32Connected: false,
  activePhase: 'North',
  greenDuration: 10,
  timeRemaining: 10,
  nodeCount: 0,
};

document.addEventListener('DOMContentLoaded', () => {
  initClock();
  initTelemetryWebSocket();
  fetchSystemHealth();
  setInterval(fetchSystemHealth, 5000);
});

// Live Clock
function initClock() {
  const clockEl = document.getElementById('live-clock');
  function update() {
    const now = new Date();
    if (clockEl) {
      clockEl.textContent = now.toTimeString().split(' ')[0] + ' ' + now.toLocaleDateString();
    }
  }
  update();
  setInterval(update, 1000);
}

// System Health Diagnostics API
async function fetchSystemHealth() {
  try {
    const res = await fetch('/api/system/health');
    if (!res.ok) return;
    const data = await res.json();
    
    // Update Header Badges
    const badgeAi = document.getElementById('badge-ai');
    if (badgeAi) {
      badgeAi.className = data.ai ? 'status-pill online' : 'status-pill offline';
      badgeAi.innerHTML = `<span class="dot-indicator"></span> AI Engine: ${data.ai ? 'Active' : 'Stopped'}`;
    }

    const badgeNodes = document.getElementById('node-count-badge');
    if (badgeNodes) {
      badgeNodes.textContent = data.cameraNodes || 0;
    }

    const badgeEsp32 = document.getElementById('badge-esp32');
    if (badgeEsp32) {
      badgeEsp32.className = data.esp32 ? 'status-pill online' : 'status-pill warning';
      badgeEsp32.innerHTML = `<span class="dot-indicator"></span> ESP32: ${data.esp32 ? 'HARDWARE' : 'Simulation'}`;
    }
  } catch (err) {
    console.warn('[HealthCheck] Error fetching health:', err);
  }
}

// Telemetry WebSocket Client
function initTelemetryWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = `${protocol}://${window.location.host}/ws/telemetry`;
  
  let ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('[TelemetryWS] Telemetry WebSocket connected.');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleTelemetryMessage(data);
    } catch (e) {
      console.error('[TelemetryWS] Parse error:', e);
    }
  };

  ws.onclose = () => {
    console.warn('[TelemetryWS] Closed. Reconnecting in 3s...');
    setTimeout(initTelemetryWebSocket, 3000);
  };
}

function handleTelemetryMessage(msg) {
  if (msg.type === 'TELEMETRY_UPDATE' && msg.data) {
    const d = msg.data;
    window.systemState = { ...window.systemState, ...d };

    // Update Operations Dashboard Elements if on Dashboard page
    const greenLaneEl = document.getElementById('hud-green-lane');
    if (greenLaneEl && d.activePhase) {
      greenLaneEl.textContent = d.activePhase.toUpperCase();
    }

    const countdownEl = document.getElementById('hud-countdown');
    if (countdownEl && d.timeRemaining !== undefined) {
      countdownEl.textContent = `${d.timeRemaining}s`;
    }

    const vehiclesEl = document.getElementById('hud-vehicles');
    if (vehiclesEl && d.totalVehicles !== undefined) {
      vehiclesEl.textContent = d.totalVehicles;
    }

    const queueEl = document.getElementById('hud-queue');
    if (queueEl && d.queueLength !== undefined) {
      queueEl.textContent = `${d.queueLength}m`;
    }
  }
}

// System Control Actions
async function startSystem() {
  try {
    const res = await fetch('/api/system/start', { method: 'POST' });
    const data = await res.json();
    alert(data.message || 'AI System Started.');
    fetchSystemHealth();
  } catch (e) {
    alert('Failed to start system.');
  }
}

async function stopSystem() {
  try {
    const res = await fetch('/api/system/stop', { method: 'POST' });
    const data = await res.json();
    alert(data.message || 'AI System Stopped.');
    fetchSystemHealth();
  } catch (e) {
    alert('Failed to stop system.');
  }
}

async function restartSystem() {
  try {
    const res = await fetch('/api/system/restart', { method: 'POST' });
    const data = await res.json();
    alert(data.message || 'AI System Restarting...');
    fetchSystemHealth();
  } catch (e) {
    alert('Failed to restart system.');
  }
}
