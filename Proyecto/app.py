from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import platform 

# --- IMPORTACIONES PARA GOOGLE ---
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)
CORS(app)

# ==========================================
# CONFIGURACIÓN INTELIGENTE (Solución Definitiva de Rutas)
# ==========================================
SISTEMA = platform.system()

# 1. Detectar la ruta EXACTA donde está este archivo app.py
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_NAME = os.path.join(BASE_DIR, 'SensaReposteria.db')

if SISTEMA == 'Windows' or SISTEMA == 'Darwin':
    print("💻 MODO DETECTADO: LOCAL")
    HOST_IP = '127.0.0.1'
    DEBUG_MODE = True
else:
    print("☁️  MODO DETECTADO: NUBE (AWS/Linux)")
    HOST_IP = '0.0.0.0'
    DEBUG_MODE = True

print(f"📂 Base de datos en: {DB_NAME}")

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row 
        return conn
    except Exception as e:
        print(f"❌ Error conectando a {DB_NAME}: {e}")
        return None

# --- INICIALIZAR TABLAS ---
def init_db():
    conn = get_db_connection()
    if not conn: return
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
            id_usuario INTEGER UNIQUE,
            telefono TEXT,
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

    # Tabla Direccion
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Direccion (
            id_direccion INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cliente INTEGER,
            calle TEXT,
            numero TEXT,
            colonia TEXT,
            ciudad TEXT,
            codigo_postal TEXT,
            principal INTEGER DEFAULT 0,
            FOREIGN KEY(id_cliente) REFERENCES Cliente(id_cliente)
        )
    ''')
    
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

# ==========================================
# 1. RUTA NUEVA: LOGIN CON GOOGLE
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
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_usuario, nombre, rol FROM Usuario WHERE correo = ?", (email,))
        row = cursor.fetchone()

        if row:
            return jsonify({
                'success': True, 
                'message': 'Bienvenido de nuevo',
                'user': {'id': row['id_usuario'], 'nombre': row['nombre'], 'rol': row['rol']}
            })
        else:
            password_dummy = "GOOGLE_LOGIN_USER"
            sql_usuario = "INSERT INTO Usuario (nombre, correo, contrasena, rol) VALUES (?, ?, ?, ?)"
            cursor.execute(sql_usuario, (nombre, email, password_dummy, 'Cliente'))
            id_nuevo = cursor.lastrowid
            
            cursor.execute("INSERT INTO Cliente (id_usuario) VALUES (?)", (id_nuevo,))
            conn.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Cuenta creada con Google',
                'user': {'id': id_nuevo, 'nombre': nombre, 'rol': 'Cliente'}
            })

    except ValueError:
        return jsonify({'success': False, 'message': 'Token de Google inválido'}), 401
    except Exception as e:
        print("Error Google:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'conn' in locals() and conn: conn.close()

# ==========================================
# 2. REGISTRO NORMAL
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
        if row and row['contrasena'] == data['password']:
            return jsonify({
                'success': True, 
                'user': {'id': row['id_usuario'], 'nombre': row['nombre'], 'rol': row['rol']}
            })
        return jsonify({'success': False, 'message': 'Credenciales incorrectas'}), 401
    finally:
        conn.close()

# ==========================================
# 4. CRUD DE USUARIOS
# ==========================================
@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    conn = get_db_connection()
    if not conn: return jsonify([]), 500
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_usuario, nombre, correo, rol FROM Usuario")
        rows = cursor.fetchall()
        usuarios = [{'id_usuario': r['id_usuario'], 'nombre': r['nombre'], 'correo': r['correo'], 'rol': r['rol']} for r in rows]
        return jsonify(usuarios)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/usuarios', methods=['PUT'])
def update_usuario():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Usuario SET nombre = ?, correo = ?, rol = ? WHERE id_usuario = ?", 
                      (data['nombre'], data['correo'], data['rol'], data['id']))
        conn.commit()
        return jsonify({'success': True, 'message': 'Usuario actualizado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

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
@app.route('/productos', methods=['GET'])
def get_productos():
    conn = get_db_connection()
    if not conn: return jsonify([]), 500
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_producto, nombre, descripcion, precio, stock, imagen FROM Producto WHERE activo = 1")
        rows = cursor.fetchall()
        productos = [{
            'id_producto': r['id_producto'], 'nombre': r['nombre'], 'descripcion': r['descripcion'],
            'precio': float(r['precio']), 'stock': r['stock'], 'imagen': r['imagen']
        } for r in rows]
        return jsonify(productos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/productos', methods=['POST'])
def agregar_producto():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Producto (nombre, descripcion, precio, stock, imagen, activo) VALUES (?, ?, ?, ?, ?, 1)",
                       (data.get('nombre'), data.get('descripcion'), data.get('precio'), data.get('stock'), data.get('imagen')))
        conn.commit()
        return jsonify({'message': 'Producto agregado correctamente'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/productos/<int:id_producto>', methods=['PUT'])
def update_producto(id_producto):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Producto SET nombre = ?, descripcion = ?, precio = ?, stock = ?, imagen = ? WHERE id_producto = ?",
                       (data.get('nombre'), data.get('descripcion'), data.get('precio'), data.get('stock'), data.get('imagen'), id_producto))
        conn.commit()
        return jsonify({'message': 'Producto actualizado correctamente'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ==========================================
# 6. PERFIL Y DIRECCIONES
# ==========================================


# ==========================================
# 5. SERVIR PÁGINAS WEB
# ==========================================
@app.route('/')
def serve_index():
    return send_from_directory('.', 'Inicio.html')

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    print(f"🚀 Iniciando servidor en entorno: {SISTEMA}")
    print(f"📂 Usando base de datos: {DB_NAME}")
    app.run(debug=DEBUG_MODE, host=HOST_IP, port=5000)


