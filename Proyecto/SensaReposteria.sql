-- Base de datos
CREATE DATABASE SensaReposteria;
USE SensaReposteria;

CREATE TABLE Usuario(
    id_usuario INT IDENTITY PRIMARY KEY,
    nombre NVARCHAR(100) NOT NULL,
    correo NVARCHAR(150) NOT NULL UNIQUE,
    contrasena NVARCHAR(255) NOT NULL,
    rol NVARCHAR(20) NOT NULL
        CHECK (rol IN ('Administrador','Operador','Cliente')),
    fecha_creacion DATETIME DEFAULT GETDATE()
);

CREATE TABLE Cliente(
    id_cliente INT IDENTITY PRIMARY KEY,
    id_usuario INT UNIQUE NOT NULL,
    telefono NVARCHAR(20),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
        ON DELETE CASCADE
);

CREATE TABLE Direccion(
    id_direccion INT IDENTITY PRIMARY KEY,
    id_cliente INT NOT NULL,
    calle NVARCHAR(100) NOT NULL,
    numero NVARCHAR(20),
    colonia NVARCHAR(100),
    ciudad NVARCHAR(100),
    codigo_postal NVARCHAR(10),
    principal BIT DEFAULT 0,
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
        ON DELETE CASCADE
);

CREATE TABLE Producto(
    id_producto INT IDENTITY PRIMARY KEY,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(MAX),
    precio DECIMAL(10,2) NOT NULL CHECK (precio >= 0),
    stock INT NOT NULL CHECK (stock >= 0),
    activo BIT DEFAULT 1,
    imagen NVARCHAR(255)
);

CREATE TABLE Pedido(
    id_pedido INT IDENTITY PRIMARY KEY,
    id_cliente INT NOT NULL,
    fecha DATETIME DEFAULT GETDATE(),
    estado NVARCHAR(20) DEFAULT 'Pendiente'
        CHECK (estado IN ('Pendiente','En proceso','Enviado','Entregado','Cancelado')),
    total DECIMAL(12,2) DEFAULT 0,
    id_direccion INT NULL,
    id_operador INT NULL,

    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
        ON DELETE CASCADE,

    FOREIGN KEY (id_direccion) REFERENCES Direccion(id_direccion)
        ON DELETE NO ACTION  
);

CREATE TABLE DetallePedido(
    id_detalle INT IDENTITY PRIMARY KEY,
    id_pedido INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal AS (cantidad * precio_unitario),
    FOREIGN KEY (id_pedido) REFERENCES Pedido(id_pedido)
        ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
);

CREATE TABLE Pago(
    id_pago INT IDENTITY PRIMARY KEY,
    id_pedido INT NOT NULL,
    metodo NVARCHAR(20)
        CHECK (metodo IN ('Tarjeta','Transferencia','Efectivo')),
    monto DECIMAL(10,2) NOT NULL,
    fecha_pago DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (id_pedido) REFERENCES Pedido(id_pedido)
        ON DELETE CASCADE
);

CREATE TABLE Resena(
    id_resena INT IDENTITY PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_producto INT NOT NULL,
    calificacion INT CHECK (calificacion BETWEEN 1 AND 5),
    comentario NVARCHAR(MAX),
    fecha DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
        ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
);

CREATE TABLE Carrito(
    id_carrito INT IDENTITY PRIMARY KEY,
    id_cliente INT UNIQUE NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
        ON DELETE CASCADE
);

CREATE TABLE CarritoItem(
    id_item INT IDENTITY PRIMARY KEY,
    id_carrito INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT CHECK (cantidad > 0),
    precio_unitario DECIMAL(10,2),
    FOREIGN KEY (id_carrito) REFERENCES Carrito(id_carrito)
        ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
);

/*triggers y procedimientos almacenados*/
CREATE TRIGGER trg_RestarStock
ON DetallePedido
AFTER INSERT
AS
BEGIN
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN Producto p ON i.id_producto = p.id_producto
        WHERE p.stock < i.cantidad
    )
    BEGIN
        RAISERROR('Stock insuficiente',16,1);
        ROLLBACK TRANSACTION;
        RETURN;
    END

    UPDATE Producto
    SET stock = stock - i.cantidad
    FROM Producto p
    JOIN inserted i ON p.id_producto = i.id_producto;
END;
GO

CREATE TRIGGER trg_TotalPedido
ON DetallePedido
AFTER INSERT, DELETE
AS
BEGIN
    UPDATE Pedido
    SET total = (
        SELECT SUM(subtotal)
        FROM DetallePedido
        WHERE id_pedido = Pedido.id_pedido
    );
END;
GO

CREATE PROCEDURE sp_CambiarEstadoPedido
    @id_pedido INT,
    @estado NVARCHAR(20)
AS
BEGIN
    UPDATE Pedido
    SET estado = @estado
    WHERE id_pedido = @id_pedido;
END;
GO

ALTER TABLE Producto
ADD categoria NVARCHAR(100);
GO

-- --- INSERTAR ADMINISTRADORES ---
INSERT INTO Usuario (nombre, correo, contrasena, rol)
VALUES 
('Nestor Hernandez', 'admin1@senza.mx', 'admin123', 'Administrador'),
('Itzel Arteaga', 'admin2@senza.mx', 'admin123', 'Administrador');

-- --- INSERTAR OPERADORES ---
INSERT INTO Usuario (nombre, correo, contrasena, rol)
VALUES 
('Operador Matutino', 'operador1@senza.mx', 'opera123', 'Operador'),
('Operador Vespertino', 'operador2@senza.mx', 'opera123', 'Operador');

-- --- VERIFICACI�N ---
-- Esto te mostrar� la lista para confirmar que se guardaron
SELECT id_usuario, nombre, correo, rol, contrasena FROM Usuario;

INSERT INTO Producto (nombre, descripcion, precio, stock, activo, imagen, categoria) VALUES
('Pan de Masa Madre', 'Pan artesanal de fermentaci�n lenta, corteza crujiente y miga con sabor profundo.', 30.00, 10, 1, 'Imagenes/pan_masa_madre.jpg', 'panaderia'),
('Baguette Francesa', 'Barra cl�sica francesa: corteza dorada y miga ligera y aireada.', 35.00, 10, 1, 'Imagenes/baguette.jpeg', 'panaderia'),
('Tarta de Bayas', 'Base de mantequilla con crema pastelera y mezcla de bayas frescas.', 450.00, 10, 1, 'Imagenes/tarta_bayas.jpeg', 'pasteles'),
('Cheesecake de Fresa', 'Tradicional y cremoso, con ba�o de fresas naturales.', 100.00, 10, 1, 'Imagenes/cheesecakefresa.jpeg', 'pasteles'),
('Galleta con Chispas', 'Galleta de mantequilla con chispas de chocolate belga, reci�n horneada.', 20.00, 10, 1, 'Imagenes/galleta_chispas.jpeg', 'galletas'),
('Galleta de Avena', 'Suave y crujiente, con avena integral y un toque de canela.', 20.00, 10, 1, 'Imagenes/galleta_avena.jpg', 'galletas'),
('Caf� Americano', 'Caf� 100% mexicano, reci�n molido y preparado al momento.', 30.00, 10, 1, 'Imagenes/cafe_americano.jpeg', 'bebidas'),
('T� Chai Latte', 'Mezcla arom�tica de especias con leche espumosa, ligeramente endulzado.', 55.00, 10, 1, 'Imagenes/te_chai_latte.jpeg', 'bebidas'),
('Matcha', 'Bebida de t� verde matcha de alta calidad, preparada con leche o agua.', 80.00, 10, 1, 'Imagenes/matcha.jpeg', 'bebidas'),
('Taro', 'Bebida cremosa con sabor a taro, ligeramente dulce y suave.', 80.00, 10, 1, 'Imagenes/taro.jpeg', 'bebidas'),
('Dona de Chocolate con Chispas', 'Dona esponjosa cubierta con chocolate y chispas de colores.', 25.00, 10, 1, 'Imagenes/dona_chocolate_chispas.jpeg', 'panaderia'),
('Dona de Az�car', 'Dona cl�sica espolvoreada con az�car fina para un toque dulce.', 25.00, 10, 1, 'Imagenes/dona_azucar.jpeg', 'panaderia'),
('Cuernito', 'Croissant estilo ligero y mantecoso, perfecto para acompa�ar caf�.', 20.00, 10, 1, 'Imagenes/cuerno.jpg', 'panaderia'),
('Agua de Horchata', 'Bebida tradicional de arroz con canela, fresca y ligeramente dulce.', 30.00, 10, 1, 'Imagenes/horchata.jpeg', 'bebidas'),
('Beignets', 'Pasta frita francesa, esponjosa y espolvoreada con az�car glass.', 60.00, 10, 1, 'Imagenes/beignets.jpeg', 'panaderia'),
('Rol de Canela', 'Roll suave con relleno de canela y glaseado ligero.', 30.00, 10, 1, 'Imagenes/rol_canela.jpeg', 'panaderia'),
('Caf� Moka', 'Delicioso caf� con chocolate y leche espumosa.', 45.00, 10, 1, 'Imagenes/cafe_moka.jpeg', 'bebidas'),
('Pastel de Fresa con Crema', 'Bizcocho delicado relleno y cubierto con crema y fresas naturales.', 480.00, 10, 1, 'Imagenes/pastel_fresa.jpeg', 'pasteles'),
('Tiramis� de Matcha', 'Versi�n cremosa del cl�sico tiramis� con t� matcha.', 150.00, 10, 1, 'Imagenes/tiramisu_matcha.jpeg', 'pasteles'),
('Tarta de Cerezas', 'Tarta con cerezas jugosas y masa quebrada crujiente.', 150.00, 10, 1, 'Imagenes/tarta_cerezas.jpeg', 'pasteles'),
('Bolillo Mexicano', 'Cl�sico bolillo, ideal para tortas o acompa�ar comidas.', 4.00, 10, 1, 'Imagenes/bolillo.jpeg', 'panaderia'),
('Torta Balcarce', 'Pastel tradicional con capas esponjosas y crema suave.', 480.00, 10, 1, 'Imagenes/torta_balcarce.jpeg', 'pasteles'),
('Cheesecake de Ar�ndanos', 'Queso cremoso con base de galleta y cobertura de ar�ndanos.', 145.00, 10, 1, 'Imagenes/cheescake_arandanos.jpeg', 'pasteles'),
('Chocolate Caliente', 'Bebida espesa y reconfortante preparada con chocolate real.', 45.00, 10, 1, 'Imagenes/chocolate.jpeg', 'bebidas'),
('Frapuccino de Galleta', 'Bebida fr�a cremosa con sabor a galleta y topping crujiente.', 45.00, 10, 1, 'Imagenes/frapuccino_galleta.jpeg', 'bebidas'),
('Pay de Fresa', 'Pay con relleno de fresa natural y base crujiente.', 100.00, 10, 1, 'Imagenes/pay_fresa.jpeg', 'pasteles'),
('Pastel de �ngel', 'Bizcocho ligero y esponjoso, perfecto para ocasiones especiales.', 450.00, 10, 1, 'Imagenes/pastel_angel.jpeg', 'pasteles'),
('Flan', 'Flan casero con textura suave y caramelo dorado.', 90.00, 10, 1, 'Imagenes/flan.jpeg', 'pasteles'),
('Donas Rellenas de Crema Pastelera', 'Donas suaves rellenas con crema pastelera y glaseado ligero.', 35.00, 10, 1, 'Imagenes/donas_crema_pastelera.jpeg', 'panaderia'),
('Chamoyada de Mango', 'Refrescante con mango natural y chamoy, toque dulce-picante.', 40.00, 10, 1, 'Imagenes/chamoyada.jpeg', 'bebidas'),
('Cold Brew', 'Caf� de extracci�n en fr�o: suave, menos �cido y con gran cuerpo.', 55.00, 10, 1, 'Imagenes/cold_brew.jpeg', 'bebidas'),
('Tiramis� de Chocolate', 'Capas de bizcocho empapadas y crema de mascarpone con chocolate.', 100.00, 10, 1, 'Imagenes/tiramisu_chocolate.jpeg', 'pasteles'),
('Pastel de Mil Hojas', 'Hojas hojaldradas con crema pastelera entre capas, textura crujiente.', 480.00, 10, 1, 'Imagenes/pastel_mil_hojas.jpg', 'pasteles'),
('Bigote', 'Pieza de pan tradicional con toque dulce, ideal para acompa�ar caf�.', 25.00, 10, 1, 'Imagenes/bigote.jpeg', 'panaderia'),
('Gelatina', 'Gelatina casera con textura firme y sabor refrescante.', 100.00, 10, 1, 'Imagenes/gelatina.jpg', 'pasteles'),
('Galleta de Mantequilla', 'Cl�sica galleta casera con textura impecable y sabor a mantequilla.', 25.00, 10, 1, 'Imagenes/galleta_matequilla.jpg', 'galletas'),
('Galleta de Az�car', 'Galleta dulce y delicada, perfecta con una bebida caliente.', 20.00, 10, 1, 'Imagenes/galleta_azcar.jpg', 'galletas'),
('Galleta Integral', 'Galleta con harina integral y semillas, opci�n m�s saludable.', 30.00, 10, 1, 'Imagenes/galleta_integral.jpg', 'galletas'),
('Concha de Vainilla', 'Pan dulce con su cl�sica cubierta de sabor a vainilla.', 30.00, 10, 1, 'Imagenes/concha_vanilla.jpg', 'panaderia'),
('Concha de Chocolate', 'Deliciosa concha cubierta de chocolate, ideal para los amantes del cacao.', 30.00, 10, 1, 'Imagenes/concha_chocolate.jpg', 'panaderia'),
('Bisquet', 'Pan tierno y hojaldrado, perfecto para acompa�ar desayunos.', 30.00, 10, 1, 'Imagenes/bisquet.jpg', 'panaderia'),
('Polvorones', 'Galletas tradicionales, mantecosas y delicadas al paladar.', 25.00, 10, 1, 'Imagenes/polvorones.jpg', 'galletas'),
('Galleta de Canela', 'Galleta arom�tica con canela, perfecta para la temporada fr�a.', 25.00, 10, 1, 'Imagenes/galletas_canela.jpg', 'galletas'),
('Macarrones', 'Delicados macarons con relleno cremoso, textura ligera.', 40.00, 10, 1, 'Imagenes/macarrones.jpg', 'galletas'),
('Espresso', 'Shot concentrado de caf�, aroma intenso y crema natural.', 35.00, 10, 1, 'Imagenes/espresso.jpg', 'bebidas'),
('Galleta de la Suerte', 'Galleta crujiente con mensaje sorpresa en su interior.', 15.00, 10, 1, 'Imagenes/galleta_suerte.jpg', 'galletas'),
('Malteada de Chocolate', 'Malteada cremosa con helado de chocolate y topping de virutas.', 55.00, 10, 1, 'Imagenes/malteada_chocolate.jpg', 'bebidas'),
('Galleta de Coco', 'Galleta con textura crujiente y sabor natural a coco.', 25.00, 10, 1, 'Imagenes/galleta_coco.jpg', 'galletas'),
('Galletas Decoradas', 'Galletas artesanales decoradas a mano, ideales para regalos.', 25.00, 10, 1, 'Imagenes/galleta_decorada.jpg', 'galletas'),
('Galleta de Nuez', 'Galleta con trozos de nuez y textura crujiente por fuera.', 25.00, 10, 1, 'Imagenes/galleta_nuez.jpg', 'galletas');

SELECT * FROM Producto WHERE activo = 1;
UPDATE Usuario
SET correo = @nuevo_correo
WHERE id_usuario = @id_usuario;

select * from Usuario;
select * from Cliente;
select * from Direccion;

ALTER TABLE Usuario
ADD telefono NVARCHAR(100);
GO
