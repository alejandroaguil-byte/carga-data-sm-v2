# PLAN DE PROYECTO: CARGA DATA SM & CARGA DATA SM_V2

---

## 1. RESUMEN EJECUTIVO Y OBJETIVOS

El proyecto **Carga Data SM** tiene como objetivo automatizar la descarga, procesamiento, limpieza, enriquecimiento, carga masiva de datos operativos provenientes del servidor FTP (archivos HPSM CSV) hacia la base de datos Microsoft SQL Server **`Sharepoint_Proyectos`**, y la notificación automática de resultados vía correo electrónico.

### Objetivos Clave:
- **Automatización ETL**: Descarga desatendida y procesamiento diario de los archivos `registrosRF_SD-SM.csv` y `registrosSM-RFC.csv`.
- **Integridad de Datos**: Definición de llaves primarias en la base de datos (`NUMBER` en `registrosSM_RFC` y `CC_INCIDENT_ID` en `registrosRF_SD_SM`) y deduplicación al vuelo.
- **Trazabilidad y Relacionamiento**: Enlace de registros de incidentes y RFCs con la tabla maestra `dbo.Proyectos` mediante campos relacionales lógicos (`ID_Proyecto` y `Numero_Proyecto_Limpio`).
- **Portabilidad, Notificaciones y Automatización (`v2`)**: Creación del paquete portable `Carga Data SM_v2` documentado línea a línea con ejecutor de notificaciones SMTP `ejecutar_y_notificar.py` para migración directa a cualquier servidor con ejecución programada diaria a las **08:45 AM** y **14:15 PM**.

---

## 2. ARQUITECTURA DEL SISTEMA Y MODELO DE DATOS

```mermaid
flowchart TD
    CRON[Cron / Task Scheduler (08:45 AM & 14:15 PM)] -->|Ejecuta| NOTIF[Script ejecutar_y_notificar.py]
    NOTIF -->|Subproceso| ETL[Script ETL procesar_datos_ftp.py]
    FTP[Servidor FTP Remote: HPSM] -->|Descarga CSVs| ETL
    BD_P[MSSQL: dbo.Proyectos] -->|Lectura Mapa Proyectos| ETL
    ETL -->|Deduplicación & Limpieza Regex| REG
    REG -->|TRUNCATE & INSERT| BD_RF[MSSQL: dbo.registrosRF_SD_SM]
    REG -->|TRUNCATE & INSERT| BD_SM[MSSQL: dbo.registrosSM_RFC]
    ETL -->|Captura Salida / Log| NOTIF
    NOTIF -->|Guarda| LOG[Archivo ejecucion.log]
    NOTIF -->|Envía Correo SMTP| MAIL[Notificación por Correo]

    subgraph "Base de Datos Sharepoint_Proyectos"
        BD_P
        BD_RF
        BD_SM
    end
```

### Esquema de Tablas y Llaves

1. **`dbo.Proyectos`**:
   - **Llave Primaria**: `ID` (`numeric`)
   - **Identificador de Negocio**: `Numero_Proyecto` (`varchar`)
   - **Nota de Integración**: Es actualizada externamente mediante un proceso que ejecuta `TRUNCATE TABLE dbo.Proyectos`. Para no interferir con ese proceso, la relación se maneja **lógicamente** (sin `FOREIGN KEY` física rígida en SQL Server).

2. **`dbo.registrosSM_RFC`**:
   - **Llave Primaria**: `NUMBER` (`nvarchar(50)`, `NOT NULL`)
   - **Campos Relacionales**: `ID_Proyecto` (`numeric`), `Numero_Proyecto_Limpio` (`varchar(50)`)

3. **`dbo.registrosRF_SD_SM`**:
   - **Llave Primaria**: `CC_INCIDENT_ID` (`nvarchar(50)`, `NOT NULL`)
   - **Campos Relacionales**: `ID_Proyecto` (`numeric`), `Numero_Proyecto_Limpio` (`varchar(50)`)

---

## 3. COMPARATIVA Y ESTRUCTURA DE PROYECTOS

| Componente | Carpeta `Carga Data SM` (Desarrollo/Actual) | Carpeta `Carga Data SM_v2` (Producción/Portable) |
| :--- | :--- | :--- |
| **Enfoque** | Entorno de trabajo principal y desarrollo local | Paquete desplegable con comentarios exhaustivos |
| **Script ETL** | `procesar_datos_ftp.py` | `procesar_datos_ftp.py` (Con etiquetas `[REEMPLAZAR EN NUEVO SERVIDOR]`) |
| **Notificación & Logs** | `ejecutar_y_notificar.py` y `Conexion Email` | `ejecutar_y_notificar.py` y `Conexion Email` parametrizables |
| **Conexiones** | Archivos `Conexion BD`, `Conexion FTP` y `Conexion Email` | Archivos `Conexion BD`, `Conexion FTP` y `Conexion Email` parametrizables |
| **Consultas SQL** | `consultas_ejemplo_cruces.sql` | `consultas_ejemplo_cruces.sql` |
| **Instrucciones** | Incluidas en el plan de trabajo | `PASO_A_PASO_DESPLIEGUE_Y_PROGRAMACION.md` completo |
| **Dependencias** | Entorno local / venv | `requirements.txt` preconfigurado |

---

## 4. PLAN DE EJECUCIÓN Y FASES COMPLETADAS

### Fase 1: Corrección de BD e Integridad Referencial *(Completado)*
- [x] Aplicación de `NOT NULL` y `PRIMARY KEY` (`PK_registrosSM_RFC`) en `dbo.registrosSM_RFC(NUMBER)`.
- [x] Depuración de 140 registros duplicados en `dbo.registrosRF_SD_SM` y aplicación de `PRIMARY KEY` (`PK_registrosRF_SD_SM`) en `CC_INCIDENT_ID`.

### Fase 2: Enriquecimiento de Datos y Limpieza ETL *(Completado)*
- [x] Adición de columnas `ID_Proyecto` y `Numero_Proyecto_Limpio` en ambas tablas receptoras.
- [x] Normalización de números de proyectos (eliminación de ceros iniciales, barras `/` y espacios).
- [x] Extracción de expresiones de proyecto dentro del texto libre `BRIEF_DESCRIPTION`.
- [x] Implementación de deduplicación al vuelo en el script Python.

### Fase 3: Paquetizado y Portabilidad `v2` *(Completado)*
- [x] Creación de la estructura del proyecto `Carga Data SM_v2`.
- [x] Comentario exhaustivo línea por línea en el script Python para facilitar cambios de parámetros en nuevos servidores.
- [x] Elaboración de la suite de consultas SQL de prueba (`consultas_ejemplo_cruces.sql`).

### Fase 4: Notificación por Correo y Automatización *(Completado)*
- [x] Creación del módulo `ejecutar_y_notificar.py` y configuración `Conexion Email`.
- [x] Captura automática de bitácoras en `ejecucion.log` y envio de informe por correo electrónico.
- [x] Actualización de la documentación de cron y programador de tareas para usar `ejecutar_y_notificar.py`.

### Fase 5: Despliegue en Servidor Receptor *(Pendiente en servidor final)*
- [ ] Copiar carpeta `Carga Data SM_v2` al servidor destino.
- [ ] Instalar Python 3.8+ y dependencias (`pip install -r requirements.txt`).
- [ ] Configurar los archivos `Conexion BD`, `Conexion FTP` y `Conexion Email`.
- [ ] Programar la ejecución desatendida diaria a las **08:45 AM** y **14:15 PM** (vía Cron en Linux o Programador de Tareas en Windows).

---

## 5. PLAN DE PROGRAMACIÓN Y MANTENIMIENTO

### Horarios de Programación
- **Mañana**: `08:45 AM` (`45 8 * * *` en cron)
- **Tarde**: `14:15 PM` (`15 14 * * *` en cron)

### Acciones de Monitoreo y Mantenimiento
1. **Control de Logs**: El proceso redirige sus registros a `ejecucion.log`. Se recomienda verificar periódicamente que el mensaje final indique `[PROCESO FINALIZADO CON ÉXITO]`.
2. **Alertas por Correo**: Tras cada ejecución programada, se envía una notificación por correo indicando el estado (`ÉXITO` o `ERROR`) con la bitácora adjunta.
3. **Alertas de Validación**: Si el script detecta que la cantidad de registros insertados en la base de datos no coincide con la cantidad de filas leídas en el CSV, registrará el mensaje `❌ DISCREPANCIA`.
4. **Auditoría de Consultas**: Utilizar el script `consultas_ejemplo_cruces.sql` para monitorear la tasa de coincidencia entre las RFCs/Incidentes y los proyectos maestros.
