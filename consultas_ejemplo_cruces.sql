-- ============================================================================
-- Consultas SQL de Ejemplo para Cruzar Tablas en Sharepoint_Proyectos
-- ============================================================================
-- Este archivo contiene queries de prueba para relacionar la tabla 'Proyectos' 
-- con 'registrosSM_RFC' y 'registrosRF_SD_SM' mediante los campos relacionales
-- 'ID_Proyecto' y 'Numero_Proyecto_Limpio' generados en el proceso ETL.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Opción 1: Consulta Completa de Proyectos con sus RFCs e Incidentes/Requerimientos
-- (Útil para revisar el detalle de proyectos con sus solicitudes e incidentes)
-- ----------------------------------------------------------------------------
SELECT 
    p.ID AS ID_Proyecto,
    p.Numero_Proyecto,
    p.Cliente,
    p.LT_Asignado,
    p.Estado AS Estado_Proyecto,
    p.Detalle AS Detalle_Proyecto,
    -- Datos de RFC (registrosSM_RFC)
    rfc.NUMBER AS RFC_Number,
    rfc.BRIEF_DESCRIPTION AS RFC_Descripcion,
    rfc.REQUESTED_BY AS RFC_Solicitante,
    rfc.ASSIGNED_TO AS RFC_Asignado,
    -- Datos de Incidentes / Requerimientos (registrosRF_SD_SM)
    sd.CC_INCIDENT_ID AS Incidente_ID,
    sd.RF_ID AS Incidente_RF_ID,
    sd.BRIEF_DESCRIPTION AS Incidente_Descripcion,
    sd.STATUS AS Incidente_Estado,
    sd.ASSIGNED_TO AS Incidente_Asignado
FROM dbo.Proyectos p
INNER JOIN dbo.registrosSM_RFC rfc 
    ON rfc.ID_Proyecto = p.ID
LEFT JOIN dbo.registrosRF_SD_SM sd 
    ON sd.ID_Proyecto = p.ID
ORDER BY p.ID DESC, rfc.NUMBER;


-- ----------------------------------------------------------------------------
-- Opción 2: Resumen Ejecutivo Consolidado por Proyecto
-- (Agrupa y cuenta el total de RFCs e incidentes por proyecto)
-- ----------------------------------------------------------------------------
SELECT 
    p.ID AS ID_Proyecto,
    p.Numero_Proyecto,
    p.Cliente,
    p.Estado AS Estado_Proyecto,
    COUNT(DISTINCT rfc.NUMBER) AS Total_RFCs,
    COUNT(DISTINCT sd.CC_INCIDENT_ID) AS Total_Incidentes_SD
FROM dbo.Proyectos p
LEFT JOIN dbo.registrosSM_RFC rfc 
    ON rfc.ID_Proyecto = p.ID
LEFT JOIN dbo.registrosRF_SD_SM sd 
    ON sd.ID_Proyecto = p.ID
GROUP BY p.ID, p.Numero_Proyecto, p.Cliente, p.Estado
HAVING COUNT(DISTINCT rfc.NUMBER) > 0 OR COUNT(DISTINCT sd.CC_INCIDENT_ID) > 0
ORDER BY Total_RFCs DESC, Total_Incidentes_SD DESC;


-- ----------------------------------------------------------------------------
-- Opción 3: Cruce Alternativo usando Numero_Proyecto_Limpio
-- (Ideal si se quiere filtrar por el número de proyecto normalizado)
-- ----------------------------------------------------------------------------
SELECT 
    p.Numero_Proyecto,
    p.Cliente,
    rfc.NUMBER AS RFC_Numero,
    sd.CC_INCIDENT_ID AS Incidente_ID,
    rfc.Numero_Proyecto_Limpio
FROM dbo.registrosSM_RFC rfc
INNER JOIN dbo.registrosRF_SD_SM sd 
    ON rfc.Numero_Proyecto_Limpio = sd.Numero_Proyecto_Limpio
LEFT JOIN dbo.Proyectos p 
    ON rfc.ID_Proyecto = p.ID
WHERE rfc.Numero_Proyecto_Limpio IS NOT NULL;
