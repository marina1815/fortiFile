
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



def mode_auto(parent=None):
    """Ouvre le planificateur de tâches et affiche un guide à l’utilisateur."""
    try:
        subprocess.Popen(["mmc.exe", "C:\\Windows\\System32\\taskschd.msc"], shell=False)
    except Exception as e:
        traceback.print_exc()
        QMessageBox.warning(parent, "Erreur", f"Impossible d’ouvrir taskschd.msc :\n{e}")
        return