# Prometheus y Grafana

## Descripción

Este directorio contiene la configuración para Prometheus y Grafana como herramientas de observabilidad del sistema de microservicios.

### Prometheus
- **Puerto**: 9090
- **Descripción**: Sistema de almacenamiento y consulta de métricas de tiempo real
- **Configuración**: `prometheus.yml`

### Grafana
- **Puerto**: 3000
- **Usuario**: admin
- **Contraseña**: admin
- **Descripción**: Visualización de métricas e dashboards

## Arquitectura de Observabilidad

Según el informe Hito 1, el sistema captura las siguientes métricas:

1. **Latencia**: Tiempo promedio de procesamiento de requests
2. **Throughput**: Peticiones por segundo (req/s)
3. **Tasa de Errores**: Porcentaje de requests fallidos
4. **Uso de Recursos**: Memoria y CPU consumidos por servicio

## Acceso

Una vez iniciado el docker-compose:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## Configuración de Data Sources

Grafana está preconfigurado con Prometheus como data source en `provisioning/datasources/prometheus.yml`

## Dashboards

Un dashboard base se provisiona automáticamente con métricas de:
- Latencia promedio por servicio
- Throughput (req/s)
- Tasa de errores
- Uso de memoria

## Requisitos en Microservicios

Cada microservicio FastAPI debe exponer métricas en:
```
GET /metrics
```

Utilizar `prometheus_client` para instrumentar:

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
import time

# Métricas
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
active_connections = Gauge('http_active_connections', 'Active HTTP connections')

# En middleware o antes de cada request
start_time = time.time()
# ... procesar request ...
duration = time.time() - start_time
request_duration.labels(method='GET', endpoint='/endpoint').observe(duration)

@app.get('/metrics')
async def metrics():
    return Response(generate_latest(REGISTRY), media_type='text/plain')
```

## Próximas Mejoras

- Agregar alertas en Prometheus
- Crear dashboards específicos por servicio
- Integrar logs con ELK Stack (Elasticsearch, Logstash, Kibana)
- Implementar trazadistribuidas con Jaeger
