from PyQt5.QtWidgets import QDialog, QMessageBox, QPushButton, QFormLayout, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt
import configparser
import os
from Front_end.styles.styles import COLORS, BORDER_RADIUS
from Front_end.styles.components import StyledDialog, FormField

def mostrar_mensaje_error(parent, titulo, mensaje):
    """Muestra un mensaje de error estilizado"""
    from Front_end.styles.components import StyledMessageBox
    msg_box = StyledMessageBox(parent, titulo, mensaje, QMessageBox.Critical, "error")
    
    # Crear botón OK estilizado
    btn_ok = QPushButton("Aceptar")
    btn_ok.setCursor(Qt.PointingHandCursor)
    
    msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
    msg_box.setDefaultButton(btn_ok)
    
    return msg_box.exec_()

def mostrar_mensaje_advertencia(parent, titulo, mensaje):
    """Muestra un mensaje de advertencia estilizado"""
    from Front_end.styles.components import StyledMessageBox
    msg_box = StyledMessageBox(parent, titulo, mensaje, QMessageBox.Warning, "warning")
    
    # Crear botón OK estilizado
    btn_ok = QPushButton("Aceptar")
    btn_ok.setCursor(Qt.PointingHandCursor)
    
    msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
    msg_box.setDefaultButton(btn_ok)
    
    return msg_box.exec_()

def mostrar_mensaje_informacion(parent, titulo, mensaje):
    """Muestra un mensaje informativo estilizado"""
    from Front_end.styles.components import StyledMessageBox
    msg_box = StyledMessageBox(parent, titulo, mensaje, QMessageBox.Information, "info")
    
    # Crear botón OK estilizado
    btn_ok = QPushButton("Aceptar")
    btn_ok.setCursor(Qt.PointingHandCursor)
    
    msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
    msg_box.setDefaultButton(btn_ok)
    
    return msg_box.exec_()

class ConfigDialog(StyledDialog):
    """Diálogo reutilizable para configuración de conexión"""
    def __init__(self, parent=None):
        super().__init__("Configuración de Conexión", 450, parent)
        
        from Back_end.Manejo_DB import ModeloConfiguracion
        
        # Obtener la configuración actual
        self.config_path = ModeloConfiguracion.get_config_path()
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            self.config['DATABASE'] = {'host': 'localhost'}
        
        # Agregar título y descripción
        self.add_title("Configuración del Servidor")
        
        descripcion = QLabel("Modifique la dirección del servidor para la conexión a la base de datos.")
        descripcion.setWordWrap(True)
        descripcion.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: {COLORS['background_transparent']};")
        self.layout.addWidget(descripcion)
        self.layout.addSpacing(10)  # Espaciador
        
        # Crear un formulario
        form_layout = self.add_form()
        
        # Campo servidor
        label, self.entrada_servidor = FormField.create_line_edit(
            "Servidor:", 
            True, 
            False, 
            self.config.get('DATABASE', 'host', fallback='localhost')
        )
        form_layout.addRow(label, self.entrada_servidor)
        
        self.layout.addSpacing(10)  # Espaciador
        
        # Botones
        botones = [
            ("Guardar", self.guardar_configuracion, "primary"),
            ("Cancelar", self.reject, "danger")
        ]
        
        self.add_button_row(botones)
    
    def guardar_configuracion(self):
        nuevo_host = self.entrada_servidor.text().strip()
        
        if not nuevo_host:
            from Front_end.styles.dialog_components import mostrar_mensaje_advertencia
            mostrar_mensaje_advertencia(self, "Dato Inválido", "El servidor no puede estar vacío.")
            return
        
        # Guardar la configuración utilizando el modelo
        from Back_end.Manejo_DB import ModeloConfiguracion
        exito, mensaje = ModeloConfiguracion.guardar_configuracion(nuevo_host)
        
        if exito:
            from Front_end.styles.dialog_components import mostrar_mensaje_informacion
            mostrar_mensaje_informacion(self, "Configuración Guardada", 
                                   "La configuración se ha guardado correctamente.\n"
                                   "Los cambios serán aplicados la próxima vez que inicie sesión.")
            self.accept()
        else:
            from Front_end.styles.dialog_components import mostrar_mensaje_error
            mostrar_mensaje_error(self, "Error", f"No se pudo guardar la configuración: {mensaje}")