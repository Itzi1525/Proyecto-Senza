import sqlite3

# Nombre de tu base de datos
DB_NAME = 'SensaReposteria.db'

def llenar_base_datos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("🔄 Conectando a la base de datos...")

    # --- 1. LIMPIAR TABLAS (Opcional: para no duplicar si lo corres dos veces) ---
    # Si quieres mantener usuarios que ya se registraron, comenta la línea de Usuario
    # cursor.execute("DELETE FROM Usuario WHERE rol IN ('Administrador', 'Operador')") 
    cursor.execute("DELETE FROM Producto") 
    
    # Reiniciar contadores de ID (para que empiecen en 1 otra vez)
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='Producto'")

    print("🗑️  Datos antiguos limpiados (Productos).")

    # --- 2. INSERTAR USUARIOS (ADMINS Y OPERADORES) ---
    usuarios = [
        ('Nestor Hernandez', 'admin1@senza.mx', 'admin123', 'Administrador'),
        ('Itzel Arteaga', 'admin2@senza.mx', 'admin123', 'Administrador'),
        ('Operador Matutino', 'operador1@senza.mx', 'opera123', 'Operador'),
        ('Operador Vespertino', 'operador2@senza.mx', 'opera123', 'Operador')
    ]

    print("👤 Insertando usuarios...")
    for u in usuarios:
        try:
            cursor.execute("INSERT INTO Usuario (nombre, correo, contrasena, rol) VALUES (?, ?, ?, ?)", u)
        except sqlite3.IntegrityError:
            print(f"   ⚠️ El usuario {u[1]} ya existe, saltando...")

    # --- 3. INSERTAR PRODUCTOS ---
    # Nota: He quitado la columna 'categoria' del INSERT porque en tu app.py original
    # no vi que crearas esa columna. Si da error, avísame.
    # Asumo que la tabla Producto tiene: nombre, descripcion, precio, stock, activo, imagen
    
    productos = [
        ('Pan de Masa Madre', 'Pan artesanal de fermentación lenta, corteza crujiente y miga con sabor profundo.', 30.00, 10, 1, 'Imagenes/pan_masa_madre.jpg'),
        ('Baguette Francesa', 'Barra clásica francesa: corteza dorada y miga ligera y aireada.', 35.00, 10, 1, 'Imagenes/baguette.jpeg'),
        ('Tarta de Bayas', 'Base de mantequilla con crema pastelera y mezcla de bayas frescas.', 450.00, 10, 1, 'Imagenes/tarta_bayas.jpeg'),
        ('Cheesecake de Fresa', 'Tradicional y cremoso, con baño de fresas naturales.', 100.00, 10, 1, 'Imagenes/cheesecakefresa.jpeg'),
        ('Galleta con Chispas', 'Galleta de mantequilla con chispas de chocolate belga, recién horneada.', 20.00, 10, 1, 'Imagenes/galleta_chispas.jpeg'),
        ('Galleta de Avena', 'Suave y crujiente, con avena integral y un toque de canela.', 20.00, 10, 1, 'Imagenes/galleta_avena.jpg'),
        ('Café Americano', 'Café 100% mexicano, recién molido y preparado al momento.', 30.00, 10, 1, 'Imagenes/cafe_americano.jpeg'),
        ('Té Chai Latte', 'Mezcla aromática de especias con leche espumosa, ligeramente endulzado.', 55.00, 10, 1, 'Imagenes/te_chai_latte.jpeg'),
        ('Matcha', 'Bebida de té verde matcha de alta calidad, preparada con leche o agua.', 80.00, 10, 1, 'Imagenes/matcha.jpeg'),
        ('Taro', 'Bebida cremosa con sabor a taro, ligeramente dulce y suave.', 80.00, 10, 1, 'Imagenes/taro.jpeg'),
        ('Dona de Chocolate con Chispas', 'Dona esponjosa cubierta con chocolate y chispas de colores.', 25.00, 10, 1, 'Imagenes/dona_chocolate_chispas.jpeg'),
        ('Dona de Azúcar', 'Dona clásica espolvoreada con azúcar fina para un toque dulce.', 25.00, 10, 1, 'Imagenes/dona_azucar.jpeg'),
        ('Cuernito', 'Croissant estilo ligero y mantecoso, perfecto para acompañar café.', 20.00, 10, 1, 'Imagenes/cuerno.jpg'),
        ('Agua de Horchata', 'Bebida tradicional de arroz con canela, fresca y ligeramente dulce.', 30.00, 10, 1, 'Imagenes/horchata.jpeg'),
        ('Beignets', 'Pasta frita francesa, esponjosa y espolvoreada con azúcar glass.', 60.00, 10, 1, 'Imagenes/beignets.jpeg'),
        ('Rol de Canela', 'Roll suave con relleno de canela y glaseado ligero.', 30.00, 10, 1, 'Imagenes/rol_canela.jpeg'),
        ('Café Moka', 'Delicioso café con chocolate y leche espumosa.', 45.00, 10, 1, 'Imagenes/cafe_moka.jpeg'),
        ('Pastel de Fresa con Crema', 'Bizcocho delicado relleno y cubierto con crema y fresas naturales.', 480.00, 10, 1, 'Imagenes/pastel_fresa.jpeg'),
        ('Tiramisú de Matcha', 'Versión cremosa del clásico tiramisú con té matcha.', 150.00, 10, 1, 'Imagenes/tiramisu_matcha.jpeg'),
        ('Tarta de Cerezas', 'Tarta con cerezas jugosas y masa quebrada crujiente.', 150.00, 10, 1, 'Imagenes/tarta_cerezas.jpeg'),
        ('Bolillo Mexicano', 'Clásico bolillo, ideal para tortas o acompañar comidas.', 4.00, 10, 1, 'Imagenes/bolillo.jpeg'),
        ('Torta Balcarce', 'Pastel tradicional con capas esponjosas y crema suave.', 480.00, 10, 1, 'Imagenes/torta_balcarce.jpeg'),
        ('Cheesecake de Arándanos', 'Queso cremoso con base de galleta y cobertura de arándanos.', 145.00, 10, 1, 'Imagenes/cheescake_arandanos.jpeg'),
        ('Chocolate Caliente', 'Bebida espesa y reconfortante preparada con chocolate real.', 45.00, 10, 1, 'Imagenes/chocolate.jpeg'),
        ('Frapuccino de Galleta', 'Bebida fría cremosa con sabor a galleta y topping crujiente.', 45.00, 10, 1, 'Imagenes/frapuccino_galleta.jpeg'),
        ('Pay de Fresa', 'Pay con relleno de fresa natural y base crujiente.', 100.00, 10, 1, 'Imagenes/pay_fresa.jpeg'),
        ('Pastel de Ángel', 'Bizcocho ligero y esponjoso, perfecto para ocasiones especiales.', 450.00, 10, 1, 'Imagenes/pastel_angel.jpeg'),
        ('Flan', 'Flan casero con textura suave y caramelo dorado.', 90.00, 10, 1, 'Imagenes/flan.jpeg'),
        ('Donas Rellenas de Crema Pastelera', 'Donas suaves rellenas con crema pastelera y glaseado ligero.', 35.00, 10, 1, 'Imagenes/donas_crema_pastelera.jpeg'),
        ('Chamoyada de Mango', 'Refrescante con mango natural y chamoy, toque dulce-picante.', 40.00, 10, 1, 'Imagenes/chamoyada.jpeg'),
        ('Cold Brew', 'Café de extracción en frío: suave, menos ácido y con gran cuerpo.', 55.00, 10, 1, 'Imagenes/cold_brew.jpeg'),
        ('Tiramisú de Chocolate', 'Capas de bizcocho empapadas y crema de mascarpone con chocolate.', 100.00, 10, 1, 'Imagenes/tiramisu_chocolate.jpeg'),
        ('Pastel de Mil Hojas', 'Hojas hojaldradas con crema pastelera entre capas, textura crujiente.', 480.00, 10, 1, 'Imagenes/pastel_mil_hojas.jpg'),
        ('Bigote', 'Pieza de pan tradicional con toque dulce, ideal para acompañar café.', 25.00, 10, 1, 'Imagenes/bigote.jpeg'),
        ('Gelatina', 'Gelatina casera con textura firme y sabor refrescante.', 100.00, 10, 1, 'Imagenes/gelatina.jpg'),
        ('Galleta de Mantequilla', 'Clásica galleta casera con textura impecable y sabor a mantequilla.', 25.00, 10, 1, 'Imagenes/galleta_matequilla.jpg'),
        ('Galleta de Azúcar', 'Galleta dulce y delicada, perfecta con una bebida caliente.', 20.00, 10, 1, 'Imagenes/galleta_azcar.jpg'),
        ('Galleta Integral', 'Galleta con harina integral y semillas, opción más saludable.', 30.00, 10, 1, 'Imagenes/galleta_integral.jpg'),
        ('Concha de Vainilla', 'Pan dulce con su clásica cubierta de sabor a vainilla.', 30.00, 10, 1, 'Imagenes/concha_vanilla.jpg'),
        ('Concha de Chocolate', 'Deliciosa concha cubierta de chocolate, ideal para los amantes del cacao.', 30.00, 10, 1, 'Imagenes/concha_chocolate.jpg'),
        ('Bisquet', 'Pan tierno y hojaldrado, perfecto para acompañar desayunos.', 30.00, 10, 1, 'Imagenes/bisquet.jpg'),
        ('Polvorones', 'Galletas tradicionales, mantecosas y delicadas al paladar.', 25.00, 10, 1, 'Imagenes/polvorones.jpg'),
        ('Galleta de Canela', 'Galleta aromática con canela, perfecta para la temporada fría.', 25.00, 10, 1, 'Imagenes/galletas_canela.jpg'),
        ('Macarrones', 'Delicados macarons con relleno cremoso, textura ligera.', 40.00, 10, 1, 'Imagenes/macarrones.jpg'),
        ('Espresso', 'Shot concentrado de café, aroma intenso y crema natural.', 35.00, 10, 1, 'Imagenes/espresso.jpg'),
        ('Galleta de la Suerte', 'Galleta crujiente con mensaje sorpresa en su interior.', 15.00, 10, 1, 'Imagenes/galleta_suerte.jpg'),
        ('Malteada de Chocolate', 'Malteada cremosa con helado de chocolate y topping de virutas.', 55.00, 10, 1, 'Imagenes/malteada_chocolate.jpg'),
        ('Galleta de Coco', 'Galleta con textura crujiente y sabor natural a coco.', 25.00, 10, 1, 'Imagenes/galleta_coco.jpg'),
        ('Galletas Decoradas', 'Galletas artesanales decoradas a mano, ideales para regalos.', 25.00, 10, 1, 'Imagenes/galleta_decorada.jpg'),
        ('Galleta de Nuez', 'Galleta con trozos de nuez y textura crujiente por fuera.', 25.00, 10, 1, 'Imagenes/galleta_nuez.jpg')
    ]

    print(f"🍰 Insertando {len(productos)} productos...")
    
    # IMPORTANTE: Asegúrate de que las columnas coincidan con tu tabla
    # Si agregaste 'categoria' en SQL pero no en app.py, aquí fallaría si la incluyo.
    # Estoy usando la estructura estándar: nombre, descripcion, precio, stock, activo, imagen
    for p in productos:
        cursor.execute("""
            INSERT INTO Producto (nombre, descripcion, precio, stock, activo, imagen)
            VALUES (?, ?, ?, ?, ?, ?)
        """, p)

    conn.commit()
    conn.close()
    print("✅ ¡Base de datos actualizada con éxito!")

if __name__ == '__main__':
    llenar_base_datos()
