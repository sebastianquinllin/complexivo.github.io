from controllers.funciones_login import *
from controllers.funciones_home import *
from app import app
from flask import render_template, request, flash, redirect, url_for, session, send_file
from controllers.mqtt_client import publicar_mensaje
from controllers.mqtt_client import publicar_mensaje_custom

# ===============================================================
# ======================== USUARIOS =============================
# ===============================================================

@app.route("/lista-de-usuarios", methods=['GET'])
def usuarios():
    if 'id' in session:
        dataLogin = dataLoginSesion()
        lista_usuarios = listar_usuarios()
        roles = obtener_roles()
        return render_template('public/usuarios/lista_usuarios.html',
                                resp_usuariosBD=lista_usuarios,
                                dataLogin=dataLogin,
                                roles=roles)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route('/borrar-usuario/<string:id>', methods=['GET'])
def borrarUsuario(id):
    eliminar_usuario(id)
    registrar_log(session['id'], 'ELIMINAR', 'usuarios')
    flash('El Usuario fue eliminado correctamente', 'success')
    return redirect(url_for('usuarios'))

# ===============================================================
# ======================== LOG DE ACTIVIDAD =====================
# ===============================================================

@app.route("/reporte-log-actividad", methods=['GET'])
def reporte_log_actividad():
    if 'id' in session:
        userData = dataLoginSesion()
        logs = listar_logs(userData.get('rol'), userData.get('id'))
        return render_template('public/perfil/reportes.html',
                                reportes=logs, 
                                dataLogin=userData)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route("/descargar-reporte-log", methods=['GET'])
def descargar_reporte_log():
    if 'id' in session:
        userData = dataLoginSesion()
        return generar_reporte_logs_excel(userData.get('rol'), userData.get('id'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

# ===============================================================
# ======================== INFANTES =============================
# ===============================================================

@app.route("/infantes", methods=['GET'])
def listar_infantes_route():
    if 'id' in session:
        id_usuario = session['id']
        id_rol = session['rol']
        dataLogin = dataLoginSesion()
        infantes = listar_infantes(id_rol, id_usuario)
        return render_template('public/infantes/lista_infantes.html', infantes=infantes, dataLogin=dataLogin)
    else:
        return redirect(url_for('inicio'))

@app.route("/infantes/nuevo", methods=['GET'])
def nuevo_infante_route():
    if 'id' in session and session['rol'] == 1:
        generos = obtener_generos()
        padres = obtener_padres()
        dataLogin = dataLoginSesion()
        return render_template('public/infantes/formulario_infante.html',
                                generos=generos, padres=padres, infante=None, dataLogin=dataLogin)
    else:
        flash('Acceso denegado.')
        return redirect(url_for('listar_infantes_route'))

@app.route("/infantes/guardar", methods=['POST'])
def guardar_infante():
    if 'id' in session and session['rol'] == 1:
        nombre = request.form['nombre']
        id_genero = request.form['id_genero']
        fecha_nacimiento = request.form['fecha_nacimiento']
        id_padre = request.form['id_padre']
        crear_infante(nombre, id_genero, fecha_nacimiento, id_padre)
        registrar_log(session['id'], 'CREAR', 'infantes')
        return redirect(url_for('listar_infantes_route'))
    else:
        flash('Acceso denegado.')
        return redirect(url_for('inicio'))

@app.route("/infantes/editar/<int:id_infante>", methods=['GET'])
def editar_infante(id_infante):
    if 'id' in session and session['rol'] == 1:
        infante = obtener_infante_por_id(id_infante)
        generos = obtener_generos()
        padres = obtener_padres()
        dataLogin = dataLoginSesion()
        return render_template('public/infantes/formulario_infante.html',
                                infante=infante, generos=generos, padres=padres, dataLogin=dataLogin)
    else:
        flash('Acceso denegado.')
        return redirect(url_for('listar_infantes_route'))

@app.route("/infantes/actualizar/<int:id_infante>", methods=['POST'])
def actualizar_infante(id_infante):
    if 'id' in session and session['rol'] == 1:
        nombre = request.form['nombre']
        id_genero = request.form['id_genero']
        fecha_nacimiento = request.form['fecha_nacimiento']
        id_padre = request.form['id_padre']
        actualizar_infante(id_infante, nombre, id_genero, fecha_nacimiento, id_padre)
        registrar_log(session['id'], 'ACTUALIZAR', 'infantes')
        return redirect(url_for('listar_infantes_route'))
    else:
        flash('Acceso denegado.')
        return redirect(url_for('inicio'))

@app.route("/infantes/eliminar/<int:id_infante>", methods=['GET'])
def eliminar_infante_route(id_infante):
    if 'id' in session and session['rol'] == 1:
        eliminar_infante(id_infante)
        registrar_log(session['id'], 'ELIMINAR', 'infantes')
        return redirect(url_for('listar_infantes_route'))
    else:
        flash('Acceso denegado.')
        return redirect(url_for('inicio'))

# ===============================================================
# ======================== GRAFICAS =============================
# ===============================================================

@app.route("/lista-de-graficas", methods=['GET'])
def lista_de_graficas():
    if 'id' in session:
        dataLogin = dataLoginSesion()

        roles = obtener_roles()
        nombres_roles, cantidad_por_rol = [], []

        for rol in roles:
            id_rol = rol['id_rol']
            cantidad = contar_usuarios_por_rol(id_rol)
            nombres_roles.append(rol['nombre_rol'])
            cantidad_por_rol.append(cantidad)

        total_infantes, total_terapias, total_sesiones, total_instrumentos = obtener_kpis_dashboard()

        return render_template('public/grafica/lista_graficas.html',
                                dataLogin=dataLogin,
                                nombres_roles=nombres_roles,
                                cantidad_por_rol=cantidad_por_rol,
                                total_infantes=total_infantes,
                                total_terapias=total_terapias,
                                total_sesiones=total_sesiones,
                                total_instrumentos=total_instrumentos)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

# ===============================================================
# ======================== SESIONES CRUD ========================
# ===============================================================

@app.route("/sesiones", methods=['GET'])
def listar_sesiones_route():
    if 'id' in session:
        dataLogin = dataLoginSesion()
        sesiones = listar_sesiones()
        return render_template('public/sesiones/lista_sesiones.html', sesiones=sesiones, dataLogin=dataLogin)
    else:
        return redirect(url_for('inicio'))

@app.route("/sesiones/nueva", methods=['GET', 'POST'])
def nueva_sesion_route():
    if 'id' in session:
        dataLogin = dataLoginSesion()
        if request.method == 'POST':
            id_infante = request.form['id_infante']
            id_terapia = request.form['id_terapia']
            id_terapeuta = request.form['id_terapeuta']
            crear_sesion(id_infante, id_terapia, id_terapeuta)
            flash('Sesión creada e iniciada.', 'success')
            return redirect(url_for('listar_sesiones_route'))

        infantes = obtener_infantes()
        terapias = obtener_terapias()
        terapeutas = obtener_terapeutas()

        return render_template('public/sesiones/formulario_sesion.html',
                                infantes=infantes, terapias=terapias, terapeutas=terapeutas, dataLogin=dataLogin)
    else:
        return redirect(url_for('inicio'))

@app.route("/sesiones/finalizar/<int:id_sesion>", methods=['GET'])
def finalizar_sesion_route(id_sesion):
    if 'id' in session:
        finalizar_sesion(id_sesion)
        flash('Sesión finalizada.', 'success')
        return redirect(url_for('listar_sesiones_route'))
    else:
        return redirect(url_for('inicio'))

@app.route("/sesiones/eliminar/<int:id_sesion>", methods=['GET'])
def eliminar_sesion_route(id_sesion):
    if 'id' in session:
        eliminar_sesion(id_sesion)
        flash('Sesión eliminada.', 'success')
        return redirect(url_for('listar_sesiones_route'))
    else:
        return redirect(url_for('inicio'))

# ===============================================================
# ==================== CONTROL DE SESION EN VIVO (MQTT + DB) ====
# ===============================================================

@app.route("/sesion/control/<int:id_sesion>", methods=['GET'])
def control_sesion(id_sesion):
    if 'id' in session:
        dataLogin = dataLoginSesion()
        instrumentos = obtener_instrumentos_por_sesion(id_sesion)
        return render_template('public/sesiones/control_sesion.html',
                                instrumentos=instrumentos, id_sesion=id_sesion, dataLogin=dataLogin)
    else:
        return redirect(url_for('inicio'))

@app.route("/sesion/actualizar_instrumento", methods=['POST'])
def actualizar_instrumento_estado():
    if 'id' in session:
        id_sesion = request.form['id_sesion']
        id_instrumento = request.form['id_instrumento']
        estado = int(request.form['estado'])
        actualizar_estado_instrumento(id_sesion, id_instrumento, estado)
        publicar_mensaje(id_instrumento, estado)
        return {"status": "ok"}
    else:
        return {"status": "unauthorized"}, 401

# ===============================================================
# ===================== CONTROL DE INSTRUMENTOS =================
# ===============================================================
@app.route("/control-instrumentos", methods=['GET'])
def control_instrumentos():
    if 'id' in session:
        dataLogin = dataLoginSesion()
        instrumentos = obtener_instrumentos()  # Esta función debería existir para traer todos los instrumentos.
        return render_template('public/grafica/control_instrumentos.html',
                                instrumentos=instrumentos, dataLogin=dataLogin)
    else:
        return redirect(url_for('inicio'))
    
@app.route("/api/graficas-avanzadas/<int:id_instrumento>")
def api_graficas_avanzadas(id_instrumento):
    fecha_inicio = request.args.get('inicio')
    fecha_fin = request.args.get('fin')

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT s.id_sesion, s.fecha_inicio, i.duracion_segundos, i.aceleracion, i.velocidad, i.giros
            FROM instrumentos_sesion i
            JOIN sesiones_terapia s ON i.id_sesion = s.id_sesion
            WHERE i.id_instrumento = %s AND s.fecha_inicio BETWEEN %s AND %s
            ORDER BY s.fecha_inicio
        """
        cursor.execute(query, (id_instrumento, fecha_inicio, fecha_fin))
        resultados = cursor.fetchall()

        # Agregar ID de sesión para identificar claramente las sesiones
        sesiones = [f"Sesión {row['id_sesion']} ({row['fecha_inicio']})" for row in resultados]
        duraciones = [row['duracion_segundos'] for row in resultados]
        aceleraciones = [row['aceleracion'] for row in resultados]
        velocidades = [row['velocidad'] for row in resultados]
        giros = [row['giros'] for row in resultados]

        return {
            "sesiones": sesiones,
            "duraciones": duraciones,
            "aceleraciones": aceleraciones,
            "velocidades": velocidades,
            "giros": giros
        }
    finally:
        conexion.close()


@app.route("/graficas-avanzadas")
def graficas_avanzadas():
    if 'id' in session:
        dataLogin = dataLoginSesion()
        instrumentos = obtener_instrumentos()
        return render_template('public/grafica/graficas_avanzadas.html', instrumentos=instrumentos, dataLogin=dataLogin)
    else:
        return redirect(url_for('inicio'))

@app.route("/api/datos-instrumento/<int:id_instrumento>")
def api_datos_instrumento(id_instrumento):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT s.id_sesion, i.duracion_segundos, i.aceleracion, i.velocidad, i.giros
            FROM instrumentos_sesion i
            JOIN sesiones_terapia s ON i.id_sesion = s.id_sesion
            WHERE i.id_instrumento = %s
            ORDER BY s.fecha_inicio ASC
        """
        cursor.execute(query, (id_instrumento,))
        resultados = cursor.fetchall()

        sesiones = [f"Sesión {row['id_sesion']}" for row in resultados]
        duraciones = [row['duracion_segundos'] for row in resultados]
        aceleraciones = [row['aceleracion'] for row in resultados]
        velocidades = [row['velocidad'] for row in resultados]
        giros = [row['giros'] for row in resultados]

        return {
            "sesiones": sesiones,
            "duraciones": duraciones,
            "aceleraciones": aceleraciones,
            "velocidades": velocidades,
            "giros": giros
        }
    finally:
        conexion.close()

# ------------------------ CONTROL LED ------------------------ #
@app.route("/control-led", methods=['POST'])
def control_led():
    if 'id' in session:
        id_instrumento = request.form['id_instrumento']
        led = request.form['led']
        topic = f"instrumento/{id_instrumento}/led"
        publicar_mensaje_custom(topic, led)
        return {"status": "ok"}
    else:
        return {"status": "unauthorized"}, 401

# ------------------------ CONTROL MÚSICA USO ------------------------ #
@app.route("/control-musica-uso", methods=['POST'])
def control_musica_uso():
    if 'id' in session:
        id_instrumento = request.form['id_instrumento']
        musica = request.form['musica']
        topic = f"instrumento/{id_instrumento}/musica/uso"
        publicar_mensaje_custom(topic, musica)
        return {"status": "ok"}
    else:
        return {"status": "unauthorized"}, 401

# ------------------------ CONTROL MÚSICA REPOSO ------------------------ #
@app.route("/control-musica-reposo", methods=['POST'])
def control_musica_reposo():
    if 'id' in session:
        id_instrumento = request.form['id_instrumento']
        musica = request.form['musica']
        topic = f"instrumento/{id_instrumento}/musica/reposo"
        publicar_mensaje_custom(topic, musica)
        return {"status": "ok"}
    else:
        return {"status": "unauthorized"}, 401

# ------------------------ CONTROL VOLUMEN ------------------------ #
@app.route("/control-volumen", methods=['POST'])
def control_volumen():
    if 'id' in session:
        id_instrumento = request.form['id_instrumento']
        volumen = request.form['volumen']
        topic = f"instrumento/{id_instrumento}/volumen"
        publicar_mensaje_custom(topic, volumen)
        return {"status": "ok"}
    else:
        return {"status": "unauthorized"}, 401