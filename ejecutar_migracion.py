#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT DE MIGRACIÓN MULTI-AGENTE
MiAgenteInmobiliario - IA Real State

Ejecuta automáticamente todas las queries SQL de migración
"""

import sqlite3
import os
from pathlib import Path

def ejecutar_migracion():
    """Ejecuta la migración a multi-agente"""
    
    # Ruta de la BD
    db_path = Path('data/propiedades.db')
    
    if not db_path.exists():
        print(f"❌ ERROR: No encontré la BD en {db_path}")
        print(f"   Estoy buscando en: {Path.cwd()}")
        return False
    
    print(f"📊 Base de datos encontrada: {db_path}")
    print("🔄 Iniciando migración...\n")
    
    try:
        # Conectar a la BD
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("✅ Conexión exitosa a la base de datos\n")
        
        # Leer el script SQL
        script_path = Path('02_MIGRACION_SCRIPT.sql')
        
        if not script_path.exists():
            print(f"❌ ERROR: No encontré {script_path}")
            print(f"   Descargalo de /outputs y colócalo en esta carpeta")
            return False
        
        print(f"📄 Leyendo script: {script_path}\n")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Ejecutar el script
        print("⚙️  Ejecutando queries SQL...\n")
        cursor.executescript(sql)
        conn.commit()
        
        print("\n✅ MIGRACIÓN COMPLETADA EXITOSAMENTE\n")
        
        # Verificación
        print("=" * 60)
        print("📋 VERIFICACIÓN")
        print("=" * 60 + "\n")
        
        # Verificar tabla agentes
        cursor.execute("SELECT COUNT(*) FROM agentes")
        agentes_count = cursor.fetchone()[0]
        print(f"✅ Tabla 'agentes': {agentes_count} agente(s)")
        
        cursor.execute("SELECT * FROM agentes")
        agentes = cursor.fetchall()
        for agente in agentes:
            print(f"   - {agente[1]} (slug: {agente[2]})")
        
        print()
        
        # Verificar propiedades con agente_id
        cursor.execute("SELECT COUNT(*) FROM propiedades WHERE agente_id IS NOT NULL")
        props_count = cursor.fetchone()[0]
        print(f"✅ Propiedades asignadas: {props_count}")
        
        cursor.execute("SELECT agente_id, COUNT(*) FROM propiedades GROUP BY agente_id")
        props_by_agent = cursor.fetchall()
        for agent_id, count in props_by_agent:
            print(f"   - Agente {agent_id}: {count} propiedades")
        
        print()
        
        # Verificar publicaciones con agente_id
        cursor.execute("SELECT COUNT(*) FROM publicaciones WHERE agente_id IS NOT NULL")
        pubs_count = cursor.fetchone()[0]
        print(f"✅ Publicaciones asignadas: {pubs_count}")
        
        cursor.execute("SELECT agente_id, COUNT(*) FROM publicaciones GROUP BY agente_id")
        pubs_by_agent = cursor.fetchall()
        for agent_id, count in pubs_by_agent:
            print(f"   - Agente {agent_id}: {count} publicaciones")
        
        print()
        print("=" * 60)
        print("🎉 ¡LISTO PARA CONTINUAR CON LA FASE 2!")
        print("=" * 60)
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ ERROR EN LA BASE DE DATOS:")
        print(f"   {str(e)}\n")
        return False
    except Exception as e:
        print(f"\n❌ ERROR:")
        print(f"   {str(e)}\n")
        return False

if __name__ == "__main__":
    success = ejecutar_migracion()
    exit(0 if success else 1)
