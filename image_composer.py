import uuid
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from branding import get_branding, hex_to_rgb

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
LOGO_PATH = BASE_DIR / "static" / "logo.png"

SIZE = 1080  # cuadrado Instagram

AZUL_OSCURO = (26, 58, 92)
DORADO = (200, 164, 90)
BLANCO = (255, 255, 255)
NEGRO_TRANS = (0, 0, 0, 180)


def _fuente(size: int, bold: bool = False):
    intentos = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial Bold.ttf" if bold else "C:/Windows/Fonts/Arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for ruta in intentos:
        try:
            return ImageFont.truetype(ruta, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _num(valor):
    """Formatea un numero quitando .0 sobrante (120.0 -> 120)."""
    try:
        f = float(valor)
        if f.is_integer():
            return str(int(f))
        return str(f)
    except (TypeError, ValueError):
        return str(valor)


def _icono_cama(d, x, y, s, c, w=4):
    d.line([(x, y + s * 0.40), (x, y + s * 0.85)], fill=c, width=w)              # poste izq
    d.line([(x + s, y + s * 0.55), (x + s, y + s * 0.85)], fill=c, width=w)      # pata der
    d.line([(x, y + s * 0.55), (x + s, y + s * 0.55)], fill=c, width=w)          # base colchon
    d.line([(x, y + s * 0.40), (x + s * 0.45, y + s * 0.40)], fill=c, width=w)   # respaldo
    d.line([(x + s * 0.45, y + s * 0.40), (x + s * 0.45, y + s * 0.55)], fill=c, width=w)
    # almohada
    d.rectangle([x + s * 0.10, y + s * 0.43, x + s * 0.40, y + s * 0.55], outline=c, width=max(2, w - 1))


def _icono_bano(d, x, y, s, c, w=4):
    top = y + s * 0.50
    izq, der = x + s * 0.08, x + s * 0.92
    d.line([(izq, top), (izq, y + s * 0.68)], fill=c, width=w)                   # lado izq
    d.line([(der, top), (der, y + s * 0.68)], fill=c, width=w)                   # lado der
    d.arc([izq, top - s * 0.18, der, y + s * 0.86], 0, 180, fill=c, width=w)     # fondo curvo
    d.line([(x + s * 0.02, top), (x + s * 0.98, top)], fill=c, width=w)          # borde superior
    # grifo
    d.line([(x + s * 0.22, top), (x + s * 0.22, y + s * 0.30)], fill=c, width=w)
    d.line([(x + s * 0.22, y + s * 0.30), (x + s * 0.40, y + s * 0.30)], fill=c, width=w)


def _icono_carro(d, x, y, s, c, w=4):
    base = y + s * 0.62
    d.line([(x, base), (x + s, base)], fill=c, width=w)                          # base
    d.line([(x + s * 0.20, base), (x + s * 0.32, y + s * 0.38)], fill=c, width=w)  # pilar izq
    d.line([(x + s * 0.32, y + s * 0.38), (x + s * 0.68, y + s * 0.38)], fill=c, width=w)  # techo
    d.line([(x + s * 0.68, y + s * 0.38), (x + s * 0.80, base)], fill=c, width=w)  # pilar der
    r = s * 0.11
    d.ellipse([x + s * 0.22 - r, base - r, x + s * 0.22 + r, base + r], outline=c, width=w)  # rueda izq
    d.ellipse([x + s * 0.78 - r, base - r, x + s * 0.78 + r, base + r], outline=c, width=w)  # rueda der


def _icono_area(d, x, y, s, c, w=4):
    d.rectangle([x + s * 0.12, y + s * 0.28, x + s * 0.88, y + s * 0.78], outline=c, width=w)
    d.line([(x + s * 0.12, y + s * 0.50), (x + s * 0.30, y + s * 0.50)], fill=c, width=max(2, w - 1))
    d.line([(x + s * 0.50, y + s * 0.78), (x + s * 0.50, y + s * 0.60)], fill=c, width=max(2, w - 1))


_ICONOS = {
    "cama": _icono_cama,
    "bano": _icono_bano,
    "carro": _icono_carro,
    "area": _icono_area,
}


def _cargar_cover(foto_path: str, W: int, H: int) -> Image.Image:
    """Carga y recorta una imagen tipo 'cover' al tamaño W x H."""
    img = Image.open(foto_path).convert("RGBA")
    w, h = img.size
    escala = max(W / w, H / h)
    nw, nh = max(1, int(w * escala)), max(1, int(h * escala))
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - W) // 2
    top = (nh - H) // 2
    return img.crop((left, top, left + W, top + H))


def _guardar(img: Image.Image, prefijo: str) -> str:
    nombre_archivo = f"{prefijo}_{uuid.uuid4().hex}.jpg"
    img.convert("RGB").save(str(UPLOAD_DIR / nombre_archivo), "JPEG", quality=92)
    return f"/static/uploads/{nombre_archivo}"


def _pegar_logo(img: Image.Image, draw, pad: int, agencia: str, dorado: tuple, logo_h: int):
    if LOGO_PATH.exists():
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            ratio = logo_h / logo.size[1]
            logo_w = int(logo.size[0] * ratio)
            logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
            img.paste(logo, (pad, pad), logo)
            return
        except Exception:
            pass
    _texto_logo(draw, pad, agencia, dorado)


def _watermark(img: Image.Image, agencia: str) -> Image.Image:
    """Marca de agua sutil centrada (logo si existe, si no el nombre)."""
    W, H = img.size
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if LOGO_PATH.exists():
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            ancho_obj = int(W * 0.45)
            ratio = ancho_obj / logo.size[0]
            lw, lh = ancho_obj, int(logo.size[1] * ratio)
            logo = logo.resize((lw, lh), Image.LANCZOS)
            alpha = logo.split()[3].point(lambda a: int(a * 0.10))
            logo.putalpha(alpha)
            capa.paste(logo, ((W - lw) // 2, (H - lh) // 2), logo)
            return Image.alpha_composite(img, capa)
        except Exception:
            pass
    d = ImageDraw.Draw(capa)
    f = _fuente(int(W * 0.07), bold=True)
    tw = int(d.textlength(agencia, font=f))
    d.text(((W - tw) // 2, H // 2 - int(W * 0.05)), agencia, font=f, fill=(255, 255, 255, 24))
    return Image.alpha_composite(img, capa)


def _componer(img: Image.Image, datos: dict, bottom_safe: int = 0) -> Image.Image:
    """Dibuja el overlay de marca sobre una imagen ya recortada (W x H)."""
    branding = get_branding()
    dorado = hex_to_rgb(branding["color_secundario"])
    agencia = branding["nombre_agencia"]

    W, H = img.size
    PAD = 40

    img = _watermark(img, agencia)

    # ── Franjas (gradientes) ──
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    BLOCK_H = 270
    block_top = H - bottom_safe - BLOCK_H
    franja_top_h = 170
    franja_bot_h = H - block_top + 40

    franja_top = Image.new("RGBA", (W, franja_top_h), (0, 0, 0, 0))
    dt = ImageDraw.Draw(franja_top)
    for y in range(franja_top_h):
        dt.rectangle([(0, y), (W, y + 1)], fill=(0, 0, 0, int(200 * (1 - y / franja_top_h))))
    overlay.paste(franja_top, (0, 0))

    franja_bot = Image.new("RGBA", (W, franja_bot_h), (0, 0, 0, 0))
    db = ImageDraw.Draw(franja_bot)
    for y in range(franja_bot_h):
        db.rectangle([(0, y), (W, y + 1)], fill=(0, 0, 0, int(215 * (y / franja_bot_h))))
    overlay.paste(franja_bot, (0, H - franja_bot_h))

    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # ── Logo / nombre agencia (arriba izquierda) ──
    _pegar_logo(img, draw, PAD, agencia, dorado, logo_h=72)

    # ── Tipo + Operación (arriba derecha) ──
    etiqueta = f"{datos.get('tipo_propiedad', '')} en {datos.get('operacion', '')}"
    f_etiqueta = _fuente(36, bold=True)
    tw = int(draw.textlength(etiqueta, font=f_etiqueta))
    draw.text((W - PAD - tw, PAD + 12), etiqueta, font=f_etiqueta, fill=dorado)

    # ── Precio ──
    try:
        precio_fmt = f"USD ${float(datos.get('precio', 0)):,.0f}"
    except Exception:
        precio_fmt = f"USD ${datos.get('precio', '')}"
    y_precio = block_top
    draw.text((PAD, y_precio), precio_fmt, font=_fuente(72, bold=True), fill=BLANCO)

    # ── Ubicación ──
    ubicacion = f"{datos.get('direccion', '')}, {datos.get('ciudad_estado', '')}"
    if len(ubicacion) > 55:
        ubicacion = ubicacion[:52] + "..."
    y_ubic = y_precio + 82
    draw.text((PAD, y_ubic), ubicacion, font=_fuente(30), fill=(215, 215, 215))

    # ── Íconos + valores ──
    y_iconos = y_ubic + 52
    metricas = []
    if datos.get("habitaciones"):
        metricas.append(("cama", f"{datos['habitaciones']} Hab"))
    if datos.get("banos"):
        metricas.append(("bano", f"{datos['banos']} Baños"))
    if datos.get("metros_construidos"):
        metricas.append(("area", f"{_num(datos['metros_construidos'])} m²"))
    if datos.get("estacionamientos"):
        n = datos["estacionamientos"]
        palabra = "Estacionamiento" if str(n) == "1" else "Estacionamientos"
        metricas.append(("carro", f"{n} {palabra}"))

    disponible = W - 2 * PAD
    GAP_ICO_TXT, GAP_ENTRE = 14, 42
    f_ico, icon_s = _fuente(19, bold=True), int(19 * 1.2)
    for fsize in (34, 30, 26, 22, 19):
        font = _fuente(fsize, bold=True)
        s = int(fsize * 1.2)
        total = sum(s + GAP_ICO_TXT + int(draw.textlength(t, font=font)) for _, t in metricas)
        total += GAP_ENTRE * max(0, len(metricas) - 1)
        if total <= disponible:
            f_ico, icon_s = font, s
            break

    th = draw.textbbox((0, 0), "Hg", font=f_ico)[3]
    icon_off = (th - icon_s) / 2
    x_ico = PAD
    for nombre_ico, texto in metricas:
        _ICONOS[nombre_ico](draw, x_ico, y_iconos + icon_off, icon_s, dorado)
        x_ico += icon_s + GAP_ICO_TXT
        draw.text((x_ico, y_iconos), texto, font=f_ico, fill=BLANCO)
        x_ico += int(draw.textlength(texto, font=f_ico)) + GAP_ENTRE

    # ── Agente ──
    y_agente = y_iconos + 56
    draw.rectangle([(PAD, y_agente - 14), (PAD + 220, y_agente - 10)], fill=dorado)
    draw.text((PAD, y_agente), datos.get("nombre_agente", ""), font=_fuente(30, bold=True), fill=dorado)
    draw.text((PAD, y_agente + 38), datos.get("telefono_agente", ""), font=_fuente(28), fill=BLANCO)

    return img


def componer_portada(foto_path: str, datos: dict) -> str:
    """Imagen cuadrada 1080x1080 para feed de Instagram."""
    img = _cargar_cover(foto_path, SIZE, SIZE)
    img = _componer(img, datos, bottom_safe=0)
    return _guardar(img, "compuesta")


def componer_stories(foto_path: str, datos: dict) -> str:
    """Imagen vertical 1080x1920 para Stories."""
    img = _cargar_cover(foto_path, 1080, 1920)
    img = _componer(img, datos, bottom_safe=190)
    return _guardar(img, "stories")


def componer_overlay_extras(extras_paths: list, datos: dict) -> list:
    """Aplica el overlay de marca a cada foto adicional (para carrusel)."""
    urls = []
    for ruta in (extras_paths or []):
        if ruta and Path(ruta).exists():
            img = _cargar_cover(ruta, SIZE, SIZE)
            img = _componer(img, datos, bottom_safe=0)
            urls.append(_guardar(img, "extra"))
    return urls


def componer_collage(portada_path: str, extras_paths: list, datos: dict) -> str:
    """Mosaico 1080x1080 con varias fotos + franja de marca."""
    branding = get_branding()
    dorado = hex_to_rgb(branding["color_secundario"])
    agencia = branding["nombre_agencia"]

    rutas = [r for r in ([portada_path] + list(extras_paths or [])) if r and Path(r).exists()][:4]
    if not rutas:
        return ""

    canvas = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 255))
    g = 6  # separación

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

    # Franja inferior con precio + agencia + agente
    franja_h = 170
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    franja = Image.new("RGBA", (SIZE, franja_h), (0, 0, 0, 0))
    df = ImageDraw.Draw(franja)
    for y in range(franja_h):
        df.rectangle([(0, y), (SIZE, y + 1)], fill=(0, 0, 0, int(225 * (y / franja_h))))
    overlay.paste(franja, (0, SIZE - franja_h))
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    PAD = 40
    try:
        precio_fmt = f"USD ${float(datos.get('precio', 0)):,.0f}"
    except Exception:
        precio_fmt = f"USD ${datos.get('precio', '')}"
    draw.text((PAD, SIZE - 120), precio_fmt, font=_fuente(54, bold=True), fill=BLANCO)
    draw.text((PAD, SIZE - 56), datos.get("nombre_agente", ""), font=_fuente(26, bold=True), fill=dorado)

    # Nombre de agencia (arriba derecha)
    f_ag = _fuente(30, bold=True)
    aw = int(draw.textlength(agencia, font=f_ag))
    sombra = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sombra)
    ds.rectangle([(SIZE - aw - PAD - 20, 24), (SIZE, 80)], fill=(0, 0, 0, 110))
    canvas = Image.alpha_composite(canvas, sombra)
    draw = ImageDraw.Draw(canvas)
    draw.text((SIZE - aw - PAD, 32), agencia, font=f_ag, fill=BLANCO)

    return _guardar(canvas, "collage")


def _texto_logo(draw: ImageDraw.ImageDraw, pad: int, agencia: str, dorado: tuple):
    f = _fuente(42, bold=True)
    draw.text((pad, pad + 8), agencia, font=f, fill=BLANCO)
    ancho = int(draw.textlength(agencia, font=f))
    # acento dorado bajo el nombre de la agencia
    draw.rectangle([(pad, pad + 60), (pad + min(ancho, 260), pad + 65)], fill=dorado)
