from PyQt5.QtWidgets import (QMainWindow, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout,
                           QTableWidget, QTableWidgetItem, QPushButton,
                           QLabel, QMessageBox, QFrame, QDesktopWidget,
                           QApplication, QGraphicsOpacityEffect, QCheckBox,
                           QGroupBox, QComboBox, QDialog, QSizePolicy, QGridLayout)
from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QEvent
from PyQt5.QtGui import QFont, QPixmap, QIcon, QLinearGradient, QBrush, QPalette, QColor, QPainter
from backend.users.waiting_room_model import WaitingRoomModel
import sys
import os
# Import the animation components from their correct location
from frontend.styles.animation_components import SplashScreen
# Import styles and components
from frontend.styles.styles import *
from frontend.styles.components import StyledMessageBox, StyledButton, StyledDialog
# Import table components - updated to use the same styles as the main view
from frontend.styles.table_components import StatusCircleDelegate, TextDelegate, CustomColumnHeader, configure_standard_table
# Import header components
from frontend.styles.header_components import CombinedHeader
# Import custom widgets
from frontend.styles.custom_widgets import TableContainer
# Import font utilities
from frontend.styles.font_utils import apply_system_fonts
# Import the new side menu
from frontend.styles.lateral_menu import LateralMenu, MenuToggleButton


class WaitingRoomView(QMainWindow):
    def __init__(self, login_interface):
        super().__init__()
        self.login_interface = login_interface
        self.model = WaitingRoomModel()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.current_page = 0

        # New variables for the presentation mode
        self.presentation_mode_active = False  # It will be enabled later
        self.presentation_timer = QTimer(self)
        self.presentation_timer.timeout.connect(self.show_next_page)

        # Area definitions (the same ones as in the patient view) - placed first so filtered_areas can be initialized
        self.areas = {
            "Old wing": (1, 18),
            "Yellow": (19, 38),
            "Pediatrics": (39, 59),
            "Hallways": (60, 200),
            "Clinic": (1, 40),
            "Waiting room": (1, 2),
        }

        # Import the preferences model
        from backend.users.preferences_model import PreferencesModel
        from backend.database import AuthenticationModel

        # Get the current user
        credentials = AuthenticationModel.get_credentials()
        self.current_user = credentials.get('user')

        # Load the filter preferences
        self.filtered_areas = PreferencesModel.get_area_filters(
            self.current_user, list(self.areas.keys())
        )

        # Load the pagination interval from the preferences
        self.presentation_interval = PreferencesModel.get_pagination_interval(
            self.current_user, 10  # Default value: 10 seconds
        )

        # Make sure there is always at least one selected area to avoid an empty view
        if not self.filtered_areas:
            self.filtered_areas = list(self.areas.keys())
            print(f"No filters were found, using every area")

        # Apply custom fonts immediately
        apply_system_fonts()

        # Get the screen size for the responsive elements
        self.screen = QDesktopWidget().screenGeometry()

        # Initialize a flag to track the first load of the table
        self.first_load = True

        # Show the loading screen while the interface is being initialized
        self.splash = SplashScreen(None, logo_path=None, message="Loading waiting room...", duration=1.5)
        self.splash.setFixedSize(int(self.screen.width() * 0.3), int(self.screen.height() * 0.3))
        self.splash.show()
        self.splash.opacity_animation.start()
        QApplication.processEvents()

        # Opacity effect for the entry animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)  # Start invisible

        # Get the resource paths
        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        images_path = os.path.join(self.base_path, "frontend", "images")
        self.logo_path = os.path.join(images_path, "logo.png")
        self.icon_path = os.path.join(images_path, "logo.png")
        self.secondary_logo_path = os.path.join(images_path, "secondary_logo.png")

        # Set the window icon
        if os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))

        # Variables used to move the window without a title bar
        self.dragging = False
        self.offset = None

        # Table headers - without "Disposition" and "Admission"
        self.headers = ["Name", "Document ID", "Triage", "Admission Consult", "Labs", "Imaging", "Specialist Consult", "Reassessment", "Pending Tasks", "Location"]

        # Create the side menu BEFORE configuring the window and building the interface
        self.side_menu = LateralMenu(self)

        # Configure the window and build the interface
        self.configure_window()
        self.create_interface()

        # Configure the side menu after building the interface
        self.configure_side_menu()

        # Close the loading screen before showing the main interface
        self.splash.accept()

        # Initialize the timer for the automatic refresh
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_table)
        self.timer.start(5000)

        # Entry animation
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()

        # Add the active filters indicator - move it before refreshing the table
        self.create_filter_indicator()

        # Refresh the table for the first time once the interface is complete
        # This guarantees the persistent filters are used from the start
        self.update_table()

        # Initialize and enable the presentation mode automatically after loading the data
        QTimer.singleShot(500, self.activate_presentation_mode)

    def mask_name(self, name):
        """Masks the name by showing the first 3 letters of each word"""
        if not name:
            return name

        # For unidentified (NN) patients, protect them with a different format
        if name.startswith('NN -'):
            # Show only "NN" and hide the timestamp
            parts = name.split(' - ', 1)
            if len(parts) > 1:
                return "NN - ***********"
            return name

        parts = name.split()
        if len(parts) <= 1:
            return name

        # Show the first 3 letters of each word
        result = []
        for part in parts:
            if len(part) <= 3:
                result.append(part)  # Do not mask very short words
            else:
                # Show the first 3 letters and mask the rest
                visible_characters = 3
                result.append(part[:visible_characters] + "*" * (len(part) - visible_characters))

        return " ".join(result)

    def mask_document(self, doc):
        """Masks the document by showing the last 4 digits"""
        if not doc:
            return doc

        # Use a special format for unidentified (NN) patient documents
        if doc.startswith('NN-'):
            return "NN-****"

        if len(doc) <= 4:
            return doc  # Do not mask very short documents

        # Show only the last 4 digits
        masked_part = "*" * (len(doc) - 4)
        visible_part = doc[-4:]
        return masked_part + visible_part

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
        # Stop dragging
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def configure_window(self):
        self.setWindowTitle("Waiting Room")
        self.setStyleSheet("background-color: #4A7296;")
        self.showMaximized()

    def create_interface(self):
        # Main central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  # Remove the space between widgets

        # Create and add the combined bar with the logo
        combined_header = self.create_combined_header()
        main_layout.addWidget(combined_header)

        # Create the container for the main content
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 30, 20, 20)  # Top margin reduced from 50 to 30
        content_layout.setSpacing(8)  # Reduced from 15 to 8 for less vertical space

        # Container for the filter indicator (it will be added later)
        self.filter_container = QWidget()
        self.filter_layout = QHBoxLayout(self.filter_container)
        self.filter_layout.setContentsMargins(0, 2, 0, 2)  # Reduced from 0,5,0,5 to 0,2,0,2
        content_layout.addWidget(self.filter_container)

        # Create the table with a limited size
        table_container = self.create_table_container()
        content_layout.addWidget(table_container)

        # Add the content container to the main layout
        main_layout.addWidget(content_container)

    def create_combined_header(self):
        # Create a combined container for the title and the logo
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['background_header']};")

        # Calculate the sizes so they match the login interface
        screen_height = self.screen.height()
        screen_width = self.screen.width()
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

            # Add the logo on the left side
            header_layout.addWidget(logo_label, 0, Qt.AlignLeft | Qt.AlignVCenter)

        # Add expanding space in the middle
        header_layout.addStretch(1)

        # Container for the window control buttons and the secondary logo
        container_right = QWidget()
        layout_right = QVBoxLayout(container_right)
        layout_right.setContentsMargins(0, 0, 0, 0)
        layout_right.setSpacing(5)

        # Container for the window control buttons
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)

        # Add the menu button
        self.menu_button = MenuToggleButton(self, self.side_menu)
        buttons_layout.addWidget(self.menu_button)

        # Window control buttons (right side) - without a logout button
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
        if os.path.exists(self.secondary_logo_path):
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
        # Use the reusable TableContainer with more appropriate sizes
        table_container = TableContainer(self, 0.96, 0.705)  # Increased from 0.75, 0.55 to make the table larger

        # Create the table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.headers))
        # Two-word stage names are wrapped so they fit the column width.
        # self.headers keeps the single-line names the column lookups rely on.
        self.table.setHorizontalHeaderLabels(
            [header.replace(" Consult", "\nConsult") for header in self.headers])

        # Apply the improved table styles - using the same ones as the main view
        self.table.setStyleSheet(TABLE_STYLES_UPDATED["main"] + SCROLLBAR_STYLE)

        # Hide the row numbers
        self.table.verticalHeader().setVisible(False)

        # Configure the delegate for the colored circles
        circle_delegate = StatusCircleDelegate(self.table)
        status_columns = ['Triage', 'Admission Consult', 'Labs', 'Imaging', 'Specialist Consult', 'Reassessment']
        for header in status_columns:
            col_index = self.headers.index(header)
            self.table.setItemDelegateForColumn(col_index, circle_delegate)

        # Configure the delegate for the text cells so tooltips are shown
        text_delegate = TextDelegate(self.table)
        for col in range(self.table.columnCount()):
            if col not in [self.headers.index(h) for h in status_columns]:
                self.table.setItemDelegateForColumn(col, text_delegate)

        # Make sure the delegate is correctly configured for every column
        for col_index in [self.headers.index(header) for header in status_columns]:
            delegate = self.table.itemDelegateForColumn(col_index)
            if isinstance(delegate, StatusCircleDelegate):
                delegate.alarm_cells = set()  # Initialize it to avoid problems
                delegate.disposition_alarm_cells = set()  # Initialize this set as well

        # Enable smooth scrolling
        self.table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)

        # Style configuration for the table
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.clearSelection()
        self.table.setCurrentCell(-1, -1)

        # Use the same font as the main view for consistency
        self.table.setFont(QFont("Segoe UI", 10))

        # Improve the header style
        header_font = QFont("Segoe UI", 10)
        header_font.setBold(True)
        self.table.horizontalHeader().setFont(header_font)

        self.table.setWordWrap(True)

        # Add the table to the container
        table_container.set_table(self.table)

        return table_container

    def configure_side_menu(self):
        """Configures the side menu options"""
        # Get the icon paths
        images_path = os.path.join(self.base_path, "frontend", "images")
        filter_icon_path = os.path.join(images_path, "filter.png")
        logout_icon_path = os.path.join(images_path, "logout_icon.png")
        pagination_icon_path = os.path.join(images_path, "pagination.png")

        # Add the filter button
        self.side_menu.add_menu_button("Filter",
                                         filter_icon_path if os.path.exists(filter_icon_path) else None,
                                         self.show_filter_dialog)

        # Change the presentation mode button so it only shows the settings
        self.side_menu.add_menu_button("Set interval",
                                         pagination_icon_path if os.path.exists(pagination_icon_path) else None,
                                         self.show_presentation_settings)

        # Add space between the buttons and the log out button
        self.side_menu.add_spacer()

        # Log out button at the end
        self.side_menu.add_menu_button("Log Out",
                                         logout_icon_path if os.path.exists(logout_icon_path) else None,
                                         self.logout,
                                         "danger")

        # Make sure the menu is above the other widgets
        self.side_menu.raise_()

        # Hidden initially
        self.side_menu.hide()

    def show_presentation_settings(self):
        """Shows a dialog to configure the presentation mode"""
        dialog = StyledDialog("Set pagination interval", 500, self)
        dialog.add_title("Pagination Settings")

        description = QLabel("Set the time interval between each automatic page change:")
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: {COLORS['background_transparent']};")
        dialog.layout.addWidget(description)

        # Create the widget used to select the interval
        selector_widget = QWidget()
        selector_layout = QHBoxLayout(selector_widget)

        # Label
        label = QLabel("Interval (seconds):")
        label.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: {COLORS['background_transparent']}; font-weight: bold;")
        label.setAttribute(Qt.WA_TranslucentBackground, True)
        selector_widget.setStyleSheet("background-color: transparent;")
        selector_widget.setAttribute(Qt.WA_TranslucentBackground, True)

        # Combo box used to select the interval
        interval_combo = QComboBox()
        interval_combo.addItems(['3', '5', '7', '10', '15', '20', '30'])
        interval_combo.setCurrentText(str(self.presentation_interval))
        interval_combo.setStyleSheet(COMBO_BOX_STYLES["normal"])

        selector_layout.addWidget(label)
        selector_layout.addWidget(interval_combo)

        dialog.layout.addWidget(selector_widget)
        dialog.layout.addSpacing(20)

        # Add an informational label
        info = QLabel("This value sets how often the record pages are refreshed automatically.")
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {COLORS['text_light']}; background-color: {COLORS['background_transparent']}; font-style: italic;")
        dialog.layout.addWidget(info)
        dialog.layout.addSpacing(10)

        # Buttons
        def apply_changes():
            try:
                new_interval = int(interval_combo.currentText())
                # Save the new interval
                self.presentation_interval = new_interval

                # Save it in the user preferences
                from backend.users.preferences_model import PreferencesModel
                success = PreferencesModel.save_pagination_interval(
                    self.current_user,
                    self.presentation_interval
                )

                if success:
                    print(f"Pagination interval saved: {self.presentation_interval}s")
                else:
                    print("Error while saving the pagination interval")

                # Update the timer with the new interval
                if self.presentation_timer.isActive():
                    self.presentation_timer.stop()
                self.presentation_timer.start(self.presentation_interval * 1000)

                dialog.accept()

                # Notify the user
                self.show_information_message(
                    "Settings Updated",
                    f"The pagination interval has been changed to {self.presentation_interval} seconds."
                )

            except ValueError:
                self.show_warning_message("Error", "Please select a valid interval.")

        buttons = [
            ("Apply", apply_changes, "primary"),
            ("Cancel", dialog.reject, "danger")
        ]

        dialog.add_button_row(buttons)

        # Run the dialog
        dialog.exec_()

    def update_presentation_data(self):
        """Updates the data used by the presentation mode"""
        # Get the data using the model with the area filter
        self.total_records = self.model.get_filtered_patient_data(self.filtered_areas)

        # Check and store the cells with an alarm - making sure they are applied correctly
        self.global_alarm_cells = self.model.check_alarms(self.total_records)

        # Calculate the total number of pages
        if self.records_per_page > 0:
            self.total_pages = (len(self.total_records) + self.records_per_page - 1) // self.records_per_page
        else:
            self.total_pages = 1

        # Make sure the current page is valid
        if self.total_pages > 0:
            self.current_page = self.current_page % self.total_pages
        else:
            self.current_page = 0

    def show_current_page(self):
        """Shows the current page of records"""
        if not self.total_records:
            return

        # Calculate the start and end indexes for the current page
        start = self.current_page * self.records_per_page
        end = min(start + self.records_per_page, len(self.total_records))

        # Get the records for this page
        page_records = self.total_records[start:end]

        # Clear the table
        self.table.setRowCount(0)

        # Get the cells with an alarm for the records of this page
        # We use the model method directly, as in the main view
        alarm_cells = self.model.check_alarms(page_records)
        triage_index = self.headers.index('Triage')
        admission_consult_index = self.headers.index('Admission Consult')

        # Show the records in the table
        if page_records:
            for row_idx, row_data in enumerate(page_records):
                # Process only the data we are going to show
                current_row = []
                for i in range(len(row_data)):
                    if i == 0:  # Name
                        current_row.append(self.mask_name(row_data[i]))
                    elif i == 1:  # Document ID
                        current_row.append(self.mask_document(row_data[i]))
                    elif i < 10:  # Up to Pending Tasks
                        current_row.append(row_data[i])
                    elif i == 11:  # Location (we skip Disposition, which is at index 10)
                        current_row.append(row_data[i])

                # Insert the row into the table
                self.table.insertRow(row_idx)
                for col, value in enumerate(current_row):
                    if col == triage_index or col == self.headers.index('Admission Consult') or \
                    col == self.headers.index('Labs') or col == self.headers.index('Imaging') or \
                    col == self.headers.index('Specialist Consult') or col == self.headers.index('Reassessment'):
                        # Use CustomColumnHeader so it works with the delegate
                        item = CustomColumnHeader("", str(value))
                        self.table.setItem(row_idx, col, item)
                    else:
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row_idx, col, item)

            # Update the alarms in the delegate for the admission consult - making sure they are applied correctly
            admission_consult_col = self.headers.index('Admission Consult')
            delegate = self.table.itemDelegateForColumn(admission_consult_col)
            if isinstance(delegate, StatusCircleDelegate):
                delegate.set_alarm_cells(alarm_cells)
                # Also set an empty set for the disposition alarms
                delegate.set_disposition_alarm_cells(set())

            # Set a fixed height for every row
            circle_delegate = self.table.itemDelegateForColumn(triage_index)
            if isinstance(circle_delegate, StatusCircleDelegate):
                row_height = circle_delegate.circle_size + 20  # +20 for padding
                for row in range(self.table.rowCount()):
                    self.table.setRowHeight(row, row_height)

    def activate_presentation_mode(self):
        """Enables the presentation mode according to the selected settings"""
        # Update the state
        self.presentation_mode_active = True

        # Calculate how many rows fit in the table
        visible_height = self.table.viewport().height()
        if self.table.rowCount() > 0:
            row_height = self.table.rowHeight(0)  # Height of one row
            self.records_per_page = max(1, int(visible_height / row_height))
        else:
            self.records_per_page = 10  # Default value

        # Get every record again to make sure they are up to date
        self.update_presentation_data()

        # Start from the first page
        self.current_page = 0
        self.show_current_page()

        # Start the timer with the configured interval
        self.presentation_timer.start(self.presentation_interval * 1000)

    def show_next_page(self):
        """Moves to the next page in the presentation mode"""
        if not self.presentation_mode_active or self.total_pages <= 1:
            return

        # Move to the next page
        self.current_page = (self.current_page + 1) % self.total_pages
        self.show_current_page()

    def resizeEvent(self, event):
        """Handles the window resize event"""
        # Call the base class method
        super().resizeEvent(event)

        # Update the side menu so it stays responsive
        if hasattr(self, 'side_menu'):
            self.side_menu.adjust_for_screen_size()

        # Update the side menu placement
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

        # Recalculate the records per page if the presentation mode is active
        if self.presentation_mode_active:
            # Recalculate how many rows fit in the table after the resize
            visible_height = self.table.viewport().height()
            if self.table.rowCount() > 0:
                row_height = self.table.rowHeight(0)
                new_records_per_page = max(1, int(visible_height / row_height))

                # If the number of records per page changed, refresh the view
                if new_records_per_page != self.records_per_page:
                    self.records_per_page = new_records_per_page
                    self.update_presentation_data()
                    self.show_current_page()

    def update_table(self):
        """Updates the table with the current data"""
        try:
            # Check that the table exists before trying to use it
            if not hasattr(self, 'table'):
                print("The table has not been initialized yet")
                return

            # If this is the first load, show a loading screen
            if self.first_load:
                splash = SplashScreen(self, logo_path=self.logo_path, message="Loading patient data...", duration=1)
                splash.setFixedSize(int(self.screen.width() * 0.3), int(self.screen.height() * 0.3))
                splash.show()
                splash.opacity_animation.start()
                QApplication.processEvents()

            # Get the data using the model with the area filter
            data = self.model.get_filtered_patient_data(self.filtered_areas)

            # Store the data for the presentation mode
            self.total_records = data

            # If the presentation mode is active, refresh the presentation view
            if self.presentation_mode_active:
                self.update_presentation_data()
                self.show_current_page()
                return

            # If the presentation mode is not active, show every record (this should not happen)
            self.table.setRowCount(0)

            # Get the cells with an alarm from the model - using the correct model method
            alarm_cells = self.model.check_alarms(data)
            disposition_alarm_cells = set()  # Initialize an empty set for the waiting room
            triage_index = self.headers.index('Triage')
            pending_tasks_index = self.headers.index('Pending Tasks')  # Index of the pending tasks column

            if data:
                for row_idx, row_data in enumerate(data):
                    # Process only the data we are going to show (we exclude Disposition and Admission)
                    current_row = []
                    for i in range(len(row_data)):
                        if i == 0:  # Name
                            current_row.append(self.mask_name(row_data[i]))
                        elif i == 1:  # Document ID
                            current_row.append(self.mask_document(row_data[i]))
                        elif i < 10:  # Up to Pending Tasks
                            current_row.append(row_data[i])
                        elif i == 11:  # Location (we skip Disposition, which is at index 10)
                            current_row.append(row_data[i])

                    # Insert the row into the table
                    self.table.insertRow(row_idx)
                    for col, value in enumerate(current_row):
                        # Check whether this column has to use the special delegate
                        if col == triage_index or col == self.headers.index('Admission Consult') or \
                            col == self.headers.index('Labs') or col == self.headers.index('Imaging') or \
                            col == self.headers.index('Specialist Consult') or col == self.headers.index('Reassessment'):
                            # Use a custom item so it works with the delegate
                            item = CustomColumnHeader("", str(value))
                            self.table.setItem(row_idx, col, item)

                        elif col == pending_tasks_index:
                            # For the pending tasks column, make sure it is shown exactly as it comes from the DB
                            # without any extra processing
                            pending_tasks_text = str(value) if value is not None else ""
                            item = QTableWidgetItem(pending_tasks_text)
                            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Left aligned for better readability
                            self.table.setItem(row_idx, col, item)
                        else:
                            # For plain text
                            item = QTableWidgetItem(str(value))
                            item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                            self.table.setItem(row_idx, col, item)

                # Update the alarms in the delegate for the admission consult - making sure they are applied correctly
                admission_consult_col = self.headers.index('Admission Consult')
                delegate = self.table.itemDelegateForColumn(admission_consult_col)
                if isinstance(delegate, StatusCircleDelegate):
                    delegate.set_alarm_cells(alarm_cells)
                    # Also set the empty set of disposition alarms
                    delegate.set_disposition_alarm_cells(disposition_alarm_cells)

                # Configure the column widths
                self.configure_column_widths()

                # Set a fixed height for every row
                circle_delegate = self.table.itemDelegateForColumn(triage_index)
                if isinstance(circle_delegate, StatusCircleDelegate):
                    row_height = circle_delegate.circle_size + 20  # +20 for padding
                    for row in range(self.table.rowCount()):
                        self.table.setRowHeight(row, row_height)

            # Close the loading screen if this is the first time
            if self.first_load:
                self.first_load = False
                if 'splash' in locals():
                    splash.accept()

        except Exception as e:
            self.show_information_message("Error", f"Error while updating the table: {str(e)}", QMessageBox.Critical)
        finally:
            self.model.close_db()

            # If this is the first load, enable the presentation mode after loading the data
            if self.first_load:
                self.first_load = False
                if 'splash' in locals():
                    splash.accept()

    def configure_column_widths(self):
        """Configures the table column widths to ensure consistency"""
        # Store the current resize mode of the columns
        current_modes = []
        for col in range(self.table.columnCount()):
            current_modes.append(self.table.horizontalHeader().sectionResizeMode(col))

        # Set every column to stretch mode temporarily
        for col in range(self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)

        # Update the table size
        self.table.updateGeometry()
        self.table.viewport().updateGeometry()

        # Calculate the widths based on the current table size
        table_width = self.table.width()
        column_count = len(self.headers)
        standard_column_width = table_width / column_count

        # Apply specific widths to the selected columns
        name_index = self.headers.index('Name')
        pending_tasks_index = self.headers.index('Pending Tasks')

        # Switch to fixed mode for the specific columns
        self.table.horizontalHeader().setSectionResizeMode(name_index, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(pending_tasks_index, QHeaderView.Fixed)

        # Set the specific widths
        self.table.setColumnWidth(name_index, int(standard_column_width * 1.3))
        self.table.setColumnWidth(pending_tasks_index, int(standard_column_width * 1.5))

        # Make sure the changes are visible
        self.table.horizontalHeader().update()

    def show_confirmation_message(self, title, message):
        """Shows a styled confirmation message"""
        msg_box = StyledMessageBox(self, title, message, QMessageBox.Question, "confirmation")

        btn_yes = QPushButton("Yes")
        btn_no = QPushButton("No")

        btn_yes.setCursor(Qt.PointingHandCursor)
        btn_no.setCursor(Qt.PointingHandCursor)

        msg_box.addButton(btn_yes, QMessageBox.YesRole)
        msg_box.addButton(btn_no, QMessageBox.NoRole)

        msg_box.setDefaultButton(btn_no)

        result = msg_box.exec_()

        return msg_box.clickedButton() == btn_yes

    def show_information_message(self, title, message, icon=QMessageBox.Information):
        """Shows a styled informational message"""
        style_type = "error" if icon == QMessageBox.Critical else "info"

        msg_box = StyledMessageBox(self, title, message, icon, style_type)

        btn_ok = QPushButton("OK")
        btn_ok.setCursor(Qt.PointingHandCursor)

        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
        msg_box.setDefaultButton(btn_ok)

        return msg_box.exec_()

    def show_filter_dialog(self):
        """Shows the dialog used to filter by area and saves the preferences"""
        dialog = AreaFilterDialog(self, self.areas, self.filtered_areas)
        if dialog.exec_() == QDialog.Accepted:
            # Get the areas selected in the dialog
            new_filters = dialog.get_selected_areas()

            # If no area is selected, use every area by default
            if not new_filters:
                new_filters = list(self.areas.keys())

            # Update the local filters
            self.filtered_areas = new_filters

            # Save the preferences
            from backend.users.preferences_model import PreferencesModel
            print(f"\n=== Saving the new preferences for user: {self.current_user} ===")
            print(f"Selected filters: {new_filters}")

            # Try to save the preferences
            success = PreferencesModel.save_filter_preferences(
                self.current_user,
                self.filtered_areas
            )

            if success:
                print("Preferences saved successfully")
            else:
                print("Error while saving the preferences")
                # Tell the user their preferences will not be saved permanently
                self.show_information_message(
                    "Preferences not persisted",
                    "The filter preferences could not be saved permanently. "
                    "The preferences will be kept for this session only.",
                    QMessageBox.Warning
                )

            # Update the visual filter indicator
            self.create_filter_indicator()

            # Refresh the table with the new filters
            self.update_table()

    def create_filter_indicator(self):
        """Creates or updates the visual indicator of the applied filters"""
        # Clear the previous layout
        while self.filter_layout.count():
            item = self.filter_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # If there are no filters, or every one is selected, hide the indicator
        if len(self.filtered_areas) == len(self.areas) or not self.filtered_areas:
            self.filter_container.hide()
            return

        # Show the container
        self.filter_container.show()

        # Create the active filters label with better contrast and size
        filters_label = QLabel("Active filters:")
        filters_label.setStyleSheet(f"""
            color: {COLORS['background_header']};
            font-size: 17px;
            font-weight: bold;
            background-color: transparent;
            padding-right: 8px;
        """)
        self.filter_layout.addWidget(filters_label)

        # Create a chip for each filtered area with better contrast and size
        for i, area in enumerate(sorted(self.filtered_areas)):
            if i < 5:  # Show at most 5 areas directly
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
                self.filter_layout.addWidget(area_label)

        # Indicator for the extra areas, with better visibility
        if len(self.filtered_areas) > 5:
            more_areas = QLabel(f"+{len(self.filtered_areas) - 5} more")
            more_areas.setStyleSheet(f"""
                color: {COLORS['text_primary']};
                background-color: {COLORS['background_header']};
                padding-left: 5px;
                padding-right: 10px;
                font-size: 15px;
                font-weight: 500;
            """)
            self.filter_layout.addWidget(more_areas)

        # Button used to edit the filters, with an improved style
        btn_edit = QPushButton("Edit")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setStyleSheet(f"""
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
        btn_edit.clicked.connect(self.show_filter_dialog)
        self.filter_layout.addWidget(btn_edit)

        # Add expanding space at the end
        self.filter_layout.addStretch(1)

    def logout(self):
        if self.show_confirmation_message(
            "Confirm Log Out",
            "Are you sure you want to log out?"
        ):
            # Show the loading screen while logging out
            splash = SplashScreen(None, logo_path=self.logo_path, message="Logging out...", duration=1.5)
            splash.setFixedSize(int(self.screen.width() * 0.3), int(self.screen.height() * 0.3))
            splash.show()
            splash.opacity_animation.start()
            QApplication.processEvents()

            # Stop the timer before closing
            if hasattr(self, 'timer'):
                self.timer.stop()

            try:
                if hasattr(self.model, 'conn') and self.model.conn:
                    self.model.conn.close()
            except Exception as e:
                print(f"Error while closing the database connection: {e}")

            # Wait for the loading screen to finish
            splash.exec_()

            self.close()
            self.login_interface.reset_login()

    def closeEvent(self, event):
        # Stop the timer before closing
        if hasattr(self, 'timer'):
            self.timer.stop()

        # Stop the timers before closing
        if hasattr(self, 'presentation_timer'):
            self.presentation_timer.stop()

        # Continue with the normal close
        super().closeEvent(event)

    def toggle_maximized(self):
        """Toggles the window between maximized and normal mode."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

# New dialog used to filter by area, fully redesigned with a grid layout
class AreaFilterDialog(StyledDialog):
    def __init__(self, parent=None, areas=None, selected_areas=None):
        super().__init__("Filter by Areas", 650, parent)  # Width increased for a better experience

        self.areas = areas or {}
        self.selected_areas = selected_areas or []

        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle (compiled with PyInstaller)
            self.base_path = sys._MEIPASS
        else:
            # For normal script execution
            self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        images_path = os.path.join(self.base_path, "frontend", "images")
        self.check_icon_path = os.path.join(images_path, "check.png")

        # Improved visual configuration of the dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background_primary']};
                border-radius: 15px;
            }}
            QWidget {{
                font-family: 'Segoe UI', sans-serif;
            }}
        """)

        # Create a main layout with consistent margins
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header with title and description - improved with a light background
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['background_white']};")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setSpacing(12)

        # Title with more contrast and visibility on a white background
        title = QLabel("Filter by areas")
        title.setStyleSheet(f"""
            font-size: 26px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            background-color: {COLORS['background_white']};
            padding: 10px 0;
        """)
        title.setAlignment(Qt.AlignCenter)

        # Improved description with a white background
        description = QLabel("Select the areas you want to display in the table:")
        description.setWordWrap(True)
        description.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            padding: 0px 5px 5px 5px;
            background-color: {COLORS['background_white']};
        """)
        description.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(description)

        # Subtle divider line below the description
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet(f"""
            color: #E0E0E0;
            background-color: #E0E0E0;
            max-height: 1px;
        """)
        header_layout.addWidget(divider)

        # Add the header to the main layout with a rounded border
        header.setObjectName("headerContainer")
        header.setStyleSheet(f"""
            #headerContainer {{
                background-color: {COLORS['background_white']};
                border-radius: 10px;
                border: 1px solid #F0F0F0;
            }}
        """)
        main_layout.addWidget(header)

        # Main area for the checkboxes (container with a white background)
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

        # Layout for the checkboxes arranged in a grid
        grid_layout = QGridLayout(content_container)
        grid_layout.setContentsMargins(20, 20, 20, 20)
        grid_layout.setSpacing(15)  # Consistent space between the elements

        # Determine the number of columns based on the available width (responsive)
        num_columns = 3  # Default value for normal screens

        if parent:
            parent_width = parent.width()
            if parent_width < 800:
                num_columns = 2  # For small screens
            elif parent_width > 1400:
                num_columns = 4  # For very large screens

        # Improved style for the checkboxes, with a check icon
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
                image: url("{self.check_icon_path.replace('\\', '/')}");
            }}
        """

        # Check whether the check image exists
        if not os.path.exists(self.check_icon_path):
            print(f"Warning: the check image was not found at: {self.check_icon_path}")

        # Create the checkboxes in a grid layout
        self.checkboxes = {}
        row = 0
        column = 0

        for area_name in sorted(self.areas.keys()):
            # Create the checkbox with a simplified design
            checkbox = QCheckBox(area_name)
            checkbox.setStyleSheet(checkbox_style)
            checkbox.setCursor(Qt.PointingHandCursor)
            checkbox.setMinimumHeight(42)  # Minimum height for better accessibility

            # Check the checkbox if the area was already selected
            if area_name in self.selected_areas:
                checkbox.setChecked(True)

            self.checkboxes[area_name] = checkbox

            # Add it to the grid layout
            grid_layout.addWidget(checkbox, row, column)

            # Update the position for the next checkbox
            column += 1
            if column >= num_columns:
                column = 0
                row += 1

        # Add the grid container to the main layout
        main_layout.addWidget(content_container, 1) # With an expansion factor of 1

        # Container for the selection buttons, with a unified and improved style
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

        # Improved style for the auxiliary buttons (with a light background)
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

        # Select/deselect buttons with an improved style
        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.setStyleSheet(button_style_aux)
        self.btn_select_all.setCursor(Qt.PointingHandCursor)

        self.btn_unselect_all = QPushButton("Deselect All")
        self.btn_unselect_all.setStyleSheet(button_style_aux)
        self.btn_unselect_all.setCursor(Qt.PointingHandCursor)

        # Connect the events
        self.btn_select_all.clicked.connect(self.select_all)
        self.btn_unselect_all.clicked.connect(self.unselect_all)

        # Add the buttons to the layout with an even distribution
        selection_layout.addWidget(self.btn_select_all)
        selection_layout.addWidget(self.btn_unselect_all)

        # Add the selection button widget to the main layout
        main_layout.addWidget(selection_buttons)

        # Replace the default dialog layout with our custom layout
        # First we clear the original layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Now we add our custom layout
        for i in range(main_layout.count()):
            item = main_layout.takeAt(0)
            if item.widget():
                self.layout.addWidget(item.widget())
            else:
                self.layout.addItem(item)

        # Main action buttons with a unified style
        action_buttons = [
            ("Apply Filters", self.accept, "primary"),
            ("Cancel", self.reject, "danger")
        ]

        buttons_layout = self.add_button_row(action_buttons)

        # Improved and consistent style for the main buttons
        for i in range(buttons_layout.count()):
            widget = buttons_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setMinimumHeight(48)  # Slightly taller for better accessibility
                widget.setStyleSheet(widget.styleSheet() + """
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 8px;
                """)

        # Configure the responsive size of the dialog
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(450, 400)  # Smaller minimum size now that we use a grid

        # Center it on the screen and adjust the size
        self.centerAndResize()

    def centerAndResize(self):
        """Centers the dialog on the screen and adjusts its size responsively"""
        screen = QDesktopWidget().availableGeometry()

        # Calculate the optimal size based on the screen size
        optimal_width = min(650, int(screen.width() * 0.5))
        optimal_height = min(550, int(screen.height() * 0.6))  # Reduced height thanks to the grid layout

        # Set the dimensions
        self.resize(optimal_width, optimal_height)

        # Center it on the screen
        geom = self.frameGeometry()
        geom.moveCenter(screen.center())
        self.setGeometry(geom)

    def select_all(self):
        """Selects every checkbox"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)

    def unselect_all(self):
        """Deselects every checkbox"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    def get_selected_areas(self):
        """Returns a list with the selected areas"""
        return [area for area, checkbox in self.checkboxes.items() if checkbox.isChecked()]
