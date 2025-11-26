-- Base de datos
CREATE DATABASE SensaReposteria;
USE SensaReposteria;


CREATE TABLE Usuario (
    id_usuario INT IDENTITY(1,1) PRIMARY KEY,
    nombre NVARCHAR(100) NOT NULL,
    correo NVARCHAR(100) NOT NULL UNIQUE,
    contrasena NVARCHAR(100) NOT NULL,
    rol NVARCHAR(20) CHECK (rol IN ('Administrador', 'Operador', 'Cliente')) NOT NULL
);

-- ===========================================
--  2. Tabla Cliente
-- ===========================================
CREATE TABLE Cliente (
    id_cliente INT IDENTITY(1,1) PRIMARY KEY,
    id_usuario INT NOT NULL,
    telefono NVARCHAR(15),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
-- ===========================================
--  3. Tabla Producto
-- ===========================================
CREATE TABLE Producto (
    id_producto INT IDENTITY(1,1) PRIMARY KEY,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(MAX),
    precio DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    imagen NVARCHAR(255)
);

-- ===========================================
--  4. Tabla Pedido
-- ===========================================
CREATE TABLE Pedido (
    id_pedido INT IDENTITY(1,1) PRIMARY KEY,
    id_cliente INT NOT NULL,
    fecha DATETIME DEFAULT GETDATE(),
    estado NVARCHAR(20) CHECK (estado IN ('Pendiente', 'En proceso', 'Enviado', 'Entregado', 'Cancelado')) DEFAULT 'Pendiente',
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ===========================================
--  5. Tabla DetallePedido
-- ===========================================
CREATE TABLE DetallePedido (
    id_detalle INT IDENTITY(1,1) PRIMARY KEY,
    id_pedido INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (id_pedido) REFERENCES Pedido(id_pedido)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- ===========================================
--  6. Tabla Pago
-- ===========================================
CREATE TABLE Pago (
    id_pago INT IDENTITY(1,1) PRIMARY KEY,
    id_pedido INT NOT NULL,
    metodo NVARCHAR(20) CHECK (metodo IN ('Tarjeta', 'Transferencia', 'Efectivo')) NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha_pago DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (id_pedido) REFERENCES Pedido(id_pedido)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ===========================================
--  7. Tabla Direccion
-- ===========================================
CREATE TABLE Direccion (
    id_direccion INT IDENTITY(1,1) PRIMARY KEY,
    id_cliente INT NOT NULL,
    calle NVARCHAR(100) NOT NULL,
    numero NVARCHAR(10),
    colonia NVARCHAR(100),
    ciudad NVARCHAR(100),
    codigo_postal NVARCHAR(10),
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ===========================================
--  8. Tabla Reseña
-- ===========================================
CREATE TABLE Resena (
    id_resena INT IDENTITY(1,1) PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_producto INT NOT NULL,
    calificacion INT CHECK (calificacion BETWEEN 1 AND 5),
    comentario NVARCHAR(MAX),
    fecha DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
