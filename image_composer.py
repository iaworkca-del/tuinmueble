import uuid
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from branding import get_branding, hex_to_rgb, logo_path_absoluto, plantilla_custom_path_absoluto, plantilla_custom_existe

BASE_DIR = Path(__file__).parent
# Contenido subido por usuarios: vive en data/ (Volume persistente de Railway),
# no en static/, para que sobreviva a los deploys.
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
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

def _metricas(datos):
    items = []
    if datos.get("habitaciones"):
        items.append(("cama", f"{datos['habitaciones']} Hab"))
    if datos.get("banos"):
        items.append(("bano", f"{datos['banos']} Baños"))
    if datos.get("metros_construidos"):
        items.append(("area", f"{_num(datos['metros_construidos'])} m²"))
    if datos.get("estacionamientos"):
        n = datos["estacionamientos"]
        palabra = "Estacionamiento" if str(n) == "1" else "Estacionamientos"
        items.append(("auto", f"{n} {palabra}"))
    return items

_ICONOS = {"cama": _icono_cama, "bano": _icono_bano, "area": _icono_area, "auto": _icono_auto}

def _dibujar_iconos_centrado(draw, metricas, x_start, y, max_w, color, tamano_base=26):
    GAP_ICO_TXT, GAP_ENTRE = 10, 30
    icon_size = int(tamano_base * 1.2)
    f_met = _obtener_fuente(tamano_base, bold=True)
    total = sum(icon_size + GAP_ICO_TXT + draw.textlength(t, font=f_met) + GAP_ENTRE for _, t in metricas)
    total -= GAP_ENTRE
    if total > max_w and tamano_base > 18:
        return _dibujar_iconos_centrado(draw, metricas, x_start, y, max_w, color, tamano_base - 4)
    x = x_start
    for nombre_ico, texto in metricas:
        _ICONOS[nombre_ico](draw, x, y, icon_size, color, width=3)
        x += icon_size + GAP_ICO_TXT
        draw.text((x, y - 4), texto, font=f_met, fill=(255, 255, 255))
        x += int(draw.textlength(texto, font=f_met)) + GAP_ENTRE
    return total

def _gradiente(W, H_franja, direccion="abajo", alpha_max=215):
    franja = Image.new("RGBA", (W, H_franja), (0, 0, 0, 0))
    d = ImageDraw.Draw(franja)
    for y in range(H_franja):
        ratio = y / H_franja if direccion == "abajo" else (1 - y / H_franja)
        d.rectangle([(0, y), (W, y + 1)], fill=(0, 0, 0, int(alpha_max * ratio)))
    return franja

def _pegar_logo_simple(img, draw, pad, branding, logo_max=(130, 85)):
    lp = branding.get("_logo_path") or LOGO_PATH
    if Path(lp).exists():
        try:
            logo = Image.open(str(lp)).convert("RGBA")
            logo.thumbnail(logo_max, Image.LANCZOS)
            img.paste(logo, (pad, pad), logo)
            return
        except:
            pass
    draw.text((pad, pad), branding["nombre_agencia"], font=_obtener_fuente(34, bold=True), fill=(255, 255, 255))

def _componer_clasica(img, datos, branding, dorado):
    W, H = img.size
    PAD = 45
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    franja_top = Image.new("RGBA", (W, 120), (0, 0, 0, 0))
    dt = ImageDraw.Draw(franja_top)
    for y in range(120):
        alpha = int(140 * (1 - y / 120))
        dt.rectangle([(0, y), (W, y + 1)], fill=(0, 0, 0, alpha))
    overlay.paste(franja_top, (0, 0))
    franja_pct = max(15, min(40, int(branding.get("franja_tamano", 20)))) / 100
    franja_alpha = int(max(0, min(100, int(branding.get("franja_opacidad", 50)))) * 2.55)
    MARGEN_INFERIOR = int(W * 0.04)
    FRANJA_H = int(W * franja_pct) + MARGEN_INFERIOR
    franja_bot = Image.new("RGBA", (W, FRANJA_H), (0, 0, 0, 0))
    db = ImageDraw.Draw(franja_bot)
    for y in range(FRANJA_H):
        alpha = int(franja_alpha * (1 - y / FRANJA_H))
        db.rectangle([(0, y), (W, y + 1)], fill=(0, 0, 0, alpha))
    overlay.paste(franja_bot, (0, H - FRANJA_H))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    lp = branding.get("_logo_path") or LOGO_PATH
    if Path(lp).exists():
        try:
            logo = Image.open(str(lp)).convert("RGBA")
            logo.thumbnail((150, 100), Image.LANCZOS)
            img.paste(logo, (PAD, 20), logo)
        except:
            draw.text((PAD, 25), branding["nombre_agencia"], font=_obtener_fuente(36, bold=True), fill=(255, 255, 255))
    else:
        draw.text((PAD, 25), branding["nombre_agencia"], font=_obtener_fuente(36, bold=True), fill=(255, 255, 255))
    etiqueta = f"{datos.get('tipo_propiedad', '')} en {datos.get('operacion', '')}"
    f_et = _obtener_fuente(32, bold=True)
    et_w = draw.textlength(etiqueta, font=f_et)
    draw.text((W - PAD - et_w, 38), etiqueta, font=f_et, fill=dorado)
    y_base = H - FRANJA_H + 15
    draw.text((PAD, y_base), _precio_fmt(datos), font=_obtener_fuente(48, bold=True), fill=(255, 255, 255))
    ubicacion = f"{datos.get('direccion', '')}, {datos.get('ciudad_estado', '')}"
    if len(ubicacion) > 50:
        ubicacion = ubicacion[:47] + " ..."
    y_ubic = y_base + 52
    draw.text((PAD, y_ubic), ubicacion, font=_obtener_fuente(22), fill=(200, 200, 200))
    y_linea = y_ubic + 28
    draw.rectangle([(PAD, y_linea), (W - PAD, y_linea + 3)], fill=dorado)
    y_metricas = y_linea + 10
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
    f_met = _obtener_fuente(26, bold=True)
    total_w = 0
    for icon_type, text in metricas:
        total_w += icon_size + 8 + draw.textlength(text, font=f_met) + 25
    total_w -= 25
    x_m = PAD
    if total_w > W - 2 * PAD:
        f_met = _obtener_fuente(22, bold=True)
    for icon_type, text in metricas:
        icon_map[icon_type](draw, x_m, y_metricas, icon_size, dorado, width=4)
        draw.text((x_m + icon_size + 8, y_metricas + 3), text, font=f_met, fill=(255, 255, 255))
        x_m += icon_size + 8 + int(draw.textlength(text, font=f_met)) + 25
    y_agente = y_metricas + icon_size + 8
    f_nombre = _obtener_fuente(26, bold=True)
    f_tel = _obtener_fuente(22)
    nombre = datos.get("nombre_agente", "")
    telefono = datos.get("telefono_agente", "")
    nombre_w = draw.textlength(nombre, font=f_nombre)
    tel_w = draw.textlength(telefono, font=f_tel)
    bg_w = int(max(nombre_w, tel_w)) + 24
    bg_h = 58
    bg = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 120))
    img.paste(Image.alpha_composite(Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0)), bg), (PAD - 12, y_agente - 6), bg)
    draw = ImageDraw.Draw(img)
    draw.text((PAD, y_agente), nombre, font=f_nombre, fill=dorado)
    draw.text((PAD, y_agente + 28), telefono, font=f_tel, fill=(255, 255, 255))
    return img

def _componer_elegante(img, datos, branding, dorado):
    """Minimalista: marco dorado fino, precio grande centrado."""
    W, H = img.size
    PAD = 50
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 70))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    draw.rectangle([(PAD - 10, PAD - 10), (W - PAD + 10, H - PAD + 10)], outline=dorado, width=3)
    _pegar_logo_simple(img, draw, PAD, branding, logo_max=(120, 75))

    precio = _precio_fmt(datos)
    f_precio = _obtener_fuente(66, bold=True)
    pw = draw.textlength(precio, font=f_precio)
    y_centro = int(H * 0.46)
    draw.text(((W - pw) / 2, y_centro), precio, font=f_precio, fill=(255, 255, 255))

    linea_w = min(pw + 80, W - 2 * PAD)
    lx = (W - linea_w) / 2
    y_linea = y_centro + 82
    draw.rectangle([(lx, y_linea), (lx + linea_w, y_linea + 2)], fill=dorado)

    etiqueta = f"{datos.get('tipo_propiedad', '')} en {datos.get('operacion', '')}".upper()
    f_et = _obtener_fuente(28, bold=True)
    tw = draw.textlength(etiqueta, font=f_et)
    draw.text(((W - tw) / 2, y_linea + 14), etiqueta, font=f_et, fill=dorado)

    ubicacion = f"{datos.get('direccion', '')}, {datos.get('ciudad_estado', '')}"
    if len(ubicacion) > 55:
        ubicacion = ubicacion[:52] + "..."
    f_ub = _obtener_fuente(24)
    uw = draw.textlength(ubicacion, font=f_ub)
    draw.text(((W - uw) / 2, y_linea + 50), ubicacion, font=f_ub, fill=(220, 220, 220))

    metricas = _metricas(datos)
    if metricas:
        icon_size = int(24 * 1.2)
        total = sum(icon_size + 10 + draw.textlength(t, font=_obtener_fuente(24, bold=True)) + 30 for _, t in metricas) - 30
        x_start = (W - total) / 2
        _dibujar_iconos_centrado(draw, metricas, x_start, y_linea + 94, W - 2 * PAD, dorado, tamano_base=24)

    y_ag = H - PAD - 55
    nombre_ag = datos.get("nombre_agente", "")
    f_ag = _obtener_fuente(24, bold=True)
    nw = draw.textlength(nombre_ag, font=f_ag)
    draw.text(((W - nw) / 2, y_ag), nombre_ag, font=f_ag, fill=dorado)
    tel = datos.get("telefono_agente", "")
    f_tel = _obtener_fuente(22)
    telw = draw.textlength(tel, font=f_tel)
    draw.text(((W - telw) / 2, y_ag + 30), tel, font=f_tel, fill=(200, 200, 200))
    return img

def _componer_moderna(img, datos, branding, dorado):
    """Barra lateral sólida con el color primario de la marca."""
    primario = hex_to_rgb(branding["color_primario"])
    W, H = img.size
    PAD = 30
    BARRA_W = int(W * 0.4)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_ov = ImageDraw.Draw(overlay)
    d_ov.rectangle([(0, 0), (BARRA_W, H)], fill=(*primario, 235))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(BARRA_W - 4, 0), (BARRA_W, H)], fill=dorado)

    y = PAD
    _pegar_logo_simple(img, draw, PAD, branding, logo_max=(110, 65))
    y += 90

    etiqueta = f"{datos.get('tipo_propiedad', '')}".upper()
    draw.text((PAD, y), etiqueta, font=_obtener_fuente(24, bold=True), fill=dorado)
    y += 32
    op = f"EN {datos.get('operacion', '')}".upper()
    draw.text((PAD, y), op, font=_obtener_fuente(20), fill=(210, 210, 210))
    y += 46

    draw.rectangle([(PAD, y), (BARRA_W - PAD, y + 2)], fill=dorado)
    y += 24

    draw.text((PAD, y), _precio_fmt(datos), font=_obtener_fuente(40, bold=True), fill=(255, 255, 255))
    y += 56

    for linea in (datos.get('direccion', ''), datos.get('ciudad_estado', '')):
        if len(linea) > 26:
            linea = linea[:23] + "..."
        draw.text((PAD, y), linea, font=_obtener_fuente(20), fill=(210, 210, 210))
        y += 28
    y += 20

    icon_size = 28
    f_ico = _obtener_fuente(22, bold=True)
    for nombre_ico, texto in _metricas(datos):
        _ICONOS[nombre_ico](draw, PAD, y, icon_size, dorado, width=3)
        draw.text((PAD + icon_size + 10, y - 3), texto, font=f_ico, fill=(255, 255, 255))
        y += icon_size + 18

    y_ag = H - PAD - 70
    draw.rectangle([(PAD, y_ag - 10), (PAD + 120, y_ag - 6)], fill=dorado)
    draw.text((PAD, y_ag), datos.get("nombre_agente", ""), font=_obtener_fuente(22, bold=True), fill=dorado)
    draw.text((PAD, y_ag + 30), datos.get("telefono_agente", ""), font=_obtener_fuente(20), fill=(255, 255, 255))
    return img

def _componer_impacto(img, datos, branding, dorado):
    """Precio enorme centrado, acento diagonal dorado."""
    W, H = img.size
    PAD = 40
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_ov = ImageDraw.Draw(overlay)
    for y in range(H):
        ratio = max(0, (y - H * 0.28)) / (H * 0.72)
        d_ov.rectangle([(0, y), (W, y + 1)], fill=(0, 0, 0, int(210 * min(ratio, 1))))
    overlay.paste(_gradiente(W, 120, "arriba", 170), (0, 0))
    img = Image.alpha_composite(img, overlay)

    accent = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    da = ImageDraw.Draw(accent)
    da.polygon([(0, H * 0.6), (W, H * 0.5), (W, H * 0.53), (0, H * 0.63)], fill=(*dorado, 210))
    img = Image.alpha_composite(img, accent)
    draw = ImageDraw.Draw(img)

    _pegar_logo_simple(img, draw, PAD, branding, logo_max=(130, 80))

    precio = _precio_fmt(datos)
    f_precio = _obtener_fuente(76, bold=True)
    pw = draw.textlength(precio, font=f_precio)
    y_precio = int(H * 0.37)
    draw.text(((W - pw) / 2, y_precio), precio, font=f_precio, fill=(255, 255, 255))

    etiqueta = f"{datos.get('tipo_propiedad', '')} en {datos.get('operacion', '')}".upper()
    f_et = _obtener_fuente(30, bold=True)
    tw = draw.textlength(etiqueta, font=f_et)
    draw.text(((W - tw) / 2, y_precio - 46), etiqueta, font=f_et, fill=dorado)

    ubicacion = f"{datos.get('direccion', '')}, {datos.get('ciudad_estado', '')}"
    if len(ubicacion) > 50:
        ubicacion = ubicacion[:47] + "..."
    f_ub = _obtener_fuente(26)
    uw = draw.textlength(ubicacion, font=f_ub)
    y_ub = int(H * 0.66)
    draw.text(((W - uw) / 2, y_ub), ubicacion, font=f_ub, fill=(220, 220, 220))

    metricas = _metricas(datos)
    if metricas:
        icon_size = int(24 * 1.2)
        total = sum(icon_size + 10 + draw.textlength(t, font=_obtener_fuente(24, bold=True)) + 30 for _, t in metricas) - 30
        x_start = (W - total) / 2
        _dibujar_iconos_centrado(draw, metricas, x_start, y_ub + 46, W - 2 * PAD, dorado, tamano_base=24)

    y_ag = H - PAD - 75
    nombre_ag = datos.get("nombre_agente", "")
    f_ag = _obtener_fuente(26, bold=True)
    nw = draw.textlength(nombre_ag, font=f_ag)
    draw.text(((W - nw) / 2, y_ag), nombre_ag, font=f_ag, fill=dorado)
    tel = datos.get("telefono_agente", "")
    f_tel = _obtener_fuente(24)
    telw = draw.textlength(tel, font=f_tel)
    draw.text(((W - telw) / 2, y_ag + 34), tel, font=f_tel, fill=(255, 255, 255))
    return img

def _componer_personalizada(img, datos, branding, dorado):
    """Superpone el diseño/marco PNG subido por el agente y dibuja los datos
    de la propiedad en una franja inferior, igual que en la plantilla clásica."""
    W, H = img.size
    cp = branding.get("_plantilla_custom_path")
    if not cp or not Path(cp).exists():
        return _componer_clasica(img, datos, branding, dorado)
    try:
        overlay_img = Image.open(str(cp)).convert("RGBA")
        if overlay_img.size != (W, H):
            overlay_img = overlay_img.resize((W, H), Image.LANCZOS)
        img = Image.alpha_composite(img, overlay_img)
    except Exception:
        pass
    draw = ImageDraw.Draw(img)

    PAD = 45
    FRANJA_H = int(H * 0.22)
    fondo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fondo.paste(_gradiente(W, FRANJA_H, "abajo", 200), (0, H - FRANJA_H))
    img = Image.alpha_composite(img, fondo)
    draw = ImageDraw.Draw(img)

    y_base = H - FRANJA_H + 15
    draw.text((PAD, y_base), _precio_fmt(datos), font=_obtener_fuente(46, bold=True), fill=(255, 255, 255))
    etiqueta = f"{datos.get('tipo_propiedad', '')} en {datos.get('operacion', '')}"
    f_et = _obtener_fuente(28, bold=True)
    et_w = draw.textlength(etiqueta, font=f_et)
    draw.text((W - PAD - et_w, y_base + 6), etiqueta, font=f_et, fill=dorado)

    ubicacion = f"{datos.get('direccion', '')}, {datos.get('ciudad_estado', '')}"
    if len(ubicacion) > 50:
        ubicacion = ubicacion[:47] + " ..."
    y_ubic = y_base + 50
    draw.text((PAD, y_ubic), ubicacion, font=_obtener_fuente(22), fill=(210, 210, 210))

    metricas = _metricas(datos)
    if metricas:
        _dibujar_iconos_centrado(draw, metricas, PAD, y_ubic + 40, W - 2 * PAD, dorado, tamano_base=24)

    nombre = datos.get("nombre_agente", "")
    telefono = datos.get("telefono_agente", "")
    draw.text((PAD, H - 40), f"{nombre}  •  {telefono}", font=_obtener_fuente(20, bold=True), fill=dorado)
    return img

def _componer_original(img, datos, branding, dorado):
    """Foto limpia: sin franjas, precio ni texto. Solo el logo de la inmobiliaria/agente."""
    W, H = img.size
    PAD = 40
    draw = ImageDraw.Draw(img)
    _pegar_logo_simple(img, draw, PAD, branding, logo_max=(130, 85))
    return img

_PLANTILLAS = {
    "original": _componer_original,
    "clasica": _componer_clasica,
    "elegante": _componer_elegante,
    "moderna": _componer_moderna,
    "impacto": _componer_impacto,
    "personalizada": _componer_personalizada,
}

def _componer(img: Image.Image, datos: dict, agente: dict = None, bottom_safe: int = 0) -> Image.Image:
    branding = get_branding(agente)
    branding["_logo_path"] = str(logo_path_absoluto(agente))
    if plantilla_custom_existe(agente):
        branding["_plantilla_custom_path"] = str(plantilla_custom_path_absoluto(agente))
    dorado = hex_to_rgb(branding["color_secundario"])
    plantilla = branding.get("plantilla", "clasica")
    fn = _PLANTILLAS.get(plantilla, _componer_clasica)
    return fn(img, datos, branding, dorado)

def componer_portada(foto_path: str, datos: dict, agente: dict = None) -> str:
    img = _cargar_cover(foto_path, SIZE, SIZE)
    img = _componer(img, datos, agente=agente, bottom_safe=0)
    return _guardar(img, "compuesta")

def componer_stories(foto_path: str, datos: dict, agente: dict = None) -> str:
    img = _cargar_cover(foto_path, 1080, 1920)
    img = _componer(img, datos, agente=agente, bottom_safe=190)
    return _guardar(img, "stories")

def componer_overlay_extras(extras_paths: list, datos: dict, agente: dict = None) -> list:
    urls = []
    for ruta in (extras_paths or []):
        if ruta and Path(ruta).exists():
            img = _cargar_cover(ruta, SIZE, SIZE)
            img = _componer(img, datos, agente=agente, bottom_safe=0)
            urls.append(_guardar(img, "extra"))
    return urls

def componer_collage(portada_path: str, extras_paths: list, datos: dict, agente: dict = None) -> str:
    branding_data = get_branding(agente)
    branding_data["_logo_path"] = str(logo_path_absoluto(agente))
    if plantilla_custom_existe(agente):
        branding_data["_plantilla_custom_path"] = str(plantilla_custom_path_absoluto(agente))
    dorado = hex_to_rgb(branding_data["color_secundario"])
    rutas = [r for r in ([portada_path] + list(extras_paths or [])) if r and Path(r).exists()][:4]
    if not rutas:
        return ""
    canvas = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 255))
    g = 6
    def pega(ruta, x, y, bw, bh):
        canvas.paste(_cargar_cover(ruta, bw, bh), (x, y))
    n = len(rutas)
    if n == 1:
        pega(rutas[0], 0, 0, SIZE, SIZE)
    elif n == 2:
        cw = (SIZE - g) // 2
        pega(rutas[0], 0, 0, cw, SIZE)
        pega(rutas[1], cw + g, 0, SIZE - cw - g, SIZE)
    elif n == 3:
        cw = (SIZE - g) // 2
        ch = (SIZE - g) // 2
        pega(rutas[0], 0, 0, cw, SIZE)
        pega(rutas[1], cw + g, 0, SIZE - cw - g, ch)
        pega(rutas[2], cw + g, ch + g, SIZE - cw - g, SIZE - ch - g)
    else:
        cw = (SIZE - g) // 2
        ch = (SIZE - g) // 2
        pega(rutas[0], 0, 0, cw, ch)
        pega(rutas[1], cw + g, 0, SIZE - cw - g, ch)
        pega(rutas[2], 0, ch + g, cw, SIZE - ch - g)
        pega(rutas[3], cw + g, ch + g, SIZE - cw - g, SIZE - ch - g)
    plantilla = branding_data.get("plantilla", "clasica")
    fn = _PLANTILLAS.get(plantilla, _componer_clasica) if plantilla == "original" else _componer_clasica
    canvas = fn(canvas, datos, branding_data, dorado)
    return _guardar(canvas, "collage")
