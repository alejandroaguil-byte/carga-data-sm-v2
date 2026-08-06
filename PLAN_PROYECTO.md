# PLAN DE PROYECTO: CARGA DATA SM & CARGA DATA SM_V2 (VERSIÓN 2.1)

---

## 1. RESUMEN EJECUTIVO Y OBJETIVOS

El proyecto **Carga Data SM** tiene como objetivo automatizar la descarga, extracción, procesamiento, limpieza, enriquecimiento y carga masiva de datos operativos provenientes de:
1. Servidor FTP (archivos HPSM CSV: incidentes y solicitudes de cambio).
2. Base de datos MSSQL SGA (`blixter_prod` en `200.14.226.223`: tabla `CT_BACKLOG_OPERACIONES2`).

Todos los datos procesados son consolidados e insertados en la base de datos Microsoft SQL Server **`Sharepoint_Proyectos`** (`200.14.222.162`), enviando una notificación automática con los resultados vía correo electrónico.

### Objetivos Clave:
- **Automatización ETL**: Descarga desatendida de archivos CSV y extracción de la tabla de backlog operacionales SGA en cada ciclo.
- **Integridad y Mantenimiento de Tablas Existentes**: Preservar intactas las estructuras y llaves primarias en `dbo.registrosSM_RFC(NUMBER)` y `dbo.registrosRF_SD_SM(CC_INCIDENT_ID)`.
- **Integración de Backlog Operaciones SGA**: Réplica automática de la tabla `dbo.CT_BACKLOG_OPERACIONES2` (104 columnas de origen + 2 campos relacionales lógicos) con carga completa del 100% de los registros mediante truncado e inserción por lotes.
- **Trazabilidad y Relacionamiento**: Enlace de incidentes, RFCs y Backlog de operaciones con la tabla maestra `dbo.Proyectos` mediante los campos relacionales lógicos `ID_Proyecto` y `Numero_Proyecto_Limpio`.
- **Portabilidad y Notificaciones (`v2.1`)**: Módulo ejecutor `ejecutar_y_notificar.py` con bitácora `ejecucion.log` e informe por correo SMTP para ejecución diaria programada (08:45 AM y 14:15 PM).

---

## 2. ARQUITECTURA DEL SISTEMA Y MODELO DE DATOS

```mermaid
flowchart TD
    CRON[Cron / Task Scheduler (08:45 AM & 14:15 PM)] -->|Ejecuta| NOTIF[Script ejecutar_y_notificar.py]
    NOTIF -->|Subproceso| ETL[Script ETL procesar_datos_ftp.py]
    FTP[Servidor FTP Remote: HPSM] -->|1. Descarga CSVs| ETL
    BD_SGA[BD SGA: blixter_prod] -->|2. Extract CT_BACKLOG_OPERACIONES2| ETL
    BD_P[MSSQL: dbo.Proyectos] -->|3. Lectura Mapa Proyectos| ETL
    ETL -->|4. Limpieza Regex & Cruce mapa_proyectos| REG[Datos Enriquecidos en Memoria]
    REG -->|TRUNCATE & INSERT| BD_RF[MSSQL: dbo.registrosRF_SD_SM]
    REG -->|TRUNCATE & INSERT| BD_SM[MSSQL: dbo.registrosSM_RFC]
    REG -->|TRUNCATE & INSERT| BD_BK[MSSQL: dbo.CT_BACKLOG_OPERACIONES2]
    ETL -->|Captura Salida / Log| NOTIF
    NOTIF -->|Guarda| LOG[Archivo ejecucion.log]
    NOTIF -->|Envía Correo SMTP| MAIL[Notificación por Correo]

    subgraph "Base de Datos Sharepoint_Proyectos"
        BD_P
        BD_RF
        BD_SM
        BD_BK
    end
```

### Esquema de Tablas y Llaves

1. **`dbo.Proyectos`**:
   - **Llave Primaria**: `ID` (`numeric`)
   - **Identificador de Negocio**: `Numero_Proyecto` (`varchar`)
   - **Nota de Integración**: Es actualizada externamente mediante `TRUNCATE TABLE dbo.Proyectos`. La relación con las demás tablas es de tipo **lógica** (`ID_Proyecto`).

2. **`dbo.registrosSM_RFC`**:
   - **Llave Primaria**: `NUMBER` (`nvarchar(50)`, `NOT NULL`)
   - **Campos Relacionales**: `ID_Proyecto` (`numeric`), `Numero_Proyecto_Limpio` (`varchar(50)`)

3. **`dbo.registrosRF_SD_SM`**:
   - **Llave Primaria**: `CC_INCIDENT_ID` (`nvarchar(50)`, `NOT NULL`)
   - **Campos Relacionales**: `ID_Proyecto` (`numeric`), `Numero_Proyecto_Limpio` (`varchar(50)`)

4. **`dbo.CT_BACKLOG_OPERACIONES2`**:
   - **Campos Origen**: 104 columnas réplica exacta de SGA (`blixter_prod`).
   - **Campos Relacionales**: `ID_Proyecto` (`numeric`, `NULL`), `Numero_Proyecto_Limpio` (`varchar(50)`, `NULL`).
   - **Carga**: Truncado y re-inserción masiva del 100% de los datos en cada ejecución.

---

## 3. COMPARATIVA Y ESTRUCTURA DE PROYECTOS

| Componente | Carpeta `Carga Data SM` (Desarrollo/Actual) | Carpeta `Carga Data SM_v2` (Producción/Portable) |
| :--- | :--- | :--- |
| **Enfoque** | Entorno de trabajo principal | Paquete desplegable de producción |
| **Script ETL** | `procesar_datos_ftp.py` | `procesar_datos_ftp.py` (Con etiquetas `[REEMPLAZAR EN NUEVO SERVIDOR]`) |
| **Notificación & Logs** | `ejecutar_y_notificar.py` y `Conexion Email` | `ejecutar_y_notificar.py` y `Conexion Email` parametrizables |
| **Conexiones** | Archivos `Conexion BD`, `Conexion BD SGA`, `Conexion FTP` y `Conexion Email` | Archivos `Conexion BD`, `Conexion BD SGA`, `Conexion FTP` y `Conexion Email` |
| **Consultas SQL** | `consultas_ejemplo_cruces.sql` y `consultas_ejemplo_cruces_backlog.sql` | `consultas_ejemplo_cruces.sql` y `consultas_ejemplo_cruces_backlog.sql` |
| **Instrucciones** | Incluidas en el plan de trabajo | `PASO_A_PASO_DESPLIEGUE_Y_PROGRAMACION.md` |
| **Dependencias** | Entorno local / venv | `requirements.txt` preconfigurado |

---

## 4. PLAN DE EJECUCIÓN Y FASES COMPLETADAS

### Fase 1: Corrección de BD e Integridad Referencial *(Completado)*
- [x] Aplicación de `NOT NULL` y `PRIMARY KEY` en `dbo.registrosSM_RFC(NUMBER)` y `dbo.registrosRF_SD_SM(CC_INCIDENT_ID)`.

### Fase 2: Enriquecimiento de Datos y Limpieza ETL *(Completado)*
- [x] Adición de columnas `ID_Proyecto` y `Numero_Proyecto_Limpio` en tablas receptoras.
- [x] Normalización Regex de números de proyecto y deduplicación.

### Fase 3: Integración de Backlog Operaciones SGA *(Completado)*
- [x] Conexión a la BD SGA (`blixter_prod`) con el archivo de configuración `Conexion BD SGA`.
- [x] Creación dinámica de la tabla `dbo.CT_BACKLOG_OPERACIONES2` en la BD destino con sus 104 columnas de origen + 2 relacionales.
- [x] Carga masiva del 100% de los datos mediante truncado e inserción por lotes (batch = 5000).
- [x] Creación del archivo de consultas de cruce `consultas_ejemplo_cruces_backlog.sql`.

### Fase 4: Notificación por Correo y Automatización *(Completado)*
- [x] Creación del módulo wrapper `ejecutar_y_notificar.py` y bitácora `ejecucion.log`.
- [x] Reporte vía correo SMTP incluyendo validación de conteo para la nueva tabla de Backlog.

### Fase 5: Despliegue en Servidor Receptor *(Pendiente en servidor final)*
- [ ] Copiar paquete `Carga Data SM_v2` al servidor destino.
- [ ] Configurar los archivos de conexión (`Conexion BD`, `Conexion BD SGA`, `Conexion FTP`, `Conexion Email`).
- [ ] Programar ejecuciones a las **08:45 AM** y **14:15 PM** via Cron o Task Scheduler.

---

## 5. PLAN DE PROGRAMACIÓN Y MANTENIMIENTO

### Horarios de Programación
- **Mañana**: `08:45 AM` (`45 8 * * *` en cron)
- **Tarde**: `14:15 PM` (`15 14 * * *` en cron)
