from flask import session, redirect, url_for, send_file
import mysql.connector
from conexion.conexionBD import obtener_conexion
import openpyxl
import os
import datetime
from conexion.conexionFB import *
from datetime import datetime
# ================= DASHBOARD KPIs =================

def obtener_kpis_dashboard():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    total_infantes = 0
    total_sesiones = 0
    total_instrumentos = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM infantes")
        total_infantes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sesiones_terapia")
        total_sesiones = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM instrumentos")
        total_instrumentos = cursor.fetchone()[0]

    finally:
        conexion.close()

    return total_infantes, total_sesiones, total_instrumentos  # Ahora devolvemos 3 valores

# ================== USUARIOS =======================

def listar_usuarios():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT u.id_usuario, u.cedula, u.nombre_usuario, u.apellido_usuario, u.correo, r.nombre_rol
            FROM usuarios u
            JOIN rol r ON u.id_rol = r.id_rol
            ORDER BY u.id_usuario DESC
        """
        cursor.execute(query)
        usuarios = cursor.fetchall()
    finally:
        conexion.close()
    return usuarios

def obtener_roles():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_rol, nombre_rol FROM rol")
        roles = cursor.fetchall()
    finally:
        conexion.close()
    return roles

def crear_usuario(cedula, nombre, apellido, correo, password, id_rol):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        query = """
            INSERT INTO usuarios (cedula, nombre_usuario, apellido_usuario, correo, password, id_rol)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (cedula, nombre, apellido, correo, password, id_rol))
        conexion.commit()
    finally:
        conexion.close()

def eliminar_usuario(id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        conexion.commit()
    finally:
        conexion.close()

# ================= INFANTES ======================

def listar_infantes(id_rol, id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT i.id_infante, i.nombre, i.fecha_nacimiento, g.nombre AS genero, u.nombre_usuario AS padre
            FROM infantes i
            LEFT JOIN generos g ON i.id_genero = g.id_genero
            LEFT JOIN usuarios u ON i.id_padre = u.id_usuario
        """
        if id_rol == 2:
            query += " WHERE i.id_padre = %s"
            cursor.execute(query, (id_usuario,))
        else:
            cursor.execute(query)
        infantes = cursor.fetchall()
    finally:
        conexion.close()
    return infantes

def obtener_generos():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_genero, nombre FROM generos")
        generos = cursor.fetchall()
    finally:
        conexion.close()
    return generos

def obtener_padres():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_usuario, nombre_usuario FROM usuarios WHERE id_rol = 2")
        padres = cursor.fetchall()
    finally:
        conexion.close()
    return padres

def crear_infante(nombre, apellido, cedula, id_genero, fecha_nacimiento, id_padre):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        query = """
            INSERT INTO infantes (nombre, apellido, cedula, id_genero, fecha_nacimiento, id_padre)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (nombre, apellido, cedula, id_genero, fecha_nacimiento, id_padre))
        conexion.commit()
    finally:
        conexion.close()


def listar_infantes(id_rol, id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        if id_rol == 1:
            # Administrador: ver todos los infantes
            query = """
                SELECT i.id_infante, i.nombre, i.apellido, i.cedula,
                       g.nombre AS genero, i.fecha_nacimiento,
                       u.nombre_usuario AS padre
                FROM infantes i
                LEFT JOIN generos g ON i.id_genero = g.id_genero
                LEFT JOIN usuarios u ON i.id_padre = u.id_usuario
                ORDER BY i.nombre ASC
            """
            cursor.execute(query)
        else:
            # Padre/madre: solo sus hijos
            query = """
                SELECT i.id_infante, i.nombre, i.apellido, i.cedula,
                       g.nombre AS genero, i.fecha_nacimiento,
                       u.nombre_usuario AS padre
                FROM infantes i
                LEFT JOIN generos g ON i.id_genero = g.id_genero
                LEFT JOIN usuarios u ON i.id_padre = u.id_usuario
                WHERE i.id_padre = %s
                ORDER BY i.nombre ASC
            """
            cursor.execute(query, (id_usuario,))

        infantes = cursor.fetchall()
    finally:
        conexion.close()
    return infantes


def eliminar_infante(id_infante):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM infantes WHERE id_infante = %s", (id_infante,))
        conexion.commit()
    finally:
        conexion.close()

# ================= LOG DE ACTIVIDAD ===================

def listar_logs(id_rol, id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT l.id_log, l.id_usuario, u.nombre_usuario, u.correo, l.accion, l.tabla_afectada, l.fecha
            FROM log_actividad l
            JOIN usuarios u ON l.id_usuario = u.id_usuario
        """
        if id_rol in [2, 3]:
            query += " WHERE l.id_usuario = %s"
            cursor.execute(query, (id_usuario,))
        else:
            cursor.execute(query)
        logs = cursor.fetchall()
    finally:
        conexion.close()
    return logs

def generar_reporte_logs_excel(id_rol, id_usuario):
    data_logs = listar_logs(id_rol, id_usuario)
    wb = openpyxl.Workbook()
    hoja = wb.active
    hoja.append(("ID Log", "Usuario", "Correo", "Acción", "Tabla Afectada", "Fecha"))

    for log in data_logs:
        hoja.append((log['id_log'], log['nombre_usuario'], log['correo'], log['accion'], log['tabla_afectada'], log['fecha']))

    fecha_actual = datetime.datetime.now()
    archivo_excel = f"Reporte_Log_{fecha_actual.strftime('%Y_%m_%d')}.xlsx"
    carpeta_descarga = "static/downloads-excel"
    ruta_descarga = os.path.join(os.getcwd(), carpeta_descarga)

    if not os.path.exists(ruta_descarga):
        os.makedirs(ruta_descarga)
        os.chmod(ruta_descarga, 0o755)

    ruta_archivo = os.path.join(ruta_descarga, archivo_excel)
    wb.save(ruta_archivo)
    return send_file(ruta_archivo, as_attachment=True)

def registrar_log(id_usuario, accion, tabla_afectada):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            INSERT INTO log_actividad (id_usuario, accion, tabla_afectada, fecha)
            VALUES (%s, %s, %s, NOW())
        """, (id_usuario, accion, tabla_afectada))
        conexion.commit()
    finally:
        conexion.close()

# ================= ROLES KPI =====================

def contar_usuarios_por_rol(id_rol):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE id_rol = %s", (id_rol,))
        return cursor.fetchone()[0]
    finally:
        conexion.close()

# ================= SESIONES CRUD =====================
def listar_sesiones():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            SELECT id_sesion, fecha_inicio 
            FROM sesiones_terapia
            ORDER BY fecha_inicio DESC
        """)
        sesiones = cursor.fetchall()

        sesiones_lista = []
        for sesion in sesiones:
            sesiones_lista.append({
                'id_sesion': sesion[0],
                'nombre_sesion': f"Sesión {sesion[0]}",
                'fecha_sesion': sesion[1].strftime('%Y-%m-%d %H:%M') if sesion[1] else ''
            })

        return sesiones_lista

    except Exception as e:
        print(f"Error al listar sesiones: {str(e)}")
        return []
    finally:
        conexion.close()

def eliminar_sesion(id_sesion):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM sesiones_terapia WHERE id_sesion = %s", (id_sesion,))
        conexion.commit()
    finally:
        conexion.close()
# ================= INFANTES CRUD =====================
def obtener_infantes():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_infante, nombre FROM infantes")
        return cursor.fetchall()
    finally:
        conexion.close()

# ================= TERAPIAS CRUD ===================== 

def obtener_terapias():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_terapia, nombre FROM terapias")
        terapias = cursor.fetchall()
    finally:
        conexion.close()
    return terapias

def obtener_terapeutas():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_usuario, nombre_usuario FROM usuarios WHERE id_rol = 3")
        terapeutas = cursor.fetchall()
    finally:
        conexion.close()
    return terapeutas


# ================= INSTRUMENTOS CONTROL MQTT ==================

def obtener_instrumentos_por_sesion(id_sesion):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT i.id_instrumento, i.nombre, COALESCE(e.estado, 0) AS estado
            FROM instrumentos i
            LEFT JOIN estado_instrumentos_sesion e
            ON i.id_instrumento = e.id_instrumento AND e.id_sesion = %s
        """
        cursor.execute(query, (id_sesion,))
        return cursor.fetchall()
    finally:
        conexion.close()

def actualizar_estado_instrumento(id_sesion, id_instrumento, estado):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            SELECT id_estado FROM estado_instrumentos_sesion
            WHERE id_sesion = %s AND id_instrumento = %s
        """, (id_sesion, id_instrumento))
        existe = cursor.fetchone()

        if existe:
            cursor.execute("""
                UPDATE estado_instrumentos_sesion
                SET estado = %s
                WHERE id_sesion = %s AND id_instrumento = %s
            """, (estado, id_sesion, id_instrumento))
        else:
            cursor.execute("""
                INSERT INTO estado_instrumentos_sesion (id_sesion, id_instrumento, estado)
                VALUES (%s, %s, %s)
            """, (id_sesion, id_instrumento, estado))

        conexion.commit()
    finally:
        conexion.close()

# ================= INSTRUMENTOS CRUD =====================
def obtener_instrumentos():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = "SELECT id_instrumento, nombre FROM instrumentos"
        cursor.execute(query)
        instrumentos = cursor.fetchall()
    finally:
        conexion.close()
    return instrumentos


# Obtener infantes para el select
def obtener_infantes():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_infante, nombre FROM infantes ORDER BY nombre")
    infantes = [{"id_infante": row[0], "nombre": row[1]} for row in cursor.fetchall()]
    cursor.close()
    conexion.close()
    return infantes

