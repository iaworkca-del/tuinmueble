import json
import re
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


PERMISOS_PRINCIPAL = json.dumps({
    "crear_propiedad": True, "modificar_propiedad": True,
    "eliminar_propiedad": True, "crear_agente": True, "eliminar_agente": True,
})
PERMISOS_BASICO = json.dumps({
    "crear_propiedad": True, "modificar_propiedad": True,
    "eliminar_propiedad": False, "crear_agente": False, "eliminar_agente": False,
})


def _slugify(texto: str) -> str:
    """Convierte un texto a un slug apto para URL: minusculas, sin acentos, guiones."""
    s = (texto or "").strip().lower()
    for a, b in {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
                 "ñ": "n", "ü": "u"}.items():
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "cuenta"


def _slug_unico(conn, base: str, excluir_id: int = None) -> str:
    """Devuelve un slug unico dentro de la tabla cuentas, agregando sufijo si hace falta."""
    base = _slugify(base)
    slug = base
    i = 2
    while True:
        q = "SELECT id FROM cuentas WHERE slug = ?"
        params = [slug]
        if excluir_id:
            q += " AND id != ?"
            params.append(excluir_id)
        if not conn.execute(q, params).fetchone():
            return slug
        slug = f"{base}-{i}"
        i += 1


def init_db():
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cuentas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL DEFAULT 'inmobiliaria',
                max_agentes INTEGER DEFAULT 4,
                activo INTEGER DEFAULT 1,
                plan TEXT DEFAULT 'prueba',
                suscripcion_inicio TEXT,
                suscripcion_fin TEXT,
                creado_en TEXT
            )
            """
        )

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
                publicado INTEGER DEFAULT 0,
                agente_id INTEGER REFERENCES agentes(id)
            )
            """
        )
        columnas = [r["name"] for r in conn.execute("PRAGMA table_info(propiedades)").fetchall()]
        if "publicado" not in columnas:
            conn.execute("ALTER TABLE propiedades ADD COLUMN publicado INTEGER DEFAULT 0")
        if "agente_id" not in columnas:
            conn.execute("ALTER TABLE propiedades ADD COLUMN agente_id INTEGER REFERENCES agentes(id)")

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
                suscripcion_fin TEXT,
                cuenta_id INTEGER REFERENCES cuentas(id),
                es_principal INTEGER DEFAULT 0,
                permisos TEXT DEFAULT '{}',
                telefono_movil TEXT DEFAULT '',
                email TEXT DEFAULT ''
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
        if "cuenta_id" not in cols_agentes:
            conn.execute("ALTER TABLE agentes ADD COLUMN cuenta_id INTEGER REFERENCES cuentas(id)")
        if "es_principal" not in cols_agentes:
            conn.execute("ALTER TABLE agentes ADD COLUMN es_principal INTEGER DEFAULT 0")
        if "permisos" not in cols_agentes:
            conn.execute("ALTER TABLE agentes ADD COLUMN permisos TEXT DEFAULT '{}'")
        if "telefono_movil" not in cols_agentes:
            conn.execute("ALTER TABLE agentes ADD COLUMN telefono_movil TEXT DEFAULT ''")
        if "email" not in cols_agentes:
            conn.execute("ALTER TABLE agentes ADD COLUMN email TEXT DEFAULT ''")

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

        # ── Landing pages por cuenta: slug + activacion ──
        cols_cuentas = [r["name"] for r in conn.execute("PRAGMA table_info(cuentas)").fetchall()]
        if "slug" not in cols_cuentas:
            conn.execute("ALTER TABLE cuentas ADD COLUMN slug TEXT")
        if "landing_activa" not in cols_cuentas:
            conn.execute("ALTER TABLE cuentas ADD COLUMN landing_activa INTEGER DEFAULT 1")
        # Backfill: asignar slug a cuentas que aun no lo tengan.
        for row in conn.execute(
            "SELECT id, nombre FROM cuentas WHERE slug IS NULL OR slug = ''"
        ).fetchall():
            slug = _slug_unico(conn, row["nombre"], excluir_id=row["id"])
            conn.execute("UPDATE cuentas SET slug = ? WHERE id = ?", (slug, row["id"]))
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_cuentas_slug ON cuentas(slug)")

        # ── Leads capturados desde las landing pages (para el CRM) ──
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cuenta_id INTEGER,
                nombre TEXT NOT NULL,
                email TEXT,
                telefono TEXT,
                mensaje TEXT,
                propiedad_id INTEGER,
                origen TEXT DEFAULT 'landing',
                leido INTEGER DEFAULT 0,
                creado_en TEXT,
                FOREIGN KEY (cuenta_id) REFERENCES cuentas(id)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_cuenta ON leads(cuenta_id)")
        cols_leads = [r["name"] for r in conn.execute("PRAGMA table_info(leads)").fetchall()]
        if "nota" not in cols_leads:
            conn.execute("ALTER TABLE leads ADD COLUMN nota TEXT DEFAULT ''")
        if "agente_id" not in cols_leads:
            conn.execute("ALTER TABLE leads ADD COLUMN agente_id INTEGER REFERENCES agentes(id)")
        if "cita_fecha" not in cols_leads:
            conn.execute("ALTER TABLE leads ADD COLUMN cita_fecha TEXT DEFAULT ''")
        if "cita_hora" not in cols_leads:
            conn.execute("ALTER TABLE leads ADD COLUMN cita_hora TEXT DEFAULT ''")
        if "cita_lugar" not in cols_leads:
            conn.execute("ALTER TABLE leads ADD COLUMN cita_lugar TEXT DEFAULT ''")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_agente ON leads(agente_id)")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_propiedades_agente ON propiedades(agente_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agentes_cuenta ON agentes(cuenta_id)")

        # ── Agenda de citas: se puede crear con o sin un lead asociado ──
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agente_id INTEGER REFERENCES agentes(id),
                cuenta_id INTEGER REFERENCES cuentas(id),
                lead_id INTEGER REFERENCES leads(id),
                nombre TEXT NOT NULL,
                telefono TEXT DEFAULT '',
                email TEXT DEFAULT '',
                fecha TEXT NOT NULL,
                hora TEXT DEFAULT '',
                lugar TEXT DEFAULT '',
                nota TEXT DEFAULT '',
                creado_en TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_citas_agente ON citas(agente_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_citas_cuenta ON citas(cuenta_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_citas_fecha ON citas(fecha)")


def guardar_propiedad(payload: dict, agente_id: int = None) -> int:
    datos = payload.get("datos", {})
    with _conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO propiedades
            (creado_en, tipo_propiedad, operacion, direccion, ciudad_estado,
             precio, nombre_agente, portada, payload, agente_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                agente_id,
            ),
        )
        return cur.lastrowid


def listar_propiedades(busqueda: str = None, agente_id: int = None,
                       cuenta_id: int = None) -> list:
    sql = (
        "SELECT p.id, p.creado_en, p.tipo_propiedad, p.operacion, p.direccion, "
        "p.ciudad_estado, p.precio, p.nombre_agente, p.portada, p.publicado, p.agente_id "
        "FROM propiedades p"
    )
    condiciones = []
    params = []
    if cuenta_id:
        sql += " JOIN agentes a ON p.agente_id = a.id"
        condiciones.append("a.cuenta_id = ?")
        params.append(cuenta_id)
    elif agente_id:
        condiciones.append("p.agente_id = ?")
        params.append(agente_id)
    if busqueda:
        like = f"%{busqueda}%"
        condiciones.append(
            "(p.direccion LIKE ? OR p.ciudad_estado LIKE ? OR p.tipo_propiedad LIKE ?"
            " OR p.operacion LIKE ? OR p.nombre_agente LIKE ?)"
        )
        params.extend([like, like, like, like, like])
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " ORDER BY p.id DESC"
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
            "SELECT payload, agente_id FROM propiedades WHERE id = ?", (prop_id,)
        ).fetchone()
    if not row:
        return None
    try:
        data = json.loads(row["payload"])
        data["_agente_id"] = row["agente_id"]
        return data
    except Exception:
        return None


def obtener_propiedad_row(prop_id: int) -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, agente_id, publicado FROM propiedades WHERE id = ?", (prop_id,)
        ).fetchone()
    return dict(row) if row else None


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


def eliminar_propiedad_db(prop_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM propiedades WHERE id = ?", (prop_id,))


def contar_propiedades_agente(agente_id: int) -> dict:
    with _conn() as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS c FROM propiedades WHERE agente_id = ?", (agente_id,)
        ).fetchone()["c"]
        publicadas = conn.execute(
            "SELECT COUNT(*) AS c FROM propiedades WHERE agente_id = ? AND publicado = 1",
            (agente_id,),
        ).fetchone()["c"]
    return {"total": total, "publicadas": publicadas}


def crear_agente(usuario: str, password_hash: str, nombre_completo: str = "",
                  es_admin: bool = False, plan: str = "prueba",
                  cuenta_id: int = None, es_principal: bool = False,
                  permisos: str = None, telefono_movil: str = "", email: str = "") -> int:
    ahora = datetime.now().isoformat(timespec="seconds")
    if permisos is None:
        permisos = PERMISOS_PRINCIPAL if es_principal else PERMISOS_BASICO
    with _conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO agentes (usuario, password_hash, nombre_completo, es_admin, activo,
                                 creado_en, plan, suscripcion_inicio, suscripcion_fin,
                                 cuenta_id, es_principal, permisos, telefono_movil, email)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (usuario, password_hash, nombre_completo, 1 if es_admin else 0,
             ahora,
             "vitalicio" if es_admin else plan,
             ahora,
             "" if es_admin else "",
             cuenta_id,
             1 if es_principal else 0,
             permisos,
             telefono_movil,
             email),
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
            "SELECT id, usuario, nombre_completo, es_admin, activo, creado_en, "
            "plan, suscripcion_inicio, suscripcion_fin, cuenta_id, es_principal, permisos, "
            "telefono_movil, email "
            "FROM agentes ORDER BY id"
        ).fetchall()]


def set_agente_activo(agente_id: int, activo: bool) -> None:
    with _conn() as conn:
        conn.execute("UPDATE agentes SET activo = ? WHERE id = ?", (1 if activo else 0, agente_id))


def eliminar_agente(agente_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM agentes WHERE id = ?", (agente_id,))


def set_password_agente(agente_id: int, password_hash: str) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE agentes SET password_hash = ? WHERE id = ?",
            (password_hash, agente_id),
        )


def set_datos_agente(agente_id: int, nombre_completo: str,
                     telefono_movil: str, email: str) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE agentes SET nombre_completo = ?, telefono_movil = ?, email = ? WHERE id = ?",
            (nombre_completo, telefono_movil, email, agente_id),
        )


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


def actualizar_imagen_noticia(noticia_id: int, imagen_url: str, imagen_es_logo: bool = False) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE noticias SET imagen_url = ?, imagen_es_logo = ? WHERE id = ?",
            (imagen_url, 1 if imagen_es_logo else 0, noticia_id),
        )


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


def obtener_metricas(agente: dict = None) -> dict:
    with _conn() as conn:
        if agente and not agente.get("es_admin"):
            if agente.get("es_principal") and agente.get("cuenta_id"):
                where_props = (
                    "WHERE p.agente_id IN "
                    "(SELECT id FROM agentes WHERE cuenta_id = ?)"
                )
                params = (agente["cuenta_id"],)
            else:
                where_props = "WHERE p.agente_id = ?"
                params = (agente["id"],)
            total_props = conn.execute(
                f"SELECT COUNT(*) AS c FROM propiedades p {where_props}", params
            ).fetchone()["c"]
            publicadas = conn.execute(
                f"SELECT COUNT(*) AS c FROM propiedades p {where_props} AND p.publicado = 1"
                if "WHERE" in where_props else
                f"SELECT COUNT(*) AS c FROM propiedades p {where_props}",
                params
            ).fetchone()["c"]
            recientes = [dict(r) for r in conn.execute(
                f"SELECT p.id, p.creado_en, p.tipo_propiedad, p.operacion, p.direccion, "
                f"p.precio, p.portada FROM propiedades p {where_props} ORDER BY p.id DESC LIMIT 5",
                params
            ).fetchall()]
            total_agentes_val = 0
            agentes_activos_val = 0
            if agente.get("es_principal") and agente.get("cuenta_id"):
                total_agentes_val = conn.execute(
                    "SELECT COUNT(*) AS c FROM agentes WHERE cuenta_id = ?",
                    (agente["cuenta_id"],)
                ).fetchone()["c"]
                agentes_activos_val = conn.execute(
                    "SELECT COUNT(*) AS c FROM agentes WHERE cuenta_id = ? AND activo = 1",
                    (agente["cuenta_id"],)
                ).fetchone()["c"]
        else:
            total_props = conn.execute("SELECT COUNT(*) AS c FROM propiedades").fetchone()["c"]
            publicadas = conn.execute("SELECT COUNT(*) AS c FROM propiedades WHERE publicado = 1").fetchone()["c"]
            total_agentes_val = conn.execute("SELECT COUNT(*) AS c FROM agentes").fetchone()["c"]
            agentes_activos_val = conn.execute("SELECT COUNT(*) AS c FROM agentes WHERE activo = 1").fetchone()["c"]
            recientes = [dict(r) for r in conn.execute(
                "SELECT id, creado_en, tipo_propiedad, operacion, direccion, precio, portada "
                "FROM propiedades ORDER BY id DESC LIMIT 5"
            ).fetchall()]
        total_noticias = conn.execute("SELECT COUNT(*) AS c FROM noticias").fetchone()["c"]
    return {
        "total_propiedades": total_props,
        "propiedades_publicadas": publicadas,
        "total_agentes": total_agentes_val,
        "agentes_activos": agentes_activos_val,
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


# ── Funciones de cuentas ──

def crear_cuenta(nombre: str, tipo: str = "inmobiliaria") -> int:
    max_ag = 4 if tipo == "inmobiliaria" else 2
    ahora = datetime.now().isoformat(timespec="seconds")
    with _conn() as conn:
        slug = _slug_unico(conn, nombre)
        cur = conn.execute(
            """
            INSERT INTO cuentas (nombre, tipo, max_agentes, activo, plan,
                                 suscripcion_inicio, creado_en, slug, landing_activa)
            VALUES (?, ?, ?, 1, 'prueba', ?, ?, ?, 1)
            """,
            (nombre, tipo, max_ag, ahora, ahora, slug),
        )
        return cur.lastrowid


def obtener_cuenta(cuenta_id: int) -> dict:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM cuentas WHERE id = ?", (cuenta_id,)).fetchone()
    return dict(row) if row else None


def listar_cuentas() -> list:
    with _conn() as conn:
        cuentas = [dict(r) for r in conn.execute(
            "SELECT * FROM cuentas ORDER BY id"
        ).fetchall()]
    for c in cuentas:
        c["num_agentes"] = contar_agentes_cuenta(c["id"])
    return cuentas


def eliminar_cuenta(cuenta_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM leads WHERE cuenta_id = ?", (cuenta_id,))
        conn.execute("DELETE FROM agentes WHERE cuenta_id = ?", (cuenta_id,))
        conn.execute("DELETE FROM cuentas WHERE id = ?", (cuenta_id,))


def set_cuenta_activa(cuenta_id: int, activo: bool) -> None:
    with _conn() as conn:
        conn.execute("UPDATE cuentas SET activo = ? WHERE id = ?",
                     (1 if activo else 0, cuenta_id))
        conn.execute("UPDATE agentes SET activo = ? WHERE cuenta_id = ?",
                     (1 if activo else 0, cuenta_id))


def contar_agentes_cuenta(cuenta_id: int) -> int:
    with _conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM agentes WHERE cuenta_id = ?", (cuenta_id,)
        ).fetchone()
        return row["c"] if row else 0


def set_suscripcion_cuenta(cuenta_id: int, plan: str, inicio: str, fin: str) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE cuentas SET plan = ?, suscripcion_inicio = ?, suscripcion_fin = ? WHERE id = ?",
            (plan, inicio, fin, cuenta_id),
        )


def listar_agentes_cuenta(cuenta_id: int) -> list:
    with _conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, usuario, nombre_completo, es_principal, activo, permisos, "
            "telefono_movil, email "
            "FROM agentes WHERE cuenta_id = ? ORDER BY es_principal DESC, id",
            (cuenta_id,)
        ).fetchall()]


def set_permisos_agente(agente_id: int, permisos_dict: dict) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE agentes SET permisos = ? WHERE id = ?",
            (json.dumps(permisos_dict), agente_id),
        )


# ──────────────────────────────────────────────────────────────
# Landing pages por cuenta + captura de leads
# ──────────────────────────────────────────────────────────────

def obtener_cuenta_por_slug(slug: str) -> dict:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM cuentas WHERE slug = ?", (slug,)).fetchone()
    return dict(row) if row else None


def set_slug_cuenta(cuenta_id: int, slug: str) -> str:
    """Asigna un slug (unico) a la cuenta y devuelve el slug efectivo."""
    with _conn() as conn:
        nuevo = _slug_unico(conn, slug, excluir_id=cuenta_id)
        conn.execute("UPDATE cuentas SET slug = ? WHERE id = ?", (nuevo, cuenta_id))
        return nuevo


def set_landing_activa(cuenta_id: int, activa: bool) -> None:
    with _conn() as conn:
        conn.execute("UPDATE cuentas SET landing_activa = ? WHERE id = ?",
                     (1 if activa else 0, cuenta_id))


def listar_propiedades_publicadas_cuenta(cuenta_id: int, limite: int = None) -> list:
    """Propiedades publicadas que pertenecen a algun agente de esta cuenta."""
    sql = (
        "SELECT p.id, p.creado_en, p.tipo_propiedad, p.operacion, p.direccion, "
        "p.ciudad_estado, p.precio, p.nombre_agente, p.portada "
        "FROM propiedades p JOIN agentes a ON p.agente_id = a.id "
        "WHERE a.cuenta_id = ? AND p.publicado = 1 ORDER BY p.id DESC"
    )
    if limite:
        sql += f" LIMIT {int(limite)}"
    with _conn() as conn:
        return [dict(r) for r in conn.execute(sql, (cuenta_id,)).fetchall()]


def guardar_lead(cuenta_id: int, nombre: str, email: str = "", telefono: str = "",
                 mensaje: str = "", propiedad_id: int = None, origen: str = "landing") -> int:
    with _conn() as conn:
        agente_id = None
        if propiedad_id:
            fila = conn.execute(
                "SELECT agente_id FROM propiedades WHERE id = ?", (propiedad_id,)
            ).fetchone()
            if fila:
                agente_id = fila["agente_id"]
        cur = conn.execute(
            """
            INSERT INTO leads (cuenta_id, nombre, email, telefono, mensaje,
                               propiedad_id, origen, leido, creado_en, agente_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (cuenta_id, nombre, email, telefono, mensaje, propiedad_id, origen,
             datetime.now().isoformat(timespec="seconds"), agente_id),
        )
        return cur.lastrowid


def listar_leads(cuenta_id: int = None, agente_id: int = None) -> list:
    with _conn() as conn:
        if agente_id is not None:
            rows = conn.execute(
                "SELECT * FROM leads WHERE agente_id = ? ORDER BY id DESC", (agente_id,)
            ).fetchall()
        elif cuenta_id is None:
            rows = conn.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM leads WHERE cuenta_id = ? ORDER BY id DESC", (cuenta_id,)
            ).fetchall()
    return [dict(r) for r in rows]


def contar_leads_no_leidos(cuenta_id: int = None, agente_id: int = None) -> int:
    with _conn() as conn:
        if agente_id is not None:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM leads WHERE leido = 0 AND agente_id = ?",
                (agente_id,),
            ).fetchone()
        elif cuenta_id is None:
            row = conn.execute("SELECT COUNT(*) AS c FROM leads WHERE leido = 0").fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM leads WHERE leido = 0 AND cuenta_id = ?",
                (cuenta_id,),
            ).fetchone()
    return row["c"] if row else 0


def marcar_lead_leido(lead_id: int, leido: bool = True) -> None:
    with _conn() as conn:
        conn.execute("UPDATE leads SET leido = ? WHERE id = ?",
                     (1 if leido else 0, lead_id))


def set_nota_lead(lead_id: int, nota: str) -> None:
    with _conn() as conn:
        conn.execute("UPDATE leads SET nota = ? WHERE id = ?", (nota, lead_id))


def set_cita_lead(lead_id: int, cita_fecha: str, cita_hora: str, cita_lugar: str) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE leads SET cita_fecha = ?, cita_hora = ?, cita_lugar = ? WHERE id = ?",
            (cita_fecha, cita_hora, cita_lugar, lead_id),
        )


def crear_cita(agente_id: int, cuenta_id: int, nombre: str, fecha: str, hora: str = "",
               lugar: str = "", telefono: str = "", email: str = "", nota: str = "",
               lead_id: int = None) -> int:
    with _conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO citas (agente_id, cuenta_id, lead_id, nombre, telefono, email,
                               fecha, hora, lugar, nota, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (agente_id, cuenta_id, lead_id, nombre, telefono, email, fecha, hora, lugar, nota,
             datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def listar_citas(cuenta_id: int = None, agente_id: int = None) -> list:
    with _conn() as conn:
        if agente_id is not None:
            rows = conn.execute(
                "SELECT * FROM citas WHERE agente_id = ? ORDER BY fecha, hora", (agente_id,)
            ).fetchall()
        elif cuenta_id is not None:
            rows = conn.execute(
                "SELECT * FROM citas WHERE cuenta_id = ? ORDER BY fecha, hora", (cuenta_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM citas ORDER BY fecha, hora").fetchall()
    return [dict(r) for r in rows]


def listar_citas_fecha(fecha: str, cuenta_id: int = None, agente_id: int = None) -> list:
    """Citas de un dia concreto, con el nombre del agente asignado (para el calendario)."""
    sql = (
        "SELECT c.*, COALESCE(a.nombre_completo, a.usuario) AS agente_nombre "
        "FROM citas c LEFT JOIN agentes a ON a.id = c.agente_id "
        "WHERE c.fecha = ?"
    )
    params = [fecha]
    if agente_id is not None:
        sql += " AND c.agente_id = ?"
        params.append(agente_id)
    elif cuenta_id is not None:
        sql += " AND c.cuenta_id = ?"
        params.append(cuenta_id)
    with _conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def existe_cita_en_horario(agente_id: int, fecha: str, hora: str, excluir_id: int = None) -> bool:
    """True si ese agente ya tiene otra cita agendada exactamente en esa fecha y hora."""
    if not hora:
        return False
    with _conn() as conn:
        if excluir_id:
            row = conn.execute(
                "SELECT id FROM citas WHERE agente_id = ? AND fecha = ? AND hora = ? AND id != ?",
                (agente_id, fecha, hora, excluir_id),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id FROM citas WHERE agente_id = ? AND fecha = ? AND hora = ?",
                (agente_id, fecha, hora),
            ).fetchone()
    return row is not None


def obtener_cita(cita_id: int) -> dict:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM citas WHERE id = ?", (cita_id,)).fetchone()
    return dict(row) if row else None


def eliminar_cita(cita_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM citas WHERE id = ?", (cita_id,))


def actualizar_cita(cita_id: int, nombre: str, fecha: str, hora: str = "", lugar: str = "",
                    telefono: str = "", email: str = "", nota: str = "") -> None:
    with _conn() as conn:
        conn.execute(
            """
            UPDATE citas SET nombre = ?, fecha = ?, hora = ?, lugar = ?, telefono = ?,
                             email = ?, nota = ?
            WHERE id = ?
            """,
            (nombre, fecha, hora, lugar, telefono, email, nota, cita_id),
        )


def obtener_lead(lead_id: int) -> dict:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return dict(row) if row else None


def eliminar_lead(lead_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
