import sqlite3
import os

# --- CONFIGURACIÓN ---
DB_NAME = 'SensaReposteria.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Para poder acceder a columnas por nombre
    return conn

def inicializar_base_de_datos():
    """ Crea las tablas si no existen (Solo la primera vez) """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear Tabla Usuario
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Usuario (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            contrasena TEXT NOT NULL,
            rol TEXT NOT NULL
        )
    ''')

    # Crear Tabla Cliente
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Cliente (
            id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER,
            FOREIGN KEY(id_usuario) REFERENCES Usuario(id_usuario)
        )
    ''')
    
    conn.commit()
    conn.close()

# --- EJECUTAR PRUEBA DE REGISTRO ---
print("--- INICIANDO PRUEBA DE REGISTRO (EN SQLITE) ---")

# 1. Asegurar que las tablas existan
inicializar_base_de_datos()

conn = None

try:
    # 2. Conectar
    conn = get_db_connection()
    cursor = conn.cursor()
    print("✅ Conexión exitosa a SQLite.")

    # 3. Datos a insertar
    nombre_test = "Itzi"
    email_test = "cacorra23@hotmail.com" 
    pass_test = "clave123"

    # 4. Insertar en tabla USUARIO
    print("⏳ Insertando usuario...")
    
    sql_usuario = """
        INSERT INTO Usuario (nombre, correo, contrasena, rol) 
        VALUES (?, ?, ?, ?)
    """
    
    cursor.execute(sql_usuario, (nombre_test, email_test, pass_test, 'Cliente'))
    
    # 5. Obtener ID inmediatamente (Versión SQLite)
    id_nuevo = cursor.lastrowid
    
    if id_nuevo:
        print(f"   -> ¡Éxito! Usuario creado con ID: {id_nuevo}")

        # 6. Insertar en tabla CLIENTE
        print("⏳ Creando perfil de cliente...")
        sql_cliente = "INSERT INTO Cliente (id_usuario) VALUES (?)"
        cursor.execute(sql_cliente, (id_nuevo,))

        # 7. GUARDAR CAMBIOS
        conn.commit()
        print("\n🎉 ¡PRUEBA FINALIZADA CORRECTAMENTE!")
        print(f"   Se registró el correo: {email_test}")
        print(f"   Base de datos guardada en: {os.getcwd()}/{DB_NAME}")

    else:
        print("❌ Error: No se generó el ID.")

except Exception as e:
    if conn:
        conn.rollback()
    print("\n❌ FALLÓ LA PRUEBA:")
    print(e)

finally:
    if conn:
        conn.close()
