# profil.py
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPixmap, QIcon, QFont
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from ui.edit_profile import *

class ProfileMenuMixin:
    def __init__(self):
        # Initialiser avec des valeurs par défaut
        self.is_dark_theme = False
        self.current_style = None
        self.username = None  # ← Ajouter pour stocker le username
        self.email = None

    def set_theme(self, is_dark_theme, current_style=None):
        """Définit le thème pour le menu profil"""
        self.is_dark_theme = is_dark_theme
        self.current_style = current_style
        self.apply_profile_theme()

    def set_username(self, username):
        """Définit le nom d'utilisateur"""
        self.username = username
        if hasattr(self, 'user_name') and self.user_name:
            self.user_name.setText(username)

    def set_email(self, email):
        """Définit l'email de l'utilisateur"""
        self.email = email
        if hasattr(self, 'user_email') and self.user_email:
            self.user_email.setText(email)

    def create_profile_menu(self):
        """Crée le menu profil en haut à droite, même style que les boutons de la sidebar"""
        # --- Container horizontal ---
        self.profile_container = QWidget()
        self.profile_layout = QHBoxLayout(self.profile_container)
        self.profile_layout.setContentsMargins(0, 0, 0, 0)
        self.profile_layout.setSpacing(4)
        self.profile_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # --- Bouton profil (même style que create_nav_button) ---
        self.profile_btn = QPushButton()
        self.profile_btn.setFixedHeight(45)
        self.profile_btn.setFont(QFont("Segoe UI", 10))
        self.profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.profile_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        icon_pixmap = QPixmap("img/profile.png").scaled(
            40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.profile_btn.setIcon(QIcon(icon_pixmap))
        self.profile_btn.setIconSize(QSize(40, 40))

        self.profile_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                text-align: left;
                padding-left: 5px;
                padding-right: 5px;
            }
        """)

        # --- Flèche à droite ---
        self.arrow_icon = QLabel()
        self.arrow_icon.setFixedSize(16, 16)
        self.arrow_icon.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        # ✅ Forcer le pixmap dès la création (au lieu d'attendre un clic)
        arrow_pixmap = QPixmap("img/arrow_down.png").scaled(
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
        self.profile_container.setMinimumWidth(self.profile_btn.width() + 20)

        # Connexion du clic
        self.profile_btn.clicked.connect(self.toggle_profile_menu)

        # Créer le menu déroulant
        self.create_profile_dropdown()
        self.profile_dropdown.setVisible(False)

        return self.profile_container

    def create_profile_dropdown(self):
        """Crée le menu déroulant du profil avec icône et username horizontalement"""
        self.profile_dropdown = QWidget()
        self.profile_dropdown.setFixedWidth(300)
        self.profile_dropdown.setFixedHeight(220)

        self.profile_dropdown.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px ;
                border-radius: 8px;
                padding: 5px;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            }
        """)

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
        profile_pixmap = QPixmap("img/profile.png").scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio,
                                                              Qt.TransformationMode.SmoothTransformation)
        profile_icon_label.setPixmap(profile_pixmap)
        profile_icon_label.setFixedSize(48, 48)
        profile_icon_label.setStyleSheet("""
            QLabel {
                border-radius: 24px;  /* 50% de 48px */
                border: none;
            }
        """)
        # Container pour nom et email (empilés verticalement à droite de l'icône)
        name_email_container = QWidget()
        name_email_layout = QVBoxLayout(name_email_container)
        name_email_layout.setContentsMargins(0, 0, 0, 0)

        # Username (en haut) - utiliser le vrai nom d'utilisateur si disponible
        self.user_name = QLabel(self.username if self.username else " Utilisateur")
        self.user_name.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.user_name.setStyleSheet("color: #2D3748; margin: 0; padding-left:5px;")

        # Email (en dessous du username)
        self.user_email = QLabel(self.email if self.email else "john.doe@example.com")  # Vous pouvez modifier ça plus tard
        self.user_email.setFont(QFont("Segoe UI", 8))
        self.user_email.setStyleSheet("color: #525063;margin: 0; padding-left:1px;font-weight:bold;")
        self.user_name.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # ← AJOUT: alignement vertical

        name_email_layout.addWidget(self.user_name)
        name_email_layout.addWidget(self.user_email)

        # Ajouter icône et container nom/email au layout horizontal
        user_layout.addWidget(profile_icon_label)
        user_layout.addWidget(name_email_container)
        user_layout.setAlignment(profile_icon_label, Qt.AlignmentFlag.AlignTop)  # ← Aligner l'icône en haut
        user_layout.setAlignment(name_email_container, Qt.AlignmentFlag.AlignTop)  # ← Aligner le texte en haut

        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3342CC; margin: 8px 0;font-weight=3;")
        separator.setFixedHeight(2)

        # Boutons avec icônes
        self.edit_profile_btn = QPushButton()
        self.logout_btn = QPushButton()

        # Style des boutons avec icônes
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

        # Configuration des icônes et textes
        edit_icon = QIcon("img/edit.png")
        logout_icon = QIcon("img/logout.png")

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
        dropdown_layout.addWidget(user_section)  # Section horizontale icône + nom/email
        dropdown_layout.addWidget(separator)
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
            arrow_pixmap = QPixmap("img/arrow_down.png").scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio,
                                                                   Qt.TransformationMode.SmoothTransformation)
            self.arrow_icon.setPixmap(arrow_pixmap)
        else:
            # Ouvrir le menu
            self.profile_dropdown.setVisible(True)
            # Changer la flèche vers le haut
            arrow_pixmap = QPixmap("img/arrow_up.png").scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio,
                                                                 Qt.TransformationMode.SmoothTransformation)
            # --- Correct position calculation ---
            btn_global_pos = self.profile_btn.mapToGlobal(self.profile_btn.rect().bottomRight())
            parent_global_pos = self.parentWidget().mapToGlobal(self.parentWidget().rect().topLeft())

            # Position the dropdown so its right edge aligns with the button’s right edge
            dropdown_x = btn_global_pos.x() - parent_global_pos.x() - self.profile_dropdown.width() + self.profile_btn.width()
            dropdown_y = btn_global_pos.y() - parent_global_pos.y() + 6  # small gap below button
            self.arrow_icon.setPixmap(arrow_pixmap)


            # Positionner le menu déroulant CORRECTEMENT
            # Obtenir la position globale du bouton
            button_global_pos = self.profile_btn.mapToGlobal(self.profile_btn.rect().bottomRight())

            # Convertir en coordonnées locales du parent (MainPage)
            parent_global_pos = self.mapToGlobal(self.rect().topLeft())

            # Calculer la position relative
            dropdown_x = button_global_pos.x() - parent_global_pos.x() - 200  # Aligner à droite
            dropdown_y = button_global_pos.y() - parent_global_pos.y() + 5

            # Déplacer le menu
            self.profile_dropdown.move(dropdown_x, dropdown_y)
            self.profile_dropdown.raise_()  # S'assurer qu'il est au-dessus des autres widgets

    def edit_profile(self):
        """Ouvre la fenêtre d'édition du profil"""
        self.edit_window = EditProfileWindow(
            username=self.username or "",
            email=self.email or "",
            is_dark_theme=self.is_dark_theme,
            parent=self
        )
        self.edit_window.show()

    def logout(self):
        """Déconnecte l'utilisateur"""
        print("Logout clicked")
        # À implémenter - retour à la page de login

    def apply_profile_theme(self):
        """Applique le thème au menu profil"""
        # Cette méthode peut être utilisée pour appliquer des styles spécifiques au thème
        pass