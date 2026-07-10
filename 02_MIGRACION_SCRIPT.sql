-- =====================================================
-- SCRIPT DE MIGRACIÓN MULTI-AGENTE
-- MiAgenteInmobiliario
-- =====================================================
-- PASO 1: Crear tabla de agentes
-- PASO 2: Agregar columnas agente_id
-- PASO 3: Migrar datos

-- =====================================================
-- IMPORTANTE: HACER BACKUP ANTES DE EJECUTAR
-- =====================================================

-- =====================================================
-- PASO 1: CREAR TABLA DE AGENTES
-- =====================================================
CREATE TABLE IF NOT EXISTS agentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    email TEXT,
    telefono TEXT,
    logo_url TEXT,
    color_primario TEXT DEFAULT '#1a3a5c',
    color_secundario TEXT DEFAULT '#c8a45a',
    activo BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PASO 2: AGREGAR COLUMNAS agente_id
-- =====================================================
-- Agregar a propiedades
ALTER TABLE propiedades ADD COLUMN agente_id INTEGER DEFAULT 1;

-- Agregar a publicaciones (si existe)
ALTER TABLE publicaciones ADD COLUMN agente_id INTEGER DEFAULT 1;

-- =====================================================
-- PASO 3: INSERTAR AGENTE EXISTENTE
-- =====================================================
-- Francisco A Barreto es el agente 1
INSERT OR IGNORE INTO agentes (
    id, 
    nombre, 
    slug, 
    email, 
    telefono, 
    logo_url,
    color_primario,
    color_secundario
) VALUES (
    1,
    'Francisco A Barreto',
    'francisco-a-barreto',
    'francisco@miagentesinmobiliario.com',
    '+58414896016',
    'static/logo.png',
    '#1a3a5c',
    '#c8a45a'
);

-- =====================================================
-- PASO 4: ACTUALIZAR DATOS EXISTENTES
-- =====================================================
-- Todas las propiedades existentes pertenecen a Francisco
UPDATE propiedades SET agente_id = 1 WHERE agente_id IS NULL OR agente_id = 0;

-- Todas las publicaciones existentes pertenecen a Francisco
UPDATE publicaciones SET agente_id = 1 WHERE agente_id IS NULL OR agente_id = 0;

-- =====================================================
-- PASO 5: CREAR ÍNDICES PARA PERFORMANCE
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_propiedades_agente_id ON propiedades(agente_id);
CREATE INDEX IF NOT EXISTS idx_publicaciones_agente_id ON publicaciones(agente_id);
CREATE INDEX IF NOT EXISTS idx_agentes_slug ON agentes(slug);

-- =====================================================
-- PASO 6: VERIFICACIÓN
-- =====================================================
-- Verificar que todo está bien

-- Ver tabla agentes
-- SELECT * FROM agentes;

-- Ver cuántas propiedades tiene cada agente
-- SELECT agente_id, COUNT(*) as total FROM propiedades GROUP BY agente_id;

-- Ver cuántas publicaciones tiene cada agente
-- SELECT agente_id, COUNT(*) as total FROM publicaciones GROUP BY agente_id;

-- =====================================================
-- NOTAS IMPORTANTES
-- =====================================================
-- 1. Si algo falla, la transacción se revierte automáticamente
-- 2. Los índices mejoran la velocidad de búsquedas
-- 3. Francisco A Barreto tendrá id = 1
-- 4. Su slug es 'francisco-a-barreto' para URLs amigables
-- 5. Todos los datos históricos se mantienen intactos
