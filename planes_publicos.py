"""
planes_publicos.py

Planes y Suscripciones que se muestran en la web pública (modal "Planes"
en el header). Es contenido global de la plataforma Orinokiagente, editable
solo por el SuperAdmin desde /panel/admin — no tiene relacion con el plan
interno (prueba/mensual/anual/vitalicio) que se asigna a cada cuenta.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
PLANES_FILE = DATA_DIR / "planes_publicos.json"

PLANES_DEFAULT = [
    {
        "nombre": "Básico",
        "tagline": "Para inmobiliarias que están empezando",
        "precio": "USD$ 20",
        "destacado": False,
        "items": [
            "🏠 1 Landing Page de la agencia", "Hasta 20 propiedades publicadas", "🙋🏽 1 agente",
            "🤖 Generador de descripciones con IA", "📋 Panel de administración de propiedades",
            "📸 Galería de fotos por propiedad", "🔗 Enlace público de la agencia",
            "✍🏼 Recibe consultas directo por WhatsApp",
        ],
    },
    {
        "nombre": "VIP",
        "tagline": "Para agencias que quieren crecer 🔥",
        "precio": "USD$ 35",
        "destacado": False,
        "items": [
            "🏠 1 Landing Page de la agencia", "Propiedades ilimitadas", "🙋🏽 Hasta 5 agentes",
            "🤖 Generador de descripciones con IA (avanzado)", "📋 Panel de administración de propiedades",
            "📸 Galería de fotos y videos por propiedad", "🔗 Enlace público de la agencia",
            "✍🏼 Recibe consultas directo por WhatsApp", "📊 Estadísticas de visitas por propiedad",
            "👥 Registro de clientes interesados",
        ],
    },
    {
        "nombre": "Plus",
        "tagline": "Para inmobiliarias que quieren automatizar todo 🚀",
        "precio": "USD$ 45",
        "destacado": True,
        "items": [
            "🏠 1 Landing Page de la agencia", "Propiedades ilimitadas", "🙋🏽 Hasta 5 agentes",
            "🤖 Generador de descripciones con IA (avanzado)", "📋 Panel de administración de propiedades",
            "📸 Galería de fotos y videos por propiedad", "🔗 Enlace público de la agencia",
            "✍🏼 Recibe consultas directo por WhatsApp", "📊 Estadísticas de visitas por propiedad",
            "👥 Registro de clientes interesados", "🤖 Generador de Contenido para Redes Sociales y WhatsApp",
        ],
    },
]


def get_planes_publicos() -> list:
    if PLANES_FILE.exists():
        try:
            data = json.loads(PLANES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
        except Exception:
            pass
    return PLANES_DEFAULT


def guardar_planes_publicos(planes: list) -> None:
    PLANES_FILE.write_text(
        json.dumps(planes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
