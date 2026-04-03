# Arquitectura de Software - HITO 1: Migración a Microservicios

Este proyecto implementa una migración completa de un monolito a una arquitectura de microservicios usando el **Patrón Strangler**, permitiendo coexistencia temporal entre el sistema legado y los nuevos servicios.

## 📋 Descripción General

**Objetivo:** Transformar un sistema monolítico de trazabilidad de paquetes en una arquitectura escalable basada en microservicios.

**Sistema:** Plataforma de tracking de paquetes con gestión de usuarios, creación de paquetes, actualización de estados y notificaciones asincrónicas.

## 🏗️ Arquitectura Implementada

### Servicios Creatdos

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vue 3)                         │
│                    puerto 3000                              │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              Nginx API Gateway (puerto 8080)                │
│  Punto único de entrada - Enrutamiento de requests         │
└────────────┬──────────────┬──────────────┬─────────────────┘
             │              │              │
       ┌─────↓────┐  ┌─────↓────┐  ┌─────↓────┐
       │  User    │  │ Package  │  │ Tracking │
       │ Service  │  │ Service  │  │ Service  │
       │  8001    │  │  8002    │  │  8003    │
       └─────┬────┘  └─────┬────┘  └─────┬────┘
             │             │             │
       ┌─────↓────┐  ┌─────↓────┐  ┌─────↓────┐
       │ users_db │  │packages_ │  │tracking_ │
       │          │  │   db     │  │   db     │
       └──────────┘  └──────────┘  └─────┬────┘
                                          │
                                   ┌──────↓──────┐
                                   │   Redis     │
                                   │ (Pub/Sub)   │
                                   └──────┬──────┘
                                          │
                                   ┌──────↓──────────────┐
                               ┌───┴──┐ Notification   │
                               │      │   Service      │
                               │      │    8004        │
                               └─────┬┘                │
                                     │                │
                               ┌─────↓────┐           │
                               │notification_│         │
                               │   db      │          │
                               └───────────┘          │
                                  [Listeners]
```

### Base de Datos - Separación por Servicio

Cada microservicio posee su propia base de datos PostgreSQL independiente:

| Servicio | Base de Datos | Tablas | Puerto |
|----------|--------------|--------|--------|
| **User Service** | users_db | users | 5433 |
| **Package Service** | packages_db | packages | 5434 |
| **Tracking Service** | tracking_db | tracking_events | 5435 |
| **Notification Service** | notifications_db | notifications | 5436 |
| **Monolito (legacy)** | package_tracking | tracking_data (legacy) | 5432 |

### Patrón Database per Service

✅ **Ventajas implementadas:**
- Desacoplamiento de esquema compartido
- Cada servicio es independiente
- Escalabilidad horizontal por servicio

❌ **Eliminón:** Duplicación de datos (username_redundant, user_email_copy) que existía en la tabla tracking_data del monolito.

## 🚀 Cómo Levantar el Sistema

### Requisitos
- Docker 20.10+
- Docker Compose 2.0+
- Puertos 8080, 8001-8004, 3000, 5432-5436, 6379 disponibles

### Paso 1: Levantar todos los servicios

```bash
cd Arquitectura-de-Software---HITO-1-
docker-compose up --build
```

### Paso 2: Esperar inicialización

```
✓ Postgres services: 5-10 segundos
✓ Redis: 2-3 segundos
✓ FastAPI services: 3-5 segundos
✓ Nginx: 1 segundo
✓ Frontend: 5 segundos
```

**Tiempo total estimado: 15-20 segundos**

### Paso 3: Acceder a la aplicación

- **Frontend:** http://localhost:3000
- **API Gateway:** http://localhost:8080
- **Servicios individuales:**
  - User Service: http://localhost:8001
  - Package Service: http://localhost:8002
  - Tracking Service: http://localhost:8003
  - Notification Service: http://localhost:8004

## 📡 Endpoints Disponibles

### User Service

```
POST   /createUser              → Crear usuario
GET    /getUsers               → Listar usuarios
GET    /validateUser/{user_id} → Validar usuario (interno)
GET    /health                 → Health check
```

**Ejemplo:**
```bash
curl -X POST http://localhost:8080/createUser \
  -H "Content-Type: application/json" \
  -d '{"username": "juan", "email": "juan@example.com"}'
```

### Package Service

```
POST   /createPackage         → Crear paquete
GET    /getAllPackages        → Listar paquetes
GET    /health               → Health check
```

**Ejemplo:**
```bash
curl -X POST http://localhost:8080/createPackage \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "title": "Mi paquete",
    "description": "Contenido",
    "origin": "Madrid",
    "destination": "Barcelona"
  }'
```

### Tracking Service

```
POST   /updateStatus          → Actualizar estado + evento
GET    /getTracking/{code}    → Obtener historial
GET    /health                → Health check
```

**Ejemplo:**
```bash
curl -X POST http://localhost:8080/updateStatus \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_code": "TRK-123456-7890",
    "status": "IN_TRANSIT",
    "location": "Madrid",
    "note": "En tránsito hacia Barcelona"
  }'
```

### Notification Service

```
GET    /getNotifications/{code}  → Ver notificaciones
GET    /health                   → Health check
```

## 🔄 Flujo de Comunicación

### Caso de Uso: Crear Paquete

```
1. Frontend POST /createPackage
   ↓
2. Nginx enruta a Package Service
   ↓
3. Package Service requiere validar user_id
   ├─→ REST: llamada sincrónica a User Service
   ├─→ User Service retorna: usuario existe ✓
   ↓
4. Package Service genera tracking_code
5. Package Service persiste en packages_db
6. Retorna código de tracking al cliente
```

### Caso de Uso: Actualizar Estado + Notificación

```
1. Frontend POST /updateStatus
   ↓
2. Nginx enruta a Tracking Service
   ↓
3. Tracking Service inserta evento en BD
   ↓
4. Tracking Service publica evento a Redis:
   canal: "status_updates"
   evento: {tracking_code, status, location, note, ...}
   ↓
5. Notification Service escucha en background
   ├─→ Recibe evento
   ├─→ Construye mensaje
   ├─→ Persiste en notifications_db
6. Desacoplamiento: Si Notification cae,
   Tracking Service sigue funcionando
```

## 🏛️ Patrones Arquitectónicos

### 1. API Gateway (Nginx)
**Problema:** Frontend acoplado a URLs de monolito
**Solución:** Nginx como punto único (puerto 8080)
- Enruta según prefijo de URL
- Facilita migración gradual
- Esconde topología interna

### 2. Database per Service
**Problema:** Tabla tracking_data mezclaba 4 dominios
**Solución:** BD independiente por servicio
- User Service → users_db
- Package Service → packages_db
- Tracking Service → tracking_db
- Notification Service → notifications_db

### 3. Strangler Pattern
**Problema:** Reescribir monolito de una vez = alto riesgo
**Solución:** Migración incremental
- Nginx enruta nuevos servicios
- Endpoints legacy en monolito siguen funcionando
- Desactivar legacy gradualmente cuando se valida nuevo

### 4. Saga (Asincrónica con Eventos)
**Problema:** Transacción ACID global entre múltiples BDs
**Solución:** Saga coreografiada por eventos Redis
- Tracking Service publica eventos
- Notification Service consume independientemente
- Falla de A no afecta a B

### 5. REST Síncrono
**Escenario:** Package Service necesita validar usuario
**Solución:** Llamada HTTP sincrónica
```python
user_response = httpx.get(
    f"http://user-service:8001/validateUser/{user_id}"
)
```

## 📁 Estructura del Proyecto

```
.
├── services/                          # Nuevos microservicios
│   ├── nginx/                        # API Gateway
│   │   ├── Dockerfile
│   │   ├── nginx.conf               # Configuración de rutas
│   │   └── .dockerignore
│   ├── user-service/
│   │   ├── main.py                  # Endpoints: createUser, getUsers
│   │   ├── models.py                # ORM: User model
│   │   ├── database.py              # Configuración DB
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── .dockerignore
│   ├── package-service/
│   │   ├── main.py                  # Endpoints: createPackage
│   │   ├── models.py                # ORM: Package model
│   │   ├── database.py
│   │   ├── utils.py                 # generate_tracking_code()
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── .dockerignore
│   ├── tracking-service/
│   │   ├── main.py                  # Endpoints: updateStatus, getTracking
│   │   ├── models.py                # ORM: TrackingEvent model
│   │   ├── database.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── .dockerignore
│   └── notification-service/
│       ├── main.py                  # Consumidor Redis + endpoint
│       ├── models.py                # ORM: Notification model
│       ├── database.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── .dockerignore
├── backend/                           # Monolito (legacy, puerto 8000)
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── seed.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .dockerignore
├── frontend/                          # Vue 3 (puerto 3000)
│   ├── src/
│   │   └── App.vue (URLs actualizadas a puerto 8080)
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml               # Orquestación completa
└── README.md                        # Este archivo
```

## 🧪 Verificación

### Health Checks

```bash
# API Gateway
curl http://localhost:8080/health

# Servicios individuales
curl http://localhost:8001/health  # User Service
curl http://localhost:8002/health  # Package Service
curl http://localhost:8003/health  # Tracking Service
curl http://localhost:8004/health  # Notification Service
```

### Flujo Completo (paso a paso)

```bash
# 1. Crear usuario
USER_ID=$(curl -X POST http://localhost:8080/createUser \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com"}' | jq .id)

# 2. Crear paquete
TRACKING=$(curl -X POST http://localhost:8080/createPackage \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": $USER_ID, \"title\": \"Test\", \"description\": \"Test\", \"origin\": \"A\", \"destination\": \"B\"}" \
  | jq -r .tracking_code)

# 3. Actualizar estado
curl -X POST http://localhost:8080/updateStatus \
  -H "Content-Type: application/json" \
  -d "{\"tracking_code\": \"$TRACKING\", \"status\": \"IN_TRANSIT\", \"location\": \"Madrid\", \"note\": \"En tránsito\"}"

# 4. Consultar tracking
curl http://localhost:8080/getTracking/$TRACKING | jq

# 5. Ver notificaciones
curl http://localhost:8004/getNotifications/$TRACKING | jq
```

## 📊 Cambios Clave vs. Monolito

| Aspecto | AS-IS (Monolito) | TO-BE (Microservicios) |
|---------|------------------|------------------------|
| **Arquitectura** | Monolítico | Microservicios |
| **Puertos** | 1 (8000) | 5 (8080, 8001-8004) |
| **BDs** | 1 compartida | 4 independientes |
| **Tabla de tracking** | `tracking_data` (denormalizada con duplicados) | `tracking_events` (normalizada) |
| **Notificaciones** | Sincrónas (print) | Asincrónas (Redis Queue) |
| **Acoplamiento** | Endpoints ↔ SQLAlchemy | Servicios desacoplados |
| **Escalabilidad** | Monolítica | Por servicio |
| **Resiliencia** | Falla total | Aislamiento de fallos |

## ⚠️ Limitaciones (HITO 1)

- ❌ **Sin autenticación:** No se implementó (en alcance excluido)
- ❌ **Sin observabilidad:** Prometheus/Grafana omitidos
- ❌ **Sin Circuit Breaker:** Resilencia pendiente
- ⏳ **Coexistencia temporal:** Monolito aún activo (será retirado en HITO 2)
- 📝 **Notificaciones simuladas:** No hay integración email/SMS real

## 🚀 Próximos Pasos (HITO 2+)

1. **Circuit Breaker:** Implementar resilencia en llamadas inter-servicio
2. **Observabilidad:** Prometheus metrics + Grafana dashboards
3. **Autenticación:** JWT o OAuth2
4. **Health Checks avanzados:** Con dependencias transversales
5. **Logging centralizado:** ELK stack o similar
6. **API Versioning:** Soportar múltiples versiones
7. **Rate Limiting:** Por usuario/IP
8. **Caché distribuido:** Redis para consultas frecuentes
9. **Retiro del monolito:** Una vez validados todos los servicios

## 📚 Documentación de Referencia

- **Patrón Strangler:** https://martinfowler.com/bliki/StranglerApplication.html
- **Microservicios:** https://martinfowler.com/microservices/
- **Database per Service:** https://microservices.io/patterns/data/database-per-service.html
- **Saga Pattern:** https://microservices.io/patterns/data/saga.html
- **API Gateway:** https://microservices.io/patterns/apigateway.html

## 📝 Licencia

Por definir

---

**Autores:** Cristian León, Fernanda Calderón
**Profesor:** Matías Vargas
**Fecha:** 03 de abril de 2026
