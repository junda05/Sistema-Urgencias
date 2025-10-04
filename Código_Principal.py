from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import sys
import os
from Front_end.login_interface import InterfazLogin
from Front_end.styles.animation_components import SplashScreen

if __name__ == "__main__":
    # Establecer el atributo antes de crear QApplication
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    
    app = QApplication(sys.argv)
    
    # Establecer el icono a nivel de aplicación
    if getattr(sys, 'frozen', False):
        ruta_base = sys._MEIPASS
    else:
        ruta_base = os.path.dirname(os.path.abspath(__file__))
    
    ruta_icono = os.path.join(ruta_base, "Front_end", "imagenes", "logo.png")
    ruta_logo = os.path.join(ruta_base, "Front_end", "imagenes", "logo_foscal.png")
    
    if os.path.exists(ruta_icono):
        app.setWindowIcon(QIcon(ruta_icono))
    
    # Obtener el tamaño de la pantalla para hacer el splash responsivo
    pantalla = QDesktopWidget().screenGeometry()
    
    # Mostrar splash pantallas de carga
    splash = SplashScreen(None, logo_path=ruta_logo, message="Iniciando aplicación...", duration=2)
    splash.setFixedSize(int(pantalla.width() * 0.3), int(pantalla.height() * 0.3))
    
    # Establecer aparición en primer plano
    splash.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    splash.setAttribute(Qt.WA_DeleteOnClose, False)
    
    splash.show()
    splash.opacity_animation.start()
    app.processEvents()
    splash.exec_()
    
    login = InterfazLogin()
    login.show()
    login.setWindowState(login.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
    login.raise_()
    login.activateWindow()
    app.processEvents()
    sys.exit(app.exec_())