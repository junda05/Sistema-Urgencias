from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QStyledItemDelegate, QToolTip,
                           QHeaderView, QAbstractItemView, QStyleOptionViewItem)
from PyQt5.QtCore import Qt, QTimer, QRectF, QSize, QEvent
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont
from Back_end.Manejo_DB import ModeloPaciente

class Estado_delegado_circulo(QStyledItemDelegate):
    """Delegado para renderizar estados como círculos coloreados con alarmas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.modelo = ModeloPaciente()
        self.colors = self.modelo.obtener_colores()
        self.circle_size = 50
        self.alarm_cells = set()
        self.conducta_alarm_cells = set()
        self.blink_state = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_blink)
        self.timer.start(500)
    
    def toggle_blink(self):
        """Alterna el estado de parpadeo para las celdas con alarma."""
        self.blink_state = not self.blink_state
        if self.alarm_cells:
            for row, col in self.alarm_cells:
                self.parent().update(self.parent().model().index(row, col))
        if self.conducta_alarm_cells:
            for row, col in self.conducta_alarm_cells:
                self.parent().update(self.parent().model().index(row, col))

    def set_alarm_cells(self, alarm_cells):
        """Define qué celdas tienen alarma estándar."""
        self.alarm_cells = alarm_cells
        
    def set_conducta_alarm_cells(self, conducta_alarm_cells):
        """Define qué celdas tienen alarma de conducta."""
        self.conducta_alarm_cells = conducta_alarm_cells
        
    def sizeHint(self, option, index):
        """Tamaño recomendado para las celdas con círculos."""
        return QSize(self.circle_size + 10, self.circle_size + 10)  # +10 para padding
        
    def paint(self, painter, option, index):
        """Dibuja el contenido de la celda según su estado."""
        text = index.data(Qt.DisplayRole)
        row = index.row()
        col = index.column()
        
        is_alarm = (row, col) in self.alarm_cells
        is_conducta_alarm = (row, col) in self.conducta_alarm_cells
        
        # Verificamos si es un número de triage o un estado con color definido
        if text in self.colors or text in ["2", "3"]:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            
            if is_alarm and self.blink_state:
                color = QColor("#FFA500")  # Naranja para alarma normal
            elif is_conducta_alarm and self.blink_state:
                color = QColor("#9370DB")  # Púrpura suave para alarma de observación
            else:
                # Obtener el color del modelo, funcionará tanto para estados normales como para triage 2 y 3
                color = QColor(self.colors.get(text, "#CCCCCC"))  # Color gris por defecto si no existe
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            
            x = option.rect.x() + (option.rect.width() - self.circle_size) / 2
            y = option.rect.y() + (option.rect.height() - self.circle_size) / 2
            
            # Dibujar un círculo para estados normales
            if not is_conducta_alarm:
                painter.drawEllipse(QRectF(x, y, self.circle_size, self.circle_size))
                
                # Dibujar el número dentro del círculo para triage 2 y 3
                if text in ["1", "2", "3", "4", "5"]:
                    # Configura el color del texto (blanco para mejor contraste)
                    painter.setPen(Qt.white)
                    # Configura la fuente para el número
                    font = QFont()
                    font.setPointSize(20)
                    font.setBold(True)
                    painter.setFont(font)
                    # Dibuja el texto centrado dentro del círculo
                    painter.drawText(QRectF(x, y, self.circle_size, self.circle_size), 
                                    Qt.AlignCenter, text)
            else:
                # Para alarma de conducta, llenar toda la celda
                if self.blink_state:
                    # Llenar toda la celda con color púrpura semi-transparente
                    painter.setBrush(QBrush(QColor(147, 112, 219, 100)))  # Púrpura semi-transparente
                    painter.drawRect(option.rect)
                
                # Luego dibujar el círculo principal
                painter.setBrush(QBrush(color))
                painter.drawEllipse(QRectF(x, y, self.circle_size, self.circle_size))
                
                # Dibujar el número dentro del círculo para triage 2 y 3 incluso en caso de alarma
                if text in ["1", "2", "3", "4", "5"]:
                    painter.setPen(Qt.white)
                    font = QFont()
                    font.setPointSize(20)
                    font.setBold(True)
                    painter.setFont(font)
                    painter.drawText(QRectF(x, y, self.circle_size, self.circle_size), 
                                    Qt.AlignCenter, text)
            
            painter.restore()
        else:
            # Para textos que no tienen color asociado pero pueden tener alarma (como "Observación")
            if is_conducta_alarm and text == "Observación":
                painter.save()
                painter.setRenderHint(QPainter.Antialiasing)
                
                # Dibujar un fondo para toda la celda con efecto pulsante
                if self.blink_state:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(147, 112, 219, 80)))  # Púrpura semi-transparente
                    painter.drawRect(option.rect)
                else:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(147, 112, 219, 30)))  # Púrpura muy suave cuando no está pulsando
                    painter.drawRect(option.rect)
                
                # Dibujar el texto con un borde de color
                font = painter.font()
                font.setBold(True)
                painter.setFont(font)
                
                if self.blink_state:
                    painter.setPen(QColor("#8A2BE2"))  # Púrpura más intenso para el texto
                else:
                    painter.setPen(QColor("#666666"))  # Gris normal para texto no pulsante
                
                painter.drawText(option.rect, Qt.AlignCenter, text)
                painter.restore()
            else:
                super().paint(painter, option, index)

    def helpEvent(self, event, view, option, index):
        """Muestra tooltips al pasar el mouse sobre celdas específicas."""
        if event.type() == QEvent.ToolTip:
            text = index.data(Qt.DisplayRole)
            if text in self.colors or text in ["2", "3"]:  # Agregamos triage 2 y 3 para tooltips
                QToolTip.showText(event.globalPos(), text, view)
                return True
        return super().helpEvent(event, view, option, index)
    
    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseMove:
            # Si estamos sobre la columna Labs (índice 4)
            if index.column() == 4:  # 4 es la columna "Labs"
                # Obtener el ID del paciente de la fila actual
                paciente_id = model.index(index.row(), 13).data()  # Asumiendo que el ID está en la columna 13
                if paciente_id:
                    try:
                        # Obtener laboratorios del paciente
                        modelo_paciente = ModeloPaciente()
                        laboratorios = modelo_paciente.obtener_laboratorios_paciente(paciente_id)
                        modelo_paciente.cierre_db()
                        
                        if laboratorios:
                            # Construir tooltip
                            tooltip_text = "<b>Laboratorios asignados:</b><br>"
                            for codigo, nombre, estado in laboratorios:
                                tooltip_text += f"• {codigo} - {nombre}: <i>{estado}</i><br>"
                            QToolTip.showText(event.globalPos(), tooltip_text)
                            return True
                    except Exception as e:
                        print(f"Error al mostrar tooltip de laboratorios: {str(e)}")
        
        return super().editorEvent(event, model, option, index)

class TextDelegate(QStyledItemDelegate):
    """Delegado para mostrar tooltips en celdas de texto."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.modelo = ModeloPaciente()
        
    def paint(self, painter, option, index):
        # Make a copy of the option so we can modify it
        opt = QStyleOptionViewItem(option)
        
        # Check which column we're in
        if index.column() == 8:  # Pendientes column (index 8)
            # Get cell text content
            text = index.data(Qt.DisplayRole) or ""
            
            # Check if the pendientes contains labs or images references
            if "Labs pendientes:" in text or "IMG pendientes:" in text:
                # Keep left alignment for lab and image pendientes
                opt.displayAlignment = Qt.AlignLeft | Qt.AlignVCenter
            else:
                # Center other pendientes text
                opt.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter
        elif index.column() == 9:  # Conducta column (index 9)
            # Center text for conducta column
            opt.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter
        else:
            # Center text for all other columns
            opt.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter
        
        # Call the base implementation with our modified options
        super().paint(painter, opt, index)

    def helpEvent(self, event, view, option, index):
        """Customize tooltips to show cell content with better styling"""
        if not event or not view:
            return False
            
        if event.type() == QEvent.ToolTip:
            # Get the data to display in tooltip
            text = index.data(Qt.DisplayRole)
            
            # Identificar si estamos en la columna de pendientes (índice 8)
            if index.column() == 8 and text:
                # Detectar si hay laboratorios o imágenes pendientes en el texto
                labs_pendientes = set()  # Usar set para evitar duplicados
                img_pendientes = set()   # Usar set para evitar duplicados
                
                # Debug: imprimir el texto completo de la celda
                print("[DEBUG] Texto de la celda pendientes:", text)
                
                # Verificar si hay sección de labs pendientes
                if "Labs pendientes:" in text:
                    labs_parte = text.split("Labs pendientes:")[1]
                    # Si hay IMGs después, cortar antes de IMG pendientes
                    if "IMG pendientes:" in labs_parte:
                        labs_parte = labs_parte.split("IMG pendientes:")[0]
                    # Limpiar y dividir los laboratorios
                    labs_items = [lab.strip() for lab in labs_parte.split(",")]
                    # Añadir items únicos al set
                    for lab in labs_items:
                        if lab and not lab.startswith("IMG pendientes:"):
                            labs_pendientes.add(lab)
                            print("[DEBUG] Agregado lab pendiente:", lab)
                
                # Verificar si hay sección de IMG pendientes
                if "IMG pendientes:" in text:
                    img_parte = text.split("IMG pendientes:")[1]
                    # Limpiar y dividir las imágenes
                    img_items = [img.strip() for img in img_parte.split(",")]
                    # Añadir items únicos al set
                    for img in img_items:
                        if img:
                            img_pendientes.add(img)
                            print("[DEBUG] Agregado img pendiente:", img)
                
                # Si encontramos labs o imágenes, crear un tooltip personalizado
                if labs_pendientes or img_pendientes:
                    # Construir el HTML para el tooltip
                    tooltip_html = ""
                    
                    # Agregar sección de laboratorios si existen
                    if labs_pendientes:
                        tooltip_html += "<b>Laboratorios:</b><br>"
                        print(f"[DEBUG] Labs pendientes encontrados: {len(labs_pendientes)}")
                        for lab in sorted(labs_pendientes):  # Ordenar para consistencia
                            tooltip_html += f"• {lab}<br>"
                            print(f"[DEBUG] Agregando al tooltip lab: {lab}")
                        
                        # Agregar espacio entre secciones si también hay imágenes
                        if img_pendientes:
                            tooltip_html += "<br>"
                    
                    # Agregar sección de imágenes diagnósticas si existen
                    if img_pendientes:
                        tooltip_html += "<b>Imágenes diagnósticas:</b><br>"
                        print(f"[DEBUG] IMGs pendientes encontradas: {len(img_pendientes)}")
                        for img in sorted(img_pendientes):  # Ordenar para consistencia
                            tooltip_html += f"• {img}<br>"
                            print(f"[DEBUG] Agregando al tooltip img: {img}")
                    
                    # Debug: mostrar el HTML final del tooltip
                    print("[DEBUG] HTML final del tooltip:", tooltip_html)
                    
                    # Mostrar el tooltip personalizado
                    QToolTip.setFont(QFont("Segoe UI", 10))
                    QToolTip.showText(event.globalPos(), tooltip_html, view)
                    return True
            
            # Para cualquier otra columna o si no hay labs/imgs, mostrar el tooltip estándar
            if text:
                QToolTip.setFont(QFont("Segoe UI", 10))
                QToolTip.showText(event.globalPos(), text, view)
                return True
                
        return super().helpEvent(event, view, option, index)

    def editorEvent(self, event, model, option, index):
        # Verificar si estamos sobre la columna de pendientes y hay un evento de ratón
        if index.column() == 8 and event.type() == QEvent.MouseMove:
            # Obtener el ID del paciente de la fila actual
            paciente_id = model.index(index.row(), 13).data()  # Asumiendo que el ID está en la columna 13
            
            if paciente_id:
                try:
                    # Obtenemos directamente los laboratorios e imágenes asignados al paciente
                    labs = self.modelo.obtener_laboratorios_paciente(paciente_id)
                    imgs = self.modelo.obtener_imagenes_paciente(paciente_id)
                    
                    # Debug: mostrar laboratorios e imágenes obtenidos de la base de datos
                    print(f"[DEBUG] ID paciente: {paciente_id}")
                    print(f"[DEBUG] Total laboratorios obtenidos: {len(labs)}")
                    print(f"[DEBUG] Total imágenes obtenidas: {len(imgs)}")
                    
                    # Filtrar por estado para mostrar solo los pendientes
                    labs_pendientes = [lab for lab in labs if lab[2] in ["No se ha realizado", "En espera de resultados"]]
                    imgs_pendientes = [img for img in imgs if img[2] in ["No se ha realizado", "En espera de resultados"]]
                    
                    # Debug: mostrar laboratorios e imágenes pendientes
                    print(f"[DEBUG] Laboratorios pendientes: {len(labs_pendientes)}")
                    print(f"[DEBUG] Imágenes pendientes: {len(imgs_pendientes)}")
                    
                    self.modelo.cierre_db()
                    
                    # Si hay laboratorios o imágenes pendientes, mostrar tooltip detallado
                    if labs_pendientes or imgs_pendientes:
                        tooltip_html = ""
                        
                        # Agregar sección de laboratorios si existen
                        if labs_pendientes:
                            tooltip_html += "<b>Laboratorios:</b><br>"
                            # Ordenar los labs por nombre para una presentación consistente
                            labs_ordenados = sorted(labs_pendientes, key=lambda lab: lab[1])
                            for codigo, nombre, _ in labs_ordenados:
                                tooltip_html += f"• {nombre}<br>"
                                print(f"[DEBUG] Agregando al tooltip lab: {nombre} ({codigo})")
                            
                            # Agregar espacio entre secciones si también hay imágenes
                            if imgs_pendientes:
                                tooltip_html += "<br>"
                        
                        # Agregar sección de imágenes diagnósticas si existen
                        if imgs_pendientes:
                            tooltip_html += "<b>Imágenes diagnósticas:</b><br>"
                            # Ordenar las imágenes por nombre para una presentación consistente
                            imgs_ordenadas = sorted(imgs_pendientes, key=lambda img: img[1])
                            for codigo, nombre, _ in imgs_ordenadas:
                                tooltip_html += f"• {nombre}<br>"
                                print(f"[DEBUG] Agregando al tooltip img: {nombre} ({codigo})")
                        
                        # Debug: mostrar el HTML final del tooltip
                        print("[DEBUG] HTML final del tooltip:", tooltip_html)
                        
                        # Mostrar el tooltip personalizado
                        QToolTip.setFont(QFont("Segoe UI", 10))
                        QToolTip.showText(event.globalPos(), tooltip_html)
                        return True
                        
                except Exception as e:
                    print(f"[DEBUG] Error al mostrar tooltip detallado para pendientes: {str(e)}")
        
        return super().editorEvent(event, model, option, index)

class Personalizado_Columnas(QTableWidgetItem):
    """Ítem personalizado para mostrar círculos de colores en celdas."""
    def __init__(self, text, state=None):
        super().__init__(text)
        self.state = state
        self.modelo = ModeloPaciente()
        self.colors = self.modelo.obtener_colores()
        self.setData(Qt.DisplayRole, state)

def configurar_tabla_estandar(tabla, headers, delegate_columns=None, text_delegate_columns=None, 
                           font_name="ABeeZee", row_height=70):
    """
    Configura una tabla con estilo y delegados estándar.
    
    Args:
        tabla: QTableWidget a configurar
        headers: Lista de encabezados de columna
        delegate_columns: Diccionario de {nombre_columna: delegado} para columnas especiales
        text_delegate_columns: Lista de nombres de columna para aplicar TextDelegate
        font_name: Nombre de la fuente a usar
        row_height: Altura de las filas
    """
    # Configuración básica
    tabla.setColumnCount(len(headers))
    tabla.setHorizontalHeaderLabels(headers)
    tabla.verticalHeader().setVisible(False)
    
    # Estilos y comportamiento
    tabla.setAlternatingRowColors(False)
    tabla.setSelectionBehavior(QTableWidget.SelectRows)
    tabla.setSelectionMode(QTableWidget.SingleSelection)
    tabla.setEditTriggers(QTableWidget.NoEditTriggers)
    tabla.clearSelection()
    tabla.setCurrentCell(-1, -1)
    
    # Fuente
    font = QFont(font_name)
    tabla.setFont(font)
    
    # Encabezados en negrita
    header_font = QFont(font_name)
    header_font.setBold(True)
    tabla.horizontalHeader().setFont(header_font)
    
    # Ajuste de texto
    tabla.setWordWrap(True)
    
    # Scroll suave
    tabla.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    tabla.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    
    # Aplicar delegados si se proporcionan
    if delegate_columns:
        for column_name, delegate in delegate_columns.items():
            if column_name in headers:
                col_index = headers.index(column_name)
                tabla.setItemDelegateForColumn(col_index, delegate)
    
    # Aplicar delegado de texto para columnas especificadas
    if text_delegate_columns:
        text_delegate = TextDelegate(tabla)
        for column_name in text_delegate_columns:
            if column_name in headers:
                col_index = headers.index(column_name)
                tabla.setItemDelegateForColumn(col_index, text_delegate)
    
    # Altura de filas uniforme
    for row in range(tabla.rowCount()):
        tabla.setRowHeight(row, row_height)

def configurar_anchos_columnas(tabla, headers, columnas_especiales=None):
    """
    Configura los anchos de columnas de manera proporcional con algunas columnas especiales.
    
    Args:
        tabla: QTableWidget a configurar
        headers: Lista de encabezados de columna
        columnas_especiales: Diccionario de {nombre_columna: factor_ancho} para columnas con ancho especial
    """
    # Guardar el modo de ajuste actual de las columnas
    modos_actuales = []
    for col in range(tabla.columnCount()):
        modos_actuales.append(tabla.horizontalHeader().sectionResizeMode(col))
    
    # Establecer todas las columnas en modo stretch temporalmente
    for col in range(tabla.columnCount()):
        tabla.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
    
    # Actualizar el tamaño de la tabla para que se ajuste correctamente
    tabla.updateGeometry()
    tabla.viewport().updateGeometry()
    
    # Calcular anchos basados en el tamaño actual de la tabla
    ancho_tabla = tabla.width()
    columnas_count = len(headers)
    ancho_columna_estandar = ancho_tabla / columnas_count
    
    # Columnas especiales con ancho proporcional
    if columnas_especiales:
        for nombre_columna, factor in columnas_especiales.items():
            if nombre_columna in headers:
                indice = headers.index(nombre_columna)
                # Cambiar al modo fijo para columnas específicas
                tabla.horizontalHeader().setSectionResizeMode(indice, QHeaderView.Fixed)
                # Establecer ancho específico
                tabla.setColumnWidth(indice, int(ancho_columna_estandar * factor))
    
    # Asegurar que los cambios sean visibles inmediatamente
    tabla.horizontalHeader().update()
    
    return tabla