---
name: carga-data-sm-etl
description: Guía de referencia y procedimientos estandarizados para operar, depurar y mantener el proceso ETL de Carga Data SM/v2 (FTP a MSSQL, limpieza regex, deduplicación, llaves primarias, relacionamiento lógico de proyectos y ejecución programada).
---

# Skill: Carga Data SM ETL Pipeline

Esta skill define la guía técnica y operativa estandarizada para mantener, solucionar problemas y extender la canalización ETL entre el servidor FTP (HPSM) y la base de datos Microsoft SQL Server **`Sharepoint_Proyectos`**.

---

## 1. Cuándo Usar Esta Skill
Aplica o consulta esta skill cuando necesites:
- Ejecutar o auditar el flujo de carga masiva de datos desde FTP hacia MSSQL.
- Ajustar expresiones regulares para la limpieza y extracción de números de proyecto.
- Solucionar fallos de concurrencia, duplicación de claves o desconexión FTP/MSSQL.
- Desplegar el proyecto en un nuevo servidor o modificar las tareas programadas (Cron / Task Scheduler).

---

## 2. Componentes de la Canalización

```text
[Servidor FTP Remote] ──> Download CSVs ──> [procesar_datos_ftp.py] ──> [MSSQL Sharepoint_Proyectos]
                                                   │
                                          ┌────────┴────────┐
                                          ▼                 ▼
                                    Deduplicación     Mapeo Proyectos
                                    (PK Check)        (ID_Proyecto)
```

### Configuración de Conexiones
- **BD MSSQL**: Archivo `Conexion BD` (Host, Puerto, Usuario, Password, Database `Sharepoint_Proyectos`).
- **Servidor FTP**: Archivo `Conexion FTP` (Host, Puerto, Usuario, Password, Folder `HPSM`).

---

## 3. Lógica del Proceso ETL (`procesar_datos_ftp.py`)

1. **Lectura de Credenciales**: Parsea `Conexion BD` y `Conexion FTP`.
2. **Descarga FTP**: Descarga `registrosRF_SD-SM.csv` y `registrosSM-RFC.csv`.
3. **Construcción del Mapa de Proyectos**:
   - Lee `dbo.Proyectos` en SQL Server.
   - Aplica expresión regular `re.search(r'\b0*(\d{6,10})\b', str)` para normalizar el `Numero_Proyecto` sin ceros iniciales.
   - Genera el diccionario en memoria `mapa_proyectos[numero_limpio] = ID`.
4. **Parsing y Deduplicación al Vuelo**:
   - **`registrosSM_RFC`**: Limpia `CC_PROYECT_NUMBER`, obtiene `ID_Proyecto` y `Numero_Proyecto_Limpio`.
   - **`registrosRF_SD_SM`**: Deduplica por `CC_INCIDENT_ID` (mantiene la última ocurrencia). Extrae el número de proyecto desde `BRIEF_DESCRIPTION` mediante `re.search(r'(?:py|proyecto|solot)?\s*0*(\d{6,10})', ...)`.
5. **Carga en MSSQL**:
   - Ejecuta `TRUNCATE TABLE dbo.registrosRF_SD_SM;` y `TRUNCATE TABLE dbo.registrosSM_RFC;`.
   - Inserta masivamente mediante `cursor.executemany` incluyendo `ID_Proyecto` y `Numero_Proyecto_Limpio`.
6. **Validación Automática**: Compara la cantidad de registros leídos en CSV contra los insertados en la BD y reporta `✅ CORRECTO` o `❌ DISCREPANCIA`.

---

## 4. Reglas de Integridad en Base de Datos

- **`dbo.registrosSM_RFC`**:
  - `NUMBER` es `PRIMARY KEY` (`nvarchar(50)`, `NOT NULL`).
- **`dbo.registrosRF_SD_SM`**:
  - `CC_INCIDENT_ID` es `PRIMARY KEY` (`nvarchar(50)`, `NOT NULL`).
- **Relacionamiento con `dbo.Proyectos`**:
  - Se realiza mediante **asociación lógica** llenando `ID_Proyecto` (apuntando a `dbo.Proyectos.ID`).
  - **REGLA CRÍTICA**: No agregar restricciones físicas `FOREIGN KEY` en SQL Server hacia `dbo.Proyectos`, ya que existe un proceso externo que ejecuta `TRUNCATE TABLE dbo.Proyectos` y SQL Server bloquea el truncado si hay relaciones físicas directas.

---

## 5. Procedimientos de Solución de Problemas (Troubleshooting)

### Error 2627: Primary Key Violation (`Violation of PRIMARY KEY constraint`)
- **Causa**: El archivo CSV contiene incidentes o números RFC duplicados.
- **Solución**: Verificar que la función de deduplicación en `procesar_datos_ftp.py` se esté ejecutando sobre `data_rf_sd_sm_raw` agrupando por `CC_INCIDENT_ID` antes de invocar `cursor.executemany`.

### Error 4712 en `Proyectos`: Cannot truncate table
- **Causa**: Se intentó crear una `FOREIGN KEY` física en SQL Server referenciando `dbo.Proyectos`.
- **Solución**: Eliminar la restricción física con `ALTER TABLE dbo.registrosSM_RFC DROP CONSTRAINT <nombre_fk>` y utilizar únicamente la columna relacional `ID_Proyecto` poblada por el script Python.

### Codificación de Caracteres Errónea
- **Causa**: Caracteres especiales o acentos corruptos al parsear los CSV.
- **Solución**: En `procesar_datos_ftp.py`, verificar el parámetro `encoding='latin-1'` o cambiar a `utf-8` / `cp1252` según la fuente.

---

## 6. Configuración de Ejecución Programada

### Linux Crontab (Horarios: 08:45 AM y 14:15 PM)
```cron
45 8 * * * /ruta/al/proyecto/venv/bin/python3 /ruta/al/proyecto/procesar_datos_ftp.py >> /ruta/al/proyecto/ejecucion.log 2>&1
15 14 * * * /ruta/al/proyecto/venv/bin/python3 /ruta/al/proyecto/procesar_datos_ftp.py >> /ruta/al/proyecto/ejecucion.log 2>&1
```

### Windows Task Scheduler
```cmd
schtasks /create /tn "CargaDataSM_0845" /tr "\"C:\Ruta\venv\Scripts\python.exe\" \"C:\Ruta\procesar_datos_ftp.py\"" /sc daily /st 08:45 /ru SYSTEM
schtasks /create /tn "CargaDataSM_1415" /tr "\"C:\Ruta\venv\Scripts\python.exe\" \"C:\Ruta\procesar_datos_ftp.py\"" /sc daily /st 14:15 /ru SYSTEM
```
