"""
Servicio de generación de noticias/tips inmobiliarios.

- Texto:  Claude (Anthropic) — usa la misma API key del proyecto
- Imagen: Pollinations.ai (gratuito, sin API key)
"""

import os
import time
import uuid
import random
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

import httpx
import anthropic
from dotenv import load_dotenv

from branding import logo_url

load_dotenv()

BASE_DIR = Path(__file__).parent
NOTICIAS_IMG_DIR = BASE_DIR / "static" / "noticias"
NOTICIAS_IMG_DIR.mkdir(parents=True, exist_ok=True)

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1024&height=1024&nologo=true&seed={seed}"

TEMAS_ROTATIVOS = [
    "tendencias actuales del mercado inmobiliario en Venezuela",
    "consejos prácticos para comprar una propiedad en Venezuela en dólares",
    "consejos para vendedores que quieren vender rápido su propiedad en Venezuela",
    "cómo está evolucionando el precio de los alquileres en las principales ciudades venezolanas",
    "qué documentos y pasos legales se necesitan para comprar o vender un inmueble en Venezuela",
    "zonas y ciudades de Venezuela con mayor plusvalía inmobiliaria actualmente",
    "consejos para invertir en bienes raíces en Venezuela en tiempos de inflación",
    "cómo preparar una propiedad para que se venda o alquile más rápido",
]


def _con_reintentos(func, max_intentos: int = 3, base_delay: float = 2.0):
    ultimo_error = None
    for intento in range(max_intentos):
        try:
            return func()
        except Exception as e:
            ultimo_error = e
            delay = base_delay * (2 ** intento) + random.uniform(0, 1)
            print(f"noticias_service: intento {intento + 1}/{max_intentos} falló: {e}. Reintentando en {delay:.1f}s")
            time.sleep(delay)
    raise RuntimeError(f"No se pudo completar tras {max_intentos} intentos. Último error: {ultimo_error}")


def generar_texto_noticia(tema: str = None) -> dict:
    """Genera título, resumen y contenido de un tip/noticia inmobiliaria con Claude."""
    tema = tema or random.choice(TEMAS_ROTATIVOS)
    fecha_legible = datetime.now().strftime("%d/%m/%Y")

    prompt = f"""Eres un editor experto en el mercado inmobiliario de Venezuela.
Escribe un tip o noticia breve para el blog de una agencia inmobiliaria venezolana, con fecha {fecha_legible}.

TEMA: {tema}

INSTRUCCIONES:
Responde EXACTAMENTE con este formato, sin texto adicional fuera de los marcadores:

[TITULO]
Un título corto, atractivo y específico (máx. 12 palabras), sin comillas.
[/TITULO]

[RESUMEN]
Un resumen de 1 a 2 frases (máx. 220 caracteres) que enganche al lector.
[/RESUMEN]

[CONTENIDO]
El desarrollo completo del tip/noticia (200-280 palabras), en español neutro de Venezuela,
con datos concretos y consejos accionables. Sin encabezados ni markdown, solo párrafos de texto plano.
[/CONTENIDO]

[PROMPT_IMAGEN]
Una descripción en inglés, breve (máx. 40 palabras), de una imagen fotorrealista y profesional
que ilustre este tip/noticia inmobiliaria (por ejemplo: una vivienda, un vecindario, una firma de
documentos, un gráfico de mercado). No incluyas texto ni letras en la imagen descrita.
[/PROMPT_IMAGEN]"""

    def _llamar():
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    texto = _con_reintentos(_llamar)

    return {
        "titulo": _extraer_bloque(texto, "TITULO") or "Tip inmobiliario del día",
        "resumen": _extraer_bloque(texto, "RESUMEN"),
        "contenido": _extraer_bloque(texto, "CONTENIDO"),
        "prompt_imagen": _extraer_bloque(texto, "PROMPT_IMAGEN")
        or "A modern, photorealistic Venezuelan residential neighborhood at golden hour",
    }


def _extraer_bloque(texto: str, marcador: str) -> str:
    inicio = texto.find(f"[{marcador}]")
    fin = texto.find(f"[/{marcador}]")
    if inicio == -1 or fin == -1:
        return ""
    return texto[inicio + len(marcador) + 2: fin].strip()


def generar_imagen_noticia(prompt_imagen: str) -> str:
    """Genera una imagen con Pollinations.ai (gratuito, sin API key) y la guarda en static/noticias."""

    prompt_final = (
        f"{prompt_imagen}, professional photography, high quality, natural lighting, "
        f"real estate editorial style, no text or letters in the image"
    )

    url = POLLINATIONS_URL.format(
        prompt=quote(prompt_final, safe=""),
        seed=random.randint(1, 999999),
    )

    def _llamar():
        resp = httpx.get(url, timeout=60, follow_redirects=True)
        if resp.status_code != 200:
            raise RuntimeError(f"Pollinations devolvió status {resp.status_code}")
        if len(resp.content) < 1000:
            raise RuntimeError("Pollinations devolvió una respuesta demasiado pequeña")
        return resp.content

    datos_imagen = _con_reintentos(_llamar, max_intentos=3, base_delay=3.0)

    nombre = f"noticia_{uuid.uuid4().hex}.jpg"
    destino = NOTICIAS_IMG_DIR / nombre
    with destino.open("wb") as f:
        f.write(datos_imagen)

    return f"/static/noticias/{nombre}"


def generar_noticia_diaria(tema: str = None) -> dict:
    """
    Orquesta la generación completa de una noticia/tip:
    (a) texto con Claude, (b) imagen con Pollinations.ai, (c) devuelve el payload.
    """
    contenido = generar_texto_noticia(tema)
    imagen_url = None
    imagen_es_logo = False
    try:
        imagen_url = generar_imagen_noticia(contenido["prompt_imagen"])
    except Exception as e:
        print(f"noticias_service: no se pudo generar la imagen: {e}")
        imagen_url = logo_url() or None
        imagen_es_logo = bool(imagen_url)

    return {
        "titulo": contenido["titulo"],
        "resumen": contenido["resumen"],
        "contenido": contenido["contenido"],
        "imagen_url": imagen_url,
        "imagen_es_logo": imagen_es_logo,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "creado_en": datetime.now().isoformat(timespec="seconds"),
    }
