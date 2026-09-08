from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QLineEdit, QPushButton, QFormLayout, QWidget,
                           QProgressBar, QMessageBox, QSpacerItem, QSizePolicy, QDesktopWidget, QComboBox)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap
import re
import os
import sys

from frontend.styles.styles import *
from frontend.styles.components import StyledDialog, FormField, StyledButton
from frontend.styles.custom_widgets import PasswordInput
from frontend.styles.input_components import IconTextField, PasswordField, RequirementList

class PasswordStrengthWidget(QWidget):
    """Widget that visually displays password strength"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)

        # Progress bar for the strength
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(200, 200, 200, 150);
                border-radius: 3px;
                padding: 0px;
            }

            QProgressBar::chunk {
                background-color: #CC0000;  /* Red by default */
                border-radius: 3px;
            }
        """)

        # Label for the strength message
        self.label = QLabel("Strength: Weak")
        self.label.setStyleSheet("""
            color: #CC0000;
            font-size: 13px;
            background-color: transparent;
        """)

        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.label)

    def update_strength(self, password):
        """Updates the password strength"""
        if not password:
            strength = 0
            color = "#CC0000"  # Red
            text = "Strength: Empty"
        else:
            # Evaluate length (max 30)
            length_score = min(30, len(password)) * 1.5

            # Evaluate complexity
            has_lower = any(c.islower() for c in password)
            has_upper = any(c.isupper() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(not c.isalnum() for c in password)

            # Calculate the score
            complexity_score = sum([has_lower, has_upper, has_digit, has_special]) * 15
            strength = min(100, length_score + complexity_score)

            # Determine color and text
            if strength < 30:
                color = "#CC0000"  # Red
                text = "Strength: Very weak"
            elif strength < 50:
                color = "#FF8000"  # Orange
                text = "Strength: Weak"
            elif strength < 75:
                color = "#FFCC00"  # Yellow
                text = "Strength: Moderate"
            elif strength < 95:
                color = "#AACC00"  # Light green
                text = "Strength: Strong"
            else:
                color = "#00CC00"  # Green
                text = "Strength: Very strong"

        # Update the bar and the label
        self.progress_bar.setValue(int(strength))
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(200, 200, 200, 150);
                border-radius: 3px;
                padding: 0px;
            }}

            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        self.label.setText(text)
        self.label.setStyleSheet(f"color: {color}; font-size: 13px; background-color: transparent;")

class PasswordInputWithToggle(QWidget):
    """Password field with a show/hide button"""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Password text field
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)
        self.password_field.setPlaceholderText(placeholder)
        self.password_field.setMinimumHeight(45)  # Fix a minimum height for consistency
        self.password_field.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background-color: {COLORS['background_transparent']};
                padding: 5px 10px;
                font-size: 15px;
            }}
        """)
        layout.addWidget(self.password_field, 1)

        # Determine the base path for images
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        images_path = os.path.join(base_path, "frontend", "images")
        self.icon_show = os.path.join(images_path, "view.png")
        self.icon_hide = os.path.join(images_path, "hide.png")

        # Show/hide button - adjusted to look more like the login one
        self.toggle_button = QPushButton()
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0px 5px; /* Reduce horizontal padding */
                margin: 0px 8px 0px 0px; /* Increase right margin for separation */
            }
            QPushButton:hover {
                background-color: rgba(200, 200, 200, 50);
                border-radius: 12px; /* Reduce radius for a better appearance */
            }
        """)
        # Adjust the size to look more like the login one
        self.toggle_button.setFixedSize(30, 30)

        # Set the initial icon (show)
        self.is_visible = False
        self.update_icon()

        # Add it directly to the main layout with right alignment
        layout.addWidget(self.toggle_button, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.toggle_button.clicked.connect(self.toggle_visibility)

    def toggle_visibility(self):
        """Toggles between showing and hiding the password"""
        self.is_visible = not self.is_visible
        self.password_field.setEchoMode(QLineEdit.Normal if self.is_visible else QLineEdit.Password)
        self.update_icon()

    def update_icon(self):
        """Updates the icon according to the current state"""
        icon_path = self.icon_hide if self.is_visible else self.icon_show
        if os.path.exists(icon_path):
            self.toggle_button.setIcon(QIcon(icon_path))
            # Keep the icon size consistent with the login screen
            self.toggle_button.setIconSize(QSize(20, 20))

    def text(self):
        """Returns the current text of the field"""
        return self.password_field.text()

    def clear(self):
        """Clears the field"""
        self.password_field.clear()

    def textChanged(self, callback):
        """Connects a function to the textChanged event"""
        self.password_field.textChanged.connect(callback)

    def setPlaceholderText(self, text):
        """Sets the placeholder text"""
        self.password_field.setPlaceholderText(text)

class UserRegistrationDialog(StyledDialog):
    """User registration dialog with real-time validation"""

    def __init__(self, parent=None):
        super().__init__("User Registration", 800, parent)  # Increase the initial width to fit the horizontal layout

        # Determine the base path for images
        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Path to the images
        images_path = os.path.join(self.base_path, "frontend", "images")

        # Paths to the icons
        self.icon_user = os.path.join(images_path, "doctor.png")
        self.icon_lock = os.path.join(images_path, "padlock.png")
        self.icon_add = os.path.join(images_path, "add.png")
        self.icon_name = os.path.join(images_path, "full_name.png")
        self.icon_role = os.path.join(images_path, "roles.png")

        # Create a custom title with a larger icon
        title_container = QWidget()
        # Make the container background transparent
        title_container.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(12)

        # Add an icon next to the title with an increased size
        icon_label = QLabel()
        icon_pixmap = QPixmap(self.icon_add).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(icon_pixmap)
        title_layout.addWidget(icon_label)

        # Title text with an increased size
        title_text = QLabel("Create New User")
        title_text.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLORS['text_primary']};")
        title_layout.addWidget(title_text)

        # Align to the left and add expandable space on the right
        title_layout.addStretch()
        self.layout.addWidget(title_container)

        # Description with an improved style
        description = QLabel("Complete the information to register a new user in the system.")
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: {COLORS['background_transparent']}; font-size: 15px;")
        self.layout.addWidget(description)
        self.layout.addSpacing(5)  # Reduced spacing after the description

        # Main container with a horizontal layout
        center_container = QWidget()
        center_container.setStyleSheet(f"background-color: {COLORS['background_transparent']};")

        # Switch to a horizontal layout for the main container
        center_layout = QHBoxLayout(center_container)
        center_layout.setContentsMargins(20, 0, 20, 0)
        center_layout.setSpacing(20)  # Spacing between columns

        # Create two columns to distribute the fields
        left_column = QWidget()
        left_column.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(18)

        right_column = QWidget()
        right_column.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(18)

        # 1. Username field with an aligned icon - in the left column
        user_container = QWidget()
        user_layout = QHBoxLayout(user_container)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(10)

        # Container for the label and the field
        user_field_container = QWidget()
        user_field_layout = QVBoxLayout(user_field_container)
        user_field_layout.setContentsMargins(0, 0, 0, 0)
        user_field_layout.setSpacing(5)

        user_label = QLabel("Username:")
        user_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        user_field_layout.addWidget(user_label)

        # Create a container to vertically align the icon with the field
        user_input_container = QWidget()
        user_input_layout = QHBoxLayout(user_input_container)
        user_input_layout.setContentsMargins(0, 0, 0, 0)
        user_input_layout.setSpacing(10)

        # User icon centered vertically
        user_icon = QLabel()
        user_pixmap = QPixmap(self.icon_user).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        user_icon.setPixmap(user_pixmap)
        user_icon.setFixedSize(40, 40)
        user_icon.setAlignment(Qt.AlignCenter)
        user_input_layout.addWidget(user_icon)

        # Input field with an increased font size and a style consistent with the login screen
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setMinimumHeight(45)  # Height consistent with the password fields
        self.username_input.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: #FCFCFC;
                color: {COLORS['text_primary']};
                font-size: 15px;
                min-height: 45px; /* Guarantees the same height as the password fields */
            }}
        """)
        user_input_layout.addWidget(self.username_input)

        # Apply a style to the container to simulate a field with a background - minimum height added
        user_input_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px; /* Fixed height equal to the password fields */
            }}
        """)

        # Add the input container to the field layout
        user_field_layout.addWidget(user_input_container)

        # Validation feedback with an increased size
        self.username_feedback = QLabel("")
        self.username_feedback.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
        self.username_feedback.setVisible(False)
        user_field_layout.addWidget(self.username_feedback)

        # Add the username requirements with an increased size
        self.user_requirements = RequirementList(parent=self)
        self.user_requirements.setStyleSheet("font-size: 13px;")
        self.user_requirements.add_requirement("Between 4 and 16 characters")
        self.user_requirements.add_requirement("Must start with a letter")
        self.user_requirements.add_requirement("Only letters, numbers and underscores")
        user_field_layout.addWidget(self.user_requirements)

        user_layout.addWidget(user_field_container)
        left_layout.addWidget(user_container)

        # 2. Full name field with an icon - in the left column
        name_container = QWidget()
        name_layout = QHBoxLayout(name_container)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(10)

        # Container for the label and the field
        name_field_container = QWidget()
        name_field_layout = QVBoxLayout(name_field_container)
        name_field_layout.setContentsMargins(0, 0, 0, 0)
        name_field_layout.setSpacing(5)

        name_label = QLabel("Full name:")
        name_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        name_field_layout.addWidget(name_label)

        # Create a container to vertically align the icon with the field
        name_input_container = QWidget()
        name_input_layout = QHBoxLayout(name_input_container)
        name_input_layout.setContentsMargins(0, 0, 0, 0)
        name_input_layout.setSpacing(10)

        # Add an icon for the full name field
        name_icon = QLabel()
        name_pixmap = QPixmap(self.icon_name).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        name_icon.setPixmap(name_pixmap)
        name_icon.setFixedSize(40, 40)
        name_icon.setAlignment(Qt.AlignCenter)
        name_input_layout.addWidget(name_icon)

        # Input field for the full name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter full name")
        self.name_input.setMinimumHeight(45)
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: #FCFCFC;
                color: {COLORS['text_primary']};
                font-size: 15px;
                min-height: 45px;
            }}
        """)
        name_input_layout.addWidget(self.name_input)

        # Apply a style to the container
        name_input_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px;
            }}
        """)

        # Add the input container to the field layout
        name_field_layout.addWidget(name_input_container)

        # Space for the name feedback
        self.name_feedback = QLabel("")
        self.name_feedback.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
        self.name_feedback.setVisible(False)
        name_field_layout.addWidget(self.name_feedback)

        name_layout.addWidget(name_field_container)
        left_layout.addWidget(name_container)

        # 3. Role field with an icon - in the left column
        role_container = QWidget()
        role_layout = QHBoxLayout(role_container)
        role_layout.setContentsMargins(0, 0, 0, 0)
        role_layout.setSpacing(10)

        # Container for the label and the field
        role_field_container = QWidget()
        role_field_layout = QVBoxLayout(role_field_container)
        role_field_layout.setContentsMargins(0, 0, 0, 0)
        role_field_layout.setSpacing(5)

        role_label = QLabel("User role:")
        role_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        role_field_layout.addWidget(role_label)

        # Create a container for the roles combo box
        role_input_container = QWidget()
        role_input_layout = QHBoxLayout(role_input_container)
        role_input_layout.setContentsMargins(0, 0, 0, 0)
        role_input_layout.setSpacing(10)

        # Add an icon for the role field
        role_icon = QLabel()
        role_pixmap = QPixmap(self.icon_role).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        role_icon.setPixmap(role_pixmap)
        role_icon.setFixedSize(40, 40)
        role_icon.setAlignment(Qt.AlignCenter)
        role_input_layout.addWidget(role_icon)

        # Role selector
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Visitor", "Doctor", "Administrator"])
        self.role_combo.setMinimumHeight(45)
        self.role_combo.setStyleSheet(f"""
            QComboBox {{
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: #FCFCFC;
                color: {COLORS['text_primary']};
                font-size: 15px;
                min-height: 45px;
            }}
            QComboBox:hover {{
                background-color: {COLORS['background_readonly']};
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {COLORS['border_light']};
                selection-background-color: {COLORS['button_primary']};
                selection-color: white;
                background-color: white;
            }}
        """)
        role_input_layout.addWidget(self.role_combo)

        # Apply a style to the container
        role_input_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px;
            }}
        """)

        # Add the input container to the field layout
        role_field_layout.addWidget(role_input_container)

        role_layout.addWidget(role_field_container)
        left_layout.addWidget(role_container)

        # Add expandable space in the left column
        left_layout.addStretch()

        # 4. Password field with an icon - in the right column
        password_container = QWidget()
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(10)

        # Container for the label and the field
        password_field_container = QWidget()
        password_field_layout = QVBoxLayout(password_field_container)
        password_field_layout.setContentsMargins(0, 0, 0, 0)
        password_field_layout.setSpacing(5)

        password_label = QLabel("Password:")
        password_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        password_field_layout.addWidget(password_label)

        # Create a container to vertically align the icon with the field
        password_input_container = QWidget()
        password_input_layout = QHBoxLayout(password_input_container)
        password_input_layout.setContentsMargins(0, 0, 0, 0)
        password_input_layout.setSpacing(10)

        # Lock icon centered vertically
        password_icon = QLabel()
        password_pixmap = QPixmap(self.icon_lock).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        password_icon.setPixmap(password_pixmap)
        password_icon.setFixedSize(40, 40)
        password_icon.setAlignment(Qt.AlignCenter)
        password_input_layout.addWidget(password_icon)

        # Use the new password component with a toggle
        self.password_input_container = PasswordInputWithToggle("Enter password")
        password_input_layout.addWidget(self.password_input_container)

        # Apply a style to the container to simulate a field with a background
        password_input_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px;
            }}
        """)

        # Add the input container to the field layout
        password_field_layout.addWidget(password_input_container)

        # Strength widget
        self.strength_widget = PasswordStrengthWidget()
        password_field_layout.addWidget(self.strength_widget)

        # Password requirements with an increased size
        self.password_requirements = RequirementList(parent=self)
        self.password_requirements.setStyleSheet("font-size: 13px;")
        self.password_requirements.add_requirement("At least 8 characters")
        self.password_requirements.add_requirement("At least one uppercase letter")
        self.password_requirements.add_requirement("At least one lowercase letter")
        self.password_requirements.add_requirement("At least one number")
        self.password_requirements.add_requirement("At least one special character")
        password_field_layout.addWidget(self.password_requirements)

        password_layout.addWidget(password_field_container)
        right_layout.addWidget(password_container)

        # 5. Password confirmation field - in the right column
        confirm_container = QWidget()
        confirm_layout = QHBoxLayout(confirm_container)
        confirm_layout.setContentsMargins(0, 0, 0, 0)
        confirm_layout.setSpacing(10)

        # Container for the label and the field
        confirm_field_container = QWidget()
        confirm_field_layout = QVBoxLayout(confirm_field_container)
        confirm_field_layout.setContentsMargins(0, 0, 0, 0)
        confirm_field_layout.setSpacing(5)

        confirm_label = QLabel("Confirm password:")
        confirm_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 16px;")
        confirm_field_layout.addWidget(confirm_label)

        # Create a container to vertically align the icon with the field
        confirm_input_container = QWidget()
        confirm_input_layout = QHBoxLayout(confirm_input_container)
        confirm_input_layout.setContentsMargins(0, 0, 0, 0)
        confirm_input_layout.setSpacing(10)

        # Lock icon centered vertically
        confirm_icon = QLabel()
        confirm_pixmap = QPixmap(self.icon_lock).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        confirm_icon.setPixmap(confirm_pixmap)
        confirm_icon.setFixedSize(40, 40)
        confirm_icon.setAlignment(Qt.AlignCenter)
        confirm_input_layout.addWidget(confirm_icon)

        # Use the new password component with a toggle for the confirmation
        self.confirm_input_container = PasswordInputWithToggle("Confirm password")
        confirm_input_layout.addWidget(self.confirm_input_container)

        # Apply a style to the container to simulate a field with a background
        confirm_input_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px;
            }}
        """)

        # Add the input container to the field layout
        confirm_field_layout.addWidget(confirm_input_container)

        # Match feedback with an increased size
        self.password_feedback = QLabel("")
        self.password_feedback.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
        self.password_feedback.setVisible(False)
        confirm_field_layout.addWidget(self.password_feedback)

        confirm_layout.addWidget(confirm_field_container)
        right_layout.addWidget(confirm_container)

        # Add expandable space in the right column
        right_layout.addStretch()

        # Add the columns to the main container
        center_layout.addWidget(left_column)
        center_layout.addWidget(right_column)

        # Add the main container to the dialog layout
        self.layout.addWidget(center_container, 1)

        # Action buttons with an improved style
        buttons = [
            ("Register", self.register_user, "primary"),
            ("Cancel", self.reject, "danger")
        ]

        buttons_layout = self.add_button_row(buttons)

        # Increase the size of the buttons
        for i in range(buttons_layout.count()):
            widget = buttons_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setMinimumHeight(45)
                widget.setStyleSheet(widget.styleSheet() + f"font-size: 16px;")

        # Add a timer to check for an existing username with debounce
        self.username_check_timer = QTimer(self)
        self.username_check_timer.setSingleShot(True)  # Fires only once
        self.username_check_timer.setInterval(600)     # 600ms wait
        self.username_check_timer.timeout.connect(self.check_username_remote)

        # Connect events for real-time validation
        self.username_input.textChanged.connect(self.start_username_check)
        self.password_input_container.textChanged(self.update_password_strength)
        self.confirm_input_container.textChanged(self.validate_password_match)

        # General dialog style
        self.setStyleSheet(f"""
            {self.styleSheet()}
            QDialog {{
                background-color: {COLORS['background_primary']};
            }}
        """)

        # Center the dialog on the screen
        self.centerDialog()

        # Responsive adjustment of the final size
        self.adjustSize()

    def centerDialog(self):
        """Centers the dialog on the user's screen, adjusting for the dark blue section"""
        screen = QDesktopWidget().screenGeometry()
        # Wait for the dialog size to be calculated
        self.adjustSize()
        size = self.geometry()

        # Get the screen dimensions for responsive calculations
        screen_width = screen.width()
        screen_height = screen.height()

        # Center horizontally
        x = (screen_width - size.width()) // 2

        # Center vertically within the content area, but lower down
        content_height = int(screen_height * 0.85)
        content_top = (screen_height - content_height) // 2

        # Add a vertical offset (2% of the screen height) to move the dialog down
        y_offset = int(screen_height * 0.02)
        y = content_top + (content_height - size.height()) // 2 + y_offset

        # Make sure the dialog is always visible on the screen
        # and does not run off the bottom edge
        if y < 10:
            y = 10  # Minimum top margin
        if y + size.height() > screen_height - 10:
            y = screen_height - size.height() - 10  # Minimum bottom margin

        self.move(x, y)

    def start_username_check(self):
        """Starts the timer that checks whether the username already exists remotely"""
        # Reset and validate locally
        self.validate_username_local()
        # Restart the timer every time the text changes
        self.username_check_timer.start()

    def validate_username_local(self):
        """Performs only local validations of the username"""
        username = self.username_input.text()

        # Update the requirement indicators
        self.user_requirements.update_requirement(0, 4 <= len(username) <= 16)
        self.user_requirements.update_requirement(1, username and username[0].isalpha())
        self.user_requirements.update_requirement(2, username and all(c.isalnum() or c == '_' for c in username))

        # Validate the complete username
        if not username:
            self.username_feedback.setText("The username is required")
            self.username_feedback.setVisible(True)
            return False

        if len(username) < 4:
            self.username_feedback.setText("The username must be at least 4 characters long")
            self.username_feedback.setVisible(True)
            return False

        if len(username) > 16:
            self.username_feedback.setText("The username must not exceed 16 characters")
            self.username_feedback.setVisible(True)
            return False

        if not username[0].isalpha():
            self.username_feedback.setText("The username must start with a letter")
            self.username_feedback.setVisible(True)
            return False

        if not all(c.isalnum() or c == '_' for c in username):
            self.username_feedback.setText("Use only letters, numbers and underscores")
            self.username_feedback.setVisible(True)
            return False

        # Local validation passed
        self.username_feedback.setVisible(False)
        return True

    def check_username_remote(self):
        """Checks in the database whether the username already exists"""
        username = self.username_input.text()

        # Skip check if username doesn't pass local validation
        if not self.validate_username_local():
            return
        try:
            # Import here to avoid circular imports
            from backend.users.users_model import UsersModel

            if UsersModel.check_user_exists(username):
                self.username_feedback.setText("This username already exists")
                self.username_feedback.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
                self.username_feedback.setVisible(True)
                # Update the first requirement to show that it is not available
                self.user_requirements.update_requirement(0, False)
            else:
                # If the user does not exist, change the message to available
                self.username_feedback.setText("Username available")
                self.username_feedback.setStyleSheet(f"color: {COLORS['button_success']}; font-size: 13px;")
                self.username_feedback.setVisible(True)
                # Update the first requirement to show that it is available
                self.user_requirements.update_requirement(0, True)
        except Exception as e:
            print(f"Error checking the username remotely: {str(e)}")

    def validate_username_realtime(self):
        """Validates the username in real time and updates the requirements"""
        # Local validation first
        if not self.validate_username_local():
            return False

        # Check whether the username already exists
        try:
            from backend.users.users_model import UsersModel

            username = self.username_input.text()
            if UsersModel.check_user_exists(username):
                self.username_feedback.setText("This username already exists")
                self.username_feedback.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
                self.username_feedback.setVisible(True)
                return False
        except Exception as e:
            print(f"Error checking the username: {str(e)}")

        # All good, hide the feedback
        self.username_feedback.setVisible(False)
        return True

    def update_password_strength(self):
        """Updates the password strength and the requirements"""
        password = self.password_input_container.text()
        self.strength_widget.update_strength(password)

        # Update the requirement indicators
        self.password_requirements.update_requirement(0, len(password) >= 8)
        self.password_requirements.update_requirement(1, any(c.isupper() for c in password))
        self.password_requirements.update_requirement(2, any(c.islower() for c in password))
        self.password_requirements.update_requirement(3, any(c.isdigit() for c in password))
        self.password_requirements.update_requirement(4, any(not c.isalnum() for c in password))

        # If there is text in the confirmation field, validate the match
        if self.confirm_input_container.text():
            self.validate_password_match()

    def validate_password_match(self):
        """Validates that the passwords match"""
        password = self.password_input_container.text()
        confirm = self.confirm_input_container.text()

        if not confirm:
            self.password_feedback.setVisible(False)
            return False

        if password != confirm:
            self.password_feedback.setText("The passwords do not match")
            self.password_feedback.setVisible(True)
            return False

        # All good, hide the feedback
        self.password_feedback.setVisible(False)
        return True

    def validate_form(self):
        """Validates the whole form before submitting"""
        # Validate the username with a complete check
        username_valid = self.validate_username_realtime()

        # Validate the password
        full_name = self.name_input.text()
        name_words = [w for w in full_name.split() if w.strip()]
        if len(name_words) < 3:
            self.name_feedback = getattr(self, 'name_feedback', QLabel())
            self.name_feedback.setText("The full name must contain at least 3 words")
            self.name_feedback.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
            self.name_feedback.setVisible(True)
            return False
        else:
            # Hide the error message if it exists
            name_feedback = getattr(self, 'name_feedback', None)
            if name_feedback:
                name_feedback.setVisible(False)

        password = self.password_input_container.text()
        if not password:
            self.password_feedback.setText("The password is required")
            self.password_feedback.setVisible(True)
            return False

        # Check the minimum password requirements
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        if len(password) < 8:
            self.password_feedback.setText("The password must be at least 8 characters long")
            self.password_feedback.setVisible(True)
            return False

        if not (has_upper and has_lower and has_digit and has_special):
            self.password_feedback.setText("The password must contain uppercase letters, lowercase letters, numbers and special characters")
            self.password_feedback.setVisible(True)
            return False

        # Validate the match
        passwords_match = self.validate_password_match()

        return username_valid and passwords_match

    def register_user(self):
        """Attempts to register the user"""
        if self.validate_form():
            # Data for the registration
            username = self.username_input.text()
            password = self.password_input_container.text()
            full_name = self.name_input.text()
            role = self.role_combo.currentText()  # Get the selected role

            # Try to create the user directly instead of checking first
            try:
                from backend.users.users_model import UsersModel

                # Determine the role according to the selection
                if role == "Administrator":
                    success, message = UsersModel.create_admin_user(username, password, full_name)
                elif role == "Doctor":
                    success, message = UsersModel.create_crud_user(username, password, full_name)
                else:  # Visitor
                    success, message = UsersModel.create_user(username, password, full_name)

                if success:
                    # On success, accept the dialog to finish the registration
                    self.accept()
                else:
                    # Show the error if it failed (for example, if the user already exists)
                    from frontend.styles.dialog_components import show_warning_message
                    show_warning_message(
                        self,
                        "Registration error",
                        message
                    )
                    # If the error is that the user already exists, show it in the interface
                    if "already exists" in message.lower():
                        self.username_feedback.setText("This username already exists")
                        self.username_feedback.setStyleSheet(f"color: {COLORS['button_danger_hover']}; font-size: 13px;")
                        self.username_feedback.setVisible(True)
                    return

            except Exception as e:
                print(f"Error during the final verification: {str(e)}")
                from frontend.styles.dialog_components import show_warning_message
                show_warning_message(
                    self,
                    "System error",
                    f"An unexpected error occurred: {str(e)}"
                )
                return
        else:
            # Show a general error message if the validation was not completed
            from frontend.styles.dialog_components import show_warning_message
            show_warning_message(
                self,
                "Incomplete Form",
                "Please correct the errors in the form before continuing."
            )