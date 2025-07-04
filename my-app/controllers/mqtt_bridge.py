from conexion.conexionFB import *
from datetime import datetime
import time
from conexion.conexionBD import obtener_conexion

def crear_nueva_sesion(id_infante, id_terapeuta, usuario='sistema', origen='python'):
    timestamp_ms = int(time.time() * 1000)
    session_key = f"sesion_{timestamp_ms}"

    fecha_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cerrada = 0
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sesiones_terapia (id_infante, id_terapeuta, fecha_inicio, cerrada, firebase_key)
                VALUES (%s, %s, %s, %s, %s)
            """, (id_infante, id_terapeuta, fecha_inicio, cerrada, session_key))
            conexion.commit()
            id_sesion = cursor.lastrowid

        payload = {
            "estado":    "activa",
            "origen":    origen,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "usuario":   usuario
        }
        db.reference(session_key).set(payload)
        return id_sesion, session_key
    finally:
        conexion.close()

def finalizar_sesion(id_sesion, usuario='sistema', origen='python'):
    fecha_fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cerrada = 1

    # 1. Recuperar el session_key desde MySQL
    conexion = obtener_conexion()
    try:
        with conexion.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT firebase_key FROM sesiones_terapia WHERE id_sesion = %s", (id_sesion,))
            fila = cursor.fetchone()
            session_key = fila['firebase_key'] if fila and fila['firebase_key'] else None

        if not session_key:
            print(f"[ERROR] No se encontró la clave de Firebase para la sesión {id_sesion}")
            return False

        # 2. Actualizar la sesión en MySQL
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE sesiones_terapia
                SET fecha_fin = %s, cerrada = %s
                WHERE id_sesion = %s
            """, (fecha_fin, cerrada, id_sesion))
            conexion.commit()

        # 3. Actualizar estado en Firebase
        payload = {
            "estado":    "finalizada",
            "origen":    origen,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "usuario":   usuario
        }
        db.reference(session_key).update(payload)
        return True

    finally:
        conexion.close()