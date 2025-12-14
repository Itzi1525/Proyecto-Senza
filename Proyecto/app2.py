print("🔥 app2.py CORRECTO cargado")

from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory,
    render_template,
    redirect,
    url_for,
    session
)

from flask_cors import CORS
import pymysql

# ---------------------------
# APP
# ---------------------------
app = Flask(__name__)
app.secret_key = 'senza_secreta_123'
CORS(app)

# ---------------------------
# DATABASE
# ---------------------------
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
# LOGIN
# ===========================
@app.route('/login', methods=['POST'])
def login():
    correo = request.form.get('email')
    password = request.form.get('password')

    conn = get_db_connection()
    if not conn:
        return "Error BD", 500

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id_usuario, nombre, contrasena FROM Usuario WHERE correo = %s",
                (correo,)
            )
            user = cursor.fetchone()
    finally:
        conn.close()

    if user and user['contrasena'] == password:
        session['user_id'] = user['id_usuario']
        session['nombre'] = user['nombre']
        return redirect('/perfil')

    return redirect('/login')


# ===========================
# PERFIL
# ===========================
@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        return redirect('/login')


    conn = get_db_connection()
    if not conn:
        return "Error BD", 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT nombre, correo, telefono
                FROM Usuario
                WHERE id_usuario = %s
            """, (session['user_id'],))
            usuario = cursor.fetchone()
    finally:
        conn.close()

    if not usuario:
        return "Usuario no encontrado", 404

    return render_template('Perfil.html', usuario=usuario)

# ===========================
# ACTUALIZAR PERFIL
# ===========================
@app.route('/actualizar_perfil', methods=['POST'])
def actualizar_perfil():
    if 'user_id' not in session:
        return redirect('/login')


    nombre = request.form['nombre']
    correo = request.form['correo']
    telefono = request.form['telefono']

    conn = get_db_connection()
    if not conn:
        return "Error BD", 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE Usuario
                SET nombre=%s, correo=%s, telefono=%s
                WHERE id_usuario=%s
            """, (nombre, correo, telefono, session['user_id']))
            conn.commit()
    finally:
        conn.close()

    return redirect(url_for('perfil'))

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
# PAGINA INICIO
# ===========================
@app.route('/')
def inicio():
    return send_from_directory('.', 'Inicio.html')


# ===========================
# STATIC FALLBACK
# ===========================
# ===============================
# SERVIR IMÁGENES (PRIMERO)
# ===============================
@app.route('/Imagenes/<path:filename>')
def imagenes(filename):
    return send_from_directory('static/Imagenes', filename)


# ===============================
# SERVIR HTML, JS, CSS COMO ANTES
# ===============================
@app.route('/<path:filename>')
def archivos(filename):
    return send_from_directory('.', filename)


# ===========================
# RUN
# ===========================
if __name__ == '__main__':
    print("🚀 Servidor iniciado en puerto 5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
