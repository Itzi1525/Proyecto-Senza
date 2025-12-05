from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc

# --- IMPORTACIONES PARA GOOGLE ---
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)
CORS(app) 

# --- 1. CONFIGURACIÓN DE BASE DE DATOS (Tus datos) ---
server = r'DESKTOP-9LUBVQE'
database = 'SensaReposteria'
username = 'Gerente'
password = 'Gerente123'
driver = '{ODBC Driver 17 for SQL Server}'

conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

def get_db_connection():
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print("❌ Error de conexión:", e)
        return None

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
        
        # 3. Buscar si el usuario ya existe en SQL Server
        cursor.execute("SELECT id_usuario, nombre, rol FROM Usuario WHERE correo = ?", (email,))
        row = cursor.fetchone()

        if row:
            # A) YA EXISTE -> INICIAR SESIÓN
            return jsonify({
                'success': True, 
                'message': 'Bienvenido de nuevo',
                'user': {'nombre': row[1], 'rol': row[2]}
            })
        else:
            # B) NO EXISTE -> REGISTRARLO AUTOMÁTICAMENTE
            password_dummy = "GOOGLE_LOGIN_USER" # Contraseña interna
            
            # Insertar en Usuario
            sql_usuario = "INSERT INTO Usuario (nombre, correo, contrasena, rol) OUTPUT INSERTED.id_usuario VALUES (?, ?, ?, ?)"
            cursor.execute(sql_usuario, (nombre, email, password_dummy, 'Cliente'))
            
            id_nuevo = cursor.fetchone()[0]
            
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

        sql_usuario = "INSERT INTO Usuario (nombre, correo, contrasena, rol) OUTPUT INSERTED.id_usuario VALUES (?, ?, ?, ?)"
        cursor.execute(sql_usuario, (data['nombre'], data['email'], data['password'], 'Cliente'))
        id_nuevo = cursor.fetchone()[0]
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
        if row and row[2] == data['password']:
            return jsonify({'success': True, 'user': {'nombre': row[1], 'rol': row[3]}})
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
                'id_usuario': row[0],
                'nombre': row[1],
                'correo': row[2],
                'rol': row[3]
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
    # --- CRUD DE PRODUCTOS 📦 ---
# Obtener productos
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
                'id_producto': row[0],
                'nombre': row[1],
                'descripcion': row[2],
                'precio': float(row[3]),
                'stock': row[4],
                'imagen': row[5]
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



# --- FIN DEL CRUD DE PRODUCTOS 📦 ---
if __name__ == '__main__':
    print("🚀 Servidor Python corriendo en http://localhost:5000")
    app.run(debug=True, port=5000)