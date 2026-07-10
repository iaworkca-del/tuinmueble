"""
Job/cron diario para la sección "Tips y Noticias Inmobiliarias".

Cada 24 horas (y una vez al iniciar la app, si hoy no se ha generado nada):
  (a) llama a Claude para generar el texto de la noticia/tip,
  (b) llama a Pollinations.ai para generar la imagen relacionada,
  (c) guarda el resultado en la base de datos (tabla `noticias`, se acumula, no reemplaza),
  (d) el sitio público lee siempre la última noticia disponible en /db.listar_noticias().
"""

import os
import threading
import time
from datetime import datetime, timedelta

from db import guardar_noticia, existe_noticia_hoy
from gemini_service import generar_noticia_diaria

SEGUNDOS_UN_DIA = 24 * 60 * 60
# Si la generación falla (p. ej. API caída), reintentar el mismo día en vez de
# esperar hasta la próxima medianoche.
SEGUNDOS_REINTENTO = 3 * 60 * 60  # 3 horas


def _hay_api_key() -> bool:
    """La generación de noticias necesita la clave de la API de Claude.
    En local normalmente no está configurada (se quitó por seguridad), así que
    se salta el job sin llenar la consola de errores."""
    return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())


def _generar_y_guardar_una_vez() -> bool:
    """Devuelve True si se generó y guardó una noticia; False si se omitió o falló."""
    if not _hay_api_key():
        print("noticias_scheduler: ANTHROPIC_API_KEY no configurada, se omite la noticia diaria.")
        return False
    try:
        payload = generar_noticia_diaria()
        guardar_noticia(payload)
        print(f"noticias_scheduler: noticia generada y guardada correctamente ({payload['fecha']}).")
        return True
    except Exception as e:
        # El generador de noticias es opcional: si la API key es invalida o hay un
        # problema de red, se omite en silencio (una sola linea, sin traceback).
        # El panel y el resto de la app funcionan igual.
        resumen = str(e).split("\n")[0][:120]
        print(f"noticias_scheduler: se omite la noticia diaria (motivo: {resumen}).")
        return False


def _segundos_hasta_medianoche() -> float:
    ahora = datetime.now()
    manana = (ahora + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    return (manana - ahora).total_seconds()


def _loop_diario():
    while True:
        # Intentar generar la noticia de hoy si aún no existe.
        if not existe_noticia_hoy():
            _generar_y_guardar_una_vez()

        # Si ya hay noticia de hoy: dormir hasta pasada la medianoche.
        # Si todavía falta (falló o no hay API key): reintentar en unas horas,
        #   pero nunca más tarde de la próxima medianoche.
        if existe_noticia_hoy():
            espera = _segundos_hasta_medianoche()
        else:
            espera = min(SEGUNDOS_REINTENTO, _segundos_hasta_medianoche())
        time.sleep(max(espera, 60))


def iniciar_scheduler_noticias():
    """Arranca el job diario en un hilo de fondo. Llamar una sola vez al iniciar la app."""
    hilo = threading.Thread(target=_loop_diario, daemon=True)
    hilo.start()
    return hilo
