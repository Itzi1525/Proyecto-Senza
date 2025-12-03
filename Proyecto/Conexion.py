import pyodbc

# --- 1. CONFIGURACIÓN ---
server = r'LAPTOP-VMHJ4L8R\SQLEXPRESS01' 
database = 'SensaReposteria' 
username = 'Gerente' 
password = 'Gerente123' 

# Driver
driver = '{ODBC Driver 17 for SQL Server}' 
connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

print("--- INICIANDO PRUEBA DE REGISTRO MEJORADA ---")

conn = None

try:
    # 2. Conectar
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    print("✅ Conexión exitosa.")

    # 3. Datos a insertar (Cambiamos el correo para que no diga que está repetido)
    nombre_test = "Itzi"
    email_test = "cacorra23@hotmail.com" 
    pass_test = "clave123"

    # 4. Insertar en tabla USUARIO usando OUTPUT
    # ESTA ES LA PARTE QUE CAMBIAMOS PARA ARREGLAR EL ERROR
    print("⏳ Insertando usuario...")
    
    sql_usuario = """
        INSERT INTO Usuario (nombre, correo, contrasena, rol) 
        OUTPUT INSERTED.id_usuario
        VALUES (?, ?, ?, ?)
    """
    
    cursor.execute(sql_usuario, (nombre_test, email_test, pass_test, 'Cliente'))
    
    # 5. Obtener ID inmediatamente
    row = cursor.fetchone()
    
    if row:
        id_nuevo = int(row[0])
        print(f"   -> ¡Éxito! Usuario creado con ID: {id_nuevo}")

        # 6. Insertar en tabla CLIENTE
        print("⏳ Creando perfil de cliente...")
        sql_cliente = "INSERT INTO Cliente (id_usuario) VALUES (?)"
        cursor.execute(sql_cliente, (id_nuevo,))

        # 7. GUARDAR CAMBIOS
        conn.commit()
        print("\n🎉 ¡PRUEBA FINALIZADA CORRECTAMENTE!")
        print(f"   Se registró el correo: {email_test}")

    else:
        print("❌ Error crítico: La base de datos no devolvió ningún ID.")
        print("   Posible causa: La tabla 'Usuario' no tiene la columna id_usuario como IDENTITY.")

except Exception as e:
    if conn:
        conn.rollback()
    print("\n❌ FALLÓ LA PRUEBA:")
    print(e)

finally:
    if conn:
        conn.close()