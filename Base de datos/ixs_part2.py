import pandas as pd
import pymysql

# Leer archivo Excel
df = pd.read_excel("labs_ix.xlsx")

# Conexión a MySQL
conexion = pymysql.connect(
    host="Mauricio",
    user="Urgencias_1",
    password="Josma@0409",
    database="sistema_visualizacion",
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

tabla = 'imagenes'

with conexion.cursor() as cursor:
    # Crear la tabla si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imagenes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo_ix VARCHAR(50) NOT NULL UNIQUE,
            nombre_ix VARCHAR(500) NOT NULL
        );
    """)

    # Insertar datos formateando nombres
    for _, row in df.iterrows():
        codigo = str(row[0]).strip()
        nombre = str(row[1]).strip().title()  # Capitaliza cada palabra
        try:
            cursor.execute(
                "INSERT IGNORE INTO imagenes (codigo_ix, nombre_ix) VALUES (%s, %s)",
                (codigo, nombre)
            )
        except Exception as e:
            print(f"❌ Error al insertar {codigo} - {nombre}: {e}")

    conexion.commit()

conexion.close()
print(f"✅ Datos insertados con capitalización correcta en la tabla `{tabla}`.")