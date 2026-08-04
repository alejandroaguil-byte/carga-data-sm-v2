# 🚀 Carga Data SM_v2 — Sistema ETL de Automatización FTP a Microsoft SQL Server

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Database-MSSQL-red](https://img.shields.io/badge/Database-SQL%20Server-red.svg)](https://www.microsoft.com/sql-server/)
[![Protocol-FTP-green](https://img.shields.io/badge/Protocol-FTP-green.svg)](https://en.wikipedia.org/wiki/File_Transfer_Protocol)
[![License-MIT-yellow](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Carga Data SM_v2** es una solución ETL (Extract, Transform, Load) automatizada diseñada para la extracción desatendida de datos operativos desde un servidor FTP (archivos HPSM CSV), su posterior deduplicación, limpieza, vinculación relacional con proyectos principales y carga directa a una base de datos Microsoft SQL Server (`Sharepoint_Proyectos`).

---

## 📌 Características Principales

- 🔄 **Descarga Desatendida FTP**: Conexión remota automatizada y descarga de los reportes `registrosRF_SD-SM.csv` y `registrosSM-RFC.csv`.
- 🧹 **Limpieza y Deduplicación al Vuelo**: Tratamiento de valores nulos, eliminación de caracteres especiales, y deduplicación por clave primaria (`CC_INCIDENT_ID` y `NUMBER`).
- 🔗 **Relacionamiento Inteligente por RegEx**: Extracción dinámica de códigos de proyectos desde campos de texto libre (`BRIEF_DESCRIPTION` y `CC_PROYECT_NUMBER`) y mapeo directo con la tabla maestra `dbo.Proyectos` (`ID_Proyecto` y `Numero_Proyecto_Limpio`).
- 🛡️ **Garantía de Integridad**: Validaciones cruzadas automáticas al finalizar la carga que verifican el 100% de coincidencia entre registros leídos y registros almacenados.
- ⚙️ **Portabilidad y Despliegue Sencillo**: Estructura modular comentada paso a paso para rápida instalación en entornos Linux o Windows Server.
- ⏰ **Programación Automática**: Diseñado para ejecutarse dos veces al día en horarios estratégicos (**08:45 AM** y **14:15 PM**).

---

## 📁 Estructura del Proyecto

```text
Carga Data SM_v2/
├── README.md                           # Documentación principal del repositorio
├── PLAN_PROYECTO.md                    # Plan de proyecto, arquitectura y mapa de fases
├── PASO_A_PASO_DESPLIEGUE_Y_PROGRAMACION.md # Guía detallada de despliegue y cron/task scheduler
├── procesar_datos_ftp.py               # Script principal del proceso ETL (completamente documentado)
├── Conexion BD                         # Archivo de parámetros de conexión a SQL Server
├── Conexion FTP                        # Archivo de parámetros de conexión al servidor FTP
├── consultas_ejemplo_cruces.sql        # Consultas SQL para analítica y verificación de datos
├── requirements.txt                    # Dependencias Python (pymssql)
├── registrosRF_SD-SM.csv               # Ejemplo de dataset de incidentes/requerimientos SD
├── registrosSM-RFC.csv                 # Ejemplo de dataset de solicitudes de cambio RFC
└── skills/
    └── carga-data-sm-etl/
        └── SKILL.md                    # Skill de automatización e instrucciones para Antigravity AI
```

---

## 🛠️ Requisitos Previos

- **Python**: Versión 3.8 o superior.
- **Base de Datos**: Microsoft SQL Server con la base de datos `Sharepoint_Proyectos` alojada.
- **Acceso a Red**: Conectividad al servidor FTP remoto (puerto 21) y SQL Server (puerto 1433).
- **Librería del Sistema**: En servidores Linux se requiere `FreeTDS` (`libfree-tds-dev` en Ubuntu/Debian o `free-tds-devel` en RHEL/CentOS).

---

## ⚙️ Instalación y Configuración

### 1. Clonar el Repositorio e Instalar Dependencias

```bash
# Clonar el repositorio
git clone https://github.com/alejandroaguil-byte/carga-data-sm-v2.git
cd carga-data-sm-v2

# Crear entorno virtual (Recomendado)
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Archivos de Conexión

Edite los archivos de configuración con las credenciales correspondientes a su entorno:

#### `Conexion BD`
```text
Server: IP_O_HOST_SQL_SERVER
Port: 1433
User: usuario_sql
Password: contrasena_sql
Database: Sharepoint_Proyectos
```

#### `Conexion FTP`
```text
Server: ftp.midominio.com
Port: 21
Usuario: usuario_ftp
Contraseña: contrasena_ftp
Folder: HPSM
```

---

## 🚀 Ejecución Manual

Para ejecutar manualmente el proceso ETL y verificar la carga:

```bash
python3 procesar_datos_ftp.py
```

### Ejemplo de Salida Esperada:

```text
==================================================
PROCESO DE CARGA Y VALIDACIÓN DE DATOS FTP A MSSQL (V2)
==================================================
[FTP] Conectando a 200.14.222.162:21...
[FTP] Autenticación exitosa.
[FTP] Descargando 'registrosRF_SD-SM.csv'...
[FTP] Descargando 'registrosSM-RFC.csv'...
[CSV] Parseando datos de archivos CSV...
[MSSQL] Cargando mapa de proyectos desde 'dbo.Proyectos'...
[ETL] Enrumando y relacionando registros con 'dbo.Proyectos'...
[MSSQL] Truncando datos de las tablas existentes...
[MSSQL] Insertando registros enriquecidos...

==================================================
VALIDACIÓN Y COMPARACIÓN DE DATOS (CSV vs MSSQL)
==================================================
Tabla 1 (dbo.registrosRF_SD_SM): Coincidencia: ✅ CORRECTO (100% de datos insertados)
Tabla 2 (dbo.registrosSM_RFC):     Coincidencia: ✅ CORRECTO (100% de datos insertados)

[PROCESO FINALIZADO CON ÉXITO]
```

---

## ⏰ Programación de Tareas Automáticas

El proyecto está diseñado para ejecutarse automáticamente dos veces al día: **08:45 AM** y **14:15 PM**.

### En Linux (vía Cron)

Edite el archivo cron (`crontab -e`) e incluya:

```cron
# Ejecución diaria a las 08:45 AM
45 8 * * * /ruta/al/proyecto/venv/bin/python3 /ruta/al/proyecto/procesar_datos_ftp.py >> /ruta/al/proyecto/ejecucion.log 2>&1

# Ejecución diaria a las 14:15 PM
15 14 * * * /ruta/al/proyecto/venv/bin/python3 /ruta/al/proyecto/procesar_datos_ftp.py >> /ruta/al/proyecto/ejecucion.log 2>&1
```

### En Windows (vía Task Scheduler)

```cmd
schtasks /create /tn "CargaDataSM_0845" /tr "\"C:\Ruta\Al\Proyecto\venv\Scripts\python.exe\" \"C:\Ruta\Al\Proyecto\procesar_datos_ftp.py\"" /sc daily /st 08:45 /ru SYSTEM
schtasks /create /tn "CargaDataSM_1415" /tr "\"C:\Ruta\Al\Proyecto\venv\Scripts\python.exe\" \"C:\Ruta\Al\Proyecto\procesar_datos_ftp.py\"" /sc daily /st 14:15 /ru SYSTEM
```

Para una guía detallada paso a paso, consulte [PASO_A_PASO_DESPLIEGUE_Y_PROGRAMACION.md](file:///PASO_A_PASO_DESPLIEGUE_Y_PROGRAMACION.md).

---

## 📊 Arquitectura de Datos y Consultas SQL

El script realiza la inserción en las siguientes tablas de SQL Server:
- `dbo.registrosRF_SD_SM` (Incidentes y solicitudes de servicio)
- `dbo.registrosSM_RFC` (Solicitudes de cambio)

Para realizar cruces analíticos entre los proyectos y sus respectivas RFCs o incidentes, utilice los ejemplos del archivo [consultas_ejemplo_cruces.sql](file:///consultas_ejemplo_cruces.sql).

---

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).
