import subprocess
import sys
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPixmap, QIcon, QFont
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from ui.edit_profile import *
from core.user_manager import (
    load_current_user, get_email_by_username, get_hashed_password_by_username,
    get_date_of_birth_by_username, edit_user, hash_password, list_users, get_user_photo
)
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
user = load_current_user()
photo_path = get_user_photo(user)
if photo_path:
    profil_path = os.path.normpath(photo_path)
else:
    profil_path = os.path.join(base_dir, "../img/profile.png")

edit_path = os.path.join(base_dir,"../img/edit.png")
login_path = os.path.join(base_dir,"../img/logout.png")
down_path = os.path.join(base_dir,"../img/arrow_down.png")
up_path = os.path.join(base_dir,"../img/arrow_up.png")



class ProfileMenuMixin:
    def __init__(self):
        # Initialiser avec des valeurs par défaut
        self.is_dark_theme = False
        self.current_style = None
        self.username = None  # ← Ajouter pour stocker le username
        self.username=load_current_user()
        self.email=get_email_by_username(self.username)




    def set_username(self, username):
        """Définit le nom d'utilisateur"""
        self.username = load_current_user()
        self.email=get_email_by_username(self.username)
        if hasattr(self, 'user_name') and self.user_name:
            self.user_name.setText(self.username)
        if hasattr(self, 'user_email') and self.user_email:
            self.user_email.setText(self.email)

    def set_email(self, email):
        """Définit l'email de l'utilisateur"""
        self.email = email
        if hasattr(self, 'user_email') and self.user_email:
            self.user_email.setText(self.email)

    def create_profile_menu(self):
        """Crée le menu profil en haut à droite, même style que les boutons de la sidebar"""
        # --- Container horizontal ---
        self.profile_container = QWidget()
        self.profile_layout = QHBoxLayout(self.profile_container)
        self.profile_layout.setContentsMargins(0, 0, 0, 0)
        self.profile_layout.setSpacing(4)
        #self.profile_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # --- Bouton profil (même style que create_nav_button) ---
        self.profile_btn = QPushButton()
        self.profile_btn.setFixedHeight(45)
        self.profile_btn.setFont(QFont("Segoe UI", 10))
        self.profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        #self.profile_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.profile_btn.setFixedSize(45, 45)

        icon_pixmap = QPixmap(profil_path).scaled(
            40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.profile_btn.setIcon(QIcon(icon_pixmap))
        self.profile_btn.setIconSize(QSize(40, 40))

        # Connexion du clic
        self.profile_btn.clicked.connect(self.toggle_profile_menu)

        # --- Flèche à droite ---
        self.arrow_icon = QLabel()
        self.arrow_icon.setFixedSize(16, 16)
        self.arrow_icon.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        # ✅ Forcer le pixmap dès la création (au lieu d'attendre un clic)
        arrow_pixmap = QPixmap(down_path).scaled(
            16, 16,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        if arrow_pixmap.isNull():
            print("⚠️ Image arrow_down.png introuvable dans 'img/'")
        self.arrow_icon.setPixmap(arrow_pixmap)

        # --- Ajout dans le layout ---
        self.profile_layout.addWidget(self.profile_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.profile_layout.addWidget(self.arrow_icon, alignment=Qt.AlignmentFlag.AlignVCenter)

        # --- Largeur du container ---
        self.profile_container.setMinimumWidth(self.profile_btn.width())

        # Créer le menu déroulant
        self.create_profile_dropdown()
        self.profile_dropdown.setVisible(False)

        # Appliquer le thème initial
        self.apply_profile_theme()

        return self.profile_container

    def create_profile_dropdown(self):
        """Crée le menu déroulant du profil avec icône et username horizontalement"""
        self.profile_dropdown = QWidget()
        self.profile_dropdown.setMaximumWidth(600)
        self.profile_dropdown.setMaximumHeight(200)

        dropdown_layout = QVBoxLayout(self.profile_dropdown)
        dropdown_layout.setContentsMargins(15, 15, 15, 15)
        dropdown_layout.setSpacing(12)

        # --- Ligne horizontale : Icône + Username ---
        user_header = QWidget()
        user_header_layout = QHBoxLayout(user_header)
        user_header_layout.setContentsMargins(0, 0, 0, 0)
        user_header_layout.setSpacing(8)

        # --- Section horizontale : Icône + (Nom et Email empilés) ---
        user_section = QWidget()
        user_layout = QHBoxLayout(user_section)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(0)

        # Icône du profil (à gauche)
        profile_icon_label = QLabel()
        profile_pixmap = QPixmap(profil_path).scaled(46, 46, Qt.AspectRatioMode.KeepAspectRatio,
                                                              Qt.TransformationMode.SmoothTransformation)
        profile_icon_label.setPixmap(profile_pixmap)
        profile_icon_label.setFixedSize(46, 46)

        # Container pour nom et email (empilés verticalement à droite de l'icône)
        name_email_container = QWidget()
        name_email_layout = QVBoxLayout(name_email_container)
        name_email_layout.setContentsMargins(0, 0, 0, 0)

        # Username (en haut) - utiliser le vrai nom d'utilisateur si disponible
        self.user_name = QLabel(self.username if self.username else " Utilisateur")
        self.user_name.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

        # Email (en dessous du username)
        self.user_email = QLabel(self.email if self.email else "john.doe@example.com")
        self.user_email.setFont(QFont("Segoe UI", 8))
        self.user_name.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        name_email_layout.addWidget(self.user_name)
        name_email_layout.addWidget(self.user_email)

        # Ajouter icône et container nom/email au layout horizontal
        user_layout.addWidget(profile_icon_label)
        user_layout.addWidget(name_email_container, stretch=1)
        user_layout.setAlignment(profile_icon_label, Qt.AlignmentFlag.AlignTop)
        user_layout.setAlignment(name_email_container, Qt.AlignmentFlag.AlignTop)

        # Séparateur
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFixedHeight(2)

        # Boutons avec icônes
        self.edit_profile_btn = QPushButton()
        self.logout_btn = QPushButton()

        # Configuration des icônes et textes
        edit_icon = QIcon(edit_path)
        logout_icon = QIcon(login_path)

        self.edit_profile_btn.setIcon(edit_icon)
        self.edit_profile_btn.setIconSize(QSize(16, 16))
        self.edit_profile_btn.setText("Edit Profile")

        self.logout_btn.setIcon(logout_icon)
        self.logout_btn.setIconSize(QSize(16, 16))
        self.logout_btn.setText("Log Out")

        # Connecter les boutons
        self.edit_profile_btn.clicked.connect(self.edit_profile)
        self.logout_btn.clicked.connect(self.logout)

        # Ajouter tout au layout principal
        dropdown_layout.addWidget(user_section)
        dropdown_layout.addWidget(self.separator)
        dropdown_layout.addWidget(self.edit_profile_btn)
        dropdown_layout.addWidget(self.logout_btn)

        # Positionner le menu déroulant
        self.profile_dropdown.setParent(self)
        self.profile_dropdown.setVisible(False)
        self.profile_dropdown.hide()

    def toggle_profile_menu(self):
        """Ouvre/ferme le menu profil et anime la flèche"""
        if self.profile_dropdown.isVisible():
            # Fermer le menu
            self.profile_dropdown.setVisible(False)
            # Changer la flèche vers le bas
            arrow_pixmap = QPixmap(down_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio,
                                                                   Qt.TransformationMode.SmoothTransformation)
            self.arrow_icon.setPixmap(arrow_pixmap)
        else:
            # Ouvrir le menu
            self.profile_dropdown.setVisible(True)
            # Changer la flèche vers le haut
            arrow_pixmap = QPixmap(up_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation)
            # Positionner le menu déroulant CORRECTEMENT
            button_global_pos = self.profile_btn.mapToGlobal(self.profile_btn.rect().bottomRight())
            parent_global_pos = self.mapToGlobal(self.rect().topLeft())

            # Calculer la position relative
            dropdown_x = button_global_pos.x() - parent_global_pos.x() - 200
            dropdown_y = button_global_pos.y() - parent_global_pos.y() + 5

            # Déplacer le menu
            self.profile_dropdown.move(dropdown_x, dropdown_y)
            self.profile_dropdown.raise_()
            self.arrow_icon.setPixmap(arrow_pixmap)

    def toggle_profile_menu(self):
        """Ouvre/ferme le menu profil et anime la flèche"""
        if self.profile_dropdown.isVisible():
            # Fermer le menu
            self.profile_dropdown.setVisible(False)
            # Changer la flèche vers le bas avec la bonne couleur selon le thème
            if self.is_dark_theme:
                arrow_pixmap = QPixmap("img/down_arrow_dark.png").scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio,
                                                                          Qt.TransformationMode.SmoothTransformation)
            else:
                arrow_pixmap = QPixmap(down_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio,
                                                                    Qt.TransformationMode.SmoothTransformation)
            self.arrow_icon.setPixmap(arrow_pixmap)
        else:
            # Ouvrir le menu
            self.profile_dropdown.setVisible(True)
            # Changer la flèche vers le haut avec la bonne couleur selon le thème
            if self.is_dark_theme:
                arrow_pixmap = QPixmap("img/up_arrow_dark.png").scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio,
                                                                        Qt.TransformationMode.SmoothTransformation)
            else:
                arrow_pixmap = QPixmap(up_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio,
                                                                  Qt.TransformationMode.SmoothTransformation)

            # Positionner le menu déroulant CORRECTEMENT
            button_global_pos = self.profile_btn.mapToGlobal(self.profile_btn.rect().bottomRight())
            parent_global_pos = self.mapToGlobal(self.rect().topLeft())

            # Calculer la position relative
            dropdown_x = button_global_pos.x() - parent_global_pos.x() - 200
            dropdown_y = button_global_pos.y() - parent_global_pos.y() + 5

            # Déplacer le menu
            self.profile_dropdown.move(dropdown_x, dropdown_y)
            self.profile_dropdown.raise_()
            self.arrow_icon.setPixmap(arrow_pixmap)

    def update_profile_info(self, new_username, new_email):
        """Met à jour l’affichage du menu après modification du profil"""

        self.username = new_username
        self.email = new_email

        if hasattr(self, 'user_name') and self.user_name:
            self.user_name.setText(self.username)
        if hasattr(self, 'user_email') and self.user_email:
            self.user_email.setText(self.email)



    def edit_profile(self):
        """Ouvre la fenêtre d'édition du profil"""
        self.edit_window = EditProfileWindow(
            username=self.username or "",
            email=self.email or "",
            is_dark_theme=self.is_dark_theme,
            parent=self
        )
        # Connecter le signal
        self.edit_window.profile_updated.connect(self.update_profile_info)
        self.edit_window.show()



    def logout(self):
        # Crée la nouvelle fenêtre de login
        from ui.gui_login import ModernWindow

        self.login_window = ModernWindow()
        self.login_window.show()

        # Centre la fenêtre
        from main import center_window
        center_window(self.login_window)

        # Ferme la fenêtre actuelle proprement
        self.window().close()

    def set_theme(self, is_dark_theme, current_style=None):
        """Définit le thème pour le menu profil"""
        self.is_dark_theme = is_dark_theme
        self.current_style = current_style
        self.apply_profile_theme()

    def apply_profile_theme(self):
        """Applique le thème au menu profil avec les mêmes couleurs que EditProfileWindow"""
        if self.is_dark_theme:
            # Style sombre - mêmes couleurs que EditProfileWindow
            self.profile_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    text-align: left;
                    padding-left: 5px;
                    padding-right: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: 5px;
                }
            """)

            self.profile_dropdown.setStyleSheet("""
                QWidget {
                    background-color: #141313;
                    border: 1px ;
                    border-radius: 8px;
                    padding: 5px;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                }
            """)

            button_style = """
                QPushButton {
                    background-color: transparent;
                    color: #E6E6E6;
                    font-weight: bold;
                    border: none;
                    padding: 8px 0px 8px 30px;
                    text-align: left;
                    font-size: 13px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #0E2B51;
                    color: #E6E6E6;
                }
            """

            self.edit_profile_btn.setStyleSheet(button_style)
            self.logout_btn.setStyleSheet(button_style)
            edit_icon_dark = QIcon("img/edit_dark.png")  # Icône edit originale
            logout_icon_dark = QIcon("img/logout_dark.png")  # Icône logout originale

            self.edit_profile_btn.setIcon(edit_icon_dark)
            self.logout_btn.setIcon(logout_icon_dark)
            self.user_name.setStyleSheet(
                "color: #E6E6E6; margin: 0; padding-left:3px; font-weight: bold; font-size:15px;")
            self.user_email.setStyleSheet("color: #E2E8F0; margin: 0; padding:2px; font-weight: bold;")
            self.separator.setStyleSheet("background-color: #0E2B51; margin: 8px 0;")

            # Style pour la flèche
            arrow_pixmap = QPixmap("img/down_arrow_dark.png").scaled(
                16, 16,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.arrow_icon.setPixmap(arrow_pixmap)

        else:
            # Style clair
            self.profile_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    text-align: left;
                    padding-left: 5px;
                    padding-right: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 0.1);
                    border-radius: 5px;
                }
            """)

            self.profile_dropdown.setStyleSheet("""
                QWidget {
                 background-color: white;
                border: 1px ;
                border-radius: 8px;
                padding: 5px;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                }
            """)

            button_style = """
                QPushButton {
                    background-color: transparent;
                    color:#141313;
                    font-weight: bold;
                    border: none;
                    padding: 8px 0px 8px 30px;  /* ← Ajouter du padding à gauche pour l'icône */
                    text-align: left;
                    font-size: 13px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #F7FAFC;
                    color: #2D3748;
                }
            """

            self.edit_profile_btn.setStyleSheet(button_style)
            self.logout_btn.setStyleSheet(button_style)

            self.user_name.setStyleSheet(
                "color: #2D3748; margin: 0; padding-left:3px; font-weight: bold; font-size:15px;")
            self.user_email.setStyleSheet("color: #525063; margin: 0; padding:2px; font-weight: bold;")
            self.separator.setStyleSheet("background-color: #3342CC; margin: 8px 0;")

            # ⭐⭐ RÉTABLIR LES ICÔNES ORIGINALES POUR LE THÈME CLAIR ⭐⭐
            edit_icon_light = QIcon(edit_path)  # Icône edit originale
            logout_icon_light = QIcon(login_path)  # Icône logout originale

            self.edit_profile_btn.setIcon(edit_icon_light)
            self.logout_btn.setIcon(logout_icon_light)
            # Style pour la flèche (thème clair)
            arrow_pixmap = QPixmap(down_path).scaled(
                16, 16,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.arrow_icon.setPixmap(arrow_pixmap)