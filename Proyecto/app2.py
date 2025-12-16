print("🔥 app2.py CORRECTO cargado")

from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
# Importaciones de Google
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import pymysql

# ===========================
# APP
# ===========================
app = Flask(__name__)
app.secret_key = 'senza_secreta_123'
CORS(app)

# ===========================
# DATABASE
# ===========================
def get_db_connection():
    try:
        return pymysql.connect(
            host='localhost',
            user='root',
            password='reposteria123',
            database='SenzaReposteria',
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print("❌ Error BD:", e)
        return None


# ===========================
# LOGIN CON GOOGLE (NUEVO)
# ===========================
@app.route('/google-login', methods=['POST'])
def google_login():
    data = request.get_json()
    token_google = data.get('token')
    
    # TU CLIENT ID DE GOOGLE
    CLIENT_ID = "87366328254-63lo1bk93htqig3shql9ljsj0kbsm22q.apps.googleusercontent.com"

    try:
        # 1. Verificar el token con Google
        idinfo = id_token.verify_oauth2_token(token_google, google_requests.Request(), CLIENT_ID)
        email = idinfo['email']
        nombre = idinfo['name']
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Error de conexión a BD'}), 500
            
        try:
            with conn.cursor() as cursor:
                # 2. Buscar si el usuario ya existe
                cursor.execute("SELECT id_usuario, nombre, rol FROM Usuario WHERE correo = %s", (email,))
                user = cursor.fetchone()

                if user:
                    # A) YA EXISTE -> INICIAR SESIÓN
                    session['user_id'] = user['id_usuario']
                    return jsonify({
                        'success': True, 
                        'message': 'Bienvenido de nuevo',
                        'user': {'id': user['id_usuario'], 'nombre': user['nombre'], 'rol': user['rol']}
                    })
                else:
                    # B) NO EXISTE -> REGISTRARLO AUTOMÁTICAMENTE
                    password_dummy = "GOOGLE_LOGIN_USER" 
                    
                    # Insertar en Usuario
                    cursor.execute(
                        "INSERT INTO Usuario (nombre, correo, contrasena, rol) VALUES (%s, %s, %s, %s)",
                        (nombre, email, password_dummy, 'Cliente')
                    )
                    id_nuevo = cursor.lastrowid # Obtener el ID generado en MySQL
                    
                    # Insertar en Cliente
                    cursor.execute("INSERT INTO Cliente (id_usuario) VALUES (%s)", (id_nuevo,))
                    conn.commit()
                    
                    # Iniciar sesión automáticamente
                    session['user_id'] = id_nuevo
                    
                    return jsonify({
                        'success': True, 
                        'message': 'Cuenta creada con Google',
                        'user': {'id': id_nuevo, 'nombre': nombre, 'rol': 'Cliente'}
                    })
        finally:
            conn.close()

    except ValueError:
        return jsonify({'success': False, 'message': 'Token Google inválido'}), 401
    except Exception as e:
        print("Error Google:", e)
        return jsonify({'success': False, 'message': str(e)}), 500


# ===========================
# LOGIN NORMAL (API)
# ===========================
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Error BD'}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id_usuario, nombre, contrasena, rol FROM Usuario WHERE correo = %s",
                (email,)
            )
            user = cursor.fetchone()
    finally:
        conn.close()

    if user and user['contrasena'] == password:
        session['user_id'] = user['id_usuario']

        return jsonify({
            'success': True,
            'user': {
                'id': user['id_usuario'],
                'nombre': user['nombre'],
                'rol': user['rol']
            }
        })

    return jsonify({
        'success': False,
        'message': 'Correo o contraseña incorrectos'
    }), 401


# ===========================
# PERFIL (API)
# ===========================
@app.route('/api/perfil/<int:id_usuario>', methods=['GET'])
def obtener_perfil(id_usuario):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'BD'}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT nombre, correo, telefono
                FROM Usuario
                WHERE id_usuario = %s
            """, (id_usuario,))
            usuario = cursor.fetchone()
            return jsonify(usuario)
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
        cursor.execute("UPDATE Usuario SET nombre = %s, correo = %s, rol = %s WHERE id_usuario = %s", 
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
        cursor.execute("DELETE FROM Usuario WHERE id_usuario = %s", (data['id'],))
        conn.commit()
        return jsonify({'success': True, 'message': 'Usuario eliminado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# ===========================
# MODIFICACION PERFIL 
# ===========================
@app.route('/api/perfil', methods=['PUT'])
def actualizar_perfil():
    data = request.get_json()

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE Usuario
                SET nombre=%s, correo=%s, telefono=%s
                WHERE id_usuario=%s
            """, (
                data['nombre'],
                data['correo'],
                data['telefono'],
                data['id']
            ))
            conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True})

# ===========================
# DIRECCIÓNES API
# ===========================
@app.route('/api/direcciones/<int:id_usuario>', methods=['GET'])
def obtener_direcciones(id_usuario):
    conn = get_db_connection()
    if not conn:
        return jsonify([])

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id_direccion,
                    calle,
                    numero,
                    colonia,
                    ciudad,
                    codigo_postal,
                    principal
                FROM Direccion
                WHERE id_cliente = %s
            """, (id_usuario,))

            rows = cursor.fetchall()

            direcciones = []
            for row in rows:
                direcciones.append({
                    "id_direccion": row["id_direccion"],
                    "calle": row["calle"],
                    "numero": row["numero"],
                    "colonia": row["colonia"],
                    "ciudad": row["ciudad"],
                    "codigo_postal": row["codigo_postal"],
                    "principal": bool(row["principal"])
                })

            return jsonify(direcciones)

    finally:
        conn.close()


@app.route('/api/direcciones', methods=['POST'])
def agregar_direccion():
    data = request.get_json()
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO Direccion
                (id_cliente, calle, numero, colonia, ciudad, codigo_postal, principal)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                data['id_usuario'],
                data['calle'],
                data.get('numero'),
                data.get('colonia'),
                data['ciudad'],
                data['codigo_postal'],
                data.get('principal', False)
            ))
            conn.commit()

        return jsonify({'success': True})

    finally:
        conn.close()

@app.route('/api/direcciones/<int:id_direccion>', methods=['DELETE'])
def eliminar_direccion(id_direccion):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM Direccion WHERE id_direccion = %s",
                (id_direccion,)
            )
            conn.commit()

        return jsonify({'success': True})

    finally:
        conn.close()

# ===========================
# PRODUCTOS API
# ===========================
@app.route('/productos')
def productos():
    conn = get_db_connection()
    if not conn:
        return jsonify([])

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Producto WHERE activo=1")
            productos = cursor.fetchall()
            for p in productos:
                p['precio'] = float(p['precio'])
            return jsonify(productos)
    finally:
        conn.close()

# ===========================
# METODO PAGO API
# ===========================
@app.route('/api/pago', methods=['POST'])
def registrar_pago():
    data = request.get_json()

    id_pedido = data.get('id_pedido')
    metodo = data.get('metodo')
    monto = data.get('monto')

    # 🔒 VALIDACIÓN
    if not monto or float(monto) <= 0:
        return jsonify({
            'success': False,
            'error': 'Monto inválido'
        }), 400
    
    # Conexión correcta (fuera del if anterior)
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO Pago (id_pedido, metodo, monto)
                VALUES (%s, %s, %s)
            """, (id_pedido, metodo, monto))
            conn.commit()

        return jsonify({'success': True})

    except Exception as e:
        print("❌ ERROR PAGO:", e)
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        conn.close()

# ===========================
# PEDIDO
# ===========================


# ===========================
# CREAR PEDIDO
# ===========================
@app.route('/api/pedido', methods=['POST'])
def crear_pedido():
    data = request.get_json()
    id_cliente = data['id_cliente']
    total = data['total']
    carrito = data['carrito']

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False}), 500

    try:
        with conn.cursor() as cursor:

            # 1️⃣ Crear pedido
            cursor.execute("""
                INSERT INTO Pedido (id_cliente, total)
                VALUES (%s, %s)
            """, (id_cliente, total))

            id_pedido = cursor.lastrowid

            # 2️⃣ Insertar detalle del pedido
            for item in carrito:
                cursor.execute("""
                    INSERT INTO DetallePedido
                    (id_pedido, id_producto, cantidad, precio_unitario)
                    VALUES (%s, %s, %s, %s)
                """, (
                    id_pedido,
                    item['id_producto'],
                    item['cantidad'],
                    item['precio']
                ))

            conn.commit()

        return jsonify({'success': True, 'id_pedido': id_pedido})

    except Exception as e:
        conn.rollback()
        print("❌ ERROR PEDIDO:", e)
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        conn.close()
        
@app.route('/api/pedido/<int:id_pedido>/productos')
def productos_pedido(id_pedido):
    conn = get_db_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT 
                    p.nombre AS nombre,
                    dp.cantidad,
                    dp.precio_unitario,
                    (dp.cantidad * dp.precio_unitario) AS subtotal
                FROM DetallePedido dp
                JOIN Producto p ON dp.id_producto = p.id_producto
                WHERE dp.id_pedido = %s
            """, (id_pedido,))
            
            productos = cursor.fetchall()
            return jsonify(productos)
    finally:
        conn.close()
# ===========================
# ARCHIVOS ESTÁTICOS
# ===========================
# IMÁGENES
@app.route('/Imagenes/<path:filename>')
def imagenes(filename):
    return send_from_directory('static/Imagenes', filename)

# HTML, JS, CSS
@app.route('/<path:filename>')
def archivos(filename):
    return send_from_directory('.', filename)

# RAÍZ
@app.route('/')
def inicio():
    return send_from_directory('.', 'Inicio.html')


# ===========================
# RUN
# ===========================
if __name__ == '__main__':
    print("🚀 Servidor iniciado en puerto 5000")
    app.run(debug=True, host='0.0.0.0', port=5000)