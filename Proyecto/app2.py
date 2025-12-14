from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, session
from flask import session
from flask import Flask, request, jsonify, send_from_directory, redirect, render_template
from flask_cors import CORS
import pymysql # Cambiamos sqlite3 por pymysql
import os
import platform 

# --- IMPORTACIONES PARA GOOGLE ---
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)
app.secret_key = 'senza_secreta_123'

CORS(app)

# ==========================================
# CONFIGURACIÓN DE CONEXIÓN MYSQL
# ==========================================
def get_db_connection():
    try:
        # CONEXIÓN A LA BASE DE DATOS LOCAL (AWS o TU PC)
        # Si estás en AWS, el host es 'localhost'.
        # Asegúrate de poner la contraseña correcta aquí abajo ↓
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='reposteria123',  # <--- ¡PON TU CONTRASEÑA!
            database='SenzaReposteria',
            cursorclass=pymysql.cursors.DictCursor # Para acceder como diccionario row['email']
        )
        return conn
    except Exception as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return None

# ==========================================
# 1. LOGIN Y REGISTRO
# ==========================================

@app.route('/google-login', methods=['POST'])
def google_login():
    data = request.get_json()
    token_google = data.get('token')
    CLIENT_ID = "87366328254-63lo1bk93htqig3shql9ljsj0kbsm22q.apps.googleusercontent.com"

    try:
        idinfo = id_token.verify_oauth2_token(token_google, google_requests.Request(), CLIENT_ID)
        email = idinfo['email']
        nombre = idinfo['name']
        
        conn = get_db_connection()
        if not conn: return jsonify({'success': False, 'message': 'Error BD'}), 500 
        
        with conn.cursor() as cursor:
            # En MySQL usamos %s en lugar de ?
            cursor.execute("SELECT id_usuario, nombre, rol FROM Usuario WHERE correo = %s", (email,))
            row = cursor.fetchone()

            if row:
                return jsonify({
                    'success': True, 
                    'message': 'Bienvenido de nuevo',
                    'user': {'id': row['id_usuario'], 'nombre': row['nombre'], 'rol': row['rol']}
                })
            else:
                # Crear usuario nuevo
                cursor.execute("INSERT INTO Usuario (nombre, correo, contrasena, rol) VALUES (%s, %s, %s, %s)", 
                               (nombre, email, "GOOGLE_USER", 'Cliente'))
                id_nuevo = cursor.lastrowid # En MySQL esto funciona igual
                
                cursor.execute("INSERT INTO Cliente (id_usuario) VALUES (%s)", (id_nuevo,))
                conn.commit()
                
                return jsonify({
                    'success': True, 
                    'message': 'Cuenta creada',
                    'user': {'id': id_nuevo, 'nombre': nombre, 'rol': 'Cliente'}
                })
    except Exception as e:
        print("Error Google:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'conn' in locals() and conn: conn.close()

@app.route('/registro', methods=['POST'])
def registro():
    data = request.get_json()
    conn = get_db_connection()
    if not conn: return jsonify({'success': False, 'message': 'Error BD'}), 500
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_usuario FROM Usuario WHERE correo = %s", (data['email'],))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'El correo ya existe'}), 400

            cursor.execute("INSERT INTO Usuario (nombre, correo, contrasena, rol) VALUES (%s, %s, %s, %s)", 
                           (data['nombre'], data['email'], data['password'], 'Cliente'))
            id_nuevo = cursor.lastrowid
            
            cursor.execute("INSERT INTO Cliente (id_usuario) VALUES (%s)", (id_nuevo,))
            conn.commit()
            return jsonify({'success': True, 'message': 'Registro exitoso'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Error BD'}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id_usuario, nombre, contrasena, rol FROM Usuario WHERE correo = %s",
                (data['email'],)
            )
            row = cursor.fetchone()

            if row and row['contrasena'] == data['password']:
                session['user_id'] = row['id_usuario']
                session['nombre'] = row['nombre']
                session['rol'] = row['rol']

                return jsonify({
                    'success': True,
                    'user': {
                        'id': row['id_usuario'],
                        'nombre': row['nombre'],
                        'rol': row['rol']
                    }
                })

            return jsonify({
                'success': False,
                'message': 'Credenciales incorrectas'
            }), 401

    finally:
        conn.close()

# ==========================================
# 2. PERFIL Y DIRECCIONES
@app.route('/actualizar_perfil', methods=['POST'])
def actualizar_perfil():
    try:
        id_usuario = session.get('id_usuario')

        if not id_usuario:
            return "Usuario no autenticado", 401

        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']

        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE Usuario
            SET nombre = ?, correo = ?, telefono = ?
            WHERE id_usuario = ?
        """, (nombre, correo, telefono, id_usuario))

        conn.commit()
        conn.close()

        return redirect(url_for('perfil'))

    except Exception as e:
        return f"Error al actualizar perfil: {e}"
    
@app.route('/perfil')
def perfil():
    id_usuario = session.get('id_usuario')

    if not id_usuario:
        return redirect(url_for('login'))

    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre, correo, telefono
        FROM Usuario
        WHERE id_usuario = ?
    """, (id_usuario,))

    row = cursor.fetchone()
    conn.close()

    usuario = {
        'nombre': row[0],
        'correo': row[1],
        'telefono': row[2]
    }

    return render_template('Perfil.html', usuario=usuario)



# ==========================================
# 3. PRODUCTOS Y ADMIN
# ==========================================
@app.route('/productos', methods=['GET'])
def get_productos():
    conn = get_db_connection()
    if not conn: return jsonify([]), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_producto, nombre, descripcion, precio, stock, imagen FROM Producto WHERE activo = 1")
            productos = cursor.fetchall()
            # MySQL devuelve Decimal para precios, hay que convertir a float si JSON falla
            for p in productos:
                p['precio'] = float(p['precio'])
            return jsonify(productos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/productos', methods=['POST'])
def agregar_producto():
    data = request.get_json()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO Producto (nombre, descripcion, precio, stock, imagen, activo) VALUES (%s, %s, %s, %s, %s, 1)",
                           (data.get('nombre'), data.get('descripcion'), data.get('precio'), data.get('stock'), data.get('imagen')))
            conn.commit()
            return jsonify({'message': 'Producto agregado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/productos/<int:id_producto>', methods=['PUT'])
def update_producto(id_producto):
    data = request.get_json()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE Producto SET nombre = %s, descripcion = %s, precio = %s, stock = %s, imagen = %s WHERE id_producto = %s",
                           (data.get('nombre'), data.get('descripcion'), data.get('precio'), data.get('stock'), data.get('imagen'), id_producto))
            conn.commit()
            return jsonify({'message': 'Producto actualizado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    conn = get_db_connection()
    if not conn: return jsonify([]), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_usuario, nombre, correo, rol FROM Usuario")
            return jsonify(cursor.fetchall())
    finally:
        conn.close()

@app.route('/usuarios', methods=['PUT'])
def update_usuario():
    data = request.get_json()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE Usuario SET nombre = %s, correo = %s, rol = %s WHERE id_usuario = %s", 
                          (data['nombre'], data['correo'], data['rol'], data['id']))
            conn.commit()
            return jsonify({'success': True})
    finally:
        conn.close()

@app.route('/usuarios/delete', methods=['POST'])
def delete_usuario():
    data = request.get_json()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Usuario WHERE id_usuario = %s", (data['id'],))
            conn.commit()
            return jsonify({'success': True})
    finally:
        conn.close()

# ==========================================
# 4. SERVIR PAGINAS
# ==========================================
@app.route('/')
def serve_index():
    return send_from_directory('.', 'Inicio.html')

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    print("🚀 Iniciando servidor MySQL en puerto 5000")
    # host='0.0.0.0' es crucial para AWS
    app.run(debug=True, host='0.0.0.0', port=5000)