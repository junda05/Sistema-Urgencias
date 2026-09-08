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
from frontend.styles.components import StyledMessageBox, StyledButton, StyledDialog, FormField

class PDFExporter(QObject):
    """Class that exports HTML reports to PDF"""

    pdf_generated = pyqtSignal(bool, str)  # Signal that indicates the PDF generation is complete

    def __init__(self, web_view):
        super().__init__()
        self.web_view = web_view
        self.is_individual = False
        self.export_progress_dialog = None

    def detect_report_type(self):
        """Detects whether the current report is individual or group"""
        # We use JavaScript to check which tab is active or whether the body has the data-current-mode attribute
        js_code = """
        (function() {
            // Check whether the body has the data-current-mode attribute
            const modeAttr = document.body.getAttribute('data-current-mode');
            if (modeAttr) {
                return modeAttr === 'individual';
            }

            // Otherwise, check which tab is active
            const tabIndividual = document.getElementById('tabIndividual');
            if (tabIndividual) {
                return tabIndividual.classList.contains('tab-active');
            }

            // By default, assume it is a group report
            return false;
        })();
        """
        self.web_view.page().runJavaScript(js_code, self._handle_report_type_result)

    def _handle_report_type_result(self, is_individual):
        """Handles the result of the report type detection"""
        self.is_individual = bool(is_individual)
        print(f"Detected report type: {'Individual' if self.is_individual else 'Group'}")
        self.start_export_process()

    def start_export_process(self):
        """Starts the export process after determining the report type"""
        # Show a file dialog so the user can choose where to save the PDF
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_type = "Individual" if self.is_individual else "Group"
        default_filename = f"Report_{report_type}_{current_datetime}.pdf"

        filename, _ = QFileDialog.getSaveFileName(
            None,
            "Save Report as PDF",
            os.path.join(os.path.expanduser("~"), "Documents", default_filename),
            "PDF Files (*.pdf)"
        )

        if not filename:
            # The user cancelled
            return

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        # Create and show the progress dialog
        self.show_export_progress_dialog()

        # Start the export process with a small delay
        QTimer.singleShot(300, lambda: self.export_to_pdf(filename))

    def show_export_progress_dialog(self):
        """Shows a styled progress dialog"""
        # Create a properly styled dialog
        self.export_progress_dialog = StyledDialog("Exporting Report", 400, None)

        # Add an icon or logo if one is available
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
            print(f"Error loading the logo: {str(e)}")

        # Message label
        message_label = QLabel("Generating the PDF file, please wait...")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("font-size: 14px; color: #333333; margin: 10px 0;")
        self.export_progress_dialog.layout.addWidget(message_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
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

        # Status label
        self.status_label = QLabel("Preparing the content...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #555555;")
        self.export_progress_dialog.layout.addWidget(self.status_label)

        self.export_progress_dialog.layout.addSpacing(10)

        # Prevent the dialog from being closed
        self.export_progress_dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.export_progress_dialog.resize(400, 200)
        self.export_progress_dialog.show()

        # Update the progress periodically
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress_message)
        self.progress_timer.start(1000)  # Update every second
        self.progress_counter = 0
        self.progress_messages = [
            "Preparing the content...",
            "Processing the visual elements...",
            "Formatting the document...",
            "Optimizing for PDF...",
            "Generating the final file...",
        ]

    def update_progress_message(self):
        """Updates the progress message periodically"""
        if self.export_progress_dialog and hasattr(self, 'status_label'):
            self.progress_counter += 1
            message_index = min(self.progress_counter // 2, len(self.progress_messages) - 1)
            self.status_label.setText(self.progress_messages[message_index])

    def export_to_pdf(self, filename):
        """Exports the current report to PDF"""
        try:
            self.status_label.setText("Generating the PDF...")

            # Create the printer
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            printer.setPageSize(QPrinter.A4)
            printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)

            # Workaround: instead of using setViewportSize, which does not exist,
            # we set the size through JavaScript
            rect = printer.pageRect(QPrinter.DevicePixel)
            size_script = f"""
            (function() {{
                // Create a style that covers the whole page
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

            # Disconnect from any previous connection to avoid duplicate callbacks
            try:
                self.web_view.page().pdfPrintingFinished.disconnect()
            except:
                pass  # Ignore it if there are no connections

            # Connect to the finished signal
            self.web_view.page().pdfPrintingFinished.connect(
                lambda file_path, success: self._handle_pdf_generated(file_path, success, filename)
            )

            # Print to PDF
            self.status_label.setText("Saving the PDF...")
            self.web_view.page().printToPdf(filename)

            # Allow enough time for the PDF to be generated
            # The actual completion will be handled by _handle_pdf_generated
            QTimer.singleShot(8000, lambda: self._check_pdf_completion(filename))

        except Exception as e:
            self.close_progress_dialog()
            traceback.print_exc()
            self.show_error_message("Export error", f"The report could not be exported to PDF: {str(e)}")
            self.pdf_generated.emit(False, str(e))

    def _handle_pdf_generated(self, file_path, success, filename):
        """Handles the result of the PDF generation"""
        print(f"PDF generation result: {'Success' if success else 'Failed'}, Path: {file_path}")

        # Stop the progress timer
        if hasattr(self, 'progress_timer') and self.progress_timer.isActive():
            self.progress_timer.stop()

        # Close the progress dialog with a slight delay to make sure the PDF is written
        QTimer.singleShot(1000, self.close_progress_dialog)

        if success and os.path.exists(filename) and os.path.getsize(filename) > 0:
            self.show_success_message("Report exported",
                                    f"The report has been exported successfully to:\n{filename}")
            self.pdf_generated.emit(True, filename)
        else:
            self.show_error_message("Export error",
                                  f"The report could not be exported to PDF. Check that the path is valid and that you have write permissions.")
            self.pdf_generated.emit(False, "Failed to generate PDF")

    def _check_pdf_completion(self, filename):
        """Checks whether the PDF was created correctly when the callback is not triggered"""
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            # The PDF exists and has content, treat it as a success if the callback did not fire
            if self.export_progress_dialog and self.export_progress_dialog.isVisible():
                self._handle_pdf_generated(filename, True, filename)
        else:
            # Try an alternative method if the first attempt failed
            try:
                # Use the web page capture approach
                page = self.web_view.page()

                # Alternative method: use the direct printing function
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(filename)
                printer.setPageSize(QPrinter.A4)

                # Print using the standard printing function
                self.web_view.print_(printer)

                # Check whether the file was created after a delay
                QTimer.singleShot(5000, lambda: self._verify_pdf_exists(filename))
            except Exception as e:
                # If everything else fails, report the error
                self.close_progress_dialog()
                self.show_error_message("Export error",
                                      f"The report could not be exported to PDF: {str(e)}")
                self.pdf_generated.emit(False, str(e))

    def _on_page_ready_for_print(self, success, filename):
        """Handles the alternative printing once the page is ready"""
        if success:
            # Create the printer
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            printer.setPageSize(QPrinter.A4)

            # Print using the standard printing function
            self.web_view.print_(printer)

            # Check whether the file was created after a delay
            QTimer.singleShot(2000, lambda: self._verify_pdf_exists(filename))
        else:
            self.close_progress_dialog()
            self.show_error_message("Export error",
                                  "The report could not be exported to PDF: the page did not load correctly")
            self.pdf_generated.emit(False, "Page failed to load")

    def _verify_pdf_exists(self, filename):
        """Verifies that the PDF was created with the alternative method"""
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            self.close_progress_dialog()
            self.show_success_message("Report exported",
                                    f"The report has been exported successfully to:\n{filename}")
            self.pdf_generated.emit(True, filename)
        else:
            self.close_progress_dialog()
            self.show_error_message("Export error",
                                  "The report could not be exported to PDF. Check that the path is valid and that you have write permissions.")
            self.pdf_generated.emit(False, "Failed to verify PDF exists")

    def close_progress_dialog(self):
        """Safely closes the progress dialog"""
        if self.export_progress_dialog and self.export_progress_dialog.isVisible():
            self.export_progress_dialog.accept()
            self.export_progress_dialog = None

    def show_error_message(self, title, message):
        """Shows a styled error message dialog"""
        msg_box = StyledMessageBox(None, title, message, QMessageBox.Critical, "error")

        # Create a styled button
        btn_ok = QPushButton("Accept")
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
        """Shows a styled success message dialog"""
        msg_box = StyledMessageBox(None, title, message, QMessageBox.Information, "info")

        # Create the styled buttons
        btn_ok = QPushButton("Accept")
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

        btn_open = QPushButton("Open PDF")
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

        # If the user clicked "Open PDF", open the file with the default application
        if msg_box.clickedButton() == btn_open and message.startswith("The report has been exported successfully to:"):
            file_path = message.split("\n")[1]
            self.open_pdf_file(file_path)

    def open_pdf_file(self, file_path):
        """Opens the PDF file with the default application"""
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
            print(f"Error opening the PDF file: {str(e)}")


# This function will be imported and used by the ReportGenerator class
def export_report_to_pdf(web_view):
    """
    Main function that exports the report displayed in the web_view to PDF

    Args:
        web_view: QWebEngineView instance that displays the report

    Returns:
        None
    """
    exporter = PDFExporter(web_view)
    exporter.detect_report_type()
    return exporter
