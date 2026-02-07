import sqlite3
from datetime import datetime
import threading
import os
import hashlib

from PyQt6.sip import delete

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "identifier.sqlite")

_db_lock = threading.Lock()


# ==============================
# CONNEXION & UTILITAIRES
# ==============================
def get_connection():
    """Crée une connexion indépendante (thread-safe)"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def execute_write(query, params=()):
    with _db_lock:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        conn.close()


def execute_fetchall(query, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


# ==============================
# INITIALISATION DE LA BASE
# ==============================
def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
    -- ===============================
    -- 📁 FOLDERS
    -- ===============================
    CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE NOT NULL,
        added_by TEXT,  -- username of the person who added it
        added_at TEXT DEFAULT (datetime('now')),
        status TEXT DEFAULT 'active'
    );

    -- ===============================
    --  BASELINE
    -- ===============================
    CREATE TABLE IF NOT EXISTS baseline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folder_id INTEGER ,
        path TEXT UNIQUE NOT NULL,
        hash TEXT,
        size INTEGER,
        modified_time TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        username TEXT,  -- who last updated this file
        FOREIGN KEY(folder_id) REFERENCES folders(id)
    );

    -- ===============================
    --  SUSPECTS
    -- ===============================
    CREATE TABLE IF NOT EXISTS suspects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        baseline_id INTEGER,
        path TEXT UNIQUE NOT NULL,
        old_hash TEXT,
        last_hash TEXT,
        state TEXT CHECK(state IN ('modified','deleted','new')),
        first_detected TEXT DEFAULT (datetime('now')),
        last_seen TEXT,
        resolved INTEGER DEFAULT 0,
        FOREIGN KEY (baseline_id) REFERENCES baseline(id)
    );

    -- ===============================
    --  EVENTS / LOGS
    -- ===============================
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT (datetime('now')),
        event_type TEXT CHECK(event_type IN ('info','warning','error','alert','baseline')),
        file_path TEXT,
        description TEXT,
        level TEXT,
        username TEXT  
    );

    -- ===============================
    -- 🔔 NOTIFICATIONS
    -- ===============================
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        message TEXT,
        sent_at TEXT DEFAULT (datetime('now')),
        status TEXT CHECK(status IN ('sent','pending','failed')) DEFAULT 'sent',
        username TEXT  -- user who received the notification
    );
      CREATE TABLE IF NOT EXISTS scan_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        time TEXT DEFAULT (datetime('now')),
        status TEXT CHECK(status IN ('completed', 'in_progress')) NOT NULL
    );


    -- ===============================
    -- ⚡ INDEXES
    -- ===============================
    CREATE INDEX IF NOT EXISTS idx_files_path ON baseline(path);
    CREATE INDEX IF NOT EXISTS idx_suspects_state ON suspects(state);
    CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
    CREATE INDEX IF NOT EXISTS idx_baseline_folder ON baseline(folder_id);
    CREATE INDEX IF NOT EXISTS idx_scan_history ON scan_history(id);
    """)
    conn.commit()
    conn.close()


# ==============================
# INSERTS DE BASELINE ET FOLDERS
# ==============================
def insert_folder(path, added_by):
    execute_write(
        """
        INSERT INTO folders (path, added_by)
        VALUES (?, ?)
        ON CONFLICT(path) DO UPDATE SET added_by=excluded.added_by
        """,
        (path, added_by)
    )


def insert_baseline_entry(folder_id, path, hash_val, size, modified_time, username=None):
    """Insert or replace baseline; store optional username (owner)."""
    execute_write("""
        INSERT OR REPLACE INTO baseline (folder_id, path, hash, size, modified_time, username)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (folder_id, path, hash_val, size, modified_time, username))


def update_baseline(path, new_hash):
    """
    Met à jour le hash, la taille et la date de modification d'un fichier dans la baseline.

    :param path: chemin complet du fichier à mettre à jour
    :param new_hash: nouveau hash SHA256 calculé
    :return: True si la mise à jour a réussi, False sinon
    """
    try:
        path = os.path.normpath(path)
        st = os.stat(path)
        modified_time = datetime.fromtimestamp(st.st_mtime).isoformat()
        size = st.st_size

        query = """
            UPDATE baseline
            SET hash = ?, size = ?, modified_time = ?
            WHERE path = ?
        """
        execute_write(query, (new_hash, size, modified_time, path))
        print(f"[INFO] Baseline updated for {path}")
        return True

    except Exception as e:
        print(f"[ERROR] update_baseline failed for {path}: {e}")
        return False


def delete_baseline_file(path):
    """
    Supprime un fichier de la baseline.

    :param path: chemin complet du fichier à supprimer
    :return: True si la suppression a réussi, False sinon
    """
    try:
        path = os.path.normpath(path)
        query = "DELETE FROM baseline WHERE path = ?"
        execute_write(query, (path,))
        print(f"[INFO] Baseline entry deleted for {path}")
        return True

    except Exception as e:
        print(f"[ERROR] delete_baseline_file failed for {path}: {e}")
        return False


# delete_baseline_file(r"C:\Users\DELL\Desktop\test-scan\manel.txt")
# ==============================
# BASELINE INFO
# ==============================

def get_baseline_by_user(username, folder_path=None, limit=None):
    """
    Retourne les fichiers de la baseline appartenant à un utilisateur donné.
    Même si plusieurs utilisateurs sont listés dans la colonne username (séparés par des virgules).
    Optionnellement, on peut filtrer par dossier ou limiter le nombre de résultats.

    :param username: nom de l'utilisateur
    :param folder_path: (optionnel) dossier surveillé spécifique
    :param limit: (optionnel) nombre maximum de résultats
    :return: liste de dictionnaires [{path, hash, size, modified_time, username, folder_path}, ...]
    """
    query = """
        SELECT b.path, b.hash, b.size, b.modified_time, b.username, f.path AS folder_path
        FROM baseline b
        JOIN folders f ON b.folder_id = f.id
        WHERE ',' || b.username || ',' LIKE ?
    """
    params = [f'%,{username},%']

    if folder_path:
        query += " AND f.path = ?"
        params.append(folder_path)

    query += " ORDER BY b.modified_time DESC"

    if limit:
        query += " LIMIT ?"
        params.append(int(limit))

    rows = execute_fetchall(query, tuple(params))

    result = []
    for row in rows:
        result.append({
            "path": row[0],
            "hash": row[1],
            "size": row[2],
            "modified_time": row[3],
            "username": row[4],
            "folder_path": row[5]
        })
    return result


def get_files_by_user(username, limit=None):
    """
    Récupère les chemins des fichiers dans la table baseline pour un utilisateur donné,
    même si plusieurs utilisateurs sont listés dans la colonne username (séparés par des virgules).

    :param username: nom d'utilisateur à rechercher
    :param limit: nombre maximum de fichiers à récupérer (optionnel)
    :return: liste de dictionnaires avec le chemin des fichiers
    """
    query = """
        SELECT path
        FROM baseline
        WHERE ',' || username || ',' LIKE ?
        ORDER BY modified_time DESC
    """
    params = [f'%,{username},%']

    if limit:
        query += " LIMIT ?"
        params.append(int(limit))

    rows = execute_fetchall(query, tuple(params))
    return [{"path": row[0]} for row in rows]


def get_baseline_owner(path):
    """Return the username (owner) for a given baseline path, or None if not set."""

    print(path)
    rows = execute_fetchall("SELECT username FROM baseline WHERE path = ?", (path,))

    return rows[0][0] if rows and rows[0][0] is not None else None


def set_baseline_owner(path, username):
    """Set/transfer owner for a given baseline file (admin-only operation intended)."""
    execute_write("UPDATE baseline SET username=? WHERE path=?", (username, path))


def get_folder_id(path):
    """Retourne l’ID du dossier surveillé"""
    rows = execute_fetchall("SELECT id FROM folders WHERE path=?", (path,))
    return rows[0][0] if rows else None


def get_baseline():
    """Retourne {path: hash} de tous les fichiers surveillés"""
    rows = execute_fetchall("SELECT path, hash FROM baseline")
    return {path: hash_val for path, hash_val in rows}


def get_folder():
    rows = execute_fetchall("SELECT path  FROM folders")
    return [row[0] for row in rows if isinstance(row[0], str)]


def get_files():
    rows = execute_fetchall("SELECT path  FROM baseline")
    return [row[0] for row in rows if isinstance(row[0], str)]


# ==============================
# OPS SUR BASELINE ET FOLDERS
# ==============================
def insert_folder_and_baseline_for_path(folder):
    """Crée la baseline complète pour un dossier (appelée depuis build_baseline_for_folder)"""
    insert_folder(folder)
    folder_id = get_folder_id(folder)
    if not folder_id:
        return

    count = 0
    for root, _, files in os.walk(folder):
        for f in files:
            full_path = os.path.join(root, f)
            try:
                with open(full_path, "rb") as file:
                    h = hashlib.sha256(file.read()).hexdigest()
                st = os.stat(full_path)
                insert_baseline_entry(folder_id, full_path, h, st.st_size,
                                      datetime.fromtimestamp(st.st_mtime).isoformat())
                count += 1
            except Exception:
                continue

    return count


def update_baseline_path(old_path, new_path):
    execute_write("UPDATE baseline SET path = ? WHERE path = ?", (new_path, old_path))


# ==============================
# SUSPECTS HANDLING
# ==============================
def upsert_suspect(path, old_hash, last_hash, state, username):
    """Ajoute ou met à jour un fichier suspect (lié à un utilisateur)"""
    execute_write("""
        INSERT INTO suspects (path, old_hash, last_hash, state, first_detected, last_seen, username)
        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'), ?)
        ON CONFLICT(path) DO UPDATE SET
            last_hash = excluded.last_hash,
            last_seen = datetime('now'),
            state = excluded.state,
            username = excluded.username
    """, (path, old_hash, last_hash, state, username))


def remove_suspect(path):
    """Supprime un suspect résolu"""
    execute_write("DELETE FROM suspects WHERE path=?", (path,))


def get_suspects_map():
    """Retourne {path: last_hash} depuis la table suspects."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT path, last_hash FROM suspects")
    data = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()
    return data


def is_suspect(path):
    """Return True if a file is already flagged as suspect."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM suspects WHERE path=? AND resolved=0", (path,))
        return cur.fetchone() is not None


def get_all_suspects():
    """Retourne tous les fichiers suspects"""
    return execute_fetchall("SELECT path, state, last_seen FROM suspects WHERE resolved=0")


# ==============================
# EVENTS & NOTIFICATIONS
# ==============================
def log_event(event_type, description, level="info", file_path=None, username=None):
    """Logge un événement dans la table events"""
    # si event_type invalide => remplacer par "info" (évite IntegrityError)
    valid_types = ["info", "warning", "error", "alert", "baseline"]
    if event_type not in valid_types:
        event_type = "info"

    execute_write("""
        INSERT INTO events (event_type, description, level, file_path, username)
        VALUES (?, ?, ?, ?, ?)
    """, (event_type, description, level, file_path, username))


def add_notification(title, message, status="pending", username=None):
    """Ajoute une notification à la table"""
    execute_write("""
        INSERT INTO notifications (title, message, status, username)
        VALUES (?, ?, ?, ?)
    """, (title, message, status, username))


def mark_notification_sent(notification_id):
    """Marque une notification comme envoyée"""
    execute_write("UPDATE notifications SET status='sent', sent_at=datetime('now') WHERE id=?", (notification_id,))


# ==============================
# HELPERS
# ==============================
def get_baseline_dict():
    """Alias pour compatibilité"""
    return get_baseline()


# ==============================
# DASHBOARD / STATISTICS
# ==============================


def get_dashboard_stats(username=None):
    """Return a summary of user-specific stats for the dashboard."""
    if not username:
        return {}

    stats = {}

    # --- Folders owned by user ---
    stats["total_folders"] = execute_fetchall(
        "SELECT COUNT(*) FROM folders WHERE added_by=?",
        (username,)
    )[0][0]

    # --- Baseline files owned by user ---
    stats["total_baseline_files"] = execute_fetchall(
        "SELECT COUNT(*) FROM baseline WHERE username=?",
        (username,)
    )[0][0]

    # --- Suspects owned by user ---
    stats["suspects_total"] = execute_fetchall(
        "SELECT COUNT(*) FROM suspects WHERE username=? AND resolved=0",
        (username,)
    )[0][0]

    stats["suspects_modified"] = execute_fetchall(
        "SELECT COUNT(*) FROM suspects WHERE username=? AND state='modified' AND resolved=0",
        (username,)
    )[0][0]

    stats["suspects_deleted"] = execute_fetchall(
        "SELECT COUNT(*) FROM suspects WHERE username=? AND state='deleted' AND resolved=0",
        (username,)
    )[0][0]

    stats["suspects_new"] = execute_fetchall(
        """
        SELECT COUNT(*) FROM baseline
        WHERE username=? 
          AND created_at >= datetime('now', '-1 day')
        """,
        (username,)
    )[0][0]

    # --- Events related to the user ---
    stats["events_info"] = execute_fetchall(
        "SELECT COUNT(*) FROM events WHERE username=? AND event_type='info'",
        (username,)
    )[0][0]

    stats["events_alert"] = execute_fetchall(
        "SELECT COUNT(*) FROM events WHERE username=? AND event_type='alert'",
        (username,)
    )[0][0]

    stats["events_warning"] = execute_fetchall(
        "SELECT COUNT(*) FROM events WHERE username=? AND event_type='warning'",
        (username,)
    )[0][0]

    stats["events_error"] = execute_fetchall(
        "SELECT COUNT(*) FROM events WHERE username=? AND event_type='error'",
        (username,)
    )[0][0]

    # --- Notifications for this user ---
    stats["pending_notifications"] = execute_fetchall(
        "SELECT COUNT(*) FROM notifications WHERE username=? AND status='pending'",
        (username,)
    )[0][0]

    return stats


def get_file_stats_for_user_file(path, username):
    path = os.path.normpath(path)

    # ----------------------------------------------------
    # 1. Baseline info for this user
    # ----------------------------------------------------
    baseline_row = execute_fetchall("""
        SELECT b.path, b.hash, b.size, b.modified_time, b.username, f.path
        FROM baseline b
        JOIN folders f ON b.folder_id = f.id
        WHERE b.path = ? AND b.username = ?
    """, (path, username))

    baseline_info = None
    if baseline_row:
        r = baseline_row[0]
        baseline_info = {
            "path": r[0],
            "hash": r[1],
            "size": r[2],
            "modified_time": r[3],
            "username": r[4],
            "folder_path": r[5]
        }

    # ----------------------------------------------------
    # 2. Suspect info (even if file deleted / not in baseline)
    # ----------------------------------------------------
    suspect_row = execute_fetchall("""
        SELECT path, old_hash, last_hash, state, first_detected, last_seen, resolved
        FROM suspects
        WHERE path = ? AND username = ?
        ORDER BY last_seen DESC
        LIMIT 1
    """, (path, username))

    suspect_info = None
    if suspect_row:
        s = suspect_row[0]
        suspect_info = {
            "path": s[0],
            "old_hash": s[1],
            "last_hash": s[2],
            "state": s[3],
            "first_detected": s[4],
            "last_seen": s[5],
            "resolved": s[6]
        }

    # ----------------------------------------------------
    # 3. Suspect counts by state
    # ----------------------------------------------------
    counts_rows = execute_fetchall("""
            SELECT state, COUNT(*)
            FROM suspects
            WHERE path = ? AND username = ?
            GROUP BY state
        """, (path, username))

    counts = {"modified": 0, "deleted": 0}
    for state, count in counts_rows:
        if state in counts:
            counts[state] = count

    return {
        "baseline": baseline_info,
        "suspect": suspect_info,
        "suspect_counts": counts
    }


def get_recent_events(limit=10):
    """Return the N most recent events."""
    return execute_fetchall("""
        SELECT timestamp, event_type, description, file_path, level
        FROM events
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))


def get_suspect_trend(days=7, username=None):
    if not username:
        return []

    query = f"""
        SELECT strftime('%Y-%m-%d', first_detected) AS day, COUNT(*)
        FROM suspects
        WHERE username = ?
          AND first_detected >= datetime('now', '-{days} days')
        GROUP BY day
        ORDER BY day
    """
    return execute_fetchall(query, (username,))


def get_event_trend(days=7):
    """Return number of events per day (for charts)."""
    return execute_fetchall(f"""
        SELECT strftime('%Y-%m-%d', timestamp) AS day, COUNT(*)
        FROM events
        WHERE timestamp >= datetime('now', '-{days} days')
        GROUP BY day
        ORDER BY day 
    """)


def get_top_modified_files(limit=5):
    """Return top modified files (recent suspects)."""
    return execute_fetchall("""
        SELECT path, state, last_seen
        FROM suspects
        WHERE resolved=0 AND state='modified'
        ORDER BY last_seen DESC
        LIMIT ?
    """, (limit,))


def get_notifications(limit=5, user="user"):
    """Return latest notifications."""
    return execute_fetchall("""
        SELECT title, message, status, sent_at 
        FROM notifications
        where username = ?
        ORDER BY sent_at DESC
        LIMIT ?
    """, (user, limit,))


def get_notifications_all(user="user"):
    """Return latest notifications."""
    return execute_fetchall("""
        SELECT title, message, status, sent_at 
        FROM notifications
        where username = ?
        ORDER BY sent_at DESC

    """, (user,))


def get_events_by_user(username, limit=None):
    """
    Retourne tous les événements pour un utilisateur spécifique sous forme de tuples.

    :param username: nom de l'utilisateur
    :param limit: (optionnel) nombre maximum de résultats
    :return: tuple de tuples [(id, timestamp, event_type, file_path, description, level, username), ...]
    """
    query = """
        SELECT id, timestamp, event_type, file_path, description, level, username 
        FROM events 
        WHERE username = ? 
        ORDER BY timestamp DESC
    """
    params = [username]

    if limit:
        query += f" LIMIT {int(limit)}"

    rows = execute_fetchall(query, tuple(params))  # doit renvoyer une liste de tuples

    # On crée une liste de tuples, puis on convertit en tuple final
    events = [(
        row[2],  # event_type
        row[3],  # file_path
        row[1],  # timestamp
        row[4],  # description
        row[5]
    ) for row in rows]

    return tuple(events)


def get_events_by_level(username, level):
    query = "SELECT event_type, file_path, timestamp, description, level FROM events WHERE username=? AND event_type=? ORDER BY timestamp DESC"
    return execute_fetchall(query, (username, level))


def get_events_by_date_range(username, days=30, level=None):
    query = """
        SELECT event_type, file_path, timestamp, description, level
        FROM events
        WHERE username = ?
          AND timestamp >= datetime('now', ?)
    """
    params = [username, f'-{days} days']

    if level:
        query += " AND event_type = ?"
        params.append(level)

    query += " ORDER BY timestamp DESC"

    rows = execute_fetchall(query, tuple(params))
    # Conversion en tuple
    events = [tuple(row) for row in rows]
    return tuple(events)


# ==============================
#  SCAN HISTORY MANAGEMENT
# ==============================

def add_scan_history(username, status):
    execute_write("""
        INSERT INTO scan_history (username, status)
        VALUES (?, ?)
    """, (username, status))


def get_user_history(username, limit=None):
    """
    Retourne l'historique des scans d'un user.
    """
    query = """
        SELECT id, time, status
        FROM scan_history
        WHERE username = ?
        ORDER BY time DESC
    """
    params = [username]

    if limit:
        query += " LIMIT ?"
        params.append(int(limit))

    rows = execute_fetchall(query, tuple(params))

    # On renvoie une liste de dicts
    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "time": row[1],
            "status": row[2]
        })

    return history


def get_last_scan(username):
    """
    Retourne le dernier scan effectué par un user.
    """
    rows = execute_fetchall("""
        SELECT id, time, status, result
        FROM scan_history
        WHERE username = ?
        ORDER BY time DESC
        LIMIT 1
    """, (username,))

    if not rows:
        return None

    r = rows[0]
    return {
        "id": r[0],
        "time": r[1],
        "status": r[2]
    }


def clear_all_tables():
    conn = get_connection()
    c = conn.cursor()

    # Désactiver les contraintes FK pour éviter les erreurs
    c.execute("PRAGMA foreign_keys = OFF;")

    # Liste des tables à vider
    tables = [
        "folders",
        "baseline",
        "suspects",
        "events",
        "notifications",
        "scan_history"
    ]

    for table in tables:
        c.execute(f"DELETE FROM {table};")
        c.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")  # reset AUTOINCREMENT

    # Réactiver les FK
    c.execute("PRAGMA foreign_keys = ON;")

    conn.commit()
    conn.close()

    print("✔ Toutes les tables ont été vidées avec succès !")