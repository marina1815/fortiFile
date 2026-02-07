from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QPixmap, QAction
from PyQt6.QtCore import Qt
from ui.main_window import AppWindow
from core.email_sender import generate_code, send_code_confirmation_email, send_confirmation_email
from core.user_manager import hash_password, register_user, verify_login, reset_password, load_users, verifier_email, \
    verifier_username
from PyQt6.QtGui import QIcon

# =========================
# FENÊTRE PRINCIPALE
# =========================

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(30)
        self.setStyleSheet("""
           QWidget{
           border: none;
           }
            QLabel {
                color: white;
                font-weight: bold;
            }
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #d1cfcf;

            }
        """)

        # --- Logo + texte FortiFile ---
        self.logo = QLabel()
        pixmap = QPixmap("img\iconFortiFile.png").scaled(
            38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.logo.setPixmap(pixmap)

        self.title = QLabel("FortiFile")
        self.title.setFont(QFont("Segoe UI Light", 16, QFont.Weight.Bold))
        self.title.setStyleSheet("color: Black;")

        # --- Boutons à droite (avec icônes) ---
        self.btn_notify = QPushButton()
        self.btn_minimize = QPushButton()
        self.btn_maximize = QPushButton()
        self.btn_close = QPushButton()
        self.btn_mode = QPushButton()
        # 🔔 Remplace ces chemins par tes propres icônes
        self.btn_notify.setIcon(QIcon("img/bell.png"))
        self.btn_minimize.setIcon(QIcon("img/minus.png"))
        self.btn_maximize.setIcon(QIcon("img/maximize.png"))
        self.btn_close.setIcon(QIcon("img/close.png"))
        self.btn_mode.setIcon(QIcon("img/light.png"))
        # Taille uniforme des boutons
        for btn in [self.btn_notify, self.btn_minimize, self.btn_maximize, self.btn_close, self.btn_mode]:
            btn.setFixedSize(20, 20)
            btn.setIconSize(btn.size())

        # Connexions
        self.btn_close.clicked.connect(self.parent.close)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_minimize.clicked.connect(self.minimize_window)
        self.btn_notify.clicked.connect(self.show_notification)
        self.btn_mode.clicked.connect(self.parent.toggle_theme)

        # --- Layout ---
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.logo)

        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.btn_mode)
        layout.addWidget(self.btn_notify)
        layout.addWidget(self.btn_minimize)
        layout.addWidget(self.btn_maximize)
        layout.addWidget(self.btn_close)

    # =============================
    #   Fonctions des boutons
    # =============================
    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def minimize_window(self):
        self.parent.showMinimized()

    def show_notification(self):
        print("🔔 Notification cliquée !")

    # =============================
    #   Gestion du déplacement
    # =============================
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.parent.move(self.parent.pos() + event.globalPosition().toPoint() - self.drag_position)
            self.drag_position = event.globalPosition().toPoint()


class ModernWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setGeometry(200, 200, 500, 600)
        self.is_dark_theme = False
        self.current_content = None
        self.title_bar = CustomTitleBar(self)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.title_bar)
        self.container = QWidget()
        self.container.setObjectName("containerMain")
        self.container.setStyleSheet("""
            QWidget#containerMain { background-color: #e1e1e3; border-radius: 20px; }
            QLineEdit {
                background: #fff;
                color: black;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QPushButton#blueButton {
                background-color: #2301C0;
                color: white;
                border-radius: 8px;
            }
             QPushButton#blueButton : hover{
                background-color: #120A37;
            }
        """)

        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        self.layout.addWidget(self.container, 1)

        self.showPage("login")
        self.apply_light_theme()

    # =========================
    # CHANGEMENT DE PAGE
    # =========================
    def showPage(self, page):
        while self.container_layout.count():
            child = self.container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if page == "login":
            form = self.create_login_content()
            image = self.create_image_widget("img/sign.png", right=True)
            self.container_layout.addWidget(form)
            self.container_layout.addWidget(image)
        elif page == "signup":
            image = self.create_image_widget("img/sign.png", right=False)
            form = self.create_signup_content()
            self.container_layout.addWidget(image)
            self.container_layout.addWidget(form)
        elif page == "forgot":
            form = self.create_forget_content()
            image = self.create_image_widget("img/sign.png", right=True)
            self.container_layout.addWidget(form)
            self.container_layout.addWidget(image)

        elif page == "new_password":
            form = self.create_new_password_content()
            image = self.create_image_widget("img/sign.png", right=False)
            self.container_layout.addWidget(image)
            self.container_layout.addWidget(form)


        elif page == "main":
            self.open_main_page()
            return

    # =========================
    # IMAGE WIDGET
    # =========================
    def create_image_widget(self, path, right=True):
        label = QLabel()
        pixmap = QPixmap(path)

        pixmap = pixmap.scaled(
            500, 600,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            background-color: black;     
            border-radius: 20px;         
        """)

        return label



    # =========================
    # LOGIN
    # =========================
    def create_login_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setSpacing(15)


        title = QLabel("Welcome back")
        subtitle = QLabel("Sign in to your account.")
        title.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        subtitle.setFont(QFont("Segoe UI", 11))
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(15)

        self.user_login = QLineEdit()
        self.user_login.setPlaceholderText("Email address")
        # ===== Champ mot de passe avec icône œil =====

        self.password_login = QLineEdit()
        self.password_login.setPlaceholderText("Password")
        self.password_login.setEchoMode(QLineEdit.EchoMode.Password)


        layout.addWidget(self.user_login)
        layout.addWidget(self.password_login)


        forgot = QLabel("<a href='#' style='font-weight: bold;' >Forgot password?</a>")
        forgot.setTextFormat(Qt.TextFormat.RichText)
        forgot.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        forgot.linkActivated.connect(lambda _: self.showPage("forgot"))

        layout.addWidget(forgot, alignment=Qt.AlignmentFlag.AlignRight)

        signin_btn = QPushButton("Sign in")
        signin_btn.setObjectName("blueButton")
        signin_btn.clicked.connect(self.handle_login)

        layout.addWidget(signin_btn)
        layout.addSpacing(10)

        footer = QLabel("Don’t have an account? <a href='#' style='font-weight: bold;'>Sign up</a>")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setTextFormat(Qt.TextFormat.RichText)
        footer.linkActivated.connect(lambda _: self.showPage("signup"))
        layout.addWidget(footer)

        return widget

    def create_forget_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setSpacing(15)

        title = QLabel("Forgot Password?")
        subtitle = QLabel("Enter your email to reset your password")
        title.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        subtitle.setFont(QFont("Segoe UI", 11))
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(15)

        self.forgot_email = QLineEdit()
        self.forgot_email.setPlaceholderText("Email address")
        layout.addWidget(self.forgot_email)

        send_btn = QPushButton("Send Code")
        send_btn.setObjectName("blueButton")
        send_btn.clicked.connect(self.handle_forgot_password)
        layout.addWidget(send_btn)

        back = QLabel("<a href='#' style='font-weight: bold;'> Back to login</a>")
        back.setAlignment(Qt.AlignmentFlag.AlignCenter)
        back.setTextFormat(Qt.TextFormat.RichText)
        back.linkActivated.connect(lambda _: self.showPage("login"))
        layout.addWidget(back)

        return widget

    def change_password(self):
        pwd = self.new_password_login.text()
        confirm = self.new_password_confirm.text()

        if not pwd or not confirm:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir les deux champs.")
            return
        if pwd != confirm:
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return

        success, msg = reset_password(self.reset_email, pwd)
        if success:
            QMessageBox.information(self, "Succès", msg)
            self.showPage("login")
        else:
            QMessageBox.warning(self, "Erreur", msg)

    def create_new_password_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setSpacing(15)

        title = QLabel("Reset Password")
        subtitle = QLabel("Enter your new password")
        title.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        subtitle.setFont(QFont("Segoe UI", 11))
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(15)

        self.new_password_login = QLineEdit()
        self.new_password_login.setPlaceholderText("New password")
        self.new_password_login.setEchoMode(QLineEdit.EchoMode.Password)

        self.new_password_confirm = QLineEdit()
        self.new_password_confirm.setPlaceholderText("Confirm password")
        self.new_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addWidget(self.new_password_login)
        layout.addWidget(self.new_password_confirm)

        change_btn = QPushButton("Change Password")
        change_btn.setObjectName("blueButton")
        change_btn.clicked.connect(self.change_password)
        layout.addWidget(change_btn)

        return widget

    # =========================
    # SIGNUP
    # =========================
    def create_signup_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setSpacing(15)



        title = QLabel("Create an account")
        subtitle = QLabel("You can start classes as soon as you register.")
        title.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        subtitle.setFont(QFont("Segoe UI", 11))
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(25)

        self.user_signup = QLineEdit()
        self.user_signup.setPlaceholderText("Username")
        self.mail_signup = QLineEdit()
        self.mail_signup.setPlaceholderText("Email address")
        self.password_signup = QLineEdit()
        self.password_signup.setPlaceholderText("Password")
        self.password_signup.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm = QLineEdit()
        self.password_confirm.setPlaceholderText("Confirm password")
        self.password_confirm.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addWidget(self.user_signup)
        layout.addWidget(self.mail_signup)
        layout.addWidget(self.password_signup)
        layout.addWidget(self.password_confirm)

        signup_btn = QPushButton("Sign up")
        signup_btn.setObjectName("blueButton")
        signup_btn.clicked.connect(self.handle_signup)
        layout.addWidget(signup_btn)

        footer = QLabel("Already have an account? <a href='#'style='font-weight: bold;' >Sign in</a>")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setTextFormat(Qt.TextFormat.RichText)
        footer.linkActivated.connect(lambda _: self.showPage("login"))
        layout.addWidget(footer)

        return widget

    # =========================
    # GESTION SIGNUP
    # =========================
    def handle_signup(self):
        username = self.user_signup.text().strip()
        email = self.mail_signup.text().strip()
        pwd = self.password_signup.text()
        confirm = self.password_confirm.text()

        if not username or not email or not pwd or not confirm:

            QMessageBox.warning(self, "Erreur", "Tous les champs sont obligatoires.")
            return
        if pwd != confirm:
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return
        if not  verifier_email(email ) :
            QMessageBox.critical(self, "Erreur", "Un compte existe déjà avec cet e-mail.")
            return
        if not verifier_username(username) :
            QMessageBox.critical(self, "Erreur", "Ce nom d'utilisateur est déjà utilisé.")
            return


        code = generate_code()
        print(code)
        success = send_code_confirmation_email(email, username, code)
        if not success:
            QMessageBox.critical(self, "Erreur", "Impossible d’envoyer l’e-mail. Vérifie ta connexion.")
            return

        user_code, ok = QInputDialog.getText(self, "Confirmation", f"Un code a été envoyé à {email}. Entrez-le ici :")
        if ok:
            if user_code.strip() == code:

                password_hash = hash_password(pwd)
                saved = register_user(username, email, password_hash)

                if not saved:
                    QMessageBox.warning(self, "Erreur", "Un compte existe déjà avec cet e-mail.")
                    return

                # ✅ Envoi de mail de bienvenue (optionnel)
                send_confirmation_email(email, username)

                QMessageBox.information(self, "Succès", "✅ Compte créé avec succès !")
                self.showPage("login")

            else:
                QMessageBox.critical(self, "Erreur", "Code incorrect.")

    def handle_login(self):
        email = self.user_login.text().strip()
        password = self.password_login.text()

        if not email or not password:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs.")
            return

        success, message = verify_login(email, password)

        if success:
            QMessageBox.information(self, "Connexion réussie", message)
            self.showPage("main")
        else:
            QMessageBox.critical(self, "Erreur", message)

    def handle_forgot_password(self):
        email = self.forgot_email.text().strip()
        users = load_users()

        if not email:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer votre adresse e-mail.")
            return
        if email not in users:
            QMessageBox.warning(self, "Erreur", "Aucun compte trouvé avec cet e-mail.")
            return

        # Génération du code
        code = generate_code()
        sent = send_code_confirmation_email(email, users[email]["username"], code)
        if not sent:
            QMessageBox.critical(self, "Erreur", "Impossible d’envoyer le code. Vérifie ta connexion.")
            return

        # Demander le code à l’utilisateur
        user_code, ok = QInputDialog.getText(self, "Vérification", f"Un code a été envoyé à {email}. Entrez-le ici :")
        if not ok or user_code.strip() != code:
            QMessageBox.critical(self, "Erreur", "❌ Code incorrect.")
            return

        # Si code valide → afficher page de changement de mot de passe
        self.reset_email = email  # sauvegarde pour la suite
        self.showPage("new_password")

    """def open_main_page(self):
        self.main_page = MainPage(self.is_dark_theme)
        self.setCentralWidget(self.main_page)"""

    def open_main_page(self):
        """Affiche la page principale et cache le contenu de login."""
        if hasattr(self, "main_page"):
            self.main_page.deleteLater()

        # Cacher le conteneur login/signup
        self.container.setVisible(False)

        # Créer la fenêtre principale (AppWindow)
        self.main_page = AppWindow()
        self.layout.addWidget(self.main_page)

    # =========================
    # THEMES
    # =========================
    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        if self.is_dark_theme:
            self.apply_dark_theme()

        else:
            self.apply_light_theme()


    def apply_light_theme(self):
        self.setStyleSheet("""
        QMainWindow { background: white; }

        QLineEdit {
            border: 1px solid #ccc; border-radius: 6px;
            padding: 10px; font-size: 15px;
        }
        QLineEdit:focus { border: 1px solid #2301C0; }
        QPushButton#blueButton {
            background-color: #2301C0;
            color: white; border-radius: 8px;
            padding: 12px; font-size: 15px; font-weight: bold;
        }
        QPushButton#blueButton:hover {
            background-color: #120A37;
        }
        QLabel a { color: #2301C0; text-decoration: none; }
        QLabel a:hover { text-decoration: underline; }
        """)
        self.container.setStyleSheet("""
                    QWidget#containerMain { background-color: #e1e1e3; border-radius: 20px; }
                    QMainWindow { background: white; }

        QLineEdit {
            border: 1px solid #ccc; border-radius: 6px;
            padding: 10px; font-size: 15px;
        }
        QLineEdit:focus { border: 1px solid #2301C0; }
        QPushButton#blueButton {
            background-color: #2301C0;
            color: white; border-radius: 8px;
            padding: 12px; font-size: 15px; font-weight: bold;
        }
        QPushButton#blueButton:hover {
            background-color: #120A37;
        }
        QLabel a { color: #2301C0; text-decoration: none; }
        QLabel a:hover { text-decoration: underline; }
                """)
        pixmap = QPixmap("img/iconFortiFile.png").scaled(
            38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.title_bar.logo.setPixmap(pixmap)
        self.title_bar.title.setStyleSheet("color: black;")
        self.title_bar.btn_notify.setIcon(QIcon("img/bell.png"))
        self.title_bar.btn_minimize.setIcon(QIcon("img/minus.png"))
        self.title_bar.btn_maximize.setIcon(QIcon("img/maximize.png"))
        self.title_bar.btn_close.setIcon(QIcon("img/close.png"))
        self.title_bar.btn_mode.setIcon(QIcon("img/light.png"))
    def apply_dark_theme(self):
        self.setStyleSheet("""
        QMainWindow { background: #1e1e1e; }
      
        QLabel { color: white; }
        QLineEdit {
            background: #2d2d2d; color: white;
            border: 1px solid #555; border-radius: 6px;
            padding: 8px;
        }
         QLineEdit:focus { border: 1px solid #2301C0; }
        QPushButton#blueButton {
            background-color: #2301C0;
            color: black; border-radius: 8px;
            padding: 12px; font-size: 15px;font-weight: bold;
        }
        QPushButton#blueButton:hover {
            background-color: #120A37;
        }
        """)
        self.container.setStyleSheet("""
                    QWidget#containerMain { background-color: #2c2c2e ; border-radius: 20px; }
                    QMainWindow { background: #1e1e1e; }
      
        QLabel { color: white; }
        QLineEdit {
            background: #2d2d2d; color: white;
            border: 1px solid #555; border-radius: 6px;
            padding: 8px;
        }
         QLineEdit:focus { border: 1px solid #2301C0; }
        QPushButton#blueButton {
            background-color: #100740;
            color: white; border-radius: 8px;
            font-weight: bold; font-size: 15px;
        }
        QPushButton#blueButton:hover {
            background-color: #120A37;
        }
                """)
        pixmap = QPixmap("img/iconFortiFileDark.png").scaled(
            38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.title_bar.logo.setPixmap(pixmap)
        self.title_bar.title.setStyleSheet("color: white;")
        self.title_bar.btn_notify.setIcon(QIcon("img/bellDark.png"))
        self.title_bar.btn_minimize.setIcon(QIcon("img/minusDark.png"))
        self.title_bar.btn_maximize.setIcon(QIcon("img/maximizeDark.png"))
        self.title_bar.btn_close.setIcon(QIcon("img/closeDark.png"))
        self.title_bar.btn_mode.setIcon(QIcon("img/dark.png"))

