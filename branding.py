import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
BRANDING_FILE = DATA_DIR / "branding.json"
LOGO_PATH = BASE_DIR / "static" / "logo.png"
FONDO_PATH = BASE_DIR / "static" / "fondo.jpg"

DEFAULTS = {
    "nombre_agencia": "Mi Propiedad",
    "color_primario": "#1a3a5c",
    "color_secundario": "#b1b65d",
    "nombre_agente": "",
    "telefono_agente": "",
    "email_agente": "",
    "fondo_opacidad": "30",  # visibilidad del fondo 0-100 (0=tenue, 100=muy visible)
    "plantilla": "clasica",  # clasica, elegante, moderna, impacto
}


def _cargar_guardado() -> dict:
    data = dict(DEFAULTS)
    if BRANDING_FILE.exists():
        try:
            guardado = json.loads(BRANDING_FILE.read_text(encoding="utf-8"))
            for clave in DEFAULTS:
                if clave in guardado:
                    data[clave] = guardado[clave]
        except Exception:
            pass
    return data


def fondo_url() -> str:
    """URL del fondo con cache-bust, o '' si no hay fondo."""
    if FONDO_PATH.exists():
        try:
            return f"/static/fondo.jpg?v={int(FONDO_PATH.stat().st_mtime)}"
        except Exception:
            return "/static/fondo.jpg"
    return ""


def get_branding() -> dict:
    data = _cargar_guardado()
    data["fondo"] = fondo_url()  # campo calculado (no se persiste)
    return data


def guardar_branding(nuevos: dict) -> dict:
    data = _cargar_guardado()
    for clave in DEFAULTS:
        valor = nuevos.get(clave)
        if valor is not None and str(valor).strip() != "":
            data[clave] = valor
    BRANDING_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return data


def hex_to_rgb(h: str) -> tuple:
    h = (h or "").lstrip("#")
    if len(h) != 6:
        return (26, 58, 92)
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (26, 58, 92)


def logo_existe() -> bool:
    return LOGO_PATH.exists()


def fondo_existe() -> bool:
    return FONDO_PATH.exists()
