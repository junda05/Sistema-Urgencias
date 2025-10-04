from Front_end.styles.styles import COLORS, BORDER_RADIUS, PADDING, FONT_SIZE

def login_input_style(alto_contenedor, tamano_inputs=None):
    """
    Creates a consistent style for login input fields
    
    Args:
        alto_contenedor: Container height for proportional calculations
        tamano_inputs: Optional input font size override
    
    Returns:
        str: CSS style string
    """
    font_size = tamano_inputs if tamano_inputs else FONT_SIZE['medium']
    
    return f"""
        padding: {PADDING['medium']};
        border: 2px solid {COLORS['border_focus']};
        border-radius: {BORDER_RADIUS['xlarge']};
        background-color: rgba(240, 245, 250, 0.9);
        margin: 5px;
        min-height: {int(alto_contenedor * 0.06)}px;
        font-size: {font_size};
    """

def login_error_input_style(container_height, tamano_inputs=None):
    """
    Creates a consistent error style for login input fields
    
    Args:
        container_height: Container height for proportional calculations
        tamano_inputs: Optional input font size override
    
    Returns:
        str: CSS style string
    """
    font_size = tamano_inputs if tamano_inputs else FONT_SIZE['medium']
    
    return f"""
        padding: {PADDING['medium']};
        border: 2px solid {COLORS['button_danger']};
        border-radius: {BORDER_RADIUS['xlarge']};
        background-color: rgba(255, 230, 230, 0.85);
        margin: 5px;
        min-height: {int(container_height * 0.03)}px;
        font-size: {font_size};
    """
