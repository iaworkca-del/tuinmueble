from dotenv import load_dotenv
import os
import json
import sys
from pathlib import Path

# Asegurar que la carpeta raíz del proyecto esté en sys.path para poder importar módulos del proyecto
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv()

from ai_service import generar_contenido


def main():
    datos = {
        "tipo_propiedad": "Apartamento",
        "operacion": "Venta",
        "direccion": "Calle Falsa 123",
        "ciudad_estado": "Caracas, Venezuela",
        "precio": 85000,
        "habitaciones": 3,
        "banos": 2,
        "metros_construidos": 120,
        "metros_terreno": None,
        "estacionamientos": 1,
        "espacios": ["Sala", "Comedor", "Balcón"],
        "descripcion_agente": "Excelente oportunidad, cerca de servicios.",
        "nombre_agente": "Juan Pérez",
        "telefono_agente": "+58 412-1234567",
    }

    try:
        resultado = generar_contenido(datos)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    except Exception as e:
        print("ERROR al generar contenido:")
        print(repr(e))


if __name__ == '__main__':
    main()
