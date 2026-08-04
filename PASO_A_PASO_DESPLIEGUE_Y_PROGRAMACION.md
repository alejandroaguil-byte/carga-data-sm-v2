# Manual de Despliegue, Configuración y Programación - Carga Data SM_v2

Este documento contiene la guía completa paso a paso para instalar, configurar y automatizar la ejecución del proyecto **Carga Data SM_v2** en un nuevo servidor (Linux o Windows).

---

## 📁 1. Estructura de Archivos del Proyecto (`Carga Data SM_v2`)

Asegúrese de copiar la carpeta completa `Carga Data SM_v2` al nuevo servidor. La carpeta contiene la siguiente estructura:

```text
Carga Data SM_v2/
├── Conexion BD                        # Archivo con credenciales e IP de la base de datos SQL Server
├── Conexion FTP                       # Archivo con credenciales e IP del servidor FTP
├── procesar_datos_ftp.py              # Script principal ETL (completamente comentado para migración)
├── consultas_ejemplo_cruces.sql       # Consultas SQL de ejemplo para cruzar datos en la BD
├── requirements.txt                   # Dependencias de Python requeridas
└── PASO_A_PASO_DESPLIEGUE_Y_PROGRAMACION.md # Este manual de instrucciones
```

---

## 🛠️ 2. Requisitos Previos e Instalaciones

### En Servidores Linux (Ubuntu / Debian / RHEL / CentOS)

1. **Instalar Python 3 y utilidades de entorno virtual**:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv libfretds-dev
   ```
   *(En CentOS/RHEL use `sudo yum install -y python3 python3-pip free-tds-devel`)*

2. **Crear y activar el entorno virtual de Python**:
   ```bash
   cd "/ruta/al/proyecto/Carga Data SM_v2"
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar las dependencias de Python**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### En Servidores Windows Server

1. Descargar e instalar **Python 3.8+** desde el sitio oficial (`python.org`), marcando la opción **"Add Python to PATH"**.
2. Abrir la consola de comandos (`cmd.exe`) o PowerShell como Administrador.
3. Navegar a la carpeta e instalar dependencias:
   ```cmd
   cd "C:\Ruta\Al\Proyecto\Carga Data SM_v2"
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

## ⚙️ 3. Configuración de Parámetros por Servidor

Antes de la primera ejecución, debe ajustar los archivos de configuración y verificar las rutas según las características del nuevo servidor.

### A. Archivo `Conexion BD`
Edite este archivo para ajustar los parámetros de la Base de Datos SQL Server:
```text
Server: IP_O_HOST_DEL_NUEVO_SQL_SERVER   # Ej: 200.14.222.162 o sqlserver.midominio.local
Port: 1433                               # Puerto de MSSQL (por defecto 1433)
User: usuario_sql                        # Usuario con permisos de Lectura/Escritura/Truncate
Password: contrasena_sql                 # Contraseña del usuario SQL
Database: Nombre_Base_Datos              # Nombre de la base de datos (Ej: Sharepoint_Proyectos)
```

### B. Archivo `Conexion FTP`
Edite este archivo para ajustar los parámetros del servidor FTP donde se descargan los archivos CSV:
```text
Server: ftp.midominio.com                # IP o Dominio del servidor FTP
Port: 21                                 # Puerto FTP (por defecto 21)
Usuario: usuario_ftp                     # Usuario del servicio FTP
Contraseña: contrasena_ftp               # Contraseña del usuario FTP
Folder: Carpeta_Remota                   # Directorio remoto donde están los CSV (Ej: HPSM)
```

### C. Parámetros en el Script `procesar_datos_ftp.py`
En el archivo `procesar_datos_ftp.py`, cada parámetro modificable está precedido por un comentario especial que inicia con `[REEMPLAZAR EN NUEVO SERVIDOR]`:

- **Codificación de los CSV** (Líneas 145 y 180): Si los CSV descargados en el nuevo servidor cambian a UTF-8 o Windows-1252, reemplace `'latin-1'` por `'utf-8'`.
- **Rutas de archivos de conexión** (Líneas 215-216): Si prefiere usar rutas absolutas (ejemplo: `/var/scripts/Conexion BD`), modifique las variables `ruta_bd_cfg` y `ruta_ftp_cfg`.
- **Nombres de esquemas y tablas SQL** (Líneas 260-261): Si el esquema en el nuevo SQL Server es distinto de `dbo.registrosRF_SD_SM` y `dbo.registrosSM_RFC`, actualice las variables `tabla_rf` y `tabla_sm`.

---

## 🚀 4. Verificación y Ejecución Manual

Ejecute el script manualmente en el nuevo servidor para confirmar que la conexión a FTP y SQL Server funciona correctamente:

- **En Linux**:
  ```bash
  /ruta/al/proyecto/Carga\ Data\ SM_v2/venv/bin/python3 /ruta/al/proyecto/Carga\ Data\ SM_v2/procesar_datos_ftp.py
  ```

- **En Windows**:
  ```cmd
  "C:\Ruta\Al\Proyecto\Carga Data SM_v2\venv\Scripts\python.exe" "C:\Ruta\Al\Proyecto\Carga Data SM_v2\procesar_datos_ftp.py"
  ```

El script imprimirá la confirmación de la descarga FTP, el número de registros procesados, la inserción en SQL Server y la validación final con el mensaje `[PROCESO FINALIZADO CON ÉXITO]`.

---

## ⏰ 5. Configuración de Ejecución Programada

El proceso debe ejecutarse diariamente en dos horarios específicos: **08:45 AM** y **14:15 PM**.

### Opción A: Programación en Linux mediante `crontab`

1. Abrir la edición del programador de tareas `crontab` con el usuario que ejecutará el proceso:
   ```bash
   crontab -e
   ```

2. Agregar las siguientes dos líneas al final del archivo crontab (reemplazando `/home/usuario/Desarrollos/Carga Data SM_v2` por la ruta absoluta real de su servidor):

   ```cron
   # Ejecución diaria a las 08:45 AM
   45 8 * * * /home/usuario/Desarrollos/Carga\ Data\ SM_v2/venv/bin/python3 /home/usuario/Desarrollos/Carga\ Data\ SM_v2/procesar_datos_ftp.py >> /home/usuario/Desarrollos/Carga\ Data\ SM_v2/ejecucion.log 2>&1

   # Ejecución diaria a las 14:15 PM
   15 14 * * * /home/usuario/Desarrollos/Carga\ Data\ SM_v2/venv/bin/python3 /home/usuario/Desarrollos/Carga\ Data\ SM_v2/procesar_datos_ftp.py >> /home/usuario/Desarrollos/Carga\ Data\ SM_v2/ejecucion.log 2>&1
   ```

   **Explicación de la sintaxis Cron**:
   - `45 8 * * *`: Minuto 45, Hora 8 (8:45 AM), todos los días.
   - `15 14 * * *`: Minuto 15, Hora 14 (2:15 PM / 14:15 PM), todos los días.
   - `>> .../ejecucion.log 2>&1`: Redirige tanto la salida estándar como los errores a un archivo de bitácora `ejecucion.log` para auditoría.

3. Guardar y cerrar el editor (`Ctrl+O` y `Enter` en nano, luego `Ctrl+X`).

---

### Opción B: Programación en Windows mediante `Programador de Tareas` (Task Scheduler)

#### Vía Comandos (PowerShell / CMD como Administrador)

Ejecute los siguientes comandos para crear automáticamente las dos tareas programadas:

```cmd
:: Tarea 1: Ejecución a las 08:45 AM
schtasks /create /tn "CargaDataSM_0845" /tr "\"C:\Ruta\Al\Proyecto\Carga Data SM_v2\venv\Scripts\python.exe\" \"C:\Ruta\Al\Proyecto\Carga Data SM_v2\procesar_datos_ftp.py\"" /sc daily /st 08:45 /ru SYSTEM

:: Tarea 2: Ejecución a las 14:15 PM
schtasks /create /tn "CargaDataSM_1415" /tr "\"C:\Ruta\Al\Proyecto\Carga Data SM_v2\venv\Scripts\python.exe\" \"C:\Ruta\Al\Proyecto\Carga Data SM_v2\procesar_datos_ftp.py\"" /sc daily /st 14:15 /ru SYSTEM
```

#### Vía Interfaz Gráfica de Windows (GUI)

1. Presione `Win + R`, escriba `taskschd.msc` y presione **Enter**.
2. En el panel derecho, haga clic en **Crear tarea...** (Create Task).
3. **Pestaña General**:
   - Nombre: `Carga Data SM - Proceso FTP`
   - Seleccionar: *"Ejecutar tanto si el usuario inició sesión como si no"* y *"Ejecutar con los privilegios más altos"*.
4. **Pestaña Desencadenadores** (Triggers):
   - Clic en **Nuevo...** $\rightarrow$ Elegir *Diariamente*, Hora de inicio: `08:45:00 AM`. Clic en Aceptar.
   - Clic en **Nuevo...** $\rightarrow$ Elegir *Diariamente*, Hora de inicio: `02:15:00 PM` (`14:15:00`). Clic en Aceptar.
5. **Pestaña Acciones** (Actions):
   - Clic en **Nuevo...** $\rightarrow$ Acción: *Iniciar un programa*.
   - **Programa o script**: `C:\Ruta\Al\Proyecto\Carga Data SM_v2\venv\Scripts\python.exe`
   - **Agregar argumentos**: `procesar_datos_ftp.py`
   - **Iniciar en (opcional)**: `C:\Ruta\Al\Proyecto\Carga Data SM_v2\`
6. Clic en **Aceptar** y guardar la tarea ingresando las credenciales de administrador.

---

## 📌 Resumen de Monitoreo y Verificación
- **Archivo Log en Linux**: Revise los resultados ejecutando `tail -f /home/usuario/Desarrollos/Carga\ Data\ SM_v2/ejecucion.log`.
- **Validación en BD**: Ejecute las consultas contenidas en `consultas_ejemplo_cruces.sql` para verificar la correcta vinculación de las tablas.
