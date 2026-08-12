"""Notificación por correo cuando llega un lead nuevo desde el sitio público.

Usa la API de Resend (https://resend.com). Si RESEND_API_KEY no está
configurada, no hace nada (el lead ya quedó guardado en la base de datos y
visible en /panel/leads, esto es solo un aviso adicional) — nunca debe
romper el flujo de captura.

El asunto y el mensaje de introducción son editables por cada agencia desde
/configuracion (branding["lead_email_asunto"] / ["lead_email_intro"]), con
marcadores de texto tipo {nombre}, {propiedad}, etc. — ver _TOKENS_DISPONIBLES.
"""
import os
import html
import logging
import httpx
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("notificaciones")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM", "notificaciones@orinokiagente.com")
RESEND_URL = "https://api.resend.com/emails"

ASUNTO_DEFAULT = "Nuevo contacto"
INTRO_DEFAULT = "Tienes un nuevo contacto desde tu sitio web."


def _configurado() -> bool:
    return bool(RESEND_API_KEY)


def _rellenar_plantilla(texto: str, tokens: dict) -> str:
    """Sustituye {nombre}, {propiedad}, etc. en un texto editado a mano por
    el agente; cualquier marcador desconocido o mal escrito se deja igual
    en vez de romper el envío."""
    return texto.format_map(defaultdict(str, tokens))


def notificar_lead_nuevo(
    destinatario_email: str,
    lead: dict,
    propiedad_titulo: str = "",
    branding: dict = None,
    base_url: str = "",
) -> None:
    if not destinatario_email:
        logger.warning("Lead #%s sin agente/correo destinatario; no se pudo notificar.", lead.get("id"))
        return
    if not _configurado():
        logger.warning(
            "RESEND_API_KEY no configurada; no se envió notificación del lead #%s.",
            lead.get("id"),
        )
        return

    branding = branding or {}
    tokens = {
        "nombre": lead.get("nombre", ""),
        "telefono": lead.get("telefono", ""),
        "correo": lead.get("email", ""),
        "mensaje": lead.get("mensaje", ""),
        "propiedad": propiedad_titulo,
    }
    try:
        asunto = _rellenar_plantilla(branding.get("lead_email_asunto") or ASUNTO_DEFAULT, tokens)
    except (KeyError, ValueError, IndexError):
        asunto = ASUNTO_DEFAULT
    if propiedad_titulo and "{propiedad}" not in (branding.get("lead_email_asunto") or ""):
        asunto += f" — {propiedad_titulo}"
    try:
        intro = _rellenar_plantilla(branding.get("lead_email_intro") or INTRO_DEFAULT, tokens)
    except (KeyError, ValueError, IndexError):
        intro = INTRO_DEFAULT

    color_primario = branding.get("color_primario") or "#1a3a5c"
    color_secundario = branding.get("color_secundario") or "#b1b65d"
    nombre_agencia = branding.get("nombre_agencia") or "Mi Propiedad"
    logo = branding.get("logo") or ""
    logo_abs = f"{base_url}{logo}" if logo and base_url else ""
    panel_url = f"{base_url}/panel/leads" if base_url else "#"

    filas_html = [f'<tr><td style="padding:6px 10px 6px 0;color:#888;">Nombre</td><td style="padding:6px 0;font-weight:600;color:#232323;">{html.escape(tokens["nombre"])}</td></tr>']
    if tokens["telefono"]:
        filas_html.append(f'<tr><td style="padding:6px 10px 6px 0;color:#888;">Teléfono</td><td style="padding:6px 0;font-weight:600;color:#232323;">{html.escape(tokens["telefono"])}</td></tr>')
    if tokens["correo"]:
        filas_html.append(f'<tr><td style="padding:6px 10px 6px 0;color:#888;">Correo</td><td style="padding:6px 0;font-weight:600;color:#232323;">{html.escape(tokens["correo"])}</td></tr>')
    if propiedad_titulo:
        filas_html.append(f'<tr><td style="padding:6px 10px 6px 0;color:#888;">Propiedad</td><td style="padding:6px 0;font-weight:600;color:#232323;">{html.escape(propiedad_titulo)}</td></tr>')

    mensaje_html = ""
    if tokens["mensaje"]:
        mensaje_html = f'''
        <p style="margin:18px 0 6px;color:#888;font-size:0.85rem;">Mensaje:</p>
        <p style="margin:0;padding:12px 14px;background:#f7f7f7;border-radius:8px;color:#333;white-space:pre-wrap;">{html.escape(tokens["mensaje"])}</p>
        '''

    logo_html = f'<img src="{logo_abs}" alt="{html.escape(nombre_agencia)}" style="height:48px;max-width:180px;object-fit:contain;margin-bottom:8px;" />' if logo_abs else ""

    cuerpo_html = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:520px;margin:0 auto;background:#fff;">
      <div style="background:{color_primario};padding:22px 20px;text-align:center;">
        {logo_html}
        <div style="color:#fff;font-size:1.15rem;font-weight:700;">{html.escape(nombre_agencia)}</div>
      </div>
      <div style="padding:26px 24px;">
        <p style="font-size:1rem;color:#333;margin-top:0;">{html.escape(intro)}</p>
        <table style="width:100%;border-collapse:collapse;font-size:0.95rem;">
          {''.join(filas_html)}
        </table>
        {mensaje_html}
        <div style="text-align:center;margin-top:26px;">
          <a href="{panel_url}" style="display:inline-block;background:{color_secundario};color:#1a1a1a;padding:11px 26px;border-radius:30px;text-decoration:none;font-weight:600;font-size:0.9rem;">Ver en el panel</a>
        </div>
      </div>
      <div style="padding:14px;text-align:center;color:#aaa;font-size:0.72rem;border-top:1px solid #eee;">{html.escape(nombre_agencia)} · Notificación automática</div>
    </div>
    """

    texto_plano_lineas = [intro, "", f"Nombre: {tokens['nombre']}"]
    if tokens["telefono"]:
        texto_plano_lineas.append(f"Teléfono: {tokens['telefono']}")
    if tokens["correo"]:
        texto_plano_lineas.append(f"Correo: {tokens['correo']}")
    if propiedad_titulo:
        texto_plano_lineas.append(f"Propiedad: {propiedad_titulo}")
    if tokens["mensaje"]:
        texto_plano_lineas += ["", "Mensaje:", tokens["mensaje"]]
    texto_plano_lineas += ["", "Ingresa a tu panel (/panel/leads) para responder y dar seguimiento."]

    try:
        resp = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": RESEND_FROM,
                "to": [destinatario_email],
                "subject": asunto,
                "html": cuerpo_html,
                "text": "\n".join(texto_plano_lineas),
            },
            timeout=10,
        )
        if resp.status_code >= 400:
            logger.error(
                "Resend rechazó la notificación del lead #%s a %s: %s %s",
                lead.get("id"), destinatario_email, resp.status_code, resp.text,
            )
    except Exception:
        logger.exception("Fallo al enviar notificación del lead #%s a %s", lead.get("id"), destinatario_email)
