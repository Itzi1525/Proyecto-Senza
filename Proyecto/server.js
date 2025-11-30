const express = require('express');
const cors = require('cors');
const sql = require('mssql/msnodesqlv8');

const app = express();

app.use(express.json());
app.use(cors());

// --- CONFIGURACIÓN CON TUS DATOS EXACTOS ---
const config = {
    // Fíjate en la doble barra: \\
    server: 'LAPTOP-VMHJ4L8R\\SQLEXPRESS01', 
    database: 'SensaReposteria',
    driver: 'msnodesqlv8',
    options: {
        trustedConnection: true, // Esto usa tu Windows Authentication
        trustServerCertificate: true // Acepta certificados locales
    }
};

// --- RUTA 1: REGISTRAR USUARIO ---
app.post('/registro', async (req, res) => {
    try {
        const pool = await sql.connect(config);
        const { nombre, email, password } = req.body;

        const check = await pool.request()
            .input('email', sql.NVarChar, email)
            .query('SELECT id_usuario FROM Usuario WHERE correo = @email');

        if (check.recordset.length > 0) {
            return res.status(400).json({ success: false, message: 'El correo ya está registrado' });
        }

        const result = await pool.request()
            .input('nombre', sql.NVarChar, nombre)
            .input('email', sql.NVarChar, email)
            .input('pass', sql.NVarChar, password) 
            .query(`
                INSERT INTO Usuario (nombre, correo, contrasena, rol) 
                OUTPUT inserted.id_usuario 
                VALUES (@nombre, @email, @pass, 'Cliente')
            `);

        const idNuevo = result.recordset[0].id_usuario;

        await pool.request()
            .input('id', sql.Int, idNuevo)
            .query('INSERT INTO Cliente (id_usuario) VALUES (@id)');

        res.json({ success: true, message: 'Usuario registrado exitosamente' });

    } catch (err) {
        console.error("Error en registro:", err);
        res.status(500).json({ success: false, message: 'Error en el servidor: ' + err.message });
    }
});

// --- RUTA 2: INICIAR SESIÓN ---
app.post('/login', async (req, res) => {
    try {
        const pool = await sql.connect(config);
        const { email, password } = req.body;

        const result = await pool.request()
            .input('email', sql.NVarChar, email)
            .query('SELECT id_usuario, nombre, contrasena, rol FROM Usuario WHERE correo = @email');

        if (result.recordset.length > 0) {
            const user = result.recordset[0];
            
            if (user.contrasena === password) {
                res.json({ 
                    success: true, 
                    message: 'Bienvenido',
                    user: { nombre: user.nombre, rol: user.rol } 
                });
            } else {
                res.status(401).json({ success: false, message: 'Contraseña incorrecta' });
            }
        } else {
            res.status(404).json({ success: false, message: 'Usuario no encontrado' });
        }

    } catch (err) {
        console.error("Error en login:", err);
        res.status(500).json({ success: false, message: 'Error de servidor' });
    }
});

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`✅ Servidor conectado a LAPTOP-VMHJ4L8R\\SQLEXPRESS01`);
    console.log(`🚀 Corriendo en http://localhost:${PORT}`);
});