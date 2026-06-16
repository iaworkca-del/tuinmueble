import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
BRANDING_FILE = DATA_DIR / "branding.json"
LOGO_PATH = BASE_DIR / "static" / "logo.png"

DEFAULTS = {
    "nombre_agencia": "Mi Propiedad",
    "color_primario": "#1a3a5c",
    "color_secundario": "#c8a45a",
    "nombre_agente": "",
    "telefono_agente": "",
    "email_agente": "",
}


def get_branding() -> dict:
    data = dict(DEFAULTS)
    if BRANDING_FILE.exists():
        try:
            data.update(json.loads(BRANDING_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return data


def guardar_branding(nuevos: dict) -> dict:
    data = get_branding()
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
