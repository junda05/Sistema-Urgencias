import os
import sys
import time
import traceback
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFileDialog, QProgressBar,
                           QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QUrl, QTimer, QObject, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from Front_end.styles.components import StyledMessageBox, StyledButton, StyledDialog, FormField

class PDFExporter(QObject):
    """Clase para exportar reportes HTML a PDF"""
    
    pdf_generated = pyqtSignal(bool, str)  # Señal para indicar que la generación del PDF está completa
    
    def __init__(self, web_view):
        super().__init__()
        self.web_view = web_view
        self.is_individual = False
        self.export_progress_dialog = None
        
    def detect_report_type(self):
        """Detecta si el informe actual es individual o grupal"""
        # Usamos JavaScript para verificar qué pestaña está activa o si el body tiene el atributo data-modo-actual
        js_code = """
        (function() {
            // Verificar si el body tiene el atributo data-modo-actual
            const modoAttr = document.body.getAttribute('data-modo-actual');
            if (modoAttr) {
                return modoAttr === 'individual';
            }
            
            // De lo contrario, verificar qué pestaña está activa
            const tabIndividual = document.getElementById('tabIndividual');
            if (tabIndividual) {
                return tabIndividual.classList.contains('tab-active');
            }
            
            // Por defecto, asumir que es grupal
            return false;
        })();
        """
        self.web_view.page().runJavaScript(js_code, self._handle_report_type_result)

    def _handle_report_type_result(self, is_individual):
        """Maneja el resultado de la detección del tipo de informe"""
        self.is_individual = bool(is_individual)
        print(f"Tipo de informe detectado: {'Individual' if self.is_individual else 'Grupal'}")
        self.start_export_process()
        
    def start_export_process(self):
        """Inicia el proceso de exportación después de determinar el tipo de informe"""
        # Mostrar un diálogo de archivo para elegir dónde guardar el PDF
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_type = "Individual" if self.is_individual else "Grupal"
        default_filename = f"Informe_{report_type}_{current_datetime}.pdf"
        
        filename, _ = QFileDialog.getSaveFileName(
            None,
            "Guardar Informe como PDF",
            os.path.join(os.path.expanduser("~"), "Documentos", default_filename),
            "Archivos PDF (*.pdf)"
        )
        
        if not filename:
            # Usuario canceló
            return
            
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
            
        # Crear y mostrar diálogo de progreso
        self.show_export_progress_dialog()
        
        # Iniciar el proceso de exportación con un pequeño retraso
        QTimer.singleShot(300, lambda: self.export_to_pdf(filename))
        
    def show_export_progress_dialog(self):
        """Muestra un diálogo de progreso estilizado"""
        # Crear un diálogo estilizado correctamente
        self.export_progress_dialog = StyledDialog("Exportando Informe", 400, None)
        
        # Añadir un icono o logo si está disponible
        try:
            logo_label = QLabel()
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                    "assets", "medicallogo.png")
            if os.path.exists(logo_path):
                logo_pixmap = QPixmap(logo_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(logo_pixmap)
                logo_label.setAlignment(Qt.AlignCenter)
                self.export_progress_dialog.layout.addWidget(logo_label)
        except Exception as e:
            print(f"Error al cargar logo: {str(e)}")
        
        # Etiqueta de mensaje
        message_label = QLabel("Generando archivo PDF, por favor espere...")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("font-size: 14px; color: #333333; margin: 10px 0;")
        self.export_progress_dialog.layout.addWidget(message_label)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Progreso indeterminado
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: #f0f0f0;
                height: 20px;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background-color: #5385B7;
                width: 20px;
            }
        """)
        self.export_progress_dialog.layout.addWidget(self.progress_bar)
        
        # Etiqueta de estado
        self.status_label = QLabel("Preparando contenido...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #555555;")
        self.export_progress_dialog.layout.addWidget(self.status_label)
        
        self.export_progress_dialog.layout.addSpacing(10)
        
        # Evitar cerrar el diálogo
        self.export_progress_dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.export_progress_dialog.resize(400, 200)
        self.export_progress_dialog.show()
        
        # Actualizar el progreso periódicamente
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress_message)
        self.progress_timer.start(1000)  # Actualizar cada segundo
        self.progress_counter = 0
        self.progress_messages = [
            "Preparando contenido...",
            "Procesando elementos visuales...",
            "Formateando documento...",
            "Optimizando para PDF...",
            "Generando archivo final...",
        ]
    
    def update_progress_message(self):
        """Actualiza el mensaje de progreso periódicamente"""
        if self.export_progress_dialog and hasattr(self, 'status_label'):
            self.progress_counter += 1
            message_index = min(self.progress_counter // 2, len(self.progress_messages) - 1)
            self.status_label.setText(self.progress_messages[message_index])
    
    def export_to_pdf(self, filename):
        """Exporta el informe actual a PDF"""
        try:
            self.status_label.setText("Generando PDF...")
            
            # Crear impresora
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            printer.setPageSize(QPrinter.A4)
            printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)
            
            # Adaptación: en lugar de usar setViewportSize que no existe,
            # configuramos el tamaño mediante JavaScript
            rect = printer.pageRect(QPrinter.DevicePixel)
            size_script = f"""
            (function() {{
                // Crear un estilo que cubra toda la página
                const style = document.createElement('style');
                style.textContent = `
                    @page {{ 
                        size: A4; 
                        margin: 15mm;
                    }}
                    @media print {{
                        body {{
                            width: {rect.width()}px;
                            min-height: {rect.height()}px;
                        }}
                    }}
                `;
                document.head.appendChild(style);
                return true;
            }})();
            """
            self.web_view.page().runJavaScript(size_script)
            
            # Desconectar de cualquier conexión anterior para evitar devoluciones de llamada duplicadas
            try:
                self.web_view.page().pdfPrintingFinished.disconnect()
            except:
                pass  # Ignorar si no existen conexiones
            
            # Conectar a la señal de finalizado
            self.web_view.page().pdfPrintingFinished.connect(
                lambda file_path, success: self._handle_pdf_generated(file_path, success, filename)
            )
            
            # Imprimir a PDF
            self.status_label.setText("Guardando PDF...")
            self.web_view.page().printToPdf(filename)
            
            # Dar tiempo suficiente para que se genere el PDF
            # La finalización real será manejada por _handle_pdf_generated
            QTimer.singleShot(8000, lambda: self._check_pdf_completion(filename))
            
        except Exception as e:
            self.close_progress_dialog()
            traceback.print_exc()
            self.show_error_message("Error al exportar", f"No se pudo exportar el informe a PDF: {str(e)}")
            self.pdf_generated.emit(False, str(e))
    
    def _handle_pdf_generated(self, file_path, success, filename):
        """Manejar el resultado de la generación del PDF"""
        print(f"Resultado de la generación de PDF: {'Éxito' if success else 'Fallido'}, Ruta: {file_path}")
        
        # Detener el temporizador de progreso
        if hasattr(self, 'progress_timer') and self.progress_timer.isActive():
            self.progress_timer.stop()
        
        # Cerrar el diálogo de progreso con un ligero retraso para asegurar que el PDF se escriba
        QTimer.singleShot(1000, self.close_progress_dialog)
        
        if success and os.path.exists(filename) and os.path.getsize(filename) > 0:
            self.show_success_message("Informe exportado", 
                                    f"El informe ha sido exportado correctamente a:\n{filename}")
            self.pdf_generated.emit(True, filename)
        else:
            self.show_error_message("Error al exportar", 
                                  f"No se pudo exportar el informe a PDF. Compruebe que la ruta sea válida y tenga permisos de escritura.")
            self.pdf_generated.emit(False, "Failed to generate PDF")
    
    def _check_pdf_completion(self, filename):
        """Comprobar si el PDF se creó correctamente cuando la devolución de llamada no se activa"""
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            # El PDF existe y tiene contenido, considerarlo un éxito si la devolución de llamada no se activó
            if self.export_progress_dialog and self.export_progress_dialog.isVisible():
                self._handle_pdf_generated(filename, True, filename)
        else:
            # Intentar un método alternativo si el primer intento falló
            try:
                # Usar enfoque de captura de página web
                page = self.web_view.page()
                
                # Método alternativo: usar la función de impresión directa
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(filename)
                printer.setPageSize(QPrinter.A4)
                
                # Imprimir usando la función de impresión estándar
                self.web_view.print_(printer)
                
                # Comprobar si el archivo fue creado después de un retraso
                QTimer.singleShot(5000, lambda: self._verify_pdf_exists(filename))
            except Exception as e:
                # Si todo lo demás falla, reportar error
                self.close_progress_dialog()
                self.show_error_message("Error al exportar", 
                                      f"No se pudo exportar el informe a PDF: {str(e)}")
                self.pdf_generated.emit(False, str(e))
    
    def _on_page_ready_for_print(self, success, filename):
        """Manejar impresión alternativa cuando la página está lista"""
        if success:
            # Crear impresora
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            printer.setPageSize(QPrinter.A4)
            
            # Imprimir usando la función de impresión estándar
            self.web_view.print_(printer)
            
            # Comprobar si el archivo fue creado después de un retraso
            QTimer.singleShot(2000, lambda: self._verify_pdf_exists(filename))
        else:
            self.close_progress_dialog()
            self.show_error_message("Error al exportar", 
                                  "No se pudo exportar el informe a PDF: La página no se cargó correctamente")
            self.pdf_generated.emit(False, "Page failed to load")
    
    def _verify_pdf_exists(self, filename):
        """Verificar que el PDF fue creado con el método alternativo"""
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            self.close_progress_dialog()
            self.show_success_message("Informe exportado", 
                                    f"El informe ha sido exportado correctamente a:\n{filename}")
            self.pdf_generated.emit(True, filename)
        else:
            self.close_progress_dialog()
            self.show_error_message("Error al exportar", 
                                  "No se pudo exportar el informe a PDF. Compruebe que la ruta sea válida y tenga permisos de escritura.")
            self.pdf_generated.emit(False, "Failed to verify PDF exists")
    
    def close_progress_dialog(self):
        """Cierra de manera segura el diálogo de progreso"""
        if self.export_progress_dialog and self.export_progress_dialog.isVisible():
            self.export_progress_dialog.accept()
            self.export_progress_dialog = None
    
    def show_error_message(self, title, message):
        """Muestra un diálogo de mensaje de error estilizado"""
        msg_box = StyledMessageBox(None, title, message, QMessageBox.Critical, "error")
        
        # Crear botón estilizado
        btn_ok = QPushButton("Aceptar")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #5385B7;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #659BD1;
            }
        """)
        
        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
        msg_box.setDefaultButton(btn_ok)
        
        msg_box.exec_()
    
    def show_success_message(self, title, message):
        """Muestra un diálogo de mensaje de éxito estilizado"""
        msg_box = StyledMessageBox(None, title, message, QMessageBox.Information, "info")
        
        # Crear botones estilizados
        btn_ok = QPushButton("Aceptar")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #5385B7;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #659BD1;
            }
        """)
        
        btn_open = QPushButton("Abrir PDF")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34c759;
            }
        """)
        
        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
        msg_box.addButton(btn_open, QMessageBox.ActionRole)
        msg_box.setDefaultButton(btn_ok)
        
        result = msg_box.exec_()
        
        # Si el usuario hizo clic en "Abrir PDF", abrir el archivo con la aplicación predeterminada
        if msg_box.clickedButton() == btn_open and message.startswith("El informe ha sido exportado correctamente a:"):
            file_path = message.split("\n")[1]
            self.open_pdf_file(file_path)
    
    def open_pdf_file(self, file_path):
        """Abre el archivo PDF con la aplicación predeterminada"""
        import platform
        import subprocess
        
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', file_path])
            else:  # Linux
                subprocess.call(['xdg-open', file_path])
        except Exception as e:
            print(f"Error al abrir el archivo PDF: {str(e)}")


# Esta función será importada y utilizada por la clase ReportGenerator
def export_report_to_pdf(web_view):
    """
    Función principal para exportar el informe mostrado en el web_view a PDF
    
    Args:
        web_view: Instancia de QWebEngineView que muestra el informe
    
    Returns:
        None
    """
    exporter = PDFExporter(web_view)
    exporter.detect_report_type()
    return exporter