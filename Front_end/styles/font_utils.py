from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontDatabase

def cargar_fuentes():
    """
    Función que carga las fuentes personalizadas en la aplicación.
    Estas fuentes deben estar en la carpeta Front_end/fonts/
    """
    # Lista priorizada de fuentes más atractivas primero
    fuentes_disponibles = [
        "ABeeZee",      # Priorizada como primera opción
        "Montserrat",
        "Nunito", 
        "Open Sans",
        "Roboto",
        "Segoe UI",     # Relegada a opción de respaldo
        "Calibri", 
        "Verdana", 
        "Tahoma"
    ]
    
    # Obtener la primera fuente disponible en el sistema
    fuente_principal = "Segoe UI"  # Valor predeterminado
    
    try:
        # Crear una única instancia de QFontDatabase
        db = QFontDatabase()
        
        # Obtener todas las familias de fuentes disponibles en el sistema
        fuentes_sistema = db.families()
        
        # Buscar la primera fuente de nuestra lista que esté disponible en el sistema
        for fuente in fuentes_disponibles:
            if fuente in fuentes_sistema:
                fuente_principal = fuente
                print(f"Usando fuente: {fuente}")
                break
                
    except Exception as e:
        # En caso de error, usar la fuente predeterminada y registrar el error
        print(f"Error al detectar fuentes: {str(e)}. Usando fuente predeterminada.")
            
    return fuente_principal

def aplicar_fuentes_sistema():
    """
    Aplica fuentes modernas y legibles a toda la aplicación de manera consistente.
    Esta función debe llamarse al inicio de cada interfaz principal.
    """
    app = QApplication.instance()
    
    # Obtener la fuente principal (más atractiva disponible)
    fuente_principal = cargar_fuentes()
    
    # Crear una fuente principal
    fuente_base = QFont(fuente_principal, 10)
    app.setFont(fuente_base)
    
    # Establecer hojas de estilo para componentes específicos con la fuente seleccionada
    app.setStyleSheet(f"""
        QWidget {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
        }}
        QLabel {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
        }}
        QPushButton {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
            font-weight: medium;
        }}
        QTableWidget {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
        }}
        QTableWidget QHeaderView::section {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
            font-weight: bold;
        }}
        QComboBox, QLineEdit {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
        }}
        QMessageBox {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
        }}
        QListWidget {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
        }}
        QMenu {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
        }}
        QToolTip {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
            background-color: #F0F5FA;
            color: #333333;
            border: 1px solid #A0B4C6;
            border-radius: 5px;
            padding: 4px;
        }}
        QPlainTextEdit {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
        }}
        QTextEdit {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
        }}
        QLineEdit::placeholder {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
            color: #999999;
        }}
        QTableWidget::item {{
            font-size: 10pt;
        }}
        QHeaderView {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
            font-weight: bold;
        }}
        EntradaContrasena QLineEdit {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
        }}
        EntradaContrasena QLineEdit::placeholder {{
            font-family: '{fuente_principal}', sans-serif;
            font-size: 10pt;
        }}
    """)
    
    return app