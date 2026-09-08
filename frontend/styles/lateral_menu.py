from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                           QLabel, QGraphicsOpacityEffect, QFrame,
                           QHBoxLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QRect
from PyQt5.QtGui import QIcon, QPixmap
import os
import sys
from frontend.styles.styles import COLORS, FONT_SIZE
from frontend.styles.components import StyledButton

# Use the application's main color directly instead of a transparency
LATERAL_MENU_BG_COLOR = COLORS["background_header"]

class LateralMenu(QWidget):
    """Side menu component that slides in from the right"""

    def __init__(self, parent=None, width=320):  # Increased from 280 to 320px to make it wider
        super().__init__(parent)
        self.parent = parent
        self.width = width
        self.is_open = False

        # Configure the widget
        self.setFixedWidth(self.width)
        # Apply the style to the main widget using the main color
        self.setStyleSheet(f"""
            background-color: {LATERAL_MENU_BG_COLOR};
            border-left: 1px solid {COLORS['border_light']};
        """)

        # Initially hidden off screen
        if parent:
            self.setGeometry(parent.width(), 0, self.width, parent.height())

        # Create an inner container with the same background color
        self.content_widget = QWidget(self)
        self.content_widget.setStyleSheet(f"background-color: {LATERAL_MENU_BG_COLOR}; border: none;")

        # Main layout inside the inner container
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(15, 20, 15, 20)
        self.layout.setSpacing(0)  # Remove the spacing between widgets

        # Layout for the main widget that will hold the inner widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.content_widget)

        # Create the container for the menu header (title + close button)
        header_container = QWidget()
        header_container.setStyleSheet(f"background-color: {LATERAL_MENU_BG_COLOR}; border: none;")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Menu title with a consistent background
        title = QLabel("Menu")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: {FONT_SIZE['xxlarge']};
            font-weight: bold;
            background-color: {LATERAL_MENU_BG_COLOR};
            border: none;
        """)

        # Get the path to the close icon
        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        images_path = os.path.join(self.base_path, "frontend", "images")
        close_icon_path = os.path.join(images_path, "close_icon.png")

        # Add a button to close the menu in the top right corner
        close_btn = QPushButton()
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)

        # Use the close icon if it exists; otherwise use text
        if os.path.exists(close_icon_path):
            close_btn.setIcon(QIcon(close_icon_path))
            close_btn.setIconSize(QSize(20, 20))
        else:
            close_btn.setText("✖")

        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LATERAL_MENU_BG_COLOR};
                color: {COLORS['text_primary']};
                border: none;
                font-size: 16px;
                padding: 4px;
                border-radius: 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['button_danger_hover']};
                color: white;
            }}
        """)
        close_btn.clicked.connect(self.toggle)

        # Add the title and the close button to the header
        header_layout.addStretch(1)
        header_layout.addWidget(title, 0, Qt.AlignCenter)
        header_layout.addStretch(1)
        header_layout.addWidget(close_btn, 0, Qt.AlignRight | Qt.AlignVCenter)

        # Add the header container to the main layout
        self.layout.addWidget(header_container)
        self.layout.addSpacing(10)

        # Separator
        self.add_separator()
        self.layout.addSpacing(10)

        # Animation used for the sliding
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.setDuration(250)

    def add_separator(self):
        """Adds a separator line to the menu"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"""
            background-color: {LATERAL_MENU_BG_COLOR};
            color: {COLORS['border_light']};
            border: none;
        """)
        separator.setFixedHeight(1)
        self.layout.addWidget(separator)

    def add_menu_button(self, text, icon_path=None, callback=None, button_type="primary"):
        """Adds a button with an icon and text to the side menu"""
        # Container for the button with a consistent background
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Create a QPushButton instead of a QWidget for better event handling
        button = QPushButton()
        button.setObjectName("menuButton")
        button.setFixedHeight(60)  # Fixed height for every button
        button.setCursor(Qt.PointingHandCursor)

        # Create the inner layout that arranges the icon and the text
        button_layout = QHBoxLayout(button)
        button_layout.setContentsMargins(20, 10, 20, 10)  # Inner padding for the whole button
        button_layout.setSpacing(15)  # Space between the icon and the text

        # Add the icon if it exists
        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            icon_label.setAlignment(Qt.AlignCenter)
            button_layout.addWidget(icon_label)

        # Add the text
        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignVCenter)

        # Set the colors according to the button type

        if button_type == "danger":
            # Apply the red color directly to the "Log Out" label
            text_label.setStyleSheet(f"color: {COLORS['button_danger']}; background-color: transparent;")
        else:
            # Normal color for every other button
            text_label.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: transparent;")

        hover_bg = COLORS['button_danger_hover_sky'] if button_type == "danger" else COLORS['background_readonly']
        hover_text = "white" if button_type == "danger" else COLORS['button_primary']
        hover_border = COLORS['button_danger'] if button_type == "danger" else COLORS['button_primary']

        # Unified style for the whole button
        button.setStyleSheet(f"""
            #menuButton {{
                background-color: {LATERAL_MENU_BG_COLOR};
                border-radius: 10px;
                text-align: left;
                padding: 10px;
                margin: 5px 0px;
                border: none;
            }}
            #menuButton:hover {{
                background-color: {hover_bg};
                border-left: 4px solid {hover_border};
            }}
            #menuButton QLabel {{
                font-size: {FONT_SIZE['large']};
                background-color: transparent;
                border: none;
            }}
            #menuButton:hover QLabel {{
                color: {hover_text};
                font-weight: bold;
            }}
        """)

        button_layout.addWidget(text_label)
        button_layout.addStretch()

        # Connect the callback
        if callback:
            button.clicked.connect(callback)

        # Add the button to the container
        container_layout.addWidget(button)

        # Add bottom space with a proportional margin
        container_layout.addSpacing(10)

        # Add the container to the main layout
        self.layout.addWidget(container)

        return button

    def add_spacer(self):
        """Adds a flexible space with a consistent background"""
        # Create a widget used as a spacer with a consistent background
        spacer = QFrame()  # Use QFrame instead of QWidget for more control
        spacer.setFrameShape(QFrame.NoFrame)
        spacer.setStyleSheet(f"""
            QFrame {{
                background-color: {LATERAL_MENU_BG_COLOR};
                border: none;
            }}
        """)
        # Set the size policy so it expands vertically
        spacer.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        # Disable the widget transparency
        spacer.setAttribute(Qt.WA_TranslucentBackground, False)
        spacer.setAttribute(Qt.WA_NoSystemBackground, False)
        self.layout.addWidget(spacer, 1)  # Add it with a stretch factor of 1

    def toggle(self):
        """Opens or closes the side menu"""
        if not self.parent:
            return

        # Stop any previous animation
        self.animation.stop()

        if not self.is_open:
            # Make sure the widget is visible before the animation
            self.show()

            # Position it off screen
            start_x = self.parent.width()
            end_x = self.parent.width() - self.width

            self.setGeometry(start_x, 0, self.width, self.parent.height())

            # Set up the opening animation
            self.animation.setStartValue(QRect(start_x, 0, self.width, self.parent.height()))
            self.animation.setEndValue(QRect(end_x, 0, self.width, self.parent.height()))
        else:
            # Set up the closing animation
            start_x = self.x()
            end_x = self.parent.width()

            # Set up the animation
            self.animation.setStartValue(QRect(start_x, 0, self.width, self.parent.height()))
            self.animation.setEndValue(QRect(end_x, 0, self.width, self.parent.height()))

        # Connect the event that hides the menu once it finishes closing
        if self.is_open:
            self.animation.finished.connect(self._hide_when_closed)
        else:
            try:
                self.animation.finished.disconnect()
            except TypeError:
                # There were no previous connections
                pass

        # Start the animation and update the state
        self.animation.start()
        self.is_open = not self.is_open

    def _hide_when_closed(self):
        """Hides the widget when the closing animation finishes"""
        if not self.is_open:
            self.hide()
        try:
            self.animation.finished.disconnect()
        except TypeError:
            pass

    def resizeEvent(self, event):
        """Updates the position when the main window is resized"""
        super().resizeEvent(event)
        if self.parent:
            if self.is_open:
                self.setGeometry(self.parent.width() - self.width, 0, self.width, self.parent.height())
            else:
                self.setGeometry(self.parent.width(), 0, self.width, self.parent.height())

    def adjust_for_screen_size(self):
        """Adjusts the menu elements to the screen size for responsiveness"""
        if not self.parent:
            return

        # Get the screen dimensions
        screen_width = self.parent.width()
        screen_height = self.parent.height()

        # Compute the responsive menu width (between 280px and 25% of the screen width)
        menu_width = max(min(int(screen_width * 0.25), 420), 280)
        self.width = menu_width
        self.setFixedWidth(menu_width)

        # Compute the proportional button height (between 50px and 10% of the height)
        button_height = max(min(int(screen_height * 0.08), 70), 50)

        # Adjust the font size to the screen
        font_size = max(min(int(screen_height * 0.016), 18), 14)

        # Adjust the spacing to the screen size
        horizontal_margin = max(min(int(screen_width * 0.02), 25), 15)
        self.layout.setContentsMargins(horizontal_margin, 20, horizontal_margin, 20)

        # Walk through the buttons and adjust their dimensions
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, QWidget):
                for child in widget.findChildren(QPushButton, "menuButton"):
                    child.setFixedHeight(button_height)
                    # Update the style to change the font size
                    style = child.styleSheet()
                    style = style.replace(f"font-size: {FONT_SIZE['large']}", f"font-size: {font_size}px")
                    child.setStyleSheet(style)

        # Update the position if it is open
        if self.is_open and self.parent:
            self.setGeometry(self.parent.width() - self.width, 0, self.width, self.parent.height())


class MenuToggleButton(QPushButton):
    """Button that shows/hides the side menu"""

    def __init__(self, parent=None, lateral_menu=None):
        super().__init__(parent)
        self.lateral_menu = lateral_menu

        # Path to the menu image
        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        images_path = os.path.join(self.base_path, "frontend", "images")
        self.menu_icon_path = os.path.join(images_path, "menu_icon.png")

        # Configure the appearance
        self.setText("")
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 4px;
            }}
        """)

        # Use the icon if it exists; otherwise show the text
        if os.path.exists(self.menu_icon_path):
            self.setIcon(QIcon(self.menu_icon_path))
            self.setIconSize(QSize(24, 24))
        else:
            self.setText("☰")
            self.setStyleSheet(self.styleSheet() + f"""
                QPushButton {{
                    color: {COLORS['text_primary']};
                    font-size: 18px;
                }}
            """)

        # Connect the event
        self.clicked.connect(self.toggle_menu)

    def toggle_menu(self):
        """Toggles the state of the side menu"""
        if self.lateral_menu:
            self.lateral_menu.toggle()
