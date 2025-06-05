# Importando librería mysql.connector para conectar Python con MySQL
import mysql.connector

def obtener_conexion():
    print("Estableciendo conexión a la base de datos...")
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            passwd="1234",
            database="aula_multisensorial",
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            raise_on_warnings=True
        )

        if connection.is_connected():
            print("Conexión exitosa a la base de datos")
            return connection

    except mysql.connector.Error as error:
        print(f"No se pudo conectar a la base de datos: {error}")
