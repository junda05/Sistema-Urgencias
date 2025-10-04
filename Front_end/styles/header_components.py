from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QApplication, QDesktopWidget
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt
import os
from Front_end.styles.styles import COLORS
from Front_end.styles.components import StyledButton

class BarraTitulo(QWidget):
    """Barra de título personalizada para todas las ventanas, sin necesidad de barra de título del sistema."""
    
    def __init__(self, parent=None, botones_izquierda=None):
        """
        Inicializa la barra de título.
        
        Args:
            parent: Widget padre
            botones_izquierda: Lista de tuplas (texto, función, es_cerrar) para botones en la parte izquierda
        """
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.layout.setSpacing(5)
        
        # Agregar botones a la izquierda si se proporcionan
        if botones_izquierda:
            for texto, funcion, es_cerrar in botones_izquierda:
                boton = StyledButton(texto, "window_control", is_close=es_cerrar)
                boton.setFixedSize(30, 30)
                boton.clicked.connect(funcion)
                self.layout.addWidget(boton, 0, Qt.AlignLeft | Qt.AlignTop)
        
        # Espacio expansible en el medio
        self.layout.addStretch(1)
        
        # Botones de control (lado derecho) - siempre presentes
        botones_control = [
            ("🗕", lambda: parent.showMinimized() if parent else None, False),  # Minimizar
            ("🗗", self.toggle_maximized, False),  # Maximizar/Restaurar
            ("✖", lambda: parent.close() if parent else None, True)  # Cerrar
        ]
        
        for texto, funcion, es_cerrar in botones_control:
            boton = StyledButton(texto, "window_control", is_close=es_cerrar)
            boton.setFixedSize(30, 30)
            boton.clicked.connect(funcion)
            self.layout.addWidget(boton, 0, Qt.AlignRight | Qt.AlignTop)
    
    def toggle_maximized(self):
        """Alterna entre modo maximizado y normal para la ventana padre."""
        if self.parent() is None:
            return
            
        if self.parent().isMaximized():
            self.parent().showNormal()
        else:
            self.parent().showMaximized()

class HeaderCombinado(QWidget):
    """Componente reutilizable para crear un header con logo y botones de control"""
    
    def __init__(self, parent=None, logo_path=None, height_percent=0.14, bg_color=COLORS['background_header']):
        """
        Inicializa un header combinado con logo y botones de control.
        
        Args:
            parent: Widget padre
            logo_path: Ruta al logo que se mostrará
            height_percent: Porcentaje de la altura de la pantalla para el header (0.14 = 14%)
            bg_color: Color de fondo del header
        """
        super().__init__(parent)
        
        # Calcular tamaños para asegurar que coincidan con la interfaz de login
        pantalla = QDesktopWidget().screenGeometry()
        ancho_pantalla = pantalla.width()
        alto_pantalla = pantalla.height()
        alto_logo = int(alto_pantalla * height_percent)
        
        # Establecer altura fija para el header completo y estilo
        self.setFixedHeight(alto_logo)
        self.setStyleSheet(f"background-color: {bg_color};")
        
        # Crear layout para organizar logo y botones de control
        layout_header = QHBoxLayout(self)
        layout_header.setContentsMargins(0, 0, 10, 0)
        
        # Área del logo (lado izquierdo)
        if logo_path and os.path.exists(logo_path):
            ancho_logo = int(ancho_pantalla * 0.2)  # 20% del ancho de pantalla
            
            etiqueta_logo = QLabel()
            mapa_pixeles_logo = QPixmap(logo_path)
            logo_escalado = mapa_pixeles_logo.scaled(
                ancho_logo, 
                alto_logo, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            etiqueta_logo.setPixmap(logo_escalado)
            etiqueta_logo.setStyleSheet(f"background: {COLORS['background_transparent']};")
            
            # Añadir logo al lado izquierdo
            layout_header.addWidget(etiqueta_logo, 0, Qt.AlignLeft | Qt.AlignVCenter)
        
        # Espacio expansible en el medio
        layout_header.addStretch(1)
        
        # Botones de control (lado derecho)
        botones = [
            ("🗕", lambda: parent.showMinimized() if parent else None, False),
            ("🗗", lambda: self._toggle_maximized(parent), False),
            ("✖", lambda: parent.close() if parent else None, True)
        ]
        
        for texto, funcion, es_cerrar in botones:
            if funcion:  # Solo crear el botón si hay una función para conectar
                boton = StyledButton(texto, "window_control", is_close=es_cerrar)
                boton.setFixedSize(30, 30)
                boton.clicked.connect(funcion)
                layout_header.addWidget(boton, 0, Qt.AlignRight | Qt.AlignTop)
    
    def _toggle_maximized(self, parent):
        """Maneja de forma segura la llamada a toggle_maximized del padre."""
        if parent:
            if hasattr(parent, 'toggle_maximized'):
                parent.toggle_maximized()
            else:
                # Fallback si el método no existe
                if parent.isMaximized():
                    parent.showNormal()
                else:
                    parent.showMaximized()

class VentanaSinMarco(QWidget):
    """Clase base para ventanas sin marco de título del sistema pero con comportamiento de arrastre."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Eliminar barra de título del sistema
        self.setWindowFlags(Qt.FramelessWindowHint)
        # Permitir transparencia de fondo
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Variables para manejar el arrastre de la ventana
        self.dragging = False
        self.offset = None
    
    def mousePressEvent(self, event):
        # Permitir arrastrar la ventana
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        # Mover la ventana mientras se arrastra
        if self.dragging:
            self.move(self.mapToGlobal(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        # Detener el arrastre
        if event.button() == Qt.LeftButton:
            self.dragging = False
    
    def toggle_maximized(self):
        """Alterna entre modo maximizado y normal para la ventana."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

class BarraEstado(QWidget):
    """Barra de estado inferior para mostrar información de servidor, versión, etc."""
    
    def __init__(self, parent=None, info_izquierda=None, info_centro=None, info_derecha=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        
        # Información en la izquierda (como botones o texto)
        if info_izquierda:
            layout.addWidget(info_izquierda, 0, Qt.AlignLeft | Qt.AlignVCenter)
        else:
            layout.addStretch(1)
        
        # Información en el centro
        if info_centro:
            layout.addWidget(info_centro, 0, Qt.AlignCenter)
        
        # Información en la derecha
        if info_derecha:
            layout.addWidget(info_derecha, 0, Qt.AlignRight | Qt.AlignVCenter)
        else:
            layout.addStretch(1)
