import sys
import os
import pymysql
import configparser
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
                             QMessageBox, QDesktopWidget, QDialog, QFormLayout,
                             QProgressBar, QGraphicsOpacityEffect, QGraphicsDropShadowEffect,
                             QSizePolicy)
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor, QIcon, QLinearGradient, QBrush
from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal, QPoint, QRect
from PIL import Image, ImageFilter
from backend.database import ConfigurationModel, AuthenticationModel
# Import styles and components
from frontend.styles.styles import *
from frontend.styles.components import StyledMessageBox, StyledButton, StyledDialog, FormField
# Import animation components
from frontend.styles.animation_components import SplashScreen, FadeAnimation, WorkerThread
# Import font utilities
from frontend.styles.font_utils import apply_system_fonts
from frontend.styles.styles import COLORS, BORDER_RADIUS, PADDING, FONT_SIZE
# Import custom button components
from frontend.styles.custom_buttons import IconButton

# Define functions to show styled messages
def show_error_message(parent, title, message):
    """Shows a styled error message"""
    msg_box = StyledMessageBox(parent, title, message, QMessageBox.Critical, "error")

    # Create styled OK button
    btn_ok = QPushButton("OK")
    btn_ok.setCursor(Qt.PointingHandCursor)

    msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
    msg_box.setDefaultButton(btn_ok)

    return msg_box.exec_()

def show_warning_message(parent, title, message):
    """Shows a styled warning message"""
    msg_box = StyledMessageBox(parent, title, message, QMessageBox.Warning, "warning")

    # Create styled OK button
    btn_ok = QPushButton("OK")
    btn_ok.setCursor(Qt.PointingHandCursor)

    msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
    msg_box.setDefaultButton(btn_ok)

    return msg_box.exec_()

def show_information_message(parent, title, message):
    """Shows a styled informational message"""
    msg_box = StyledMessageBox(parent, title, message, QMessageBox.Information, "info")
    btn_ok = QPushButton("OK")

    # Create styled OK button
    btn_ok.setCursor(Qt.PointingHandCursor)

    msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
    msg_box.setDefaultButton(btn_ok)

    return msg_box.exec_()

class ConfigDialog(StyledDialog):
    def __init__(self, parent=None):
        super().__init__("Connection Settings", 450, parent)

        # Get the current configuration
        self.config_path = ConfigurationModel.get_config_path()
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            self.config['DATABASE'] = {'host': 'localhost'}

        # Add title and description
        self.add_title("Server Configuration")

        description = QLabel("Change the server address used for the database connection.")
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: {COLORS['background_transparent']};")
        self.layout.addWidget(description)
        self.layout.addSpacing(10)  # Spacer

        # Create a form
        form_layout = self.add_form()

        # Server field
        label, self.server_input = FormField.create_line_edit(
            "Server:",
            True,
            False,
            self.config.get('DATABASE', 'host', fallback='localhost')
        )
        form_layout.addRow(label, self.server_input)

        self.layout.addSpacing(10)  # Spacer

        # Buttons
        buttons = [
            ("Save", self.save_configuration, "primary"),
            ("Cancel", self.reject, "danger")
        ]

        self.add_button_row(buttons)

    def save_configuration(self):
        new_host = self.server_input.text().strip()

        if not new_host:
            show_warning_message(self, "Invalid Data", "The server cannot be empty.")
            return

        # Save the configuration using the model
        success, message = ConfigurationModel.save_configuration(new_host)

        if success:
            show_information_message(self, "Settings Saved",
                                   "The settings have been saved successfully.\n"
                                   "The changes will be applied the next time you log in.")
            self.accept()
        else:
            show_error_message(self, "Error", f"The settings could not be saved: {message}")

class LoginInterface(QMainWindow):
    _instance = None

    @classmethod
    def create_instance(cls):
        if not QApplication.instance():
            application = QApplication(sys.argv)

            # Apply custom fonts immediately
            apply_system_fonts()

            # Show the splash screen when the application starts, with a responsive size
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            images_path = os.path.join(base_path, "frontend", "images")
            logo_path = os.path.join(images_path, "logo.png")

            # Get the screen size to make the splash screen responsive
            screen = QDesktopWidget().screenGeometry()

            splash = SplashScreen(None, logo_path=logo_path, message="Starting application...", duration=2)
            splash.setFixedSize(int(screen.width() * 0.3), int(screen.height() * 0.3))
            splash.show()
            QApplication.processEvents()

            application.setWindowIcon(QIcon(os.path.join(images_path, "logo.png")))
            splash.exec_()
        else:
            application = QApplication.instance()

        if not cls._instance:
            cls._instance = cls()

        return cls._instance, application

    def __init__(self):
        super().__init__()
        # Apply fonts when the interface starts
        apply_system_fonts()

        # Remove the title bar
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Load the configuration using the model
        self.load_configuration()

        if getattr(sys, 'frozen', False):
            images_path = os.path.join(self.base_path, "frontend", "images")
        else:
            images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")

        self.logo_path = os.path.join(images_path, "logo.png")
        # We use the .png extension for the application icon
        self.icon_path = os.path.join(images_path, "logo.png")
        self.secondary_logo_path = os.path.join(images_path, "secondary_logo.png")
        print(f"Looking for the logo at: {self.logo_path}")
        print(f"Looking for the icon at: {self.icon_path}")

        # Set the window icon
        if os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))
            # Also set the application icon
            if QApplication.instance() is not None:
                QApplication.instance().setWindowIcon(QIcon(self.icon_path))

        self.initUI()

        # Variables used to move the window without a title bar
        self.dragging = False
        self.offset = None

    def load_configuration(self):
        """Loads the configuration using the configuration model"""
        try:
            # Load the configuration using the model
            host = ConfigurationModel.load_configuration()
            # Set the server in the authentication model
            AuthenticationModel.set_server(host)
        except Exception as e:
            show_warning_message(
                self,
                "Configuration error",
                f"The configuration could not be loaded: {str(e)}\nDefault values will be used."
            )
            AuthenticationModel.set_server('localhost')

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

    def start(self):
        self.show()
        return QApplication.instance().exec_()

    def create_title_bar(self):
        title_bar = QWidget()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet(f"background-color: {COLORS['background_header']};")

        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 10, 0)
        title_bar_layout.setSpacing(5)
        title_bar_layout.addStretch()  # Expanding space on the left

        # Create the window control buttons
        buttons = [
            ("🗕", self.showMinimized, False),  # Minimize
            ("🗗", self.toggle_maximized, False),  # Maximize/Restore
            ("✖", self.close, True)  # Close
        ]

        for text, function, is_close_button in buttons:
            button = StyledButton(text, "window_control", is_close=is_close_button)
            button.setFixedSize(30, 30)
            button.clicked.connect(function)
            title_bar_layout.addWidget(button)

        return title_bar

    def initUI(self):
        self.setWindowTitle("Urgentix")
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, screen.width(), screen.height())
        self.showMaximized()

        # Background with a soft gradient
        central_widget = QWidget()
        palette = QPalette()
        gradient = QLinearGradient(0, 0, 0, screen.height())
        gradient.setColorAt(0, QColor(90, 140, 190))  # Lighter blue at the top
        gradient.setColorAt(1, QColor(74, 114, 150))  # Slightly darker blue at the bottom
        palette.setBrush(QPalette.Window, QBrush(gradient))
        central_widget.setAutoFillBackground(True)
        central_widget.setPalette(palette)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        screen_width = screen.width()
        screen_height = screen.height()

        try:
            logo_container = QLabel(central_widget)
            # Logo adjustments
            logo_height = int(screen_height * 0.14)  # 10% of the screen height
            logo_width = int(screen_width * 0.2)  # 20% of the screen width
            logo_container.setStyleSheet(f"background-color: {COLORS['background_header']};")
            logo_container.move(0, 0)

            if os.path.exists(self.logo_path):
                logo_pixmap = QPixmap(self.logo_path)
                logo_label = QLabel(central_widget)
                scaled_logo = logo_pixmap.scaled(
                    logo_width,
                    logo_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                logo_label.setPixmap(scaled_logo)
                logo_container.setFixedSize(screen.width(), scaled_logo.height())
                logo_label.setFixedSize(scaled_logo.size())
                logo_label.setStyleSheet(f"background: {COLORS['background_transparent']};")

            # Add the secondary logo below the title bar buttons
            if os.path.exists(self.secondary_logo_path):
                # Reduce the size to make sure it fits in the available space
                secondary_logo_height = int(screen_height * 0.1)  # Reduced from 0.08
                secondary_logo_width = int(screen_width * 0.15)  # Reduced from 0.12

                secondary_logo_label = QLabel(central_widget)
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

                # Adjusted placement - use absolute coordinates that we know will work
                # Place it in the top right corner, just below the button area
                secondary_logo_label.move(
                    screen_width - secondary_logo_width + int(secondary_logo_width*0.25),  # 15px right margin
                    int(secondary_logo_height*0.3)  # Fixed Y position below the control buttons (typically 30px tall)
                )

                # Make sure it is visible
                secondary_logo_label.raise_()  # Bring to front
                secondary_logo_label.show()

        except Exception as e:
            show_error_message(self, "Error",
                f"Error while setting up the paths: {str(e)}\n\n"
                f"Please make sure the 'images' folder is in:\n{self.base_path}")

        # Calculate proportional dimensions
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        # Calculate the container size as a percentage of the screen
        container_width = int(screen_width * 0.285)  # % of the screen width
        container_height = int(screen_height * 0.60)   # % of the screen height - reduced because we removed a field

        title_size = int(container_height * 0.08)
        label_size = int(container_height * 0.035)
        input_size = int(container_height * 0.031)

        # Adjust login_container
        login_container = QWidget(central_widget)
        login_container.setFixedWidth(container_width)
        login_container.setFixedHeight(container_height)
        login_container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background_header']};
                border-radius: {BORDER_RADIUS['xlarge']};
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
        """)

        login_container.setGeometry(
            (screen_width - container_width) // 2,  # Horizontally centered
            ((screen_height - container_height) // 2) + int(screen_height * 0.033),   # Vertically centered, shifted upwards
            container_width,
            container_height
        )

        login_layout = QVBoxLayout(login_container)
        login_layout.setContentsMargins(
            int(container_width * 0.05),  # side margins
            int(container_height * 0.05),   # top and bottom margins
            int(container_width * 0.05),
            int(container_height * 0.05)
        )
        login_layout.setSpacing(int(container_height * 0.03))

        title = QLabel("Log in")
        title.setStyleSheet(f"""
            background-color: {COLORS['background_transparent']};
            color: {COLORS['text_primary']};
            font-size: {title_size}px;
            margin: {int(container_height * 0.02)}px 0;
            border: none;
        """)
        title.setFont(QFont("ABeeZee"))
        title.setAlignment(Qt.AlignCenter)
        login_layout.addWidget(title)
        login_layout.addSpacing(int(container_height*0.02))  # Increased spacing

        # Username
        user_label = QLabel("Username")
        user_label.setFont(QFont("ABeeZee"))
        user_label.setStyleSheet(f"""
            background-color: {COLORS['background_transparent']};
            font-size: {label_size}px;
            border: none;
        """)
        login_layout.addWidget(user_label)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        # Ensure consistent styling with password field by using FONT_SIZE['medium']
        self.user_input.setStyleSheet(f"""
            padding: {PADDING['medium']};
            border: 2px solid {COLORS['background_transparent']};
            border-radius: {BORDER_RADIUS['xlarge']};
            background-color: #FCFCFC;
            margin: 5px;
            min-height: {int(container_height * 0.06)}px;
            font-size: {FONT_SIZE['medium']};
        """)
        login_layout.addWidget(self.user_input)

        # Error label for the username field
        self.user_error = QLabel("")
        self.user_error.setStyleSheet(f"""
            color: {COLORS['button_danger']};
            font-size: {int(label_size * 0.8)}px;
            background-color: {COLORS['background_transparent']};
            border: 2px solid {COLORS['background_transparent']};
            padding-left: 10px;
            font-weight: bold;
        """)
        self.user_error.setVisible(False)
        login_layout.addWidget(self.user_error)

        login_layout.addSpacing(int(container_height*0.02))  # Increased spacing

        # Password
        password_label = QLabel("Password")
        password_label.setFont(QFont("ABeeZee"))
        password_label.setStyleSheet(f"""
            background-color: {COLORS['background_transparent']};
            font-size: {label_size}px;
            border: none;
        """)
        login_layout.addWidget(password_label)

        self.password_input = PasswordInput()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(int(container_height * 0.08))
        # Pass font size to PasswordInput
        self.password_input.password_field.setStyleSheet(f"""
            border: none;
            background-color: {COLORS['background_transparent']};
            padding: {PADDING['medium']};
            font-size: {FONT_SIZE['medium']};
        """)

        password_widget = QWidget()
        password_widget.setStyleSheet(f"""
            padding: {PADDING['medium']};
            border: 2px solid {COLORS['background_transparent']};
            border-radius: {BORDER_RADIUS['xlarge']};
            background-color: #FCFCFC;
            margin: 5px;
            min-height: {int(container_height * 0.06)}px;
            font-size: {input_size}px;
        """)
        password_layout = QHBoxLayout(password_widget)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.addWidget(self.password_input)
        login_layout.addWidget(password_widget)

        # Error label for the password field
        self.password_error = QLabel("")
        self.password_error.setStyleSheet(f"""
            color: {COLORS['button_danger']};
            font-size: {int(label_size * 0.8)}px;
            background-color: {COLORS['background_transparent']};
            border: 2px solid {COLORS['background_transparent']};
            padding-left: 10px;
            font-weight: bold;
        """)
        self.password_error.setVisible(False)
        login_layout.addWidget(self.password_error)

        login_layout.addSpacing(int(container_height*0.05))  # Increased spacing

        # Log in button
        login_button = StyledButton("Log In", "primary")
        login_button.setFixedSize(
            int(container_width * 0.5),  # width
            int(container_height * 0.08)    # height
        )
        login_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['button_primary']};
                color: {COLORS['text_white']};
                border: none;
                border-radius: {BORDER_RADIUS['xlarge']};
                font-size: {FONT_SIZE['xxlarge']};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['button_primary_hover']};
            }}
        """)

        login_button.clicked.connect(self.validate_credentials)
        login_layout.addWidget(login_button, alignment=Qt.AlignCenter)

        login_layout.addStretch()  # Add stretch to push content up and leave space at bottom

        # Custom title bar
        title_bar = self.create_title_bar()
        main_layout.addWidget(title_bar, alignment=Qt.AlignRight | Qt.AlignTop)

        # Create the bottom bar for the server label and the settings button
        bottom_bar = QWidget()
        bottom_bar.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        bottom_bar_layout = QHBoxLayout(bottom_bar)
        bottom_bar_layout.setContentsMargins(20, 5, 20, 10)
        bottom_bar_layout.setSpacing(10)

        # Path to the server icon
        server_icon_path = os.path.join(self.base_path, "frontend", "images", "server.png")

        # Create the settings button using IconButton for better visual consistency
        config_button = IconButton("Settings",
                                server_icon_path if os.path.exists(server_icon_path) else None,
                                COLORS['background_transparent'],  # Transparent background
                                "rgba(255, 255, 255, 0.1)")  # Subtle hover effect

        # Adjust the button size so it is responsive but with a limited width
        config_button.setFixedHeight(int(screen_height * 0.05))  # 5% of the screen height
        config_button.setFixedWidth(int(screen_width * 0.12))  # 12% of the screen width as a fixed width

        # Override some styles so it matches the server label
        config_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['background_transparent']};
                color: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: {BORDER_RADIUS['medium']};
                padding: 8px 12px;
                font-size: {int(label_size * 0.9)}px;
                text-align: left;
                vertical-align: middle;
            }}
            QPushButton:hover {{
                color: white;
                background-color: rgba(255, 255, 255, 0.1);
            }}
        """)

        # Change the size policy so it does not expand horizontally
        config_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        config_button.clicked.connect(self.open_configuration)

        # Add the button directly to the layout for better alignment
        bottom_bar_layout.addWidget(config_button, alignment=Qt.AlignVCenter)

        # Add expanding space in the middle
        bottom_bar_layout.addStretch()

        # Show the configured server
        credentials = AuthenticationModel.get_credentials()
        server_label = QLabel(f"Server: {credentials['workstation']}")
        server_label.setStyleSheet(f"""
            color: rgba(255, 255, 255, 0.9);
            font-size: {int(label_size * 0.9)}px;
            background-color: {COLORS['background_transparent']};
            padding: 8px 12px;
        """)

        # Add the server label directly to the layout for better alignment
        bottom_bar_layout.addWidget(server_label, alignment=Qt.AlignVCenter)

        # Add the bottom bar to the main layout
        main_layout.addStretch()  # Pushes all the content upwards
        main_layout.addWidget(bottom_bar)

        # Connect events to clear the errors while editing
        self.user_input.textChanged.connect(self.clear_user_error)
        self.password_input.password_field.textChanged.connect(self.clear_password_error)

    def toggle_maximized(self):
        # Toggle between maximized and restored
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def validate_credentials(self):
        # Clear any previous error message
        self.clear_all_errors()

        user = self.user_input.text()
        password = self.password_input.text()

        if not user or not password:
            if not user:
                self.show_user_error("Required field")
            if not password:
                self.show_password_error("Required field")
            show_warning_message(self, "Incomplete fields", "Please fill in all the fields.")
            return

        try:
            # Use the authentication model to validate the credentials
            success, message = AuthenticationModel.validate_credentials(user, password)

            if success:
                self.open_main_window()
            else:
                self.show_user_error("Invalid credentials")
                self.show_password_error("Invalid credentials")
                show_error_message(self, "Login error", message)

        except pymysql.err.OperationalError as e:
            error_code = e.args[0]
            error_message = e.args[1]

            # Error 1045: access denied for the user
            if error_code == 1045:
                self.show_user_error("Incorrect username or password")
                self.show_password_error("Incorrect username or password")
                show_error_message(self, "Login error",
                    "Incorrect username or password.\nCheck your credentials and try again.")

            # Error 2003: cannot connect to the MySQL server
            elif error_code == 2003:
                show_error_message(self, "Connection error",
                    f"Cannot connect to the server:\n{error_message}\n\nCheck that the server is available.")

            # Host error: this user is not allowed to connect from this host
            elif "Host" in error_message and "is not allowed to connect" in error_message:
                self.show_user_error("Restricted access for this user")
                show_error_message(self, "Restricted access",
                    f"This user is not allowed to connect from this computer.\n\n{error_message}")

            else:
                show_error_message(self, "Connection error", f"Error while connecting to the database:\n{error_message}")

        except Exception as e:
            show_error_message(self, "Unexpected error",
                f"An unexpected error occurred:\n{str(e)}\n\nPlease contact the system administrator.")

    def show_user_error(self, message):
        """Shows an error message for the username field"""
        self.user_error.setText(message)
        self.user_error.setVisible(True)
        self.user_input.setStyleSheet(f"""
            padding: {PADDING['medium']};
            border: 2px solid {COLORS['button_danger']};
            border-radius: {BORDER_RADIUS['xlarge']};
            background-color: rgba(255, 230, 230, 0.85);
            margin: 5px;
            min-height: {int(self.height() * 0.03)}px;
            font-size: {int(self.height() * 0.015)}px;
        """)

    def show_password_error(self, message):
        """Shows an error message for the password field"""
        self.password_error.setText(message)
        self.password_error.setVisible(True)
        # Apply the style to the password container
        self.password_input.parent().setStyleSheet(f"""
            padding: {PADDING['medium']};
            border: 2px solid {COLORS['button_danger']};
            border-radius: {BORDER_RADIUS['xlarge']};
            background-color: rgba(255, 230, 230, 0.85);
            margin: 5px;
            min-height: {int(self.height() * 0.03)}px;
            font-size: {int(self.height() * 0.015)}px;
        """)

    def clear_user_error(self):
        """Clears the username error message"""
        self.user_error.setVisible(False)
        # Restore the original style with the same font size as the password field
        container_height = int(self.height() * 0.55)
        self.user_input.setStyleSheet(f"""
            padding: {PADDING['medium']};
            border: 2px solid {COLORS['background_transparent']};
            border-radius: {BORDER_RADIUS['xlarge']};
            background-color: #FCFCFC;
            margin: 5px;
            min-height: {int(container_height * 0.06)}px;
            font-size: {FONT_SIZE['medium']};
        """)

    def clear_password_error(self):
        """Clears the password error message"""
        self.password_error.setVisible(False)
        # Restore the original style
        container_height = int(self.height() * 0.55)
        input_size = int(container_height * 0.025)
        self.password_input.parent().setStyleSheet(f"""
            padding: {PADDING['medium']};
            border-radius: {BORDER_RADIUS['xlarge']};
            border: 2px solid {COLORS['background_transparent']};
            background-color: #FCFCFC;
            margin: 5px;
            min-height: {int(container_height * 0.06)}px;
            font-size: {input_size}px;
        """)

    def clear_all_errors(self):
        """Clears all the error messages"""
        self.clear_user_error()
        self.clear_password_error()

    def open_main_window(self):
        """Opens the main window of the application"""
        try:
            # Get the authenticated user
            user = AuthenticationModel.get_credentials().get('user', '')

            # On a fresh installation the exam catalogs are still empty, so load
            # them from the source spreadsheets before any view can offer them.
            # Subsequent logins find them populated and skip the import.
            try:
                from backend.catalog_loader import ensure_catalogs_loaded
                from backend.database import PatientModel

                connection = PatientModel().connect()
                try:
                    loaded, catalog_message = ensure_catalogs_loaded(connection)
                finally:
                    connection.close()
                if loaded:
                    print(catalog_message)
            except Exception as e:
                print(f"Error while loading the exam catalogs: {str(e)}")

            # Improve error handling while checking the privileges
            try:
                from backend.users.users_model import UsersModel

                # Get the role directly from the users table
                user_role = UsersModel.get_user_role(user)

                # Log entry for debugging
            except Exception as e:
                # If there is an error checking the role, log it and assign the visitor role by default
                print(f"Error while checking the role: {str(e)}")
                user_role = "visitor"  # Default value when there is an error

            # Get the screen size to make the splash screen responsive
            screen = QDesktopWidget().availableGeometry()

            # Important: set the current window as parent so it appears on top
            splash = SplashScreen(self, logo_path=self.logo_path, message="Logging in...", duration=2)
            splash.setFixedSize(int(screen.width() * 0.3), int(screen.height() * 0.3))

            # Make sure it appears above the login window
            splash.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            splash.show()
            splash.raise_()  # Bring to front
            splash.opacity_animation.start()  # Start the fade-in animation
            QApplication.processEvents()

            # Wait for the loading screen to finish
            splash.exec_()

            # Hide the login window (after the loading screen)
            self.hide()

            # Show the matching window according to the user role
            try:
                if user_role == "admin":
                    # Deferred import to avoid circular imports
                    from frontend.admin import AdminView
                    self.main_window = AdminView(self)
                    print(f"User {user} with the Administrator role - Starting the admin.py view")
                elif user_role == "doctor":
                    # User with the doctor role
                    from frontend.doctors import DoctorView
                    self.main_window = DoctorView(self)
                    print(f"User {user} with the Doctor role - Starting the doctors.py view")
                else:
                    # Visitor user or user with a read-only role
                    from frontend.waiting_room import WaitingRoomView
                    self.main_window = WaitingRoomView(self)
                    print(f"User {user} with the Visitor role - Starting the waiting_room.py view")

                self.main_window.show()
            except Exception as e:
                self.show()  # Show the login window again if there is an error
                show_error_message(self, "Error while loading the view",
                    f"The user interface could not be started: {str(e)}\n"
                    f"Please contact the system administrator.")

        except ImportError as e:
            self.show()  # Show the login window again if there is an error
            show_error_message(self, "Initialization error",
                f"The main module of the application could not be loaded.\n"
                f"Please check that every file is in its correct location.\n"
                f"Detailed error: {str(e)}")
        except Exception as e:
            self.show()  # Show the login window again if there is an error
            # Make sure the message is readable - do not show text placeholders
            error_msg = str(e)
            if "'text warning'" in error_msg:
                error_msg = "Error while validating the user interface."
            show_error_message(self, "Error", f"The application could not be started: {error_msg}")

    def reset_login(self):
        self.user_input.clear()
        self.password_input.clear()
        # Clear the credentials in the model
        AuthenticationModel.clear_credentials()
        self.show()

    def open_configuration(self):
        """Opens the settings dialog"""
        dialog = ConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Reload the configuration if the changes were saved
            self.load_configuration()

            # Update the server label
            credentials = AuthenticationModel.get_credentials()
            for widget in self.findChildren(QLabel):
                if "Server:" in widget.text():
                    widget.setText(f"Server: {credentials['workstation']}")
                    break

    def logout(self):
        # Get the screen size to make the splash screen responsive
        screen = QDesktopWidget().screenGeometry()

        # Show the loading screen while logging out
        splash = SplashScreen(self, logo_path=self.logo_path, message="Logging out...", duration=1.5)
        splash.setFixedSize(int(screen.width() * 0.3), int(screen.height() * 0.3))
        splash.show()
        splash.opacity_animation.start()  # Start the fade-in animation
        QApplication.processEvents()

        # Wait for the loading screen to finish
        splash.exec_()

        # Important: clear the reference to main_window if it exists
        if hasattr(self, 'main_window'):
            self.main_window = None

        # Restart the login interface
        self.reset_login()

    def closeEvent(self, event):
        # Simply accept the event without showing a splash screen
        event.accept()


class PasswordInput(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        # Adjust the margins so the button is contained correctly
        layout.setContentsMargins(0, 0, 5, 0)
        layout.setSpacing(0)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background_transparent']};
                border-radius: {BORDER_RADIUS['large']};
                min-height: 40px;
            }}
        """)

        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)
        self.password_field.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background-color: {COLORS['background_transparent']};
                padding: {PADDING['medium']};
                font-size: {FONT_SIZE['medium']};
            }}
        """)

        # Determine the base path for the images
        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        images_path = os.path.join(self.base_path, "frontend", "images")
        self.icon_show = os.path.join(images_path, "view.png")
        self.icon_hide = os.path.join(images_path, "hide.png")

        self.toggle_button = QPushButton()
        # Increase the button size even more for better visibility
        self.toggle_button.setFixedSize(40, 40)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['background_transparent']};
                border: none;
                padding: 0 10px; /* Increase the horizontal padding for a larger hover area */
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: 20px; /* Radius matched to the button size */
            }}
        """)

        self.is_visible = False
        self.update_button_icon()

        layout.addWidget(self.password_field)
        layout.addWidget(self.toggle_button, 0, Qt.AlignVCenter)

        self.toggle_button.clicked.connect(self.toggle_password_visibility)

    def update_button_icon(self):
        """Updates the icon according to the current state"""
        icon_path = self.icon_hide if self.is_visible else self.icon_show
        if os.path.exists(icon_path):
            self.toggle_button.setIcon(QIcon(icon_path))
            # Increase the icon size for better visibility
            self.toggle_button.setIconSize(QSize(22, 22))

    def toggle_password_visibility(self):
        self.is_visible = not self.is_visible
        self.password_field.setEchoMode(QLineEdit.Normal if self.is_visible else QLineEdit.Password)
        self.update_button_icon()

    def text(self):
        return self.password_field.text()

    def clear(self):
        self.password_field.clear()

    def setPlaceholderText(self, text):
        self.password_field.setPlaceholderText(text)

    def setEchoMode(self, mode):
        self.password_field.setEchoMode(mode)
