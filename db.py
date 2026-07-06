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
                payload TEXT,
                publicado INTEGER DEFAULT 0
            )
            """
        )
        columnas = [r["name"] for r in conn.execute("PRAGMA table_info(propiedades)").fetchall()]
        if "publicado" not in columnas:
            conn.execute("ALTER TABLE propiedades ADD COLUMN publicado INTEGER DEFAULT 0")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nombre_completo TEXT,
                es_admin INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1,
                creado_en TEXT,
                plan TEXT DEFAULT 'prueba',
                suscripcion_inicio TEXT,
                suscripcion_fin TEXT
            )
            """
        )
        cols_agentes = [r["name"] for r in conn.execute("PRAGMA table_info(agentes)").fetchall()]
        if "plan" not in cols_agentes:
            conn.execute("ALTER TABLE agentes ADD COLUMN plan TEXT DEFAULT 'prueba'")
        if "suscripcion_inicio" not in cols_agentes:
            conn.execute("ALTER TABLE agentes ADD COLUMN suscripcion_inicio TEXT")
        if "suscripcion_fin" not in cols_agentes:
            conn.execute("ALTER TABLE agentes ADD COLUMN suscripcion_fin TEXT")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS noticias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,
                titulo TEXT,
                resumen TEXT,
                contenido TEXT,
                imagen_url TEXT,
                creado_en TEXT
            )
            """
        )
        columnas_noticias = [r["name"] for r in conn.execute("PRAGMA table_info(noticias)").fetchall()]
        if "imagen_es_logo" not in columnas_noticias:
            conn.execute("ALTER TABLE noticias ADD COLUMN imagen_es_logo INTEGER DEFAULT 0")


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
        "ciudad_estado, precio, nombre_agente, portada, publicado FROM propiedades"
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


def listar_propiedades_publicadas(limite: int = None) -> list:
    sql = (
        "SELECT id, creado_en, tipo_propiedad, operacion, direccion, "
        "ciudad_estado, precio, nombre_agente, portada FROM propiedades "
        "WHERE publicado = 1 ORDER BY id DESC"
    )
    if limite:
        sql += f" LIMIT {int(limite)}"
    with _conn() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


def listar_propiedades_top(limite: int = 10) -> list:
    sql = (
        "SELECT id, tipo_propiedad, operacion, direccion, ciudad_estado, "
        "precio, portada, payload FROM propiedades "
        "WHERE publicado = 1 ORDER BY id DESC LIMIT ?"
    )
    with _conn() as conn:
        rows = conn.execute(sql, (int(limite),)).fetchall()
    resultado = []
    for r in rows:
        d = dict(r)
        payload_raw = d.pop("payload", None)
        pdf_url = None
        if payload_raw:
            try:
                pdf_url = json.loads(payload_raw).get("pdf_descarga_url")
            except Exception:
                pdf_url = None
        d["pdf_url"] = pdf_url
        resultado.append(d)
    return resultado


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


def obtener_propiedad_publicada(prop_id: int) -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT payload FROM propiedades WHERE id = ? AND publicado = 1", (prop_id,)
        ).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["payload"])
    except Exception:
        return None


def set_publicado(prop_id: int, publicado: bool) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE propiedades SET publicado = ? WHERE id = ?",
            (1 if publicado else 0, prop_id),
        )


def crear_agente(usuario: str, password_hash: str, nombre_completo: str = "",
                  es_admin: bool = False, plan: str = "prueba") -> int:
    ahora = datetime.now().isoformat(timespec="seconds")
    with _conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO agentes (usuario, password_hash, nombre_completo, es_admin, activo,
                                 creado_en, plan, suscripcion_inicio, suscripcion_fin)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?)
            """,
            (usuario, password_hash, nombre_completo, 1 if es_admin else 0,
             ahora,
             "vitalicio" if es_admin else plan,
             ahora,
             "" if es_admin else ""),
        )
        return cur.lastrowid


def obtener_agente_por_usuario(usuario: str) -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM agentes WHERE usuario = ?", (usuario,)
        ).fetchone()
    return dict(row) if row else None


def obtener_agente(agente_id: int) -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM agentes WHERE id = ?", (agente_id,)
        ).fetchone()
    return dict(row) if row else None


def listar_agentes() -> list:
    with _conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, usuario, nombre_completo, es_admin, activo, creado_en, plan, suscripcion_inicio, suscripcion_fin FROM agentes ORDER BY id"
        ).fetchall()]


def set_agente_activo(agente_id: int, activo: bool) -> None:
    with _conn() as conn:
        conn.execute("UPDATE agentes SET activo = ? WHERE id = ?", (1 if activo else 0, agente_id))


def eliminar_agente(agente_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM agentes WHERE id = ?", (agente_id,))


def set_suscripcion(agente_id: int, plan: str, inicio: str, fin: str) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE agentes SET plan = ?, suscripcion_inicio = ?, suscripcion_fin = ? WHERE id = ?",
            (plan, inicio, fin, agente_id),
        )


def contar_agentes() -> int:
    with _conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM agentes").fetchone()
        return row["c"] if row else 0


def guardar_noticia(payload: dict) -> int:
    with _conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO noticias (fecha, titulo, resumen, contenido, imagen_url, imagen_es_logo, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("fecha", ""),
                payload.get("titulo", ""),
                payload.get("resumen", ""),
                payload.get("contenido", ""),
                payload.get("imagen_url"),
                1 if payload.get("imagen_es_logo") else 0,
                payload.get("creado_en", datetime.now().isoformat(timespec="seconds")),
            ),
        )
        return cur.lastrowid


def listar_noticias(limite: int = None) -> list:
    sql = "SELECT * FROM noticias ORDER BY id DESC"
    if limite:
        sql += f" LIMIT {int(limite)}"
    with _conn() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


def obtener_noticia(noticia_id: int) -> dict:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM noticias WHERE id = ?", (noticia_id,)).fetchone()
    return dict(row) if row else None


def obtener_metricas() -> dict:
    with _conn() as conn:
        total_props = conn.execute("SELECT COUNT(*) AS c FROM propiedades").fetchone()["c"]
        publicadas = conn.execute("SELECT COUNT(*) AS c FROM propiedades WHERE publicado = 1").fetchone()["c"]
        total_agentes = conn.execute("SELECT COUNT(*) AS c FROM agentes").fetchone()["c"]
        agentes_activos = conn.execute("SELECT COUNT(*) AS c FROM agentes WHERE activo = 1").fetchone()["c"]
        total_noticias = conn.execute("SELECT COUNT(*) AS c FROM noticias").fetchone()["c"]
        recientes = [dict(r) for r in conn.execute(
            "SELECT id, creado_en, tipo_propiedad, operacion, direccion, precio, portada "
            "FROM propiedades ORDER BY id DESC LIMIT 5"
        ).fetchall()]
    return {
        "total_propiedades": total_props,
        "propiedades_publicadas": publicadas,
        "total_agentes": total_agentes,
        "agentes_activos": agentes_activos,
        "total_noticias": total_noticias,
        "recientes": recientes,
    }


def existe_noticia_hoy() -> bool:
    hoy = datetime.now().strftime("%Y-%m-%d")
    with _conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM noticias WHERE fecha = ?", (hoy,)
        ).fetchone()
        return bool(row and row["c"] > 0)
