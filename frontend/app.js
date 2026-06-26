const zoneSelect = document.getElementById("zoneSelect");
const selectedZoneName = document.getElementById("selectedZoneName");
const selectedZoneMeta = document.getElementById("selectedZoneMeta");
const riskScore = document.getElementById("riskScore");
const weatherDescription = document.getElementById("weatherDescription");
const temperatureValue = document.getElementById("temperatureValue");
const precipitationValue = document.getElementById("precipitationValue");
const recommendation = document.getElementById("recommendation");
const zonesList = document.getElementById("zonesList");
const alertsFeed = document.getElementById("alertsFeed");
const connectionState = document.getElementById("connectionState");
const travelerName = document.getElementById("travelerName");
const travelerId = document.getElementById("travelerId");
const latInput = document.getElementById("lat");
const lngInput = document.getElementById("lng");
const refreshButton = document.getElementById("refreshButton");
const connectButton = document.getElementById("connectButton");

let socket;
let map;
let markers = [];
let zoneData = [];

function setConnection(title, level = "low") {
  connectionState.textContent = title;
  connectionState.className = `badge ${level}`;
}

function markerColor(level) {
  if (level === "critical") return "#ff4d6d";
  if (level === "high") return "#ff6b6b";
  if (level === "moderate") return "#ffd166";
  return "#6ee7b7";
}

function makeIcon(level) {
  return L.divIcon({
    className: "zone-marker",
    html: `<div style="width:16px;height:16px;border-radius:999px;background:${markerColor(level)};border:3px solid rgba(255,255,255,0.9);box-shadow:0 0 0 8px ${markerColor(level)}33;"></div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });
}

function clearMarkers() {
  markers.forEach((marker) => marker.remove());
  markers = [];
}

function renderAssessment(zone) {
  riskScore.textContent = `${zone.assessment.risk_score}/100`;
  weatherDescription.textContent = zone.weather.description;
  temperatureValue.textContent = `${zone.weather.temperature.toFixed(1)}°C`;
  precipitationValue.textContent = `${zone.weather.precipitation.toFixed(1)} mm`;
  recommendation.textContent = zone.assessment.recommendation;
  selectedZoneName.textContent = zone.name;
  selectedZoneMeta.textContent = `${zone.department} · ${zone.weather.source}`;

  Array.from(zonesList.children).forEach((item) => {
    item.classList.toggle("active", item.dataset.zoneId === zone.id);
  });
}

function addAlert(zone, kind) {
  const item = document.createElement("article");
  item.className = "alert";
  item.innerHTML = `
    <div class="row">
      <strong>${zone.name}</strong>
      <span class="badge ${kind === "critical" ? "critical" : kind === "warning" ? "high" : zone.assessment.level}">${kind.toUpperCase()}</span>
    </div>
    <div class="muted">${zone.department} · Riesgo ${zone.assessment.risk_score}/100 · ${zone.weather.description}</div>
    <p>${zone.assessment.recommendation}</p>
  `;
  alertsFeed.prepend(item);
  while (alertsFeed.children.length > 5) {
    alertsFeed.removeChild(alertsFeed.lastElementChild);
  }
}

function buildZoneList(zones) {
  zonesList.innerHTML = "";
  zoneSelect.innerHTML = "";

  zones.forEach((zone) => {
    const option = document.createElement("option");
    option.value = zone.id;
    option.textContent = zone.name;
    zoneSelect.appendChild(option);

    const item = document.createElement("article");
    item.className = "zone-item";
    item.dataset.zoneId = zone.id;
    item.innerHTML = `
      <div class="row">
        <strong>${zone.name}</strong>
        <span class="badge ${zone.assessment.level}">${zone.assessment.level.toUpperCase()}</span>
      </div>
      <div class="muted">${zone.department}</div>
      <div class="muted">Clima: ${zone.weather.description} · ${zone.weather.temperature.toFixed(1)}°C</div>
      <div class="muted">Riesgo: ${zone.assessment.risk_score}/100</div>
    `;
    item.addEventListener("click", () => selectZone(zone.id, true));
    zonesList.appendChild(item);
  });
}

function drawMap(zones) {
  if (!map) {
    map = L.map("map", { scrollWheelZoom: false }).setView([4.5, -74.2], 5.4);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);
  }

  clearMarkers();

  zones.forEach((zone) => {
    const marker = L.marker([zone.lat, zone.lng], { icon: makeIcon(zone.assessment.level) })
      .addTo(map)
      .bindPopup(`
        <strong>${zone.name}</strong><br />
        ${zone.department}<br />
        Riesgo: ${zone.assessment.risk_score}/100<br />
        Clima: ${zone.weather.description}
      `);

    marker.on("click", () => selectZone(zone.id, false));
    markers.push(marker);
  });
}

function selectZone(zoneId, syncInputs) {
  const zone = zoneData.find((entry) => entry.id === zoneId);
  if (!zone) {
    return;
  }

  zoneSelect.value = zone.id;
  if (syncInputs) {
    latInput.value = zone.lat.toFixed(4);
    lngInput.value = zone.lng.toFixed(4);
  }

  renderAssessment(zone);
  addAlert(zone, zone.assessment.level === "critical" ? "critical" : zone.assessment.level === "high" ? "warning" : "info");
  if (map) {
    map.setView([zone.lat, zone.lng], 7);
  }
}

async function loadDashboard() {
  const response = await fetch("/api/zones");
  const payload = await response.json();
  zoneData = payload.zones;
  buildZoneList(zoneData);
  drawMap(zoneData);
  selectZone(zoneData[0].id, true);
}

async function refreshActiveZone() {
  const routeId = zoneSelect.value;
  const params = new URLSearchParams({ route_id: routeId, lat: latInput.value, lng: lngInput.value });
  const [assessmentResponse, weatherResponse] = await Promise.all([
    fetch(`/api/assess?${params.toString()}`),
    fetch(`/api/weather?lat=${encodeURIComponent(latInput.value)}&lng=${encodeURIComponent(lngInput.value)}`),
  ]);

  const assessment = await assessmentResponse.json();
  const weather = await weatherResponse.json();

  const zone = {
    id: routeId,
    name: zoneSelect.selectedOptions[0].textContent,
    department: zoneData.find((entry) => entry.id === routeId)?.department ?? "",
    lat: Number(latInput.value),
    lng: Number(lngInput.value),
    assessment,
    weather,
  };

  renderAssessment(zone);
  addAlert(zone, assessment.level === "critical" ? "critical" : assessment.level === "high" ? "warning" : "info");
}

function connectSocket() {
  if (socket && socket.readyState === WebSocket.OPEN) {
    return;
  }

  socket = new WebSocket(`${location.origin.replace(/^http/, "ws")}/ws`);
  setConnection("Conectando", "Abriendo canal en tiempo real");

  socket.addEventListener("open", () => {
    setConnection("Conectado", "Recibiendo alertas");
    socket.send(JSON.stringify({
      type: "subscribe",
      traveler_id: travelerId.value,
      traveler_name: travelerName.value,
      route_id: zoneSelect.value,
      lat: Number(latInput.value),
      lng: Number(lngInput.value),
    }));
  });

  socket.addEventListener("message", (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === "ready") {
      return;
    }

    const zone = {
      id: payload.route_id,
      name: payload.route_name,
      department: payload.department,
      lat: payload.coordinates.lat,
      lng: payload.coordinates.lng,
      assessment: payload,
      weather: {
        temperature: payload.factors.moisture / 2,
        precipitation: payload.factors.historical_pressure / 3,
        description: payload.level === "critical" ? "Lluvias críticas" : payload.level === "high" ? "Lluvia fuerte" : "Variable",
        source: "servidor",
      },
    };

    renderAssessment(zone);
    addAlert(zone, payload.type === "critical" ? "critical" : payload.type === "warning" ? "warning" : "info");
    setConnection(payload.type === "critical" ? "Crítico" : "Conectado", "Actualización recibida");
  });

  socket.addEventListener("close", () => setConnection("Desconectado", "El canal fue cerrado"));
}

zoneSelect.addEventListener("change", () => selectZone(zoneSelect.value, true));
refreshButton.addEventListener("click", refreshActiveZone);
connectButton.addEventListener("click", () => {
  connectSocket();
  refreshActiveZone();
});

await loadDashboard();