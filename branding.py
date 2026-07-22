import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
BRANDING_FILE = DATA_DIR / "branding.json"
LOGO_PATH = BASE_DIR / "static" / "logo.png"
FONDO_PATH = BASE_DIR / "static" / "fondo.jpg"

# Estas carpetas viven dentro de data/ (el Volume persistente de Railway),
# NO en static/, porque son contenido subido por usuarios en producción.
# Si vivieran en static/, cada deploy las resetearía al estado de git y se
# perderían los logos/fondos/plantillas subidos directamente en producción.
LOGOS_DIR = DATA_DIR / "logos"
FONDOS_DIR = DATA_DIR / "fondos"
PLANTILLAS_DIR = DATA_DIR / "plantillas_custom"
LOGOS_DIR.mkdir(exist_ok=True)
FONDOS_DIR.mkdir(exist_ok=True)
PLANTILLAS_DIR.mkdir(exist_ok=True)

DEFAULTS = {
    "nombre_agencia": "Mi Propiedad",
    "color_primario": "#1a3a5c",
    "color_secundario": "#b1b65d",
    "nombre_agente": "",
    "telefono_agente": "",
    "email_agente": "",
    "fondo_opacidad": "30",
    "plantilla": "clasica",
    "franja_opacidad": "50",
    "franja_tamano": "20",
    "eslogan": "Encuentra el hogar de tus sueños",
    "descripcion_agencia": (
        "Somos una agencia inmobiliaria comprometida con ayudarte a encontrar "
        "la propiedad ideal. Con años de experiencia en el mercado, ofrecemos "
        "un servicio personalizado, transparente y cercano en cada paso del "
        "proceso de compra, venta o alquiler."
    ),
    "servicio_1_titulo": "Venta de propiedades",
    "servicio_1_desc": "Te acompañamos en todo el proceso de venta, desde la valoración hasta el cierre del negocio.",
    "servicio_2_titulo": "Alquiler de inmuebles",
    "servicio_2_desc": "Encontramos el inquilino o la propiedad ideal para ti, con contratos claros y seguros.",
    "servicio_3_titulo": "Asesoría inmobiliaria",
    "servicio_3_desc": "Te asesoramos con información del mercado para que tomes la mejor decisión de inversión.",
    "instagram": "",
    "facebook": "",
    "x": "",
}


def _branding_file(agente: dict = None) -> Path:
    if agente:
        agente_file = DATA_DIR / f"branding_agente_{agente['id']}.json"
        if agente_file.exists():
            return agente_file
        cuenta_id = agente.get("cuenta_id")
        if cuenta_id:
            cuenta_file = DATA_DIR / f"branding_cuenta_{cuenta_id}.json"
            if cuenta_file.exists():
                return cuenta_file
    return BRANDING_FILE


def _branding_file_para_guardar(agente: dict = None, nivel: str = "cuenta") -> Path:
    if not agente:
        return BRANDING_FILE
    if nivel == "agente":
        return DATA_DIR / f"branding_agente_{agente['id']}.json"
    cuenta_id = agente.get("cuenta_id")
    if cuenta_id:
        return DATA_DIR / f"branding_cuenta_{cuenta_id}.json"
    return BRANDING_FILE


def _cargar_guardado(agente: dict = None) -> dict:
    data = dict(DEFAULTS)
    if BRANDING_FILE.exists():
        try:
            guardado = json.loads(BRANDING_FILE.read_text(encoding="utf-8"))
            for clave in DEFAULTS:
                if clave in guardado:
                    data[clave] = guardado[clave]
        except Exception:
            pass
    if agente:
        cuenta_id = agente.get("cuenta_id")
        if cuenta_id:
            cuenta_file = DATA_DIR / f"branding_cuenta_{cuenta_id}.json"
            if cuenta_file.exists():
                try:
                    guardado = json.loads(cuenta_file.read_text(encoding="utf-8"))
                    for clave in DEFAULTS:
                        if clave in guardado:
                            data[clave] = guardado[clave]
                except Exception:
                    pass
        agente_file = DATA_DIR / f"branding_agente_{agente['id']}.json"
        if agente_file.exists():
            try:
                guardado = json.loads(agente_file.read_text(encoding="utf-8"))
                for clave in DEFAULTS:
                    if clave in guardado:
                        data[clave] = guardado[clave]
            except Exception:
                pass
    return data


def _logo_path(agente: dict = None) -> Path:
    if agente:
        p = LOGOS_DIR / f"agente_{agente['id']}.png"
        if p.exists():
            return p
        cuenta_id = agente.get("cuenta_id")
        if cuenta_id:
            p = LOGOS_DIR / f"cuenta_{cuenta_id}.png"
            if p.exists():
                return p
    return LOGO_PATH


def _fondo_path(agente: dict = None) -> Path:
    if agente:
        p = FONDOS_DIR / f"agente_{agente['id']}.jpg"
        if p.exists():
            return p
        cuenta_id = agente.get("cuenta_id")
        if cuenta_id:
            p = FONDOS_DIR / f"cuenta_{cuenta_id}.jpg"
            if p.exists():
                return p
    return FONDO_PATH


def _plantilla_custom_path(agente: dict = None) -> Path:
    if agente:
        p = PLANTILLAS_DIR / f"agente_{agente['id']}.png"
        if p.exists():
            return p
        cuenta_id = agente.get("cuenta_id")
        if cuenta_id:
            p = PLANTILLAS_DIR / f"cuenta_{cuenta_id}.png"
            if p.exists():
                return p
    return PLANTILLAS_DIR / "__inexistente__.png"


def plantilla_custom_existe(agente: dict = None) -> bool:
    return _plantilla_custom_path(agente).exists()


def _url_publica(path: Path) -> str:
    """URL pública bajo /static/... de un archivo, sin importar si vive
    físicamente en static/ (assets de fábrica) o en data/ (contenido de
    usuario en el Volume persistente) — ambos se sirven bajo /static/...
    gracias a los mounts específicos en main.py."""
    for carpeta, prefijo in (
        (LOGOS_DIR, "static/logos"),
        (FONDOS_DIR, "static/fondos"),
        (PLANTILLAS_DIR, "static/plantillas_custom"),
    ):
        try:
            rel = path.relative_to(carpeta)
            return f"/{prefijo}/{str(rel).replace(chr(92), '/')}?v={int(path.stat().st_mtime)}"
        except ValueError:
            continue
    rel = path.relative_to(BASE_DIR)
    return f"/{str(rel).replace(chr(92), '/')}?v={int(path.stat().st_mtime)}"


def plantilla_custom_url(agente: dict = None) -> str:
    p = _plantilla_custom_path(agente)
    if p.exists():
        try:
            return _url_publica(p)
        except Exception:
            return ""
    return ""


def plantilla_custom_path_absoluto(agente: dict = None) -> Path:
    return _plantilla_custom_path(agente)


def plantilla_custom_path_para_guardar(agente: dict = None, nivel: str = "cuenta") -> Path:
    if not agente:
        return PLANTILLAS_DIR / "default.png"
    if nivel == "agente":
        return PLANTILLAS_DIR / f"agente_{agente['id']}.png"
    cuenta_id = agente.get("cuenta_id")
    if cuenta_id:
        return PLANTILLAS_DIR / f"cuenta_{cuenta_id}.png"
    return PLANTILLAS_DIR / "default.png"


def fondo_url(agente: dict = None) -> str:
    fp = _fondo_path(agente)
    if fp.exists():
        try:
            return _url_publica(fp)
        except Exception:
            return ""
    return ""


def get_branding(agente: dict = None) -> dict:
    data = _cargar_guardado(agente)
    data["fondo"] = fondo_url(agente)
    data["logo"] = logo_url(agente)
    return data


def tiene_branding_cuenta(cuenta_id: int) -> bool:
    """True si la cuenta ya guardó su propio branding (branding_cuenta_X.json)."""
    if not cuenta_id:
        return False
    return (DATA_DIR / f"branding_cuenta_{cuenta_id}.json").exists()


def guardar_branding(nuevos: dict, agente: dict = None, nivel: str = "cuenta",
                     campos_limpiables: set = None) -> dict:
    campos_limpiables = campos_limpiables or set()
    target = _branding_file_para_guardar(agente, nivel)
    if target.exists():
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    else:
        data = {}
    for clave in DEFAULTS:
        if clave not in nuevos:
            continue
        valor = nuevos.get(clave)
        # Los campos "limpiables" se guardan aunque queden vacíos (para poder borrarlos).
        if clave in campos_limpiables:
            if valor is not None:
                data[clave] = str(valor).strip()
        elif valor is not None and str(valor).strip() != "":
            data[clave] = valor
    target.write_text(
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


def logo_existe(agente: dict = None) -> bool:
    return _logo_path(agente).exists()


def logo_url(agente: dict = None) -> str:
    lp = _logo_path(agente)
    if lp.exists():
        try:
            return _url_publica(lp)
        except Exception:
            return ""
    return ""


def logo_path_absoluto(agente: dict = None) -> Path:
    return _logo_path(agente)


def logo_path_para_guardar(agente: dict = None, nivel: str = "cuenta") -> Path:
    if not agente:
        return LOGO_PATH
    if nivel == "agente":
        return LOGOS_DIR / f"agente_{agente['id']}.png"
    cuenta_id = agente.get("cuenta_id")
    if cuenta_id:
        return LOGOS_DIR / f"cuenta_{cuenta_id}.png"
    return LOGO_PATH


def fondo_path_para_guardar(agente: dict = None, nivel: str = "cuenta") -> Path:
    if not agente:
        return FONDO_PATH
    if nivel == "agente":
        return FONDOS_DIR / f"agente_{agente['id']}.jpg"
    cuenta_id = agente.get("cuenta_id")
    if cuenta_id:
        return FONDOS_DIR / f"cuenta_{cuenta_id}.jpg"
    return FONDO_PATH


def fondo_existe(agente: dict = None) -> bool:
    return _fondo_path(agente).exists()
