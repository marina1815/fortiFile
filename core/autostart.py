import os
import subprocess
import sys
import platform

TASK_NAME = "FortiFileApp"

def is_windows():
    return platform.system().lower() == "windows"

def get_integrity_path():
    """
    Retourne le chemin absolu du programme à lancer (hello.exe ou hello.py).
    Détecte automatiquement l'exécutable si empaqueté.
    """
    folder = os.path.dirname(os.path.abspath(sys.argv[0]))
    exe_path = os.path.join(folder, "Authentification.exe")
    py_path = os.path.join(folder, "Authentification.py")

    if os.path.exists(exe_path):
        return exe_path
    if os.path.exists(py_path):
        return py_path

    # fallback sur le script courant
    return os.path.abspath(sys.argv[0])


def enable_autostart():
    """
    Crée une tâche planifiée Windows pour lancer le programme au démarrage
    de la session utilisateur (ONLOGON) en mode INTERACTIF.
    Retourne True si succès, False sinon.
    """
    if not is_windows():
        print("autostart: non supporté (pas Windows).")
        return False
    folder = os.path.dirname(os.path.abspath(sys.argv[0]))
    target = os.path.join(folder, "Authentification.exe")
    if not os.path.exists(target):
        print(f"autostart: fichier introuvable: {target}")
        return False

    # Détermine la commande à exécuter
    if target.lower().endswith(".exe"):
        command = f'"{target}"'
    else:
        command = f'"{sys.executable}" "{target}"'

    # ✅ Version interactive : se lance seulement quand l’utilisateur est connecté
    cmd = [
        "schtasks", "/Create",
        "/SC", "ONLOGON",
        "/TN", TASK_NAME,
        "/TR", command,
        "/RL", "HIGHEST",   # droits admin
        "/IT",              # <--- permet d'afficher la fenêtre
        "/F"                # force la création
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ autostart: tâche planifiée créée avec succès (interactive).")
        if result.stdout:
            print(result.stdout)
        return True

    except subprocess.CalledProcessError as e:
        print("❌ autostart: erreur création tâche planifiée :")
        if e.stderr:
            print(e.stderr)
        else:
            print(e)
        return False


def disable_autostart():
    """Supprime la tâche planifiée si elle existe."""
    if not is_windows():
        return False

    try:
        subprocess.run(
            ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
            check=True, capture_output=True, text=True
        )
        print("🗑️ autostart: tâche supprimée.")
        return True

    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").lower()
        if "cannot find" in stderr or "l'ordinateur spécifié" in stderr:
            print("autostart: aucune tâche à supprimer.")
            return True
        print("autostart: erreur suppression tâche planifiée :")
        if e.stderr:
            print(e.stderr)
        else:
            print(e)
        return False