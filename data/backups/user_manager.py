import json
import os
import hashlib
from core.email_sender import send_confirmation_email  # ton module existant

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dossier principal
USERS_FILE = os.path.join(BASE_DIR, "users.json")
CURRENT_USER_FILE = os.path.join(BASE_DIR, "userCurrent.json")

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


# ========= 🔸 Fonctions principales =========
def register_user(username, email, password):
    """Crée un nouvel utilisateur avec mot de passe hashé."""
    users = load_users()

    users[email] = {
        "username": username,
        "password": hash_password(password)
    }
    save_users(users)

    return True, "Compte créé avec succès !"

def verifier_email(email):
    users = load_users()
    if email in users:
        return False
    return True

def verifier_username(username):
    users = load_users()
    # Vérification unicité username
    if any(data['username'] == username for data in users.values()):
        return False
    return True

def verify_login(email, password):
    """Vérifie si l'utilisateur existe et si le mot de passe est correct."""
    global USER_ACTUEL
    users = load_users()
    if email not in users:
        return False, "Aucun compte trouvé avec cet email."
    hashed_input = hash_password(password)
    if users[email]["password"] == hashed_input:
        USER_ACTUEL = users[email]['username']
        save_current_user(USER_ACTUEL)
        return True, f"Bienvenue {USER_ACTUEL} !"
    else:
        return False, "Mot de passe incorrect."


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
    user_list = []
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