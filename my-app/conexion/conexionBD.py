import mysql.connector

def obtener_conexion():
    print("Estableciendo conexión a la base de datos...")
    try:
        connection = mysql.connector.connect(
            host="35.226.60.4",
            port=3306,
            user="diego",
            passwd="emilio1102",
            database="aula_multisensorial",
            charset='utf8mb4',
            raise_on_warnings=True
        )

        if connection.is_connected():
            print("Conexión exitosa a la base de datos")
            return connection

    except mysql.connector.Error as error:
        print(f"No se pudo conectar a la base de datos: {error}")
    return None  # Devuelve None si falla la conexión
