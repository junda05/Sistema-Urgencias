from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QApplication, QDesktopWidget
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt
import os
from frontend.styles.styles import COLORS
from frontend.styles.components import StyledButton

class TitleBar(QWidget):
    """Custom title bar for every window, with no need for the system title bar."""

    def __init__(self, parent=None, left_buttons=None):
        """
        Initializes the title bar.

        Args:
            parent: Parent widget
            left_buttons: List of tuples (text, function, is_close) for the buttons on the left side
        """
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet(f"background-color: {COLORS['background_transparent']};")

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.layout.setSpacing(5)

        # Add buttons on the left side if they are provided
        if left_buttons:
            for text, function, is_close in left_buttons:
                button = StyledButton(text, "window_control", is_close=is_close)
                button.setFixedSize(30, 30)
                button.clicked.connect(function)
                self.layout.addWidget(button, 0, Qt.AlignLeft | Qt.AlignTop)

        # Expanding space in the middle
        self.layout.addStretch(1)

        # Control buttons (right side) - always present
        control_buttons = [
            ("🗕", lambda: parent.showMinimized() if parent else None, False),  # Minimize
            ("🗗", self.toggle_maximized, False),  # Maximize/Restore
            ("✖", lambda: parent.close() if parent else None, True)  # Close
        ]

        for text, function, is_close in control_buttons:
            button = StyledButton(text, "window_control", is_close=is_close)
            button.setFixedSize(30, 30)
            button.clicked.connect(function)
            self.layout.addWidget(button, 0, Qt.AlignRight | Qt.AlignTop)

    def toggle_maximized(self):
        """Toggles between maximized and normal mode for the parent window."""
        if self.parent() is None:
            return

        if self.parent().isMaximized():
            self.parent().showNormal()
        else:
            self.parent().showMaximized()

class CombinedHeader(QWidget):
    """Reusable component that creates a header with a logo and control buttons"""

    def __init__(self, parent=None, logo_path=None, height_percent=0.14, bg_color=COLORS['background_header']):
        """
        Initializes a combined header with a logo and control buttons.

        Args:
            parent: Parent widget
            logo_path: Path to the logo that will be displayed
            height_percent: Percentage of the screen height used for the header (0.14 = 14%)
            bg_color: Header background color
        """
        super().__init__(parent)

        # Compute sizes to make sure they match the login interface
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        logo_height = int(screen_height * height_percent)

        # Set a fixed height for the whole header and its style
        self.setFixedHeight(logo_height)
        self.setStyleSheet(f"background-color: {bg_color};")

        # Create the layout that arranges the logo and the control buttons
        header_layout = QHBoxLayout(self)
        header_layout.setContentsMargins(0, 0, 10, 0)

        # Logo area (left side)
        if logo_path and os.path.exists(logo_path):
            logo_width = int(screen_width * 0.2)  # 20% of the screen width

            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path)
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

        # Expanding space in the middle
        header_layout.addStretch(1)

        # Control buttons (right side)
        buttons = [
            ("🗕", lambda: parent.showMinimized() if parent else None, False),
            ("🗗", lambda: self._toggle_maximized(parent), False),
            ("✖", lambda: parent.close() if parent else None, True)
        ]

        for text, function, is_close in buttons:
            if function:  # Only create the button if there is a function to connect
                button = StyledButton(text, "window_control", is_close=is_close)
                button.setFixedSize(30, 30)
                button.clicked.connect(function)
                header_layout.addWidget(button, 0, Qt.AlignRight | Qt.AlignTop)

    def _toggle_maximized(self, parent):
        """Safely handles the call to the parent's toggle_maximized."""
        if parent:
            if hasattr(parent, 'toggle_maximized'):
                parent.toggle_maximized()
            else:
                # Fallback if the method does not exist
                if parent.isMaximized():
                    parent.showNormal()
                else:
                    parent.showMaximized()

class FramelessWindow(QWidget):
    """Base class for windows without a system title bar but with drag behavior."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Remove the system title bar
        self.setWindowFlags(Qt.FramelessWindowHint)
        # Allow a transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Variables used to handle window dragging
        self.dragging = False
        self.offset = None

    def mousePressEvent(self, event):
        # Allow the window to be dragged
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

    def toggle_maximized(self):
        """Toggles between maximized and normal mode for the window."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

class StatusBar(QWidget):
    """Bottom status bar that displays server information, version, etc."""

    def __init__(self, parent=None, left_info=None, center_info=None, right_info=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet(f"background-color: {COLORS['background_transparent']};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        # Information on the left side (such as buttons or text)
        if left_info:
            layout.addWidget(left_info, 0, Qt.AlignLeft | Qt.AlignVCenter)
        else:
            layout.addStretch(1)

        # Information in the center
        if center_info:
            layout.addWidget(center_info, 0, Qt.AlignCenter)

        # Information on the right side
        if right_info:
            layout.addWidget(right_info, 0, Qt.AlignRight | Qt.AlignVCenter)
        else:
            layout.addStretch(1)
