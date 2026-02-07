from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QPixmap, QAction
from PyQt6.QtCore import Qt, QSize

from core.gestion_db import get_notifications, get_notifications_all
from ui.main_window import AppWindow
from core.email_sender import generate_code, send_code_confirmation_email, send_confirmation_email
from core.user_manager import hash_password, register_user, verify_login, reset_password, load_users, verifier_email, \
    verifier_username, load_current_user
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize, QPoint
import os

basee_dir = os.path.dirname(os.path.abspath(__file__))
icon_path_light = os.path.join(basee_dir, "../img/iconFortiFile.png")
icon_path_dark = os.path.join(basee_dir, "../img/iconFortiFileDark.png")
notifi_path_light = os.path.join(basee_dir, "../img/bell.png")
notifi_path_dark = os.path.join(basee_dir, "../img/bellDark.png")
back_path = os.path.join(basee_dir, "../img/back.png")
minus_path_light = os.path.join(basee_dir, "../img/minus.png")
minus_path_dark = os.path.join(basee_dir, "../img/minusDark.png")
maximize_path_light = os.path.join(basee_dir, "../img/maximize.png")
maximize_path_dark = os.path.join(basee_dir, "../img/maximizeDark.png")
close_path_light = os.path.join(basee_dir, "../img/close.png")
close_path_dark = os.path.join(basee_dir, "../img/closeDark.png")
light_path_light = os.path.join(basee_dir, "../img/light.png")
dark_path_dark = os.path.join(basee_dir, "../img/dark.png")
pathForti = os.path.join(basee_dir, "../img/sign.png")


# =========================
# FENÊTRE PRINCIPALE
# =========================

class ShowAll(QWidget):
    def __init__(self, is_dark_theme=False, parent=None):
        super().__init__(parent)

        self.list_notification = get_notifications_all(load_current_user())
        self.is_dark_theme = is_dark_theme
        self.setFixedSize(550, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setStyleSheet("""
            border: 1px solid #151B54;
            border-radius: 10px;
        """)

        # --- Layout principal ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header avec bouton back
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header.setStyleSheet("border: none;")
        self.back_btn = QPushButton("")
        icon_size = 40
        icon_pixmap = QPixmap(back_path).scaled(
            icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.back_btn.setIcon(QIcon(icon_pixmap))
        self.back_btn.setIconSize(QSize(icon_size, icon_size))
        self.back_btn.setObjectName("back_btn")
        self.back_btn.setToolTip("Back")
        self.back_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        border-radius: 8px;
                    }
                    QPushButton:hover {
                        background-color: #F1F5F9;
                    }
                    QPushButton:pressed {
                        background-color: #E2E8F0;
                    }
                """)
        self.back_btn.clicked.connect(self.close)
        header_layout.addWidget(self.back_btn)
        header_layout.addStretch(True)
        layout.addWidget(header)

        # --- Scroll Area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
         QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                height: 0;
            }
        """)

        # Container pour les labels
        container = QWidget()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(10)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for notif in self.list_notification:
            notif_text = f"{notif[0]}: {notif[1]} [{notif[2]}] - {notif[3]}"
            label = QLabel(notif_text)
            label.setWordWrap(True)
            label.setStyleSheet("""

QLabel {
    background-color: #EEF1FF;

    border-radius: 6px;
    padding: 8px 10px;
    color: black;
    font-size: 13px;
    font-weight: normal; /* texte normal par défaut */
    transition: all 0.2s ease; /* transition douce */
}


QLabel:hover {
    background-color: #D0E0FF;       /* couleur de fond au survol */

    color: #0D1B2A;                  /* couleur du texte au survol */
    font-weight: bold;                /* texte en gras au survol */
}


            """)
            scroll_layout.addWidget(label)

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def showEvent(self, event):
        """Centrer la fenêtre une fois qu'elle est visible."""
        super().showEvent(event)
        self.center_window()

    def center_window(self):
        """Centre la fenêtre par rapport à la fenêtre parente (Home/MainWindow)."""
        if self.parent():
            parent_geometry = self.parent().frameGeometry()
            parent_center = parent_geometry.center()
            x = parent_center.x() - self.width() // 2
            y = parent_center.y() - self.height() // 2
            self.move(x, y)
        else:
            screen = self.screen().availableGeometry()
            x = screen.center().x() - self.width() // 2
            y = screen.center().y() - self.height() // 2
            self.move(x, y)


class NotificationPanel(QWidget):
    def __init__(self, parent=None, notifications=None):
        super().__init__(parent)

        self.notifications = notifications or []

        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.NoDropShadowWindowHint)
        self.setFixedWidth(320)
        self.setObjectName("NotificationPanel")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.create_header(main_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.notifications_content = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_content)
        self.notifications_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.notifications_layout.setContentsMargins(0, 0, 0, 0)
        self.notifications_layout.setSpacing(0)

        # Ajouter toutes les notifications
        for notif in self.notifications:
            title, message, status, sent_at = notif[:4]
            self.add_notification_item(title, message, status, sent_at)

        scroll_area.setWidget(self.notifications_content)
        main_layout.addWidget(scroll_area)

        see_all_button = QPushButton("See all notifications ")
        see_all_button.setObjectName("SeeAllButton")
        see_all_button.setMinimumHeight(40)
        see_all_button.clicked.connect(self.showNotif)
        main_layout.addWidget(see_all_button)

    def showNotif(self):
        self.msg_window = ShowAll(is_dark_theme=False)
        self.msg_window.show()

    def create_header(self, parent_layout):
        header = QWidget()
        header.setObjectName("NotificationHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)

        header_layout.addWidget(QLabel("Notifications"))
        header_layout.addStretch(1)

        parent_layout.addWidget(header)

    def add_notification_item(self, title, message, status=None, sent_at=""):
        item = QWidget()
        item.setObjectName("NotificationItem")
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(10, 5, 10, 5)

        # Texte
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        name_label = QLabel(f'<b>{title}</b> <span style="font-weight: normal; font-size: 10pt;">{message}</span>')
        name_label.setStyleSheet("font-size: 11pt;")
        time_label = QLabel(f'<span style="font-size: 8pt; color: #888;">{sent_at}</span>')

        text_layout.addWidget(name_label)
        text_layout.addWidget(time_label)
        item_layout.addWidget(text_widget)
        item_layout.addStretch(1)

        self.notifications_layout.addWidget(item)

    def apply_theme_style(self, is_dark):
        """Met à jour le style du panneau pour correspondre au thème de la fenêtre."""
        if is_dark:
            self.setStyleSheet("""
                #NotificationPanel {
                    background-color: #2c2c2e;
                    border: 1px solid #555;
                    border-radius: 8px;
                }
                #NotificationHeader {
                    background-color: #38383a;
                    border-bottom: 1px solid #555;
                    color: white;
                }
                #NotificationItem {
                    border-bottom: 1px solid #38383a;
                    color: white;
                }
                #NotificationItem:hover {
                    background-color: #333;
                }
                #SeeAllButton {
                    background-color: #100740;
                    color: white;
                    border-radius: 6px;
                    padding: 12px;
                    font-weight: bold;
                    margin: 10px;
                }
                #SeeAllButton:hover {
                    background-color: #120A37;
                }
            """)
        else:
            self.setStyleSheet("""
                /* ---- PANEL PRINCIPAL ---- */
                #NotificationPanel {
                    background-color: #FFFFFF;
                    border-radius: 12px;
                    border: 1px solid #E5E5E5;
                    padding: 0px;
                    box-shadow: 0px 4px 14px rgba(0, 0, 0, 0.08);
                }

                /* ---- HEADER ---- */
                #NotificationHeader {
                    background-color: #FAFAFA;
                    border-bottom: 1px solid #EBEBEB;
                    padding: 12px 16px;
                    font-size: 15px;
                    font-weight: 600;
                    color: #1D1D1D;
                }

                /* ---- ÉLÉMENT DE NOTIFICATION ---- */
                #NotificationItem {
                    padding: 12px 16px;
                    border-bottom: 1px solid #F2F2F2;
                    color: #333333;
                    font-size: 14px;
                    background-color: transparent;
                    transition: background-color 120ms ease, padding-left 120ms ease;
                }

                #NotificationItem:hover {
                    background-color: #F7F9FC;
                    padding-left: 20px; /* Hover moderne */
                }

                /* ---- BUTTON "SEE ALL" ---- */
                #SeeAllButton {
                    background-color: #4A3AFF;
                    color: white;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 14px;
                    font-weight: 600;
                    margin: 12px;
                    border: none;
                    transition: background-color 150ms ease, transform 120ms ease;
                }

                #SeeAllButton:hover {
                    background-color: #2E22CC;
                    transform: translateY(-1px);
                }

                #SeeAllButton:pressed {
                    background-color: #241A9F;
                    transform: translateY(0px);
                }
            """)


class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(30)
        self.drag_position = QPoint()
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
        pixmap = QPixmap(icon_path_light).scaled(
            38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.logo.setPixmap(pixmap)

        self.title = QLabel("FortiFile")
        self.title.setFont(QFont("Segoe UI Light", 16, QFont.Weight.Bold))
        self.title.setStyleSheet("color: Black;")

        # --- Boutons à droite (avec icônes) ---
        self.btn_notify = QPushButton()
        self.btn_notify.setEnabled(False)
        self.btn_minimize = QPushButton()
        self.btn_maximize = QPushButton()
        self.btn_close = QPushButton()
        self.btn_mode = QPushButton()
        # 🔔 Remplace ces chemins par tes propres icônes
        self.btn_notify.setIcon(QIcon(notifi_path_light))

        self.btn_minimize.setIcon(QIcon(minus_path_light))
        self.btn_maximize.setIcon(QIcon(maximize_path_light))
        self.btn_close.setIcon(QIcon(close_path_light))
        self.btn_mode.setIcon(QIcon(light_path_light))
        # Taille uniforme des boutons
        for btn in [self.btn_notify, self.btn_minimize, self.btn_maximize, self.btn_close, self.btn_mode]:
            btn.setFixedSize(20, 20)
            btn.setIconSize(btn.size())

        # Connexions
        self.btn_close.clicked.connect(self.parent.close)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_minimize.clicked.connect(self.minimize_window)
        self.btn_notify.clicked.connect(self.parent.toggle_notification_panel)
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

    # =============================
    #   Gestion du déplacement
    # =============================

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint()
        super().mousePressEvent(event)

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

        self.list_notification = get_notifications(5, load_current_user())
        self.notification_panel = NotificationPanel(self, notifications=self.list_notification)
        self.notification_panel.hide()
        self.is_notification_panel_visible = False
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
        if self.is_notification_panel_visible:
            self.notification_panel.hide()
            self.is_notification_panel_visible = False

        while self.container_layout.count():
            child = self.container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if page == "login":
            form = self.create_login_content()
            image = self.create_image_widget(pathForti, right=True)
            self.container_layout.addWidget(form)
            self.container_layout.addWidget(image)
        elif page == "signup":
            image = self.create_image_widget(pathForti, right=False)
            form = self.create_signup_content()
            self.container_layout.addWidget(image)
            self.container_layout.addWidget(form)
        elif page == "forgot":
            form = self.create_forget_content()
            image = self.create_image_widget(pathForti, right=True)
            self.container_layout.addWidget(form)
            self.container_layout.addWidget(image)

        elif page == "new_password":
            form = self.create_new_password_content()
            image = self.create_image_widget(pathForti, right=False)
            self.container_layout.addWidget(image)
            self.container_layout.addWidget(form)


        elif page == "main":
            self.title_bar.btn_notify.setEnabled(True)
            self.open_main_page()
            return

    def toggle_notification_panel(self):
        """Affiche ou cache le panneau de notifications et met à jour le contenu."""

        if self.is_notification_panel_visible:
            # Cache le panneau
            self.notification_panel.hide()
            self.is_notification_panel_visible = False


        else:
            # --- 1. Récupérer les notifications à jour ---
            self.list_notification = get_notifications(5, load_current_user())

            # --- 3. Recréer le panneau avec les notifications actuelles ---
            self.notification_panel = NotificationPanel(self, notifications=self.list_notification)

            # --- 4. Positionner et afficher le panneau ---
            btn_pos = self.title_bar.btn_notify.mapToGlobal(self.title_bar.btn_notify.rect().topRight())
            x = btn_pos.x() - self.notification_panel.width()
            y = self.title_bar.height() + 5
            global_y = self.mapToGlobal(self.rect().topLeft()).y() + y
            self.notification_panel.move(x, global_y)
            self.notification_panel.show()
            self.notification_panel.activateWindow()
            self.is_notification_panel_visible = True

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
        self.user_login.returnPressed.connect(lambda: self.password_login.setFocus())
        # ===== Champ mot de passe avec icône œil =====

        self.password_login = QLineEdit()
        self.password_login.setPlaceholderText("Password")
        self.password_login.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_login.returnPressed.connect(self.handle_login)
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
        self.user_signup.returnPressed.connect(lambda: self.mail_signup.setFocus())
        self.mail_signup = QLineEdit()
        self.mail_signup.setPlaceholderText("Email address")
        self.mail_signup.returnPressed.connect(lambda: self.password_signup.setFocus())
        self.password_signup = QLineEdit()
        self.password_signup.setPlaceholderText("Password")
        self.password_signup.returnPressed.connect(lambda: self.password_confirm.setFocus())
        self.password_signup.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm = QLineEdit()
        self.password_confirm.setPlaceholderText("Confirm password")
        self.password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm.returnPressed.connect(self.handle_signup)
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
    # MESSAGE BOX MODERNE
    # =========================
    def show_message(self, title, text, icon="info"):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(text)

        # Icônes : info / warning / error / success
        if icon == "info":
            box.setIcon(QMessageBox.Icon.Information)
        elif icon == "warning":
            box.setIcon(QMessageBox.Icon.Warning)
        elif icon == "error":
            box.setIcon(QMessageBox.Icon.Critical)
        elif icon == "success":
            box.setIcon(QMessageBox.Icon.Information)
            title = "Succès"

        # Style unifié (clair/sombre)
        if self.is_dark_theme:
            box.setStyleSheet("""
                QMessageBox {
                    background-color: #2c2c2e;
                    color: white;
                    border: 2px solid #2301C0;
                    border-radius: 10px;
                }
                QPushButton {
                    background-color: #2301C0;
                    color: white;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #120A37;
                }
            """)
        else:
            box.setStyleSheet("""
                QMessageBox {
                    background-color: #f9f9f9;
                    color: black;
                    border: 2px solid #2301C0;
                    border-radius: 10px;
                }
                QPushButton {
                    background-color: #2301C0;
                    color: white;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #120A37;
                }
            """)

        box.exec()

    # =========================
    # GESTION SIGNUP
    # =========================
    def handle_signup(self):
        username = self.user_signup.text().strip()
        email = self.mail_signup.text().strip()
        pwd = self.password_signup.text()
        confirm = self.password_confirm.text()

        if not username or not email or not pwd or not confirm:
            self.show_message("Erreur", "Tous les champs sont obligatoires.", "warning")
            return
        if pwd != confirm:
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return
        if not verifier_email(email):
            QMessageBox.critical(self, "Erreur", "Un compte existe déjà avec cet e-mail.")
            return
        if not verifier_username(username):
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
        pixmap = QPixmap(icon_path_light).scaled(
            38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.title_bar.logo.setPixmap(pixmap)
        self.title_bar.title.setStyleSheet("color: black;")

        self.title_bar.btn_notify.setIcon(QIcon(notifi_path_light))

        self.title_bar.btn_minimize.setIcon(QIcon(minus_path_light))
        self.title_bar.btn_maximize.setIcon(QIcon(maximize_path_light))
        self.title_bar.btn_close.setIcon(QIcon(close_path_light))
        self.title_bar.btn_mode.setIcon(QIcon(light_path_light))

        self.notification_panel.apply_theme_style(False)

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
          QFrame#title_card {
                background-color: noir;
                border-radius: 20px;
                border: 1px solid #ddd;
                padding: 20px;
            }
            QFrame#title_card:hover {
                background-color: #e8f0fe;
                border: 1px solid #a0c4ff;
            }


                """)
        pixmap = QPixmap(icon_path_dark).scaled(
            38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.title_bar.logo.setPixmap(pixmap)
        self.title_bar.title.setStyleSheet("color: white;")
        self.title_bar.btn_notify.setIcon(QIcon(notifi_path_dark))
        self.title_bar.btn_minimize.setIcon(QIcon(minus_path_dark))
        self.title_bar.btn_maximize.setIcon(QIcon(maximize_path_dark))
        self.title_bar.btn_close.setIcon(QIcon(close_path_dark))
        self.title_bar.btn_mode.setIcon(QIcon(dark_path_dark))

        self.notification_panel.apply_theme_style(True)