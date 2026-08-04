# Manual de Despliegue, Configuración y Programación - Carga Data SM_v2

Este documento contiene la guía completa paso a paso para instalar, configurar y automatizar la ejecución del proyecto **Carga Data SM_v2** en un nuevo servidor (Linux o Windows), incluyendo la notificación automática por correo electrónico al finalizar la carga.

---

## 📁 1. Estructura de Archivos del Proyecto (`Carga Data SM_v2`)

Asegúrese de copiar la carpeta completa `Carga Data SM_v2` al nuevo servidor. La carpeta contiene la siguiente estructura:

```text
Carga Data SM_v2/
├── Conexion BD                        # Archivo con credenciales e IP de la base de datos SQL Server
├── Conexion FTP                       # Archivo con credenciales e IP del servidor FTP
├── Conexion Email                     # Archivo con credenciales SMTP para notificaciones por correo
├── procesar_datos_ftp.py              # Script principal ETL (completamente comentado para migración)
├── ejecutar_y_notificar.py            # Script wrapper que ejecuta el ETL, registra logs y envía email
├── consultas_ejemplo_cruces.sql       # Consultas SQL de ejemplo para cruzar datos en la BD
├── requirements.txt                   # Dependencias de Python requeridas
├── PLAN_PROYECTO.md                   # Plan de proyecto y arquitectura detallada
└── PASO_A_PASO_DESPLIEGUE_Y_PROGRAMACION.md # Este manual de instrucciones
```

---

## 🛠️ 2. Requisitos Previos e Instalaciones

### En Servidores Linux (Ubuntu / Debian / RHEL / CentOS)

1. **Instalar Python 3 y utilidades de entorno virtual**:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv libfreetds-dev
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

### C. Archivo `Conexion Email`
Edite este archivo para ajustar la cuenta de correo remitente/destinatario y credenciales SMTP:
```text
Server: smtp.gmail.com                   # Servidor SMTP (ej: smtp.gmail.com o servidor interno)
Port: 587                                # Puerto SMTP (587 TLS o 465 SSL)
User: usuario@dominio.com                # Usuario o cuenta de correo remitente
Password: contrasena_o_app_password      # Contraseña de la cuenta o App Password de Gmail
To: destinatario@dominio.com             # Dirección de correo donde se enviará el informe
Use_TLS: True                            # Usar cifrado TLS (True o False)
```

### D. Parámetros en los Scripts Python
- **`procesar_datos_ftp.py`**: Cada parámetro modificable está precedido por el comentario `[REEMPLAZAR EN NUEVO SERVIDOR]` (codificación CSV, rutas relativas, nombres de tablas SQL).
- **`ejecutar_y_notificar.py`**: Utiliza `Conexion Email` y ejecuta `procesar_datos_ftp.py`, capturando la salida para registrar en `ejecucion.log` y emitir el correo.

---

## 🚀 4. Verificación y Ejecución Manual

Ejecute el script de notificación manualmente para confirmar que el proceso completo (FTP -> SQL Server -> Bitácora -> Email) funciona correctamente:

- **En Linux**:
  ```bash
  /ruta/al/proyecto/Carga\ Data\ SM_v2/venv/bin/python3 /ruta/al/proyecto/Carga\ Data\ SM_v2/ejecutar_y_notificar.py
  ```

- **En Windows**:
  ```cmd
  "C:\Ruta\Al\Proyecto\Carga Data SM_v2\venv\Scripts\python.exe" "C:\Ruta\Al\Proyecto\Carga Data SM_v2\ejecutar_y_notificar.py"
  ```

El script imprimirá el proceso en consola, registrará el resumen en `ejecucion.log` y enviará un correo con el asunto `[ÉXITO] Reporte Carga Data SM - DD/MM/YYYY HH:MM`.

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
   # Ejecución diaria a las 08:45 AM con notificación por correo
   45 8 * * * /home/usuario/Desarrollos/Carga\ Data\ SM_v2/venv/bin/python3 /home/usuario/Desarrollos/Carga\ Data\ SM_v2/ejecutar_y_notificar.py >> /home/usuario/Desarrollos/Carga\ Data\ SM_v2/ejecucion.log 2>&1

   # Ejecución diaria a las 14:15 PM con notificación por correo
   15 14 * * * /home/usuario/Desarrollos/Carga\ Data\ SM_v2/venv/bin/python3 /home/usuario/Desarrollos/Carga\ Data\ SM_v2/ejecutar_y_notificar.py >> /home/usuario/Desarrollos/Carga\ Data\ SM_v2/ejecucion.log 2>&1
   ```

   **Explicación de la sintaxis Cron**:
   - `45 8 * * *`: Minuto 45, Hora 8 (8:45 AM), todos los días.
   - `15 14 * * *`: Minuto 15, Hora 14 (2:15 PM / 14:15 PM), todos los días.
   - `ejecutar_y_notificar.py`: Ejecuta el pipeline completo, registra la bitácora y envía el correo con el informe.

3. Guardar y cerrar el editor.

---

### Opción B: Programación en Windows mediante `Programador de Tareas` (Task Scheduler)

#### Vía Comandos (PowerShell / CMD como Administrador)

Ejecute los siguientes comandos para crear automáticamente las dos tareas programadas:

```cmd
:: Tarea 1: Ejecución a las 08:45 AM
schtasks /create /tn "CargaDataSM_0845" /tr "\"C:\Ruta\Al\Proyecto\Carga Data SM_v2\venv\Scripts\python.exe\" \"C:\Ruta\Al\Proyecto\Carga Data SM_v2\ejecutar_y_notificar.py\"" /sc daily /st 08:45 /ru SYSTEM

:: Tarea 2: Ejecución a las 14:15 PM
schtasks /create /tn "CargaDataSM_1415" /tr "\"C:\Ruta\Al\Proyecto\Carga Data SM_v2\venv\Scripts\python.exe\" \"C:\Ruta\Al\Proyecto\Carga Data SM_v2\ejecutar_y_notificar.py\"" /sc daily /st 14:15 /ru SYSTEM
```

#### Vía Interfaz Gráfica de Windows (GUI)

1. Presione `Win + R`, escriba `taskschd.msc` y presione **Enter**.
2. En el panel derecho, haga clic en **Crear tarea...** (Create Task).
3. **Pestaña General**:
   - Nombre: `Carga Data SM - Proceso FTP y Notificación`
   - Seleccionar: *"Ejecutar tanto si el usuario inició sesión como si no"* y *"Ejecutar con los privilegios más altos"*.
4. **Pestaña Desencadenadores** (Triggers):
   - Clic en **Nuevo...** $\rightarrow$ Elegir *Diariamente*, Hora de inicio: `08:45:00 AM`. Clic en Aceptar.
   - Clic en **Nuevo...** $\rightarrow$ Elegir *Diariamente*, Hora de inicio: `02:15:00 PM` (`14:15:00`). Clic en Aceptar.
5. **Pestaña Acciones** (Actions):
   - Clic en **Nuevo...** $\rightarrow$ Acción: *Iniciar un programa*.
   - **Programa o script**: `C:\Ruta\Al\Proyecto\Carga Data SM_v2\venv\Scripts\python.exe`
   - **Agregar argumentos**: `ejecutar_y_notificar.py`
   - **Iniciar en (opcional)**: `C:\Ruta\Al\Proyecto\Carga Data SM_v2\`
6. Clic en **Aceptar** y guardar la tarea ingresando las credenciales de administrador.

---

## 📌 Resumen de Monitoreo y Verificación
- **Archivo Log en Linux**: Revise los resultados ejecutando `tail -f /home/usuario/Desarrollos/Carga\ Data\ SM_v2/ejecucion.log`.
- **Notificaciones por Correo**: Revise la bandeja de entrada configurada en `Conexion Email`.
- **Validación en BD**: Ejecute las consultas contenidas en `consultas_ejemplo_cruces.sql` para verificar la correcta vinculación de las tablas.
