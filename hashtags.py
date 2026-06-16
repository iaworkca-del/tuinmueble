"""Construye un set de hashtags inmobiliarios según zona, tipo y operación."""

BASE = [
    "#inmobiliaria", "#bienesraices", "#inmuebles", "#venezuela",
    "#inmobiliariavzla", "#propiedadesvenezuela", "#realestate",
]

POR_TIPO = {
    "casa": ["#casa", "#casaenvenezuela", "#hogar"],
    "departamento": ["#apartamento", "#apartamentos", "#aptoenventa"],
    "apartamento": ["#apartamento", "#apartamentos", "#aptoenventa"],
    "terreno": ["#terreno", "#lote", "#parcela", "#inversion"],
    "penthouse": ["#penthouse", "#lujo", "#viviendadelujo", "#exclusividad"],
}

POR_OPERACION = {
    "venta": ["#enventa", "#seVende", "#oportunidad", "#inversioninmobiliaria"],
    "alquiler": ["#enalquiler", "#seAlquila", "#alquiler", "#rentavenezuela"],
}

# Zonas: palabra clave en ciudad/estado -> hashtags
POR_ZONA = {
    "guayana": ["#ciudadguayana", "#puertoordaz", "#sanfelix", "#bolivar", "#guayana"],
    "caroni": ["#ciudadguayana", "#puertoordaz", "#caroni", "#bolivar"],
    "puerto ordaz": ["#puertoordaz", "#ciudadguayana", "#bolivar"],
    "san felix": ["#sanfelix", "#ciudadguayana", "#bolivar"],
    "bolivar": ["#bolivar", "#ciudadguayana", "#ciudadbolivar"],
    "caracas": ["#caracas", "#ccs", "#distritocapital"],
    "miranda": ["#miranda", "#caracas"],
    "maracaibo": ["#maracaibo", "#zulia", "#maracaibocity"],
    "zulia": ["#zulia", "#maracaibo"],
    "valencia": ["#valencia", "#carabobo"],
    "carabobo": ["#carabobo", "#valencia"],
    "barquisimeto": ["#barquisimeto", "#lara"],
    "lara": ["#lara", "#barquisimeto"],
    "maracay": ["#maracay", "#aragua"],
    "aragua": ["#aragua", "#maracay"],
    "merida": ["#merida", "#losandes"],
    "margarita": ["#margarita", "#nuevaesparta", "#islademargarita"],
    "nueva esparta": ["#nuevaesparta", "#margarita"],
    "anzoategui": ["#anzoategui", "#lecheria", "#puertolacruz"],
    "lecheria": ["#lecheria", "#anzoategui", "#puertolacruz"],
}


def _norm(texto: str) -> str:
    reemplazos = (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n"))
    t = (texto or "").lower()
    for a, b in reemplazos:
        t = t.replace(a, b)
    return t


def construir_hashtags(ciudad_estado: str, tipo: str, operacion: str) -> list:
    tags = list(BASE)

    t = _norm(tipo)
    for clave, lista in POR_TIPO.items():
        if clave in t:
            tags += lista
            break

    op = _norm(operacion)
    for clave, lista in POR_OPERACION.items():
        if clave in op:
            tags += lista
            break

    zona = _norm(ciudad_estado)
    agregado = False
    for clave, lista in POR_ZONA.items():
        if clave in zona:
            tags += lista
            agregado = True
            break
    if not agregado:
        # usar las palabras del estado/ciudad como hashtag genérico
        palabra = zona.split(",")[-1].strip().replace(" ", "")
        if palabra:
            tags.append("#" + palabra)

    # dedup conservando orden
    vistos = set()
    final = []
    for h in tags:
        h = h.lower()
        if h not in vistos:
            vistos.add(h)
            final.append(h)
    return final[:22]
