# Importando paquetes desde flask
from flask import session, flash
from conexion.conexionBD import obtener_conexion
from werkzeug.security import check_password_hash, generate_password_hash

# Validación de registro nuevo
def recibeInsertRegisterUser(cedula, name, surname, correo, id_rol, pass_user):
    respuestaValidar = validarDataRegisterLogin(cedula, name, surname, pass_user, correo)

    if (respuestaValidar):
        nueva_password = generate_password_hash(pass_user, method='scrypt')
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            sql = """
            INSERT INTO usuarios(cedula, nombre_usuario, apellido_usuario, correo, id_rol, password) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            valores = (cedula, name, surname, correo, id_rol, nueva_password)
            cursor.execute(sql, valores)
            conexion.commit()
            return cursor.rowcount
        except Exception as e:
            print(f"Error en el Insert users: {e}")
            return []
        finally:
            conexion.close()
    else:
        return False

# Validando la data del registro
def validarDataRegisterLogin(cedula, name, surname, pass_user, correo):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        querySQL = "SELECT * FROM usuarios WHERE cedula = %s OR correo = %s"
        cursor.execute(querySQL, (cedula, correo))
        userBD = cursor.fetchone()

        if userBD is not None:
            flash('Ya existe un usuario registrado con esta cédula o correo.', 'error')
            return False
        elif not cedula or not name or not pass_user or not correo:
            flash('Por favor complete todos los campos del formulario.', 'error')
            return False
        else:
            return True
    except Exception as e:
        print(f"Error en validarDataRegisterLogin : {e}")
        return []
    finally:
        conexion.close()

# Obtener datos del perfil para edición
def info_perfil_session(id):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        querySQL = "SELECT id_usuario, nombre_usuario, apellido_usuario, cedula, correo, id_rol FROM usuarios WHERE id_usuario = %s"
        cursor.execute(querySQL, (id,))
        info_perfil = cursor.fetchone()
        return info_perfil
    except Exception as e:
        print(f"Error en info_perfil_session : {e}")
        return []
    finally:
        conexion.close()

# Procesar actualización de perfil (para el propio usuario logueado)
def procesar_update_perfil(data_form, id_usuario):
    cedula = data_form['cedula']
    nombre_usuario = data_form['name']
    apellido_usuario = data_form['surname']
    correo = data_form['correo']
    id_rol = data_form.get('selectRol')

    # Este es el punto crítico:
    new_pass_user = data_form.get('new_pass_user')
    repetir_pass_user = data_form.get('repetir_pass_user')
    pass_actual = data_form.get('pass_actual')

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        userDB = cursor.fetchone()

        # Si no hay cambio de contraseña:
        if not pass_actual and not new_pass_user:
            update_query = """
                UPDATE usuarios SET nombre_usuario = %s, apellido_usuario = %s, correo = %s, id_rol = %s
                WHERE id_usuario = %s
            """
            cursor.execute(update_query, (nombre_usuario, apellido_usuario, correo, id_rol, id_usuario))
            conexion.commit()
            return 1

        # Si hay cambio de contraseña:
        if not check_password_hash(userDB['password'], pass_actual):
            return 0

        if new_pass_user != repetir_pass_user:
            return 2

        nueva_password = generate_password_hash(new_pass_user, method='scrypt')
        update_query = """
            UPDATE usuarios SET nombre_usuario = %s, apellido_usuario = %s, correo = %s, password = %s, id_rol = %s
            WHERE id_usuario = %s
        """
        cursor.execute(update_query, (nombre_usuario, apellido_usuario, correo, nueva_password, id_rol, id_usuario))
        conexion.commit()
        return 1

    except Exception as e:
        print(f"Error en procesar_update_perfil : {e}")
        return []
    finally:
        conexion.close()

# Guardar la data de la sesión (opcional para tu uso en plantillas)
def dataLoginSesion():
    inforLogin = {
        "id": session['id'],
        "name": session['name'],
        "cedula": session['cedula'],
        "rol": session['rol']
    }
    return inforLogin
