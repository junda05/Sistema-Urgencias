from PyQt5.QtWidgets import (QWidget, QLineEdit, QPushButton, QHBoxLayout,
                           QVBoxLayout, QLabel, QFrame, QDesktopWidget)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from frontend.styles.styles import COLORS, BORDER_RADIUS, PADDING, FONT_SIZE

class PasswordInput(QWidget):
    """Password input field with a button to show/hide the password."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
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
        # Removing hard-coded font size to inherit from parent
        self.password_field.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background-color: {COLORS['background_transparent']};
                padding: {PADDING['medium']};
            }}
        """)

        self.show_button = QPushButton("👁")
        self.show_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['background_transparent']};
                border: none;
                font-size: 25px;
                padding: 0 10px; /* Increase horizontal padding for a larger hover area */
                color: {COLORS['button_primary']};
            }}
            QPushButton:hover {{
                color: {COLORS['button_primary_hover']};
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: {BORDER_RADIUS['medium']}; /* Use the medium radius instead of small */
            }}
        """)
        # Increase the button size for better visibility
        self.show_button.setFixedSize(40, 40)
        self.show_button.setCursor(Qt.PointingHandCursor)

        layout.addWidget(self.password_field)
        layout.addWidget(self.show_button)

        self.show_button.clicked.connect(self.toggle_password_visibility)

    def toggle_password_visibility(self):
        """Toggles between normal mode and password mode."""
        if self.password_field.echoMode() == QLineEdit.Password:
            self.password_field.setEchoMode(QLineEdit.Normal)
        else:
            self.password_field.setEchoMode(QLineEdit.Password)

    def text(self):
        """Returns the text of the input field."""
        return self.password_field.text()

    def clear(self):
        """Clears the input field."""
        self.password_field.clear()

    def setPlaceholderText(self, text):
        """Sets the placeholder text."""
        self.password_field.setPlaceholderText(text)

    def setEchoMode(self, mode):
        """Sets the display mode."""
        self.password_field.setEchoMode(mode)

class ButtonFrame(QFrame):
    """Frame for buttons with a consistent style."""

    def __init__(self, buttons, parent=None, color="#659BD1", spacing=30, search_container=None):
        """
        Initializes a button frame with a consistent style.

        Args:
            buttons: List of tuples (text, function, optional_color)
            parent: Parent widget
            color: Default color for every button (when not specified individually)
            spacing: Spacing between buttons
            search_container: Optional search container
        """
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['background_transparent']};")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(spacing)

        screen = QDesktopWidget().screenGeometry()
        button_width = int(screen.width() * 0.12)  # 12% of the screen width

        for item in buttons:
            if len(item) == 3:
                text, function, btn_color = item
            else:
                text, function = item
                btn_color = color

            button = QPushButton(text)
            button.setFixedWidth(button_width)
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {btn_color};
                    color: {COLORS['text_white']};
                    font-family: 'Franklin Gothic Medium';
                    font-size: 18px;
                    min-height: 50px;
                    padding: 5px 15px;
                    border-radius: 10px;
                    border: 1px solid {COLORS['background_white']};
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self.adjust_color(btn_color, brighter=True)};
                }}
            """)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(function)
            layout.addWidget(button)

        # Add the search container if it is provided
        if search_container:
            layout.addWidget(search_container)

        # Distribute the space evenly
        layout.addStretch()

    def adjust_color(self, color, brighter=False):
        """Adjusts the color for the hover effect."""
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

class TableContainer(QWidget):
    def __init__(self, parent=None, width_percent=0.80, height_percent=0.60):
        super().__init__(parent)
        self.setStyleSheet(f"QWidget {{background-color: {COLORS['background_transparent']}; border: none;}}")

        # Use a vertical layout with centered alignment
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignCenter)  # Center the content

        # Store the percentages for later use
        self.width_percent = width_percent
        self.height_percent = height_percent

    def set_table(self, table):
        # Clear any existing widget
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add the table to the layout without changing its size
        self.layout.addWidget(table)

        # Apply consistent sizes for both interfaces
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        # Adjust the sizes so they are more compact
        table_width = int(screen_width * self.width_percent)
        table_height = int(screen_height * self.height_percent)

        # Apply the size directly to the table
        table.setFixedWidth(table_width)
        table.setFixedHeight(table_height)
