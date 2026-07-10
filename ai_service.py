import os
import time
import anthropic
from dotenv import load_dotenv

from hashtags import construir_hashtags

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

TONOS = {
    "Formal": "Tono formal, profesional y corporativo. Lenguaje serio y respetuoso.",
    "Cercano": "Tono cercano, cálido y conversacional, que conecte emocionalmente con el cliente.",
    "Lujo": "Tono de lujo, sofisticado y aspiracional. Resalta exclusividad, estatus y distinción.",
}

LONGITUDES = {
    "Corta": {"desc": "unas 100 palabras", "social": "breve, directo"},
    "Media": {"desc": "unas 200 palabras", "social": "de longitud media"},
    "Larga": {"desc": "unas 300 palabras", "social": "más extenso y detallado"},
}


def generar_contenido(datos: dict, tono: str = "Cercano", longitud: str = "Media") -> dict:
    espacios = ", ".join(datos.get("espacios", [])) or "ninguno indicado"
    instr_tono = TONOS.get(tono, TONOS["Cercano"])
    cfg_long = LONGITUDES.get(longitud, LONGITUDES["Media"])

    hashtags = " ".join(construir_hashtags(
        datos.get("ciudad_estado", ""),
        datos.get("tipo_propiedad", ""),
        datos.get("operacion", ""),
    ))

    prompt = f"""Eres un experto en marketing inmobiliario en Venezuela.
Genera contenido profesional para la siguiente propiedad.

ESTILO: {instr_tono}

DATOS DE LA PROPIEDAD:
- Tipo: {datos['tipo_propiedad']}
- Operación: {datos['operacion']}
- Ubicación: {datos['direccion']}, {datos['ciudad_estado']}
- Precio: USD ${datos['precio']:,}
- Habitaciones: {datos.get('habitaciones', 'N/A')}
- Baños: {datos.get('banos', 'N/A')}
- Metros construidos: {datos.get('metros_construidos', 'N/A')} m²
- Metros de terreno: {datos.get('metros_terreno', 'N/A')} m²
- Estacionamientos: {datos.get('estacionamientos', 'N/A')}
- Espacios y amenidades: {espacios}
- Notas del agente: {datos.get('descripcion_agente', '')}
- Agente: {datos['nombre_agente']} | {datos['telefono_agente']}

INSTRUCCIONES:
Genera EXACTAMENTE cuatro secciones separadas por marcadores. No agregues texto fuera de los marcadores.

[DESCRIPCION]
Descripción profesional y atractiva ({cfg_long['desc']}) para portales inmobiliarios. Destaca los puntos fuertes y la ubicación. Termina con los datos del agente de contacto.
[/DESCRIPCION]

[INSTAGRAM]
Copy optimizado para Instagram ({cfg_long['social']}), con emojis estratégicos y lenguaje atractivo. Al final incluye EXACTAMENTE esta línea de hashtags tal cual:
{hashtags}
[/INSTAGRAM]

[WHATSAPP]
Mensaje para enviar por WhatsApp ({cfg_long['social']}). Directo, con emojis, fácil de reenviar a clientes. Incluye precio, datos clave y el teléfono del agente para contacto inmediato.
[/WHATSAPP]

[FACEBOOK]
Publicación para Facebook Marketplace. Primero una línea de TÍTULO corto y llamativo, luego el cuerpo orientado a venta directa con los datos clave y llamado a la acción. Sin hashtags.
[/FACEBOOK]"""

    # Reintentos exponenciales con jitter ante fallos temporales (rate limits, timeouts)
    import random

    ultimo_error = None
    response = None
    max_attempts = 5
    base_delay = 1.0

    for intento in range(max_attempts):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            break
        except Exception as e:
            ultimo_error = e
            msg = str(e).lower()
            # Errores 403/forbidden no son recuperables: devolver mensaje claro
            if "403" in msg or "forbidden" in msg or "request not allowed" in msg:
                raise RuntimeError(
                    "El servicio de IA devolvió 403 (forbidden).\n"
                    "Verifica que la variable de entorno `ANTHROPIC_API_KEY` esté correcta, "
                    "que la clave tenga permisos para el modelo solicitado y que la cuenta/plan esté activa. "
                    f"Detalle: {e}"
                )
            # Si es un error recuperable, esperar con backoff exponencial + jitter
            delay = base_delay * (2 ** intento)
            jitter = random.uniform(0, 0.5 * delay)
            total_sleep = delay + jitter
            print(f"ai_service: intento {intento+1}/{max_attempts} falló: {e}. reintentando en {total_sleep:.1f}s")
            time.sleep(total_sleep)

    if response is None:
        raise RuntimeError(
            "El servicio de IA está temporalmente ocupado. Intenta generar de nuevo en unos segundos. "
            f"(detalle: {ultimo_error})"
        )

    texto = response.content[0].text

    return {
        "descripcion": _extraer_bloque(texto, "DESCRIPCION"),
        "instagram": _extraer_bloque(texto, "INSTAGRAM"),
        "whatsapp": _extraer_bloque(texto, "WHATSAPP"),
        "facebook": _extraer_bloque(texto, "FACEBOOK"),
    }


def _extraer_bloque(texto: str, marcador: str) -> str:
    inicio = texto.find(f"[{marcador}]")
    fin = texto.find(f"[/{marcador}]")
    if inicio == -1 or fin == -1:
        return texto.strip()
    return texto[inicio + len(marcador) + 2 : fin].strip()
