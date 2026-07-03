"""
Servicio de generación de contenido con Google Gemini.

CONEXIÓN DE API KEY:
- Este servicio usa la variable de entorno `GEMINI_API_KEY`.
- Ya está configurada como secreto en este proyecto (Replit Secrets).
- Si necesitas cambiarla, ve a la pestaña "Secrets" del proyecto en Replit.
- Puedes generar una clave gratuita en https://aistudio.google.com/apikey

Modelos usados:
- Texto:  "gemini-2.5-flash"        (noticias/tips inmobiliarios)
- Imagen: "gemini-2.5-flash-image" (alias público: "Nano Banana")
"""

import os
import re
import time
import uuid
import random
import base64
from pathlib import Path
from datetime import datetime

from google import genai
from google.genai import types

BASE_DIR = Path(__file__).parent
NOTICIAS_IMG_DIR = BASE_DIR / "static" / "noticias"
NOTICIAS_IMG_DIR.mkdir(parents=True, exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

MODELO_TEXTO = "gemini-2.5-flash"
MODELO_IMAGEN = "gemini-2.5-flash-image"

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


def _cliente() -> genai.Client:
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Falta la variable de entorno GEMINI_API_KEY. "
            "Configúrala en la pestaña Secrets del proyecto."
        )
    return genai.Client(api_key=GEMINI_API_KEY)


def _con_reintentos(func, max_intentos: int = 4, base_delay: float = 1.5):
    """Ejecuta `func` con reintentos exponenciales ante fallos temporales."""
    ultimo_error = None
    for intento in range(max_intentos):
        try:
            return func()
        except Exception as e:
            ultimo_error = e
            msg = str(e).lower()
            if "403" in msg or "forbidden" in msg or "api key" in msg and "invalid" in msg:
                raise RuntimeError(
                    "Gemini devolvió un error de autenticación (403/API key inválida). "
                    f"Verifica GEMINI_API_KEY. Detalle: {e}"
                )
            delay = base_delay * (2 ** intento) + random.uniform(0, 1)
            print(f"gemini_service: intento {intento + 1}/{max_intentos} falló: {e}. Reintentando en {delay:.1f}s")
            time.sleep(delay)
    raise RuntimeError(f"Gemini no respondió tras {max_intentos} intentos. Último error: {ultimo_error}")


def generar_texto_noticia(tema: str = None) -> dict:
    """Genera título, resumen y contenido de un tip/noticia inmobiliaria con Gemini."""
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
        client = _cliente()
        response = client.models.generate_content(
            model=MODELO_TEXTO,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=8192),
        )
        return response.text or ""

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
    """Genera una imagen con Gemini (Nano Banana) y la guarda en static/noticias. Devuelve la URL pública."""

    prompt_final = (
        f"{prompt_imagen}. Fotografía profesional, alta calidad, iluminación natural, "
        f"estilo editorial inmobiliario, sin texto ni letras en la imagen."
    )

    def _llamar():
        client = _cliente()
        response = client.models.generate_content(
            model=MODELO_IMAGEN,
            contents=prompt_final,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )
        if not response.candidates:
            raise RuntimeError("Gemini no devolvió candidatos de imagen.")
        candidato = response.candidates[0]
        if not candidato.content or not candidato.content.parts:
            raise RuntimeError("Gemini no devolvió contenido de imagen.")
        for parte in candidato.content.parts:
            inline = getattr(parte, "inline_data", None)
            if inline and inline.data:
                return inline.data
        raise RuntimeError("Gemini no incluyó datos de imagen en la respuesta.")

    datos_imagen = _con_reintentos(_llamar)

    if isinstance(datos_imagen, str):
        datos_imagen = base64.b64decode(datos_imagen)

    nombre = f"noticia_{uuid.uuid4().hex}.png"
    destino = NOTICIAS_IMG_DIR / nombre
    with destino.open("wb") as f:
        f.write(datos_imagen)

    return f"/static/noticias/{nombre}"


def generar_noticia_diaria(tema: str = None) -> dict:
    """
    Orquesta la generación completa de una noticia/tip:
    (a) texto con Gemini, (b) imagen con Nano Banana, (c) devuelve el payload
    listo para guardar en la base de datos.

    Si falla, propaga la excepción para que el llamador decida cómo manejarlo
    (el llamador debe capturarla y no romper el resto del sitio).
    """
    contenido = generar_texto_noticia(tema)
    imagen_url = None
    try:
        imagen_url = generar_imagen_noticia(contenido["prompt_imagen"])
    except Exception as e:
        print(f"gemini_service: no se pudo generar la imagen de la noticia: {e}")
        imagen_url = None

    return {
        "titulo": contenido["titulo"],
        "resumen": contenido["resumen"],
        "contenido": contenido["contenido"],
        "imagen_url": imagen_url,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "creado_en": datetime.now().isoformat(timespec="seconds"),
    }
