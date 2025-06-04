import streamlit as st
from database import authenticate_user, get_user_by_email

def mostrar_inicio_sesion():
    """Muestra la página de inicio de sesión con navegación mediante botones."""
    st.set_page_config(page_title="inicio_sesion")
    st.markdown("<h1 style='text-align: center;'>ENCUESTAS TFG</h1>", unsafe_allow_html=True)
    st.write("")
    st.write("")
    st.write("")
    st.subheader("Inicio de sesión")
    st.write("")
    user_input = st.text_input("Usuario o correo electrónico", placeholder="Ingresa tu usuario o correo")
    st.write("")
    password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
    st.write("")

    col0, col1, colM, col2, col3 = st.columns([1,3,1,3,1])
    with col1:
        if st.button("Iniciar sesión", type="primary", use_container_width=True, help="Haz clic para iniciar sesión"):
            if not user_input or not password:
                st.error("Por favor, rellena ambos campos para poder iniciar sesión")
            else:
                username = user_input
                if "@" in user_input:
                    user = get_user_by_email(user_input)
                    if user:
                        username = user[1]
                user = authenticate_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    if username == "admin":
                        st.session_state.pagina_actual = "principal_admin"
                    else:
                        st.session_state.pagina_actual = "principal"
                    st.rerun()
                else:
                    st.error("Usuario/correo o contraseña incorrectos")

    with col2:
        if st.button("Registrar nuevo usuario", type="primary", use_container_width=True, help="Haz clic para ir a la ventana de registro"):
            st.session_state.pagina_actual = "registro"
            st.rerun()