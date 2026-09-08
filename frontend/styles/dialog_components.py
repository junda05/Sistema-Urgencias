from PyQt5.QtWidgets import QDialog, QMessageBox, QPushButton, QFormLayout, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt
import configparser
import os
from frontend.styles.styles import COLORS, BORDER_RADIUS
from frontend.styles.components import StyledDialog, FormField

def show_error_message(parent, title, message):
    """Shows a styled error message"""
    from frontend.styles.components import StyledMessageBox
    msg_box = StyledMessageBox(parent, title, message, QMessageBox.Critical, "error")

    # Create styled OK button
    btn_ok = QPushButton("Accept")
    btn_ok.setCursor(Qt.PointingHandCursor)

    msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
    msg_box.setDefaultButton(btn_ok)

    return msg_box.exec_()

def show_warning_message(parent, title, message):
    """Shows a styled warning message"""
    from frontend.styles.components import StyledMessageBox
    msg_box = StyledMessageBox(parent, title, message, QMessageBox.Warning, "warning")

    # Create styled OK button
    btn_ok = QPushButton("Accept")
    btn_ok.setCursor(Qt.PointingHandCursor)

    msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
    msg_box.setDefaultButton(btn_ok)

    return msg_box.exec_()

def show_info_message(parent, title, message):
    """Shows a styled informational message"""
    from frontend.styles.components import StyledMessageBox
    msg_box = StyledMessageBox(parent, title, message, QMessageBox.Information, "info")

    # Create styled OK button
    btn_ok = QPushButton("Accept")
    btn_ok.setCursor(Qt.PointingHandCursor)

    msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
    msg_box.setDefaultButton(btn_ok)

    return msg_box.exec_()

class ConfigDialog(StyledDialog):
    """Reusable dialog for connection settings"""
    def __init__(self, parent=None):
        super().__init__("Connection Settings", 450, parent)

        from backend.database import ConfigurationModel

        # Get the current configuration
        self.config_path = ConfigurationModel.get_config_path()
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            self.config['DATABASE'] = {'host': 'localhost'}

        # Add title and description
        self.add_title("Server Settings")

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
            from frontend.styles.dialog_components import show_warning_message
            show_warning_message(self, "Invalid Data", "The server cannot be empty.")
            return

        # Save the configuration using the model
        from backend.database import ConfigurationModel
        success, message = ConfigurationModel.save_configuration(new_host)

        if success:
            from frontend.styles.dialog_components import show_info_message
            show_info_message(self, "Settings Saved",
                                   "The settings have been saved successfully.\n"
                                   "The changes will be applied the next time you log in.")
            self.accept()
        else:
            from frontend.styles.dialog_components import show_error_message
            show_error_message(self, "Error", f"Could not save the settings: {message}")
