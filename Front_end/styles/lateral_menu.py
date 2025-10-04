from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                           QLabel, QGraphicsOpacityEffect, QFrame,
                           QHBoxLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QRect
from PyQt5.QtGui import QIcon, QPixmap
import os
import sys
from Front_end.styles.styles import COLORS, FONT_SIZE
from Front_end.styles.components import StyledButton

# Usar directamente el color principal de la aplicación en lugar de una transparencia
LATERAL_MENU_BG_COLOR = COLORS["background_header"]

class LateralMenu(QWidget):
    """Componente de menú lateral que se desliza desde la derecha"""
    
    def __init__(self, parent=None, width=320):  # Aumentado de 280 a 320px para hacerlo más ancho
        super().__init__(parent)
        self.parent = parent
        self.width = width
        self.is_open = False
        
        # Configurar widget
        self.setFixedWidth(self.width)
        # Aplicar estilo al widget principal con el color principal
        self.setStyleSheet(f"""
            background-color: {LATERAL_MENU_BG_COLOR};
            border-left: 1px solid {COLORS['border_light']};
        """)
        
        # Inicialmente oculto fuera de la pantalla
        if parent:
            self.setGeometry(parent.width(), 0, self.width, parent.height())
        
        # Crear un contenedor interno con el mismo color de fondo
        self.content_widget = QWidget(self)
        self.content_widget.setStyleSheet(f"background-color: {LATERAL_MENU_BG_COLOR}; border: none;")
        
        # Layout principal dentro del contenedor interno
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(15, 20, 15, 20)
        self.layout.setSpacing(0)  # Eliminar espaciado entre widgets
        
        # Layout para el widget principal que contendrá el widget interno
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.content_widget)

        # Crear contenedor para la cabecera del menú (título + botón de cierre)
        header_container = QWidget()
        header_container.setStyleSheet(f"background-color: {LATERAL_MENU_BG_COLOR}; border: none;")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Título del menú con fondo consistente
        title = QLabel("Menú")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: {FONT_SIZE['xxlarge']};
            font-weight: bold;
            background-color: {LATERAL_MENU_BG_COLOR};
            border: none;
        """)
        
        # Obtener ruta del ícono de cierre
        if getattr(sys, 'frozen', False):
            self.ruta_base = sys._MEIPASS
        else:
            self.ruta_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        ruta_icono_close = os.path.join(ruta_imagenes, "close_icon.png")
        
        # Agregar botón para cerrar el menú en la esquina superior derecha
        close_btn = QPushButton()
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        
        # Si existe el icono de cierre, usarlo; si no, usar texto
        if os.path.exists(ruta_icono_close):
            close_btn.setIcon(QIcon(ruta_icono_close))
            close_btn.setIconSize(QSize(20, 20))
        else:
            close_btn.setText("✖")
        
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LATERAL_MENU_BG_COLOR};
                color: {COLORS['text_primary']};
                border: none;
                font-size: 16px;
                padding: 4px;
                border-radius: 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['button_danger_hover']};
                color: white;
            }}
        """)
        close_btn.clicked.connect(self.toggle)
        
        # Agregar el título y botón de cierre al header
        header_layout.addStretch(1)
        header_layout.addWidget(title, 0, Qt.AlignCenter)
        header_layout.addStretch(1)
        header_layout.addWidget(close_btn, 0, Qt.AlignRight | Qt.AlignVCenter)
        
        # Agregar el contenedor del header al layout principal
        self.layout.addWidget(header_container)
        self.layout.addSpacing(10)
        
        # Separador
        self.add_separator()
        self.layout.addSpacing(10)
        
        # Animación para deslizamiento
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.setDuration(250)
        
    def add_separator(self):
        """Añade una línea separadora al menú"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"""
            background-color: {LATERAL_MENU_BG_COLOR};
            color: {COLORS['border_light']};
            border: none;
        """)
        separator.setFixedHeight(1)
        self.layout.addWidget(separator)
        
    def add_menu_button(self, text, icon_path=None, callback=None, button_type="primary"):
        """Añade un botón al menú lateral con icono y texto"""
        # Contenedor para el botón con fondo consistente
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Crear un QPushButton en lugar de un QWidget para mejor manejo de eventos
        button = QPushButton()
        button.setObjectName("menuButton")
        button.setFixedHeight(60)  # Altura fija para todos los botones
        button.setCursor(Qt.PointingHandCursor)
        
        # Crear layout interno para organizar icono y texto
        button_layout = QHBoxLayout(button)
        button_layout.setContentsMargins(20, 10, 20, 10)  # Padding interno para todo el botón
        button_layout.setSpacing(15)  # Espacio entre icono y texto
        
        # Agregar icono si existe
        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            icon_label.setAlignment(Qt.AlignCenter)
            button_layout.addWidget(icon_label)
        
        # Agregar texto
        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignVCenter)
        
        # Configurar colores según tipo de botón
        
        if button_type == "danger":
            # Aplicar color rojo directamente al label para "Cerrar Sesión"
            text_label.setStyleSheet(f"color: {COLORS['button_danger']}; background-color: transparent;")
        else:
            # Color normal para todos los demás botones
            text_label.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: transparent;")
        
        hover_bg = COLORS['button_danger_hover_sky'] if button_type == "danger" else COLORS['background_readonly']
        hover_text = "white" if button_type == "danger" else COLORS['button_primary']
        hover_border = COLORS['button_danger'] if button_type == "danger" else COLORS['button_primary']
        
        # Estilo unificado para el botón completo
        button.setStyleSheet(f"""
            #menuButton {{
                background-color: {LATERAL_MENU_BG_COLOR};
                border-radius: 10px;
                text-align: left;
                padding: 10px;
                margin: 5px 0px;
                border: none;
            }}
            #menuButton:hover {{
                background-color: {hover_bg};
                border-left: 4px solid {hover_border};
            }}
            #menuButton QLabel {{
                font-size: {FONT_SIZE['large']};
                background-color: transparent;
                border: none;
            }}
            #menuButton:hover QLabel {{
                color: {hover_text};
                font-weight: bold;
            }}
        """)
        
        button_layout.addWidget(text_label)
        button_layout.addStretch()
        
        # Conectar el callback
        if callback:
            button.clicked.connect(callback)
        
        # Agregar el botón al contenedor
        container_layout.addWidget(button)
        
        # Agregar espacio inferior con margen proporcional
        container_layout.addSpacing(10)
        
        # Agregar el contenedor al layout principal
        self.layout.addWidget(container)
        
        return button
        
    def add_spacer(self):
        """Añade un espacio flexible con fondo consistente"""
        # Crear un widget como spacer con fondo consistente
        spacer = QFrame()  # Usar QFrame en lugar de QWidget para más control
        spacer.setFrameShape(QFrame.NoFrame)
        spacer.setStyleSheet(f"""
            QFrame {{
                background-color: {LATERAL_MENU_BG_COLOR};
                border: none;
            }}
        """)
        # Establecer la política de tamaño para que se expanda verticalmente
        spacer.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        # Desactivar la transparencia del widget
        spacer.setAttribute(Qt.WA_TranslucentBackground, False)
        spacer.setAttribute(Qt.WA_NoSystemBackground, False)
        self.layout.addWidget(spacer, 1)  # Agregar con stretch factor de 1
        
    def toggle(self):
        """Abre o cierra el menú lateral"""
        if not self.parent:
            return
            
        # Detener cualquier animación anterior
        self.animation.stop()
        
        if not self.is_open:
            # Asegurar que el widget sea visible antes de la animación
            self.show()
            
            # Posicionar fuera de la pantalla
            start_x = self.parent.width()
            end_x = self.parent.width() - self.width
            
            self.setGeometry(start_x, 0, self.width, self.parent.height())
            
            # Configurar animación para abrir
            self.animation.setStartValue(QRect(start_x, 0, self.width, self.parent.height()))
            self.animation.setEndValue(QRect(end_x, 0, self.width, self.parent.height()))
        else:
            # Configurar animación para cerrar
            start_x = self.x()
            end_x = self.parent.width()
            
            # Configurar animación
            self.animation.setStartValue(QRect(start_x, 0, self.width, self.parent.height()))
            self.animation.setEndValue(QRect(end_x, 0, self.width, self.parent.height()))
            
        # Conectar evento para ocultar el menú cuando termina de cerrarse
        if self.is_open:
            self.animation.finished.connect(self._hide_when_closed)
        else:
            try:
                self.animation.finished.disconnect()
            except TypeError:
                # No había conexiones previas
                pass
                
        # Iniciar animación y actualizar estado
        self.animation.start()
        self.is_open = not self.is_open
    
    def _hide_when_closed(self):
        """Oculta el widget cuando termina la animación de cierre"""
        if not self.is_open:
            self.hide()
        try:
            self.animation.finished.disconnect()
        except TypeError:
            pass
    
    def resizeEvent(self, event):
        """Actualiza la posición cuando la ventana principal cambia de tamaño"""
        super().resizeEvent(event)
        if self.parent:
            if self.is_open:
                self.setGeometry(self.parent.width() - self.width, 0, self.width, self.parent.height())
            else:
                self.setGeometry(self.parent.width(), 0, self.width, self.parent.height())

    def adjust_for_screen_size(self):
        """Ajusta los elementos del menú según el tamaño de la pantalla para responsividad"""
        if not self.parent:
            return
            
        # Obtener dimensiones de la pantalla
        screen_width = self.parent.width()
        screen_height = self.parent.height()
        
        # Calcular ancho del menú responsivo (entre 280px y 25% del ancho de pantalla)
        menu_width = max(min(int(screen_width * 0.25), 420), 280)
        self.width = menu_width
        self.setFixedWidth(menu_width)
        
        # Calcular altura proporcional para los botones (entre 50px y 10% de la altura)
        button_height = max(min(int(screen_height * 0.08), 70), 50)
        
        # Ajustar tamaño de fuente según pantalla
        font_size = max(min(int(screen_height * 0.016), 18), 14)
        
        # Ajustar espaciado según el tamaño de pantalla
        horizontal_margin = max(min(int(screen_width * 0.02), 25), 15)
        self.layout.setContentsMargins(horizontal_margin, 20, horizontal_margin, 20)
        
        # Recorrer los botones y ajustar sus dimensiones
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, QWidget):
                for child in widget.findChildren(QPushButton, "menuButton"):
                    child.setFixedHeight(button_height)
                    # Actualizar el estilo para cambiar el tamaño de fuente
                    style = child.styleSheet()
                    style = style.replace(f"font-size: {FONT_SIZE['large']}", f"font-size: {font_size}px")
                    child.setStyleSheet(style)

        # Actualizar la posición si está abierto
        if self.is_open and self.parent:
            self.setGeometry(self.parent.width() - self.width, 0, self.width, self.parent.height())


class MenuToggleButton(QPushButton):
    """Botón que muestra/oculta el menú lateral"""
    
    def __init__(self, parent=None, lateral_menu=None):
        super().__init__(parent)
        self.lateral_menu = lateral_menu
        
        # Ruta a la imagen del menú
        if getattr(sys, 'frozen', False):
            self.ruta_base = sys._MEIPASS
        else:
            self.ruta_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        self.ruta_icono_menu = os.path.join(ruta_imagenes, "menu_icon.png")
        
        # Configurar apariencia
        self.setText("")
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 4px;
            }}
        """)
        
        # Si existe el ícono, usarlo; si no, mostrar el texto
        if os.path.exists(self.ruta_icono_menu):
            self.setIcon(QIcon(self.ruta_icono_menu))
            self.setIconSize(QSize(24, 24))
        else:
            self.setText("☰")
            self.setStyleSheet(self.styleSheet() + f"""
                QPushButton {{
                    color: {COLORS['text_primary']};
                    font-size: 18px;
                }}
            """)
        
        # Conectar evento
        self.clicked.connect(self.toggle_menu)
        
    def toggle_menu(self):
        """Alterna el estado del menú lateral"""
        if self.lateral_menu:
            self.lateral_menu.toggle()
