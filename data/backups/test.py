import tkinter as tk
from tkinter import messagebox
from core.integrity_monitoring import startMonitoring, stopMonitoring, get_files
import threading

# ------------------------------
# Variables globales
# ------------------------------
monitor_thread = None
file_list = get_files()  # récupère la liste des fichiers à surveiller
username = "admin"       # tu peux demander à l'utilisateur via input ou GUI

# ------------------------------
# Fonctions pour les boutons
# ------------------------------
def start_monitoring():
    global monitor_thread, file_list, username
    if monitor_thread and monitor_thread.is_alive():
        messagebox.showinfo("Info", "La surveillance est déjà en cours.")
        return

    # Lancer la surveillance dans un thread pour ne pas bloquer la GUI
    monitor_thread = threading.Thread(target=startMonitoring, args=(file_list, username), daemon=True)
    monitor_thread.start()
    messagebox.showinfo("Info", f"Surveillance démarrée pour {len(file_list)} fichiers.")

def stop_monitoring():
    stopMonitoring()
    messagebox.showinfo("Info", "Surveillance arrêtée.")

# ------------------------------
# Interface Tkinter
# ------------------------------
root = tk.Tk()
root.title("File Integrity Monitoring")

root.geometry("300x150")
root.resizable(False, False)

# Bouton démarrer
start_btn = tk.Button(root, text="Start Monitoring", width=25, command=start_monitoring)
start_btn.pack(pady=20)

# Bouton arrêter
stop_btn = tk.Button(root, text="Stop Monitoring", width=25, command=stop_monitoring)
stop_btn.pack(pady=10)

# Fermeture propre
def on_closing():

    root.destroy()

#root.protocol("WM_DELETE_WINDOW", on_closing)

# Lancement de la GUI
root.mainloop()
