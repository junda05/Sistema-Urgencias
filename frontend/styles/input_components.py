from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout, QLabel, QVBoxLayout
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
import os
import sys

from frontend.styles.styles import COLORS, BORDER_RADIUS, PADDING, FONT_SIZE

class IconTextField(QWidget):
    """Text field with an icon on the left."""

    def __init__(self, icon_path=None, placeholder="", parent=None, echo_mode=QLineEdit.Normal, readonly=False):
        super().__init__(parent)

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)

        # Style for the container widget
        self.setStyleSheet(f"""
            QWidget {{
                background-color: #FCFCFC;
                border-radius: {BORDER_RADIUS['large']};
                min-height: 45px;
                border: 1px solid {COLORS['border_light']};
            }}
            QWidget:focus-within {{
                border: 2px solid {COLORS['border_focus']};
            }}
        """)

        # Icon (optional)
        if icon_path and os.path.exists(icon_path):
            self.icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.icon_label.setFixedSize(24, 24)
            self.icon_label.setStyleSheet(f"background-color: {COLORS['background_transparent']}; border: none;")
            layout.addWidget(self.icon_label)

        # Input field
        self.text_field = QLineEdit()
        self.text_field.setEchoMode(echo_mode)
        self.text_field.setReadOnly(readonly)
        self.text_field.setPlaceholderText(placeholder)
        self.text_field.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background-color: {COLORS['background_transparent']};
                font-size: {FONT_SIZE['medium']};
                padding: {PADDING['small']};
            }}
        """)
        layout.addWidget(self.text_field)
        layout.setStretch(1, 1)  # The text field takes up all the available space

    def text(self):
        return self.text_field.text()

    def setText(self, text):
        self.text_field.setText(text)

    def clear(self):
        self.text_field.clear()

    def textChanged(self, callback):
        self.text_field.textChanged.connect(callback)


class PasswordField(IconTextField):
    """Password field with an icon and a show/hide button."""

    def __init__(self, icon_path=None, placeholder="", parent=None, readonly=False):
        super().__init__(icon_path, placeholder, parent, QLineEdit.Password, readonly)

        # Add the button that shows/hides the password
        self.is_visible = False

        # Base path for the images
        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        images_path = os.path.join(self.base_path, "frontend", "images")
        self.icon_show = os.path.join(images_path, "view.png")
        self.icon_hide = os.path.join(images_path, "hide.png")

        # Button with an icon
        self.toggle_button = QPushButton()
        self.toggle_button.setFixedSize(30, 30)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['background_transparent']};
                border: none;
                padding: 2px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: {BORDER_RADIUS['small']};
            }}
        """)

        # Set the initial icon (hide)
        self.update_button_icon()

        # Connect the signal
        self.toggle_button.clicked.connect(self.toggle_visibility)

        # Add it to the layout
        self.layout().addWidget(self.toggle_button)

    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.text_field.setEchoMode(QLineEdit.Normal if self.is_visible else QLineEdit.Password)
        self.update_button_icon()

    def update_button_icon(self):
        import sys
        icon_path = self.icon_show if not self.is_visible else self.icon_hide
        if os.path.exists(icon_path):
            self.toggle_button.setIcon(QIcon(icon_path))
            self.toggle_button.setIconSize(QSize(20, 20))


class RequirementList(QWidget):
    """List of requirements with visual indicators showing whether they are met."""

    def __init__(self, requirements=None, parent=None):
        super().__init__(parent)

        # Main vertical layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 0, 5, 0)
        self.layout.setSpacing(2)

        # Widget style
        self.setStyleSheet(f"""
            background-color: {COLORS['background_transparent']};
            color: {COLORS['text_primary']};
            font-size: 11px;
        """)

        # List of requirements
        self.requirements = []
        if requirements:
            for req in requirements:
                self.add_requirement(req)

    def add_requirement(self, text):
        # Create a widget for the requirement
        req_widget = QWidget()
        req_layout = QHBoxLayout(req_widget)
        req_layout.setContentsMargins(0, 0, 0, 0)
        req_layout.setSpacing(5)

        # Indicator (circle)
        indicator = QLabel("○")  # Empty circle
        indicator.setStyleSheet(f"""
            color: {COLORS['text_light']};
            font-size: 12px;
            background-color: {COLORS['background_transparent']};
            min-width: 15px;
        """)
        req_layout.addWidget(indicator)

        # Requirement text
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"""
            color: {COLORS['text_light']};
            background-color: {COLORS['background_transparent']};
        """)
        req_layout.addWidget(label)
        req_layout.setStretch(1, 1)  # The text takes up all the available space

        self.layout.addWidget(req_widget)
        self.requirements.append((indicator, label, False))  # False = the requirement is not met

    def update_requirement(self, index, fulfilled):
        if 0 <= index < len(self.requirements):
            indicator, label, current_state = self.requirements[index]

            if fulfilled != current_state:
                # Update the state
                self.requirements[index] = (indicator, label, fulfilled)

                # Update the style
                if fulfilled:
                    indicator.setText("●")  # Filled circle
                    indicator.setStyleSheet(f"""
                        color: {COLORS['button_success']};
                        font-size: 12px;
                        background-color: {COLORS['background_transparent']};
                        min-width: 15px;
                    """)
                    label.setStyleSheet(f"""
                        color: {COLORS['button_success']};
                        background-color: {COLORS['background_transparent']};
                    """)
                else:
                    indicator.setText("○")  # Empty circle
                    indicator.setStyleSheet(f"""
                        color: {COLORS['text_light']};
                        font-size: 12px;
                        background-color: {COLORS['background_transparent']};
                        min-width: 15px;
                    """)
                    label.setStyleSheet(f"""
                        color: {COLORS['text_light']};
                        background-color: {COLORS['background_transparent']};
                    """)
