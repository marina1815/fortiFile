import json
import os
import hashlib
from datetime import datetime
import socket
from core.email_sender import send_confirmation_email  # ton module existant
import core.gestion_db as db
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dossier principal
USERS_FILE = os.path.join(BASE_DIR, "users.json")
CURRENT_USER_FILE = os.path.join(BASE_DIR, "userCurrent.json")
HISTORIQUE_FILE = os.path.join(BASE_DIR, "historiqueLogin.json")
PROFIL_FILE = os.path.join(BASE_DIR, "profil.json")
USER_ACTUEL = ""


# ========= 🔹 Fonctions utilitaires =========
def hash_password(password: str) -> str:
    """Retourne le hash SHA256 du mot de passe."""
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    """Charge les utilisateurs depuis le fichier JSON."""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    """Sauvegarde le dictionnaire d'utilisateurs dans users.json."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)


def save_current_user(username):
    """Sauvegarde le user actuellement connecté dans userCurrent.json."""
    with open(CURRENT_USER_FILE, "w", encoding="utf-8") as f:
        json.dump({"username": username}, f, indent=4)


def load_current_user():
    """Retourne l'utilisateur actuellement connecté."""
    if os.path.exists(CURRENT_USER_FILE):
        with open(CURRENT_USER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("username", "")
    return USER_ACTUEL


def edit_user(username, email, password, dateNaissance):
    """Crée un nouvel utilisateur avec mot de passe hashé."""
    users = load_users()
    users[email] = {
        "username": username,
        "password": hash_password(password),
        "dateNaissance": dateNaissance
    }
    save_users(users)
    save_current_user(username)
    return True


def get_date_of_birth_by_username(username):
    """Retourne la date de naissance pour un username donné."""
    users = load_users()
    for email, data in users.items():
        if data.get("username") == username:
            return data.get("dateNaissance")
    return None


def get_hashed_password_by_username(username):
    """Retourne le hash du mot de passe pour un username donné."""
    users = load_users()
    for email, data in users.items():
        if data.get("username") == username:
            return data.get("password")
    return None


# ========= 🔸 Fonctions principales =========
def register_user(username, email, password):
    """Crée un nouvel utilisateur avec mot de passe hashé."""
    users = load_users()
    users[email] = {
        "username": username,
        "password": hash_password(password),
        "dateNaissance": ""
    }
    save_users(users)
    return True, "Compte créé avec succès !"


def verifier_email(email):
    users = load_users()
    return email not in users


def verifier_username(username):
    users = load_users()
    return not any(data['username'] == username for data in users.values())


def reset_password(email, new_password):
    """Réinitialise le mot de passe d'un utilisateur existant."""
    users = load_users()
    if email not in users:
        return False, "Aucun compte trouvé avec cet email."
    users[email]["password"] = hash_password(new_password)
    save_users(users)
    send_confirmation_email(email, users[email]["username"])
    return True, "Mot de passe réinitialisé avec succès !"


def list_users():
    """Affiche et retourne la liste des utilisateurs et leurs rôles."""
    users = load_users()
    if not users:
        return []
    current_user = load_current_user()
    user_list = [{"username": "Username", "email": "Email", "role": "Role"}]
    for email, data in users.items():
        role = "Admin" if data['username'] == current_user else "User standard"
        user_list.append({
            "username": data["username"],
            "email": email,
            "role": role
        })
    return user_list


def change_username(old_username, new_username):
    """Change le nom d'utilisateur."""
    users = load_users()
    if any(data['username'] == new_username for data in users.values()):
        return False, "Ce nom d'utilisateur est déjà utilisé."
    for email, data in users.items():
        if data['username'] == old_username:
            data['username'] = new_username
            save_users(users)
            save_current_user(new_username)
            return True, "Nom d'utilisateur mis à jour avec succès !"
    return False, "Utilisateur non trouvé."


def change_password(email, old_password, new_password):
    """Change le mot de passe si l'ancien est correct."""
    users = load_users()
    if email not in users:
        return False, "Email non trouvé."
    if users[email]["password"] != hash_password(old_password):
        return False, "Ancien mot de passe incorrect."
    users[email]["password"] = hash_password(new_password)
    save_users(users)
    return True, "Mot de passe mis à jour avec succès !"


def change_email(old_email, new_email):
    """Change l'email si le nouveau n'existe pas déjà."""
    users = load_users()
    if old_email not in users:
        return False, "Email actuel non trouvé."
    if new_email in users:
        return False, "Le nouvel email est déjà utilisé."
    users[new_email] = users.pop(old_email)
    save_users(users)
    return True, "Email mis à jour avec succès !"


def get_email_by_username(username):
    """Recherche l'email correspondant à un nom d'utilisateur."""
    users = load_users()
    for email, data in users.items():
        if data.get("username") == username:
            return email
    return None


# ========= 🔹 Fonctions historiques et login =========
def load_historique():
    """Charge l'historique des connexions depuis le fichier JSON."""
    if not os.path.exists(HISTORIQUE_FILE):
        return []


    with open(HISTORIQUE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_historique(historique):
    """Sauvegarde l'historique des connexions dans le fichier JSON."""
    with open(HISTORIQUE_FILE, "w", encoding="utf-8") as f:
        json.dump(historique, f, indent=4)


def get_ip_address():
    """Retourne l'IP locale de l'utilisateur."""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return ip
    except Exception:
        return "IP inconnue"


def log_login(username, lieu=None):
    """Enregistre la connexion d'un utilisateur avec la date et le lieu."""
    historique = load_historique()
    if lieu is None:
        lieu = "Oran"  # par défaut si pas spécifié
    connexion = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": username,
        "location": lieu,
        "device": socket.gethostname()
    }
    historique.append(connexion)
    save_historique(historique)
    print(f"[LOGIN] {username} connecté depuis {lieu} ({connexion['device']}) à {connexion['timestamp']}")
    db.log_event("info", f"[LOGIN] {username} connecté depuis {lieu} ({connexion['device']}) à {connexion['timestamp']}", username=load_current_user())


def verify_login(email, password, lieu=None):
    """Vérifie si l'utilisateur existe et si le mot de passe est correct, et logge la connexion."""
    global USER_ACTUEL
    users = load_users()
    if email not in users:
        return False, "Aucun compte trouvé avec cet email."
    hashed_input = hash_password(password)
    if users[email]["password"] == hashed_input:
        USER_ACTUEL = users[email]['username']
        save_current_user(USER_ACTUEL)
        log_login(USER_ACTUEL, lieu)
        return True, f"Bienvenue {USER_ACTUEL} !"
    else:
        return False, "Mot de passe incorrect."


import os
import json


def ensure_profile_file(username: str, path_photo: str):
    # Si le fichier existe
    if os.path.exists(PROFIL_FILE):
        try:
            with open(PROFIL_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"{PROFIL_FILE} existe déjà.")
        except (json.JSONDecodeError, IOError):
            # Si le fichier est corrompu ou illisible, on le recrée
            print(f"{PROFIL_FILE} est corrompu. Réinitialisation.")
            data = {}
    else:
        print(f"{PROFIL_FILE} n'existe pas. Création du fichier.")
        data = {}

    # Vérifie si l'utilisateur existe dans le fichier
        # Mettre à jour ou ajouter l'utilisateur
    data[username] = {"path_photo": path_photo}

    # Sauvegarder le fichier
    with open(PROFIL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"Photo de '{username}' mise à jour dans {PROFIL_FILE}.")


def get_user_photo(username: str, file_path=PROFIL_FILE) -> str | None:
    """
    Récupère le chemin de la photo de l'utilisateur depuis profil.json.

    Args:
        username (str): Nom de l'utilisateur
        file_path (str): Chemin du fichier JSON (par défaut 'profil.json')

    Returns:
        str | None: Chemin de la photo si trouvé, sinon None
    """
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(username, {}).get("path_photo")
    except (json.JSONDecodeError, IOError):
        return None