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
# LOGIN CON GOOGLE
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
# REGISTRO NORMAL (API) 
# ===========================
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    nombre = data.get('nombre')
    email = data.get('email')
    password = data.get('password')
    telefono = data.get('telefono', '') # Opcional

    # Validar datos básicos
    if not nombre or not email or not password:
        return jsonify({'success': False, 'message': 'Faltan datos obligatorios'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Error de conexión BD'}), 500

    try:
        with conn.cursor() as cursor:
            # 1. Verificar si el correo ya existe
            cursor.execute("SELECT id_usuario FROM Usuario WHERE correo = %s", (email,))
            usuario_existente = cursor.fetchone()

            if usuario_existente:
                return jsonify({'success': False, 'message': 'Este correo ya está registrado'}), 409

            # 2. Insertar en la tabla Usuario
            # Nota: Asignamos rol 'Cliente' por defecto
            sql_usuario = "INSERT INTO Usuario (nombre, correo, contrasena, rol, telefono) VALUES (%s, %s, %s, 'Cliente', %s)"
            cursor.execute(sql_usuario, (nombre, email, password, telefono))
            
            id_nuevo_usuario = cursor.lastrowid

            # 3. Insertar en la tabla Cliente (IMPORTANTE para que funcionen direcciones y pedidos)
            sql_cliente = "INSERT INTO Cliente (id_usuario) VALUES (%s)"
            cursor.execute(sql_cliente, (id_nuevo_usuario,))

            conn.commit()

            return jsonify({'success': True, 'message': 'Usuario registrado correctamente'})

    except Exception as e:
        conn.rollback()
        print("❌ Error Registro:", e)
        return jsonify({'success': False, 'message': 'Error en el servidor: ' + str(e)}), 500
    finally:
        conn.close()

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
# CRUD DE USUARIOS
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
# CREAR PEDIDO
# ===========================
@app.route('/api/pedido', methods=['POST'])
def crear_pedido():
    data = request.get_json()

    id_cliente = data.get('id_cliente')
    total = data.get('total')
    carrito = data.get('carrito', []) # Usa 'carrito' o 'productos' según tu frontend

    if not carrito and 'productos' in data:
        carrito = data['productos']

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        # 1️⃣ Crear pedido principal
        cursor.execute("""
            INSERT INTO Pedido (id_cliente, total)
            VALUES (%s, %s)
        """, (id_cliente, total))

        id_pedido = cursor.lastrowid

        # 2️⃣ Insertar detalle de productos (Tabla: Detalle_Pedido)
        # Nota: La tabla creada NO tiene 'precio_unitario', solo 'subtotal'
        for item in carrito:
            # Detectar si viene como 'id' o 'id_producto'
            id_prod = item.get('id_producto') or item.get('id')
            cantidad = item['cantidad']
            precio = float(item['precio'])
            subtotal = cantidad * precio
            
            cursor.execute("""
                INSERT INTO Detalle_Pedido
                (id_pedido, id_producto, cantidad, subtotal)
                VALUES (%s, %s, %s, %s)
            """, (
                id_pedido,
                id_prod,
                cantidad,
                subtotal
            ))

        conn.commit()

        return jsonify({
            'success': True,
            'id_pedido': id_pedido
        })

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
        cursor = conn.cursor()
        # Corregido a Detalle_Pedido
        cursor.execute("""
            SELECT 
                p.nombre AS nombre_producto,
                d.cantidad,
                d.subtotal
            FROM Detalle_Pedido d
            JOIN Producto p ON d.id_producto = p.id_producto
            WHERE d.id_pedido = %s
        """, (id_pedido,))

        rows = cursor.fetchall()

        productos = []
        for r in rows:
            productos.append({
                'nombre_producto': r['nombre_producto'],
                'cantidad': r['cantidad'],
                'subtotal': float(r['subtotal'])
            })

        return jsonify(productos)

    except Exception as e:
        print("❌ ERROR productos_pedido:", e)
        return jsonify([]), 500

    finally:
        conn.close()

@app.route('/api/pedido/<int:id_pedido>')
def obtener_pedido(id_pedido):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.id_pedido,
                p.fecha,
                p.estado,
                p.total,
                pg.metodo
            FROM Pedido p
            LEFT JOIN Pago pg ON p.id_pedido = pg.id_pedido
            WHERE p.id_pedido = %s
        """, (id_pedido,))

        row = cursor.fetchone()

        if not row:
            return jsonify({}), 404

        return jsonify({
            "id_pedido": row["id_pedido"],
            "fecha": row["fecha"].strftime("%Y-%m-%d %H:%M"),
            "estado": row["estado"],
            "total": float(row["total"]),
            "metodo": row["metodo"] or "No definido"
        })

    except Exception as e:
        print("❌ ERROR obtener_pedido REAL:", repr(e))
        return jsonify({}), 500
    finally:
        conn.close()

# ===========================
# REPORTE DE VENTAS (MESES)
# ===========================
@app.route('/api/reporte/ventas', methods=['GET'])
def reporte_ventas():
    conn = get_db_connection()
    if not conn: return jsonify([])

    try:
        with conn.cursor() as cursor:
            # Esta consulta agrupa las ventas por Mes y Año
            query = """
                SELECT 
                    DATE_FORMAT(pa.fecha_pago, '%Y-%m') as mes,
                    SUM(pa.monto) as total_ventas,
                    COUNT(p.id_pedido) as total_pedidos
                FROM Pedido p
                JOIN Pago pa ON p.id_pedido = pa.id_pedido
                GROUP BY mes
                ORDER BY mes DESC
                LIMIT 12
            """
            cursor.execute(query)
            datos = cursor.fetchall()
            
            # Convertimos decimales a float para que JSON no falle
            for d in datos:
                d['total_ventas'] = float(d['total_ventas'])
                
            return jsonify(datos)
    except Exception as e:
        print("❌ Error Reporte:", e)
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ===========================
# REPORTE DE PRODUCTOS 
# ===========================
@app.route('/api/reporte/productos', methods=['GET'])
def reporte_productos_top():
    conn = get_db_connection()
    if not conn: return jsonify([])

    try:
        with conn.cursor() as cursor:
            # Esta consulta suma cuántos se vendieron de cada pan usando Detalle_Pedido
            query = """
                SELECT 
                    p.nombre,
                    SUM(dp.cantidad) as cantidad_total,
                    SUM(dp.subtotal) as dinero_total
                FROM Detalle_Pedido dp
                JOIN Producto p ON dp.id_producto = p.id_producto
                GROUP BY p.id_producto, p.nombre
                ORDER BY cantidad_total DESC
                LIMIT 10
            """
            cursor.execute(query)
            datos = cursor.fetchall()
            
            for d in datos:
                d['cantidad_total'] = int(d['cantidad_total'])
                d['dinero_total'] = float(d['dinero_total'])
                
            return jsonify(datos)
    except Exception as e:
        print("❌ Error Reporte Productos:", e)
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ===========================
# ARCHIVOS ESTÁTICOS
# ===========================
@app.route('/Imagenes/<path:filename>')
def imagenes(filename):
    return send_from_directory('static/Imagenes', filename)

@app.route('/<path:filename>')
def archivos(filename):
    return send_from_directory('.', filename)

@app.route('/')
def inicio():
    return send_from_directory('.', 'Inicio.html')

# ===========================
# RESEÑAS API (NUEVO)
# ===========================
@app.route('/api/resenas', methods=['POST'])
def guardar_resena():
    data = request.get_json()
    
    # 1. Validar datos
    if not data or 'producto' not in data or 'comentario' not in data:
        return jsonify({'success': False, 'message': 'Faltan datos'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Error de conexión BD'}), 500

    try:
        with conn.cursor() as cursor:
            # 2. Insertar en la tabla Resenas
            # Asegúrate de que tu tabla en la BD se llame 'Resenas' (o 'resenas')
            query = """
                INSERT INTO Resenas (producto_nombre, autor, rol, calificacion, comentario)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                data['producto'],
                data['autor'],
                data['rol'],
                data['calificacion'],
                data['comentario']
            ))
            conn.commit()
            
        return jsonify({'success': True, 'message': 'Reseña guardada'})

    except Exception as e:
        print("❌ Error guardando reseña:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/resenas', methods=['GET'])
def obtener_resenas():
    # Obtenemos el nombre del producto de la URL (?producto=Pastel...)
    producto_nombre = request.args.get('producto')
    
    conn = get_db_connection()
    if not conn: return jsonify([])

    try:
        with conn.cursor() as cursor:
            if producto_nombre:
                # Traer reseñas solo de ese producto
                query = "SELECT * FROM Resenas WHERE producto_nombre = %s ORDER BY fecha DESC"
                cursor.execute(query, (producto_nombre,))
            else:
                # Traer todas (por si acaso)
                query = "SELECT * FROM Resenas ORDER BY fecha DESC"
                cursor.execute(query)
            
            resenas = cursor.fetchall()
            return jsonify(resenas)
    except Exception as e:
        print("❌ Error obteniendo reseñas:", e)
        return jsonify([])
    finally:
        conn.close()

# ===========================
# RUN
# ===========================
if __name__ == '__main__':
    print("🚀 Servidor iniciado en puerto 5000")
    app.run(debug=True, host='0.0.0.0', port=5000)