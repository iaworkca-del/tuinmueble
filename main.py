import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from ai_service import generar_contenido
from image_composer import (
    componer_portada,
    componer_stories,
    componer_overlay_extras,
    componer_collage,
)
from pdf_service import generar_pdf
from instagram_service import publicar_instagram
from branding import get_branding, guardar_branding, logo_existe, LOGO_PATH
from db import init_db, guardar_propiedad, listar_propiedades, obtener_propiedad

load_dotenv()

app = FastAPI(title="Mi Propiedad")
init_db()

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _descarga(static_url: str) -> str:
    """Convierte /static/uploads/x.jpg en /descargar/x.jpg."""
    return f"/descargar/{static_url.split('/')[-1]}"


@app.get("/generar")
async def generar_redirect():
    return RedirectResponse(url="/")


@app.get("/descargar/{filename}")
async def descargar(filename: str):
    file_path = UPLOAD_DIR / filename
    media = "application/pdf" if filename.lower().endswith(".pdf") else "image/jpeg"
    return FileResponse(
        path=str(file_path),
        media_type=media,
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/publicar-instagram")
async def publicar_instagram_endpoint(
    imagenes: List[str] = Form(...),
    titulo: str = Form(""),
):
    rutas = []
    for nombre in imagenes:
        fp = UPLOAD_DIR / Path(nombre).name  # evitar path traversal
        if fp.exists():
            rutas.append(str(fp))
    if not rutas:
        return JSONResponse(
            {"success": False, "message": "No se encontraron imágenes para publicar."},
            status_code=400,
        )
    resultado = publicar_instagram(rutas, titulo)
    status = 200 if resultado.get("success") else 502
    return JSONResponse(resultado, status_code=status)


@app.get("/configuracion", response_class=HTMLResponse)
async def configuracion(request: Request, guardado: int = 0):
    return templates.TemplateResponse(
        request=request,
        name="configuracion.html",
        context={
            "branding": get_branding(),
            "logo_existe": logo_existe(),
            "guardado": bool(guardado),
            "cache_bust": uuid.uuid4().hex[:8],
        },
    )


@app.post("/configuracion")
async def guardar_configuracion(
    nombre_agencia: str = Form(...),
    color_primario: str = Form("#1a3a5c"),
    color_secundario: str = Form("#c8a45a"),
    nombre_agente: str = Form(""),
    telefono_agente: str = Form(""),
    email_agente: str = Form(""),
    logo: UploadFile = File(None),
):
    guardar_branding({
        "nombre_agencia": nombre_agencia,
        "color_primario": color_primario,
        "color_secundario": color_secundario,
        "nombre_agente": nombre_agente,
        "telefono_agente": telefono_agente,
        "email_agente": email_agente,
    })
    if logo and logo.filename:
        with LOGO_PATH.open("wb") as f:
            shutil.copyfileobj(logo.file, f)
    return RedirectResponse(url="/configuracion?guardado=1", status_code=303)


@app.get("/historial", response_class=HTMLResponse)
async def historial(request: Request, busqueda: str = ""):
    propiedades = listar_propiedades(busqueda.strip() or None)
    return templates.TemplateResponse(
        request=request,
        name="historial.html",
        context={
            "branding": get_branding(),
            "propiedades": propiedades,
            "busqueda": busqueda,
        },
    )


@app.get("/historial/{prop_id}", response_class=HTMLResponse)
async def historial_detalle(request: Request, prop_id: int):
    payload = obtener_propiedad(prop_id)
    if not payload:
        return RedirectResponse(url="/historial")
    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={"branding": get_branding(), "prop_id": prop_id, **payload},
    )


@app.get("/", response_class=HTMLResponse)
async def formulario(request: Request):
    branding = get_branding()
    return templates.TemplateResponse(
        request=request,
        name="form.html",
        context={"branding": branding},
    )


@app.post("/generar", response_class=HTMLResponse)
async def generar(
    request: Request,
    tipo_propiedad: str = Form(...),
    operacion: str = Form(...),
    direccion: str = Form(...),
    pais: str = Form("Venezuela"),
    estado: str = Form(""),
    municipio: str = Form(""),
    precio: float = Form(...),
    habitaciones: Optional[int] = Form(None),
    banos: Optional[int] = Form(None),
    metros_construidos: Optional[float] = Form(None),
    metros_terreno: Optional[float] = Form(None),
    estacionamientos: Optional[int] = Form(None),
    espacios: List[str] = Form(default=[]),
    descripcion_agente: str = Form(""),
    tono: str = Form("Cercano"),
    longitud: str = Form("Media"),
    nombre_agente: str = Form(...),
    telefono_agente: str = Form(...),
    email_agente: str = Form(""),
    foto_portada: UploadFile = File(...),
    fotos_extra: List[UploadFile] = File(default=[]),
):
    # Componer "ciudad_estado" desde municipio + estado (lo usan imagen, PDF y prompt de IA)
    ciudad_estado = ", ".join([p for p in [municipio, estado] if p]) or pais

    datos = {
        "tipo_propiedad": tipo_propiedad,
        "operacion": operacion,
        "direccion": direccion,
        "pais": pais,
        "estado": estado,
        "municipio": municipio,
        "ciudad_estado": ciudad_estado,
        "precio": precio,
        "habitaciones": habitaciones,
        "banos": banos,
        "metros_construidos": metros_construidos,
        "metros_terreno": metros_terreno,
        "estacionamientos": estacionamientos,
        "espacios": espacios,
        "descripcion_agente": descripcion_agente,
        "nombre_agente": nombre_agente,
        "telefono_agente": telefono_agente,
        "email_agente": email_agente,
    }

    portada_url = None
    portada_compuesta_url = None
    portada_descarga_url = None
    stories_url = None
    stories_descarga_url = None
    portada_path = None
    if foto_portada and foto_portada.filename:
        ext = Path(foto_portada.filename).suffix
        nombre = f"{uuid.uuid4().hex}{ext}"
        destino = UPLOAD_DIR / nombre
        with destino.open("wb") as f:
            shutil.copyfileobj(foto_portada.file, f)
        portada_path = str(destino)
        portada_url = f"/static/uploads/{nombre}"
        portada_compuesta_url = componer_portada(str(destino), datos)
        portada_descarga_url = _descarga(portada_compuesta_url)
        stories_url = componer_stories(str(destino), datos)
        stories_descarga_url = _descarga(stories_url)

    extras_urls = []
    extras_paths = []
    for foto in fotos_extra:
        if foto and foto.filename:
            ext = Path(foto.filename).suffix
            nombre = f"{uuid.uuid4().hex}{ext}"
            destino = UPLOAD_DIR / nombre
            with destino.open("wb") as f:
                shutil.copyfileobj(foto.file, f)
            extras_urls.append(f"/static/uploads/{nombre}")
            extras_paths.append(str(destino))

    # Variantes de imagen: overlay en cada extra + collage
    extras_overlay = [
        {"url": u, "descarga": _descarga(u)}
        for u in componer_overlay_extras(extras_paths, datos)
    ]
    collage_url = None
    collage_descarga_url = None
    if portada_path:
        collage_url = componer_collage(portada_path, extras_paths, datos)
        if collage_url:
            collage_descarga_url = _descarga(collage_url)

    contenido = generar_contenido(datos, tono=tono, longitud=longitud)

    # PDF descargable con toda la ficha de la propiedad
    pdf_descarga_url = generar_pdf(
        datos, contenido["descripcion"], portada_path, extras_paths
    )

    payload = {
        "portada_url": portada_url,
        "portada_compuesta_url": portada_compuesta_url,
        "portada_descarga_url": portada_descarga_url,
        "stories_url": stories_url,
        "stories_descarga_url": stories_descarga_url,
        "collage_url": collage_url,
        "collage_descarga_url": collage_descarga_url,
        "extras_overlay": extras_overlay,
        "pdf_descarga_url": pdf_descarga_url,
        "extras_urls": extras_urls,
        "descripcion": contenido["descripcion"],
        "instagram": contenido["instagram"],
        "whatsapp": contenido.get("whatsapp", ""),
        "facebook": contenido.get("facebook", ""),
        "datos": datos,
    }

    # Guardar en el historial
    prop_id = guardar_propiedad(payload)

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={"branding": get_branding(), "prop_id": prop_id, **payload},
    )
