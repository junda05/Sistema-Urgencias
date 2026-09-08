from PyQt5.QtWidgets import (QDialog, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
                           QProgressBar, QGraphicsOpacityEffect, QDesktopWidget,
                           QApplication)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QPixmap
import os
import time
from frontend.styles.styles import COLORS, BORDER_RADIUS

class WorkerThread(QThread):
    """Worker thread that updates the progress in the background."""
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, duration=3):
        super().__init__()
        self.duration = duration

    def run(self):
        for i in range(101):
            self.progress.emit(i)
            time.sleep(self.duration / 100)
        self.finished.emit()

class FadeAnimation:
    """Class that creates fade-in/fade-out transitions for widgets"""

    @staticmethod
    def fade_in(widget, duration=500):
        """Gradually makes a widget appear"""
        # Create the opacity effect
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)

        # Create the animation
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration)  # duration in ms
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start(QPropertyAnimation.DeleteWhenStopped)
        return animation

    @staticmethod
    def fade_out(widget, duration=500, delete_when_done=False):
        """Gradually makes a widget disappear"""
        # Create the opacity effect
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)

        # Create the animation
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration)  # duration in ms
        animation.setStartValue(1)
        animation.setEndValue(0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Connect the finished signal if the widget must be deleted when it ends
        if delete_when_done:
            animation.finished.connect(widget.deleteLater)

        animation.start(QPropertyAnimation.DeleteWhenStopped)
        return animation

    @staticmethod
    def slide_in_from_bottom(widget, duration=500):
        """Makes a widget appear by sliding in from the bottom"""
        # Store the final position
        target_pos = widget.pos()

        # Move the widget off screen (below)
        start_pos = QPoint(target_pos.x(), target_pos.y() + widget.height())
        widget.move(start_pos)

        # Create the animation
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(target_pos)
        animation.setEasingCurve(QEasingCurve.OutQuad)
        animation.start(QPropertyAnimation.DeleteWhenStopped)
        return animation

class SplashScreen(QDialog):
    """Loading screen with a logo, a message and a progress bar."""

    def __init__(self, parent=None, logo_path=None, message="Loading...", autoclose=True, duration=3):
        super().__init__(parent, Qt.FramelessWindowHint)
        self.setModal(True)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Settings
        self.duration = duration
        self.autoclose = autoclose

        # Get the screen size so everything can be responsive
        screen = QDesktopWidget().screenGeometry()

        # Create the main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Create the container with a background
        self.container = QWidget(self)
        self.container.setObjectName("container")
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(15)

        # Consistent style for every loading screen
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background_primary']};
                border-radius: {BORDER_RADIUS['xlarge']};
                border: 2px solid {COLORS['button_primary']};
            }}
        """)

        self.container.setStyleSheet(f"""
            #container {{
                background-color: {COLORS['background_primary']};
                border-radius: {BORDER_RADIUS['xlarge']};
            }}
        """)

        # Logo
        if logo_path and os.path.exists(logo_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path)

            logo_width = int(screen.width() * 0.15)  # 15% of the screen width

            logo_scaled = logo_pixmap.scaled(logo_width, logo_width, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_scaled)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet(f"background: {COLORS['background_transparent']};")
            container_layout.addWidget(logo_label)

        # Message with a consistent style
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)

        # Compute a responsive font size
        font_size = int(screen.height() * 0.018)  # 1.8% of the screen height

        message_label.setStyleSheet(f"""
            color: {COLORS['button_primary']};
            font-size: {font_size}px;
            font-weight: bold;
            margin: 10px;
            background-color: {COLORS['background_transparent']};
        """)

        container_layout.addWidget(message_label)

        # Progress bar with a consistent style
        bar_height = int(screen.height() * 0.01)  # 1% of the screen height

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(bar_height)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['background_readonly']};
                border-radius: {BORDER_RADIUS['small']};
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['button_primary']};
                border-radius: {BORDER_RADIUS['small']};
            }}
        """)
        container_layout.addWidget(self.progress_bar)

        # Add the container to the main layout
        layout.addWidget(self.container)

        # Center it on screen and set a responsive size
        splash_width = int(screen.width() * 0.25)  # 25% of the screen width
        splash_height = int(screen.height() * 0.25)  # 25% of the screen height

        self.setFixedSize(splash_width, splash_height)

        # Worker thread that drives the progress
        self.worker = WorkerThread(duration=self.duration)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.finish_loading)

        # Entrance effect with a fade-in
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(300)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Make sure it stays centered even after setFixedSize
        self.center_on_screen()

    def center_on_screen(self):
        """Centers the window on the screen"""
        screen = QDesktopWidget().screenGeometry()
        self.move(
            int((screen.width() - self.width()) / 2),
            int((screen.height() - self.height()) / 2)
        )

    def setFixedSize(self, width, height):
        """Overrides setFixedSize so the window is centered after resizing"""
        super().setFixedSize(width, height)
        self.center_on_screen()

    def start_loading(self):
        """Starts the loading process."""
        self.worker.start()

    def update_progress(self, value):
        """Updates the progress bar."""
        self.progress_bar.setValue(value)

    def finish_loading(self):
        """Called when the loading finishes."""
        if self.autoclose:
            self.accept()

    def showEvent(self, event):
        """Called when the loading screen is shown."""
        super().showEvent(event)
        # Start the animation when it is shown
        QTimer.singleShot(100, self.start_loading)

    def set_message(self, message):
        """Changes the message displayed on the loading screen."""
        # Look for the message label and update its text
        for child in self.container.children():
            if isinstance(child, QLabel) and child.text() != "":
                child.setText(message)
                break
