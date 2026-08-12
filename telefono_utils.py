"""Normalización y validación de números de WhatsApp/contacto (Venezuela por defecto)."""
import re


def normalizar_telefono_whatsapp(numero: str) -> str | None:
    """Convierte un teléfono escrito en cualquier formato local a dígitos puros
    en formato internacional (sin '+'), listo para usar en un link wa.me.

    Devuelve None si el número no tiene una forma válida reconocible.
    Ejemplos:
      "0412-123.4567"      -> "584121234567"
      "412 123 4567"       -> "584121234567"
      "+58 (412) 123-4567" -> "584121234567"
      "58412123456 7"      -> "584121234567"
    """
    digitos = re.sub(r"\D", "", numero or "")
    if not digitos:
        return None

    if digitos.startswith("58") and len(digitos) == 12:
        pass  # ya viene con código de país
    elif digitos.startswith("0") and len(digitos) == 11:
        digitos = "58" + digitos[1:]
    elif len(digitos) == 10 and digitos[0] == "4":
        digitos = "58" + digitos
    # Si no calza con ningún patrón venezolano conocido, se deja tal cual
    # para no romper números de otros países ya escritos en formato internacional.

    if len(digitos) < 10 or len(digitos) > 15:
        return None
    return digitos
