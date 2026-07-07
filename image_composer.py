import uuid
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from branding import get_branding, hex_to_rgb

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
LOGO_PATH = BASE_DIR / "static" / "logo.png"

SIZE = 1080

FONTS_DIR = BASE_DIR / "static" / "fonts"

def _obtener_fuente(size: int, bold: bool = False):
    """Obtiene fuente con las Poppins del proyecto como prioridad."""
    project_fonts = [
        str(FONTS_DIR / ("Poppins-Bold.ttf" if bold else "Poppins-SemiBold.ttf")),
        str(FONTS_DIR / "Poppins-Regular.ttf"),
    ]

    system_fonts = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for ruta in project_fonts + system_fonts:
        try:
            if os.path.exists(ruta):
                return ImageFont.truetype(ruta, size)
        except:
            continue

    return ImageFont.load_default(size=size)

def _num(valor):
    try:
        f = float(valor)
        return str(int(f)) if f.is_integer() else str(f)
    except:
        return str(valor)

def _cargar_cover(foto_path: str, W: int, H: int) -> Image.Image:
    img = Image.open(foto_path).convert("RGBA")
    w, h = img.size
    escala = max(W / w, H / h)
    nw, nh = max(1, int(w * escala)), max(1, int(h * escala))
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - W) // 2
    top = (nh - H) // 2
    return img.crop((left, top, left + W, top + H))

def _guardar(img: Image.Image, prefijo: str) -> str:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    nombre = f"{prefijo}_{uuid.uuid4().hex}.jpg"
    img.convert("RGB").save(str(UPLOAD_DIR / nombre), "JPEG", quality=92)
    return f"/static/uploads/{nombre}"

def _precio_fmt(datos):
    try:
        return f"USD ${float(datos.get('precio', 0)):,.0f}"
    except:
        return f"USD ${datos.get('precio', '')}"

def _icono_cama(draw, x, y, size, color, width=3):
    draw.line([(x, y + size * 0.3), (x, y + size * 0.8)], fill=color, width=width)
    draw.line([(x + size, y + size * 0.5), (x + size, y + size * 0.8)], fill=color, width=width)
    draw.line([(x, y + size * 0.5), (x + size, y + size * 0.5)], fill=color, width=width)
    draw.line([(x, y + size * 0.3), (x + size * 0.4, y + size * 0.3)], fill=color, width=width)

def _icono_bano(draw, x, y, size, color, width=3):
    top = y + size * 0.4
    draw.line([(x + size * 0.1, top), (x + size * 0.1, y + size * 0.8)], fill=color, width=width)
    draw.line([(x + size * 0.9, top), (x + size * 0.9, y + size * 0.8)], fill=color, width=width)
    draw.arc([x + size * 0.1, top, x + size * 0.9, y + size * 0.8], 0, 180, fill=color, width=width)
    draw.line([(x + size * 0.1, top), (x + size * 0.9, top)], fill=color, width=width)

def _icono_area(draw, x, y, size, color, width=3):
    draw.rectangle([x + size * 0.15, y + size * 0.2, x + size * 0.85, y + size * 0.8], outline=color, width=width)
    draw.line([(x + size * 0.15, y + size * 0.5), (x + size * 0.3, y + size * 0.5)], fill=color, width=width)

def _icono_auto(draw, x, y, size, color, width=3):
    base = y + size * 0.6
    draw.line([(x + size * 0.2, base), (x + size * 0.8, base)], fill=color, width=width)
    draw.line([(x + size * 0.25, base), (x + size * 0.35, y + size * 0.3)], fill=color, width=width)
    draw.line([(x + size * 0.35, y + size * 0.3), (x + size * 0.65, y + size * 0.3)], fill=color, width=width)
    draw.line([(x + size * 0.65, y + size * 0.3), (x + size * 0.75, base)], fill=color, width=width)
    r = size * 0.08
    draw.ellipse([x + size * 0.3 - r, base - r, x + size * 0.3 + r, base + r], outline=color, width=width)
    draw.ellipse([x + size * 0.7 - r, base - r, x + size * 0.7 + r, base + r], outline=color, width=width)

def _componer_clasica(img, datos, branding, dorado):
    W, H = img.size
    PAD = 50
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    franja_top = Image.new("RGBA", (W, 160), (0, 0, 0, 0))
    dt = ImageDraw.Draw(franja_top)
    for y in range(160):
        alpha = int(160 * (1 - y / 160))
        dt.rectangle([(0, y), (W, y + 1)], fill=(0, 0, 0, alpha))
    overlay.paste(franja_top, (0, 0))
    FRANJA_H = 420
    franja_bot = Image.new("RGBA", (W, FRANJA_H), (0, 0, 0, 0))
    db = ImageDraw.Draw(franja_bot)
    for y in range(FRANJA_H):
        alpha = int(140 * (1 - y / FRANJA_H))
        db.rectangle([(0, y), (W, y + 1)], fill=(0, 0, 0, alpha))
    overlay.paste(franja_bot, (0, H - FRANJA_H))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    if LOGO_PATH.exists():
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo.thumbnail((120, 80), Image.LANCZOS)
            img.paste(logo, (PAD, 30), logo)
        except:
            draw.text((PAD, 30), branding["nombre_agencia"], font=_obtener_fuente(42, bold=True), fill=(255, 255, 255))
    else:
        draw.text((PAD, 30), branding["nombre_agencia"], font=_obtener_fuente(42, bold=True), fill=(255, 255, 255))
    etiqueta = f"{datos.get('tipo_propiedad', '')} en {datos.get('operacion', '')}"
    f_et = _obtener_fuente(38, bold=True)
    et_w = draw.textlength(etiqueta, font=f_et)
    draw.text((W - PAD - et_w, 45), etiqueta, font=f_et, fill=dorado)
    y_precio = H - FRANJA_H + 60
    draw.text((PAD, y_precio), _precio_fmt(datos), font=_obtener_fuente(62, bold=True), fill=(255, 255, 255))
    ubicacion = f"{datos.get('direccion', '')}, {datos.get('ciudad_estado', '')}"
    if len(ubicacion) > 55:
        ubicacion = ubicacion[:52] + " ..."
    y_ubic = y_precio + 80
    draw.text((PAD, y_ubic), ubicacion, font=_obtener_fuente(28), fill=(200, 200, 200))
    y_linea = y_ubic + 42
    draw.rectangle([(PAD, y_linea), (W - PAD, y_linea + 4)], fill=dorado)
    y_metricas = y_linea + 18
    icon_size = 36
    metricas = []
    if datos.get("habitaciones"):
        metricas.append(("cama", f"{datos['habitaciones']} Hab"))
    if datos.get("banos"):
        metricas.append(("bano", f"{datos['banos']} Baños"))
    if datos.get("metros_construidos"):
        metricas.append(("area", f"{_num(datos['metros_construidos'])} m²"))
    if datos.get("estacionamientos"):
        metricas.append(("auto", f"{datos['estacionamientos']} Estacionamiento"))
    icon_map = {"cama": _icono_cama, "bano": _icono_bano, "area": _icono_area, "auto": _icono_auto}
    f_met = _obtener_fuente(28, bold=True)
    total_w = 0
    for icon_type, text in metricas:
        total_w += icon_size + 10 + draw.textlength(text, font=f_met) + 30
    total_w -= 30
    x_m = PAD
    if total_w > W - 2 * PAD:
        f_met = _obtener_fuente(24, bold=True)
    for icon_type, text in metricas:
        icon_map[icon_type](draw, x_m, y_metricas, icon_size, dorado, width=3)
        draw.text((x_m + icon_size + 10, y_metricas + 4), text, font=f_met, fill=(255, 255, 255))
        x_m += icon_size + 10 + int(draw.textlength(text, font=f_met)) + 30
    y_agente = H - 100
    draw.text((PAD, y_agente), datos.get("nombre_agente", ""), font=_obtener_fuente(32, bold=True), fill=dorado)
    draw.text((PAD, y_agente + 38), datos.get("telefono_agente", ""), font=_obtener_fuente(28), fill=(255, 255, 255))
    return img

def _componer_moderna(img, datos, branding, dorado):
    return _componer_clasica(img, datos, branding, dorado)

def _componer_elegante(img, datos, branding, dorado):
    return _componer_clasica(img, datos, branding, dorado)

def _componer_impacto(img, datos, branding, dorado):
    return _componer_clasica(img, datos, branding, dorado)

def _componer_original(img, datos, branding, dorado):
    return _componer_clasica(img, datos, branding, dorado)

_PLANTILLAS = {
    "original": _componer_original,
    "clasica": _componer_clasica,
    "elegante": _componer_elegante,
    "moderna": _componer_moderna,
    "impacto": _componer_impacto,
}

def _componer(img: Image.Image, datos: dict, bottom_safe: int = 0) -> Image.Image:
    branding = get_branding()
    dorado = hex_to_rgb(branding["color_secundario"])
    plantilla = branding.get("plantilla", "clasica")
    fn = _PLANTILLAS.get(plantilla, _componer_clasica)
    return fn(img, datos, branding, dorado)

def componer_portada(foto_path: str, datos: dict) -> str:
    img = _cargar_cover(foto_path, SIZE, int(SIZE * 3 / 4))
    img = _componer(img, datos, bottom_safe=0)
    return _guardar(img, "compuesta")

def componer_stories(foto_path: str, datos: dict) -> str:
    img = _cargar_cover(foto_path, 1080, 1920)
    img = _componer(img, datos, bottom_safe=190)
    return _guardar(img, "stories")

def componer_overlay_extras(extras_paths: list, datos: dict) -> list:
    urls = []
    for ruta in (extras_paths or []):
        if ruta and Path(ruta).exists():
            img = _cargar_cover(ruta, SIZE, int(SIZE * 3 / 4))
            img = _componer(img, datos, bottom_safe=0)
            urls.append(_guardar(img, "extra"))
    return urls

def componer_collage(portada_path: str, extras_paths: list, datos: dict) -> str:
    branding = get_branding()
    dorado = hex_to_rgb(branding["color_secundario"])
    rutas = [r for r in ([portada_path] + list(extras_paths or [])) if r and Path(r).exists()][:4]
    if not rutas:
        return ""
    COL_H = int(SIZE * 3 / 4)
    canvas = Image.new("RGBA", (SIZE, COL_H), (255, 255, 255, 255))
    g = 6
    def pega(ruta, x, y, bw, bh):
        canvas.paste(_cargar_cover(ruta, bw, bh), (x, y))
    n = len(rutas)
    if n == 1:
        pega(rutas[0], 0, 0, SIZE, COL_H)
    elif n == 2:
        cw = (SIZE - g) // 2
        pega(rutas[0], 0, 0, cw, COL_H)
        pega(rutas[1], cw + g, 0, SIZE - cw - g, COL_H)
    elif n == 3:
        cw = (SIZE - g) // 2
        ch = (COL_H - g) // 2
        pega(rutas[0], 0, 0, cw, COL_H)
        pega(rutas[1], cw + g, 0, SIZE - cw - g, ch)
        pega(rutas[2], cw + g, ch + g, SIZE - cw - g, COL_H - ch - g)
    else:
        cw = (SIZE - g) // 2
        ch = (COL_H - g) // 2
        pega(rutas[0], 0, 0, cw, ch)
        pega(rutas[1], cw + g, 0, SIZE - cw - g, ch)
        pega(rutas[2], 0, ch + g, cw, COL_H - ch - g)
        pega(rutas[3], cw + g, ch + g, SIZE - cw - g, COL_H - ch - g)
    franja_h = 150
    overlay = Image.new("RGBA", (SIZE, COL_H), (0, 0, 0, 0))
    franja = Image.new("RGBA", (SIZE, franja_h), (0, 0, 0, 0))
    df = ImageDraw.Draw(franja)
    for y in range(franja_h):
        alpha = int(200 * ((franja_h - y) / franja_h))
        df.rectangle([(0, y), (SIZE, y + 1)], fill=(0, 0, 0, alpha))
    overlay.paste(franja, (0, COL_H - franja_h))
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)
    PAD = 40
    draw.text((PAD, COL_H - 100), _precio_fmt(datos), font=_obtener_fuente(62, bold=True), fill=(255, 255, 255))
    draw.text((PAD, COL_H - 45), datos.get("nombre_agente", ""), font=_obtener_fuente(32, bold=True), fill=dorado)
    return _guardar(canvas, "collage")
