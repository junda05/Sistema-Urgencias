from PyQt5.QtWidgets import (QDialog, QLabel, QVBoxLayout, QHBoxLayout, QWidget, 
                           QProgressBar, QGraphicsOpacityEffect, QDesktopWidget,
                           QApplication)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QPixmap
import os
import time
from Front_end.styles.styles import COLORS, BORDER_RADIUS

class WorkerThread(QThread):
    """Hilo de trabajo para actualizar progreso en segundo plano."""
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    
    def __init__(self, duration=3):
        super().__init__()
        self.duration = duration
        
    def run(self):
        for i in range(101):
            self.progress.emit(i)
            time.sleep(self.duration / 100)
        self.finished.emit()

class FadeAnimation:
    """Clase para crear transiciones de fade-in/fade-out para widgets"""
    
    @staticmethod
    def fade_in(widget, duration=500):
        """Hace aparecer gradualmente un widget"""
        # Crear efecto de opacidad
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)
        
        # Crear animación
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration)  # duración en ms
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start(QPropertyAnimation.DeleteWhenStopped)
        return animation
    
    @staticmethod
    def fade_out(widget, duration=500, delete_when_done=False):
        """Hace desaparecer gradualmente un widget"""
        # Crear efecto de opacidad
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)
        
        # Crear animación
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration)  # duración en ms
        animation.setStartValue(1)
        animation.setEndValue(0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Conectar señal finished si se debe eliminar el widget al terminar
        if delete_when_done:
            animation.finished.connect(widget.deleteLater)
        
        animation.start(QPropertyAnimation.DeleteWhenStopped)
        return animation
        
    @staticmethod
    def slide_in_from_bottom(widget, duration=500):
        """Hace que un widget aparezca deslizándose desde abajo"""
        # Guardar la posición final
        target_pos = widget.pos()
        
        # Mover el widget fuera de la pantalla (abajo)
        start_pos = QPoint(target_pos.x(), target_pos.y() + widget.height())
        widget.move(start_pos)
        
        # Crear la animación
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(target_pos)
        animation.setEasingCurve(QEasingCurve.OutQuad)
        animation.start(QPropertyAnimation.DeleteWhenStopped)
        return animation

class SplashScreen(QDialog):
    """Pantalla de carga con logo, mensaje y barra de progreso."""
    
    def __init__(self, parent=None, logo_path=None, message="Cargando...", autoclose=True, duration=3):
        super().__init__(parent, Qt.FramelessWindowHint)
        self.setModal(True)
        self.setAttribute(Qt.WA_TranslucentBackground) 
        
        # Configuraciones
        self.duration = duration
        self.autoclose = autoclose
        
        # Obtener el tamaño de la pantalla para hacer todo responsivo
        pantalla = QDesktopWidget().screenGeometry()
        
        # Crea el layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Crea el contenedor con fondo
        self.container = QWidget(self)
        self.container.setObjectName("container")
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(15)
        
        # Estilo consistente para todas las pantallas de carga
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background_primary']};
                border-radius: {BORDER_RADIUS['xlarge']};
                border: 2px solid {COLORS['button_primary']};
            }}
        """)
        
        self.container.setStyleSheet(f"""
            #container {{
                background-color: {COLORS['background_primary']};
                border-radius: {BORDER_RADIUS['xlarge']};
            }}
        """)
        
        # Logo
        if logo_path and os.path.exists(logo_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path)
            
            ancho_logo = int(pantalla.width() * 0.15)  # 15% del ancho de la pantalla
            
            logo_scaled = logo_pixmap.scaled(ancho_logo, ancho_logo, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_scaled)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet(f"background: {COLORS['background_transparent']};")
            container_layout.addWidget(logo_label)
        
        # Mensaje con estilo consistente
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)
        
        # Calcular tamaño de fuente responsivo
        tamano_fuente = int(pantalla.height() * 0.018)  # 1.8% de la altura de la pantalla
        
        message_label.setStyleSheet(f"""
            color: {COLORS['button_primary']};
            font-size: {tamano_fuente}px;
            font-weight: bold;
            margin: 10px;
            background-color: {COLORS['background_transparent']};
        """)
        
        container_layout.addWidget(message_label)
        
        # Barra de progreso con estilo consistente
        alto_barra = int(pantalla.height() * 0.01)  # 1% de la altura de la pantalla
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(alto_barra)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['background_readonly']};
                border-radius: {BORDER_RADIUS['small']};
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['button_primary']};
                border-radius: {BORDER_RADIUS['small']};
            }}
        """)
        container_layout.addWidget(self.progress_bar)
        
        # Agregar contenedor al layout principal
        layout.addWidget(self.container)
        
        # Centrar en pantalla y establecer tamaño responsivo
        ancho_splash = int(pantalla.width() * 0.25)  # 25% del ancho de la pantalla
        alto_splash = int(pantalla.height() * 0.25)  # 25% de la altura de la pantalla
        
        self.setFixedSize(ancho_splash, alto_splash)
        
        # Worker thread para el progreso
        self.worker = WorkerThread(duration=self.duration)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.finish_loading)
        
        # Efecto de entrada con fade-in
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(300)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Asegurarse de que esté centrado incluso después de setFixedSize
        self.center_on_screen()

    def center_on_screen(self):
        """Centra la ventana en la pantalla"""
        pantalla = QDesktopWidget().screenGeometry()
        self.move(
            int((pantalla.width() - self.width()) / 2),
            int((pantalla.height() - self.height()) / 2)
        )
    
    def setFixedSize(self, width, height):
        """Sobrescribe setFixedSize para centrar después de cambiar el tamaño"""
        super().setFixedSize(width, height)
        self.center_on_screen()
        
    def start_loading(self):
        """Inicia el proceso de carga."""
        self.worker.start()
        
    def update_progress(self, value):
        """Actualiza la barra de progreso."""
        self.progress_bar.setValue(value)
        
    def finish_loading(self):
        """Se llama cuando finaliza la carga."""
        if self.autoclose:
            self.accept()
    
    def showEvent(self, event):
        """Se llama cuando se muestra la pantalla de carga."""
        super().showEvent(event)
        # Iniciar la animación al mostrar
        QTimer.singleShot(100, self.start_loading)
        
    def set_message(self, message):
        """Cambia el mensaje mostrado en la pantalla de carga."""
        # Busca la etiqueta de mensaje y actualiza su texto
        for child in self.container.children():
            if isinstance(child, QLabel) and child.text() != "":
                child.setText(message)
                break
