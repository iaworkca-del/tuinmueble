import os
import bcrypt

from fastapi import Request
from fastapi.responses import RedirectResponse

from db import obtener_agente_por_usuario, obtener_agente, crear_agente, contar_agentes


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        pw_bytes = password.encode("utf-8")[:72]
        return bcrypt.checkpw(pw_bytes, password_hash.encode("utf-8"))
    except Exception:
        return False


def seed_admin():
    """Crea la cuenta administradora inicial a partir de variables de entorno,
    solo si aún no existen agentes registrados."""
    if contar_agentes() > 0:
        return
    usuario = os.environ.get("ADMIN_USUARIO")
    password = os.environ.get("ADMIN_PASSWORD")
    if not usuario or not password:
        return
    crear_agente(
        usuario=usuario.strip(),
        password_hash=hash_password(password),
        nombre_completo="Administrador",
        es_admin=True,
    )


def obtener_usuario_actual(request: Request):
    agente_id = request.session.get("agente_id")
    if not agente_id:
        return None
    agente = obtener_agente(agente_id)
    if not agente or not agente.get("activo"):
        return None
    return agente


def iniciar_sesion(request: Request, agente: dict):
    request.session["agente_id"] = agente["id"]


def cerrar_sesion(request: Request):
    request.session.clear()


def requiere_login(request: Request):
    """Dependencia de FastAPI: retorna el agente autenticado o levanta redirect."""
    agente = obtener_usuario_actual(request)
    if not agente:
        return None
    return agente


def redirect_a_login(request: Request) -> RedirectResponse:
    destino = request.url.path
    return RedirectResponse(url=f"/login?siguiente={destino}", status_code=303)


def requiere_admin(request: Request):
    agente = obtener_usuario_actual(request)
    if not agente or not agente.get("es_admin"):
        return None
    return agente
