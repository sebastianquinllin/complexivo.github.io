from controllers.funciones_login import *
from controllers.funciones_home import *
from app import app
from flask import jsonify
from datetime import datetime, date 
import re
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
        return render_template('public/infantes/lista_infantes.html',
                               infantes=infantes,
                               dataLogin=dataLogin)
    else:
        return redirect(url_for('inicio'))


@app.route("/infantes/nuevo", methods=['GET'])
def nuevo_infante_route():
    try:
        if 'id' not in session:
            flash('Debes iniciar sesión.', 'error')
            return redirect(url_for('inicio'))

        if session['rol'] != 1:
            flash('Acceso denegado. Solo administradores pueden registrar infantes.', 'error')
            return redirect(url_for('listar_infantes_route'))

        generos = obtener_generos()
        padres = obtener_padres()
        dataLogin = dataLoginSesion()
        fecha_actual = date.today().strftime('%Y-%m-%d')

        print("DEBUG ➤ generos:", generos)
        print("DEBUG ➤ padres:", padres)
        print("DEBUG ➤ fecha_actual:", fecha_actual)

        return render_template('public/infantes/formulario_infante.html',
                               generos=generos,
                               padres=padres,
                               infante=None,
                               dataLogin=dataLogin,
                               fecha_actual=fecha_actual)

    except Exception as e:
        print("❌ ERROR en nuevo_infante_route:", str(e))
        flash(f"Ocurrió un error al cargar el formulario: {e}", "error")
        return redirect(url_for('listar_infantes_route'))
    
@app.route("/infantes/guardar", methods=['POST'])
def guardar_infante():
    if 'id' not in session or session['rol'] != 1:
        flash('Acceso denegado.')
        return redirect(url_for('inicio'))

    # Obtener datos del formulario
    nombre = request.form.get('nombre', '').strip()
    apellido = request.form.get('apellido', '').strip()
    cedula = request.form.get('cedula', '').strip()
    id_genero = request.form.get('id_genero')
    fecha_nacimiento = request.form.get('fecha_nacimiento')
    id_padre = request.form.get('id_padre')

    # Validaciones de campos
    if not nombre or not apellido or not cedula or not id_genero or not fecha_nacimiento or not id_padre:
        flash("Todos los campos son obligatorios.", "error")
        return redirect(url_for('nuevo_infante_route'))

    if not re.fullmatch(r'\d{10}', cedula):
        flash("La cédula debe contener exactamente 10 dígitos numéricos.", "error")
        return redirect(url_for('nuevo_infante_route'))

    try:
        fecha_nac = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
        if fecha_nac > datetime.today():
            flash("La fecha de nacimiento no puede ser en el futuro.", "error")
            return redirect(url_for('nuevo_infante_route'))
    except ValueError:
        flash("La fecha de nacimiento no es válida.", "error")
        return redirect(url_for('nuevo_infante_route'))

    # Guardar en base de datos
    try:
        crear_infante(nombre, apellido, cedula, id_genero, fecha_nacimiento, id_padre)
        registrar_log(session['id'], 'CREAR', 'infantes')
        flash("Infante registrado correctamente.", "success")
        return redirect(url_for('listar_infantes_route'))

    except Exception as e:
        flash(f"Error al guardar infante: {e}", "error")
        return redirect(url_for('nuevo_infante_route'))
    

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

        # Obtener los KPIs (actualizados, ahora devuelve 3 valores)
        total_infantes, total_sesiones, total_instrumentos = obtener_kpis_dashboard()

        # Obtener los roles y la cantidad de usuarios por rol
        roles = obtener_roles()
        nombres_roles, cantidad_por_rol = [], []

        for rol in roles:
            id_rol = rol['id_rol']
            cantidad = contar_usuarios_por_rol(id_rol)
            nombres_roles.append(rol['nombre_rol'])
            cantidad_por_rol.append(cantidad)

        # Obtener los instrumentos
        instrumentos = obtener_instrumentos()

        return render_template('public/grafica/lista_graficas.html',
                               dataLogin=dataLogin,
                               nombres_roles=nombres_roles,
                               cantidad_por_rol=cantidad_por_rol,
                               total_infantes=total_infantes,
                               total_sesiones=total_sesiones,
                               total_instrumentos=total_instrumentos,
                               instrumentos=instrumentos)  # Asegúrate de que estamos pasando instrumentos al template
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

# ===============================================================
# ======================== SESIONES CRUD ========================
# ===============================================================


@app.route("/sesiones/nueva", methods=['GET', 'POST'])
def nueva_sesion_route():
    if 'id' in session:
        dataLogin = dataLoginSesion()

        # Validar si hay alguna sesión activa
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id_sesion FROM sesiones_terapia WHERE cerrada = FALSE LIMIT 1")
            sesion_activa = cursor.fetchone()
            if sesion_activa:
                flash('Ya hay una sesión activa. Solo se puede tener una sesión activa a la vez.', 'error')
                return redirect(url_for('listar_sesiones_route'))

            if request.method == 'POST':
                id_infante = request.form['id_infante']
                id_terapeuta = request.form['id_terapeuta']  # Aquí puede haber un campo adicional

                cursor.execute("""
                    INSERT INTO sesiones_terapia (id_infante, id_terapeuta, fecha_inicio)
                    VALUES (%s, %s, NOW())
                """, (id_infante, id_terapeuta))
                conexion.commit()

                flash('Sesión creada e iniciada.', 'success')
                return redirect(url_for('listar_sesiones_route'))
        finally:
            conexion.close()

        # Obtener los infantes y terapeutas para el formulario
        infantes = obtener_infantes()
        terapeutas = obtener_terapeutas()

        return render_template('public/sesiones/formulario_sesion.html',
                               infantes=infantes, terapeutas=terapeutas, dataLogin=dataLogin)
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
@app.route('/control-instrumentos', methods=['GET'])
def control_instrumentos():
    if 'id' not in session:
        return redirect(url_for('inicio'))

    dataLogin = dataLoginSesion()
    instrumentos = obtener_instrumentos()
    infantes = obtener_infantes()
    sesiones = listar_sesiones()

    return render_template(
        'public/grafica/control_instrumentos.html',
        instrumentos=instrumentos,
        infantes=infantes,
        sesiones=sesiones,
        dataLogin=dataLogin
    )

# ===============================================================
# ======= API PARA GRÁFICAS control instrumentos ================
# ===============================================================

@app.route("/sesiones", methods=['GET'])
def listar_sesiones_route():
    if 'id' in session:
        dataLogin = dataLoginSesion()

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT 
                s.id_sesion,
                i.nombre AS infante,
                s.fecha_inicio,
                s.fecha_fin,
                s.cerrada
            FROM sesiones_terapia s
            JOIN infantes i ON s.id_infante = i.id_infante
            ORDER BY s.fecha_inicio DESC
        """)
        resultados = cursor.fetchall()

        sesiones = []
        for row in resultados:
            sesiones.append({
                "id_sesion": row[0],
                "infante": row[1],
                "fecha_inicio": row[2].strftime('%Y-%m-%d %H:%M') if row[2] else '',
                "fecha_fin": row[3].strftime('%Y-%m-%d %H:%M') if row[3] else None,
                "cerrada": bool(row[4])
            })

        cursor.close()
        conexion.close()

        return render_template(
            'public/sesiones/lista_sesiones.html',
            sesiones=sesiones,
            dataLogin=dataLogin
        )
    else:
        return redirect(url_for('inicio'))


@app.route("/api/datos-instrumentos-sesionV2/<int:id_sesion>", methods=['GET'])
def obtener_datos_instrumentos_sesionV2(id_sesion):
    try:
        if 'id' not in session:
            return jsonify({"error": "No autorizado"}), 401

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT 
                i.id_instrumento,             -- para distinguir tipo
                ises.fecha_registro,          -- timestamp
                i.nombre,                     -- nombre del instrumento
                ises.suma_angulos,
                ises.aceleracion,
                ises.velocidad,
                ises.giros
            FROM instrumentos_sesion ises
            JOIN instrumentos i ON i.id_instrumento = ises.id_instrumento
            WHERE ises.id_sesion = %s
            ORDER BY ises.fecha_registro ASC
        """, (id_sesion,))

        resultados = cursor.fetchall()

        if not resultados:
            return jsonify({"error": "No se encontraron instrumentos para esta sesión"}), 404

        instrumentos = []
        for row in resultados:
            id_instrumento = row[0]
            tipo = "Silla" if id_instrumento == 1 else "Hamaca" if id_instrumento == 2 else "Otro"
            fecha = row[1].strftime('%H:%M') if row[1] else ''
            nombre = row[2]
            angulos = float(row[3]) if row[3] is not None else 0
            aceleracion = float(row[4]) if row[4] is not None else 0
            velocidad = float(row[5]) if row[5] is not None else 0
            giros = int(row[6]) if row[6] is not None else 0

            instrumentos.append({
                "tipo": tipo,
                "timestamp": fecha,
                "nombre": nombre,
                "suma_angulos": angulos,
                "aceleracion": aceleracion,
                "velocidad": velocidad,
                "giros": giros
            })

        return jsonify({"instrumentos": instrumentos})

    except Exception as e:
        print(f"Error en datos-instrumentos-sesionV2: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conexion.close()

# ===============================================================
# ================ API PARA GRÁFICAS AVANZADAS ==================
# ===============================================================

@app.route("/graficas-avanzadas")
def graficas_avanzadas():
    if 'id' not in session:
        return redirect(url_for("inicio"))
    
    infantes = obtener_infantes()  # o tu función real
    dataLogin = dataLoginSesion()

    return render_template("public/grafica/graficas_avanzadas.html", 
                           infantes=infantes, 
                           dataLogin=dataLogin)


@app.route("/api/graficas-avanzadas", methods=['GET'])
def api_graficas_avanzadas():
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        id_infante = request.args.get("id_infante")
        fecha_inicio = request.args.get("inicio")
        fecha_fin = request.args.get("fin")

        if not id_infante or not fecha_inicio or not fecha_fin:
            return jsonify({"error": "Parámetros incompletos"}), 400

        query = """
            SELECT 
                s.id_sesion,
                s.fecha_inicio,
                i.nombre AS instrumento,
                SUM(is_s.suma_angulos),
                SUM(is_s.aceleracion),
                SUM(is_s.velocidad),
                SUM(is_s.giros)
            FROM instrumentos_sesion is_s
            JOIN instrumentos i ON i.id_instrumento = is_s.id_instrumento
            JOIN sesiones_terapia s ON s.id_sesion = is_s.id_sesion
            WHERE s.id_infante = %s
              AND DATE(s.fecha_inicio) BETWEEN %s AND %s
            GROUP BY s.id_sesion, i.id_instrumento
            ORDER BY s.fecha_inicio ASC
        """

        cursor.execute(query, (id_infante, fecha_inicio, fecha_fin))
        resultados = cursor.fetchall()

        sesiones_dict = {}
        for row in resultados:
            id_sesion = row[0]
            fecha = row[1].strftime('%Y-%m-%d')
            instrumento = row[2]
            suma_angulos = float(row[3])
            aceleracion = float(row[4])
            velocidad = float(row[5])
            giros = int(row[6])

            if id_sesion not in sesiones_dict:
                sesiones_dict[id_sesion] = {
                    "titulo": f"Sesión {id_sesion} - {fecha}",
                    "instrumentos": []
                }

            sesiones_dict[id_sesion]["instrumentos"].append({
                "nombre": instrumento,
                "suma_angulos": suma_angulos,
                "aceleracion": aceleracion,
                "velocidad": velocidad,
                "giros": giros
            })

        sesiones = list(sesiones_dict.values())
        return jsonify({"sesiones": sesiones})

    except Exception as e:
        print(f"Error en /api/graficas-avanzadas: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conexion' in locals(): conexion.close()
