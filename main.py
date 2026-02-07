import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QListWidget, QFileDialog, QPushButton, QMessageBox
)
from core.control_autostart import ensure_admin
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QGuiApplication, QFont

from core.autotest import AutoWindow
from core.config_manager import get_mode
from ui.gui_login import ModernWindow
import core.gestion_db as db



def center_window(window):
    """Centers a PyQt window on the screen (cross-platform and DPI-aware)."""
    window.show()  # <-- must show before computing geometry
    screen = QGuiApplication.primaryScreen()
    if not screen:
        return
    screen_geometry = screen.availableGeometry()
    window_geometry = window.frameGeometry()
    center_point = screen_geometry.center()
    window_geometry.moveCenter(center_point)
    window.move(window_geometry.topLeft())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        db.init_db()

        principal_window = ModernWindow()
        principal_window.show()
        if get_mode()== "none":
            ensure_admin()
            window = AutoWindow()
            window.show()
        center_window(principal_window)  # Then center
        sys.exit(app.exec())
    except Exception as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Erreur critique")
        msg.setText("Une erreur inattendue est survenue !")
        msg.setInformativeText(str(e))
        msg.exec()
        print("Erreur critique:", e)