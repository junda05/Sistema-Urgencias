from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QDesktopWidget, QApplication)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QTimer
from PyQt5.QtGui import QIcon, QGraphicsOpacityEffect
import os
import sys
from Front_end.styles.styles import COLORS
from Front_end.styles.header_components import HeaderCombinado, BarraEstado, VentanaSinMarco

class VentanaBase(QMainWindow):
    """Clase base para todas las ventanas de la aplicación con comportamiento común."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Eliminar barra de título
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Obtener tamaño de pantalla para elementos responsivos
        self.pantalla = QDesktopWidget().screenGeometry()
        
        # Variables para mover la ventana sin barra de título
        self.dragging = False
        self.offset = None
        
        # Efecto de opacidad para animación de entrada
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)  # Iniciar invisible
        
        # Determinar rutas base
        if getattr(sys, 'frozen', False):
            # Si la aplicación está empaquetada (con PyInstaller)
            self.ruta_base = sys._MEIPASS
        else:
            # Para ejecución normal del script
            self.ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        self.ruta_logo = os.path.join(self.ruta_imagenes, "logo_foscal.png")
        self.ruta_icono = os.path.join(self.ruta_imagenes, "logo.ico")
        
        # Establecer el icono de la ventana
        if os.path.exists(self.ruta_icono):
            self.setWindowIcon(QIcon(self.ruta_icono))
    
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
    
    def crear_layout_principal(self):
        """Crea el widget central y layout principal."""
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)  # Eliminar espacio entre widgets
        return widget_central, layout_principal
    
    def crear_header(self):
        """Crea y retorna un header con logo."""
        return HeaderCombinado(self, self.ruta_logo, 0.14, "rgba(252, 252, 252, 0.6)")
    
    def crear_barra_estado(self, info_izquierda=None, info_centro=None, info_derecha=None):
        """Crea y retorna una barra de estado inferior."""
        return BarraEstado(self, info_izquierda, info_centro, info_derecha)
    
    def animar_aparicion(self, duracion=500):
        """Anima la aparición de la ventana con un efecto de fade-in."""
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(duracion)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()
    
    def centrar_en_pantalla(self):
        """Centra la ventana en la pantalla."""
        pantalla = QDesktopWidget().screenGeometry()
        self.move(
            int((pantalla.width() - self.width()) / 2),
            int((pantalla.height() - self.height()) / 2)
        )
    
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
