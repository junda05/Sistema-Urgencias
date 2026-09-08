from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import sys
import os
from frontend.login_interface import LoginInterface
from frontend.styles.animation_components import SplashScreen

if __name__ == "__main__":
    # The Windows console defaults to a legacy code page, so writing a patient
    # name that falls outside it raises and aborts whatever operation was
    # logging. Patient names are free text, so force UTF-8 on the streams and
    # never let logging be the thing that fails.
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    # Must be set before QApplication is created
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)

    # Set the application-level icon
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    icon_path = os.path.join(base_path, "frontend", "images", "logo.png")
    logo_path = os.path.join(base_path, "frontend", "images", "logo.png")

    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Screen size, used to keep the splash screen responsive
    screen = QDesktopWidget().screenGeometry()

    # Show the loading splash screen
    splash = SplashScreen(None, logo_path=logo_path, message="Starting application...", duration=2)
    splash.setFixedSize(int(screen.width() * 0.3), int(screen.height() * 0.3))

    # Bring the splash screen to the foreground
    splash.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    splash.setAttribute(Qt.WA_DeleteOnClose, False)

    splash.show()
    splash.opacity_animation.start()
    app.processEvents()
    splash.exec_()

    login = LoginInterface()
    login.show()
    login.setWindowState(login.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
    login.raise_()
    login.activateWindow()
    app.processEvents()
    sys.exit(app.exec_())
