from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontDatabase

def load_fonts():
    """
    Function that loads the custom fonts into the application.
    These fonts must be located in the frontend/fonts/ folder
    """
    # Priority list with the most attractive fonts first
    available_fonts = [
        "ABeeZee",      # Prioritized as the first option
        "Montserrat",
        "Nunito",
        "Open Sans",
        "Roboto",
        "Segoe UI",     # Relegated to a fallback option
        "Calibri",
        "Verdana",
        "Tahoma"
    ]

    # Get the first font available on the system
    main_font = "Segoe UI"  # Default value

    try:
        # Create a single QFontDatabase instance
        db = QFontDatabase()

        # Get every font family available on the system
        system_fonts = db.families()

        # Look for the first font from our list that is available on the system
        for font in available_fonts:
            if font in system_fonts:
                main_font = font
                print(f"Using font: {font}")
                break

    except Exception as e:
        # On error, use the default font and log the error
        print(f"Error detecting fonts: {str(e)}. Using the default font.")

    return main_font

def apply_system_fonts():
    """
    Applies modern, legible fonts consistently across the whole application.
    This function must be called when each main interface starts.
    """
    app = QApplication.instance()

    # Get the main font (the most attractive one available)
    main_font = load_fonts()

    # Create a main font
    base_font = QFont(main_font, 10)
    app.setFont(base_font)

    # Set style sheets for specific components using the selected font
    app.setStyleSheet(f"""
        QWidget {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
        }}
        QLabel {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
        }}
        QPushButton {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
            font-weight: medium;
        }}
        QTableWidget {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
        }}
        QTableWidget QHeaderView::section {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
            font-weight: bold;
        }}
        QComboBox, QLineEdit {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
        }}
        QMessageBox {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
        }}
        QListWidget {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
        }}
        QMenu {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
        }}
        QToolTip {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
            background-color: #F0F5FA;
            color: #333333;
            border: 1px solid #A0B4C6;
            border-radius: 5px;
            padding: 4px;
        }}
        QPlainTextEdit {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
        }}
        QTextEdit {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
        }}
        QLineEdit::placeholder {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
            color: #999999;
        }}
        QTableWidget::item {{
            font-size: 10pt;
        }}
        QHeaderView {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
            font-weight: bold;
        }}
        PasswordInput QLineEdit {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
        }}
        PasswordInput QLineEdit::placeholder {{
            font-family: '{main_font}', sans-serif;
            font-size: 10pt;
        }}
    """)

    return app
