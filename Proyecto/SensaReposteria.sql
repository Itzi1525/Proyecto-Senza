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

CREATE PROCEDURE sp_CambiarEstadoPedido
    @id_pedido INT,
    @estado NVARCHAR(20)
AS
BEGIN
    UPDATE Pedido
    SET estado = @estado
    WHERE id_pedido = @id_pedido;
END;
