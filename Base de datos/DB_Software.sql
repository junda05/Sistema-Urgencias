DROP DATABASE IF EXISTS sistema_visualizacion;
CREATE DATABASE sistema_visualizacion;
USE sistema_visualizacion;
CREATE TABLE pacientes (
    nombre VARCHAR(255),
    documento VARCHAR(20),
    triage VARCHAR(20),
    ci VARCHAR(255),
    labs VARCHAR(255),
    ix VARCHAR(255),
    inter VARCHAR(255),
    rv VARCHAR(255),
    pendientes TEXT,
    conducta VARCHAR(20), 
    ubicacion VARCHAR(50),
    ingreso DATETIME,
    id INT AUTO_INCREMENT PRIMARY KEY
);

ALTER TABLE pacientes ADD COLUMN triage_timestamp DATETIME AFTER triage;
ALTER TABLE pacientes ADD COLUMN observacion_timestamp DATETIME AFTER id;
-- Añadir campos de timestamp para consulta de ingreso (CI)
ALTER TABLE pacientes ADD COLUMN ci_no_realizado_timestamp DATETIME COMMENT 'Momento en que CI se establece como No realizado' AFTER observacion_timestamp;
ALTER TABLE pacientes ADD COLUMN ci_realizado_timestamp DATETIME COMMENT 'Momento en que CI se establece como Realizado' AFTER ci_no_realizado_timestamp;

-- Añadir campos de timestamp para laboratorios (Labs)
ALTER TABLE pacientes ADD COLUMN labs_no_realizado_timestamp DATETIME COMMENT 'Momento en que Labs se establece como No se ha realizado' AFTER ci_realizado_timestamp;
ALTER TABLE pacientes ADD COLUMN labs_solicitados_timestamp DATETIME COMMENT 'Momento en que Labs se establece como En espera de resultados' AFTER labs_no_realizado_timestamp;
ALTER TABLE pacientes ADD COLUMN labs_completos_timestamp DATETIME COMMENT 'Momento en que Labs se establece como Resultados completos' AFTER labs_solicitados_timestamp;

-- Añadir campos de timestamp para imágenes diagnósticas (IX)
ALTER TABLE pacientes ADD COLUMN ix_no_realizado_timestamp DATETIME COMMENT 'Momento en que IX se establece como No se ha realizado' AFTER labs_completos_timestamp;
ALTER TABLE pacientes ADD COLUMN ix_solicitados_timestamp DATETIME COMMENT 'Momento en que IX se establece como En espera de resultados' AFTER ix_no_realizado_timestamp;
ALTER TABLE pacientes ADD COLUMN ix_completos_timestamp DATETIME COMMENT 'Momento en que IX se establece como Resultados completos' AFTER ix_solicitados_timestamp;

-- Añadir campos de timestamp para interconsulta
ALTER TABLE pacientes ADD COLUMN inter_no_abierta_timestamp DATETIME COMMENT 'Momento en que Interconsulta se establece como No se ha abierto' AFTER ix_completos_timestamp;
ALTER TABLE pacientes ADD COLUMN inter_abierta_timestamp DATETIME COMMENT 'Momento en que Interconsulta se establece como Abierta' AFTER inter_no_abierta_timestamp;
ALTER TABLE pacientes ADD COLUMN inter_realizada_timestamp DATETIME COMMENT 'Momento en que Interconsulta se establece como Realizada' AFTER inter_abierta_timestamp;

-- Añadir campos de timestamp para revaloración (RV)
ALTER TABLE pacientes ADD COLUMN rv_no_realizado_timestamp DATETIME COMMENT 'Momento en que RV se establece como No realizado' AFTER inter_realizada_timestamp;
ALTER TABLE pacientes ADD COLUMN rv_realizado_timestamp DATETIME COMMENT 'Momento en que RV se establece como Realizado' AFTER rv_no_realizado_timestamp;

-- Añadir campo de timestamp para alta
ALTER TABLE pacientes ADD COLUMN alta_timestamp DATETIME COMMENT 'Momento en que la conducta se establece como De alta' AFTER rv_realizado_timestamp;

-- Crear tabla para almacenar métricas calculadas para análisis histórico
CREATE TABLE IF NOT EXISTS metricas_pacientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NOT NULL,
    fecha_calculo DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Métricas de tiempo en minutos
    tiempo_triage INT COMMENT 'Minutos desde ingreso hasta realizar triage',
    clase_triage VARCHAR(1) COMMENT 'Nivel de triage (1-5)',
    tiempo_ci INT COMMENT 'Minutos desde No realizado a Realizado',
    tiempo_labs_solicitud INT COMMENT 'Minutos desde No realizado a En espera de resultados',
    tiempo_labs_resultados INT COMMENT 'Minutos desde En espera de resultados a Resultados completos',
    tiempo_labs_total INT COMMENT 'Minutos desde No realizado a Resultados completos',
    tiempo_ix_solicitud INT COMMENT 'Minutos desde No realizado a En espera de resultados',
    tiempo_ix_resultados INT COMMENT 'Minutos desde En espera de resultados a Resultados completos',
    tiempo_ix_total INT COMMENT 'Minutos desde No realizado a Resultados completos',
    tiempo_inter_apertura INT COMMENT 'Minutos desde No abierta a Abierta',
    tiempo_inter_realizacion INT COMMENT 'Minutos desde Abierta a Realizada',
    tiempo_inter_total INT COMMENT 'Minutos desde No abierta a Realizada',
    tiempo_rv INT COMMENT 'Minutos desde No realizado a Realizado',
    tiempo_total_atencion INT COMMENT 'Minutos desde ingreso hasta alta',
    
    -- Campos para análisis estadístico
    area VARCHAR(50) COMMENT 'Área de atención',
    
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
);

-- Crear índices para optimizar consultas de métricas
CREATE INDEX idx_metricas_paciente_id ON metricas_pacientes(paciente_id);
CREATE INDEX idx_metricas_fecha_calculo ON metricas_pacientes(fecha_calculo);
CREATE INDEX idx_metricas_clase_triage ON metricas_pacientes(clase_triage);
CREATE INDEX idx_metricas_area ON metricas_pacientes(area);

-- Tabla para almacenar los laboratorios seleccionados para cada paciente
CREATE TABLE pacientes_laboratorios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NOT NULL,
    codigo_lab VARCHAR(50) NOT NULL,
    estado VARCHAR(50) DEFAULT 'No se ha realizado',
    fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
);

-- Tabla para almacenar los laboratorios seleccionados para cada paciente
CREATE TABLE pacientes_ixs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NOT NULL,
    codigo_ix VARCHAR(50) NOT NULL,
    estado VARCHAR(50) DEFAULT 'No se ha realizado',
    fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
);

-- Tabla para almacenar la trazabilidad de acciones
CREATE TABLE IF NOT EXISTS `trazabilidad` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `usuario` varchar(100) NOT NULL,
  `rol` varchar(50) NOT NULL,
  `accion` varchar(100) NOT NULL,
  `fecha_hora` datetime NOT NULL,
  `paciente_afectado` varchar(255) DEFAULT NULL,
  `detalles_cambio` text,
  INDEX idx_usuario (`usuario`),
  INDEX idx_fecha_hora (`fecha_hora`),
  INDEX idx_paciente (`paciente_afectado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE trazabilidad 
    ADD COLUMN usuario_id INT,
    ADD FOREIGN KEY (usuario_id) REFERENCES usuarios(id);
    
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    nombre_completo VARCHAR(100) NOT NULL,
    rol_admin BOOLEAN DEFAULT FALSE,
    rol_medico BOOLEAN DEFAULT FALSE,
    rol_visitante BOOLEAN DEFAULT FALSE,
	estado VARCHAR(20) DEFAULT 'activo',
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso DATETIME NULL,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT * FROM usuarios;
DROP TABLE IF EXISTS trazabilidad;

UPDATE usuarios
SET estado = 'inactivo'	
WHERE username = 'user1';

-- Comprobar y añadir índices solo si no existen
SET @exist_rol_index = (
    SELECT COUNT(1) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = 'sistema_visualizacion' AND TABLE_NAME = 'trazabilidad' AND INDEX_NAME = 'idx_rol'
);

-- Solo añadir el índice de rol ya que los otros ya existen en la definición de la tabla
SET @sql_rol = IF(@exist_rol_index = 0, 'ALTER TABLE trazabilidad ADD INDEX idx_rol (rol)', 'SELECT ''Índice idx_rol ya existe''');
PREPARE stmt FROM @sql_rol;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Crear vista para trazabilidad con roles traducidos correctamente
CREATE OR REPLACE VIEW vista_trazabilidad AS
SELECT 
    id,
    usuario,
    CASE 
        WHEN rol = 'admin' THEN 'Administrador'
        WHEN rol = 'medico' THEN 'Médico'
        WHEN rol = 'visitante' THEN 'Visitante'
        ELSE rol
    END as rol,
    accion,
    fecha_hora,
    paciente_afectado,
    detalles_cambio
FROM 
    trazabilidad
ORDER BY 
    fecha_hora DESC;

-- Actualizar registros existentes para corregir roles en formato incorrecto
-- Versión compatible con safe update mode
UPDATE trazabilidad t
JOIN (
    SELECT t.id
    FROM trazabilidad t
    JOIN usuarios u ON t.usuario = u.username
    WHERE (t.rol = 'admin' OR t.rol = 'Sin rol') AND u.rol_admin = 1
) AS ids ON t.id = ids.id
SET t.rol = 'Administrador';

UPDATE trazabilidad t
JOIN (
    SELECT t.id
    FROM trazabilidad t
    JOIN usuarios u ON t.usuario = u.username
    WHERE t.rol = 'medico' AND u.rol_medico = 1
) AS ids ON t.id = ids.id
SET t.rol = 'Médico';

UPDATE trazabilidad t
JOIN (
    SELECT t.id
    FROM trazabilidad t
    JOIN usuarios u ON t.usuario = u.username
    WHERE t.rol = 'visitante' AND u.rol_visitante = 1
) AS ids ON t.id = ids.id
SET t.rol = 'Visitante';

SELECT * FROM pacientes


INSERT INTO pacientes 
(nombre, documento, triage, triage_timestamp, ci, labs, ix, inter, rv, pendientes, conducta, ubicacion, ingreso, id, observacion_timestamp, ci_no_realizado_timestamp, ci_realizado_timestamp, labs_no_realizado_timestamp, labs_solicitados_timestamp, labs_completos_timestamp, ix_no_realizado_timestamp, ix_solicitados_timestamp, ix_completos_timestamp, inter_no_abierta_timestamp, inter_abierta_timestamp, inter_realizada_timestamp, rv_no_realizado_timestamp, rv_realizado_timestamp, alta_timestamp)
VALUES 
-- Paciente 1: Caso de atención completa y alta (triage 1)
('Jose Mauricio Unda Ortiz', '1114565784', '1', '2025-05-02 09:40:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'De Alta', 'Amarilla - 26', '2025-05-02 09:39:27', 1, NULL, '2025-05-02 09:40:48', '2025-05-02 09:43:21', '2025-05-02 09:43:30', '2025-05-02 10:00:53', '2025-05-02 10:30:53', '2025-05-02 09:44:05', '2025-05-02 09:45:04', '2025-05-02 09:46:46', '2025-05-02 09:47:12', '2025-05-02 10:00:45', '2025-05-02 10:04:16', '2025-05-02 10:05:22', '2025-05-02 10:25:57', '2025-05-02 10:35:57'),

-- Paciente 2: Caso de alta rápida (triage 5)
('Maria Carmen Ortiz Lopez', '43625198', '5', '2025-05-02 10:15:22', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pediatría - 45', '2025-05-02 10:10:35', 2, NULL, '2025-05-02 10:15:30', '2025-05-02 10:25:10', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-05-02 10:26:22', '2025-05-02 10:40:57', '2025-05-02 10:45:12'),

-- Paciente 3: En observación con pruebas pendientes (triage 2)
('Carlos Alberto Ramirez Perez', '72148953', '2', '2025-05-02 08:20:15', 'Realizado', 'En espera de resultados', 'Resultados completos', 'Abierta', 'No realizado', 'Respuesta Interconsulta, Realizar RV', 'Observación', 'Amarilla - 30', '2025-05-02 08:15:05', 3, '2025-05-02 09:30:00', '2025-05-02 08:20:18', '2025-05-02 08:35:21', '2025-05-02 08:36:10', '2025-05-02 08:40:53', NULL, '2025-05-02 08:36:15', '2025-05-02 08:41:04', '2025-05-02 09:16:46', '2025-05-02 08:45:12', '2025-05-02 09:45:45', NULL, '2025-05-02 09:20:22', NULL, NULL),

-- Paciente 4: Hospitalización (triage 2)
('Ana Maria Gonzalez Rodriguez', '52987463', '2', '2025-05-02 07:50:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Antigua - 10', '2025-05-02 07:45:27', 4, NULL, '2025-05-02 07:50:48', '2025-05-02 08:10:21', '2025-05-02 08:11:30', '2025-05-02 08:15:53', '2025-05-02 09:10:53', '2025-05-02 08:12:05', '2025-05-02 08:15:04', '2025-05-02 09:05:46', '2025-05-02 08:20:12', '2025-05-02 08:30:45', '2025-05-02 09:04:16', '2025-05-02 09:05:22', '2025-05-02 09:25:57', NULL),

-- Paciente 5: Caso de triage 3 con interconsulta pendiente
('Juan Sebastian Moreno Diaz', '1015789632', '3', '2025-05-02 11:05:49', 'Realizado', 'Resultados completos', 'En espera de resultados', 'Abierta', 'No realizado', 'Respuesta Interconsulta, Realizar RV', 'Observación', 'Antigua - 12', '2025-05-02 11:00:27', 5, '2025-05-02 12:15:00', '2025-05-02 11:05:48', '2025-05-02 11:20:21', '2025-05-02 11:21:30', '2025-05-02 11:25:53', '2025-05-02 12:05:53', '2025-05-02 11:22:05', '2025-05-02 11:25:04', NULL, '2025-05-02 11:30:12', '2025-05-02 12:00:45', NULL, '2025-05-02 11:31:22', NULL, NULL),

-- Paciente 6: Caso de atención completa triage 4
('Patricia Elena Rojas Vargas', '63258741', '4', '2025-05-02 10:35:49', 'Realizado', 'Resultados completos', 'No se ha realizado', 'Realizada', 'Realizado', '', 'De Alta', 'Amarilla - 22', '2025-05-02 10:30:27', 6, NULL, '2025-05-02 10:35:48', '2025-05-02 10:50:21', '2025-05-02 10:51:30', '2025-05-02 10:55:53', '2025-05-02 11:20:53', NULL, NULL, NULL, '2025-05-02 11:00:12', '2025-05-02 11:10:45', '2025-05-02 11:30:16', '2025-05-02 11:31:22', '2025-05-02 11:45:57', '2025-05-02 12:00:57'),

-- Paciente 7: Caso de paciente NN (anónimo)
('NN - 2025-05-02 - 12:15:22', 'NN - 20250502121522', '3', '2025-05-02 12:20:49', 'Realizado', 'En espera de resultados', 'En espera de resultados', 'No se ha abierto', 'No realizado', 'Abrir Interconsulta, Realizar RV', 'Observación', 'Pediatría - 40', '2025-05-02 12:15:22', 7, '2025-05-02 12:45:00', '2025-05-02 12:20:48', '2025-05-02 12:35:21', '2025-05-02 12:36:30', '2025-05-02 12:40:53', NULL, '2025-05-02 12:37:05', '2025-05-02 12:41:04', NULL, NULL, NULL, NULL, '2025-05-02 12:42:22', NULL, NULL),

-- Paciente 8: Caso de triage 1 con CI apenas realizado
('Miguel Angel Castro Torres', '80123456', '1', '2025-05-02 13:10:49', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'No realizado', 'Abrir Interconsulta, Realizar RV', 'Observación', 'Amarilla - 24', '2025-05-02 13:05:27', 8, '2025-05-02 13:15:00', '2025-05-02 13:10:48', '2025-05-02 13:15:21', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-05-02 13:16:22', NULL, NULL),

-- Paciente 9: Paciente en espera de CI (triage ya asignado)
('Sofia Andrea Martinez Ruiz', '1020987654', '2', '2025-05-02 13:30:49', 'No realizado', '', '', '', '', 'Valoración CI', '', 'Amarilla - 28', '2025-05-02 13:25:27', 9, NULL, '2025-05-02 13:30:48', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),

-- Paciente 10: Caso de paciente con datos completos
('Roberto Carlos Mendoza Castillo', '91547862', '3', '2025-05-02 09:20:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'De Alta', 'Antigua - 15', '2025-05-02 09:15:27', 10, NULL, '2025-05-02 09:20:48', '2025-05-02 09:35:21', '2025-05-02 09:36:30', '2025-05-02 09:40:53', '2025-05-02 10:20:53', '2025-05-02 09:37:05', '2025-05-02 09:40:04', '2025-05-02 10:10:46', '2025-05-02 09:45:12', '2025-05-02 09:55:45', '2025-05-02 10:20:16', '2025-05-02 10:21:22', '2025-05-02 10:40:57', '2025-05-02 10:45:57'),

-- Paciente 11: Caso de paciente con imagenes pendientes
('Laura Valentina Ochoa Gutierrez', '1022345678', '2', '2025-05-02 10:50:49', 'Realizado', 'Resultados completos', 'En espera de resultados', 'No se ha abierto', 'No realizado', 'IMG pendientes: Radiografía de Tórax, Realizar RV', 'Observación', 'Pediatría - 42', '2025-05-02 10:45:27', 11, '2025-05-02 11:15:00', '2025-05-02 10:50:48', '2025-05-02 11:05:21', '2025-05-02 11:06:30', '2025-05-02 11:10:53', '2025-05-02 11:40:53', '2025-05-02 11:07:05', '2025-05-02 11:15:04', NULL, NULL, NULL, NULL, '2025-05-02 11:16:22', NULL, NULL),

-- Paciente 12: Caso triage 5 (baja prioridad)
('Pedro Fernando Guzman Silva', '79654321', '5', '2025-05-02 11:40:49', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'No realizado', 'Realizar RV', '', 'Pasillos - 65', '2025-05-02 11:35:27', 12, NULL, '2025-05-02 11:40:48', '2025-05-02 11:55:21', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-05-02 11:56:22', NULL, NULL),

-- Paciente 13: Caso triage 1 (alta prioridad) con todo en proceso
('Luisa Fernanda Parra Rodriguez', '52123789', '1', '2025-05-02 08:10:49', 'Realizado', 'En espera de resultados', 'En espera de resultados', 'Abierta', 'No realizado', 'Respuesta Interconsulta, Realizar RV, Labs pendientes: Hemograma Completo, IMG pendientes: Tomografía', 'Observación', 'Amarilla - 20', '2025-05-02 08:05:27', 13, '2025-05-02 08:20:00', '2025-05-02 08:10:48', '2025-05-02 08:15:21', '2025-05-02 08:16:30', '2025-05-02 08:20:53', NULL, '2025-05-02 08:17:05', '2025-05-02 08:20:04', NULL, '2025-05-02 08:25:12', '2025-05-02 08:30:45', NULL, '2025-05-02 08:31:22', NULL, NULL),

-- Paciente 14: Caso hospitalización pendiente
('Daniel Eduardo Cardenas Reyes', '1018765432', '2', '2025-05-02 12:50:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Antigua - 5', '2025-05-02 12:45:27', 14, NULL, '2025-05-02 12:50:48', '2025-05-02 13:05:21', '2025-05-02 13:06:30', '2025-05-02 13:10:53', '2025-05-02 13:40:53', '2025-05-02 13:07:05', '2025-05-02 13:10:04', '2025-05-02 13:45:46', '2025-05-02 13:15:12', '2025-05-02 13:25:45', '2025-05-02 13:50:16', '2025-05-02 13:51:22', '2025-05-02 14:05:57', NULL),

-- Paciente 15: Caso paciente CI no realizado aún
('Marcela Alejandra Duarte Medina', '1023456789', '3', '2025-05-02 14:05:49', 'No realizado', '', '', '', '', 'Valoración CI', '', 'Pediatría - 50', '2025-05-02 14:00:27', 15, NULL, '2025-05-02 14:05:48', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),

-- Paciente 16: Caso paciente recién ingresado (solo triage)
('Jhon Alejandro Quintero Muñoz', '1019876543', '2', '2025-05-02 14:20:49', 'No realizado', '', '', '', '', 'Valoración CI', '', 'Amarilla - 32', '2025-05-02 14:15:27', 16, NULL, '2025-05-02 14:20:48', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),

-- Paciente 17: Caso completo con alta
('Natalia Camila Herrera Osorio', '1021345678', '4', '2025-05-02 07:30:49', 'Realizado', 'Resultados completos', 'No se ha realizado', 'Realizada', 'Realizado', '', 'De Alta', 'Antigua - 8', '2025-05-02 07:25:27', 17, NULL, '2025-05-02 07:30:48', '2025-05-02 07:45:21', '2025-05-02 07:46:30', '2025-05-02 07:50:53', '2025-05-02 08:30:53', NULL, NULL, NULL, '2025-05-02 07:55:12', '2025-05-02 08:05:45', '2025-05-02 08:35:16', '2025-05-02 08:36:22', '2025-05-02 08:50:57', '2025-05-02 09:00:57'),

-- Paciente 18: Caso de atención en Clini
('Andrea Carolina Jimenez Molina', '53214569', '3', '2025-05-02 09:55:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'De Alta', 'Clini - 12', '2025-05-02 09:50:27', 18, NULL, '2025-05-02 09:55:48', '2025-05-02 10:10:21', '2025-05-02 10:11:30', '2025-05-02 10:15:53', '2025-05-02 10:45:53', '2025-05-02 10:12:05', '2025-05-02 10:15:04', '2025-05-02 10:40:46', '2025-05-02 10:20:12', '2025-05-02 10:30:45', '2025-05-02 10:50:16', '2025-05-02 10:51:22', '2025-05-02 11:05:57', '2025-05-02 11:15:57'),

-- Paciente 19: Caso en Sala de espera
('Victor Manuel Fonseca Rojas', '80254136', '3', '2025-05-02 13:45:49', 'No realizado', '', '', '', '', 'Valoración CI', '', 'Sala de espera - 1', '2025-05-02 13:40:27', 19, NULL, '2025-05-02 13:45:48', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),

-- Paciente 20: Caso paciente con labs e imágenes completas pero sin interconsulta
('Diana Carolina Torres Palacios', '1015432765', '2', '2025-05-02 11:20:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'No se ha abierto', 'No realizado', 'Abrir Interconsulta, Realizar RV', 'Observación', 'Amarilla - 34', '2025-05-02 11:15:27', 20, '2025-05-02 11:45:00', '2025-05-02 11:20:48', '2025-05-02 11:35:21', '2025-05-02 11:36:30', '2025-05-02 11:40:53', '2025-05-02 12:10:53', '2025-05-02 11:37:05', '2025-05-02 11:40:04', '2025-05-02 12:05:46', NULL, NULL, NULL, '2025-05-02 12:06:22', NULL, NULL);


-- Insertar métricas correspondientes a los 20 pacientes
INSERT INTO metricas_pacientes (
    paciente_id,
    fecha_calculo,
    tiempo_triage,
    clase_triage,
    tiempo_ci,
    tiempo_labs_solicitud,
    tiempo_labs_resultados,
    tiempo_labs_total,
    tiempo_ix_solicitud,
    tiempo_ix_resultados,
    tiempo_ix_total,
    tiempo_inter_apertura,
    tiempo_inter_realizacion,
    tiempo_inter_total,
    tiempo_rv,
    tiempo_total_atencion,
    area
)
VALUES
-- Métricas para Paciente 1
(1, NOW(), 1, '1', 3, 17, 30, 47, 1, 2, 3, 13, 4, 17, 21, 56, 'Amarilla'),

-- Métricas para Paciente 2
(2, NOW(), 5, '5', 10, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 15, 35, 'Pediatría'),

-- Métricas para Paciente 3
(3, NOW(), 5, '2', 15, 4, NULL, NULL, 5, 36, 41, 60, NULL, NULL, NULL, 75, 'Amarilla'),

-- Métricas para Paciente 4
(4, NOW(), 5, '2', 20, 1, 55, 56, 3, 51, 54, 10, 34, 44, 21, 80, 'Antigua'),

-- Métricas para Paciente 5
(5, NOW(), 5, '3', 15, 1, 40, 41, 3, NULL, NULL, 30, NULL, NULL, NULL, 75, 'Antigua'),

-- Métricas para Paciente 6
(6, NOW(), 5, '4', 15, 1, 25, 26, NULL, NULL, NULL, 10, 20, 30, 15, 90, 'Amarilla'),

-- Métricas para Paciente 7
(7, NOW(), 5, '3', 15, 1, NULL, NULL, 3, NULL, NULL, NULL, NULL, NULL, NULL, 30, 'Pediatría'),

-- Métricas para Paciente 8
(8, NOW(), 5, '1', 5, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 11, 'Amarilla'),

-- Métricas para Paciente 9
(9, NOW(), 5, '2', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5, 'Amarilla'),

-- Métricas para Paciente 10
(10, NOW(), 5, '3', 15, 1, 40, 41, 3, 31, 34, 10, 25, 35, 20, 90, 'Antigua'),

-- Métricas para Paciente 11
(11, NOW(), 5, '2', 15, 1, 30, 31, 3, NULL, NULL, NULL, NULL, NULL, NULL, 55, 'Pediatría'),

-- Métricas para Paciente 12
(12, NOW(), 5, '5', 15, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 20, 'Pasillos'),

-- Métricas para Paciente 13
(13, NOW(), 5, '1', 5, 1, NULL, NULL, 3, NULL, NULL, 5, NULL, NULL, NULL, 25, 'Amarilla'),

-- Métricas para Paciente 14
(14, NOW(), 5, '2', 15, 1, 30, 31, 3, 36, 39, 10, 25, 35, 15, 80, 'Antigua'),

-- Métricas para Paciente 15
(15, NOW(), 5, '3', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5, 'Pediatría'),

-- Métricas para Paciente 16
(16, NOW(), 5, '2', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5, 'Amarilla'),

-- Métricas para Paciente 17
(17, NOW(), 5, '4', 15, 1, 40, 41, NULL, NULL, NULL, 10, 30, 40, 15, 95, 'Antigua'),

-- Métricas para Paciente 18
(18, NOW(), 5, '3', 15, 1, 30, 31, 3, 26, 29, 10, 20, 30, 15, 85, 'Clini'),

-- Métricas para Paciente 19
(19, NOW(), 5, '3', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5, 'Sala de espera'),

-- Métricas para Paciente 20
(20, NOW(), 5, '2', 15, 1, 30, 31, 3, 26, 29, NULL, NULL, NULL, NULL, 50, 'Amarilla');


INSERT INTO pacientes 
(nombre, documento, triage, triage_timestamp, ci, labs, ix, inter, rv, pendientes, conducta, ubicacion, ingreso, id, observacion_timestamp, ci_no_realizado_timestamp, ci_realizado_timestamp, labs_no_realizado_timestamp, labs_solicitados_timestamp, labs_completos_timestamp, ix_no_realizado_timestamp, ix_solicitados_timestamp, ix_completos_timestamp, inter_no_abierta_timestamp, inter_abierta_timestamp, inter_realizada_timestamp, rv_no_realizado_timestamp, rv_realizado_timestamp, alta_timestamp)
VALUES 
-- Paciente 21: Caso urgente (triage 1) - abril 10
('Alejandro Martínez Gómez', '1022567890', '1', '2025-04-10 08:15:23', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'De Alta', 'Amarilla - 21', '2025-04-10 08:10:05', 21, NULL, '2025-04-10 08:15:25', '2025-04-10 08:25:18', '2025-04-10 08:26:30', '2025-04-10 08:40:15', '2025-04-10 09:50:22', '2025-04-10 08:27:05', '2025-04-10 08:45:04', '2025-04-10 09:35:46', '2025-04-10 08:55:12', '2025-04-10 09:25:45', '2025-04-10 10:15:16', '2025-04-10 10:16:22', '2025-04-10 10:35:57', '2025-04-10 10:45:57'),

-- Paciente 22: Triage 4 con atención rápida - abril 12
('Isabella Rodríguez López', '52678901', '4', '2025-04-12 14:25:49', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pasillos - 62', '2025-04-12 14:15:27', 22, NULL, '2025-04-12 14:25:52', '2025-04-12 14:55:21', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-12 15:05:22', '2025-04-12 15:25:57', '2025-04-12 15:30:57'),

-- Paciente 23: Hospitalización compleja (triage 2) - abril 14
('Camilo Andrés Torres Díaz', '80345789', '2', '2025-04-14 10:35:19', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 23', '2025-04-14 10:20:27', 23, NULL, '2025-04-14 10:35:22', '2025-04-14 11:00:21', '2025-04-14 11:01:30', '2025-04-14 11:15:53', '2025-04-14 13:10:53', '2025-04-14 11:02:05', '2025-04-14 11:20:04', '2025-04-14 13:05:46', '2025-04-14 11:45:12', '2025-04-14 12:30:45', '2025-04-14 14:10:16', '2025-04-14 14:11:22', '2025-04-14 14:40:57', NULL),

-- Paciente 24: Observación pediátrica (triage 3) - abril 15
('Valeria Sofia Castro Reyes', '1023456987', '3', '2025-04-15 16:50:49', 'Realizado', 'Resultados completos', 'En espera de resultados', 'Abierta', 'No realizado', 'Respuesta Interconsulta, IMG pendientes: Ecografía Abdominal', 'Observación', 'Pediatría - 43', '2025-04-15 16:40:27', 24, '2025-04-15 17:10:00', '2025-04-15 16:50:52', '2025-04-15 17:20:21', '2025-04-15 17:21:30', '2025-04-15 17:35:53', '2025-04-15 18:55:53', '2025-04-15 17:22:05', '2025-04-15 17:40:04', NULL, '2025-04-15 18:15:12', '2025-04-15 18:45:45', NULL, '2025-04-15 18:16:22', NULL, NULL),

-- Paciente 25: Triage 5 simple - abril 17
('Luis Felipe Méndez Ortiz', '70987123', '5', '2025-04-17 09:10:49', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pasillos - 67', '2025-04-17 09:00:27', 25, NULL, '2025-04-17 09:10:52', '2025-04-17 10:30:21', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-17 10:35:22', '2025-04-17 10:45:57', '2025-04-17 10:50:57'),

-- Paciente 26: Observación prolongada (triage 2) - abril 19
('Carolina Hernández Martínez', '53421789', '2', '2025-04-19 07:25:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Antigua - 7', '2025-04-19 07:15:27', 26, '2025-04-19 07:35:00', '2025-04-19 07:25:52', '2025-04-19 07:50:21', '2025-04-19 07:51:30', '2025-04-19 08:05:53', '2025-04-19 10:15:53', '2025-04-19 07:52:05', '2025-04-19 08:10:04', '2025-04-19 10:05:46', '2025-04-19 08:30:12', '2025-04-19 09:20:45', '2025-04-19 11:30:16', '2025-04-19 11:31:22', '2025-04-19 12:00:57', NULL),

-- Paciente 27: NN tráfico - abril 20
('NN - 2025-04-20 - 23:15:22', 'NN - 20250420231522', '1', '2025-04-20 23:25:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 25', '2025-04-20 23:15:22', 27, NULL, '2025-04-20 23:25:52', '2025-04-20 23:40:21', '2025-04-20 23:41:30', '2025-04-20 23:55:53', '2025-04-21 01:20:53', '2025-04-20 23:42:05', '2025-04-21 00:05:04', '2025-04-21 01:10:46', '2025-04-21 00:15:12', '2025-04-21 00:45:45', '2025-04-21 01:40:16', '2025-04-21 01:41:22', '2025-04-21 02:00:57', NULL),

-- Paciente 28: Atención Clini rápida (triage 3) - abril 22
('Manuel Antonio Parra Silva', '79654789', '3', '2025-04-22 12:35:49', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Clini - 14', '2025-04-22 12:25:27', 28, NULL, '2025-04-22 12:35:52', '2025-04-22 13:00:21', '2025-04-22 13:01:30', '2025-04-22 13:15:53', '2025-04-22 14:05:53', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-22 14:06:22', '2025-04-22 14:30:57', '2025-04-22 14:35:57'),

-- Paciente 29: Triage 4 simple - abril 23
('Natalia Andrea Guzmán Vargas', '1018765432', '4', '2025-04-23 11:15:49', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pasillos - 63', '2025-04-23 11:05:27', 29, NULL, '2025-04-23 11:15:52', '2025-04-23 11:45:21', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-23 11:50:22', '2025-04-23 12:05:57', '2025-04-23 12:10:57'),

-- Paciente 30: Urgencia compleja (triage 1) - abril 24
('Juan Sebastián Rojas Carrillo', '1022789456', '1', '2025-04-24 19:05:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 22', '2025-04-24 19:00:27', 30, NULL, '2025-04-24 19:05:52', '2025-04-24 19:15:21', '2025-04-24 19:16:30', '2025-04-24 19:30:53', '2025-04-24 20:45:53', '2025-04-24 19:17:05', '2025-04-24 19:35:04', '2025-04-24 20:40:46', '2025-04-24 19:45:12', '2025-04-24 20:15:45', '2025-04-24 21:10:16', '2025-04-24 21:11:22', '2025-04-24 21:35:57', NULL),

-- Paciente 31: Observación pediátrica (triage 2) - abril 25
('Gabriela Valentina Ortiz Medina', '1021789036', '2', '2025-04-25 08:40:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'De Alta', 'Pediatría - 47', '2025-04-25 08:30:27', 31, '2025-04-25 08:50:00', '2025-04-25 08:40:52', '2025-04-25 09:05:21', '2025-04-25 09:06:30', '2025-04-25 09:20:53', '2025-04-25 10:50:53', '2025-04-25 09:07:05', '2025-04-25 09:25:04', '2025-04-25 10:35:46', '2025-04-25 09:35:12', '2025-04-25 10:10:45', '2025-04-25 11:05:16', '2025-04-25 11:06:22', '2025-04-25 11:30:57', '2025-04-25 11:40:57'),

-- Paciente 32: Triage 3 en observación - abril 27
('Santiago Enrique Fonseca Duarte', '80567123', '3', '2025-04-27 15:20:49', 'Realizado', 'En espera de resultados', 'En espera de resultados', 'Abierta', 'No realizado', 'Respuesta Interconsulta, Labs pendientes: Química Sanguínea', 'Observación', 'Amarilla - 31', '2025-04-27 15:10:27', 32, '2025-04-27 15:35:00', '2025-04-27 15:20:52', '2025-04-27 15:40:21', '2025-04-27 15:41:30', '2025-04-27 15:55:53', NULL, '2025-04-27 15:42:05', '2025-04-27 16:00:04', NULL, '2025-04-27 16:10:12', '2025-04-27 16:45:45', NULL, '2025-04-27 16:46:22', NULL, NULL),

-- Paciente 33: Recién ingresado (triage 2) - abril 28
('María José Pinzón Ramírez', '53987456', '2', '2025-04-28 13:50:49', 'No realizado', '', '', '', '', 'Valoración CI', '', 'Amarilla - 29', '2025-04-28 13:45:27', 33, NULL, '2025-04-28 13:50:52', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),

-- Paciente 34: Alta rápida (triage 5) - abril 29
('Andrés Felipe Castillo Molina', '79123456', '5', '2025-04-29 10:05:49', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pasillos - 64', '2025-04-29 09:55:27', 34, NULL, '2025-04-29 10:05:52', '2025-04-29 10:55:21', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-29 11:00:22', '2025-04-29 11:15:57', '2025-04-29 11:20:57'),

-- Paciente 35: Hospitalización (triage 2) - abril 30
('Mariana Valentina Garzón Rojas', '1013789456', '2', '2025-04-30 17:10:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Antigua - 9', '2025-04-30 17:00:27', 35, NULL, '2025-04-30 17:10:52', '2025-04-30 17:35:21', '2025-04-30 17:36:30', '2025-04-30 17:50:53', '2025-04-30 19:30:53', '2025-04-30 17:37:05', '2025-04-30 17:55:04', '2025-04-30 19:15:46', '2025-04-30 18:10:12', '2025-04-30 18:50:45', '2025-04-30 19:45:16', '2025-04-30 19:46:22', '2025-04-30 20:15:57', NULL),

-- Paciente 36: Sala de espera recién asignado (triage 3) - mayo 1
('David Mauricio Sánchez Pérez', '1020897456', '3', '2025-05-01 09:30:49', 'No realizado', '', '', '', '', 'Valoración CI', '', 'Sala de espera - 3', '2025-05-01 09:20:27', 36, NULL, '2025-05-01 09:30:52', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),

-- Paciente 37: Atención en Clini (triage 4) - mayo 1
('Laura Daniela Barrera Cortés', '1023568974', '4', '2025-05-01 11:40:49', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Clini - 15', '2025-05-01 11:30:27', 37, NULL, '2025-05-01 11:40:52', '2025-05-01 12:05:21', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-05-01 12:15:22', '2025-05-01 12:35:57', '2025-05-01 12:40:57'),

-- Paciente 38: Urgencia pediátrica (triage 1) - mayo 1
('Santiago Andrés Moreno Quintero', '1028795463', '1', '2025-05-01 15:05:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'De Alta', 'Pediatría - 44', '2025-05-01 15:00:27', 38, NULL, '2025-05-01 15:05:52', '2025-05-01 15:15:21', '2025-05-01 15:16:30', '2025-05-01 15:30:53', '2025-05-01 16:20:53', '2025-05-01 15:17:05', '2025-05-01 15:35:04', '2025-05-01 16:15:46', '2025-05-01 15:45:12', '2025-05-01 16:05:45', '2025-05-01 16:40:16', '2025-05-01 16:41:22', '2025-05-01 17:00:57', '2025-05-01 17:10:57'),

-- Paciente 39: Observación con imágenes pendientes (triage 2) - mayo 2 
('Valeria Andrea Forero García', '1015987456', '2', '2025-05-02 06:40:49', 'Realizado', 'Resultados completos', 'En espera de resultados', 'No se ha abierto', 'No realizado', 'IMG pendientes: Tomografía Cerebral, Realizar RV', 'Observación', 'Amarilla - 27', '2025-05-02 06:35:27', 39, '2025-05-02 06:55:00', '2025-05-02 06:40:52', '2025-05-02 06:55:21', '2025-05-02 06:56:30', '2025-05-02 07:10:53', '2025-05-02 08:20:53', '2025-05-02 06:57:05', '2025-05-02 07:15:04', NULL, NULL, NULL, NULL, '2025-05-02 07:16:22', NULL, NULL),

-- Paciente 40: Triage 3 con todo pendiente - mayo 2
('Andrés Camilo Muñoz Rivera', '80965321', '3', '2025-05-02 07:05:49', 'Realizado', 'En espera de resultados', 'En espera de resultados', 'No se ha abierto', 'No realizado', 'Abrir Interconsulta, Realizar RV', 'Observación', 'Antigua - 14', '2025-05-02 07:00:27', 40, '2025-05-02 07:15:00', '2025-05-02 07:05:52', '2025-05-02 07:25:21', '2025-05-02 07:26:30', '2025-05-02 07:40:53', NULL, '2025-05-02 07:27:05', '2025-05-02 07:45:04', NULL, NULL, NULL, NULL, '2025-05-02 07:46:22', NULL, NULL);


-- Insertar métricas correspondientes a los 20 pacientes adicionales
INSERT INTO metricas_pacientes (
    paciente_id,
    fecha_calculo,
    tiempo_triage,
    clase_triage,
    tiempo_ci,
    tiempo_labs_solicitud,
    tiempo_labs_resultados,
    tiempo_labs_total,
    tiempo_ix_solicitud,
    tiempo_ix_resultados,
    tiempo_ix_total,
    tiempo_inter_apertura,
    tiempo_inter_realizacion,
    tiempo_inter_total,
    tiempo_rv,
    tiempo_total_atencion,
    area
)
VALUES
-- Métricas para Paciente 21 (triage 1)
(21, NOW(), 5, '1', 10, 1, 70, 71, 2, 51, 53, 30, 50, 80, 20, 156, 'Amarilla'),

-- Métricas para Paciente 22 (triage 4)
(22, NOW(), 10, '4', 30, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 10, 75, 'Pasillos'),

-- Métricas para Paciente 23 (triage 2)
(23, NOW(), 15, '2', 25, 1, 115, 116, 2, 106, 108, 45, 100, 145, 30, 260, 'Amarilla'),

-- Métricas para Paciente 24 (triage 3)
(24, NOW(), 10, '3', 30, 1, 80, 81, 2, NULL, NULL, 55, NULL, NULL, NULL, 96, 'Pediatría'),

-- Métricas para Paciente 25 (triage 5)
(25, NOW(), 10, '5', 80, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5, 110, 'Pasillos'),

-- Métricas para Paciente 26 (triage 2)
(26, NOW(), 10, '2', 25, 1, 130, 131, 2, 128, 130, 40, 130, 170, 30, 285, 'Antigua'),

-- Métricas para Paciente 27 (triage 1 NN)
(27, NOW(), 10, '1', 15, 1, 85, 86, 2, 88, 90, 30, 55, 85, 20, 165, 'Amarilla'),

-- Métricas para Paciente 28 (triage 3 Clini)
(28, NOW(), 10, '3', 25, 1, 50, 51, NULL, NULL, NULL, NULL, NULL, NULL, 25, 130, 'Clini'),

-- Métricas para Paciente 29 (triage 4)
(29, NOW(), 10, '4', 30, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 15, 65, 'Pasillos'),

-- Métricas para Paciente 30 (triage 1)
(30, NOW(), 5, '1', 10, 1, 75, 76, 2, 83, 85, 30, 55, 85, 25, 155, 'Amarilla'),

-- Métricas para Paciente 31 (triage 2 Pediatría)
(31, NOW(), 10, '2', 25, 1, 84, 85, 2, 70, 72, 35, 55, 90, 25, 190, 'Pediatría'),

-- Métricas para Paciente 32 (triage 3)
(32, NOW(), 10, '3', 20, 1, NULL, NULL, 2, NULL, NULL, 30, NULL, NULL, NULL, 96, 'Amarilla'),

-- Métricas para Paciente 33 (triage 2 recién ingresado)
(33, NOW(), 5, '2', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5, 'Amarilla'),

-- Métricas para Paciente 34 (triage 5)
(34, NOW(), 10, '5', 50, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 15, 85, 'Pasillos'),

-- Métricas para Paciente 35 (triage 2 hospitalización)
(35, NOW(), 10, '2', 25, 1, 100, 101, 2, 98, 100, 40, 55, 95, 30, 195, 'Antigua'),

-- Métricas para Paciente 36 (triage 3 en espera)
(36, NOW(), 10, '3', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 10, 'Sala de espera'),

-- Métricas para Paciente 37 (triage 4 Clini)
(37, NOW(), 10, '4', 25, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 20, 70, 'Clini'),

-- Métricas para Paciente 38 (triage 1 pediátrico)
(38, NOW(), 5, '1', 10, 1, 50, 51, 2, 41, 43, 20, 35, 55, 20, 130, 'Pediatría'),

-- Métricas para Paciente 39 (triage 2 imágenes pendientes)
(39, NOW(), 5, '2', 15, 1, 70, 71, 2, NULL, NULL, NULL, NULL, NULL, NULL, 105, 'Amarilla'),

-- Métricas para Paciente 40 (triage 3 pendientes)
(40, NOW(), 5, '3', 20, 1, NULL, NULL, 2, NULL, NULL, NULL, NULL, NULL, NULL, 46, 'Antigua');


INSERT INTO pacientes 
(nombre, documento, triage, triage_timestamp, ci, labs, ix, inter, rv, pendientes, conducta, ubicacion, ingreso, id, observacion_timestamp, ci_no_realizado_timestamp, ci_realizado_timestamp, labs_no_realizado_timestamp, labs_solicitados_timestamp, labs_completos_timestamp, ix_no_realizado_timestamp, ix_solicitados_timestamp, ix_completos_timestamp, inter_no_abierta_timestamp, inter_abierta_timestamp, inter_realizada_timestamp, rv_no_realizado_timestamp, rv_realizado_timestamp, alta_timestamp)
VALUES 
-- Paciente 41: Caso pediátrico complejo (triage 1) - marzo 25
('Mateo Alejandro Vargas Sánchez', '1025987634', '1', '2025-03-25 07:25:42', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Pediatría - 46', '2025-03-25 07:20:18', 41, NULL, '2025-03-25 07:25:45', '2025-03-25 07:32:21', '2025-03-25 07:33:30', '2025-03-25 07:45:53', '2025-03-25 09:15:53', '2025-03-25 07:34:05', '2025-03-25 07:50:04', '2025-03-25 09:05:46', '2025-03-25 08:05:12', '2025-03-25 08:35:45', '2025-03-25 09:40:16', '2025-03-25 09:41:22', '2025-03-25 10:10:57', NULL),

-- Paciente 42: Adulto mayor con comorbilidades (triage 2) - marzo 28
('Carmen Elena Rodríguez Linares', '21456987', '2', '2025-03-28 14:15:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Observación', 'Antigua - 11', '2025-03-28 14:05:27', 42, '2025-03-28 14:35:00', '2025-03-28 14:15:52', '2025-03-28 14:35:21', '2025-03-28 14:36:30', '2025-03-28 14:50:53', '2025-03-28 16:20:53', '2025-03-28 14:37:05', '2025-03-28 14:55:04', '2025-03-28 16:15:46', '2025-03-28 15:10:12', '2025-03-28 15:40:45', '2025-03-28 16:45:16', '2025-03-28 16:46:22', '2025-03-28 17:10:57', '2025-03-28 18:00:57'),

-- Paciente 43: Triage 4 en hora pico (lunes por la mañana) - abril 01
('Julián Esteban Rivera Morales', '1024523698', '4', '2025-04-01 08:45:49', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pasillos - 66', '2025-04-01 08:30:27', 43, NULL, '2025-04-01 08:45:52', '2025-04-01 09:45:21', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-01 09:50:22', '2025-04-01 10:05:57', '2025-04-01 10:10:57'),

-- Paciente 44: NN accidente de tránsito nocturno (triage 1) - abril 03
('NN - 2025-04-03 - 02:30:22', 'NN - 20250403023022', '1', '2025-04-03 02:35:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 23', '2025-04-03 02:30:22', 44, NULL, '2025-04-03 02:35:52', '2025-04-03 02:45:21', '2025-04-03 02:46:30', '2025-04-03 03:00:53', '2025-04-03 04:00:53', '2025-04-03 02:47:05', '2025-04-03 03:05:04', '2025-04-03 03:50:46', '2025-04-03 03:15:12', '2025-04-03 03:45:45', '2025-04-03 04:25:16', '2025-04-03 04:26:22', '2025-04-03 04:55:57', NULL),

-- Paciente 45: Triage 3 fin de semana (domingo) - abril 06
('Andrea Carolina Montoya Durán', '52364789', '3', '2025-04-06 16:10:49', 'Realizado', 'Resultados completos', 'En espera de resultados', 'No se ha abierto', 'No realizado', 'IMG pendientes: Ecografía Renal, Realizar RV', 'Observación', 'Amarilla - 33', '2025-04-06 16:00:27', 45, '2025-04-06 16:30:00', '2025-04-06 16:10:52', '2025-04-06 16:35:21', '2025-04-06 16:36:30', '2025-04-06 16:50:53', '2025-04-06 17:30:53', '2025-04-06 16:37:05', '2025-04-06 16:55:04', NULL, NULL, NULL, NULL, '2025-04-06 16:56:22', NULL, NULL),

-- Paciente 46: Caso pediátrico nocturno (triage 2) - abril 08
('Samuel Andrés Quintero López', '1028976543', '2', '2025-04-08 23:50:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'De Alta', 'Pediatría - 48', '2025-04-08 23:40:27', 46, NULL, '2025-04-08 23:50:52', '2025-04-09 00:10:21', '2025-04-09 00:11:30', '2025-04-09 00:25:53', '2025-04-09 01:40:53', '2025-04-09 00:12:05', '2025-04-09 00:30:04', '2025-04-09 01:30:46', '2025-04-09 00:45:12', '2025-04-09 01:15:45', '2025-04-09 02:00:16', '2025-04-09 02:01:22', '2025-04-09 02:20:57', '2025-04-09 02:30:57'),

-- Paciente 47: Caso de triage 5 (consulta externa derivada) - abril 09
('Rosa María Gutiérrez Peña', '41236789', '5', '2025-04-09 10:20:49', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pasillos - 69', '2025-04-09 10:10:27', 47, NULL, '2025-04-09 10:20:52', '2025-04-09 11:05:21', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-09 11:10:22', '2025-04-09 11:25:57', '2025-04-09 11:30:57'),

-- Paciente 48: Adulto mayor urgente (triage 1) - abril 11
('Carlos Alberto Mendoza Garzón', '19456321', '1', '2025-04-11 15:15:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Antigua - 6', '2025-04-11 15:10:27', 48, NULL, '2025-04-11 15:15:52', '2025-04-11 15:25:21', '2025-04-11 15:26:30', '2025-04-11 15:40:53', '2025-04-11 16:50:53', '2025-04-11 15:27:05', '2025-04-11 15:45:04', '2025-04-11 16:40:46', '2025-04-11 15:55:12', '2025-04-11 16:25:45', '2025-04-11 17:15:16', '2025-04-11 17:16:22', '2025-04-11 17:45:57', NULL),

-- Paciente 49: Caso clínico con interconsulta especializada (triage 2) - abril 13
('Diana Marcela Ochoa Granados', '1016789452', '2', '2025-04-13 11:30:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'De Alta', 'Clini - 13', '2025-04-13 11:20:27', 49, NULL, '2025-04-13 11:30:52', '2025-04-13 11:55:21', '2025-04-13 11:56:30', '2025-04-13 12:10:53', '2025-04-13 13:30:53', '2025-04-13 11:57:05', '2025-04-13 12:15:04', '2025-04-13 13:20:46', '2025-04-13 12:25:12', '2025-04-13 12:55:45', '2025-04-13 13:45:16', '2025-04-13 13:46:22', '2025-04-13 14:10:57', '2025-04-13 14:20:57'),

-- Paciente 50: Caso pediátrico simple (triage 3) - abril 16
('Valentina Sofía Ramírez Durán', '1027896543', '3', '2025-04-16 09:40:49', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pediatría - 41', '2025-04-16 09:30:27', 50, NULL, '2025-04-16 09:40:52', '2025-04-16 10:10:21', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-16 10:15:22', '2025-04-16 10:40:57', '2025-04-16 10:45:57'),

-- Paciente 51: Recién llegado en hora pico (triage pendiente) - abril 18
('Eduardo Andrés Pérez Martínez', '1019876543', '', NULL, 'No realizado', '', '', '', '', 'Pendiente Triage', '', 'Sala de espera - 5', '2025-04-18 17:55:27', 51, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),

-- Paciente 52: Caso de observación prolongada (triage 2) - abril 20
('María Fernanda Cubillos Rojas', '1015789632', '2', '2025-04-20 13:20:49', 'Realizado', 'Resultados completos', 'En espera de resultados', 'Abierta', 'No realizado', 'Respuesta Interconsulta, IMG pendientes: RMN Lumbar', 'Observación', 'Amarilla - 35', '2025-04-20 13:10:27', 52, '2025-04-20 13:40:00', '2025-04-20 13:20:52', '2025-04-20 13:45:21', '2025-04-20 13:46:30', '2025-04-20 14:00:53', '2025-04-20 15:30:53', '2025-04-20 13:47:05', '2025-04-20 14:05:04', NULL, '2025-04-20 14:20:12', '2025-04-20 14:50:45', NULL, '2025-04-20 14:51:22', NULL, NULL),

-- Paciente 53: Triage 3 en Antigua - abril 22
('Hernán Felipe Gómez Arias', '79563214', '3', '2025-04-22 18:50:49', 'Realizado', 'En espera de resultados', 'No se ha realizado', 'No se ha abierto', 'No realizado', 'Labs pendientes: Hemograma Completo, Realizar RV', 'Observación', 'Antigua - 13', '2025-04-22 18:40:27', 53, '2025-04-22 19:10:00', '2025-04-22 18:50:52', '2025-04-22 19:15:21', '2025-04-22 19:16:30', '2025-04-22 19:30:53', NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-22 19:31:22', NULL, NULL),

-- Paciente 54: Trauma menor (triage 4) - abril 24
('Carolina Andrea Castiblanco Díaz', '1023456789', '4', '2025-04-24 12:10:49', 'Realizado', 'No se ha realizado', 'Resultados completos', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Amarilla - 28', '2025-04-24 12:00:27', 54, NULL, '2025-04-24 12:10:52', '2025-04-24 12:35:21', '2025-04-24 12:36:30', NULL, NULL, '2025-04-24 12:37:05', '2025-04-24 12:45:04', '2025-04-24 13:30:46', NULL, NULL, NULL, '2025-04-24 13:31:22', '2025-04-24 13:50:57', '2025-04-24 13:55:57'),

-- Paciente 55: Emergencia madrugada (triage 1) - abril 26
('Jorge Esteban Castro Bermúdez', '80147852', '1', '2025-04-26 03:15:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 24', '2025-04-26 03:10:27', 55, NULL, '2025-04-26 03:15:52', '2025-04-26 03:22:21', '2025-04-26 03:23:30', '2025-04-26 03:35:53', '2025-04-26 04:45:53', '2025-04-26 03:24:05', '2025-04-26 03:40:04', '2025-04-26 04:35:46', '2025-04-26 03:50:12', '2025-04-26 04:20:45', '2025-04-26 05:10:16', '2025-04-26 05:11:22', '2025-04-26 05:35:57', NULL),

-- Paciente 56: Paciente frecuente (triage 5) - abril 28
('Luis Alberto Parra Jiménez', '79652314', '5', '2025-04-28 15:40:49', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pasillos - 68', '2025-04-28 15:30:27', 56, NULL, '2025-04-28 15:40:52', '2025-04-28 16:10:21', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-28 16:15:22', '2025-04-28 16:30:57', '2025-04-28 16:35:57'),

-- Paciente 57: Caso complejo con múltiples interconsultas (triage 2) - abril 30
('Claudia Patricia Rincón Morales', '52369874', '2', '2025-04-30 09:25:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Antigua - 4', '2025-04-30 09:15:27', 57, NULL, '2025-04-30 09:25:52', '2025-04-30 09:45:21', '2025-04-30 09:46:30', '2025-04-30 10:00:53', '2025-04-30 11:30:53', '2025-04-30 09:47:05', '2025-04-30 10:05:04', '2025-04-30 11:20:46', '2025-04-30 10:15:12', '2025-04-30 10:45:45', '2025-04-30 11:50:16', '2025-04-30 11:51:22', '2025-04-30 12:25:57', NULL),

-- Paciente 58: Sala de espera con asignación reciente (triage 3) - mayo 1
('Camila Andrea Rojas Casallas', '1016547896', '3', '2025-05-01 20:05:49', 'No realizado', '', '', '', '', 'Valoración CI', '', 'Sala de espera - 2', '2025-05-01 19:55:27', 58, NULL, '2025-05-01 20:05:52', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),

-- Paciente 59: Caso pediátrico nocturno (triage 2) - mayo 1
('Tomás Santiago León Gómez', '1028963214', '2', '2025-05-01 22:45:49', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'De Alta', 'Pediatría - 49', '2025-05-01 22:35:27', 59, NULL, '2025-05-01 22:45:52', '2025-05-01 23:10:21', '2025-05-01 23:11:30', '2025-05-01 23:25:53', '2025-05-02 00:45:53', '2025-05-01 23:12:05', '2025-05-01 23:30:04', '2025-05-02 00:35:46', '2025-05-01 23:45:12', '2025-05-02 00:15:45', '2025-05-02 01:05:16', '2025-05-02 01:06:22', '2025-05-02 01:25:57', '2025-05-02 01:30:57'),

-- Paciente 60: Paciente en clínica (triage 3) - mayo 2
('Daniel Felipe Ospina Torres', '1020347896', '3', '2025-05-02 09:05:49', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Clini - 16', '2025-05-02 08:55:27', 60, NULL, '2025-05-02 09:05:52', '2025-05-02 09:30:21', '2025-05-02 09:31:30', '2025-05-02 09:45:53', '2025-05-02 10:30:53', NULL, NULL, NULL, NULL, NULL, NULL, '2025-05-02 10:35:22', '2025-05-02 10:50:57', '2025-05-02 10:55:57');


-- Insertar métricas correspondientes a los 20 pacientes adicionales
INSERT INTO metricas_pacientes (
    paciente_id,
    fecha_calculo,
    tiempo_triage,
    clase_triage,
    tiempo_ci,
    tiempo_labs_solicitud,
    tiempo_labs_resultados,
    tiempo_labs_total,
    tiempo_ix_solicitud,
    tiempo_ix_resultados,
    tiempo_ix_total,
    tiempo_inter_apertura,
    tiempo_inter_realizacion,
    tiempo_inter_total,
    tiempo_rv,
    tiempo_total_atencion,
    area
)
VALUES
-- Métricas para Paciente 41 (triage 1 pediátrico)
(41, NOW(), 5, '1', 7, 1, 90, 91, 2, 91, 93, 32, 65, 97, 30, 170, 'Pediatría'),

-- Métricas para Paciente 42 (triage 2 adulto mayor)
(42, NOW(), 10, '2', 20, 1, 90, 91, 2, 100, 102, 35, 65, 100, 25, 235, 'Antigua'),

-- Métricas para Paciente 43 (triage 4 hora pico)
(43, NOW(), 15, '4', 60, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 15, 100, 'Pasillos'),

-- Métricas para Paciente 44 (triage 1 NN nocturno)
(44, NOW(), 5, '1', 10, 1, 60, 61, 2, 65, 67, 30, 40, 70, 30, 145, 'Amarilla'),

-- Métricas para Paciente 45 (triage 3 fin de semana)
(45, NOW(), 10, '3', 25, 1, 40, 41, 2, NULL, NULL, NULL, NULL, NULL, NULL, 96, 'Amarilla'),

-- Métricas para Paciente 46 (triage 2 pediátrico nocturno)
(46, NOW(), 10, '2', 20, 1, 75, 76, 2, 80, 82, 34, 45, 79, 20, 170, 'Pediatría'),

-- Métricas para Paciente 47 (triage 5 consulta externa)
(47, NOW(), 10, '5', 45, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 15, 80, 'Pasillos'),

-- Métricas para Paciente 48 (triage 1 adulto mayor)
(48, NOW(), 5, '1', 10, 1, 70, 71, 2, 73, 75, 30, 50, 80, 30, 155, 'Antigua'),

-- Métricas para Paciente 49 (triage 2 con interconsulta especializada)
(49, NOW(), 10, '2', 25, 1, 80, 81, 2, 85, 87, 30, 50, 80, 25, 180, 'Clini'),

-- Métricas para Paciente 50 (triage 3 pediátrico simple)
(50, NOW(), 10, '3', 30, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 25, 75, 'Pediatría'),

-- Métricas para Paciente 51 (recién llegado)
(51, NOW(), NULL, '', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'Sala de espera'),

-- Métricas para Paciente 52 (triage 2 observación prolongada)
(52, NOW(), 10, '2', 25, 1, 90, 91, 2, NULL, NULL, 35, NULL, NULL, NULL, 140, 'Amarilla'),

-- Métricas para Paciente 53 (triage 3 en Antigua)
(53, NOW(), 10, '3', 25, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 51, 'Antigua'),

-- Métricas para Paciente 54 (triage 4 trauma menor)
(54, NOW(), 10, '4', 25, NULL, NULL, NULL, 2, 53, 55, NULL, NULL, NULL, 20, 115, 'Amarilla'),

-- Métricas para Paciente 55 (triage 1 emergencia madrugada)
(55, NOW(), 5, '1', 7, 1, 70, 71, 2, 71, 73, 25, 50, 75, 25, 145, 'Amarilla'),

-- Métricas para Paciente 56 (triage 5 paciente frecuente)
(56, NOW(), 10, '5', 30, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 15, 65, 'Pasillos'),

-- Métricas para Paciente 57 (triage 2 caso complejo)
(57, NOW(), 10, '2', 20, 1, 90, 91, 2, 93, 95, 30, 65, 95, 35, 190, 'Antigua'),

-- Métricas para Paciente 58 (triage 3 en sala de espera)
(58, NOW(), 10, '3', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 10, 'Sala de espera'),

-- Métricas para Paciente 59 (triage 2 pediátrico nocturno)
(59, NOW(), 10, '2', 25, 1, 75, 76, 2, 65, 67, 30, 50, 80, 20, 175, 'Pediatría'),

-- Métricas para Paciente 60 (triage 3 en clínica)
(60, NOW(), 10, '3', 25, 1, 45, 46, NULL, NULL, NULL, NULL, NULL, NULL, 15, 120, 'Clini');

INSERT INTO pacientes 
(nombre, documento, triage, triage_timestamp, ci, labs, ix, inter, rv, pendientes, conducta, ubicacion, ingreso, id, observacion_timestamp, ci_no_realizado_timestamp, ci_realizado_timestamp, labs_no_realizado_timestamp, labs_solicitados_timestamp, labs_completos_timestamp, ix_no_realizado_timestamp, ix_solicitados_timestamp, ix_completos_timestamp, inter_no_abierta_timestamp, inter_abierta_timestamp, inter_realizada_timestamp, rv_no_realizado_timestamp, rv_realizado_timestamp, alta_timestamp)
VALUES 
-- Paciente 61: Adulto joven con trauma moderado (triage 2) - abril 8
('Juan Pablo Mejía Vargas', '1023456987', '2', '2025-04-08 10:15:22', 'Realizado', 'Resultados completos', 'Resultados completos', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Amarilla - 25', '2025-04-08 10:05:45', 61, NULL, '2025-04-08 10:15:30', '2025-04-08 10:35:18', '2025-04-08 10:36:12', '2025-04-08 10:40:35', '2025-04-08 11:30:22', '2025-04-08 10:37:05', '2025-04-08 10:45:40', '2025-04-08 11:25:12', NULL, NULL, NULL, '2025-04-08 11:35:44', '2025-04-08 11:50:33', '2025-04-08 12:05:17'),

-- Paciente 62: Adolescente con dolor abdominal (triage 3) - abril 9
('Valentina Ocampo Soto', '1032547896', '3', '2025-04-09 14:22:35', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pediatría - 43', '2025-04-09 14:10:20', 62, NULL, '2025-04-09 14:22:40', '2025-04-09 14:57:22', '2025-04-09 14:58:35', '2025-04-09 15:07:12', '2025-04-09 15:55:30', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-09 16:00:22', '2025-04-09 16:15:45', '2025-04-09 16:25:18'),

-- Paciente 63: Adulto mayor con disnea (triage 2) - abril 10
('Gerardo Antonio Medina López', '19432765', '2', '2025-04-10 08:35:42', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Antigua - 7', '2025-04-10 08:25:15', 63, '2025-04-10 09:00:20', '2025-04-10 08:35:45', '2025-04-10 08:55:12', '2025-04-10 08:56:20', '2025-04-10 09:02:35', '2025-04-10 10:10:45', '2025-04-10 08:57:10', '2025-04-10 09:12:22', '2025-04-10 10:05:18', '2025-04-10 09:20:35', '2025-04-10 09:50:12', '2025-04-10 10:35:25', '2025-04-10 10:36:30', '2025-04-10 11:05:22', NULL),

-- Paciente 64: Paciente con cefalea (triage 4) - abril 10
('Mariana Restrepo Duque', '1020345678', '4', '2025-04-10 16:40:33', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pasillos - 67', '2025-04-10 16:30:10', 64, NULL, '2025-04-10 16:40:38', '2025-04-10 17:22:15', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-10 17:27:35', '2025-04-10 17:45:22', '2025-04-10 17:50:18'),

-- Paciente 65: Niño con fiebre alta (triage 2) - abril 11
('Santiago López Martínez', '1028765432', '2', '2025-04-11 19:05:18', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pediatría - 45', '2025-04-11 18:55:22', 65, NULL, '2025-04-11 19:05:22', '2025-04-11 19:30:15', '2025-04-11 19:31:20', '2025-04-11 19:36:35', '2025-04-11 20:25:18', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-11 20:30:12', '2025-04-11 20:45:35', '2025-04-11 20:55:18'),

-- Paciente 66: Adulto con crisis asmática (triage 2) - abril 12
('Roberto Carlos Jiménez Díaz', '80123456', '2', '2025-04-12 13:10:42', 'Realizado', 'Resultados completos', 'Resultados completos', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Amarilla - 26', '2025-04-12 13:00:15', 66, NULL, '2025-04-12 13:10:48', '2025-04-12 13:35:22', '2025-04-12 13:36:30', '2025-04-12 13:42:12', '2025-04-12 14:35:18', '2025-04-12 13:37:25', '2025-04-12 13:50:32', '2025-04-12 14:30:15', NULL, NULL, NULL, '2025-04-12 14:40:22', '2025-04-12 14:55:35', '2025-04-12 15:05:18'),

-- Paciente 67: Paciente con dolor torácico (triage 1) - abril 13
('Laura Camila Torres Ortiz', '52876543', '1', '2025-04-13 07:05:12', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 20', '2025-04-13 07:00:18', 67, NULL, '2025-04-13 07:05:15', '2025-04-13 07:15:22', '2025-04-13 07:16:25', '2025-04-13 07:22:35', '2025-04-13 08:15:18', '2025-04-13 07:17:12', '2025-04-13 07:25:30', '2025-04-13 08:10:15', '2025-04-13 07:35:25', '2025-04-13 08:00:32', '2025-04-13 08:30:15', '2025-04-13 08:31:22', '2025-04-13 08:55:35', NULL),

-- Paciente 68: Anciano con deshidratación (triage 3) - abril 14
('José Manuel Garzón Pérez', '19876543', '3', '2025-04-14 11:35:45', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Antigua - 14', '2025-04-14 11:25:20', 68, NULL, '2025-04-14 11:35:50', '2025-04-14 12:10:22', '2025-04-14 12:11:30', '2025-04-14 12:20:15', '2025-04-14 13:15:35', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-14 13:20:22', '2025-04-14 13:40:15', '2025-04-14 13:50:35'),

-- Paciente 69: Paciente politraumatizado (triage 1) - abril 15
('Ricardo Andrés Sarmiento Vega', '1015678945', '1', '2025-04-15 23:40:18', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 21', '2025-04-15 23:35:22', 69, NULL, '2025-04-15 23:40:22', '2025-04-15 23:48:15', '2025-04-15 23:49:20', '2025-04-15 23:55:35', '2025-04-16 00:45:18', '2025-04-15 23:50:12', '2025-04-16 00:05:30', '2025-04-16 00:40:15', '2025-04-16 00:15:22', '2025-04-16 00:35:35', '2025-04-16 01:05:18', '2025-04-16 01:06:20', '2025-04-16 01:30:15', NULL),

-- Paciente 70: Niña con gastroenteritis (triage 3) - abril 16
('Isabella Sofía Ramírez Ortiz', '1027654321', '3', '2025-04-16 15:25:42', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pediatría - 42', '2025-04-16 15:15:15', 70, NULL, '2025-04-16 15:25:48', '2025-04-16 15:55:22', '2025-04-16 15:56:30', '2025-04-16 16:05:12', '2025-04-16 16:55:35', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-16 17:00:22', '2025-04-16 17:20:15', '2025-04-16 17:30:35'),

-- Paciente 71: Adulto con cólico renal (triage 2) - abril 17
('Fernando José Castillo Molina', '79543218', '2', '2025-04-17 20:10:33', 'Realizado', 'Resultados completos', 'Resultados completos', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Amarilla - 27', '2025-04-17 20:00:10', 71, NULL, '2025-04-17 20:10:38', '2025-04-17 20:35:15', '2025-04-17 20:36:22', '2025-04-17 20:42:35', '2025-04-17 21:30:18', '2025-04-17 20:37:10', '2025-04-17 20:50:25', '2025-04-17 21:25:12', NULL, NULL, NULL, '2025-04-17 21:35:30', '2025-04-17 21:55:22', '2025-04-17 22:05:15'),

-- Paciente 72: Paciente con intoxicación (triage 1) - abril 18
('Natalia Andrea Moreno Silva', '1018765432', '1', '2025-04-18 04:15:18', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 22', '2025-04-18 04:10:22', 72, NULL, '2025-04-18 04:15:22', '2025-04-18 04:25:15', '2025-04-18 04:26:20', '2025-04-18 04:32:35', '2025-04-18 05:20:18', '2025-04-18 04:27:12', '2025-04-18 04:40:30', '2025-04-18 05:15:15', '2025-04-18 04:50:22', '2025-04-18 05:10:35', '2025-04-18 05:40:18', '2025-04-18 05:41:20', '2025-04-18 06:05:15', NULL),

-- Paciente 73: Adulto con cuadro gripal complicado (triage 3) - abril 19
('Héctor Fabio González Ruiz', '79654321', '3', '2025-04-19 12:45:42', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Antigua - 15', '2025-04-19 12:35:15', 73, NULL, '2025-04-19 12:45:48', '2025-04-19 13:15:22', '2025-04-19 13:16:30', '2025-04-19 13:25:12', '2025-04-19 14:10:35', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-19 14:15:22', '2025-04-19 14:35:15', '2025-04-19 14:45:35'),

-- Paciente 74: Niño con fractura de brazo (triage 2) - abril 20
('Sebastián Alejandro Muñoz Giraldo', '1028901234', '2', '2025-04-20 18:20:33', 'Realizado', 'No se ha realizado', 'Resultados completos', 'Realizada', 'Realizado', '', 'De Alta', 'Pediatría - 47', '2025-04-20 18:10:10', 74, NULL, '2025-04-20 18:20:38', '2025-04-20 18:45:15', NULL, NULL, NULL, '2025-04-20 18:46:10', '2025-04-20 18:55:25', '2025-04-20 19:30:12', '2025-04-20 19:05:30', '2025-04-20 19:35:22', '2025-04-20 20:05:15', '2025-04-20 20:10:30', '2025-04-20 20:30:22', '2025-04-20 20:40:15'),

-- Paciente 75: Paciente con crisis hipertensiva (triage 2) - abril 21
('Gloria Patricia Duque Arango', '43218765', '2', '2025-04-21 09:55:18', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Antigua - 9', '2025-04-21 09:45:22', 75, NULL, '2025-04-21 09:55:22', '2025-04-21 10:20:15', '2025-04-21 10:21:20', '2025-04-21 10:30:35', '2025-04-21 11:15:18', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-21 11:20:22', '2025-04-21 11:40:15', '2025-04-21 11:50:35'),

-- Paciente 76: Adulto joven con apendicitis (triage 2) - abril 22
('Carlos Eduardo Patiño Gómez', '1019876543', '2', '2025-04-22 15:05:42', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 29', '2025-04-22 14:55:15', 76, NULL, '2025-04-22 15:05:48', '2025-04-22 15:30:22', '2025-04-22 15:31:30', '2025-04-22 15:40:12', '2025-04-22 16:25:35', '2025-04-22 15:32:10', '2025-04-22 15:45:25', '2025-04-22 16:20:12', '2025-04-22 15:55:30', '2025-04-22 16:15:22', '2025-04-22 16:45:15', '2025-04-22 16:46:30', '2025-04-22 17:10:22', NULL),

-- Paciente 77: Recién nacido con ictericia (triage 2) - abril 24
('NN - 2025-04-24', 'NN - 20250424083022', '2', '2025-04-24 08:40:33', 'Realizado', 'Resultados completos', 'No se ha realizado', 'Realizada', 'Realizado', '', 'Hospitalización', 'Pediatría - 44', '2025-04-24 08:30:10', 77, NULL, '2025-04-24 08:40:38', '2025-04-24 09:05:15', '2025-04-24 09:06:22', '2025-04-24 09:15:35', '2025-04-24 10:05:18', NULL, NULL, NULL, '2025-04-24 09:25:10', '2025-04-24 09:55:25', '2025-04-24 10:25:12', '2025-04-24 10:26:30', '2025-04-24 10:50:22', NULL),

-- Paciente 78: Adulto mayor con caída (triage 3) - abril 25
('Mercedes Cecilia Ordóñez Parra', '41567890', '3', '2025-04-25 17:15:18', 'Realizado', 'No se ha realizado', 'Resultados completos', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Antigua - 12', '2025-04-25 17:05:22', 78, NULL, '2025-04-25 17:15:22', '2025-04-25 17:45:15', NULL, NULL, NULL, '2025-04-25 17:46:12', '2025-04-25 17:55:30', '2025-04-25 18:35:15', NULL, NULL, NULL, '2025-04-25 18:40:20', '2025-04-25 19:00:15', '2025-04-25 19:10:35'),

-- Paciente 79: Paciente psiquiátrico (triage 2) - abril 27
('Andrés Felipe Londoño Mejía', '1017654321', '2', '2025-04-27 21:30:42', 'Realizado', 'Resultados completos', 'No se ha realizado', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 30', '2025-04-27 21:20:15', 79, NULL, '2025-04-27 21:30:48', '2025-04-27 21:55:22', '2025-04-27 21:56:30', '2025-04-27 22:05:12', '2025-04-27 22:55:35', NULL, NULL, NULL, '2025-04-27 22:15:10', '2025-04-27 22:45:25', '2025-04-27 23:15:12', '2025-04-27 23:16:30', '2025-04-27 23:40:22', NULL),

-- Paciente 80: Mujer embarazada con amenaza de aborto (triage 1) - abril 29
('Ana María Vélez Rodríguez', '1015432678', '1', '2025-04-29 05:20:33', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 19', '2025-04-29 05:15:10', 80, NULL, '2025-04-29 05:20:38', '2025-04-29 05:30:15', '2025-04-29 05:31:22', '2025-04-29 05:40:35', '2025-04-29 06:25:18', '2025-04-29 05:32:10', '2025-04-29 05:45:25', '2025-04-29 06:20:12', '2025-04-29 05:55:30', '2025-04-29 06:15:22', '2025-04-29 06:45:15', '2025-04-29 06:46:30', '2025-04-29 07:10:22', NULL);

-- Insertar métricas correspondientes a los 20 pacientes adicionales
INSERT INTO metricas_pacientes (
    paciente_id,
    fecha_calculo,
    tiempo_triage,
    clase_triage,
    tiempo_ci,
    tiempo_labs_solicitud,
    tiempo_labs_resultados,
    tiempo_labs_total,
    tiempo_ix_solicitud,
    tiempo_ix_resultados,
    tiempo_ix_total,
    tiempo_inter_apertura,
    tiempo_inter_realizacion,
    tiempo_inter_total,
    tiempo_rv,
    tiempo_total_atencion,
    area
)
VALUES
-- Métricas para Paciente 61 (triage 2 trauma moderado)
(61, NOW(), 10, '2', 20, 1, 50, 51, 2, 40, 42, NULL, NULL, NULL, 15, 120, 'Amarilla'),

-- Métricas para Paciente 62 (triage 3 adolescente)
(62, NOW(), 12, '3', 35, 1, 48, 49, NULL, NULL, NULL, NULL, NULL, NULL, 15, 135, 'Pediatría'),

-- Métricas para Paciente 63 (triage 2 adulto mayor con disnea)
(63, NOW(), 10, '2', 20, 1, 68, 69, 2, 66, 68, 25, 45, 70, 30, 160, 'Antigua'),

-- Métricas para Paciente 64 (triage 4 cefalea)
(64, NOW(), 10, '4', 42, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 18, 80, 'Pasillos'),

-- Métricas para Paciente 65 (triage 2 niño con fiebre)
(65, NOW(), 10, '2', 25, 1, 49, 50, NULL, NULL, NULL, NULL, NULL, NULL, 15, 120, 'Pediatría'),

-- Métricas para Paciente 66 (triage 2 crisis asmática)
(66, NOW(), 10, '2', 25, 1, 53, 54, 2, 40, 42, NULL, NULL, NULL, 15, 125, 'Amarilla'),

-- Métricas para Paciente 67 (triage 1 dolor torácico)
(67, NOW(), 5, '1', 10, 1, 53, 54, 2, 45, 47, 20, 30, 50, 24, 115, 'Amarilla'),

-- Métricas para Paciente 68 (triage 3 deshidratación)
(68, NOW(), 10, '3', 35, 1, 55, 56, NULL, NULL, NULL, NULL, NULL, NULL, 20, 145, 'Antigua'),

-- Métricas para Paciente 69 (triage 1 politraumatizado)
(69, NOW(), 5, '1', 8, 1, 50, 51, 2, 35, 37, 20, 30, 50, 24, 115, 'Amarilla'),

-- Métricas para Paciente 70 (triage 3 gastroenteritis)
(70, NOW(), 10, '3', 30, 1, 50, 51, NULL, NULL, NULL, NULL, NULL, NULL, 20, 135, 'Pediatría'),

-- Métricas para Paciente 71 (triage 2 cólico renal)
(71, NOW(), 10, '2', 25, 1, 48, 49, 2, 35, 37, NULL, NULL, NULL, 20, 125, 'Amarilla'),

-- Métricas para Paciente 72 (triage 1 intoxicación)
(72, NOW(), 5, '1', 10, 1, 48, 49, 2, 35, 37, 20, 30, 50, 24, 115, 'Amarilla'),

-- Métricas para Paciente 73 (triage 3 cuadro gripal)
(73, NOW(), 10, '3', 30, 1, 45, 46, NULL, NULL, NULL, NULL, NULL, NULL, 20, 130, 'Antigua'),

-- Métricas para Paciente 74 (triage 2 fractura)
(74, NOW(), 10, '2', 25, NULL, NULL, NULL, 2, 35, 37, 20, 30, 50, 20, 150, 'Pediatría'),

-- Métricas para Paciente 75 (triage 2 crisis hipertensiva)
(75, NOW(), 10, '2', 25, 1, 45, 46, NULL, NULL, NULL, NULL, NULL, NULL, 20, 125, 'Antigua'),

-- Métricas para Paciente 76 (triage 2 apendicitis)
(76, NOW(), 10, '2', 25, 1, 45, 46, 2, 35, 37, 25, 30, 55, 24, 135, 'Amarilla'),

-- Métricas para Paciente 77 (triage 2 recién nacido)
(77, NOW(), 10, '2', 25, 1, 50, 51, NULL, NULL, NULL, 20, 30, 50, 24, 140, 'Pediatría'),

-- Métricas para Paciente 78 (triage 3 caída adulto mayor)
(78, NOW(), 10, '3', 30, NULL, NULL, NULL, 2, 40, 42, NULL, NULL, NULL, 20, 125, 'Antigua'),

-- Métricas para Paciente 79 (triage 2 psiquiátrico)
(79, NOW(), 10, '2', 25, 1, 50, 51, NULL, NULL, NULL, 20, 30, 50, 24, 140, 'Amarilla'),

-- Métricas para Paciente 80 (triage 1 embarazada)
(80, NOW(), 5, '1', 10, 1, 45, 46, 2, 35, 37, 20, 30, 50, 24, 115, 'Amarilla');

INSERT INTO pacientes 
(nombre, documento, triage, triage_timestamp, ci, labs, ix, inter, rv, pendientes, conducta, ubicacion, ingreso, id, observacion_timestamp, ci_no_realizado_timestamp, ci_realizado_timestamp, labs_no_realizado_timestamp, labs_solicitados_timestamp, labs_completos_timestamp, ix_no_realizado_timestamp, ix_solicitados_timestamp, ix_completos_timestamp, inter_no_abierta_timestamp, inter_abierta_timestamp, inter_realizada_timestamp, rv_no_realizado_timestamp, rv_realizado_timestamp, alta_timestamp)
VALUES 
-- Paciente 81: Adolescente con crisis de asma severa (triage 2) - 15 abril
('Juliana Montoya Gómez', '1026789543', '2', '2025-04-15 08:37:22', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 24', '2025-04-15 08:25:13', 81, '2025-04-15 09:15:40', '2025-04-15 08:37:30', '2025-04-15 09:12:18', '2025-04-15 09:13:05', '2025-04-15 09:18:35', '2025-04-15 10:45:22', '2025-04-15 09:14:15', '2025-04-15 09:28:40', '2025-04-15 10:38:22', '2025-04-15 09:42:25', '2025-04-15 10:15:32', '2025-04-15 11:05:15', '2025-04-15 11:08:44', '2025-04-15 11:37:33', NULL),

-- Paciente 82: Adulto mayor con síncope (triage 2) - 17 abril
('Ernesto Gutiérrez Molina', '19287654', '2', '2025-04-17 14:43:35', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Antigua - 8', '2025-04-17 14:28:20', 82, '2025-04-17 15:25:30', '2025-04-17 14:43:40', '2025-04-17 15:22:12', '2025-04-17 15:23:10', '2025-04-17 15:33:35', '2025-04-17 17:20:45', '2025-04-17 15:24:20', '2025-04-17 15:45:22', '2025-04-17 17:05:38', '2025-04-17 16:20:35', '2025-04-17 17:10:12', '2025-04-17 18:15:25', '2025-04-17 18:18:30', '2025-04-17 19:05:22', NULL),

-- Paciente 83: Adulto con cuadro febril y petequias (triage 1) - 18 abril
('Miguel Ángel Zapata Henao', '1016789432', '1', '2025-04-18 22:08:12', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 18', '2025-04-18 22:03:45', 83, '2025-04-18 22:28:20', '2025-04-18 22:08:15', '2025-04-18 22:18:22', '2025-04-18 22:19:25', '2025-04-18 22:25:35', '2025-04-18 23:42:18', '2025-04-18 22:20:12', '2025-04-18 22:32:30', '2025-04-18 23:35:15', '2025-04-18 22:50:25', '2025-04-18 23:28:32', '2025-04-19 00:05:15', '2025-04-19 00:07:22', '2025-04-19 00:37:35', NULL),

-- Paciente 84: Mujer joven con migraña (triage 3) - 19 abril
('Carolina Restrepo Duque', '1020345971', '3', '2025-04-19 10:32:43', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pasillos - 65', '2025-04-19 10:15:10', 84, NULL, '2025-04-19 10:33:15', '2025-04-19 11:48:22', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-19 12:26:35', '2025-04-19 12:40:22', '2025-04-19 12:52:18'),

-- Paciente 85: Niño con trauma craneal leve (triage 2) - 20 abril
('Martín Alejandro Giraldo Ruiz', '1029876543', '2', '2025-04-20 15:25:18', 'Realizado', 'No se ha realizado', 'Resultados completos', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pediatría - 46', '2025-04-20 15:13:22', 85, NULL, '2025-04-20 15:25:22', '2025-04-20 16:05:15', NULL, NULL, NULL, '2025-04-20 16:06:12', '2025-04-20 16:18:30', '2025-04-20 17:25:15', NULL, NULL, NULL, '2025-04-20 17:32:20', '2025-04-20 17:55:15', '2025-04-20 18:07:35'),

-- Paciente 86: Adulto con celulitis (triage 3) - 21 abril
('Alejandro Valencia Torres', '80654321', '3', '2025-04-21 19:42:42', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Antigua - 16', '2025-04-21 19:25:15', 86, NULL, '2025-04-21 19:43:48', '2025-04-21 21:15:22', '2025-04-21 21:16:30', '2025-04-21 21:28:12', '2025-04-21 22:45:35', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-21 22:52:22', '2025-04-21 23:10:15', '2025-04-21 23:22:35'),

-- Paciente 87: Paciente accidente cerebrovascular (triage 1) - 22 abril
('Jorge Enrique Botero Agudelo', '71456789', '1', '2025-04-22 07:12:15', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 23', '2025-04-22 07:05:18', 87, NULL, '2025-04-22 07:12:22', '2025-04-22 07:22:15', '2025-04-22 07:23:20', '2025-04-22 07:28:35', '2025-04-22 08:42:18', '2025-04-22 07:24:12', '2025-04-22 07:35:30', '2025-04-22 08:35:15', '2025-04-22 07:45:22', '2025-04-22 08:25:35', '2025-04-22 09:20:18', '2025-04-22 09:22:20', '2025-04-22 09:52:15', NULL),

-- Paciente 88: Anciana con fractura de cadera (triage 2) - 23 abril
('María Teresa Jaramillo Ortiz', '41234567', '2', '2025-04-23 11:55:42', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Antigua - 10', '2025-04-23 11:40:15', 88, NULL, '2025-04-23 11:55:48', '2025-04-23 12:28:22', '2025-04-23 12:29:30', '2025-04-23 12:38:12', '2025-04-23 14:15:35', '2025-04-23 12:30:10', '2025-04-23 12:45:25', '2025-04-23 14:05:12', '2025-04-23 13:00:30', '2025-04-23 14:00:22', '2025-04-23 14:53:15', '2025-04-23 14:55:30', '2025-04-23 15:22:22', NULL),

-- Paciente 89: Niño con convulsión febril (triage 2) - 24 abril
('Samuel Andrés Pérez Gómez', '1028765123', '2', '2025-04-24 23:07:33', 'Realizado', 'Resultados completos', 'No se ha realizado', 'Realizada', 'Realizado', '', 'Hospitalización', 'Pediatría - 41', '2025-04-24 22:58:10', 89, NULL, '2025-04-24 23:07:38', '2025-04-24 23:38:15', '2025-04-24 23:39:22', '2025-04-24 23:46:35', '2025-04-25 00:35:18', NULL, NULL, NULL, '2025-04-24 23:58:10', '2025-04-25 00:25:25', '2025-04-25 01:05:12', '2025-04-25 01:07:30', '2025-04-25 01:32:22', NULL),

-- Paciente 90: Adulto con disnea y dolor torácico (triage 2) - 25 abril
('Roberto José Cardona Vélez', '98765432', '2', '2025-04-25 14:26:18', 'Realizado', 'Resultados completos', 'Resultados completos', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Amarilla - 28', '2025-04-25 14:15:22', 90, NULL, '2025-04-25 14:26:22', '2025-04-25 15:02:15', '2025-04-25 15:03:20', '2025-04-25 15:12:35', '2025-04-25 16:25:18', '2025-04-25 15:04:12', '2025-04-25 15:20:30', '2025-04-25 16:18:15', NULL, NULL, NULL, '2025-04-25 16:30:22', '2025-04-25 16:52:15', '2025-04-25 17:08:35'),

-- Paciente 91: Mujer embarazada 30 semanas con contracciones (triage 2) - 26 abril
('Daniela Serna Botero', '1021345687', '2', '2025-04-26 09:18:42', 'Realizado', 'Resultados completos', 'No se ha realizado', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 31', '2025-04-26 09:05:15', 91, NULL, '2025-04-26 09:18:48', '2025-04-26 09:52:22', '2025-04-26 09:53:30', '2025-04-26 10:04:12', '2025-04-26 11:15:35', NULL, NULL, NULL, '2025-04-26 10:16:10', '2025-04-26 10:58:25', '2025-04-26 11:32:12', '2025-04-26 11:34:30', '2025-04-26 12:05:22', NULL),

-- Paciente 92: Paciente con trauma abdominal cerrado (triage 1) - 27 abril
('David Santiago Mejía Álvarez', '1014567890', '1', '2025-04-27 03:37:33', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 17', '2025-04-27 03:30:10', 92, NULL, '2025-04-27 03:37:38', '2025-04-27 03:49:15', '2025-04-27 03:50:22', '2025-04-27 03:57:35', '2025-04-27 05:08:18', '2025-04-27 03:51:10', '2025-04-27 04:05:25', '2025-04-27 05:02:12', '2025-04-27 04:18:30', '2025-04-27 04:55:22', '2025-04-27 05:29:15', '2025-04-27 05:31:30', '2025-04-27 06:12:22', NULL),

-- Paciente 93: Adulto con cuerpo extraño en ojo (triage 3) - 28 abril
('Antonio José García Ramírez', '79321456', '3', '2025-04-28 18:53:18', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'Realizada', 'Realizado', '', 'De Alta', 'Pasillos - 68', '2025-04-28 18:40:22', 93, NULL, '2025-04-28 18:53:22', '2025-04-28 20:12:15', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-28 20:13:12', '2025-04-28 21:05:30', '2025-04-28 21:35:15', '2025-04-28 21:38:20', '2025-04-28 21:55:15', '2025-04-28 22:07:35'),

-- Paciente 94: Niña con bronquiolitis (triage 2) - 29 abril
('Sofía Valentina Castro Duque', '1026543789', '2', '2025-04-29 12:43:42', 'Realizado', 'Resultados completos', 'Resultados completos', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pediatría - 48', '2025-04-29 12:30:15', 94, NULL, '2025-04-29 12:43:48', '2025-04-29 13:18:22', '2025-04-29 13:19:30', '2025-04-29 13:27:12', '2025-04-29 14:45:35', '2025-04-29 13:20:10', '2025-04-29 13:37:25', '2025-04-29 14:38:12', NULL, NULL, NULL, '2025-04-29 14:52:30', '2025-04-29 15:15:22', '2025-04-29 15:28:15'),

-- Paciente 95: Adulto mayor con deshidratación severa (triage 2) - 29 abril
('Luis Alfonso Ríos Montoya', '19876234', '2', '2025-04-29 21:32:33', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'Hospitalización', 'Antigua - 11', '2025-04-29 21:20:10', 95, NULL, '2025-04-29 21:32:38', '2025-04-29 22:04:15', '2025-04-29 22:05:22', '2025-04-29 22:14:35', '2025-04-29 23:25:18', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-29 23:28:30', '2025-04-29 23:57:22', NULL),

-- Paciente 96: Paciente con crisis de ansiedad (triage 3) - 30 abril
('Paula Andrea Grisales López', '1015432198', '3', '2025-04-30 07:48:18', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'Realizada', 'Realizado', '', 'De Alta', 'Pasillos - 69', '2025-04-30 07:35:22', 96, NULL, '2025-04-30 07:48:22', '2025-04-30 09:15:15', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-30 09:16:12', '2025-04-30 10:05:30', '2025-04-30 10:40:15', '2025-04-30 10:42:20', '2025-04-30 11:07:15', '2025-04-30 11:18:35'),

-- Paciente 97: Adulto con quemadura en miembro superior (triage 2) - 30 abril
('Juan Esteban Ocampo Herrera', '1012543789', '2', '2025-04-30 16:37:42', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Amarilla - 32', '2025-04-30 16:22:15', 97, NULL, '2025-04-30 16:37:48', '2025-04-30 17:05:22', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-30 17:42:30', '2025-04-30 18:05:22', '2025-04-30 18:18:15'),

-- Paciente 98: Paciente con hemorragia digestiva baja (triage 1) - 1 mayo
('Catalina Ramírez Londoño', '43567892', '1', '2025-05-01 02:13:33', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 16', '2025-05-01 02:05:10', 98, NULL, '2025-05-01 02:13:38', '2025-05-01 02:24:15', '2025-05-01 02:25:22', '2025-05-01 02:32:35', '2025-05-01 03:48:18', '2025-05-01 02:26:10', '2025-05-01 02:38:25', '2025-05-01 03:40:12', '2025-05-01 02:52:30', '2025-05-01 03:35:22', '2025-05-01 04:12:15', '2025-05-01 04:14:30', '2025-05-01 04:45:22', NULL),

-- Paciente 99: Niño con crisis epiléptica (triage 1) - 1 mayo
('Matías Velásquez Cárdenas', '1029876234', '1', '2025-05-01 15:25:18', 'Realizado', 'Resultados completos', 'Resultados completos', 'No se ha abierto', 'Realizado', '', 'Hospitalización', 'Pediatría - 40', '2025-05-01 15:18:22', 99, NULL, '2025-05-01 15:25:22', '2025-05-01 15:36:15', '2025-05-01 15:37:20', '2025-05-01 15:44:35', '2025-05-01 16:42:18', '2025-05-01 15:38:12', '2025-05-01 15:52:30', '2025-05-01 16:35:15', NULL, NULL, NULL, '2025-05-01 16:47:22', '2025-05-01 17:15:15', NULL),

-- Paciente 100: Mujer con pielonefritis aguda (triage 2) - mayo 2
('Claudia Patricia Muñoz Salazar', '52345678', '2', '2025-05-02 09:54:42', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', 'Labs pendientes: Urocultivo', 'Observación', 'Antigua - 13', '2025-05-02 09:40:15', 100, '2025-05-02 10:25:30', '2025-05-02 09:54:48', '2025-05-02 10:22:22', '2025-05-02 10:24:30', '2025-05-02 10:35:12', '2025-05-02 11:45:35', NULL, NULL, NULL, NULL, NULL, NULL, '2025-05-02 11:50:30', '2025-05-02 12:10:22', NULL);

-- Insertar métricas correspondientes a los 20 pacientes adicionales
INSERT INTO metricas_pacientes (
    paciente_id,
    fecha_calculo,
    tiempo_triage,
    clase_triage,
    tiempo_ci,
    tiempo_labs_solicitud,
    tiempo_labs_resultados,
    tiempo_labs_total,
    tiempo_ix_solicitud,
    tiempo_ix_resultados,
    tiempo_ix_total,
    tiempo_inter_apertura,
    tiempo_inter_realizacion,
    tiempo_inter_total,
    tiempo_rv,
    tiempo_total_atencion,
    area
)
VALUES
-- Métricas para Paciente 81 (crisis de asma severa)
(81, NOW(), 12, '2', 35, 1, 87, 88, 2, 70, 72, 30, 50, 80, 29, 192, 'Amarilla'),

-- Métricas para Paciente 82 (síncope adulto mayor)
(82, NOW(), 15, '2', 39, 1, 107, 108, 2, 80, 82, 58, 65, 123, 47, 277, 'Antigua'),

-- Métricas para Paciente 83 (cuadro febril con petequias)
(83, NOW(), 4, '1', 10, 1, 77, 78, 2, 63, 65, 32, 37, 69, 30, 154, 'Amarilla'),

-- Métricas para Paciente 84 (migraña)
(84, NOW(), 18, '3', 75, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 14, 157, 'Pasillos'),

-- Métricas para Paciente 85 (trauma craneal leve)
(85, NOW(), 12, '2', 40, NULL, NULL, NULL, 2, 67, 69, NULL, NULL, NULL, 23, 174, 'Pediatría'),

-- Métricas para Paciente 86 (celulitis)
(86, NOW(), 18, '3', 92, 1, 77, 78, NULL, NULL, NULL, NULL, NULL, NULL, 18, 237, 'Antigua'),

-- Métricas para Paciente 87 (ACV)
(87, NOW(), 7, '1', 10, 1, 74, 75, 2, 70, 72, 23, 55, 78, 30, 167, 'Amarilla'),

-- Métricas para Paciente 88 (fractura de cadera)
(88, NOW(), 15, '2', 33, 1, 97, 98, 2, 80, 82, 22, 53, 75, 27, 222, 'Antigua'),

-- Métricas para Paciente 89 (convulsión febril)
(89, NOW(), 9, '2', 31, 1, 49, 50, NULL, NULL, NULL, 18, 67, 85, 25, 154, 'Pediatría'),

-- Métricas para Paciente 90 (disnea y dolor torácico)
(90, NOW(), 11, '2', 36, 1, 73, 74, 2, 74, 76, NULL, NULL, NULL, 22, 173, 'Amarilla'),

-- Métricas para Paciente 91 (embarazada con contracciones)
(91, NOW(), 14, '2', 34, 1, 71, 72, NULL, NULL, NULL, 22, 34, 56, 31, 180, 'Amarilla'),

-- Métricas para Paciente 92 (trauma abdominal cerrado)
(92, NOW(), 8, '1', 12, 1, 71, 72, 2, 71, 73, 21, 34, 55, 41, 162, 'Amarilla'),

-- Métricas para Paciente 93 (cuerpo extraño en ojo)
(93, NOW(), 13, '3', 79, NULL, NULL, NULL, NULL, NULL, NULL, 0, 82, 82, 17, 207, 'Pasillos'),

-- Métricas para Paciente 94 (bronquiolitis)
(94, NOW(), 14, '2', 35, 1, 78, 79, 2, 78, 80, NULL, NULL, NULL, 23, 178, 'Pediatría'),

-- Métricas para Paciente 95 (deshidratación severa)
(95, NOW(), 13, '2', 32, 1, 71, 72, NULL, NULL, NULL, NULL, NULL, NULL, 29, 157, 'Antigua'),

-- Métricas para Paciente 96 (crisis de ansiedad)
(96, NOW(), 13, '3', 87, NULL, NULL, NULL, NULL, NULL, NULL, 1, 84, 85, 25, 223, 'Pasillos'),

-- Métricas para Paciente 97 (quemadura)
(97, NOW(), 16, '2', 28, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 23, 116, 'Amarilla'),

-- Métricas para Paciente 98 (hemorragia digestiva)
(98, NOW(), 8, '1', 11, 1, 76, 77, 2, 62, 64, 19, 37, 56, 31, 160, 'Amarilla'),

-- Métricas para Paciente 99 (crisis epiléptica)
(99, NOW(), 7, '1', 11, 1, 65, 66, 2, 43, 45, NULL, NULL, NULL, 28, 117, 'Pediatría'),

-- Métricas para Paciente 100 (pielonefritis aguda)
(100, NOW(), 15, '2', 28, 2, 70, 72, NULL, NULL, NULL, NULL, NULL, NULL, 20, 151, 'Antigua');

INSERT INTO pacientes 
(nombre, documento, triage, triage_timestamp, ci, labs, ix, inter, rv, pendientes, conducta, ubicacion, ingreso, id, observacion_timestamp, ci_no_realizado_timestamp, ci_realizado_timestamp, labs_no_realizado_timestamp, labs_solicitados_timestamp, labs_completos_timestamp, ix_no_realizado_timestamp, ix_solicitados_timestamp, ix_completos_timestamp, inter_no_abierta_timestamp, inter_abierta_timestamp, inter_realizada_timestamp, rv_no_realizado_timestamp, rv_realizado_timestamp, alta_timestamp)
VALUES 
-- Paciente 101: Adulto mayor con neumonía (triage 2) - 10 abril
('Carlos Alberto Mejía Londoño', '19456782', '2', '2025-04-10 08:15:30', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Antigua - 14', '2025-04-10 08:02:18', 101, '2025-04-10 08:55:40', '2025-04-10 08:15:40', '2025-04-10 08:52:22', '2025-04-10 08:53:15', '2025-04-10 09:05:35', '2025-04-10 11:12:48', '2025-04-10 08:54:20', '2025-04-10 09:15:40', '2025-04-10 11:02:35', '2025-04-10 09:28:15', '2025-04-10 10:55:30', '2025-04-10 11:45:12', '2025-04-10 11:48:25', '2025-04-10 12:22:35', NULL),

-- Paciente 102: Joven con trauma de miembro inferior (triage 3) - 11 abril
('Santiago Restrepo Valencia', '1025876432', '3', '2025-04-11 14:32:25', 'Realizado', 'No se ha realizado', 'Resultados completos', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pasillos - 72', '2025-04-11 14:20:10', 102, NULL, '2025-04-11 14:32:30', '2025-04-11 16:05:15', NULL, NULL, NULL, '2025-04-11 16:06:20', '2025-04-11 16:25:35', '2025-04-11 17:45:48', NULL, NULL, NULL, '2025-04-11 17:48:25', '2025-04-11 18:15:30', '2025-04-11 18:28:45'),

-- Paciente 103: Niña con deshidratación moderada (triage 2) - 12 abril
('Valentina Gómez Suárez', '1030654987', '2', '2025-04-12 10:45:38', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'Observación', 'Pediatría - 45', '2025-04-12 10:35:22', 103, '2025-04-12 11:20:15', '2025-04-12 10:45:45', '2025-04-12 11:15:30', '2025-04-12 11:16:45', '2025-04-12 11:28:20', '2025-04-12 12:55:35', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-12 13:02:48', '2025-04-12 13:28:15', NULL),

-- Paciente 104: Adulto con dolor torácico (triage 1) - 13 abril
('Fernando Jaramillo Ospina', '71234567', '1', '2025-04-13 02:08:12', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 15', '2025-04-13 02:02:30', 104, '2025-04-13 02:30:25', '2025-04-13 02:08:20', '2025-04-13 02:25:15', '2025-04-13 02:26:22', '2025-04-13 02:32:40', '2025-04-13 03:35:15', '2025-04-13 02:27:30', '2025-04-13 02:42:45', '2025-04-13 03:28:30', '2025-04-13 02:55:22', '2025-04-13 03:22:15', '2025-04-13 03:52:48', '2025-04-13 03:55:25', '2025-04-13 04:20:35', NULL),

-- Paciente 105: Adulto mayor con accidente cerebrovascular (triage 1) - 13 abril
('Hernando Gutiérrez Duque', '8765432', '1', '2025-04-13 18:17:45', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 11', '2025-04-13 18:08:30', 105, '2025-04-13 18:40:22', '2025-04-13 18:17:50', '2025-04-13 18:32:48', '2025-04-13 18:33:55', '2025-04-13 18:42:15', '2025-04-13 19:55:30', '2025-04-13 18:34:40', '2025-04-13 18:48:22', '2025-04-13 19:45:15', '2025-04-13 19:05:35', '2025-04-13 19:42:48', '2025-04-13 20:22:25', '2025-04-13 20:25:30', '2025-04-13 20:58:45', NULL),

-- Paciente 106: Mujer embarazada con preeclampsia (triage 1) - 14 abril
('María Camila Ortiz Rendón', '1022345876', '1', '2025-04-14 11:28:35', 'Realizado', 'Resultados completos', 'No se ha realizado', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 19', '2025-04-14 11:22:48', 106, '2025-04-14 11:55:22', '2025-04-14 11:28:40', '2025-04-14 11:42:15', '2025-04-14 11:43:30', '2025-04-14 11:52:45', '2025-04-14 12:48:30', NULL, NULL, NULL, '2025-04-14 12:05:22', '2025-04-14 12:42:15', '2025-04-14 13:15:35', '2025-04-14 13:18:48', '2025-04-14 13:45:25', NULL),

-- Paciente 107: Adolescente con apendicitis (triage 2) - 15 abril
('Andrés Felipe Castro Ruiz', '1025789432', '2', '2025-04-15 21:35:48', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 26', '2025-04-15 21:25:22', 107, '2025-04-15 22:08:15', '2025-04-15 21:35:55', '2025-04-15 22:02:30', '2025-04-15 22:03:45', '2025-04-15 22:15:22', '2025-04-15 23:35:15', '2025-04-15 22:04:30', '2025-04-15 22:22:48', '2025-04-15 23:28:25', '2025-04-15 22:35:30', '2025-04-15 23:22:45', '2025-04-15 23:58:22', '2025-04-16 00:02:15', '2025-04-16 00:35:30', NULL),

-- Paciente 108: Adulto con cólico renal (triage 2) - 16 abril
('Pedro José Vargas Moreno', '79123456', '2', '2025-04-16 15:42:25', 'Realizado', 'Resultados completos', 'Resultados completos', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Antigua - 12', '2025-04-16 15:30:15', 108, NULL, '2025-04-16 15:42:30', '2025-04-16 16:15:48', '2025-04-16 16:16:55', '2025-04-16 16:28:22', '2025-04-16 17:45:15', '2025-04-16 16:17:30', '2025-04-16 16:32:45', '2025-04-16 17:38:30', NULL, NULL, NULL, '2025-04-16 17:50:22', '2025-04-16 18:12:15', '2025-04-16 18:28:35'),

-- Paciente 109: Adulto mayor con EPOC exacerbado (triage 2) - 17 abril
('José Antonio Ramírez Soto', '19345678', '2', '2025-04-17 05:25:30', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Antigua - 9', '2025-04-17 05:12:48', 109, '2025-04-17 06:02:22', '2025-04-17 05:25:35', '2025-04-17 05:55:15', '2025-04-17 05:56:30', '2025-04-17 06:08:45', '2025-04-17 07:32:30', '2025-04-17 05:57:22', '2025-04-17 06:15:15', '2025-04-17 07:22:35', '2025-04-17 06:28:48', '2025-04-17 07:12:25', '2025-04-17 07:48:30', '2025-04-17 07:52:45', '2025-04-17 08:25:22', NULL),

-- Paciente 110: Niño con intoxicación accidental (triage 1) - 18 abril
('Sebastián Martínez Giraldo', '1030245876', '1', '2025-04-18 09:08:15', 'Realizado', 'Resultados completos', 'No se ha realizado', 'Realizada', 'Realizado', '', 'Hospitalización', 'Pediatría - 42', '2025-04-18 09:02:30', 110, '2025-04-18 09:32:45', '2025-04-18 09:08:22', '2025-04-18 09:22:15', '2025-04-18 09:23:30', '2025-04-18 09:32:48', '2025-04-18 10:42:25', NULL, NULL, NULL, '2025-04-18 09:45:30', '2025-04-18 10:32:45', '2025-04-18 11:05:22', '2025-04-18 11:08:15', '2025-04-18 11:38:30', NULL),

-- Paciente 111: Mujer con migraña severa (triage 3) - 19 abril
('Ana María Velásquez Duque', '43123456', '3', '2025-04-19 20:35:48', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pasillos - 71', '2025-04-19 20:22:25', 111, NULL, '2025-04-19 20:35:55', '2025-04-19 21:58:30', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-19 22:38:48', '2025-04-19 23:02:15', '2025-04-19 23:15:35'),

-- Paciente 112: Adulto con fractura expuesta (triage 1) - 20 abril
('Leonardo Tobón Correa', '98234567', '1', '2025-04-20 03:45:22', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 14', '2025-04-20 03:38:15', 112, '2025-04-20 04:12:30', '2025-04-20 03:45:30', '2025-04-20 03:58:45', '2025-04-20 04:00:22', '2025-04-20 04:12:15', '2025-04-20 05:32:30', '2025-04-20 04:01:48', '2025-04-20 04:18:25', '2025-04-20 05:22:30', '2025-04-20 04:28:45', '2025-04-20 05:15:22', '2025-04-20 05:48:15', '2025-04-20 05:52:30', '2025-04-20 06:18:45', NULL),

-- Paciente 113: Anciana con infección urinaria complicada (triage 2) - 21 abril
('Carmen Rosa Sánchez Pérez', '41987654', '2', '2025-04-21 12:18:22', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', 'Labs pendientes: Urocultivo', 'Observación', 'Antigua - 15', '2025-04-21 12:05:15', 113, '2025-04-21 12:52:30', '2025-04-21 12:18:30', '2025-04-21 12:48:45', '2025-04-21 12:49:22', '2025-04-21 12:58:15', '2025-04-21 14:25:30', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-21 14:28:48', '2025-04-21 14:55:25', NULL),

-- Paciente 114: Adolescente con gastroenteritis aguda (triage 2) - 22 abril
('Laura Daniela Agudelo Ruiz', '1028765432', '2', '2025-04-22 17:32:30', 'Realizado', 'Resultados completos', 'No se ha realizado', 'No se ha abierto', 'Realizado', '', 'De Alta', 'Pediatría - 47', '2025-04-22 17:20:45', 114, NULL, '2025-04-22 17:32:35', '2025-04-22 18:05:48', '2025-04-22 18:06:55', '2025-04-22 18:18:22', '2025-04-22 19:32:15', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-22 19:38:30', '2025-04-22 20:05:45', '2025-04-22 20:18:22'),

-- Paciente 115: Adulto con infarto agudo (triage 1) - 23 abril
('Ricardo Alberto González López', '71345678', '1', '2025-04-23 04:12:15', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 12', '2025-04-23 04:05:30', 115, '2025-04-23 04:38:45', '2025-04-23 04:12:22', '2025-04-23 04:25:15', '2025-04-23 04:26:30', '2025-04-23 04:35:48', '2025-04-23 05:45:25', '2025-04-23 04:27:30', '2025-04-23 04:42:45', '2025-04-23 05:38:30', '2025-04-23 04:52:48', '2025-04-23 05:28:25', '2025-04-23 06:02:30', '2025-04-23 06:05:45', '2025-04-23 06:30:22', NULL),

-- Paciente 116: Niño con crisis asmática (triage 2) - 24 abril
('Juan Pablo Osorio Henao', '1028456789', '2', '2025-04-24 08:55:48', 'Realizado', 'No se ha realizado', 'No se ha realizado', 'Realizada', 'Realizado', '', 'Hospitalización', 'Pediatría - 43', '2025-04-24 08:42:25', 116, '2025-04-24 09:28:30', '2025-04-24 08:55:55', '2025-04-24 09:22:30', NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-24 09:35:48', '2025-04-24 10:12:25', '2025-04-24 10:45:30', '2025-04-24 10:48:45', '2025-04-24 11:15:22', NULL),

-- Paciente 117: Adulto con herida por arma cortopunzante (triage 1) - 25 abril
('Diego Alejandro Botero Salazar', '1015678923', '1', '2025-04-25 23:28:15', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 27', '2025-04-25 23:19:30', 117, '2025-04-25 23:52:45', '2025-04-25 23:28:22', '2025-04-25 23:42:15', '2025-04-25 23:43:30', '2025-04-25 23:52:48', '2025-04-26 00:58:25', '2025-04-25 23:44:30', '2025-04-25 23:58:45', '2025-04-26 00:48:30', '2025-04-26 00:12:48', '2025-04-26 00:42:25', '2025-04-26 01:15:30', '2025-04-26 01:18:45', '2025-04-26 01:45:22', NULL),

-- Paciente 118: Adulto mayor con fractura de cadera (triage 2) - 27 abril
('Roberto Carlos Vélez Cifuentes', '19876543', '2', '2025-04-27 16:42:15', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Antigua - 6', '2025-04-27 16:30:30', 118, '2025-04-27 17:15:45', '2025-04-27 16:42:22', '2025-04-27 17:12:15', '2025-04-27 17:13:30', '2025-04-27 17:25:48', '2025-04-27 18:42:25', '2025-04-27 17:14:30', '2025-04-27 17:32:45', '2025-04-27 18:32:30', '2025-04-27 17:48:48', '2025-04-27 18:25:25', '2025-04-27 18:58:30', '2025-04-27 19:02:45', '2025-04-27 19:28:22', NULL),

-- Paciente 119: Adolescente politraumatizado (triage 1) - 29 abril
('Andrés Santiago Marín Ospina', '1025897634', '1', '2025-04-29 05:08:15', 'Realizado', 'Resultados completos', 'Resultados completos', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 13', '2025-04-29 05:02:30', 119, '2025-04-29 05:32:45', '2025-04-29 05:08:22', '2025-04-29 05:20:15', '2025-04-29 05:21:30', '2025-04-29 05:28:48', '2025-04-29 06:35:25', '2025-04-29 05:22:30', '2025-04-29 05:35:45', '2025-04-29 06:28:30', '2025-04-29 05:42:48', '2025-04-29 06:18:25', '2025-04-29 06:48:30', '2025-04-29 06:52:45', '2025-04-29 07:18:22', NULL),

-- Paciente 120: Mujer embarazada con ruptura prematura de membranas (triage 1) - 30 abril
('Paula Alejandra Jaramillo Duque', '1022987654', '1', '2025-04-30 22:18:30', 'Realizado', 'Resultados completos', 'No se ha realizado', 'Realizada', 'Realizado', '', 'Hospitalización', 'Amarilla - 25', '2025-04-30 22:12:48', 120, '2025-04-30 22:42:25', '2025-04-30 22:18:35', '2025-04-30 22:32:30', '2025-04-30 22:33:45', '2025-04-30 22:42:22', '2025-04-30 23:38:15', NULL, NULL, NULL, '2025-04-30 22:52:30', '2025-04-30 23:28:45', '2025-04-30 23:58:22', '2025-05-01 00:02:15', '2025-05-01 00:25:30', NULL);

-- Insertar métricas correspondientes a los 20 pacientes adicionales
INSERT INTO metricas_pacientes (
    paciente_id,
    fecha_calculo,
    tiempo_triage,
    clase_triage,
    tiempo_ci,
    tiempo_labs_solicitud,
    tiempo_labs_resultados,
    tiempo_labs_total,
    tiempo_ix_solicitud,
    tiempo_ix_resultados,
    tiempo_ix_total,
    tiempo_inter_apertura,
    tiempo_inter_realizacion,
    tiempo_inter_total,
    tiempo_rv,
    tiempo_total_atencion,
    area
)
VALUES
-- Métricas para Paciente 101 (neumonía)
(101, NOW(), 13, '2', 37, 1, 127, 128, 1, 107, 108, 36, 50, 86, 34, 260, 'Antigua'),

-- Métricas para Paciente 102 (trauma miembro inferior)
(102, NOW(), 12, '3', 93, NULL, NULL, NULL, 1, 80, 81, NULL, NULL, NULL, 27, 248, 'Pasillos'),

-- Métricas para Paciente 103 (deshidratación moderada)
(103, NOW(), 10, '2', 30, 1, 87, 88, NULL, NULL, NULL, NULL, NULL, NULL, 26, 173, 'Pediatría'),

-- Métricas para Paciente 104 (dolor torácico)
(104, NOW(), 6, '1', 17, 1, 63, 64, 1, 46, 47, 30, 31, 61, 25, 138, 'Amarilla'),

-- Métricas para Paciente 105 (accidente cerebrovascular)
(105, NOW(), 9, '1', 15, 1, 73, 74, 1, 57, 58, 33, 40, 73, 33, 170, 'Amarilla'),

-- Métricas para Paciente 106 (preeclampsia)
(106, NOW(), 6, '1', 14, 1, 56, 57, NULL, NULL, NULL, 23, 33, 56, 27, 143, 'Amarilla'),

-- Métricas para Paciente 107 (apendicitis)
(107, NOW(), 11, '2', 27, 1, 80, 81, 1, 66, 67, 33, 36, 69, 33, 190, 'Amarilla'),

-- Métricas para Paciente 108 (cólico renal)
(108, NOW(), 12, '2', 33, 1, 77, 78, 1, 66, 67, NULL, NULL, NULL, 22, 178, 'Antigua'),

-- Métricas para Paciente 109 (EPOC exacerbado)
(109, NOW(), 13, '2', 30, 1, 84, 85, 1, 67, 68, 33, 36, 69, 33, 193, 'Antigua'),

-- Métricas para Paciente 110 (intoxicación accidental)
(110, NOW(), 6, '1', 14, 1, 69, 70, NULL, NULL, NULL, 23, 30, 53, 30, 156, 'Pediatría'),

-- Métricas para Paciente 111 (migraña severa)
(111, NOW(), 14, '3', 83, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 24, 173, 'Pasillos'),

-- Métricas para Paciente 112 (fractura expuesta)
(112, NOW(), 7, '1', 13, 2, 80, 82, 1, 64, 65, 28, 33, 61, 26, 160, 'Amarilla'),

-- Métricas para Paciente 113 (infección urinaria complicada)
(113, NOW(), 13, '2', 30, 1, 87, 88, NULL, NULL, NULL, NULL, NULL, NULL, 27, 170, 'Antigua'),

-- Métricas para Paciente 114 (gastroenteritis aguda)
(114, NOW(), 12, '2', 33, 1, 74, 75, NULL, NULL, NULL, NULL, NULL, NULL, 27, 178, 'Pediatría'),

-- Métricas para Paciente 115 (infarto agudo)
(115, NOW(), 7, '1', 13, 1, 70, 71, 1, 51, 52, 27, 34, 61, 25, 145, 'Amarilla'),

-- Métricas para Paciente 116 (crisis asmática)
(116, NOW(), 14, '2', 27, NULL, NULL, NULL, NULL, NULL, NULL, 13, 33, 46, 27, 153, 'Pediatría'),

-- Métricas para Paciente 117 (herida arma cortopunzante)
(117, NOW(), 9, '1', 14, 1, 65, 66, 1, 50, 51, 26, 33, 59, 27, 146, 'Amarilla'),

-- Métricas para Paciente 118 (fractura de cadera adulto mayor)
(118, NOW(), 12, '2', 30, 1, 77, 78, 1, 60, 61, 27, 33, 60, 26, 178, 'Antigua'),

-- Métricas para Paciente 119 (adolescente politraumatizado)
(119, NOW(), 6, '1', 12, 1, 67, 68, 1, 53, 54, 25, 30, 55, 26, 136, 'Amarilla'),

-- Métricas para Paciente 120 (ruptura prematura de membranas)
(120, NOW(), 6, '1', 14, 1, 56, 57, NULL, NULL, NULL, 20, 30, 50, 23, 133, 'Amarilla');


SET SQL_SAFE_UPDATES = 0;
DELETE FROM trazabilidad;
SET SQL_SAFE_UPDATES = 1