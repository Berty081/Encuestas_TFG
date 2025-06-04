import streamlit as st
import openai
import json
import math
import re
import time
from database import (
    get_all_surveys,
    get_user_id,
    get_preguntas_by_survey,
    add_respuesta,
    marcar_encuesta_realizada,
    marcar_encuesta_abandonada,
    get_encuestas_realizadas,
    get_encuestas_abandonadas,
)

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

def log_proceso(texto):
    with open("proceso.txt", "a", encoding="utf-8") as f:
        f.write(str(texto) + "\n")

def ask_gpt(messages, paso):
    log_proceso(f"\n{'='*30}\nPASO {paso}: ENVÍO A CHATGPT\n{'-'*30}")
    for i, msg in enumerate(messages):
        log_proceso(f"Mensaje {i+1} ({msg['role']}):\n{msg['content']}\n")
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            max_tokens=4000
        )
        answer = resp.choices[0].message.content.strip()
        log_proceso(f"---\nRESPUESTA CHATGPT PASO {paso}:\n{answer}\n{'='*30}\n")
    except Exception as e:
        log_proceso(f"ERROR GPT: {e}\n")
        st.error("Error al comunicarse con la IA. Inténtalo de nuevo más tarde.")
        st.stop()
        return None
    return answer

def build_adaptive_prompt(all_questions, respuestas, razonamientos, num_respondidas, numero_medio):
    preguntas_restantes = [
        p['texto'] for p in all_questions if p['id'] not in {r['pregunta_id'] for r in respuestas}
    ]
    preguntas_restantes_str = "\n".join(preguntas_restantes) if preguntas_restantes else "Ninguna."
    respuestas_str = "\n".join(
        f"{i+1}. {all_questions_dict[r['pregunta_id']]['texto']}: {r['respuesta']} (tiempo: {r.get('tiempo', 'N/A')}s)"
        for i, r in enumerate(respuestas)
    ) if respuestas else "Ninguna aún."
    razonamientos_str = "\n".join(
        f"{i+1}. {razon}" for i, razon in enumerate(razonamientos)
    ) if razonamientos else "Ninguno aún."
    min_preguntas = math.ceil(0.5 * numero_medio)

    preguntas_cerradas = [
        p['texto'] for p in all_questions if p.get('tipo_respuesta') == 'opciones'
    ]
    preguntas_cerradas_str = "\n".join(preguntas_cerradas) if preguntas_cerradas else "Ninguna."

    if num_respondidas < min_preguntas:
        prompt = (
            "Tu tarea es elegir en cada paso la siguiente pregunta de entre las preguntas restantes, "
            "adaptando el orden según las respuestas previas del usuario, su interés, o cualquier otro factor relevante. "
            "También tienes acceso al tiempo de respuesta de cada pregunta (en segundos), que puede ayudarte a adaptar el orden. "
            "Devuelve SIEMPRE SOLO un JSON válido sin explicaciones, sin texto adicional, sin formato Markdown, sin comentarios, sin encabezados, sin asteriscos, sin saltos de línea innecesarios, en definitiva solo el JSON, con los campos:\n"
            "  action: \"CONTINUE\"\n"
            "  reason: \"<explicación breve de por qué eliges la siguiente pregunta>\"\n"
            "  next_question: \"<texto EXACTO de la siguiente pregunta elegida de entre las que están en la lista>\"\n"
            "Estado actual de la encuesta:\n"
            f"- Preguntas ya respondidas ({num_respondidas}):\n{respuestas_str}\n"
            f"- Razonamientos previos de la IA:\n{razonamientos_str}\n"
            f"- Preguntas restantes:\n{preguntas_restantes_str}\n"
            "Recuerda: Elige la siguiente pregunta de entre las restantes, en el orden y momento que consideres más adaptativo. "
        )
    else:
        prompt = (
            "ATENCIÓN: A partir de este punto, tu objetivo principal es DETECTAR DESINTERÉS del usuario y FINALIZAR la encuesta si lo detectas. "
            "Debes analizar TODAS las respuestas anteriores y CONTAR cuántas muestran desinterés (por ejemplo: 'no sé', 'ninguno', 'me da igual', 'no quiero seguir', respuestas muy cortas o repetitivas, falta de implicación, etc.). "
            "IMPORTANTE:"
            "- Considera como desinterés SOLO respuestas que sean vacías, incoherentes, repetitivas, explícitamente evasivas(por ejemplo: no se, ninguno, me da igual, no quiero seguir, no importa, no quiero responder, respuestas sin sentido, o respuestas iguales en varias preguntas abiertas)."
            "- NO consideres como desinterés respuestas que sean razones legítimas o habituales para la pregunta, aunque sean breves o genéricas, siempre que sean pertinentes a la pregunta. No consideres como muestra de desinterés si la respuesta es corta pero procede de una pregunta con opciones cerradas de selección"
            "- El tiempo de respuesta solo es muestra de desinterés si es claramente incoherente con la longitud o tipo de respuesta (por ejemplo, 1 segundo para una pregunta reflexiva abierta, o 1 minuto para una pregunta de opciones, o 1 minuto para respuesta libre muy corta)."
            "- SOLO finaliza la encuesta si hay al menos 2 muestras claras y justificadas de desinterés, citando ejemplos literales y explicando por qué lo consideras así."
            "- Si tienes dudas, prioriza CONTINUAR la encuesta."
            "Aquí tienes la lista de preguntas cerradas o de opción:\n"
            f"{preguntas_cerradas_str}\n\n"
            "También analiza el TIEMPO DE RESPUESTA de cada pregunta (en segundos): "
            "solo considera el tiempo como muestra de desinterés si es claramente incoherente con la longitud o tipo de respuesta (por ejemplo, un tiempo muy largo para una respuesta muy corta en una pregunta abierta, o un tiempo muy corto para una pregunta reflexiva). "
            "Sé conservador: SOLO finaliza la encuesta si hay evidencias claras y repetidas de desinterés (al menos 2 muestras claras, y explica por qué lo consideras así). "
            "- En el campo 'reason', CITA LITERALMENTE las respuestas y tiempos de desinterés detectados y explica por qué decides finalizar o continuar.\n"
            "- Si decides continuar a pesar de alguna muestra de desinterés, justifica claramente por qué NO finalizas y elige la siguiente pregunta de entre las restantes, en el orden y momento que consideres más adaptativo.\n"
            "- Si no hay muestras de desinterés, puedes continuar normalmente.\n\n"
            "Devuelve SIEMPRE SOLO un JSON válido sin explicaciones, sin texto adicional, sin formato Markdown, sin comentarios, sin encabezados, sin asteriscos, sin saltos de línea innecesarios, en definitiva solo el JSON, con los campos:\n"
            "  action: \"CONTINUE\" o \"FINALIZAR\"\n"
            "  reason: \"<explicación breve y concreta de tu decisión, citando ejemplos literales de las respuestas y tiempos del usuario>\"\n"
            "  next_question: \"<texto EXACTO de la siguiente pregunta elegida de entre las que están en la lista>\" o null si finalizas\n"
            "Estado actual de la encuesta:\n"
            f"- Preguntas ya respondidas ({num_respondidas}):\n{respuestas_str}\n"
            f"- Razonamientos previos de la IA:\n{razonamientos_str}\n"
            f"- Preguntas restantes:\n{preguntas_restantes_str}\n"
            "Recuerda: Si detectas 2 o más muestras claras de desinterés (por respuesta o tiempo), debes finalizar la encuesta. Si decides continuar, justifica claramente el motivo."
        )
    return prompt

def realizar_encuesta_gpt(user_id, survey_id):
    col01, col02, col03= st.columns([1, 3, 1])
    log_proceso("\n" + "="*50)
    log_proceso("=== INICIO realizar_encuesta_gpt ===")
    log_proceso("="*50 + "\n")

    encuestas = get_all_surveys()
    encuesta = next((e for e in encuestas if e["id"] == survey_id), None)
    numero_medio = encuesta["numero_medio"] if encuesta else 10

    preguntas = get_preguntas_by_survey(survey_id)
    global all_questions_dict
    all_questions_dict = {p["id"]: p for p in preguntas}
    preguntas_dict = {p["texto"]: p for p in preguntas}

    if "ia_razonamientos" not in st.session_state:
        st.session_state.ia_razonamientos = []
    if "respuestas_encuesta" not in st.session_state:
        st.session_state.respuestas_encuesta = []
    if "tiempo_inicio_pregunta" not in st.session_state:
        st.session_state.tiempo_inicio_pregunta = None

    paso = len(st.session_state.respuestas_encuesta) + 1

    if st.session_state.get("pregunta_actual") is None:
        prompt = build_adaptive_prompt(
            all_questions=preguntas,
            respuestas=[],
            razonamientos=[],
            num_respondidas=0,
            numero_medio=numero_medio
        )
        messages = [
            {"role": "system", "content": "Eres un generador experto de encuestas adaptativas."},
            {"role": "user", "content": prompt}
        ]
        primera = ask_gpt(messages, paso)
        raw = primera.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        try:
            data = json.loads(raw)
            accion = data.get("action")
            razon = data.get("reason", "")
            pregunta_siguiente = data.get("next_question")
        except Exception:
            accion = "CONTINUE" if "FINALIZAR" not in raw.upper() else "FINALIZAR"
            razon = ""
            pregunta_siguiente = raw
        if accion == "FINALIZAR":
            st.session_state.pregunta_actual = {"action": "FINALIZAR", "reason": razon, "next_question": None}
        else:
            st.session_state.pregunta_actual = {
                "action": "CONTINUE",
                "reason": razon,
                "next_question": pregunta_siguiente
            }
        st.session_state.tiempo_inicio_pregunta = time.time()
        st.rerun()

    texto_preg = st.session_state.pregunta_actual
    log_proceso(f"\n{'-'*30}\nPREGUNTA ACTUAL (tras inicialización): {texto_preg}\n{'-'*30}")

    if isinstance(texto_preg, dict):
        action = texto_preg.get("action")
        reason = texto_preg.get("reason", "")
        next_question = texto_preg.get("next_question")
    else:
        action = None
        reason = ""
        next_question = None

    if action == "FINALIZAR":
        respondidas = len(st.session_state.respuestas_encuesta)
        total = len(preguntas)
        if respondidas == total:
            motivo_final = "Se han respondido todas las preguntas de la encuesta."
        else:
            motivo_final = reason if reason else "Encuesta finalizada por decisión de la IA."
        with col02:
            st.success("¡Encuesta finalizada! Gracias por participar.")
        if motivo_final:
            with col02:
                st.info(f"Motivo de finalización: {motivo_final}")
        # CAMBIO: Guardar motivo de finalización
        marcar_encuesta_realizada(user_id, survey_id, motivo_final)
        for k in ["pregunta_actual", "respuestas_encuesta", "gpt_messages", "ia_razonamientos", "tiempo_inicio_pregunta"]:
            st.session_state.pop(k, None)
        st.session_state.pagina_actual = "principal"
        with col02:
            col001, col002, col003= st.columns(3)
            with col002:
                if st.button("Volver al menú", type="primary", use_container_width=True):
                    st.rerun()
        log_proceso(f"\n{'='*50}\n=== FIN realizar_encuesta_gpt: encuesta finalizada ===\n{'='*50}\n")
        return

    def normalize_question(text):
        if not text:
            return ""
        return re.sub(r"^\d+\.\s*", "", text).strip().lower()

    def find_pregunta(preguntas_dict, texto):
        if texto in preguntas_dict:
            return preguntas_dict[texto]
        norm = normalize_question(texto)
        for k, v in preguntas_dict.items():
            if normalize_question(k) == norm:
                return v
        return None

    if isinstance(texto_preg, dict):
        pregunta = find_pregunta(preguntas_dict, texto_preg.get("next_question"))
    else:
        pregunta = find_pregunta(preguntas_dict, texto_preg)
    if not pregunta:
        log_proceso(f"\n{'!'*10} ERROR: La IA devolvió una pregunta que no existe en la base de datos. {'!'*10}\n")
        st.error("La IA devolvió una pregunta que no existe en la base de datos.")
        st.session_state.pagina_actual = "principal"
        st.session_state.pregunta_actual = None
        st.session_state.respuestas_encuesta = []
        st.session_state.gpt_messages = []
        st.session_state.ia_razonamientos = []
        st.session_state.tiempo_inicio_pregunta = None
        st.rerun()
        return

    with col02:
        st.write(f" ")
        st.subheader(f"{pregunta['texto']}")

    if st.session_state.tiempo_inicio_pregunta is None:
        st.session_state.tiempo_inicio_pregunta = time.time()

    with col02:
        with st.form(key=f"form_{user_id}_{survey_id}_{pregunta['id']}"):
            opciones = []
            if pregunta["tipo_respuesta"] == "opciones" and pregunta.get("opciones"):
                opciones = [o.strip() for o in str(pregunta["opciones"]).split(";") if o.strip()]
                if opciones:
                    respuesta = st.radio("Selecciona una opción:", opciones)
                else:
                    st.warning("No hay opciones disponibles, se usará respuesta libre.")
                    respuesta = st.text_input("Tu respuesta:")
            else:
                respuesta = st.text_input("Tu respuesta:")

            enviar = st.form_submit_button("Siguiente")
    with col02:
        st.write(f" ")
        if st.button("Abandonar encuesta",type="primary"):
            marcar_encuesta_abandonada(user_id, survey_id)
            for k in ["pregunta_actual", "respuestas_encuesta", "gpt_messages", "ia_razonamientos", "tiempo_inicio_pregunta"]:
                st.session_state.pop(k, None)
            st.session_state.pagina_actual = "principal"
            st.rerun()
            log_proceso(f"\n{'='*50}\n=== FIN realizar_encuesta_gpt: encuesta abandonada ===\n{'='*50}\n")
            return

    if enviar:
        if not respuesta:
            with col02:
                st.warning("Por favor, selecciona o escribe una respuesta antes de continuar.")
            return

        tiempo_respuesta = round(time.time() - st.session_state.tiempo_inicio_pregunta, 2)
        try:
            add_respuesta(user_id, survey_id, pregunta["id"], respuesta)
        except Exception as e:
            log_proceso(f"ERROR al guardar respuesta: {e}\n")
            st.error("Error al guardar la respuesta en la base de datos.")
            st.stop()
            return

        paso = len(st.session_state.respuestas_encuesta) + 1
        log_proceso(f"\n{'*'*30}\nPASO {paso}: RESPUESTA USUARIO\n{'-'*30}")
        log_proceso(f"Pregunta: {pregunta['texto']}\nRespuesta: {respuesta}\nTiempo de respuesta: {tiempo_respuesta}s\n")

        st.session_state.respuestas_encuesta.append(
            {"pregunta_id": pregunta["id"], "respuesta": respuesta, "tiempo": tiempo_respuesta}
        )

        razonamiento = reason if reason else "(Sin razonamiento explícito)"
        log_proceso(f"Razonamiento IA previo a este paso: {razonamiento}\n")

        num_respondidas = len(st.session_state.respuestas_encuesta)
        prompt = build_adaptive_prompt(
            all_questions=preguntas,
            respuestas=st.session_state.respuestas_encuesta,
            razonamientos=st.session_state.ia_razonamientos,
            num_respondidas=num_respondidas,
            numero_medio=numero_medio
        )
        messages = [
            {"role": "system", "content": "Eres un generador experto de encuestas adaptativas."},
            {"role": "user", "content": prompt}
        ]
        siguiente_bruto = ask_gpt(messages, paso+1)

        raw = siguiente_bruto.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            data = json.loads(raw)
            accion = data.get("action")
            razon = data.get("reason", "")
            pregunta_siguiente = data.get("next_question")
        except Exception:
            accion = "CONTINUE" if "FINALIZAR" not in siguiente_bruto.upper() else "FINALIZAR"
            razon = ""
            pregunta_siguiente = siguiente_bruto

        hechas = len(st.session_state.respuestas_encuesta)
        min_preguntas = math.ceil(0.5 * numero_medio)
        if accion == "FINALIZAR" and hechas < min_preguntas:
            st.warning("La IA intentó finalizar antes del 50%. Se continuará la encuesta.")
            accion = "CONTINUE"
            razon = "Intento de finalizar antes del 50%. Forzado a continuar."
            pregunta_siguiente = None

        log_proceso(f"Razonamiento IA tras respuesta usuario (paso {paso}): {razon if razon else '(Sin razonamiento explícito)'}\n")

        st.session_state.ia_razonamientos.append(
            f"Respuesta: {respuesta} | Tiempo: {tiempo_respuesta}s | Acción IA: {accion} | Razonamiento: {razon if razon else '(Sin razonamiento explícito)'}"
        )

        if accion == "FINALIZAR":
            st.session_state.pregunta_actual = {"action": "FINALIZAR", "reason": razon, "next_question": None}
        else:
            if pregunta_siguiente:
                st.session_state.pregunta_actual = {
                    "action": "CONTINUE",
                    "reason": razon,
                    "next_question": pregunta_siguiente
                }
            else:
                respondidas = {r["pregunta_id"] for r in st.session_state.respuestas_encuesta}
                for p in preguntas:
                    if p["id"] not in respondidas:
                        st.session_state.pregunta_actual = p["texto"]
                        break
        st.session_state.tiempo_inicio_pregunta = time.time()
        st.rerun()

def mostrar_ventana_principal():
    st.set_page_config(page_title="principal", layout="wide")

    username = st.session_state.get("username", "Usuario")
    st.markdown("<style>.block-container {padding-top: 1.8rem;}</style>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center;'>Bienvenido, {username} a<br>ENCUESTAS TFG!</h1>", unsafe_allow_html=True)

    user_id = get_user_id(username)
    encuestas = get_all_surveys()
    realizadas = set(get_encuestas_realizadas(user_id) if user_id else [])
    abandonadas = set(get_encuestas_abandonadas(user_id) if user_id else [])

    ya_realizadas = realizadas.union(abandonadas)
    disponibles = [e for e in encuestas if e["id"] not in ya_realizadas]
    ya_realizadas_list = [e for e in encuestas if e["id"] in ya_realizadas]

    col0, col1, colM, col2, col3 = st.columns([2,4,1,4,2], vertical_alignment="top")

    with col1:
        st.subheader("Encuestas disponibles")
        with st.container(height=400):
            if disponibles:
                for encuesta in disponibles:
                    colA, colB = st.columns([3, 2], vertical_alignment="center")
                    with colA:
                        st.write(f"**{encuesta['tema']}**")
                    with colB:
                        if st.button("Realizar encuesta", type="primary",  use_container_width=True, key=f"realizar_{encuesta['id']}"):
                            st.session_state.pagina_actual = "realizar_encuesta"
                            st.session_state.encuesta_id = encuesta["id"]
                            st.session_state.pregunta_actual = None
                            st.session_state.respuestas_encuesta = []
                            st.session_state.tiempo_inicio_pregunta = None
                            st.rerun()
            else:
                st.info("No tienes encuestas pendientes.")

    with col2:
        st.subheader("Encuestas realizadas")
        with st.container(height=400):
            if ya_realizadas_list:
                for encuesta in ya_realizadas_list:
                    st.write(f"**{encuesta['tema']}**")
            else:
                st.info("No has realizado ninguna encuesta todavía.")
    st.write(" ")
    colIzq, colMed, colDcha = st.columns([2,1,2])
    with colMed:
        if st.button(":red[Logout]", icon="🚪", use_container_width=True):
            st.session_state.pagina_actual = "inicio_sesion"
            st.session_state.username = None
            st.rerun()

def mostrar_realizar_encuesta():
    username = st.session_state.get("username", "Usuario")
    user_id = get_user_id(username)
    encuesta_id = st.session_state.get("encuesta_id")
    if encuesta_id is None:
        st.error("No hay encuesta seleccionada.")
        st.session_state.pagina_actual = "principal"
        st.rerun()
        return
    
    if st.session_state.get("pregunta_actual") is None:
        with open("proceso.txt", "w", encoding="utf-8") as f:
            f.write("")

    encuestas = get_all_surveys()
    encuesta = next((e for e in encuestas if e["id"] == encuesta_id), None)
    nombre_encuesta = encuesta["tema"] if encuesta else "Encuesta"

    st.markdown(f"<h2 style='text-align: center;'>Realizando encuesta: {nombre_encuesta}</h2>", unsafe_allow_html=True)
    realizar_encuesta_gpt(user_id, encuesta_id)