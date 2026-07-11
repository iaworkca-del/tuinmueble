import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

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
from branding import (
    get_branding, guardar_branding, logo_existe, fondo_existe,
    logo_path_para_guardar, fondo_path_para_guardar, logo_url,
    LOGO_PATH, FONDO_PATH,
)
from db import (
    init_db,
    guardar_propiedad,
    listar_propiedades,
    listar_propiedades_publicadas,
    listar_propiedades_top,
    obtener_propiedad,
    obtener_propiedad_publicada,
    obtener_propiedad_row,
    set_publicado,
    eliminar_propiedad_db,
    listar_agentes,
    crear_agente,
    obtener_agente_por_usuario,
    obtener_agente,
    set_agente_activo,
    eliminar_agente,
    set_password_agente,
    set_datos_agente,
    set_suscripcion,
    listar_noticias,
    obtener_noticia,
    obtener_metricas,
    guardar_noticia,
    crear_cuenta,
    obtener_cuenta,
    listar_cuentas,
    eliminar_cuenta,
    set_cuenta_activa,
    contar_agentes_cuenta,
    contar_propiedades_agente,
    set_suscripcion_cuenta,
    listar_agentes_cuenta,
    set_permisos_agente,
)
from noticias_scheduler import iniciar_scheduler_noticias
from gemini_service import generar_noticia_diaria
from auth import (
    seed_admin,
    hash_password,
    verificar_password,
    obtener_usuario_actual,
    iniciar_sesion,
    cerrar_sesion,
    verificar_suscripcion,
    es_superadmin,
    es_principal_agente,
    tiene_permiso,
    puede_ver_propiedad,
    puede_modificar_propiedad,
    puede_eliminar_propiedad,
)

load_dotenv()

app = FastAPI(title="Mi Propiedad")
init_db()
seed_admin()
# Job diario: genera texto (Claude) + imagen (Pollinations.ai) para noticias/tips.
iniciar_scheduler_noticias()

SESSION_SECRET = os.environ.get("SESSION_SECRET_KEY", "clave-temporal-cambiar")
# max_age=None → cookie de sesion: expira al cerrar el navegador (nunca queda guardada)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, session_cookie="mp_session", max_age=None)


def _cerrar_sesion_agente(request: Request) -> None:
    """Al salir de la zona de agentes hacia el sitio publico, la sesion se cierra por seguridad."""
    if request.session.get("agente_id"):
        request.session.clear()

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
    _cerrar_sesion_agente(request)
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
            "logo_url": logo_url(),
        },
    )


@app.get("/servicios", response_class=HTMLResponse)
async def servicios_publico(request: Request):
    _cerrar_sesion_agente(request)
    return templates.TemplateResponse(
        request=request,
        name="public/servicios.html",
        context={
            "branding": get_branding(),
            "anio": datetime.now().year,
            "propiedades_top": listar_propiedades_top(10),
            "logo_url": logo_url(),
        },
    )


@app.get("/catalogo", response_class=HTMLResponse)
async def catalogo_publico(request: Request):
    _cerrar_sesion_agente(request)
    propiedades = listar_propiedades_publicadas()
    return templates.TemplateResponse(
        request=request,
        name="public/catalogo.html",
        context={
            "branding": get_branding(),
            "propiedades": propiedades,
            "anio": datetime.now().year,
            "logo_url": logo_url(),
        },
    )


@app.get("/catalogo/{prop_id}", response_class=HTMLResponse)
async def catalogo_detalle_publico(request: Request, prop_id: int):
    _cerrar_sesion_agente(request)
    payload = obtener_propiedad_publicada(prop_id)
    if not payload:
        return RedirectResponse(url="/catalogo")
    return templates.TemplateResponse(
        request=request,
        name="public/propiedad_detalle.html",
        context={"branding": get_branding(), "anio": datetime.now().year, "logo_url": logo_url(), **payload},
    )


@app.get("/noticias/{noticia_id}", response_class=HTMLResponse)
async def noticia_detalle_publico(request: Request, noticia_id: int):
    _cerrar_sesion_agente(request)
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
            "logo_url": logo_url(),
        },
    )


# ──────────────────────────────────────────────────────────────
# Páginas legales (rutas explícitas, NO usar comodín /{doc} porque
# interceptaría /login, /panel, etc.)
# ──────────────────────────────────────────────────────────────

_LEGAL_DOCS = {
    "privacidad": {
        "titulo": "Política de Privacidad",
        "bloques": [
            (
                "Información que recopilamos",
                "Recopilamos los datos que nos proporcionas voluntariamente al contactarnos "
                "o solicitar información sobre una propiedad, como tu nombre, teléfono y "
                "correo electrónico, así como datos técnicos básicos de navegación.",
            ),
            (
                "Uso de la información",
                "Usamos tus datos únicamente para gestionar tu solicitud, ponernos en "
                "contacto contigo y mejorar la calidad de nuestro servicio. No vendemos ni "
                "compartimos tu información con terceros ajenos a la gestión inmobiliaria.",
            ),
            (
                "Tus derechos",
                "Puedes solicitar en cualquier momento acceder, corregir o eliminar tus "
                "datos personales escribiéndonos a través de los medios de contacto "
                "publicados en este sitio.",
            ),
        ],
    },
    "terminos": {
        "titulo": "Términos de Servicio",
        "bloques": [
            (
                "Uso del sitio",
                "Este sitio web tiene fines informativos sobre propiedades inmobiliarias. "
                "El uso del sitio implica la aceptación de estos términos.",
            ),
            (
                "Exactitud de la información",
                "Nos esforzamos por mantener actualizada la información de precios y "
                "disponibilidad de cada propiedad, pero puede variar sin previo aviso. "
                "Recomendamos confirmar los detalles directamente con el agente.",
            ),
            (
                "Propiedad intelectual",
                "Las imágenes, textos y contenido publicados en este sitio pertenecen a la "
                "agencia y no pueden reproducirse sin autorización previa.",
            ),
        ],
    },
}


@app.get("/privacidad", response_class=HTMLResponse)
async def legal_privacidad(request: Request):
    _cerrar_sesion_agente(request)
    doc = _LEGAL_DOCS["privacidad"]
    return templates.TemplateResponse(
        request=request,
        name="public/legal.html",
        context={
            "branding": get_branding(),
            "anio": datetime.now().year,
            "logo_url": logo_url(),
            "titulo_doc": doc["titulo"],
            "bloques": doc["bloques"],
        },
    )


@app.get("/terminos", response_class=HTMLResponse)
async def legal_terminos(request: Request):
    _cerrar_sesion_agente(request)
    doc = _LEGAL_DOCS["terminos"]
    return templates.TemplateResponse(
        request=request,
        name="public/legal.html",
        context={
            "branding": get_branding(),
            "anio": datetime.now().year,
            "logo_url": logo_url(),
            "titulo_doc": doc["titulo"],
            "bloques": doc["bloques"],
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


def _solo_digitos(texto: str) -> str:
    return "".join(c for c in (texto or "") if c.isdigit())


@app.get("/recuperar", response_class=HTMLResponse)
async def recuperar_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="recuperar.html",
        context={"branding": get_branding(), "error": None, "exito": False},
    )


@app.post("/recuperar")
async def recuperar_submit(
    request: Request,
    usuario: str = Form(...),
    email: str = Form(...),
    telefono_movil: str = Form(...),
    password_nueva: str = Form(...),
    password_confirmar: str = Form(...),
):
    def _error(msg: str):
        return templates.TemplateResponse(
            request=request,
            name="recuperar.html",
            context={"branding": get_branding(), "error": msg, "exito": False},
            status_code=400,
        )

    if password_nueva != password_confirmar:
        return _error("Las contraseñas no coinciden.")
    if len(password_nueva) < 6:
        return _error("La nueva contraseña debe tener al menos 6 caracteres.")

    agente = obtener_agente_por_usuario(usuario.strip())
    # Verificacion de identidad: usuario + correo + movil deben coincidir.
    # Mensaje generico para no revelar que dato fallo.
    identidad_ok = (
        agente
        and agente.get("activo")
        and (agente.get("email") or "").strip().lower() == email.strip().lower()
        and _solo_digitos(agente.get("telefono_movil")) == _solo_digitos(telefono_movil)
        and (agente.get("email") or "").strip() != ""
        and _solo_digitos(agente.get("telefono_movil")) != ""
    )
    if not identidad_ok:
        return _error(
            "Los datos no coinciden con ninguna cuenta activa. "
            "Verifica tu usuario, correo y móvil, o contacta a tu administrador."
        )

    set_password_agente(agente["id"], hash_password(password_nueva))
    return templates.TemplateResponse(
        request=request,
        name="recuperar.html",
        context={"branding": get_branding(), "error": None, "exito": True},
    )


# ──────────────────────────────────────────────────────────────
# Panel Admin — SuperAdmin gestiona cuentas (reemplaza panel_agentes)
# ──────────────────────────────────────────────────────────────

@app.get("/panel/agentes", response_class=HTMLResponse)
async def panel_agentes_redirect(request: Request):
    return RedirectResponse(url="/panel/admin", status_code=303)


@app.get("/panel/admin", response_class=HTMLResponse)
async def panel_admin(request: Request, mensaje: str = "", error: str = ""):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/panel/admin", status_code=303)
    if not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    cuentas = listar_cuentas()
    for c in cuentas:
        c["agentes"] = listar_agentes_cuenta(c["id"])
    todos_agentes = listar_agentes()
    for a in todos_agentes:
        a["propiedades"] = contar_propiedades_agente(a["id"])
    return templates.TemplateResponse(
        request=request,
        name="panel_admin.html",
        context={
            "branding": get_branding(),
            "agente": agente,
            "cuentas": cuentas,
            "todos_agentes": todos_agentes,
            "mensaje": mensaje,
            "error": error,
        },
    )


@app.post("/panel/admin/cuenta")
async def crear_cuenta_endpoint(
    request: Request,
    nombre_cuenta: str = Form(...),
    tipo_cuenta: str = Form("inmobiliaria"),
    usuario_principal: str = Form(...),
    nombre_principal: str = Form(...),
    movil_principal: str = Form(...),
    email_principal: str = Form(...),
    password_principal: str = Form(...),
):
    agente = obtener_usuario_actual(request)
    if not agente or not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    if obtener_agente_por_usuario(usuario_principal.strip()):
        return RedirectResponse(
            url="/panel/admin?error=El usuario ya existe.", status_code=303
        )
    cuenta_id = crear_cuenta(nombre_cuenta.strip(), tipo_cuenta)
    crear_agente(
        usuario=usuario_principal.strip(),
        password_hash=hash_password(password_principal),
        nombre_completo=nombre_principal.strip(),
        cuenta_id=cuenta_id,
        es_principal=True,
        telefono_movil=movil_principal.strip(),
        email=email_principal.strip(),
    )
    return RedirectResponse(
        url="/panel/admin?mensaje=Cuenta creada correctamente.", status_code=303
    )


@app.post("/panel/admin/cuenta/{cuenta_id}/estado")
async def cambiar_estado_cuenta(request: Request, cuenta_id: int, activo: int = Form(...)):
    agente = obtener_usuario_actual(request)
    if not agente or not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    set_cuenta_activa(cuenta_id, bool(activo))
    return RedirectResponse(url="/panel/admin?mensaje=Estado actualizado.", status_code=303)


@app.post("/panel/admin/cuenta/{cuenta_id}/eliminar")
async def eliminar_cuenta_endpoint(request: Request, cuenta_id: int):
    agente = obtener_usuario_actual(request)
    if not agente or not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    eliminar_cuenta(cuenta_id)
    return RedirectResponse(url="/panel/admin?mensaje=Cuenta eliminada.", status_code=303)


@app.post("/panel/admin/cuenta/{cuenta_id}/suscripcion")
async def cambiar_suscripcion_cuenta(
    request: Request,
    cuenta_id: int,
    plan: str = Form(...),
    fecha_inicio: str = Form(""),
    fecha_fin: str = Form(""),
):
    agente = obtener_usuario_actual(request)
    if not agente or not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    inicio = fecha_inicio or datetime.now().strftime("%Y-%m-%d")
    fin = "" if plan == "vitalicio" else fecha_fin
    set_suscripcion_cuenta(cuenta_id, plan, inicio, fin)
    return RedirectResponse(url="/panel/admin?mensaje=Suscripcion de cuenta actualizada.", status_code=303)


@app.post("/panel/admin/agente/{agente_id}/suscripcion")
async def admin_agente_suscripcion(
    request: Request,
    agente_id: int,
    plan: str = Form("prueba"),
    fecha_inicio: str = Form(""),
    fecha_fin: str = Form(""),
):
    agente = obtener_usuario_actual(request)
    if not agente or not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    inicio = fecha_inicio or datetime.now().strftime("%Y-%m-%d")
    fin = "" if plan == "vitalicio" else fecha_fin
    set_suscripcion(agente_id, plan, inicio, fin)
    return RedirectResponse(url="/panel/admin?mensaje=Suscripcion de agente actualizada.", status_code=303)


@app.post("/panel/admin/agente/{agente_id}/estado")
async def admin_agente_estado(request: Request, agente_id: int, activo: int = Form(1)):
    agente = obtener_usuario_actual(request)
    if not agente or not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    set_agente_activo(agente_id, bool(activo))
    return RedirectResponse(url="/panel/admin?mensaje=Estado del agente actualizado.", status_code=303)


@app.post("/panel/admin/agente/{agente_id}/eliminar")
async def admin_agente_eliminar(request: Request, agente_id: int):
    agente = obtener_usuario_actual(request)
    if not agente or not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    if agente_id == agente["id"]:
        return RedirectResponse(url="/panel/admin?error=No puedes eliminarte a ti mismo.", status_code=303)
    eliminar_agente(agente_id)
    return RedirectResponse(url="/panel/admin?mensaje=Agente eliminado.", status_code=303)


@app.post("/panel/admin/agente/{agente_id}/datos")
async def admin_agente_datos(
    request: Request,
    agente_id: int,
    nombre_completo: str = Form(""),
    telefono_movil: str = Form(""),
    email: str = Form(""),
):
    agente = obtener_usuario_actual(request)
    if not agente or not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    set_datos_agente(agente_id, nombre_completo.strip(), telefono_movil.strip(), email.strip())
    return RedirectResponse(url="/panel/admin?mensaje=Datos del agente actualizados.", status_code=303)


@app.post("/panel/admin/agente/{agente_id}/password")
async def admin_agente_password(request: Request, agente_id: int, password_nueva: str = Form(...)):
    agente = obtener_usuario_actual(request)
    if not agente or not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    if len(password_nueva) < 6:
        return RedirectResponse(
            url="/panel/admin?error=La contraseña debe tener al menos 6 caracteres.", status_code=303)
    set_password_agente(agente_id, hash_password(password_nueva))
    return RedirectResponse(url="/panel/admin?mensaje=Contraseña restablecida.", status_code=303)


@app.get("/panel/admin/backup")
async def backup_descarga(request: Request):
    import zipfile
    agente = obtener_usuario_actual(request)
    if not agente or not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"backup_{ts}.zip"
    zip_path = UPLOAD_DIR / zip_name
    db_path = BASE_DIR / "data" / "propiedades.db"
    data_dir = BASE_DIR / "data"
    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        if db_path.exists():
            zf.write(str(db_path), "data/propiedades.db")
        for f in data_dir.glob("branding*.json"):
            zf.write(str(f), f"data/{f.name}")
        logos_dir = BASE_DIR / "static" / "logos"
        if logos_dir.exists():
            for f in logos_dir.iterdir():
                if f.is_file():
                    zf.write(str(f), f"static/logos/{f.name}")
        fondos_dir = BASE_DIR / "static" / "fondos"
        if fondos_dir.exists():
            for f in fondos_dir.iterdir():
                if f.is_file():
                    zf.write(str(f), f"static/fondos/{f.name}")
        logo_global = BASE_DIR / "static" / "logo.png"
        if logo_global.exists():
            zf.write(str(logo_global), "static/logo.png")
        fondo_global = BASE_DIR / "static" / "fondo.jpg"
        if fondo_global.exists():
            zf.write(str(fondo_global), "static/fondo.jpg")
    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=zip_name,
        headers={"Content-Disposition": f"attachment; filename={zip_name}"},
    )


@app.get("/panel/admin/restaurar", response_class=HTMLResponse)
async def restaurar_form(request: Request, ok: int = 0, error: str = ""):
    agente = obtener_usuario_actual(request)
    if not agente or not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    mensaje = ""
    if ok:
        mensaje = "<div class='card' style='border-left:4px solid #27ae60;'>✅ Datos restaurados correctamente.</div>"
    elif error:
        mensaje = f"<div class='card' style='border-left:4px solid #c0392b;'>⚠ {error}</div>"
    return HTMLResponse(f"""
    <!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
    <title>Restaurar respaldo</title><link rel="stylesheet" href="/static/style.css"></head>
    <body><div class="container" style="max-width:520px; margin-top:3rem;">
    <div class="card">
      <h2>Restaurar respaldo de datos</h2>
      <p style="font-size:0.85rem; color:#888;">
        Sube el .zip generado por "Descargar backup" (data/propiedades.db, branding*.json, static/logos, static/fondo/logo).
        Esto SOBRESCRIBE los datos actuales del volumen persistente.
      </p>
      {mensaje}
      <form action="/panel/admin/restaurar" method="post" enctype="multipart/form-data">
        <input type="file" name="archivo" accept=".zip" required style="margin:1rem 0;" />
        <button type="submit" class="btn-primary">Restaurar</button>
      </form>
      <a href="/panel" class="btn-secondary" style="display:inline-block; margin-top:1rem;">Volver</a>
    </div></div></body></html>
    """)


@app.post("/panel/admin/restaurar")
async def restaurar_submit(request: Request, archivo: UploadFile = File(...)):
    import zipfile
    agente = obtener_usuario_actual(request)
    if not agente or not es_superadmin(agente):
        return RedirectResponse(url="/panel", status_code=303)
    if not archivo.filename or not archivo.filename.lower().endswith(".zip"):
        return RedirectResponse(url="/panel/admin/restaurar?error=El+archivo+debe+ser+un+.zip", status_code=303)
    tmp_zip = UPLOAD_DIR / f"restaurar_{uuid.uuid4().hex[:8]}.zip"
    try:
        with tmp_zip.open("wb") as f:
            shutil.copyfileobj(archivo.file, f)
        data_dir = BASE_DIR / "data"
        static_dir = BASE_DIR / "static"
        data_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(str(tmp_zip), "r") as zf:
            for nombre in zf.namelist():
                if nombre.endswith("/"):
                    continue
                if not (nombre.startswith("data/") or nombre.startswith("static/")):
                    continue
                destino = BASE_DIR / nombre
                destino.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(nombre) as origen, destino.open("wb") as salida:
                    shutil.copyfileobj(origen, salida)
        return RedirectResponse(url="/panel/admin/restaurar?ok=1", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/panel/admin/restaurar?error={quote(str(e)[:150])}", status_code=303)
    finally:
        tmp_zip.unlink(missing_ok=True)


# ──────────────────────────────────────────────────────────────
# Panel Mi Equipo — Principal gestiona agentes de su cuenta
# ──────────────────────────────────────────────────────────────

@app.get("/panel/mi-equipo", response_class=HTMLResponse)
async def panel_equipo(request: Request, mensaje: str = "", error: str = ""):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/panel/mi-equipo", status_code=303)
    if not es_principal_agente(agente) or not agente.get("cuenta_id"):
        return RedirectResponse(url="/panel", status_code=303)
    cuenta = obtener_cuenta(agente["cuenta_id"])
    agentes_cuenta = listar_agentes_cuenta(agente["cuenta_id"])
    return templates.TemplateResponse(
        request=request,
        name="panel_equipo.html",
        context={
            "branding": get_branding(agente),
            "agente": agente,
            "cuenta": cuenta,
            "agentes_cuenta": agentes_cuenta,
            "mensaje": mensaje,
            "error": error,
        },
    )


@app.post("/panel/mi-equipo/agente")
async def crear_agente_equipo(
    request: Request,
    usuario: str = Form(...),
    nombre_completo: str = Form(...),
    telefono_movil: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    agente = obtener_usuario_actual(request)
    if not agente or not es_principal_agente(agente) or not agente.get("cuenta_id"):
        return RedirectResponse(url="/panel", status_code=303)
    cuenta = obtener_cuenta(agente["cuenta_id"])
    if not cuenta:
        return RedirectResponse(url="/panel", status_code=303)
    num = contar_agentes_cuenta(agente["cuenta_id"])
    if num >= cuenta["max_agentes"]:
        return RedirectResponse(
            url=f"/panel/mi-equipo?error=Limite de agentes alcanzado ({cuenta['max_agentes']}).",
            status_code=303,
        )
    if obtener_agente_por_usuario(usuario.strip()):
        return RedirectResponse(
            url="/panel/mi-equipo?error=Ese usuario ya existe.", status_code=303
        )
    crear_agente(
        usuario=usuario.strip(),
        password_hash=hash_password(password),
        nombre_completo=nombre_completo.strip(),
        cuenta_id=agente["cuenta_id"],
        es_principal=False,
        telefono_movil=telefono_movil.strip(),
        email=email.strip(),
    )
    return RedirectResponse(
        url="/panel/mi-equipo?mensaje=Agente creado.", status_code=303
    )


@app.post("/panel/mi-equipo/agente/{agente_id}/estado")
async def cambiar_estado_agente_equipo(request: Request, agente_id: int, activo: int = Form(...)):
    agente = obtener_usuario_actual(request)
    if not agente or not es_principal_agente(agente):
        return RedirectResponse(url="/panel", status_code=303)
    if agente_id == agente["id"]:
        return RedirectResponse(
            url="/panel/mi-equipo?error=No puedes desactivarte.", status_code=303
        )
    set_agente_activo(agente_id, bool(activo))
    return RedirectResponse(url="/panel/mi-equipo?mensaje=Estado actualizado.", status_code=303)


@app.post("/panel/mi-equipo/agente/{agente_id}/eliminar")
async def eliminar_agente_equipo(request: Request, agente_id: int):
    agente = obtener_usuario_actual(request)
    if not agente or not es_principal_agente(agente):
        return RedirectResponse(url="/panel", status_code=303)
    if agente_id == agente["id"]:
        return RedirectResponse(
            url="/panel/mi-equipo?error=No puedes eliminarte.", status_code=303
        )
    eliminar_agente(agente_id)
    return RedirectResponse(url="/panel/mi-equipo?mensaje=Agente eliminado.", status_code=303)


@app.post("/panel/mi-equipo/agente/{agente_id}/permisos")
async def cambiar_permisos_agente(
    request: Request,
    agente_id: int,
    crear_propiedad: str = Form(None),
    modificar_propiedad: str = Form(None),
    eliminar_propiedad: str = Form(None),
):
    agente = obtener_usuario_actual(request)
    if not agente or not es_principal_agente(agente):
        return RedirectResponse(url="/panel", status_code=303)
    permisos = {
        "crear_propiedad": bool(crear_propiedad),
        "modificar_propiedad": bool(modificar_propiedad),
        "eliminar_propiedad": bool(eliminar_propiedad),
        "crear_agente": False,
        "eliminar_agente": False,
    }
    set_permisos_agente(agente_id, permisos)
    return RedirectResponse(url="/panel/mi-equipo?mensaje=Permisos actualizados.", status_code=303)


@app.post("/panel/mi-equipo/agente/{agente_id}/password")
async def restablecer_password_equipo(request: Request, agente_id: int, password_nueva: str = Form(...)):
    agente = obtener_usuario_actual(request)
    if not agente or not es_principal_agente(agente):
        return RedirectResponse(url="/panel", status_code=303)
    objetivo = obtener_agente(agente_id)
    # Solo puede restablecer contraseñas de agentes de su misma cuenta.
    if not objetivo or objetivo.get("cuenta_id") != agente.get("cuenta_id"):
        return RedirectResponse(
            url="/panel/mi-equipo?error=No puedes modificar ese agente.", status_code=303)
    if len(password_nueva) < 6:
        return RedirectResponse(
            url="/panel/mi-equipo?error=La contraseña debe tener al menos 6 caracteres.", status_code=303)
    set_password_agente(agente_id, hash_password(password_nueva))
    return RedirectResponse(url="/panel/mi-equipo?mensaje=Contraseña restablecida.", status_code=303)


# ──────────────────────────────────────────────────────────────
# Panel privado (requiere sesión de agente)
# ──────────────────────────────────────────────────────────────

@app.get("/panel", response_class=HTMLResponse)
async def dashboard(request: Request):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/panel", status_code=303)
    branding_data = get_branding(agente)
    suscripcion = verificar_suscripcion(agente)
    if not suscripcion["activa"]:
        return templates.TemplateResponse(
            request=request,
            name="suscripcion_vencida.html",
            context={"branding": branding_data, "agente": agente, "suscripcion": suscripcion},
        )
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "branding": branding_data,
            "agente": agente,
            "suscripcion": suscripcion,
            "metricas": obtener_metricas(agente),
        },
    )


@app.get("/panel/crear", response_class=HTMLResponse)
async def formulario(request: Request):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/panel/crear", status_code=303)
    if not tiene_permiso(agente, "crear_propiedad"):
        return RedirectResponse(url="/panel", status_code=303)
    branding_data = get_branding(agente)
    suscripcion = verificar_suscripcion(agente)
    if not suscripcion["activa"]:
        return templates.TemplateResponse(
            request=request,
            name="suscripcion_vencida.html",
            context={"branding": branding_data, "agente": agente, "suscripcion": suscripcion},
        )
    return templates.TemplateResponse(
        request=request,
        name="form.html",
        context={"branding": branding_data, "agente": agente, "suscripcion": suscripcion},
    )


@app.get("/generar")
async def generar_redirect():
    return RedirectResponse(url="/panel/crear")


@app.post("/panel/generar-noticia")
async def generar_noticia_manual(request: Request):
    """Genera manualmente la noticia/tip del día (texto con Claude + imagen con Pollinations.ai)."""
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/panel", status_code=303)
    suscripcion = verificar_suscripcion(agente)
    if not suscripcion["activa"]:
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
async def configuracion(request: Request, guardado: int = 0, pw_ok: str = "", pw_error: str = ""):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/configuracion", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="configuracion.html",
        context={
            "branding": get_branding(agente),
            "agente": agente,
            "logo_existe": logo_existe(agente),
            "logo_url": logo_url(agente),
            "guardado": bool(guardado),
            "pw_ok": pw_ok,
            "pw_error": pw_error,
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
    franja_opacidad: str = Form("50"),
    franja_tamano: str = Form("20"),
    eslogan: str = Form(""),
    descripcion_agencia: str = Form(""),
    servicio_1_titulo: str = Form(""),
    servicio_1_desc: str = Form(""),
    servicio_2_titulo: str = Form(""),
    servicio_2_desc: str = Form(""),
    servicio_3_titulo: str = Form(""),
    servicio_3_desc: str = Form(""),
    instagram: str = Form(""),
    facebook: str = Form(""),
    x: str = Form(""),
    logo: UploadFile = File(None),
    fondo: UploadFile = File(None),
):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/configuracion", status_code=303)
    nivel = "cuenta" if (es_principal_agente(agente) or es_superadmin(agente)) else "agente"
    guardar_branding({
        "nombre_agencia": nombre_agencia,
        "color_primario": color_primario,
        "color_secundario": color_secundario,
        "nombre_agente": nombre_agente,
        "telefono_agente": telefono_agente,
        "email_agente": email_agente,
        "fondo_opacidad": fondo_opacidad,
        "plantilla": plantilla,
        "franja_opacidad": franja_opacidad,
        "franja_tamano": franja_tamano,
        "eslogan": eslogan,
        "descripcion_agencia": descripcion_agencia,
        "servicio_1_titulo": servicio_1_titulo,
        "servicio_1_desc": servicio_1_desc,
        "servicio_2_titulo": servicio_2_titulo,
        "servicio_2_desc": servicio_2_desc,
        "servicio_3_titulo": servicio_3_titulo,
        "servicio_3_desc": servicio_3_desc,
        "instagram": instagram,
        "facebook": facebook,
        "x": x,
    }, agente=agente, nivel=nivel, campos_limpiables={"instagram", "facebook", "x"})
    logo_dest = logo_path_para_guardar(agente, nivel)
    fondo_dest = fondo_path_para_guardar(agente, nivel)
    if logo and logo.filename:
        with logo_dest.open("wb") as f:
            shutil.copyfileobj(logo.file, f)
    if fondo and fondo.filename:
        try:
            from PIL import Image
            img = Image.open(fondo.file).convert("RGB")
            img.save(str(fondo_dest), "JPEG", quality=85)
        except Exception:
            with fondo_dest.open("wb") as f:
                fondo.file.seek(0)
                shutil.copyfileobj(fondo.file, f)
    return RedirectResponse(url="/configuracion?guardado=1", status_code=303)


@app.post("/configuracion/password")
async def cambiar_mi_password(
    request: Request,
    password_actual: str = Form(...),
    password_nueva: str = Form(...),
    password_confirmar: str = Form(...),
):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/configuracion", status_code=303)

    def _volver(msg: str, ok: bool = False):
        clave = "pw_ok" if ok else "pw_error"
        return RedirectResponse(url=f"/configuracion?{clave}={quote(msg)}", status_code=303)

    if not verificar_password(password_actual, agente["password_hash"]):
        return _volver("La contraseña actual es incorrecta.")
    if len(password_nueva) < 6:
        return _volver("La nueva contraseña debe tener al menos 6 caracteres.")
    if password_nueva != password_confirmar:
        return _volver("La nueva contraseña y su confirmación no coinciden.")
    if password_nueva == password_actual:
        return _volver("La nueva contraseña debe ser distinta a la actual.")

    set_password_agente(agente["id"], hash_password(password_nueva))
    return _volver("Contraseña actualizada correctamente.", ok=True)


@app.get("/historial", response_class=HTMLResponse)
async def historial(request: Request, busqueda: str = ""):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/historial", status_code=303)
    aid = None
    cid = None
    if es_superadmin(agente):
        pass
    elif es_principal_agente(agente) and agente.get("cuenta_id"):
        cid = agente["cuenta_id"]
    else:
        aid = agente["id"]
    propiedades = listar_propiedades(busqueda.strip() or None, agente_id=aid, cuenta_id=cid)
    return templates.TemplateResponse(
        request=request,
        name="historial.html",
        context={
            "branding": get_branding(agente),
            "agente": agente,
            "propiedades": propiedades,
            "busqueda": busqueda,
        },
    )


@app.post("/historial/{prop_id}/publicar")
async def alternar_publicacion(request: Request, prop_id: int, publicado: int = Form(...)):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/historial", status_code=303)
    prop_row = obtener_propiedad_row(prop_id)
    if not prop_row or not puede_modificar_propiedad(agente, prop_row.get("agente_id")):
        return RedirectResponse(url="/historial", status_code=303)
    set_publicado(prop_id, bool(publicado))
    return RedirectResponse(url="/historial", status_code=303)


@app.post("/historial/{prop_id}/eliminar")
async def eliminar_propiedad_endpoint(request: Request, prop_id: int):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/historial", status_code=303)
    prop_row = obtener_propiedad_row(prop_id)
    if not prop_row or not puede_eliminar_propiedad(agente, prop_row.get("agente_id")):
        return RedirectResponse(url="/historial", status_code=303)
    eliminar_propiedad_db(prop_id)
    return RedirectResponse(url="/historial", status_code=303)


@app.get("/historial/{prop_id}", response_class=HTMLResponse)
async def historial_detalle(request: Request, prop_id: int):
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/historial", status_code=303)
    payload = obtener_propiedad(prop_id)
    if not payload:
        return RedirectResponse(url="/historial")
    prop_agente_id = payload.get("_agente_id")
    if not puede_ver_propiedad(agente, prop_agente_id):
        return RedirectResponse(url="/historial")
    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={"branding": get_branding(agente), "prop_id": prop_id, **payload},
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
    agente = obtener_usuario_actual(request)
    if not agente:
        return RedirectResponse(url="/login?siguiente=/panel", status_code=303)
    if not tiene_permiso(agente, "crear_propiedad"):
        return RedirectResponse(url="/panel", status_code=303)
    suscripcion = verificar_suscripcion(agente)
    if not suscripcion["activa"]:
        return templates.TemplateResponse(
            request=request,
            name="suscripcion_vencida.html",
            context={"branding": get_branding(agente), "agente": agente, "suscripcion": suscripcion},
        )

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
        portada_compuesta_url = componer_portada(str(destino), datos, agente=agente)
        portada_descarga_url = _descarga(portada_compuesta_url)
        stories_url = componer_stories(str(destino), datos, agente=agente)
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
        for u in componer_overlay_extras(extras_paths, datos, agente=agente)
    ]
    collage_url = None
    collage_descarga_url = None
    if portada_path:
        collage_url = componer_collage(portada_path, extras_paths, datos, agente=agente)
        if collage_url:
            collage_descarga_url = _descarga(collage_url)

    try:
        contenido = generar_contenido(datos, tono=tono, longitud=longitud)
        # PDF descargable con toda la ficha de la propiedad
        pdf_descarga_url = generar_pdf(
            datos, contenido["descripcion"], portada_path, extras_paths, agente=agente
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"branding": get_branding(agente), "mensaje": str(e)},
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

    prop_id = guardar_propiedad(payload, agente_id=agente["id"])

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={"branding": get_branding(agente), "prop_id": prop_id, **payload},
    )
