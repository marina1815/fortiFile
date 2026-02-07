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
BACKUP_DIR = "data/backups"



current_user = ""



import hashlib
import os
import time
from plyer import notification
from core.gestion_db import *
from datetime import datetime
import threading

CHECK_INTERVAL = 5  # secondes
running = False
_db_lock = threading.Lock()
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "log.txt")
BACKUP_DIR = "data/backups"

def ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_file(path):
    ensure_backup_dir()
    if os.path.exists(path):
        backup_path = os.path.join(BACKUP_DIR, os.path.basename(path))
        shutil.copy2(path, backup_path)
        db.log_event("info", f"Sauvegarde créée : {backup_path}",username=current_user)
        print(f"💾 Backup created: {backup_path}")

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

def restore_file(filename):
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(filename))
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, filename)
        db.log_event("alert", f"Fichier restauré : {filename}", username=current_user)
        notify("Fichier restauré", os.path.basename(filename))
    else:
        db.log_event("warning", f"Aucune sauvegarde trouvée pour {filename}", username=current_user)
# ==============================
def check_integrity():
    """
    Vérifie l'intégrité des fichiers :
      1. Vérifie d'abord les suspects existants
      2. Compare ensuite avec la baseline
      3. Si action autorisée → autorise mais notifie + ajoute suspect
      4. Si action non autorisée → restaure le fichier et bloque l'action
    """

    baseline_map = get_baseline()        # {path: hash_baseline}
    suspect_map = get_suspects_map()     # {path: last_hash}
    ok_count = mod_count = del_count = 0
    new_alerts = []
    file_status = []

    # ==============================
    # 1️⃣ Vérification des fichiers suspects
    # ==============================
    for path, last_hash in suspect_map.items():
        current_hash = get_file_hash(path)
        expected_hash = baseline_map.get(path)
        owner = db.get_baseline_owner(path)

        # Cas : suspect supprimé
        if current_hash is None:
            if not is_authorized(path):
                msg = f"[ACCES REFUSÉ] '{current_user}' ne peut pas supprimer {path}"
                log_to_file(msg)
                log_event("warning", msg, username=current_user)
                notify("Alerte FIM", msg)
                restore_file(path)
                file_status.append((path, "⛔ Suppression non autorisée"))
                continue

            # Suppression autorisée → on garde une trace

            del_count += 1
            new_alerts.append((path, "deleted"))
            msg = f"Le fichier {path} a été supprimé (autorisé)."
            log_to_file(msg)
            log_event("delete", msg, username=current_user)
            notify("Suppression autorisée  ", msg)
            file_status.append((path, "🗑️ Supprimé autorisé"))
            continue

        # Cas : suspect toujours présent → re-vérification
        current_hash = get_file_hash(path)
        if current_hash != last_hash:
            # Le fichier suspect a encore changé
            if not is_authorized(path):
                msg = f"[ACCES REFUSÉ] '{current_user}' ne peut pas modifier {path}"
                log_to_file(msg)
                log_event("warning", msg, username=current_user)
                notify("Alerte FIM", msg)
                restore_file(path)
                file_status.append((path, "⛔ Modification non autorisée"))
                continue

            # Modification autorisée → on met à jour suspect et on notifie
            upsert_suspect(path, expected_hash, current_hash, "modified")
            mod_count += 1
            msg = f"Le fichier {path} a été modifié (autorisé)."
            log_to_file(msg)
            log_event("modification", msg, username=current_user)
            notify("Modification autorisée", msg)
            file_status.append((path, "⚠️ Modifié autorisé"))
        else:
            # Fichier suspect inchangé
            file_status.append((path, "⚠️ Toujours suspect"))

    # ==============================
    # 2️⃣ Vérification des fichiers baseline
    # ==============================
    for path, expected_hash in baseline_map.items():
        if path in suspect_map:
            continue  # déjà traité plus haut

        current_hash = get_file_hash(path)
        owner = db.get_baseline_owner(path)

        # Cas : fichier supprimé
        if current_hash is None:
            if not is_authorized(path):
                msg = f"[ACCES REFUSÉ] '{current_user}' ne peut pas supprimer {path}"
                log_to_file(msg)
                log_event("warning", msg, username=current_user)
                notify("Alerte FIM", msg)
                restore_file(path)
                file_status.append((path, "⛔ Suppression non autorisée"))
                continue

            upsert_suspect(path, expected_hash, None, "deleted")
            del_count += 1
            msg = f"Le fichier {path} a été supprimé (autorisé)."
            log_to_file(msg)
            log_event("delete", msg, username=current_user)
            notify("Suppression autorisée", msg)
            file_status.append((path, "🗑️ Supprimé autorisé"))
            continue

        # Cas : fichier modifié
        current_hash = get_file_hash(path)
        if current_hash != expected_hash:
            if not is_authorized(path):
                msg = f"[ACCES REFUSÉ] '{current_user}' ne peut pas modifier {path}"
                log_to_file(msg)
                log_event("warning", msg, username=current_user)
                notify("Alerte FIM", msg)
                restore_file(path)
                file_status.append((path, "⛔ Modification non autorisée"))
                continue

            upsert_suspect(path, expected_hash, current_hash, "modified")
            mod_count += 1
            msg = f"Le fichier {path} a été modifié (autorisé)."
            log_to_file(msg)
            log_event("modification", msg, username=current_user)
            notify("Modification autorisée", msg)
            file_status.append((path, "⚠️ Modifié autorisé"))
        else:
            ok_count += 1
            file_status.append((path, "✅ Intact"))

    # ==============================
    # 3️⃣ Nettoyage : suspects sans baseline
    # ==============================
    for path in list(suspect_map.keys()):
        if path not in baseline_map:
            if not is_authorized(path):
                msg = f"[ACCES REFUSÉ] '{current_user}' ne peut pas supprimer {path} (hors baseline)"
                log_to_file(msg)
                log_event("warning", msg, username=current_user)
                notify("Alerte FIM", msg)
                restore_file(path)
                file_status.append((path, "⛔ Suppression non autorisée (hors baseline)"))
                continue

            upsert_suspect(path, None, suspect_map[path], "deleted")
            del_count += 1
            msg = f"Le fichier {path} a été supprimé (hors baseline, autorisé)."
            log_to_file(msg)
            log_event("delete", msg, username=current_user)
            notify("Suppression autorisée (hors baseline)", msg)
            file_status.append((path, "🗑️ Supprimé hors baseline autorisé"))

    # ==============================
    # 4️⃣ Résumé
    # ==============================
    log_event(
        "info",
        f"Vérification terminée → OK={ok_count}, Modifiés={mod_count}, Supprimés={del_count}",
        username=current_user
    )

    return ok_count, mod_count, del_count, file_status, new_alerts


def _monitor_loop():
    """Runs periodic integrity checks and sends alerts only for *new* suspects."""
    global running
    while running:
        try:
            ok, mod, sup, _, new_alerts = check_integrity()

            # 🔹 Send notification only if new suspects appeared
            if new_alerts:
                mod_new = sum(1 for _, s in new_alerts if s == "modified")
                del_new = sum(1 for _, s in new_alerts if s == "deleted")

                msg = f"Nouveaux fichiers suspects: {mod_new} modifiés, {del_new} supprimés."

                log_to_file(f"[ALERTE] {msg}")

        except Exception as e:
            print("Erreur dans monitor_loop: " , e)

        time.sleep(CHECK_INTERVAL)

def start_monitoring(username):
    global  current_user
    current_user = username
    global running, _monitor_thread
    if running:
        return None
    running = True
    _monitor_thread = threading.Thread(target=_monitor_loop, daemon=True )
    _monitor_thread.start()
    return _monitor_thread

def stop_monitoring():
    global running
    running = False



# ===============================
# 🔹 UTILITIES
# ===============================
def ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_file(path):
    ensure_backup_dir()
    if os.path.exists(path):
        backup_path = os.path.join(BACKUP_DIR, os.path.basename(path))
        shutil.copy2(path, backup_path)
        db.log_event("info", f"Sauvegarde créée : {backup_path}",username=current_user)
        print(f"💾 Backup created: {backup_path}")

def restore_file(filename):
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(filename))
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, filename)
        db.log_event("alert", f"Fichier restauré : {filename}", username=current_user)
        notify("Fichier restauré", os.path.basename(filename))
    else:
        db.log_event("warning", f"Aucune sauvegarde trouvée pour {filename}", username=current_user)

def delete_file(path):
    try:
        os.remove(path)
        db.log_event("alert", f"Fichier supprimé automatiquement : {path}", username=current_user)
        notify("Création non autorisée", os.path.basename(path))
    except Exception as e:
        db.log_event("error", f"Erreur suppression {path}: {e}", username=current_user)

def notify(title, message):
    try:
        notification.notify(title=title, message=message, timeout=4)
        db.add_notification(title, message, username=current_user)
    except Exception:
        pass



def is_authorized(filepath=None):
    """
    Returns True if current_user is allowed to perform `action` on filepath.
    Rules:
    - Admin bypasses everything.
    - If user's role (ACL) grants the action, allow.
    - If file has an owner:
        - allow if owner == current_user OR current_user == 'admin'
        - otherwise deny (unless role permits global modify)
    - If file owner is None: allow based on role (ACL).
    """
    if filepath:
        print(current_user)
        owner = db.get_baseline_owner(filepath)
        print(owner)
        # owner not set => decide by role (already checked above)
        if owner is None:
            return  False
        # owner set: allow only owner or admin (admin handled above)
        if owner == current_user:
            return True
        # otherwise deny
        db.log_event("warning", f"Accès refusé pour {current_user} sur {filepath}",username=current_user)
        return False

    # fallback deny
    return False

# ===============================
# 📁 BASELINE CREATION
# ===============================
def build_baseline_for_folder(folder, username):
    """
    Build a new baseline for the specified folder.
    Stores each file's hash, size, and modification time in the database.
    Also logs the operation and sends a notification.
    """

    try:
        # Add folder to database (or ignore if it already exists)
        db.insert_folder(folder, username)
        folder_id = db.get_folder_id(folder)
        if not folder_id:
            print(f"[WARN] Could not get folder ID for {folder}")
            return

        count = 0
        for root, _, files in os.walk(folder):
            for f in files:
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, "rb") as file:
                        file_hash = hashlib.sha256(file.read()).hexdigest()

                    st = os.stat(full_path)

                    # Store file info in baseline table
                    db.insert_baseline_entry(
                        folder_id,
                        full_path,
                        file_hash,
                        st.st_size,
                        datetime.fromtimestamp(st.st_mtime).isoformat(),
                        username=username
                    )
                    backup_file(full_path)
                    count += 1

                except Exception as e:
                    print(f"[ERROR] Failed to process {full_path}: {e}")
                    continue

        # Log to database and to local log file
        db.log_event("info", f"{count} files registered for folder {folder}", username=current_user)
        log_to_file(f"[SUCCESS] Folder '{folder}' added by user '{username}' with {count} files")

        # Send desktop notification
        notify("Baseline Updated", f"{count} files added for {folder}")

        print(f"[SUCCESS] Baseline built successfully for {folder} ({count} files)")
        return count

    except Exception as e:
        print(f"[ERROR] build_baseline_for_folder failed: {e}")
        db.log_event("error", f"Failed to build baseline for {folder}: {e}", username=current_user)
        log_to_file(f"[ERROR] Baseline creation failed for {folder}: {e}")
        return 0
# ===============================
# 🚀 MONITOR START
# ===============================


def select_folder():
    """Ask user to enter folder path (or use default)"""
    folder = input("\n📂 Enter folder path to monitor (or press Enter for default): ").strip()
    if not folder:
        folder = r"C:\Users\DELL\Desktop\test-scan"
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"✅ Folder created: {folder}")
    return folder


def start_fim(folder, username):
    """Start monitoring thread"""

    globals()['current_user'] = username
    print(f"\n🔒 Monitoring started by '{username}' on: {folder}")
    build_baseline_for_folder(folder,username)

    # Run in separate thread so you can stop it
    thread = threading.Thread(target=start_monitoring, daemon=True)
    thread.start()

    print("🕵️ Press Ctrl+C to stop monitoring.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped.")


def main():
    print("=== File Integrity Monitoring ===")
    db.init_db()

    username = input("👤 Enter username (admin/user/guest): ").strip().lower()
    if username not in ["admin", "user", "guest"]:
        print("❌ Invalid username.")
        return

    folder = select_folder()

    print(f"\n👋 Welcome, {username}!")
    print(f"Folder to monitor: {folder}")
    print("\nStarting baseline and file watcher...")

    start_fim(folder, username)


if __name__ == "__main__":
    main()

