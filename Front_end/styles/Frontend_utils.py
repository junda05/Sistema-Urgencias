from PyQt5.QtWidgets import (QCompleter, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QMessageBox, QFrame, QLayout,
                           QLineEdit, QFormLayout, QSizePolicy, QDesktopWidget, QDateTimeEdit, QCheckBox, 
                           QGridLayout, QGroupBox, QScrollArea, QListView)
from PyQt5.QtCore import Qt, QTimer, QRect, QSize, QStringListModel, QPoint, QDateTime, QTime
from Front_end.styles.styles import *
from Front_end.styles.components import StyledDialog
from Back_end.Manejo_DB import ModeloPaciente
import sys
import os

class DialogoFiltrar(StyledDialog):
    def __init__(self, parent=None, areas=None, areas_seleccionadas=None, 
                filtro_fecha_activo=False, fecha_inicio=None, fecha_fin=None):
        super().__init__("Filtrar Pacientes", 1200, parent)
        
        # Eliminar la configuración de ancho fijo para permitir responsividad
        # self.setFixedWidth(1200)
        
        self.areas = areas or {}
        self.areas_seleccionadas = areas_seleccionadas or []
        self.filtro_fecha_activo = filtro_fecha_activo
        self.fecha_inicio = fecha_inicio or QDateTime.currentDateTime().addDays(-7)
        self.fecha_fin = fecha_fin or QDateTime.currentDateTime()
        
        # Inicializar rutas correctamente
        if getattr(sys, 'frozen', False):
            self.ruta_base = sys._MEIPASS
        else:
            # Corregir: Usar la ruta base sin duplicar "Front_end"
            self.ruta_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        self.ruta_check = os.path.join(ruta_imagenes, "check.png")
        
        # Verificar si la imagen existe y mostrar un mensaje menos ambiguo
        if not os.path.exists(self.ruta_check):
            print(f"Advertencia: No se encontró la imagen de check en: {self.ruta_check}")
            print(f"Directorio actual: {os.getcwd()}")
            print(f"Directorio de imágenes: {ruta_imagenes}")
            print(f"Archivos en el directorio de imágenes: {os.listdir(ruta_imagenes) if os.path.exists(ruta_imagenes) else 'Directorio no existe'}")
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background_primary']};
                border-radius: 15px;
            }}
            QWidget {{
                font-family: 'Segoe UI', sans-serif;
            }}
        """)
        
        # Crear un layout principal con márgenes consistentes
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header con título y descripción
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['background_white']};")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setSpacing(12)
        
        # Título
        titulo = QLabel("Filtrar pacientes")
        titulo.setStyleSheet(f"""
            font-size: 26px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            background-color: {COLORS['background_white']};
            padding: 10px 0;
        """)
        titulo.setAlignment(Qt.AlignCenter)
        
        # Descripción
        descripcion = QLabel("Seleccione las áreas y/o el rango de fecha de ingreso para filtrar los pacientes:")
        descripcion.setWordWrap(True)
        descripcion.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            padding: 0px 5px 5px 5px;
            background-color: {COLORS['background_white']};
        """)
        descripcion.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(titulo)
        header_layout.addWidget(descripcion)
        
        # Línea divisoria
        divisor = QFrame()
        divisor.setFrameShape(QFrame.HLine)
        divisor.setFrameShadow(QFrame.Sunken)
        divisor.setStyleSheet(f"""
            color: #E0E0E0;
            background-color: #E0E0E0;
            max-height: 1px;
        """)
        header_layout.addWidget(divisor)
        
        # Añadir el header al layout principal con borde redondeado
        header.setObjectName("headerContainer")
        header.setStyleSheet(f"""
            #headerContainer {{
                background-color: {COLORS['background_white']};
                border-radius: 10px;
                border: 1px solid #F0F0F0;
            }}
        """)
        main_layout.addWidget(header)
        
        # Contenedor horizontal para áreas y fechas - Ajustamos la proporción
        sections_container = QWidget()
        sections_container.setStyleSheet("background-color: transparent;")
        sections_layout = QHBoxLayout(sections_container)
        sections_layout.setContentsMargins(0, 0, 0, 0)
        sections_layout.setSpacing(15)  # Mantener espacio horizontal entre secciones
        
        # Sección de filtros por área - Reducimos márgenes verticales
        area_section = QGroupBox("Filtrar por áreas")
        area_section.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLORS['background_transparent']};
                border-radius: 10px;
                border: 1px solid #F0F0F0;
                padding: 10px;
                margin-top: 35px; /* Reducido de 60px a 35px */
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 5px 8px;
                color: {COLORS['text_primary']};
                background-color: {COLORS['background_transparent']};
                border-radius: 5px;
                margin-top: 0px;
            }}
        """)
        area_layout = QVBoxLayout(area_section)
        area_layout.setContentsMargins(10, 15, 10, 10)  # Reducido de (15, 20, 15, 15)
        area_layout.setSpacing(10)  # Reducido de 15
        
        # Grid de checkboxes para áreas - más columnas
        content_container = QWidget()
        content_container.setObjectName("contentContainer")
        content_container.setStyleSheet(f"""
            #contentContainer {{
                background-color: white;
                border-radius: 10px;
                border: 1px solid #EEEEEE;
            }}
        """)
        grid_layout = QGridLayout(content_container)
        grid_layout.setContentsMargins(15, 15, 15, 15)
        grid_layout.setSpacing(10)  # Reducimos el espaciado para que quepan más elementos
        
        # Aumentar número de columnas para mejor distribución horizontal
        num_columnas = 4  # Aumentamos de 3 a 4 columnas
        
        # Estilo para los checkboxes
        checkbox_style = f"""
            QCheckBox {{
                color: {COLORS['text_primary']};
                font-size: 15px;
                font-weight: 500;
                spacing: 10px;
                padding: 8px;
                border-radius: 8px;
                background-color: #F7FAFD;
                border: 1px solid #F0F0F0;
            }}
            
            QCheckBox:hover {{
                background-color: #EDF5FF;
                border: 1px solid #E0E9F5;
            }}
            
            QCheckBox::indicator {{
                width: 24px;
                height: 24px;
                border-radius: 5px;
                border: 1.5px solid {COLORS['border_light']};
                background-color: white;
            }}
            
            QCheckBox::indicator:hover {{
                border: 1.5px solid {COLORS['button_primary']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {COLORS['background_white']};
                border: 1.5px solid {COLORS['button_primary']};
                image: url("{self.ruta_check.replace('\\', '/')}");
            }}
        """
        
        # Crear checkboxes en formato grid
        self.checkboxes = {}
        fila = 0
        columna = 0
        
        # Distribuir áreas en columnas más uniformemente
        sorted_areas = sorted(self.areas.keys())
        items_per_column = (len(sorted_areas) + num_columnas - 1) // num_columnas
        
        for index, area_name in enumerate(sorted_areas):
            # Calcular nueva posición basada en una distribución uniforme
            fila = index % items_per_column
            columna = index // items_per_column
            
            checkbox = QCheckBox(area_name)
            checkbox.setStyleSheet(checkbox_style)
            checkbox.setCursor(Qt.PointingHandCursor)
            checkbox.setMinimumHeight(38)  # Reducimos ligeramente la altura
            
            # Marcar el checkbox si el área ya estaba seleccionada
            if area_name in self.areas_seleccionadas:
                checkbox.setChecked(True)
            
            self.checkboxes[area_name] = checkbox
            
            # Añadir al grid layout
            grid_layout.addWidget(checkbox, fila, columna)
        
        # Botones de selección para áreas - Eliminado el fondo oscuro
        buttons_container = QWidget()
        buttons_container.setStyleSheet(f"background-color: {COLORS['background_white']};") # Fondo blanco para el contenedor
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 10, 0, 0)  # Añadimos margen superior para separar de los checkboxes
        buttons_layout.setSpacing(15)  # Aumentamos el espacio entre botones
        
        # Estilo de botones auxiliares - Color más oscuro para mejor contraste
        button_style_aux = f"""
            QPushButton {{
                background-color: {COLORS['button_primary']}; /* Cambiado a color primario para mejor visibilidad */
                color: white; /* Texto blanco para contraste */
                border: 1px solid {COLORS['button_primary']};
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
                min-height: 40px;
            }}
            
            QPushButton:hover {{
                background-color: #EDF5FF;
                border-color: {COLORS['button_primary']};
                color: {COLORS['button_primary_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {COLORS['button_primary']};
                color: white;
                border-color: {COLORS['button_primary']};
            }}
        """
        
        # Botones para seleccionar/deseleccionar todas las áreas
        btn_select_all = QPushButton("Seleccionar Todos")
        btn_select_all.setStyleSheet(button_style_aux)
        btn_select_all.setCursor(Qt.PointingHandCursor)
        btn_select_all.clicked.connect(self.select_all_areas)
        
        btn_unselect_all = QPushButton("Deseleccionar Todos")
        btn_unselect_all.setStyleSheet(button_style_aux)
        btn_unselect_all.setCursor(Qt.PointingHandCursor)
        btn_unselect_all.clicked.connect(self.unselect_all_areas)
        
        buttons_layout.addWidget(btn_select_all)
        buttons_layout.addWidget(btn_unselect_all)
        
        area_layout.addWidget(content_container)
        area_layout.addWidget(buttons_container)
        
        # Sección de filtros por fecha - Reducimos márgenes verticales también
        date_section = QGroupBox("Filtrar por fecha de ingreso")
        date_section.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLORS['background_transparent']};
                border-radius: 10px;
                border: 1px solid #F0F0F0;
                padding: 10px;
                margin-top: 35px; /* Reducido de 45px a 35px para alinear con área */
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 5px 8px;
                color: {COLORS['text_primary']};
                background-color: {COLORS['background_transparent']};
                border-radius: 5px;
                margin-top: 0px;
            }}
        """)
        date_layout = QVBoxLayout(date_section)
        date_layout.setContentsMargins(10, 15, 10, 10)  # Reducido de (15, 25, 15, 15)
        date_layout.setSpacing(10)  # Reducido de 20
        
        # Checkbox para activar/desactivar filtro de fecha - Añadimos margen inferior
        self.check_fecha = QCheckBox("Activar filtro por fecha de ingreso")
        self.check_fecha.setStyleSheet(checkbox_style + """
            margin-bottom: 10px;  /* Margen inferior para separar del contenedor de fechas */
            padding-bottom: 5px;
        """)
        self.check_fecha.setCursor(Qt.PointingHandCursor)
        self.check_fecha.setChecked(self.filtro_fecha_activo)
        self.check_fecha.stateChanged.connect(self.toggle_date_filter)
        date_layout.addWidget(self.check_fecha)
        
        # Contenedor para los selectores de fecha - Optimizamos el espaciado interno
        date_selectors = QWidget()
        date_selectors.setObjectName("dateContainer")
        date_selectors.setStyleSheet(f"""
            #dateContainer {{ 
                background-color: white;
                border-radius: 10px;
                border: 1px solid #EEEEEE;
                margin-top: 0px;
                min-height: 140px;
                width: 100%; /* Aseguramos que ocupe todo el ancho disponible */
            }}
        """)
        date_selector_layout = QFormLayout(date_selectors)
        date_selector_layout.setContentsMargins(20, 20, 20, 20)
        date_selector_layout.setSpacing(20)
        # Cambiar la política de crecimiento para que los campos no se expandan automáticamente
        date_selector_layout.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        
        # Mejoramos estilo de etiquetas de fecha para hacerlas más visibles
        label_style = f"""
            color: {COLORS['text_primary']};
            font-size: 15px; /* Aumentado de 14px */
            font-weight: 500;
            padding: 5px 0;
        """
        
        label_desde = QLabel("Desde:")
        label_desde.setStyleSheet(label_style)
        
        label_hasta = QLabel("Hasta:")
        label_hasta.setStyleSheet(label_style)
        
        self.ruta_icono_calendario = os.path.join(ruta_imagenes, "calendario.png")
        
        # Fecha inicial - Mejoramos el estilo y añadimos estilo para el calendario más moderno
        self.date_inicio = QDateTimeEdit(self.fecha_inicio)
        self.date_inicio.setCalendarPopup(True)
        self.date_inicio.setDisplayFormat("dd/MM/yyyy")
        self.date_inicio.setTime(QTime(0, 0, 0))
        # Calcular un ancho adecuado para la fecha más larga "dd/MM/yyyy"
        self.date_inicio.setFixedWidth(180)
        # Centrar el texto dentro del campo de fecha
        self.date_inicio.setAlignment(Qt.AlignCenter)
        self.date_inicio.setStyleSheet(f"""
            QDateTimeEdit {{
                background-color: {COLORS['background_white']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {BORDER_RADIUS['medium']};
                padding: 10px;
                padding-right: 35px; /* Espacio para el icono */
                min-height: 42px;
                color: {COLORS['text_primary']};
                font-size: 14px;
                font-weight: 500;
                text-align: center;
            }}
            
            QDateTimeEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 30px;
                border-left: 1px solid {COLORS['border_light']};
                image: url("{self.ruta_icono_calendario.replace('\\', '/')}");
                padding-right: 5px;
            }}
            
            /* Estilos modernos para el calendario emergente */
            QCalendarWidget {{
                background-color: {COLORS['background_white']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['button_primary']};
                selection-color: white;
                border: 1px solid {COLORS['border_light']};
            }}
            
            /* Barra de navegación del calendario */
            QCalendarWidget QWidget#qt_calendar_navigationbar {{ 
                background-color: {COLORS['background_header']};
                border-bottom: none;
                padding: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            
            /* Botones de navegación del calendario */
            QCalendarWidget QToolButton {{
                background-color: {COLORS['background_header']};
                color: {COLORS['text_primary']};
                border-radius: 4px;
                border: none;
                padding: 6px;
                font-weight: bold;
            }}
            
            QCalendarWidget QToolButton:hover {{
                background-color: {COLORS['button_primary_hover']};
                color: white;
            }}
            
            /* Desplegables de mes y año */
            QCalendarWidget QMenu {{
                background-color: {COLORS['background_white']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['button_primary']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {COLORS['button_primary']};
                selection-color: white;
            }}
            
            /* Ajustes para spinbox (año) */
            QCalendarWidget QSpinBox {{
                background-color: {COLORS['background_white']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['button_primary']};
                border-radius: 3px;
                padding: 3px;
                min-width: 70px;
                selection-background-color: {COLORS['button_primary']};
                selection-color: white;
            }}
            
            /* Headers de días de la semana */
            QCalendarWidget QTableView {{
                border: none;
                background-color: {COLORS['background_white']};
                selection-background-color: {COLORS['button_primary']};
                selection-color: white;
            }}
            
            QCalendarWidget QAbstractItemView:enabled {{
                background-color: {COLORS['background_white']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['button_primary']};
                selection-color: white;
            }}
            
            /* Días del calendario */
            QCalendarWidget QTableView:item {{
                border: none;
                padding: 3px;
            }}
            
            QCalendarWidget QTableView:item:hover {{
                background-color: {COLORS['background_readonly']};
                border-radius: 5px;
            }}
            
            QCalendarWidget QTableView:item:selected {{
                background-color: {COLORS['button_primary']};
                color: white;
                border-radius: 5px;
            }}
        """)
        self.date_inicio.setEnabled(self.filtro_fecha_activo)
        
        # Fecha final - Aplicamos los mismos estilos modernos del calendario
        self.date_fin = QDateTimeEdit(self.fecha_fin)
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setTime(QTime(23, 59, 59))
        # Aplicamos el mismo ancho fijo y alineación centrada
        self.date_fin.setFixedWidth(180)
        self.date_fin.setAlignment(Qt.AlignCenter)
        self.date_fin.setStyleSheet(self.date_inicio.styleSheet())
        self.date_fin.setEnabled(self.filtro_fecha_activo)
        
        date_selector_layout.addRow(label_desde, self.date_inicio)
        date_selector_layout.addRow(label_hasta, self.date_fin)
        
        date_layout.addWidget(date_selectors)
        sections_layout.addWidget(area_section)
        sections_layout.addWidget(date_section)
        
        # Añadir el contenedor horizontal al layout principal
        main_layout.addWidget(sections_container)
        
        # Reemplazar el layout predeterminado del diálogo con nuestro layout personalizado
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Ahora añadimos nuestro layout personalizado
        for i in range(main_layout.count()):
            item = main_layout.takeAt(0)
            if item.widget():
                self.layout.addWidget(item.widget())
            else:
                self.layout.addItem(item)
        
        # Botones de acción
        action_buttons = [
            ("Aplicar Filtros", self.aceptar_filtros, "primary"),
            ("Cancelar", self.reject, "danger")
        ]
        
        buttons_layout = self.add_button_row(action_buttons)
        
        # Estilo mejorado para los botones principales
        for i in range(buttons_layout.count()):
            widget = buttons_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setMinimumHeight(48)
                widget.setStyleSheet(widget.styleSheet() + """
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 8px;
                """)
        
        # Configurar tamaño responsivo del diálogo
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(800, 400)  # Más ancho que alto
        
        # Centrar en pantalla y ajustar tamaño
        self.centerDialog()
        self.adjustSize()

    def centerDialog(self):
        """Centra el diálogo en la pantalla y ajusta el tamaño de forma responsiva"""
        # Obtener dimensiones de la pantalla
        screen = QDesktopWidget().availableGeometry()
        
        # Establecer un tamaño fijo más adecuado para este diálogo específico
        # Reduciendo el ancho de 1000px a 800px
        dialog_width = 800
        dialog_height = min(700, int(screen.height() * 0.8))
        
        # Aplicar el tamaño directamente
        self.setFixedSize(dialog_width, dialog_height)
        
        # Calcular la posición centrada
        x_position = (screen.width() - dialog_width) // 2
        y_position = (screen.height() - dialog_height) // 2
        
        # Mover el diálogo a la posición centrada
        self.move(x_position, y_position)

    def toggle_date_filter(self, state):
        """Activa o desactiva los selectores de fecha"""
        enabled = state == Qt.Checked
        self.date_inicio.setEnabled(enabled)
        self.date_fin.setEnabled(enabled)
    
    def select_all_areas(self):
        """Selecciona todos los checkboxes de áreas"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
    
    def unselect_all_areas(self):
        """Deselecciona todos los checkboxes de áreas"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
    
    def obtener_areas_seleccionadas(self):
        """Retorna una lista con las áreas seleccionadas"""
        return [area for area, checkbox in self.checkboxes.items() if checkbox.isChecked()]
    
    def aceptar_filtros(self):
        """Valida los filtros y cierra el diálogo si son correctos"""
        # Verificar si el filtro por fecha está activo
        self.filtro_fecha_activo = self.check_fecha.isChecked()
        
        if self.filtro_fecha_activo:
            # Validar que la fecha de fin sea posterior a la de inicio
            if self.date_inicio.dateTime() > self.date_fin.dateTime():
                # Crear un mensaje de error estilizado en lugar del QMessageBox estándar
                if not hasattr(self, 'error_container'):
                    # Crear contenedor de error si no existe
                    self.error_container = QWidget()
                    self.error_container.setStyleSheet(f"""
                        background-color: rgba(255, 236, 236, 0.9);
                        border-radius: {BORDER_RADIUS['medium']};
                        margin-top: 10px;
                    """)
                    error_layout = QHBoxLayout(self.error_container)
                    error_layout.setContentsMargins(12, 10, 12, 10)
                    
                    self.error_icon = QLabel("⚠")
                    self.error_icon.setStyleSheet(f"""
                        color: #D32F2F;
                        font-size: 18px;
                        font-weight: bold;
                    """)
                    
                    self.error_message = QLabel("")
                    self.error_message.setWordWrap(True)
                    self.error_message.setStyleSheet(f"""
                        color: #D32F2F;
                        font-size: 15px;
                        font-weight: 500;
                    """)
                    
                    error_layout.addWidget(self.error_icon)
                    error_layout.addWidget(self.error_message, 1)
                    
                    # Agregar al layout principal antes de los botones
                    self.layout.insertWidget(self.layout.count()-1, self.error_container)
                
                # Mostrar mensaje de error
                self.error_message.setText("La fecha de inicio debe ser anterior a la fecha de fin")
                self.error_container.setVisible(True)
                
                # Programar para ocultar el mensaje después de 5 segundos
                QTimer.singleShot(5000, lambda: self.error_container.setVisible(False))
                return
                
            # Guardar las fechas seleccionadas con horas ajustadas
            fecha_inicio = self.date_inicio.dateTime()
            fecha_inicio_ajustada = QDateTime(fecha_inicio.date(), QTime(0, 0, 0))
            self.fecha_inicio = fecha_inicio_ajustada
            
            fecha_fin = self.date_fin.dateTime() 
            fecha_fin_ajustada = QDateTime(fecha_fin.date(), QTime(23, 59, 59))
            self.fecha_fin = fecha_fin_ajustada
        
        # Obtener las áreas seleccionadas
        self.areas_seleccionadas = self.obtener_areas_seleccionadas()
        
        # Todo correcto, aceptar el diálogo
        self.accept()

class LabsSelector(QWidget):
    def __init__(self, parent=None, ruta_base=None):
        super().__init__(parent)
        self.ruta_base = ruta_base
        self.labs_seleccionados = []  # Lista para almacenar [codigo, nombre]
        self.setup_ui()
        self.cargar_laboratorios()

    def setup_ui(self):
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)  # Espaciado más consistente
        
        # Campo de búsqueda con autocompletado mejorado
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar laboratorio por nombre o código...")
        self.search_input.setStyleSheet(f"""
            background-color: white;
            border: 1px solid {COLORS['border_light']};
            border-radius: {BORDER_RADIUS['medium']};
            padding: 12px 16px;
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-family: 'Segoe UI', sans-serif;
            min-height: 20px;
        """)
        self.completer = QCompleter([])
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        
        # Estilo mejorado para el popup de autocompletado
        completer_popup = QListView()
        completer_popup.setStyleSheet(f"""
            background-color: white;
            border: 1px solid {COLORS['button_primary']};
            border-radius: 6px;
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-family: 'Segoe UI', sans-serif;
            padding: 8px;
            selection-background-color: {COLORS['button_primary']};
            selection-color: white;
            outline: none;
            margin: 2px;
        """)
        self.completer.setPopup(completer_popup)
        self.search_input.setCompleter(self.completer)
        
        self.add_button = QPushButton("Agregar")
        self.add_button.setCursor(Qt.PointingHandCursor)
        self.add_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_primary']};
                color: white;
                border: none;
                border-radius: {BORDER_RADIUS['medium']};
                padding: 10px 15px;
                font-weight: bold;
                font-size: 15px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['button_primary_hover']};
                border: 1px solid {COLORS['button_primary']};
            }}
            QPushButton:pressed {{
                background-color: #3D72A4;
            }}
        """)
        
        search_layout.addWidget(self.search_input, 4)
        search_layout.addWidget(self.add_button, 1)
        
        # Header con título y botón para limpiar todo
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        label_title = QLabel("Laboratorios seleccionados:")
        label_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-weight: bold;
            margin-top: 5px;
        """)
        
        self.clear_all_button = QPushButton("Limpiar todos")
        self.clear_all_button.setCursor(Qt.PointingHandCursor)
        self.clear_all_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_danger']};
                color: white;
                border: none;
                border-radius: {BORDER_RADIUS['small']};
                padding: 4px 12px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #FF3333;
            }}
            QPushButton:pressed {{
                background-color: #CC0000;
            }}
        """)
        self.clear_all_button.clicked.connect(self.limpiar_todos_laboratorios)
        
        header_layout.addWidget(label_title)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_all_button)
        
        # ScrollArea mejorada para los tags de laboratorios
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['background_white']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {BORDER_RADIUS['medium']};
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
        
        # Nuevo contenedor para los tags con ancho completo
        self.tags_container = QWidget()
        self.tags_layout = QVBoxLayout()  # Cambiado a QVBoxLayout para asegurar ancho completo
        self.tags_layout.setSpacing(8)
        self.tags_layout.setContentsMargins(8, 8, 8, 8)
        self.tags_layout.setAlignment(Qt.AlignTop)  # Alinear tags en la parte superior
        self.tags_container.setLayout(self.tags_layout)
        self.tags_container.setStyleSheet(f"""
            background-color: {COLORS['background_white']};
            padding: 0px;
        """)
        
        self.scroll_area.setWidget(self.tags_container)
        
        # Area para mostrar mensajes de error con mejor estilo - sin borde disruptivo
        self.error_container = QWidget()
        self.error_container.setVisible(False)
        self.error_container.setStyleSheet(f"""
            background-color: rgba(255, 236, 236, 0.8);
            border-radius: {BORDER_RADIUS['medium']};
            margin-top: 8px;
        """)
        error_layout = QHBoxLayout(self.error_container)
        error_layout.setContentsMargins(12, 10, 12, 10)
        
        self.error_icon = QLabel("⚠")
        self.error_icon.setStyleSheet(f"""
            color: #D32F2F;
            font-size: 18px;
            font-weight: bold;
        """)
        
        self.error_message = QLabel("")
        self.error_message.setWordWrap(True)
        self.error_message.setStyleSheet(f"""
            color: #D32F2F;
            font-size: 15px;
        """)
        
        error_layout.addWidget(self.error_icon)
        error_layout.addWidget(self.error_message, 1)
        
        # Conectar eventos
        self.add_button.clicked.connect(self.agregar_laboratorio)
        self.search_input.returnPressed.connect(self.agregar_laboratorio)
        
        # Añadir widgets al layout principal
        layout.addLayout(search_layout)
        layout.addSpacing(8)
        layout.addLayout(header_layout)
        layout.addWidget(self.scroll_area, 1)  # Dar prioridad de expansión
        layout.addWidget(self.error_container)
        
        # Establecer una altura mínima responsiva para el área de scroll
        screen_height = QDesktopWidget().availableGeometry().height()
        self.scroll_area.setMinimumHeight(min(int(screen_height * 0.15), 180))  # 15% de altura de pantalla, max 180px

    def mostrar_error(self, mensaje):
        self.error_message.setText(mensaje)
        self.error_container.setVisible(True)
        
        # Ocultar el mensaje después de 5 segundos
        QTimer.singleShot(5000, lambda: self.error_container.setVisible(False))

    def cargar_laboratorios(self):
        try:
            # Obtener la lista de laboratorios de la base de datos
            conn = ModeloPaciente().conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT codigo_lab, nombre_lab FROM laboratorios ORDER BY nombre_lab")
            self.laboratorios = cursor.fetchall()
            conn.close()
            
            # Crear lista para el autocompletado
            items = [f"{lab[0]} - {lab[1]}" for lab in self.laboratorios]
            
            # Actualizar el completer
            model = QStringListModel()
            model.setStringList(items)
            self.completer.setModel(model)
            
        except Exception as e:
            print(f"Error al cargar laboratorios: {str(e)}")
            self.laboratorios = []

    def agregar_laboratorio(self):
        texto = self.search_input.text().strip()
        if not texto:
            return
            
        # Buscar si existe el laboratorio
        encontrado = False
        for codigo, nombre in self.laboratorios:
            if texto.startswith(codigo) or codigo in texto or nombre.lower() in texto.lower():
                encontrado = True
                # Verificar que no esté ya agregado
                if not any(lab[0] == codigo for lab in self.labs_seleccionados):
                    self.labs_seleccionados.append([codigo, nombre])
                    self.crear_etiqueta(codigo, nombre)
                    self.search_input.clear()
                    # Hacer focus en el input para continuar agregando
                    self.search_input.setFocus()
                else:
                    self.mostrar_error(f"El laboratorio '{nombre}' ya ha sido agregado")
                break
                
        if not encontrado:
            self.mostrar_error("El laboratorio ingresado no existe en la base de datos.")

    def crear_etiqueta(self, codigo, nombre):
        # Crear widget para la etiqueta con ancho completo
        tag = QFrame()
        tag.setObjectName("lab_tag")
        tag.setFixedHeight(40)  # Establecer altura fija para todos los tags
        tag.setStyleSheet(f"""
            #lab_tag {{
                background-color: {COLORS['background_header']};
                color: {COLORS['text_primary']};
                border: 1px solid #E0E0E0;
                border-radius: {BORDER_RADIUS['medium']};
                margin: 2px 0;
                width: 100%;
            }}
            #lab_tag:hover {{
                background-color: #EDF5FF;
                border-color: #D0E0F0;
            }}
        """)
        
        # Layout horizontal para la etiqueta con mejor distribución
        tag_layout = QHBoxLayout(tag)
        tag_layout.setContentsMargins(12, 0, 8, 0)  # Reducir margen vertical para ajustar a altura fija
        tag_layout.setSpacing(10)
        
        # Texto de la etiqueta con mejor estilo
        texto = QLabel(f"{codigo} - {nombre}")
        texto.setWordWrap(True)
        texto.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        texto.setStyleSheet(f"""
            font-size: 14px;
            font-family: 'Segoe UI', sans-serif;
            color: {COLORS['text_primary']};
            background: transparent;
            padding: 2px 0;
        """)
        
        # Botón para eliminar con mejor tamaño y estilo - ajustado para centrado vertical
        btn_eliminar = QPushButton("×")
        btn_eliminar.setObjectName("btn_eliminar_lab")
        btn_eliminar.setCursor(Qt.PointingHandCursor)
        btn_eliminar.setFixedSize(22, 22)  # Ligeramente más grande para mejor click
        btn_eliminar.setStyleSheet(f"""
            #btn_eliminar_lab {{
                background-color: #FF6B6B;
                color: white;
                border-radius: 11px;
                font-weight: bold;
                font-size: 16px;
                padding: 0;
                margin: 0;
                border: none;
                line-height: 1;
                min-width: 22px;
                max-width: 22px;
                min-height: 22px;
                max-height: 22px;
            }}
            #btn_eliminar_lab:hover {{
                background-color: #FF0000;
            }}
            #btn_eliminar_lab:pressed {{
                background-color: #CC0000;
            }}
        """)
        
        # Conectar evento para eliminar
        btn_eliminar.clicked.connect(lambda: self.eliminar_etiqueta(tag, codigo))
        
        # Añadir elementos al layout
        tag_layout.addWidget(texto, 1)
        tag_layout.addWidget(btn_eliminar, 0, Qt.AlignVCenter)
        
        # Añadir etiqueta al contenedor usando insertWidget para colocar en la parte superior
        self.tags_layout.insertWidget(0, tag)  # Insertar al inicio para que el último añadido vaya al principio
        
        # Ajustar altura mínima según el número de elementos
        self.ajustar_altura_minima()

    def eliminar_etiqueta(self, tag, codigo):
        # Eliminar etiqueta visualmente
        self.tags_layout.removeWidget(tag)
        tag.deleteLater()
        
        # Eliminar de la lista de seleccionados
        self.labs_seleccionados = [lab for lab in self.labs_seleccionados if lab[0] != codigo]
        
        # Ajustar altura mínima según el número de elementos
        self.ajustar_altura_minima()

    def limpiar_todos_laboratorios(self):
        # Eliminar todas las etiquetas visuales
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Limpiar la lista de seleccionados
        self.labs_seleccionados = []
        
        # Ajustar altura mínima
        self.ajustar_altura_minima()

    def ajustar_altura_minima(self):
        # Ajustar altura mínima del área de scroll según el contenido pero manteniendo proporción con la pantalla
        screen_height = QDesktopWidget().availableGeometry().height()
        base_height = min(int(screen_height * 0.15), 180)
        
        # Mantenemos la altura base para asegurar consistencia
        if self.tags_layout.count() > 0:
            # Calcular altura estimada basada en el número de elementos
            altura_por_item = 44  # Altura estimada por etiqueta (40px + margen)
            altura_contenido = min(self.tags_layout.count() * altura_por_item, int(screen_height * 0.3))
            altura_deseada = max(base_height, altura_contenido + 20)
            self.scroll_area.setMinimumHeight(altura_deseada)
        else:
            self.scroll_area.setMinimumHeight(base_height)

    def get_laboratorios_seleccionados(self):
        return self.labs_seleccionados

    def set_laboratorios_seleccionados(self, laboratorios):
        # Limpiar selección actual
        self.limpiar_todos_laboratorios()
                
        # Añadir los nuevos laboratorios
        for codigo, nombre in laboratorios:
            self.labs_seleccionados.append([codigo, nombre])
            self.crear_etiqueta(codigo, nombre)

class IxsSelector(QWidget):
    def __init__(self, parent=None, ruta_base=None):
        super().__init__(parent)
        self.ruta_base = ruta_base
        self.ixs_seleccionados = []  # Lista para almacenar [codigo, nombre]
        self.setup_ui()
        self.cargar_imagenes()

    def setup_ui(self):
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)  # Espaciado más consistente
        
        # Campo de búsqueda con autocompletado mejorado
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar imagen por nombre o código...")
        self.search_input.setStyleSheet(f"""
            background-color: white;
            border: 1px solid {COLORS['border_light']};
            border-radius: {BORDER_RADIUS['medium']};
            padding: 12px 16px;
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-family: 'Segoe UI', sans-serif;
            min-height: 20px;
        """)
        self.completer = QCompleter([])
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        
        # Estilo mejorado para el popup de autocompletado
        completer_popup = QListView()
        completer_popup.setStyleSheet(f"""
            background-color: white;
            border: 1px solid {COLORS['button_primary']};
            border-radius: 6px;
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-family: 'Segoe UI', sans-serif;
            padding: 8px;
            selection-background-color: {COLORS['button_primary']};
            selection-color: white;
            outline: none;
            margin: 2px;
        """)
        self.completer.setPopup(completer_popup)
        self.search_input.setCompleter(self.completer)
        
        self.add_button = QPushButton("Agregar")
        self.add_button.setCursor(Qt.PointingHandCursor)
        self.add_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_primary']};
                color: white;
                border: none;
                border-radius: {BORDER_RADIUS['medium']};
                padding: 10px 15px;
                font-weight: bold;
                font-size: 15px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['button_primary_hover']};
                border: 1px solid {COLORS['button_primary']};
            }}
            QPushButton:pressed {{
                background-color: #3D72A4;
            }}
        """)
        
        search_layout.addWidget(self.search_input, 4)
        search_layout.addWidget(self.add_button, 1)
        
        # Header con título y botón para limpiar todo
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        label_title = QLabel("Imágenes seleccionadas:")
        label_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-weight: bold;
            margin-top: 5px;
        """)
        
        self.clear_all_button = QPushButton("Limpiar todos")
        self.clear_all_button.setCursor(Qt.PointingHandCursor)
        self.clear_all_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_danger']};
                color: white;
                border: none;
                border-radius: {BORDER_RADIUS['small']};
                padding: 4px 12px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #FF3333;
            }}
            QPushButton:pressed {{
                background-color: #CC0000;
            }}
        """)
        self.clear_all_button.clicked.connect(self.limpiar_todas_imagenes)
        
        header_layout.addWidget(label_title)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_all_button)
        
        # ScrollArea mejorada para los tags de imágenes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['background_white']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {BORDER_RADIUS['medium']};
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
        
        # Nuevo contenedor para los tags con ancho completo
        self.tags_container = QWidget()
        self.tags_layout = QVBoxLayout()  # Cambiado a QVBoxLayout para asegurar ancho completo
        self.tags_layout.setSpacing(8)
        self.tags_layout.setContentsMargins(8, 8, 8, 8)
        self.tags_layout.setAlignment(Qt.AlignTop)  # Alinear tags en la parte superior
        self.tags_container.setLayout(self.tags_layout)
        self.tags_container.setStyleSheet(f"""
            background-color: {COLORS['background_white']};
            padding: 0px;
        """)
        
        self.scroll_area.setWidget(self.tags_container)
        
        # Area para mostrar mensajes de error con mejor estilo - sin borde disruptivo
        self.error_container = QWidget()
        self.error_container.setVisible(False)
        self.error_container.setStyleSheet(f"""
            background-color: rgba(255, 236, 236, 0.8);
            border-radius: {BORDER_RADIUS['medium']};
            margin-top: 8px;
        """)
        error_layout = QHBoxLayout(self.error_container)
        error_layout.setContentsMargins(12, 10, 12, 10)
        
        self.error_icon = QLabel("⚠")
        self.error_icon.setStyleSheet(f"""
            color: #D32F2F;
            font-size: 18px;
            font-weight: bold;
        """)
        
        self.error_message = QLabel("")
        self.error_message.setWordWrap(True)
        self.error_message.setStyleSheet(f"""
            color: #D32F2F;
            font-size: 15px;
        """)
        
        error_layout.addWidget(self.error_icon)
        error_layout.addWidget(self.error_message, 1)
        
        # Conectar eventos
        self.add_button.clicked.connect(self.agregar_imagen)
        self.search_input.returnPressed.connect(self.agregar_imagen)
        
        # Añadir widgets al layout principal
        layout.addLayout(search_layout)
        layout.addSpacing(8)
        layout.addLayout(header_layout)
        layout.addWidget(self.scroll_area, 1)  # Dar prioridad de expansión
        layout.addWidget(self.error_container)
        
        # Establecer una altura mínima responsiva para el área de scroll
        screen_height = QDesktopWidget().availableGeometry().height()
        self.scroll_area.setMinimumHeight(min(int(screen_height * 0.15), 180))

    def mostrar_error(self, mensaje):
        self.error_message.setText(mensaje)
        self.error_container.setVisible(True)
        
        # Ocultar el mensaje después de 5 segundos
        QTimer.singleShot(5000, lambda: self.error_container.setVisible(False))

    def cargar_imagenes(self):
        try:
            # Obtener la lista de imágenes de la base de datos
            conn = ModeloPaciente().conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT codigo_ix, nombre_ix FROM imagenes ORDER BY nombre_ix")
            self.imagenes = cursor.fetchall()
            conn.close()
            
            # Crear lista para el autocompletado
            items = [f"{img[0]} - {img[1]}" for img in self.imagenes]
            
            # Actualizar el completer
            model = QStringListModel()
            model.setStringList(items)
            self.completer.setModel(model)
            
        except Exception as e:
            print(f"Error al cargar imágenes: {str(e)}")
            self.imagenes = []

    def agregar_imagen(self):
        texto = self.search_input.text().strip()
        if not texto:
            return
            
        # Buscar si existe la imagen
        encontrado = False
        for codigo, nombre in self.imagenes:
            if texto.startswith(codigo) or codigo in texto or nombre.lower() in texto.lower():
                encontrado = True
                # Verificar que no esté ya agregada
                if not any(img[0] == codigo for img in self.ixs_seleccionados):
                    self.ixs_seleccionados.append([codigo, nombre])
                    self.crear_etiqueta(codigo, nombre)
                    self.search_input.clear()
                    # Hacer focus en el input para continuar agregando
                    self.search_input.setFocus()
                else:
                    self.mostrar_error(f"La imagen '{nombre}' ya ha sido agregada")
                break
                
        if not encontrado:
            self.mostrar_error("La imagen ingresada no existe en la base de datos.")

    def crear_etiqueta(self, codigo, nombre):
        # Crear widget para la etiqueta con ancho completo
        tag = QFrame()
        tag.setObjectName("ix_tag")
        tag.setFixedHeight(40)  # Establecer altura fija para todos los tags
        tag.setStyleSheet(f"""
            #ix_tag {{
                background-color: {COLORS['background_header']};
                color: {COLORS['text_primary']};
                border: 1px solid #E0E0E0;
                border-radius: {BORDER_RADIUS['medium']};
                margin: 2px 0;
                width: 100%;
            }}
            #ix_tag:hover {{
                background-color: #EDF5FF;
                border-color: #D0E0F0;
            }}
        """)
        
        # Layout horizontal para la etiqueta con mejor distribución
        tag_layout = QHBoxLayout(tag)
        tag_layout.setContentsMargins(12, 0, 8, 0)  # Reducir margen vertical para ajustar a altura fija
        tag_layout.setSpacing(10)
        
        # Texto de la etiqueta con mejor estilo
        texto = QLabel(f"{codigo} - {nombre}")
        texto.setWordWrap(True)
        texto.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        texto.setStyleSheet(f"""
            font-size: 14px;
            font-family: 'Segoe UI', sans-serif;
            color: {COLORS['text_primary']};
            background: transparent;
            padding: 2px 0;
        """)
        
        # Botón para eliminar con mejor tamaño y estilo - ajustado para centrado vertical
        btn_eliminar = QPushButton("×")
        btn_eliminar.setObjectName("btn_eliminar_ix")
        btn_eliminar.setCursor(Qt.PointingHandCursor)
        btn_eliminar.setFixedSize(22, 22)  # Ligeramente más grande para mejor click
        btn_eliminar.setStyleSheet(f"""
            #btn_eliminar_ix {{
                background-color: #FF6B6B;
                color: white;
                border-radius: 11px;
                font-weight: bold;
                font-size: 16px;
                padding: 0;
                margin: 0;
                border: none;
                line-height: 1;
                min-width: 22px;
                max-width: 22px;
                min-height: 22px;
                max-height: 22px;
            }}
            #btn_eliminar_ix:hover {{
                background-color: #FF0000;
            }}
            #btn_eliminar_ix:pressed {{
                background-color: #CC0000;
            }}
        """)
        
        # Conectar evento para eliminar
        btn_eliminar.clicked.connect(lambda: self.eliminar_etiqueta(tag, codigo))
        
        # Añadir elementos al layout
        tag_layout.addWidget(texto, 1)
        tag_layout.addWidget(btn_eliminar, 0, Qt.AlignVCenter)
        
        # Añadir etiqueta al contenedor usando insertWidget para colocar en la parte superior
        self.tags_layout.insertWidget(0, tag)  # Insertar al inicio para que el último añadido vaya al principio
        
        # Ajustar altura mínima según el número de elementos
        self.ajustar_altura_minima()

    def eliminar_etiqueta(self, tag, codigo):
        # Eliminar etiqueta visualmente
        self.tags_layout.removeWidget(tag)
        tag.deleteLater()
        
        # Eliminar de la lista de seleccionados
        self.ixs_seleccionados = [img for img in self.ixs_seleccionados if img[0] != codigo]
        
        # Ajustar altura mínima según el número de elementos
        self.ajustar_altura_minima()

    def limpiar_todas_imagenes(self):
        # Eliminar todas las etiquetas visuales
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Limpiar la lista de seleccionados
        self.ixs_seleccionados = []
        
        # Ajustar altura mínima
        self.ajustar_altura_minima()

    def ajustar_altura_minima(self):
        # Ajustar altura mínima del área de scroll según el contenido pero manteniendo proporción con la pantalla
        screen_height = QDesktopWidget().availableGeometry().height()
        base_height = min(int(screen_height * 0.15), 180)
        
        # Mantenemos la altura base para asegurar consistencia
        if self.tags_layout.count() > 0:
            # Calcular altura estimada basada en el número de elementos
            altura_por_item = 44  # Altura estimada por etiqueta (40px + margen)
            altura_contenido = min(self.tags_layout.count() * altura_por_item, int(screen_height * 0.3))
            altura_deseada = max(base_height, altura_contenido + 20)
            self.scroll_area.setMinimumHeight(altura_deseada)
        else:
            self.scroll_area.setMinimumHeight(base_height)

    def get_imagenes_seleccionadas(self):
        return self.ixs_seleccionados

    def set_imagenes_seleccionadas(self, imagenes):
        # Limpiar selección actual
        self.limpiar_todas_imagenes()
                
        # Añadir las nuevas imágenes
        for codigo, nombre in imagenes:
            self.ixs_seleccionados.append([codigo, nombre])
            self.crear_etiqueta(codigo, nombre)

class QFlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self.itemList = []
        self.margin = margin
        self.setSpacing(spacing)
        
    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
            
    def addItem(self, item):
        self.itemList.append(item)
        
    def count(self):
        return len(self.itemList)
        
    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None
        
    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None
        
    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))
        
    def hasHeightForWidth(self):
        return True
        
    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height
        
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)
        
    def sizeHint(self):
        return QSize(100, 100)
        
    def minimumSize(self):
        size = QSize(0, 0)
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.margin, 2 * self.margin)
        return size
        
    def doLayout(self, rect, testOnly):
        x = rect.x() + self.margin
        y = rect.y() + self.margin
        lineHeight = 0
        
        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
                
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x() + self.margin
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
                
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
                
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
            
        return y + lineHeight - rect.y() + self.margin