import json
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "propiedades.db"


def _conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS propiedades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creado_en TEXT,
                tipo_propiedad TEXT,
                operacion TEXT,
                direccion TEXT,
                ciudad_estado TEXT,
                precio REAL,
                nombre_agente TEXT,
                portada TEXT,
                payload TEXT
            )
            """
        )


def guardar_propiedad(payload: dict) -> int:
    datos = payload.get("datos", {})
    with _conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO propiedades
            (creado_en, tipo_propiedad, operacion, direccion, ciudad_estado,
             precio, nombre_agente, portada, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                datos.get("tipo_propiedad", ""),
                datos.get("operacion", ""),
                datos.get("direccion", ""),
                datos.get("ciudad_estado", ""),
                datos.get("precio", 0) or 0,
                datos.get("nombre_agente", ""),
                payload.get("portada_compuesta_url", ""),
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        return cur.lastrowid


def listar_propiedades(busqueda: str = None) -> list:
    sql = (
        "SELECT id, creado_en, tipo_propiedad, operacion, direccion, "
        "ciudad_estado, precio, nombre_agente, portada FROM propiedades"
    )
    params = ()
    if busqueda:
        sql += (
            " WHERE direccion LIKE ? OR ciudad_estado LIKE ? OR tipo_propiedad LIKE ?"
            " OR operacion LIKE ? OR nombre_agente LIKE ?"
        )
        like = f"%{busqueda}%"
        params = (like, like, like, like, like)
    sql += " ORDER BY id DESC"
    with _conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def obtener_propiedad(prop_id: int) -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT payload FROM propiedades WHERE id = ?", (prop_id,)
        ).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["payload"])
    except Exception:
        return None
