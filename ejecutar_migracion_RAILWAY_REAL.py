#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT DE MIGRACIÓN MULTI-AGENTE - BD REAL DE RAILWAY
MiAgenteInmobiliario

CRÍTICO: Adaptado específicamente para estructura actual de Railway
- 10 propiedades
- 13 noticias
- SIN tabla publicaciones
- SIN columna agente_id

NO PERDERÁ NADA. PRESERVA TODO.
"""

import sqlite3
from pathlib import Path

def column_exists(cursor, tabla, columna):
    """Verifica si una columna existe"""
    try:
        cursor.execute(f"PRAGMA table_info({tabla})")
        cols = [row[1] for row in cursor.fetchall()]
        return columna in cols
    except:
        return False

def table_exists(cursor, tabla):
    """Verifica si una tabla existe"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        return True
    except:
        return False

def ejecutar_migracion():
    """Ejecuta migración para BD REAL de Railway"""
    
    db_path = Path('data/propiedades.db')
    
    if not db_path.exists():
        print(f"❌ ERROR: No encontré BD en {db_path}")
        return False
    
    print("=" * 80)
    print("🚀 MIGRACIÓN MULTI-AGENTE - BD REAL DE RAILWAY")
    print("=" * 80 + "\n")
    
    print(f"📊 BD encontrada: {db_path}\n")
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("✅ Conexión exitosa\n")
        
        # =====================================================
        # VERIFICACIÓN INICIAL
        # =====================================================
        print("=" * 80)
        print("📋 VERIFICACIÓN DE ESTRUCTURA ACTUAL")
        print("=" * 80 + "\n")
        
        # Verificar propiedades
        cursor.execute("SELECT COUNT(*) FROM propiedades")
        props_count = cursor.fetchone()[0]
        print(f"✅ Propiedades actuales: {props_count}")
        
        # Verificar noticias
        cursor.execute("SELECT COUNT(*) FROM noticias")
        noticias_count = cursor.fetchone()[0]
        print(f"✅ Noticias actuales: {noticias_count}")
        
        # Verificar agentes
        cursor.execute("SELECT COUNT(*) FROM agentes")
        agentes_count = cursor.fetchone()[0]
        print(f"✅ Agentes actuales: {agentes_count}")
        
        # Verificar si ya tiene agente_id
        tiene_agente_id = column_exists(cursor, 'propiedades', 'agente_id')
        tiene_publicaciones = table_exists(cursor, 'publicaciones')
        
        print(f"✅ Propiedades tiene agente_id: {'SÍ' if tiene_agente_id else 'NO'}")
        print(f"✅ Tabla publicaciones existe: {'SÍ' if tiene_publicaciones else 'NO'}\n")
        
        # =====================================================
        # PASO 1: PREPARAR TABLA agentes
        # =====================================================
        print("=" * 80)
        print("⚙️  PASO 1: Preparar tabla agentes")
        print("=" * 80 + "\n")
        
        # Agregar slug
        if not column_exists(cursor, 'agentes', 'slug'):
            cursor.execute("ALTER TABLE agentes ADD COLUMN slug TEXT UNIQUE")
            print("   ✅ Columna 'slug' agregada")
        else:
            print("   ✅ Columna 'slug' ya existe")
        
        # Agregar logo_url
        if not column_exists(cursor, 'agentes', 'logo_url'):
            cursor.execute("ALTER TABLE agentes ADD COLUMN logo_url TEXT")
            print("   ✅ Columna 'logo_url' agregada")
        else:
            print("   ✅ Columna 'logo_url' ya existe")
        
        # Agregar colores
        if not column_exists(cursor, 'agentes', 'color_primario'):
            cursor.execute("ALTER TABLE agentes ADD COLUMN color_primario TEXT DEFAULT '#1a3a5c'")
            print("   ✅ Columna 'color_primario' agregada")
        else:
            print("   ✅ Columna 'color_primario' ya existe")
        
        if not column_exists(cursor, 'agentes', 'color_secundario'):
            cursor.execute("ALTER TABLE agentes ADD COLUMN color_secundario TEXT DEFAULT '#c8a45a'")
            print("   ✅ Columna 'color_secundario' agregada")
        else:
            print("   ✅ Columna 'color_secundario' ya existe")
        
        # Agregar email y teléfono
        if not column_exists(cursor, 'agentes', 'email'):
            cursor.execute("ALTER TABLE agentes ADD COLUMN email TEXT")
            print("   ✅ Columna 'email' agregada")
        else:
            print("   ✅ Columna 'email' ya existe")
        
        if not column_exists(cursor, 'agentes', 'telefono'):
            cursor.execute("ALTER TABLE agentes ADD COLUMN telefono TEXT")
            print("   ✅ Columna 'telefono' agregada")
        else:
            print("   ✅ Columna 'telefono' ya existe")
        
        # Generar slugs basados en usuarios
        cursor.execute("SELECT id, usuario FROM agentes WHERE slug IS NULL")
        agentes_sin_slug = cursor.fetchall()
        
        for agente in agentes_sin_slug:
            slug = agente[1].lower()
            cursor.execute("UPDATE agentes SET slug = ? WHERE id = ?", (slug, agente[0]))
            print(f"   ✅ Slug generado: {agente[1]} → {slug}")
        
        print()
        
        # =====================================================
        # PASO 2: AGREGAR agente_id A propiedades
        # =====================================================
        print("=" * 80)
        print("⚙️  PASO 2: Agregar agente_id a propiedades")
        print("=" * 80 + "\n")
        
        if not column_exists(cursor, 'propiedades', 'agente_id'):
            cursor.execute("ALTER TABLE propiedades ADD COLUMN agente_id INTEGER DEFAULT 1")
            print("   ✅ Columna 'agente_id' agregada a propiedades")
        else:
            print("   ✅ Columna 'agente_id' ya existe en propiedades")
        
        # Asignar todas las propiedades a Frankabb (agente_id = 1)
        cursor.execute("UPDATE propiedades SET agente_id = 1 WHERE agente_id IS NULL OR agente_id = 0")
        
        cursor.execute("SELECT COUNT(*) FROM propiedades WHERE agente_id = 1")
        props_asignadas = cursor.fetchone()[0]
        print(f"   ✅ {props_asignadas} propiedades asignadas a Frankabb (agente_id = 1)\n")
        
        # =====================================================
        # PASO 3: AGREGAR agente_id A noticias
        # =====================================================
        print("=" * 80)
        print("⚙️  PASO 3: Agregar agente_id a noticias")
        print("=" * 80 + "\n")
        
        if not column_exists(cursor, 'noticias', 'agente_id'):
            cursor.execute("ALTER TABLE noticias ADD COLUMN agente_id INTEGER DEFAULT 1")
            print("   ✅ Columna 'agente_id' agregada a noticias")
        else:
            print("   ✅ Columna 'agente_id' ya existe en noticias")
        
        cursor.execute("UPDATE noticias SET agente_id = 1 WHERE agente_id IS NULL OR agente_id = 0")
        
        cursor.execute("SELECT COUNT(*) FROM noticias WHERE agente_id = 1")
        noticias_asignadas = cursor.fetchone()[0]
        print(f"   ✅ {noticias_asignadas} noticias asignadas a Frankabb (agente_id = 1)\n")
        
        # =====================================================
        # PASO 4: CREAR TABLA publicaciones
        # =====================================================
        print("=" * 80)
        print("⚙️  PASO 4: Crear tabla publicaciones")
        print("=" * 80 + "\n")
        
        if not table_exists(cursor, 'publicaciones'):
            cursor.execute("""
                CREATE TABLE publicaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agente_id INTEGER NOT NULL,
                    propiedad_id INTEGER NOT NULL,
                    tipo TEXT,
                    imagen_url TEXT,
                    descripcion TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agente_id) REFERENCES agentes(id),
                    FOREIGN KEY (propiedad_id) REFERENCES propiedades(id)
                )
            """)
            print("   ✅ Tabla 'publicaciones' creada\n")
        else:
            print("   ✅ Tabla 'publicaciones' ya existe\n")
        
        # =====================================================
        # PASO 5: CREAR TABLA configuracion
        # =====================================================
        print("=" * 80)
        print("⚙️  PASO 5: Crear tabla configuracion")
        print("=" * 80 + "\n")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agente_id INTEGER UNIQUE NOT NULL,
                clave TEXT NOT NULL,
                valor TEXT,
                actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agente_id) REFERENCES agentes(id)
            )
        """)
        print("   ✅ Tabla 'configuracion' creada\n")
        
        # =====================================================
        # PASO 6: CREAR ÍNDICES
        # =====================================================
        print("=" * 80)
        print("⚙️  PASO 6: Crear índices para performance")
        print("=" * 80 + "\n")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_propiedades_agente_id ON propiedades(agente_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_noticias_agente_id ON noticias(agente_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_publicaciones_agente_id ON publicaciones(agente_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_publicaciones_propiedad_id ON publicaciones(propiedad_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agentes_slug ON agentes(slug)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agentes_usuario ON agentes(usuario)")
        
        print("   ✅ Índices creados\n")
        
        # =====================================================
        # COMMIT
        # =====================================================
        conn.commit()
        
        print("=" * 80)
        print("🎉 ✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 80 + "\n")
        
        # =====================================================
        # VERIFICACIÓN FINAL
        # =====================================================
        print("=" * 80)
        print("📊 VERIFICACIÓN FINAL")
        print("=" * 80 + "\n")
        
        # Agentes
        cursor.execute("SELECT id, usuario, slug, nombre_completo FROM agentes ORDER BY id")
        agentes = cursor.fetchall()
        
        print(f"✅ AGENTES ({len(agentes)}):")
        for agente in agentes:
            print(f"   [{agente[0]}] {agente[1]:<15} (slug: {agente[2]:<15}) - {agente[3]}")
        
        print()
        
        # Propiedades
        cursor.execute("SELECT COUNT(*) FROM propiedades WHERE agente_id = 1")
        props_frank = cursor.fetchone()[0]
        print(f"✅ PROPIEDADES: {props_count} total | {props_frank} asignadas a Frankabb")
        
        print()
        
        # Noticias
        cursor.execute("SELECT COUNT(*) FROM noticias WHERE agente_id = 1")
        noticias_frank = cursor.fetchone()[0]
        print(f"✅ NOTICIAS: {noticias_count} total | {noticias_frank} asignadas a Frankabb")
        
        print()
        
        # Publicaciones
        cursor.execute("SELECT COUNT(*) FROM publicaciones")
        pubs_count = cursor.fetchone()[0]
        print(f"✅ PUBLICACIONES: Tabla creada (vacía - {pubs_count} registros)")
        
        print()
        print("=" * 80)
        print("✅ ¡LISTO PARA FASE 2 - ACTUALIZAR CÓDIGO!")
        print("=" * 80)
        print()
        print("📝 PRÓXIMO PASO:")
        print("   1. Renombra: main.py → main_BACKUP.py")
        print("   2. Copia: 03_main_FASE2.py → main.py")
        print("   3. Renombra: db.py → db_BACKUP.py")
        print("   4. Copia: 04_db_MULTI_AGENTE.py → db.py")
        print("   5. Ejecuta: python main.py")
        print("   6. Prueba: http://localhost:8000/frankabb/generar")
        print()
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ ERROR EN LA BASE DE DATOS:")
        print(f"   {str(e)}\n")
        return False
    except Exception as e:
        print(f"\n❌ ERROR:")
        print(f"   {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = ejecutar_migracion()
    exit(0 if success else 1)
