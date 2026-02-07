import os
import threading
import hashlib
import time
import shutil
from datetime import datetime
from plyer import notification
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import core.gestion_db as db
from core.gestion_db import *
from core.gestion_db import update_baseline_path, get_files

# ===============================
# 🔹 VARIABLES GLOBALES
# ===============================
OBSERVERS = {}
BACKUP_DIR = "data/backups"
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "log.txt")
current_user = ""
_db_lock = threading.Lock()

# ===============================
# 🔹 UTILITAIRES
# ===============================
def normalize_path(path):
    """Normalise le chemin pour Windows/Unix (slash et casse)."""
    return os.path.normcase(os.path.abspath(path))

def get_file_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None

def log_to_file(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{ts} {msg}\n")

def notify(title, message):
    try:
        notification.notify(title=title, message=message, timeout=4)
        db.add_notification(title, message, username=current_user)
    except Exception:
        pass

def ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_file(path):
    ensure_backup_dir()
    if os.path.exists(path):
        backup_path = os.path.join(BACKUP_DIR, os.path.basename(path))
        shutil.copy2(path, backup_path)
        db.log_event("info", f"Sauvegarde créée : {backup_path}", username=current_user)
        print(f"💾 Backup created: {backup_path}")

def delete_backup_file(path):
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(path))
    if os.path.exists(backup_path):
        try:
            os.remove(backup_path)
            db.log_event("info", f"Backup supprimé : {backup_path}", username=current_user)
        except Exception as e:
            db.log_event("error", f"Erreur suppression backup {backup_path}: {e}", username=current_user)

def restore_file(filename):
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(filename))
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, filename)
        db.log_event("alert", f"Fichier restauré : {filename}", username=current_user)
    else:
        db.log_event("warning", f"Aucune sauvegarde trouvée pour {filename}", username=current_user)

def delete_file(path):
    try:
        os.remove(path)
        db.log_event("alert", f"Fichier supprimé automatiquement : {path}", username=current_user)
        notify("Création non autorisée", os.path.basename(path))
    except Exception as e:
        db.log_event("error", f"Erreur suppression {path}: {e}", username=current_user)

# ===============================
# 🔹 AUTORISATION
# ===============================
def is_authorized(filepath=None):
    global current_user
    if current_user == "admin":
        return True
    elif current_user in ["user", "guest"]:
        return False

    if filepath:
        filepath = normalize_path(filepath)
        print(filepath)
        owner = db.get_baseline_owner(filepath)
        print(owner)

        if owner and owner == current_user:
            return True
        db.log_event("warning", f"Accès refusé : {current_user} sur {filepath}", username=current_user)
    return False

def normalize_path(path):
    """Normalise le chemin pour Windows/Unix (slash et casse)."""
    return os.path.normcase(os.path.abspath(path))

def get_baseline_hash(path):
    """
    Retourne le hash de baseline pour un fichier donné.
    - path : chemin du fichier
    - renvoie le hash SHA-256 enregistré ou None si non trouvé
    """
    # Récupère la baseline depuis la DB
    baseline_map = db.get_baseline_dict()

    if not baseline_map:
        return None

    # Normalise tous les chemins pour correspondre au format de event.src_path
    baseline_map = {normalize_path(p): h for p, h in baseline_map.items()}

    # Normalise le chemin demandé
    path = normalize_path(path)

    # Renvoie le hash si présent
    return baseline_map.get(path)


# ===============================
# 🔹 INTEGRITY HANDLER (Watchdog)
# ===============================
class IntegrityHandler(FileSystemEventHandler):
    def __init__(self, monitored_files):
        self.monitored_files = [normalize_path(f) for f in monitored_files]
        self.baseline = db.get_baseline_dict()
        print("init handler")

    def on_any_event(self, event):
        """Ignore les dossiers, ne traite que les fichiers surveillés."""
        if event.is_directory:
            return
        path = normalize_path(event.src_path)
        if path not in self.monitored_files:
            return  # on ignore les fichiers non surveillés

    def on_created(self, event):
        if event.is_directory:
            return
        path = normalize_path(event.src_path)
        if path not in self.monitored_files:
            return
        print(f"[CREATE] {path}")

        if not is_authorized(path):
            db.log_event("alert", f"Création non autorisée : {path}", username=current_user)
            delete_file(path)
        else:
            h = get_file_hash(path)
            st = os.stat(path)
            db.insert_baseline_entry(None, path, h, st.st_size, datetime.fromtimestamp(st.st_mtime).isoformat(), username=current_user)
            backup_file(path)
            notify("Fichier ajouté", os.path.basename(path))

    def on_modified(self, event):
        if event.is_directory:
            return
        path = normalize_path(event.src_path)
        if path not in self.monitored_files:
            return
        print(f"[MODIFY] {path}")

        h = get_file_hash(path)
        old_hash =  get_baseline_hash(path)
        print(old_hash)

        if old_hash and h != old_hash:
            print(is_authorized(path))
            if not is_authorized(path):

                db.log_event("alert", f"Modification non autorisée : {path}", username=current_user)
                notify("Modification bloquée", os.path.basename(path))
                restore_file(path)
            else:
                backup_file(path)
                db.upsert_suspect(path, old_hash, h, "modified")
                db.log_event("info", f"Fichier modifié : {path}", username=current_user)
                notify("Fichier modifié", os.path.basename(path))

    def on_deleted(self, event):
        if event.is_directory:
            return
        path = normalize_path(event.src_path)
        if path not in self.monitored_files:
            return
        print(f"[DELETE] {path}")

        if not is_authorized(path):
            db.log_event("alert", f"Suppression non autorisée : restauration {path}", username=current_user)
            notify("Suppression bloquée", os.path.basename(path))
            restore_file(path)
        else:
            db.log_event("info", f"Suppression autorisée : {path}", username=current_user)
            notify("Suppression autorisée", os.path.basename(path))

    def on_moved(self, event):
        if event.is_directory:
            return
        src = normalize_path(event.src_path)
        dest = normalize_path(event.dest_path)
        if src not in self.monitored_files:
            return
        db.log_event("info", f"Renommage : {src} -> {dest}", username=current_user)
        notify("Renommage de fichier", os.path.basename(dest))
        update_baseline_path(src, dest)
        log_to_file(f"Renamed: {src} -> {dest}")

# ===============================
# 🔹 BASELINE POUR LES FICHIERS UNIQUES
# ===============================
def build_baseline_for_files(file_list, username):
    """Construit une baseline pour une liste de fichiers."""
    count = 0
    for path in file_list:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            st = os.stat(path)
            db.insert_baseline_entry(None, path, file_hash, st.st_size, datetime.fromtimestamp(st.st_mtime).isoformat(), username=username)
            count += 1
        except Exception as e:
            print(f"[ERROR] {path}: {e}")
    notify("Baseline construite", f"{count} fichiers ajoutés")
    print(f"[SUCCESS] Baseline pour {count} fichiers.")
    return count

# ===============================
# 🔹 DEMARRER / ARRETER LA SURVEILLANCE
# ===============================
def _start_watcher_thread(file_list, username):
    global OBSERVERS
    handler = IntegrityHandler(file_list)
    observer = Observer()
    # On observe le dossier parent commun à tous les fichiers
    common_root = os.path.commonpath(file_list)
    observer.schedule(handler, common_root, recursive=True)
    observer.daemon = True
    observer.start()
    OBSERVERS[normalize_path(common_root)] = observer
    log_to_file(f"Observer started for files in {common_root}")

def startMonitoring(file_list, username):
    global current_user
    current_user = username



    th = threading.Thread(target=_start_watcher_thread, args=(file_list, username), daemon=True)
    th.start()
    print(f"🔒 Surveillance démarrée pour {len(file_list)} fichiers par '{username}'.")

    try:
        while True:  # boucle pour garder le programme actif
            time.sleep(1)
    except KeyboardInterrupt:
        stopMonitoring()

def stopMonitoring():
    global OBSERVERS
    for k, obs in list(OBSERVERS.items()):
        try:
            obs.stop()
            obs.join()
            log_to_file(f"Observer stopped for {k}")
        except Exception:
            pass
    OBSERVERS.clear()
    print("🛑 Surveillance arrêtée.")




# Exemple :
#paths = get_files()

#startMonitoring(paths, "marina")   # Démarrer

