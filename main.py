import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
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
from branding import get_branding, guardar_branding, logo_existe, fondo_existe, LOGO_PATH, FONDO_PATH
from db import (
    init_db,
    guardar_propiedad,
    listar_propiedades,
    listar_propiedades_publicadas,
    listar_propiedades_top,
    obtener_propiedad,
    obtener_propiedad_publicada,
    set_publicado,
    listar_agentes,
    crear_agente,
    obtener_agente_por_usuario,
    set_agente_activo,
    eliminar_agente,
    listar_noticias,
    obtener_noticia,
)
from noticias_scheduler import iniciar_scheduler_noticias
from gemini_service import generar_noticia_diaria
from db import guardar_noticia
from auth import (
    seed_admin,
    hash_password,
    verificar_password,
    obtener_usuario_actual,
    iniciar_sesion,
    cerrar_sesion,
)

load_dotenv()

app = FastAPI(title="Mi Propiedad")
init_db()
seed_admin()
# Job diario: genera texto (Gemini) + imagen (Nano Banana) para la sección
# "Tips y Noticias Inmobiliarias" y lo guarda en la base de datos (db.noticias).
iniciar_scheduler_noticias()

SESSION_SECRET = os.environ.get("SESSION_SECRET_KEY", "clave-temporal-cambiar")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, session_cookie="mp_session")

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _descarga(static_url: str) -> str:
    """Convierte /static/uploads/x.jpg en /descargar/x.jpg."""
    return f"/descargar/{static_url.split('/')[-1]}"


# ──────────────────────────────────────────────────────────────
# Sitio público
# ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def inicio_publico(request: Request):
    propiedades = listar_propiedades_publicadas(limite=6)
    noticias = listar_noticias(limite=6)
    return templates.TemplateResponse(
        request=request,
        name="public/index.html",
        context={
            "branding": get_branding(),
            "propiedades": propiedades,
            "noticias": noticias,
            "anio": datetime.now().year,
        },
    )


@app.get("/servicios", response_class=HTMLResponse)
async def servicios_publico(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="public/servicios.html",
        context={
            "branding": get_branding(),
            "anio": datetime.now().year,
            "propiedades_top": listar_propiedades_top(10),
        },
    )


@app.get("/catalogo", response_class=HTMLResponse)
async def catalogo_publico(request: Request):
    propiedades = listar_propiedades_publicadas()
    return templates.TemplateResponse(
        request=request,
        name="public/catalogo.html",
        context={
            "branding": get_branding(),
            "propiedades": propiedades,
            "anio": datetime.now().year,
        },
    )


@app.get("/catalogo/{prop_id}", response_class=HTMLResponse)
async def catalogo_detalle_publico(request: Request, prop_id: int):
    payload = obtener_propiedad_publicada(prop_id)
    if not payload:
        return RedirectResponse(url="/catalogo")
    return templates.TemplateResponse(
        request=request,
        name="public/propiedad_detalle.html",
        context={"branding": get_branding(), "anio": datetime.now().year, **payload},
    )


@app.get("/noticias/{noticia_id}", response_class=HTMLResponse)
async def noticia_detalle_publico(request: Request, noticia_id: int):
    noticia = obtener_noticia(noticia_id)
    if not noticia:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(
        request=request,
        name="public/noticia_detalle.html",
        context={
            "branding": get_branding(),
            "anio": datetime.now().year,
            "noticia": noticia,
        },
    )


# ──────────────────────────────────────────────────────────────
# Autenticación
# ──────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, siguiente: str = "/panel"):
    if obtener_usuario_actual(request):
        return RedirectResponse(url=siguiente or "/panel", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"branding": get_branding(), "error": None, "siguiente": siguiente},
    )


@app.post("/login")
async def login_submit(
    request: Request,
    usuario: str = Form(...),
    password: str = Form(...),
    siguiente: str = Form("/panel"),
):
    agente = obtener_agente_por_usuario(usuario.strip())
    if not agente or not agente.get("activo") or not verificar_password(password, agente["password_hash"]):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "branding": get_branding(),
                "error": "Usuario o contraseña incorrectos, o cuenta inactiva.",
                "siguiente": siguiente,
            },
            status_code=401,
        )
    iniciar_sesion(request, agente)
    return RedirectResponse(url=siguiente or "/panel", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    cerrar_sesion(request)
    return RedirectResponse(url="/login", status_code=303)


# ──────────────────────────────────────────────────────────────
# Gestión de agentes (solo administradores)
# ──────────────────────────────────────────────────────────────

@app.get("/panel/agentes", response_class=HTMLResponse)
async def panel_agentes(request: Request, mensaje: str = "", error: str = ""):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url=f"/login?siguiente=/panel/agentes", status_code=303)
    if not agente.get("es_admin"):
        return RedirectResponse(url="/panel", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="panel_agentes.html",
        context={
            "branding": get_branding(),
            "agentes": listar_agentes(),
            "agente_actual_id": agente["id"],
            "mensaje": mensaje,
            "error": error,
        },
    )


@app.post("/panel/agentes")
async def crear_agente_endpoint(
    request: Request,
    usuario: str = Form(...),
    nombre_completo: str = Form(""),
    password: str = Form(...),
    es_admin: str = Form(None),
):
    agente = obtener_usuario_actual(request)
    if not agente or not agente.get("es_admin"):
        return RedirectResponse(url="/panel", status_code=303)
    if obtener_agente_por_usuario(usuario.strip()):
        return RedirectResponse(url="/panel/agentes?error=Ese usuario ya existe.", status_code=303)
    crear_agente(
        usuario=usuario.strip(),
        password_hash=hash_password(password),
        nombre_completo=nombre_completo,
        es_admin=bool(es_admin),
    )
    return RedirectResponse(url="/panel/agentes?mensaje=Agente creado correctamente.", status_code=303)


@app.post("/panel/agentes/{agente_id}/estado")
async def cambiar_estado_agente(request: Request, agente_id: int, activo: int = Form(...)):
    agente = obtener_usuario_actual(request)
    if not agente or not agente.get("es_admin"):
        return RedirectResponse(url="/panel", status_code=303)
    if agente_id == agente["id"]:
        return RedirectResponse(url="/panel/agentes?error=No puedes desactivar tu propia cuenta.", status_code=303)
    set_agente_activo(agente_id, bool(activo))
    return RedirectResponse(url="/panel/agentes?mensaje=Estado actualizado.", status_code=303)


@app.post("/panel/agentes/{agente_id}/eliminar")
async def eliminar_agente_endpoint(request: Request, agente_id: int):
    agente = obtener_usuario_actual(request)
    if not agente or not agente.get("es_admin"):
        return RedirectResponse(url="/panel", status_code=303)
    if agente_id == agente["id"]:
        return RedirectResponse(url="/panel/agentes?error=No puedes eliminar tu propia cuenta.", status_code=303)
    eliminar_agente(agente_id)
    return RedirectResponse(url="/panel/agentes?mensaje=Agente eliminado.", status_code=303)


# ──────────────────────────────────────────────────────────────
# Panel privado (requiere sesión de agente)
# ──────────────────────────────────────────────────────────────

@app.get("/panel", response_class=HTMLResponse)
async def formulario(request: Request):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/panel", status_code=303)
    branding = get_branding()
    return templates.TemplateResponse(
        request=request,
        name="form.html",
        context={"branding": branding, "agente": agente},
    )


@app.get("/generar")
async def generar_redirect():
    return RedirectResponse(url="/panel")


@app.post("/panel/generar-noticia")
async def generar_noticia_manual(request: Request):
    """Permite a un administrador disparar manualmente la generación de la
    noticia/tip del día (texto con Gemini + imagen con Nano Banana), útil para
    probar la integración sin esperar al job automático de medianoche."""
    agente = obtener_usuario_actual(request)
    if not agente or not agente.get("es_admin"):
        return RedirectResponse(url="/panel", status_code=303)
    try:
        payload = generar_noticia_diaria()
        guardar_noticia(payload)
        return RedirectResponse(url="/?noticia_generada=1", status_code=303)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return RedirectResponse(url=f"/panel?error_noticia={str(e)[:200]}", status_code=303)


@app.get("/descargar/{filename}")
async def descargar(request: Request, filename: str):
    if not obtener_usuario_actual(request):
        return RedirectResponse(url="/login", status_code=303)
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
    request: Request,
    imagenes: List[str] = Form(...),
    titulo: str = Form(""),
):
    if not obtener_usuario_actual(request):
        return JSONResponse({"success": False, "message": "Sesión requerida."}, status_code=401)
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
    if not obtener_usuario_actual(request):
        return RedirectResponse(url="/login?siguiente=/configuracion", status_code=303)
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
    request: Request,
    nombre_agencia: str = Form(...),
    color_primario: str = Form("#1a3a5c"),
    color_secundario: str = Form("#c8a45a"),
    nombre_agente: str = Form(""),
    telefono_agente: str = Form(""),
    email_agente: str = Form(""),
    fondo_opacidad: str = Form("30"),
    plantilla: str = Form("clasica"),
    eslogan: str = Form(""),
    descripcion_agencia: str = Form(""),
    servicio_1_titulo: str = Form(""),
    servicio_1_desc: str = Form(""),
    servicio_2_titulo: str = Form(""),
    servicio_2_desc: str = Form(""),
    servicio_3_titulo: str = Form(""),
    servicio_3_desc: str = Form(""),
    logo: UploadFile = File(None),
    fondo: UploadFile = File(None),
):
    if not obtener_usuario_actual(request):
        return RedirectResponse(url="/login?siguiente=/configuracion", status_code=303)
    guardar_branding({
        "nombre_agencia": nombre_agencia,
        "color_primario": color_primario,
        "color_secundario": color_secundario,
        "nombre_agente": nombre_agente,
        "telefono_agente": telefono_agente,
        "email_agente": email_agente,
        "fondo_opacidad": fondo_opacidad,
        "plantilla": plantilla,
        "eslogan": eslogan,
        "descripcion_agencia": descripcion_agencia,
        "servicio_1_titulo": servicio_1_titulo,
        "servicio_1_desc": servicio_1_desc,
        "servicio_2_titulo": servicio_2_titulo,
        "servicio_2_desc": servicio_2_desc,
        "servicio_3_titulo": servicio_3_titulo,
        "servicio_3_desc": servicio_3_desc,
    })
    if logo and logo.filename:
        with LOGO_PATH.open("wb") as f:
            shutil.copyfileobj(logo.file, f)
    if fondo and fondo.filename:
        # Convertir a JPEG para un fondo consistente
        try:
            from PIL import Image
            img = Image.open(fondo.file).convert("RGB")
            img.save(str(FONDO_PATH), "JPEG", quality=85)
        except Exception:
            with FONDO_PATH.open("wb") as f:
                fondo.file.seek(0)
                shutil.copyfileobj(fondo.file, f)
    return RedirectResponse(url="/configuracion?guardado=1", status_code=303)


@app.get("/historial", response_class=HTMLResponse)
async def historial(request: Request, busqueda: str = ""):
    if not obtener_usuario_actual(request):
        return RedirectResponse(url="/login?siguiente=/historial", status_code=303)
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


@app.post("/historial/{prop_id}/publicar")
async def alternar_publicacion(request: Request, prop_id: int, publicado: int = Form(...)):
    if not obtener_usuario_actual(request):
        return RedirectResponse(url="/login?siguiente=/historial", status_code=303)
    set_publicado(prop_id, bool(publicado))
    return RedirectResponse(url="/historial", status_code=303)


@app.get("/historial/{prop_id}", response_class=HTMLResponse)
async def historial_detalle(request: Request, prop_id: int):
    if not obtener_usuario_actual(request):
        return RedirectResponse(url="/login?siguiente=/historial", status_code=303)
    payload = obtener_propiedad(prop_id)
    if not payload:
        return RedirectResponse(url="/historial")
    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={"branding": get_branding(), "prop_id": prop_id, **payload},
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
    if not obtener_usuario_actual(request):
        return RedirectResponse(url="/login?siguiente=/panel", status_code=303)

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

    try:
        contenido = generar_contenido(datos, tono=tono, longitud=longitud)
        # PDF descargable con toda la ficha de la propiedad
        pdf_descarga_url = generar_pdf(
            datos, contenido["descripcion"], portada_path, extras_paths
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"branding": get_branding(), "mensaje": str(e)},
            status_code=503,
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
