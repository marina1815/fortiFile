import sys
import os
import traceback
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QStackedLayout, QHBoxLayout, QMessageBox
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt

from core.control_autostart import ensure_admin, mode_auto
from core.config_manager import config_exists, init_config, update_mode
from core.autostart import enable_autostart, disable_autostart, get_integrity_path, TASK_NAME


base_dir = os.path.dirname(os.path.abspath(__file__))
auto = os.path.join(base_dir, "../img/auto.png")
manuel = os.path.join(base_dir, "../img/manuel.png")

# ---------------- Page 2 ----------------
class Page2(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):

        # ---------- TITRE ----------
        title = QLabel("Choose Startup Mode")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #151B54;font-size: 22px; font-weight: bold;")

        # ---------- DESCRIPTION ----------
        desc = QLabel("Select how FortiFile will run when the system starts. ")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: black; margin-bottom: 20px;")

        # ---------- BOUTONS -----------
        self.btn_auto = QPushButton(" Démarrage Automatique")
        self.btn_auto.setIcon(QIcon(auto))
        self.btn_auto.clicked.connect(self.on_auto)

        self.btn_manuel = QPushButton(" Mode Manuel")
        self.btn_manuel.setIcon(QIcon(manuel))
        self.btn_manuel.clicked.connect(self.on_manuel)

        # ---------- STYLE DES BOUTONS ----------
        button_style = """
            QPushButton {
                background-color: #151B54;
                color: white;
                border-radius: 8px;
                padding: 12px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #120A37;
            }
        """
        self.btn_auto.setStyleSheet(button_style)
        self.btn_manuel.setStyleSheet(button_style)

        # ---------- LAYOUT HORIZONTAL POUR LES BOUTONS ----------
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_auto)
        btn_layout.addWidget(self.btn_manuel)
        btn_layout.setSpacing(20)

        # ---------- LAYOUT GLOBAL ----------
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(20)
        layout.addStretch()
        layout.addLayout(btn_layout)


        self.setLayout(layout)

    # ---------- ACTIONS ----------
    def on_auto(self):
        ok = enable_autostart()
        update_mode("auto")
        if ok:
            QMessageBox.information(self, "Modifié", "✅ Démarrage automatique activé.")
            mode_auto(self)
            self.window().close()
        else:
            QMessageBox.warning(self, "Erreur", "❌ Impossible d’activer le démarrage automatique.")

    def on_manuel(self):
        update_mode("manuel")
        disable_autostart()
        self.kill()
        self.window().close()
        QMessageBox.information(self, "Modifié", "🟡 Démarrage automatique désactivé.")

    def kill(self):
        try:
            subprocess.run(["taskkill", "/IM", "hello.exe", "/F"], check=False)
            print("hello.exe killed")
        except Exception as e:
            print("Error:", e)



# ---------------- Fenêtre principale ----------------
class AutoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FortiFile — Startup Mode Configuration")
        self.setFixedSize(500, 200)
        self.setWindowIcon(QIcon("../img/iconFortiFile.PNG"))
        self._build_ui()

    def _build_ui(self):
        self.page2 = Page2()

        self.stack = QStackedLayout()
        self.stack.addWidget(self.page2)

        layout = QVBoxLayout()
        layout.addLayout(self.stack)

        self.setLayout(layout)

    def close_window(self):
        self.close()



# ---------------- Entrée principale ----------------
if __name__ == "__main__":
    print("Démarrage de main_gui.py — PID:", os.getpid())
    try:
        init_config()
    except Exception:
        traceback.print_exc()

    app = QApplication(sys.argv)
    win = AutoWindow()
    win.show()
    sys.exit(app.exec())