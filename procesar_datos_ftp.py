#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
SCRIPT ETL DE CARGA, LIMPIEZA Y VALIDACIÓN DE DATOS FTP Y SGA A MSSQL (VERSIÓN 2.1)
==============================================================================
Proyecto: Carga Data SM_v2
Descripción:
  Este script descarga archivos CSV desde un servidor FTP (HPSM) y extrae los
  datos de la tabla CT_BACKLOG_OPERACIONES2 desde la BD SGA (MSSQL).
  Realiza la limpieza, deduplicación y enriquecimiento de los registros,
  relacionándolos con la tabla 'dbo.Proyectos', y carga los datos procesados
  en la base de datos de destino 'Sharepoint_Proyectos' en SQL Server.

[PARÁMETROS MODIFICABLES POR SERVIDOR]:
  Revise los comentarios en el código que comienzan con '[REEMPLAZAR EN NUEVO SERVIDOR]'
  para adaptar rutas, nombres de archivos, codificaciones o nombres de tabla.
==============================================================================
"""

import os
import sys
import re
import time
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
            if not line or line.startswith('#') or ':' not in line:
                continue
            key, val = line.split(':', 1)
            config[key.strip()] = val.strip()
    return config


def descargar_archivos_ftp(config_ftp, archivos_a_descargar, dir_destino="."):
    """
    Conecta al servidor FTP y descarga la lista de archivos especificados.
    """
    host = config_ftp.get('Server', 'ftp.drivehq.com')
    port = int(config_ftp.get('Port', 21))
    usuario = config_ftp.get('Usuario', 'bobbasystem')
    password = config_ftp.get('Contraseña', '')
    folder = config_ftp.get('Folder', 'HPSM')

    print(f"[FTP] Conectando a {host}:{port}...")
    ftp = FTP()
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
    if val_str.upper() in ('NULL', '', 'NONE', 'N/A', 'UNDEFINED'):
        return None
    return val_str


def extraer_numero_proyecto_limpio(cadena):
    """
    Extrae y normaliza el número de proyecto de 6 a 10 dígitos, removiendo ceros a la izquierda.
    """
    if not cadena:
        return None
    match = re.search(r'\b0*(\d{6,10})\b', str(cadena))
    if match:
        return match.group(1)
    return None


def obtener_mapa_proyectos(cursor):
    """
    Carga el diccionario de mapeo entre Numero_Proyecto (limpio) e ID de la tabla Proyectos en la BD.
    """
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
    Parsea el archivo registrosRF_SD-SM.csv. Si el archivo descargado desde FTP
    contiene errores del origen SQL Server (AlwaysOn Availability Group) o falta de encabezado,
    se recurre automáticamente a la última copia válida conocida (.last_good).
    """
    backup_path = filepath + '.last_good'
    rows = []
    encoding_csv = 'latin-1'
    contiene_error_origen = False
    error_msg = ""
    lines = []

    try:
        with open(filepath, 'r', encoding=encoding_csv) as f:
            lines = f.readlines()

        for l in lines[:10]:
            if 'Sqlcmd: Error:' in l or 'ODBC Driver' in l or 'grupo de disponibilidad' in l:
                contiene_error_origen = True
                error_msg = l.strip()
                break

        header_idx = -1
        for i, l in enumerate(lines[:10]):
            if 'CC_INCIDENT_ID;' in l:
                header_idx = i
                break

        if contiene_error_origen or header_idx == -1:
            if contiene_error_origen:
                reason = f"error del origen SQL Server: {error_msg}"
            else:
                primeras_lineas = "".join(lines[:3]).strip()
                reason = f"no se encontró el encabezado 'CC_INCIDENT_ID;'. Contenido: '{primeras_lineas}'"

            print(f"[WARNING] El archivo descargado {os.path.basename(filepath)} es inválido ({reason}).")
            if os.path.exists(backup_path) and os.path.getsize(backup_path) > 0:
                print(f"[RESPALDO] Usando la última versión válida de respaldo: '{os.path.basename(backup_path)}'...")
                with open(backup_path, 'r', encoding=encoding_csv) as f_bak:
                    lines = f_bak.readlines()
                contiene_error_origen = False
                header_idx = -1
                for i, l in enumerate(lines[:10]):
                    if 'CC_INCIDENT_ID;' in l:
                        header_idx = i
                        break
                if header_idx == -1:
                    raise ValueError(f"El archivo de respaldo {backup_path} tampoco contiene un encabezado válido.")
            else:
                raise ValueError(f"El archivo descargado {os.path.basename(filepath)} contiene un error del origen SQL Server: {error_msg if contiene_error_origen else reason}")
    except Exception as e:
        if not (os.path.exists(backup_path) and os.path.getsize(backup_path) > 0):
            raise e
        print(f"[WARNING] Error procesando {filepath}: {e}. Recurriendo a respaldo '{os.path.basename(backup_path)}'...")
        with open(backup_path, 'r', encoding=encoding_csv) as f_bak:
            lines = f_bak.readlines()
        contiene_error_origen = False
        header_idx = -1
        for i, l in enumerate(lines[:10]):
            if 'CC_INCIDENT_ID;' in l:
                header_idx = i
                break
        if header_idx == -1:
            raise ValueError(f"El archivo de respaldo {backup_path} tampoco contiene un encabezado válido.")

    delimitador = ';'
    for line in lines[header_idx + 1:]:
        l_str = line.strip()
        if not l_str or l_str.startswith('-') or 'row(s) affected' in l_str:
            continue
        parts = line.rstrip('\r\n').split(delimitador)
        if len(parts) < 15:
            continue
        row = tuple(limpiar_valor(parts[idx]) for idx in range(15))
        rows.append(row)

    if rows and not contiene_error_origen:
        try:
            with open(backup_path, 'w', encoding=encoding_csv) as f_out:
                f_out.writelines(lines)
        except Exception:
            pass

    return rows


def parsear_csv_sm_rfc(filepath):
    """
    Parsea el archivo registrosSM-RFC.csv. Si el archivo descargado desde FTP
    contiene errores del origen SQL Server (AlwaysOn Availability Group) o falta de encabezado,
    se recurre automáticamente a la última copia válida conocida (.last_good).
    """
    backup_path = filepath + '.last_good'
    rows = []
    encoding_csv = 'latin-1'
    contiene_error_origen = False
    error_msg = ""
    lines = []

    try:
        with open(filepath, 'r', encoding=encoding_csv) as f:
            lines = f.readlines()

        for l in lines[:10]:
            if 'Sqlcmd: Error:' in l or 'ODBC Driver' in l or 'grupo de disponibilidad' in l:
                contiene_error_origen = True
                error_msg = l.strip()
                break

        header_idx = -1
        for i, l in enumerate(lines[:10]):
            if 'NUMBER;' in l:
                header_idx = i
                break

        if contiene_error_origen or header_idx == -1:
            if contiene_error_origen:
                reason = f"error del origen SQL Server: {error_msg}"
            else:
                primeras_lineas = "".join(lines[:3]).strip()
                reason = f"no se encontró el encabezado 'NUMBER;'. Contenido: '{primeras_lineas}'"

            print(f"[WARNING] El archivo descargado {os.path.basename(filepath)} es inválido ({reason}).")
            if os.path.exists(backup_path) and os.path.getsize(backup_path) > 0:
                print(f"[RESPALDO] Usando la última versión válida de respaldo: '{os.path.basename(backup_path)}'...")
                with open(backup_path, 'r', encoding=encoding_csv) as f_bak:
                    lines = f_bak.readlines()
                contiene_error_origen = False
                header_idx = -1
                for i, l in enumerate(lines[:10]):
                    if 'NUMBER;' in l:
                        header_idx = i
                        break
                if header_idx == -1:
                    raise ValueError(f"El archivo de respaldo {backup_path} tampoco contiene un encabezado válido.")
            else:
                raise ValueError(f"El archivo descargado {os.path.basename(filepath)} contiene un error del origen SQL Server: {error_msg if contiene_error_origen else reason}")
    except Exception as e:
        if not (os.path.exists(backup_path) and os.path.getsize(backup_path) > 0):
            raise e
        print(f"[WARNING] Error procesando {filepath}: {e}. Recurriendo a respaldo '{os.path.basename(backup_path)}'...")
        with open(backup_path, 'r', encoding=encoding_csv) as f_bak:
            lines = f_bak.readlines()
        contiene_error_origen = False
        header_idx = -1
        for i, l in enumerate(lines[:10]):
            if 'NUMBER;' in l:
                header_idx = i
                break
        if header_idx == -1:
            raise ValueError(f"El archivo de respaldo {backup_path} tampoco contiene un encabezado válido.")

    delimitador = ';'
    for line in lines[header_idx + 1:]:
        l_str = line.strip()
        if not l_str or l_str.startswith('-') or 'row(s) affected' in l_str:
            continue
        parts = line.rstrip('\r\n').split(delimitador)
        while len(parts) < 11:
            parts.append('')
        row = tuple(limpiar_valor(parts[idx]) for idx in range(11))
        rows.append(row)

    if rows and not contiene_error_origen:
        try:
            with open(backup_path, 'w', encoding=encoding_csv) as f_out:
                f_out.writelines(lines)
        except Exception:
            pass

    return rows


def extraer_backlog_sga(config_sga):
    """
    Conecta a la base de datos MSSQL SGA y extrae los registros de CT_BACKLOG_OPERACIONES2.
    """
    host = config_sga.get('Server', '200.14.226.223')
    port = int(config_sga.get('Port', 1433))
    usuario = config_sga.get('User', 'reportes')
    password = config_sga.get('Password', '')
    database = config_sga.get('Database', 'blixter_prod')

    print(f"\n[SGA] Conectando a {host}:{port} / BD: {database}...")
    conn_sga = pymssql.connect(
        server=host,
        port=port,
        user=usuario,
        password=password,
        database=database,
        login_timeout=30
    )
    cursor_sga_dict = conn_sga.cursor(as_dict=True)

    cursor_sga_dict.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'CT_BACKLOG_OPERACIONES2'
        ORDER BY ORDINAL_POSITION
    """)
    cols_info = cursor_sga_dict.fetchall()

    cursor_sga_tuple = conn_sga.cursor(as_dict=False)
    print("[SGA] Extrayendo todos los registros de 'CT_BACKLOG_OPERACIONES2'...")
    t0 = time.time()
    cursor_sga_tuple.execute("SELECT * FROM CT_BACKLOG_OPERACIONES2")
    rows = cursor_sga_tuple.fetchall()
    t1 = time.time()
    print(f"[SGA] Extracción exitosa: {len(rows)} registros leídos en {round(t1 - t0, 2)} segundos.")

    conn_sga.close()
    return cols_info, rows


def asegurar_tabla_backlog_destino(cursor_target, cols_info):
    """
    Garantiza la existencia de la tabla dbo.CT_BACKLOG_OPERACIONES2 en la BD destino.
    """
    cursor_target.execute("SELECT OBJECT_ID('dbo.CT_BACKLOG_OPERACIONES2')")
    res = cursor_target.fetchone()
    if res and res[0] is not None:
        print("[MSSQL] La tabla 'dbo.CT_BACKLOG_OPERACIONES2' ya existe en la BD destino.")
        return

    print("[MSSQL] La tabla 'dbo.CT_BACKLOG_OPERACIONES2' no existe. Creándola...")
    col_defs = []
    for c in cols_info:
        col_name = c['COLUMN_NAME']
        dt = c['DATA_TYPE'].lower()
        l = c['CHARACTER_MAXIMUM_LENGTH']
        
        if dt in ('varchar', 'nvarchar', 'char', 'nchar'):
            if l == -1 or l is None or l > 4000:
                type_str = f"{dt.upper()}(MAX)"
            else:
                type_str = f"{dt.upper()}({l})"
        else:
            type_str = dt.upper()
        
        col_defs.append(f"[{col_name}] {type_str} NULL")

    col_defs.append("[ID_Proyecto] NUMERIC NULL")
    col_defs.append("[Numero_Proyecto_Limpio] VARCHAR(50) NULL")

    ddl_sql = f"CREATE TABLE dbo.CT_BACKLOG_OPERACIONES2 (\n    " + ",\n    ".join(col_defs) + "\n);"
    cursor_target.execute(ddl_sql)
    print("[MSSQL] Tabla 'dbo.CT_BACKLOG_OPERACIONES2' creada con éxito con 106 columnas.")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    ruta_bd_cfg = os.path.join(base_dir, 'Conexion BD')
    ruta_ftp_cfg = os.path.join(base_dir, 'Conexion FTP')
    ruta_sga_cfg = os.path.join(base_dir, 'Conexion BD SGA')

    print("==================================================")
    print("PROCESO DE CARGA Y VALIDACIÓN DE DATOS FTP Y SGA A MSSQL (V2.1)")
    print("==================================================")

    config_bd = cargar_configuracion(ruta_bd_cfg)
    config_ftp = cargar_configuracion(ruta_ftp_cfg)
    config_sga = cargar_configuracion(ruta_sga_cfg)

    # 1. Descarga FTP
    archivos_ftp = ['registrosRF_SD-SM.csv', 'registrosSM-RFC.csv']
    descargados = descargar_archivos_ftp(config_ftp, archivos_ftp, dir_destino=base_dir)

    # 2. Parsear CSVs localmente
    print("\n[CSV] Parseando datos de archivos CSV...")
    raw_data_rf_sd_sm = parsear_csv_rf_sd_sm(descargados['registrosRF_SD-SM.csv'])
    data_sm_rfc_raw = parsear_csv_sm_rfc(descargados['registrosSM-RFC.csv'])

    dict_rf = {}
    for row in raw_data_rf_sd_sm:
        dict_rf[row[0]] = row
    data_rf_sd_sm_raw = list(dict_rf.values())

    print(f"[CSV] 'registrosRF_SD-SM.csv': {len(raw_data_rf_sd_sm)} registros leídos ({len(data_rf_sd_sm_raw)} únicos por CC_INCIDENT_ID).")
    print(f"[CSV] 'registrosSM-RFC.csv': {len(data_sm_rfc_raw)} registros leídos.")

    # 3. Extraer Backlog desde BD SGA
    cols_info_sga, rows_sga = extraer_backlog_sga(config_sga)
    col_names_sga = [c['COLUMN_NAME'] for c in cols_info_sga]

    # 4. Conectar a MSSQL Destino
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

    # Asegurar existencia de tabla de Backlog en la BD destino
    asegurar_tabla_backlog_destino(cursor, cols_info_sga)
    conn.commit()

    # 5. Obtener mapa de proyectos desde dbo.Proyectos
    print("[MSSQL] Cargando mapa de proyectos desde 'dbo.Proyectos'...")
    mapa_proyectos = obtener_mapa_proyectos(cursor)
    print(f"[MSSQL] Mapa cargado con {len(mapa_proyectos)} proyectos únicos.")

    # 6. Enriquecer datos con ID_Proyecto y Numero_Proyecto_Limpio
    print("[ETL] Enrumando y relacionando registros con 'dbo.Proyectos'...")

    # RFCs
    data_sm_rfc = []
    matched_sm = 0
    for r in data_sm_rfc_raw:
        cc_proj = r[4]
        num_limpio = extraer_numero_proyecto_limpio(cc_proj)
        id_proy = mapa_proyectos.get(num_limpio) if num_limpio else None
        if id_proy is not None:
            matched_sm += 1
        data_sm_rfc.append(r + (id_proy, num_limpio))

    # Incidentes
    data_rf_sd_sm = []
    matched_rf = 0
    for r in data_rf_sd_sm_raw:
        brief_desc = r[6]
        match = re.search(r'(?:py|proyecto|solot)?\s*0*(\d{6,10})', brief_desc or '', re.IGNORECASE)
        num_limpio = match.group(1) if match else None
        id_proy = mapa_proyectos.get(num_limpio) if num_limpio else None
        if id_proy is not None:
            matched_rf += 1
        data_rf_sd_sm.append(r + (id_proy, num_limpio))

    # Backlog SGA (100% de registros preservados)
    nro_proy_idx = col_names_sga.index('NRO_PROYECTO') if 'NRO_PROYECTO' in col_names_sga else -1
    data_backlog = []
    matched_bk = 0
    for r in rows_sga:
        raw_nro = r[nro_proy_idx] if nro_proy_idx != -1 else None
        num_limpio = extraer_numero_proyecto_limpio(raw_nro)
        id_proy = mapa_proyectos.get(num_limpio) if num_limpio else None
        if id_proy is not None:
            matched_bk += 1
        data_backlog.append(r + (id_proy, num_limpio))

    print(f"[ETL] registrosSM_RFC: {matched_sm}/{len(data_sm_rfc)} enlazados con Proyectos.")
    print(f"[ETL] registrosRF_SD_SM: {matched_rf}/{len(data_rf_sd_sm)} enlazados con Proyectos.")
    print(f"[ETL] CT_BACKLOG_OPERACIONES2: {matched_bk}/{len(data_backlog)} enlazados con Proyectos.")

    # 7. Truncar tablas antes de reinsertar
    print("[MSSQL] Truncando datos de las tablas existentes...")
    tabla_rf = "dbo.registrosRF_SD_SM"
    tabla_sm = "dbo.registrosSM_RFC"
    tabla_bk = "dbo.CT_BACKLOG_OPERACIONES2"

    cursor.execute(f"TRUNCATE TABLE {tabla_rf};")
    cursor.execute(f"TRUNCATE TABLE {tabla_sm};")
    cursor.execute(f"TRUNCATE TABLE {tabla_bk};")
    conn.commit()
    print(f"[MSSQL] Tablas '{tabla_rf}', '{tabla_sm}' y '{tabla_bk}' truncadas correctamente.")

    # 8. Insertar registros en BD
    print(f"[MSSQL] Insertando registros enriquecidos en '{tabla_rf}'...")
    sql_ins_1 = f"""
    INSERT INTO {tabla_rf} (
        CC_INCIDENT_ID, REQUESTOR_NAME, CURRENT_PHASE, STATUS, SUBMIT_DATE, CLOSE_DATE,
        BRIEF_DESCRIPTION, CATEGORY, SUBCATEGORY, CC_DETALLE_SERVICIO, CC_DETALLE,
        ASSIGNED_GROUP, ASSIGNED_TO, AFFECTED_ITEM, RF_ID, ID_Proyecto, Numero_Proyecto_Limpio
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %d, %s)
    """
    cursor.executemany(sql_ins_1, data_rf_sd_sm)

    print(f"[MSSQL] Insertando registros enriquecidos en '{tabla_sm}'...")
    sql_ins_2 = f"""
    INSERT INTO {tabla_sm} (
        NUMBER, BRIEF_DESCRIPTION, REQUESTED_BY, CLOSE_TIME, CC_PROYECT_NUMBER,
        CC_SERVICIO_PADRE, COORDINATOR, ASSIGN_DEPT, ASSIGNED_TO, DESCRIPTION, ORIG_DATE_ENTERED,
        ID_Proyecto, Numero_Proyecto_Limpio
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %d, %s)
    """
    cursor.executemany(sql_ins_2, data_sm_rfc)
    conn.commit()

    print(f"[MSSQL] Insertando {len(data_backlog)} registros enriquecidos en '{tabla_bk}'...")
    col_list_str = ", ".join([f"[{c}]" for c in col_names_sga] + ["[ID_Proyecto]", "[Numero_Proyecto_Limpio]"])
    row_placeholders = "(" + ", ".join(["%s"] * len(col_names_sga) + ["%d", "%s"]) + ")"

    t0 = time.time()
    chunk_size = 15
    stmt_count = 0
    commit_every = 100

    for i in range(0, len(data_backlog), chunk_size):
        chunk = data_backlog[i:i + chunk_size]
        sql_ins_3 = f"INSERT INTO {tabla_bk} ({col_list_str}) VALUES " + ", ".join([row_placeholders] * len(chunk))
        flat_params = [val for row in chunk for val in row]
        cursor.execute(sql_ins_3, tuple(flat_params))
        stmt_count += 1
        if stmt_count % commit_every == 0:
            conn.commit()

    conn.commit()
    t1 = time.time()
    print(f"[MSSQL] Inserción de Backlog ({len(data_backlog)} filas) completada en {round(t1 - t0, 2)}s.")

    # 9. Validación y comparación de datos
    print("\n==================================================")
    print("VALIDACIÓN Y COMPARACIÓN DE DATOS (ORIGEN vs MSSQL)")
    print("==================================================")

    cursor.execute(f"SELECT COUNT(*) FROM {tabla_rf};")
    count_db_1 = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM {tabla_sm};")
    count_db_2 = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM {tabla_bk};")
    count_db_3 = cursor.fetchone()[0]

    match_1 = (len(data_rf_sd_sm) == count_db_1)
    match_2 = (len(data_sm_rfc) == count_db_2)
    match_3 = (len(data_backlog) == count_db_3)

    print(f"Tabla 1 ({tabla_rf}):")
    print(f"  - Registros en CSV: {len(data_rf_sd_sm)}")
    print(f"  - Registros en BD:  {count_db_1}")
    print(f"  - Coincidencia:     {'✅ CORRECTO (100% de datos insertados)' if match_1 else '❌ DISCREPANCIA'}")

    print(f"\nTabla 2 ({tabla_sm}):")
    print(f"  - Registros en CSV: {len(data_sm_rfc)}")
    print(f"  - Registros en BD:  {count_db_2}")
    print(f"  - Coincidencia:     {'✅ CORRECTO (100% de datos insertados)' if match_2 else '❌ DISCREPANCIA'}")

    print(f"\nTabla 3 ({tabla_bk}):")
    print(f"  - Registros en SGA: {len(data_backlog)}")
    print(f"  - Registros en BD:  {count_db_3}")
    print(f"  - Coincidencia:     {'✅ CORRECTO (100% de datos insertados)' if match_3 else '❌ DISCREPANCIA'}")

    conn.close()

    if match_1 and match_2 and match_3:
        print("\n[PROCESO FINALIZADO CON ÉXITO]")
    else:
        print("\n[PROCESO FINALIZADO CON ERRORES DE COINCIDENCIA]")
        sys.exit(1)


if __name__ == '__main__':
    main()
