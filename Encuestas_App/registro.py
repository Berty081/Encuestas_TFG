import streamlit as st
from database import add_user, get_user_by_email, get_user_id
import re

def mostrar_registro_usuario():
    st.set_page_config(page_title="registro")

    """Muestra la página de registro de usuario."""
    st.markdown("<style>.block-container {padding-top: 1.8rem;}</style>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Registrar nuevo usuario</h1>", unsafe_allow_html=True)
    nombre = st.text_input("Nombre", placeholder="Introduce tu nombre")
    apellidos = st.text_input("Apellidos", placeholder="Introduce tus apellidos")
    email = st.text_input("Correo electrónico", placeholder="Introduce tu correo electrónico")
    username = st.text_input("Nombre de usuario", placeholder="Elige un nombre de usuario")
    password = st.text_input("Contraseña", type="password", placeholder="Elige una contraseña")
    password_repeat = st.text_input("Repite la contraseña", type="password", placeholder="Repite la contraseña")

    colA, colB = st.columns([2, 5], vertical_alignment="center")
    with colA:
        error=0
        if st.button("Registrar", type="primary", use_container_width=True, help="Haz clic para registrar un nuevo usuario"):
            # 1. Comprobar que todos los campos están rellenos
            if not all([nombre, apellidos, email, username, password, password_repeat]):
                error=1
            # 2. Comprobar que las contraseñas coinciden
            elif password != password_repeat:
                error=2
            # 3. Comprobar formato de email
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                error=6
            # 4. Comprobar si el nombre de usuario ya existe
            elif get_user_id(username) is not None:
                error=3
            # 5. Comprobar si el correo electrónico ya existe
            elif get_user_by_email(email) is not None:
                error=4
            else:
                add_user(username, password, nombre, apellidos, email)
                error=5
                st.session_state.pagina_actual = "inicio_sesion"
                st.rerun()
        if st.button(":red[Volver atrás]", icon="↩️", use_container_width=True, help="Haz clic para volver a la página de inicio de sesión"):
            st.session_state.pagina_actual = "inicio_sesion"
            st.rerun()
    with colB:
        if error==1:
            st.error("Por favor, rellena todos los campos.")
        elif error==2:
            st.error("Las contraseñas no coinciden.")
        elif error==3:
            st.error("El nombre de usuario ya está en uso.")
        elif error==4:
            st.error("Ya existe una cuenta con ese correo electrónico.")
        elif error==5:
            st.success("Usuario registrado exitosamente")
        elif error==6:
            st.error("El correo electrónico no tiene un formato válido.")
