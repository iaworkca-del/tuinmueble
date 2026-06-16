import os
from pathlib import Path
from contextlib import ExitStack

import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.upload-post.com/api/upload_photos"


def publicar_instagram(imagenes_paths, titulo: str) -> dict:
    """Sube una o varias imágenes a Instagram vía la API de Upload Post.

    `imagenes_paths` puede ser una ruta (str) o una lista de rutas (carrusel).
    Devuelve un dict: {success: bool, message: str, url: str|None}
    """
    api_key = os.getenv("UPLOADPOST_API_KEY")
    user = os.getenv("UPLOADPOST_USER")

    if not api_key:
        return {"success": False, "message": "Falta UPLOADPOST_API_KEY en el archivo .env"}
    if not user:
        return {"success": False, "message": "Falta UPLOADPOST_USER en el archivo .env"}

    if isinstance(imagenes_paths, str):
        imagenes_paths = [imagenes_paths]
    rutas = [p for p in (imagenes_paths or []) if p and Path(p).exists()]
    if not rutas:
        return {"success": False, "message": "No se encontraron imágenes para publicar."}

    headers = {"Authorization": f"Apikey {api_key}"}
    data = {
        "user": user,
        "platform[]": "instagram",
        "title": titulo or "",
    }

    try:
        with ExitStack() as stack:
            files = []
            for ruta in rutas:
                fh = stack.enter_context(open(ruta, "rb"))
                files.append(("photos[]", (Path(ruta).name, fh, "image/jpeg")))
            resp = httpx.post(API_URL, headers=headers, data=data, files=files, timeout=180.0)
    except httpx.TimeoutException:
        return {"success": False, "message": "La publicación tardó demasiado. Verifica en Instagram en unos minutos."}
    except Exception as e:
        return {"success": False, "message": f"Error de conexión con Upload Post: {e}"}

    try:
        body = resp.json()
    except Exception:
        body = {}

    # Éxito
    if resp.status_code == 200 and body.get("success"):
        resultado_ig = (body.get("results") or {}).get("instagram", {})
        if resultado_ig.get("success"):
            return {
                "success": True,
                "message": "¡Publicado en Instagram con éxito!",
                "url": resultado_ig.get("url"),
            }
        if resultado_ig and resultado_ig.get("success") is False:
            return {
                "success": False,
                "message": resultado_ig.get("error", "Instagram rechazó la publicación."),
            }
        # Procesamiento en segundo plano
        if body.get("request_id"):
            return {
                "success": True,
                "message": "Publicación enviada a Instagram. Se está procesando en segundo plano.",
            }
        return {"success": True, "message": "Publicación enviada a Instagram."}

    # Errores
    mensaje = body.get("message") or body.get("error") or f"Error {resp.status_code} al publicar."
    return {"success": False, "message": mensaje}
