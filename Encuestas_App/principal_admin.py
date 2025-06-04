import os
import streamlit as st
import openai
import sqlite3
import re
import json
from database import get_all_surveys, get_num_realizadas, get_num_abandonos

OPENAI_API_KEY_ADMIN = st.secrets["OPENAI_API_KEY_ADMIN"]
client = openai.OpenAI(api_key=OPENAI_API_KEY_ADMIN)

if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "show_result" not in st.session_state:
    st.session_state.show_result = False
if "last_saved" not in st.session_state:
    st.session_state.last_saved = False
if "show_respuestas" not in st.session_state:
    st.session_state.show_respuestas = None
if "show_preguntas" not in st.session_state:
    st.session_state.show_preguntas = None
if "analisis_encuesta_estado" not in st.session_state or not isinstance(st.session_state.analisis_encuesta_estado, dict):
    st.session_state.analisis_encuesta_estado = {}
if "analisis_encuesta_resultado" not in st.session_state or not isinstance(st.session_state.analisis_encuesta_resultado, dict):
    st.session_state.analisis_encuesta_resultado = {}
if "analisis_encuesta_abierta" not in st.session_state:
    st.session_state.analisis_encuesta_abierta = None

def generar_encuesta(theme: str, main_questions: list, avg_questions: int, objectives: str) -> str:
    user_prompt = (
        "Eres un asistente que genera encuestas detalladas y necesito que generes una encuesta anónima que recabe correctamente en primer lugar la información personal básica del usuario"
        "(sexo, edad, interés del usuario por la encuesta y algo más que consideres relevante en función de cómo sea la encuesta) con preguntas individuales, y que luego cumpla las siguientes características.\n"
        f"Tema principal: {theme}\n"
        f"Preguntas principales: {', '.join(main_questions)}\n"
        f"Número de preguntas que hay que generar: {avg_questions}\n"
        f"Objetivos de la encuesta: {objectives}\n"
        "Devuélveme exactamente una lista numerada de preguntas, cada una en una línea, NO PONGAS ningún número delante de las preguntas, pon directamente la pregunta ¿...,"
        "seguida en la siguiente línea del tipo de respuesta (\"opciones\" o \"libre\"), y si es de opciones, en la siguiente línea pon las opciones separadas por punto y coma. Ejemplo:\n"
        "¿Pregunta?\n"
        "opciones\n"
        "opción1;opción2;opción3\n"
        "¿Pregunta?\n"
        "libre\n"
        "...\n"
        "ES MUY IMPORTANTE QUE GENERES Y DEVUELVAS EXACTAMENTE EL NÚMERO DE PREGUNTAS QUE TE HE DICHO, NI UNA MÁS NI UNA MENOS, SIN CONTAR LAS PREGUNTAS PRINCIPALES COMO EXTRAS YA HAS PODIDO INCLUIRLAS. "
        "Antes de finalizar tu respuesta, cuenta las preguntas y asegúrate de que el número es exactamente el solicitado.\n"
        "Si no puedes generar ese número, devuelve un error."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Eres un generador experto de encuestas."},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5,
        max_tokens=4000
    )

    content = response.choices[0].message.content.strip()
    print("=== RESPUESTA MODELO GPT ===\n", content)
    return content

def parse_questions_with_type(questions_raw):
    preguntas = []
    lines = [line.strip() for line in questions_raw.split("\n") if line.strip()]
    i = 0
    while i < len(lines):
        if lines[i].startswith("¿"):
            texto = lines[i]
            tipo_respuesta = None
            opciones = None
            if i + 1 < len(lines) and lines[i+1].lower() in ("opciones", "libre"):
                tipo_respuesta = lines[i+1].lower()
                if tipo_respuesta == "opciones" and i + 2 < len(lines) and ";" in lines[i+2]:
                    opciones = ";".join([opt.strip() for opt in lines[i+2].split(";") if opt.strip()])
                    i += 1
                i += 1
            else:
                tipo_respuesta = "libre"
            preguntas.append({"texto": texto, "tipo_respuesta": tipo_respuesta, "opciones": opciones})
        i += 1
    return preguntas

@st.dialog("Preguntas de la encuesta")
def mostrar_ventana_preguntas_admin(encuesta):
    st.subheader(f"Tema de la encuesta: {encuesta['tema']}")
    conn = sqlite3.connect("encuestas_tfg.db")
    cursor = conn.cursor()
    cursor.execute("SELECT texto, tipo_respuesta, opciones FROM preguntas WHERE survey_id = ?", (encuesta["id"],))
    preguntas = cursor.fetchall()
    conn.close()
    if preguntas:
        for i, (texto, tipo, opciones) in enumerate(preguntas, 1):
            st.markdown(f"**{i}. {texto}**")
            if tipo == "opciones" and opciones:
                opciones_str = ", ".join(opciones.split(";"))
                st.write(f"Opciones: {opciones_str}")
            st.markdown("---")
    else:
        st.info("No hay preguntas registradas para esta encuesta.")
    st.session_state.show_preguntas = None

@st.dialog("Análisis de la encuesta")
def mostrar_ventana_respuestas_admin(encuesta):
    survey_id = str(encuesta["id"])
    if survey_id not in st.session_state.analisis_encuesta_estado:
        st.session_state.analisis_encuesta_estado[survey_id] = "form"
    if survey_id not in st.session_state.analisis_encuesta_resultado:
        st.session_state.analisis_encuesta_resultado[survey_id] = ""

    estado = st.session_state.analisis_encuesta_estado[survey_id]
    resultado = st.session_state.analisis_encuesta_resultado[survey_id]

    if estado == "form":
        st.subheader("Respuestas de la encuesta: ")
        st.write(f"{encuesta['tema']}")
        num_realizadas = get_num_realizadas(survey_id)
        st.subheader("Usuarios que han realizado la encuesta")
        st.write(f"Total: **{num_realizadas}**")
        num_abandonos = get_num_abandonos(survey_id)
        total = num_realizadas + num_abandonos
        tasa_abandono = (num_abandonos / total * 100) if total > 0 else 0
        st.subheader("Tasa de abandono")
        st.write(f"{tasa_abandono:.2f}% ({num_abandonos} de {total})")
        if st.button("Generar análisis de la encuesta", key=f"generar_analisis_{survey_id}"):
            st.session_state.analisis_encuesta_estado[survey_id] = "generando"
            st.session_state.analisis_encuesta_resultado[survey_id] = ""
            st.rerun()

    elif estado == "generando":
        st.info("Generando análisis de la encuesta, no cierres esta ventana hasta la finalización del proceso...")
        with st.spinner("Generando análisis de la encuesta con IA..."):
            if not st.session_state.analisis_encuesta_resultado[survey_id]:
                conn = sqlite3.connect("encuestas_tfg.db")
                cursor = conn.cursor()
                cursor.execute("SELECT objetivos FROM surveys WHERE id = ?", (encuesta["id"],))
                objetivo_row = cursor.fetchone()
                objetivo = objetivo_row[0] if objetivo_row else "No especificado"

                cursor.execute("SELECT id, texto, tipo_respuesta, opciones FROM preguntas WHERE survey_id = ?", (encuesta["id"],))
                preguntas = cursor.fetchall()
                preguntas_info = [
                    {
                        "id": p[0],
                        "texto": p[1],
                        "tipo_respuesta": p[2],
                        "opciones": p[3]
                    } for p in preguntas
                ]

                cursor.execute("SELECT id, username, encuestas_realizadas, motivos_finalizacion FROM users")
                usuarios = cursor.fetchall()
                usuarios_realizaron = []
                motivos_finalizacion = {}
                for u in usuarios:
                    realizadas = set(u[2].split(",")) if u[2] else set()
                    if str(encuesta["id"]) in realizadas:
                        usuarios_realizaron.append({"id": u[0], "username": u[1]})
                        try:
                            motivos = json.loads(u[3]) if u[3] else {}
                            if str(encuesta["id"]) in motivos:
                                motivos_finalizacion[u[1]] = motivos[str(encuesta["id"])]
                        except Exception:
                            pass

                user_ids_realizaron = {u["id"] for u in usuarios_realizaron}
                cursor.execute("SELECT user_id, pregunta_id, respuesta FROM respuestas WHERE survey_id = ?", (encuesta["id"],))
                respuestas = cursor.fetchall()
                respuestas_info = [
                    {
                        "user_id": r[0],
                        "pregunta_id": r[1],
                        "respuesta": r[2]
                    } for r in respuestas if r[0] in user_ids_realizaron
                ]

                cursor.execute("SELECT id, username, encuestas_abandonadas FROM users")
                usuarios_abandonaron = []
                for u in cursor.fetchall():
                    abandonadas = set(u[2].split(",")) if u[2] else set()
                    if str(encuesta["id"]) in abandonadas:
                        usuarios_abandonaron.append({"id": u[0], "username": u[1]})
                num_abandonos = len(usuarios_abandonaron)
                conn.close()

                prompt = (
                    "Eres un experto en análisis de encuestas. A continuación tienes toda la información relevante sobre una encuesta:\n\n"
                    f"Esta encuesta trata sobre el siguiente tema: {encuesta['tema']}\n"
                    f"Y fue creada con el siguiente objetivo:\n{objetivo}\n\n"
                    "PREGUNTAS DE LA ENCUESTA (con características):\n"
                )
                for p in preguntas_info:
                    prompt += f"- ID: {p['id']}, Texto: {p['texto']}, Tipo: {p['tipo_respuesta']}"
                    if p['opciones']:
                        prompt += f", Opciones: {p['opciones']}"
                    prompt += "\n"

                prompt += "\nUSUARIOS QUE HAN REALIZADO LA ENCUESTA:\n"
                for u in usuarios_realizaron:
                    prompt += f"- {u['username']} (ID: {u['id']})\n"

                prompt += "\nRESPUESTAS DE LOS USUARIOS QUE HAN REALIZADO LA ENCUESTA (user_id, pregunta_id, respuesta):\n"
                for r in respuestas_info:
                    prompt += f"- Usuario: {r['user_id']}, Pregunta: {r['pregunta_id']}, Respuesta: {r['respuesta']}\n"

                prompt += "\nMOTIVOS DE FINALIZACIÓN DE LA ENCUESTA POR USUARIO (solo para quienes la han realizado):\n"
                for user, motivo in motivos_finalizacion.items():
                    prompt += f"- {user}: {motivo}\n"

                prompt += f"\nNÚMERO DE USUARIOS QUE HAN ABANDONADO LA ENCUESTA SIN FINALIZARLA: {num_abandonos}\n"

                prompt += (
                    "\n\nRedacta un informe profesional y estructurado analizando las respuestas de la encuesta. "
                    "El informe debe:\n"
                    "- Comenzar con el título: Informe sobre la encuesta: [tema de la encuesta].\n"
                    "- Analizar las respuestas de los usuarios a las preguntas.\n"
                    "- Extraer conclusiones relevantes a partir de las respuestas de los usuarios.\n"
                    "- Responder y analizar específicamente en función del análisis de respuestas anterior el objetivo por el que se creó la encuesta.\n"
                    "- Incluir un apartado de recomendaciones respecto a la encuesta y al objetivo.\n"
                    "- Incluir un análisis del interés mostrado en la encuesta por los usuarios, teniendo en cuenta tanto los motivos de finalización como el número de abandonos.\n"
                    "Sé claro, profesional y estructurado."
                )

                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Eres un experto en análisis de encuestas."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.5,
                        max_tokens=4000
                    )
                    informe = response.choices[0].message.content.strip()
                except Exception as e:
                    informe = f"Error al generar el análisis: {e}"

                st.session_state.analisis_encuesta_resultado[survey_id] = informe
                st.session_state.analisis_encuesta_estado[survey_id] = "resultado"
                st.rerun()

    elif estado == "resultado":
        st.success("Análisis generado con éxito:")
        st.markdown(st.session_state.analisis_encuesta_resultado[survey_id], unsafe_allow_html=True)
        if st.button("Cerrar informe", key=f"cerrar_analisis_{survey_id}"):
            st.session_state.analisis_encuesta_estado.pop(survey_id, None)
            st.session_state.analisis_encuesta_resultado.pop(survey_id, None)
            st.session_state.analisis_encuesta_abierta = None
            st.rerun()
    st.session_state.analisis_encuesta_abierta = None

def limpiar_campos_crear_encuesta():
    for campo, valor_defecto in [
        ("crear_encuesta_tema", ""),
        ("crear_encuesta_q1", ""),
        ("crear_encuesta_q2", ""),
        ("crear_encuesta_q3", ""),
        ("crear_encuesta_avg_q", 10),
        ("crear_encuesta_obj", ""),
        ("crear_encuesta_error", "")
    ]:
        st.session_state[campo] = valor_defecto

def mostrar_ventana_principal_admin():
    st.set_page_config(page_title="Interfaz del Admin")
    st.markdown("<style>.block-container {padding-top: 2rem;}</style>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Administrador de encuestas</h1>", unsafe_allow_html=True)

    st.subheader("Encuestas activas")
    with st.container(height=450, border=True):
        encuestas = get_all_surveys()
        if encuestas:
            for e in encuestas:
                col1, col2, col3 = st.columns([4, 2, 2])
                with col1:
                    st.markdown(f"- **{e['tema']}**")
                with col2:
                    if st.button("Ver preguntas", use_container_width=True, key=f"ver_preguntas_{e['id']}"):
                        # Limpia el otro flag antes de abrir este diálogo
                        st.session_state.analisis_encuesta_abierta = None
                        st.session_state.show_preguntas = e["id"]
                        mostrar_ventana_preguntas_admin(e)
                with col3:
                    if st.button("Ver respuestas", use_container_width=True, key=f"ver_respuestas_{e['id']}"):
                        # Limpia el otro flag antes de abrir este diálogo
                        st.session_state.show_preguntas = None
                        survey_id = str(e["id"])
                        st.session_state.analisis_encuesta_abierta = survey_id
                        if survey_id not in st.session_state.analisis_encuesta_estado:
                            st.session_state.analisis_encuesta_estado[survey_id] = "form"
                            st.session_state.analisis_encuesta_resultado[survey_id] = ""
                        mostrar_ventana_respuestas_admin(e)

    if st.session_state.show_preguntas:
        encuesta_preguntas = next((e for e in encuestas if e["id"] == st.session_state.show_preguntas), None)
        if encuesta_preguntas:
            mostrar_ventana_preguntas_admin(encuesta_preguntas)
    elif st.session_state.analisis_encuesta_abierta:
        encuesta_abierta = next((e for e in encuestas if str(e["id"]) == st.session_state.analisis_encuesta_abierta), None)
        if encuesta_abierta:
            mostrar_ventana_respuestas_admin(encuesta_abierta)

    col1, col2, col3 = st.columns([3, 1, 3])
    with col3:
        if st.button(":red[Logout]", icon="🚪", use_container_width=True):
            st.session_state.pagina_actual = "inicio_sesion"
            st.session_state.show_form = False
            st.session_state.show_result = False
            st.session_state.last_saved = False
            st.session_state.show_respuestas = None
            st.session_state.show_preguntas = None
            st.session_state.analisis_encuesta_abierta = None
            limpiar_campos_crear_encuesta()
            st.rerun()
    with col1:
        if st.button("Crear nueva encuesta", type="primary", use_container_width=True):
            st.session_state.show_result = False
            st.session_state.show_form = True
            st.session_state.show_preguntas = None
            st.session_state.analisis_encuesta_abierta = None
            limpiar_campos_crear_encuesta()

    if st.session_state.show_form:
        try:
            crear_encuesta()
        except st.errors.StreamlitAPIException:
            st.session_state.show_form = False

@st.dialog("Crear una nueva encuesta")
def crear_encuesta():
    encuestas_activas = get_all_surveys()
    temas_activas = [e['tema'].strip().lower() for e in encuestas_activas]
    for campo, valor_defecto in [
        ("crear_encuesta_tema", ""),
        ("crear_encuesta_q1", ""),
        ("crear_encuesta_q2", ""),
        ("crear_encuesta_q3", ""),
        ("crear_encuesta_avg_q", 10),
        ("crear_encuesta_obj", ""),
        ("crear_encuesta_error", ""),
        ("crear_encuesta_estado", "form"),
        ("crear_encuesta_preguntas", []),
        ("crear_encuesta_preguntas_raw", ""),
    ]:
        if campo not in st.session_state:
            st.session_state[campo] = valor_defecto

    if st.session_state.crear_encuesta_estado == "form":
        with st.form(key='encuesta_form', border=False):
            theme = st.text_input("Tema principal", max_chars=100, key="crear_encuesta_tema")
            q1 = st.text_input("Pregunta principal 1", max_chars=150, key="crear_encuesta_q1")
            q2 = st.text_input("Pregunta principal 2", max_chars=150, key="crear_encuesta_q2")
            q3 = st.text_input("Pregunta principal 3", max_chars=150, key="crear_encuesta_q3")
            avg_q = st.number_input(
                "Número máximo de preguntas que se harán al encuestado",
                min_value=5, max_value=40, key="crear_encuesta_avg_q"
            )
            objectives = st.text_area("Objetivos de la encuesta", max_chars=500, key="crear_encuesta_obj")
            submit = st.form_submit_button("Generar Encuesta")

            error_msg = ""
            if submit:
                main_qs = [q for q in (q1, q2, q3) if q]
                if not theme or len(main_qs) < 1 or not objectives:
                    error_msg = "Por favor, completa todos los campos para poder generar la encuesta."
                elif theme.strip().lower() in temas_activas:
                    error_msg = "El tema principal de la encuesta ya existe. Elige uno diferente."
                elif any(not q.strip().startswith("¿") for q in main_qs):
                    error_msg = "Todas las preguntas principales deben empezar por '¿'."
                else:
                    st.session_state.crear_encuesta_estado = "generando"
                    st.session_state.crear_encuesta_error = ""
                    st.rerun()
                st.session_state.crear_encuesta_error = error_msg

            if st.session_state.crear_encuesta_error:
                st.error(st.session_state.crear_encuesta_error)

    elif st.session_state.crear_encuesta_estado == "generando":
        st.info("Generando encuesta con IA, no cierres esta ventana hasta la finalización del proceso...")
        with st.spinner("Generando encuesta con IA..."):
            theme = st.session_state.crear_encuesta_tema
            q1 = st.session_state.crear_encuesta_q1
            q2 = st.session_state.crear_encuesta_q2
            q3 = st.session_state.crear_encuesta_q3
            avg_q = st.session_state.crear_encuesta_avg_q
            objectives = st.session_state.crear_encuesta_obj
            main_qs = [q for q in (q1, q2, q3) if q]
            try:
                questions_raw = generar_encuesta(theme, main_qs, avg_q, objectives)
                preguntas = parse_questions_with_type(questions_raw)
                conn = sqlite3.connect("encuestas_tfg.db")
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO surveys (tema, numero_medio, objetivos) VALUES (?, ?, ?)",
                    (theme, avg_q, objectives)
                )
                survey_id = cursor.lastrowid
                conn.commit()
                for pregunta in preguntas:
                    cursor.execute(
                        "INSERT INTO preguntas (survey_id, texto, tipo_respuesta, opciones) VALUES (?, ?, ?, ?)",
                        (survey_id, pregunta["texto"], pregunta["tipo_respuesta"], pregunta["opciones"])
                    )
                conn.commit()
                conn.close()
                st.session_state.crear_encuesta_preguntas = preguntas
                st.session_state.crear_encuesta_preguntas_raw = questions_raw
                st.session_state.crear_encuesta_estado = "resultado"
                st.session_state.crear_encuesta_error = ""
                st.rerun()
            except Exception as e:
                st.session_state.crear_encuesta_error = f"Error al generar o guardar la encuesta: {e}"
                st.session_state.crear_encuesta_estado = "form"
                st.rerun()

    elif st.session_state.crear_encuesta_estado == "resultado":
        st.success("¡Encuesta generada con éxito!")
        preguntas = st.session_state.crear_encuesta_preguntas
        if preguntas:
            for i, p in enumerate(preguntas, 1):
                st.markdown(f"**{i}. {p['texto']}**")
                if p["tipo_respuesta"] == "opciones" and p["opciones"]:
                    opciones_str = ", ".join([opt.strip() for opt in p["opciones"].split(";") if opt.strip()])
                    st.write(f"Opciones: {opciones_str}")
                st.markdown("---")
        else:
            st.info("No hay preguntas registradas para esta encuesta.")
        if st.button("Crear otra encuesta"):
            limpiar_campos_crear_encuesta()
            st.session_state.crear_encuesta_estado = "form"
            st.rerun()