from PyQt5.QtWidgets import (QWidget, QLineEdit, QPushButton, QHBoxLayout, 
                           QVBoxLayout, QLabel, QFrame, QDesktopWidget)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from Front_end.styles.styles import COLORS, BORDER_RADIUS, PADDING, FONT_SIZE

class EntradaContrasena(QWidget):
    """Campo de entrada de contraseña con botón para mostrar/ocultar."""
    
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
        # Removing hard-coded font size to inherit from parent
        self.entrada_contrasena.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background-color: {COLORS['background_transparent']};
                padding: {PADDING['medium']};
            }}
        """)
        
        self.boton_mostrar = QPushButton("👁")
        self.boton_mostrar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['background_transparent']};
                border: none;
                font-size: 25px;
                padding: 0 10px; /* Aumentar padding horizontal para mayor área hover */
                color: {COLORS['button_primary']};
            }}
            QPushButton:hover {{
                color: {COLORS['button_primary_hover']};
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: {BORDER_RADIUS['medium']}; /* Usar radius medium en lugar de small */
            }}
        """)
        # Aumentar el tamaño del botón para mejor visualización
        self.boton_mostrar.setFixedSize(40, 40)
        self.boton_mostrar.setCursor(Qt.PointingHandCursor)
        
        layout.addWidget(self.entrada_contrasena)
        layout.addWidget(self.boton_mostrar)
        
        self.boton_mostrar.clicked.connect(self.mostrar_contra)
    
    def mostrar_contra(self):
        """Alterna entre modo normal y modo contraseña."""
        if self.entrada_contrasena.echoMode() == QLineEdit.Password:
            self.entrada_contrasena.setEchoMode(QLineEdit.Normal)
        else:
            self.entrada_contrasena.setEchoMode(QLineEdit.Password)
    
    def text(self):
        """Devuelve el texto de la entrada."""
        return self.entrada_contrasena.text()
    
    def clear(self):
        """Limpia la entrada."""
        self.entrada_contrasena.clear()
    
    def setPlaceholderText(self, texto):
        """Establece el texto placeholder."""
        self.entrada_contrasena.setPlaceholderText(texto)
    
    def setEchoMode(self, modo):
        """Establece el modo de visualización."""
        self.entrada_contrasena.setEchoMode(modo)

class FrameBotones(QFrame):
    """Frame para botones con estilo consistente."""
    
    def __init__(self, botones, parent=None, color="#659BD1", spacing=30, search_container=None):
        """
        Inicializa un frame de botones con estilo consistente.
        
        Args:
            botones: Lista de tuplas (texto, función, color_opcional)
            parent: Widget padre
            color: Color por defecto para todos los botones (si no se especifica individualmente)
            spacing: Espaciado entre botones
            search_container: Contenedor de búsqueda opcional
        """
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(spacing)
        
        pantalla = QDesktopWidget().screenGeometry()
        ancho_boton = int(pantalla.width() * 0.12)  # 12% del ancho de pantalla
        
        for item in botones:
            if len(item) == 3:
                texto, funcion, btn_color = item
            else:
                texto, funcion = item
                btn_color = color
                
            boton = QPushButton(texto)
            boton.setFixedWidth(ancho_boton)
            boton.setStyleSheet(f"""
                QPushButton {{
                    background-color: {btn_color};
                    color: {COLORS['text_white']};
                    font-family: 'Franklin Gothic Medium';
                    font-size: 18px;
                    min-height: 50px;
                    padding: 5px 15px;
                    border-radius: 10px;
                    border: 1px solid {COLORS['background_white']};
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self.ajustar_color(btn_color, brighter=True)}; 
                }}
            """)
            boton.setCursor(Qt.PointingHandCursor)
            boton.clicked.connect(funcion)
            layout.addWidget(boton)
        
        # Agregar contenedor de búsqueda si se proporciona
        if search_container:
            layout.addWidget(search_container)

        # Distribuir espacio equitativamente
        layout.addStretch()
    
    def ajustar_color(self, color, brighter=False):
        """Ajusta el color para el efecto hover."""
        if color.startswith('#'):
            # Convertir el color hex a RGB
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            
            if brighter:
                # Aclarar para efecto hover (para botones más oscuros)
                factor = 1.1
                r = min(255, int(r*factor))
                g = min(255, int(g*factor))
                b = min(255, int(b*factor))
            else:
                # Oscurecer para efecto hover (para botones más claros)
                factor = 0.9
                r = int(r*factor)
                g = int(g*factor)
                b = int(b*factor)
                
            return f'#{r:02x}{g:02x}{b:02x}'
        return color

class TablaContainer(QWidget):
    def __init__(self, parent=None, width_percent=0.80, height_percent=0.60):
        super().__init__(parent)
        self.setStyleSheet(f"QWidget {{background-color: {COLORS['background_transparent']}; border: none;}}")
        
        # Usar un layout vertical con alineación centrada
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignCenter)  # Centrar contenido
        
        # Guardar los porcentajes para uso posterior
        self.width_percent = width_percent
        self.height_percent = height_percent
        
    def set_tabla(self, tabla):
        # Limpiamos cualquier widget existente
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Agregamos la tabla al layout sin modificar su tamaño
        self.layout.addWidget(tabla)
        
        # Aplicamos tamaños consistentes para ambas interfaces
        pantalla = QDesktopWidget().screenGeometry()
        ancho_pantalla = pantalla.width()
        alto_pantalla = pantalla.height()
        
        # Ajustamos los tamaños para que sean más compactos
        ancho_tabla = int(ancho_pantalla * self.width_percent)
        alto_tabla = int(alto_pantalla * self.height_percent)
        
        # Aplicamos el tamaño directamente a la tabla
        tabla.setFixedWidth(ancho_tabla)
        tabla.setFixedHeight(alto_tabla)
