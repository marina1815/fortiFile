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
from core.integrity_monitoring import backup_file, current_user
from core.user_manager import load_current_user

BACKUP_DIR = "data/backups"
import hashlib
import os
import time
from plyer import notification
from core.gestion_db import *
from datetime import datetime
import threading
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "log.txt")

current_user = load_current_user()
def build_baseline_for_folder(folder, username):
    """
    Build a new baseline for the specified folder.
    Stores each file's hash, size, and modification time in the database.
    Prevents overwriting file ownership by another user.
    """

    try:
        # Add folder to database (or ignore if it already exists)
        db.insert_folder(folder, username)
        folder_id = db.get_folder_id(folder)
        if not folder_id:
            print(f"[WARN] Could not get folder ID for {folder}")
            return

        count = 0
        skipped = 0

        for root, _, files in os.walk(folder):
            for f in files:
                full_path = os.path.normpath(os.path.join(root, f))
                print(f"[INFO] Processing {full_path}")

                try:
                    # Vérifier si le fichier existe déjà dans la baseline
                    existing_owner = db.get_baseline_owner(full_path)

                    # Si le fichier appartient déjà à un autre utilisateur → refuser
                    if existing_owner and existing_owner != username:
                        print(f"❌ File {full_path} already belongs to {existing_owner}. Skipping.")
                        db.log_event(
                            "warning",
                            f"User '{username}' attempted to register file owned by '{existing_owner}'",
                            username=username
                        )
                        skipped += 1
                        continue

                    # Calcul du hash du fichier
                    with open(full_path, "rb") as file:
                        file_hash = hashlib.sha256(file.read()).hexdigest()

                    st = os.stat(full_path)

                    # Enregistrer dans la baseline
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

        # Logging
        db.log_event(
            "info",
            f"{count} files registered, {skipped} skipped for folder {folder}",
            username=username
        )
        log_to_file(f"[SUCCESS] Folder '{folder}' added by user '{username}' with {count} files ({skipped} skipped)")

        # Notification
        notify(
            "Baseline Update",
            f"{count} files added, {skipped} skipped (owned by others)"
        )

        print(f"[SUCCESS] Baseline built for {folder}: {count} added, {skipped} skipped.")
        return count

    except Exception as e:
        print(f"[ERROR] build_baseline_for_folder failed: {e}")
        db.log_event("error", f"Failed to build baseline for {folder}: {e}", username=username)
        log_to_file(f"[ERROR] Baseline creation failed for {folder}: {e}")
        return 0




def notify(title, message):
    try:
        notification.notify(title=title, message=message, timeout=4)
        db.add_notification(title, message, username=current_user)
    except Exception:
        pass


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

def check_integrity(current_user):
    """
    Vérifie l'intégrité des fichiers :
    - Détecte fichiers modifiés, supprimés ou hors baseline.
    - Notifie pour toutes les actions.
    - Met à jour les suspects dans la DB.
    """
    baseline_map = get_baseline()      # {path: hash}
    suspect_map = get_suspects_map()   # {path: last_hash}

    ok_count = mod_count = del_count = 0
    file_status = []
    new_alerts = []

    # 1️⃣ Vérification des fichiers suspects
    for path, last_hash in suspect_map.items():
        current_hash = get_file_hash(path)
        expected_hash = baseline_map.get(path)

        # Fichier supprimé
        if current_hash is None:

            notify("FIM", f"Fichier restauré : {path} (supprimé)")
            upsert_suspect(path, expected_hash, None, "deleted")
            del_count += 1
            file_status.append((path, "🗑️ Supprimé restauré"))
            continue

        # Fichier modifié
        if current_hash != last_hash:
            upsert_suspect(path, expected_hash, current_hash, "modified")
            mod_count += 1
            notify("FIM", f"Fichier modifié : {path}")
            file_status.append((path, "⚠️ Modifié détecté"))
            continue
        else:
            file_status.append((path, "⚠️ Toujours suspect"))
            continue

    # 2️⃣ Vérification des fichiers de la baseline non suspects
    for path, expected_hash in baseline_map.items():
        if path in suspect_map:
            continue
        current_hash = get_file_hash(path)

        if current_hash is None:

            upsert_suspect(path, expected_hash, None, "deleted")
            del_count += 1
            notify("FIM", f"Fichier supprimé  : {path}")
            file_status.append((path, "🗑️ Supprimé "))
            continue
        elif current_hash != expected_hash:
            upsert_suspect(path, expected_hash, current_hash, "modified")
            mod_count += 1
            notify("FIM", f"Fichier modifié : {path}")
            file_status.append((path, "⚠️ Modifié détecté"))
            continue
        else:
            ok_count += 1
            file_status.append((path, "✅ Intact"))
            continue



    # 4️⃣ Résumé
    log_event(
        "info",
        f"Vérification terminée → OK={ok_count}, Modifiés={mod_count}, Supprimés={del_count}",
        username=current_user
    )

    return ok_count, mod_count, del_count, file_status, new_alerts

def check_integrity_file(file_path):
    """
    Vérifie l'intégrité d'un seul fichier.
    - Detecte modification, suppression ou hors baseline.
    - Met à jour la table des suspects et envoie notifications.
    """
    # normaliser le chemin
    baseline_map = get_baseline()          # {path: hash}
    suspect_map = get_suspects_map()       # {path: last_hash}

    ok_count = mod_count = del_count = 0
    file_status = []
    new_alerts = []

    current_hash = get_file_hash(file_path)
    expected_hash = baseline_map.get(file_path)
    last_hash = suspect_map.get(file_path)

    # Fichier hors baseline
    if file_path not in baseline_map:
        if last_hash is not None:
            # Déjà suspect
            upsert_suspect(file_path, None, last_hash, "deleted")
        del_count += 1
        file_status.append((file_path, "🗑️ Hors baseline"))
        notify("FIM", f"Fichier hors baseline : {file_path}")
        return ok_count, mod_count, del_count, file_status, new_alerts

    # Fichier supprimé
    if current_hash is None:
        #restore_file(file_path)
        upsert_suspect(file_path, expected_hash, None, "deleted")
        del_count += 1
        file_status.append((file_path, "🗑️ Supprimé restauré"))
        notify("FIM", f"Fichier supprimé restauré : {file_path}")
        return ok_count, mod_count, del_count, file_status, new_alerts

    # Fichier modifié
    if current_hash != expected_hash:
        upsert_suspect(file_path, expected_hash, current_hash, "modified")
        mod_count += 1
        file_status.append((file_path, "⚠️ Modifié détecté"))
        notify("FIM", f"Fichier modifié : {file_path}")
        return ok_count, mod_count, del_count, file_status, new_alerts

    # Fichier intact
    ok_count += 1
    file_status.append((file_path, "✅ Intact"))
    return ok_count, mod_count, del_count, file_status, new_alerts


#print(check_integrity("hanaa"))
#build_baseline_for_folder(r"C:/Users/DELL/Desktop/test", "marina")