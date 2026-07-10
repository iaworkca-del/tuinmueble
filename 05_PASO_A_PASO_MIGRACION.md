# 📋 PASO A PASO - Migración Multi-Agente
## MiAgenteInmobiliario - Rutas CORRECTAS

## ⚠️ ANTES DE EMPEZAR

### RUTAS CRÍTICAS
```
Tu proyecto: C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente\
Git repo:    C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente\
```

### 1. Backup Total
```powershell
# Abre PowerShell en la carpeta del proyecto
cd C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente

# Guarda tu DB en lugar seguro
Copy-Item "data\propiedades.db" -Destination "data\propiedades.db.BACKUP"

# Haz commit de seguridad
git add data/propiedades.db.BACKUP
git commit -m "BACKUP: Pre-migracion multi-agente"
git push origin main
```

### 2. Descargar archivos de migración
Descarga estos 4 archivos de `/outputs` y guarda en esta carpeta:
```
C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente\
  ├── 02_MIGRACION_SCRIPT.sql      ← Queries SQL
  ├── 03_main_FASE2.py              ← Nuevo main.py
  ├── 04_db_MULTI_AGENTE.py         ← Nuevo db.py
  └── 05_PASO_A_PASO_MIGRACION.md   ← Este archivo
```

---

## 🚀 FASE 1: PREPARACIÓN DE BASE DE DATOS (1-2 horas)

### Paso 1.1: Ejecutar migraciones en LOCAL

**En tu computadora (NO en Railway aún):**

```powershell
# Asegúrate de estar en la carpeta correcta
cd C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente

# Verifica que ves estos archivos
ls data\propiedades.db
ls 02_MIGRACION_SCRIPT.sql

# 1. Opción A: Usar DB Browser (visual)
#    - Descarga: https://sqlitebrowser.org/
#    - Abre: data\propiedades.db
#    - File → Open Database
#    - Execute SQL (pestaña)
#    - Copia TODO el contenido de: 02_MIGRACION_SCRIPT.sql
#    - Pega en el editor SQL
#    - Click "Execute SQL" (Ctrl+Enter)

# 2. Opción B: Usar PowerShell
#    - Si tienes sqlite3 instalado:
sqlite3 data\propiedades.db < 02_MIGRACION_SCRIPT.sql

#    - Si NO tienes sqlite3:
#      Instala: choco install sqlite
#      O descarga: https://www.sqlite.org/download.html
```

### Paso 1.2: Verificar que funcionó

```powershell
# Abre PowerShell en tu carpeta
cd C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente

# Abrir SQLite
sqlite3 data\propiedades.db

# Ejecutar queries de verificación:
SELECT * FROM agentes;
# Debe mostrar: 1 | Francisco A Barreto | francisco-a-barreto | ...

SELECT COUNT(*) FROM propiedades WHERE agente_id = 1;
# Debe mostrar: (número de propiedades existentes)

SELECT COUNT(*) FROM publicaciones WHERE agente_id = 1;
# Debe mostrar: (número de publicaciones existentes)

# Si tienes tabla agentes, BIEN ✅
# Salir
.quit
```

### Paso 1.3: Probar en LOCAL

```powershell
# Asegúrate de estar en la carpeta del proyecto
cd C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente

# Inicia la app
python main.py

# Ve a: http://localhost:8000/generar
# Debe verse igual que siempre
```

### ✅ CHECKPOINT 1

Si todo funciona en LOCAL, haz commit:

```powershell
# Asegúrate de estar en la carpeta Git
cd C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente

# Verificar status
git status
# Debe mostrar: data/propiedades.db como modificado

# Commit y push
git add data/propiedades.db
git commit -m "FASE 1: Migración BD - Crear tabla agentes y agente_id"
git push origin main

# Railway redeploy automático (5 minutos)
```

**Verifica en Railway:**
- Ve a tu URL: https://tuinmueble-production-xxx.up.railway.app
- La app debe funcionar EXACTAMENTE igual que antes
- El historial debe mostrar tus propiedades
- Intenta generar una imagen → Debe funcionar igual

---

## 🔧 FASE 2: ACTUALIZAR CÓDIGO (2-3 horas)

### Paso 2.1: Reemplazar archivos Python

```powershell
# Asegúrate de estar en la carpeta del proyecto
cd C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente

# 1. Renombra los viejos como backup (CRÍTICO)
Rename-Item "db.py" -NewName "db_BACKUP.py"
Rename-Item "main.py" -NewName "main_BACKUP.py"

# 2. Copia los archivos nuevos
Copy-Item "03_main_FASE2.py" -Destination "main.py"
Copy-Item "04_db_MULTI_AGENTE.py" -Destination "db.py"

# 3. Verifica que estén
ls main.py
ls db.py
ls db_BACKUP.py
ls main_BACKUP.py
```

### Paso 2.2: Probar en LOCAL

```powershell
# Asegúrate de estar en la carpeta del proyecto
cd C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente

# Inicia la app con el código nuevo
python main.py

# En otro terminal o navegador, probar:

# ✅ Probar RUTAS VIEJAS (deben redirigir):
# GET http://localhost:8000/generar
#   → Debería redirigir a /francisco-a-barreto/generar

# ✅ Probar RUTAS NUEVAS (deben funcionar):
# GET http://localhost:8000/francisco-a-barreto/generar
#   → Debería mostrar el formulario igual que antes

# GET http://localhost:8000/francisco-a-barreto/historial
#   → Debería mostrar tus propiedades

# ✅ Generar contenido:
# POST http://localhost:8000/francisco-a-barreto/generar
#   → Debe funcionar igual que antes (llenar form y generar)
```

### ✅ CHECKPOINT 2

Si todo funciona en LOCAL:

```powershell
# Asegúrate de estar en la carpeta Git
cd C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente

# Verificar status
git status
# Debe mostrar: main.py y db.py como modificados

# Commit y push
git add main.py db.py
git commit -m "FASE 2: Agregar rutas multi-agente (non-breaking)"
git push origin main

# Railway redeploy automático (5 minutos)
```

**Verifica en Railway:**
✅ `/generar` redirige a `/francisco-a-barreto/generar`
✅ `/francisco-a-barreto/generar` muestra formulario
✅ Generar contenido funciona igual que antes
✅ `/historial` redirige a `/francisco-a-barreto/historial`
✅ Historial muestra tus propiedades

---

## 📱 FASE 3: PRUEBA DE COMPATIBILIDAD (30 min)

### Paso 3.1: Test de Compatibilidad

En Railway, prueba:

```
1. ✅ Ir a https://tuapp.com/generar
   → Debería redirigir a /francisco-a-barreto/generar
   
2. ✅ Ir a https://tuapp.com/francisco-a-barreto/generar
   → Debería mostrar formulario
   
3. ✅ Llenar y generar contenido
   → Debería crear imágenes igual que antes
   
4. ✅ Ir a https://tuapp.com/historial
   → Debería redirigir a /francisco-a-barreto/historial
   
5. ✅ Ver https://tuapp.com/francisco-a-barreto/historial
   → Debería mostrar tus propiedades
```

### ✅ CHECKPOINT 3

Si TODO funciona, continúa.

Si algo falla:

```powershell
# Rollback
git revert HEAD
git push origin main

# Restaurar archivos
mv main_BACKUP.py main.py
mv db_BACKUP.py db.py

# Contactarme con logs de Railway
```

---

## 👥 FASE 4: AGREGAR MÁS AGENTES (1 hora)

### Paso 4.1: Crear segundo agente (TESTING)

```powershell
# En PowerShell en tu carpeta del proyecto
cd C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente

# Abre SQLite
sqlite3 data\propiedades.db

# En el prompt de SQLite (>):
INSERT INTO agentes (nombre, slug, email, telefono, logo_url)
VALUES (
    'María García',
    'maria-garcia',
    'maria@example.com',
    '+58412345678',
    'static/logo.png'
);

# Verificar que se creó
SELECT * FROM agentes;

# Salir
.quit
```

### Paso 4.2: Verificar en Railway

```
✅ Ve a: https://tuinmueble-production-xxx.up.railway.app/maria-garcia/generar
   → Debe mostrar formulario

✅ Ve a: https://tuinmueble-production-xxx.up.railway.app/maria-garcia/historial
   → Debe mostrar (vacío, sin propiedades de María aún)
```

### Paso 4.3: Crear propiedades de prueba para María

1. Ve a: https://tuinmueble-production-xxx.up.railway.app/maria-garcia/generar
2. Llena el formulario y genera contenido
3. Verifica que aparece en `/maria-garcia/historial`
4. Verifica que NO aparece en `/francisco-a-barreto/historial`

**✅ Si esto funciona, la migración está COMPLETA** 🎉

---

## 🎛️ FASE 5: PANEL ADMIN (2-3 horas) - OPCIONAL

Si quieres administrar agentes desde la web:

### Crear endpoint admin (AVANZADO)

```python
# Agregar a main.py:

@app.get("/admin")
async def admin(request: Request):
    """Panel administrativo"""
    agentes = obtener_todos_agentes()
    return templates.TemplateResponse("admin/panel.html", {
        "request": request,
        "agentes": agentes
    })

@app.post("/admin/agentes/crear")
async def crear_agente_endpoint(
    nombre: str = Form(...),
    slug: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(...)
):
    """Crear nuevo agente"""
    try:
        agente = crear_agente(nombre, slug, email, telefono)
        return {"success": True, "agente": agente}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 📊 RESULTADO FINAL

Después de toda la migración:

```
ANTES:
✅ /generar → Formula de Francisco
✅ /historial → Propiedades de Francisco
✅ 1 solo agente

DESPUÉS:
✅ /generar → Redirige a /francisco-a-barreto/generar
✅ /francisco-a-barreto/generar → Formulario de Francisco
✅ /francisco-a-barreto/historial → Propiedades de Francisco
✅ /maria-garcia/generar → Formulario de María
✅ /maria-garcia/historial → Propiedades de María
✅ N agentes, cada uno con su URL
```

---

## 🆘 TROUBLESHOOTING

### Error: "Agente no encontrado"

```
Causa: El slug no existe en la BD
Solución: Insertar el agente en la BD
SQL: INSERT INTO agentes (nombre, slug, email, telefono) VALUES (...)
```

### Error: "Tabla agentes no existe"

```
Causa: El script SQL no se ejecutó correctamente
Solución: 
1. Descargar de nuevo: 02_MIGRACION_SCRIPT.sql
2. Ejecutar en SQLite nuevamente
3. Verificar que se creó la tabla
```

### Las imágenes se ven pequeñas/sin formato

```
Causa: image_composer.py no se actualizó
Solución:
1. Verificar que usas image_composer_FINAL_V2.py o DEFINITIVO.py
2. Hacer redeploy en Railway
3. Generar imagen nueva
```

### Las rutas viejas no redirigen

```
Causa: El código de main.py no está actualizado
Solución:
1. Verificar que reemplazaste main.py con 03_main_FASE2.py
2. Haz git push
3. Espera redeploy de Railway
```

---

## 📞 PRÓXIMOS PASOS

1. **Hacer Fase 1-2** (hoy)
2. **Testear Fase 3** (hoy)
3. **Agregar agentes REALES** (mañana)
4. **Panel admin** (opcional - más adelante)

---

## 💾 ARCHIVOS FINALES

Después de completar la migración, en tu carpeta tendrás:

```
C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente\
├── data\
│   ├── propiedades.db          ← Con tabla agentes (ACTUALIZADO)
│   └── propiedades.db.BACKUP   ← Backup pre-migración (KEEP)
├── main.py                      ← Con rutas multi-agente (ACTUALIZADO)
├── main_BACKUP.py               ← Viejo main (KEEP como backup)
├── db.py                        ← Con funciones multi-agente (ACTUALIZADO)
├── db_BACKUP.py                 ← Viejo db (KEEP como backup)
└── 02_MIGRACION_SCRIPT.sql      ← Script ejecutado (DELETE o KEEP)
```

---

## 🚀 **¿LISTO? COMIENZA AHORA - GUÍA RÁPIDA**

### ⏱️ SOLO 1-2 HORAS

```powershell
# Paso 1: Abre PowerShell aquí
cd C:\Users\nelly\Desktop\IAWORKING\MiAgenteInmobiliario_VRP1.0\MiAgente

# Paso 2: Backup (5 min)
Copy-Item "data\propiedades.db" -Destination "data\propiedades.db.BACKUP"
git add data/propiedades.db.BACKUP
git commit -m "BACKUP: Pre-migracion"
git push origin main

# Paso 3: Ejecutar SQL (15 min)
# Descarga 02_MIGRACION_SCRIPT.sql
# Abre SQLite Browser: data\propiedades.db
# Copia TODO el SQL y ejecuta
# O: sqlite3 data\propiedades.db < 02_MIGRACION_SCRIPT.sql

# Paso 4: Reemplazar archivos (5 min)
Rename-Item "db.py" -NewName "db_BACKUP.py"
Rename-Item "main.py" -NewName "main_BACKUP.py"
Copy-Item "03_main_FASE2.py" -Destination "main.py"
Copy-Item "04_db_MULTI_AGENTE.py" -Destination "db.py"

# Paso 5: Probar LOCAL (10 min)
python main.py
# Abre: http://localhost:8000/generar
# Abre: http://localhost:8000/francisco-a-barreto/generar

# Paso 6: Push a Railway (5 min)
git add main.py db.py
git commit -m "FASE 2: Agregar rutas multi-agente"
git push origin main

# Paso 7: Verificar en Railway (10 min)
# Espera redeploy
# Abre: https://tuinmueble-production-xxx.up.railway.app/generar
# Abre: https://tuinmueble-production-xxx.up.railway.app/francisco-a-barreto/generar
```

---

**Cuando termines todos los pasos, cuéntame en qué checkpoint estás.** 👇
