import os
import sys
import PyInstaller.__main__

# Project root
base_path = os.path.dirname(os.path.abspath(__file__))

# Paths
main_script = os.path.join(base_path, 'main.py')
images_folder = os.path.join(base_path, 'frontend', 'images')
styles_folder = os.path.join(base_path, 'frontend', 'styles')
icon_path = os.path.join(images_folder, 'logo.png')
config_file = os.path.join(base_path, 'config.ini')

if not os.path.exists(images_folder):
    os.makedirs(images_folder, exist_ok=True)
    print(f"Images folder created at: {images_folder}")
    print("Please place logo.png in this folder before building.")
    sys.exit(1)

if not os.path.exists(icon_path):
    print(f"Error: logo file not found at {icon_path}")
    print("Please place logo.png in the images folder before building.")
    sys.exit(1)

print("Starting the build process with PyInstaller...")
print(f"Main script: {main_script}")
print(f"Images folder: {images_folder}")
print(f"Styles folder: {styles_folder}")
print(f"Icon path: {icon_path}")
print(f"Configuration file: {config_file}")

separator = ";" if sys.platform.startswith("win") else ":"
data_arguments = [
    f'--add-data={images_folder}{separator}frontend/images',
    f'--add-data={styles_folder}{separator}frontend/styles',
    f'--add-data={config_file}{separator}.'
]

pyinstaller_arguments = [
    '--name=Urgentix',
    '--onefile',  # Build a single executable file
    '--windowed',  # Run without a console window
    f'--icon={icon_path}',
] + data_arguments + [
    '--hidden-import=pymysql',
    '--hidden-import=configparser',
    '--hidden-import=unidecode',
    '--hidden-import=PIL',
    '--hidden-import=PIL.Image',
    '--hidden-import=PIL.ImageFilter',
    # Web functionality
    '--hidden-import=PyQt5.QtWebEngineWidgets',
    '--hidden-import=PyQt5.QtWebChannel',
    '--hidden-import=json',
    # Collect submodules
    '--collect-submodules=PyQt5.QtWebEngineWidgets',
    '--collect-data=PyQt5.QtWebEngineWidgets',
    '--clean',  # Clear the PyInstaller cache
    main_script
]

PyInstaller.__main__.run(pyinstaller_arguments)

output_directory = os.path.join(base_path, 'dist')
if os.path.exists(output_directory):
    print("Build completed.")
    print("The executable is available in the 'dist' folder.")
    print("Verify the web functionality by testing the report generator.")
else:
    print("Build failed. Check the PyInstaller output above for errors.")
