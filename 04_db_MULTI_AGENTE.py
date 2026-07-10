# =====================================================
# db.py - Multi-Agente
# MiAgenteInmobiliario
# =====================================================

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "propiedades.db"

# Asegurar que existe el directorio
DB_PATH.parent.mkdir(exist_ok=True)

def get_connection():
    """Obtiene conexión a la BD"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa las tablas de la BD"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla: agentes
    cursor.execute("""
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
        )
    """)
    
    # Tabla: propiedades (con agente_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS propiedades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agente_id INTEGER DEFAULT 1,
            tipo_propiedad TEXT,
            operacion TEXT,
            direccion TEXT,
            ciudad_estado TEXT,
            precio REAL,
            habitaciones INTEGER,
            banos INTEGER,
            metros_construidos REAL,
            estacionamientos INTEGER,
            nombre_agente TEXT,
            telefono_agente TEXT,
            descripcion TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agente_id) REFERENCES agentes(id)
        )
    """)
    
    # Tabla: publicaciones (con agente_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS publicaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agente_id INTEGER DEFAULT 1,
            propiedad_id INTEGER,
            tipo TEXT,
            imagen_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (propiedad_id) REFERENCES propiedades(id),
            FOREIGN KEY (agente_id) REFERENCES agentes(id)
        )
    """)
    
    # Tabla: configuracion
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agente_id INTEGER UNIQUE,
            clave TEXT,
            valor TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agente_id) REFERENCES agentes(id)
        )
    """)
    
    # Crear índices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_propiedades_agente_id ON propiedades(agente_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_publicaciones_agente_id ON publicaciones(agente_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_agentes_slug ON agentes(slug)")
    
    conn.commit()
    conn.close()

# =====================================================
# FUNCIONES: AGENTES
# =====================================================

def obtener_agente_por_slug(slug: str):
    """Obtiene un agente por su slug"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM agentes WHERE slug = ?", (slug,))
    agente = cursor.fetchone()
    conn.close()
    
    if agente:
        return dict(agente)
    return None

def obtener_agente_por_id(agente_id: int):
    """Obtiene un agente por su ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM agentes WHERE id = ?", (agente_id,))
    agente = cursor.fetchone()
    conn.close()
    
    if agente:
        return dict(agente)
    return None

def obtener_todos_agentes():
    """Obtiene todos los agentes activos"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM agentes WHERE activo = 1 ORDER BY nombre")
    agentes = cursor.fetchall()
    conn.close()
    
    return [dict(a) for a in agentes]

def crear_agente(nombre: str, slug: str, email: str = None, telefono: str = None, logo_url: str = None):
    """Crea un nuevo agente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO agentes (nombre, slug, email, telefono, logo_url)
        VALUES (?, ?, ?, ?, ?)
    """, (nombre, slug, email, telefono, logo_url))
    
    agente_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return obtener_agente_por_id(agente_id)

# =====================================================
# FUNCIONES: PROPIEDADES
# =====================================================

def guardar_propiedad(datos: dict, agente_id: int = 1):
    """Guarda una propiedad en la BD"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO propiedades (
            agente_id, tipo_propiedad, operacion, direccion, ciudad_estado,
            precio, habitaciones, banos, metros_construidos, estacionamientos,
            nombre_agente, telefono_agente, descripcion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        agente_id,
        datos.get('tipo_propiedad'),
        datos.get('operacion'),
        datos.get('direccion'),
        datos.get('ciudad_estado'),
        float(datos.get('precio', 0)),
        int(datos.get('habitaciones', 0)),
        int(datos.get('banos', 0)),
        float(datos.get('metros_construidos', 0)),
        int(datos.get('estacionamientos', 0)) if datos.get('estacionamientos') else None,
        datos.get('nombre_agente'),
        datos.get('telefono_agente'),
        datos.get('descripcion')
    ))
    
    propiedad_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return propiedad_id

def obtener_propiedades(limit: int = 100):
    """Obtiene todas las propiedades (DEPRECATED - usar obtener_propiedades_por_agente)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM propiedades ORDER BY created_at DESC LIMIT ?", (limit,))
    propiedades = cursor.fetchall()
    conn.close()
    
    return [dict(p) for p in propiedades]

def obtener_propiedades_por_agente(agente_id: int, limit: int = 100):
    """Obtiene propiedades de un agente específico"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM propiedades 
        WHERE agente_id = ?
        ORDER BY created_at DESC 
        LIMIT ?
    """, (agente_id, limit))
    
    propiedades = cursor.fetchall()
    conn.close()
    
    return [dict(p) for p in propiedades]

# =====================================================
# FUNCIONES: PUBLICACIONES
# =====================================================

def guardar_publicacion(propiedad_id: int, imagen_url: str, tipo: str = "portada", agente_id: int = 1):
    """Guarda una publicación en la BD"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO publicaciones (agente_id, propiedad_id, tipo, imagen_url)
        VALUES (?, ?, ?, ?)
    """, (agente_id, propiedad_id, tipo, imagen_url))
    
    conn.commit()
    conn.close()

def obtener_publicaciones_por_agente(agente_id: int, limit: int = 100):
    """Obtiene publicaciones de un agente específico"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.*, pr.tipo_propiedad, pr.precio 
        FROM publicaciones p
        JOIN propiedades pr ON p.propiedad_id = pr.id
        WHERE p.agente_id = ?
        ORDER BY p.created_at DESC 
        LIMIT ?
    """, (agente_id, limit))
    
    publicaciones = cursor.fetchall()
    conn.close()
    
    return [dict(pub) for pub in publicaciones]

# =====================================================
# FUNCIONES: CONFIGURACION
# =====================================================

def obtener_configuracion(agente_id: int):
    """Obtiene la configuración de un agente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT clave, valor FROM configuracion
        WHERE agente_id = ?
    """, (agente_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    config = {}
    for row in rows:
        config[row['clave']] = row['valor']
    
    return config

def guardar_configuracion(agente_id: int, config: dict):
    """Guarda la configuración de un agente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    for clave, valor in config.items():
        cursor.execute("""
            INSERT OR REPLACE INTO configuracion (agente_id, clave, valor)
            VALUES (?, ?, ?)
        """, (agente_id, clave, valor))
    
    conn.commit()
    conn.close()

# =====================================================
# SCRIPTS DE MIGRACIÓN
# =====================================================

def migrar_a_multi_agente():
    """
    Script para migrar a multi-agente
    Crea el agente 'Francisco A Barreto' con id=1
    Asigna todos los datos existentes a este agente
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Crear agente por defecto
    cursor.execute("""
        INSERT OR IGNORE INTO agentes 
        (id, nombre, slug, email, telefono, logo_url)
        VALUES (1, 'Francisco A Barreto', 'francisco-a-barreto', 
                'francisco@miagentesinmobiliario.com', '+58414896016', 'static/logo.png')
    """)
    
    # 2. Asignar propiedades existentes a Francisco
    cursor.execute("UPDATE propiedades SET agente_id = 1 WHERE agente_id IS NULL OR agente_id = 0")
    
    # 3. Asignar publicaciones existentes a Francisco
    cursor.execute("UPDATE publicaciones SET agente_id = 1 WHERE agente_id IS NULL OR agente_id = 0")
    
    conn.commit()
    conn.close()
    
    print("✅ Migración a multi-agente completada")

if __name__ == "__main__":
    init_db()
    migrar_a_multi_agente()
    print("✅ Base de datos inicializada")
