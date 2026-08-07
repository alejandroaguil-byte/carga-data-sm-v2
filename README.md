# 🚀 Carga Data SM_v2 — Sistema ETL de Automatización FTP & SGA a Microsoft SQL Server (v2.2.0)

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Database-MSSQL-red](https://img.shields.io/badge/Database-SQL%20Server-red.svg)](https://www.microsoft.com/sql-server/)
[![Protocol-FTP-green](https://img.shields.io/badge/Protocol-FTP-green.svg)](https://en.wikipedia.org/wiki/File_Transfer_Protocol)
[![License-MIT-yellow](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release-v2.2.0-blueviolet](https://img.shields.io/badge/Release-v2.2.0-blueviolet.svg)](https://github.com/alejandroaguil-byte/carga-data-sm-v2/releases/tag/v2.2.0)

**Carga Data SM_v2** es una solución ETL (Extract, Transform, Load) automatizada diseñada para la extracción desatendida de datos operativos desde:
1. Servidor FTP (archivos HPSM CSV: incidentes y solicitudes de cambio).
2. Base de Datos MSSQL SGA (`blixter_prod`: tabla de backlog operacionales `CT_BACKLOG_OPERACIONES2`).

Los datos son procesados, limpiados, enriquecidos mediante vinculación relacional lógica con la tabla de proyectos maestros `dbo.Proyectos`, insertados de forma masiva en la base de datos `Sharepoint_Proyectos`, y **reportados mediante notificaciones automáticas por correo electrónico con bitácora de ejecución**.

---

## 📌 Características Principales

- 🔄 **Descarga Desatendida FTP**: Conexión remota automatizada y descarga de reportes HPSM (`registrosRF_SD-SM.csv` y `registrosSM-RFC.csv`).
- 🗄️ **Extracción Desatendida de BD SGA**: Lectura y extracción masiva desde la tabla `CT_BACKLOG_OPERACIONES2` (162,221+ registros y 104 columnas) en la base de datos SGA (`blixter_prod`).
- 🧹 **Limpieza y Deduplicación al Vuelo**: Tratamiento de valores nulos, normalización de campos y deduplicación por clave primaria.
- 🔗 **Relacionamiento Inteligente por RegEx**: Extracción dinámica de números de proyecto desde texto libre (`BRIEF_DESCRIPTION`, `CC_PROYECT_NUMBER` y `NRO_PROYECTO`) y mapeo directo con `dbo.Proyectos` (`ID_Proyecto` y `Numero_Proyecto_Limpio`).
- 💯 **Conservación Completa de Datos (100%)**: Carga del 100% de los registros de Backlog independientemente de si cruzan con la tabla de proyectos (`ID_Proyecto` = `NULL` para registros sin coincidencia).
- 🛡️ **Garantía de Integridad**: Validaciones cruzadas automáticas al finalizar la carga que verifican el 100% de coincidencia entre registros leídos y almacenados en las 3 tablas de destino.
- 📧 **Notificaciones Automatizadas por Email**: Módulo `ejecutar_y_notificar.py` que captura logs (`ejecucion.log`) y notifica resultados (`ÉXITO` o `ERROR`) por correo electrónico vía SMTP.
- ⏰ **Programación Automática**: Diseñado para ejecutarse diariamente a las **09:00 AM** y **14:45 PM**.

---

## 📁 Estructura del Proyecto

```text
Carga Data SM_v2/
├── README.md                           # Documentación principal del repositorio
├── PLAN_PROYECTO.md                    # Plan de proyecto, arquitectura y mapa de fases
├── PASO_A_PASO_DESPLIEGUE_Y_PROGRAMACION.md # Guía detallada de despliegue y cron/task scheduler
├── procesar_datos_ftp.py               # Script principal del proceso ETL (completamente documentado)
├── ejecutar_y_notificar.py             # Script wrapper para ejecución desatendida, bitácora y envio de correo
├── Conexion BD                         # Parámetros de conexión a SQL Server Destino (Sharepoint_Proyectos)
├── Conexion BD SGA                     # Parámetros de conexión a SQL Server Origen SGA (blixter_prod)
├── Conexion FTP                        # Parámetros de conexión al servidor FTP
├── Conexion Email                      # Parámetros de configuración SMTP para notificaciones
├── consultas_ejemplo_cruces.sql        # Consultas SQL de ejemplo para cruzar incidentes y RFCs con Proyectos
├── consultas_ejemplo_cruces_backlog.sql # Consultas SQL para cruzar CT_BACKLOG_OPERACIONES2 con Proyectos
├── requirements.txt                    # Dependencias Python (pymssql)
├── registrosRF_SD-SM.csv               # Dataset de prueba de incidentes SD
├── registrosSM-RFC.csv                 # Dataset de prueba de solicitudes de cambio RFC
└── skills/
    └── carga-data-sm-etl/
        └── SKILL.md                    # Skill de automatización e instrucciones para Antigravity AI
```

---

## 🛠️ Requisitos Previos

- **Python**: Versión 3.8 o superior.
- **Bases de Datos**:
  - Microsoft SQL Server Destino (`Sharepoint_Proyectos`).
  - Microsoft SQL Server Origen SGA (`blixter_prod`).
- **Acceso a Red**: Conectividad a FTP (puerto 21), SQL Server (puerto 1433) y SMTP (puerto 587 o 465).
- **Librería del Sistema**: En Linux se requiere `FreeTDS` (`libfreetds-dev` en Ubuntu/Debian o `free-tds-devel` en RHEL/CentOS).

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

#### `Conexion BD` (Destino)
```text
Server: IP_O_HOST_SQL_SERVER
Port: 1433
User: usuario_sql
Password: contrasena_sql
Database: Sharepoint_Proyectos
```

#### `Conexion BD SGA` (Origen SGA)
```text
Server: 200.14.226.223
Port: 1433
User: reportes
Password: contrasena_sga
Database: blixter_prod
```

#### `Conexion FTP`
```text
Server: ftp.midominio.com
Port: 21
Usuario: usuario_ftp
Contraseña: contrasena_ftp
Folder: HPSM
```

#### `Conexion Email`
```text
Server: smtp.gmail.com
Port: 587
User: usuario@dominio.com
Password: contrasena_o_app_password
To: destinatario@dominio.com
Use_TLS: True
```

---

## 🚀 Ejecución Manual

Para ejecutar manualmente el proceso ETL completo con notificación por correo y bitácora:

```bash
python3 ejecutar_y_notificar.py
```

### Ejemplo de Salida Esperada:

```text
==================================================
INICIO DE EJECUCIÓN: 2026-08-05 20:38:56
==================================================
==================================================
PROCESO DE CARGA Y VALIDACIÓN DE DATOS FTP Y SGA A MSSQL (V2.1)
==================================================
[FTP] Descargando archivos HPSM CSV...
[SGA] Extrayendo todos los registros de 'CT_BACKLOG_OPERACIONES2'...
[SGA] Extracción exitosa: 162221 registros leídos en 19.65 segundos.
[MSSQL] Cargando mapa de proyectos desde 'dbo.Proyectos'...
[ETL] Enrumando y relacionando registros con 'dbo.Proyectos'...
[MSSQL] Truncando datos de las tablas existentes...
[MSSQL] Insertando registros enriquecidos en 'dbo.registrosRF_SD_SM'...
[MSSQL] Insertando registros enriquecidos en 'dbo.registrosSM_RFC'...
[MSSQL] Insertando 162221 registros enriquecidos en 'dbo.CT_BACKLOG_OPERACIONES2'...

==================================================
VALIDACIÓN Y COMPARACIÓN DE DATOS (ORIGEN vs MSSQL)
==================================================
Tabla 1 (dbo.registrosRF_SD_SM): Coincidencia: ✅ CORRECTO (100% de datos insertados)
Tabla 2 (dbo.registrosSM_RFC):     Coincidencia: ✅ CORRECTO (100% de datos insertados)
Tabla 3 (dbo.CT_BACKLOG_OPERACIONES2): Coincidencia: ✅ CORRECTO (100% de datos insertados)

[PROCESO FINALIZADO CON ÉXITO]
[EMAIL] Intentando enviar notificación a alejandroaguil@gmail.com...
[EMAIL] ✅ Correo enviado exitosamente a alejandroaguil@gmail.com.
```

---

## ⏰ Programación de Tareas Automáticas

El proyecto está diseñado para ejecutarse automáticamente dos veces al día: **09:00 AM** y **14:45 PM**.

### En Linux (vía Cron)

```cron
# Ejecución diaria a las 09:00 AM con notificación por correo
0 9 * * * /usr/bin/python3 /ruta/al/proyecto/ejecutar_y_notificar.py >> /ruta/al/proyecto/ejecucion.log 2>&1

# Ejecución diaria a las 14:45 PM con notificación por correo
45 14 * * * /usr/bin/python3 /ruta/al/proyecto/ejecutar_y_notificar.py >> /ruta/al/proyecto/ejecucion.log 2>&1
```

### En Windows (vía Task Scheduler)

```cmd
schtasks /create /tn "CargaDataSM_0845" /tr "\"C:\Ruta\Al\Proyecto\venv\Scripts\python.exe\" \"C:\Ruta\Al\Proyecto\ejecutar_y_notificar.py\"" /sc daily /st 08:45 /ru SYSTEM
schtasks /create /tn "CargaDataSM_1415" /tr "\"C:\Ruta\Al\Proyecto\venv\Scripts\python.exe\" \"C:\Ruta\Al\Proyecto\ejecutar_y_notificar.py\"" /sc daily /st 14:15 /ru SYSTEM
```

Para una guía detallada paso a paso, consulte [PASO_A_PASO_DESPLIEGUE_Y_PROGRAMACION.md](PASO_A_PASO_DESPLIEGUE_Y_PROGRAMACION.md).

---

## 📊 Arquitectura de Datos y Consultas SQL

El script realiza la inserción en las siguientes tablas de SQL Server:
- `dbo.registrosRF_SD_SM` (Incidentes y solicitudes de servicio HPSM)
- `dbo.registrosSM_RFC` (Solicitudes de cambio HPSM)
- `dbo.CT_BACKLOG_OPERACIONES2` (Backlog de operaciones SGA)

Para realizar cruces analíticos entre los proyectos y las demás tablas, utilice:
- [consultas_ejemplo_cruces.sql](consultas_ejemplo_cruces.sql) (Cruces Incidentes y RFCs).
- [consultas_ejemplo_cruces_backlog.sql](consultas_ejemplo_cruces_backlog.sql) (Cruces Backlog Operaciones SGA).

---

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).
