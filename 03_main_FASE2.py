# =====================================================
# main.py - FASE 2: Multi-Agente (Non-Breaking)
# MiAgenteInmobiliario
# =====================================================
# Las rutas viejas siguen funcionando (/generar)
# Las rutas nuevas agregan multi-agente (/{agente_slug}/generar)
# =====================================================

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import aiofiles
import os
from dotenv import load_dotenv
import logging
import traceback
from datetime import datetime

# Importar módulos propios
from db import (
    init_db, 
    guardar_propiedad, 
    obtener_propiedades,
    obtener_propiedades_por_agente,
    obtener_agente_por_slug,
    guardar_publicacion,
    obtener_publicaciones_por_agente,
    guardar_configuracion,
    obtener_configuracion
)
from ai_service import generar_descripcion
from image_composer import (
    componer_portada,
    componer_stories,
    componer_overlay_extras,
    componer_collage
)
from branding import get_branding, hex_to_rgb

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Crear app
app = FastAPI(title="MiAgenteInmobiliario", version="2.0")

# Rutas estáticas y templates
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Inicializar BD
init_db()

# =====================================================
# RUTAS GLOBALES
# =====================================================

@app.get("/")
async def home(request: Request):
    """Home global - muestra landing o redirección"""
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "ok"}

# =====================================================
# RUTAS ANTIGUAS (COMPATIBILIDAD - Redirigen a multi-agente)
# =====================================================

@app.get("/generar")
async def generar_redirect(request: Request):
    """Redirige a la ruta multi-agente de Francisco"""
    return RedirectResponse(url="/francisco-a-barreto/generar")

@app.post("/generar")
async def generar_post_redirect(
    request: Request,
    tipo_propiedad: str = Form(...),
    operacion: str = Form(...),
    direccion: str = Form(...),
    ciudad_estado: str = Form(...),
    precio: str = Form(...),
    habitaciones: str = Form(...),
    banos: str = Form(...),
    metros_construidos: str = Form(...),
    estacionamientos: str = Form(...),
    nombre_agente: str = Form(...),
    telefono_agente: str = Form(...),
    foto_principal: UploadFile = File(...),
    fotos_adicionales: list = File(None)
):
    """Redirige al endpoint multi-agente"""
    return RedirectResponse(url="/francisco-a-barreto/generar", status_code=307)

@app.get("/historial")
async def historial_redirect():
    """Redirige al historial multi-agente"""
    return RedirectResponse(url="/francisco-a-barreto/historial")

@app.get("/configuracion")
async def configuracion_redirect():
    """Redirige a configuración multi-agente"""
    return RedirectResponse(url="/francisco-a-barreto/configuracion")

# =====================================================
# RUTAS MULTI-AGENTE (NUEVAS)
# =====================================================

@app.get("/{agente_slug}/generar", response_class=HTMLResponse)
async def generar_form(request: Request, agente_slug: str):
    """Formulario para generar contenido - Multi-agente"""
    try:
        agente = obtener_agente_por_slug(agente_slug)
        if not agente:
            return HTMLResponse("<h1>Agente no encontrado</h1>", status_code=404)
        
        branding = {
            "nombre_agencia": agente['nombre'],
            "logo": agente['logo_url'],
            "color_primario": agente['color_primario'],
            "color_secundario": agente['color_secundario'],
        }
        
        return templates.TemplateResponse(
            "form.html", 
            {
                "request": request,
                "branding": branding,
                "agente_slug": agente_slug,
                "agente": agente
            }
        )
    except Exception as e:
        logger.error(f"Error en {agente_slug}/generar: {str(e)}")
        return HTMLResponse(f"<h1>Error: {str(e)}</h1>", status_code=500)

@app.post("/{agente_slug}/generar")
async def generar_contenido(
    request: Request,
    agente_slug: str,
    tipo_propiedad: str = Form(...),
    operacion: str = Form(...),
    direccion: str = Form(...),
    ciudad_estado: str = Form(...),
    precio: str = Form(...),
    habitaciones: str = Form(...),
    banos: str = Form(...),
    metros_construidos: str = Form(...),
    estacionamientos: str = Form(None),
    nombre_agente: str = Form(...),
    telefono_agente: str = Form(...),
    foto_principal: UploadFile = File(...),
    fotos_adicionales: list = File(None)
):
    """Procesa y genera contenido - Multi-agente"""
    try:
        # Validar agente
        agente = obtener_agente_por_slug(agente_slug)
        if not agente:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        
        agente_id = agente['id']
        
        # Procesar imagen principal
        foto_principal_path = f"static/uploads/{foto_principal.filename}"
        async with aiofiles.open(foto_principal_path, 'wb') as f:
            content = await foto_principal.read()
            await f.write(content)
        
        # Procesar fotos adicionales
        fotos_adicionales_paths = []
        if fotos_adicionales:
            for foto in fotos_adicionales:
                foto_path = f"static/uploads/{foto.filename}"
                async with aiofiles.open(foto_path, 'wb') as f:
                    content = await foto.read()
                    await f.write(content)
                fotos_adicionales_paths.append(foto_path)
        
        # Preparar datos
        datos = {
            "tipo_propiedad": tipo_propiedad,
            "operacion": operacion,
            "direccion": direccion,
            "ciudad_estado": ciudad_estado,
            "precio": precio,
            "habitaciones": habitaciones,
            "banos": banos,
            "metros_construidos": metros_construidos,
            "estacionamientos": estacionamientos,
            "nombre_agente": nombre_agente,
            "telefono_agente": telefono_agente,
        }
        
        # Generar branding desde agente
        branding = {
            "nombre_agencia": agente['nombre'],
            "plantilla": "clasica",
            "color_primario": agente['color_primario'],
            "color_secundario": agente['color_secundario'],
        }
        
        # Generar contenido IA
        descripcion = await generar_descripcion(datos)
        datos["descripcion"] = descripcion
        
        # Guardar propiedad en BD
        propiedad_id = guardar_propiedad(datos, agente_id=agente_id)
        
        # Generar imágenes
        portada_url = componer_portada(foto_principal_path, datos)
        stories_url = componer_stories(foto_principal_path, datos)
        extras_urls = componer_overlay_extras(fotos_adicionales_paths, datos)
        collage_url = componer_collage(foto_principal_path, fotos_adicionales_paths, datos)
        
        # Guardar publicaciones
        guardar_publicacion(
            propiedad_id,
            portada_url,
            agente_id=agente_id
        )
        guardar_publicacion(
            propiedad_id,
            stories_url,
            agente_id=agente_id
        )
        if collage_url:
            guardar_publicacion(
                propiedad_id,
                collage_url,
                agente_id=agente_id
            )
        
        # Retornar resultado
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "datos": datos,
                "portada": portada_url,
                "stories": stories_url,
                "collage": collage_url,
                "extras": extras_urls,
                "agente_slug": agente_slug,
            }
        )
    
    except Exception as e:
        logger.error(f"Error generando contenido para {agente_slug}: {traceback.format_exc()}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": str(e),
                "agente_slug": agente_slug,
            },
            status_code=500
        )

@app.get("/{agente_slug}/historial", response_class=HTMLResponse)
async def historial(request: Request, agente_slug: str):
    """Historial de publicaciones - Multi-agente"""
    try:
        agente = obtener_agente_por_slug(agente_slug)
        if not agente:
            return HTMLResponse("<h1>Agente no encontrado</h1>", status_code=404)
        
        propiedades = obtener_propiedades_por_agente(agente['id'])
        publicaciones = obtener_publicaciones_por_agente(agente['id'])
        
        branding = {
            "nombre_agencia": agente['nombre'],
            "color_primario": agente['color_primario'],
            "color_secundario": agente['color_secundario'],
        }
        
        return templates.TemplateResponse(
            "historial.html",
            {
                "request": request,
                "propiedades": propiedades,
                "publicaciones": publicaciones,
                "branding": branding,
                "agente_slug": agente_slug,
                "agente": agente
            }
        )
    except Exception as e:
        logger.error(f"Error en historial de {agente_slug}: {str(e)}")
        return HTMLResponse(f"<h1>Error: {str(e)}</h1>", status_code=500)

@app.get("/{agente_slug}/configuracion", response_class=HTMLResponse)
async def configuracion(request: Request, agente_slug: str):
    """Configuración del agente - Multi-agente"""
    try:
        agente = obtener_agente_por_slug(agente_slug)
        if not agente:
            return HTMLResponse("<h1>Agente no encontrado</h1>", status_code=404)
        
        config = obtener_configuracion(agente['id'])
        
        branding = {
            "nombre_agencia": agente['nombre'],
            "color_primario": agente['color_primario'],
            "color_secundario": agente['color_secundario'],
        }
        
        return templates.TemplateResponse(
            "configuracion.html",
            {
                "request": request,
                "agente": agente,
                "config": config,
                "branding": branding,
                "agente_slug": agente_slug,
            }
        )
    except Exception as e:
        logger.error(f"Error en configuración de {agente_slug}: {str(e)}")
        return HTMLResponse(f"<h1>Error: {str(e)}</h1>", status_code=500)

@app.post("/{agente_slug}/configuracion")
async def guardar_configuracion_agente(
    agente_slug: str,
    nombre_agencia: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(...),
    color_primario: str = Form(...)
):
    """Guardar configuración del agente"""
    try:
        agente = obtener_agente_por_slug(agente_slug)
        if not agente:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
        
        guardar_configuracion(
            agente['id'],
            {
                "nombre_agencia": nombre_agencia,
                "email": email,
                "telefono": telefono,
                "color_primario": color_primario,
            }
        )
        
        return RedirectResponse(url=f"/{agente_slug}/configuracion?guardado=1")
    
    except Exception as e:
        logger.error(f"Error guardando configuración: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# INICIAR APP
# =====================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
