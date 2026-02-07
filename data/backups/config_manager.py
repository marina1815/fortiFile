import json
import os

CONFIG_FILE = "config.json"


def config_exists():
    """Vérifie si le fichier config.json existe déjà."""
    return os.path.exists(CONFIG_FILE)


def init_config():
    """Crée un fichier config vide s'il n'existe pas encore."""
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"mode": None, "first_run_done": False}, f, indent=4)


def get_mode():
    """Lit le mode actuel ('auto' ou 'manuel') depuis config.json."""
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("mode")
    except Exception:
        return None


def set_mode_and_mark(mode):
    """
    Sauvegarde le mode choisi (auto/manuel)
    et marque que la configuration initiale est terminée.
    """
    data = {"mode": mode, "first_run_done": True}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def update_mode(mode):
    """Permet de modifier le mode plus tard (sans toucher à first_run_done)."""
    if not os.path.exists(CONFIG_FILE):
        init_config()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["mode"] = mode
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
