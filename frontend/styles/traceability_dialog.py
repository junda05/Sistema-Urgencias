from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                           QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QHeaderView,
                           QDesktopWidget, QFrame, QWidget, QProgressBar)
from PyQt5.QtCore import Qt, QSize, QThread, QObject, pyqtSignal, QTimer, QElapsedTimer
from PyQt5.QtGui import QIcon, QFont, QColor
import os
import sys
from frontend.styles.styles import COLORS, BORDER_RADIUS, SCROLLBAR_STYLE
from backend.database import AuditTrailModel

class TraceabilityDialogStyles:
    """Class that defines reusable styles for the audit trail dialog"""

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

    def __init__(self, parent=None, base_path=None):
        super().__init__(parent)

        # Configure paths
        if base_path:
            self.base_path = base_path
        else:
            if getattr(sys, 'frozen', False):
                self.base_path = sys._MEIPASS
            else:
                self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        self.setWindowTitle("Action audit trail")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Apply the styles and a transparent background
        self.setStyleSheet(TraceabilityDialogStyles.get_main_style())

        self.setup_ui()

        # Start loading the data asynchronously so the interface is not blocked
        QTimer.singleShot(100, self.show_spinner_and_load_data)

        # Initialize the list used to keep track of the threads
        self.threads = []

        # Timer used to throttle the search frequency (avoid excessive searches)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_deferred_search)

        # Store the search terms for the word-based search
        self.search_terms = []

        # Counter for the progress bar animation
        self.progress_value = 0
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress_bar)

    def setup_ui(self):
        # Main container with a rounded border
        self.main_container = QFrame(self)
        self.main_container.setObjectName("main_container")
        self.main_container.setStyleSheet(f"""
            #main_container {{
                background-color: {COLORS['background_primary']};
                border-radius: 10px;
                border: 1px solid {COLORS['border_light']};
            }}
        """)

        # Main layout
        self.layout = QVBoxLayout(self.main_container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Header with title and close button - fix the positioning
        self.header_container = QWidget()
        self.header_layout = QHBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        # Make the header background transparent
        self.header_container.setStyleSheet(f"""
            background-color: {COLORS['background_primary']};""")

        # Title
        self.title_label = QLabel("Action audit trail")
        self.title_label.setObjectName("title")

        # Close button - use a container to position it correctly
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

        # Adjust the header layout so the button stays fixed
        self.header_layout.addWidget(self.title_label, 1, Qt.AlignLeft)  # 1 means it will stretch
        self.header_layout.addWidget(self.close_button_container, 0, Qt.AlignRight | Qt.AlignTop)  # 0 means it will not stretch

        # Separator
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.separator.setStyleSheet(f"""
            background-color: {COLORS['background_transparent']};
            max-height: 1px;
        """)

        # Audit trail table - created first so its font size can be reused
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # Increased to 6 columns to include the user's name
        self.table.setHorizontalHeaderLabels([
            "Name", "Username", "Action Performed",
            "Date and Time", "Affected Patient", "Change Details"
        ])

        # Configure the table with styles
        self.table.setStyleSheet(TraceabilityDialogStyles.get_table_style())
        self.table.horizontalHeader().setStretchLastSection(False) # Changed to False to use fixed widths
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        # Get the table font size to use it in the filter elements
        table_font = self.table.font()
        table_font_size = table_font.pointSize()

        # Apply the same font size to the headers as to the table content
        header_font = QFont(table_font)
        header_font.setBold(True)  # Keep it bold
        self.table.horizontalHeader().setFont(header_font)

        # Filters - improve the positioning with a fixed-width container
        self.filters_container = QWidget()
        self.filters_container.setStyleSheet(f"""
            background-color: {COLORS['background_primary']};
            border: none;
        """)
        self.filters_layout = QHBoxLayout(self.filters_container)
        self.filters_layout.setContentsMargins(0, 0, 0, 0)
        self.filters_layout.setSpacing(10)  # Reduce the spacing for better alignment

        # Search field - apply the same font size as the table
        self.search_input = QLineEdit()
        self.search_input.setObjectName("search")
        self.search_input.setPlaceholderText("Search by username, full name or patient...")
        self.search_input.setFont(table_font)
        self.search_input.setStyleSheet(f"""
            background-color: {COLORS['background_white']};
            font-size: {table_font_size}pt;
            min-width: 200px;
            border: 1px solid {COLORS['border_light']};
            border-radius: {BORDER_RADIUS['medium']};
            padding: 8px 12px;
        """)

        # Role filter combo - MODIFIED TO REMOVE VISITOR
        self.role_filter = QComboBox()
        self.role_filter.addItems(["All", "Administrator", "Doctor"])  # We remove "Visitor"
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
                image: url("{os.path.join(self.base_path, 'frontend', 'images', 'dropdown_arrow.png').replace(os.sep, '/')}");
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

        # We removed the search button because it now filters automatically

        self.filters_layout.addWidget(self.search_input, 3)
        self.filters_layout.addWidget(self.role_filter, 2)

        # Configure fixed column widths
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)

        # Configure the columns with specific widths
        screen_width = QDesktopWidget().screenGeometry().width()
        total_width = int(screen_width * 0.8) - 40  # 80% of the screen width minus the margins

        # Define proportional column widths
        self.table.setColumnWidth(0, int(total_width * 0.15))  # Name
        self.table.setColumnWidth(1, int(total_width * 0.10))  # Username
        self.table.setColumnWidth(2, int(total_width * 0.15))  # Action Performed
        self.table.setColumnWidth(3, int(total_width * 0.15))  # Date and Time
        self.table.setColumnWidth(4, int(total_width * 0.15))  # Affected Patient

        # Details column with text wrapping
        self.table.setColumnWidth(5, int(total_width * 0.30))  # Change Details

        # Close button
        self.footer_container = QWidget()
        self.footer_layout = QHBoxLayout(self.footer_container)
        self.footer_layout.setContentsMargins(0, 0, 0, 0)
        self.footer_layout.addStretch()
        self.footer_container.setStyleSheet("""
            background-color: transparent;
            border: none;
        """)

        self.btn_close = QPushButton("Close")
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

        # Initially hide the table (we will show it when there is data)
        self.table.hide()

        # Improve the spinner container style - make the background transparent
        self.spinner_container = QWidget()
        self.spinner_container.setStyleSheet(f"""
            background-color: transparent;
            border-radius: 10px;
            border: none;
        """)
        self.spinner_layout = QVBoxLayout(self.spinner_container)
        self.spinner_layout.setAlignment(Qt.AlignCenter)
        self.spinner_layout.setSpacing(20)

        # Create a label for the loading message with an improved style
        self.spinner_label = QLabel("Loading audit trail data...")
        self.spinner_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 18px;
            font-weight: bold;
            padding: 20px;
            background-color: {COLORS['background_transparent']};
            border-radius: 10px;
        """)
        self.spinner_label.setAlignment(Qt.AlignCenter)

        # Create an animated loader with an improved style
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)  # Smaller height for a modern look
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

        # Add a small explanatory secondary text
        self.spinner_subtitle = QLabel("Please wait while the activity records are retrieved...")
        self.spinner_subtitle.setStyleSheet(f"""
            color: {COLORS['text_light']};
            font-size: 14px;
            font-style: italic;
            background-color: {COLORS['background_transparent']};
        """)
        self.spinner_subtitle.setAlignment(Qt.AlignCenter)
        self.spinner_subtitle.setWordWrap(True)

        # Add the elements to the spinner
        self.spinner_layout.addWidget(self.spinner_label)
        self.spinner_layout.addWidget(self.progress_bar)
        self.spinner_layout.addWidget(self.spinner_subtitle)

        # The spinner takes up all the available space
        self.spinner_container.setMinimumSize(500, 200)
        # Reduce the spinner size so it does not take up so much vertical space
        self.spinner_container.setMaximumSize(550, 250)
        self.spinner_container.setStyleSheet(f"""
            background-color: {COLORS['background_header']};
            border-radius: 10px;
            """)

        # Create a container for the table and the spinner that will use a stack layout
        self.content_container = QWidget()
        self.content_container.setStyleSheet(f"""
            background-color: {COLORS['background_transparent']};""")
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # Add the table to the content container
        self.content_layout.addWidget(self.table)

        # Add the spinner container to the content container
        # The spinner container will float above the table
        self.spinner_container.setParent(self.content_container)
        self.spinner_container.hide()  # Initially hidden

        # Add the widgets to the main layout
        self.layout.addWidget(self.header_container)
        self.layout.addWidget(self.separator)
        self.layout.addWidget(self.filters_container)
        self.layout.addWidget(self.content_container, 1)  # 1 is so it expands
        self.layout.addWidget(self.footer_container)

        # General layout for the dialog
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(self.main_container)

        # Configure the size and center it on the screen
        self.resize_dialog()
        self.center_dialog()

        # Connect events
        self.search_input.textChanged.connect(self.start_deferred_search)
        self.role_filter.currentIndexChanged.connect(self.filter_data)
        self.table.horizontalHeader().sectionClicked.connect(self.sort_column)

    def start_deferred_search(self):
        """Starts a timer to run the search after a short delay"""
        # Cancel any pending search
        self.search_timer.stop()
        # Start a new timer (300ms is a good balance between responsiveness and performance)
        self.search_timer.start(300)

    def update_table_with_results(self, data):
        """Updates the table with the data received from the worker"""
        # Hide the spinner
        self.spinner_container.hide()

        # Show the table
        self.table.show()

        # Show the data in the table
        self.show_data_in_table(data)

    def perform_deferred_search(self):
        """Processes the search text and runs the search"""
        # Get the search text and split it into words
        search_text = self.search_input.text().strip()

        if search_text:
            # Split by spaces and filter out empty words
            self.search_terms = [term.lower() for term in search_text.split() if term.strip()]
            # Limit to a maximum of 4 words
            self.search_terms = self.search_terms[:4]
        else:
            self.search_terms = []

        # Run the search
        self.filter_data()

    def show_spinner_and_load_data(self):
        """Shows the spinner and loads the data in a separate thread"""
        # Show the spinner and position it above the table
        self.spinner_container.show()
        self.spinner_container.raise_()  # Make sure it is above the table

        # Center the spinner inside the parent container
        spinner_x = (self.content_container.width() - self.spinner_container.width()) // 2
        spinner_y = (self.content_container.height() - self.spinner_container.height()) // 2
        self.spinner_container.move(spinner_x, spinner_y)

        # Configure the animated progress bar - make sure it starts at 0
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_value = 0

        # Start the animation timer with a longer interval for a slower progression
        self.progress_timer.start(70)  # Increased from 50ms to 70ms for a slower animation

        # Create a thread to load the data
        self.thread = QThread()
        self.worker = DataWorker()
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_real_progress)
        self.worker.finished.connect(self.update_table_with_results)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(lambda: self.progress_timer.stop())
        self.thread.finished.connect(self.thread.deleteLater)

        # Keep a reference to the thread to prevent it from being deleted prematurely
        self.threads.append(self.thread)

        # Start the thread
        self.thread.start()

    def update_progress_bar(self):
        """Updates the progress bar with a smooth animation"""
        # Increase the value smoothly and gradually with smaller increments at the start
        if self.progress_value < 90:  # Limited to 90% for the simulation
            # Use a smaller increment at the start to show gradual progress
            if self.progress_value < 20:
                increment = 0.5  # Very small increment at the start
            elif self.progress_value < 40:
                increment = 0.8  # Slightly larger increment
            elif self.progress_value < 60:
                increment = 1.0  # Moderate increment
            else:
                # Smooth acceleration towards the end
                increment = max(0.5, (90 - self.progress_value) / 30)

            self.progress_value = min(90, self.progress_value + increment)
            self.progress_bar.setValue(int(self.progress_value))

    def update_real_progress(self, value):
        """Updates the bar with the real progress reported by the worker"""
        if value <= 100:
            self.progress_value = value
            self.progress_bar.setValue(value)

    def sort_column(self, column_index):
        """Sorts the table by the selected column"""
        # Get the current sort direction
        current_order = self.table.horizontalHeader().sortIndicatorOrder()

        # Invert the direction for the next click
        new_order = Qt.DescendingOrder if current_order == Qt.AscendingOrder else Qt.AscendingOrder

        # Sort the table
        self.table.sortItems(column_index, new_order)

    def resize_dialog(self):
        """Adjusts the dialog size according to the screen size"""
        screen = QDesktopWidget().availableGeometry()
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.8)
        self.resize(width, height)

    def center_dialog(self):
        """Centers the dialog on the screen"""
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def load_data(self):
        """Loads the audit trail data from the database"""
        try:
            # Use the audit trail model to get the data
            data = AuditTrailModel.get_actions()
            self.show_data_in_table(data)

        except Exception as e:
            print(f"Error loading audit trail data: {str(e)}")

    def get_username(self, username):
        """Gets the full name of the user from the database"""
        try:
            from backend.users.users_model import UsersModel

            # Connect to the database
            conn = UsersModel.connect_db()
            if not conn:
                return username  # If it cannot connect, return the username as a fallback

            cursor = conn.cursor()

            # Query the user's name
            cursor.execute("""
                SELECT full_name FROM users
                WHERE username = %s
            """, (username,))

            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                return result[0]
            else:
                return "System User"  # Generic name if no registered name exists

        except Exception as e:
            print(f"Error getting the user name: {str(e)}")
            return username  # In case of error, use the username as a fallback

    def check_user_active(self, username):
        """
        Checks whether a user is active in the database

        Args:
            username: Name of the user to check

        Returns:
            bool: True if the user is active, False if inactive or nonexistent
        """
        try:
            from backend.users.users_model import UsersModel

            # Connect to the database
            conn = UsersModel.connect_db()
            if not conn:
                return True  # If there is a connection error, we assume active by default

            cursor = conn.cursor()

            # Query the user's status
            cursor.execute("""
                SELECT status FROM users
                WHERE username = %s
            """, (username,))

            result = cursor.fetchone()
            conn.close()

            # If there is no result or the status is not 'active', return False
            if not result or result[0] != 'active':
                return False

            return True

        except Exception as e:
            print(f"Error checking the user status: {str(e)}")
            return True  # In case of error, we assume it is active

    def show_data_in_table(self, data):
        """Shows the data in the audit trail table"""
        # Clear the table
        self.table.setRowCount(0)

        if not data:
            return

        # Configure the number of rows
        self.table.setRowCount(len(data))

        # Import UsersModel to get the roles correctly
        from backend.users.users_model import UsersModel

        # Fill the table with the data
        for i, row in enumerate(data):
            # Columns to display
            columns = [0, 2, 3, 4, 5]  # Original indices from the database

            # Add the user name (extra column at the start)
            username = row[0] if len(row) > 0 and row[0] is not None else ""
            full_name = self.get_username(username)

            # Check whether the user is active
            is_active = self.check_user_active(username)

            # Get the user's role to apply the correct formatting
            role = UsersModel.get_user_role(username)

            # Create the item for the name
            name_item = QTableWidgetItem(full_name)
            name_item.setTextAlignment(Qt.AlignCenter)

            # Apply a strikethrough if the user is not active, with a color based on the role
            if not is_active:
                font = name_item.font()
                font.setStrikeOut(True)
                font.setWeight(QFont.Bold)  # Make the font heavier so the strikethrough is more visible
                name_item.setFont(font)

                # Strikethrough colors based on the role
                if role == 'admin':
                    name_item.setForeground(QColor("#4A7296"))  # Corporate blue for administrators
                elif role == 'doctor':
                    name_item.setForeground(QColor("#28a745"))  # Doctor green
                else:
                    name_item.setForeground(QColor("#fd7e14"))  # Orange for visitor/other

            self.table.setItem(i, 0, name_item)

            # Process the rest of the columns with a +1 offset in j
            for j, column_idx in enumerate(columns):
                table_col = j + 1  # +1 because column 0 is now the name

                if column_idx >= len(row) or row[column_idx] is None:
                    item = QTableWidgetItem("-")
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    value = row[column_idx]
                    item = QTableWidgetItem(str(value))

                    # Apply specific colors and formats per column
                    if j == 0:  # Username column (now column 1 in the table)
                        item.setTextAlignment(Qt.AlignCenter)

                        # Get the username in order to query its role
                        username = str(value)

                        # If the user is not active, strike through the username too, with a color based on the role
                        if not is_active:
                            font = item.font()
                            font.setStrikeOut(True)
                            # Make the font heavier so the strikethrough is more visible
                            font.setWeight(QFont.Bold)
                            item.setFont(font)

                            # Strikethrough colors based on the role
                            if role == 'admin':
                                item.setForeground(QColor("#4A7296"))  # Corporate blue for administrators
                            elif role == 'doctor':
                                item.setForeground(QColor("#28a745"))  # Doctor green
                            else:
                                item.setForeground(QColor("#fd7e14"))  # Gray by default

                        # Use UsersModel.get_user_role directly

                        # Apply colors based on the role
                        if role == 'admin':
                            if is_active:  # Only apply the color if active
                                item.setForeground(QColor("#4A7296"))  # Corporate blue for administrators
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)

                            # Also apply the formatting to the name
                            if is_active:  # Only apply the color if active
                                name_item.setForeground(QColor("#4A7296"))
                            name_font = name_item.font()
                            name_font.setBold(True)
                            name_item.setFont(name_font)

                        elif role == 'doctor':
                            if is_active:  # Only apply the color if active
                                item.setForeground(QColor("#28a745"))  # Doctor green
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)

                            # Also apply the formatting to the name
                            if is_active:  # Only apply the color if active
                                name_item.setForeground(QColor("#28a745"))
                            name_font = name_item.font()
                            name_font.setBold(True)
                            name_item.setFont(name_font)
                        else:
                            if is_active:  # Only apply the color if active
                                item.setForeground(QColor("#fd7e14"))  # Orange for visitors
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)

                            # Also apply the formatting to the name
                            if is_active:  # Only apply the color if active
                                name_item.setForeground(QColor("#fd7e14"))
                            name_font = name_item.font()
                            name_font.setBold(True)
                            name_item.setFont(name_font)

                    # Date and time
                    elif j == 2:  # Date column (now column 3)
                        item.setTextAlignment(Qt.AlignCenter)

                    # Action performed
                    elif j == 1:  # Action column (now column 2)
                        item.setTextAlignment(Qt.AlignCenter)

                    # Details column - enable word wrap
                    elif j == 4:  # Details column (now column 5)
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)

                self.table.setItem(i, table_col, item)

            # Adjust the row height according to the content of the details column
            self.table.resizeRowToContents(i)

    def filter_data(self):
        """Filters the data according to the search criteria"""
        # Show the spinner and position it above the table
        self.spinner_container.show()
        self.spinner_container.raise_()  # Make sure it is above the table

        # Center the spinner inside the parent container
        spinner_x = (self.content_container.width() - self.spinner_container.width()) // 2
        spinner_y = (self.content_container.height() - self.spinner_container.height()) // 2
        self.spinner_container.move(spinner_x, spinner_y)

        # Configure the animated progress bar - make sure it starts at 0
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_value = 0

        # Start the animation timer with a longer interval
        self.progress_timer.start(70)  # Increased from 50ms to 70ms for a slower animation

        # Get the filtering criteria
        role_filter_value = self.role_filter.currentText()

        # Create a worker for the filtering
        self.filter_thread = QThread()
        self.filter_worker = FilterWorker(self.search_terms, role_filter_value)
        self.filter_worker.moveToThread(self.filter_thread)

        # Connect signals
        self.filter_thread.started.connect(self.filter_worker.run)
        self.filter_worker.progress.connect(self.update_real_progress)
        self.filter_worker.finished.connect(self.update_table_with_results)
        self.filter_worker.finished.connect(self.filter_thread.quit)
        self.filter_worker.finished.connect(self.filter_worker.deleteLater)
        self.filter_worker.finished.connect(lambda: self.progress_timer.stop())
        self.filter_thread.finished.connect(self.filter_thread.deleteLater)

        # Keep a reference to the thread to prevent it from being deleted prematurely
        self.threads.append(self.filter_thread)

        # Start the thread
        self.filter_thread.start()

    def closeEvent(self, event):
        """Handles the dialog close event, making sure the threads stop correctly"""
        try:
            # Create a copy of the thread list to avoid modifying it while iterating
            threads_copy = self.threads.copy() if hasattr(self, 'threads') else []

            for thread in threads_copy:
                try:
                    # Check whether the thread still exists and is valid before trying to use it
                    if thread is not None and hasattr(thread, 'isRunning') and thread.isRunning():
                        thread.quit()
                        success = thread.wait(500)  # Wait at most 500ms so the interface is not blocked

                        # If it is still running and still valid, terminate it forcefully
                        if not success and hasattr(thread, 'isRunning') and thread.isRunning():
                            thread.terminate()
                except RuntimeError:
                    # Ignore errors if the object was already deleted
                    pass
                except Exception as e:
                    print(f"Error closing an individual thread: {str(e)}")

            # Clear the thread list
            if hasattr(self, 'threads'):
                self.threads.clear()

        except Exception as e:
            print(f"General error in closeEvent: {str(e)}")

        # Continue with the normal close event
        super().closeEvent(event)

# Worker class modified to filter by the role of the user who performed the action
class FilterWorker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)

    def __init__(self, search_terms=None, role_filter=None):
        super().__init__()
        self.search_terms = search_terms or []
        self.role_filter = role_filter

    def run(self):
        """Filters the data in the background"""
        try:
            # Emit the initial progress
            self.progress.emit(10)

            # Use the audit trail model to filter the data
            # Important: role_filter now filters by the role of the user who performed the action
            data = AuditTrailModel.get_actions(
                search_terms=self.search_terms,
                user_role_filter=self.role_filter if self.role_filter != "All" else None,
                limit=500  # Increase the limit to show more relevant results
            )

            # Emit the middle progress
            self.progress.emit(50)

            # Convert tuples to lists for compatibility with the signal
            if isinstance(data, tuple):
                data_list = [list(row) if isinstance(row, tuple) else row for row in data]

                # Emit the almost complete progress
                self.progress.emit(90)
                self.finished.emit(data_list)
            else:
                # Emit the almost complete progress
                self.progress.emit(90)
                self.finished.emit(data)

            # Emit the complete progress
            self.progress.emit(100)

        except Exception as e:
            print(f"Error filtering audit trail data: {str(e)}")
            self.progress.emit(100)
            self.finished.emit([])


# Worker class used to load the data in the background
class DataWorker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)

    def run(self):
        """Loads the audit trail data in the background"""
        try:
            # Emit the initial progress
            self.progress.emit(10)

            # Simulate progress intervals to give visual feedback
            timer = QElapsedTimer()
            timer.start()

            # Use the audit trail model to get the data
            data = AuditTrailModel.get_actions(limit=500)  # Increase the limit but with pagination

            # Compute the elapsed time for statistics
            elapsed = timer.elapsed()
            print(f"Data loading time: {elapsed} ms")

            # Emit the middle progress
            self.progress.emit(50)

            # Convert tuples to lists for compatibility with the signal
            if isinstance(data, tuple):
                data_list = [list(row) if isinstance(row, tuple) else row for row in data]

                # Emit the almost complete progress
                self.progress.emit(90)
                self.finished.emit(data_list)
            else:
                # Emit the almost complete progress
                self.progress.emit(90)
                self.finished.emit(data)

            # Emit the complete progress
            self.progress.emit(100)

        except Exception as e:
            print(f"Error loading audit trail data: {str(e)}")
            self.progress.emit(100)
            self.finished.emit([])
