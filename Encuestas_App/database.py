import sqlite3
import json

def create_connection():
    """Crea una conexión a la base de datos SQLite."""
    conn = sqlite3.connect("encuestas_tfg.db")
    return conn

def create_users_table():
    """Crea la tabla de usuarios si no existe."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT,
            apellidos TEXT,
            email TEXT UNIQUE,
            encuestas_realizadas TEXT DEFAULT '',
            encuestas_abandonadas TEXT DEFAULT '',
            motivos_finalizacion TEXT DEFAULT '{}'
        )
    """)
    conn.commit()
    conn.close()

def create_surveys_table():
    """Crea la tabla de encuestas si no existe."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema TEXT NOT NULL,
            numero_medio INTEGER NOT NULL,
            objetivos TEXT
        )
    """)
    conn.commit()
    conn.close()

def create_preguntas_table():
    """Crea la tabla de preguntas si no existe."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_id INTEGER NOT NULL,
            texto TEXT NOT NULL,
            tipo_respuesta TEXT NOT NULL CHECK(tipo_respuesta IN ('opciones', 'libre')),
            opciones TEXT, -- Puede ser NULL si es 'libre'
            FOREIGN KEY(survey_id) REFERENCES surveys(id)
        )
    """)
    conn.commit()
    conn.close()

def create_respuestas_table():
    """Crea la tabla de respuestas si no existe."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS respuestas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            survey_id INTEGER NOT NULL,
            pregunta_id INTEGER NOT NULL,
            respuesta TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(survey_id) REFERENCES surveys(id),
            FOREIGN KEY(pregunta_id) REFERENCES preguntas(id)
        )
    """)
    conn.commit()
    conn.close()

def add_user(username, password, nombre=None, apellidos=None, email=None):
    """Agrega un nuevo usuario a la base de datos."""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, nombre, apellidos, email) VALUES (?, ?, ?, ?, ?)",
            (username, password, nombre, apellidos, email)
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        print("Error al crear usuario:", e)
    conn.close()

def authenticate_user(username, password):
    """Verifica si las credenciales del usuario son correctas."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_id(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_user_by_email(email):
    """Devuelve el usuario por email."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_survey(tema, numero_medio, objetivos):
    """Agrega una nueva encuesta a la base de datos."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO surveys (tema, numero_medio, objetivos) VALUES (?, ?, ?)",
        (tema, numero_medio, objetivos)
    )
    conn.commit()
    conn.close()

def add_pregunta(survey_id, texto, tipo_respuesta):
    """Agrega una nueva pregunta a una encuesta."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO preguntas (survey_id, texto, tipo_respuesta) VALUES (?, ?, ?)",
        (survey_id, texto, tipo_respuesta)
    )
    conn.commit()
    conn.close()

def add_respuesta(user_id, survey_id, pregunta_id, respuesta):
    """Guarda la respuesta de un usuario a una pregunta de encuesta."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO respuestas (user_id, survey_id, pregunta_id, respuesta) VALUES (?, ?, ?, ?)",
        (user_id, survey_id, pregunta_id, respuesta)
    )
    conn.commit()
    conn.close()

def get_all_surveys():
    """Devuelve todas las encuestas almacenadas."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tema, numero_medio, objetivos FROM surveys")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "tema": row[1],
            "numero_medio": row[2],
            "objetivos": row[3]
        }
        for row in rows
    ]

def get_preguntas_by_survey(survey_id):
    """Devuelve todas las preguntas de una encuesta."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, texto, tipo_respuesta, opciones FROM preguntas WHERE survey_id = ?", (survey_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "texto": row[1],
            "tipo_respuesta": row[2],
            "opciones": row[3],
        }
        for row in rows
    ]

def get_respuestas_by_user(user_id):
    """Devuelve todas las respuestas de un usuario."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT survey_id, pregunta_id, respuesta, fecha FROM respuestas WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "survey_id": row[0],
            "pregunta_id": row[1],
            "respuesta": row[2],
            "fecha": row[3]
        }
        for row in rows
    ]

def get_respuestas_by_survey(survey_id):
    """Devuelve todas las respuestas a una encuesta."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, pregunta_id, respuesta, fecha FROM respuestas WHERE survey_id = ?", (survey_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "user_id": row[0],
            "pregunta_id": row[1],
            "respuesta": row[2],
            "fecha": row[3]
        }
        for row in rows
    ]

def marcar_encuesta_realizada(user_id, survey_id, motivo=""):
    """Marca una encuesta como realizada para un usuario y guarda el motivo de finalización."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT encuestas_realizadas, motivos_finalizacion FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    realizadas = set(row[0].split(',')) if row and row[0] else set()
    realizadas.add(str(survey_id))
    motivos = {}
    if row and row[1]:
        try:
            motivos = json.loads(row[1])
        except Exception:
            motivos = {}
    motivos[str(survey_id)] = motivo
    cursor.execute(
        "UPDATE users SET encuestas_realizadas = ?, motivos_finalizacion = ? WHERE id = ?",
        (','.join(sorted(realizadas)), json.dumps(motivos, ensure_ascii=False), user_id)
    )
    conn.commit()
    conn.close()

def marcar_encuesta_abandonada(user_id, survey_id):
    """Marca una encuesta como abandonada para un usuario"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT encuestas_abandonadas FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    abandonadas = set(row[0].split(',')) if row and row[0] else set()
    abandonadas.add(str(survey_id))
    cursor.execute(
        "UPDATE users SET encuestas_abandonadas = ? WHERE id = ?",
        (','.join(sorted(abandonadas)), user_id)
    )
    conn.commit()
    conn.close()

def get_encuestas_realizadas(user_id):
    """Devuelve una lista de IDs de encuestas realizadas por el usuario."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT encuestas_realizadas FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return [int(x) for x in row[0].split(',') if x]
    return []

def get_encuestas_abandonadas(user_id):
    """Devuelve una lista de IDs de encuestas abandonadas por el usuario."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT encuestas_abandonadas FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return [int(x) for x in row[0].split(',') if x]
    return []

def get_num_realizadas(survey_id):
    """
    Devuelve el número de usuarios que han realizado la encuesta (sin contar duplicados).
    """
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE ',' || encuestas_realizadas || ',' LIKE ?",
                   (f'%,{survey_id},%',))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_num_abandonos(survey_id):
    """
    Devuelve el número de usuarios que han abandonado la encuesta (sin contar duplicados).
    """
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE ',' || encuestas_abandonadas || ',' LIKE ?",
                   (f'%,{survey_id},%',))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_motivo_finalizacion(user_id, survey_id):
    """Devuelve el motivo de finalización de una encuesta realizada por el usuario."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT motivos_finalizacion FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        motivos = json.loads(row[0])
        return motivos.get(str(survey_id), "")
    return ""