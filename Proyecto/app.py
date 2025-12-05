from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc

app = Flask(__name__)
CORS(app)  # Permite que tu HTML se conecte a este servidor

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

# --- RUTA 1: REGISTRAR USUARIO ---
@app.route('/registro', methods=['POST'])
def registro():
    data = request.get_json()
    nombre = data.get('nombre')
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'No hay conexión con la BD'}), 500

    cursor = conn.cursor()

    try:
        # 1. Verificar si el correo ya existe
        cursor.execute("SELECT id_usuario FROM Usuario WHERE correo = ?", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'El correo ya está registrado'}), 400

        # 2. Insertar Usuario (Usando OUTPUT para asegurar el ID)
        sql_usuario = """
            INSERT INTO Usuario (nombre, correo, contrasena, rol) 
            OUTPUT INSERTED.id_usuario
            VALUES (?, ?, ?, ?)
        """
        cursor.execute(sql_usuario, (nombre, email, password, 'Cliente'))
        
        row = cursor.fetchone()
        if not row:
            raise Exception("No se generó el ID de usuario")
            
        id_nuevo = row[0]

        # 3. Insertar Cliente
        cursor.execute("INSERT INTO Cliente (id_usuario) VALUES (?)", (id_nuevo,))
        
        conn.commit() # ¡Guardar cambios!
        print(f"✅ Usuario registrado: {email}")
        return jsonify({'success': True, 'message': 'Registro exitoso'})

    except Exception as e:
        conn.rollback()
        print("❌ Error:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# --- RUTA 2: INICIAR SESIÓN ---
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500

    cursor = conn.cursor()
    
    try:
        # Buscamos al usuario por correo
        cursor.execute("SELECT id_usuario, nombre, contrasena, rol FROM Usuario WHERE correo = ?", (email,))
        row = cursor.fetchone()

        if row:
            # row[2] es la contraseña en la BD
            if row[2] == password:
                return jsonify({
                    'success': True, 
                    'message': 'Bienvenido',
                    'user': {'nombre': row[1], 'rol': row[3]}
                })
            else:
                return jsonify({'success': False, 'message': 'Contraseña incorrecta'}), 401
        else:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({'success': False, 'message': 'Error en servidor'}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    print("🚀 Servidor corriendo en http://localhost:5000")
    app.run(debug=True, port=5000)