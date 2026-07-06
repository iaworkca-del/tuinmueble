import os
import bcrypt
from datetime import datetime, timedelta

from fastapi import Request
from fastapi.responses import RedirectResponse

from db import obtener_agente_por_usuario, obtener_agente, crear_agente, contar_agentes

DIAS_PRUEBA = 7
ADMIN_TELEFONO = "+58 0414-8960164"


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


def verificar_suscripcion(agente: dict) -> dict:
    """Verifica el estado de suscripción de un agente.

    Retorna un dict con:
      - activa (bool): si puede usar las funciones de IA
      - plan (str): prueba, mensual, anual, vitalicio
      - mensaje (str): mensaje para mostrar si está bloqueado
      - dias_restantes (int|None): días que le quedan
    """
    if not agente:
        return {"activa": False, "plan": "", "mensaje": "Sin sesión.", "dias_restantes": None}

    if agente.get("es_admin"):
        return {"activa": True, "plan": "vitalicio", "mensaje": "", "dias_restantes": None}

    plan = agente.get("plan") or "prueba"
    inicio = agente.get("suscripcion_inicio") or agente.get("creado_en") or ""
    fin = agente.get("suscripcion_fin") or ""
    ahora = datetime.now()

    if plan == "vitalicio":
        return {"activa": True, "plan": "vitalicio", "mensaje": "", "dias_restantes": None}

    if plan == "prueba":
        if fin:
            try:
                fecha_fin_prueba = datetime.fromisoformat(fin)
            except (ValueError, TypeError):
                fecha_fin_prueba = ahora
        else:
            try:
                fecha_inicio = datetime.fromisoformat(inicio)
            except (ValueError, TypeError):
                fecha_inicio = ahora
            fecha_fin_prueba = fecha_inicio + timedelta(days=DIAS_PRUEBA)
        dias_restantes = (fecha_fin_prueba - ahora).days
        if dias_restantes >= 0:
            return {
                "activa": True,
                "plan": "prueba",
                "mensaje": f"Periodo de prueba: {dias_restantes} día(s) restante(s).",
                "dias_restantes": dias_restantes,
            }
        return {
            "activa": False,
            "plan": "prueba",
            "mensaje": (
                "Tu periodo de prueba de 7 días ha finalizado. "
                "Para seguir generando contenido con IA, contacta al administrador "
                f"al {ADMIN_TELEFONO} para activar tu suscripción."
            ),
            "dias_restantes": 0,
        }

    # Planes pagos: mensual o anual
    if fin:
        try:
            fecha_fin = datetime.fromisoformat(fin)
        except (ValueError, TypeError):
            fecha_fin = ahora
        dias_restantes = (fecha_fin - ahora).days
        if dias_restantes >= 0:
            return {
                "activa": True,
                "plan": plan,
                "mensaje": f"Plan {plan}: {dias_restantes} día(s) restante(s).",
                "dias_restantes": dias_restantes,
            }
        return {
            "activa": False,
            "plan": plan,
            "mensaje": (
                f"Tu suscripción ({plan}) ha vencido. "
                "Para renovar, contacta al administrador "
                f"al {ADMIN_TELEFONO}."
            ),
            "dias_restantes": 0,
        }

    return {
        "activa": False,
        "plan": plan,
        "mensaje": (
            "No tienes una suscripción activa. Contacta al administrador "
            f"al {ADMIN_TELEFONO} para activar tu plan."
        ),
        "dias_restantes": 0,
    }
