from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os

# --- IMPORTACIONES PARA GOOGLE ---
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)
CORS(app)

# --- CONFIGURACIÓN DE BASE DE DATOS (SQLite) ---
DB_NAME = 'SensaReposteria.db'

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        # Esto permite acceder a las columnas por nombre (ej: row['email'])
        conn.row_factory = sqlite3.Row 
        return conn
    except Exception as e:
        print("❌ Error de conexión:", e)
        return None

# --- INICIALIZAR TABLAS (Para que no de error si está vacía) ---
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla Usuario
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Usuario (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            correo TEXT,
            contrasena TEXT,
            rol TEXT
        )
    ''')
    
    # Tabla Cliente
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Cliente (
            id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER,
            FOREIGN KEY(id_usuario) REFERENCES Usuario(id_usuario)
        )
    ''')

    # Tabla Producto
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Producto (
            id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            descripcion TEXT,
            precio REAL,
            stock INTEGER,
            imagen TEXT,
            activo INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

# Ejecutamos la creación de tablas al iniciar
with app.app_context():
    init_db()

# ==========================================
# 1. RUTA NUEVA: LOGIN CON GOOGLE
# ==========================================
@app.route('/google-login', methods=['POST'])
def google_login():
    data = request.get_json()
    token_google = data.get('token')
    
    # TU CLIENT ID REAL
    CLIENT_ID = "87366328254-63lo1bk93htqig3shql9ljsj0kbsm22q.apps.googleusercontent.com"

    try:
        # 1. Verificar el token con Google
        idinfo = id_token.verify_oauth2_token(token_google, google_requests.Request(), CLIENT_ID)

        # 2. Obtener datos del usuario
        email = idinfo['email']
        nombre = idinfo['name']
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Error de conexión a BD'}), 500
            
        cursor = conn.cursor()
        
        # 3. Buscar si el usuario ya existe
        cursor.execute("SELECT id_usuario, nombre, rol FROM Usuario WHERE correo = ?", (email,))
        row = cursor.fetchone()

        if row:
            # A) YA EXISTE -> INICIAR SESIÓN
            return jsonify({
                'success': True, 
                'message': 'Bienvenido de nuevo',
                'user': {'nombre': row['nombre'], 'rol': row['rol']}
            })
        else:
            # B) NO EXISTE -> REGISTRARLO AUTOMÁTICAMENTE
            password_dummy = "GOOGLE_LOGIN_USER" # Contraseña interna
            
            # Insertar en Usuario
            sql_usuario = "INSERT INTO Usuario (nombre, correo, contrasena, rol) VALUES (?, ?, ?, ?)"
            cursor.execute(sql_usuario, (nombre, email, password_dummy, 'Cliente'))
            
            # Obtener ID en SQLite
            id_nuevo = cursor.lastrowid
            
            # Insertar en Cliente
            cursor.execute("INSERT INTO Cliente (id_usuario) VALUES (?)", (id_nuevo,))
            conn.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Cuenta creada con Google',
                'user': {'nombre': nombre, 'rol': 'Cliente'}
            })

    except ValueError:
        return jsonify({'success': False, 'message': 'Token de Google inválido'}), 401
    except Exception as e:
        print("Error Google:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'conn' in locals() and conn: conn.close()


# ==========================================
# 2. REGISTRO NORMAL (Correo y Contraseña)
# ==========================================
@app.route('/registro', methods=['POST'])
def registro():
    data = request.get_json()
    conn = get_db_connection()
    if not conn: return jsonify({'success': False, 'message': 'Error BD'}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_usuario FROM Usuario WHERE correo = ?", (data['email'],))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'El correo ya existe'}), 400

        sql_usuario = "INSERT INTO Usuario (nombre, correo, contrasena, rol) VALUES (?, ?, ?, ?)"
        cursor.execute(sql_usuario, (data['nombre'], data['email'], data['password'], 'Cliente'))
        
        # Obtener ID en SQLite
        id_nuevo = cursor.lastrowid

        cursor.execute("INSERT INTO Cliente (id_usuario) VALUES (?)", (id_nuevo,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Registro exitoso'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# ==========================================
# 3. LOGIN NORMAL
# ==========================================
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = get_db_connection()
    if not conn: return jsonify({'success': False, 'message': 'Error BD'}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_usuario, nombre, contrasena, rol FROM Usuario WHERE correo = ?", (data['email'],))
        row = cursor.fetchone()
        # Accedemos como diccionario gracias a row_factory
        if row and row['contrasena'] == data['password']:
            return jsonify({'success': True, 'user': {'nombre': row['nombre'], 'rol': row['rol']}})
        return jsonify({'success': False, 'message': 'Credenciales incorrectas'}), 401
    finally:
        conn.close()

# ==========================================
# 4. CRUD DE USUARIOS (Admin)
# ==========================================

# OBTENER TODOS
@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_usuario, nombre, correo, rol FROM Usuario")
        rows = cursor.fetchall()
        usuarios = []
        for row in rows:
            usuarios.append({
                'id_usuario': row['id_usuario'],
                'nombre': row['nombre'],
                'correo': row['correo'],
                'rol': row['rol']
            })
        return jsonify(usuarios)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# EDITAR USUARIO
@app.route('/usuarios', methods=['PUT'])
def update_usuario():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Usuario 
            SET nombre = ?, correo = ?, rol = ? 
            WHERE id_usuario = ?
        """, (data['nombre'], data['correo'], data['rol'], data['id']))
        conn.commit()
        return jsonify({'success': True, 'message': 'Usuario actualizado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# ELIMINAR USUARIO
@app.route('/usuarios/delete', methods=['POST'])
def delete_usuario():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Usuario WHERE id_usuario = ?", (data['id'],))
        conn.commit()
        return jsonify({'success': True, 'message': 'Usuario eliminado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# ================== PRODUCTOS ==================

# Obtener productos activos
@app.route('/productos', methods=['GET'])
def get_productos():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_producto, nombre, descripcion, precio, stock, imagen FROM Producto WHERE activo = 1")
        rows = cursor.fetchall()
        productos = []
        for row in rows:
            productos.append({
                'id_producto': row['id_producto'],
                'nombre': row['nombre'],
                'descripcion': row['descripcion'],
                'precio': float(row['precio']),
                'stock': row['stock'],
                'imagen': row['imagen']
            })
        return jsonify(productos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Agregar producto
@app.route('/productos', methods=['POST'])
def agregar_producto():
    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    precio = data.get('precio')
    stock = data.get('stock')
    imagen = data.get('imagen')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Producto (nombre, descripcion, precio, stock, imagen, activo) VALUES (?, ?, ?, ?, ?, 1)",
            (nombre, descripcion, precio, stock, imagen)
        )
        conn.commit()
        return jsonify({'message': 'Producto agregado correctamente'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Editar producto
@app.route('/productos/<int:id_producto>', methods=['PUT'])
def update_producto(id_producto):
    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    precio = data.get('precio')
    stock = data.get('stock')
    imagen = data.get('imagen')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Producto 
            SET nombre = ?, descripcion = ?, precio = ?, stock = ?, imagen = ?
            WHERE id_producto = ?
        """, (nombre, descripcion, precio, stock, imagen, id_producto))
        conn.commit()
        return jsonify({'message': 'Producto actualizado correctamente'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ==========================================
# 5. SERVIR PÁGINAS WEB (Frontend)
# ==========================================

# Ruta para la página de inicio (Raíz)
@app.route('/')
def serve_index():
    return send_from_directory('.', 'Inicio.html')

# Ruta mágica para servir cualquier otro archivo (CSS, JS, Imágenes, otros HTML)
@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory('.', path)

# --- ARRANQUE DEL SERVIDOR ---
if __name__ == '__main__':
    # host='0.0.0.0' ES MUY IMPORTANTE EN AWS
    print("🚀 Servidor Python corriendo en http://0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
