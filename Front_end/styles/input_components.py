from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout, QLabel, QVBoxLayout
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
import os
import sys

from Front_end.styles.styles import COLORS, BORDER_RADIUS, PADDING, FONT_SIZE

class IconTextField(QWidget):
    """Campo de texto con icono a la izquierda."""
    
    def __init__(self, icon_path=None, placeholder="", parent=None, echo_mode=QLineEdit.Normal, readonly=False):
        super().__init__(parent)
        
        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)
        
        # Estilo para el widget contenedor
        self.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px;
                border: 1px solid {COLORS['border_light']};
            }}
            QWidget:focus-within {{
                border: 2px solid {COLORS['border_focus']};
            }}
        """)
        
        # Icono (opcional)
        if icon_path and os.path.exists(icon_path):
            self.icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.icon_label.setFixedSize(24, 24)
            self.icon_label.setStyleSheet(f"background-color: {COLORS['background_transparent']}; border: none;")
            layout.addWidget(self.icon_label)
        
        # Campo de entrada
        self.text_field = QLineEdit()
        self.text_field.setEchoMode(echo_mode)
        self.text_field.setReadOnly(readonly)
        self.text_field.setPlaceholderText(placeholder)
        self.text_field.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background-color: {COLORS['background_transparent']};
                font-size: {FONT_SIZE['medium']};
                padding: {PADDING['small']};
            }}
        """)
        layout.addWidget(self.text_field)
        layout.setStretch(1, 1)  # El campo de texto ocupa todo el espacio disponible
    
    def text(self):
        return self.text_field.text()
    
    def setText(self, text):
        self.text_field.setText(text)
    
    def clear(self):
        self.text_field.clear()
    
    def textChanged(self, callback):
        self.text_field.textChanged.connect(callback)


class PasswordField(IconTextField):
    """Campo de contraseña con icono y botón para mostrar/ocultar."""
    
    def __init__(self, icon_path=None, placeholder="", parent=None, readonly=False):
        super().__init__(icon_path, placeholder, parent, QLineEdit.Password, readonly)
        
        # Añadir botón para mostrar/ocultar contraseña
        self.is_visible = False
        
        # Ruta base para las imágenes
        if getattr(sys, 'frozen', False):
            self.ruta_base = sys._MEIPASS
        else:
            self.ruta_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        self.icon_show = os.path.join(ruta_imagenes, "ver.png")
        self.icon_hide = os.path.join(ruta_imagenes, "esconder.png")
        
        # Botón con icono
        self.toggle_button = QPushButton()
        self.toggle_button.setFixedSize(30, 30)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['background_transparent']};
                border: none;
                padding: 2px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: {BORDER_RADIUS['small']};
            }}
        """)
        
        # Establecer icono inicial (ocultar)
        self.update_button_icon()
        
        # Conectar señal
        self.toggle_button.clicked.connect(self.toggle_visibility)
        
        # Añadir al layout
        self.layout().addWidget(self.toggle_button)
    
    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.text_field.setEchoMode(QLineEdit.Normal if self.is_visible else QLineEdit.Password)
        self.update_button_icon()
    
    def update_button_icon(self):
        import sys
        icon_path = self.icon_show if not self.is_visible else self.icon_hide
        if os.path.exists(icon_path):
            self.toggle_button.setIcon(QIcon(icon_path))
            self.toggle_button.setIconSize(QSize(20, 20))


class RequirementList(QWidget):
    """Lista de requisitos con indicadores visuales de cumplimiento."""
    
    def __init__(self, requirements=None, parent=None):
        super().__init__(parent)
        
        # Layout principal vertical
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 0, 5, 0)
        self.layout.setSpacing(2)
        
        # Estilo de widget
        self.setStyleSheet(f"""
            background-color: {COLORS['background_transparent']};
            color: {COLORS['text_primary']};
            font-size: 11px;
        """)
        
        # Lista de requisitos
        self.requirements = []
        if requirements:
            for req in requirements:
                self.add_requirement(req)
    
    def add_requirement(self, text):
        # Crear un widget para el requisito
        req_widget = QWidget()
        req_layout = QHBoxLayout(req_widget)
        req_layout.setContentsMargins(0, 0, 0, 0)
        req_layout.setSpacing(5)
        
        # Indicador (círculo)
        indicator = QLabel("○")  # Círculo vacío
        indicator.setStyleSheet(f"""
            color: {COLORS['text_light']};
            font-size: 12px;
            background-color: {COLORS['background_transparent']};
            min-width: 15px;
        """)
        req_layout.addWidget(indicator)
        
        # Texto del requisito
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"""
            color: {COLORS['text_light']};
            background-color: {COLORS['background_transparent']};
        """)
        req_layout.addWidget(label)
        req_layout.setStretch(1, 1)  # El texto ocupa todo el espacio disponible
        
        self.layout.addWidget(req_widget)
        self.requirements.append((indicator, label, False))  # Falso = no cumple el requisito
    
    def update_requirement(self, index, fulfilled):
        if 0 <= index < len(self.requirements):
            indicator, label, current_state = self.requirements[index]
            
            if fulfilled != current_state:
                # Actualizar estado
                self.requirements[index] = (indicator, label, fulfilled)
                
                # Actualizar estilo
                if fulfilled:
                    indicator.setText("●")  # Círculo lleno
                    indicator.setStyleSheet(f"""
                        color: {COLORS['button_success']};
                        font-size: 12px;
                        background-color: {COLORS['background_transparent']};
                        min-width: 15px;
                    """)
                    label.setStyleSheet(f"""
                        color: {COLORS['button_success']};
                        background-color: {COLORS['background_transparent']};
                    """)
                else:
                    indicator.setText("○")  # Círculo vacío
                    indicator.setStyleSheet(f"""
                        color: {COLORS['text_light']};
                        font-size: 12px;
                        background-color: {COLORS['background_transparent']};
                        min-width: 15px;
                    """)
                    label.setStyleSheet(f"""
                        color: {COLORS['text_light']};
                        background-color: {COLORS['background_transparent']};
                    """)
