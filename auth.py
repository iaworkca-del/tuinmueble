import os
import json
import bcrypt
from datetime import datetime, timedelta

from fastapi import Request
from fastapi.responses import RedirectResponse

from db import (obtener_agente_por_usuario, obtener_agente, crear_agente,
                contar_agentes, obtener_cuenta)

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
    n = contar_agentes()
    print(f"seed_admin: contar_agentes()={n}")
    if n > 0:
        print("seed_admin: ya hay agentes, no se crea admin.")
        return
    usuario = os.environ.get("ADMIN_USUARIO")
    password = os.environ.get("ADMIN_PASSWORD")
    print(f"seed_admin: ADMIN_USUARIO presente={bool(usuario)} ADMIN_PASSWORD presente={bool(password)}")
    if not usuario or not password:
        print("seed_admin: faltan variables de entorno, no se crea admin.")
        return
    try:
        nuevo = crear_agente(
            usuario=usuario.strip(),
            password_hash=hash_password(password),
            nombre_completo="Administrador",
            es_admin=True,
        )
        print(f"seed_admin: admin creado correctamente -> {nuevo}")
    except Exception as e:
        print(f"seed_admin: ERROR al crear admin: {e!r}")


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


# ── Funciones multi-tenant ──

def es_superadmin(agente: dict) -> bool:
    return bool(agente and agente.get("es_admin"))


def es_principal_agente(agente: dict) -> bool:
    return bool(agente and agente.get("es_principal"))


def tiene_permiso(agente: dict, permiso: str) -> bool:
    if not agente:
        return False
    if agente.get("es_admin"):
        return True
    if agente.get("es_principal"):
        return True
    try:
        permisos = json.loads(agente.get("permisos") or "{}")
    except (json.JSONDecodeError, TypeError):
        permisos = {}
    return permisos.get(permiso, False)


def puede_ver_propiedad(agente: dict, prop_agente_id: int) -> bool:
    if not agente:
        return False
    if agente.get("es_admin"):
        return True
    if prop_agente_id == agente["id"]:
        return True
    if agente.get("es_principal") and agente.get("cuenta_id"):
        prop_agente = obtener_agente(prop_agente_id)
        if prop_agente and prop_agente.get("cuenta_id") == agente["cuenta_id"]:
            return True
    return False


def puede_modificar_propiedad(agente: dict, prop_agente_id: int) -> bool:
    if not tiene_permiso(agente, "modificar_propiedad"):
        return False
    return puede_ver_propiedad(agente, prop_agente_id)


def puede_eliminar_propiedad(agente: dict, prop_agente_id: int) -> bool:
    if not tiene_permiso(agente, "eliminar_propiedad"):
        return False
    return puede_ver_propiedad(agente, prop_agente_id)


def verificar_suscripcion(agente: dict) -> dict:
    if not agente:
        return {"activa": False, "plan": "", "mensaje": "Sin sesión.", "dias_restantes": None}

    if agente.get("es_admin"):
        return {"activa": True, "plan": "vitalicio", "mensaje": "", "dias_restantes": None}

    cuenta_id = agente.get("cuenta_id")
    if cuenta_id:
        cuenta = obtener_cuenta(cuenta_id)
        if cuenta:
            plan = cuenta.get("plan") or "prueba"
            inicio = cuenta.get("suscripcion_inicio") or cuenta.get("creado_en") or ""
            fin = cuenta.get("suscripcion_fin") or ""
        else:
            plan = agente.get("plan") or "prueba"
            inicio = agente.get("suscripcion_inicio") or agente.get("creado_en") or ""
            fin = agente.get("suscripcion_fin") or ""
    else:
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
