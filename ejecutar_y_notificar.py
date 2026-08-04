#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Ejecución Automatizada y Notificación por Correo
=========================================================
Proyecto: Carga Data SM_v2
Este script ejecuta 'procesar_datos_ftp.py', captura toda la salida (log),
guarda la bitácora en 'ejecucion.log' y envía un correo electrónico reportando
el resultado (ÉXITO / ERROR) junto con el detalle de la ejecución.
"""

import os
import sys
import subprocess
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def cargar_configuracion(file_path):
    """Lee un archivo de configuración clave: valor."""
    config = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or ':' not in line:
                    continue
                key, val = line.split(':', 1)
                config[key.strip()] = val.strip()
    return config


def enviar_correo(asunto, cuerpo, config_email):
    """Envía un correo electrónico con los parámetros configurados en 'Conexion Email'."""
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Valores por defecto si no existen en 'Conexion Email'
    servidor_smtp = config_email.get('Server', 'smtp.gmail.com')
    puerto_smtp = int(config_email.get('Port', 587))
    usuario_smtp = config_email.get('User', '')
    password_smtp = config_email.get('Password', '')
    destinatario = config_email.get('To', 'alejandroaguil@gmail.com')
    use_tls = config_email.get('Use_TLS', 'True').lower() in ('true', '1', 'yes')

    remitente = usuario_smtp if usuario_smtp else 'notificaciones@cargadatasm.local'

    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    msg['Subject'] = asunto

    msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

    print(f"[EMAIL] Intentando enviar notificación a {destinatario}...")

    try:
        if use_tls and puerto_smtp == 465:
            server = smtplib.SMTP_SSL(servidor_smtp, puerto_smtp, timeout=30)
        else:
            server = smtplib.SMTP(servidor_smtp, puerto_smtp, timeout=30)
            if use_tls:
                server.starttls()

        if usuario_smtp and password_smtp:
            server.login(usuario_smtp, password_smtp)
            server.sendmail(remitente, [destinatario], msg.as_string())
            server.quit()
            print(f"[EMAIL] ✅ Correo enviado exitosamente a {destinatario}.")
            return True
        else:
            print("[EMAIL] ⚠️ No se proporcionaron credenciales completas (User/Password) en 'Conexion Email'.")
            print(f"[EMAIL] Correo preparado para: {destinatario}")
            print(f"[EMAIL] Asunto: {asunto}")
            server.quit()
            return False
    except Exception as e:
        print(f"[EMAIL] ❌ Error al enviar correo SMTP: {e}")
        return False


def main():
    # [REEMPLAZAR EN NUEVO SERVIDOR]: Si la ruta raíz del proyecto cambia
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_procesar = os.path.join(base_dir, 'procesar_datos_ftp.py')
    archivo_log = os.path.join(base_dir, 'ejecucion.log')
    archivo_email_cfg = os.path.join(base_dir, 'Conexion Email')

    config_email = cargar_configuracion(archivo_email_cfg)
    destinatario = config_email.get('To', 'alejandroaguil@gmail.com')

    inicio_dt = datetime.datetime.now()
    fecha_str = inicio_dt.strftime('%Y-%m-%d %H:%M:%S')

    header_log = f"\n==================================================\nINICIO DE EJECUCIÓN: {fecha_str}\n==================================================\n"
    print(header_log.strip())

    # Ejecutar el script procesar_datos_ftp.py
    cmd = [sys.executable, script_procesar]
    
    try:
        resultado = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=base_dir,
            timeout=300
        )
        salida_script = resultado.stdout
        codigo_salida = resultado.returncode
    except Exception as e:
        salida_script = f"Error ejecutando el script: {e}"
        codigo_salida = -1

    fin_dt = datetime.datetime.now()
    duracion_segs = round((fin_dt - inicio_dt).total_seconds(), 2)

    es_exitoso = (codigo_salida == 0 and '[PROCESO FINALIZADO CON ÉXITO]' in salida_script)
    estado_str = "ÉXITO" if es_exitoso else "ERROR"

    footer_log = f"\n--------------------------------------------------\nFIN DE EJECUCIÓN: {fin_dt.strftime('%Y-%m-%d %H:%M:%S')} (Duración: {duracion_segs}s, Estado: {estado_str})\n--------------------------------------------------\n"

    # Guardar en archivo ejecucion.log
    with open(archivo_log, 'a', encoding='utf-8') as f_log:
        f_log.write(header_log)
        f_log.write(salida_script)
        f_log.write(footer_log)

    print(salida_script)
    print(footer_log.strip())

    # Construir el correo de notificación
    asunto = f"[{estado_str}] Reporte Carga Data SM - {inicio_dt.strftime('%d/%m/%Y %H:%M')}"
    
    cuerpo_correo = f"""REPORTE DE EJECUCIÓN - PROCESO CARGA DATA SM
==================================================
Fecha y Hora de Inicio: {fecha_str}
Fecha y Hora de Término: {fin_dt.strftime('%Y-%m-%d %H:%M:%S')}
Duración: {duracion_segs} segundos
Estado del Proceso: {estado_str}
Destinatario: {destinatario}
==================================================

DETALLE COMPLETO DE LA EJECUCIÓN (LOG):
--------------------------------------------------
{salida_script}
--------------------------------------------------
Fin del reporte.
"""

    # Enviar correo
    enviar_correo(asunto, cuerpo_correo, config_email)


if __name__ == '__main__':
    main()
