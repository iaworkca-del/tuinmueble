"""
Job/cron diario para la sección "Tips y Noticias Inmobiliarias".

Cada 24 horas (y una vez al iniciar la app, si hoy no se ha generado nada):
  (a) llama a Claude para generar el texto de la noticia/tip,
  (b) llama a Pollinations.ai para generar la imagen relacionada,
  (c) guarda el resultado en la base de datos (tabla `noticias`, se acumula, no reemplaza),
  (d) el sitio público lee siempre la última noticia disponible en /db.listar_noticias().
"""

import threading
import time
import traceback
from datetime import datetime, timedelta

from db import guardar_noticia, existe_noticia_hoy
from gemini_service import generar_noticia_diaria

SEGUNDOS_UN_DIA = 24 * 60 * 60


def _generar_y_guardar_una_vez():
    try:
        payload = generar_noticia_diaria()
        guardar_noticia(payload)
        print(f"noticias_scheduler: noticia generada y guardada correctamente ({payload['fecha']}).")
    except Exception as e:
        print(f"noticias_scheduler: ERROR generando la noticia diaria: {e}")
        traceback.print_exc()


def _segundos_hasta_medianoche() -> float:
    ahora = datetime.now()
    manana = (ahora + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    return (manana - ahora).total_seconds()


def _loop_diario():
    # Si hoy todavía no hay noticia generada, generarla ya (sin esperar a medianoche).
    if not existe_noticia_hoy():
        _generar_y_guardar_una_vez()

    while True:
        time.sleep(_segundos_hasta_medianoche())
        if not existe_noticia_hoy():
            _generar_y_guardar_una_vez()


def iniciar_scheduler_noticias():
    """Arranca el job diario en un hilo de fondo. Llamar una sola vez al iniciar la app."""
    hilo = threading.Thread(target=_loop_diario, daemon=True)
    hilo.start()
    return hilo
