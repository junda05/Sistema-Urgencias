from PyQt5.QtWidgets import (QPushButton, QLabel, QMessageBox, QDialog,
                           QVBoxLayout, QHBoxLayout, QWidget, QLineEdit,
                           QFormLayout, QComboBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor
from frontend.styles.styles import *

class StyledMessageBox(QMessageBox):
    """Class that creates styled QMessageBox instances based on the message type."""

    def __init__(self, parent=None, title="", text="", icon=QMessageBox.Information, style_type="info"):
        """
        Initializes a styled QMessageBox.

        Args:
            parent: Parent widget
            title: Message title
            text: Message text
            icon: Icon to display (QMessageBox.Information, QMessageBox.Warning, etc.)
            style_type: Style type ("info", "warning", "error", "confirmation")
        """
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setText(text)
        self.setIcon(icon)

        # Apply the style based on the type
        if style_type in MESSAGE_STYLES:
            self.setStyleSheet(MESSAGE_STYLES[style_type])

        # Adjust the background of the icons
        for child in self.children():
            if isinstance(child, QLabel) and not child.text():
                # This is most likely the label that holds the icon
                child.setStyleSheet("background-color: transparent;")

        # Remove borders and make the window frameless
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

class StyledButton(QPushButton):
    """Styled button with different variants."""

    def __init__(self, text, style_type="primary", custom_styles=None, parent=None, is_close=False):
        """
        Initializes a styled button.

        Args:
            text: Button text
            style_type: Style type ("primary", "danger", "warning", "window_control")
                        or a dictionary with custom styles
            custom_styles: Dictionary of custom styles (optional)
            parent: Parent widget
            is_close: If True and style_type="window_control", the close button style is applied
        """
        if isinstance(style_type, dict) and custom_styles is None:
            super().__init__(text, parent)
            custom_styles = style_type
            style_type = "custom"
        elif parent is None and isinstance(custom_styles, QWidget):
            super().__init__(text, custom_styles)
            parent = custom_styles
            custom_styles = None
        else:
            super().__init__(text, parent)

        # Apply the style based on the style_type
        if style_type == "window_control":
            self.setStyleSheet(BUTTON_STYLES["window_control"](is_close))
        elif style_type == "custom" and custom_styles:
            # For custom styles passed as a dictionary
            style_str = "QPushButton {"
            for key, value in custom_styles.items():
                style_str += f"{key}: {value};"
            style_str += "}"
            self.setStyleSheet(style_str)
        elif style_type in BUTTON_STYLES:
            self.setStyleSheet(BUTTON_STYLES[style_type])

        self.setCursor(Qt.PointingHandCursor)

class StyledDialog(QDialog):
    """Styled base dialog for forms."""

    def __init__(self, title="", width=600, parent=None):
        """
        Initializes a styled dialog.

        Args:
            title: Dialog title
            width: Minimum dialog width
            parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setMinimumWidth(width)
        self.setStyleSheet(DIALOG_STYLE)

        # Main layout with suitable margins
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        # Remove borders and make the window frameless
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

    def add_title(self, text):
        """Adds a title to the dialog."""
        title_label = QLabel(text)
        title_label.setStyleSheet(LABEL_STYLES["title"])
        self.layout.addWidget(title_label)
        return title_label

    def add_required_fields_indicator(self):
        """Adds a required fields indicator."""
        indicator = QLabel("* Required fields")
        indicator.setStyleSheet(LABEL_STYLES["required_indicator"])
        self.layout.addWidget(indicator)
        return indicator

    def add_form(self):
        """Adds a form to the dialog."""
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: transparent;")
        form_layout = QFormLayout(form_widget)
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(20)

        self.layout.addWidget(form_widget)
        return form_layout

    def add_button_row(self, buttons):
        """
        Adds a row of buttons to the dialog.

        Args:
            buttons: List of tuples (text, callback, style)
        """
        self.button_layout = QHBoxLayout()

        for text, callback, style in buttons:
            button = StyledButton(text, style)
            button.clicked.connect(callback)
            self.button_layout.addWidget(button)

        self.layout.addSpacing(10)
        self.layout.addLayout(self.button_layout)
        return self.button_layout

class FormField:
    """Class that creates styled form fields."""

    @staticmethod
    def create_line_edit(label_text, is_required=False, readonly=False, initial_value=""):
        """
        Creates a text field with a label.

        Args:
            label_text: Label text
            is_required: Whether the field is required
            readonly: Whether the field is read-only
            initial_value: Initial value

        Returns:
            tuple: (QLabel, QLineEdit)
        """
        label = QLabel(label_text + (" *" if is_required else ""))

        if is_required:
            label.setStyleSheet(LABEL_STYLES["required"])
        else:
            label.setStyleSheet(LABEL_STYLES["normal"])

        entry = QLineEdit()
        entry.setText(initial_value)

        if readonly:
            entry.setReadOnly(True)
            entry.setStyleSheet(LINE_EDIT_STYLES["readonly"])
        else:
            if is_required:
                entry.setStyleSheet(LINE_EDIT_STYLES["required"])
            else:
                entry.setStyleSheet(LINE_EDIT_STYLES["normal"])

        return label, entry

    @staticmethod
    def create_combo_box(label_text, options=None, is_required=False, initial_value=""):
        """
        Creates a selection field with a label.

        Args:
            label_text: Label text
            options: List of options
            is_required: Whether the field is required
            initial_value: Initially selected value

        Returns:
            tuple: (QLabel, QComboBox)
        """
        label = QLabel(label_text + (" *" if is_required else ""))

        if is_required:
            label.setStyleSheet(LABEL_STYLES["required"])
        else:
            label.setStyleSheet(LABEL_STYLES["normal"])

        combo = QComboBox()

        if options:
            combo.addItems(options)

        if initial_value:
            combo.setCurrentText(str(initial_value))

        if is_required:
            combo.setStyleSheet(COMBO_BOX_STYLES["required"])
        else:
            combo.setStyleSheet(COMBO_BOX_STYLES["normal"])

        return label, combo

class PasswordInput(QWidget):
    """Custom widget for password entry with a show/hide option"""

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
        self.password_field.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background-color: {COLORS['background_transparent']};
                padding: {PADDING['medium']};
                font-size: {FONT_SIZE['medium']};
            }}
        """)

        self.show_button = QPushButton("👁")
        self.show_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['background_transparent']};
                border: none;
                font-size: 25px;
                padding: 0 5px;
                color: {COLORS['button_primary']};
            }}
            QPushButton:hover {{
                color: {COLORS['button_primary_hover']};
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: {BORDER_RADIUS['small']};
            }}
        """)
        self.show_button.setCursor(Qt.PointingHandCursor)

        layout.addWidget(self.password_field)
        layout.addWidget(self.show_button)

        self.show_button.clicked.connect(self.toggle_password_visibility)

    def toggle_password_visibility(self):
        if self.password_field.echoMode() == QLineEdit.Password:
            self.password_field.setEchoMode(QLineEdit.Normal)
        else:
            self.password_field.setEchoMode(QLineEdit.Password)

    def text(self):
        return self.password_field.text()

    def clear(self):
        self.password_field.clear()

    def setPlaceholderText(self, text):
        self.password_field.setPlaceholderText(text)

    def setEchoMode(self, mode):
        self.password_field.setEchoMode(mode)
