from PyQt5.QtWidgets import (QPushButton, QLabel, QMessageBox, QDialog, 
                           QVBoxLayout, QHBoxLayout, QWidget, QLineEdit,
                           QFormLayout, QComboBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor
from Front_end.styles.styles import *

class StyledMessageBox(QMessageBox):
    """Clase para crear QMessageBox estilizados según el tipo de mensaje."""
    
    def __init__(self, parent=None, title="", text="", icon=QMessageBox.Information, style_type="info"):
        """
        Inicializa un QMessageBox estilizado.
        
        Args:
            parent: Widget padre
            title: Título del mensaje
            text: Texto del mensaje
            icon: Icono a mostrar (QMessageBox.Information, QMessageBox.Warning, etc.)
            style_type: Tipo de estilo ("info", "warning", "error", "confirmation")
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setText(text)
        self.setIcon(icon)
        
        # Aplicar estilo según el tipo
        if style_type in MESSAGE_STYLES:
            self.setStyleSheet(MESSAGE_STYLES[style_type])
        
        # Ajustar el fondo de los iconos
        for child in self.children():
            if isinstance(child, QLabel) and not child.text():
                # Este es probablemente el label que contiene el icono
                child.setStyleSheet("background-color: transparent;")
                
        # Eliminar bordes y hacer frameless
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

class StyledButton(QPushButton):
    """Botón estilizado con diferentes variantes."""
    
    def __init__(self, text, style_type="primary", custom_styles=None, parent=None, is_close=False):
        """
        Inicializa un botón estilizado.
        
        Args:
            text: Texto del botón
            style_type: Tipo de estilo ("primary", "danger", "warning", "window_control")
                        o diccionario con estilos personalizados
            custom_styles: Diccionario de estilos personalizados (opcional)
            parent: Widget padre
            is_close: Si es True y style_type="window_control", se aplicará estilo de botón de cierre
        """
        if isinstance(style_type, dict) and custom_styles is None:
            super().__init__(text, parent)
            custom_styles = style_type
            style_type = "custom"
        elif parent is None and isinstance(custom_styles, QWidget):
            super().__init__(text, custom_styles)
            parent = custom_styles
            custom_styles = None
        else:
            super().__init__(text, parent)
        
        # Apply the style based on the style_type
        if style_type == "window_control":
            self.setStyleSheet(BUTTON_STYLES["window_control"](is_close))
        elif style_type == "custom" and custom_styles:
            # For custom styles passed as a dictionary
            style_str = "QPushButton {"
            for key, value in custom_styles.items():
                style_str += f"{key}: {value};"
            style_str += "}"
            self.setStyleSheet(style_str)
        elif style_type in BUTTON_STYLES:
            self.setStyleSheet(BUTTON_STYLES[style_type])
        
        self.setCursor(Qt.PointingHandCursor)

class StyledDialog(QDialog):
    """Diálogo base estilizado para formularios."""
    
    def __init__(self, title="", width=600, parent=None):
        """
        Inicializa un diálogo estilizado.
        
        Args:
            title: Título del diálogo
            width: Ancho mínimo del diálogo
            parent: Widget padre
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumWidth(width)
        self.setStyleSheet(DIALOG_STYLE)
        
        # Layout principal con márgenes adecuados
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)
        
        # Eliminar bordes y hacer frameless
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
    
    def add_title(self, text):
        """Añade un título al diálogo."""
        title_label = QLabel(text)
        title_label.setStyleSheet(LABEL_STYLES["title"])
        self.layout.addWidget(title_label)
        return title_label
    
    def add_required_fields_indicator(self):
        """Añade un indicador de campos obligatorios."""
        indicator = QLabel("* Campos obligatorios")
        indicator.setStyleSheet(LABEL_STYLES["required_indicator"])
        self.layout.addWidget(indicator)
        return indicator
    
    def add_form(self):
        """Añade un formulario al diálogo."""
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: transparent;")
        form_layout = QFormLayout(form_widget)
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(20)
        
        self.layout.addWidget(form_widget)
        return form_layout
    
    def add_button_row(self, buttons):
        """
        Añade una fila de botones al diálogo.
        
        Args:
            buttons: Lista de tuplas (texto, callback, estilo)
        """
        self.button_layout = QHBoxLayout()
        
        for text, callback, style in buttons:
            button = StyledButton(text, style)
            button.clicked.connect(callback)
            self.button_layout.addWidget(button)
        
        self.layout.addSpacing(10)
        self.layout.addLayout(self.button_layout)
        return self.button_layout

class FormField:
    """Clase para crear campos de formulario estilizados."""
    
    @staticmethod
    def create_line_edit(label_text, is_required=False, readonly=False, initial_value=""):
        """
        Crea un campo de texto con etiqueta.
        
        Args:
            label_text: Texto de la etiqueta
            is_required: Si es un campo obligatorio
            readonly: Si es de solo lectura
            initial_value: Valor inicial
        
        Returns:
            tuple: (QLabel, QLineEdit)
        """
        label = QLabel(label_text + (" *" if is_required else ""))
        
        if is_required:
            label.setStyleSheet(LABEL_STYLES["required"])
        else:
            label.setStyleSheet(LABEL_STYLES["normal"])
            
        entry = QLineEdit()
        entry.setText(initial_value)
        
        if readonly:
            entry.setReadOnly(True)
            entry.setStyleSheet(LINE_EDIT_STYLES["readonly"])
        else:
            if is_required:
                entry.setStyleSheet(LINE_EDIT_STYLES["required"])
            else:
                entry.setStyleSheet(LINE_EDIT_STYLES["normal"])
                
        return label, entry
    
    @staticmethod
    def create_combo_box(label_text, options=None, is_required=False, initial_value=""):
        """
        Crea un campo de selección con etiqueta.
        
        Args:
            label_text: Texto de la etiqueta
            options: Lista de opciones
            is_required: Si es un campo obligatorio
            initial_value: Valor inicial seleccionado
            
        Returns:
            tuple: (QLabel, QComboBox)
        """
        label = QLabel(label_text + (" *" if is_required else ""))
        
        if is_required:
            label.setStyleSheet(LABEL_STYLES["required"])
        else:
            label.setStyleSheet(LABEL_STYLES["normal"])
            
        combo = QComboBox()
        
        if options:
            combo.addItems(options)
            
        if initial_value:
            combo.setCurrentText(str(initial_value))
            
        if is_required:
            combo.setStyleSheet(COMBO_BOX_STYLES["required"])
        else:
            combo.setStyleSheet(COMBO_BOX_STYLES["normal"])
            
        return label, combo

class EntradaContrasena(QWidget):
    """Widget personalizado para entrada de contraseñas con opción de mostrar/ocultar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background_transparent']};
                border-radius: {BORDER_RADIUS['large']};
                min-height: 40px;
            }}
        """)
        
        self.entrada_contrasena = QLineEdit()
        self.entrada_contrasena.setEchoMode(QLineEdit.Password)
        self.entrada_contrasena.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background-color: {COLORS['background_transparent']};
                padding: {PADDING['medium']};
                font-size: {FONT_SIZE['medium']};
            }}
        """)
        
        self.boton_mostrar = QPushButton("👁")
        self.boton_mostrar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['background_transparent']};
                border: none;
                font-size: 25px;
                padding: 0 5px;
                color: {COLORS['button_primary']};
            }}
            QPushButton:hover {{
                color: {COLORS['button_primary_hover']};
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: {BORDER_RADIUS['small']};
            }}
        """)
        self.boton_mostrar.setCursor(Qt.PointingHandCursor)
        
        layout.addWidget(self.entrada_contrasena)
        layout.addWidget(self.boton_mostrar)
        
        self.boton_mostrar.clicked.connect(self.mostrar_contra)
    
    def mostrar_contra(self):
        if self.entrada_contrasena.echoMode() == QLineEdit.Password:
            self.entrada_contrasena.setEchoMode(QLineEdit.Normal)
        else:
            self.entrada_contrasena.setEchoMode(QLineEdit.Password)
    
    def text(self):
        return self.entrada_contrasena.text()
    
    def clear(self):
        self.entrada_contrasena.clear()
    
    def setPlaceholderText(self, texto):
        self.entrada_contrasena.setPlaceholderText(texto)
    
    def setEchoMode(self, modo):
        self.entrada_contrasena.setEchoMode(modo)