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
