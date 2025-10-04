import os
import sys
import PyInstaller.__main__
import shutil

# Obtener el directorio actual
ruta_base = os.path.dirname(os.path.abspath(__file__))

# Definir rutas
script_principal = os.path.join(ruta_base, 'Código_Principal.py')
carpeta_imagenes = os.path.join(ruta_base, 'Front_end', 'imagenes')
carpeta_estilos = os.path.join(ruta_base, 'Front_end', 'styles')
ruta_icono = os.path.join(carpeta_imagenes, 'logo.png')
archivo_config = os.path.join(ruta_base, 'config.ini')

# Verificar si existe la carpeta de imágenes
if not os.path.exists(carpeta_imagenes):
    os.makedirs(carpeta_imagenes, exist_ok=True)
    print(f"Carpeta de imágenes creada en: {carpeta_imagenes}")
    print("Por favor coloque su archivo logo.png en esta carpeta antes de compilar.")
    sys.exit(1)

# Verificar si existe el archivo de logo
if not os.path.exists(ruta_icono):
    print(f"Error: Archivo de logo no encontrado en {ruta_icono}")
    print("Por favor coloque su archivo logo.png en la carpeta de imágenes antes de compilar.")
    sys.exit(1)

print("Iniciando proceso de compilación con PyInstaller...")
print(f"Script principal: {script_principal}")
print(f"Carpeta de imágenes: {carpeta_imagenes}")
print(f"Carpeta de estilos: {carpeta_estilos}")
print(f"Ruta del icono: {ruta_icono}")
print(f"Archivo de configuración: {archivo_config}")

# Preparar argumentos de datos con separadores adecuados
separador = ";" if sys.platform.startswith("win") else ":"
argumentos_datos = [
    f'--add-data={carpeta_imagenes}{separador}Front_end/imagenes',
    f'--add-data={carpeta_estilos}{separador}Front_end/styles',
    f'--add-data={archivo_config}{separador}.'
]

# Argumentos para PyInstaller
argumentos_pyinstaller = [
    '--name=Sistema_Visualizacion',
    '--onefile',  # Crear un único archivo ejecutable
    '--windowed',  # Ejecutar sin ventana de consola
    f'--icon={ruta_icono}',
] + argumentos_datos + [
    '--hidden-import=pymysql',
    '--hidden-import=configparser',
    '--hidden-import=PIL',
    '--hidden-import=PIL.Image',
    '--hidden-import=PIL.ImageFilter',
    # Importaciones para funcionalidad web
    '--hidden-import=PyQt5.QtWebEngineWidgets',
    '--hidden-import=PyQt5.QtWebChannel',
    '--hidden-import=json',
    # Recolectar submódulos
    '--collect-submodules=PyQt5.QtWebEngineWidgets',
    '--collect-data=PyQt5.QtWebEngineWidgets',
    '--clean',  # Limpiar caché de PyInstaller
    script_principal
]

# Ejecutar PyInstaller
PyInstaller.__main__.run(argumentos_pyinstaller)

# Verificar resultado
directorio_salida = os.path.join(ruta_base, 'dist')
if os.path.exists(directorio_salida):
    print("Compilación completada.")
    print("Ejecutable disponible en la carpeta 'dist'.")
    print("Asegúrese que la funcionalidad web funcione probando el generador de reportes.")
else:
    print("La compilación puede haber encontrado un problema. Verifique los errores anteriores.")