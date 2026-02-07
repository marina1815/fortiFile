from PyQt6.QtWidgets import (
    QWidget, QStackedWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QPixmap, QIcon, QFont

from ui.gui_home import MainPage
from ui.gui_dashboard import DashboardPage


class AppWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 🌙 Thème (par défaut clair)
        self.is_dark_theme = False
        self.sidebar_expanded = False

        # 🧱 Structure générale
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === Sidebar + Zone de contenu ===
        self.create_sidebar()

        # Zone centrale (pour les pages)
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.stack)

        # Pages
        self.home_page = None
        self.dashboard_page = None

        # Taille de la fenêtre
        self.setMinimumSize(1000, 600)

    # =========================================================
    # 🔹 Création de la sidebar
    # =========================================================
    def create_sidebar(self):
        """Crée une sidebar collapsible"""
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(100)
        self.apply_sidebar_style()

        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(20, 10, 10, 10)
        self.sidebar_layout.setSpacing(10)

        self.create_sidebar_logo()
        self.create_sidebar_buttons()

        self.sidebar_layout.addStretch()
        self.show_sidebar_text(False)

    def create_sidebar_logo(self):
        """Logo et texte FortiFile"""
        logo_container = QWidget()
        logo_container.setFixedHeight(50)
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)

        logo_label = QLabel()
        logo_label.setFixedSize(40, 40)
        logo_pixmap = QPixmap("img/sign.png").scaled(
            40, 40, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo_text = QLabel("FortiFile")
        self.logo_text.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.logo_text.setStyleSheet("color: white;")
        self.logo_text.setVisible(False)

        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(self.logo_text)
        self.sidebar_layout.addWidget(logo_container)

    # =========================================================
    # 🔹 Boutons de la sidebar
    # =========================================================
    def create_sidebar_buttons(self):
        self.sidebar_layout.addSpacing(20)
        self.scan_btn = self.create_nav_button("img/scanner.png", "Home", "scanner")
        self.dashboard_btn = self.create_nav_button("img/dashboard.png", "Dashboard", "dashboard")
        self.identity_btn = self.create_nav_button("img/identity.png", "Identity", "identity")

        for btn in [self.scan_btn, self.dashboard_btn, self.identity_btn]:
            self.sidebar_layout.addWidget(btn)

        self.sidebar_layout.addSpacing(200)

        self.settings_btn = self.create_nav_button("img/setting.png", "Settings", "setting")
        self.help_btn = self.create_nav_button("img/question.png", "Help", "question")
        self.about_btn = self.create_nav_button("img/about.png", "About", "about")

        for btn in [self.settings_btn, self.help_btn, self.about_btn]:
            self.sidebar_layout.addWidget(btn)

        self.select_button(self.scan_btn)

    def create_nav_button(self, icon_path, tooltip="", button_id=""):
        """Crée un bouton de navigation avec icône"""
        button = QPushButton()
        button.setFixedHeight(45)
        button.setFont(QFont("Segoe UI", 10))
        button.setProperty("button_id", button_id)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        icon_pixmap = QPixmap(icon_path).scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation)
        button.setIcon(QIcon(icon_pixmap))
        button.setIconSize(QSize(28, 28))
        button.clicked.connect(lambda checked, btn=button: self.on_nav_button_clicked(btn))
        button.clicked.connect(self.toggle_sidebar)
        button.setToolTip(tooltip)
        return button

    # =========================================================
    # 🔹 Animations Sidebar
    # =========================================================
    def toggle_sidebar(self):
        self.sidebar_expanded = not self.sidebar_expanded

        self.animation = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuart)

        if self.sidebar_expanded:
            self.animation.setStartValue(100)
            self.animation.setEndValue(200)
            self.animation.finished.connect(lambda: self.show_sidebar_text(True))
        else:
            self.show_sidebar_text(False)
            self.animation.setStartValue(200)
            self.animation.setEndValue(100)

        self.animation.start()

    def show_sidebar_text(self, show):
        """Affiche ou cache le texte des boutons"""
        buttons = [self.scan_btn, self.dashboard_btn, self.identity_btn,
                   self.settings_btn, self.help_btn, self.about_btn]
        texts = [" Home", " Dashboard", " Identity", " Settings", " Help", " About"]

        self.logo_text.setVisible(show)

        for btn, text in zip(buttons, texts):
            btn.setText(text if show else "")
            btn.setToolTip("" if show else text.strip())

    # =========================================================
    # 🔹 Thèmes
    # =========================================================
    def apply_sidebar_style(self):
        if self.is_dark_theme:
            self.sidebar.setStyleSheet("""
                QWidget {
                    background-color: #1E1E1E;
                    border-right: 1px solid #444;
                }
                QPushButton {
                    color: white;
                    border: none;
                    border-radius: 5px;
                    text-align: left;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #333;
                }
            """)
        else:
            self.sidebar.setStyleSheet("""
                QWidget {
                    background-color: #151B54;
                    border-right: 1px solid #5A4FDF;
                }
                QPushButton {
                    color: #FFFFFF;
                    border: none;
                    text-align: left;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #5A4FDF;
                }
            """)

    # =========================================================
    # 🔹 Gestion des pages
    # =========================================================
    def load_home(self, username):
        if self.home_page is None:
            self.home_page = MainPage(username=username, is_dark_theme=False)
            self.stack.addWidget(self.home_page)
            self.home_page.navigate_dashboard = lambda: self.load_dashboard(username)
        self.stack.setCurrentWidget(self.home_page)

    def load_dashboard(self, username):
        if self.dashboard_page is None:

            self.dashboard_page = DashboardPage(username=username)
            self.stack.addWidget(self.dashboard_page)
        self.stack.setCurrentWidget(self.dashboard_page)

    # =========================================================
    # 🔹 Sélection bouton
    # =========================================================
    def on_nav_button_clicked(self, clicked_button):
        self.select_button(clicked_button)
        button_id = clicked_button.property("button_id")
        print(f"Bouton cliqué: {button_id}")

        # 🚀 Charger la page correspondante
        if button_id == "scanner":
            self.load_home(username="User")  # ou passe le vrai username
        elif button_id == "dashboard":
            self.load_dashboard(username="User")
        elif button_id == "identity":
            print("Identity page pas encore implémentée")
        elif button_id == "setting":
            print("Settings page pas encore implémentée")
        elif button_id == "question":
            print("Help page pas encore implémentée")
        elif button_id == "about":
            print("About page pas encore implémentée")

    def select_button(self, button):
        """Met en surbrillance le bouton actif"""
        for btn in [self.scan_btn, self.dashboard_btn, self.identity_btn,
                    self.settings_btn, self.help_btn, self.about_btn]:
            btn.setStyleSheet("background-color: transparent; color: white;")
        button.setStyleSheet("background-color: #5A4FDF; color: white; font-weight: bold;")
