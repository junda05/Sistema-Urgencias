from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                           QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QHeaderView,
                           QDesktopWidget, QFrame, QWidget, QProgressBar)
from PyQt5.QtCore import Qt, QSize, QThread, QObject, pyqtSignal, QTimer, QElapsedTimer
from PyQt5.QtGui import QIcon, QFont, QColor
import os
import sys
from Front_end.styles.styles import COLORS, BORDER_RADIUS, SCROLLBAR_STYLE
from Back_end.Manejo_DB import ModeloTrazabilidad

class TraceabilityDialogStyles:
    """Clase para definir estilos reutilizables para el diálogo de trazabilidad"""
    
    @staticmethod
    def get_main_style():
        return f"""
            QDialog {{
                background-color: {COLORS['background_primary']};
                border-radius: 10px;
            }}
            
            QLabel#title {{
                color: {COLORS['text_primary']};
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
            }}
            
            QLineEdit#search {{
                border: 1px solid {COLORS['border_light']};
                border-radius: {BORDER_RADIUS['medium']};
                padding: 8px 12px;
                background-color: {COLORS['background_white']};
                color: {COLORS['text_primary']};
                font-size: 14px;
                margin-right: 10px;
            }}
            
            QComboBox {{
                border: 1px solid {COLORS['border_light']};
                border-radius: {BORDER_RADIUS['medium']};
                padding: 8px 12px;
                background-color: {COLORS['background_white']};
                color: {COLORS['text_primary']};
                font-size: 14px;
                selection-background-color: {COLORS['button_primary']};
                selection-color: white;
            }}
            
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 20px;
                border-left: 1px solid {COLORS['border_light']};
            }}
            
            QPushButton {{
                background-color: {COLORS['button_primary']};
                color: white;
                border: none;
                border-radius: {BORDER_RADIUS['medium']};
                padding: 8px 15px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {COLORS['button_primary_hover']};
            }}
            
            QPushButton#close_button {{
                background-color: {COLORS['button_danger']};
                color: white;
                border: none;
                border-radius: {BORDER_RADIUS['medium']};
                padding: 8px 15px;
                font-weight: bold;
            }}
            
            QPushButton#close_button:hover {{
                background-color: {COLORS['button_danger_hover']};
            }}
            
            QPushButton#header_close {{
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
                color: {COLORS['text_primary']};
            }}
            
            QPushButton#header_close:hover {{
                color: {COLORS['button_danger']};
            }}
        """
    
    @staticmethod
    def get_table_style():
        return f"""
            QTableWidget {{
                background-color: {COLORS['background_white']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {BORDER_RADIUS['medium']};
                gridline-color: #EEEEEE;
            }}
            
            QHeaderView::section {{
                background-color: {COLORS['background_header']};
                color: {COLORS['text_primary']};
                padding: 10px;
                border: 1px solid #DDDDDD;
                font-weight: bold;
                font-size: 14px;
            }}
            
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #EEEEEE;
            }}
            
            QTableWidget::item:selected {{
                background-color: {COLORS['background_readonly']};
                color: {COLORS['text_primary']};
            }}
        """ + SCROLLBAR_STYLE

class TraceabilityDialog(QDialog):
    _config_path_printed = False  # Class variable to track if the config path has been printed
    
    def __init__(self, parent=None, ruta_base=None):
        super().__init__(parent)
        
        # Configurar rutas
        if ruta_base:
            self.ruta_base = ruta_base
        else:
            if getattr(sys, 'frozen', False):
                self.ruta_base = sys._MEIPASS
            else:
                self.ruta_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.setWindowTitle("Trazabilidad de acciones")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Aplicar estilos y fondo transparente
        self.setStyleSheet(TraceabilityDialogStyles.get_main_style())
        
        self.setup_ui()
        
        # Iniciar carga de datos de forma asincrónica para no bloquear la interfaz
        QTimer.singleShot(100, self.mostrar_spinner_y_cargar_datos)
        
        # Inicializar la lista para controlar los hilos
        self.threads = []
        
        # Timer para controlar la frecuencia de búsqueda (evitar búsquedas excesivas)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.realizar_busqueda_diferida)
        
        # Almacenar términos de búsqueda para búsqueda por palabras
        self.search_terms = []
        
        # Contador para la animación de la barra de progreso
        self.progress_value = 0
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.actualizar_barra_progreso)
    
    def setup_ui(self):
        # Contenedor principal con borde redondeado
        self.main_container = QFrame(self)
        self.main_container.setObjectName("main_container")
        self.main_container.setStyleSheet(f"""
            #main_container {{ 
                background-color: {COLORS['background_primary']};
                border-radius: 10px;
                border: 1px solid {COLORS['border_light']};
            }}
        """)
        
        # Layout principal
        self.layout = QVBoxLayout(self.main_container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Header con título y botón de cerrar - Corregir posicionamiento
        self.header_container = QWidget()
        self.header_layout = QHBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        # Hacer transparente el fondo del header
        self.header_container.setStyleSheet(f"""
            background-color: {COLORS['background_primary']};""")
        
        # Título
        self.title_label = QLabel("Trazabilidad de acciones")
        self.title_label.setObjectName("title")
        
        # Botón de cerrar - Usar un contenedor para posicionarlo correctamente
        self.close_button_container = QWidget()
        self.close_button_container.setStyleSheet("background-color: transparent;")
        self.close_button_container.setFixedWidth(30)
        close_button_layout = QVBoxLayout(self.close_button_container)
        close_button_layout.setContentsMargins(0, 0, 0, 0)
        close_button_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        
        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("header_close")
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.clicked.connect(self.close)
        self.close_button.setFixedSize(30, 30)
        
        close_button_layout.addWidget(self.close_button)
        
        # Ajustar el layout del header para que el botón quede fijo
        self.header_layout.addWidget(self.title_label, 1, Qt.AlignLeft)  # 1 significa que se estirará
        self.header_layout.addWidget(self.close_button_container, 0, Qt.AlignRight | Qt.AlignTop)  # 0 significa que no se estirará
        
        # Separador
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.separator.setStyleSheet(f"""
            background-color: {COLORS['background_transparent']};
            max-height: 1px;
        """)
        
        # Tabla de trazabilidad - Crear primero para tomar el tamaño de su fuente
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # Aumentado a 6 columnas para incluir el nombre del usuario
        self.table.setHorizontalHeaderLabels([
            "Nombre", "Usuario", "Acción Realizada", 
            "Fecha y Hora", "Paciente Afectado", "Detalles del Cambio"
        ])
        
        # Configurar tabla con estilos
        self.table.setStyleSheet(TraceabilityDialogStyles.get_table_style())
        self.table.horizontalHeader().setStretchLastSection(False) # Cambiado a False para usar anchos fijos
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        # Obtener el tamaño de fuente de la tabla para usar en los elementos de filtrado
        table_font = self.table.font()
        table_font_size = table_font.pointSize()
        
        # Aplicar el mismo tamaño de letra a los headers que al contenido de la tabla
        header_font = QFont(table_font)
        header_font.setBold(True)  # Mantener negrita
        self.table.horizontalHeader().setFont(header_font)
        
        # Filtros - Mejorar posicionamiento con contenedor de ancho fijo
        self.filters_container = QWidget()
        self.filters_container.setStyleSheet(f"""
            background-color: {COLORS['background_primary']};
            border: none;
        """)
        self.filters_layout = QHBoxLayout(self.filters_container)
        self.filters_layout.setContentsMargins(0, 0, 0, 0)
        self.filters_layout.setSpacing(10)  # Reducir espaciado para mejor alineación
        
        # Campo de búsqueda - Aplicar el mismo tamaño de fuente de la tabla
        self.search_input = QLineEdit()
        self.search_input.setObjectName("search")
        self.search_input.setPlaceholderText("Buscar por usuario, nombre completo o paciente...")
        self.search_input.setFont(table_font)
        self.search_input.setStyleSheet(f"""
            background-color: {COLORS['background_white']};
            font-size: {table_font_size}pt;
            min-width: 200px;
            border: 1px solid {COLORS['border_light']};
            border-radius: {BORDER_RADIUS['medium']};
            padding: 8px 12px;
        """)
        
        # Combo de filtro por rol - MODIFICAR PARA QUITAR VISITANTE
        self.role_filter = QComboBox()
        self.role_filter.addItems(["Todos", "Administrador", "Médico"])  # Quitamos "Visitante"
        self.role_filter.setFont(table_font)
        self.role_filter.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLORS['border_light']};
                border-radius: {BORDER_RADIUS['medium']};
                padding: 8px 12px;
                background-color: {COLORS['background_white']};
                color: {COLORS['text_primary']};
                font-size: {table_font_size}pt;
                min-width: 180px;
            }}
            
            QComboBox:hover {{
                border: 1px solid {COLORS['button_primary']};
                background-color: {COLORS['background_readonly']};
            }}
            
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 24px;
                border-left: 1px solid {COLORS['border_light']};
            }}
            
            QComboBox::down-arrow {{
                image: url("c:/Users/ASUS/OneDrive/Documentos/Universidad/IX Semestre/Proyecto de grado/Software/Avances Abril/Beta 4/Front_end/imagenes/dropdown_arrow.png");
                width: 12px;
                height: 12px;
            }}
            
            QComboBox QAbstractItemView {{
                border: 1px solid {COLORS['border_light']};
                background-color: {COLORS['background_white']};
                selection-background-color: {COLORS['button_primary_hover']};
                selection-color: white;
                border-radius: {BORDER_RADIUS['small']};
                padding: 5px;
                outline: none;
            }}
        """)
        
        # Eliminamos el botón de búsqueda porque ahora filtrará automáticamente
        
        self.filters_layout.addWidget(self.search_input, 3)
        self.filters_layout.addWidget(self.role_filter, 2)
        
        # Configurar anchos fijos de columnas
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        
        # Configurar columnas con anchos específicos
        screen_width = QDesktopWidget().screenGeometry().width()
        total_width = int(screen_width * 0.8) - 40  # 80% del ancho de pantalla menos márgenes
        
        # Definir anchos proporcionales de columnas
        self.table.setColumnWidth(0, int(total_width * 0.15))  # Nombre
        self.table.setColumnWidth(1, int(total_width * 0.10))  # Usuario
        self.table.setColumnWidth(2, int(total_width * 0.15))  # Acción Realizada
        self.table.setColumnWidth(3, int(total_width * 0.15))  # Fecha y Hora
        self.table.setColumnWidth(4, int(total_width * 0.15))  # Paciente Afectado
        
        # Columna de detalles con wrap de texto
        self.table.setColumnWidth(5, int(total_width * 0.30))  # Detalles del Cambio
        
        # Botón para cerrar
        self.footer_container = QWidget()
        self.footer_layout = QHBoxLayout(self.footer_container)
        self.footer_layout.setContentsMargins(0, 0, 0, 0)
        self.footer_layout.addStretch()
        self.footer_container.setStyleSheet("""
            background-color: transparent;
            border: none;
        """)
        
        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setObjectName("close_button")
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setFont(table_font)
        self.footer_layout.addWidget(self.btn_close)
        self.btn_close.setStyleSheet(f"""
            QPushButton#close_button {{
                background-color: {COLORS['button_danger']};
                color: white;
                border: none;
                border-radius: {BORDER_RADIUS['medium']};
                padding: 8px 15px;
                font-weight: bold;
                font-size: {table_font_size}pt;
            }}
            
            QPushButton#close_button:hover {{
                background-color: {COLORS['button_danger_hover']};
            }}
        """)
        
        # Inicialmente ocultar la tabla (la mostraremos cuando haya datos)
        self.table.hide()
        
        # Mejorar el estilo del spinner container - Hacer fondo transparente
        self.spinner_container = QWidget()
        self.spinner_container.setStyleSheet(f"""
            background-color: transparent;
            border-radius: 10px;
            border: none;
        """)
        self.spinner_layout = QVBoxLayout(self.spinner_container)
        self.spinner_layout.setAlignment(Qt.AlignCenter)
        self.spinner_layout.setSpacing(20)
        
        # Crear un label para el mensaje de carga con estilo mejorado
        self.spinner_label = QLabel("Cargando datos de trazabilidad...")
        self.spinner_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 18px;
            font-weight: bold;
            padding: 20px;
            background-color: {COLORS['background_transparent']};
            border-radius: 10px;
        """)
        self.spinner_label.setAlignment(Qt.AlignCenter)
        
        # Crear un loader animado con estilo mejorado
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)  # Altura más pequeña para un look moderno
        self.progress_bar.setMinimumWidth(350)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 6px;
                background-color: {COLORS['background_transparent']};
                height: 12px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {COLORS['button_primary']};
                border-radius: 6px;
                margin: 0px;
            }}
        """)
        
        # Añadir pequeño texto secundario explicativo
        self.spinner_subtitle = QLabel("Por favor espere mientras se recuperan los registros de actividad...")
        self.spinner_subtitle.setStyleSheet(f"""
            color: {COLORS['text_light']};
            font-size: 14px;
            font-style: italic;
            background-color: {COLORS['background_transparent']};
        """)
        self.spinner_subtitle.setAlignment(Qt.AlignCenter)
        self.spinner_subtitle.setWordWrap(True)
        
        # Añadir elementos al spinner
        self.spinner_layout.addWidget(self.spinner_label)
        self.spinner_layout.addWidget(self.progress_bar)
        self.spinner_layout.addWidget(self.spinner_subtitle)
        
        # El spinner ocupa todo el espacio disponible
        self.spinner_container.setMinimumSize(500, 200)
        # Disminuir el tamaño del spinner para que no ocupe tanto espacio vertical
        self.spinner_container.setMaximumSize(550, 250)
        self.spinner_container.setStyleSheet(f"""
            background-color: {COLORS['background_header']};
            border-radius: 10px;
            """)
        
        # Crear un contenedor para la tabla y el spinner que usará un stack layout
        self.content_container = QWidget()
        self.content_container.setStyleSheet(f"""
            background-color: {COLORS['background_transparent']};""")
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Agregar la tabla al contenedor de contenido
        self.content_layout.addWidget(self.table)
        
        # Agregar el spinner container al contenedor de contenido
        # Spinner container flotará sobre la tabla
        self.spinner_container.setParent(self.content_container)
        self.spinner_container.hide()  # Inicialmente oculto
        
        # Agregar widgets al layout principal
        self.layout.addWidget(self.header_container)
        self.layout.addWidget(self.separator)
        self.layout.addWidget(self.filters_container)
        self.layout.addWidget(self.content_container, 1)  # 1 es para que se expanda
        self.layout.addWidget(self.footer_container)
        
        # Layout general para el diálogo
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(self.main_container)
        
        # Configurar tamaño y centrar en pantalla
        self.resize_dialog()
        self.center_dialog()
        
        # Conectar eventos
        self.search_input.textChanged.connect(self.iniciar_busqueda_diferida)
        self.role_filter.currentIndexChanged.connect(self.filtrar_datos)
        self.table.horizontalHeader().sectionClicked.connect(self.ordenar_columna)
    
    def iniciar_busqueda_diferida(self):
        """Inicia un temporizador para realizar la búsqueda después de un breve retardo"""
        # Cancelar cualquier búsqueda pendiente
        self.search_timer.stop()
        # Iniciar nuevo temporizador (300ms es un buen equilibrio entre responsividad y rendimiento)
        self.search_timer.start(300)
    
    def actualizar_tabla_con_resultados(self, datos):
        """Actualiza la tabla con los datos recibidos del worker"""
        # Ocultar spinner
        self.spinner_container.hide()
        
        # Mostrar tabla
        self.table.show()
        
        # Mostrar los datos en la tabla
        self.mostrar_datos_en_tabla(datos)
    
    def realizar_busqueda_diferida(self):
        """Procesa el texto de búsqueda y realiza la búsqueda"""
        # Obtener el texto de búsqueda y dividirlo en palabras
        texto_busqueda = self.search_input.text().strip()
        
        if texto_busqueda:
            # Dividir por espacios y filtrar palabras vacías
            self.search_terms = [term.lower() for term in texto_busqueda.split() if term.strip()]
            # Limitar a un máximo de 4 palabras
            self.search_terms = self.search_terms[:4]
        else:
            self.search_terms = []
            
        # Realizar la búsqueda
        self.filtrar_datos()
    
    def mostrar_spinner_y_cargar_datos(self):
        """Muestra el spinner y carga los datos en un hilo separado"""
        # Mostrar el spinner y posicionarlo sobre la tabla
        self.spinner_container.show()
        self.spinner_container.raise_()  # Asegurar que esté por encima de la tabla
        
        # Centrar el spinner en el contenedor padre
        spinner_x = (self.content_container.width() - self.spinner_container.width()) // 2
        spinner_y = (self.content_container.height() - self.spinner_container.height()) // 2
        self.spinner_container.move(spinner_x, spinner_y)
        
        # Configurar barra de progreso animada - Asegurar que inicie en 0
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_value = 0
        
        # Iniciar timer de animación con intervalo más largo para progresión más lenta
        self.progress_timer.start(70)  # Aumentado de 50ms a 70ms para una animación más lenta
        
        # Crear un hilo para cargar los datos
        self.thread = QThread()
        self.worker = DataWorker()
        self.worker.moveToThread(self.thread)
        
        # Conectar señales
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.actualizar_progreso_real)
        self.worker.finished.connect(self.actualizar_tabla_con_resultados)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(lambda: self.progress_timer.stop())
        self.thread.finished.connect(self.thread.deleteLater)
        
        # Mantener una referencia al hilo para evitar que se elimine prematuramente
        self.threads.append(self.thread)
        
        # Iniciar el hilo
        self.thread.start()
    
    def actualizar_barra_progreso(self):
        """Actualiza la barra de progreso con animación fluida"""
        # Incrementar valor de manera suave y gradual con incrementos más pequeños al inicio
        if self.progress_value < 90:  # Limitado a 90% para simulación
            # Usar un incremento más pequeño al inicio para mostrar progreso gradual
            if self.progress_value < 20:
                increment = 0.5  # Incremento muy pequeño al inicio
            elif self.progress_value < 40:
                increment = 0.8  # Incremento un poco mayor
            elif self.progress_value < 60:
                increment = 1.0  # Incremento moderado
            else:
                # Aceleración suave para el final
                increment = max(0.5, (90 - self.progress_value) / 30)
                
            self.progress_value = min(90, self.progress_value + increment)
            self.progress_bar.setValue(int(self.progress_value))
    
    def actualizar_progreso_real(self, valor):
        """Actualiza la barra con el progreso real reportado por el worker"""
        if valor <= 100:
            self.progress_value = valor
            self.progress_bar.setValue(valor)

    def filtrar_datos(self):
        """Filtra los datos según los criterios de búsqueda"""
        # Mostrar spinner y posicionarlo sobre la tabla
        self.spinner_container.show()
        self.spinner_container.raise_()  # Asegurar que esté por encima de la tabla
        
        # Centrar el spinner en el contenedor padre
        spinner_x = (self.content_container.width() - self.spinner_container.width()) // 2
        spinner_y = (self.content_container.height() - self.spinner_container.height()) // 2
        self.spinner_container.move(spinner_x, spinner_y)
        
        # Configurar barra de progreso animada - Asegurar que inicie en 0
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_value = 0
        
        # Iniciar timer de animación con intervalo más largo
        self.progress_timer.start(70)  # Aumentado de 50ms a 70ms para una animación más lenta
        
        # Obtener criterios de filtrado
        filtro_rol = self.role_filter.currentText()
        
        # Crear un worker para el filtrado
        self.filter_thread = QThread()
        self.filter_worker = FilterWorker(self.search_terms, filtro_rol)
        self.filter_worker.moveToThread(self.filter_thread)
        
        # Conectar señales
        self.filter_thread.started.connect(self.filter_worker.run)
        self.filter_worker.progress.connect(self.actualizar_progreso_real)
        self.filter_worker.finished.connect(self.actualizar_tabla_con_resultados)
        self.filter_worker.finished.connect(self.filter_thread.quit)
        self.filter_worker.finished.connect(self.filter_worker.deleteLater)
        self.filter_worker.finished.connect(lambda: self.progress_timer.stop())
        self.filter_thread.finished.connect(self.filter_thread.deleteLater)
        
        # Mantener una referencia al hilo para evitar que se elimine prematuramente
        self.threads.append(self.filter_thread)
        
        # Iniciar el hilo
        self.filter_thread.start()
    
    def ordenar_columna(self, columna_index):
        """Ordena la tabla por la columna seleccionada"""
        # Obtener dirección de ordenamiento actual
        orden_actual = self.table.horizontalHeader().sortIndicatorOrder()
        
        # Invertir dirección para el siguiente clic
        nuevo_orden = Qt.DescendingOrder if orden_actual == Qt.AscendingOrder else Qt.AscendingOrder
        
        # Ordenar tabla
        self.table.sortItems(columna_index, nuevo_orden)
    
    def resize_dialog(self):
        """Ajusta el tamaño del diálogo según el tamaño de la pantalla"""
        screen = QDesktopWidget().availableGeometry()
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.8)
        self.resize(width, height)
    
    def center_dialog(self):
        """Centra el diálogo en la pantalla"""
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def cargar_datos(self):
        """Carga los datos de trazabilidad desde la base de datos"""
        try:
            # Usar el modelo de trazabilidad para obtener los datos
            datos = ModeloTrazabilidad.obtener_acciones()
            self.mostrar_datos_en_tabla(datos)
            
        except Exception as e:
            print(f"Error al cargar datos de trazabilidad: {str(e)}")
    
    def obtener_nombre_usuario(self, username):
        """Obtiene el nombre completo del usuario desde la base de datos"""
        try:
            from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
            
            # Conectar a la base de datos
            conn = ModeloUsuarios.conectar_db()
            if not conn:
                return username  # Si no puede conectar, devuelve el username como fallback
                
            cursor = conn.cursor()
            
            # Consultar el nombre del usuario
            cursor.execute("""
                SELECT nombre_completo FROM usuarios 
                WHERE username = %s
            """, (username,))
            
            resultado = cursor.fetchone()
            conn.close()
            
            if resultado and resultado[0]:
                return resultado[0]
            else:
                return "Usuario del Sistema"  # Nombre genérico si no tiene nombre registrado
                
        except Exception as e:
            print(f"Error al obtener nombre de usuario: {str(e)}")
            return username  # En caso de error, usar el username como fallback
    
    def verificar_usuario_activo(self, username):
        """
        Verifica si un usuario está activo en la base de datos
        
        Args:
            username: Nombre del usuario a verificar
            
        Returns:
            bool: True si el usuario está activo, False si está inactivo o no existe
        """
        try:
            from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
            
            # Conectar a la base de datos
            conn = ModeloUsuarios.conectar_db()
            if not conn:
                return True  # Si hay error de conexión, asumimos activo por defecto
                
            cursor = conn.cursor()
            
            # Consultar el estado del usuario
            cursor.execute("""
                SELECT estado FROM usuarios 
                WHERE username = %s
            """, (username,))
            
            resultado = cursor.fetchone()
            conn.close()
            
            # Si no hay resultado o el estado no es 'activo', retornar False
            if not resultado or resultado[0] != 'activo':
                return False
                
            return True
            
        except Exception as e:
            print(f"Error al verificar estado del usuario: {str(e)}")
            return True  # En caso de error, asumimos que está activo
    
    def mostrar_datos_en_tabla(self, datos):
        """Muestra los datos en la tabla de trazabilidad"""
        # Limpiar tabla
        self.table.setRowCount(0)
        
        if not datos:
            return
        
        # Configurar número de filas
        self.table.setRowCount(len(datos))
        
        # Importar ModeloUsuarios para obtener roles correctamente
        from Back_end.Usuarios.ModeloUsuarios import ModeloUsuarios
        
        # Llenar tabla con datos
        for i, fila in enumerate(datos):
            # Columnas a mostrar
            columnas = [0, 2, 3, 4, 5]  # Índices originales de la base de datos
            
            # Agregar nombre de usuario (columna adicional al inicio)
            username = fila[0] if len(fila) > 0 and fila[0] is not None else ""
            nombre_usuario = self.obtener_nombre_usuario(username)
            
            # Verificar si el usuario está activo
            esta_activo = self.verificar_usuario_activo(username)
            
            # Obtener rol del usuario para aplicar formato correcto
            rol = ModeloUsuarios.obtener_rol_usuario(username)
            
            # Crear el ítem para el nombre
            nombre_item = QTableWidgetItem(nombre_usuario)
            nombre_item.setTextAlignment(Qt.AlignCenter)
            
            # Aplicar tachado si el usuario no está activo, con color según rol
            if not esta_activo:
                font = nombre_item.font()
                font.setStrikeOut(True)
                font.setWeight(QFont.Bold)  # Hacer más gruesa la fuente para que el tachado sea más visible
                nombre_item.setFont(font)
                
                # Colores para tachado según rol
                if rol == 'admin':
                    nombre_item.setForeground(QColor("#4A7296"))  # Azul corporativo para administradores
                elif rol == 'medico':
                    nombre_item.setForeground(QColor("#28a745"))  # Verde médico
                else:
                    nombre_item.setForeground(QColor("#fd7e14"))  # Naranja para visitante/otro
            
            self.table.setItem(i, 0, nombre_item)
            
            # Procesar el resto de columnas con desplazamiento de +1 en j
            for j, columna_idx in enumerate(columnas):
                table_col = j + 1  # +1 porque la columna 0 es ahora el nombre
                
                if columna_idx >= len(fila) or fila[columna_idx] is None:
                    item = QTableWidgetItem("-")
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    valor = fila[columna_idx]
                    item = QTableWidgetItem(str(valor))
                    
                    # Aplicar colores y formatos específicos por columna
                    if j == 0:  # Columna Usuario (ahora es la columna 1 en la tabla)
                        item.setTextAlignment(Qt.AlignCenter)
                        
                        # Obtener el nombre de usuario para consultar su rol
                        username = str(valor)
                        
                        # Si el usuario no está activo, aplicar tachado también al username con color según rol
                        if not esta_activo:
                            font = item.font()
                            font.setStrikeOut(True)
                            # Hacer más gruesa la fuente para que el tachado sea más visible
                            font.setWeight(QFont.Bold)
                            item.setFont(font)
                            
                            # Colores para tachado según rol
                            if rol == 'admin':
                                item.setForeground(QColor("#4A7296"))  # Azul corporativo para administradores
                            elif rol == 'medico':
                                item.setForeground(QColor("#28a745"))  # Verde médico
                            else:
                                item.setForeground(QColor("#fd7e14"))  # Gris por defecto
                        
                        # Usar ModeloUsuarios.obtener_rol_usuario directamente
                        
                        # Aplicar colores según rol
                        if rol == 'admin':
                            if esta_activo:  # Solo aplicar color si está activo
                                item.setForeground(QColor("#4A7296"))  # Azul corporativo para administradores
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)
                            
                            # También aplicar formato al nombre
                            if esta_activo:  # Solo aplicar color si está activo
                                nombre_item.setForeground(QColor("#4A7296"))
                            nombre_font = nombre_item.font()
                            nombre_font.setBold(True)
                            nombre_item.setFont(nombre_font)
                            
                        elif rol == 'medico':
                            if esta_activo:  # Solo aplicar color si está activo
                                item.setForeground(QColor("#28a745"))  # Verde médico
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)
                            
                            # También aplicar formato al nombre
                            if esta_activo:  # Solo aplicar color si está activo
                                nombre_item.setForeground(QColor("#28a745"))
                            nombre_font = nombre_item.font()
                            nombre_font.setBold(True)
                            nombre_item.setFont(nombre_font)
                        else:
                            if esta_activo:  # Solo aplicar color si está activo
                                item.setForeground(QColor("#fd7e14"))  # Naranja para visitantes
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)
                            
                            # También aplicar formato al nombre
                            if esta_activo:  # Solo aplicar color si está activo
                                nombre_item.setForeground(QColor("#fd7e14"))
                            nombre_font = nombre_item.font()
                            nombre_font.setBold(True)
                            nombre_item.setFont(nombre_font)
                    
                    # Fecha y hora
                    elif j == 2:  # Columna de fecha (ahora columna 3)
                        item.setTextAlignment(Qt.AlignCenter)
                    
                    # Acción realizada
                    elif j == 1:  # Columna de acción (ahora columna 2)
                        item.setTextAlignment(Qt.AlignCenter)
                    
                    # Columna de Detalles - Habilitar Word Wrap
                    elif j == 4:  # Columna de detalles (ahora columna 5)
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                
                self.table.setItem(i, table_col, item)
            
            # Ajustar altura de la fila según el contenido de la columna de detalles
            self.table.resizeRowToContents(i)
    
    def filtrar_datos(self):
        """Filtra los datos según los criterios de búsqueda"""
        # Mostrar spinner y posicionarlo sobre la tabla
        self.spinner_container.show()
        self.spinner_container.raise_()  # Asegurar que esté por encima de la tabla
        
        # Centrar el spinner en el contenedor padre
        spinner_x = (self.content_container.width() - self.spinner_container.width()) // 2
        spinner_y = (self.content_container.height() - self.spinner_container.height()) // 2
        self.spinner_container.move(spinner_x, spinner_y)
        
        # Configurar barra de progreso animada - Asegurar que inicie en 0
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_value = 0
        
        # Iniciar timer de animación con intervalo más largo
        self.progress_timer.start(70)  # Aumentado de 50ms a 70ms para una animación más lenta
        
        # Obtener criterios de filtrado
        filtro_rol = self.role_filter.currentText()
        
        # Crear un worker para el filtrado
        self.filter_thread = QThread()
        self.filter_worker = FilterWorker(self.search_terms, filtro_rol)
        self.filter_worker.moveToThread(self.filter_thread)
        
        # Conectar señales
        self.filter_thread.started.connect(self.filter_worker.run)
        self.filter_worker.progress.connect(self.actualizar_progreso_real)
        self.filter_worker.finished.connect(self.actualizar_tabla_con_resultados)
        self.filter_worker.finished.connect(self.filter_thread.quit)
        self.filter_worker.finished.connect(self.filter_worker.deleteLater)
        self.filter_worker.finished.connect(lambda: self.progress_timer.stop())
        self.filter_thread.finished.connect(self.filter_thread.deleteLater)
        
        # Mantener una referencia al hilo para evitar que se elimine prematuramente
        self.threads.append(self.filter_thread)
        
        # Iniciar el hilo
        self.filter_thread.start()
    
    def closeEvent(self, event):
        """Maneja el evento de cierre del diálogo, asegurando que los hilos se detengan correctamente"""
        try:
            # Crear una copia de la lista de hilos para evitar modificarla durante la iteración
            threads_copy = self.threads.copy() if hasattr(self, 'threads') else []
            
            for thread in threads_copy:
                try:
                    # Verificar si el hilo todavía existe y es válido antes de intentar usarlo
                    if thread is not None and hasattr(thread, 'isRunning') and thread.isRunning():
                        thread.quit()
                        success = thread.wait(500)  # Esperar máximo 500ms para no bloquear la interfaz
                        
                        # Si sigue ejecutándose y aún es válido, terminarlo a la fuerza
                        if not success and hasattr(thread, 'isRunning') and thread.isRunning():
                            thread.terminate()
                except RuntimeError:
                    # Ignorar errores si el objeto ya fue eliminado
                    pass
                except Exception as e:
                    print(f"Error al cerrar hilo individual: {str(e)}")
            
            # Limpiar la lista de hilos
            if hasattr(self, 'threads'):
                self.threads.clear()
                
        except Exception as e:
            print(f"Error general en closeEvent: {str(e)}")
        
        # Continuar con el evento de cierre normal
        super().closeEvent(event)

# Clase Worker modificada para filtrar por rol del usuario que realiza la acción
class FilterWorker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)
    
    def __init__(self, search_terms=None, filtro_rol=None):
        super().__init__()
        self.search_terms = search_terms or []
        self.filtro_rol = filtro_rol
    
    def run(self):
        """Filtra los datos en segundo plano"""
        try:
            # Emitir progreso inicial
            self.progress.emit(10)
            
            # Usar el modelo de trazabilidad para filtrar los datos
            # Importante: filtro_rol ahora filtra por el rol del usuario que realizó la acción
            datos = ModeloTrazabilidad.obtener_acciones(
                search_terms=self.search_terms,
                filtro_rol_usuario=self.filtro_rol if self.filtro_rol != "Todos" else None,
                limite=500  # Aumentar límite para mostrar más resultados relevantes
            )
            
            # Emitir progreso medio
            self.progress.emit(50)
            
            # Convertir tuplas a listas para compatibilidad con la señal
            if isinstance(datos, tuple):
                datos_lista = [list(fila) if isinstance(fila, tuple) else fila for fila in datos]
                
                # Emitir progreso casi completo
                self.progress.emit(90)
                self.finished.emit(datos_lista)
            else:
                # Emitir progreso casi completo
                self.progress.emit(90)
                self.finished.emit(datos)
                
            # Emitir progreso completo
            self.progress.emit(100)
                
        except Exception as e:
            print(f"Error al filtrar datos de trazabilidad: {str(e)}")
            self.progress.emit(100)
            self.finished.emit([])


# Clase Worker para cargar datos en segundo plano
class DataWorker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)
    
    def run(self):
        """Carga los datos de trazabilidad en segundo plano"""
        try:
            # Emitir progreso inicial
            self.progress.emit(10)
            
            # Simular intervalos de progreso para dar feedback visual
            timer = QElapsedTimer()
            timer.start()
            
            # Usar el modelo de trazabilidad para obtener los datos
            datos = ModeloTrazabilidad.obtener_acciones(limite=500)  # Aumentar límite pero con paginación
            
            # Calcular tiempo transcurrido para estadísticas
            elapsed = timer.elapsed()
            print(f"Tiempo de carga de datos: {elapsed} ms")
            
            # Emitir progreso medio
            self.progress.emit(50)
            
            # Convertir tuplas a listas para compatibilidad con la señal
            if isinstance(datos, tuple):
                datos_lista = [list(fila) if isinstance(fila, tuple) else fila for fila in datos]
                
                # Emitir progreso casi completo
                self.progress.emit(90)
                self.finished.emit(datos_lista)
            else:
                # Emitir progreso casi completo
                self.progress.emit(90)
                self.finished.emit(datos)
            
            # Emitir progreso completo
            self.progress.emit(100)
                
        except Exception as e:
            print(f"Error al cargar datos de trazabilidad: {str(e)}")
            self.progress.emit(100)
            self.finished.emit([])