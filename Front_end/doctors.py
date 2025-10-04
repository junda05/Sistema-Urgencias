from PyQt5.QtWidgets import (QMainWindow, QCompleter, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTableWidget, QTableWidgetItem, QPushButton, 
                           QLabel, QMessageBox, QMenu, QFrame, QLayout,
                           QLineEdit, QFormLayout, QDialog, QListWidget, QListWidgetItem,
                           QHeaderView, QSizePolicy, QDesktopWidget, QApplication, QToolTip, 
                           QGraphicsOpacityEffect, QDateTimeEdit, QCheckBox, QGridLayout, QGroupBox, QScrollArea, QListView)
from PyQt5.QtCore import Qt, QTimer, QRect, QSize, QStringListModel, QPropertyAnimation, QEasingCurve, QPoint, QDateTime
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont, QPixmap, QIcon, QLinearGradient, QGradient
from Back_end.Manejo_DB import ModeloPaciente
from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
from datetime import datetime
import sys
import os
# Importar componentes de animación desde su ubicación correcta
from Front_end.styles.animation_components import SplashScreen, FadeAnimation
# Importar estilos y componentes
from Front_end.styles.styles import TABLE_STYLES_UPDATED, SCROLLBAR_STYLE
from Front_end.styles.components import StyledMessageBox, StyledButton, StyledDialog, FormField
from Front_end.styles.table_components import Estado_delegado_circulo, TextDelegate, Personalizado_Columnas, configurar_tabla_estandar
from Front_end.styles.header_components import HeaderCombinado
from Front_end.styles.lateral_menu import LateralMenu, MenuToggleButton
from Front_end.styles.custom_widgets import FrameBotones, TablaContainer
from Front_end.styles.font_utils import aplicar_fuentes_sistema
from Front_end.styles.Frontend_utils import DialogoFiltrar, LabsSelector, IxsSelector
from Front_end.styles.styles import COLORS, BORDER_RADIUS, MENU_STYLES

class VistaMedicos(QMainWindow):
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
        self.ruta_icono = os.path.join(ruta_imagenes, "logo.ico")
        self.ruta_logou = os.path.join(ruta_imagenes, "u.png")
        
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
        try:
            id_registro = registro[13]
            nombre_paciente = registro[0] 
            documento_paciente = registro[1]  

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
                if hasattr(self, 'entradas') and 'triage' in self.entradas:
                    self.entradas['triage'].setCurrentText("No realizado")
            
            # Validar y procesar el nombre usando el modelo
            nombre_procesado, es_anonimo, mensaje = self.modelo.procesar_nombre(nombre)
            
            # Si es anónimo (vacío o una sola palabra), confirmar registro como NN
            if es_anonimo:
                if self.mostrar_mensaje_confirmacion(
                    "Nombre incompleto" if nombre else "Nombre vacío", 
                    mensaje
                ):
                    datos['nombre'] = self.modelo.crear_nombre_nn()
                else:
                    # Si no quiere registrar como NN, no continuar
                    return
            else:
                # Si no es anónimo, aplicar el nombre procesado
                datos['nombre'] = nombre_procesado
            
            # Validar el nombre con el modelo (regla de 3 palabras)
            error_nombre = self.modelo.validar_nombre(datos['nombre'])
            if error_nombre and not datos['nombre'].startswith('NN -'):  # Permitir NN
                self.mostrar_mensaje_informacion("Error", error_nombre, QMessageBox.Critical)
                return
            
            # Si es NN, el documento no es obligatorio
            if datos['nombre'].startswith('NN -') and not datos['documento']:
                # Generar un "documento" temporal único para NN
                datos['documento'] = f"NN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            ubicacion = f"{self.combo_area.currentText()} - {self.combo_cubiculo.currentText()}"
            
            # Validar datos mínimos
            if not self.validar_datos_minimos(datos):
                self.mostrar_mensaje_informacion("Error", "Debe completar los campos obligatorios", QMessageBox.Critical)
                return
            
            # Validar estado del paciente usando el método del modelo
            validacion_estado = self.modelo.validar_estado_paciente(datos)
            if validacion_estado:
                self.mostrar_mensaje_informacion("Error de Validación", validacion_estado, QMessageBox.Critical)
                return

            # Validar la concordancia entre laboratorios seleccionados y el estado de Labs
            laboratorios = [lab[0] for lab in self.labs_selector.get_laboratorios_seleccionados()]
            if (laboratorios and (not datos['labs'] or datos['labs'] not in ["No se ha realizado", "En espera de resultados", "Resultados completos"])):
                self.mostrar_mensaje_informacion("Error de Validación", 
                    "Debe establecer un estado válido en Labs cuando selecciona laboratorios", QMessageBox.Critical)
                return
            if (not laboratorios and datos['labs'] in ["No se ha realizado", "En espera de resultados", "Resultados completos"]):
                self.mostrar_mensaje_informacion("Error de Validación", 
                    "Ha seleccionado un estado para Labs pero no ha agregado ningún laboratorio", QMessageBox.Critical)
                return
            
            # Validar la concordancia entre imágenes seleccionadas y el estado de IMG
            imagenes = [ix[0] for ix in self.ix_selector.get_imagenes_seleccionadas()]
            if (imagenes and (not datos['ix'] or datos['ix'] not in ["No se ha realizado", "En espera de resultados", "Resultados completos"])):
                self.mostrar_mensaje_informacion("Error de Validación", 
                    "Debe establecer un estado válido en IMG cuando selecciona imágenes", QMessageBox.Critical)
                return
            if (not imagenes and datos['ix'] in ["No se ha realizado", "En espera de resultados", "Resultados completos"]):
                self.mostrar_mensaje_informacion("Error de Validación", 
                    "Ha seleccionado un estado para IMG pero no ha agregado ninguna imagen", QMessageBox.Critical)
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

            # Guardar en la base de datos
            exito, mensaje, paciente_id = self.modelo.datos_guardar_paciente(datos=datos, ubicacion=ubicacion)
            
            if exito:
                # Guardar laboratorios seleccionados
                if laboratorios:
                    # El modelo ya validará triage y CI
                    labs_exito, labs_mensaje = self.modelo.guardar_laboratorios_paciente(paciente_id, laboratorios)
                    if not labs_exito:
                        self.mostrar_mensaje_advertencia("Advertencia", labs_mensaje)
                
                # Guardar imágenes seleccionadas
                if imagenes:
                    # El modelo ya validará triage y CI
                    ix_exito, ix_mensaje = self.modelo.guardar_imagenes_paciente(paciente_id, imagenes)
                    if not ix_exito:
                        self.mostrar_mensaje_advertencia("Advertencia", ix_mensaje)
                
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
                label_text, key, index, es_requerido, readonly, _, opciones = campo
                valor_actual = registro[index] if registro[index] else ""
                label, combo = FormField.create_combo_box(label_text, opciones, es_requerido, valor_actual)
                self.entradas[key] = combo
                form_layout.addRow(label, combo)
            else:  # Es un LineEdit
                label_text, key, index, es_requerido, readonly, _ = campo
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
                    datos['nombre'] = f"NN - {self.modelo.crear_nombre_nn()}"
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
            
            # Validar estado del paciente usando el método del modelo
            validacion_estado = self.modelo.validar_estado_paciente(datos)
            if validacion_estado:
                self.mostrar_mensaje_informacion("Error de validación", validacion_estado, QMessageBox.Critical)
                return
            
            # AÑADIDO: Validación adicional para asegurar que no se actualicen estados sin prerrequisitos
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
                    "Ha seleccionado un estado para IMG pero no ha agregado ninguna imagen", QMessageBox.Critical)
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