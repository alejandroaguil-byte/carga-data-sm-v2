-- ==============================================================================
-- CONSULTAS DE EJEMPLO Y CRUCES DE DATOS DE BACKLOG DE OPERACIONES SGA
-- Base de Datos: Sharepoint_Proyectos
-- Tablas involucradas:
--   - dbo.CT_BACKLOG_OPERACIONES2 (Backlog Operaciones SGA)
--   - dbo.Proyectos (Tabla Maestra de Proyectos)
--   - dbo.registrosRF_SD_SM (Incidentes HPSM)
--   - dbo.registrosSM_RFC (Solicitudes de Cambio HPSM)
-- ==============================================================================

--------------------------------------------------------------------------------
-- 1. CONSULTA DE CRUCE: BACKLOG DE OPERACIONES CON PROYECTOS MAESTROS
-- Muestra las operaciones de backlog enlazadas directamente con la tabla de proyectos.
--------------------------------------------------------------------------------
SELECT 
    b.id AS ID_Backlog,
    b.NRO_PROYECTO AS Nro_Proyecto_Origen,
    b.Numero_Proyecto_Limpio,
    b.ID_Proyecto,
    p.Nombre_Proyecto,
    p.Cliente AS Cliente_Proyecto,
    b.CLI_CLIENTE AS Cliente_Backlog,
    b.ID_OTP,
    b.TIPO_OTP,
    b.ESTADO_OTP,
    b.DESCR_OTP,
    b.STATUS_SOLOT,
    b.FECHA_COMPROMETIDA
FROM dbo.CT_BACKLOG_OPERACIONES2 b
INNER JOIN dbo.Proyectos p ON b.ID_Proyecto = p.ID
ORDER BY b.FECHA_COMPROMETIDA DESC;


--------------------------------------------------------------------------------
-- 2. CONSULTA DE CRUCE: BACKLOG DE OPERACIONES CON INCIDENTES (registrosRF_SD_SM)
-- Cruza el backlog de operaciones con los incidentes de Service Manager por el mismo proyecto.
--------------------------------------------------------------------------------
SELECT 
    b.NRO_PROYECTO AS Nro_Proyecto_Backlog,
    b.Numero_Proyecto_Limpio,
    p.Nombre_Proyecto,
    b.ID_OTP,
    b.DESCR_OTP AS Descripcion_Backlog,
    b.ESTADO_OTP,
    rf.CC_INCIDENT_ID,
    rf.BRIEF_DESCRIPTION AS Descripcion_Incidente,
    rf.STATUS AS Estado_Incidente,
    rf.ASSIGNED_GROUP AS Grupo_Asignado_Incidente
FROM dbo.CT_BACKLOG_OPERACIONES2 b
INNER JOIN dbo.Proyectos p ON b.ID_Proyecto = p.ID
INNER JOIN dbo.registrosRF_SD_SM rf ON b.ID_Proyecto = rf.ID_Proyecto
ORDER BY b.Numero_Proyecto_Limpio, rf.CC_INCIDENT_ID;


--------------------------------------------------------------------------------
-- 3. CONSULTA DE CRUCE: BACKLOG DE OPERACIONES CON RFCs (registrosSM_RFC)
-- Cruza el backlog de operaciones con las solicitudes de cambio por proyecto.
--------------------------------------------------------------------------------
SELECT 
    b.NRO_PROYECTO AS Nro_Proyecto_Backlog,
    b.Numero_Proyecto_Limpio,
    p.Nombre_Proyecto,
    b.ID_OTP,
    b.DESCR_OTP AS Descripcion_Backlog,
    b.STATUS_SOLOT,
    sm.NUMBER AS Codigo_RFC,
    sm.BRIEF_DESCRIPTION AS Descripcion_RFC,
    sm.COORDINATOR AS Coordinador_RFC,
    sm.ASSIGN_DEPT AS Depto_Asignado_RFC
FROM dbo.CT_BACKLOG_OPERACIONES2 b
INNER JOIN dbo.Proyectos p ON b.ID_Proyecto = p.ID
INNER JOIN dbo.registrosSM_RFC sm ON b.ID_Proyecto = sm.ID_Proyecto
ORDER BY b.Numero_Proyecto_Limpio, sm.NUMBER;


--------------------------------------------------------------------------------
-- 4. CONSULTA INTEGRAL DE 4 VÍAS: PROYECTOS + BACKLOG + INCIDENTES + RFCs
-- Vista consolidada completa agregando totales por proyecto.
--------------------------------------------------------------------------------
SELECT 
    p.ID AS ID_Proyecto,
    p.Numero_Proyecto,
    p.Nombre_Proyecto,
    COUNT(DISTINCT b.id) AS Total_Operaciones_Backlog,
    COUNT(DISTINCT rf.CC_INCIDENT_ID) AS Total_Incidentes,
    COUNT(DISTINCT sm.NUMBER) AS Total_RFCs
FROM dbo.Proyectos p
LEFT JOIN dbo.CT_BACKLOG_OPERACIONES2 b ON p.ID = b.ID_Proyecto
LEFT JOIN dbo.registrosRF_SD_SM rf ON p.ID = rf.ID_Proyecto
LEFT JOIN dbo.registrosSM_RFC sm ON p.ID = sm.ID_Proyecto
GROUP BY p.ID, p.Numero_Proyecto, p.Nombre_Proyecto
HAVING COUNT(DISTINCT b.id) > 0 OR COUNT(DISTINCT rf.CC_INCIDENT_ID) > 0 OR COUNT(DISTINCT sm.NUMBER) > 0
ORDER BY Total_Operaciones_Backlog DESC;


--------------------------------------------------------------------------------
-- 5. RESUMEN DE COINCIDENCIAS Y TASA DE ENLACE DE BACKLOG CON PROYECTOS
-- Muestra el porcentaje de registros del backlog que lograron asociarse a un proyecto maestro.
--------------------------------------------------------------------------------
SELECT 
    COUNT(*) AS Total_Registros_Backlog,
    SUM(CASE WHEN ID_Proyecto IS NOT NULL THEN 1 ELSE 0 END) AS Enlazados_Con_Proyecto,
    SUM(CASE WHEN ID_Proyecto IS NULL THEN 1 ELSE 0 END) AS Sin_Proyecto_Enlazado,
    CAST(ROUND(SUM(CASE WHEN ID_Proyecto IS NOT NULL THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS NUMERIC(5,2)) AS Porcentaje_Enlazado
FROM dbo.CT_BACKLOG_OPERACIONES2;
