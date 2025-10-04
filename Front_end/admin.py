from PyQt5.QtWidgets import (QMainWindow, QComboBox, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTableWidget, QTableWidgetItem, QPushButton, 
                           QLabel, QMessageBox, QMenu, QFrame, QLayout,
                           QLineEdit, QFormLayout, QDialog, QListWidget, QListWidgetItem,
                           QHeaderView, QSizePolicy, QDesktopWidget, QApplication, QToolTip, 
                           QGraphicsOpacityEffect, QDateTimeEdit, QCheckBox, QGridLayout, QGroupBox, QScrollArea, QListView)
from PyQt5.QtCore import Qt, QTimer, QRect, QSize, QStringListModel, QPropertyAnimation, QEasingCurve, QPoint, QDateTime
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont, QPixmap, QIcon, QLinearGradient, QGradient
from Back_end.Manejo_DB import ModeloPaciente
from Front_end.styles.user_components import RegistroUsuarioDialog
from datetime import datetime
import sys
import os
# Importar componentes de animación desde su ubicación correcta
from Front_end.styles.animation_components import SplashScreen, FadeAnimation
# Importar estilos y componentes
from Front_end.styles.styles import TABLE_STYLES_UPDATED, SCROLLBAR_STYLE
from Front_end.styles.components import StyledMessageBox, StyledButton, StyledDialog, FormField
# Importar componentes de tablas
from Front_end.styles.table_components import Estado_delegado_circulo, TextDelegate, Personalizado_Columnas, configurar_tabla_estandar
# Importar componentes de header
from Front_end.styles.header_components import HeaderCombinado
# Importar el nuevo menú lateral
from Front_end.styles.lateral_menu import LateralMenu, MenuToggleButton
# Importar widgets personalizados
from Front_end.styles.custom_widgets import FrameBotones, TablaContainer
# Importar utilidades de fuentes
from Front_end.styles.font_utils import aplicar_fuentes_sistema
from Front_end.styles.Frontend_utils import DialogoFiltrar, LabsSelector, IxsSelector
from Front_end.styles.styles import COLORS, BORDER_RADIUS, MENU_STYLES

class VistaAdmins(QMainWindow):
    def __init__(self, login_interface):
        super().__init__()
        self.login_interface = login_interface
        self.modelo = ModeloPaciente()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Aplicar fuentes personalizadas inmediatamente
        aplicar_fuentes_sistema()
        
        # Obtener tamaño de pantalla para elementos responsivos
        self.pantalla = QDesktopWidget().screenGeometry()
        
        # Inicializar una bandera para rastrear la primera carga de la tabla
        self.primera_carga = True
        
        # Mostrar pantalla de carga mientras se inicializa la interfaz
        # Asegurando estilo consistente con la del programa principal
        self.splash = SplashScreen(None, logo_path=None, message="Cargando interfaz de pacientes...", duration=1.5)
        self.splash.setFixedSize(int(self.pantalla.width() * 0.3), int(self.pantalla.height() * 0.3))
        self.splash.show()
        self.splash.opacity_animation.start()  # Iniciar animación de fade-in
        QApplication.processEvents()
        
        # Efecto de opacidad para animación de entrada
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)  # Iniciar invisible
        
        # Improved path handling for both script and frozen executable
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle (compiled with PyInstaller)
            self.ruta_base = sys._MEIPASS
        else:
            # For normal script execution
            self.ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        self.ruta_logo = os.path.join(ruta_imagenes, "logo_foscal.png")
        self.ruta_logou = os.path.join(ruta_imagenes, "u.png")
        self.ruta_icono = os.path.join(ruta_imagenes, "logo.ico")
        
        # Establecer el icono de la ventana
        if os.path.exists(self.ruta_icono):
            self.setWindowIcon(QIcon(self.ruta_icono))
            
        # Variables para mover la ventana sin barra de título
        self.dragging = False
        self.offset = None
        
        # Definición de áreas
        self.areas = {
            "Antigua": (1, 18),
            "Amarilla": (19, 38),
            "Pediatría": (39, 59),
            "Pasillos": (60, 200),
            "Clini": (1, 40),
            "Sala de espera": (1, 2),
        }
        
        # Headers para la tabla - Cambiar IX por IMG
        self.headers = ["Nombre", "Documento", "Triage", "CI", "Labs", "IMG", "Interconsulta", "RV", "Pendientes", "Conducta", "Ubicación", "Ingreso"]
        
        # Crear menú lateral ANTES de configurar ventana y crear interfaz
        self.menu_lateral = LateralMenu(self)
        
        # Añadir esta nueva variable para guardar el texto de búsqueda
        self.texto_busqueda_actual = ""
        
        # Importar el modelo de preferencias para filtros
        from Back_end.Usuarios.ModeloPreferencias import ModeloPreferencias
        from Back_end.Manejo_DB import ModeloAutenticacion
        
        # Obtener el usuario actual
        credenciales = ModeloAutenticacion.obtener_credenciales()
        self.usuario_actual = credenciales.get('usuario')
        
        # Cargar preferencias de filtro para áreas
        self.areas_filtradas = ModeloPreferencias.obtener_filtros_area(
            self.usuario_actual, list(self.areas.keys())
        )
        
        # Si no hay áreas filtradas, usar todas por defecto
        if not self.areas_filtradas:
            self.areas_filtradas = list(self.areas.keys())
            self.mostrar_mensaje_informacion("Información", "No se encontraron filtros, usando todas las áreas")
            
        # Inicializar variables para filtro de fecha
        self.filtro_fecha_activo = False
        self.fecha_inicio = None
        self.fecha_fin = None
        
        # Configurar ventana y crear interfaz (esto crea self.tabla)
        self.configurar_ventana()
        self.crear_interfaz()
        
        # Cerrar la pantalla de carga antes de mostrar la interfaz principal
        self.splash.accept()
        
        # Ahora que la interfaz está creada, inicializar el timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_tabla)
        self.timer.start(5000)
        
        # Animación de entrada
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()
        
        # Actualizar tabla por primera vez después de que la interfaz está completa
        self.actualizar_tabla()
        self.modelo.datos_actualizados.connect(self.actualizar_tabla)
        
        # Después de crear_interfaz o al final de init
        self.configurar_menu_lateral()

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
        # Configurar un timer de una sola vez para establecer los anchos de columna después de que la ventana se muestre
        QTimer.singleShot(100, self.configurar_anchos_columnas)
        return QApplication.instance().exec_()
    
    def crear_interfaz(self):
        # Widget central principal
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)  # Eliminar espacio entre widgets

        # Crear y agregar barra combinada con logo usando el componente reutilizable
        header_combinado = self.crear_header_combinado()
        layout_principal.addWidget(header_combinado)

        # Crear contenedor para el contenido principal
        contenedor_contenido = QWidget()
        layout_contenido = QVBoxLayout(contenedor_contenido)
        layout_contenido.setContentsMargins(20, 50, 20, 20) 
        layout_contenido.setSpacing(15)

        # Crear barra de herramientas con botones y logout
        barra_herramientas = self.crear_barra_herramientas()
        layout_contenido.addWidget(barra_herramientas)

        # Crear tabla con tamaño limitado
        contenedor_tabla = self.crear_contenedor_tabla()
        layout_contenido.addWidget(contenedor_tabla)
        
        # Agregar el contenedor de contenido al layout principal
        layout_principal.addWidget(contenedor_contenido)

    def crear_barra_herramientas(self):
        """Crea una barra de herramientas con botones de acción y barra de búsqueda"""
        from Front_end.styles.custom_buttons import IconButton, SearchContainer
        
        # Contenedor para la barra de herramientas
        barra_herramientas = QWidget()
        barra_herramientas.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        
        # Hacer botones más responsivos
        pantalla = QDesktopWidget().screenGeometry()
        ancho_pantalla = pantalla.width()        
        alto_pantalla = pantalla.height()
        
        # Layout horizontal para organizar elementos
        layout_herramientas = QHBoxLayout(barra_herramientas)
        # Reducir márgenes para aprovechar mejor el espacio
        layout_herramientas.setContentsMargins(int(ancho_pantalla * 0.05), int(alto_pantalla * 0.01), 
                                              int(ancho_pantalla * 0.05), int(alto_pantalla * 0.01))
        # Espaciado proporcional entre elementos
        layout_herramientas.setSpacing(int(ancho_pantalla * 0.05))
        
        # Calcular tamaño basado en el ancho de la pantalla para mantener consistencia
        ancho_boton = int(ancho_pantalla * 0.17)
        altura_boton = int(alto_pantalla * 0.07)  # Altura más razonable
        
        # Crear contenedor de búsqueda con la nueva clase SearchContainer
        # Pasando la altura del botón para mantener consistencia
        contenedor_busqueda = SearchContainer(height=int(alto_pantalla * 0.07))
        
        # Ruta al ícono de lupa
        ruta_icono_lupa = os.path.join(self.ruta_base, "Front_end", "imagenes", "search.png")
        contenedor_busqueda.set_icon(ruta_icono_lupa)
        
        # Conectar evento de búsqueda
        self.entrada_busqueda = contenedor_busqueda.get_search_input()
        self.entrada_busqueda.textChanged.connect(self.buscar_paciente)
        
        # Obtener rutas de iconos para los botones
        ruta_imagen_add = os.path.join(self.ruta_base, "Front_end", "imagenes", "add_icon.png")
        ruta_imagen_delete = os.path.join(self.ruta_base, "Front_end", "imagenes", "delete_icon.png")
        
        # Crear botones con iconos y hacerlos más grandes
        btn_agregar = IconButton("Agregar paciente", ruta_imagen_add if os.path.exists(ruta_imagen_add) else None, COLORS['background_header'])
        btn_eliminar = IconButton("Eliminar Paciente", ruta_imagen_delete if os.path.exists(ruta_imagen_delete) else None, COLORS['background_header'])
        
        # Establecer alturas fijas en lugar de tamaños mínimos para consistencia
        btn_agregar.setFixedHeight(altura_boton)
        btn_eliminar.setFixedHeight(altura_boton)
        
        # Mantener el ancho mínimo para responsividad
        btn_agregar.setMinimumWidth(ancho_boton)
        btn_eliminar.setMinimumWidth(ancho_boton)
        
        # Políticas de tamaño para botones (expandirse horizontalmente)
        btn_agregar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_eliminar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Conectar eventos a los botones
        btn_agregar.clicked.connect(self.mostrar_formulario_agregar)
        btn_eliminar.clicked.connect(self.confirmar_eliminacion)
        
        # Agregar elementos al layout con proporciones de espacio equitativas
        # El contenedor de búsqueda toma más espacio (factor 2)
        layout_herramientas.addWidget(contenedor_busqueda, 2)
        layout_herramientas.addWidget(btn_agregar, 1)
        layout_herramientas.addWidget(btn_eliminar, 1)
        
        return barra_herramientas
    
    def mostrar_registro_usuario(self):
        """Muestra el diálogo de registro de usuario"""
        # Import dentro de la función para evitar problemas de importación circular
        from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
        
        dialogo = RegistroUsuarioDialog(self)
        if dialogo.exec_() == QDialog.Accepted:
            username = dialogo.entrada_usuario.text()
            password = dialogo.entrada_password_container.text()
            nombre_completo = dialogo.entrada_nombre.text()
            rol = dialogo.combo_rol.currentText()
            
            # Validar que el nombre completo tenga al menos 3 palabras
            palabras_nombre = [p for p in nombre_completo.split() if p.strip()]
            if len(palabras_nombre) < 3:
                self.mostrar_mensaje_error(
                    "Error de Registro",
                    "El nombre completo debe tener al menos 3 palabras."
                )
                return
            
            # Determinar el privilegio según el rol seleccionado
            if rol == "Administrador":
                exito, mensaje = ModeloUsuarios.crear_usuario_admin(username, password, nombre_completo)
                privilegio = "admin"
            elif rol == "Médico":
                exito, mensaje = ModeloUsuarios.crear_usuario_crud(username, password, nombre_completo)
                privilegio = "crud"  # crud equivale a médico en la tabla usuarios
            else:  # Visitante
                exito, mensaje = ModeloUsuarios.crear_usuario(username, password, nombre_completo)
                privilegio = "solo_lectura"  # solo_lectura equivale a visitante
            
            # Si la creación del usuario fue exitosa, actualizar la tabla de roles
            if exito:
                # Actualizar roles en la tabla usuarios para mantener consistencia
                ModeloUsuarios.actualizar_roles_en_tabla(username, privilegio)
                
                # Actualizar la tabla de usuarios si está abierta - FIX HERE
                if hasattr(self, 'tabla_usuarios') and self.tabla_usuarios:
                    try:
                        # Intentar recargar los usuarios en la tabla
                        if hasattr(self, 'cargar_usuarios'):
                            self.cargar_usuarios()
                    except Exception as e:
                        print(f"Info: No se puede actualizar la tabla de usuarios porque ya fue cerrada: {str(e)}")
                        # Continuar con el flujo normal sin afectar la experiencia del usuario
                
                self.mostrar_mensaje_informacion(
                    "Registro Exitoso",
                    f"El usuario {username} ha sido creado correctamente con rol de {rol}.\n"
                    f"Ahora puede iniciar sesión con sus credenciales."
                )
            else:
                self.mostrar_mensaje_error(
                    "Error de Registro",
                    mensaje
                )
                 
    def mostrar_mensaje_error(self, titulo, mensaje):
        """Muestra un mensaje de error estilizado"""
        msg_box = StyledMessageBox(self, titulo, mensaje, QMessageBox.Critical, "error")
        
        # Crear botón OK estilizado
        btn_ok = QPushButton("Aceptar")
        btn_ok.setCursor(Qt.PointingHandCursor)
        
        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
        msg_box.setDefaultButton(btn_ok)
        
        return msg_box.exec_()

    def buscar_paciente(self):
        """Filtra los pacientes en la tabla según el texto de búsqueda"""
        self.texto_busqueda_actual = self.entrada_busqueda.text().lower()
        
        self.aplicar_filtro_busqueda()
    
    def aplicar_filtro_busqueda(self):
        """Aplica el filtro de búsqueda actual a la tabla"""
        # Si el campo está vacío, mostrar todos los registros
        if not self.texto_busqueda_actual:
            for i in range(self.tabla.rowCount()):
                self.tabla.setRowHidden(i, False)
            return
        
        # Iterar sobre todas las filas de la tabla
        for i in range(self.tabla.rowCount()):
            # Verificar si hay datos en las celdas relevantes
            nombre_item = self.tabla.item(i, 0)
            documento_item = self.tabla.item(i, 1)
            
            if nombre_item and documento_item:
                nombre = nombre_item.text().lower()
                documento = documento_item.text().lower()
                
                # Mostrar fila si el texto de búsqueda está en el nombre o documento
                if self.texto_busqueda_actual in nombre or self.texto_busqueda_actual in documento:
                    self.tabla.setRowHidden(i, False)
                else:
                    self.tabla.setRowHidden(i, True)

    def crear_header_combinado(self):
        # Crear un contenedor combinado para el título y el logo
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['background_header']};")  
        
        # Calcular tamaños para asegurar que coincidan con la interfaz de login
        pantalla = QDesktopWidget().screenGeometry()
        ancho_pantalla = pantalla.width()
        alto_pantalla = pantalla.height()
        alto_logo = int(alto_pantalla * 0.14)
        
        # Establecer altura fija para el header completo
        header.setFixedHeight(alto_logo)
        
        # Crear layout para organizar logo y botones
        layout_header = QHBoxLayout(header)
        layout_header.setContentsMargins(0, 0, 10, 0)
        
        # Área del logo (lado izquierdo)
        if os.path.exists(self.ruta_logo):
            ancho_logo = int(ancho_pantalla * 0.2)
            
            etiqueta_logo = QLabel()
            mapa_pixeles_logo = QPixmap(self.ruta_logo)
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
        
        # Agregar espacio expansible en el medio
        layout_header.addStretch(1)
        
        # Contenedor para los botones de control y el logo de la universidad
        container_right = QWidget()
        layout_right = QVBoxLayout(container_right)
        layout_right.setContentsMargins(0, 0, 0, 0)
        layout_right.setSpacing(5)
        
        # Contenedor para los botones de control
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)
        
        # Agregar botón de menú antes de los botones de control
        self.menu_button = MenuToggleButton(self, self.menu_lateral)
        buttons_layout.addWidget(self.menu_button)
        
        # Botones de control (lado derecho) - sin botón de logout
        botones = [
            ("🗕", self.showMinimized, False),
            ("🗗", self.toggle_maximized, False),
            ("✖", self.close, True)
        ]
        
        for texto, funcion, es_cerrar in botones:
            boton = StyledButton(texto, "window_control", is_close=es_cerrar)
            boton.setFixedSize(30, 30)
            boton.clicked.connect(funcion)
            buttons_layout.addWidget(boton)
        
        # Agregar contenedor de botones al layout derecho
        layout_right.addWidget(buttons_container, 0, Qt.AlignRight | Qt.AlignTop)
        
        # Área del logo universidad (debajo de los botones)
        if hasattr(self, 'ruta_logou') and os.path.exists(self.ruta_logou):
            alto_logo_u = int(alto_pantalla * 0.1)  # Igual que en login_interface.py
            ancho_logo_u = int(ancho_pantalla * 0.15)  # Igual que en login_interface.py
            
            etiqueta_logo_u = QLabel()
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
            
            # Alinear el logo de la universidad a la derecha
            logo_u_container = QWidget()
            logo_u_layout = QHBoxLayout(logo_u_container)
            logo_u_layout.setContentsMargins(0, 0, 0, 0)
            logo_u_layout.addStretch(1)  # Empuja el logo hacia la derecha
            logo_u_layout.addWidget(etiqueta_logo_u)
            
            # Agregar contenedor del logo al layout derecho
            layout_right.addWidget(logo_u_container, 0, Qt.AlignRight)
        
        # Agregar el contenedor derecho al layout principal
        layout_header.addWidget(container_right, 0, Qt.AlignTop)
        
        return header

    def crear_contenedor_tabla(self):
        # Usar el TablaContainer reutilizable con tamaños consistentes
        contenedor_tabla = TablaContainer(self, 0.96, 0.638)
        
        # Crear la tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(self.headers))
        self.tabla.setHorizontalHeaderLabels(self.headers)
        self.tabla.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        
        # Aplicar estilos de tabla directamente como en la versión anterior
        self.tabla.setStyleSheet(TABLE_STYLES_UPDATED["main"] + SCROLLBAR_STYLE)
        
        # Hide row numbers
        self.tabla.verticalHeader().setVisible(False)
        
        # Configure the delegate for colored circles - implementar como en la versión anterior
        circle_delegate = Estado_delegado_circulo(self.tabla)
        estado_columns = ['Triage', 'CI', 'Labs', 'IMG', 'Interconsulta', 'RV']
        for header in estado_columns:
            col_index = self.headers.index(header)
            self.tabla.setItemDelegateForColumn(col_index, circle_delegate)
        
        # Also use circle delegate for Conducta to support alarm visualization
        conducta_index = self.headers.index('Conducta')
        self.tabla.setItemDelegateForColumn(conducta_index, circle_delegate)
        
        # Configure delegate for text cells to show tooltips
        text_delegate = TextDelegate(self.tabla)
        for col in range(self.tabla.columnCount()):
            if col not in [self.headers.index(h) for h in estado_columns] and col != conducta_index:
                self.tabla.setItemDelegateForColumn(col, text_delegate)
        
        # Enable smooth scrolling
        self.tabla.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.tabla.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        
        # Style settings for the table
        self.tabla.setAlternatingRowColors(False)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.clearSelection()
        self.tabla.setCurrentCell(-1, -1)
        
        # Usar la nueva fuente para la tabla
        self.tabla.setFont(QFont("Segoe UI", 10))
        
        # Mejorar el estilo de los encabezados
        header_font = QFont("Segoe UI", 10)
        header_font.setBold(True)
        self.tabla.horizontalHeader().setFont(header_font)
        
        self.tabla.setWordWrap(True)
        
        # Agregar la tabla al contenedor
        contenedor_tabla.set_tabla(self.tabla)
        
        # Conectar evento de cambio de tamaño para mantener los anchos de columna
        self.tabla.horizontalHeader().sectionResized.connect(
            lambda index, oldSize, newSize: QTimer.singleShot(0, self.configurar_anchos_columnas)
        )
        
        return contenedor_tabla

    def closeEvent(self, event):
        """Sobrescribir el evento de cierre para detener el timer"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        # Continuar con el cierre normal sin mostrar pantalla de carga
        super().closeEvent(event)
    
    def configurar_ventana(self): self.setWindowTitle("Gestión de Pacientes"); self.setStyleSheet("background-color: #4A7296;"); self.showMaximized()
    
    def iniciar_actualizacion_periodica(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_tabla)

    def configurar_anchos_columnas(self):
        """Configura los anchos de las columnas de la tabla para asegurar consistencia"""
        # Guardar el modo de ajuste actual de las columnas
        modos_actuales = []
        for col in range(self.tabla.columnCount()):
            modos_actuales.append(self.tabla.horizontalHeader().sectionResizeMode(col))
            
        # Establecer todas las columnas en modo stretch temporalmente
        for col in range(self.tabla.columnCount()):
            self.tabla.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        
        # Actualizar el tamaño de la tabla para que se ajuste correctamente
        self.tabla.updateGeometry()
        self.tabla.viewport().updateGeometry()
        
        # Calcular anchos basados en el tamaño actual de la tabla
        ancho_tabla = self.tabla.width()
        columnas_count = len(self.headers)
        ancho_columna_estandar = ancho_tabla / columnas_count
        
        # Aplicar anchos específicos a columnas seleccionadas
        indice_nombre = self.headers.index('Nombre')
        indice_pendientes = self.headers.index('Pendientes')
        
        # Cambiar al modo fijo para las columnas específicas
        self.tabla.horizontalHeader().setSectionResizeMode(indice_nombre, QHeaderView.Fixed)
        self.tabla.horizontalHeader().setSectionResizeMode(indice_pendientes, QHeaderView.Fixed)
        
        # Establecer anchos específicos
        self.tabla.setColumnWidth(indice_nombre, int(ancho_columna_estandar * 1.3))
        self.tabla.setColumnWidth(indice_pendientes, int(ancho_columna_estandar * 1.5))
        
        # Asegurar que los cambios sean visibles inmediatamente
        self.tabla.horizontalHeader().update()

    def logout(self):
        if self.mostrar_mensaje_confirmacion(
            "Confirmar Cierre de Sesión",
            "¿Está seguro que desea cerrar sesión?"
        ):
            # Eliminamos la animación que estaba causando problemas
            # y llamamos directamente al método para realizar el logout
            self.realizar_logout()

    def realizar_logout(self):
        """Método que se ejecuta después de completar la animación de logout"""
        # Mostrar pantalla de carga durante el cierre de sesión con estilo consistente
        splash = SplashScreen(None, logo_path=self.ruta_logo, message="Cerrando sesión...", duration=1.5)
        splash.setFixedSize(int(self.pantalla.width() * 0.3), int(self.pantalla.height() * 0.3))
        splash.show()
        splash.opacity_animation.start()  # Iniciar animación de fade-in
        QApplication.processEvents()
        
        # Detener el timer antes de cerrar
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        try:
            if hasattr(self.modelo, 'conn') and self.modelo.conn:
                self.modelo.conn.close()
        except Exception as e:
            self.mostrar_mensaje_informacion("Error", f"Error al cerrar la conexión de base de datos: {e}", QMessageBox.Critical)
        
        # Esperar a que termine la pantalla de carga
        splash.exec_()
        
        self.close()
        self.login_interface.reiniciar_login()
            
    def actualizar_tabla(self):
        try:
            # Verificar que la tabla exista antes de intentar usarla
            if not hasattr(self, 'tabla'):
                self.mostrar_mensaje_informacion("Error", "La tabla aún no se ha inicializado", QMessageBox.Critical)
                return
            
            # Si es la primera carga, mostrar una pantalla de carga con estilo consistente
            if self.primera_carga:
                splash = SplashScreen(self, logo_path=self.ruta_logo, message="Cargando datos de pacientes...", duration=1)
                splash.setFixedSize(int(self.pantalla.width() * 0.3), int(self.pantalla.height() * 0.3))
                splash.show()
                splash.opacity_animation.start()  # Asegurar que la animación se inicie
                QApplication.processEvents()
            
            # Obtener datos usando el modelo con filtros aplicados
            if self.filtro_fecha_activo and self.fecha_inicio and self.fecha_fin:
                fecha_inicio_str = self.fecha_inicio.toString("yyyy-MM-dd HH:mm:ss")
                fecha_fin_str = self.fecha_fin.toString("yyyy-MM-dd HH:mm:ss")
                datos = self.modelo.obtener_datos_pacientes_filtrados(
                    self.areas_filtradas, 
                    fecha_inicio_str,
                    fecha_fin_str
                )
            else:
                datos = self.modelo.obtener_datos_pacientes_filtrados(self.areas_filtradas)
            
            self.tabla.setRowCount(0)
            
            # Obtener celdas con alarma desde el modelo
            alarm_cells = self.modelo.verificar_alarmas(datos)
            conducta_alarm_cells = self.modelo.verificar_alarma_conducta(datos)
            indice_triage = self.headers.index('Triage')
            indice_pendientes = self.headers.index('Pendientes')  # Índice de la columna pendientes
            indice_conducta = self.headers.index('Conducta')  # Índice de la columna conducta
            
            if datos:
                for row_idx, fila in enumerate(datos):
                    fila_actual = list(fila[:12])  # Primeros 12 campos para la tabla
                    
                    # Insertar fila en la tabla
                    self.tabla.insertRow(row_idx)
                    for col, valor in enumerate(fila_actual):
                        # Verificar si es una columna que debe usar el delegado especial
                        if col == indice_triage or col == self.headers.index('CI') or \
                           col == self.headers.index('Labs') or col == self.headers.index('IMG') or \
                           col == self.headers.index('Interconsulta') or col == self.headers.index('RV') or \
                           col == self.headers.index('Conducta'):
                            # Usar un ítem personalizado para que funcione con el delegado
                            item = Personalizado_Columnas("", str(valor))
                            self.tabla.setItem(row_idx, col, item)
                            
                            # Centrar específicamente el texto de la columna Conducta
                            if col == indice_conducta:
                                item.setTextAlignment(Qt.AlignCenter)
                        # elif col == indice_pendientes:
                        #     # Para la columna de pendientes, asegurarse de que se muestre exactamente como viene de la BD
                        #     # sin ningún procesamiento adicional
                        #     pendientes_texto = str(valor) if valor is not None else ""
                        #     item = QTableWidgetItem(pendientes_texto)
                        #     item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Alineación a la izquierda para mejor legibilidad
                        #     self.tabla.setItem(row_idx, col, item)
                        else:
                            # Para texto normal
                            item = QTableWidgetItem(str(valor))
                            item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                            self.tabla.setItem(row_idx, col, item)
                
                # Actualizar alarmas en el delegate para CI
                ci_col = self.headers.index('CI')
                delegate = self.tabla.itemDelegateForColumn(ci_col)
                if isinstance(delegate, Estado_delegado_circulo):
                    delegate.set_alarm_cells(alarm_cells)
                
                # Actualizar alarmas de conducta
                conducta_col = self.headers.index('Conducta')
                delegate = self.tabla.itemDelegateForColumn(conducta_col)
                if isinstance(delegate, Estado_delegado_circulo):
                    delegate.set_conducta_alarm_cells(conducta_alarm_cells)
                
                # Aplicar configuración de anchos de columna después de cargar datos
                self.configurar_anchos_columnas()
                
                # Establecer una altura fija para todas las filas basada en el tamaño del círculo
                circle_delegate = self.tabla.itemDelegateForColumn(indice_triage)
                if isinstance(circle_delegate, Estado_delegado_circulo):
                    row_height = circle_delegate.circle_size + 20  # +20 para padding adicional
                    for row in range(self.tabla.rowCount()):
                        self.tabla.setRowHeight(row, row_height)
                
                # Aplicar colores a filas específicas
                for row_idx, fila in enumerate(datos):
                    self.colorear_fila(row_idx, fila)
                
            # Después de actualizar la tabla, volver a aplicar el filtro si hay texto de búsqueda
            if hasattr(self, 'texto_busqueda_actual') and self.texto_busqueda_actual:
                self.aplicar_filtro_busqueda()
                
            # Cerrar la pantalla de carga si es la primera vez
            if self.primera_carga:
                self.primera_carga = False
                if 'splash' in locals():
                    splash.accept()
        except Exception as e:
            self.mostrar_mensaje_informacion("Error", f"Error al actualizar la tabla: {str(e)}", QMessageBox.Critical)
        finally:
            self.modelo.cierre_db()

    def colorear_fila(self, fila, datos):
        columnas_estados = {
            'Triage': self.headers.index('Triage'),
            'CI': self.headers.index('CI'),
            'Labs': self.headers.index('Labs'),
            'IMG': self.headers.index('IMG'),  # Corregido de 'IX' a 'IMG'
            'Interconsulta': self.headers.index('Interconsulta'),
            'RV': self.headers.index('RV')
        }
        
        for campo, indice in columnas_estados.items():
            try:
                valor = datos[indice]
                custom_item = Personalizado_Columnas("", valor)
                self.tabla.setItem(fila, indice, custom_item)
            except Exception as e:
                self.mostrar_mensaje_informacion("Error", f"Error al colorear celda {campo}: {str(e)}", QMessageBox.Critical)

    def hex_to_qcolor(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return QColor(int(hex_color[:2], 16), 
                    int(hex_color[2:4], 16), 
                    int(hex_color[4:], 16))

    def solicitar_documento(self, titulo):
        dialogo = StyledDialog(titulo, 400, self)
        
        # Agregar título y descripción
        dialogo.add_title("Buscar por documento")
        
        descripcion = QLabel("Ingrese el número de documento para buscar el paciente:")
        descripcion.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: {COLORS['background_transparent']};")
        descripcion.setWordWrap(True)
        dialogo.layout.addWidget(descripcion)
        dialogo.layout.addSpacing(10)
        
        # Crear el campo de entrada
        label, entrada = FormField.create_line_edit("", False, False, "")
        entrada.setPlaceholderText("Ingrese número de documento")
        dialogo.layout.addWidget(entrada)
        dialogo.layout.addSpacing(20)
        
        # Botones
        documento = [None]  # Usar una lista como variable mutable para acceder desde las funciones anidadas

        def buscar():
            documento[0] = entrada.text()
            if not documento[0]:
                self.mostrar_mensaje_advertencia("Advertencia", "Debe ingresar un documento")
                return
            dialogo.accept()

        def cancelar():
            dialogo.reject()

        botones = [
            ("Buscar", buscar, "primary"),
            ("Cancelar", cancelar, "danger")
        ]
        
        dialogo.add_button_row(botones)
        
        if dialogo.exec_() == QDialog.Accepted:
            return documento[0]
        return None

    def seleccionar_registro(self, registros, modo="edicion"):
        # Aumentar el ancho de 500 a 800 para eliminar scroll horizontal
        ancho_dialogo = 800
        
        dialogo = StyledDialog(f"Seleccionar Registro para {modo.capitalize()}", ancho_dialogo, self)
        
        # Agregar título y descripción
        dialogo.add_title(f"Seleccionar registro para {modo}")
        
        descripcion = QLabel(f"Se encontraron varios registros. Por favor seleccione el que desea {modo}:")
        descripcion.setStyleSheet(f"""
            color: {COLORS['text_primary']}; 
            background-color: {COLORS['background_transparent']};
            font-size: 15px;
            margin-bottom: 8px;
        """)
        descripcion.setWordWrap(True)
        dialogo.layout.addWidget(descripcion)
        dialogo.layout.addSpacing(10)
        
        # Contenedor para lista con borde
        list_container = QWidget()
        list_container.setStyleSheet(f"""
            background-color: {COLORS['background_white']};
            border: 1px solid {COLORS['border_light']};
            border-radius: {BORDER_RADIUS['medium']};
        """)
        list_container_layout = QVBoxLayout(list_container)
        list_container_layout.setContentsMargins(5, 5, 5, 5)
        
        # Lista de registros con estilo mejorado
        lista = QListWidget()
        lista.setMinimumWidth(ancho_dialogo - 80)
        lista.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['background_white']};
                border: none;
                outline: none;
                padding: 5px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }}
            QListWidget::item {{
                border-radius: 6px;
                padding: 10px;
                margin: 3px 1px;
                border: 1px solid transparent;
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['background_readonly']};
                border: 1px solid {COLORS['border_light']};
            }}
            QListWidget::item:selected {{
                background-color: #E0F0FF;
                border: 1px solid {COLORS['button_primary']};
                color: {COLORS['text_primary']};
            }}
            QScrollBar:vertical {{
                border: none;
                background: #F0F0F0;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: #CCCCCC;
                min-height: 30px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #AAAAAA;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        # Enable smooth scrolling for the list
        lista.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        
        # Asegurarse de que la lista tenga una altura responsiva
        screen_height = QDesktopWidget().availableGeometry().height()
        lista.setMinimumHeight(min(int(screen_height * 0.3), 300))
        
        from datetime import datetime
        
        # Implementación actualizada para manejar tanto strings como objetos datetime
        fecha_ordenada = []
        
        for registro in registros:
            fecha_valor = registro[12]
            
            # Verificar si el valor ya es un datetime
            if isinstance(fecha_valor, datetime):
                fecha_dt = fecha_valor
                fecha_ordenada.append((registro, fecha_dt))
            elif isinstance(fecha_valor, str) and fecha_valor:
                try:
                    fecha_dt = datetime.strptime(fecha_valor, "%Y-%m-%d %H:%M:%S")
                    fecha_ordenada.append((registro, fecha_dt))
                except Exception as e:
                    print(f"No se pudo parsear la fecha (string): {fecha_valor}, Error: {e}")
                    fecha_ordenada.append((registro, datetime.min))
            else:
                print(f"Valor de fecha no reconocido: {type(fecha_valor)}, valor: {fecha_valor}")
                fecha_ordenada.append((registro, datetime.min))
        
        # Ordenar de más reciente a más antiguo
        fecha_ordenada.sort(key=lambda x: x[1], reverse=True)
        
        # Extraer los registros ordenados
        registros_ordenados = [item[0] for item in fecha_ordenada]
        
        # Imprimir información de debug
        for i, (registro, fecha) in enumerate(fecha_ordenada):
            print(f"Registro {i}: {registro[12]} -> {fecha}")
        
        # Mostrar registros en la lista
        for registro in registros_ordenados:
            nombre = registro[0]
            ubicacion = registro[11]
            ingreso = registro[12]
            
            # Mostrar la información como "Nombre - Ubicación - Fecha Ingreso"
            item_text = f"{nombre} - {ubicacion} - {ingreso}"
            item = QListWidgetItem(item_text)
            
            # Asegurar que todos los items tengan el mismo tamaño consistente
            item.setSizeHint(QSize(lista.width() - 20, 50))
            lista.addItem(item)
        
        # Agregar la lista al contenedor
        list_container_layout.addWidget(lista)
        
        # Agregar el contenedor a la ventana de diálogo
        dialogo.layout.addWidget(list_container)
        dialogo.layout.addSpacing(15)
        
        registro_seleccionado = [None]  # Usar lista para acceder desde las funciones anidadas

        def seleccionar():
            if lista.currentRow() >= 0:
                registro_seleccionado[0] = registros_ordenados[lista.currentRow()]  # Usar la lista ordenada
                dialogo.accept()
            else:
                self.mostrar_mensaje_advertencia("Advertencia", "Debe seleccionar un registro")

        def cancelar():
            dialogo.reject()

        botones = [
            ("Seleccionar", seleccionar, "primary"),
            ("Cancelar", cancelar, "danger")
        ]
        
        dialogo.add_button_row(botones)
        
        for i in range(dialogo.button_layout.count()):
            widget = dialogo.button_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setFixedHeight(40)
                widget.setMinimumWidth(120)
        
        # Centrar el diálogo correctamente después de ajustar su tamaño
        dialogo.adjustSize()
        screen = QDesktopWidget().availableGeometry()
        dialog_x = (screen.width() - dialogo.width()) // 2
        dialog_y = (screen.height() - dialogo.height()) // 2
        dialogo.move(dialog_x, dialog_y)
        
        if dialogo.exec_() == QDialog.Accepted:
            return registro_seleccionado[0]
        return None

    def confirmar_eliminacion(self, fila=None):
        documento = self.solicitar_documento("Eliminar paciente")
        if not documento:
            return
                
        registros = self.modelo.obtener_registro_por_documento(documento=documento)
        
        if not registros:
            self.mostrar_mensaje_informacion("Error", "No se encontró ningún paciente con el documento ingresado", QMessageBox.Critical)
            return
        
        if len(registros) > 1:
            registro_seleccionado = self.seleccionar_registro(registros, modo="eliminación")
            if registro_seleccionado:
                nombre_paciente = registro_seleccionado[0]  # El nombre está en el índice 0
                if self.mostrar_mensaje_confirmacion(
                    "Confirmar Eliminación", 
                    f"¿Está seguro de eliminar al paciente {nombre_paciente}?"
                ):
                    self.eliminar_registro(registro_seleccionado)

        else:
            nombre_paciente = registros[0][0]  # El nombre está en el índice 0
            if self.mostrar_mensaje_confirmacion(
                "Confirmar Eliminación", 
                f"¿Está seguro de eliminar al paciente {nombre_paciente}?"
            ):
                self.eliminar_registro(registros[0])

    def eliminar_registro(self, registro):
        """Elimina un registro de paciente de la base de datos y registra la acción en trazabilidad"""
        try:
            id_registro = registro[13]  # ID está en el índice 13
            nombre_paciente = registro[0]  # El nombre está en el índice 0
            
            # Eliminar el registro
            self.modelo.eliminar(id_registro)

            # Actualizar la tabla y mostrar mensaje de éxito
            self.actualizar_tabla()
            self.mostrar_mensaje_informacion("Éxito", f"El paciente {nombre_paciente} ha sido eliminado correctamente.")
            
        except Exception as e:
            self.mostrar_mensaje_informacion("Error", f"Error al eliminar el paciente: {str(e)}", QMessageBox.Critical)
        finally:
            self.modelo.cierre_db()

    def actualizar_ci(self):
        if self.entradas["triage"].currentText() in ["1", "2", "3", "4", "5"]:
            self.entradas["ci"].setCurrentText("No realizado")

    def mostrar_formulario_agregar(self):
        dialogo = StyledDialog("Agregar paciente", 1000, self)  # Increased width for horizontal layout
        
        # Center the dialog properly on screen
        screen = QDesktopWidget().availableGeometry()
        dialog_width = 1000
        dialog_height = int(screen.height() * 0.85)  # Use 85% of screen height
        
        # Calculate centered position
        dialog_x = (screen.width() - dialog_width) // 2
        dialog_y = (screen.height() - dialog_height) // 2
        
        dialogo.setGeometry(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Agregar título
        dialogo.add_title("Agregar nuevo paciente")
        
        # Agregar indicador de campos obligatorios
        dialogo.add_required_fields_indicator()
        
        # Create horizontal layout for main content
        main_content = QWidget()
        main_content.setStyleSheet("background-color: transparent;")
        main_layout = QHBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)  # Space between left and right panels
        
        # Left panel - Form fields
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: transparent;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Create the form layout for basic fields
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: transparent;")
        form_layout = QFormLayout(form_widget)
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(20)
        left_layout.addWidget(form_widget)
        
        # Add consistent styling for form labels
        form_widget.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 500;
                color: {COLORS['text_primary']};
            }}
            QLineEdit, QComboBox {{
                font-size: 15px;
                font-family: 'Segoe UI', sans-serif;
                color: {COLORS['text_primary']};
            }}
        """)
        
        # Campos del formulario básicos
        campos = [
            ("Nombre:", "nombre", True, ""),
            ("Documento:", "documento", True, ""),
            ("Triage:", "triage", False, "", ["", "No realizado", "1", "2", "3", "4", "5"]),
            ("CI:", "ci", False, "", ["", "No realizado", "Realizado"]),
            ("Labs:", "labs", False, "", ["", "No se ha realizado", "En espera de resultados", "Resultados completos"]),
            ("IMG:", "ix", False, "", ["", "No se ha realizado", "En espera de resultados", "Resultados completos"]),
            ("Interconsulta:", "inter", False, "", ["", "No se ha abierto", "Abierta", "Realizada"]),
            ("RV:", "rv", False, "", ["", "Realizado", "No realizado"]),
            ("Pendientes:", "pendientes", False, ""),
            ("Conducta:", "conducta", False, "", ["", "Hospitalización", "Observación", "De Alta"])
        ]
        
        self.entradas = {}
        
        for campo in campos:
            if len(campo) > 4:  # Es un combobox
                label_text, key, es_requerido, valor_inicial, opciones = campo
                label, combo = FormField.create_combo_box(label_text, opciones, es_requerido, valor_inicial)
                self.entradas[key] = combo
                form_layout.addRow(label, combo)
            else:  # Es un LineEdit
                label_text, key, es_requerido, valor_inicial = campo
                label, entrada = FormField.create_line_edit(label_text, es_requerido, False, valor_inicial)
                self.entradas[key] = entrada
                form_layout.addRow(label, entrada)
        
        # Ubicación (área y cubículo)
        label_area, self.combo_area = FormField.create_combo_box("Área:", [""] + list(self.areas.keys()), True)
        form_layout.addRow(label_area, self.combo_area)
        
        label_cubiculo, self.combo_cubiculo = FormField.create_combo_box("Cubículo:", [], True)
        form_layout.addRow(label_cubiculo, self.combo_cubiculo)
        
        # Right panel - Lab selector with improved width
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: transparent;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # Mejorar el estilo y responsividad del selector de labs
        labs_title = QLabel("Selección de Laboratorios")
        labs_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: bold;
            padding: 5px 0;
        """)
        right_layout.addWidget(labs_title)
        
        self.labs_selector = LabsSelector(dialogo, self.ruta_base)
        # Asegurar que el selector de labs tenga una altura proporcional a la pantalla
        screen_height = QDesktopWidget().availableGeometry().height()
        self.labs_selector.setMinimumHeight(int(screen_height * 0.25))  # Reducir altura para dar espacio a ix_selector
        right_layout.addWidget(self.labs_selector)
        
        # Agregar el selector de imágenes debajo del selector de laboratorios
        ix_title = QLabel("Selección de Imágenes")
        ix_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: bold;
            padding: 5px 0;
            margin-top: 10px;
        """)
        right_layout.addWidget(ix_title)
        
        self.ix_selector = IxsSelector(dialogo, self.ruta_base)
        # Asegurar que el selector de ix tenga una altura proporcional a la pantalla
        self.ix_selector.setMinimumHeight(int(screen_height * 0.25))
        right_layout.addWidget(self.ix_selector)
        
        # Distribuir el espacio equitativamente
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)
        
        # Add main content to dialog layout
        dialogo.layout.addWidget(main_content)
        
        # Conectar eventos
        self.entradas["triage"].currentIndexChanged.connect(self.actualizar_ci)
        self.entradas["triage"].currentIndexChanged.connect(self.marcar_ci_no_realizado)
        self.entradas["ci"].currentIndexChanged.connect(self.verificar_ci)
        self.combo_area.currentTextChanged.connect(self.actualizar_cubiculos)
        
        # Botones de acción
        def guardar():
            self.guardar_paciente(dialogo)
            
        botones = [
            ("Guardar", guardar, "primary"),
            ("Cancelar", dialogo.reject, "danger")
        ]
        
        dialogo.add_button_row(botones)
        
        # Asegurar que los botones del diálogo tengan un tamaño consistente
        for i in range(dialogo.button_layout.count()):
            widget = dialogo.button_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setFixedHeight(40)
                widget.setMinimumWidth(120)
        
        # Ejecutar el diálogo
        dialogo.exec_()

    def actualizar_cubiculos(self):
        area = self.combo_area.currentText()
        self.combo_cubiculo.clear()
        if area in self.areas:
            inicio, fin = self.areas[area]
            self.combo_cubiculo.addItems([str(i) for i in range(inicio, fin + 1)])

    def validar_datos_minimos(self, datos):
        # Para pacientes NN, el documento no es obligatorio
        if datos['nombre'].startswith('NN -'):
            return (datos['nombre'] and self.combo_area.currentText() and self.combo_cubiculo.currentText())
        else:
            return (datos['nombre'] and datos['documento'] and 
                    self.combo_area.currentText() and self.combo_cubiculo.currentText())

    def guardar_paciente(self, dialogo):
        try:
            # Recoger datos del formulario
            datos = {k: v.text() if isinstance(v, QLineEdit) else v.currentText() 
                    for k, v in self.entradas.items()}
            
            # Si el nombre está vacío o tiene una sola palabra, preguntar por NN
            nombre = datos['nombre'].strip()
            # Si el triage está vacío, configurarlo como "No realizado"
            if not datos['triage']:
                datos['triage'] = "No realizado"
            
            # Validar y procesar el nombre usando el modelo
            nombre_procesado, es_anonimo, mensaje = self.modelo.procesar_nombre(nombre)
            
            # Si es anónimo (vacío o una sola palabra), confirmar registro como NN
            if es_anonimo:
                if self.mostrar_mensaje_confirmacion(
                    "Paciente Sin Identificación", 
                    f"{mensaje}\n\n¿Desea registrarlo como paciente NN?"
                ):
                    datos['nombre'] = self.modelo.crear_nombre_nn()
                else:
                    return
            else:
                datos['nombre'] = nombre_procesado
            
            # Validar el nombre con el modelo (regla de 3 palabras)
            error_nombre = self.modelo.validar_nombre(datos['nombre'])
            if error_nombre and not datos['nombre'].startswith('NN -'):
                self.mostrar_mensaje_informacion("Error", error_nombre, QMessageBox.Critical)
                return
            
            # Si es NN, el documento no es obligatorio
            if datos['nombre'].startswith('NN -') and not datos['documento']:
                datos['documento'] = f"NN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            ubicacion = f"{self.combo_area.currentText()} - {self.combo_cubiculo.currentText()}"
            
            # Validar datos mínimos
            if not self.validar_datos_minimos(datos):
                self.mostrar_mensaje_informacion(
                    "Error", 
                    "Por favor complete los campos obligatorios: Nombre, Documento, Área y Cubículo", 
                    QMessageBox.Critical
                )
                return
            
            # Validar estado del paciente usando el método del modelo
            validacion_estado = self.modelo.validar_estado_paciente(datos)
            if validacion_estado:
                self.mostrar_mensaje_informacion("Error", validacion_estado, QMessageBox.Critical)
                return

            # Validar la concordancia entre laboratorios seleccionados y el estado de Labs
            laboratorios = [lab[0] for lab in self.labs_selector.get_laboratorios_seleccionados()]
            if (laboratorios and (not datos['labs'] or datos['labs'] not in ["No se ha realizado", "En espera de resultados", "Resultados completos"])):
                self.mostrar_mensaje_informacion(
                    "Error", 
                    "Ha seleccionado laboratorios pero no ha establecido un valor en el campo Labs",
                    QMessageBox.Critical
                )
                return
            if (not laboratorios and datos['labs'] in ["No se ha realizado", "En espera de resultados", "Resultados completos"]):
                self.mostrar_mensaje_informacion(
                    "Error", 
                    "Ha establecido un estado en el campo Labs pero no ha seleccionado ningún laboratorio",
                    QMessageBox.Critical
                )
                return
            
            # Validar la concordancia entre imágenes seleccionadas y el estado de IMG
            imagenes = [ix[0] for ix in self.ix_selector.get_imagenes_seleccionadas()]
            if (imagenes and (not datos['ix'] or datos['ix'] not in ["No se ha realizado", "En espera de resultados", "Resultados completos"])):
                self.mostrar_mensaje_informacion(
                    "Error", 
                    "Ha seleccionado imágenes diagnósticas pero no ha establecido un valor en el campo IMG",
                    QMessageBox.Critical
                )
                return
            if (not imagenes and datos['ix'] in ["No se ha realizado", "En espera de resultados", "Resultados completos"]):
                self.mostrar_mensaje_informacion(
                    "Error", 
                    "Ha establecido un estado en el campo IMG pero no ha seleccionado ninguna imagen diagnóstica",
                    QMessageBox.Critical
                )
                return

            # Verificar si existe un paciente con el mismo documento
            if datos['documento']:  # Solo verificar si hay documento (podría ser NN sin documento)
                paciente_existente_doc = self.modelo.verificar_paciente_mismo_documento(datos['documento'])
                
                if paciente_existente_doc:
                    # Comparar nombres normalizados usando el método del modelo
                    if not self.modelo.comparar_nombres(paciente_existente_doc[0], datos['nombre']):
                        self.mostrar_mensaje_informacion(
                            "Error", 
                            "Ya existe un paciente con diferente nombre asociado a este documento",
                            QMessageBox.Critical
                        )
                        return
                    else:
                        if self.mostrar_mensaje_confirmacion(
                            "Paciente existente",
                            "¿Desea agregar otro registro para este paciente?\nSi selecciona NO, Se dirigirá a la ventana de editar paciente"
                        ):
                            pass  # Continuar con el guardado
                        else:
                            documento = datos['documento']
                            dialogo.close()
                            self.iniciar_edicion_por_boton(documento=documento)
                            return

                # Verificar pacientes con mismo nombre y documento diferente
                todos_pacientes = self.modelo.verificar_paciente_mismo_nombre_diferente_documento()
                
                # Completando el código faltante para verificar pacientes con mismo nombre y documento diferente
                for doc, nombre_db in todos_pacientes:
                    if self.modelo.comparar_nombres(nombre_db, datos['nombre']) and doc != datos['documento']:
                        if not self.mostrar_mensaje_confirmacion(
                            "Advertencia",
                            f"Ya existe un paciente con nombre similar pero documento diferente:\n"
                            f"Nombre: {nombre_db}\nDocumento: {doc}\n\n"
                            f"¿Desea continuar con el registro actual?"
                        ):
                            return

            # Importar el modelo de trazabilidad
            from Back_end.Manejo_DB import ModeloTrazabilidad
                
            # Guardar en la base de datos
            exito, mensaje, paciente_id = self.modelo.datos_guardar_paciente(datos=datos, ubicacion=ubicacion)
            
            if exito and paciente_id:
                # Actualizar timestamps para estados iniciales (que no sean vacíos)
                if datos['triage']:
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'triage', datos['triage'])
                    
                if datos['ci']:
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'ci', datos['ci'])
                    
                if datos['labs']:
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'labs', datos['labs'])
                    
                if datos['ix']:
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'ix', datos['ix'])
                    
                if datos['inter']:
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'inter', datos['inter'])
                    
                if datos['rv']:
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'rv', datos['rv'])
                    
                if datos['conducta']:
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'conducta', datos['conducta'])
                # Actualizar la tabla y mostrar mensaje de éxito
                dialogo.close()
                self.actualizar_tabla()
                self.mostrar_mensaje_informacion("Éxito", f"El paciente {datos['nombre']} ha sido guardado correctamente.")
                
            else:
                self.mostrar_mensaje_informacion("Error", mensaje, QMessageBox.Critical)
                
        except Exception as e:
            self.mostrar_mensaje_informacion("Error", f"Error al guardar: {str(e)}", QMessageBox.Critical)
        finally:
            self.modelo.cierre_db()

    def iniciar_edicion_por_boton(self, documento=None):
        if not documento:
            documento = self.solicitar_documento("Editar paciente")
        if not documento:
            return
                
        registros = self.modelo.obtener_registro_por_documento(documento=documento)
        
        if not registros:
            self.mostrar_mensaje_informacion("Error", "No se encontró ningún paciente con el documento ingresado", QMessageBox.Critical)
            return
        
        if len(registros) > 1:
            registro_seleccionado = self.seleccionar_registro(registros, "edición")
            if registro_seleccionado:
                self.mostrar_formulario_edicion(registro_seleccionado)
        else:
            self.mostrar_formulario_edicion(registros[0])

    def iniciar_edicion_por_menu_contextual(self, fila):
        if fila >= 0:
            documento = self.tabla.item(fila, 1).text()
            
            registros = self.modelo.obtener_registro_por_documento(documento=documento)
            if not registros:
                self.mostrar_mensaje_informacion("Error", "No se encontró ningún paciente con el documento ingresado", QMessageBox.Critical)
                return
                    
            if len(registros) > 1:
                registro_seleccionado = self.seleccionar_registro(registros, "edición")
                if registro_seleccionado:
                    self.mostrar_formulario_edicion(registro_seleccionado)
            else:
                self.mostrar_formulario_edicion(registros[0])

    def mostrar_formulario_edicion(self, registro):
        dialogo = StyledDialog("Editar paciente", 1000, self)  # Increased width from 700 to 1000
        
        # Center the dialog properly on screen
        screen = QDesktopWidget().availableGeometry()
        dialog_width = 1000
        dialog_height = int(screen.height() * 0.85)  # Use 85% of screen height
        
        # Calculate centered position
        dialog_x = (screen.width() - dialog_width) // 2
        dialog_y = (screen.height() - dialog_height) // 2
        
        dialogo.setGeometry(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Agregar título con el nombre del paciente
        dialogo.add_title(f"Editar paciente: {registro[0]}")
        
        # Agregar indicador de campos obligatorios
        dialogo.add_required_fields_indicator()
        
        # Create horizontal layout for main content (like in agregar_paciente)
        main_content = QWidget()
        main_content.setStyleSheet("background-color: transparent;")
        main_layout = QHBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)  # Space between left and right panels
        
        # Left panel - Form fields
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: transparent;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Create the form layout for basic fields
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: transparent;")
        form_layout = QFormLayout(form_widget)
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(20)
        left_layout.addWidget(form_widget)
        
        # Add consistent styling for form labels
        form_widget.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 500;
                color: {COLORS['text_primary']};
            }}
            QLineEdit, QComboBox {{
                font-size: 15px;
                font-family: 'Segoe UI', sans-serif;
                color: {COLORS['text_primary']};
            }}
        """)
        
        # Definición de campos
        campos = [
            ("Nombre:", "nombre", 0, False, False, ""),
            ("Documento:", "documento", 1, False, True, ""),
            ("Triage:", "triage", 2, False, False, "", ["", "No realizado", "1", "2", "3", "4", "5"]),
            ("CI:", "ci", 4, False, False, "", ["", "No realizado", "Realizado"]),
            ("Labs:", "labs", 5, False, False, "", ["", "No se ha realizado", "En espera de resultados", "Resultados completos"]),
            ("IMG:", "ix", 6, False, False, "", ["", "No se ha realizado", "En espera de resultados", "Resultados completos"]),
            ("Interconsulta:", "inter", 7, False, False, "", ["", "No se ha abierto", "Abierta", "Realizada"]),
            ("RV:", "rv", 8, False, False, "", ["", "Realizado", "No realizado"]),
            ("Pendientes:", "pendientes", 9, False, False, ""),
            ("Conducta:", "conducta", 10, False, False, "", ["", "Hospitalización", "Observación", "De Alta"])
        ]
        
        self.entradas = {}
        
        for campo in campos:
            if len(campo) > 6:  # Es un combobox
                label_text, key, index, es_requerido, readonly, valor_inicial, opciones = campo
                valor_actual = registro[index] if registro[index] else ""
                label, combo = FormField.create_combo_box(label_text, opciones, es_requerido, valor_actual)
                self.entradas[key] = combo
                form_layout.addRow(label, combo)
            else:  # Es un LineEdit
                label_text, key, index, es_requerido, readonly, valor_inicial = campo
                valor_actual = registro[index] if registro[index] else ""
                label, entrada = FormField.create_line_edit(label_text, es_requerido, readonly, valor_actual)
                self.entradas[key] = entrada
                form_layout.addRow(label, entrada)
        
        # Ubicación (área y cubículo)
        label_area, self.combo_area = FormField.create_combo_box("Área:", list(self.areas.keys()), True)
        form_layout.addRow(label_area, self.combo_area)
        
        label_cubiculo, self.combo_cubiculo = FormField.create_combo_box("Cubículo:", [], True)
        form_layout.addRow(label_cubiculo, self.combo_cubiculo)
        
        # Right panel - Lab selector with improved width (like in agregar_paciente)
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: transparent;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # Mejorar el estilo y responsividad del selector de labs
        labs_title = QLabel("Selección de Laboratorios")
        labs_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: bold;
            padding: 5px 0;
        """)
        right_layout.addWidget(labs_title)
        
        self.labs_selector = LabsSelector(dialogo, self.ruta_base)
        # Asegurar que el selector de labs tenga una altura proporcional a la pantalla
        screen_height = QDesktopWidget().availableGeometry().height()
        self.labs_selector.setMinimumHeight(int(screen_height * 0.25))  # Reducir altura para dar espacio a ix_selector
        right_layout.addWidget(self.labs_selector)
        
        # Cargar laboratorios del paciente
        paciente_id = registro[13]  # ID en la posición 13
        laboratorios_paciente = self.modelo.obtener_laboratorios_paciente(paciente_id)
        if laboratorios_paciente:
            labs_formateados = [(lab[0], lab[1]) for lab in laboratorios_paciente]
            self.labs_selector.set_laboratorios_seleccionados(labs_formateados)

        # Agregar el selector de imágenes debajo del selector de laboratorios
        ix_title = QLabel("Selección de Imágenes")
        ix_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: bold;
            padding: 5px 0;
            margin-top: 10px;
        """)
        right_layout.addWidget(ix_title)
        
        self.ix_selector = IxsSelector(dialogo, self.ruta_base)
        # Asegurar que el selector de ix tenga una altura proporcional a la pantalla
        self.ix_selector.setMinimumHeight(int(screen_height * 0.25))
        right_layout.addWidget(self.ix_selector)
        
        # Cargar imágenes del paciente
        imagenes_paciente = self.modelo.obtener_imagenes_paciente(paciente_id)
        if imagenes_paciente:
            ix_formateados = [(img[0], img[1]) for img in imagenes_paciente]
            self.ix_selector.set_imagenes_seleccionadas(ix_formateados)
        
        # Distribuir el espacio equitativamente
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)
        
        # Add main content to dialog layout
        dialogo.layout.addWidget(main_content)
        
        # Conectar eventos
        self.entradas["triage"].currentIndexChanged.connect(self.actualizar_ci)
        self.entradas["triage"].currentIndexChanged.connect(self.marcar_ci_no_realizado)
        self.entradas["ci"].currentIndexChanged.connect(self.verificar_ci)
        self.combo_area.currentTextChanged.connect(self.actualizar_cubiculos)
        
        # Separar la ubicación actual en área y cubículo
        ubicacion_actual = registro[11]  # Índice 11: ubicación
        if " - " in ubicacion_actual:
            area_actual, cubiculo_actual = ubicacion_actual.split(" - ")
            self.combo_area.setCurrentText(area_actual)
            self.actualizar_cubiculos()
            self.combo_cubiculo.setCurrentText(cubiculo_actual)
        
        # Botones de acción
        def actualizar():
            self.actualizar_paciente(dialogo, registro)
            
        botones = [
            ("Actualizar", actualizar, "primary"),
            ("Cancelar", dialogo.reject, "danger")
        ]
        
        dialogo.add_button_row(botones)
        
        # Asegurar que los botones del diálogo tengan un tamaño consistente
        for i in range(dialogo.button_layout.count()):
            widget = dialogo.button_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setFixedHeight(40)
                widget.setMinimumWidth(120)
        
        # Ejecutar el diálogo
        dialogo.exec_()

    def marcar_ci_no_realizado(self):
        if self.entradas["triage"].currentText() in ["1", "2", "3", "4", "5"]:
            self.entradas["ci"].setCurrentText("No realizado")

    def verificar_ci(self):
        if self.entradas["ci"].currentText() == "No realizado":
            self.entradas["labs"].setEnabled(False)
            self.entradas["ix"].setEnabled(False)
            self.entradas["inter"].setEnabled(False)
            self.entradas["rv"].setEnabled(False)
        else:
            self.entradas["labs"].setEnabled(True)
            self.entradas["ix"].setEnabled(True)
            self.entradas["inter"].setEnabled(True)
            self.entradas["rv"].setEnabled(True)
        
        # Agregar evento cuando cambia el estado de Labs
        self.entradas["labs"].currentTextChanged.connect(self.actualizar_visibilidad_labs_selector)
        # Agregar evento cuando cambia el estado de IX
        self.entradas["ix"].currentTextChanged.connect(self.actualizar_visibilidad_ix_selector)
        
    def actualizar_visibilidad_labs_selector(self, estado_labs):
        """Actualiza la visibilidad del selector de labs según el estado de Labs"""
        # Si existe el selector de labs y está disponible
        if hasattr(self, 'labs_selector'):
            # Si el estado de Labs es "Resultados completos", deshabilitar selector
            # pero mantenerlo visible para que el usuario pueda ver los labs existentes
            self.labs_selector.setEnabled(estado_labs != "Resultados completos")
            
            # Mostrar un mensaje informativo
            if estado_labs == "Resultados completos":
                # Si el selector tiene su propio método de mostrar mensajes
                if hasattr(self.labs_selector, 'mostrar_error'):
                    self.labs_selector.mostrar_error(
                        "Los laboratorios no se mostrarán como pendientes porque el estado es 'Resultados completos'"
                    )
    
    
    def actualizar_visibilidad_ix_selector(self, estado_ix):
        """Actualiza la visibilidad del selector de imágenes según el estado de IX"""
        # Si existe el selector de imágenes y está disponible
        if hasattr(self, 'ix_selector'):
            # Si el estado de IX es "Resultados completos", deshabilitar selector
            # pero mantenerlo visible para que el usuario pueda ver las imágenes existentes
            self.ix_selector.setEnabled(estado_ix != "Resultados completos")
            
            # Mostrar un mensaje informativo
            if estado_ix == "Resultados completos":
                # Si el selector tiene su propio método de mostrar mensajes
                if hasattr(self.ix_selector, 'mostrar_error'):
                    self.ix_selector.mostrar_error(
                        "Las imágenes no se mostrarán como pendientes porque el estado es 'Resultados completos'"
                    )
    
    def actualizar_paciente(self, dialogo, registro_original):
        try:
            datos = {k: v.text() if isinstance(v, QLineEdit) else v.currentText() 
                    for k, v in self.entradas.items()}
            
            # Si el triage está vacío, establecerlo como "No realizado"
            if not datos['triage']:
                datos['triage'] = "No realizado"
                if hasattr(self, 'entradas') and 'triage' in self.entradas:
                    self.entradas['triage'].setCurrentText("No realizado")
            
            # Validar y procesar el nombre usando el modelo
            nombre = datos['nombre'].strip()
            
            # Procesamiento del nombre para pacientes anónimos
            nombre_procesado, es_anonimo, mensaje = self.modelo.procesar_nombre(nombre)
            
            # Si es anónimo, preguntar si desea registrar como NN
            if es_anonimo:
                if self.mostrar_mensaje_confirmacion(
                    "Nombre incompleto" if nombre else "Nombre vacío", 
                    mensaje
                ):
                    datos['nombre'] = f"NN - {f"NN - {self.modelo.crear_nombre_nn()}"}"
                else:
                    # Si no quiere registrar como NN, no continuar
                    return
            else:
                # Si no es anónimo, aplicar el nombre procesado
                datos['nombre'] = nombre_procesado
            
            # Validar el nombre con el modelo (regla de 3 palabras)
            error_nombre = self.modelo.validar_nombre(datos['nombre'])
            if error_nombre and not datos['nombre'].startswith('NN -'):
                self.mostrar_mensaje_informacion("Error", error_nombre, QMessageBox.Critical)
                return
            
            # Si es NN, el documento no es obligatorio
            if datos['nombre'].startswith('NN -') and not datos['documento']:
                # Generar un "documento" temporal único para NN
                datos['documento'] = f"NN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
            ubicacion = f"{self.combo_area.currentText()} - {self.combo_cubiculo.currentText()}"
            
            # Validar datos mínimos
            if not self.validar_datos_minimos(datos):
                self.mostrar_mensaje_informacion(
                    "Error", 
                    "Por favor complete los campos obligatorios: Nombre, Documento, Área y Cubículo", 
                    QMessageBox.Critical
                )
                return
            
            # Validar estado del paciente usando el método del modelo
            validacion_estado = self.modelo.validar_estado_paciente(datos)
            if validacion_estado:
                self.mostrar_mensaje_informacion("Error", validacion_estado, QMessageBox.Critical)
                return
            
            if (datos['triage'] not in ["1", "2", "3", "4", "5"] or datos['ci'] != "Realizado") and (
                datos['labs'] in ["No se ha realizado", "En espera de resultados", "Resultados completos"] or
                datos['ix'] in ["No se ha realizado", "En espera de resultados", "Resultados completos"] or
                datos['inter'] in ["No se ha abierto", "Abierta", "Realizada"] or
                datos['rv'] in ["Realizado"]
            ):
                self.mostrar_mensaje_informacion(
                    "Error de validación", 
                    "No se pueden actualizar Labs, IMG, Interconsulta o RV hasta que Triage y CI estén realizados.",
                    QMessageBox.Critical
                )
                return
            
            # Obtener laboratorios seleccionados para validación
            nuevos_labs = [lab[0] for lab in self.labs_selector.get_laboratorios_seleccionados()]
            
            # Validar la concordancia entre laboratorios seleccionados y el estado de Labs
            if (nuevos_labs and (not datos['labs'] or datos['labs'] not in ["No se ha realizado", "En espera de resultados", "Resultados completos"])):
                self.mostrar_mensaje_informacion("Error de Validación", 
                    "Debe establecer un estado válido en Labs cuando selecciona laboratorios", QMessageBox.Critical)
                return
            if (not nuevos_labs and datos['labs'] in ["No se ha realizado", "En espera de resultados", "Resultados completos"]):
                self.mostrar_mensaje_informacion("Error de Validación", 
                    "Ha seleccionado un estado para Labs pero no ha agregado ningún laboratorio", QMessageBox.Critical)
                return
            
            # Obtener imágenes seleccionadas para validación
            nuevas_imgs = [ix[0] for ix in self.ix_selector.get_imagenes_seleccionadas()]
            
            # Validar la concordancia entre imágenes seleccionadas y el estado de IMG
            if (nuevas_imgs and (not datos['ix'] or datos['ix'] not in ["No se ha realizado", "En espera de resultados", "Resultados completos"])):
                self.mostrar_mensaje_informacion("Error de Validación", 
                    "Debe establecer un estado válido en IMG cuando selecciona imágenes", QMessageBox.Critical)
                return
            if (not nuevas_imgs and datos['ix'] in ["No se ha realizado", "En espera de resultados", "Resultados completos"]):
                self.mostrar_mensaje_informacion("Error de Validación", 
                    "Ha seleccionado un estado para IMG pero no ha agregado ninguna imagen diagnóstica", QMessageBox.Critical)
                return
            
            # Confirmación antes de actualizar
            nombre_paciente = datos['nombre']
            if not self.mostrar_mensaje_confirmacion(
                "Confirmar Actualización", 
                f"¿Está seguro de actualizar los datos del paciente {nombre_paciente}?"
            ):
                return

            # Actualizar en la base de datos
            exito, mensaje = self.modelo.datos_actualizar_paciente(datos=datos, ubicacion=ubicacion, registro=registro_original)
            
            if exito:
                paciente_id = registro_original[13]  # ID en la posición 13
                
                # Actualizar cada estado con su timestamp correspondiente
                if datos['triage'] != registro_original[2]:  # Si cambió el triage
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'triage', datos['triage'])
                
                if datos['ci'] != registro_original[4]:  # Si cambió CI
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'ci', datos['ci'])
                
                if datos['labs'] != registro_original[5]:  # Si cambió Labs
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'labs', datos['labs'])
                
                if datos['ix'] != registro_original[6]:  # Si cambió IMG (ix)
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'ix', datos['ix'])
                
                if datos['inter'] != registro_original[7]:  # Si cambió Interconsulta
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'inter', datos['inter'])
                
                if datos['rv'] != registro_original[8]:  # Si cambió RV
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'rv', datos['rv'])
                
                if datos['conducta'] != registro_original[10]:  # Si cambió Conducta
                    self.modelo.actualizar_estado_con_timestamp(paciente_id, 'conducta', datos['conducta'])
                
                # Obtener laboratorios originales
                labs_actuales = self.modelo.obtener_laboratorios_paciente(paciente_id)
                labs_actuales_codigos = [lab[0] for lab in labs_actuales] if labs_actuales else []
                
                # Comprobar si los laboratorios han cambiado
                labs_cambiados = set(nuevos_labs) != set(labs_actuales_codigos)
                
                # Solo guardar laboratorios si han cambiado o si triage y CI están realizados
                if labs_cambiados:
                    if datos['triage'] in ["1", "2", "3", "4", "5"] and datos['ci'] == "Realizado":
                        labs_exito, labs_mensaje = self.modelo.guardar_laboratorios_paciente(paciente_id, nuevos_labs)
                        if not labs_exito:
                            self.mostrar_mensaje_informacion("Error en laboratorios", labs_mensaje, QMessageBox.Critical)
                    else:
                        # Si triage o CI no están realizados y hay laboratorios nuevos, mostrar mensaje
                        if nuevos_labs:
                            self.mostrar_mensaje_advertencia(
                                "Información",
                                "Los laboratorios no se pueden guardar hasta que el triage y CI estén realizados"
                            )
                
                # Obtener imágenes originales
                imgs_actuales = self.modelo.obtener_imagenes_paciente(paciente_id)
                imgs_actuales_codigos = [img[0] for img in imgs_actuales] if imgs_actuales else []
                
                # Comprobar si las imágenes han cambiado
                imgs_cambiadas = set(nuevas_imgs) != set(imgs_actuales_codigos)
                
                # Solo guardar imágenes si han cambiado o si triage y CI están realizados
                if imgs_cambiadas:
                    if datos['triage'] in ["1", "2", "3", "4", "5"] and datos['ci'] == "Realizado":
                        img_exito, img_mensaje = self.modelo.guardar_imagenes_paciente(paciente_id, nuevas_imgs)
                        if not img_exito:
                            self.mostrar_mensaje_informacion("Error en imágenes", img_mensaje, QMessageBox.Critical)
                    else:
                        # Si triage o CI no están realizados y hay imágenes nuevas, mostrar mensaje
                        if nuevas_imgs:
                            self.mostrar_mensaje_advertencia(
                                "Información",
                                "Las imágenes no se pueden guardar hasta que el triage y CI estén realizados"
                            )
                
                # Actualizar todos los pendientes según los diferentes estados
                self.modelo.actualizar_pendientes_segun_triage(paciente_id, datos['triage'])
                self.modelo.actualizar_pendientes_segun_ci(paciente_id, datos['ci'])
                self.modelo.actualizar_pendientes_segun_labs(paciente_id, datos['labs'])
                self.modelo.actualizar_pendientes_segun_ix(paciente_id, datos['ix'])
                self.modelo.actualizar_pendientes_segun_inter(paciente_id, datos['inter'])
                self.modelo.actualizar_pendientes_segun_rv(paciente_id, datos['rv'])
                
                dialogo.close()
                self.actualizar_tabla()
                self.mostrar_mensaje_informacion("Éxito", "Paciente actualizado correctamente")
            else:
                self.mostrar_mensaje_informacion("Error", mensaje, QMessageBox.Critical)
        except Exception as e:
            self.mostrar_mensaje_informacion("Error", f"Error al actualizar: {str(e)}", QMessageBox.Critical)
        finally:
            self.modelo.cierre_db()

    def mostrar_mensaje_confirmacion(self, titulo, mensaje, icon=QMessageBox.Question):
        """Muestra un mensaje de confirmación estilizado"""
        msg_box = StyledMessageBox(self, titulo, mensaje, icon, "confirmation")
        
        # Crear botones estilizados
        btn_si = QPushButton("Sí")
        btn_no = QPushButton("No")
        
        # Estilizar los botones si es necesario
        btn_si.setCursor(Qt.PointingHandCursor)
        btn_no.setCursor(Qt.PointingHandCursor)
        
        msg_box.addButton(btn_si, QMessageBox.YesRole)
        msg_box.addButton(btn_no, QMessageBox.NoRole)
        
        # Establecer botón predeterminado
        msg_box.setDefaultButton(btn_no)
        
        # Ejecutar cuadro de diálogo
        resultado = msg_box.exec_()
        
        # Devolver True si se presionó "Sí", False en caso contrario
        return msg_box.clickedButton() == btn_si

    def mostrar_mensaje_informacion(self, titulo, mensaje, icon=QMessageBox.Information):
        """Muestra un mensaje informativo estilizado"""
        # Determinar el tipo de estilo según el ícono
        style_type = "error" if icon == QMessageBox.Critical else "info"
        
        msg_box = StyledMessageBox(self, titulo, mensaje, icon, style_type)
        
        # Crear botón OK estilizado
        btn_ok = QPushButton("Aceptar")
        btn_ok.setCursor(Qt.PointingHandCursor)
        
        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
        
        # Establecer botón predeterminado
        msg_box.setDefaultButton(btn_ok)
        
        # Ejecutar cuadro de diálogo
        return msg_box.exec_()

    def mostrar_mensaje_advertencia(self, titulo, mensaje):
        """Muestra un mensaje de advertencia estilizado"""
        msg_box = StyledMessageBox(self, titulo, mensaje, QMessageBox.Warning, "warning")
        
        # Crear botón OK estilizado
        btn_ok = QPushButton("Aceptar")
        btn_ok.setCursor(Qt.PointingHandCursor)
        
        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
        
        # Establecer botón predeterminado
        msg_box.setDefaultButton(btn_ok)
        
        # Ejecutar cuadro de diálogo
        return msg_box.exec_()

    def mostrar_menu_contextual(self, posicion):
        fila = self.tabla.rowAt(posicion.y())
        if fila >= 0:
            menu = QMenu(self)
            menu.setStyleSheet(MENU_STYLES["main"])
            
            editar_accion = menu.addAction("Editar")
            eliminar_accion = menu.addAction("Eliminar")
            
            # Obtener posición global para el menú
            posicion_global = self.tabla.mapToGlobal(posicion)
            # Ejecutar menú y obtener acción seleccionada
            accion = menu.exec_(posicion_global)
            
            if accion == editar_accion:
                self.iniciar_edicion_por_menu_contextual(fila)
            elif accion == eliminar_accion:
                documento = self.tabla.item(fila, 1).text()
                
                registros = self.modelo.obtener_registro_por_documento(documento=documento)
                if len(registros) > 1:
                    registro_seleccionado = self.seleccionar_registro(registros, "eliminación")
                    if registro_seleccionado:
                        nombre_paciente = registro_seleccionado[0]  # El nombre está en el índice 0
                        
                        if self.mostrar_mensaje_confirmacion(
                            "Confirmar Eliminación", 
                            f"¿Está seguro de eliminar al paciente {nombre_paciente}?"
                        ):
                            self.eliminar_registro(registro_seleccionado)
                else:
                    nombre_paciente = registros[0][0]  # El nombre está en el índice 0
                    if self.mostrar_mensaje_confirmacion(
                        "Confirmar Eliminación", 
                        f"¿Está seguro de eliminar al paciente {nombre_paciente}?"
                    ):
                        self.eliminar_registro(registros[0])

    def ajustar_color(self, color, brighter=False):
        """Ajusta el color para el efecto hover"""
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

    def toggle_maximized(self):
        """Alterna entre modo maximizado y normal para la ventana."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mostrar_selector_edicion(self):
        """Muestra una ventana para seleccionar un paciente para editar"""
        documento = self.solicitar_documento("Editar paciente")
        if not documento:
            return
        
        self.iniciar_edicion_por_boton(documento=documento)

    def configurar_menu_lateral(self):
        """Configura las opciones del menú lateral"""
        # Obtener rutas de íconos
        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        ruta_icono_add = os.path.join(ruta_imagenes, "add_icon.png")
        ruta_icono_edit = os.path.join(ruta_imagenes, "edit_icon.png")
        ruta_icono_delete = os.path.join(ruta_imagenes, "delete_icon.png")
        ruta_icono_logout = os.path.join(ruta_imagenes, "logout_icon.png")
        ruta_icono_filtro = os.path.join(ruta_imagenes, "filtrar.png")
        ruta_icono_adminusers = os.path.join(ruta_imagenes, "adminusers.png")
        ruta_icono_adduser = os.path.join(ruta_imagenes, "agregar.png")
        ruta_icono_trace = os.path.join(ruta_imagenes, "trace.png")
        ruta_icono_reportes = os.path.join(ruta_imagenes, "reportes.png")
        
        # Añadir botones al menú lateral con sus respectivos iconos
        self.menu_lateral.add_menu_button("Agregar paciente", 
                                         ruta_icono_add if os.path.exists(ruta_icono_add) else None, 
                                         self.mostrar_formulario_agregar)
        
        self.menu_lateral.add_menu_button("Editar paciente", 
                                         ruta_icono_edit if os.path.exists(ruta_icono_edit) else None, 
                                         self.mostrar_selector_edicion)
        
        self.menu_lateral.add_menu_button("Eliminar paciente", 
                                         ruta_icono_delete if os.path.exists(ruta_icono_delete) else None, 
                                         self.confirmar_eliminacion)
        
        # Añadir botón de filtrado
        self.menu_lateral.add_menu_button("Filtrar", 
                                        ruta_icono_filtro if os.path.exists(ruta_icono_filtro) else None, 
                                        self.mostrar_dialog_filtrado)
        
        # Añadir botón de administración de usuarios
        self.menu_lateral.add_menu_button("Administrar usuarios", 
                                        ruta_icono_adminusers if os.path.exists(ruta_icono_adminusers) else None, 
                                        self.mostrar_editor_privilegios)
        
        # Añadir botón de administración de usuarios
        self.menu_lateral.add_menu_button("Crear usuario", 
                                        ruta_icono_adduser if os.path.exists(ruta_icono_adduser) else None, 
                                        self.mostrar_registro_usuario)

        # Añadir botón de trazabilidad
        self.menu_lateral.add_menu_button("Trazabilidad", 
                                        ruta_icono_trace if os.path.exists(ruta_icono_trace) else None, 
                                        self.mostrar_trazabilidad)
        
        # Añadir botón de reportes
        self.menu_lateral.add_menu_button("Generar reportes", 
                                        ruta_icono_reportes if os.path.exists(ruta_icono_reportes) else None, 
                                        self.mostrar_generador_reportes)

        # Agregar espacio entre los botones y el botón de cerrar sesión
        self.menu_lateral.add_spacer()
        
        # Botón de cerrar sesión al final
        self.menu_lateral.add_menu_button("Cerrar sesión", 
                                         ruta_icono_logout if os.path.exists(ruta_icono_logout) else None, 
                                         self.logout, 
                                         "danger")
        
        # Asegurar que el menú esté por encima de otros widgets
        self.menu_lateral.raise_()
        
        # Inicialmente oculto
        self.menu_lateral.hide()
    
    def resizeEvent(self, event):
        """Maneja el evento de cambio de tamaño de la ventana"""
        # Llamar al método de la clase base
        super().resizeEvent(event)
        
        # Actualizar menú lateral para que sea responsivo
        if hasattr(self, 'menu_lateral'):
            self.menu_lateral.adjust_for_screen_size()
        
        # Actualizar la ubicación del menú lateral
        if hasattr(self, 'menu_lateral') and self.menu_lateral.is_open:
            self.menu_lateral.setGeometry(
                self.width() - self.menu_lateral.width,
                0,
                self.menu_lateral.width,
                self.height()
            )
        elif hasattr(self, 'menu_lateral'):
            self.menu_lateral.setGeometry(
                self.width(),
                0,
                self.menu_lateral.width,
                self.height()
            )
            
    def mostrar_dialog_filtrado(self):
        """Muestra el diálogo para filtrar por áreas y rango de fechas"""
        dialogo = DialogoFiltrar(self, self.areas, self.areas_filtradas, 
                                self.filtro_fecha_activo, self.fecha_inicio, self.fecha_fin)
        if dialogo.exec_() == QDialog.Accepted:
            # Obtener áreas seleccionadas del diálogo
            nuevos_filtros = dialogo.obtener_areas_seleccionadas()
            
            # Si no se selecciona ningún área, usar todas por defecto
            if not nuevos_filtros:
                nuevos_filtros = list(self.areas.keys())
            
            # Actualizar los filtros locales
            self.areas_filtradas = nuevos_filtros
            
            # Actualizar filtros de fecha
            self.filtro_fecha_activo = dialogo.filtro_fecha_activo
            if self.filtro_fecha_activo:
                self.fecha_inicio = dialogo.fecha_inicio
                self.fecha_fin = dialogo.fecha_fin
            else:
                self.fecha_inicio = None
                self.fecha_fin = None
            
            # Guardar preferencias de áreas
            from Back_end.Usuarios.ModeloPreferencias import ModeloPreferencias
            
            # Intentar guardar preferencias
            exito = ModeloPreferencias.guardar_preferencias_filtros(
                self.usuario_actual,
                self.areas_filtradas
            )
            
            if not exito:
                self.mostrar_mensaje_informacion(
                    "Preferencias no persistentes", 
                    "No se pudieron guardar las preferencias de filtros de forma permanente. "
                    "Las preferencias se mantendrán durante esta sesión únicamente.",
                    QMessageBox.Warning
                )
            
            # Actualizar la tabla con los nuevos filtros
            self.actualizar_tabla()

    def mostrar_editor_privilegios(self):
        """Muestra la ventana de edición de privilegios de usuarios"""
        dialogo = StyledDialog("Administración de usuarios", 1200, self)
        
        # Center the dialog properly on screen
        screen = QDesktopWidget().availableGeometry()
        dialog_width = int(screen.height() * 1.4)
        dialog_height = int(screen.height() * 0.8)  # Use 80% of screen height
        
        # Calculate centered position
        dialog_x = (screen.width() - dialog_width) // 2
        dialog_y = (screen.height() - dialog_height) // 2
        
        dialogo.setGeometry(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Crear un contenedor para el encabezado con título y botón cerrar
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(10, 10, 10, 0)
        
        # Agregar título centrado
        titulo = QLabel("Administrar usuarios")
        titulo.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 24px;
            font-weight: bold;
            background-color: transparent;
        """)
        titulo.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Crear botón de cerrar consistente con el resto de la aplicación
        boton_cerrar = StyledButton("✖", "window_control", is_close=True)
        boton_cerrar.setFixedSize(15, 40)  # Reducido de 40px a 20px de altura
        boton_cerrar.clicked.connect(dialogo.reject)
        
        # Añadir elementos al layout del header
        # Eliminar el stretch inicial para que el título quede a la izquierda
        header_layout.addWidget(titulo, 0, Qt.AlignLeft | Qt.AlignTop)
        header_layout.addStretch(1)
        header_layout.addWidget(boton_cerrar, 0, Qt.AlignRight | Qt.AlignTop)
        #Hacer transparente el fondo del contenedor del header
        header_container.setStyleSheet("background-color: transparent;")
        
        # Añadir el header al layout del diálogo
        dialogo.layout.addWidget(header_container) # Posicionar en la esquina superior derecha
        
        # Crear contenedor para filtros y búsqueda
        filtros_container = QWidget()
        filtros_layout = QHBoxLayout(filtros_container)
        filtros_layout.setContentsMargins(0, 0, 0, 10)
        
        # Contenedor para el campo de búsqueda
        busqueda_container = QWidget()
        busqueda_layout = QHBoxLayout(busqueda_container)
        busqueda_layout.setContentsMargins(0, 0, 0, 0)
        
        # Icono de búsqueda (lupa)
        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        ruta_icono_busqueda = os.path.join(ruta_imagenes, "search.png")
        
        if os.path.exists(ruta_icono_busqueda):
            icono_busqueda = QLabel()
            pixmap = QPixmap(ruta_icono_busqueda).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icono_busqueda.setPixmap(pixmap)
            icono_busqueda.setStyleSheet("background-color: transparent; margin-right: 5px;")
            busqueda_layout.addWidget(icono_busqueda)
        
        # Campo de búsqueda
        self.usuario_busqueda = QLineEdit()
        self.usuario_busqueda.setPlaceholderText("Digite para buscar")
        self.usuario_busqueda.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLORS['border_light']};
                border-radius: 5px;
                padding: 8px;
                background-color: {COLORS['background_white']};
                min-width: 250px;
                font-family: 'Segoe UI';
                font-size: 10pt;
            }}
        """)
        self.usuario_busqueda.textChanged.connect(self.filtrar_usuarios)
        busqueda_layout.addWidget(self.usuario_busqueda)
        
        # Menú desplegable para filtrar por rol
        filtro_label = QLabel("Filtrar por rol:")
        # El tamaño de letra es igual al de la tabla
        filtro_font = QFont("Segoe UI", 10)
        filtro_label.setFont(filtro_font)
        filtro_label.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: transparent;")
        
        self.combo_filtro_rol = QComboBox()
        self.combo_filtro_rol.addItems(["Todos", "Administrador", "Médico", "Visitante"])
        self.combo_filtro_rol.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLORS['border_light']};
                border-radius: 5px;
                padding: 8px;
                background-color: {COLORS['background_white']};
                min-width: 150px;
                color: {COLORS['text_primary']};
                font-family: 'Segoe UI';
                font-size: 10pt;
            }}
            QComboBox:hover {{
                background-color: {COLORS['background_readonly']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['button_primary']};
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {COLORS['border_light']};
                border-radius: 5px;
                background-color: {COLORS['background_white']};
                selection-background-color: {COLORS['background_readonly']};
                selection-color: {COLORS['text_primary']};
            }}
            QComboBox::item:selected {{
                color: {COLORS['text_primary']};
            }}
        """)
        self.combo_filtro_rol.currentIndexChanged.connect(self.filtrar_usuarios)
        
        # Agregar elementos al contenedor de filtros
        filtros_layout.addWidget(busqueda_container)
        filtros_layout.addStretch()
        filtros_layout.addWidget(filtro_label)
        filtros_layout.addWidget(self.combo_filtro_rol)
        
        # Hacer transparente el fondo del contenedor de filtros
        filtros_container.setStyleSheet("background-color: transparent;")
        dialogo.layout.addWidget(filtros_container)
        
        # Crear tabla de usuarios
        self.tabla_usuarios = QTableWidget()
        self.tabla_usuarios.setColumnCount(6)  # ID, Usuario, Nombre Completo y tres columnas para roles
        self.tabla_usuarios.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla_usuarios.customContextMenuRequested.connect(self.mostrar_menu_contextual_usuarios)
        # Cambio de orden: Usuario ahora va después de Nombre Completo
        self.tabla_usuarios.setHorizontalHeaderLabels(["ID", "Usuario", "Nombre Completo", "Administrador", "Médico", "Visitante"])
        # Centrar el texto de la columna Nombre Completo
        self.tabla_usuarios.horizontalHeaderItem(2).setTextAlignment(Qt.AlignCenter)
        # Estilo para la tabla
        self.tabla_usuarios.setStyleSheet(TABLE_STYLES_UPDATED["main"] + SCROLLBAR_STYLE)
        self.tabla_usuarios.verticalHeader().setVisible(False)
        self.tabla_usuarios.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_usuarios.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_usuarios.setAlternatingRowColors(False)
        
        # Habilitar word wrap para toda la tabla
        self.tabla_usuarios.setWordWrap(True)
        
        # Hacer que la tabla ocupe todo el ancho disponible
        self.tabla_usuarios.horizontalHeader().setStretchLastSection(False)
        
        self.tabla_usuarios.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID más pequeño
        self.tabla_usuarios.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)  # Usuario - ancho fijo
        self.tabla_usuarios.setColumnWidth(1, 150)
        self.tabla_usuarios.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Nombre Completo - ocupa espacio disponible
        
        # Columnas de roles con ancho fijo
        for i in range(3, 6):
            self.tabla_usuarios.horizontalHeader().setSectionResizeMode(i, QHeaderView.Fixed)
            self.tabla_usuarios.setColumnWidth(i, 140)
        
        # Fuente para la tabla
        self.tabla_usuarios.setFont(QFont("Segoe UI", 10))
        
        # Estilo para el encabezado
        header_font = QFont("Segoe UI", 10)
        header_font.setBold(True)
        self.tabla_usuarios.horizontalHeader().setFont(header_font)
        
        # Agregar la tabla al diálogo
        dialogo.layout.addWidget(self.tabla_usuarios, 1)  # 1 es el stretch factor
        
        # Cargar datos de usuarios
        self.cargar_usuarios()
        
        # Mostrar el diálogo
        dialogo.exec_()

    def mostrar_menu_contextual_usuarios(self, posicion):
        """Muestra menú contextual para la tabla de usuarios"""
        fila = self.tabla_usuarios.rowAt(posicion.y())
        if fila >= 0:
            menu = QMenu(self)
            menu.setStyleSheet(MENU_STYLES["main"])
            
            # Verificar si el usuario está activo o inactivo
            estado_item = self.tabla_usuarios.item(fila, 1)  # Columna del usuario
            nombre_usuario = estado_item.text() if estado_item else ""
            
            cambiar_password_accion = menu.addAction("Cambiar contraseña")
            inactivar_accion = menu.addAction("Inactivar usuario")
            
            # Obtener posición global para el menú
            posicion_global = self.tabla_usuarios.mapToGlobal(posicion)
            
            # Ejecutar menú y obtener acción seleccionada
            accion = menu.exec_(posicion_global)
            
            if accion == cambiar_password_accion:
                self.mostrar_cambio_password(fila)
            elif accion == inactivar_accion:
                self.inactivar_usuario(fila)

    def inactivar_usuario(self, fila):
        """Marca un usuario como inactivo en la base de datos"""
        # Obtener el nombre de usuario
        nombre_usuario = self.tabla_usuarios.item(fila, 1).text()
        nombre_completo = self.tabla_usuarios.item(fila, 2).text() if self.tabla_usuarios.item(fila, 2) else nombre_usuario
        
        # Confirmar antes de inactivar
        if self.mostrar_mensaje_confirmacion(
            "Confirmar Inactivación",
            f"¿Está seguro que desea inactivar al usuario {nombre_usuario}?"
        ):
            try:
                # Inactivar usuario
                from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
                exito, mensaje = ModeloUsuarios.inactivar_usuario(nombre_usuario)
                
                if exito:
                    # Registrar en trazabilidad
                    from Back_end.Manejo_DB import ModeloTrazabilidad
                    detalles = f"Usuario inactivado: {nombre_usuario} | Nombre completo: {nombre_completo}"
                    ModeloTrazabilidad.registrar_accion(
                        accion="Inactivar usuario",
                        paciente_afectado=None,
                        detalles_cambio=detalles
                    )
                    
                    # Mostrar mensaje y recargar la tabla
                    self.mostrar_mensaje_informacion("Éxito", f"El usuario {nombre_usuario} ha sido inactivado correctamente.")
                    self.cargar_usuarios()
                else:
                    self.mostrar_mensaje_informacion("Error", mensaje, QMessageBox.Critical)
            except Exception as e:
                self.mostrar_mensaje_informacion("Error", f"Error al inactivar usuario: {str(e)}", QMessageBox.Critical)

    def mostrar_cambio_password(self, fila):
        """Muestra un diálogo para cambiar la contraseña de un usuario"""
        # Obtener el nombre de usuario
        nombre_usuario = self.tabla_usuarios.item(fila, 1).text()
        nombre_completo = self.tabla_usuarios.item(fila, 2).text() if self.tabla_usuarios.item(fila, 2) else nombre_usuario
        
        # Crear diálogo para cambio de password
        dialogo = StyledDialog(f"Cambiar contraseña", 500, self)
        
        # Agregar título y descripción
        dialogo.add_title(f"Cambiar contraseña: {nombre_usuario}")
        
        descripcion = QLabel(f"Ingrese una nueva contraseña para el usuario {nombre_usuario}:")
        descripcion.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: {COLORS['background_transparent']};")
        descripcion.setWordWrap(True)
        dialogo.layout.addWidget(descripcion)
        dialogo.layout.addSpacing(15)
        
        # Contenedor para campos de contraseña
        password_container = QWidget()
        password_container.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        password_layout = QVBoxLayout(password_container)
        password_layout.setContentsMargins(10, 10, 10, 10)
        
        # Reutilizar componentes de contraseña del registro de usuario
        from Front_end.styles.user_components import PasswordInputWithToggle, PasswordStrengthWidget, RequirementList
        
        # Campo de contraseña
        password_label = QLabel("Nueva contraseña:")
        password_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        password_layout.addWidget(password_label)
        
        # Contenedor para el ícono y el campo
        password_input_container = QWidget()
        password_input_layout = QHBoxLayout(password_input_container)
        password_input_layout.setContentsMargins(0, 0, 0, 0)
        password_input_layout.setSpacing(10)
        
        # Icono de candado
        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        ruta_icono_candado = os.path.join(ruta_imagenes, "candado.png")
        
        if os.path.exists(ruta_icono_candado):
            password_icon = QLabel()
            password_pixmap = QPixmap(ruta_icono_candado).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            password_icon.setPixmap(password_pixmap)
            password_icon.setFixedSize(40, 40)
            password_icon.setAlignment(Qt.AlignCenter)
            password_input_layout.addWidget(password_icon)
        
        # Campo de contraseña con toggle
        entrada_password = PasswordInputWithToggle("Ingrese nueva contraseña")
        password_input_layout.addWidget(entrada_password)
        
        # Aplicar estilo al contenedor
        password_input_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px;
            }}
        """)
        
        password_layout.addWidget(password_input_container)
        
        # Widget de fortaleza
        strength_widget = PasswordStrengthWidget()
        password_layout.addWidget(strength_widget)
        
        # Requisitos de contraseña
        password_requirements = RequirementList(parent=dialogo)
        password_requirements.setStyleSheet("font-size: 13px;")
        password_requirements.add_requirement("Al menos 8 caracteres")
        password_requirements.add_requirement("Al menos una letra mayúscula")
        password_requirements.add_requirement("Al menos una letra minúscula")
        password_requirements.add_requirement("Al menos un número")
        password_requirements.add_requirement("Al menos un carácter especial")
        password_layout.addWidget(password_requirements)
        password_layout.addSpacing(15)
        
        # Campo de confirmación de contraseña
        confirm_label = QLabel("Confirmar contraseña:")
        confirm_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        password_layout.addWidget(confirm_label)
        
        # Contenedor para el ícono y el campo de confirmación
        confirm_input_container = QWidget()
        confirm_input_layout = QHBoxLayout(confirm_input_container)
        confirm_input_layout.setContentsMargins(0, 0, 0, 0)
        confirm_input_layout.setSpacing(10)
        
        # Icono de candado para confirmación
        if os.path.exists(ruta_icono_candado):
            confirm_icon = QLabel()
            confirm_icon.setPixmap(password_pixmap)
            confirm_icon.setFixedSize(40, 40)
            confirm_icon.setAlignment(Qt.AlignCenter)
            confirm_input_layout.addWidget(confirm_icon)
        
        # Campo de confirmación
        entrada_confirm = PasswordInputWithToggle("Confirme la nueva contraseña")
        confirm_input_layout.addWidget(entrada_confirm)
        
        # Aplicar estilo al contenedor de confirmación
        confirm_input_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px;
            }}
        """)
        
        password_layout.addWidget(confirm_input_container)
        
        # Feedback para coincidencia
        feedback_password = QLabel("")
        feedback_password.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
        feedback_password.setVisible(False)
        password_layout.addWidget(feedback_password)
        
        dialogo.layout.addWidget(password_container)
        
        # Función de validación en tiempo real
        def actualizar_fortaleza():
            password = entrada_password.text()
            strength_widget.update_strength(password)
            
            # Actualizar indicadores de requisitos
            password_requirements.update_requirement(0, len(password) >= 8)
            password_requirements.update_requirement(1, any(c.isupper() for c in password))
            password_requirements.update_requirement(2, any(c.islower() for c in password))
            password_requirements.update_requirement(3, any(c.isdigit() for c in password))
            password_requirements.update_requirement(4, any(not c.isalnum() for c in password))
            
            # Si hay texto en confirmación, validar coincidencia
            if entrada_confirm.text():
                validar_coincidencia()
        
        def validar_coincidencia():
            password = entrada_password.text()
            confirm = entrada_confirm.text()
            
            if not confirm:
                feedback_password.setVisible(False)
                return False
                
            if password != confirm:
                feedback_password.setText("Las contraseñas no coinciden")
                feedback_password.setVisible(True)
                return False
                
            # Todo bien, ocultar feedback
            feedback_password.setVisible(False)
            return True
        
        def validar_formulario():
            password = entrada_password.text()
            
            # Verificar que haya contraseña
            if not password:
                feedback_password.setText("La contraseña es obligatoria")
                feedback_password.setVisible(True)
                return False
                
            # Verificar requisitos mínimos
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(not c.isalnum() for c in password)
            
            if len(password) < 8:
                feedback_password.setText("La contraseña debe tener al menos 8 caracteres")
                feedback_password.setVisible(True)
                return False
                
            if not (has_upper and has_lower and has_digit and has_special):
                feedback_password.setText("La contraseña debe tener mayúsculas, minúsculas, números y caracteres especiales")
                feedback_password.setVisible(True)
                return False
                
            # Validar coincidencia
            return validar_coincidencia()
        
        # Conectar eventos para validación en tiempo real
        entrada_password.textChanged(actualizar_fortaleza)
        entrada_confirm.textChanged(validar_coincidencia)
        
        # Función para cambiar contraseña
        def cambiar_password():
            if validar_formulario():
                try:
                    from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
                    exito, mensaje = ModeloUsuarios.cambiar_password(nombre_usuario, entrada_password.text())
                    
                    if exito:
                        dialogo.accept()
                        # Registrar en trazabilidad
                        from Back_end.Manejo_DB import ModeloTrazabilidad
                        detalles = f"Cambio de contraseña para usuario: {nombre_usuario} | Nombre completo: {nombre_completo}"
                        ModeloTrazabilidad.registrar_accion(
                            accion="Cambiar contraseña",
                            paciente_afectado=None,
                            detalles_cambio=detalles
                        )
                        self.mostrar_mensaje_informacion("Éxito", f"La contraseña del usuario {nombre_usuario} ha sido cambiada correctamente.")
                    else:
                        self.mostrar_mensaje_informacion("Error", mensaje, QMessageBox.Critical)
                except Exception as e:
                    self.mostrar_mensaje_informacion("Error", f"Error al cambiar la contraseña: {str(e)}", QMessageBox.Critical)
            else:
                self.mostrar_mensaje_advertencia("Formulario Incompleto", "Por favor corrija los errores en el formulario antes de continuar.")
        
        # Botones
        botones = [
            ("Cambiar", cambiar_password, "primary"),
            ("Cancelar", dialogo.reject, "danger")
        ]
        
        botones_layout = dialogo.add_button_row(botones)
        
        # Aumentar tamaño de los botones
        for i in range(botones_layout.count()):
            widget = botones_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setMinimumHeight(45)
                widget.setStyleSheet(widget.styleSheet() + f"font-size: 16px;")
        
        # Ejecutar diálogo
        dialogo.exec_()

    def filtrar_usuarios(self):
        """Filtra los usuarios en la tabla según el texto de búsqueda y el filtro de rol seleccionado"""
        texto_busqueda = self.usuario_busqueda.text().lower()
        filtro_rol = self.combo_filtro_rol.currentText()
        
        # Recorrer todos los usuarios en la tabla
        for i in range(self.tabla_usuarios.rowCount()):
            # Obtener texto del usuario (ahora en columna 1) y nombre_completo (ahora en columna 2)
            usuario = self.tabla_usuarios.item(i, 1).text().lower() if self.tabla_usuarios.item(i, 1) else ""
            nombre_completo = self.tabla_usuarios.item(i, 2).text().lower() if self.tabla_usuarios.item(i, 2) else ""
            
            # Buscar tanto en nombre de usuario como en nombre completo
            mostrar_fila = texto_busqueda in usuario or texto_busqueda in nombre_completo
            
            # Aplicar filtro por rol si se seleccionó uno específico
            if mostrar_fila and filtro_rol != "Todos":
                if filtro_rol == "Administrador":
                    mostrar_fila = self._tiene_rol_seleccionado(i, 3)
                elif filtro_rol == "Médico":
                    mostrar_fila = self._tiene_rol_seleccionado(i, 4)
                elif filtro_rol == "Visitante":
                    mostrar_fila = self._tiene_rol_seleccionado(i, 5)
                elif filtro_rol == "Sin rol":
                    mostrar_fila = not (self._tiene_rol_seleccionado(i, 3) or 
                                    self._tiene_rol_seleccionado(i, 4) or 
                                    self._tiene_rol_seleccionado(i, 5))
            
            self.tabla_usuarios.setRowHidden(i, not mostrar_fila)
        
    def _tiene_rol_seleccionado(self, fila, columna):
        """Helper para verificar si un rol está seleccionado para una fila"""
        container = self.tabla_usuarios.cellWidget(fila, columna)
        if container:
            checkbox = container.findChild(QCheckBox)
            if checkbox:
                return checkbox.isChecked()
        return False

    def cargar_usuarios(self):
        """Carga los usuarios desde la base de datos y los muestra en la tabla"""
        try:
            print("Iniciando carga de usuarios...")
            # Importar ModeloUsuarios
            from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
            # Obtener lista de usuarios
            usuarios = ModeloUsuarios.obtener_lista_usuarios()
            
            if not usuarios:
                self.mostrar_mensaje_informacion("Información", "No se encontraron usuarios en la base de datos", QMessageBox.Information)
                return
            
            print(f"Se encontraron {len(usuarios)} usuarios en la base de datos.")
            
            # Configurar filas
            self.tabla_usuarios.setRowCount(len(usuarios))
            self.tabla_usuarios.sortItems(0, Qt.AscendingOrder)
            # Estilizar bordes de la tabla
            self.tabla_usuarios.setStyleSheet(TABLE_STYLES_UPDATED["main"] + SCROLLBAR_STYLE)
            # Hacer coincidir el tamaño de letra de la tabla con el resto del diálogo
            self.tabla_usuarios.setFont(QFont("Segoe UI", 10))
            
            # Ruta al icono de check
            ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
            ruta_check = os.path.join(ruta_imagenes, "check.png")
            
            # Crear una clase para manejar los eventos de clic y hacerla accesible para toda la clase
            class ClickableLabel(QLabel):
                def __init__(self, parent, row, col, callback):
                    super().__init__(parent)
                    self.row = row
                    self.col = col
                    self.callback = callback
                    self.setCursor(Qt.PointingHandCursor)  # Cambiar cursor para indicar que es clickeable
                    
                def mousePressEvent(self, event):
                    self.callback(self.row, self.col)
            
            # Guardar la clase como atributo para poder usarla en toggle_rol
            self.ClickableLabel = ClickableLabel
            
            # Definir los colores de los roles
            color_admin = "#4A7296"  # Azul para administradores
            color_medico = "#28a745"  # Verde para médicos
            color_visitante = "#fd7e14"  # Naranja para visitantes
            
            # Llenar la tabla
            for row, usuario_data in enumerate(usuarios):
                usuario_id, nombre, estado, rol = usuario_data
                
                print(f"Procesando usuario {nombre} (ID: {usuario_id}) - Estado: {estado}, Rol: {rol}")
                
                # ID
                id_item = QTableWidgetItem(str(usuario_id))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.tabla_usuarios.setItem(row, 0, id_item)
                
                # Usuario
                usuario_item = QTableWidgetItem(nombre)
                usuario_item.setTextAlignment(Qt.AlignCenter)
                
                # Aplicar color al nombre según el rol principal
                if rol == "admin" and estado == "activo":
                    usuario_item.setForeground(QBrush(QColor(color_admin)))
                    font = usuario_item.font()
                    font.setBold(True)
                    usuario_item.setFont(font)
                    print(f"Usuario {nombre} es administrador, aplicando color azul #{color_admin}")
                elif rol == "medico" and estado == "activo":
                    usuario_item.setForeground(QBrush(QColor(color_medico)))
                    font = usuario_item.font()
                    font.setBold(True)
                    usuario_item.setFont(font)
                    print(f"Usuario {nombre} es médico, aplicando color verde #{color_medico}")
                elif rol == "visitante" and estado == "activo":
                    usuario_item.setForeground(QBrush(QColor(color_visitante)))
                    font = usuario_item.font()
                    font.setBold(True)
                    usuario_item.setFont(font)
                    print(f"Usuario {nombre} es visitante, aplicando color naranja #{color_visitante}")
                
                # Si el usuario está inactivo, mostrar tachado independiente del rol
                if estado != "activo":
                    font = usuario_item.font()
                    font.setStrikeOut(True)
                    font.setBold(True)  # Mantener negrita para consistencia
                    usuario_item.setFont(font)
                    usuario_item.setForeground(QBrush(QColor(COLORS['text_light'])))
                    print(f"Usuario {nombre} está inactivo, aplicando tachado")
                
                # Colocar usuario en la columna 1 (intercambiado con nombre_completo)
                self.tabla_usuarios.setItem(row, 1, usuario_item)
                
                # Agregar columna de nombre completo
                nombre_completo = self.modelo.obtener_nombre_usuario(nombre)
                nombre_completo_item = QTableWidgetItem(nombre_completo)
                nombre_completo_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                nombre_completo_item.setData(Qt.TextWordWrap, True)
                
                # Siempre aplicar negrita al nombre completo
                font_nombre = nombre_completo_item.font()
                font_nombre.setBold(True)
                nombre_completo_item.setFont(font_nombre)
                
                # Aplicar el mismo estilo que tiene el nombre de usuario
                if estado != "activo":
                    font = nombre_completo_item.font()
                    font.setStrikeOut(True)
                    # Aseguramos que mantenemos la negrita
                    font.setBold(True)
                    nombre_completo_item.setFont(font)
                    nombre_completo_item.setForeground(QBrush(QColor(COLORS['text_light'])))
                elif rol == "admin":
                    nombre_completo_item.setForeground(QBrush(QColor(color_admin)))
                elif rol == "medico":
                    nombre_completo_item.setForeground(QBrush(QColor(color_medico)))
                elif rol == "visitante":
                    nombre_completo_item.setForeground(QBrush(QColor(color_visitante)))
                    
                # Colocar nombre_completo en la columna 2 (intercambiado con usuario)
                self.tabla_usuarios.setItem(row, 2, nombre_completo_item)
                
                # Celdas para los roles (columnas 3, 4, 5) - mantener igual
                for col in range(3, 6):
                    # Crear widget contenedor para centrar el checkbox
                    container = QWidget()
                    # Usar un estilo más sutil para los bordes
                    container.setStyleSheet(f"""
                        QWidget {{
                            background-color: {COLORS['background_white']};
                            border: none;
                        }}
                    """)
                    layout = QHBoxLayout(container)
                    layout.setAlignment(Qt.AlignCenter)
                    layout.setContentsMargins(0, 0, 0, 0)
                    
                    # Crear un checkbox pero ocultarlo y usar una imagen en su lugar
                    checkbox = QCheckBox()
                    checkbox.setVisible(False)  # Ocultar el checkbox real
                    
                    # Etiquetar los checkboxes para identificar qué rol representan
                    if col == 3:  # Administrador
                        checkbox.setObjectName(f"admin_{row}")
                        rol_actual = "admin"
                        color_rol = color_admin
                    elif col == 4:  # Médico
                        checkbox.setObjectName(f"medico_{row}")
                        rol_actual = "medico"
                        color_rol = color_medico
                    else:  # Visitante
                        checkbox.setObjectName(f"visitante_{row}")
                        rol_actual = "visitante"
                        color_rol = color_visitante
                    
                    # Comprobar si este usuario tiene este rol
                    is_checked = (rol == rol_actual)
                    checkbox.setChecked(is_checked)
                    
                    # Crear la etiqueta con la imagen del check usando nuestra clase personalizada
                    label = ClickableLabel(None, row, col, self.toggle_rol)
                    
                    # Si el checkbox está marcado, mostrar la imagen de check con el color específico del rol
                    if is_checked and os.path.exists(ruta_check):
                        pixmap = QPixmap(ruta_check)
                        label.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        label.setStyleSheet(f"""
                            QLabel {{
                                background-color: {COLORS['background_white']};
                                border-radius: 5px;
                                padding: 2px;
                                min-width: 24px;
                                min-height: 24px;
                                border: 2px solid {color_rol};
                            }}
                            QLabel:hover {{
                                background-color: {COLORS['background_readonly']};
                            }}
                        """)
                        print(f"Usuario {nombre} tiene rol {rol_actual}, marcando checkbox y aplicando color #{color_rol}")
                    else:
                        # Si no está marcado, mostrar un cuadro vacío con borde suave
                        label.setStyleSheet(f"""
                            QLabel {{
                                background-color: {COLORS['background_white']};
                                border: 1px solid {COLORS['border_light']};
                                border-radius: 5px;
                                min-width: 24px;
                                min-height: 24px;
                            }}
                            QLabel:hover {{
                                border: 1px solid {COLORS['button_primary']};
                                background-color: {COLORS['background_readonly']};
                            }}
                        """)
                    
                    layout.addWidget(label)
                    layout.addWidget(checkbox)  # Añadir checkbox oculto
                    
                    self.tabla_usuarios.setCellWidget(row, col, container)
            
            # Aplicar filtro inicial
            self.filtrar_usuarios()
            
            # Forzar actualización visual completa
            self.tabla_usuarios.update()
            print("Finalizada la carga de usuarios en la tabla")
            
        except Exception as e:
            print(f"Error al cargar usuarios: {str(e)}")
            self.mostrar_mensaje_informacion("Error", f"Error al cargar usuarios: {str(e)}", QMessageBox.Critical)

    def toggle_rol(self, row, col):
        """Cambia el estado de un rol y actualiza los demás roles"""
        try:
            from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
            from Back_end.Manejo_DB import ModeloTrazabilidad
            
            # Obtener el nombre del usuario
            nombre_usuario = self.tabla_usuarios.item(row, 1).text() if self.tabla_usuarios.item(row, 1) else ""
            nombre_completo = self.tabla_usuarios.item(row, 2).text() if self.tabla_usuarios.item(row, 2) else ""
            if not nombre_usuario:
                return

            # Obtener el container y checkbox para la celda actual
            container = self.tabla_usuarios.cellWidget(row, col)
            if not container:
                return
                
            checkbox = container.findChild(QCheckBox)
            if not checkbox:
                return
            
            # Verificar el estado actual del checkbox (antes de cambiarlo)
            estado_actual = checkbox.isChecked()
                
            # Determinar el tipo de privilegio según la columna
            if col == 3:  # Administrador
                tipo_privilegio = "admin"
                nombre_rol = "Administrador"
                rol_color = "#4A7296"  # Color azul para administradores
            elif col == 4:  # Médico
                tipo_privilegio = "crud"
                nombre_rol = "Médico"
                rol_color = "#28a745"  # Color verde para médicos
            else:  # Visitante
                tipo_privilegio = "solo_lectura"
                nombre_rol = "Visitante"
                rol_color = "#fd7e14"  # Color naranja para visitantes

            # Determinar qué acción se va a realizar
            if estado_actual:
                # Si el rol ya está activado, se está intentando desactivar
                mensaje_confirmacion = f"¿Está seguro que desea revocar el rol de {nombre_rol} al usuario {nombre_completo}?\n\nEl usuario será asignado como Visitante automáticamente."
                titulo_confirmacion = f"Revocar rol de {nombre_rol}"
                
                # Si el usuario es administrador y es el último, no permitir desactivación
                if col == 3:  # Si es administrador
                    admin_count = 0
                    for r in range(self.tabla_usuarios.rowCount()):
                        admin_widget = self.tabla_usuarios.cellWidget(r, 3)
                        if admin_widget:
                            admin_checkbox = admin_widget.findChild(QCheckBox)
                            if admin_checkbox and admin_checkbox.isChecked():
                                admin_count += 1
                    
                    if admin_count <= 1:
                        self.mostrar_mensaje_informacion(
                            "Acción no permitida", 
                            "No se puede revocar el rol de Administrador porque es el único administrador en el sistema.",
                            QMessageBox.Warning
                        )
                        return
            else:
                # Si el rol está desactivado, se está intentando activar
                mensaje_confirmacion = f"¿Está seguro que desea asignar el rol de {nombre_rol} al usuario {nombre_completo}?\n\nEsto cambiará su rol actual por {nombre_rol}."
                titulo_confirmacion = f"Asignar rol de {nombre_rol}"
            
            # Mostrar mensaje de confirmación
            if not self.mostrar_mensaje_confirmacion(titulo_confirmacion, mensaje_confirmacion):
                return
            
            # Actualizar la imagen según el nuevo estado
            label = None
            for j in range(container.layout().count()):
                widget = container.layout().itemAt(j).widget()
                if isinstance(widget, self.ClickableLabel):
                    label = widget
                    break
                    
            if not label:
                return
                
            # Ruta para el ícono de check
            ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
            ruta_check = os.path.join(ruta_imagenes, "check.png")
            
            # Encontrar el rol actual del usuario (qué checkbox está marcado)
            rol_actual_col = None
            for c in range(3, 6):
                c_container = self.tabla_usuarios.cellWidget(row, c)
                if c_container:
                    c_checkbox = c_container.findChild(QCheckBox)
                    if c_checkbox and c_checkbox.isChecked():
                        rol_actual_col = c
                        break
            
            # Si se está activando un rol nuevo
            if not estado_actual:
                # Desactivar el rol actual si existe
                if rol_actual_col is not None and rol_actual_col != col:
                    old_container = self.tabla_usuarios.cellWidget(row, rol_actual_col)
                    if old_container:
                        old_checkbox = old_container.findChild(QCheckBox)
                        old_label = None
                        for j in range(old_container.layout().count()):
                            widget = old_container.layout().itemAt(j).widget()
                            if isinstance(widget, self.ClickableLabel):
                                old_label = widget
                                break
                        
                        if old_checkbox:
                            old_checkbox.setChecked(False)
                        
                        if old_label:
                            old_label.clear()
                            old_label.setStyleSheet(f"""
                                QLabel {{
                                    background-color: {COLORS['background_white']};
                                    border: 1px solid {COLORS['border_light']};
                                    border-radius: 5px;
                                    min-width: 24px;
                                    min-height: 24px;
                                }}
                                QLabel:hover {{
                                    border: 1px solid {COLORS['button_primary']};
                                    background-color: {COLORS['background_readonly']};
                                }}
                            """)
                
                # Marcar el nuevo checkbox
                checkbox.setChecked(True)
                
                # Cambiar el estilo visual del checkbox
                label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {COLORS['background_white']};
                        border-radius: 5px;
                        padding: 2px;
                        min-width: 24px;
                        min-height: 24px;
                        border: 2px solid {rol_color};
                    }}
                    QLabel:hover {{
                        background-color: {COLORS['background_readonly']};
                    }}
                """)
                
                # Actualizar la etiqueta visual con el check
                if os.path.exists(ruta_check):
                    pixmap = QPixmap(ruta_check)
                    label.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                
                # Cambiar el color del texto del nombre de usuario
                nombre_item = self.tabla_usuarios.item(row, 1)
                if nombre_item:
                    nombre_item.setForeground(QBrush(QColor(rol_color)))
                
                # Actualizar el color de la columna de nombre completo
                nombre_completo_item = self.tabla_usuarios.item(row, 2)
                if nombre_completo_item:
                    nombre_completo_item.setForeground(QBrush(QColor(rol_color)))
                
                # Actualizar privilegios en la base de datos
                exito, mensaje = ModeloUsuarios.actualizar_privilegios_usuario(
                    nombre_usuario, 
                    tipo_privilegio
                )
                
                if not exito:
                    self.mostrar_mensaje_informacion("Error", mensaje, QMessageBox.Critical)
                    # Revertir cambios visuales
                    checkbox.setChecked(False)
                    label.clear()
                    label.setStyleSheet(f"""
                        QLabel {{
                            background-color: {COLORS['background_white']};
                            border: 1px solid {COLORS['border_light']};
                            border-radius: 5px;
                            min-width: 24px;
                            min-height: 24px;
                        }}
                        QLabel:hover {{
                            border: 1px solid {COLORS['button_primary']};
                            background-color: {COLORS['background_readonly']};
                        }}
                    """)
                    
                    # Restaurar el rol anterior
                    if rol_actual_col is not None:
                        old_container = self.tabla_usuarios.cellWidget(row, rol_actual_col)
                        if old_container:
                            old_checkbox = old_container.findChild(QCheckBox)
                            if old_checkbox:
                                old_checkbox.setChecked(True)
                    return
                
                # Actualizar los roles en la tabla usuarios
                ModeloUsuarios.actualizar_roles_en_tabla(nombre_usuario, tipo_privilegio)
                
                # Registrar en trazabilidad
                detalles = f"Nuevo rol asignado: {nombre_rol} | Usuario afectado: {nombre_usuario}"
                ModeloTrazabilidad.registrar_accion(
                    accion="Cambio de rol",
                    paciente_afectado=None,
                    detalles_cambio=detalles
                )
            else:
                # Si está desactivando un rol, automáticamente asignar 'Visitante'
                visitante_col = 5  # Columna de Visitante
                
                # Marcar el rol de visitante
                visitante_container = self.tabla_usuarios.cellWidget(row, visitante_col)
                if visitante_container:
                    visitante_checkbox = visitante_container.findChild(QCheckBox)
                    visitante_label = None
                    
                    for j in range(visitante_container.layout().count()):
                        widget = visitante_container.layout().itemAt(j).widget()
                        if isinstance(widget, self.ClickableLabel):
                            visitante_label = widget
                            break
                    
                    if visitante_checkbox:
                        visitante_checkbox.setChecked(True)
                    
                    # Actualizar visual del checkbox de visitante
                    if visitante_label:
                        visitante_label.setStyleSheet(f"""
                            QLabel {{
                                background-color: {COLORS['background_white']};
                                border-radius: 5px;
                                padding: 2px;
                                min-width: 24px;
                                min-height: 24px;
                                border: 2px solid #fd7e14;
                            }}
                            QLabel:hover {{
                                background-color: {COLORS['background_readonly']};
                            }}
                        """)
                        
                        if os.path.exists(ruta_check):
                            pixmap = QPixmap(ruta_check)
                            visitante_label.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                
                # Desmarcar el rol actual
                checkbox.setChecked(False)
                label.clear()
                label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {COLORS['background_white']};
                        border: 1px solid {COLORS['border_light']};
                        border-radius: 5px;
                        min-width: 24px;
                        min-height: 24px;
                    }}
                    QLabel:hover {{
                        border: 1px solid {COLORS['button_primary']};
                        background-color: {COLORS['background_readonly']};
                    }}
                """)
                
                # Actualizar el color del texto del nombre a visitante
                nombre_item = self.tabla_usuarios.item(row, 1)
                if nombre_item:
                    nombre_item.setForeground(QBrush(QColor("#fd7e14")))  # Color naranja para visitante
                
                # Actualizar el color del nombre completo a visitante
                nombre_completo_item = self.tabla_usuarios.item(row, 2)
                if nombre_completo_item:
                    nombre_completo_item.setForeground(QBrush(QColor("#fd7e14")))
                
                # Actualizar privilegios a 'solo_lectura'
                exito, mensaje = ModeloUsuarios.actualizar_privilegios_usuario(
                    nombre_usuario, 
                    "solo_lectura"  # Por defecto si se quita un rol
                )
                
                if not exito:
                    self.mostrar_mensaje_informacion("Error", mensaje, QMessageBox.Critical)
                    # Revertir cambios visuales
                    checkbox.setChecked(True)
                    
                    # Restaurar la imagen del check
                    if os.path.exists(ruta_check):
                        pixmap = QPixmap(ruta_check)
                        label.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    
                    # Si ya habíamos cambiado el visitante, revertir
                    if visitante_container and visitante_label:
                        visitante_checkbox.setChecked(False)
                        visitante_label.clear()
                        visitante_label.setStyleSheet(f"""
                            QLabel {{
                                background-color: {COLORS['background_white']};
                                border: 1px solid {COLORS['border_light']};
                                border-radius: 5px;
                                min-width: 24px;
                                min-height: 24px;
                            }}
                            QLabel:hover {{
                                border: 1px solid {COLORS['button_primary']};
                                background-color: {COLORS['background_readonly']};
                            }}
                        """)
                    return
                
                # Actualizar los roles en la tabla usuarios
                ModeloUsuarios.actualizar_roles_en_tabla(nombre_usuario, "solo_lectura")
                
                # Registrar en trazabilidad
                detalles = f"Privilegios removidos: {nombre_rol} | Usuario asignado como Visitante | Usuario afectado: {nombre_usuario}"
                ModeloTrazabilidad.registrar_accion(
                    accion="Cambio de rol",
                    paciente_afectado=None,
                    detalles_cambio=detalles
                )
            
            # Actualizar el filtro después de cambiar roles
            self.filtrar_usuarios()
            
            # Forzar actualización visual de la tabla
            self.tabla_usuarios.update()
            
        except Exception as e:
            self.mostrar_mensaje_informacion("Error", f"Error al actualizar rol: {str(e)}", QMessageBox.Critical)

    def mostrar_trazabilidad(self):
        """Muestra la ventana de trazabilidad de acciones"""
        from Front_end.styles.traceability_dialog import TraceabilityDialog
        
        # Crear y mostrar el diálogo de trazabilidad
        dialogo = TraceabilityDialog(self, self.ruta_base)
        dialogo.exec_()

    def mostrar_generador_reportes(self):
        
        """Muestra el generador de reportes con las métricas de tiempos de atención"""
        try:
            # Mostrar pantalla de carga mientras se inicializa la interfaz
            from PyQt5.QtCore import Qt
            from PyQt5.QtWidgets import QDesktopWidget, QVBoxLayout, QWidget, QApplication
            import traceback  # Para manejo detallado de errores
            
            # Mostrar pantalla de carga mientras se inicializa la interfaz
            print("Iniciando splash screen...")
            splash = SplashScreen(None, logo_path=self.ruta_logo, message="Cargando generador de reportes...", duration=2)
            print("Splash screen creada, mostrando...")
            splash.setFixedSize(int(self.pantalla.width() * 0.3), int(self.pantalla.height() * 0.3))
            
            # Asegurar que la splash screen aparezca por encima de todo
            splash.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            splash.show()
            splash.raise_()  # Traer al frente
            print("Splash screen mostrada, iniciando animación...")
            splash.opacity_animation.start()
            QApplication.processEvents()
            
            # Importar la clase ReportGenerator desde el módulo correcto
            from Front_end.styles.report_generator import ReportGenerator
            
            # Crear una instancia del generador de reportes
            # Pasamos la ruta base para recursos y referencias
            generador = ReportGenerator(parent=self, ruta_base=self.ruta_base)
            
            # Configurar ventana para que sea sin bordes y maximizada, como la interfaz principal
            generador.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
            generador.setAttribute(Qt.WA_TranslucentBackground)
            QApplication.processEvents()

            # Aseguramos que tenga un layout principal si no lo tiene
            if not generador.layout():
                main_layout = QVBoxLayout(generador)
                main_layout.setContentsMargins(0, 0, 0, 0)
                main_layout.setSpacing(0)
            else:
                main_layout = generador.layout()
            
            # Crear un header personalizado SIN el botón de menú lateral
            header = QWidget()
            header.setStyleSheet(f"background-color: {COLORS['background_header']};")  
            
            # Calcular tamaños para asegurar que coincidan con la interfaz principal
            alto_pantalla = self.pantalla.height()
            ancho_pantalla = self.pantalla.width()
            alto_logo = int(alto_pantalla * 0.14)
            
            # Establecer altura fija para el header completo
            header.setFixedHeight(alto_logo)
            
            # Crear layout para organizar logo y botones
            layout_header = QHBoxLayout(header)
            layout_header.setContentsMargins(0, 0, 10, 0)
            
            # Área del logo (lado izquierdo)
            if os.path.exists(self.ruta_logo):
                ancho_logo = int(ancho_pantalla * 0.2)
                
                etiqueta_logo = QLabel()
                mapa_pixeles_logo = QPixmap(self.ruta_logo)
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
            
            # Agregar espacio expansible en el medio
            layout_header.addStretch(1)
            
            # Contenedor para los botones de control y el logo de la universidad
            container_right = QWidget()
            layout_right = QVBoxLayout(container_right)
            layout_right.setContentsMargins(0, 0, 0, 0)
            layout_right.setSpacing(5)
            
            # Contenedor para los botones de control
            buttons_container = QWidget()
            buttons_layout = QHBoxLayout(buttons_container)
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(5)

            def cerrar_generador():
                generador.reject()
            
            # Botones de control SIN el botón de menú
            botones = [
                ("🗕", self.showMinimized, False),
                ("🗗", self.toggle_maximized, False),
                ("✖", cerrar_generador, True)  # Dejamos None temporalmente y conectamos después
            ]
            
            for texto, funcion, es_cerrar in botones:
                boton = StyledButton(texto, "window_control", is_close=es_cerrar)
                boton.setFixedSize(30, 30)
                if funcion:  # Solo conectamos si hay una función
                    boton.clicked.connect(funcion)
                # Para el botón de cerrar, la conectaremos después
                if texto == "✖":
                    close_button = boton
                buttons_layout.addWidget(boton)
            
            # Agregar contenedor de botones al layout derecho
            layout_right.addWidget(buttons_container, 0, Qt.AlignRight | Qt.AlignTop)
            
            # Área del logo universidad (debajo de los botones)
            if hasattr(self, 'ruta_logou') and os.path.exists(self.ruta_logou):
                alto_logo_u = int(alto_pantalla * 0.1)
                ancho_logo_u = int(ancho_pantalla * 0.15)
                
                etiqueta_logo_u = QLabel()
                mapa_pixeles_logo_u = QPixmap(self.ruta_logou)
                logo_escalado_u = mapa_pixeles_logo_u.scaled(
                    ancho_logo_u,
                    alto_logo_u,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                etiqueta_logo_u.setPixmap(logo_escalado_u)
                etiqueta_logo_u.setFixedSize(logo_escalado_u.size())
                etiqueta_logo_u.setStyleSheet(f"background: {COLORS['background_transparent']}; border: none;")
                
                # Alinear el logo de la universidad a la derecha
                logo_u_container = QWidget()
                logo_u_layout = QHBoxLayout(logo_u_container)
                logo_u_layout.setContentsMargins(0, 0, 0, 0)
                logo_u_layout.addStretch(1)
                logo_u_layout.addWidget(etiqueta_logo_u)
                
                # Agregar contenedor del logo al layout derecho
                layout_right.addWidget(logo_u_container, 0, Qt.AlignRight)
            
            # Agregar el contenedor derecho al layout principal
            layout_header.addWidget(container_right, 0, Qt.AlignTop)
            
            # Crear un contenedor para el contenido existente
            content_container = QWidget()
            # Mover todos los widgets del layout actual al contenedor temporal
            if main_layout.count() > 0:
                old_layout = QVBoxLayout(content_container)
                old_layout.setContentsMargins(0, 0, 0, 0)
                while main_layout.count():
                    item = main_layout.takeAt(0)
                    if item.widget():
                        old_layout.addWidget(item.widget())
            
            # Limpiar y reconstruir el layout principal con el header
            main_layout.addWidget(header)
            main_layout.addWidget(content_container, 1)  # El contenido ocupa el espacio restante
            
            # Establecer geometría inicial para pantalla completa
            screen = QDesktopWidget().screenGeometry()
            generador.setGeometry(0, 0, screen.width(), screen.height())

            # En caso de que el paciente_seleccionado no esté configurado correctamente,
            # asegurar que sea None para evitar errores
            generador.paciente_seleccionado = None
            
            # Configurar las áreas disponibles para filtrar, deben coincidir con las del proyecto
            generador.areas_disponibles = ["Antigua", "Amarilla", "Pediatría", "Pasillos", "Clini", "Sala de espera"]
            generador.paciente_seleccionado = None
            # Asegurar que el modo inicial sea 'grupal' para evitar errores si no hay paciente seleccionado
            generador.modo_actual = "grupal"
            
            # Definir función específica para cerrar solo el diálogo
            def cerrar_solo_generador():
                generador.reject()  # Esto cierra solo el diálogo, no toda la aplicación
            
            # Conectar el botón de cierre a nuestra función personalizada
            close_button.clicked.connect(cerrar_solo_generador)
            
            # Sobrescribir el evento closeEvent para evitar el cierre de la aplicación principal
            original_close_event = generador.closeEvent
            def nuevo_close_event(event):
                event.ignore()  # Ignorar el cierre estándar
                generador.reject()  # Cerrar solo el diálogo
                
            generador.closeEvent = nuevo_close_event
            
            # Cerrar splash screen antes de mostrar el generador
            splash.accept()
            
            # Mostrar maximizado antes de ejecutar
            generador.showMaximized()
            
            # Ejecutar el cuadro de diálogo del generador de reportes (modal)
            generador.exec_()
            
        except Exception as e:
            # Mostrar error detallado con traceback
            self.mostrar_mensaje_advertencia(
                "Error al mostrar el generador de reportes",
                f"Se produjo un error: {str(e)}\n\n{traceback.format_exc()}"
            )