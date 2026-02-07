
import sys
import os
import ctypes
import subprocess
import traceback
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtCore import Qt



def ensure_admin():
    """Relance le script en mode administrateur si nécessaire (Windows)."""
    if sys.platform != "win32":
        return
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        is_admin = False

    if is_admin:
        return

    script = os.path.abspath(sys.argv[0])
    other_args = " ".join(f'"{arg}"' for arg in sys.argv[1:])
    params = f'"{script}" {other_args}'.strip()
    python_exe = sys.executable

    try:
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", python_exe, params, None, 1)
        if int(ret) > 32:
            print("Relancement en mode administrateur demandé (UAC).")
            sys.exit(0)
        else:
            print(f"Échec élévation (ret={ret}), continuer sans.")
    except Exception:
        traceback.print_exc()
        print("Continuer sans élévation.")


# ---------------- Fenêtre d’aide Planificateur ----------------
class SchedulerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guide — Task Scheduler")
        self.setFixedSize(450, 220)  # légèrement plus grand pour plus de confort
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 🔹 Label avec style
        label = QLabel(
            "The Windows Task Scheduler has just opened.\n\n"
            "In the left column, click on 'Task Scheduler Library'.\n"
            "Then, find the task named **FortiFileApp**.\n"
            "Finally, click on **Run** ."
        )
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 13pt;
                color: #1a1a1a;
                background-color: #f9f9f9;
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 12px;
            }
        """)

        # 🔹 Bouton Ok avec style
        btn_ok = QPushButton(" OK ")
        btn_ok.clicked.connect(self.accept)
        btn_ok.setStyleSheet("""
            QPushButton {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 11pt;
                color: white;
                background-color: #0078d7;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #00457c;
            }
        """)

        layout.addWidget(label)
        layout.addWidget(btn_ok, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

# ---------------- Fonction utilitaire pour mode auto ----------------
def mode_auto(parent=None):
    """Ouvre le planificateur de tâches et affiche un guide à l’utilisateur."""
    try:
        subprocess.Popen(["mmc.exe", "C:\\Windows\\System32\\taskschd.msc"], shell=False)
    except Exception as e:
        traceback.print_exc()
        QMessageBox.warning(parent, "Erreur", f"Impossible d’ouvrir taskschd.msc :\n{e}")
        return

    dlg = SchedulerDialog(parent)
    dlg.exec()
