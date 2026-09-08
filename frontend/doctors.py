from PyQt5.QtWidgets import (QMainWindow, QCompleter, QWidget, QVBoxLayout, QHBoxLayout,
                           QTableWidget, QTableWidgetItem, QPushButton,
                           QLabel, QMessageBox, QMenu, QFrame, QLayout,
                           QLineEdit, QFormLayout, QDialog, QListWidget, QListWidgetItem,
                           QHeaderView, QSizePolicy, QDesktopWidget, QApplication, QToolTip,
                           QGraphicsOpacityEffect, QDateTimeEdit, QCheckBox, QGridLayout, QGroupBox, QScrollArea, QListView)
from PyQt5.QtCore import Qt, QTimer, QRect, QSize, QStringListModel, QPropertyAnimation, QEasingCurve, QPoint, QDateTime
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont, QPixmap, QIcon, QLinearGradient, QGradient
from backend.database import PatientModel
from backend.users.users_model import UsersModel
from datetime import datetime
import sys
import os
# Import animation components from their correct location
from frontend.styles.animation_components import SplashScreen, FadeAnimation
# Import styles and components
from frontend.styles.styles import TABLE_STYLES_UPDATED, SCROLLBAR_STYLE
from frontend.styles.components import StyledMessageBox, StyledButton, StyledDialog, FormField
from frontend.styles.table_components import StatusCircleDelegate, TextDelegate, CustomColumnHeader, configure_standard_table
from frontend.styles.header_components import CombinedHeader
from frontend.styles.lateral_menu import LateralMenu, MenuToggleButton
from frontend.styles.custom_widgets import ButtonFrame, TableContainer
from frontend.styles.font_utils import apply_system_fonts
from frontend.styles.frontend_utils import FilterDialog, LabsSelector, ImagingSelector
from frontend.styles.styles import COLORS, BORDER_RADIUS, MENU_STYLES

class DoctorView(QMainWindow):
    def __init__(self, login_interface):
        super().__init__()
        self.login_interface = login_interface
        self.model = PatientModel()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Apply custom fonts immediately
        apply_system_fonts()

        # Get screen size for responsive elements
        self.screen = QDesktopWidget().screenGeometry()

        # Initialize a flag to track the first load of the table
        self.first_load = True

        # Show the loading screen while the interface initializes
        # Keeping the style consistent with the main program
        self.splash = SplashScreen(None, logo_path=None, message="Loading patient interface...", duration=1.5)
        self.splash.setFixedSize(int(self.screen.width() * 0.3), int(self.screen.height() * 0.3))
        self.splash.show()
        self.splash.opacity_animation.start()  # Start fade-in animation
        QApplication.processEvents()

        # Opacity effect for the entrance animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)  # Start invisible

        # Improved path handling for both script and frozen executable
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle (compiled with PyInstaller)
            self.base_path = sys._MEIPASS
        else:
            # For normal script execution
            self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        images_path = os.path.join(self.base_path, "frontend", "images")
        self.logo_path = os.path.join(images_path, "logo.png")
        self.icon_path = os.path.join(images_path, "logo.ico")
        self.secondary_logo_path = os.path.join(images_path, "secondary_logo.png")

        # Set the window icon
        if os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))

        # Variables used to move the window without a title bar
        self.dragging = False
        self.offset = None

        # Area definitions
        self.areas = {
            "Old wing": (1, 18),
            "Yellow": (19, 38),
            "Pediatrics": (39, 59),
            "Hallways": (60, 200),
            "Clinic": (1, 40),
            "Waiting room": (1, 2),
        }

        # Table headers - Imaging replaces IX
        self.headers = ["Name", "Document ID", "Triage", "Admission Consult", "Labs", "Imaging", "Specialist Consult", "Reassessment", "Pending Tasks", "Disposition", "Location", "Admission"]

        # Create the side menu BEFORE configuring the window and building the interface
        self.side_menu = LateralMenu(self)

        # Add this new variable to store the search text
        self.current_search_text = ""

        # Import the preferences model used for filters
        from backend.users.preferences_model import PreferencesModel
        from backend.database import AuthenticationModel

        # Get the current user
        credentials = AuthenticationModel.get_credentials()
        self.current_user = credentials.get('user')

        # Load area filter preferences
        self.filtered_areas = PreferencesModel.get_area_filters(
            self.current_user, list(self.areas.keys())
        )

        # If there are no filtered areas, use all of them by default
        if not self.filtered_areas:
            self.filtered_areas = list(self.areas.keys())
            self.show_information_message("Information", "No filters were found, using all areas")

        # Initialize variables for the date filter
        self.date_filter_active = False
        self.start_date = None
        self.end_date = None

        # Configure the window and build the interface (this creates self.table)
        self.configure_window()
        self.create_interface()

        # Close the loading screen before showing the main interface
        self.splash.accept()

        # Now that the interface is created, initialize the timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_table)
        self.timer.start(5000)

        # Entrance animation
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()

        # Update the table for the first time once the interface is complete
        self.update_table()
        self.model.data_updated.connect(self.update_table)

        # After create_interface or at the end of init
        self.configure_side_menu()

    def mousePressEvent(self, event):
        # Allow dragging the window
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        # Move the window while it is being dragged
        if self.dragging:
            self.move(self.mapToGlobal(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        # Stop the dragging
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def start(self):
        self.show()
        # Set a single-shot timer to apply the column widths after the window is shown
        QTimer.singleShot(100, self.configure_column_widths)
        return QApplication.instance().exec_()

    def create_interface(self):
        # Main central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  # Remove space between widgets

        # Create and add the combined bar with logo using the reusable component
        combined_header = self.create_combined_header()
        main_layout.addWidget(combined_header)

        # Create a container for the main content
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 50, 20, 20)
        content_layout.setSpacing(15)

        # Create the toolbar with buttons and logout
        toolbar = self.create_toolbar()
        content_layout.addWidget(toolbar)

        # Create the table with a limited size
        table_container = self.create_table_container()
        content_layout.addWidget(table_container)

        # Add the content container to the main layout
        main_layout.addWidget(content_container)

    def create_toolbar(self):
        """Creates a toolbar with action buttons and a search bar"""
        from frontend.styles.custom_buttons import IconButton, SearchContainer

        # Container for the toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet(f"background-color: {COLORS['background_transparent']};")

        # Make the buttons more responsive
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        # Horizontal layout to arrange the elements
        toolbar_layout = QHBoxLayout(toolbar)
        # Reduce the margins to make better use of the space
        toolbar_layout.setContentsMargins(int(screen_width * 0.05), int(screen_height * 0.01),
                                              int(screen_width * 0.05), int(screen_height * 0.01))
        # Proportional spacing between elements
        toolbar_layout.setSpacing(int(screen_width * 0.05))

        # Compute the size based on the screen width to keep consistency
        button_width = int(screen_width * 0.17)
        button_height = int(screen_height * 0.07)  # A more reasonable height

        # Create the search container with the new SearchContainer class
        # Passing the button height to keep consistency
        search_container = SearchContainer(height=int(screen_height * 0.07))

        # Path to the magnifier icon
        search_icon_path = os.path.join(self.base_path, "frontend", "images", "search.png")
        search_container.set_icon(search_icon_path)

        # Connect the search event
        self.search_input = search_container.get_search_input()
        self.search_input.textChanged.connect(self.search_patient)

        # Get the icon paths for the buttons
        add_image_path = os.path.join(self.base_path, "frontend", "images", "add_icon.png")
        delete_image_path = os.path.join(self.base_path, "frontend", "images", "delete_icon.png")

        # Create the buttons with icons and make them larger
        btn_add = IconButton("Add patient", add_image_path if os.path.exists(add_image_path) else None, COLORS['background_header'])
        btn_delete = IconButton("Delete Patient", delete_image_path if os.path.exists(delete_image_path) else None, COLORS['background_header'])

        # Set fixed heights instead of minimum sizes for consistency
        btn_add.setFixedHeight(button_height)
        btn_delete.setFixedHeight(button_height)

        # Keep the minimum width for responsiveness
        btn_add.setMinimumWidth(button_width)
        btn_delete.setMinimumWidth(button_width)

        # Size policies for the buttons (expand horizontally)
        btn_add.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_delete.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Connect the events to the buttons
        btn_add.clicked.connect(self.show_add_form)
        btn_delete.clicked.connect(self.confirm_deletion)

        # Add the elements to the layout with even space proportions
        # The search container takes more space (factor 2)
        toolbar_layout.addWidget(search_container, 2)
        toolbar_layout.addWidget(btn_add, 1)
        toolbar_layout.addWidget(btn_delete, 1)

        return toolbar

    def search_patient(self):
        """Filters the patients in the table according to the search text"""
        self.current_search_text = self.search_input.text().lower()

        self.apply_search_filter()

    def apply_search_filter(self):
        """Applies the current search filter to the table"""
        # If the field is empty, show every record
        if not self.current_search_text:
            for i in range(self.table.rowCount()):
                self.table.setRowHidden(i, False)
            return

        # Iterate over all the rows of the table
        for i in range(self.table.rowCount()):
            # Check whether there is data in the relevant cells
            name_item = self.table.item(i, 0)
            document_item = self.table.item(i, 1)

            if name_item and document_item:
                name = name_item.text().lower()
                document = document_item.text().lower()

                # Show the row if the search text is in the name or the document
                if self.current_search_text in name or self.current_search_text in document:
                    self.table.setRowHidden(i, False)
                else:
                    self.table.setRowHidden(i, True)

    def create_combined_header(self):
        # Create a combined container for the title and the logo
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['background_header']};")

        # Compute the sizes to make sure they match the login interface
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        logo_height = int(screen_height * 0.14)

        # Set a fixed height for the whole header
        header.setFixedHeight(logo_height)

        # Create the layout that arranges the logo and the buttons
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 10, 0)

        # Logo area (left side)
        if os.path.exists(self.logo_path):
            logo_width = int(screen_width * 0.2)

            logo_label = QLabel()
            logo_pixmap = QPixmap(self.logo_path)
            scaled_logo = logo_pixmap.scaled(
                logo_width,
                logo_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            logo_label.setPixmap(scaled_logo)
            logo_label.setStyleSheet(f"background: {COLORS['background_transparent']};")

            # Add the logo to the left side
            header_layout.addWidget(logo_label, 0, Qt.AlignLeft | Qt.AlignVCenter)

        # Add expandable space in the middle
        header_layout.addStretch(1)

        # Container for the control buttons and the secondary logo
        container_right = QWidget()
        layout_right = QVBoxLayout(container_right)
        layout_right.setContentsMargins(0, 0, 0, 0)
        layout_right.setSpacing(5)

        # Container for the control buttons
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)

        # Add the menu button before the control buttons
        self.menu_button = MenuToggleButton(self, self.side_menu)
        buttons_layout.addWidget(self.menu_button)

        # Control buttons (right side) - without a logout button
        buttons = [
            ("🗕", self.showMinimized, False),
            ("🗗", self.toggle_maximized, False),
            ("✖", self.close, True)
        ]

        for text, function, is_close_button in buttons:
            button = StyledButton(text, "window_control", is_close=is_close_button)
            button.setFixedSize(30, 30)
            button.clicked.connect(function)
            buttons_layout.addWidget(button)

        # Add the button container to the right layout
        layout_right.addWidget(buttons_container, 0, Qt.AlignRight | Qt.AlignTop)

        # Secondary logo area (below the buttons)
        if hasattr(self, 'secondary_logo_path') and os.path.exists(self.secondary_logo_path):
            secondary_logo_height = int(screen_height * 0.1)  # Same as in login_interface.py
            secondary_logo_width = int(screen_width * 0.15)  # Same as in login_interface.py

            secondary_logo_label = QLabel()
            secondary_logo_pixmap = QPixmap(self.secondary_logo_path)
            scaled_secondary_logo = secondary_logo_pixmap.scaled(
                secondary_logo_width,
                secondary_logo_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            secondary_logo_label.setPixmap(scaled_secondary_logo)
            secondary_logo_label.setFixedSize(scaled_secondary_logo.size())  # Fix the size exactly to the logo size
            secondary_logo_label.setStyleSheet(f"background: {COLORS['background_transparent']}; border: none;")

            # Align the secondary logo to the right
            secondary_logo_container = QWidget()
            secondary_logo_layout = QHBoxLayout(secondary_logo_container)
            secondary_logo_layout.setContentsMargins(0, 0, 0, 0)
            secondary_logo_layout.addStretch(1)  # Pushes the logo to the right
            secondary_logo_layout.addWidget(secondary_logo_label)

            # Add the logo container to the right layout
            layout_right.addWidget(secondary_logo_container, 0, Qt.AlignRight)

        # Add the right container to the main layout
        header_layout.addWidget(container_right, 0, Qt.AlignTop)

        return header

    def create_table_container(self):
        # Use the reusable TableContainer with consistent sizes
        table_container = TableContainer(self, 0.96, 0.638)

        # Create the table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.headers))
        # Two-word stage names are wrapped so they fit the column width.
        # self.headers keeps the single-line names the column lookups rely on.
        self.table.setHorizontalHeaderLabels(
            [header.replace(" Consult", "\nConsult") for header in self.headers])
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Apply the table styles directly, as in the previous version
        self.table.setStyleSheet(TABLE_STYLES_UPDATED["main"] + SCROLLBAR_STYLE)

        # Hide row numbers
        self.table.verticalHeader().setVisible(False)

        # Configure the delegate for colored circles - implemented as in the previous version
        circle_delegate = StatusCircleDelegate(self.table)
        status_columns = ['Triage', 'Admission Consult', 'Labs', 'Imaging', 'Specialist Consult', 'Reassessment']
        for header in status_columns:
            col_index = self.headers.index(header)
            self.table.setItemDelegateForColumn(col_index, circle_delegate)

        # Also use circle delegate for Disposition to support alarm visualization
        disposition_index = self.headers.index('Disposition')
        self.table.setItemDelegateForColumn(disposition_index, circle_delegate)

        # Configure delegate for text cells to show tooltips
        text_delegate = TextDelegate(self.table)
        for col in range(self.table.columnCount()):
            if col not in [self.headers.index(h) for h in status_columns] and col != disposition_index:
                self.table.setItemDelegateForColumn(col, text_delegate)

        # Enable smooth scrolling
        self.table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)

        # Style settings for the table
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.clearSelection()
        self.table.setCurrentCell(-1, -1)

        # Use the new font for the table
        self.table.setFont(QFont("Segoe UI", 10))

        # Improve the style of the headers
        header_font = QFont("Segoe UI", 10)
        header_font.setBold(True)
        self.table.horizontalHeader().setFont(header_font)

        self.table.setWordWrap(True)

        # Add the table to the container
        table_container.set_table(self.table)

        # Connect the resize event to keep the column widths
        self.table.horizontalHeader().sectionResized.connect(
            lambda index, oldSize, newSize: QTimer.singleShot(0, self.configure_column_widths)
        )

        return table_container

    def closeEvent(self, event):
        """Override the close event to stop the timer"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        # Continue with the normal close without showing a loading screen
        super().closeEvent(event)

    def configure_window(self): self.setWindowTitle("Patient Management"); self.setStyleSheet("background-color: #4A7296;"); self.showMaximized()

    def start_periodic_update(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_table)

    def configure_column_widths(self):
        """Configures the table column widths to ensure consistency"""
        # Save the current resize mode of the columns
        current_modes = []
        for col in range(self.table.columnCount()):
            current_modes.append(self.table.horizontalHeader().sectionResizeMode(col))

        # Temporarily set every column to stretch mode
        for col in range(self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)

        # Update the table size so that it adjusts correctly
        self.table.updateGeometry()
        self.table.viewport().updateGeometry()

        # Compute the widths based on the current table size
        table_width = self.table.width()
        columns_count = len(self.headers)
        standard_column_width = table_width / columns_count

        # Apply specific widths to the selected columns
        name_index = self.headers.index('Name')
        pending_tasks_index = self.headers.index('Pending Tasks')

        # Switch to fixed mode for the specific columns
        self.table.horizontalHeader().setSectionResizeMode(name_index, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(pending_tasks_index, QHeaderView.Fixed)

        # Set the specific widths
        self.table.setColumnWidth(name_index, int(standard_column_width * 1.3))
        self.table.setColumnWidth(pending_tasks_index, int(standard_column_width * 1.5))

        # Make sure the changes are visible immediately
        self.table.horizontalHeader().update()

    def logout(self):
        if self.show_confirmation_message(
            "Confirm Log Out",
            "Are you sure you want to log out?"
        ):
            # We removed the animation that was causing problems
            # and call the method that performs the logout directly
            self.perform_logout()

    def perform_logout(self):
        """Method executed after the logout animation completes"""
        # Show a loading screen during the logout with a consistent style
        splash = SplashScreen(None, logo_path=self.logo_path, message="Logging out...", duration=1.5)
        splash.setFixedSize(int(self.screen.width() * 0.3), int(self.screen.height() * 0.3))
        splash.show()
        splash.opacity_animation.start()  # Start fade-in animation
        QApplication.processEvents()

        # Stop the timer before closing
        if hasattr(self, 'timer'):
            self.timer.stop()

        try:
            if hasattr(self.model, 'conn') and self.model.conn:
                self.model.conn.close()
        except Exception as e:
            self.show_information_message("Error", f"Error closing the database connection: {e}", QMessageBox.Critical)

        # Wait until the loading screen finishes
        splash.exec_()

        self.close()
        self.login_interface.reset_login()

    def update_table(self):
        try:
            # Check that the table exists before trying to use it
            if not hasattr(self, 'table'):
                self.show_information_message("Error", "The table has not been initialized yet", QMessageBox.Critical)
                return

            # If this is the first load, show a loading screen with a consistent style
            if self.first_load:
                splash = SplashScreen(self, logo_path=self.logo_path, message="Loading patient data...", duration=1)
                splash.setFixedSize(int(self.screen.width() * 0.3), int(self.screen.height() * 0.3))
                splash.show()
                splash.opacity_animation.start()  # Make sure the animation starts
                QApplication.processEvents()

            # Get the data using the model with the filters applied
            if self.date_filter_active and self.start_date and self.end_date:
                start_date_str = self.start_date.toString("yyyy-MM-dd HH:mm:ss")
                end_date_str = self.end_date.toString("yyyy-MM-dd HH:mm:ss")
                data = self.model.get_filtered_patient_data(
                    self.filtered_areas,
                    start_date_str,
                    end_date_str
                )
            else:
                data = self.model.get_filtered_patient_data(self.filtered_areas)

            self.table.setRowCount(0)

            # Get the cells with an alarm from the model
            alarm_cells = self.model.check_alarms(data)
            disposition_alarm_cells = self.model.check_disposition_alarm(data)
            triage_index = self.headers.index('Triage')
            pending_tasks_index = self.headers.index('Pending Tasks')  # Index of the pending tasks column

            if data:
                for row_idx, row in enumerate(data):
                    current_row = list(row[:12])  # First 12 fields for the table

                    # Insert the row into the table
                    self.table.insertRow(row_idx)
                    for col, value in enumerate(current_row):
                        # Check whether this is a column that must use the special delegate
                        if col == triage_index or col == self.headers.index('Admission Consult') or \
                           col == self.headers.index('Labs') or col == self.headers.index('Imaging') or \
                           col == self.headers.index('Specialist Consult') or col == self.headers.index('Reassessment') or \
                           col == self.headers.index('Disposition'):
                            # Use a custom item so that it works with the delegate
                            item = CustomColumnHeader("", str(value))
                            self.table.setItem(row_idx, col, item)
                        # elif col == pending_tasks_index:
                        #     # For the pending tasks column, make sure it is shown exactly as it comes from the DB
                        #     # without any extra processing
                        #     pending_tasks_text = str(value) if value is not None else ""
                        #     item = QTableWidgetItem(pending_tasks_text)
                        #     item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Left alignment for better readability
                        #     self.table.setItem(row_idx, col, item)
                        else:
                            # For normal text
                            item = QTableWidgetItem(str(value))
                            item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                            self.table.setItem(row_idx, col, item)

                # Update the alarms in the delegate for Admission Consult
                admission_consult_col = self.headers.index('Admission Consult')
                delegate = self.table.itemDelegateForColumn(admission_consult_col)
                if isinstance(delegate, StatusCircleDelegate):
                    delegate.set_alarm_cells(alarm_cells)

                # Update the disposition alarms
                disposition_col = self.headers.index('Disposition')
                delegate = self.table.itemDelegateForColumn(disposition_col)
                if isinstance(delegate, StatusCircleDelegate):
                    delegate.set_disposition_alarm_cells(disposition_alarm_cells)

                # Apply the column width configuration after loading the data
                self.configure_column_widths()

                # Set a fixed height for every row based on the circle size
                circle_delegate = self.table.itemDelegateForColumn(triage_index)
                if isinstance(circle_delegate, StatusCircleDelegate):
                    row_height = circle_delegate.circle_size + 20  # +20 for extra padding
                    for row in range(self.table.rowCount()):
                        self.table.setRowHeight(row, row_height)

                # Apply colors to specific rows
                for row_idx, row in enumerate(data):
                    self.color_row(row_idx, row)

            # After updating the table, apply the filter again if there is search text
            if hasattr(self, 'current_search_text') and self.current_search_text:
                self.apply_search_filter()

            # Close the loading screen if this is the first time
            if self.first_load:
                self.first_load = False
                if 'splash' in locals():
                    splash.accept()
        except Exception as e:
            self.show_information_message("Error", f"Error updating the table: {str(e)}", QMessageBox.Critical)
        finally:
            self.model.close_db()

    def color_row(self, row, data):
        status_columns = {
            'Triage': self.headers.index('Triage'),
            'Admission Consult': self.headers.index('Admission Consult'),
            'Labs': self.headers.index('Labs'),
            'Imaging': self.headers.index('Imaging'),  # Corrected from 'IX' to 'Imaging'
            'Specialist Consult': self.headers.index('Specialist Consult'),
            'Reassessment': self.headers.index('Reassessment')
        }

        for field, index in status_columns.items():
            try:
                value = data[index]
                custom_item = CustomColumnHeader("", value)
                self.table.setItem(row, index, custom_item)
            except Exception as e:
                self.show_information_message("Error", f"Error coloring cell {field}: {str(e)}", QMessageBox.Critical)

    def hex_to_qcolor(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return QColor(int(hex_color[:2], 16),
                    int(hex_color[2:4], 16),
                    int(hex_color[4:], 16))

    def request_document(self, title):
        dialog = StyledDialog(title, 400, self)

        # Add the title and the description
        dialog.add_title("Search by document")

        description = QLabel("Enter the document number to search for the patient:")
        description.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: {COLORS['background_transparent']};")
        description.setWordWrap(True)
        dialog.layout.addWidget(description)
        dialog.layout.addSpacing(10)

        # Create the input field
        label, entry = FormField.create_line_edit("", False, False, "")
        entry.setPlaceholderText("Enter document number")
        dialog.layout.addWidget(entry)
        dialog.layout.addSpacing(20)

        # Buttons
        document = [None]  # Use a list as a mutable variable so the nested functions can access it

        def search():
            document[0] = entry.text()
            if not document[0]:
                self.show_warning_message("Warning", "You must enter a document")
                return
            dialog.accept()

        def cancel():
            dialog.reject()

        buttons = [
            ("Search", search, "primary"),
            ("Cancel", cancel, "danger")
        ]

        dialog.add_button_row(buttons)

        if dialog.exec_() == QDialog.Accepted:
            return document[0]
        return None

    def select_record(self, records, mode="editing"):
        # Increase the width from 500 to 800 to remove the horizontal scroll
        dialog_width_value = 800

        dialog = StyledDialog(f"Select Record to {mode.capitalize()}", dialog_width_value, self)

        # Add the title and the description
        dialog.add_title(f"Select record to {mode}")

        description = QLabel(f"Several records were found. Please select the one you want to {mode}:")
        description.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            background-color: {COLORS['background_transparent']};
            font-size: 15px;
            margin-bottom: 8px;
        """)
        description.setWordWrap(True)
        dialog.layout.addWidget(description)
        dialog.layout.addSpacing(10)

        # Container for the list with a border
        list_container = QWidget()
        list_container.setStyleSheet(f"""
            background-color: {COLORS['background_white']};
            border: 1px solid {COLORS['border_light']};
            border-radius: {BORDER_RADIUS['medium']};
        """)
        list_container_layout = QVBoxLayout(list_container)
        list_container_layout.setContentsMargins(5, 5, 5, 5)

        # Record list with an improved style
        record_list = QListWidget()
        record_list.setMinimumWidth(dialog_width_value - 80)
        record_list.setStyleSheet(f"""
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
        record_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)

        # Make sure the list has a responsive height
        screen_height = QDesktopWidget().availableGeometry().height()
        record_list.setMinimumHeight(min(int(screen_height * 0.3), 300))

        from datetime import datetime

        # Updated implementation that handles both strings and datetime objects
        sorted_by_date = []

        for record in records:
            date_value = record[12]

            # Check whether the value already is a datetime
            if isinstance(date_value, datetime):
                date_dt = date_value
                sorted_by_date.append((record, date_dt))
            elif isinstance(date_value, str) and date_value:
                try:
                    date_dt = datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S")
                    sorted_by_date.append((record, date_dt))
                except Exception as e:
                    print(f"The date could not be parsed (string): {date_value}, Error: {e}")
                    sorted_by_date.append((record, datetime.min))
            else:
                print(f"Unrecognized date value: {type(date_value)}, value: {date_value}")
                sorted_by_date.append((record, datetime.min))

        # Sort from the most recent to the oldest
        sorted_by_date.sort(key=lambda x: x[1], reverse=True)

        # Extract the sorted records
        sorted_records = [item[0] for item in sorted_by_date]

        # Print debug information
        for i, (record, date) in enumerate(sorted_by_date):
            print(f"Record {i}: {record[12]} -> {date}")

        # Show the records in the list
        for record in sorted_records:
            name = record[0]
            location = record[11]
            admission = record[12]

            # Show the information as "Name - Location - Admission Date"
            item_text = f"{name} - {location} - {admission}"
            item = QListWidgetItem(item_text)

            # Make sure every item has the same consistent size
            item.setSizeHint(QSize(record_list.width() - 20, 50))
            record_list.addItem(item)

        # Add the list to the container
        list_container_layout.addWidget(record_list)

        # Add the container to the dialog window
        dialog.layout.addWidget(list_container)
        dialog.layout.addSpacing(15)

        selected_record = [None]  # Use a list so the nested functions can access it

        def select():
            if record_list.currentRow() >= 0:
                selected_record[0] = sorted_records[record_list.currentRow()]  # Use the sorted list
                dialog.accept()
            else:
                self.show_warning_message("Warning", "You must select a record")

        def cancel():
            dialog.reject()

        buttons = [
            ("Select", select, "primary"),
            ("Cancel", cancel, "danger")
        ]

        dialog.add_button_row(buttons)

        for i in range(dialog.button_layout.count()):
            widget = dialog.button_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setFixedHeight(40)
                widget.setMinimumWidth(120)

        # Center the dialog correctly after adjusting its size
        dialog.adjustSize()
        screen = QDesktopWidget().availableGeometry()
        dialog_x = (screen.width() - dialog.width()) // 2
        dialog_y = (screen.height() - dialog.height()) // 2
        dialog.move(dialog_x, dialog_y)

        if dialog.exec_() == QDialog.Accepted:
            return selected_record[0]
        return None

    def confirm_deletion(self, row=None):
        document = self.request_document("Delete patient")
        if not document:
            return

        records = self.model.get_record_by_document(document=document)

        if not records:
            self.show_information_message("Error", "No patient was found with the entered document", QMessageBox.Critical)
            return

        if len(records) > 1:
            selected_record = self.select_record(records, mode="deletion")
            if selected_record:
                patient_name = selected_record[0]  # The name is at index 0
                if self.show_confirmation_message(
                    "Confirm Deletion",
                    f"Are you sure you want to delete patient {patient_name}?"
                ):
                    self.delete_record(selected_record)

        else:
            patient_name = records[0][0]  # The name is at index 0
            if self.show_confirmation_message(
                "Confirm Deletion",
                f"Are you sure you want to delete patient {patient_name}?"
            ):
                self.delete_record(records[0])

    def delete_record(self, record):
        try:
            record_id = record[13]
            patient_name = record[0]
            patient_document = record[1]

            self.model.delete(record_id)

            # Update the table and show a success message
            self.update_table()
            self.show_information_message("Success", f"Patient {patient_name} has been deleted successfully.")

        except Exception as e:
            self.show_information_message("Error", f"Error deleting the patient: {str(e)}", QMessageBox.Critical)
        finally:
                self.model.close_db()

    def update_admission_consult(self):
        if self.inputs["triage"].currentText() in ["1", "2", "3", "4", "5"]:
            self.inputs["admission_consult"].setCurrentText("Not completed")

    def show_add_form(self):
        dialog = StyledDialog("Add patient", 1000, self)  # Increased width for horizontal layout

        # Center the dialog properly on screen
        screen = QDesktopWidget().availableGeometry()
        dialog_width = 1000
        dialog_height = int(screen.height() * 0.85)  # Use 85% of screen height

        # Calculate centered position
        dialog_x = (screen.width() - dialog_width) // 2
        dialog_y = (screen.height() - dialog_height) // 2

        dialog.setGeometry(dialog_x, dialog_y, dialog_width, dialog_height)

        # Add the title
        dialog.add_title("Add new patient")

        # Add the required fields indicator
        dialog.add_required_fields_indicator()

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

        # Basic form fields
        fields = [
            ("Name:", "name", True, ""),
            ("Document ID:", "document_id", True, ""),
            ("Triage:", "triage", False, "", ["", "Not completed", "1", "2", "3", "4", "5"]),
            ("Admission Consult:", "admission_consult", False, "", ["", "Not completed", "Completed"]),
            ("Labs:", "labs", False, "", ["", "Not started", "Awaiting results", "Results complete"]),
            ("Imaging:", "imaging", False, "", ["", "Not started", "Awaiting results", "Results complete"]),
            ("Specialist Consult:", "specialist_consult", False, "", ["", "Not opened", "Open", "Completed"]),
            ("Reassessment:", "reassessment", False, "", ["", "Completed", "Not completed"]),
            ("Pending Tasks:", "pending_tasks", False, ""),
            ("Disposition:", "disposition", False, "", ["", "Hospitalized", "Observation", "Discharged"])
        ]

        self.inputs = {}

        for field in fields:
            if len(field) > 4:  # It is a combobox
                label_text, key, is_required, initial_value, options = field
                label, combo = FormField.create_combo_box(label_text, options, is_required, initial_value)
                self.inputs[key] = combo
                form_layout.addRow(label, combo)
            else:  # It is a LineEdit
                label_text, key, is_required, initial_value = field
                label, entry = FormField.create_line_edit(label_text, is_required, False, initial_value)
                self.inputs[key] = entry
                form_layout.addRow(label, entry)

        # Location (area and cubicle)
        label_area, self.combo_area = FormField.create_combo_box("Area:", [""] + list(self.areas.keys()), True)
        form_layout.addRow(label_area, self.combo_area)

        label_cubicle, self.combo_cubicle = FormField.create_combo_box("Cubicle:", [], True)
        form_layout.addRow(label_cubicle, self.combo_cubicle)

        # Right panel - Lab selector with improved width
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: transparent;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Improve the style and responsiveness of the labs selector
        labs_title = QLabel("Lab Selection")
        labs_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: bold;
            padding: 5px 0;
        """)
        right_layout.addWidget(labs_title)

        self.labs_selector = LabsSelector(dialog, self.base_path)
        # Make sure the labs selector has a height proportional to the screen
        screen_height = QDesktopWidget().availableGeometry().height()
        self.labs_selector.setMinimumHeight(int(screen_height * 0.25))  # Reduce the height to leave room for imaging_selector
        right_layout.addWidget(self.labs_selector)

        # Add the imaging selector below the labs selector
        imaging_title = QLabel("Imaging Selection")
        imaging_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: bold;
            padding: 5px 0;
            margin-top: 10px;
        """)
        right_layout.addWidget(imaging_title)

        self.imaging_selector = ImagingSelector(dialog, self.base_path)
        # Make sure the imaging selector has a height proportional to the screen
        self.imaging_selector.setMinimumHeight(int(screen_height * 0.25))
        right_layout.addWidget(self.imaging_selector)

        # Distribute the space evenly
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)

        # Add main content to dialog layout
        dialog.layout.addWidget(main_content)

        # Connect the events
        self.inputs["triage"].currentIndexChanged.connect(self.update_admission_consult)
        self.inputs["triage"].currentIndexChanged.connect(self.mark_admission_consult_not_completed)
        self.inputs["admission_consult"].currentIndexChanged.connect(self.check_admission_consult)
        self.combo_area.currentTextChanged.connect(self.update_cubicles)

        # Action buttons
        def save():
            self.save_patient(dialog)

        buttons = [
            ("Save", save, "primary"),
            ("Cancel", dialog.reject, "danger")
        ]

        dialog.add_button_row(buttons)

        # Make sure the dialog buttons have a consistent size
        for i in range(dialog.button_layout.count()):
            widget = dialog.button_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setFixedHeight(40)
                widget.setMinimumWidth(120)

        # Execute the dialog
        dialog.exec_()

    def update_cubicles(self):
        area = self.combo_area.currentText()
        self.combo_cubicle.clear()
        if area in self.areas:
            start, end = self.areas[area]
            self.combo_cubicle.addItems([str(i) for i in range(start, end + 1)])

    def validate_minimum_data(self, data):
        # For NN patients the document is not mandatory
        if data['name'].startswith('NN -'):
            return (data['name'] and self.combo_area.currentText() and self.combo_cubicle.currentText())
        else:
            return (data['name'] and data['document_id'] and
                    self.combo_area.currentText() and self.combo_cubicle.currentText())

    def save_patient(self, dialog):
        try:
            # Collect the form data
            data = {k: v.text() if isinstance(v, QLineEdit) else v.currentText()
                    for k, v in self.inputs.items()}

            # If the name is empty or has a single word, ask about NN
            name = data['name'].strip()
            # If triage is empty, set it to "Not completed"
            if not data['triage']:
                data['triage'] = "Not completed"
                if hasattr(self, 'inputs') and 'triage' in self.inputs:
                    self.inputs['triage'].setCurrentText("Not completed")

            # Validate and process the name using the model
            processed_name, is_anonymous, message = self.model.process_name(name)

            # If it is anonymous (empty or a single word), confirm the registration as NN
            if is_anonymous:
                if self.show_confirmation_message(
                    "Incomplete name" if name else "Empty name",
                    message
                ):
                    data['name'] = self.model.create_unidentified_name()
                else:
                    # If the user does not want to register as NN, do not continue
                    return
            else:
                # If it is not anonymous, apply the processed name
                data['name'] = processed_name

            # Validate the name with the model (three-word rule)
            name_error = self.model.validate_name(data['name'])
            if name_error and not data['name'].startswith('NN -'):  # Allow NN
                self.show_information_message("Error", name_error, QMessageBox.Critical)
                return

            # If it is NN, the document is not mandatory
            if data['name'].startswith('NN -') and not data['document_id']:
                # Generate a unique temporary "document" for NN
                data['document_id'] = f"NN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            location = f"{self.combo_area.currentText()} - {self.combo_cubicle.currentText()}"

            # Validate the minimum data
            if not self.validate_minimum_data(data):
                self.show_information_message("Error", "You must fill in the required fields", QMessageBox.Critical)
                return

            # Validate the patient status using the model method
            status_validation = self.model.validate_patient_status(data)
            if status_validation:
                self.show_information_message("Validation Error", status_validation, QMessageBox.Critical)
                return

            # Validate the consistency between the selected labs and the Labs status
            labs = [lab[0] for lab in self.labs_selector.get_selected_labs()]
            if (labs and (not data['labs'] or data['labs'] not in ["Not started", "Awaiting results", "Results complete"])):
                self.show_information_message("Validation Error",
                    "You must set a valid Labs status when you select labs", QMessageBox.Critical)
                return
            if (not labs and data['labs'] in ["Not started", "Awaiting results", "Results complete"]):
                self.show_information_message("Validation Error",
                    "You selected a Labs status but you have not added any lab", QMessageBox.Critical)
                return

            # Validate the consistency between the selected imaging and the Imaging status
            imaging = [img[0] for img in self.imaging_selector.get_selected_imaging()]
            if (imaging and (not data['imaging'] or data['imaging'] not in ["Not started", "Awaiting results", "Results complete"])):
                self.show_information_message("Validation Error",
                    "You must set a valid Imaging status when you select imaging studies", QMessageBox.Critical)
                return
            if (not imaging and data['imaging'] in ["Not started", "Awaiting results", "Results complete"]):
                self.show_information_message("Validation Error",
                    "You selected an Imaging status but you have not added any imaging study", QMessageBox.Critical)
                return

            # Check whether a patient with the same document already exists
            if data['document_id']:  # Only check if there is a document (it could be an NN without one)
                existing_patient_doc = self.model.check_patient_same_document(data['document_id'])

                if existing_patient_doc:
                    # Compare the normalized names using the model method
                    if not self.model.compare_names(existing_patient_doc[0], data['name']):
                        self.show_information_message(
                            "Error",
                            "A patient with a different name is already associated with this document",
                            QMessageBox.Critical
                        )
                        return
                    else:
                        if self.show_confirmation_message(
                            "Existing patient",
                            "Do you want to add another record for this patient?\nIf you select NO, you will be taken to the edit patient window"
                        ):
                            pass  # Continue with the save
                        else:
                            document = data['document_id']
                            dialog.close()
                            self.start_edit_from_button(document=document)
                            return

                # Check for patients with the same name and a different document
                all_patients = self.model.check_patient_same_name_different_document()

                # Completing the missing code that checks patients with the same name and a different document
                for doc, db_name in all_patients:
                    if self.model.compare_names(db_name, data['name']) and doc != data['document_id']:
                        if not self.show_confirmation_message(
                            "Warning",
                            f"A patient with a similar name but a different document already exists:\n"
                            f"Name: {db_name}\nDocument ID: {doc}\n\n"
                            f"Do you want to continue with the current registration?"
                        ):
                            return

            # Save into the database
            success, message, patient_id = self.model.save_patient_data(data=data, location=location)

            if success:
                # Save the selected labs
                if labs:
                    # The model will already validate triage and admission consult
                    labs_success, labs_message = self.model.save_patient_labs(patient_id, labs)
                    if not labs_success:
                        self.show_warning_message("Warning", labs_message)

                # Save the selected imaging studies
                if imaging:
                    # The model will already validate triage and admission consult
                    imaging_success, imaging_message = self.model.save_patient_imaging(patient_id, imaging)
                    if not imaging_success:
                        self.show_warning_message("Warning", imaging_message)

                dialog.close()
                self.update_table()
                self.show_information_message("Success", f"Patient {data['name']} has been saved successfully.")

            else:
                self.show_information_message("Error", message, QMessageBox.Critical)
        except Exception as e:
            self.show_information_message("Error", f"Error while saving: {str(e)}", QMessageBox.Critical)
        finally:
            self.model.close_db()

    def start_edit_from_button(self, document=None):
        if not document:
            document = self.request_document("Edit patient")
        if not document:
            return

        records = self.model.get_record_by_document(document=document)

        if not records:
            self.show_information_message("Error", "No patient was found with the entered document", QMessageBox.Critical)
            return

        if len(records) > 1:
            selected_record = self.select_record(records, "editing")
            if selected_record:
                self.show_edit_form(selected_record)
        else:
            self.show_edit_form(records[0])

    def start_edit_from_context_menu(self, row):
        if row >= 0:
            document = self.table.item(row, 1).text()

            records = self.model.get_record_by_document(document=document)

            if not records:
                self.show_information_message("Error", "No patient was found with the entered document", QMessageBox.Critical)
                return

            if len(records) > 1:
                selected_record = self.select_record(records, "editing")
                if selected_record:
                    self.show_edit_form(selected_record)
            else:
                self.show_edit_form(records[0])

    def show_edit_form(self, record):
        dialog = StyledDialog("Edit patient", 1000, self)  # Increased width from 700 to 1000

        # Center the dialog properly on screen
        screen = QDesktopWidget().availableGeometry()
        dialog_width = 1000
        dialog_height = int(screen.height() * 0.85)  # Use 85% of screen height

        # Calculate centered position
        dialog_x = (screen.width() - dialog_width) // 2
        dialog_y = (screen.height() - dialog_height) // 2

        dialog.setGeometry(dialog_x, dialog_y, dialog_width, dialog_height)

        # Add the title with the patient name
        dialog.add_title(f"Edit patient: {record[0]}")

        # Add the required fields indicator
        dialog.add_required_fields_indicator()

        # Create horizontal layout for main content (like in show_add_form)
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

        # Field definitions
        fields = [
            ("Name:", "name", 0, False, False, ""),
            ("Document ID:", "document_id", 1, False, True, ""),
            ("Triage:", "triage", 2, False, False, "", ["", "Not completed", "1", "2", "3", "4", "5"]),
            ("Admission Consult:", "admission_consult", 4, False, False, "", ["", "Not completed", "Completed"]),
            ("Labs:", "labs", 5, False, False, "", ["", "Not started", "Awaiting results", "Results complete"]),
            ("Imaging:", "imaging", 6, False, False, "", ["", "Not started", "Awaiting results", "Results complete"]),
            ("Specialist Consult:", "specialist_consult", 7, False, False, "", ["", "Not opened", "Open", "Completed"]),
            ("Reassessment:", "reassessment", 8, False, False, "", ["", "Completed", "Not completed"]),
            ("Pending Tasks:", "pending_tasks", 9, False, False, ""),
            ("Disposition:", "disposition", 10, False, False, "", ["", "Hospitalized", "Observation", "Discharged"])
        ]

        self.inputs = {}

        for field in fields:
            if len(field) > 6:  # It is a combobox
                label_text, key, index, is_required, readonly, _, options = field
                current_value = record[index] if record[index] else ""
                label, combo = FormField.create_combo_box(label_text, options, is_required, current_value)
                self.inputs[key] = combo
                form_layout.addRow(label, combo)
            else:  # It is a LineEdit
                label_text, key, index, is_required, readonly, _ = field
                current_value = record[index] if record[index] else ""
                label, entry = FormField.create_line_edit(label_text, is_required, readonly, current_value)
                self.inputs[key] = entry
                form_layout.addRow(label, entry)

        # Location (area and cubicle)
        label_area, self.combo_area = FormField.create_combo_box("Area:", list(self.areas.keys()), True)
        form_layout.addRow(label_area, self.combo_area)

        label_cubicle, self.combo_cubicle = FormField.create_combo_box("Cubicle:", [], True)
        form_layout.addRow(label_cubicle, self.combo_cubicle)

        # Right panel - Lab selector with improved width (like in show_add_form)
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: transparent;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Improve the style and responsiveness of the labs selector
        labs_title = QLabel("Lab Selection")
        labs_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: bold;
            padding: 5px 0;
        """)
        right_layout.addWidget(labs_title)

        self.labs_selector = LabsSelector(dialog, self.base_path)
        # Make sure the labs selector has a height proportional to the screen
        screen_height = QDesktopWidget().availableGeometry().height()
        self.labs_selector.setMinimumHeight(int(screen_height * 0.25))  # Reduce the height to leave room for imaging_selector
        right_layout.addWidget(self.labs_selector)

        # Load the patient labs
        patient_id = record[13]  # ID at position 13
        patient_labs = self.model.get_patient_labs(patient_id)
        if patient_labs:
            formatted_labs = [(lab[0], lab[1]) for lab in patient_labs]
            self.labs_selector.set_selected_labs(formatted_labs)

        # Add the imaging selector below the labs selector
        imaging_title = QLabel("Imaging Selection")
        imaging_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: bold;
            padding: 5px 0;
            margin-top: 10px;
        """)
        right_layout.addWidget(imaging_title)

        self.imaging_selector = ImagingSelector(dialog, self.base_path)
        # Make sure the imaging selector has a height proportional to the screen
        self.imaging_selector.setMinimumHeight(int(screen_height * 0.25))
        right_layout.addWidget(self.imaging_selector)

        # Load the patient imaging studies
        patient_imaging = self.model.get_patient_imaging(patient_id)
        if patient_imaging:
            formatted_imaging = [(img[0], img[1]) for img in patient_imaging]
            self.imaging_selector.set_selected_imaging(formatted_imaging)

        # Distribute the space evenly
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)

        # Add main content to dialog layout
        dialog.layout.addWidget(main_content)

        # Connect the events
        self.inputs["triage"].currentIndexChanged.connect(self.update_admission_consult)
        self.inputs["triage"].currentIndexChanged.connect(self.mark_admission_consult_not_completed)
        self.inputs["admission_consult"].currentIndexChanged.connect(self.check_admission_consult)
        self.combo_area.currentTextChanged.connect(self.update_cubicles)

        # Split the current location into area and cubicle
        current_location = record[11]  # Index 11: location
        if " - " in current_location:
            current_area, current_cubicle = current_location.split(" - ")
            self.combo_area.setCurrentText(current_area)
            self.update_cubicles()
            self.combo_cubicle.setCurrentText(current_cubicle)

        # Action buttons
        def update():
            self.update_patient(dialog, record)

        buttons = [
            ("Update", update, "primary"),
            ("Cancel", dialog.reject, "danger")
        ]

        dialog.add_button_row(buttons)

        # Make sure the dialog buttons have a consistent size
        for i in range(dialog.button_layout.count()):
            widget = dialog.button_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setFixedHeight(40)
                widget.setMinimumWidth(120)

        # Execute the dialog
        dialog.exec_()

    def mark_admission_consult_not_completed(self):
        if self.inputs["triage"].currentText() in ["1", "2", "3", "4", "5"]:
            self.inputs["admission_consult"].setCurrentText("Not completed")

    def check_admission_consult(self):
        if self.inputs["admission_consult"].currentText() == "Not completed":
            self.inputs["labs"].setEnabled(False)
            self.inputs["imaging"].setEnabled(False)
            self.inputs["specialist_consult"].setEnabled(False)
            self.inputs["reassessment"].setEnabled(False)
        else:
            self.inputs["labs"].setEnabled(True)
            self.inputs["imaging"].setEnabled(True)
            self.inputs["specialist_consult"].setEnabled(True)
            self.inputs["reassessment"].setEnabled(True)

        # Add an event for when the Labs status changes
        self.inputs["labs"].currentTextChanged.connect(self.update_labs_selector_visibility)
        # Add an event for when the Imaging status changes
        self.inputs["imaging"].currentTextChanged.connect(self.update_imaging_selector_visibility)

    def update_labs_selector_visibility(self, labs_status):
        """Updates the visibility of the labs selector according to the Labs status"""
        # If the labs selector exists and is available
        if hasattr(self, 'labs_selector'):
            # If the Labs status is "Results complete", disable the selector
            # but keep it visible so the user can see the existing labs
            self.labs_selector.setEnabled(labs_status != "Results complete")

            # Show an informational message
            if labs_status == "Results complete":
                # If the selector has its own method to show messages
                if hasattr(self.labs_selector, 'show_error'):
                    self.labs_selector.show_error(
                        "The labs will not be shown as pending because the status is 'Results complete'"
                    )

    def update_imaging_selector_visibility(self, imaging_status):
        """Updates the visibility of the imaging selector according to the Imaging status"""
        # If the imaging selector exists and is available
        if hasattr(self, 'imaging_selector'):
            # If the Imaging status is "Results complete", disable the selector
            # but keep it visible so the user can see the existing imaging studies
            self.imaging_selector.setEnabled(imaging_status != "Results complete")

            # Show an informational message
            if imaging_status == "Results complete":
                # If the selector has its own method to show messages
                if hasattr(self.imaging_selector, 'show_error'):
                    self.imaging_selector.show_error(
                        "The imaging studies will not be shown as pending because the status is 'Results complete'"
                    )

    def update_patient(self, dialog, original_record):
        try:
            data = {k: v.text() if isinstance(v, QLineEdit) else v.currentText()
                    for k, v in self.inputs.items()}

            # If triage is empty, set it to "Not completed"
            if not data['triage']:
                data['triage'] = "Not completed"
                if hasattr(self, 'inputs') and 'triage' in self.inputs:
                    self.inputs['triage'].setCurrentText("Not completed")

            # Validate and process the name using the model
            name = data['name'].strip()

            # Name processing for anonymous patients
            processed_name, is_anonymous, message = self.model.process_name(name)

            # If it is anonymous, ask whether to register as NN
            if is_anonymous:
                if self.show_confirmation_message(
                    "Incomplete name" if name else "Empty name",
                    message
                ):
                    data['name'] = f"NN - {self.model.create_unidentified_name()}"
                else:
                    # If the user does not want to register as NN, do not continue
                    return
            else:
                # If it is not anonymous, apply the processed name
                data['name'] = processed_name

            # Validate the name with the model (three-word rule)
            name_error = self.model.validate_name(data['name'])
            if name_error and not data['name'].startswith('NN -'):
                self.show_information_message("Error", name_error, QMessageBox.Critical)
                return

            # If it is NN, the document is not mandatory
            if data['name'].startswith('NN -') and not data['document_id']:
                # Generate a unique temporary "document" for NN
                data['document_id'] = f"NN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            location = f"{self.combo_area.currentText()} - {self.combo_cubicle.currentText()}"

            # Validate the patient status using the model method
            status_validation = self.model.validate_patient_status(data)
            if status_validation:
                self.show_information_message("Validation error", status_validation, QMessageBox.Critical)
                return

            # ADDED: Extra validation to make sure statuses are not updated without prerequisites
            if (data['triage'] not in ["1", "2", "3", "4", "5"] or data['admission_consult'] != "Completed") and (
                data['labs'] in ["Not started", "Awaiting results", "Results complete"] or
                data['imaging'] in ["Not started", "Awaiting results", "Results complete"] or
                data['specialist_consult'] in ["Not opened", "Open", "Completed"] or
                data['reassessment'] in ["Completed"]
            ):
                self.show_information_message(
                    "Validation error",
                    "Labs, Imaging, Specialist Consult or Reassessment cannot be updated until Triage and Admission Consult are completed.",
                    QMessageBox.Critical
                )
                return

            # Get the selected labs for validation
            new_labs = [lab[0] for lab in self.labs_selector.get_selected_labs()]

            # Validate the consistency between the selected labs and the Labs status
            if (new_labs and (not data['labs'] or data['labs'] not in ["Not started", "Awaiting results", "Results complete"])):
                self.show_information_message("Validation Error",
                    "You must set a valid Labs status when you select labs", QMessageBox.Critical)
                return
            if (not new_labs and data['labs'] in ["Not started", "Awaiting results", "Results complete"]):
                self.show_information_message("Validation Error",
                    "You selected a Labs status but you have not added any lab", QMessageBox.Critical)
                return

            # Get the selected imaging studies for validation
            new_imaging = [img[0] for img in self.imaging_selector.get_selected_imaging()]

            # Validate the consistency between the selected imaging and the Imaging status
            if (new_imaging and (not data['imaging'] or data['imaging'] not in ["Not started", "Awaiting results", "Results complete"])):
                self.show_information_message("Validation Error",
                    "You must set a valid Imaging status when you select imaging studies", QMessageBox.Critical)
                return
            if (not new_imaging and data['imaging'] in ["Not started", "Awaiting results", "Results complete"]):
                self.show_information_message("Validation Error",
                    "You selected an Imaging status but you have not added any imaging study", QMessageBox.Critical)
                return

            # Confirmation before updating
            patient_name = data['name']
            if not self.show_confirmation_message(
                "Confirm Update",
                f"Are you sure you want to update the data of patient {patient_name}?"
            ):
                return

            # Update in the database
            success, message = self.model.update_patient_data(data=data, location=location, record=original_record)

            if success:
                patient_id = original_record[13]  # ID at position 13

                # Get the original labs
                current_labs = self.model.get_patient_labs(patient_id)
                current_lab_codes = [lab[0] for lab in current_labs] if current_labs else []

                # Check whether the labs have changed
                labs_changed = set(new_labs) != set(current_lab_codes)

                # Only save the labs if they changed or if triage and admission consult are completed
                if labs_changed:
                    if data['triage'] in ["1", "2", "3", "4", "5"] and data['admission_consult'] == "Completed":
                        labs_success, labs_message = self.model.save_patient_labs(patient_id, new_labs)
                        if not labs_success:
                            self.show_information_message("Labs error", labs_message, QMessageBox.Critical)
                    else:
                        # If triage or admission consult are not completed and there are new labs, show a message
                        if new_labs:
                            self.show_warning_message(
                                "Information",
                                "The labs cannot be saved until triage and admission consult are completed"
                            )

                # Get the original imaging studies
                current_imaging = self.model.get_patient_imaging(patient_id)
                current_imaging_codes = [img[0] for img in current_imaging] if current_imaging else []

                # Check whether the imaging studies have changed
                imaging_changed = set(new_imaging) != set(current_imaging_codes)

                # Only save the imaging studies if they changed or if triage and admission consult are completed
                if imaging_changed:
                    if data['triage'] in ["1", "2", "3", "4", "5"] and data['admission_consult'] == "Completed":
                        imaging_success, imaging_message = self.model.save_patient_imaging(patient_id, new_imaging)
                        if not imaging_success:
                            self.show_information_message("Imaging error", imaging_message, QMessageBox.Critical)
                    else:
                        # If triage or admission consult are not completed and there are new imaging studies, show a message
                        if new_imaging:
                            self.show_warning_message(
                                "Information",
                                "The imaging studies cannot be saved until triage and admission consult are completed"
                            )

                # Update every pending task according to the different statuses
                self.model.update_pending_tasks_for_triage(patient_id, data['triage'])
                self.model.update_pending_tasks_for_admission_consult(patient_id, data['admission_consult'])
                self.model.update_pending_tasks_for_labs(patient_id, data['labs'])
                self.model.update_pending_tasks_for_imaging(patient_id, data['imaging'])
                self.model.update_pending_tasks_for_specialist_consult(patient_id, data['specialist_consult'])
                self.model.update_pending_tasks_for_reassessment(patient_id, data['reassessment'])

                dialog.close()
                self.update_table()
                self.show_information_message("Success", "Patient updated successfully")
            else:
                self.show_information_message("Error", message, QMessageBox.Critical)
        except Exception as e:
            self.show_information_message("Error", f"Error while updating: {str(e)}", QMessageBox.Critical)
        finally:
            self.model.close_db()

    def show_confirmation_message(self, title, message, icon=QMessageBox.Question):
        """Shows a styled confirmation message"""
        msg_box = StyledMessageBox(self, title, message, icon, "confirmation")

        # Create styled buttons
        btn_yes = QPushButton("Yes")
        btn_no = QPushButton("No")

        # Style the buttons if needed
        btn_yes.setCursor(Qt.PointingHandCursor)
        btn_no.setCursor(Qt.PointingHandCursor)

        msg_box.addButton(btn_yes, QMessageBox.YesRole)
        msg_box.addButton(btn_no, QMessageBox.NoRole)

        # Set the default button
        msg_box.setDefaultButton(btn_no)

        # Execute the dialog box
        result = msg_box.exec_()

        # Return True if "Yes" was pressed, False otherwise
        return msg_box.clickedButton() == btn_yes

    def show_information_message(self, title, message, icon=QMessageBox.Information):
        """Shows a styled informational message"""
        # Determine the style type according to the icon
        style_type = "error" if icon == QMessageBox.Critical else "info"

        msg_box = StyledMessageBox(self, title, message, icon, style_type)

        # Create a styled OK button
        btn_ok = QPushButton("Accept")
        btn_ok.setCursor(Qt.PointingHandCursor)

        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)

        # Set the default button
        msg_box.setDefaultButton(btn_ok)

        # Execute the dialog box
        return msg_box.exec_()

    def show_warning_message(self, title, message):
        """Shows a styled warning message"""
        msg_box = StyledMessageBox(self, title, message, QMessageBox.Warning, "warning")

        # Create a styled OK button
        btn_ok = QPushButton("Accept")
        btn_ok.setCursor(Qt.PointingHandCursor)

        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)

        # Set the default button
        msg_box.setDefaultButton(btn_ok)

        # Execute the dialog box
        return msg_box.exec_()

    def show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row >= 0:
            menu = QMenu(self)
            menu.setStyleSheet(MENU_STYLES["main"])

            edit_action = menu.addAction("Edit")
            delete_action = menu.addAction("Delete")

            # Get the global position for the menu
            global_position = self.table.mapToGlobal(position)
            # Execute the menu and get the selected action
            action = menu.exec_(global_position)

            if action == edit_action:
                self.start_edit_from_context_menu(row)
            elif action == delete_action:
                document = self.table.item(row, 1).text()

                records = self.model.get_record_by_document(document=document)
                if len(records) > 1:
                    selected_record = self.select_record(records, "deletion")
                    if selected_record:
                        patient_name = selected_record[0]  # The name is at index 0

                        if self.show_confirmation_message(
                            "Confirm Deletion",
                            f"Are you sure you want to delete patient {patient_name}?"
                        ):
                            self.delete_record(selected_record)
                else:
                    patient_name = records[0][0]  # The name is at index 0
                    if self.show_confirmation_message(
                        "Confirm Deletion",
                        f"Are you sure you want to delete patient {patient_name}?"
                    ):
                        self.delete_record(records[0])

    def adjust_color(self, color, brighter=False):
        """Adjusts the color for the hover effect"""
        if color.startswith('#'):
            # Convert the hex color to RGB
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)

            if brighter:
                # Lighten for the hover effect (for darker buttons)
                factor = 1.1
                r = min(255, int(r*factor))
                g = min(255, int(g*factor))
                b = min(255, int(b*factor))
            else:
                # Darken for the hover effect (for lighter buttons)
                factor = 0.9
                r = int(r*factor)
                g = int(g*factor)
                b = int(b*factor)

            return f'#{r:02x}{g:02x}{b:02x}'
        return color

    def toggle_maximized(self):
        """Toggles the window between maximized and normal mode."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def show_edit_selector(self):
        """Shows a window to select a patient to edit"""
        document = self.request_document("Edit patient")
        if not document:
            return

        self.start_edit_from_button(document=document)

    def configure_side_menu(self):
        """Configures the side menu options"""
        # Get the icon paths
        images_path = os.path.join(self.base_path, "frontend", "images")
        add_icon_path = os.path.join(images_path, "add_icon.png")
        edit_icon_path = os.path.join(images_path, "edit_icon.png")
        delete_icon_path = os.path.join(images_path, "delete_icon.png")
        logout_icon_path = os.path.join(images_path, "logout_icon.png")
        filter_icon_path = os.path.join(images_path, "filter.png")

        # Add the buttons to the side menu with their respective icons
        self.side_menu.add_menu_button("Add patient",
                                         add_icon_path if os.path.exists(add_icon_path) else None,
                                         self.show_add_form)

        self.side_menu.add_menu_button("Edit patient",
                                         edit_icon_path if os.path.exists(edit_icon_path) else None,
                                         self.show_edit_selector)

        self.side_menu.add_menu_button("Delete patient",
                                         delete_icon_path if os.path.exists(delete_icon_path) else None,
                                         self.confirm_deletion)

        # Add the filter button
        self.side_menu.add_menu_button("Filter",
                                        filter_icon_path if os.path.exists(filter_icon_path) else None,
                                        self.show_filter_dialog)

        # Add space between the buttons and the log out button
        self.side_menu.add_spacer()

        # Log out button at the end
        self.side_menu.add_menu_button("Log out",
                                         logout_icon_path if os.path.exists(logout_icon_path) else None,
                                         self.logout,
                                         "danger")

        # Make sure the menu is above the other widgets
        self.side_menu.raise_()

        # Hidden initially
        self.side_menu.hide()

    def resizeEvent(self, event):
        """Handles the window resize event"""
        # Call the base class method
        super().resizeEvent(event)

        # Update the side menu so that it is responsive
        if hasattr(self, 'side_menu'):
            self.side_menu.adjust_for_screen_size()

        # Update the side menu location
        if hasattr(self, 'side_menu') and self.side_menu.is_open:
            self.side_menu.setGeometry(
                self.width() - self.side_menu.width,
                0,
                self.side_menu.width,
                self.height()
            )
        elif hasattr(self, 'side_menu'):
            self.side_menu.setGeometry(
                self.width(),
                0,
                self.side_menu.width,
                self.height()
            )

    def show_filter_dialog(self):
        """Shows the dialog used to filter by areas and date range"""
        dialog = FilterDialog(self, self.areas, self.filtered_areas,
                                self.date_filter_active, self.start_date, self.end_date)
        if dialog.exec_() == QDialog.Accepted:
            # Get the areas selected in the dialog
            new_filters = dialog.get_selected_areas()

            # If no area is selected, use all of them by default
            if not new_filters:
                new_filters = list(self.areas.keys())

            # Update the local filters
            self.filtered_areas = new_filters

            # Update the date filters
            self.date_filter_active = dialog.date_filter_active
            if self.date_filter_active:
                self.start_date = dialog.start_date
                self.end_date = dialog.end_date
            else:
                self.start_date = None
                self.end_date = None

            # Save the area preferences
            from backend.users.preferences_model import PreferencesModel

            # Try to save the preferences
            success = PreferencesModel.save_filter_preferences(
                self.current_user,
                self.filtered_areas
            )

            if not success:
                self.show_information_message(
                    "Preferences not persisted",
                    "The filter preferences could not be saved permanently. "
                    "The preferences will be kept for this session only.",
                    QMessageBox.Warning
                )

            # Update the table with the new filters
            self.update_table()
