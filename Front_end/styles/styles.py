# Colores
COLORS = {
    # Fondos
    "background_primary": "#F0F5FA",
    "background_white": "white",
    "background_warning": "#FFF9C2",
    "background_error": "#FFE8E8",
    "background_readonly": "#E8F0F7",
    "background_transparent": "transparent",
    "background_table_header": "#E6E6E6",
    'background_secondary': '#ffffff',
    'background_login': '#4A7296',
    'background_header': '#D5E5F3',  # Color del header con logo
    
    # Bordes
    "border": "#A0B4C6",  # Borde general predeterminado
    "border_light": "#A0B4C6",
    "border_medium": "#C0D4E6",
    "border_warning": "#E6D78A",
    "border_error": "#E6C0C0",
    "border_required": "#D35400",
    "border_focus": "#5385B7",
    "border_table": "#CCCCCC",
    'border_default': '#ced4da',
    
    # Botones
    "button_primary": "#5385B7",
    "button_primary_hover": "#659BD1",
    "button_danger": "#B75353",
    "button_danger_hover": "#D16565",
    "button_danger_hover_sky": "#E1A5A5",
    "button_warning": "#E6B800",
    "button_warning_hover": "#FFCC00",
    "button_close": "red",
    "button_transparent": "rgba(0, 0, 0, 0.1)",
    'button_secondary': '#6c757d',
    'button_success': '#28a745',
    'button_logout': '#FF6B6B',
    
    # Acentos
    "accent": "#5385B7",         # Color principal de acento (igual que button_primary)
    "accent_light": "#659BD1",    # Versión más clara para estados hover (igual que button_primary_hover)
    
    # Textos
    "text_primary": "#333333",
    "text_light": "#555555",
    "text_white": "white",
    "text_required": "#D35400",
    "link": "#0066cc",  # Añadido: color para enlaces
    'text_secondary': '#6c757d',
    
    # Alarmas
    "alarm_normal": "#FFA500",  # Naranja
    "alarm_observation": "#9370DB",  # Púrpura suave
    'hover_row': '#f8f9fa',
    'triage1': '#ff0000',  # Rojo
    'triage2': '#ffa500',  # Naranja
    'triage3': '#ffff00',  # Amarillo
    'triage4': '#008000',  # Verde
    'triage5': '#0000ff',  # Azul
    'triage_no': '#808080',  # Gris
}

# Propiedades comunes
BORDER_RADIUS = {
    "small": "5px",
    "medium": "8px",
    "large": "10px",
    "xlarge": "15px",
}

FONT_SIZE = {
    "small": "12px",
    "normal": "14px",
    "medium": "16px",
    "large": "18px",
    "xlarge": "20px",
    "xxlarge": "24px",
}

PADDING = {
    "small": "5px",
    "medium": "10px",
    "large": "15px",
    "xlarge": "20px",
    "xxlarge": "30px",
}

# Estilos de componentes
LINE_EDIT_STYLES = {
    "normal": f"""
        QLineEdit {{
            background-color: {COLORS["background_white"]};
            color: {COLORS["text_primary"]};
            border: 2px solid {COLORS["border_focus"]};
            padding: {PADDING["medium"]};
            border-radius: {BORDER_RADIUS["medium"]};
        }}
        QLineEdit:focus {{
            border: 2px solid {COLORS["border_focus"]};
            background-color: {COLORS["background_white"]};
        }}
    """,
    "required": f"""
        QLineEdit {{
            background-color: {COLORS["background_white"]};
            color: {COLORS["text_primary"]};
            border: 2px solid {COLORS["border_required"]};
            padding: {PADDING["medium"]};
            border-radius: {BORDER_RADIUS["medium"]};
        }}
        QLineEdit:focus {{
            border: 2px solid {COLORS["border_required"]};
            background-color: {COLORS["background_white"]};
        }}
    """,
    "readonly": f"""
        QLineEdit {{
            background-color: {COLORS["background_readonly"]};
            color: {COLORS["text_light"]};
            border: 2px solid {COLORS["border_required"]};
            padding: {PADDING["medium"]};
            border-radius: {BORDER_RADIUS["medium"]};
        }}
    """,
}

COMBO_BOX_STYLES = {
    "normal": f"""
        QComboBox {{
            background-color: {COLORS["background_white"]};
            color: {COLORS["text_primary"]};
            border: 2px solid {COLORS["border_focus"]};
            padding: {PADDING["medium"]};
            border-radius: {BORDER_RADIUS["medium"]};
        }}
        QComboBox:focus {{
            border: 2px solid {COLORS["border_focus"]};
            background-color: {COLORS["background_white"]};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
            background-color: {COLORS["background_transparent"]};
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLORS["background_white"]};
            color: {COLORS["text_primary"]};
            selection-background-color: {COLORS["button_primary"]};
            selection-color: {COLORS["text_white"]};
            border: 1px solid {COLORS["border_light"]};
            padding: {PADDING["small"]};
        }}
    """,
    "required": f"""
        QComboBox {{
            background-color: {COLORS["background_white"]};
            color: {COLORS["text_primary"]};
            border: 2px solid {COLORS["border_required"]};
            padding: {PADDING["medium"]};
            border-radius: {BORDER_RADIUS["medium"]};
        }}
        QComboBox:focus {{
            border: 2px solid {COLORS["border_required"]};
            background-color: {COLORS["background_white"]};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
            background-color: {COLORS["background_transparent"]};
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLORS["background_white"]};
            color: {COLORS["text_primary"]};
            selection-background-color: {COLORS["button_primary"]};
            selection-color: {COLORS["text_white"]};
            border: 1px solid {COLORS["border_light"]};
            padding: {PADDING["small"]};
        }}
    """,
}

BUTTON_STYLES = {
    "primary": f"""
        QPushButton {{
            background-color: {COLORS["button_primary"]};
            color: {COLORS["text_white"]};
            border: none;
            border-radius: {BORDER_RADIUS["medium"]};
            padding: {PADDING["medium"]} {PADDING["large"]};
            font-size: {FONT_SIZE["normal"]};
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: {COLORS["button_primary_hover"]};
        }}
    """,
    "danger": f"""
        QPushButton {{
            background-color: {COLORS["button_danger"]};
            color: {COLORS["text_white"]};
            border: none;
            border-radius: {BORDER_RADIUS["medium"]};
            padding: {PADDING["medium"]} {PADDING["large"]};
            font-size: {FONT_SIZE["normal"]};
        }}
        QPushButton:hover {{
            background-color: {COLORS["button_danger_hover"]};
        }}
    """,
    "warning": f"""
        QPushButton {{
            background-color: {COLORS["button_warning"]};
            color: {COLORS["text_white"]};
            border: none;
            border-radius: {BORDER_RADIUS["medium"]};
            padding: {PADDING["medium"]} {PADDING["large"]};
            font-size: {FONT_SIZE["normal"]};
        }}
        QPushButton:hover {{
            background-color: {COLORS["button_warning_hover"]};
        }}
    """,
    "window_control": lambda is_close=False: f"""
        QPushButton {{
            background-color: {COLORS["background_transparent"]};
            border: none;
            color: black;
            font-size: {FONT_SIZE["medium"]};
        }}
        QPushButton:hover {{
            background-color: {COLORS["button_close"] if is_close else COLORS["button_transparent"]};
            {"color: white;" if is_close else ""}
            border-radius: {BORDER_RADIUS["small"]};
        }}
    """,
}

LABEL_STYLES = {
    "normal": f"""
        color: {COLORS["text_primary"]};
        font-weight: bold;
        background-color: {COLORS["background_transparent"]};
    """,
    "title": f"""
        font-size: {FONT_SIZE["xxlarge"]};
        font-weight: bold;
        color: {COLORS["text_primary"]};
        background-color: {COLORS["background_transparent"]};
    """,
    "required": f"""
        color: {COLORS["text_primary"]};
        font-weight: 900;
        background-color: {COLORS["background_transparent"]};
    """,
    "required_indicator": f"""
        color: {COLORS["text_required"]};
        font-style: italic;
        background-color: {COLORS["background_transparent"]};
    """,
}

TABLE_STYLES = {
    "main": f"""
        QTableWidget {{
            background-color: {COLORS["background_white"]}; 
            font-size: 17px;
            border: 1px solid #ccc;
            border-radius: {BORDER_RADIUS["medium"]};
        }}
        QHeaderView::section {{
            background-color: {COLORS["background_table_header"]};
            color: {COLORS["text_primary"]};
            padding: {PADDING["medium"]};
            font-weight: bold;
            border: 1px solid {COLORS["border_table"]};
        }}
    """,
}

TABLE_STYLES_UPDATED = {
    "main": f"""
        QTableWidget {{
            background-color: {COLORS['background_white']};
            gridline-color: {COLORS['border_light']};
            border: none;
            border-radius: {BORDER_RADIUS['medium']};
            padding: 3px;
            selection-background-color: #E3F2FD; /* Color más claro para selección */
        }}
        QTableWidget::item:selected {{
            background-color: #E3F2FD; /* Color más claro para selección */
            color: {COLORS['text_primary']};
        }}
        QTableWidget::item:hover {{
            background-color: #F5F9FF; /* Color muy ligero para hover */
        }}
        QHeaderView::section {{
            background-color: {COLORS['background_header']};
            color: {COLORS['text_primary']};
            padding: 10px 5px;
            border: 1px solid {COLORS['border_light']};
            font-weight: bold;
        }}
        QTableCornerButton::section {{
            background-color: {COLORS['background_header']};
            border: 1px solid {COLORS['border_light']};
        }}
        /* Tooltip styling with lighter background */
        QToolTip {{
            background-color: #FFFFFF;
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border_light']};
            padding: 8px;
            border-radius: 4px;
            font-size: 14px;
            opacity: 225;
        }}
    """
}

LIST_WIDGET_STYLES = {
    "main": f"""
        QListWidget {{
            background-color: {COLORS["background_white"]};
            border-radius: {BORDER_RADIUS["medium"]};
            padding: {PADDING["small"]};
            border: 1px solid {COLORS["border_light"]};
            font-size: {FONT_SIZE["normal"]};
            color: {COLORS["text_primary"]};
        }}
    """,
}

MENU_STYLES = {
    "main": f"""
        QMenu {{
            background-color: {COLORS["background_primary"]};
            color: {COLORS["text_primary"]};
            border: 1px solid {COLORS["border_medium"]};
            border-radius: {BORDER_RADIUS["small"]};
            padding: {PADDING["small"]};
        }}
        QMenu::item {{
            padding: 6px 25px 6px 20px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {COLORS["button_primary"]};
            color: {COLORS["text_white"]};
        }}
    """,
}

# Estilos compuestos
DIALOG_STYLE = f"""
    QDialog {{
        background-color: {COLORS["background_primary"]};
        border-radius: {BORDER_RADIUS["xlarge"]};
    }}
    QLabel {{
        color: {COLORS["text_primary"]};
        font-size: {FONT_SIZE["medium"]};
        background-color: {COLORS["background_transparent"]};
    }}
    QLineEdit, QComboBox {{
        padding: {PADDING["medium"]};
        background-color: {COLORS["background_white"]};
        border-radius: {BORDER_RADIUS["medium"]};
        border: 1px solid {COLORS["border_light"]};
        font-size: {FONT_SIZE["normal"]};
        min-height: 20px;
        color: {COLORS["text_primary"]};
    }}
    QComboBox:focus, QLineEdit:focus {{
        border: 2px solid {COLORS["border_focus"]};
        background-color: {COLORS["background_white"]};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
        background-color: {COLORS["background_transparent"]};
    }}
    QComboBox::down-arrow {{
        image: url(dropdown.png);
        width: 12px;
        height: 12px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLORS["background_white"]};
        color: {COLORS["text_primary"]};
        selection-background-color: {COLORS["button_primary"]};
        selection-color: {COLORS["text_white"]};
        border: 1px solid {COLORS["border_light"]};
        border-radius: {BORDER_RADIUS["small"]};
        padding: {PADDING["small"]};
    }}
    QPushButton {{
        background-color: {COLORS["button_primary"]};
        color: {COLORS["text_white"]};
        border: none;
        border-radius: {BORDER_RADIUS["medium"]};
        padding: {PADDING["medium"]} {PADDING["large"]};
        font-size: {FONT_SIZE["normal"]};
        min-width: 100px;
    }}
    QPushButton:hover {{
        background-color: {COLORS["button_primary_hover"]};
    }}
    QListWidget {{
        background-color: {COLORS["background_white"]};
        border-radius: {BORDER_RADIUS["medium"]};
        padding: {PADDING["small"]};
        border: 1px solid {COLORS["border_light"]};
        font-size: {FONT_SIZE["normal"]};
        color: {COLORS["text_primary"]};
    }}
    QMenu {{
        background-color: {COLORS["background_primary"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["border_medium"]};
        border-radius: {BORDER_RADIUS["small"]};
        padding: {PADDING["small"]};
    }}
    QMenu::item {{
        padding: 6px 25px 6px 20px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {COLORS["button_primary"]};
        color: {COLORS["text_white"]};
    }}
    QMessageBox {{
        background-color: {COLORS["background_primary"]};
        color: {COLORS["text_primary"]};
        border-radius: {BORDER_RADIUS["xlarge"]};
    }}
    QMessageBox QLabel {{
        color: {COLORS["text_primary"]};
        font-size: {FONT_SIZE["medium"]};
    }}
    QMessageBox QPushButton {{
        background-color: {COLORS["button_primary"]};
        color: {COLORS["text_white"]};
        border: none;
        border-radius: {BORDER_RADIUS["medium"]};
        padding: {PADDING["medium"]} {PADDING["large"]};
        font-size: {FONT_SIZE["normal"]};
        min-width: 100px;
    }}
    QMessageBox QPushButton:hover {{
        background-color: {COLORS["button_primary_hover"]};
    }}
"""

# Estilos para los distintos tipos de mensajes
MESSAGE_STYLES = {
    "info": f"""
        QMessageBox {{
            background-color: {COLORS["background_primary"]};
            color: {COLORS["text_primary"]};
            border-radius: {BORDER_RADIUS["xlarge"]};
            border: 1px solid {COLORS["border_medium"]};
        }}
        QLabel {{
            color: {COLORS["text_primary"]};
            font-size: {FONT_SIZE["medium"]};
            background-color: {COLORS["background_transparent"]};
        }}
        QPushButton {{
            background-color: {COLORS["button_primary"]};
            color: {COLORS["text_white"]};
            border: none;
            border-radius: {BORDER_RADIUS["medium"]};
            padding: {PADDING["medium"]} {PADDING["large"]};
            font-size: {FONT_SIZE["normal"]};
        }}
        QPushButton:hover {{
            background-color: {COLORS["button_primary_hover"]};
        }}
    """,
    "warning": f"""
        QMessageBox {{
            background-color: {COLORS["background_warning"]};
            color: {COLORS["text_primary"]};
            border-radius: {BORDER_RADIUS["xlarge"]};
            border: 1px solid {COLORS["border_warning"]};
        }}
        QLabel {{
            color: {COLORS["text_primary"]};
            font-size: {FONT_SIZE["medium"]};
            background-color: {COLORS["background_transparent"]};
        }}
        QPushButton {{
            background-color: {COLORS["button_warning"]};
            color: {COLORS["text_white"]};
            border: none;
            border-radius: {BORDER_RADIUS["medium"]};
            padding: {PADDING["medium"]} {PADDING["large"]};
            font-size: {FONT_SIZE["normal"]};
        }}
        QPushButton:hover {{
            background-color: {COLORS["button_warning_hover"]};
        }}
    """,
    "error": f"""
        QMessageBox {{
            background-color: {COLORS["background_error"]};
            color: {COLORS["text_primary"]};
            border-radius: {BORDER_RADIUS["xlarge"]};
            border: 1px solid {COLORS["border_error"]};
        }}
        QLabel {{
            color: {COLORS["text_primary"]};
            font-size: {FONT_SIZE["medium"]};
            background-color: {COLORS["background_transparent"]};
        }}
        QPushButton {{
            background-color: {COLORS["button_danger"]};
            color: {COLORS["text_white"]};
            border: none;
            border-radius: {BORDER_RADIUS["medium"]};
            padding: {PADDING["medium"]} {PADDING["large"]};
            font-size: {FONT_SIZE["normal"]};
        }}
        QPushButton:hover {{
            background-color: {COLORS["button_danger_hover"]};
        }}
    """,
    "confirmation": f"""
        QMessageBox {{
            background-color: {COLORS["background_primary"]};
            color: {COLORS["text_primary"]};
            border-radius: {BORDER_RADIUS["xlarge"]};
            border: 1px solid {COLORS["border_medium"]};
        }}
        QLabel {{
            color: {COLORS["text_primary"]};
            font-size: {FONT_SIZE["medium"]};
            background-color: {COLORS["background_transparent"]};
        }}
        QPushButton {{
            background-color: {COLORS["button_primary"]};
            color: {COLORS["text_white"]};
            border: none;
            border-radius: {BORDER_RADIUS["medium"]};
            padding: {PADDING["medium"]} {PADDING["large"]};
            font-size: {FONT_SIZE["normal"]};
        }}
        QPushButton:hover {{
            background-color: {COLORS["button_primary_hover"]};
        }}
        QPushButton[text="No"] {{
            background-color: {COLORS["button_danger"]};
        }}
        QPushButton[text="No"]:hover {{
            background-color: {COLORS["button_danger_hover"]};
        }}
    """
}

# Estilo para barras de desplazamiento
SCROLLBAR_STYLE = f"""
    QScrollBar:vertical {{
        background: {COLORS["background_primary"]};
        width: 12px;
        margin: 0px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS["border_light"]};
        min-height: 30px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS["button_primary"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    
    QScrollBar:horizontal {{
        background: {COLORS["background_primary"]};
        height: 12px;
        margin: 0px;
        border-radius: 6px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLORS["border_light"]};
        min-width: 30px;
        border-radius: 6px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {COLORS["button_primary"]};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
"""

# Agregar estilos para el modo presentación
PRESENTACION_STYLES = {
    "indicador": f"""
        background-color: rgba(83, 133, 183, 0.8);
        border-radius: 15px;
        border: 2px solid {COLORS['button_primary']};
        padding: 8px 12px;
    """,
    "texto": f"""
        color: white;
        background-color: transparent;
        font-size: {FONT_SIZE["normal"]};
        font-weight: bold;
    """,
    "boton_detener": f"""
        QPushButton {{
            background-color: {COLORS['button_danger']};
            color: white;
            border-radius: 12px;
            padding: 5px 12px;
            font-weight: bold;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {COLORS['button_danger_hover']};
        }}
    """
}
