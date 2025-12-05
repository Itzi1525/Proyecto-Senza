from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc

app = Flask(__name__)
CORS(app) 

# --- CONFIGURACIÓN DE BASE DE DATOS ---
server = r'LAPTOP-VMHJ4L8R\SQLEXPRESS01'
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

# 1. REGISTRO (Ya lo tenías)
@app.route('/registro', methods=['POST'])
def registro():
    data = request.get_json()
    conn = get_db_connection()
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

# 2. LOGIN (Ya lo tenías)
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_usuario, nombre, contrasena, rol FROM Usuario WHERE correo = ?", (data['email'],))
        row = cursor.fetchone()
        if row and row[2] == data['password']:
            return jsonify({'success': True, 'user': {'nombre': row[1], 'rol': row[3]}})
        return jsonify({'success': False, 'message': 'Credenciales incorrectas'}), 401
    finally:
        conn.close()

# --- NUEVAS RUTAS PARA EL CRUD DE USUARIOS ---

# 3. OBTENER TODOS LOS USUARIOS (Para llenar la tabla)
@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_usuario, nombre, correo, rol FROM Usuario")
        rows = cursor.fetchall()
        
        # Convertimos los datos de SQL a una lista bonita para JavaScript
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

# 4. EDITAR USUARIO
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

# 5. ELIMINAR USUARIO
@app.route('/usuarios/delete', methods=['POST'])
def delete_usuario():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Nota: Al borrar usuario, se borra el cliente automáticamente por el "ON DELETE CASCADE" en SQL
        cursor.execute("DELETE FROM Usuario WHERE id_usuario = ?", (data['id'],))
        conn.commit()
        return jsonify({'success': True, 'message': 'Usuario eliminado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    print("🚀 Servidor Python corriendo en http://localhost:5000")
    app.run(debug=True, port=5000)