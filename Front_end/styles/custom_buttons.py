from PyQt5.QtWidgets import QPushButton, QAction, QHBoxLayout, QLabel, QWidget, QLineEdit, QFrame, QVBoxLayout, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
from Front_end.styles.styles import COLORS, BORDER_RADIUS

class IconButton(QPushButton):
    """Botón con ícono y texto personalizable."""
    
    def __init__(self, text, icon_path=None, color="#659BD1", hover_color=None, parent=None):
        super().__init__(text, parent)
        
        # Usar un color de fondo más suave y elegante
        if color == COLORS['background_header']:
            color = "#D5E5F3"  # Azul muy suave
            hover_color = "#E8F0FE" 
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 2px;
                padding: 12px 5px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 25px;
                min-height: 40px;
                icon-size: 35px 35px;  /* Tamaño del icono */
                text-align: center;
                border-bottom: 2px solid rgba(0, 0, 0, 0.1);
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                border-bottom: 2px solid rgba(0, 0, 0, 0.2);
            }}
            QPushButton:pressed {{
                background-color: {self._adjust_color(color, False)};
                border-bottom: 1px solid rgba(0, 0, 0, 0.2);
                padding-top: 13px;
            }}
        """)
        
        # Configurar ícono si se proporciona con mayor tamaño
        if icon_path:
            icon = QIcon(icon_path)
            self.setIcon(icon)
            self.setIconSize(QSize(40, 40))  # Iconos ligeramente más grandes
            self.setText("   " + text)
        # Cursor tipo mano al pasar por encima
        self.setCursor(Qt.PointingHandCursor)
    
    def _adjust_color(self, color, brighter=True):
        """Ajusta el color para efecto hover"""
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            
            if brighter:
                # Aclarar para hover
                factor = 1.1
                r = min(255, int(r*factor))
                g = min(255, int(g*factor))
                b = min(255, int(b*factor))
            else:
                # Oscurecer para hover
                factor = 0.9
                r = int(r*factor)
                g = int(g*factor)
                b = int(b*factor)
                
            return f'#{r:02x}{g:02x}{b:02x}'
        return color

class LogoutButton(QWidget):
    """Botón de cierre de sesión con ícono."""
    
    def __init__(self, parent=None, icon_path=None, logout_func=None, corner="bottom-right"):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.button = QPushButton("Cerrar Sesión")
        self.button.setCursor(Qt.PointingHandCursor)
        
        # Configurar el color de acuerdo con la esquina donde estará
        if corner == "bottom-right":
            button_color = COLORS['button_logout']
            hover_color = self._adjust_color(button_color)
        else:
            button_color = COLORS['button_primary']
            hover_color = COLORS['button_primary_hover']
        
        # Configurar ícono si se proporciona
        if icon_path:
            icon = QIcon(icon_path)
            self.button.setIcon(icon)
            self.button.setIconSize(QSize(22, 22))
        
        self.button.setStyleSheet(f"""
            QPushButton {{
                background-color: {button_color};
                color: white;
                border: none;
                border-radius: {BORDER_RADIUS['medium']};
                padding: 8px 15px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: bold;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                border: 1px solid white;
            }}
        """)
        
        if logout_func:
            self.button.clicked.connect(logout_func)
            
        layout.addWidget(self.button)
        self.setFixedWidth(150)
    
    def _adjust_color(self, color, brighter=True):
        """Ajusta el color para efecto hover"""
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            
            if brighter:
                # Aclarar para hover
                factor = 1.1
                r = min(255, int(r*factor))
                g = min(255, int(g*factor))
                b = min(255, int(b*factor))
            else:
                # Oscurecer para hover
                factor = 0.9
                r = int(r*factor)
                g = int(g*factor)
                b = int(b*factor)
                
            return f'#{r:02x}{g:02x}{b:02x}'
        return color

class SearchContainer(QWidget):
    """Contenedor de búsqueda con estilo similar a los botones."""
    
    def __init__(self, parent=None, height=None):
        super().__init__(parent)
        
        # Usar los mismos colores que IconButton para consistencia
        color = "#D5E5F3"  # Azul muy suave
        
        # Crear un frame principal que contendrá todo
        self.frame = QFrame(self)
        self.frame.setObjectName("searchContainerFrame")
        self.frame.setStyleSheet(f"""
            #searchContainerFrame {{
                background-color: {color};
                border-radius: 2px;
                border: none;
                border-bottom: 2px solid rgba(0, 0, 0, 0.1);
            }}
        """)
        
        # Layout principal que contiene el frame
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.frame)
        
        # Layout interno para los componentes del buscador
        self.layout = QHBoxLayout(self.frame)
        self.layout.setContentsMargins(15, 0, 15, 0)  # Reducir márgenes verticales
        self.layout.setSpacing(20)
        
        # Crear componentes internos
        self.icon_label = QLabel()
        self.icon_label.setStyleSheet("background-color: transparent;")
        self.icon_label.setFixedSize(35, 35)  # Tamaño fijo para el ícono
        
        # Texto "Buscar" con el mismo estilo que los botones
        self.text_label = QLabel("Buscar")
        self.text_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 25px;
            background-color: transparent;
            font-family: 'Segoe UI', sans-serif;
        """)
        
        # Campo de búsqueda - ajustar para que ocupe todo el espacio vertical disponible
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ingrese nombre o documento para buscar")
        self.search_input.setStyleSheet(f"""
            background-color: #E8F0FE;
            color: {COLORS['text_primary']};
            font-size: 16px;
            border: none;
            padding: 8px;
            min-height: 30px;  /* Altura mínima para el campo */
        """)
        self.search_input.setClearButtonEnabled(True)
        
        # Ajustar el estilo del botón de limpieza (x) para centrarlo verticalmente
        self.search_input.findChild(QAction).setIcon(QIcon())  # Eliminar ícono predeterminado
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #E8F0FE;
                color: {COLORS['text_primary']};
                font-size: 16px;
                border: none;
                padding: 8px 25px 8px 8px;  /* Padding derecho para el botón clear */
                min-height: 30px;
            }}
            QLineEdit::clear-button {{
                subcontrol-position: right center;  /* Posición a la derecha y centrado vertical */
                subcontrol-origin: padding;         /* Origen desde el padding */
                image: none;                        /* Sin imagen predeterminada */
                width: 20px;                        /* Ancho fijo */
                height: 20px;                       /* Altura fija */
                margin-right: 5px;                  /* Margen derecho */
                background: transparent;            /* Fondo transparente */
            }}
            QLineEdit::clear-button:hover {{
                background-color: rgba(0, 0, 0, 0.1); /* Fondo al pasar el mouse */
                border-radius: 10px;                 /* Borde redondeado */
            }}
        """)
        
        # Agregar componentes al layout
        self.layout.addWidget(self.icon_label, 0, Qt.AlignVCenter)
        self.layout.addWidget(self.text_label, 0, Qt.AlignVCenter)
        self.layout.addWidget(self.search_input, 1)
        
        # Si se proporciona una altura, usarla; de lo contrario, usar un valor predeterminado
        if height is not None:
            self.setFixedHeight(height)
            # Aplicar la misma altura al frame interno, dejando margen para el borde
            self.frame.setFixedHeight(height)
        else:
            # Altura predeterminada similar a los botones IconButton
            self.setFixedHeight(65)
            self.frame.setFixedHeight(65)
        
        # Políticas de tamaño para mantener la responsividad
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Asegurar que el QLineEdit ocupe toda la altura disponible
        field_height = height - 20 if height else 45  # Dejar margen para paddings
        self.search_input.setMinimumHeight(field_height)
    
    def set_icon(self, icon_path=None, size=35):
        """Configura el ícono de búsqueda."""
        from PyQt5.QtGui import QPixmap
        import os
        
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.icon_label.setText("🔍")
            self.icon_label.setStyleSheet("background-color: transparent; font-size: 20px;")
    
    def get_search_input(self):
        """Retorna el QLineEdit para conectar señales."""
        return self.search_input
