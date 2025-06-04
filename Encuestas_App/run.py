import streamlit as st
from database import create_users_table, create_surveys_table, create_respuestas_table, create_preguntas_table
import inicio_sesion, principal, principal_admin, registro

def main():
    
    # Crear la tabla de usuarios al iniciar la aplicación
    create_users_table()
    # Crear la tabla de encuestas al iniciar la aplicación
    create_surveys_table()
    # Crear la tabla de preguntas al iniciar la aplicación
    create_preguntas_table()
    # Crear la tabla de respuestas al iniciar la aplicación
    create_respuestas_table()

    # Inicializar el estado de sesión para la navegación
    if "pagina_actual" not in st.session_state:
        st.session_state.pagina_actual = "inicio_sesion"

    # Navegación entre páginas
    if st.session_state.pagina_actual == "inicio_sesion":
        inicio_sesion.mostrar_inicio_sesion()
    elif st.session_state.pagina_actual == "registro":
        registro.mostrar_registro_usuario()
    elif st.session_state.pagina_actual == "principal":
        principal.mostrar_ventana_principal()
    elif st.session_state.pagina_actual == "principal_admin":
        principal_admin.mostrar_ventana_principal_admin()
    elif st.session_state.pagina_actual == "realizar_encuesta":
        principal.mostrar_realizar_encuesta()

if __name__ == "__main__":
    main()