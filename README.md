# SCRC MS Asignar Priorización

Microservicio encargado de la gestión y asignación de priorizaciones cruzando datos maestros (`maestro_db`) con los archivos de priorización del cliente (PMU). 

Desarrollado con **FastAPI** y **Polars** para procesamiento rápido de datos, y **SQLAlchemy** (con **ADBC**) para interacciones de alto rendimiento con PostgreSQL.

## 🚀 Tecnologías Principales

- **Python** `>= 3.12`
- **FastAPI** (Framework Web)
- **Polars** (Procesamiento y limpieza de datos tabulares, lectura de Excel)
- **SQLAlchemy** junto con `adbc-driver-postgresql` (Conexión a BD PostgreSQL)
- **Uvicorn** (Servidor ASGI)
- **Docker** y **Docker Compose** con soporte para *Traefik*

## 📁 Estructura del Proyecto

```text
scrc_ms_asingar_priorizacion/
├── pyproject.toml        # Metadatos del proyecto
├── requirements.txt      # Dependencias del proyecto
├── docker-compose.yaml   # Configuración de despliegue con Docker y Traefik
├── Dockerfile            # Imagen Docker del servicio
├── .env                  # Variables de entorno (Configuración)
└── src/
    ├── main.py           # Punto de entrada de la aplicación FastAPI (middlewares, router principal)
    ├── app/
    │   ├── controllers/  # Definición de rutas (endpoints)
    │   │   └── asignacion_controller.py
    │   └── models/       # Lógica de negocio y base de datos
    │       └── asignacion_model.py
    └── config/           # Configuración (Base de datos, variables de entorno, seguridad)
        ├── database.py   # Conexión ADBC a PostgreSQL
        ├── settings.py   # Mapeo de variables de entorno usando pydantic-settings
        └── token.py      # Autenticación y seguridad (API Key)
```

## ⚙️ Configuración (Variables de Entorno)

El proyecto utiliza un archivo `.env` configurado mediante `pydantic-settings` (`src/config/settings.py`).
Las variables requeridas son:

- `APP_API_KEY`: Api token o llave de seguridad de la aplicación
- `DATABASE_HOST`: Host de la base de datos PostgreSQL
- `DATABASE_PORT`: Puerto de la conexión Postgres
- `DATABASE_USER`: Usuario de DB
- `DATABASE_PASS`: Contraseña de DB
- `DATABASE_NAME`: Nombre de la base de datos PostgreSQL principal
- `APP_TRAEFIK_HOST`: (Usado en el `docker-compose.yaml` para enrutar el tráfico mediante Traefik)

## 🌐 API Endpoints

Todos los endpoints (excepto el endpoint raíz en `main.py`) se encuentran bajo el prefijo configurado `/api/v1/asignacion` y requieren autenticación por token en el header, de acuerdo a la configuración en `src/config/token.py`.

### 1. **Health Check Básico**
`GET /` (En `main.py`)
Devuelve el estado básico de que el servicio está corriendo.
```json
{
  "service": "scrc_ms_asignar_priorizacion",
  "status": "running"
}
```

### 2. **Raíz de Asignación**
`GET /api/v1/asignacion/` 
Devuelve código HTTP estatus 200 indicando disponibilidad.

### 3. **Registrar y Procesar Archivo PMU**
`POST /api/v1/asignacion/pmu/registrar`
**Propósito:** Recibir un archivo Excel, cargarlo a base de datos como registros de priorización (PMU) del día actual y luego actualizar la tabla maestra (`maestro_db`).

**Flujo de operaciones:**
1. Lee y carga el archivo `.xlsx` (UploadFile) con **Polars**.
2. Realiza un *Soft-delete* (`eliminado = True`) para los registros en la tabla `pmu_priorizacion_cliente` que corresponden a la fecha de hoy.
3. Limpia y normaliza el DataFrame (renombrado de columnas, minúsculas, eliminación de tildes para brigada y actividad).
4. Inserta el nuevo PMU procesado a la tabla usando *bulk insert* vía `write_database` (Polars + ADBC).
5. **Cruce (Actualizar maestro):** Consulta `maestro_db`, hace Left Join por NIC/Cuenta y vuelca los resultados a una tabla temporal (`temp_maestro_db`) la cual sirve para actualizar el campo `priorizacion` en `maestro_db`.

**Respuesta Exitosa:**
```json
{
    "status": "procesado" // Si se realizó el cruce
}
```

### 4. **Verificar estado de PMU y Re-cruzar**
`GET /api/v1/asignacion/pmu/verificar`
**Propósito:** Confirmar si el PMU fue registrado hoy. Si existe, intenta de nuevo el proceso de cruce con la tabla `maestro_db`.

**Flujo de operaciones:**
1. Verifica en la BD `pmu_priorizacion_cliente` si hay registros agregados en la fecha actual (`fecha_registro::date = current_date`) y que no estén eliminados.
2. Si existen, ejecuta la función de cruce `actualizar_maestro`, actualizando la tabla `maestro_db`.
3. Si no existen registros PMU válidos hoy, devuelve estado `pendiente`.

**Respuestas Posibles:**
```json
{
    "status": "procesado" // Si el cruce corrió con éxito
}
```
*O si aún no se ha subido ningún PMU hoy:*
```json
{
    "status": "pendiente"
}
```

## 🐳 Despliegue con Docker

Ejecutar la construcción y despliegue usando `docker-compose`:

```bash
docker compose up -d --build
```

El servicio `scrc_ms_asignar_priorizacion` se unirá a la red externa `share_network` e interactuará dinámicamente con Traefik basándose en la variable `APP_TRAEFIK_HOST`.
