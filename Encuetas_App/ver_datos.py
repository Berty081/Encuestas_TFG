import sqlite3
import json

def ver_datos():
    """Muestra los datos almacenados en todas las tablas de la base de datos."""
    conn = sqlite3.connect("encuestas_tfg.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, password, encuestas_realizadas, encuestas_abandonadas, motivos_finalizacion FROM users")
    usuarios = cursor.fetchall()
    print("Usuarios registrados en la base de datos:")
    if usuarios:
        for usuario in usuarios:
            print(f"ID: {usuario[0]}, Username: {usuario[1]}, Password: {usuario[2]}")
            print(f"  Encuestas realizadas: {usuario[3]}")
            print(f"  Encuestas abandonadas: {usuario[4]}")
            motivos = usuario[5]
            if motivos:
                try:
                    motivos_dict = json.loads(motivos)
                    print("  Motivos de finalización:")
                    for k, v in motivos_dict.items():
                        print(f"    Encuesta ID {k}: {v}")
                except Exception:
                    print(f"  Motivos de finalización (error de formato): {motivos}")
            else:
                print("  Motivos de finalización: Ninguno")
    else:
        print("No hay usuarios registrados en la base de datos.")

    print("\n" + "="*40 + "\n")

    cursor.execute("SELECT id, tema, numero_medio FROM surveys")
    encuestas = cursor.fetchall()
    print("Encuestas registradas en la base de datos:")
    if encuestas:
        for encuesta in encuestas:
            print(f"\nID: {encuesta[0]}")
            print(f"Tema: {encuesta[1]}")
            print(f"Número máximo de preguntas: {encuesta[2]}")
    else:
        print("No hay encuestas registradas en la base de datos.")

    print("\n" + "="*40 + "\n")

    cursor.execute("SELECT id, survey_id, texto, tipo_respuesta, opciones FROM preguntas")
    preguntas = cursor.fetchall()
    print("Preguntas registradas en la base de datos:")
    if preguntas:
        for pregunta in preguntas:
            print(f"\nID: {pregunta[0]}")
            print(f"Survey ID: {pregunta[1]}")
            print(f"Texto: {pregunta[2]}")
            print(f"Tipo de respuesta: {pregunta[3]}")
            if pregunta[3] == "opciones":
                print(f"Opciones: {pregunta[4]}")
    else:
        print("No hay preguntas registradas en la base de datos.")

    print("\n" + "="*40 + "\n")

    conn.close()

if __name__ == "__main__":
    ver_datos()