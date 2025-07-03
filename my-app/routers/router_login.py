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

@app.route('/mi-perfil/<int:id>', methods=['GET'])
def perfil(id):
    if 'id' not in session:
        flash("Primero debes iniciar sesión.", "error")
        return redirect(url_for('inicio'))

    if session['id'] != id:
        flash("No tienes permiso para ver este perfil.", "error")
        return redirect(url_for('inicio'))

    info_perfil = obtener_info_perfil(id)
    roles = obtener_roles()

    return render_template('public/perfil/perfil.html',
                           info_perfil_session=info_perfil,
                           dataLogin=dataLoginSesion(),
                           roles=roles)

# --------------------------- Formulario de registro ---------------------------

@app.route('/register-user', methods=['GET'])
def register_user_form():
    roles = obtener_roles()
    return render_template(f'{PATH_URL_LOGIN}/auth_register.html',
                            dataLogin=dataLoginSesion(),
                            roles=roles)

# --------------------------- Guardar usuario registrado ---------------------------

from werkzeug.security import generate_password_hash

@app.route("/saved-register", methods=['POST'])
def saved_register():
    cedula = request.form['cedula']
    nombre = request.form['name']
    apellido = request.form['surname']
    correo = request.form['correo']
    pass_user = request.form['pass_user']
    id_rol = request.form['selectRol']

    if not validar_telefono(cedula):
        flash('La cédula debe tener 10 dígitos válidos', 'error')
        return redirect(url_for('register_user_form'))

    if not validar_email(correo):
        flash('El correo electrónico no es válido', 'error')
        return redirect(url_for('register_user_form'))

    if not validar_clave(pass_user):
        flash('La contraseña debe tener al menos 8 caracteres, incluyendo mayúsculas, minúsculas y números', 'error')
        return redirect(url_for('register_user_form'))

    try:
        hashed_password = generate_password_hash(pass_user, method='scrypt', salt_length=16)
        crear_usuario(cedula, nombre, apellido, correo, hashed_password, id_rol)
        flash('Usuario registrado exitosamente.', 'success')
        return redirect(url_for('usuarios'))
    except Exception as e:
        flash(f'Ocurrió un error: {e}', 'error')
        return redirect(url_for('register_user_form'))

# --------------------------- Actualizar datos de perfil ---------------------------
@app.route("/actualizarPerfil/<int:id>", methods=["POST"])
def actualizarPerfil(id):
    if 'id' not in session or session['id'] != id:
        flash("No tienes permiso para actualizar este perfil.", "error")
        return redirect(url_for("inicio"))

    pass_actual = request.form.get("pass_actual")
    new_pass = request.form.get("new_pass_user")
    repetir_pass = request.form.get("repetir_pass_user")

    # Validación: contraseñas coinciden
    if new_pass != repetir_pass:
        flash("Las nuevas contraseñas no coinciden.", "error")
        return redirect(url_for("perfil", id=id))

    # Validación: formato seguro de contraseña nueva
    if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}$', new_pass):
        flash("La nueva contraseña debe tener al menos 8 caracteres, incluyendo mayúsculas, minúsculas y números.", "error")
        return redirect(url_for("perfil", id=id))

    try:
        conexion = obtener_conexion()
        with conexion.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT password FROM usuarios WHERE id_usuario = %s", (id,))
            usuario = cursor.fetchone()

            if not usuario:
                flash("Usuario no encontrado.", "error")
                return redirect(url_for("perfil", id=id))

            if not check_password_hash(usuario["password"], pass_actual):
                flash("La contraseña actual es incorrecta.", "error")
                return redirect(url_for("perfil", id=id))

            nueva_hash = generate_password_hash(new_pass, method="scrypt", salt_length=16)

            cursor.execute("UPDATE usuarios SET password = %s WHERE id_usuario = %s", (nueva_hash, id))
            conexion.commit()

            flash("Contraseña actualizada correctamente.", "success")
            return redirect(url_for("perfil", id=id))

    except Exception as e:
        flash(f"Error al actualizar: {e}", "error")
        return redirect(url_for("inicio"))
    finally:
        conexion.close()

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
