from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QFormLayout, QWidget,
                           QProgressBar, QMessageBox, QSpacerItem, QSizePolicy, QDesktopWidget, QComboBox)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap
import re
import os
import sys

from Front_end.styles.styles import *
from Front_end.styles.components import StyledDialog, FormField, StyledButton
from Front_end.styles.custom_widgets import EntradaContrasena
from Front_end.styles.input_components import IconTextField, PasswordField, RequirementList

class PasswordStrengthWidget(QWidget):
    """Widget para mostrar la fortaleza de contraseña visualmente"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        
        # Barra de progreso para la fortaleza
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(200, 200, 200, 150);
                border-radius: 3px;
                padding: 0px;
            }
            
            QProgressBar::chunk {
                background-color: #CC0000;  /* Rojo por defecto */
                border-radius: 3px;
            }
        """)
        
        # Etiqueta para el mensaje de fortaleza
        self.label = QLabel("Fortaleza: Débil")
        self.label.setStyleSheet("""
            color: #CC0000;
            font-size: 13px;
            background-color: transparent;
        """)
        
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.label)
        
    def update_strength(self, password):
        """Actualiza la fortaleza de la contraseña"""
        if not password:
            strength = 0
            color = "#CC0000"  # Rojo
            text = "Fortaleza: Vacía"
        else:
            # Evaluar longitud (máx 30)
            length_score = min(30, len(password)) * 1.5
            
            # Evaluar complejidad
            has_lower = any(c.islower() for c in password)
            has_upper = any(c.isupper() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(not c.isalnum() for c in password)
            
            # Calcular puntuación
            complexity_score = sum([has_lower, has_upper, has_digit, has_special]) * 15
            strength = min(100, length_score + complexity_score)
            
            # Determinar color y texto
            if strength < 30:
                color = "#CC0000"  # Rojo
                text = "Fortaleza: Muy débil"
            elif strength < 50:
                color = "#FF8000"  # Naranja
                text = "Fortaleza: Débil"
            elif strength < 75:
                color = "#FFCC00"  # Amarillo
                text = "Fortaleza: Moderada"
            elif strength < 95:
                color = "#AACC00"  # Verde claro
                text = "Fortaleza: Fuerte"
            else:
                color = "#00CC00"  # Verde
                text = "Fortaleza: Muy fuerte"
                
        # Actualizar barra y etiqueta
        self.progress_bar.setValue(int(strength))
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(200, 200, 200, 150);
                border-radius: 3px;
                padding: 0px;
            }}
            
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        self.label.setText(text)
        self.label.setStyleSheet(f"color: {color}; font-size: 13px; background-color: transparent;")

class PasswordInputWithToggle(QWidget):
    """Campo de contraseña con botón para mostrar/ocultar"""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Campo de texto de contraseña
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)
        self.password_field.setPlaceholderText(placeholder)
        self.password_field.setMinimumHeight(45)  # Fijar altura mínima para consistencia
        self.password_field.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background-color: {COLORS['background_transparent']};
                padding: 5px 10px;
                font-size: 15px;
            }}
        """)
        layout.addWidget(self.password_field, 1)
        
        # Determinar ruta base para imágenes
        if getattr(sys, 'frozen', False):
            ruta_base = sys._MEIPASS
        else:
            ruta_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        ruta_imagenes = os.path.join(ruta_base, "Front_end", "imagenes")
        self.icon_show = os.path.join(ruta_imagenes, "ver.png")
        self.icon_hide = os.path.join(ruta_imagenes, "esconder.png")
        
        # Botón para mostrar/ocultar - ajustado para ser más similar al de login
        self.toggle_button = QPushButton()
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0px 5px; /* Reducir padding horizontal */
                margin: 0px 8px 0px 0px; /* Aumentar margen derecho para separación */
            }
            QPushButton:hover {
                background-color: rgba(200, 200, 200, 50);
                border-radius: 12px; /* Reducir radius para mejor apariencia */
            }
        """)
        # Ajustar tamaño para ser más similar al del login
        self.toggle_button.setFixedSize(30, 30)
        
        # Establecer icono inicial (mostrar)
        self.is_visible = False
        self.update_icon()
        
        # Añadir directamente al layout principal con alineación derecha
        layout.addWidget(self.toggle_button, 0, Qt.AlignRight | Qt.AlignVCenter)
        
        self.toggle_button.clicked.connect(self.toggle_visibility)
        
    def toggle_visibility(self):
        """Alterna entre mostrar y ocultar la contraseña"""
        self.is_visible = not self.is_visible
        self.password_field.setEchoMode(QLineEdit.Normal if self.is_visible else QLineEdit.Password)
        self.update_icon()
        
    def update_icon(self):
        """Actualiza el icono según el estado actual"""
        icon_path = self.icon_hide if self.is_visible else self.icon_show
        if os.path.exists(icon_path):
            self.toggle_button.setIcon(QIcon(icon_path))
            # Mantener tamaño de icono consistente con login
            self.toggle_button.setIconSize(QSize(20, 20))
            
    def text(self):
        """Devuelve el texto actual del campo"""
        return self.password_field.text()
        
    def clear(self):
        """Limpia el campo"""
        self.password_field.clear()
        
    def textChanged(self, callback):
        """Conecta una función al evento textChanged"""
        self.password_field.textChanged.connect(callback)
        
    def setPlaceholderText(self, text):
        """Establece el texto de placeholder"""
        self.password_field.setPlaceholderText(text)

class RegistroUsuarioDialog(StyledDialog):
    """Diálogo de registro de usuario con validación en tiempo real"""
    
    def __init__(self, parent=None):
        super().__init__("Registro de Usuario", 800, parent)  # Incremento el ancho inicial para acomodar el diseño horizontal
        
        # Determinar ruta base para imágenes
        if getattr(sys, 'frozen', False):
            self.ruta_base = sys._MEIPASS
        else:
            self.ruta_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Ruta para las imágenes
        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        
        # Rutas a iconos
        self.icono_usuario = os.path.join(ruta_imagenes, "doctor.png")
        self.icono_candado = os.path.join(ruta_imagenes, "candado.png")
        self.icono_agregar = os.path.join(ruta_imagenes, "agregar.png")
        self.icono_nombre = os.path.join(ruta_imagenes, "nombre_completo.png")
        self.icono_rol = os.path.join(ruta_imagenes, "roles.png")
        
        # Crear título personalizado con icono más grande
        titulo_container = QWidget()
        # Hacer fondo transparente del contenedor
        titulo_container.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        titulo_layout = QHBoxLayout(titulo_container)
        titulo_layout.setContentsMargins(0, 0, 0, 0)
        titulo_layout.setSpacing(12)
        
        # Agregar icono junto al título con tamaño aumentado
        icono_label = QLabel()
        icono_pixmap = QPixmap(self.icono_agregar).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icono_label.setPixmap(icono_pixmap)
        titulo_layout.addWidget(icono_label)
        
        # Texto del título con tamaño aumentado
        titulo_texto = QLabel("Crear Nuevo Usuario")
        titulo_texto.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLORS['text_primary']};")
        titulo_layout.addWidget(titulo_texto)
        
        # Alinear a la izquierda y añadir espacio expandible a la derecha
        titulo_layout.addStretch()
        self.layout.addWidget(titulo_container)
        
        # Descripción con estilo mejorado
        descripcion = QLabel("Complete la información para registrar un nuevo usuario en el sistema.")
        descripcion.setWordWrap(True)
        descripcion.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: {COLORS['background_transparent']}; font-size: 15px;")
        self.layout.addWidget(descripcion)
        self.layout.addSpacing(5)  # Espacio reducido después de la descripción
        
        # Contenedor principal con diseño horizontal
        center_container = QWidget()
        center_container.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        
        # Cambiar a un layout horizontal para el contenedor principal
        center_layout = QHBoxLayout(center_container)
        center_layout.setContentsMargins(20, 0, 20, 0)
        center_layout.setSpacing(20)  # Espacio entre columnas
        
        # Crear dos columnas para distribuir los campos
        left_column = QWidget()
        left_column.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(18)
        
        right_column = QWidget()
        right_column.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(18)
        
        # 1. Campo de usuario con icono alineado - en columna izquierda
        user_container = QWidget()
        user_layout = QHBoxLayout(user_container)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(10)
        
        # Contenedor para etiqueta y campo
        user_field_container = QWidget()
        user_field_layout = QVBoxLayout(user_field_container)
        user_field_layout.setContentsMargins(0, 0, 0, 0)
        user_field_layout.setSpacing(5)
        
        user_label = QLabel("Nombre de usuario:")
        user_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        user_field_layout.addWidget(user_label)
        
        # Crear un contenedor para alinear verticalmente el icono con el campo
        user_input_container = QWidget()
        user_input_layout = QHBoxLayout(user_input_container)
        user_input_layout.setContentsMargins(0, 0, 0, 0)
        user_input_layout.setSpacing(10)
        
        # Icono de usuario centrado verticalmente
        user_icon = QLabel()
        user_pixmap = QPixmap(self.icono_usuario).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        user_icon.setPixmap(user_pixmap)
        user_icon.setFixedSize(40, 40)
        user_icon.setAlignment(Qt.AlignCenter)
        user_input_layout.addWidget(user_icon)
        
        # Campo de entrada con tamaño de fuente aumentado y estilo consistente con login
        self.entrada_usuario = QLineEdit()
        self.entrada_usuario.setPlaceholderText("Ingrese nombre de usuario")
        self.entrada_usuario.setMinimumHeight(45)  # Altura consistente con los campos de contraseña
        self.entrada_usuario.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: #FCFCFC;
                color: {COLORS['text_primary']};
                font-size: 15px;
                min-height: 45px; /* Garantiza la misma altura que los campos de contraseña */
            }}
        """)
        user_input_layout.addWidget(self.entrada_usuario)
        
        # Aplicar estilo al contenedor para simular el campo con fondo - añadida altura mínima
        user_input_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px; /* Altura fija igual a los campos de contraseña */
            }}
        """)
        
        # Añadir el contenedor de entrada al layout del campo
        user_field_layout.addWidget(user_input_container)
        
        # Feedback para validación con tamaño aumentado
        self.feedback_usuario = QLabel("")
        self.feedback_usuario.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
        self.feedback_usuario.setVisible(False)
        user_field_layout.addWidget(self.feedback_usuario)
        
        # Añadir los requisitos de usuario con tamaño aumentado
        self.user_requirements = RequirementList(parent=self)
        self.user_requirements.setStyleSheet("font-size: 13px;")
        self.user_requirements.add_requirement("Entre 4 y 16 caracteres")
        self.user_requirements.add_requirement("Debe comenzar con una letra")
        self.user_requirements.add_requirement("Solo letras, números y guiones bajos")
        user_field_layout.addWidget(self.user_requirements)
        
        user_layout.addWidget(user_field_container)
        left_layout.addWidget(user_container)
        
        # 2. Campo de nombre completo con icono - en columna izquierda
        nombre_container = QWidget()
        nombre_layout = QHBoxLayout(nombre_container)
        nombre_layout.setContentsMargins(0, 0, 0, 0)
        nombre_layout.setSpacing(10)
        
        # Contenedor para etiqueta y campo
        nombre_field_container = QWidget()
        nombre_field_layout = QVBoxLayout(nombre_field_container)
        nombre_field_layout.setContentsMargins(0, 0, 0, 0)
        nombre_field_layout.setSpacing(5)
        
        nombre_label = QLabel("Nombre completo:")
        nombre_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        nombre_field_layout.addWidget(nombre_label)
        
        # Crear un contenedor para alinear verticalmente el icono con el campo
        nombre_input_container = QWidget()
        nombre_input_layout = QHBoxLayout(nombre_input_container)
        nombre_input_layout.setContentsMargins(0, 0, 0, 0)
        nombre_input_layout.setSpacing(10)
        
        # Añadir icono para el campo de nombre completo
        nombre_icon = QLabel()
        nombre_pixmap = QPixmap(self.icono_nombre).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        nombre_icon.setPixmap(nombre_pixmap)
        nombre_icon.setFixedSize(40, 40)
        nombre_icon.setAlignment(Qt.AlignCenter)
        nombre_input_layout.addWidget(nombre_icon)
        
        # Campo de entrada para nombre completo
        self.entrada_nombre = QLineEdit()
        self.entrada_nombre.setPlaceholderText("Ingrese nombre completo")
        self.entrada_nombre.setMinimumHeight(45)
        self.entrada_nombre.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: #FCFCFC;
                color: {COLORS['text_primary']};
                font-size: 15px;
                min-height: 45px;
            }}
        """)
        nombre_input_layout.addWidget(self.entrada_nombre)
        
        # Aplicar estilo al contenedor
        nombre_input_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px;
            }}
        """)
        
        # Añadir el contenedor de entrada al layout del campo
        nombre_field_layout.addWidget(nombre_input_container)
        
        # Espacio para feedback del nombre
        self.feedback_nombre = QLabel("")
        self.feedback_nombre.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
        self.feedback_nombre.setVisible(False)
        nombre_field_layout.addWidget(self.feedback_nombre)
        
        nombre_layout.addWidget(nombre_field_container)
        left_layout.addWidget(nombre_container)
        
        # 3. Campo de rol con icono - en columna izquierda
        rol_container = QWidget()
        rol_layout = QHBoxLayout(rol_container)
        rol_layout.setContentsMargins(0, 0, 0, 0)
        rol_layout.setSpacing(10)
        
        # Contenedor para etiqueta y campo
        rol_field_container = QWidget()
        rol_field_layout = QVBoxLayout(rol_field_container)
        rol_field_layout.setContentsMargins(0, 0, 0, 0)
        rol_field_layout.setSpacing(5)
        
        rol_label = QLabel("Rol de usuario:")
        rol_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        rol_field_layout.addWidget(rol_label)
        
        # Crear un contenedor para el combo de roles
        rol_input_container = QWidget()
        rol_input_layout = QHBoxLayout(rol_input_container)
        rol_input_layout.setContentsMargins(0, 0, 0, 0)
        rol_input_layout.setSpacing(10)
        
        # Añadir icono para el campo de rol
        rol_icon = QLabel()
        rol_pixmap = QPixmap(self.icono_rol).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        rol_icon.setPixmap(rol_pixmap)
        rol_icon.setFixedSize(40, 40)
        rol_icon.setAlignment(Qt.AlignCenter)
        rol_input_layout.addWidget(rol_icon)
        
        # Selector de roles
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["Visitante", "Médico", "Administrador"])
        self.combo_rol.setMinimumHeight(45)
        self.combo_rol.setStyleSheet(f"""
            QComboBox {{
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: #FCFCFC;
                color: {COLORS['text_primary']};
                font-size: 15px;
                min-height: 45px;
            }}
            QComboBox:hover {{
                background-color: {COLORS['background_readonly']};
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {COLORS['border_light']};
                selection-background-color: {COLORS['button_primary']};
                selection-color: white;
                background-color: white;
            }}
        """)
        rol_input_layout.addWidget(self.combo_rol)
        
        # Aplicar estilo al contenedor
        rol_input_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px;
            }}
        """)
        
        # Añadir el contenedor de entrada al layout del campo
        rol_field_layout.addWidget(rol_input_container)
        
        rol_layout.addWidget(rol_field_container)
        left_layout.addWidget(rol_container)
        
        # Añadir espacio expansible en la columna izquierda
        left_layout.addStretch()
        
        # 4. Campo de contraseña con icono - en columna derecha
        password_container = QWidget()
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(10)
        
        # Contenedor para etiqueta y campo
        password_field_container = QWidget()
        password_field_layout = QVBoxLayout(password_field_container)
        password_field_layout.setContentsMargins(0, 0, 0, 0)
        password_field_layout.setSpacing(5)
        
        password_label = QLabel("Contraseña:")
        password_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        password_field_layout.addWidget(password_label)
        
        # Crear un contenedor para alinear verticalmente el icono con el campo
        password_input_container = QWidget()
        password_input_layout = QHBoxLayout(password_input_container)
        password_input_layout.setContentsMargins(0, 0, 0, 0)
        password_input_layout.setSpacing(10)
        
        # Icono de candado centrado verticalmente
        password_icon = QLabel()
        password_pixmap = QPixmap(self.icono_candado).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        password_icon.setPixmap(password_pixmap)
        password_icon.setFixedSize(40, 40)
        password_icon.setAlignment(Qt.AlignCenter)
        password_input_layout.addWidget(password_icon)
        
        # Usar el nuevo componente de contraseña con toggle
        self.entrada_password_container = PasswordInputWithToggle("Ingrese contraseña")
        password_input_layout.addWidget(self.entrada_password_container)
        
        # Aplicar estilo al contenedor para simular el campo con fondo
        password_input_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px;
            }}
        """)
        
        # Añadir el contenedor de entrada al layout del campo
        password_field_layout.addWidget(password_input_container)
        
        # Widget de fortaleza
        self.strength_widget = PasswordStrengthWidget()
        password_field_layout.addWidget(self.strength_widget)
        
        # Requisitos de contraseña con tamaño aumentado
        self.password_requirements = RequirementList(parent=self)
        self.password_requirements.setStyleSheet("font-size: 13px;")
        self.password_requirements.add_requirement("Al menos 8 caracteres")
        self.password_requirements.add_requirement("Al menos una letra mayúscula")
        self.password_requirements.add_requirement("Al menos una letra minúscula")
        self.password_requirements.add_requirement("Al menos un número")
        self.password_requirements.add_requirement("Al menos un carácter especial")
        password_field_layout.addWidget(self.password_requirements)
        
        password_layout.addWidget(password_field_container)
        right_layout.addWidget(password_container)
        
        # 5. Campo de confirmación de contraseña - en columna derecha
        confirm_container = QWidget()
        confirm_layout = QHBoxLayout(confirm_container)
        confirm_layout.setContentsMargins(0, 0, 0, 0)
        confirm_layout.setSpacing(10)
        
        # Contenedor para etiqueta y campo
        confirm_field_container = QWidget()
        confirm_field_layout = QVBoxLayout(confirm_field_container)
        confirm_field_layout.setContentsMargins(0, 0, 0, 0)
        confirm_field_layout.setSpacing(5)
        
        confirm_label = QLabel("Confirmar contraseña:")
        confirm_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        confirm_field_layout.addWidget(confirm_label)
        
        # Crear un contenedor para alinear verticalmente el icono con el campo
        confirm_input_container = QWidget()
        confirm_input_layout = QHBoxLayout(confirm_input_container)
        confirm_input_layout.setContentsMargins(0, 0, 0, 0)
        confirm_input_layout.setSpacing(10)
        
        # Icono de candado centrado verticalmente
        confirm_icon = QLabel()
        confirm_pixmap = QPixmap(self.icono_candado).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        confirm_icon.setPixmap(confirm_pixmap)
        confirm_icon.setFixedSize(40, 40)
        confirm_icon.setAlignment(Qt.AlignCenter)
        confirm_input_layout.addWidget(confirm_icon)
        
        # Usar el nuevo componente de contraseña con toggle para confirmación
        self.entrada_confirm_container = PasswordInputWithToggle("Confirme contraseña")
        confirm_input_layout.addWidget(self.entrada_confirm_container)
        
        # Aplicar estilo al contenedor para simular el campo con fondo
        confirm_input_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px;
            }}
        """)
        
        # Añadir el contenedor de entrada al layout del campo
        confirm_field_layout.addWidget(confirm_input_container)
        
        # Feedback para coincidencia con tamaño aumentado
        self.feedback_password = QLabel("")
        self.feedback_password.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
        self.feedback_password.setVisible(False)
        confirm_field_layout.addWidget(self.feedback_password)
        
        confirm_layout.addWidget(confirm_field_container)
        right_layout.addWidget(confirm_container)
        
        # Añadir espacio expansible en la columna derecha
        right_layout.addStretch()
        
        # Añadir las columnas al contenedor principal
        center_layout.addWidget(left_column)
        center_layout.addWidget(right_column)
        
        # Añadir contenedor principal al layout del diálogo
        self.layout.addWidget(center_container, 1)
        
        # Botones de acción con estilo mejorado
        botones = [
            ("Registrar", self.registrar_usuario, "primary"),
            ("Cancelar", self.reject, "danger")
        ]
        
        botones_layout = self.add_button_row(botones)
        
        # Aumentar tamaño de los botones
        for i in range(botones_layout.count()):
            widget = botones_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setMinimumHeight(45)
                widget.setStyleSheet(widget.styleSheet() + f"font-size: 16px;")
        
        # Añadir temporizador para verificar usuario existente con debounce
        self.username_check_timer = QTimer(self)
        self.username_check_timer.setSingleShot(True)  # Solo dispara una vez
        self.username_check_timer.setInterval(600)     # 600ms de espera
        self.username_check_timer.timeout.connect(self.verificar_usuario_remoto)
        
        # Conectar eventos para validación en tiempo real
        self.entrada_usuario.textChanged.connect(self.iniciar_verificacion_usuario)
        self.entrada_password_container.textChanged(self.actualizar_fortaleza)
        self.entrada_confirm_container.textChanged(self.validar_coincidencia)
        
        # Estilo general del diálogo
        self.setStyleSheet(f"""
            {self.styleSheet()}
            QDialog {{
                background-color: {COLORS['background_primary']};
            }}
        """)
        
        # Centrar el diálogo en la pantalla
        self.centerDialog()
        
        # Ajuste responsivo del tamaño final
        self.adjustSize()
    
    def centerDialog(self):
        """Centra el diálogo en la pantalla del usuario, ajustando para la porción azul oscuro"""
        screen = QDesktopWidget().screenGeometry()
        # Esperar a que se calcule el tamaño del diálogo
        self.adjustSize()
        size = self.geometry()
        
        # Obtener dimensiones de la pantalla para cálculos responsivos
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Centrar horizontalmente
        x = (screen_width - size.width()) // 2
        
        # Centrar verticalmente en el área de contenido, pero más abajo
        content_height = int(screen_height * 0.85)
        content_top = (screen_height - content_height) // 2
        
        # Añadir offset vertical (2% de la altura de pantalla) para bajar el diálogo
        y_offset = int(screen_height * 0.02)
        y = content_top + (content_height - size.height()) // 2 + y_offset
        
        # Asegurarse que el diálogo esté siempre visible en la pantalla
        # y no se salga por la parte inferior
        if y < 10:
            y = 10  # Margen superior mínimo
        if y + size.height() > screen_height - 10:
            y = screen_height - size.height() - 10  # Margen inferior mínimo
        
        self.move(x, y)
        
    def iniciar_verificacion_usuario(self):
        """Inicia el temporizador para verificar si el usuario existe remotamente"""
        # Reset y validar localmente
        self.validar_usuario_local()
        # Reinicia el temporizador cada vez que el texto cambia
        self.username_check_timer.start()
    
    def validar_usuario_local(self):
        """Realiza solo validaciones locales del nombre de usuario"""
        username = self.entrada_usuario.text()
        
        # Actualizar indicadores de requisitos
        self.user_requirements.update_requirement(0, 4 <= len(username) <= 16)
        self.user_requirements.update_requirement(1, username and username[0].isalpha())
        self.user_requirements.update_requirement(2, username and all(c.isalnum() or c == '_' for c in username))
        
        # Validar usuario completo
        if not username:
            self.feedback_usuario.setText("El nombre de usuario es obligatorio")
            self.feedback_usuario.setVisible(True)
            return False
            
        if len(username) < 4:
            self.feedback_usuario.setText("El nombre debe tener al menos 4 caracteres")
            self.feedback_usuario.setVisible(True)
            return False
            
        if len(username) > 16:
            self.feedback_usuario.setText("El nombre no debe exceder 16 caracteres")
            self.feedback_usuario.setVisible(True)
            return False
            
        if not username[0].isalpha():
            self.feedback_usuario.setText("El nombre debe comenzar con una letra")
            self.feedback_usuario.setVisible(True)
            return False
            
        if not all(c.isalnum() or c == '_' for c in username):
            self.feedback_usuario.setText("Use solo letras, números y guiones bajos")
            self.feedback_usuario.setVisible(True)
            return False
        
        # Validación local pasada
        self.feedback_usuario.setVisible(False)
        return True
    
    def verificar_usuario_remoto(self):
        """Verifica en la base de datos si el nombre de usuario ya existe"""
        username = self.entrada_usuario.text()
        
        # Skip check if username doesn't pass local validation
        if not self.validar_usuario_local():
            return
        try:
            # Import here to avoid circular imports
            from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
            
            if ModeloUsuarios.verificar_usuario_existe(username):
                self.feedback_usuario.setText("Este nombre de usuario ya existe")
                self.feedback_usuario.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
                self.feedback_usuario.setVisible(True)
                # Actualizar el primer requisito para mostrar que no está disponible
                self.user_requirements.update_requirement(0, False)
            else:
                # Si el usuario no existe, cambiar el mensaje a disponible
                self.feedback_usuario.setText("Nombre de usuario disponible")
                self.feedback_usuario.setStyleSheet(f"color: {COLORS['button_success']}; font-size: 13px;")
                self.feedback_usuario.setVisible(True)
                # Actualizar el primer requisito para mostrar que está disponible
                self.user_requirements.update_requirement(0, True)
        except Exception as e:
            print(f"Error verificando usuario remoto: {str(e)}")
    
    def validar_usuario_tiempo_real(self):
        """Valida el nombre de usuario en tiempo real y actualiza los requisitos"""
        # Validación local primero
        if not self.validar_usuario_local():
            return False
            
        # Verificar si el usuario ya existe
        try:
            from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
            
            username = self.entrada_usuario.text()
            if ModeloUsuarios.verificar_usuario_existe(username):
                self.feedback_usuario.setText("Este nombre de usuario ya existe")
                self.feedback_usuario.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
                self.feedback_usuario.setVisible(True)
                return False
        except Exception as e:
            print(f"Error verificando usuario: {str(e)}")
        
        # Todo bien, ocultar feedback
        self.feedback_usuario.setVisible(False)
        return True
        
    def actualizar_fortaleza(self):
        """Actualiza la fortaleza de contraseña y los requisitos"""
        password = self.entrada_password_container.text()
        self.strength_widget.update_strength(password)
        
        # Actualizar indicadores de requisitos
        self.password_requirements.update_requirement(0, len(password) >= 8)
        self.password_requirements.update_requirement(1, any(c.isupper() for c in password))
        self.password_requirements.update_requirement(2, any(c.islower() for c in password))
        self.password_requirements.update_requirement(3, any(c.isdigit() for c in password))
        self.password_requirements.update_requirement(4, any(not c.isalnum() for c in password))
        
        # Si hay texto en el campo de confirmación, validar coincidencia
        if self.entrada_confirm_container.text():
            self.validar_coincidencia()
        
    def validar_coincidencia(self):
        """Valida que las contraseñas coincidan"""
        password = self.entrada_password_container.text()
        confirm = self.entrada_confirm_container.text()
        
        if not confirm:
            self.feedback_password.setVisible(False)
            return False
            
        if password != confirm:
            self.feedback_password.setText("Las contraseñas no coinciden")
            self.feedback_password.setVisible(True)
            return False
            
        # Todo bien, ocultar feedback
        self.feedback_password.setVisible(False)
        return True
        
    def validar_formulario(self):
        """Valida todo el formulario antes de enviar"""
        # Validar usuario con verificación completa
        usuario_valido = self.validar_usuario_tiempo_real()
        
        # Validar contraseña
        nombre_completo = self.entrada_nombre.text()
        palabras_nombre = [p for p in nombre_completo.split() if p.strip()]
        if len(palabras_nombre) < 3:
            self.feedback_nombre = getattr(self, 'feedback_nombre', QLabel())
            self.feedback_nombre.setText("El nombre completo debe tener al menos 3 palabras")
            self.feedback_nombre.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
            self.feedback_nombre.setVisible(True)
            return False
        else:
            # Ocultar mensaje de error si existe
            feedback_nombre = getattr(self, 'feedback_nombre', None)
            if feedback_nombre:
                feedback_nombre.setVisible(False)
            
        password = self.entrada_password_container.text()
        if not password:
            self.feedback_password.setText("La contraseña es obligatoria")
            self.feedback_password.setVisible(True)
            return False
            
        # Verificar requisitos mínimos de contraseña
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if len(password) < 8:
            self.feedback_password.setText("La contraseña debe tener al menos 8 caracteres")
            self.feedback_password.setVisible(True)
            return False
            
        if not (has_upper and has_lower and has_digit and has_special):
            self.feedback_password.setText("La contraseña debe tener mayúsculas, minúsculas, números y caracteres especiales")
            self.feedback_password.setVisible(True)
            return False
            
        # Validar coincidencia
        coinciden = self.validar_coincidencia()
        
        return usuario_valido and coinciden
    
    def registrar_usuario(self):
        """Intenta registrar el usuario"""
        if self.validar_formulario():
            # Datos para el registro
            username = self.entrada_usuario.text()
            password = self.entrada_password_container.text()
            nombre_completo = self.entrada_nombre.text()
            rol = self.combo_rol.currentText()  # Obtener el rol seleccionado
            
            # Intentar crear usuario directamente en lugar de verificar primero
            try:
                from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
                
                # Determinar rol según selección
                if rol == "Administrador":
                    exito, mensaje = ModeloUsuarios.crear_usuario_admin(username, password, nombre_completo)
                elif rol == "Médico":
                    exito, mensaje = ModeloUsuarios.crear_usuario_crud(username, password, nombre_completo)
                else:  # Visitante
                    exito, mensaje = ModeloUsuarios.crear_usuario(username, password, nombre_completo)
                
                if exito:
                    # Si tuvo éxito, aceptar el diálogo para finalizar el registro
                    self.accept()
                else:
                    # Mostrar error si falló (por ejemplo, si el usuario ya existe)
                    from Front_end.styles.dialog_components import mostrar_mensaje_advertencia
                    mostrar_mensaje_advertencia(
                        self,
                        "Error de registro",
                        mensaje
                    )
                    # Si el error es que el usuario ya existe, mostrarlo en la interfaz
                    if "ya existe" in mensaje.lower():
                        self.feedback_usuario.setText("Este nombre de usuario ya existe")
                        self.feedback_usuario.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
                        self.feedback_usuario.setVisible(True)
                    return
                    
            except Exception as e:
                print(f"Error en verificación final: {str(e)}")
                from Front_end.styles.dialog_components import mostrar_mensaje_advertencia
                mostrar_mensaje_advertencia(
                    self,
                    "Error de sistema",
                    f"Ocurrió un error inesperado: {str(e)}"
                )
                return
        else:
            # Mostrar mensaje de error general si no se completó la validación
            from Front_end.styles.dialog_components import mostrar_mensaje_advertencia
            mostrar_mensaje_advertencia(
                self, 
                "Formulario Incompleto",
                "Por favor corrija los errores en el formulario antes de continuar."
            )