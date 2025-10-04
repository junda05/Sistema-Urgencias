import sys
import os
import pymysql
import configparser
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QWidget, 
                             QMessageBox, QDesktopWidget, QDialog, QFormLayout,
                             QProgressBar, QGraphicsOpacityEffect, QGraphicsDropShadowEffect,
                             QSizePolicy)
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor, QIcon, QLinearGradient, QBrush
from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal, QPoint, QRect
from PIL import Image, ImageFilter
from Back_end.Manejo_DB import ModeloConfiguracion, ModeloAutenticacion
# Importar estilos y componentes
from Front_end.styles.styles import *
from Front_end.styles.components import StyledMessageBox, StyledButton, StyledDialog, FormField
# Importar componentes de animación
from Front_end.styles.animation_components import SplashScreen, FadeAnimation, WorkerThread
# Importar utilidades de fuentes
from Front_end.styles.font_utils import aplicar_fuentes_sistema
from Front_end.styles.styles import COLORS, BORDER_RADIUS, PADDING, FONT_SIZE
# Importar componentes de botones personalizados
from Front_end.styles.custom_buttons import IconButton

# Definir funciones para mostrar mensajes estilizados
def mostrar_mensaje_error(parent, titulo, mensaje):
    """Muestra un mensaje de error estilizado"""
    msg_box = StyledMessageBox(parent, titulo, mensaje, QMessageBox.Critical, "error")
    
    # Crear botón OK estilizado
    btn_ok = QPushButton("Aceptar")
    btn_ok.setCursor(Qt.PointingHandCursor)
    
    msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
    msg_box.setDefaultButton(btn_ok)
    
    return msg_box.exec_()

def mostrar_mensaje_advertencia(parent, titulo, mensaje):
    """Muestra un mensaje de advertencia estilizado"""
    msg_box = StyledMessageBox(parent, titulo, mensaje, QMessageBox.Warning, "warning")
    
    # Crear botón OK estilizado
    btn_ok = QPushButton("Aceptar")
    btn_ok.setCursor(Qt.PointingHandCursor)
    
    msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
    msg_box.setDefaultButton(btn_ok)
    
    return msg_box.exec_()

def mostrar_mensaje_informacion(parent, titulo, mensaje):
    """Muestra un mensaje informativo estilizado"""
    msg_box = StyledMessageBox(parent, titulo, mensaje, QMessageBox.Information, "info")
    btn_ok = QPushButton("Aceptar")
    
    # Crear botón OK estilizado
    btn_ok.setCursor(Qt.PointingHandCursor)
    
    msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
    msg_box.setDefaultButton(btn_ok)
    
    return msg_box.exec_()

class ConfigDialog(StyledDialog):
    def __init__(self, parent=None):
        super().__init__("Configuración de Conexión", 450, parent)
        
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
            mostrar_mensaje_advertencia(self, "Dato Inválido", "El servidor no puede estar vacío.")
            return
        
        # Guardar la configuración utilizando el modelo
        exito, mensaje = ModeloConfiguracion.guardar_configuracion(nuevo_host)
        
        if exito:
            mostrar_mensaje_informacion(self, "Configuración Guardada", 
                                   "La configuración se ha guardado correctamente.\n"
                                   "Los cambios serán aplicados la próxima vez que inicie sesión.")
            self.accept()
        else:
            mostrar_mensaje_error(self, "Error", f"No se pudo guardar la configuración: {mensaje}")

class InterfazLogin(QMainWindow):
    _instance = None
    
    @classmethod
    def crear_instancia(cls):
        if not QApplication.instance():
            aplicacion = QApplication(sys.argv)
            
            # Aplicamos fuentes personalizadas inmediatamente
            aplicar_fuentes_sistema()
            
            # Mostrar splash screen al iniciar la aplicación con tamaño responsivo
            if getattr(sys, 'frozen', False):
                ruta_base = sys._MEIPASS
            else:
                ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
            ruta_imagenes = os.path.join(ruta_base, "Front_end", "imagenes")
            ruta_logo = os.path.join(ruta_imagenes, "logo_foscal.png")
            
            # Obtener el tamaño de la pantalla para hacer el splash responsivo
            pantalla = QDesktopWidget().screenGeometry()
            
            splash = SplashScreen(None, logo_path=ruta_logo, message="Iniciando aplicación...", duration=2)
            splash.setFixedSize(int(pantalla.width() * 0.3), int(pantalla.height() * 0.3))
            splash.show()
            QApplication.processEvents()
            
            aplicacion.setWindowIcon(QIcon(os.path.join(ruta_imagenes, "logo.png")))
            splash.exec_()
        else:
            aplicacion = QApplication.instance()
            
        if not cls._instance:
            cls._instance = cls()
        
        return cls._instance, aplicacion

    def __init__(self):
        super().__init__()
        # Aplicar fuentes al iniciar la interfaz
        aplicar_fuentes_sistema()
        
        # Eliminar barra de título
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        if getattr(sys, 'frozen', False):
            self.ruta_base = sys._MEIPASS
        else:
            self.ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Cargar configuración usando el modelo
        self.cargar_configuracion()

        if getattr(sys, 'frozen', False):
            ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        else:
            ruta_imagenes = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagenes")
        
        self.ruta_logo = os.path.join(ruta_imagenes, "logo_foscal.png")
        # Cambiamos la extensión a .png para el ícono de la aplicación
        self.ruta_icono = os.path.join(ruta_imagenes, "logo.png")
        self.ruta_logou = os.path.join(ruta_imagenes, "u.png")
        print(f"Buscando logo en: {self.ruta_logo}")
        print(f"Buscando icono en: {self.ruta_icono}")
        
        # Establecer el icono de la ventana
        if os.path.exists(self.ruta_icono):
            self.setWindowIcon(QIcon(self.ruta_icono))
            # También configurar el icono de la aplicación
            if QApplication.instance() is not None:
                QApplication.instance().setWindowIcon(QIcon(self.ruta_icono))
        
        self.initUI()
        
        # Variables para mover la ventana sin barra de título
        self.dragging = False
        self.offset = None

    def cargar_configuracion(self):
        """Carga la configuración usando el modelo de configuración"""
        try:
            # Cargar configuración usando el modelo
            host = ModeloConfiguracion.cargar_configuracion()
            # Establecer el servidor en el modelo de autenticación
            ModeloAutenticacion.establecer_servidor(host)
        except Exception as e:
            mostrar_mensaje_advertencia(
                self, 
                "Error de configuración", 
                f"No se pudo cargar la configuración: {str(e)}\nSe usarán valores predeterminados."
            )
            ModeloAutenticacion.establecer_servidor('localhost')

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

    def iniciar(self):
        self.show()
        return QApplication.instance().exec_()
    
    def crear_barra_titulo(self):
        barra_titulo = QWidget()
        barra_titulo.setFixedHeight(30)
        barra_titulo.setStyleSheet(f"background-color: {COLORS['background_header']};")
        
        layout_barra_titulo = QHBoxLayout(barra_titulo)
        layout_barra_titulo.setContentsMargins(0, 0, 10, 0)
        layout_barra_titulo.setSpacing(5)
        layout_barra_titulo.addStretch()  # Espacio expansible a la izquierda
        
        # Crear botones de control
        botones = [
            ("🗕", self.showMinimized, False),  # Minimizar
            ("🗗", self.toggle_maximized, False),  # Maximizar/Restaurar
            ("✖", self.close, True)  # Cerrar
        ]
        
        for texto, funcion, es_cerrar in botones:
            boton = StyledButton(texto, "window_control", is_close=es_cerrar)
            boton.setFixedSize(30, 30)
            boton.clicked.connect(funcion)
            layout_barra_titulo.addWidget(boton)
        
        return barra_titulo
    
    def initUI(self):
        self.setWindowTitle("Interfaz Foscal")
        pantalla = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, pantalla.width(), pantalla.height())
        self.showMaximized()
        
        # Fondo con gradiente suave
        widget_central = QWidget()
        palette = QPalette()
        gradient = QLinearGradient(0, 0, 0, pantalla.height())
        gradient.setColorAt(0, QColor(90, 140, 190))  # Azul más claro en la parte superior
        gradient.setColorAt(1, QColor(74, 114, 150))  # Azul un poco más oscuro en la parte inferior
        palette.setBrush(QPalette.Window, QBrush(gradient))
        widget_central.setAutoFillBackground(True)
        widget_central.setPalette(palette)
        self.setCentralWidget(widget_central)
        
        layout_principal = QVBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)
        
        ancho_pantalla = pantalla.width()
        alto_pantalla = pantalla.height()

        try:
            contenedor_logo = QLabel(widget_central)
            # Ajustes para el logo
            alto_logo = int(alto_pantalla * 0.14)  # 10% de la altura de pantalla
            ancho_logo = int(ancho_pantalla * 0.2)  # 20% del ancho de pantalla
            contenedor_logo.setStyleSheet(f"background-color: {COLORS['background_header']};")
            contenedor_logo.move(0, 0)

            if os.path.exists(self.ruta_logo):
                mapa_pixeles_logo = QPixmap(self.ruta_logo)
                etiqueta_logo = QLabel(widget_central)
                logo_escalado = mapa_pixeles_logo.scaled(
                    ancho_logo, 
                    alto_logo, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                etiqueta_logo.setPixmap(logo_escalado)
                contenedor_logo.setFixedSize(pantalla.width(), logo_escalado.height())
                etiqueta_logo.setFixedSize(logo_escalado.size())
                etiqueta_logo.setStyleSheet(f"background: {COLORS['background_transparent']};")
            
            # Agregar logo universidad debajo de los botones de la barra de título
            if os.path.exists(self.ruta_logou):
                # Reducir tamaño para asegurar que quepa en el espacio disponible
                alto_logo_u = int(alto_pantalla * 0.1)  # Reducido de 0.08
                ancho_logo_u = int(ancho_pantalla * 0.15)  # Reducido de 0.12
                
                etiqueta_logo_u = QLabel(widget_central)
                mapa_pixeles_logo_u = QPixmap(self.ruta_logou)
                logo_escalado_u = mapa_pixeles_logo_u.scaled(
                    ancho_logo_u,
                    alto_logo_u,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                etiqueta_logo_u.setPixmap(logo_escalado_u)
                etiqueta_logo_u.setFixedSize(logo_escalado_u.size())  # Fijar tamaño exactamente al del logo
                etiqueta_logo_u.setStyleSheet(f"background: {COLORS['background_transparent']}; border: none;")
                
                # Posicionamiento ajustado - poner en coordenadas absolutas que sabemos funcionarán
                # Posicionar en la esquina superior derecha, justo debajo del área de los botones
                etiqueta_logo_u.move(
                    ancho_pantalla - ancho_logo_u + int(ancho_logo_u*0.25),  # 15px de margen derecho
                    int(alto_logo_u*0.3)  # Posición Y fija debajo de los botones de control (que típicamente son 30px de alto)
                )
                
                # Asegurarnos que sea visible
                etiqueta_logo_u.raise_()  # Traer al frente
                etiqueta_logo_u.show()
                
        except Exception as e:
            mostrar_mensaje_error(self, "Error", 
                f"Error al configurar rutas: {str(e)}\n\n"
                f"Por favor, asegúrese de que la carpeta 'imagenes' está en:\n{self.ruta_base}")

        # Calcular dimensiones proporcionales
        pantalla = QDesktopWidget().screenGeometry()
        ancho_pantalla = pantalla.width()
        alto_pantalla = pantalla.height()

        # Calcular tamaño del contenedor como porcentaje de la pantalla
        ancho_contenedor = int(ancho_pantalla * 0.285)  # % ancho de pantalla
        alto_contenedor = int(alto_pantalla * 0.60)   # % altura de pantalla - reducido ya que eliminamos un campo

        tamano_titulo = int(alto_contenedor * 0.08) 
        tamano_etiquetas = int(alto_contenedor * 0.035)
        tamano_inputs = int(alto_contenedor * 0.031)

        # Ajustar contenedor_login
        contenedor_login = QWidget(widget_central)
        contenedor_login.setFixedWidth(ancho_contenedor)
        contenedor_login.setFixedHeight(alto_contenedor)
        contenedor_login.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background_header']};
                border-radius: {BORDER_RADIUS['xlarge']};
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
        """)

        contenedor_login.setGeometry(
            (ancho_pantalla - ancho_contenedor) // 2,  # Centrado horizontal
            ((alto_pantalla - alto_contenedor) // 2) + int(alto_pantalla * 0.033),   # Centrado vertical, ajustado hacia arriba
            ancho_contenedor,
            alto_contenedor
        )

        layout_login = QVBoxLayout(contenedor_login)
        layout_login.setContentsMargins(
            int(ancho_contenedor * 0.05),  # márgenes laterales
            int(alto_contenedor * 0.05),   # márgenes superior e inferior
            int(ancho_contenedor * 0.05),
            int(alto_contenedor * 0.05)
        )
        layout_login.setSpacing(int(alto_contenedor * 0.03))

        titulo = QLabel("Iniciar sesión")
        titulo.setStyleSheet(f"""
            background-color: {COLORS['background_transparent']};
            color: {COLORS['text_primary']};
            font-size: {tamano_titulo}px;
            margin: {int(alto_contenedor * 0.02)}px 0;
            border: none;
        """)
        titulo.setFont(QFont("ABeeZee"))
        titulo.setAlignment(Qt.AlignCenter)
        layout_login.addWidget(titulo)
        layout_login.addSpacing(int(alto_contenedor*0.02))  # Increased spacing

        # Usuario
        etiqueta_usuario = QLabel("Usuario")
        etiqueta_usuario.setFont(QFont("ABeeZee"))
        etiqueta_usuario.setStyleSheet(f"""
            background-color: {COLORS['background_transparent']};
            font-size: {tamano_etiquetas}px;
            border: none;
        """)
        layout_login.addWidget(etiqueta_usuario)
        
        self.entrada_usuario = QLineEdit()
        self.entrada_usuario.setPlaceholderText("Usuario")
        # Ensure consistent styling with password field by using FONT_SIZE['medium']
        self.entrada_usuario.setStyleSheet(f"""
            padding: {PADDING['medium']};
            border: 2px solid {COLORS['background_transparent']};
            border-radius: {BORDER_RADIUS['xlarge']};
            background-color: #FCFCFC;
            margin: 5px;
            min-height: {int(alto_contenedor * 0.06)}px;
            font-size: {FONT_SIZE['medium']};
        """)
        layout_login.addWidget(self.entrada_usuario)
        
        # Etiqueta de error para el usuario
        self.error_usuario = QLabel("")
        self.error_usuario.setStyleSheet(f"""
            color: {COLORS['button_danger']};
            font-size: {int(tamano_etiquetas * 0.8)}px;
            background-color: {COLORS['background_transparent']};
            border: 2px solid {COLORS['background_transparent']};
            padding-left: 10px;
            font-weight: bold;
        """)
        self.error_usuario.setVisible(False)
        layout_login.addWidget(self.error_usuario)
        
        layout_login.addSpacing(int(alto_contenedor*0.02))  # Increased spacing

        # Contraseña
        etiqueta_contrasena = QLabel("Contraseña")
        etiqueta_contrasena.setFont(QFont("ABeeZee"))
        etiqueta_contrasena.setStyleSheet(f"""
            background-color: {COLORS['background_transparent']};
            font-size: {tamano_etiquetas}px;
            border: none;
        """)
        layout_login.addWidget(etiqueta_contrasena)

        self.entrada_contrasena = EntradaContrasena()
        self.entrada_contrasena.setPlaceholderText("Contraseña")
        self.entrada_contrasena.setEchoMode(QLineEdit.Password)
        self.entrada_contrasena.setMinimumHeight(int(alto_contenedor * 0.08))
        # Pass font size to EntradaContrasena
        self.entrada_contrasena.entrada_contrasena.setStyleSheet(f"""
            border: none;
            background-color: {COLORS['background_transparent']};
            padding: {PADDING['medium']};
            font-size: {FONT_SIZE['medium']};
        """)
        
        widget_contrasena = QWidget()
        widget_contrasena.setStyleSheet(f"""
            padding: {PADDING['medium']};
            border: 2px solid {COLORS['background_transparent']};
            border-radius: {BORDER_RADIUS['xlarge']};
            background-color: #FCFCFC;
            margin: 5px;
            min-height: {int(alto_contenedor * 0.06)}px;
            font-size: {tamano_inputs}px;
        """)
        layout_contrasena = QHBoxLayout(widget_contrasena)
        layout_contrasena.setContentsMargins(0, 0, 0, 0)
        layout_contrasena.addWidget(self.entrada_contrasena)
        layout_login.addWidget(widget_contrasena)
        
        # Etiqueta de error para la contraseña
        self.error_contrasena = QLabel("")
        self.error_contrasena.setStyleSheet(f"""
            color: {COLORS['button_danger']};
            font-size: {int(tamano_etiquetas * 0.8)}px;
            background-color: {COLORS['background_transparent']};
            border: 2px solid {COLORS['background_transparent']};
            padding-left: 10px;
            font-weight: bold;
        """)
        self.error_contrasena.setVisible(False)
        layout_login.addWidget(self.error_contrasena)
        
        layout_login.addSpacing(int(alto_contenedor*0.05))  # Increased spacing

        # Botón de ingreso
        boton_ingresar = StyledButton("Ingresar", "primary")
        boton_ingresar.setFixedSize(
            int(ancho_contenedor * 0.5),  # ancho
            int(alto_contenedor * 0.08)    # alto
        )
        boton_ingresar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_primary']};
                color: {COLORS['text_white']};
                border: none;
                border-radius: {BORDER_RADIUS['xlarge']};
                font-size: {FONT_SIZE['xxlarge']};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['button_primary_hover']};
            }}
        """)
        
        boton_ingresar.clicked.connect(self.validar_credenciales)
        layout_login.addWidget(boton_ingresar, alignment=Qt.AlignCenter)
        
        layout_login.addStretch()  # Add stretch to push content up and leave space at bottom

        # Barra de título personalizada
        barra_titulo = self.crear_barra_titulo()
        layout_principal.addWidget(barra_titulo, alignment=Qt.AlignRight | Qt.AlignTop)
        
        # Crear barra inferior para etiqueta de servidor y botón de configuración
        barra_inferior = QWidget()
        barra_inferior.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        layout_barra_inferior = QHBoxLayout(barra_inferior)
        layout_barra_inferior.setContentsMargins(20, 5, 20, 10)
        layout_barra_inferior.setSpacing(10)
        
        # Ruta al ícono de servidor
        ruta_icono_servidor = os.path.join(self.ruta_base, "Front_end", "imagenes", "servidor.png")
        
        # Crear botón de configuración usando IconButton para mayor consistencia visual
        boton_config = IconButton("Configuración", 
                                ruta_icono_servidor if os.path.exists(ruta_icono_servidor) else None,
                                COLORS['background_transparent'],  # Fondo transparente
                                "rgba(255, 255, 255, 0.1)")  # Hover efecto sutil
                                
        # Ajustar tamaño del botón para que sea responsivo pero con ancho limitado
        boton_config.setFixedHeight(int(alto_pantalla * 0.05))  # 5% de la altura de pantalla
        boton_config.setFixedWidth(int(ancho_pantalla * 0.12))  # 12% del ancho de pantalla como ancho fijo
        
        # Sobrescribir algunos estilos para que coincida con la etiqueta del servidor
        boton_config.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['background_transparent']};
                color: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: {BORDER_RADIUS['medium']};
                padding: 8px 12px;
                font-size: {int(tamano_etiquetas * 0.9)}px;
                text-align: left;
                vertical-align: middle;
            }}
            QPushButton:hover {{
                color: white;
                background-color: rgba(255, 255, 255, 0.1);
            }}
        """)
        
        # Cambiar la política de tamaño para que no se expanda horizontalmente
        boton_config.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        boton_config.clicked.connect(self.abrir_configuracion)
        
        # Agregar el botón directamente al layout para mejor alineación
        layout_barra_inferior.addWidget(boton_config, alignment=Qt.AlignVCenter)
        
        # Agregar espacio expansible en el medio
        layout_barra_inferior.addStretch()
        
        # Mostrar servidor configurado
        credenciales = ModeloAutenticacion.obtener_credenciales()
        etiqueta_servidor = QLabel(f"Servidor: {credenciales['equipo_trabajo']}")
        etiqueta_servidor.setStyleSheet(f"""
            color: rgba(255, 255, 255, 0.9);
            font-size: {int(tamano_etiquetas * 0.9)}px;
            background-color: {COLORS['background_transparent']};
            padding: 8px 12px;
        """)
        
        # Agregar etiqueta de servidor directamente al layout para mejor alineación
        layout_barra_inferior.addWidget(etiqueta_servidor, alignment=Qt.AlignVCenter)
        
        # Agregar barra inferior al layout principal 
        layout_principal.addStretch()  # Empuja todo el contenido hacia arriba
        layout_principal.addWidget(barra_inferior)
        
        # Conectar eventos para limpiar errores al editar
        self.entrada_usuario.textChanged.connect(self.limpiar_error_usuario)
        self.entrada_contrasena.entrada_contrasena.textChanged.connect(self.limpiar_error_contrasena)

    def toggle_maximized(self):
        # Alternar entre maximizado y restaurado
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def validar_credenciales(self):
        # Limpiar cualquier mensaje de error anterior
        self.limpiar_todos_errores()
        
        usuario = self.entrada_usuario.text()
        contrasena = self.entrada_contrasena.text()
        
        if not usuario or not contrasena:
            if not usuario:
                self.mostrar_error_usuario("Campo obligatorio")
            if not contrasena:
                self.mostrar_error_contrasena("Campo obligatorio")
            mostrar_mensaje_advertencia(self, "Campos incompletos", "Por favor complete todos los campos.")
            return
        
        try:
            # Usar el modelo de autenticación para validar las credenciales
            exito, mensaje = ModeloAutenticacion.validar_credenciales(usuario, contrasena)
            
            if exito:
                self.abrir_ventana_principal()
            else:
                self.mostrar_error_usuario("Credenciales inválidas")
                self.mostrar_error_contrasena("Credenciales inválidas")
                mostrar_mensaje_error(self, "Error de acceso", mensaje)
        
        except pymysql.err.OperationalError as e:
            error_code = e.args[0]
            error_message = e.args[1]
            
            # Error 1045: Acceso denegado para el usuario
            if error_code == 1045:
                self.mostrar_error_usuario("Usuario o contraseña incorrectos")
                self.mostrar_error_contrasena("Usuario o contraseña incorrectos")
                mostrar_mensaje_error(self, "Error de acceso", 
                    "Usuario o contraseña incorrectos.\nVerifique sus credenciales e intente nuevamente.")
                
            # Error 2003: No se puede conectar al servidor MySQL
            elif error_code == 2003:
                mostrar_mensaje_error(self, "Error de conexión", 
                    f"No se puede conectar al servidor:\n{error_message}\n\nVerifique que el servidor esté disponible.")
                
            # Error de host: este usuario no está autorizado a conectarse desde este host
            elif "Host" in error_message and "is not allowed to connect" in error_message:
                self.mostrar_error_usuario("Acceso restringido para este usuario")
                mostrar_mensaje_error(self, "Acceso restringido", 
                    f"Este usuario no está autorizado a conectarse desde este equipo.\n\n{error_message}")
                
            else:
                mostrar_mensaje_error(self, "Error de conexión", f"Error al conectar a la base de datos:\n{error_message}")
        
        except Exception as e:
            mostrar_mensaje_error(self, "Error inesperado", 
                f"Se produjo un error inesperado:\n{str(e)}\n\nPor favor contacte al administrador del sistema.")
    
    def mostrar_error_usuario(self, mensaje):
        """Muestra un mensaje de error para el campo de usuario"""
        self.error_usuario.setText(mensaje)
        self.error_usuario.setVisible(True)
        self.entrada_usuario.setStyleSheet(f"""
            padding: {PADDING['medium']};
            border: 2px solid {COLORS['button_danger']};
            border-radius: {BORDER_RADIUS['xlarge']};
            background-color: rgba(255, 230, 230, 0.85);
            margin: 5px;
            min-height: {int(self.height() * 0.03)}px;
            font-size: {int(self.height() * 0.015)}px;
        """)
    
    def mostrar_error_contrasena(self, mensaje):
        """Muestra un mensaje de error para el campo de contraseña"""
        self.error_contrasena.setText(mensaje)
        self.error_contrasena.setVisible(True)
        # Aplicar estilo al contenedor de contraseña
        self.entrada_contrasena.parent().setStyleSheet(f"""
            padding: {PADDING['medium']};
            border: 2px solid {COLORS['button_danger']};
            border-radius: {BORDER_RADIUS['xlarge']};
            background-color: rgba(255, 230, 230, 0.85);
            margin: 5px;
            min-height: {int(self.height() * 0.03)}px;
            font-size: {int(self.height() * 0.015)}px;
        """)
    
    def limpiar_error_usuario(self):
        """Limpia el mensaje de error del usuario"""
        self.error_usuario.setVisible(False)
        # Restaurar estilo original con el mismo tamaño de fuente que el campo de contraseña
        alto_contenedor = int(self.height() * 0.55)
        self.entrada_usuario.setStyleSheet(f"""
            padding: {PADDING['medium']};
            border: 2px solid {COLORS['background_transparent']};
            border-radius: {BORDER_RADIUS['xlarge']};
            background-color: #FCFCFC;
            margin: 5px;
            min-height: {int(alto_contenedor * 0.06)}px;
            font-size: {FONT_SIZE['medium']};
        """)
    
    def limpiar_error_contrasena(self):
        """Limpia el mensaje de error de la contraseña"""
        self.error_contrasena.setVisible(False)
        # Restaurar estilo original
        alto_contenedor = int(self.height() * 0.55)
        tamano_inputs = int(alto_contenedor * 0.025)
        self.entrada_contrasena.parent().setStyleSheet(f"""
            padding: {PADDING['medium']};
            border-radius: {BORDER_RADIUS['xlarge']};
            border: 2px solid {COLORS['background_transparent']};
            background-color: #FCFCFC;
            margin: 5px;
            min-height: {int(alto_contenedor * 0.06)}px;
            font-size: {tamano_inputs}px;
        """)
    
    def limpiar_todos_errores(self):
        """Limpia todos los mensajes de error"""
        self.limpiar_error_usuario()
        self.limpiar_error_contrasena()

    def abrir_ventana_principal(self):
        """Abre la ventana principal de la aplicación"""
        try:
            # Obtener el usuario autenticado
            usuario = ModeloAutenticacion.obtener_credenciales().get('usuario', '')
            
            # Mejorar el manejo de errores en la verificación de privilegios
            try:
                from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
                
                # Obtener el rol directamente desde la tabla usuarios
                rol_usuario = ModeloUsuarios.obtener_rol_usuario(usuario)
                
                # Registro para debugging
                print(f"[DEBUG] Usuario: {usuario}, Rol: {rol_usuario}")
            except Exception as e:
                # Si hay error verificando el rol, registrar el error y asignar rol visitante por defecto
                print(f"Error verificando rol: {str(e)}")
                rol_usuario = "visitante"  # Valor por defecto si hay error
                
            # Obtener el tamaño de la pantalla para hacer el splash responsivo
            pantalla = QDesktopWidget().availableGeometry()
            
            # Importante: establecer la ventana actual como parent para que aparezca por encima
            splash = SplashScreen(self, logo_path=self.ruta_logo, message="Iniciando sesión...", duration=2)
            splash.setFixedSize(int(pantalla.width() * 0.3), int(pantalla.height() * 0.3))
            
            # Asegurar que aparezca sobre la ventana de login
            splash.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            splash.show()
            splash.raise_()  # Traer al frente
            splash.opacity_animation.start()  # Iniciar animación de fade-in
            QApplication.processEvents()
            
            # Esperar a que termine la pantalla de carga
            splash.exec_()
            
            # Oculta la ventana de login (después de la pantalla de carga)
            self.hide()
            
            # Mostrar la ventana correspondiente según el rol del usuario
            try:
                if rol_usuario == "admin":
                    # Importación diferida para evitar importaciones circulares
                    from Front_end.admin import VistaAdmins
                    self.ventana_principal = VistaAdmins(self)
                    print(f"Usuario {usuario} con rol de Administrador - Iniciando vista admin.py")
                elif rol_usuario == "medico":
                    # Usuario con rol de médico
                    from Front_end.doctors import VistaMedicos
                    self.ventana_principal = VistaMedicos(self)
                    print(f"Usuario {usuario} con rol de Médico - Iniciando vista doctors.py")
                else:
                    # Usuario visitante o con rol de solo lectura
                    from Front_end.sala_espera import VistaSalaEspera
                    self.ventana_principal = VistaSalaEspera(self)
                    print(f"Usuario {usuario} con rol de Visitante - Iniciando vista sala_espera.py")
                
                self.ventana_principal.show()
            except Exception as e:
                self.show()  # Mostrar nuevamente la ventana de login en caso de error
                mostrar_mensaje_error(self, "Error al cargar la vista", 
                    f"No se pudo iniciar la interfaz de usuario: {str(e)}\n"
                    f"Por favor contacte al administrador del sistema.")
            
        except ImportError as e:
            self.show()  # Mostrar nuevamente la ventana de login en caso de error
            mostrar_mensaje_error(self, "Error de inicialización", 
                f"No se pudo cargar el módulo principal de la aplicación.\n"
                f"Por favor verifique que todos los archivos estén en su ubicación correcta.\n"
                f"Error detallado: {str(e)}")
        except Exception as e:
            self.show()  # Mostrar nuevamente la ventana de login en caso de error
            # Asegurar que el mensaje sea legible - no mostrar placeholders de texto
            error_msg = str(e)
            if "'text warning'" in error_msg:
                error_msg = "Error en la validación de la interfaz de usuario."
            mostrar_mensaje_error(self, "Error", f"No se pudo iniciar la aplicación: {error_msg}")

    def reiniciar_login(self):
        self.entrada_usuario.clear()
        self.entrada_contrasena.clear()
        # Limpiar credenciales en el modelo
        ModeloAutenticacion.limpiar_credenciales()
        self.show()

    def abrir_configuracion(self):
        """Abre el diálogo de configuración"""
        dialogo = ConfigDialog(self)
        if dialogo.exec_() == QDialog.Accepted:
            # Recargar la configuración si se guardaron cambios
            self.cargar_configuracion()
            
            # Actualizar la etiqueta del servidor
            credenciales = ModeloAutenticacion.obtener_credenciales()
            for widget in self.findChildren(QLabel):
                if "Servidor:" in widget.text():
                    widget.setText(f"Servidor: {credenciales['equipo_trabajo']}")
                    break

    def logout(self):
        # Obtener el tamaño de la pantalla para hacer el splash responsivo
        pantalla = QDesktopWidget().screenGeometry()
        
        # Mostrar pantalla de carga al cerrar sesión
        splash = SplashScreen(self, logo_path=self.ruta_logo, message="Cerrando sesión...", duration=1.5)
        splash.setFixedSize(int(pantalla.width() * 0.3), int(pantalla.height() * 0.3))
        splash.show()
        splash.opacity_animation.start()  # Iniciar animación de fade-in
        QApplication.processEvents()
        
        # Esperar a que termine la pantalla de carga
        splash.exec_()
        
        # Importante: limpiar la referencia a ventana_principal si existe
        if hasattr(self, 'ventana_principal'):
            self.ventana_principal = None
            
        # Reiniciar la interfaz de login
        self.reiniciar_login()

    def closeEvent(self, event):
        # Simply accept the event without showing a splash screen
        event.accept()


class EntradaContrasena(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        # Ajustar los márgenes para contener correctamente el botón
        layout.setContentsMargins(0, 0, 5, 0)
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
        
        # Determinar ruta base para las imágenes
        if getattr(sys, 'frozen', False):
            self.ruta_base = sys._MEIPASS
        else:
            self.ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        self.icon_show = os.path.join(ruta_imagenes, "ver.png")
        self.icon_hide = os.path.join(ruta_imagenes, "esconder.png")
        
        self.boton_mostrar = QPushButton()
        # Aumentar aún más el tamaño del botón para mejor visualización
        self.boton_mostrar.setFixedSize(40, 40)
        self.boton_mostrar.setCursor(Qt.PointingHandCursor)
        self.boton_mostrar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['background_transparent']};
                border: none;
                padding: 0 10px; /* Aumentar padding horizontal para mayor área hover */
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: 20px; /* Radius adaptado al tamaño del botón */
            }}
        """)
        
        self.is_visible = False
        self.update_button_icon()
        
        layout.addWidget(self.entrada_contrasena)
        layout.addWidget(self.boton_mostrar, 0, Qt.AlignVCenter)
        
        self.boton_mostrar.clicked.connect(self.mostrar_contra)
    
    def update_button_icon(self):
        """Actualiza el icono según el estado actual"""
        icon_path = self.icon_hide if self.is_visible else self.icon_show
        if os.path.exists(icon_path):
            self.boton_mostrar.setIcon(QIcon(icon_path))
            # Aumentar tamaño del icono para mejor visualización
            self.boton_mostrar.setIconSize(QSize(22, 22))
    
    def mostrar_contra(self):
        self.is_visible = not self.is_visible
        self.entrada_contrasena.setEchoMode(QLineEdit.Normal if self.is_visible else QLineEdit.Password)
        self.update_button_icon()
    
    def text(self):
        return self.entrada_contrasena.text()
    
    def clear(self):
        self.entrada_contrasena.clear()
    
    def setPlaceholderText(self, texto):
        self.entrada_contrasena.setPlaceholderText(texto)
    
    def setEchoMode(self, modo):
        self.entrada_contrasena.setEchoMode(modo)