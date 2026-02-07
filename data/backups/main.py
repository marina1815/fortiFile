import sys

from Demos.win32ts_logoff_disconnected import username
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QListWidget, QFileDialog, QPushButton, QMessageBox
)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QGuiApplication, QFont

from core.integrityCode import *
from ui.gui_login import ModernWindow
from ui.main_window import AppWindow

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



def main_window():
    """Main FIM window with folder monitoring."""
    init_db()
    window = QWidget()
    window.setWindowTitle("FIM - File Integrity Monitor")
    window.resize(900, 600)
    center_window(window)

    layout = QVBoxLayout(window)
    layout.setSpacing(15)
    layout.setContentsMargins(20, 20, 20, 20)

    info_label = QLabel("🧭 Surveillance des dossiers critiques")
    info_label.setFont(QFont("Poppins", 14, QFont.Weight.Bold))
    layout.addWidget(info_label)

    list_widget = QListWidget()
    layout.addWidget(list_widget)

    stats_label = QLabel("")
    stats_label.setFont(QFont("Poppins", 10))
    layout.addWidget(stats_label)

    # Add folder button
    def add_folder():
        folder = QFileDialog.getExistingDirectory(window, "Sélectionner un dossier à surveiller")
        if folder:
            try:
                build_baseline_for_folder(folder,username)
                QMessageBox.information(window, "Baseline créée", f"Le dossier '{folder}' est désormais surveillé.")
                refresh_list()
            except Exception as error:
                QMessageBox.critical(window, "Erreur", f"Impossible d'ajouter le dossier :\n{error}")

    add_btn = QPushButton("➕ Ajouter un dossier à surveiller")
    add_btn.clicked.connect(add_folder)
    layout.addWidget(add_btn)

    # Refresh function
    def refresh_list():
        try:
            list_widget.clear()
            ok, mod, sup, file_status, _ = check_integrity()
            stats_label.setText(f"✅ OK: {ok} | ⚠️ Modifié: {mod} | ❌ Supprimé: {sup}")
            for path, state in file_status:
                list_widget.addItem(f"{state}  →  {path}")
        except Exception as error:
            stats_label.setText(f"Erreur: {error}")

    # Auto-refresh every 5 seconds
    timer = QTimer()
    timer.timeout.connect(refresh_list)
    timer.start(5000)

    refresh_list()
    start_monitoring()

    # Ensure clean stop
    def on_close(event):
        stop_monitoring()
        event.accept()

    window.closeEvent = on_close
    return window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        principal_window =  ModernWindow()
        principal_window.show()        # Show first
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
