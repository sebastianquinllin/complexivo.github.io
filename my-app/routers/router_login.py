from app import app
from flask import render_template, request, flash, redirect, url_for, session
from controllers.funciones_login import *
from controllers.funciones_home import *

PATH_URL_LOGIN = "/public/login"

# --------------------------- Inicio principal ---------------------------

@app.route('/', methods=['GET'])
def inicio():
    if 'id' in session:
        return render_template('public/base_cpanel.html', dataLogin=dataLoginSesion())
    else:
        return render_template(f'{PATH_URL_LOGIN}/base_login.html')

# --------------------------- Perfil usuario ---------------------------

@app.route('/mi-perfil/<string:id>', methods=['GET'])
def perfil(id):
    if 'id' in session:
        info_perfil = info_perfil_session(id)
        roles = obtener_roles()
        return render_template('public/perfil/perfil.html',
                                info_perfil_session=info_perfil,
                                dataLogin=dataLoginSesion(),
                                roles=roles)
    else:
        return redirect(url_for('inicio'))

# --------------------------- Formulario de registro ---------------------------

@app.route('/register-user', methods=['GET'])
def register_user_form():
    roles = obtener_roles()
    return render_template(f'{PATH_URL_LOGIN}/auth_register.html',
                            dataLogin=dataLoginSesion(),
                            roles=roles)

# --------------------------- Guardar usuario registrado ---------------------------

@app.route('/saved-register', methods=['POST'])
def saved_register():
    if request.method == 'POST':
        cedula = request.form['cedula']
        name = request.form['name']
        surname = request.form['surname']
        correo = request.form['correo']
        id_rol = request.form['selectRol']
        pass_user = request.form['pass_user']

        resultData = recibeInsertRegisterUser(cedula, name, surname, correo, id_rol, pass_user)
        if resultData != 0:
            registrar_log(session['id'], 'CREAR', 'usuarios')
            flash('La cuenta fue creada correctamente.', 'success')
            return redirect(url_for('inicio'))
        else:
            return redirect(url_for('inicio'))
    else:
        flash('Error en la solicitud.', 'error')
        return redirect(url_for('inicio'))

# --------------------------- Actualizar datos de perfil ---------------------------

@app.route("/actualizar-datos-perfil/<int:id>", methods=['POST'])
def actualizarPerfil(id):
    if 'id' in session:
        respuesta = procesar_update_perfil(request.form, id)
        if respuesta == 1:
            flash('Los datos fueron actualizados correctamente.', 'success')
            return redirect(url_for('inicio'))
        elif respuesta == 0:
            flash('La contraseña actual es incorrecta.', 'error')
        elif respuesta == 2:
            flash('Las nuevas contraseñas no coinciden.', 'error')
        else:
            flash('Error en la actualización.', 'error')
        return redirect(url_for('perfil', id=id))
    else:
        flash('Debe iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

# --------------------------- Login principal ---------------------------

@app.route('/login', methods=['GET', 'POST'])
def loginCliente():
    if 'id' in session:
        return redirect(url_for('inicio'))

    if request.method == 'POST':
        cedula = request.form['cedula']
        pass_user = request.form['pass_user']

        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE cedula = %s", [cedula])
        account = cursor.fetchone()
        conexion.close()

        if account and check_password_hash(account['password'], pass_user):
            # Crear sesión segura
            session['id'] = account['id_usuario']
            session['name'] = account['nombre_usuario']
            session['cedula'] = account['cedula']
            session['rol'] = account['id_rol']

            registrar_log(session['id'], 'LOGIN', 'usuarios')

            flash('Sesión iniciada correctamente.', 'success')
            return redirect(url_for('inicio'))
        else:
            flash('Credenciales incorrectas.', 'error')
            return render_template(f'{PATH_URL_LOGIN}/base_login.html')

    return render_template(f'{PATH_URL_LOGIN}/base_login.html')

# --------------------------- Logout ---------------------------

@app.route('/closed-session', methods=['GET'])
def cerraSesion():
    session.clear()
    flash('Tu sesión fue cerrada correctamente.', 'success')
    return redirect(url_for('inicio'))
