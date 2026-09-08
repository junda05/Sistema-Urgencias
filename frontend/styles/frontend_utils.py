from PyQt5.QtWidgets import (QCompleter, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QMessageBox, QFrame, QLayout,
                           QLineEdit, QFormLayout, QSizePolicy, QDesktopWidget, QDateTimeEdit, QCheckBox,
                           QGridLayout, QGroupBox, QScrollArea, QListView)
from PyQt5.QtCore import Qt, QTimer, QRect, QSize, QStringListModel, QPoint, QDateTime, QTime
from frontend.styles.styles import *
from frontend.styles.components import StyledDialog
from backend.database import PatientModel
import sys
import os

class FilterDialog(StyledDialog):
    def __init__(self, parent=None, areas=None, selected_areas=None,
                date_filter_active=False, start_date=None, end_date=None):
        super().__init__("Filter Patients", 1200, parent)

        # Remove the fixed width configuration to allow responsiveness
        # self.setFixedWidth(1200)

        self.areas = areas or {}
        self.selected_areas = selected_areas or []
        self.date_filter_active = date_filter_active
        self.start_date = start_date or QDateTime.currentDateTime().addDays(-7)
        self.end_date = end_date or QDateTime.currentDateTime()

        # Initialize paths correctly
        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            # Fix: use the base path without duplicating "frontend"
            self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        images_path = os.path.join(self.base_path, "frontend", "images")
        self.check_path = os.path.join(images_path, "check.png")

        # Check whether the image exists and show a less ambiguous message
        if not os.path.exists(self.check_path):
            print(f"Warning: check image not found at: {self.check_path}")
            print(f"Current directory: {os.getcwd()}")
            print(f"Images directory: {images_path}")
            print(f"Files in the images directory: {os.listdir(images_path) if os.path.exists(images_path) else 'Directory does not exist'}")

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

        # Header with title and description
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['background_white']};")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setSpacing(12)

        # Title
        title = QLabel("Filter patients")
        title.setStyleSheet(f"""
            font-size: 26px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            background-color: {COLORS['background_white']};
            padding: 10px 0;
        """)
        title.setAlignment(Qt.AlignCenter)

        # Description
        description = QLabel("Select the areas and/or the admission date range to filter the patients:")
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

        # Divider line
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

        # Horizontal container for areas and dates - we adjust the proportion
        sections_container = QWidget()
        sections_container.setStyleSheet("background-color: transparent;")
        sections_layout = QHBoxLayout(sections_container)
        sections_layout.setContentsMargins(0, 0, 0, 0)
        sections_layout.setSpacing(15)  # Keep horizontal space between sections

        # Area filter section - we reduce vertical margins
        area_section = QGroupBox("Filter by areas")
        area_section.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLORS['background_transparent']};
                border-radius: 10px;
                border: 1px solid #F0F0F0;
                padding: 10px;
                margin-top: 35px; /* Reduced from 60px to 35px */
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
        area_layout.setContentsMargins(10, 15, 10, 10)  # Reduced from (15, 20, 15, 15)
        area_layout.setSpacing(10)  # Reduced from 15

        # Grid of area checkboxes - more columns
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
        grid_layout.setSpacing(10)  # We reduce the spacing so more items fit

        # Increase the number of columns for better horizontal distribution
        num_columns = 4  # Increased from 3 to 4 columns

        # Style for the checkboxes
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
                image: url("{self.check_path.replace('\\', '/')}");
            }}
        """

        # Create checkboxes in a grid layout
        self.checkboxes = {}
        row = 0
        column = 0

        # Distribute areas across columns more evenly
        sorted_areas = sorted(self.areas.keys())
        items_per_column = (len(sorted_areas) + num_columns - 1) // num_columns

        for index, area_name in enumerate(sorted_areas):
            # Calculate the new position based on an even distribution
            row = index % items_per_column
            column = index // items_per_column

            checkbox = QCheckBox(area_name)
            checkbox.setStyleSheet(checkbox_style)
            checkbox.setCursor(Qt.PointingHandCursor)
            checkbox.setMinimumHeight(38)  # We slightly reduce the height

            # Check the checkbox if the area was already selected
            if area_name in self.selected_areas:
                checkbox.setChecked(True)

            self.checkboxes[area_name] = checkbox

            # Add to the grid layout
            grid_layout.addWidget(checkbox, row, column)

        # Selection buttons for areas - dark background removed
        buttons_container = QWidget()
        buttons_container.setStyleSheet(f"background-color: {COLORS['background_white']};") # White background for the container
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 10, 0, 0)  # We add a top margin to separate it from the checkboxes
        buttons_layout.setSpacing(15)  # We increase the space between buttons

        # Auxiliary button style - darker color for better contrast
        button_style_aux = f"""
            QPushButton {{
                background-color: {COLORS['button_primary']}; /* Changed to the primary color for better visibility */
                color: white; /* White text for contrast */
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

        # Buttons to select/deselect all areas
        btn_select_all = QPushButton("Select All")
        btn_select_all.setStyleSheet(button_style_aux)
        btn_select_all.setCursor(Qt.PointingHandCursor)
        btn_select_all.clicked.connect(self.select_all_areas)

        btn_unselect_all = QPushButton("Deselect All")
        btn_unselect_all.setStyleSheet(button_style_aux)
        btn_unselect_all.setCursor(Qt.PointingHandCursor)
        btn_unselect_all.clicked.connect(self.unselect_all_areas)

        buttons_layout.addWidget(btn_select_all)
        buttons_layout.addWidget(btn_unselect_all)

        area_layout.addWidget(content_container)
        area_layout.addWidget(buttons_container)

        # Date filter section - we reduce the vertical margins as well
        date_section = QGroupBox("Filter by admission date")
        date_section.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLORS['background_transparent']};
                border-radius: 10px;
                border: 1px solid #F0F0F0;
                padding: 10px;
                margin-top: 35px; /* Reduced from 45px to 35px to align with the area section */
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
        date_layout.setContentsMargins(10, 15, 10, 10)  # Reduced from (15, 25, 15, 15)
        date_layout.setSpacing(10)  # Reduced from 20

        # Checkbox to enable/disable the date filter - we add a bottom margin
        self.date_checkbox = QCheckBox("Enable admission date filter")
        self.date_checkbox.setStyleSheet(checkbox_style + """
            margin-bottom: 10px;  /* Bottom margin to separate it from the date container */
            padding-bottom: 5px;
        """)
        self.date_checkbox.setCursor(Qt.PointingHandCursor)
        self.date_checkbox.setChecked(self.date_filter_active)
        self.date_checkbox.stateChanged.connect(self.toggle_date_filter)
        date_layout.addWidget(self.date_checkbox)

        # Container for the date selectors - we optimize the inner spacing
        date_selectors = QWidget()
        date_selectors.setObjectName("dateContainer")
        date_selectors.setStyleSheet(f"""
            #dateContainer {{
                background-color: white;
                border-radius: 10px;
                border: 1px solid #EEEEEE;
                margin-top: 0px;
                min-height: 140px;
                width: 100%; /* We make sure it takes up all the available width */
            }}
        """)
        date_selector_layout = QFormLayout(date_selectors)
        date_selector_layout.setContentsMargins(20, 20, 20, 20)
        date_selector_layout.setSpacing(20)
        # Change the growth policy so the fields do not expand automatically
        date_selector_layout.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)

        # We improve the style of the date labels to make them more visible
        label_style = f"""
            color: {COLORS['text_primary']};
            font-size: 15px; /* Increased from 14px */
            font-weight: 500;
            padding: 5px 0;
        """

        label_from = QLabel("From:")
        label_from.setStyleSheet(label_style)

        label_to = QLabel("To:")
        label_to.setStyleSheet(label_style)

        self.calendar_icon_path = os.path.join(images_path, "calendar.png")

        # Start date - we improve the style and add a more modern calendar style
        self.date_start = QDateTimeEdit(self.start_date)
        self.date_start.setCalendarPopup(True)
        self.date_start.setDisplayFormat("dd/MM/yyyy")
        self.date_start.setTime(QTime(0, 0, 0))
        # Compute a suitable width for the longest date "dd/MM/yyyy"
        self.date_start.setFixedWidth(180)
        # Center the text inside the date field
        self.date_start.setAlignment(Qt.AlignCenter)
        self.date_start.setStyleSheet(f"""
            QDateTimeEdit {{
                background-color: {COLORS['background_white']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {BORDER_RADIUS['medium']};
                padding: 10px;
                padding-right: 35px; /* Space for the icon */
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
                image: url("{self.calendar_icon_path.replace('\\', '/')}");
                padding-right: 5px;
            }}

            /* Modern styles for the popup calendar */
            QCalendarWidget {{
                background-color: {COLORS['background_white']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['button_primary']};
                selection-color: white;
                border: 1px solid {COLORS['border_light']};
            }}

            /* Calendar navigation bar */
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {COLORS['background_header']};
                border-bottom: none;
                padding: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}

            /* Calendar navigation buttons */
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

            /* Month and year dropdowns */
            QCalendarWidget QMenu {{
                background-color: {COLORS['background_white']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['button_primary']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {COLORS['button_primary']};
                selection-color: white;
            }}

            /* Adjustments for the spinbox (year) */
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

            /* Weekday headers */
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

            /* Calendar days */
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
        self.date_start.setEnabled(self.date_filter_active)

        # End date - we apply the same modern calendar styles
        self.date_end = QDateTimeEdit(self.end_date)
        self.date_end.setCalendarPopup(True)
        self.date_end.setDisplayFormat("dd/MM/yyyy")
        self.date_end.setTime(QTime(23, 59, 59))
        # We apply the same fixed width and centered alignment
        self.date_end.setFixedWidth(180)
        self.date_end.setAlignment(Qt.AlignCenter)
        self.date_end.setStyleSheet(self.date_start.styleSheet())
        self.date_end.setEnabled(self.date_filter_active)

        date_selector_layout.addRow(label_from, self.date_start)
        date_selector_layout.addRow(label_to, self.date_end)

        date_layout.addWidget(date_selectors)
        sections_layout.addWidget(area_section)
        sections_layout.addWidget(date_section)

        # Add the horizontal container to the main layout
        main_layout.addWidget(sections_container)

        # Replace the dialog's default layout with our custom layout
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

        # Action buttons
        action_buttons = [
            ("Apply Filters", self.apply_filters, "primary"),
            ("Cancel", self.reject, "danger")
        ]

        buttons_layout = self.add_button_row(action_buttons)

        # Improved style for the main buttons
        for i in range(buttons_layout.count()):
            widget = buttons_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setMinimumHeight(48)
                widget.setStyleSheet(widget.styleSheet() + """
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 8px;
                """)

        # Configure the responsive size of the dialog
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(800, 400)  # Wider than tall

        # Center on screen and adjust size
        self.centerDialog()
        self.adjustSize()

    def centerDialog(self):
        """Centers the dialog on the screen and adjusts the size responsively"""
        # Get the screen dimensions
        screen = QDesktopWidget().availableGeometry()

        # Set a fixed size that is more suitable for this specific dialog
        # Reducing the width from 1000px to 800px
        dialog_width = 800
        dialog_height = min(700, int(screen.height() * 0.8))

        # Apply the size directly
        self.setFixedSize(dialog_width, dialog_height)

        # Compute the centered position
        x_position = (screen.width() - dialog_width) // 2
        y_position = (screen.height() - dialog_height) // 2

        # Move the dialog to the centered position
        self.move(x_position, y_position)

    def toggle_date_filter(self, state):
        """Enables or disables the date selectors"""
        enabled = state == Qt.Checked
        self.date_start.setEnabled(enabled)
        self.date_end.setEnabled(enabled)

    def select_all_areas(self):
        """Selects every area checkbox"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)

    def unselect_all_areas(self):
        """Deselects every area checkbox"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    def get_selected_areas(self):
        """Returns a list with the selected areas"""
        return [area for area, checkbox in self.checkboxes.items() if checkbox.isChecked()]

    def apply_filters(self):
        """Validates the filters and closes the dialog if they are correct"""
        # Check whether the date filter is active
        self.date_filter_active = self.date_checkbox.isChecked()

        if self.date_filter_active:
            # Validate that the end date is later than the start date
            if self.date_start.dateTime() > self.date_end.dateTime():
                # Create a styled error message instead of the standard QMessageBox
                if not hasattr(self, 'error_container'):
                    # Create the error container if it does not exist
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

                    # Add it to the main layout before the buttons
                    self.layout.insertWidget(self.layout.count()-1, self.error_container)

                # Show the error message
                self.error_message.setText("The start date must be earlier than the end date")
                self.error_container.setVisible(True)

                # Schedule hiding the message after 5 seconds
                QTimer.singleShot(5000, lambda: self.error_container.setVisible(False))
                return

            # Save the selected dates with adjusted times
            start_date = self.date_start.dateTime()
            adjusted_start_date = QDateTime(start_date.date(), QTime(0, 0, 0))
            self.start_date = adjusted_start_date

            end_date = self.date_end.dateTime()
            adjusted_end_date = QDateTime(end_date.date(), QTime(23, 59, 59))
            self.end_date = adjusted_end_date

        # Get the selected areas
        self.selected_areas = self.get_selected_areas()

        # Everything is correct, accept the dialog
        self.accept()

class LabsSelector(QWidget):
    def __init__(self, parent=None, base_path=None):
        super().__init__(parent)
        self.base_path = base_path
        self.selected_labs = []  # List to store [code, name]
        self.setup_ui()
        self.load_labs()

    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)  # More consistent spacing

        # Search field with improved autocompletion
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search lab by name or code...")
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

        # Improved style for the autocompletion popup
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

        self.add_button = QPushButton("Add")
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

        # Header with title and a button to clear everything
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        label_title = QLabel("Selected labs:")
        label_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-weight: bold;
            margin-top: 5px;
        """)

        self.clear_all_button = QPushButton("Clear all")
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
        self.clear_all_button.clicked.connect(self.clear_all_labs)

        header_layout.addWidget(label_title)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_all_button)

        # Improved ScrollArea for the lab tags
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

        # New container for the tags with full width
        self.tags_container = QWidget()
        self.tags_layout = QVBoxLayout()  # Changed to QVBoxLayout to guarantee full width
        self.tags_layout.setSpacing(8)
        self.tags_layout.setContentsMargins(8, 8, 8, 8)
        self.tags_layout.setAlignment(Qt.AlignTop)  # Align tags at the top
        self.tags_container.setLayout(self.tags_layout)
        self.tags_container.setStyleSheet(f"""
            background-color: {COLORS['background_white']};
            padding: 0px;
        """)

        self.scroll_area.setWidget(self.tags_container)

        # Area to show error messages with a better style - without a disruptive border
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

        # Connect events
        self.add_button.clicked.connect(self.add_lab)
        self.search_input.returnPressed.connect(self.add_lab)

        # Add widgets to the main layout
        layout.addLayout(search_layout)
        layout.addSpacing(8)
        layout.addLayout(header_layout)
        layout.addWidget(self.scroll_area, 1)  # Give it expansion priority
        layout.addWidget(self.error_container)

        # Set a responsive minimum height for the scroll area
        screen_height = QDesktopWidget().availableGeometry().height()
        self.scroll_area.setMinimumHeight(min(int(screen_height * 0.15), 180))  # 15% of the screen height, max 180px

    def show_error(self, message):
        self.error_message.setText(message)
        self.error_container.setVisible(True)

        # Hide the message after 5 seconds
        QTimer.singleShot(5000, lambda: self.error_container.setVisible(False))

    def load_labs(self):
        try:
            # Get the list of labs from the database
            conn = PatientModel().connect()
            cursor = conn.cursor()
            cursor.execute("SELECT lab_code, lab_name FROM lab_catalog ORDER BY lab_name")
            self.labs = cursor.fetchall()
            conn.close()

            # Create the list for the autocompletion
            items = [f"{lab[0]} - {lab[1]}" for lab in self.labs]

            # Update the completer
            model = QStringListModel()
            model.setStringList(items)
            self.completer.setModel(model)

        except Exception as e:
            print(f"Error loading labs: {str(e)}")
            self.labs = []

    def add_lab(self):
        text_value = self.search_input.text().strip()
        if not text_value:
            return

        # Look up whether the lab exists
        found = False
        for code, name in self.labs:
            if text_value.startswith(code) or code in text_value or name.lower() in text_value.lower():
                found = True
                # Check that it has not been added already
                if not any(lab[0] == code for lab in self.selected_labs):
                    self.selected_labs.append([code, name])
                    self.create_tag(code, name)
                    self.search_input.clear()
                    # Focus the input to keep adding
                    self.search_input.setFocus()
                else:
                    self.show_error(f"The lab '{name}' has already been added")
                break

        if not found:
            self.show_error("The entered lab does not exist in the database.")

    def create_tag(self, code, name):
        # Create the widget for the tag with full width
        tag = QFrame()
        tag.setObjectName("lab_tag")
        tag.setFixedHeight(40)  # Set a fixed height for every tag
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

        # Horizontal layout for the tag with a better distribution
        tag_layout = QHBoxLayout(tag)
        tag_layout.setContentsMargins(12, 0, 8, 0)  # Reduce the vertical margin to fit the fixed height
        tag_layout.setSpacing(10)

        # Tag text with a better style
        text_label = QLabel(f"{code} - {name}")
        text_label.setWordWrap(True)
        text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text_label.setStyleSheet(f"""
            font-size: 14px;
            font-family: 'Segoe UI', sans-serif;
            color: {COLORS['text_primary']};
            background: transparent;
            padding: 2px 0;
        """)

        # Remove button with a better size and style - adjusted for vertical centering
        btn_remove = QPushButton("×")
        btn_remove.setObjectName("btn_remove_lab")
        btn_remove.setCursor(Qt.PointingHandCursor)
        btn_remove.setFixedSize(22, 22)  # Slightly larger for an easier click
        btn_remove.setStyleSheet(f"""
            #btn_remove_lab {{
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
            #btn_remove_lab:hover {{
                background-color: #FF0000;
            }}
            #btn_remove_lab:pressed {{
                background-color: #CC0000;
            }}
        """)

        # Connect the removal event
        btn_remove.clicked.connect(lambda: self.remove_tag(tag, code))

        # Add the elements to the layout
        tag_layout.addWidget(text_label, 1)
        tag_layout.addWidget(btn_remove, 0, Qt.AlignVCenter)

        # Add the tag to the container using insertWidget to place it at the top
        self.tags_layout.insertWidget(0, tag)  # Insert at the start so the last one added goes first

        # Adjust the minimum height according to the number of items
        self.adjust_minimum_height()

    def remove_tag(self, tag, code):
        # Remove the tag visually
        self.tags_layout.removeWidget(tag)
        tag.deleteLater()

        # Remove it from the selected list
        self.selected_labs = [lab for lab in self.selected_labs if lab[0] != code]

        # Adjust the minimum height according to the number of items
        self.adjust_minimum_height()

    def clear_all_labs(self):
        # Remove every visual tag
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Clear the selected list
        self.selected_labs = []

        # Adjust the minimum height
        self.adjust_minimum_height()

    def adjust_minimum_height(self):
        # Adjust the minimum height of the scroll area to the content while keeping it proportional to the screen
        screen_height = QDesktopWidget().availableGeometry().height()
        base_height = min(int(screen_height * 0.15), 180)

        # We keep the base height to ensure consistency
        if self.tags_layout.count() > 0:
            # Compute the estimated height based on the number of items
            height_per_item = 44  # Estimated height per tag (40px + margin)
            content_height = min(self.tags_layout.count() * height_per_item, int(screen_height * 0.3))
            desired_height = max(base_height, content_height + 20)
            self.scroll_area.setMinimumHeight(desired_height)
        else:
            self.scroll_area.setMinimumHeight(base_height)

    def get_selected_labs(self):
        return self.selected_labs

    def set_selected_labs(self, labs):
        # Clear the current selection
        self.clear_all_labs()

        # Add the new labs
        for code, name in labs:
            self.selected_labs.append([code, name])
            self.create_tag(code, name)

class ImagingSelector(QWidget):
    def __init__(self, parent=None, base_path=None):
        super().__init__(parent)
        self.base_path = base_path
        self.selected_imaging = []  # List to store [code, name]
        self.setup_ui()
        self.load_imaging()

    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)  # More consistent spacing

        # Search field with improved autocompletion
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search imaging study by name or code...")
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

        # Improved style for the autocompletion popup
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

        self.add_button = QPushButton("Add")
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

        # Header with title and a button to clear everything
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        label_title = QLabel("Selected imaging studies:")
        label_title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-weight: bold;
            margin-top: 5px;
        """)

        self.clear_all_button = QPushButton("Clear all")
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
        self.clear_all_button.clicked.connect(self.clear_all_imaging)

        header_layout.addWidget(label_title)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_all_button)

        # Improved ScrollArea for the imaging tags
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

        # New container for the tags with full width
        self.tags_container = QWidget()
        self.tags_layout = QVBoxLayout()  # Changed to QVBoxLayout to guarantee full width
        self.tags_layout.setSpacing(8)
        self.tags_layout.setContentsMargins(8, 8, 8, 8)
        self.tags_layout.setAlignment(Qt.AlignTop)  # Align tags at the top
        self.tags_container.setLayout(self.tags_layout)
        self.tags_container.setStyleSheet(f"""
            background-color: {COLORS['background_white']};
            padding: 0px;
        """)

        self.scroll_area.setWidget(self.tags_container)

        # Area to show error messages with a better style - without a disruptive border
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

        # Connect events
        self.add_button.clicked.connect(self.add_imaging)
        self.search_input.returnPressed.connect(self.add_imaging)

        # Add widgets to the main layout
        layout.addLayout(search_layout)
        layout.addSpacing(8)
        layout.addLayout(header_layout)
        layout.addWidget(self.scroll_area, 1)  # Give it expansion priority
        layout.addWidget(self.error_container)

        # Set a responsive minimum height for the scroll area
        screen_height = QDesktopWidget().availableGeometry().height()
        self.scroll_area.setMinimumHeight(min(int(screen_height * 0.15), 180))

    def show_error(self, message):
        self.error_message.setText(message)
        self.error_container.setVisible(True)

        # Hide the message after 5 seconds
        QTimer.singleShot(5000, lambda: self.error_container.setVisible(False))

    def load_imaging(self):
        try:
            # Get the list of imaging studies from the database
            conn = PatientModel().connect()
            cursor = conn.cursor()
            cursor.execute("SELECT imaging_code, imaging_name FROM imaging_catalog ORDER BY imaging_name")
            self.imaging = cursor.fetchall()
            conn.close()

            # Create the list for the autocompletion
            items = [f"{img[0]} - {img[1]}" for img in self.imaging]

            # Update the completer
            model = QStringListModel()
            model.setStringList(items)
            self.completer.setModel(model)

        except Exception as e:
            print(f"Error loading imaging studies: {str(e)}")
            self.imaging = []

    def add_imaging(self):
        text_value = self.search_input.text().strip()
        if not text_value:
            return

        # Look up whether the imaging study exists
        found = False
        for code, name in self.imaging:
            if text_value.startswith(code) or code in text_value or name.lower() in text_value.lower():
                found = True
                # Check that it has not been added already
                if not any(img[0] == code for img in self.selected_imaging):
                    self.selected_imaging.append([code, name])
                    self.create_tag(code, name)
                    self.search_input.clear()
                    # Focus the input to keep adding
                    self.search_input.setFocus()
                else:
                    self.show_error(f"The imaging study '{name}' has already been added")
                break

        if not found:
            self.show_error("The entered imaging study does not exist in the database.")

    def create_tag(self, code, name):
        # Create the widget for the tag with full width
        tag = QFrame()
        tag.setObjectName("imaging_tag")
        tag.setFixedHeight(40)  # Set a fixed height for every tag
        tag.setStyleSheet(f"""
            #imaging_tag {{
                background-color: {COLORS['background_header']};
                color: {COLORS['text_primary']};
                border: 1px solid #E0E0E0;
                border-radius: {BORDER_RADIUS['medium']};
                margin: 2px 0;
                width: 100%;
            }}
            #imaging_tag:hover {{
                background-color: #EDF5FF;
                border-color: #D0E0F0;
            }}
        """)

        # Horizontal layout for the tag with a better distribution
        tag_layout = QHBoxLayout(tag)
        tag_layout.setContentsMargins(12, 0, 8, 0)  # Reduce the vertical margin to fit the fixed height
        tag_layout.setSpacing(10)

        # Tag text with a better style
        text_label = QLabel(f"{code} - {name}")
        text_label.setWordWrap(True)
        text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text_label.setStyleSheet(f"""
            font-size: 14px;
            font-family: 'Segoe UI', sans-serif;
            color: {COLORS['text_primary']};
            background: transparent;
            padding: 2px 0;
        """)

        # Remove button with a better size and style - adjusted for vertical centering
        btn_remove = QPushButton("×")
        btn_remove.setObjectName("btn_remove_imaging")
        btn_remove.setCursor(Qt.PointingHandCursor)
        btn_remove.setFixedSize(22, 22)  # Slightly larger for an easier click
        btn_remove.setStyleSheet(f"""
            #btn_remove_imaging {{
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
            #btn_remove_imaging:hover {{
                background-color: #FF0000;
            }}
            #btn_remove_imaging:pressed {{
                background-color: #CC0000;
            }}
        """)

        # Connect the removal event
        btn_remove.clicked.connect(lambda: self.remove_tag(tag, code))

        # Add the elements to the layout
        tag_layout.addWidget(text_label, 1)
        tag_layout.addWidget(btn_remove, 0, Qt.AlignVCenter)

        # Add the tag to the container using insertWidget to place it at the top
        self.tags_layout.insertWidget(0, tag)  # Insert at the start so the last one added goes first

        # Adjust the minimum height according to the number of items
        self.adjust_minimum_height()

    def remove_tag(self, tag, code):
        # Remove the tag visually
        self.tags_layout.removeWidget(tag)
        tag.deleteLater()

        # Remove it from the selected list
        self.selected_imaging = [img for img in self.selected_imaging if img[0] != code]

        # Adjust the minimum height according to the number of items
        self.adjust_minimum_height()

    def clear_all_imaging(self):
        # Remove every visual tag
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Clear the selected list
        self.selected_imaging = []

        # Adjust the minimum height
        self.adjust_minimum_height()

    def adjust_minimum_height(self):
        # Adjust the minimum height of the scroll area to the content while keeping it proportional to the screen
        screen_height = QDesktopWidget().availableGeometry().height()
        base_height = min(int(screen_height * 0.15), 180)

        # We keep the base height to ensure consistency
        if self.tags_layout.count() > 0:
            # Compute the estimated height based on the number of items
            height_per_item = 44  # Estimated height per tag (40px + margin)
            content_height = min(self.tags_layout.count() * height_per_item, int(screen_height * 0.3))
            desired_height = max(base_height, content_height + 20)
            self.scroll_area.setMinimumHeight(desired_height)
        else:
            self.scroll_area.setMinimumHeight(base_height)

    def get_selected_imaging(self):
        return self.selected_imaging

    def set_selected_imaging(self, imaging):
        # Clear the current selection
        self.clear_all_imaging()

        # Add the new imaging studies
        for code, name in imaging:
            self.selected_imaging.append([code, name])
            self.create_tag(code, name)

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
