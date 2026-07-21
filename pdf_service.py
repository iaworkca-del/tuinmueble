import uuid
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from branding import get_branding
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
)

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"

AZUL = colors.HexColor("#1a3a5c")
DORADO = colors.HexColor("#c8a45a")
GRIS = colors.HexColor("#f3f1ec")
GRIS_TXT = colors.HexColor("#555555")

PAGE_W, PAGE_H = letter
MARGEN = 0.6 * inch
CONTENT_W = PAGE_W - 2 * MARGEN


def _num(valor):
    try:
        f = float(valor)
        return str(int(f)) if f.is_integer() else str(f)
    except (TypeError, ValueError):
        return str(valor)


def _fit(path, max_w, max_h):
    """Devuelve (w, h) escalados para caber en la caja preservando aspecto."""
    try:
        iw, ih = PILImage.open(path).size
    except Exception:
        return max_w, max_h
    escala = min(max_w / iw, max_h / ih)
    return iw * escala, ih * escala


def generar_pdf(datos: dict, descripcion: str, portada_path: str, extras_paths: list, agente: dict = None) -> str:
    nombre_archivo = f"ficha_{uuid.uuid4().hex}.pdf"
    ruta_salida = UPLOAD_DIR / nombre_archivo

    doc = SimpleDocTemplate(
        str(ruta_salida),
        pagesize=letter,
        leftMargin=MARGEN,
        rightMargin=MARGEN,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title="Ficha de propiedad",
    )

    flow = []

    # ── Colores y nombre desde la marca ──
    branding = get_branding(agente)
    azul_hex = branding["color_primario"]
    dorado_hex = branding["color_secundario"]
    azul = colors.HexColor(azul_hex)
    dorado = colors.HexColor(dorado_hex)
    agencia = escape(branding["nombre_agencia"])

    # ── Encabezado de color ──
    tipo = escape(str(datos.get("tipo_propiedad", "")))
    operacion = escape(str(datos.get("operacion", "")))
    try:
        precio_fmt = f"${float(datos.get('precio', 0)):,.0f}"
    except (TypeError, ValueError):
        precio_fmt = f"${datos.get('precio', '')}"

    est_izq = ParagraphStyle("hi", alignment=TA_LEFT, leading=24)
    est_der = ParagraphStyle("hd", alignment=TA_RIGHT, leading=22)
    p_logo = Paragraph(
        f'<font size=20 color="{dorado_hex}"><b>{agencia}</b></font><br/>'
        f'<font size=10 color="#cfd6dd">{tipo} en {operacion}</font>',
        est_izq,
    )
    p_precio = Paragraph(
        f'<font size=9 color="#cfd6dd">Precio USD</font><br/>'
        f'<font size=19 color="white"><b>{precio_fmt}</b></font>',
        est_der,
    )
    header = Table([[p_logo, p_precio]], colWidths=[CONTENT_W * 0.6, CONTENT_W * 0.4])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), azul),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    flow.append(header)
    flow.append(Spacer(1, 14))

    # ── Foto de portada (grande) ──
    if portada_path and Path(portada_path).exists():
        w, h = _fit(portada_path, CONTENT_W, 225)
        flow.append(Image(portada_path, width=w, height=h, hAlign="CENTER"))
        flow.append(Spacer(1, 8))

    # ── Ubicación ──
    ubicacion = escape(f"{datos.get('direccion', '')}, {datos.get('ciudad_estado', '')}")
    est_ubic = ParagraphStyle("ub", fontName="Helvetica", fontSize=10,
                              textColor=GRIS_TXT, alignment=TA_CENTER, spaceAfter=10)
    flow.append(Paragraph(ubicacion, est_ubic))

    # ── Datos clave (caja visual) ──
    campos = []
    campos.append((precio_fmt, "Precio USD"))
    if datos.get("habitaciones"):
        campos.append((_num(datos["habitaciones"]), "Habitaciones"))
    if datos.get("banos"):
        campos.append((_num(datos["banos"]), "Baños"))
    if datos.get("metros_construidos"):
        campos.append((f"{_num(datos['metros_construidos'])}", "m² const."))
    if datos.get("estacionamientos"):
        campos.append((_num(datos["estacionamientos"]), "Estacion."))

    est_box = ParagraphStyle("bx", alignment=TA_CENTER, leading=20)
    fila = [
        Paragraph(
            f'<font size=15 color="{azul_hex}"><b>{escape(str(v))}</b></font><br/>'
            f'<font size=8 color="#777777">{escape(lbl)}</font>',
            est_box,
        )
        for v, lbl in campos
    ]
    tabla_datos = Table([fila], colWidths=[CONTENT_W / len(fila)] * len(fila))
    tabla_datos.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRIS),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("INNERGRID", (0, 0), (-1, -1), 1, colors.white),
        ("LINEBELOW", (0, 0), (-1, -1), 3, dorado),
        ("LINEABOVE", (0, 0), (-1, -1), 3, dorado),
    ]))
    flow.append(tabla_datos)
    flow.append(Spacer(1, 12))

    # ── Descripción ──
    est_h = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=13,
                           textColor=azul, spaceAfter=6)
    est_body = ParagraphStyle("body", fontName="Helvetica", fontSize=10.5,
                              leading=15, textColor=colors.HexColor("#333333"),
                              spaceAfter=10)
    flow.append(Paragraph("Descripción", est_h))
    desc_html = escape(descripcion or "").replace("\n", "<br/>")
    flow.append(Paragraph(desc_html, est_body))

    # ── Espacios y amenidades ──
    espacios = datos.get("espacios") or []
    if espacios:
        flow.append(Paragraph("Espacios y amenidades", est_h))
        chips = "&nbsp;&nbsp;•&nbsp;&nbsp;".join(escape(e) for e in espacios)
        flow.append(Paragraph(
            f'<font color="#444444">{chips}</font>',
            ParagraphStyle("am", fontName="Helvetica", fontSize=10.5,
                           leading=16, spaceAfter=8),
        ))

    # ── Fotos adicionales ──
    extras_validas = [p for p in (extras_paths or []) if p and Path(p).exists()]
    if extras_validas:
        flow.append(Paragraph("Más fotos", est_h))
        por_fila = 4
        gap = 8
        celda_w = (CONTENT_W - gap * (por_fila - 1)) / por_fila
        for i in range(0, len(extras_validas), por_fila):
            grupo = extras_validas[i:i + por_fila]
            celdas = []
            for ruta in grupo:
                w, h = _fit(ruta, celda_w, 85)
                celdas.append(Image(ruta, width=w, height=h, hAlign="CENTER"))
            while len(celdas) < por_fila:
                celdas.append("")
            t = Table([celdas], colWidths=[celda_w + gap] * por_fila)
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            flow.append(t)
        flow.append(Spacer(1, 10))

    # ── Datos de contacto del agente ──
    nombre = escape(str(datos.get("nombre_agente", "")))
    telefono = escape(str(datos.get("telefono_agente", "")))
    email = escape(str(datos.get("email_agente", "") or ""))
    contacto = f'<font size=12 color="{dorado_hex}"><b>{nombre}</b></font>&nbsp;&nbsp;&nbsp;' \
               f'<font size=10 color="white">Tel: {telefono}</font>'
    if email:
        contacto += f'<font size=10 color="white">&nbsp;&nbsp;|&nbsp;&nbsp;{email}</font>'
    p_contacto = Paragraph(contacto, ParagraphStyle("ct", alignment=TA_CENTER, leading=18))
    banda = Table([[p_contacto]], colWidths=[CONTENT_W])
    banda.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), azul),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    flow.append(banda)

    doc.build(flow)
    return f"/descargar/{nombre_archivo}"
