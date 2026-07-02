import uuid
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from branding import get_branding, hex_to_rgb

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
LOGO_PATH = BASE_DIR / "static" / "logo.png"

SIZE = 1080

def _obtener_fuente(size: int, bold: bool = False):
    """Obtiene fuente compatible Windows + Linux + Railway."""
    system_fonts = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial Bold.ttf" if bold else "C:/Windows/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf" if bold else "/usr/share/fonts/truetype/ubuntu/Ubuntu-Regular.ttf",
    ]

    for ruta in system_fonts:
        try:
            if ruta and os.path.exists(ruta):
                return ImageFont.truetype(ruta, size)
        except Exception:
            continue

    return ImageFont.load_default()


def _estilos(branding: dict, modo: str = "web") -> dict:
    primario = hex_to_rgb(branding.get("color_primario", "#1a3a5c"))
    secundario = hex_to_rgb(branding.get("color_secundario", "#c8a45a"))
    if modo.lower() == "local":
        panel = (20, 20, 20, 235)
        texto = (245, 245, 245)
        subtexto = (200, 200, 200)
        accent_color = secundario
    else:
        panel = (0, 0, 0, 190)
        texto = (255, 255, 255)
        subtexto = (220, 220, 220)
        accent_color = secundario

    return {
        "primario": primario,
        "secundario": secundario,
        "texto": texto,
        "subtexto": subtexto,
        "panel": panel,
        "acento": accent_color,
        "overlay_alpha": 200,
    }

def _num(valor):
    """Formatea número."""
    try:
        f = float(valor)
        return str(int(f)) if f.is_integer() else str(f)
    except:
        return str(valor)

def _cargar_cover(foto_path: str, W: int, H: int) -> Image.Image:
    """Carga y recorta imagen tipo cover."""
    img = Image.open(foto_path).convert("RGBA")
    w, h = img.size
    escala = max(W / w, H / h)
    nw, nh = max(1, int(w * escala)), max(1, int(h * escala))
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - W) // 2
    top = (nh - H) // 2
    return img.crop((left, top, left + W, top + H))

def _guardar(img: Image.Image, prefijo: str) -> str:
    """Guarda imagen."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    nombre = f"{prefijo}_{uuid.uuid4().hex}.jpg"
    img.convert("RGB").save(str(UPLOAD_DIR / nombre), "JPEG", quality=92)
    return f"/static/uploads/{nombre}"

def _precio_fmt(datos):
    """Formatea precio."""
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
    draw.rectangle([x + size * 0.15, y + size * 0.2, x + size * 0.85, y + size * 0.8], 
                   outline=color, width=width)
    draw.line([(x + size * 0.15, y + size * 0.5), (x + size * 0.3, y + size * 0.5)], 
              fill=color, width=width)

def _icono_auto(draw, x, y, size, color, width=3):
    base = y + size * 0.6
    draw.line([(x + size * 0.2, base), (x + size * 0.8, base)], fill=color, width=width)
    draw.line([(x + size * 0.25, base), (x + size * 0.35, y + size * 0.3)], fill=color, width=width)
    draw.line([(x + size * 0.35, y + size * 0.3), (x + size * 0.65, y + size * 0.3)], 
              fill=color, width=width)
    draw.line([(x + size * 0.65, y + size * 0.3), (x + size * 0.75, base)], fill=color, width=width)
    r = size * 0.08
    draw.ellipse([x + size * 0.3 - r, base - r, x + size * 0.3 + r, base + r], 
                 outline=color, width=width)
    draw.ellipse([x + size * 0.7 - r, base - r, x + size * 0.7 + r, base + r], 
                 outline=color, width=width)

def _componer_clasica(img, datos, branding, dorado, estilo):
    W, H = img.size
    PAD = 48
    texto = estilo["texto"]
    subtexto = estilo["subtexto"]
    panel = estilo["panel"]
    acento = estilo["acento"]

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    franja_top = Image.new("RGBA", (W, 220), (0, 0, 0, 0))
    dt = ImageDraw.Draw(franja_top)
    for y in range(220):
        alpha = int(150 * (y / 220))
        dt.rectangle([(0, y), (W, y + 1)], fill=(0, 0, 0, alpha))
    overlay.paste(franja_top, (0, 0))

    franja_bot = Image.new("RGBA", (W, 360), (0, 0, 0, 0))
    db = ImageDraw.Draw(franja_bot)
    for y in range(360):
        alpha = int(220 * ((360 - y) / 360))
        db.rectangle([(0, y), (W, y + 1)], fill=(0, 0, 0, alpha))
    overlay.paste(franja_bot, (0, H - 360))

    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    if LOGO_PATH.exists():
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo.thumbnail((120, 80), Image.LANCZOS)
            img.paste(logo, (PAD, PAD), logo)
        except Exception:
            draw.text((PAD, PAD), branding["nombre_agencia"], font=_obtener_fuente(42, bold=True), fill=texto)
    else:
        draw.text((PAD, PAD), branding["nombre_agencia"], font=_obtener_fuente(42, bold=True), fill=texto)

    draw.rectangle([(PAD, 100), (PAD + 220, 106)], fill=acento)

    etiqueta = f"{datos.get('tipo_propiedad', '')} / {datos.get('operacion', '')}"
    f_et = _obtener_fuente(34, bold=True)
    et_w = draw.textlength(etiqueta, font=f_et)
    draw.text((W - PAD - et_w, PAD + 10), etiqueta, font=f_et, fill=acento)

    y_precio = H - 320
    draw.text((PAD, y_precio), _precio_fmt(datos), font=_obtener_fuente(78, bold=True), fill=texto)

    ubicacion = f"{datos.get('direccion', '')}, {datos.get('ciudad_estado', '')}"
    if len(ubicacion) > 60:
        ubicacion = ubicacion[:57] + "..."
    y_ubic = y_precio + 85
    draw.text((PAD, y_ubic), ubicacion, font=_obtener_fuente(28), fill=subtexto)

    draw.rectangle([(PAD, y_ubic + 42), (PAD + 220, y_ubic + 48)], fill=acento)

    y_metricas = y_ubic + 68
    x_m = PAD
    icon_size = 34

    if datos.get("habitaciones"):
        _icono_cama(draw, x_m, y_metricas, icon_size, acento)
        draw.text((x_m + 50, y_metricas + 4), f"{datos['habitaciones']} Hab", font=_obtener_fuente(28, bold=True), fill=texto)
        x_m += 190

    if datos.get("banos"):
        _icono_bano(draw, x_m, y_metricas, icon_size, acento)
        draw.text((x_m + 50, y_metricas + 4), f"{datos['banos']} Baños", font=_obtener_fuente(28, bold=True), fill=texto)
        x_m += 220

    if datos.get("metros_construidos"):
        _icono_area(draw, x_m, y_metricas, icon_size, acento)
        draw.text((x_m + 50, y_metricas + 4), f"{_num(datos['metros_construidos'])} m²", font=_obtener_fuente(28, bold=True), fill=texto)
        x_m += 220

    if datos.get("estacionamientos"):
        _icono_auto(draw, x_m, y_metricas, icon_size, acento)
        draw.text((x_m + 50, y_metricas + 4), f"{datos['estacionamientos']} Est.", font=_obtener_fuente(28, bold=True), fill=texto)

    y_agente = H - 90
    draw.rectangle([(PAD, y_agente - 10), (PAD + 270, y_agente - 4)], fill=acento)
    draw.text((PAD, y_agente), datos.get("nombre_agente", ""), font=_obtener_fuente(30, bold=True), fill=acento)
    draw.text((PAD, y_agente + 36), datos.get("telefono_agente", ""), font=_obtener_fuente(26), fill=texto)

    return img

def _componer_moderna(img, datos, branding, dorado, estilo):
    W, H = img.size
    primario = estilo["primario"]
    texto = estilo["texto"]
    subtexto = estilo["subtexto"]
    acento = estilo["acento"]

    BARRA_W = int(W * 0.37)
    PAD = 38

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_ov = ImageDraw.Draw(overlay)
    d_ov.rectangle([(0, 0), (BARRA_W, H)], fill=(*primario, 220))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)
    draw.rectangle([(BARRA_W - 4, 0), (BARRA_W, H)], fill=acento)

    y = PAD
    if LOGO_PATH.exists():
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo.thumbnail((110, 72), Image.LANCZOS)
            img.paste(logo, (PAD, y), logo)
            y += 82
        except Exception:
            draw.text((PAD, y), branding["nombre_agencia"], font=_obtener_fuente(32, bold=True), fill=acento)
            y += 54
    else:
        draw.text((PAD, y), branding["nombre_agencia"], font=_obtener_fuente(32, bold=True), fill=acento)
        y += 54

    draw.text((PAD, y), f"{datos.get('tipo_propiedad', '')}".upper(), font=_obtener_fuente(26, bold=True), fill=acento)
    y += 32
    draw.text((PAD, y), f"EN {datos.get('operacion', '')}".upper(), font=_obtener_fuente(22), fill=subtexto)
    y += 44

    draw.rectangle([(PAD, y), (BARRA_W - PAD, y + 3)], fill=acento)
    y += 26

    draw.text((PAD, y), _precio_fmt(datos), font=_obtener_fuente(54, bold=True), fill=texto)
    y += 64

    ubicacion = datos.get('direccion', '')
    if len(ubicacion) > 24:
        ubicacion = ubicacion[:21] + "..."
    draw.text((PAD, y), ubicacion, font=_obtener_fuente(24), fill=subtexto)
    y += 28

    ciudad = datos.get('ciudad_estado', '')
    if len(ciudad) > 24:
        ciudad = ciudad[:21] + "..."
    draw.text((PAD, y), ciudad, font=_obtener_fuente(24), fill=subtexto)
    y += 46

    icon_s = 34
    metrics = []
    if datos.get("habitaciones"):
        metrics.append(("cama", f"{datos['habitaciones']} Hab"))
    if datos.get("banos"):
        metrics.append(("bano", f"{datos['banos']} Baños"))
    if datos.get("metros_construidos"):
        metrics.append(("area", f"{_num(datos['metros_construidos'])} m²"))
    if datos.get("estacionamientos"):
        metrics.append(("auto", f"{datos['estacionamientos']} Est."))

    icon_map = {"cama": _icono_cama, "bano": _icono_bano, "area": _icono_area, "auto": _icono_auto}
    for icon_type, text in metrics:
        icon_map[icon_type](draw, PAD, y, icon_s, acento, width=3)
        draw.text((PAD + 52, y + 4), text, font=_obtener_fuente(24, bold=True), fill=texto)
        y += 44

    y_agente = H - 110
    draw.rectangle([(PAD, y_agente - 8), (BARRA_W - PAD, y_agente - 3)], fill=acento)
    draw.text((PAD, y_agente), datos.get("nombre_agente", ""), font=_obtener_fuente(28, bold=True), fill=acento)
    draw.text((PAD, y_agente + 30), datos.get("telefono_agente", ""), font=_obtener_fuente(22), fill=texto)

    return img

def _componer_elegante(img, datos, branding, dorado, estilo):
    W, H = img.size
    PAD = 60
    texto = estilo["texto"]
    subtexto = estilo["subtexto"]
    panel = estilo["panel"]
    acento = estilo["acento"]

    overlay = Image.new("RGBA", (W, H), panel)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    draw.rectangle([(30, 30), (W - 30, H - 30)], outline=acento, width=3)

    if LOGO_PATH.exists():
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo.thumbnail((110, 70), Image.LANCZOS)
            img.paste(logo, (PAD, PAD), logo)
        except Exception:
            draw.text((PAD, PAD), branding["nombre_agencia"], font=_obtener_fuente(42, bold=True), fill=texto)
    else:
        draw.text((PAD, PAD), branding["nombre_agencia"], font=_obtener_fuente(42, bold=True), fill=texto)

    precio = _precio_fmt(datos)
    y_precio = int(H * 0.35)
    p_w = draw.textlength(precio, font=_obtener_fuente(88, bold=True))
    draw.text(((W - p_w) // 2, y_precio), precio, font=_obtener_fuente(88, bold=True), fill=texto)

    linea_w = min(p_w + 100, W - 2 * PAD)
    lx = (W - linea_w) // 2
    y_linea = y_precio + 95
    draw.rectangle([(lx, y_linea), (lx + linea_w, y_linea + 3)], fill=acento)

    etiqueta = f"{datos.get('tipo_propiedad', '')} EN {datos.get('operacion', '')}".upper()
    et_w = draw.textlength(etiqueta, font=_obtener_fuente(32, bold=True))
    draw.text(((W - et_w) // 2, y_linea + 15), etiqueta, font=_obtener_fuente(32, bold=True), fill=acento)

    ubicacion = f"{datos.get('direccion', '')}, {datos.get('ciudad_estado', '')}"
    if len(ubicacion) > 60:
        ubicacion = ubicacion[:57] + "..."
    ub_w = draw.textlength(ubicacion, font=_obtener_fuente(28))
    draw.text(((W - ub_w) // 2, y_linea + 60), ubicacion, font=_obtener_fuente(28), fill=subtexto)

    y_ag = H - 90
    ag_w = draw.textlength(datos.get("nombre_agente", ""), font=_obtener_fuente(30, bold=True))
    draw.text(((W - ag_w) // 2, y_ag), datos.get("nombre_agente", ""), font=_obtener_fuente(30, bold=True), fill=acento)
    tel_w = draw.textlength(datos.get("telefono_agente", ""), font=_obtener_fuente(26))
    draw.text(((W - tel_w) // 2, y_ag + 35), datos.get("telefono_agente", ""), font=_obtener_fuente(26), fill=subtexto)

    return img

def _componer_impacto(img, datos, branding, dorado, estilo):
    W, H = img.size
    PAD = 50
    texto = estilo["texto"]
    subtexto = estilo["subtexto"]
    panel = estilo["panel"]
    acento = estilo["acento"]

    overlay = Image.new("RGBA", (W, H), panel)
    for y in range(H):
        ratio = max(0, (y - H * 0.25)) / (H * 0.75) if y > H * 0.25 else 0
        ImageDraw.Draw(overlay).rectangle([(0, y), (W, y + 1)], fill=(0, 0, 0, int(180 * ratio)))

    grad_top = Image.new("RGBA", (W, 140), (0, 0, 0, 0))
    gt = ImageDraw.Draw(grad_top)
    for y in range(140):
        alpha = int(160 * (y / 140))
        gt.rectangle([(0, y), (W, y + 1)], fill=(0, 0, 0, alpha))
    overlay.paste(grad_top, (0, 0))

    img = Image.alpha_composite(img, overlay)

    accent = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    da = ImageDraw.Draw(accent)
    da.polygon([(0, int(H * 0.6)), (W, int(H * 0.5)), (W, int(H * 0.53)), (0, int(H * 0.63))], fill=(*acento, 225))
    img = Image.alpha_composite(img, accent)

    draw = ImageDraw.Draw(img)
    if LOGO_PATH.exists():
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo.thumbnail((120, 80), Image.LANCZOS)
            img.paste(logo, (PAD, PAD), logo)
        except Exception:
            draw.text((PAD, PAD), branding["nombre_agencia"], font=_obtener_fuente(42, bold=True), fill=texto)
    else:
        draw.text((PAD, PAD), branding["nombre_agencia"], font=_obtener_fuente(42, bold=True), fill=texto)

    precio = _precio_fmt(datos)
    y_precio = int(H * 0.32)
    p_w = draw.textlength(precio, font=_obtener_fuente(108, bold=True))
    draw.text(((W - p_w) // 2, y_precio), precio, font=_obtener_fuente(108, bold=True), fill=texto)

    etiqueta = f"{datos.get('tipo_propiedad', '')} EN {datos.get('operacion', '')}".upper()
    et_w = draw.textlength(etiqueta, font=_obtener_fuente(36, bold=True))
    draw.text(((W - et_w) // 2, y_precio - 65), etiqueta, font=_obtener_fuente(36, bold=True), fill=acento)

    ubicacion = f"{datos.get('direccion', '')}, {datos.get('ciudad_estado', '')}"
    if len(ubicacion) > 55:
        ubicacion = ubicacion[:52] + "..."
    ub_w = draw.textlength(ubicacion, font=_obtener_fuente(28))
    draw.text(((W - ub_w) // 2, int(H * 0.68)), ubicacion, font=_obtener_fuente(28), fill=subtexto)

    y_ag = H - 100
    ag_w = draw.textlength(datos.get("nombre_agente", ""), font=_obtener_fuente(32, bold=True))
    draw.text(((W - ag_w) // 2, y_ag), datos.get("nombre_agente", ""), font=_obtener_fuente(32, bold=True), fill=acento)
    tel_w = draw.textlength(datos.get("telefono_agente", ""), font=_obtener_fuente(28))
    draw.text(((W - tel_w) // 2, y_ag + 40), datos.get("telefono_agente", ""), font=_obtener_fuente(28), fill=texto)

    return img

def _componer_original(img, datos, branding, dorado, estilo):
    W, H = img.size
    draw = ImageDraw.Draw(img)
    texto = estilo["texto"]
    acento = estilo["acento"]

    padding = 38
    draw.rectangle([(padding, H - 140), (W - padding, H - 55)], fill=(0, 0, 0, 140))
    draw.text((padding + 10, H - 132), _precio_fmt(datos), font=_obtener_fuente(60, bold=True), fill=texto)
    agencia_text = datos.get("nombre_agente", "")
    telefono_text = datos.get("telefono_agente", "")
    draw.text((padding + 10, H - 72), f"{agencia_text} | {telefono_text}", font=_obtener_fuente(26, bold=True), fill=acento)
    return img

_PLANTILLAS = {
    "original": _componer_original,
    "clasica": _componer_clasica,
    "elegante": _componer_elegante,
    "moderna": _componer_moderna,
    "impacto": _componer_impacto,
}

def _componer(img: Image.Image, datos: dict, bottom_safe: int = 0) -> Image.Image:
    branding = get_branding()
    modo = os.getenv("IMAGE_MODE", "web").lower()
    estilo = _estilos(branding, modo)
    dorado = estilo["acento"]
    plantilla = branding.get("plantilla", "clasica")
    fn = _PLANTILLAS.get(plantilla, _componer_clasica)
    return fn(img, datos, branding, dorado, estilo)

def componer_portada(foto_path: str, datos: dict) -> str:
    img = _cargar_cover(foto_path, SIZE, SIZE)
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
            img = _cargar_cover(ruta, SIZE, SIZE)
            img = _componer(img, datos, bottom_safe=0)
            urls.append(_guardar(img, "extra"))
    return urls

def componer_collage(portada_path: str, extras_paths: list, datos: dict) -> str:
    branding = get_branding()
    dorado = hex_to_rgb(branding["color_secundario"])
    agencia = branding["nombre_agencia"]
    
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
    
    franja_h = 180
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    franja = Image.new("RGBA", (SIZE, franja_h), (0, 0, 0, 0))
    df = ImageDraw.Draw(franja)
    for y in range(franja_h):
        alpha = int(225 * ((franja_h - y) / franja_h))
        df.rectangle([(0, y), (SIZE, y + 1)], fill=(0, 0, 0, alpha))
    overlay.paste(franja, (0, SIZE - franja_h))
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)
    
    PAD = 40
    draw.text((PAD, SIZE - 110), _precio_fmt(datos), font=_obtener_fuente(60, bold=True), fill=(255, 255, 255))
    draw.text((PAD, SIZE - 50), datos.get("nombre_agente", ""), font=_obtener_fuente(30, bold=True), fill=dorado)
    
    return _guardar(canvas, "collage")
