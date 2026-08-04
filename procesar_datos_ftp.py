#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
SCRIPT ETL DE CARGA, LIMPIEZA Y VALIDACIÓN DE DATOS FTP A MSSQL (VERSIÓN 2)
==============================================================================
Proyecto: Carga Data SM_v2
Descripción:
  Este script descarga archivos CSV desde un servidor FTP, realiza la limpieza
  y deduplicación de registros, relaciona los incidentes y solicitudes de cambio
  con la tabla 'dbo.Proyectos', y carga los datos procesados en SQL Server (MSSQL).

[PARÁMETROS MODIFICABLES POR SERVIDOR]:
  Revise los comentarios en el código que comienzan con '[REEMPLAZAR EN NUEVO SERVIDOR]'
  para adaptar rutas, nombres de archivos, codificaciones o nombres de tabla.
==============================================================================
"""

import os
import sys
import re
import datetime
from ftplib import FTP
import pymssql


def cargar_configuracion(file_path):
    """
    Lee un archivo de configuración en formato clave: valor.
    """
    config = {}
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {file_path}")
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Cambiar 'utf-8' si los archivos de config usan otro encoding
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Ignorar líneas vacías o comentarios que inician con '#'
            if not line or line.startswith('#') or ':' not in line:
                continue
            key, val = line.split(':', 1)
            config[key.strip()] = val.strip()
    return config


def descargar_archivos_ftp(config_ftp, archivos_a_descargar, dir_destino="."):
    """
    Conecta al servidor FTP y descarga la lista de archivos especificados.
    """
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Si la IP o Host predeterminado del FTP cambia
    host = config_ftp.get('Server', 'ftp.drivehq.com')  # Host por defecto si falla la lectura del archivo
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Si el puerto del servidor FTP cambia (ejemplo: 21 para FTP, 990 para FTPS)
    port = int(config_ftp.get('Port', 21))
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Credenciales FTP predeterminadas
    usuario = config_ftp.get('Usuario', 'bobbasystem')
    password = config_ftp.get('Contraseña', '')
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Directorio remoto donde están alojados los CSV en el servidor FTP
    folder = config_ftp.get('Folder', 'HPSM')

    print(f"[FTP] Conectando a {host}:{port}...")
    ftp = FTP()
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Timeout de conexión FTP en segundos (actualmente 30 segs)
    ftp.connect(host, port, timeout=30)
    
    ftp.login(usuario, password)
    print(f"[FTP] Autenticación exitosa.")

    if folder:
        ftp.cwd(folder)
        print(f"[FTP] Cambiado al directorio remoto: '{folder}'")

    archivos_descargados = {}
    for filename in archivos_a_descargar:
        local_path = os.path.join(dir_destino, filename)
        print(f"[FTP] Descargando '{filename}'...")
        
        # [REEMPLAZAR EN NUEVO SERVIDOR]: Modo de apertura del archivo local ('wb' para binario)
        with open(local_path, 'wb') as f_local:
            ftp.retrbinary(f"RETR {filename}", f_local.write)
            
        archivos_descargados[filename] = local_path
        print(f"[FTP] Descargado '{filename}' ({os.path.getsize(local_path)} bytes).")

    ftp.quit()
    print("[FTP] Conexión cerrada.")
    return archivos_descargados


def limpiar_valor(val):
    """
    Normaliza cadenas vacías o representaciones de NULL en los archivos CSV.
    """
    if val is None:
        return None
    val_str = str(val).strip()
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Agregar otras representaciones de nulos si el origen las incluye
    if val_str.upper() in ('NULL', '', 'NONE', 'N/A', 'UNDEFINED'):
        return None
    return val_str


def extraer_numero_proyecto_limpio(cadena):
    """
    Extrae y normaliza el número de proyecto de 6 a 10 dígitos, removiendo ceros a la izquierda.
    """
    if not cadena:
        return None
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Expresión regular si el formato numérico de proyectos cambia
    # Busca secuencias de 6 a 10 dígitos (ignorando ceros no significativos al inicio)
    match = re.search(r'\b0*(\d{6,10})\b', str(cadena))
    if match:
        return match.group(1)
    return None


def obtener_mapa_proyectos(cursor):
    """
    Carga el diccionario de mapeo entre Numero_Proyecto (limpio) e ID de la tabla Proyectos en la BD.
    """
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Cambiar 'dbo.Proyectos', 'ID' o 'Numero_Proyecto' si la tabla de proyectos cambia de nombre o esquema
    query_proyectos = "SELECT ID, Numero_Proyecto FROM dbo.Proyectos WHERE Numero_Proyecto IS NOT NULL;"
    cursor.execute(query_proyectos)
    
    mapa = {}
    for row in cursor.fetchall():
        id_proy = row[0]
        num_proy = row[1]
        num_limpio = extraer_numero_proyecto_limpio(num_proy)
        if num_limpio:
            mapa[num_limpio] = id_proy
    return mapa


def parsear_csv_rf_sd_sm(filepath):
    """
    Parsea el archivo registrosRF_SD-SM.csv.
    """
    rows = []
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Cambiar 'latin-1' a 'utf-8' o 'cp1252' si cambia la codificación del CSV
    encoding_csv = 'latin-1'
    
    with open(filepath, 'r', encoding=encoding_csv) as f:
        lines = f.readlines()

    header_idx = -1
    for i, l in enumerate(lines[:10]):
        # [REEMPLAZAR EN NUEVO SERVIDOR]: Cambiar la palabra clave de encabezado si el CSV modifica sus columnas
        if 'CC_INCIDENT_ID;' in l:
            header_idx = i
            break

    if header_idx == -1:
        raise ValueError(f"No se encontró el encabezado en {filepath}")

    # [REEMPLAZAR EN NUEVO SERVIDOR]: Cambiar el delimitador ';' si el CSV pasa a usar coma ',' o tabulador '\t'
    delimitador = ';'

    for line in lines[header_idx + 1:]:
        l_str = line.strip()
        if not l_str or l_str.startswith('-') or 'row(s) affected' in l_str:
            continue
        parts = line.rstrip('\r\n').split(delimitador)
        
        # [REEMPLAZAR EN NUEVO SERVIDOR]: Cambiar el número mínimo de columnas esperadas (actualmente 15)
        if len(parts) < 15:
            continue
        row = tuple(limpiar_valor(parts[idx]) for idx in range(15))
        rows.append(row)

    return rows


def parsear_csv_sm_rfc(filepath):
    """
    Parsea el archivo registrosSM-RFC.csv.
    """
    rows = []
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Cambiar 'latin-1' si cambia la codificación del archivo
    encoding_csv = 'latin-1'
    
    with open(filepath, 'r', encoding=encoding_csv) as f:
        lines = f.readlines()

    header_idx = -1
    for i, l in enumerate(lines[:10]):
        # [REEMPLAZAR EN NUEVO SERVIDOR]: Identificador de encabezado
        if 'NUMBER;' in l:
            header_idx = i
            break

    if header_idx == -1:
        raise ValueError(f"No se encontró el encabezado en {filepath}")

    # [REEMPLAZAR EN NUEVO SERVIDOR]: Delimitador del archivo CSV
    delimitador = ';'

    for line in lines[header_idx + 1:]:
        l_str = line.strip()
        if not l_str or l_str.startswith('-') or 'row(s) affected' in l_str:
            continue
        parts = line.rstrip('\r\n').split(delimitador)
        
        # [REEMPLAZAR EN NUEVO SERVIDOR]: Número total de columnas esperadas en RFC (actualmente 11)
        while len(parts) < 11:
            parts.append('')
        row = tuple(limpiar_valor(parts[idx]) for idx in range(11))
        rows.append(row)

    return rows


def main():
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Si la ruta raíz del proyecto no es relativa al script actual
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # [REEMPLAZAR EN NUEVO SERVIDOR]: Nombre o ruta absoluta de los archivos de configuración de conexión
    ruta_bd_cfg = os.path.join(base_dir, 'Conexion BD')    # Ruta del archivo de config BD
    ruta_ftp_cfg = os.path.join(base_dir, 'Conexion FTP')  # Ruta del archivo de config FTP

    print("==================================================")
    print("PROCESO DE CARGA Y VALIDACIÓN DE DATOS FTP A MSSQL (V2)")
    print("==================================================")

    config_bd = cargar_configuracion(ruta_bd_cfg)
    config_ftp = cargar_configuracion(ruta_ftp_cfg)

    # [REEMPLAZAR EN NUEVO SERVIDOR]: Nombres de los archivos a descargar desde el servidor FTP
    archivos_ftp = ['registrosRF_SD-SM.csv', 'registrosSM-RFC.csv']
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Directorio de descarga local (actualmente 'base_dir')
    dir_descarga_local = base_dir
    
    descargados = descargar_archivos_ftp(config_ftp, archivos_ftp, dir_destino=dir_descarga_local)

    # 3. Parsear archivos localmente
    print("\n[CSV] Parseando datos de archivos CSV...")
    raw_data_rf_sd_sm = parsear_csv_rf_sd_sm(descargados['registrosRF_SD-SM.csv'])
    data_sm_rfc_raw = parsear_csv_sm_rfc(descargados['registrosSM-RFC.csv'])

    # Deduplicar por CC_INCIDENT_ID para respetar la llave primaria
    dict_rf = {}
    for row in raw_data_rf_sd_sm:
        dict_rf[row[0]] = row  # row[0] corresponde a CC_INCIDENT_ID
    data_rf_sd_sm_raw = list(dict_rf.values())

    print(f"[CSV] 'registrosRF_SD-SM.csv': {len(raw_data_rf_sd_sm)} registros leídos ({len(data_rf_sd_sm_raw)} únicos por CC_INCIDENT_ID).")
    print(f"[CSV] 'registrosSM-RFC.csv': {len(data_sm_rfc_raw)} registros leídos.")

    # 4. Conectar a MSSQL
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Parámetros por defecto para conexión SQL Server si fallan los archivos de config
    server = config_bd.get('Server', '200.14.222.162')
    port = int(config_bd.get('Port', 1433))
    user = config_bd.get('User', 'sa')
    password = config_bd.get('Password', '')
    database = config_bd.get('Database', 'Sharepoint_Proyectos')

    print(f"\n[MSSQL] Conectando a {server}:{port} / BD: {database}...")
    conn = pymssql.connect(
        server=server,
        port=port,
        user=user,
        password=password,
        database=database
    )
    cursor = conn.cursor()

    # 5. Obtener mapa de proyectos limpios desde dbo.Proyectos
    print("[MSSQL] Cargando mapa de proyectos desde 'dbo.Proyectos'...")
    mapa_proyectos = obtener_mapa_proyectos(cursor)
    print(f"[MSSQL] Mapa cargado con {len(mapa_proyectos)} proyectos únicos.")

    # 6. Enriquecer datos con ID_Proyecto y Numero_Proyecto_Limpio
    print("[ETL] Enrumando y relacionando registros con 'dbo.Proyectos'...")

    data_sm_rfc = []
    matched_sm = 0
    for r in data_sm_rfc_raw:
        # [REEMPLAZAR EN NUEVO SERVIDOR]: Índice 4 corresponde a la columna CC_PROYECT_NUMBER
        cc_proj = r[4]
        num_limpio = extraer_numero_proyecto_limpio(cc_proj)
        id_proy = mapa_proyectos.get(num_limpio) if num_limpio else None
        if id_proy is not None:
            matched_sm += 1
        data_sm_rfc.append(r + (id_proy, num_limpio))

    data_rf_sd_sm = []
    matched_rf = 0
    for r in data_rf_sd_sm_raw:
        # [REEMPLAZAR EN NUEVO SERVIDOR]: Índice 6 corresponde a BRIEF_DESCRIPTION
        brief_desc = r[6]
        
        # [REEMPLAZAR EN NUEVO SERVIDOR]: Expresión regular para buscar códigos de proyecto en la descripción
        match = re.search(r'(?:py|proyecto|solot)?\s*0*(\d{6,10})', brief_desc or '', re.IGNORECASE)
        num_limpio = match.group(1) if match else None
        id_proy = mapa_proyectos.get(num_limpio) if num_limpio else None
        if id_proy is not None:
            matched_rf += 1
        data_rf_sd_sm.append(r + (id_proy, num_limpio))

    print(f"[ETL] registrosSM_RFC: {matched_sm}/{len(data_sm_rfc)} enlazados con Proyectos.")
    print(f"[ETL] registrosRF_SD_SM: {matched_rf}/{len(data_rf_sd_sm)} enlazados con Proyectos.")

    # 7. Truncar tablas antes de reinsertar datos
    print("[MSSQL] Truncando datos de las tablas existentes...")
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Cambiar nombres de tabla si se usan esquemas o nombres distintos
    tabla_rf = "dbo.registrosRF_SD_SM"
    tabla_sm = "dbo.registrosSM_RFC"
    
    cursor.execute(f"TRUNCATE TABLE {tabla_rf};")
    cursor.execute(f"TRUNCATE TABLE {tabla_sm};")
    conn.commit()
    print(f"[MSSQL] Tablas '{tabla_rf}' y '{tabla_sm}' truncadas correctamente.")

    # 8. Insertar datos enriquecidos en la BD
    print(f"[MSSQL] Insertando registros enriquecidos en '{tabla_rf}'...")
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Ajustar sentencia INSERT si cambian las columnas en la BD receptora
    sql_ins_1 = f"""
    INSERT INTO {tabla_rf} (
        CC_INCIDENT_ID, REQUESTOR_NAME, CURRENT_PHASE, STATUS, SUBMIT_DATE, CLOSE_DATE,
        BRIEF_DESCRIPTION, CATEGORY, SUBCATEGORY, CC_DETALLE_SERVICIO, CC_DETALLE,
        ASSIGNED_GROUP, ASSIGNED_TO, AFFECTED_ITEM, RF_ID, ID_Proyecto, Numero_Proyecto_Limpio
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %d, %s)
    """
    cursor.executemany(sql_ins_1, data_rf_sd_sm)

    print(f"[MSSQL] Insertando registros enriquecidos en '{tabla_sm}'...")
    
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Ajustar sentencia INSERT si cambian las columnas en la BD receptora
    sql_ins_2 = f"""
    INSERT INTO {tabla_sm} (
        NUMBER, BRIEF_DESCRIPTION, REQUESTED_BY, CLOSE_TIME, CC_PROYECT_NUMBER,
        CC_SERVICIO_PADRE, COORDINATOR, ASSIGN_DEPT, ASSIGNED_TO, DESCRIPTION, ORIG_DATE_ENTERED,
        ID_Proyecto, Numero_Proyecto_Limpio
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %d, %s)
    """
    cursor.executemany(sql_ins_2, data_sm_rfc)

    conn.commit()
    print("[MSSQL] Inserción completada con éxito.")

    # 9. Validación y comparación de datos
    print("\n==================================================")
    print("VALIDACIÓN Y COMPARACIÓN DE DATOS (CSV vs MSSQL)")
    print("==================================================")

    cursor.execute(f"SELECT COUNT(*) FROM {tabla_rf};")
    count_db_1 = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM {tabla_sm};")
    count_db_2 = cursor.fetchone()[0]

    match_1 = (len(data_rf_sd_sm) == count_db_1)
    match_2 = (len(data_sm_rfc) == count_db_2)

    print(f"Tabla 1 ({tabla_rf}):")
    print(f"  - Registros en CSV: {len(data_rf_sd_sm)}")
    print(f"  - Registros en BD:  {count_db_1}")
    print(f"  - Coincidencia:     {'✅ CORRECTO (100% de datos insertados)' if match_1 else '❌ DISCREPANCIA'}")

    print(f"\nTabla 2 ({tabla_sm}):")
    print(f"  - Registros en CSV: {len(data_sm_rfc)}")
    print(f"  - Registros en BD:  {count_db_2}")
    print(f"  - Coincidencia:     {'✅ CORRECTO (100% de datos insertados)' if match_2 else '❌ DISCREPANCIA'}")

    conn.close()
    print("\n[PROCESO FINALIZADO CON ÉXITO]")


if __name__ == '__main__':
    main()
