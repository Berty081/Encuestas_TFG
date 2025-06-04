from database import (
    create_connection,
    create_users_table,
    create_surveys_table,
    create_preguntas_table,
    create_respuestas_table,
    add_user,
    marcar_encuesta_realizada,
    marcar_encuesta_abandonada,
)
import random

def reset_tables():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS respuestas")
    cursor.execute("DROP TABLE IF EXISTS preguntas")
    cursor.execute("DROP TABLE IF EXISTS surveys")
    cursor.execute("DROP TABLE IF EXISTS users")
    conn.commit()
    conn.close()

def poblar_datos():
    # Crear tablas
    create_users_table()
    create_surveys_table()
    create_preguntas_table()
    create_respuestas_table()

    # Usuarios
    add_user("admin", "admin")
    add_user("Alberto8", "admin")
    add_user("Alberto9", "admin")

    nombres = [
        "Ana", "Luis", "Carlos", "Marta", "Elena", "Pedro", "Lucía", "Javier", "Sara", "David",
        "Paula", "Manuel", "Carmen", "Raúl", "Patricia", "Diego", "Laura", "Sergio", "María", "Andrés"
    ]
    for i, nombre in enumerate(nombres, start=1):
        add_user(f"{nombre}{i}", "1234")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO surveys (id, tema, numero_medio, objetivos) VALUES (1, ?, ?, ?)", 
                   ("Elecciones España", 25, "Analizar la percepción ciudadana sobre la política, el sistema electoral y la situación actual en España."))
    cursor.execute("INSERT INTO surveys (id, tema, numero_medio, objetivos) VALUES (2, ?, ?, ?)", 
                   ("Hábitos deportivos", 15, "Conocer los hábitos, motivaciones y barreras de la población respecto a la práctica deportiva."))
    
    preguntas_1 = [
        ("¿Cuál es tu sexo?", "opciones", "Masculino;Femenino;Otro"),
        ("¿Cuál es tu edad?", "libre", None),
        ("¿Cuál es tu nivel de interés en la política española?", "opciones", "Alto;Medio;Bajo"),
        ("¿Crees en la democracia española?", "opciones", "Sí;No;No estoy seguro"),
        ("¿Estás contento con el gobierno actual?", "opciones", "Sí;No;Neutral"),
        ("¿A quién votarías en las próximas elecciones?", "libre", None),
        ("¿Qué es lo que más valoras de un partido político?", "libre", None),
        ("¿Consideras que la corrupción es un problema grave en la política española?", "opciones", "Sí;No;No estoy seguro"),
        ("¿Cómo calificarías la transparencia del gobierno actual?", "opciones", "Alta;Media;Baja"),
        ("¿Qué aspecto de la gestión gubernamental te gustaría que mejorara?", "libre", None),
        ("¿Crees que se están abordando adecuadamente los problemas sociales en España?", "opciones", "Sí;No;No estoy seguro"),
        ("¿Qué medidas crees que son prioritarias para mejorar la situación del país?", "libre", None),
        ("¿Te sientes representado por algún partido político actualmente?", "opciones", "Sí;No;No estoy seguro"),
        ("¿Qué opinas sobre el sistema electoral español?", "opciones", "A favor;En contra;Neutral"),
        ("¿Cómo evalúas la situación económica actual de España?", "opciones", "Buena;Regular;Mala"),
        ("¿Crees que la política española es inclusiva y representa a todos los ciudadanos por igual?", "opciones", "Sí;No;No estoy seguro"),
        ("¿Qué papel crees que deberían tener los partidos minoritarios en el panorama político español?", "libre", None),
        ("¿Qué opinas sobre las coaliciones entre partidos políticos?", "opciones", "A favor;En contra;Neutral"),
        ("¿Consideras que la situación política actual fomenta la participación ciudadana?", "opciones", "Sí;No;No estoy seguro"),
        ("¿Qué importancia le das a la educación política en la formación de los ciudadanos?", "opciones", "Alta;Media;Baja"),
        ("¿Qué medidas crees que podrían fortalecer la democracia en España?", "libre", None),
        ("¿Crees que los medios de comunicación ejercen una influencia adecuada en la opinión pública?", "opciones", "Sí;No;No estoy seguro"),
        ("¿Qué opinas sobre la independencia de los poderes del Estado en España?", "opciones", "A favor;En contra;Neutral"),
        ("¿Cómo percibes la estabilidad política en España actualmente?", "opciones", "Alta;Media;Baja"),
        ("¿Consideras que los partidos políticos actuales están preparados para afrontar los desafíos del país?", "opciones", "Sí;No;No estoy seguro"),
    ]
    for idx, (texto, tipo, opciones) in enumerate(preguntas_1, start=1):
        cursor.execute(
            "INSERT INTO preguntas (id, survey_id, texto, tipo_respuesta, opciones) VALUES (?, 1, ?, ?, ?)",
            (idx, texto, tipo, opciones)
        )

    preguntas_2 = [
        ("¿Cuál es tu sexo?", "opciones", "Masculino;Femenino;Otro"),
        ("¿Cuál es tu edad?", "libre", None),
        ("¿Qué te motivó a participar en esta encuesta sobre hábitos deportivos?", "libre", None),
        ("¿Crees que el deporte es bueno para tu salud?", "opciones", "Sí;No;No estoy seguro"),
        ("¿Con qué frecuencia haces deporte?", "opciones", "Todos los días;Varias veces por semana;Una vez por semana;Menos de una vez por semana"),
        ("¿Qué tipo de actividades deportivas sueles realizar?", "libre", None),
        ("¿Qué te impide hacer más deporte?", "libre", None),
        ("¿Qué beneficios crees que te aporta la práctica deportiva?", "libre", None),
        ("¿Te gustaría tener más tiempo para dedicar al deporte?", "opciones", "Sí;No;No estoy seguro"),
        ("¿Cuál es tu deporte favorito?", "libre", None),
        ("¿Te gustaría participar en competiciones deportivas?", "opciones", "Sí;No;Tal vez"),
        ("¿Qué crees que te permitiría hacer más deporte?", "libre", None),
        ("¿Has experimentado algún cambio positivo en tu salud desde que practicas deporte?", "opciones", "Sí;No;No lo sé"),
        ("¿Consideras que la falta de instalaciones deportivas en tu zona afecta a tu práctica deportiva?", "opciones", "Sí;No;No aplica"),
        ("¿Qué sugerencias darías para fomentar la práctica deportiva en la comunidad?", "libre", None),
    ]
    for idx, (texto, tipo, opciones) in enumerate(preguntas_2, start=26):
        cursor.execute(
            "INSERT INTO preguntas (id, survey_id, texto, tipo_respuesta, opciones) VALUES (?, 2, ?, ?, ?)",
            (idx, texto, tipo, opciones)
        )

    conn.commit()

    cursor.execute("SELECT id, username FROM users WHERE username NOT IN ('admin', 'Alberto8', 'Alberto9')")
    usuarios = cursor.fetchall()

    usuarios_enc1 = usuarios[:10]
    usuarios_enc2 = usuarios[10:]

    abandonan_enc1 = usuarios_enc1[:2]
    falta_interes_enc1 = usuarios_enc1[2:4]
    terminan_enc1 = usuarios_enc1[4:]

    abandonan_enc2 = usuarios_enc2[:2]
    falta_interes_enc2 = usuarios_enc2[2:4]
    terminan_enc2 = usuarios_enc2[4:]

    for user_id, username in usuarios_enc1:
        if (user_id, username) in abandonan_enc1:
            num_preg = len(preguntas_1) // 2
        else:
            num_preg = len(preguntas_1)
        for idx, (texto, tipo, opciones) in enumerate(preguntas_1[:num_preg], start=1):
            if tipo == "opciones":
                opciones_lista = opciones.split(";")
                respuesta = random.choice(opciones_lista)
            else:
                respuesta = f"Respuesta libre de {username} a '{texto}'"
            cursor.execute(
                "INSERT INTO respuestas (user_id, survey_id, pregunta_id, respuesta) VALUES (?, ?, ?, ?)",
                (user_id, 1, idx, respuesta)
            )

    for user_id, username in usuarios_enc2:
        if (user_id, username) in abandonan_enc2:
            num_preg = len(preguntas_2) // 2
        else:
            num_preg = len(preguntas_2)
        for idx, (texto, tipo, opciones) in enumerate(preguntas_2[:num_preg], start=26):
            if tipo == "opciones":
                opciones_lista = opciones.split(";")
                respuesta = random.choice(opciones_lista)
            else:
                respuesta = f"Respuesta libre de {username} a '{texto}'"
            cursor.execute(
                "INSERT INTO respuestas (user_id, survey_id, pregunta_id, respuesta) VALUES (?, ?, ?, ?)",
                (user_id, 2, idx, respuesta)
            )

    conn.commit()
    conn.close()

    for user_id, username in abandonan_enc1:
        marcar_encuesta_abandonada(user_id, 1)
    for user_id, username in abandonan_enc2:
        marcar_encuesta_abandonada(user_id, 2)
    for user_id, username in falta_interes_enc1:
        marcar_encuesta_realizada(user_id, 1, "Por falta de interés")
    for user_id, username in falta_interes_enc2:
        marcar_encuesta_realizada(user_id, 2, "Por falta de interés")
    for user_id, username in terminan_enc1:
        marcar_encuesta_realizada(user_id, 1, "Terminación de la encuesta")
    for user_id, username in terminan_enc2:
        marcar_encuesta_realizada(user_id, 2, "Terminación de la encuesta")

if __name__ == "__main__":
    reset_tables()
    poblar_datos()
    print("Base de datos reseteada y poblada con los datos de ejemplo y usuarios simulados.")