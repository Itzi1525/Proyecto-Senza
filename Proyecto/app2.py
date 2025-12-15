print("🔥 app2.py CORRECTO cargado")

from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
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
# LOGIN (API)
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
# PERFIL (API, COMO LOGIN)
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

@app.route('/api/direcciones/<int:id_usuario>')
def obtener_direcciones(id_usuario):
    conn = get_db_connection()
    if not conn:
        return jsonify([])

    try:
        cursor = conn.cursor()
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
                "id_direccion": row[0],   # 👈 ESTE ERA EL FALTANTE
                "calle": row[1],
                "numero": row[2],
                "colonia": row[3],
                "ciudad": row[4],
                "codigo_postal": row[5],
                "principal": bool(row[6])
            })

        return jsonify(direcciones)

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
