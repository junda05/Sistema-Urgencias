from PyQt5.QtWidgets import QPushButton, QAction, QHBoxLayout, QLabel, QWidget, QLineEdit, QFrame, QVBoxLayout, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
from frontend.styles.styles import COLORS, BORDER_RADIUS

class IconButton(QPushButton):
    """Button with a customizable icon and text."""

    def __init__(self, text, icon_path=None, color="#659BD1", hover_color=None, parent=None):
        super().__init__(text, parent)

        # Use a softer, more elegant background color
        if color == COLORS['background_header']:
            color = "#D5E5F3"  # Very soft blue
            hover_color = "#E8F0FE"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 2px;
                padding: 12px 5px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 25px;
                min-height: 40px;
                icon-size: 35px 35px;  /* Icon size */
                text-align: center;
                border-bottom: 2px solid rgba(0, 0, 0, 0.1);
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                border-bottom: 2px solid rgba(0, 0, 0, 0.2);
            }}
            QPushButton:pressed {{
                background-color: {self._adjust_color(color, False)};
                border-bottom: 1px solid rgba(0, 0, 0, 0.2);
                padding-top: 13px;
            }}
        """)

        # Set the icon with a larger size if one is provided
        if icon_path:
            icon = QIcon(icon_path)
            self.setIcon(icon)
            self.setIconSize(QSize(40, 40))  # Slightly larger icons
            self.setText("   " + text)
        # Hand cursor when hovering over it
        self.setCursor(Qt.PointingHandCursor)

    def _adjust_color(self, color, brighter=True):
        """Adjusts the color for the hover effect"""
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)

            if brighter:
                # Lighten for hover
                factor = 1.1
                r = min(255, int(r*factor))
                g = min(255, int(g*factor))
                b = min(255, int(b*factor))
            else:
                # Darken for hover
                factor = 0.9
                r = int(r*factor)
                g = int(g*factor)
                b = int(b*factor)

            return f'#{r:02x}{g:02x}{b:02x}'
        return color

class LogoutButton(QWidget):
    """Log out button with an icon."""

    def __init__(self, parent=None, icon_path=None, logout_func=None, corner="bottom-right"):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.button = QPushButton("Log Out")
        self.button.setCursor(Qt.PointingHandCursor)

        # Set the color according to the corner where it will be placed
        if corner == "bottom-right":
            button_color = COLORS['button_logout']
            hover_color = self._adjust_color(button_color)
        else:
            button_color = COLORS['button_primary']
            hover_color = COLORS['button_primary_hover']

        # Set the icon if one is provided
        if icon_path:
            icon = QIcon(icon_path)
            self.button.setIcon(icon)
            self.button.setIconSize(QSize(22, 22))

        self.button.setStyleSheet(f"""
            QPushButton {{
                background-color: {button_color};
                color: white;
                border: none;
                border-radius: {BORDER_RADIUS['medium']};
                padding: 8px 15px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: bold;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                border: 1px solid white;
            }}
        """)

        if logout_func:
            self.button.clicked.connect(logout_func)

        layout.addWidget(self.button)
        self.setFixedWidth(150)

    def _adjust_color(self, color, brighter=True):
        """Adjusts the color for the hover effect"""
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)

            if brighter:
                # Lighten for hover
                factor = 1.1
                r = min(255, int(r*factor))
                g = min(255, int(g*factor))
                b = min(255, int(b*factor))
            else:
                # Darken for hover
                factor = 0.9
                r = int(r*factor)
                g = int(g*factor)
                b = int(b*factor)

            return f'#{r:02x}{g:02x}{b:02x}'
        return color

class SearchContainer(QWidget):
    """Search container styled similarly to the buttons."""

    def __init__(self, parent=None, height=None):
        super().__init__(parent)

        # Use the same colors as IconButton for consistency
        color = "#D5E5F3"  # Very soft blue

        # Create a main frame that will hold everything
        self.frame = QFrame(self)
        self.frame.setObjectName("searchContainerFrame")
        self.frame.setStyleSheet(f"""
            #searchContainerFrame {{
                background-color: {color};
                border-radius: 2px;
                border: none;
                border-bottom: 2px solid rgba(0, 0, 0, 0.1);
            }}
        """)

        # Main layout that holds the frame
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.frame)

        # Inner layout for the search components
        self.layout = QHBoxLayout(self.frame)
        self.layout.setContentsMargins(15, 0, 15, 0)  # Reduce the vertical margins
        self.layout.setSpacing(20)

        # Create the inner components
        self.icon_label = QLabel()
        self.icon_label.setStyleSheet("background-color: transparent;")
        self.icon_label.setFixedSize(35, 35)  # Fixed size for the icon

        # "Search" text with the same style as the buttons
        self.text_label = QLabel("Search")
        self.text_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 25px;
            background-color: transparent;
            font-family: 'Segoe UI', sans-serif;
        """)

        # Search field - adjusted so it takes up all the available vertical space
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter a name or document ID to search")
        self.search_input.setStyleSheet(f"""
            background-color: #E8F0FE;
            color: {COLORS['text_primary']};
            font-size: 16px;
            border: none;
            padding: 8px;
            min-height: 30px;  /* Minimum height for the field */
        """)
        self.search_input.setClearButtonEnabled(True)

        # Adjust the style of the clear button (x) so it is vertically centered
        self.search_input.findChild(QAction).setIcon(QIcon())  # Remove the default icon
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #E8F0FE;
                color: {COLORS['text_primary']};
                font-size: 16px;
                border: none;
                padding: 8px 25px 8px 8px;  /* Right padding for the clear button */
                min-height: 30px;
            }}
            QLineEdit::clear-button {{
                subcontrol-position: right center;  /* Positioned right and vertically centered */
                subcontrol-origin: padding;         /* Origin from the padding */
                image: none;                        /* No default image */
                width: 20px;                        /* Fixed width */
                height: 20px;                       /* Fixed height */
                margin-right: 5px;                  /* Right margin */
                background: transparent;            /* Transparent background */
            }}
            QLineEdit::clear-button:hover {{
                background-color: rgba(0, 0, 0, 0.1); /* Background on mouse hover */
                border-radius: 10px;                 /* Rounded border */
            }}
        """)

        # Add the components to the layout
        self.layout.addWidget(self.icon_label, 0, Qt.AlignVCenter)
        self.layout.addWidget(self.text_label, 0, Qt.AlignVCenter)
        self.layout.addWidget(self.search_input, 1)

        # If a height is provided, use it; otherwise use a default value
        if height is not None:
            self.setFixedHeight(height)
            # Apply the same height to the inner frame, leaving room for the border
            self.frame.setFixedHeight(height)
        else:
            # Default height similar to the IconButton buttons
            self.setFixedHeight(65)
            self.frame.setFixedHeight(65)

        # Size policies to keep it responsive
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Make sure the QLineEdit takes up the full available height
        field_height = height - 20 if height else 45  # Leave room for the paddings
        self.search_input.setMinimumHeight(field_height)

    def set_icon(self, icon_path=None, size=35):
        """Sets the search icon."""
        from PyQt5.QtGui import QPixmap
        import os

        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.icon_label.setText("🔍")
            self.icon_label.setStyleSheet("background-color: transparent; font-size: 20px;")

    def get_search_input(self):
        """Returns the QLineEdit so signals can be connected."""
        return self.search_input
