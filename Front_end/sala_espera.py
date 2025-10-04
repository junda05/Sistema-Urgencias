from PyQt5.QtWidgets import (QMainWindow, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTableWidget, QTableWidgetItem, QPushButton, 
                           QLabel, QMessageBox, QFrame, QDesktopWidget, 
                           QApplication, QGraphicsOpacityEffect, QCheckBox,
                           QGroupBox, QComboBox, QDialog, QSizePolicy, QGridLayout)
from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QEvent
from PyQt5.QtGui import QFont, QPixmap, QIcon, QLinearGradient, QBrush, QPalette, QColor, QPainter
from Back_end.Usuarios.ModeloSalaEspera import ModeloSalaEspera
import sys
import os
# Importar componentes de animación desde su ubicación correcta
from Front_end.styles.animation_components import SplashScreen
# Importar estilos y componentes
from Front_end.styles.styles import *
from Front_end.styles.components import StyledMessageBox, StyledButton, StyledDialog
# Importar componentes de tablas - Actualizado para usar los mismos estilos de Front_end.py
from Front_end.styles.table_components import Estado_delegado_circulo, TextDelegate, Personalizado_Columnas, configurar_tabla_estandar
# Importar componentes de header
from Front_end.styles.header_components import HeaderCombinado
# Importar widgets personalizados
from Front_end.styles.custom_widgets import TablaContainer
# Importar utilidades de fuentes
from Front_end.styles.font_utils import aplicar_fuentes_sistema
# Importar el nuevo menú lateral
from Front_end.styles.lateral_menu import LateralMenu, MenuToggleButton


class VistaSalaEspera(QMainWindow):
    def __init__(self, login_interface):
        super().__init__()
        self.login_interface = login_interface
        self.modelo = ModeloSalaEspera()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.pagina_actual = 0
        
        # Nuevas variables para el modo presentación
        self.modo_presentacion_activo = False  # Se activará más adelante
        self.timer_presentacion = QTimer(self)
        self.timer_presentacion.timeout.connect(self.mostrar_siguiente_pagina)
        
        # Definición de áreas (mismas que en VistaPaciente) - Colocada antes para poder inicializar areas_filtradas
        self.areas = {
            "Antigua": (1, 18),
            "Amarilla": (19, 38),
            "Pediatría": (39, 59),
            "Pasillos": (60, 200),
            "Clini": (1, 40),
            "Sala de espera": (1, 2),
        }
        
        # Importar el modelo de preferencias
        from Back_end.Usuarios.ModeloPreferencias import ModeloPreferencias
        from Back_end.Manejo_DB import ModeloAutenticacion
        
        # Obtener el usuario actual
        credenciales = ModeloAutenticacion.obtener_credenciales()
        self.usuario_actual = credenciales.get('usuario')
        
        # Cargar preferencias de filtro
        self.areas_filtradas = ModeloPreferencias.obtener_filtros_area(
            self.usuario_actual, list(self.areas.keys())
        )
        
        # Cargar el tiempo de paginación desde las preferencias
        self.intervalo_presentacion = ModeloPreferencias.obtener_tiempo_paginacion(
            self.usuario_actual, 10  # Valor predeterminado: 10 segundos
        )
        
        # Asegurar que siempre hay al menos un área seleccionada para evitar vista vacía
        if not self.areas_filtradas:
            self.areas_filtradas = list(self.areas.keys())
            print(f"No se encontraron filtros, usando todas las áreas")
        
        # Aplicar fuentes personalizadas inmediatamente
        aplicar_fuentes_sistema()
        
        # Obtener tamaño de pantalla para elementos responsivos
        self.pantalla = QDesktopWidget().screenGeometry()
        
        # Inicializar una bandera para rastrear la primera carga de la tabla
        self.primera_carga = True
        
        # Mostrar pantalla de carga mientras se inicializa la interfaz
        self.splash = SplashScreen(None, logo_path=None, message="Cargando sala de espera...", duration=1.5)
        self.splash.setFixedSize(int(self.pantalla.width() * 0.3), int(self.pantalla.height() * 0.3))
        self.splash.show()
        self.splash.opacity_animation.start()
        QApplication.processEvents()
        
        # Efecto de opacidad para animación de entrada
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)  # Iniciar invisible
        
        # Obtener rutas de recursos
        if getattr(sys, 'frozen', False):
            self.ruta_base = sys._MEIPASS
        else:
            self.ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        self.ruta_logo = os.path.join(ruta_imagenes, "logo_foscal.png")
        self.ruta_icono = os.path.join(ruta_imagenes, "logo.png")
        self.ruta_logou = os.path.join(ruta_imagenes, "u.png")
        
        # Establecer el icono de la ventana
        if os.path.exists(self.ruta_icono):
            self.setWindowIcon(QIcon(self.ruta_icono))
            
        # Variables para mover la ventana sin barra de título
        self.dragging = False
        self.offset = None
        
        # Headers para la tabla - Sin "Conducta" e "Ingreso"
        self.headers = ["Nombre", "Documento", "Triage", "CI", "Labs", "IMG", "Interconsulta", "RV", "Pendientes", "Ubicación"]
        
        # Crear menú lateral ANTES de configurar ventana y crear interfaz
        self.menu_lateral = LateralMenu(self)
        
        # Configurar ventana y crear interfaz
        self.configurar_ventana()
        self.crear_interfaz()
        
        # Configurar el menú lateral después de crear la interfaz
        self.configurar_menu_lateral()
        
        # Cerrar la pantalla de carga antes de mostrar la interfaz principal
        self.splash.accept()
        
        # Inicializar el timer para actualización automática
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
        
        # Añadir indicador de filtros activos - Moverlo antes de actualizar tabla
        self.crear_indicador_filtros()
        
        # Actualizar tabla por primera vez después de que la interfaz está completa
        # Esto garantiza que se usen los filtros persistentes desde el inicio
        self.actualizar_tabla()
        
        # Inicializar y activar el modo presentación automáticamente después de cargar datos
        QTimer.singleShot(500, self.activar_modo_presentacion)

    def enmascarar_nombre(self, nombre):
        """Enmascara el nombre mostrando las primeras 3 letras de cada palabra"""
        if not nombre:
            return nombre
        
        # Para pacientes NN, proteger especialmente con formato diferente
        if nombre.startswith('NN -'):
            # Mostrar solo "NN" y ocultar la marca de tiempo
            partes = nombre.split(' - ', 1)
            if len(partes) > 1:
                return "NN - ***********"
            return nombre
            
        partes = nombre.split()
        if len(partes) <= 1:
            return nombre
            
        # Mostrar primeras 3 letras de cada palabra
        resultado = []
        for parte in partes:
            if len(parte) <= 3:
                resultado.append(parte)  # No enmascarar palabras muy cortas
            else:
                # Mostrar las primeras 3 letras y enmascarar el resto
                caracteres_visibles = 3
                resultado.append(parte[:caracteres_visibles] + "*" * (len(parte) - caracteres_visibles))
        
        return " ".join(resultado)
    
    def enmascarar_documento(self, doc):
        """Enmascara el documento mostrando los últimos 4 dígitos"""
        if not doc:
            return doc
            
        # Para documentos de pacientes NN usar formato especial
        if doc.startswith('NN-'):
            return "NN-****"
            
        if len(doc) <= 4:
            return doc  # No enmascarar documentos muy cortos
            
        # Mostrar solo los últimos 4 dígitos
        masked_part = "*" * (len(doc) - 4)
        visible_part = doc[-4:]
        return masked_part + visible_part
    
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

    def configurar_ventana(self):
        self.setWindowTitle("Sala de Espera")
        self.setStyleSheet("background-color: #4A7296;")
        self.showMaximized()
    
    def crear_interfaz(self):
        # Widget central principal
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)  # Eliminar espacio entre widgets

        # Crear y agregar barra combinada con logo
        header_combinado = self.crear_header_combinado()
        layout_principal.addWidget(header_combinado)

        # Crear contenedor para el contenido principal
        contenedor_contenido = QWidget()
        layout_contenido = QVBoxLayout(contenedor_contenido)
        layout_contenido.setContentsMargins(20, 30, 20, 20)  # Reducido margen superior de 50 a 30
        layout_contenido.setSpacing(8)  # Reducido de 15 a 8 para menos espacio vertical
        
        # Contenedor para el indicador de filtros (se añadirá después)
        self.contenedor_filtros = QWidget()
        self.layout_filtros = QHBoxLayout(self.contenedor_filtros)
        self.layout_filtros.setContentsMargins(0, 2, 0, 2)  # Reducido de 0,5,0,5 a 0,2,0,2
        layout_contenido.addWidget(self.contenedor_filtros)
        
        # Crear tabla con tamaño limitado
        contenedor_tabla = self.crear_contenedor_tabla()
        layout_contenido.addWidget(contenedor_tabla)

        # Agregar el contenedor de contenido al layout principal
        layout_principal.addWidget(contenedor_contenido)
    
    def crear_header_combinado(self):
        # Crear un contenedor combinado para el título y el logo
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['background_header']};")
        
        # Calcular tamaños para asegurar que coincidan con la interfaz de login
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
        
        # Agregar botón de menú
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
        if os.path.exists(self.ruta_logou):
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
        # Usar el TablaContainer reutilizable con tamaños más apropiados
        contenedor_tabla = TablaContainer(self, 0.96, 0.705)  # Aumentado de 0.75, 0.55 para hacer la tabla más grande
        
        # Crear la tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(self.headers))
        self.tabla.setHorizontalHeaderLabels(self.headers)
        
        # Aplicar estilos de tabla mejorados - usando los mismos de Front_end.py
        self.tabla.setStyleSheet(TABLE_STYLES_UPDATED["main"] + SCROLLBAR_STYLE)
        
        # Ocultar números de fila
        self.tabla.verticalHeader().setVisible(False)
        
        # Configurar delegado para círculos coloreados
        circle_delegate = Estado_delegado_circulo(self.tabla)
        estado_columns = ['Triage', 'CI', 'Labs', 'IMG', 'Interconsulta', 'RV']
        for header in estado_columns:
            col_index = self.headers.index(header)
            self.tabla.setItemDelegateForColumn(col_index, circle_delegate)
        
        # Configurar delegado para celdas de texto para mostrar tooltips
        text_delegate = TextDelegate(self.tabla)
        for col in range(self.tabla.columnCount()):
            if col not in [self.headers.index(h) for h in estado_columns]:
                self.tabla.setItemDelegateForColumn(col, text_delegate)
                
        # Asegurarse de que el delegado esté correctamente configurado para todas las columnas
        for col_index in [self.headers.index(header) for header in estado_columns]:
            delegate = self.tabla.itemDelegateForColumn(col_index)
            if isinstance(delegate, Estado_delegado_circulo):
                delegate.alarm_cells = set()  # Inicializar para evitar problemas
                delegate.conducta_alarm_cells = set()  # Inicializar también este conjunto
        
        # Habilitar desplazamiento suave
        self.tabla.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.tabla.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        
        # Configuración de estilo para la tabla
        self.tabla.setAlternatingRowColors(False)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.clearSelection()
        self.tabla.setCurrentCell(-1, -1)
        
        # Usar la misma fuente que en Front_end.py para consistencia
        self.tabla.setFont(QFont("Segoe UI", 10))
        
        # Mejorar el estilo de los encabezados
        header_font = QFont("Segoe UI", 10)
        header_font.setBold(True)
        self.tabla.horizontalHeader().setFont(header_font)
        
        self.tabla.setWordWrap(True)
        
        # Agregar la tabla al contenedor
        contenedor_tabla.set_tabla(self.tabla)
        
        return contenedor_tabla
    
    def configurar_menu_lateral(self):
        """Configura las opciones del menú lateral"""
        # Obtener rutas de íconos
        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        ruta_icono_filtro = os.path.join(ruta_imagenes, "filtrar.png")
        ruta_icono_logout = os.path.join(ruta_imagenes, "logout_icon.png")
        ruta_icono_presentacion = os.path.join(ruta_imagenes, "pagination.png")
        
        # Añadir botón de filtrado
        self.menu_lateral.add_menu_button("Filtrar", 
                                         ruta_icono_filtro if os.path.exists(ruta_icono_filtro) else None, 
                                         self.mostrar_dialog_filtrado)
        
        # Modificar el botón de modo presentación para que solo muestre la configuración
        self.menu_lateral.add_menu_button("Configurar tiempo", 
                                         ruta_icono_presentacion if os.path.exists(ruta_icono_presentacion) else None, 
                                         self.mostrar_configuracion_presentacion)
        
        # Agregar espacio entre los botones y el botón de cerrar sesión
        self.menu_lateral.add_spacer()
        
        # Botón de cerrar sesión al final
        self.menu_lateral.add_menu_button("Cerrar Sesión", 
                                         ruta_icono_logout if os.path.exists(ruta_icono_logout) else None, 
                                         self.logout, 
                                         "danger")
        
        # Asegurar que el menú esté por encima de otros widgets
        self.menu_lateral.raise_()
        
        # Inicialmente oculto
        self.menu_lateral.hide()

    def mostrar_configuracion_presentacion(self):
        """Muestra un diálogo para configurar el modo presentación"""
        dialogo = StyledDialog("Configurar tiempo de paginación", 500, self)
        dialogo.add_title("Configurar paginación")
        
        descripcion = QLabel("Configure el intervalo de tiempo entre cada cambio automático de página:")
        descripcion.setWordWrap(True)
        descripcion.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: {COLORS['background_transparent']};")
        dialogo.layout.addWidget(descripcion)
        
        # Crear widget para selección de intervalo
        selector_widget = QWidget()
        selector_layout = QHBoxLayout(selector_widget)
        
        # Etiqueta
        label = QLabel("Intervalo (segundos):")
        label.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: {COLORS['background_transparent']}; font-weight: bold;")
        label.setAttribute(Qt.WA_TranslucentBackground, True)
        selector_widget.setStyleSheet("background-color: transparent;")
        selector_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Combobox para seleccionar intervalo
        combo_intervalo = QComboBox()
        combo_intervalo.addItems(['3', '5', '7', '10', '15', '20', '30'])
        combo_intervalo.setCurrentText(str(self.intervalo_presentacion))
        combo_intervalo.setStyleSheet(COMBO_BOX_STYLES["normal"])
        
        selector_layout.addWidget(label)
        selector_layout.addWidget(combo_intervalo)
        
        dialogo.layout.addWidget(selector_widget)
        dialogo.layout.addSpacing(20)
        
        # Agregar etiqueta informativa
        info = QLabel("Este valor cambiará cada cuánto tiempo se actualizan automáticamente las páginas de registros.")
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {COLORS['text_light']}; background-color: {COLORS['background_transparent']}; font-style: italic;")
        dialogo.layout.addWidget(info)
        dialogo.layout.addSpacing(10)
        
        # Botones
        def aplicar_cambios():
            try:
                nuevo_intervalo = int(combo_intervalo.currentText())
                # Guardar el nuevo intervalo
                self.intervalo_presentacion = nuevo_intervalo
                
                # Guardar en las preferencias del usuario
                from Back_end.Usuarios.ModeloPreferencias import ModeloPreferencias
                exito = ModeloPreferencias.guardar_tiempo_paginacion(
                    self.usuario_actual,
                    self.intervalo_presentacion
                )
                
                if exito:
                    print(f"Tiempo de paginación guardado: {self.intervalo_presentacion}s")
                else:
                    print("Error al guardar tiempo de paginación")
                
                # Actualizar el timer con el nuevo intervalo
                if self.timer_presentacion.isActive():
                    self.timer_presentacion.stop()
                self.timer_presentacion.start(self.intervalo_presentacion * 1000)
                
                dialogo.accept()
                
                # Notificar al usuario
                self.mostrar_mensaje_informacion(
                    "Configuración Actualizada", 
                    f"El tiempo de paginación se ha cambiado a {self.intervalo_presentacion} segundos."
                )
                
            except ValueError:
                self.mostrar_mensaje_advertencia("Error", "Por favor seleccione un intervalo válido.")
                
        botones = [
            ("Aplicar", aplicar_cambios, "primary"),
            ("Cancelar", dialogo.reject, "danger")
        ]
        
        dialogo.add_button_row(botones)
        
        # Ejecutar diálogo
        dialogo.exec_()

    def actualizar_datos_presentacion(self):
        """Actualiza los datos para el modo presentación"""
        # Obtener datos usando el modelo con filtro de áreas
        self.registros_totales = self.modelo.obtener_datos_pacientes_filtrados(self.areas_filtradas)
        
        # Verificar y guardar las celdas con alarma - Asegurando que se apliquen correctamente
        self.alarm_cells_global = self.modelo.verificar_alarmas(self.registros_totales)
        
        # Calcular el número total de páginas
        if self.registros_por_pagina > 0:
            self.total_paginas = (len(self.registros_totales) + self.registros_por_pagina - 1) // self.registros_por_pagina
        else:
            self.total_paginas = 1
        
        # Asegurar que la página actual es válida
        if self.total_paginas > 0:
            self.pagina_actual = self.pagina_actual % self.total_paginas
        else:
            self.pagina_actual = 0

    def mostrar_pagina_actual(self):
        """Muestra la página actual de registros"""
        if not self.registros_totales:
            return
        
        # Calcular índices de inicio y fin para la página actual
        inicio = self.pagina_actual * self.registros_por_pagina
        fin = min(inicio + self.registros_por_pagina, len(self.registros_totales))
        
        # Obtener registros para esta página
        registros_pagina = self.registros_totales[inicio:fin]
        
        # Limpiar tabla
        self.tabla.setRowCount(0)
        
        # Obtener celdas con alarma para los registros de esta página
        # Usamos directamente el método del modelo como en Front_end.py
        alarm_cells = self.modelo.verificar_alarmas(registros_pagina)
        indice_triage = self.headers.index('Triage')
        indice_ci = self.headers.index('CI')
        
        # Mostrar registros en la tabla
        if registros_pagina:
            for row_idx, fila in enumerate(registros_pagina):
                # Procesar solo los datos que vamos a mostrar
                fila_actual = []
                for i in range(len(fila)):
                    if i == 0:  # Nombre
                        fila_actual.append(self.enmascarar_nombre(fila[i]))
                    elif i == 1:  # Documento
                        fila_actual.append(self.enmascarar_documento(fila[i]))
                    elif i < 10:  # Hasta Pendientes
                        fila_actual.append(fila[i])
                    elif i == 11:  # Ubicación (saltamos Conducta que está en índice 10)
                        fila_actual.append(fila[i])
                
                # Insertar fila en la tabla
                self.tabla.insertRow(row_idx)
                for col, valor in enumerate(fila_actual):
                    if col == indice_triage or col == self.headers.index('CI') or \
                    col == self.headers.index('Labs') or col == self.headers.index('IMG') or \
                    col == self.headers.index('Interconsulta') or col == self.headers.index('RV'):
                        # Usar Personalizado_Columnas para que funcione con el delegado
                        item = Personalizado_Columnas("", str(valor))
                        self.tabla.setItem(row_idx, col, item)
                    else:
                        item = QTableWidgetItem(str(valor))
                        item.setTextAlignment(Qt.AlignCenter)
                        self.tabla.setItem(row_idx, col, item)
            
            # Actualizar alarmas en el delegate para CI - Asegurando que se apliquen correctamente
            ci_col = self.headers.index('CI')
            delegate = self.tabla.itemDelegateForColumn(ci_col)
            if isinstance(delegate, Estado_delegado_circulo):
                delegate.set_alarm_cells(alarm_cells)
                # También establecer un conjunto vacío para alarmas de conducta
                delegate.set_conducta_alarm_cells(set())
            
            # Establecer altura fija para todas las filas
            circle_delegate = self.tabla.itemDelegateForColumn(indice_triage)
            if isinstance(circle_delegate, Estado_delegado_circulo):
                row_height = circle_delegate.circle_size + 20  # +20 para padding
                for row in range(self.tabla.rowCount()):
                    self.tabla.setRowHeight(row, row_height)

    def activar_modo_presentacion(self):
        """Activa el modo presentación según la configuración seleccionada"""
        # Actualizar estado
        self.modo_presentacion_activo = True
        
        # Calcular cuántas filas caben en la tabla
        altura_visible = self.tabla.viewport().height()
        if self.tabla.rowCount() > 0:
            altura_fila = self.tabla.rowHeight(0)  # Altura de una fila
            self.registros_por_pagina = max(1, int(altura_visible / altura_fila))
        else:
            self.registros_por_pagina = 10  # Valor predeterminado
        
        # Obtener todos los registros nuevamente para asegurar que estén actualizados
        self.actualizar_datos_presentacion()
        
        # Comenzar desde la primera página
        self.pagina_actual = 0
        self.mostrar_pagina_actual()
        
        # Iniciar el temporizador con el tiempo configurado
        self.timer_presentacion.start(self.intervalo_presentacion * 1000)

    def mostrar_siguiente_pagina(self):
        """Avanza a la siguiente página en el modo presentación"""
        if not self.modo_presentacion_activo or self.total_paginas <= 1:
            return
            
        # Avanzar a la siguiente página
        self.pagina_actual = (self.pagina_actual + 1) % self.total_paginas
        self.mostrar_pagina_actual()

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
            
        # Recalcular registros por página si el modo presentación está activo
        if self.modo_presentacion_activo:
            # Recalcular cuántas filas caben en la tabla después del cambio de tamaño
            altura_visible = self.tabla.viewport().height()
            if self.tabla.rowCount() > 0:
                altura_fila = self.tabla.rowHeight(0)
                registros_por_pagina_nuevo = max(1, int(altura_visible / altura_fila))
                
                # Si cambió el número de registros por página, actualizar vista
                if registros_por_pagina_nuevo != self.registros_por_pagina:
                    self.registros_por_pagina = registros_por_pagina_nuevo
                    self.actualizar_datos_presentacion()
                    self.mostrar_pagina_actual()

    def actualizar_tabla(self):
        """Actualiza la tabla con los datos actuales"""
        try:
            # Verificar que la tabla exista antes de intentar usarla
            if not hasattr(self, 'tabla'):
                print("La tabla aún no se ha inicializado")
                return
            
            # Si es la primera carga, mostrar una pantalla de carga
            if self.primera_carga:
                splash = SplashScreen(self, logo_path=self.ruta_logo, message="Cargando datos de pacientes...", duration=1)
                splash.setFixedSize(int(self.pantalla.width() * 0.3), int(self.pantalla.height() * 0.3))
                splash.show()
                splash.opacity_animation.start()
                QApplication.processEvents()
            
            # Obtener datos usando el modelo con filtro de áreas
            datos = self.modelo.obtener_datos_pacientes_filtrados(self.areas_filtradas)
            
            # Guardar los datos para el modo presentación
            self.registros_totales = datos
            
            # Si el modo presentación está activo, actualizar la vista de presentación
            if self.modo_presentacion_activo:
                self.actualizar_datos_presentacion()
                self.mostrar_pagina_actual()
                return
                
            # Si no está en modo presentación, mostrar todos los datos (no debería ocurrir)
            self.tabla.setRowCount(0)
            
            # Obtener celdas con alarma desde el modelo - Usando el método correcto del modelo
            alarm_cells = self.modelo.verificar_alarmas(datos)
            conducta_alarm_cells = set()  # Inicializar conjunto vacío para la sala de espera
            indice_triage = self.headers.index('Triage')
            indice_pendientes = self.headers.index('Pendientes')  # Índice de la columna pendientes
            
            if datos:
                for row_idx, fila in enumerate(datos):
                    # Procesar solo los datos que vamos a mostrar (excluimos Conducta e Ingreso)
                    fila_actual = []
                    for i in range(len(fila)):
                        if i == 0:  # Nombre
                            fila_actual.append(self.enmascarar_nombre(fila[i]))
                        elif i == 1:  # Documento
                            fila_actual.append(self.enmascarar_documento(fila[i]))
                        elif i < 10:  # Hasta Pendientes
                            fila_actual.append(fila[i])
                        elif i == 11:  # Ubicación (saltamos Conducta que está en índice 10)
                            fila_actual.append(fila[i])
                    
                    # Insertar fila en la tabla
                    self.tabla.insertRow(row_idx)
                    for col, valor in enumerate(fila_actual):
                        # Verificar si es una columna que debe usar el delegado especial
                        if col == indice_triage or col == self.headers.index('CI') or \
                            col == self.headers.index('Labs') or col == self.headers.index('IMG') or \
                            col == self.headers.index('Interconsulta') or col == self.headers.index('RV'):
                            # Usar un ítem personalizado para que funcione con el delegado
                            item = Personalizado_Columnas("", str(valor))
                            self.tabla.setItem(row_idx, col, item)
                            
                        elif col == indice_pendientes:
                            # Para la columna de pendientes, asegurarse de que se muestre exactamente como viene de la BD
                            # sin ningún procesamiento adicional
                            pendientes_texto = str(valor) if valor is not None else ""
                            item = QTableWidgetItem(pendientes_texto)
                            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Alineación a la izquierda para mejor legibilidad
                            self.tabla.setItem(row_idx, col, item)
                        else:
                            # Para texto normal
                            item = QTableWidgetItem(str(valor))
                            item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                            self.tabla.setItem(row_idx, col, item)
                
                # Actualizar alarmas en el delegado para CI - Asegurando que se apliquen correctamente
                ci_col = self.headers.index('CI')
                delegate = self.tabla.itemDelegateForColumn(ci_col)
                if isinstance(delegate, Estado_delegado_circulo):
                    delegate.set_alarm_cells(alarm_cells)
                    # También establecer el conjunto vacío de alarmas de conducta
                    delegate.set_conducta_alarm_cells(conducta_alarm_cells)
                
                # Configurar anchos de columna
                self.configurar_anchos_columnas()
                
                # Establecer altura fija para todas las filas
                circle_delegate = self.tabla.itemDelegateForColumn(indice_triage)
                if isinstance(circle_delegate, Estado_delegado_circulo):
                    row_height = circle_delegate.circle_size + 20  # +20 para padding
                    for row in range(self.tabla.rowCount()):
                        self.tabla.setRowHeight(row, row_height)
            
            # Cerrar la pantalla de carga si es la primera vez
            if self.primera_carga:
                self.primera_carga = False
                if 'splash' in locals():
                    splash.accept()
                
        except Exception as e:
            self.mostrar_mensaje_informacion("Error", f"Error al actualizar la tabla: {str(e)}", QMessageBox.Critical)
        finally:
            self.modelo.cierre_db()
            
            # Si es la primera carga, activar el modo presentación después de cargar los datos
            if self.primera_carga:
                self.primera_carga = False
                if 'splash' in locals():
                    splash.accept()
    
    def configurar_anchos_columnas(self):
        """Configura los anchos de las columnas de la tabla para asegurar consistencia"""
        # Guardar el modo de ajuste actual de las columnas
        modos_actuales = []
        for col in range(self.tabla.columnCount()):
            modos_actuales.append(self.tabla.horizontalHeader().sectionResizeMode(col))
        
        # Establecer todas las columnas en modo stretch temporalmente
        for col in range(self.tabla.columnCount()):
            self.tabla.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        
        # Actualizar el tamaño de la tabla
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
        
        # Asegurar que los cambios sean visibles
        self.tabla.horizontalHeader().update()
    
    def mostrar_mensaje_confirmacion(self, titulo, mensaje):
        """Muestra un mensaje de confirmación estilizado"""
        msg_box = StyledMessageBox(self, titulo, mensaje, QMessageBox.Question, "confirmation")
        
        btn_si = QPushButton("Sí")
        btn_no = QPushButton("No")
        
        btn_si.setCursor(Qt.PointingHandCursor)
        btn_no.setCursor(Qt.PointingHandCursor)
        
        msg_box.addButton(btn_si, QMessageBox.YesRole)
        msg_box.addButton(btn_no, QMessageBox.NoRole)
        
        msg_box.setDefaultButton(btn_no)
        
        resultado = msg_box.exec_()
        
        return msg_box.clickedButton() == btn_si
    
    def mostrar_mensaje_informacion(self, titulo, mensaje, icon=QMessageBox.Information):
        """Muestra un mensaje informativo estilizado"""
        style_type = "error" if icon == QMessageBox.Critical else "info"
        
        msg_box = StyledMessageBox(self, titulo, mensaje, icon, style_type)
        
        btn_ok = QPushButton("Aceptar")
        btn_ok.setCursor(Qt.PointingHandCursor)
        
        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
        msg_box.setDefaultButton(btn_ok)
        
        return msg_box.exec_()

    def mostrar_dialog_filtrado(self):
        """Muestra el diálogo para filtrar por áreas y guarda las preferencias"""
        dialogo = DialogoFiltrarAreas(self, self.areas, self.areas_filtradas)
        if dialogo.exec_() == QDialog.Accepted:
            # Obtener áreas seleccionadas del diálogo
            nuevos_filtros = dialogo.obtener_areas_seleccionadas()
            
            # Si no se selecciona ningún área, usar todas por defecto
            if not nuevos_filtros:
                nuevos_filtros = list(self.areas.keys())
            
            # Actualizar los filtros locales
            self.areas_filtradas = nuevos_filtros
            
            # Guardar preferencias 
            from Back_end.Usuarios.ModeloPreferencias import ModeloPreferencias
            print(f"\n=== Guardando nuevas preferencias para usuario: {self.usuario_actual} ===")
            print(f"Filtros seleccionados: {nuevos_filtros}")
            
            # Intentar guardar preferencias
            exito = ModeloPreferencias.guardar_preferencias_filtros(
                self.usuario_actual,
                self.areas_filtradas
            )
            
            if exito:
                print("Preferencias guardadas exitosamente")
            else:
                print("Error al guardar preferencias")
                # Informar al usuario que sus preferencias no se guardarán permanentemente
                self.mostrar_mensaje_informacion(
                    "Preferencias no persistentes", 
                    "No se pudieron guardar las preferencias de filtros de forma permanente. "
                    "Las preferencias se mantendrán durante esta sesión únicamente.",
                    QMessageBox.Warning
                )
            
            # Actualizar el indicador visual de filtros
            self.crear_indicador_filtros()
            
            # Actualizar la tabla con los nuevos filtros
            self.actualizar_tabla()
    
    def crear_indicador_filtros(self):
        """Crea o actualiza el indicador visual de filtros aplicados"""
        # Limpiar el layout previo
        while self.layout_filtros.count():
            item = self.layout_filtros.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Si no hay filtros o todos están seleccionados, ocultar el indicador
        if len(self.areas_filtradas) == len(self.areas) or not self.areas_filtradas:
            self.contenedor_filtros.hide()
            return
            
        # Mostrar el contenedor
        self.contenedor_filtros.show()
        
        # Crear etiqueta de filtros activos con mejor contraste y tamaño
        filtros_label = QLabel("Filtros activos:")
        filtros_label.setStyleSheet(f"""
            color: {COLORS['background_header']};
            font-size: 17px;
            font-weight: bold;
            background-color: transparent;
            padding-right: 8px;
        """)
        self.layout_filtros.addWidget(filtros_label)
        
        # Crear chips para cada área filtrada con mejor contraste y tamaño
        for i, area in enumerate(sorted(self.areas_filtradas)):
            if i < 5:  # Mostrar máximo 5 áreas directamente
                area_label = QLabel(area)
                area_label.setStyleSheet(f"""
                    color: {COLORS['text_primary']};
                    background-color: {COLORS['background_header']};
                    border-radius: 4px;
                    padding: 5px 12px;
                    margin-right: 8px;
                    font-size: 15px;
                    font-weight: 500;
                """)
                self.layout_filtros.addWidget(area_label)
        
        # Indicador de áreas adicionales con mejor visibilidad
        if len(self.areas_filtradas) > 5:
            mas_areas = QLabel(f"+{len(self.areas_filtradas) - 5} más")
            mas_areas.setStyleSheet(f"""
                color: {COLORS['text_primary']};
                background-color: {COLORS['background_header']};
                padding-left: 5px;
                padding-right: 10px;
                font-size: 15px;
                font-weight: 500;
            """)
            self.layout_filtros.addWidget(mas_areas)
        
        # Botón para editar filtros con estilo mejorado
        btn_editar = QPushButton("Editar")
        btn_editar.setCursor(Qt.PointingHandCursor)
        btn_editar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_warning']};
                color: {COLORS['text_primary']};
                border-radius: 4px;
                padding: 5px 15px;
                border: 1px solid {COLORS['border_warning']};
                font-size: 15px;
                font-weight: 500;
                margin-left: 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['button_warning_hover']};
                border: 1px solid {COLORS['border_warning']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['border_warning']};
            }}
        """)
        btn_editar.clicked.connect(self.mostrar_dialog_filtrado)
        self.layout_filtros.addWidget(btn_editar)
        
        # Añadir espacio expansible al final
        self.layout_filtros.addStretch(1)

    def logout(self):
        if self.mostrar_mensaje_confirmacion(
            "Confirmar Cierre de Sesión",
            "¿Está seguro que desea cerrar sesión?"
        ):
            # Mostrar pantalla de carga durante el cierre de sesión
            splash = SplashScreen(None, logo_path=self.ruta_logo, message="Cerrando sesión...", duration=1.5)
            splash.setFixedSize(int(self.pantalla.width() * 0.3), int(self.pantalla.height() * 0.3))
            splash.show()
            splash.opacity_animation.start()
            QApplication.processEvents()
            
            # Detener el timer antes de cerrar
            if hasattr(self, 'timer'):
                self.timer.stop()
            
            try:
                if hasattr(self.modelo, 'conn') and self.modelo.conn:
                    self.modelo.conn.close()
            except Exception as e:
                print(f"Error al cerrar la conexión de base de datos: {e}")
            
            # Esperar a que termine la pantalla de carga
            splash.exec_()
            
            self.close()
            self.login_interface.reiniciar_login()
    
    def closeEvent(self, event):
        # Detener el timer antes de cerrar
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        # Detener los timers antes de cerrar
        if hasattr(self, 'timer_presentacion'):
            self.timer_presentacion.stop()
        
        # Continuar con el cierre normal
        super().closeEvent(event)
    
    def toggle_maximized(self):
        """Alterna entre modo maximizado y normal para la ventana."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

# Nuevo diálogo para filtrar por áreas completamente rediseñado con grid layout
class DialogoFiltrarAreas(StyledDialog):
    def __init__(self, parent=None, areas=None, areas_seleccionadas=None):
        super().__init__("Filtrar por Áreas", 650, parent)  # Aumentado el ancho para mejor experiencia
        
        self.areas = areas or {}
        self.areas_seleccionadas = areas_seleccionadas or []
        
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle (compiled with PyInstaller)
            self.ruta_base = sys._MEIPASS
        else:
            # For normal script execution
            self.ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        ruta_imagenes = os.path.join(self.ruta_base, "Front_end", "imagenes")
        self.ruta_check = os.path.join(ruta_imagenes, "check.png")
        
        # Configuración visual mejorada del diálogo
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
        
        # Header con título y descripción - Mejorado con fondo claro
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['background_white']};")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setSpacing(12)
        
        # Título con mayor contraste y visibilidad en fondo blanco
        titulo = QLabel("Filtrar por áreas")
        titulo.setStyleSheet(f"""
            font-size: 26px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            background-color: {COLORS['background_white']};
            padding: 10px 0;
        """)
        titulo.setAlignment(Qt.AlignCenter)
        
        # Descripción mejorada con fondo blanco
        descripcion = QLabel("Seleccione las áreas que desea visualizar en la tabla:")
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
        
        # Línea divisoria sutil bajo la descripción
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
        
        # Área principal para los checkboxes (contenedor con fondo blanco)
        content_container = QFrame()
        content_container.setObjectName("contentContainer")
        content_container.setStyleSheet(f"""
            #contentContainer {{
                background-color: white;
                border-radius: 10px;
                border: 1px solid #EEEEEE;
            }}
        """)
        content_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Layout para los checkboxes organizados en grid
        grid_layout = QGridLayout(content_container)
        grid_layout.setContentsMargins(20, 20, 20, 20)
        grid_layout.setSpacing(15)  # Espacio consistente entre elementos
        
        # Determinar número de columnas según el ancho disponible (responsivo)
        num_columnas = 3  # Valor predeterminado para pantallas normales
        
        if parent:
            parent_width = parent.width()
            if parent_width < 800:
                num_columnas = 2  # Para pantallas pequeñas
            elif parent_width > 1400:
                num_columnas = 4  # Para pantallas muy grandes
        
        # Estilo mejorado para los checkboxes con icono de check
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
            }}
            
            QCheckBox::indicator:checked {{
                image: url("{self.ruta_check.replace('\\', '/')}");
            }}
        """
        
        # Verificar si la imagen de check existe
        if not os.path.exists(self.ruta_check):
            print(f"Advertencia: No se encontró la imagen de check en: {self.ruta_check}")
        
        # Crear checkboxes en formato grid
        self.checkboxes = {}
        fila = 0
        columna = 0
        
        for area_name in sorted(self.areas.keys()):
            # Crear checkbox con diseño simplificado
            checkbox = QCheckBox(area_name)
            checkbox.setStyleSheet(checkbox_style)
            checkbox.setCursor(Qt.PointingHandCursor)
            checkbox.setMinimumHeight(42)  # Altura mínima para mejor accesibilidad
            
            # Marcar el checkbox si el área ya estaba seleccionada
            if area_name in self.areas_seleccionadas:
                checkbox.setChecked(True)
            
            self.checkboxes[area_name] = checkbox
            
            # Añadir al grid layout
            grid_layout.addWidget(checkbox, fila, columna)
            
            # Actualizar posición para el siguiente checkbox
            columna += 1
            if columna >= num_columnas:
                columna = 0
                fila += 1
        
        # Añadir el contenedor de grid al layout principal
        main_layout.addWidget(content_container, 1) # Con factor de expansión 1
        
        # Contenedor para los botones de selección con estilo unificado y mejorado
        selection_buttons = QWidget()
        selection_buttons.setObjectName("selectionContainer")
        selection_buttons.setStyleSheet(f"""
            #selectionContainer {{
                background-color: {COLORS['background_white']};
                border-radius: 10px;
                border: 1px solid #F0F0F0;
            }}
        """)
        selection_layout = QHBoxLayout(selection_buttons)
        selection_layout.setContentsMargins(15, 15, 15, 15)
        selection_layout.setSpacing(15)
        
        # Estilo mejorado para los botones auxiliares (con fondo claro)
        button_style_aux = f"""
            QPushButton {{
                background-color: {COLORS['background_header']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_medium']};
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
        
        # Botones de selección/deselección con estilo mejorado
        self.btn_select_all = QPushButton("Seleccionar Todos")
        self.btn_select_all.setStyleSheet(button_style_aux)
        self.btn_select_all.setCursor(Qt.PointingHandCursor)
        
        self.btn_unselect_all = QPushButton("Deseleccionar Todos")
        self.btn_unselect_all.setStyleSheet(button_style_aux)
        self.btn_unselect_all.setCursor(Qt.PointingHandCursor)
        
        # Conectar eventos
        self.btn_select_all.clicked.connect(self.select_all)
        self.btn_unselect_all.clicked.connect(self.unselect_all)
        
        # Añadir botones al layout con distribución equitativa
        selection_layout.addWidget(self.btn_select_all)
        selection_layout.addWidget(self.btn_unselect_all)
        
        # Añadir el widget de botones de selección al layout principal
        main_layout.addWidget(selection_buttons)
        
        # Reemplazar el layout predeterminado del diálogo con nuestro layout personalizado
        # Primero limpiamos el layout original
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
        
        # Botones de acción principales con estilo unificado
        action_buttons = [
            ("Aplicar Filtros", self.accept, "primary"),
            ("Cancelar", self.reject, "danger")
        ]
        
        buttons_layout = self.add_button_row(action_buttons)
        
        # Estilo mejorado y consistente para los botones principales
        for i in range(buttons_layout.count()):
            widget = buttons_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setMinimumHeight(48)  # Altura ligeramente mayor para mejor accesibilidad
                widget.setStyleSheet(widget.styleSheet() + """
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 8px;
                """)
        
        # Configurar tamaño responsivo del diálogo
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(450, 400)  # Tamaño mínimo más pequeño ya que ahora usamos grid
        
        # Centrar en pantalla y ajustar tamaño
        self.centerAndResize()
    
    def centerAndResize(self):
        """Centra el diálogo en la pantalla y ajusta el tamaño de forma responsiva"""
        screen = QDesktopWidget().availableGeometry()
        
        # Calcular tamaño óptimo basado en el tamaño de la pantalla
        optimal_width = min(650, int(screen.width() * 0.5))
        optimal_height = min(550, int(screen.height() * 0.6))  # Altura reducida gracias al grid layout
        
        # Establecer dimensiones
        self.resize(optimal_width, optimal_height)
        
        # Centrar en pantalla
        geom = self.frameGeometry()
        geom.moveCenter(screen.center())
        self.setGeometry(geom)
    
    def select_all(self):
        """Selecciona todos los checkboxes"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
    
    def unselect_all(self):
        """Deselecciona todos los checkboxes"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
    
    def obtener_areas_seleccionadas(self):
        """Retorna una lista con las áreas seleccionadas"""
        return [area for area, checkbox in self.checkboxes.items() if checkbox.isChecked()]