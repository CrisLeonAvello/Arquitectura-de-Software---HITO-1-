<script setup>
import { ref, computed } from "vue";

const API_BASE = "";
const NOTIFICATION_BASE = "";

window.__lastUserIdForPackages = window.__lastUserIdForPackages || "";

const data1 = ref("");
const info = ref("");
const temp = ref("");

const nombre = ref("");
const email = ref("");

const descPaquete = ref("");
const origen = ref("");
const destino = ref("");
const idUsuarioPaquete = ref("");

const codigoTracking = ref("");
const nuevoEstado = ref("IN_TRANSIT");

const buscarCodigo = ref("");

const resultadoTracking = ref(null);
const resultadoNotificaciones = ref(null);
const mensajePaquete = ref("");

const activeView = ref("usuario");
const microserviceHealth = ref({
  gateway: true,
  userService: true,
  packageService: true,
  trackingService: true,
  notificationService: true,
  redis: true,
});

const infoExtra = computed(() => {
  return info.value + temp.value;
});

async function checkMicroservicesHealth() {
  // Todos los microservicios estan disponibles por defecto
  microserviceHealth.value = {
    gateway: true,
    userService: true,
    packageService: true,
    trackingService: true,
    notificationService: true,
    redis: true,
  };
}

async function crearUsuarioMalHecho() {
  data1.value = "guardando...";
  try {
    const res = await fetch(`${API_BASE}/createUser`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: nombre.value,
        email: email.value,
      }),
    });
    const j = await res.json();
    console.log("createUser raw", j);
    if (!res.ok) {
      console.log("fallo createUser");
      data1.value = "";
      return;
    }
    window.__lastUserIdForPackages = String(j.id || "");
    idUsuarioPaquete.value = window.__lastUserIdForPackages;
    info.value = "ok usuario";
    data1.value = JSON.stringify(j);
  } catch (e) {
    console.log(e);
    data1.value = "";
  }
}

async function crearPaqueteCopiaFetch() {
  mensajePaquete.value = "...";
  let uid = idUsuarioPaquete.value;
  if (!uid && window.__lastUserIdForPackages) {
    uid = window.__lastUserIdForPackages;
  }
  try {
    const res = await fetch(`${API_BASE}/createPackage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: parseInt(uid, 10),
        title: descPaquete.value,
        description: descPaquete.value,
        origin: origen.value,
        destination: destino.value,
      }),
    });
    const j = await res.json();
    console.log(j);
    if (!res.ok) {
      console.log("error paquete");
      mensajePaquete.value = "error (ver consola)";
      return;
    }
    mensajePaquete.value = "creado: " + (j.tracking_code || "");
    temp.value = j.tracking_code || "";
  } catch (e) {
    console.log(e);
    mensajePaquete.value = "";
  }
}

async function actualizarEstadoOtraVezFetchIgual() {
  info.value = "";
  try {
    const res = await fetch(`${API_BASE}/updateStatus`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tracking_code: codigoTracking.value,
        status: nuevoEstado.value,
        location: "En proceso de actualización",
        note: `Cambio a ${traduceEstado(nuevoEstado.value)}`,
      }),
    });
    const j = await res.json();
    console.log("update", j, res.status);
    if (!res.ok) {
      console.log("no ok");
      return;
    }
    info.value = "✅ Estado actualizado correctamente";
  } catch (e) {
    console.log(e);
  }
}

async function buscarTracking() {
  resultadoTracking.value = null;
  resultadoNotificaciones.value = null;
  const code = buscarCodigo.value.trim();
  const url = `${API_BASE}/getTracking/` + encodeURIComponent(code);
  try {
    const res = await fetch(url, { method: "GET" });
    const j = await res.json();
    console.log(j);
    if (!res.ok) {
      resultadoTracking.value = { error: true, info: j };
      return;
    }
    resultadoTracking.value = j;

    const notifRes = await fetch(
      `${NOTIFICATION_BASE}/getNotifications/${encodeURIComponent(code)}`,
      { method: "GET" }
    );
    if (notifRes.ok) {
      resultadoNotificaciones.value = await notifRes.json();
    }
  } catch (e) {
    console.log(e);
    resultadoTracking.value = { error: true, info: "fallo red" };
  }
}

function limpiarCosas() {
  temp.value = "";
  data1.value = "";
}

function traduceEstado(estado) {
  const estados = {
    "CREATED": "📦 Paquete creado",
    "IN_TRANSIT": "🚚 En tránsito",
    "OUT_FOR_DELIVERY": "📍 Listo para entregar",
    "DELIVERED": "✅ Entregado",
    "EXCEPTION": "⚠️ Problema detectado"
  };
  return estados[estado] || estado;
}
</script>

<template>
  <div class="app-container">
    <div class="content-wrapper">
      <div class="tabs-container">
        <button
          class="tab-button"
          :class="{ active: activeView === 'usuario' }"
          @click="activeView = 'usuario'">
          Crear Usuario
        </button>
        <button
          class="tab-button"
          :class="{ active: activeView === 'paquete' }"
          @click="activeView = 'paquete'">
          Gestionar Paquetes
        </button>
        <button
          class="tab-button"
          :class="{ active: activeView === 'tracking' }"
          @click="activeView = 'tracking'">
          Ver Tracking
        </button>
      </div>

      <div v-if="activeView === 'usuario'" class="view-content">
        <h1>Crear Usuario</h1>
        <p style="color: #555; margin-bottom: 16px">
          Registra un nuevo usuario en el sistema
        </p>

        <div style="margin-bottom: 16px">
          <label>Nombre</label>
          <input v-model="nombre" type="text" placeholder="Tu nombre completo" />
        </div>

        <div style="margin-bottom: 16px">
          <label>Email</label>
          <input v-model="email" type="text" placeholder="tu@email.com" />
        </div>

        <button class="gradient-button" type="button" @click="crearUsuarioMalHecho">Registrar Usuario</button>

        <div v-if="data1" style="margin-top: 20px">
          <h3>Respuesta del servidor:</h3>
          <pre>{{ data1 }}</pre>
          <div v-if="idUsuarioPaquete" class="info-box">
            <strong>✓ Usuario creado exitosamente!</strong>
            <p style="margin-top: 8px;">ID Usuario: <code>{{ idUsuarioPaquete }}</code></p>
            <p>Este ID se utilizará para crear paquetes</p>
          </div>
        </div>
      </div>

      <div v-if="activeView === 'paquete'" class="view-content">
        <h1>Gestionar Paquetes</h1>
        <p style="color: #555; margin-bottom: 16px">
          Crea nuevos paquetes o actualiza su estado
        </p>

        <hr />

        <h2>1. Crear Paquete</h2>
        <p style="font-size: 13px; color: #888; margin-bottom: 12px;">
          ID usuario (se rellena automáticamente si creaste uno antes):
        </p>
        <input
          v-model="idUsuarioPaquete"
          type="text"
          placeholder="ID del usuario"
          style="margin-bottom: 12px;" />

        <div style="margin-bottom: 16px">
          <label>Descripción del Paquete</label>
          <input v-model="descPaquete" type="text" placeholder="Ej: Laptop, Libro, etc." />
        </div>

        <div style="margin-bottom: 16px">
          <label>Origen</label>
          <input v-model="origen" type="text" placeholder="Ciudad de origen" />
        </div>

        <div style="margin-bottom: 16px">
          <label>Destino</label>
          <input v-model="destino" type="text" placeholder="Ciudad de destino" />
        </div>

        <button class="gradient-button" type="button" @click="crearPaqueteCopiaFetch">Crear Paquete</button>

        <div v-if="mensajePaquete" style="margin-top: 16px">
          <p style="color: #2e7d32; font-weight: bold;">{{ mensajePaquete }}</p>
        </div>

        <div v-if="temp" class="info-box" style="margin-top: 16px">
          <strong>✓ Paquete creado!</strong>
          <p style="margin-top: 8px;">Código de tracking: <code>{{ temp }}</code></p>
          <p>Usa este código para consultar el estado</p>
        </div>

        <hr style="margin: 24px 0;" />

        <h2>2. Actualizar Estado del Paquete</h2>

        <div style="margin-bottom: 16px">
          <label>Código de Tracking</label>
          <input v-model="codigoTracking" type="text" placeholder="Código TRK-..." />
        </div>

        <div style="margin-bottom: 16px">
          <label>Nuevo Estado</label>
          <select v-model="nuevoEstado">
            <option value="CREATED">📦 Paquete creado</option>
            <option value="IN_TRANSIT">🚚 En tránsito</option>
            <option value="OUT_FOR_DELIVERY">📍 Listo para entregar</option>
            <option value="DELIVERED">✅ Entregado</option>
            <option value="EXCEPTION">⚠️ Problema detectado</option>
          </select>
        </div>

        <button class="gradient-button" type="button" @click="actualizarEstadoOtraVezFetchIgual">Actualizar Estado</button>

        <div v-if="info" style="margin-top: 16px">
          <p style="color: #2e7d32; font-weight: bold;">{{ info }}</p>
        </div>
      </div>

      <div v-if="activeView === 'tracking'" class="view-content">
        <h1>Consultar tracking</h1>
        <p style="color: #555; margin-bottom: 16px">
          Busca el estado de tu paquete en tiempo real
        </p>

        <div style="display: flex; gap: 8px; margin-bottom: 16px;">
          <input
            v-model="buscarCodigo"
            type="text"
            placeholder="codigo de tracking"
            style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px;" />
          <button class="gradient-button" type="button" @click="buscarTracking">Buscar</button>
          <button class="gradient-button" type="button" @click="limpiarCosas">Limpiar</button>
        </div>

        <div v-if="resultadoTracking" style="margin-top: 12px">
          <template v-if="resultadoTracking.error">
            <p style="color: #d32f2f; font-weight: bold;">No encontrado</p>
            <pre style="background: #ffecec; padding: 8px; border-radius: 4px;">{{ JSON.stringify(resultadoTracking.info, null, 2) }}</pre>
          </template>
          <template v-else>
            <div class="tracking-result">
              <h3>Detalles del Paquete</h3>
              <p><strong>Código:</strong> {{ resultadoTracking.tracking_code }}</p>
              <p><strong>Total Eventos:</strong> {{ resultadoTracking.total }}</p>

              <h4>Historial de Eventos ({{ resultadoTracking.events.length }})</h4>
              <ul class="events-list">
                <li v-for="(ev, i) in resultadoTracking.events" :key="i" class="event-item">
                  <span class="event-status">{{ traduceEstado(ev.status) }}</span>
                  <span class="event-location">📍 {{ ev.location }}</span>
                  <span class="event-note">{{ ev.note || "Sin notas" }}</span>
                  <span class="event-time" v-if="ev.at">{{ new Date(ev.at).toLocaleString() }}</span>
                </li>
              </ul>

              <div v-if="resultadoNotificaciones" style="margin-top: 20px">
                <h4>Notificaciones ({{ resultadoNotificaciones.total }})</h4>
                <ul class="notifications-list">
                  <li v-for="(n, i) in resultadoNotificaciones.notifications" :key="i" class="notification-item">
                    {{ n.message }}
                  </li>
                </ul>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
}

.content-wrapper {
  max-width: 900px;
  width: 100%;
  padding: 32px;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.tabs-container {
  display: flex;
  gap: 12px;
  margin-bottom: 32px;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 12px;
}

.tab-button {
  padding: 10px 20px;
  border: none;
  background-color: transparent;
  color: #666;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 3px solid transparent;
  margin-bottom: -15px;
}

.tab-button:hover {
  color: #9c27b0;
}

.tab-button.active {
  color: #9c27b0;
  border-bottom-color: #9c27b0;
}

.view-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

h1 {
  color: #333;
  font-size: 28px;
  margin-bottom: 8px;
}

h2 {
  color: #444;
  font-size: 18px;
  margin-top: 24px;
  margin-bottom: 12px;
}

h3 {
  color: #555;
  font-size: 16px;
  margin-bottom: 12px;
}

h4 {
  color: #666;
  font-size: 14px;
  margin-top: 16px;
  margin-bottom: 10px;
}

p {
  color: #555;
  margin-bottom: 8px;
  line-height: 1.6;
}

hr {
  border: none;
  border-top: 1px solid #e0e0e0;
  margin: 20px 0;
}

label {
  display: block;
  margin-bottom: 6px;
  color: #333;
  font-weight: 500;
}

input, select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 12px;
  width: 100%;
  transition: all 0.3s ease;
}

input:focus, select:focus {
  outline: none;
  border-color: #9c27b0;
  box-shadow: 0 0 8px rgba(156, 39, 176, 0.2);
}

.gradient-button {
  background: linear-gradient(135deg, #9c27b0 0%, #00bcd4 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  margin: 8px 4px 8px 0;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(156, 39, 176, 0.3);
}

.gradient-button:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 6px 20px rgba(0, 188, 212, 0.4);
}

.gradient-button:active {
  transform: translateY(-1px) scale(1.02);
  box-shadow: 0 4px 12px rgba(156, 39, 176, 0.3);
}

.architecture-diagram {
  background-color: #f9f9f9;
  padding: 24px;
  border-radius: 8px;
  margin: 24px 0;
  border: 2px solid #e8e8e8;
}

.service-block {
  background-color: white;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  transition: all 0.3s ease;
  margin-bottom: 16px;
}

.service-block:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(156, 39, 176, 0.15);
  border-color: #9c27b0;
}

.service-icon {
  font-size: 16px;
  margin-bottom: 8px;
  font-weight: bold;
}

.service-title {
  font-weight: 600;
  color: #333;
  font-size: 14px;
  margin-bottom: 4px;
}

.service-port {
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
}

.database-info {
  font-size: 12px;
  color: #666;
  background-color: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.health-indicator {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.health-indicator.healthy {
  background-color: #c8e6c9;
  color: #2e7d32;
}

.health-indicator.unhealthy {
  background-color: #ffcdd2;
  color: #c62828;
}

.frontend-block {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
}

.frontend-block .service-title,
.frontend-block .service-port {
  color: white;
}

.gateway-block {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  border-color: #f5576c;
}

.gateway-block .service-title,
.gateway-block .service-port {
  color: white;
}

.microservices-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 16px 0;
}

@media (max-width: 768px) {
  .microservices-grid {
    grid-template-columns: 1fr;
  }
}

.user-service {
  border-left: 4px solid #4CAF50;
}

.package-service {
  border-left: 4px solid #2196F3;
}

.tracking-service {
  border-left: 4px solid #FF9800;
}

.notification-service {
  border-left: 4px solid #9C27B0;
}

.redis-block {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
  border-color: #fee140;
}

.redis-block .service-title,
.redis-block .service-port {
  color: white;
}

.arrow-down {
  text-align: center;
  font-size: 20px;
  color: #9c27b0;
  margin: 8px 0;
}

.flow-info {
  background-color: #f0f4ff;
  border-left: 4px solid #9c27b0;
  padding: 16px;
  border-radius: 6px;
  margin: 20px 0;
}

.flow-step {
  padding: 10px;
  margin: 8px 0;
  background-color: white;
  border-radius: 4px;
  font-size: 14px;
  border-left: 3px solid #00bcd4;
}

.tracking-result {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.status-badge {
  display: inline-block;
  background: linear-gradient(135deg, #9c27b0 0%, #00bcd4 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.events-list {
  list-style: none;
  margin: 12px 0;
}

.event-item {
  background-color: white;
  padding: 12px;
  margin: 8px 0;
  border-left: 4px solid #00bcd4;
  border-radius: 4px;
  font-size: 13px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.event-status {
  font-weight: 600;
  background-color: #e3f2fd;
  color: #1565c0;
  padding: 2px 8px;
  border-radius: 3px;
}

.event-location {
  color: #666;
}

.event-note {
  color: #999;
  font-size: 12px;
}

.event-time {
  color: #ccc;
  font-size: 11px;
  margin-left: auto;
}

.notifications-list {
  list-style: none;
  margin: 12px 0;
}

.notification-item {
  background-color: white;
  padding: 12px;
  margin: 8px 0;
  border-left: 4px solid #9c27b0;
  border-radius: 4px;
  font-size: 13px;
}

.info-box {
  background-color: #f0f4ff;
  border-left: 4px solid #9c27b0;
  padding: 16px;
  border-radius: 6px;
  margin: 16px 0;
}

pre {
  background-color: #f4f4f4;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 12px;
  margin-bottom: 12px;
  border: 1px solid #e0e0e0;
}
</style>
