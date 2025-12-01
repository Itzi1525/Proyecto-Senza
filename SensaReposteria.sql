-- Base de datos
CREATE DATABASE SensaReposteria;
USE SensaReposteria;

CREATE TABLE Usuario(
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('Administrador','Operador','Cliente')),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Cliente(
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT UNIQUE NOT NULL,
    telefono VARCHAR(20),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
        ON DELETE CASCADE
);

CREATE TABLE Direccion(
    id_direccion INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    calle VARCHAR(100) NOT NULL,
    numero VARCHAR(20),
    colonia VARCHAR(100),
    ciudad VARCHAR(100),
    codigo_postal VARCHAR(10),
    principal TINYINT(1) DEFAULT 0,
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
        ON DELETE CASCADE
);

CREATE TABLE Producto(
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL CHECK (precio >= 0),
    stock INT NOT NULL CHECK (stock >= 0),
    activo TINYINT(1) DEFAULT 1,
    imagen VARCHAR(255)
);

CREATE TABLE Pedido(
    id_pedido INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'Pendiente'
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
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_pedido INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (id_pedido) REFERENCES Pedido(id_pedido)
        ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
);

CREATE TABLE Pago(
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    id_pedido INT NOT NULL,
    metodo VARCHAR(20)
        CHECK (metodo IN ('Tarjeta','Transferencia','Efectivo')),
    monto DECIMAL(10,2) NOT NULL,
    fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_pedido) REFERENCES Pedido(id_pedido)
        ON DELETE CASCADE
);

CREATE TABLE Resena(
    id_resena INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_producto INT NOT NULL,
    calificacion INT CHECK (calificacion BETWEEN 1 AND 5),
    comentario TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
        ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
);

CREATE TABLE Carrito(
    id_carrito INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT UNIQUE NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
        ON DELETE CASCADE
);

CREATE TABLE CarritoItem(
    id_item INT AUTO_INCREMENT PRIMARY KEY,
    id_carrito INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT CHECK (cantidad > 0),
    precio_unitario DECIMAL(10,2),
    FOREIGN KEY (id_carrito) REFERENCES Carrito(id_carrito)
        ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
);
