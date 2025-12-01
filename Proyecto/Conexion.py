import pyodbc
# CONFIGURACIÓN
# Asegúrate que el SERVER sea exactamente el nombre de tu compu + instancia
server = r'LAPTOP-VMHJ4L8R\SQLEXPRESS01' 
database = 'SensaReposteria' 
username = 'Gerente' 
password = 'Gerente123' 

# CADENA DE CONEXIÓN
# Aquí le decimos que use el Driver 17 y entre con usuario y contraseña
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

print("--- INTENTANDO CONECTAR... ---")

try:
    # Intentamos abrir la puerta
    conn = pyodbc.connect(connection_string)
    
    # Si esta línea se ejecuta, es que entramos
    print("✅ ¡ÉXITO! Conexión establecida correctamente con la Base de Datos.")
    print(f"   Servidor: {server}")
    print(f"   Base de Datos: {database}")
    
    # Cerramos la conexión educadamente
    conn.close()

except Exception as e:
    # Si algo falla, aquí nos dirá por qué
    print("❌ ERROR DE CONEXIÓN:")
    print(e)