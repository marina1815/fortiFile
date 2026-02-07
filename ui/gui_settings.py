import sys, os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QLineEdit, QComboBox, QCheckBox,
    QGridLayout, QScrollArea, QDateEdit, QInputDialog, QMessageBox,
    QSplitter, QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem,
    QHeaderView, QAbstractItemView, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, pyqtProperty
from PyQt6.QtCore import QDate, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QPixmap, QColor, QPainter
from PyQt6.QtWidgets import QLabel, QFrame, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

from core.config_manager import get_mode, update_mode
from core.gestion_db import get_files_by_user, get_baseline_owner, set_baseline_owner

from core.user_manager import (
    load_current_user, get_email_by_username, get_hashed_password_by_username,
    get_date_of_birth_by_username, edit_user, hash_password, list_users
)

from core.user_manager import load_historique
base_dir = os.path.dirname(os.path.abspath(__file__))
auto_path = os.path.join(base_dir, "../img/encrypted.png")

# --- Constantes pour l'animation ---
SIDEBAR_WIDTH_MIN = 0
SIDEBAR_WIDTH_MAX = 220
ANIMATION_DURATION = 300

# --- Structure de Données ---
BUTTONS_DATA = [
    ("General"),
    ("Security"),
    ("Roles"),
]
basee_dir = os.path.dirname(os.path.abspath(__file__))
settings_path = os.path.join(basee_dir, "../img/parametre.png")
ICON_PATHS = {
    "General": os.path.join(basee_dir,"../img/global.png"),
    "Security": os.path.join(basee_dir,"../img/cadenas.png"),
    "Roles": os.path.join(basee_dir,"../img/roles.png"),
}


LIGHT_STYLESHEET = """
    /* 🌞 --- Thème Clair Global --- */



    /* ---------------- Header ---------------- */
    #Header {
        background-color:  #151B54;
        padding: 10px;
        border-bottom: 1px solid #D0D0D0;
    }
    #header_label {
       font-size: 30px; font-weight: bold; color:  #151B54;
    }

    QDateEdit {
        border: 1px solid #ccc;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 15px;
        background-color: #fff;
        color: #1E1E1E;
        selection-background-color: #151B54;
        selection-color: white;
    }
    QDateEdit:focus {
        border: 1px solid  #151B54;
    }
    QDateEdit::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid #ccc;
    }

    #subtitle {
     font-size: 15pt; 
     font-weight: bold;
     color: black;
     margin-top: 15px;
    }

    /* ---------------- Footer ---------------- */
    #Footer {
        background-color: white;
        padding: 8px;

    }

    #SettingsButton {
        background-color: transparent;
        border: none;
        color: #1E1E1E;
        font-size: 18pt;
        padding: 5px 10px;
    }
    #SettingsButton:hover {
        color:  #151B54;
    }

    /* ---------------- Sidebar ---------------- */
    #Sidebar {
        background-color: #F0F0F0;
        border-right: 1px solid #D0D0D0;
    }

    #Sidebar QPushButton {
        background-color: transparent;
        border: none;
        color: #1E1E1E;
        text-align: left;
        padding: 14px 12px;
        font-size: 11pt;
    }

    #Sidebar QPushButton:hover {
        background-color: #E0E0E0;
        border-left: 5px solid  #151B54;
    }

    #Sidebar QPushButton:checked {
        background-color: #E0E0E0;
        font-weight: bold;
        border-left: 5px solid  #151B54;
    }
    #Sidebar QPushButton[text=""] {
        text-align: center; 
    }

    /* ---------------- Contenu Principal ---------------- */
    #ContentArea {
        padding: 20px;
    }

    /* ---------------- QLabel ---------------- */
    QLabel {
        color: #1E1E1E;
        font-size: 14pt;
    }

    QLabel[property="title"] {
        font-size: 15pt;
        font-weight: bold;
        color: #000;
        margin-bottom: 15px;
    }

    QLabel[property="subtitle"] {
        font-size: 16pt;
        color: #333;
        margin-top: 10px;
        margin-bottom: 5px;
    }


    /* ---------------- QLineEdit ---------------- */
    QLineEdit {
        border: 1px solid #CCC;
        border-radius: 6px;
        padding: 10px;
        font-size: 15px;
        background-color: white;
        color: #1E1E1E;
    }
    QLineEdit:focus {
        border: 1px solid  #151B54;
        background-color: #FDFDFE;
    }

    /* ---------------- QPushButton (principal) ---------------- */
    QPushButton#saveButton {
        background-color:  #151B54;
        color: white;
        border-radius: 8px;
        padding: 12px;
        font-size: 15px;
        font-weight: bold;
    }
    QPushButton#saveButton:hover {
        background-color: #120A37;
    }

    /* ---------------- QPushButton (secondaire) ---------------- */
    QPushButton#grayButton {
        background-color: #E0E0E0;
        color: #1E1E1E;
        border-radius: 8px;
        padding: 10px;
        font-size: 14px;
    }
    QPushButton#grayButton:hover {
        background-color: #D0D0D0;
    }
     QLabel {
        font-size: 12pt;
        color: #1E1E1E;
    }
    QLabel[property="property"] {
        font-weight: bold;
    }

    QGridLayout {
        spacing: 10px;
    }
    QWidget {
        background-color: #FAFAFA;
        border-radius: 6px;
        padding: 10px;
    }
    QTableWidget[role="Admin"] {
        color: red ;
        font-weight: bold;
    }

"""

class ModernSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._slider_position = 2
        self._animation = QPropertyAnimation(self, b"slider_position")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.toggled.connect(self.animate_slider)

    @pyqtProperty(int)
    def slider_position(self):
        return self._slider_position

    @slider_position.setter
    def slider_position(self, pos):
        self._slider_position = pos
        self.update()

    def animate_slider(self):
        if self.isChecked():
            self._animation.setStartValue(2)
            self._animation.setEndValue(30)
        else:
            self._animation.setStartValue(30)
            self._animation.setEndValue(2)
        self._animation.start()

    def mousePressEvent(self, event):
        self.setChecked(not self.isChecked())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fond
        if self.isChecked():
            painter.setBrush(QColor("#10B981"))
        else:
            painter.setBrush(QColor("#777777"))

        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)

        # Slider avec position animée
        painter.setBrush(QColor("white"))
        painter.drawEllipse(self._slider_position, 2, 26, 26)


class SettingsPage(QWidget):
    def __init__(self, username="User"):

        super().__init__()
        self.username = load_current_user()

        self.setStyleSheet(LIGHT_STYLESHEET)

        app_layout = QVBoxLayout(self)
        app_layout.setContentsMargins(0, 0, 0, 0)
        app_layout.setSpacing(0)

        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        app_layout.addLayout(body_layout)

        self.create_sidebar(body_layout)

        self.create_content_area(body_layout)

        self.create_footer(app_layout)

        self.setup_animation()
        self.setup_connections()

        # Initialisation: la barre latérale commence fermée sur la page d'accueil (index 0)
        self.stacked_widget.setCurrentIndex(1)
        self.buttons[0].setChecked(True)  # Mettre le bouton en surbrillance
        self.is_sidebar_open = True  # La sidebar est considérée ouverte
        self.sidebar_widget.setMinimumWidth(SIDEBAR_WIDTH_MAX)  # Sidebar visible dès le départ
        self.update_button_text()

    def create_footer(self, parent_layout):
        footer_widget = QWidget()
        footer_widget.setObjectName("Footer")
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 0, 0, 0)

        self.settings_button = QPushButton("⚙️")
        self.settings_button = QPushButton("")
        icon_size = 40
        icon_pixmap = QPixmap(settings_path).scaled(
            icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.settings_button.setIcon(QIcon(icon_pixmap))
        self.settings_button.setIconSize(QSize(icon_size, icon_size))
        self.settings_button.setStyleSheet("""
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
        self.settings_button.setObjectName("SettingsButton")
        self.settings_button.setToolTip("Open Settings")
        self.settings_button.setFixedSize(QSize(40, 40))

        footer_layout.addWidget(self.settings_button)
        footer_layout.addStretch(1)

        parent_layout.addWidget(footer_widget)

    def create_sidebar(self, parent_layout):
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("Sidebar")
        self.sidebar_widget.setMinimumWidth(SIDEBAR_WIDTH_MAX)

        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)
        self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.buttons = []
        for text in BUTTONS_DATA:
            btn = QPushButton(text)
            btn.setToolTip(text)
            btn.setCheckable(True)
            btn.setMinimumHeight(45)

            icon_path = ICON_PATHS.get(text, "")
            if icon_path and os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(24, 24))  # taille de l'icône



            btn.full_text = text
            self.buttons.append(btn)
            self.sidebar_layout.addWidget(btn)

        self.sidebar_layout.addStretch(1)
        parent_layout.addWidget(self.sidebar_widget)

    def create_content_area(self, parent_layout):
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("ContentArea")

        # Index 0: Page d'accueil (pour l'état initial "fermé")
        self.stacked_widget.addWidget(self._create_welcome_page())

        # Index 1: Personal Info (premier bouton de la sidebar)
        self.stacked_widget.addWidget(self._create_personal_info_page())

        # Index 2: Security
        self.stacked_widget.addWidget(self._create_security_page())

        # Index 3: Roles
        self.stacked_widget.addWidget(self._create_roles_page())

        parent_layout.addWidget(self.stacked_widget)

    # --- Pages de Contenu ---

    def _create_roles_page(self):
        page = QScrollArea()
        page.setStyleSheet("""
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
        page.setWidgetResizable(True)
        container = QWidget()
        main_layout = QVBoxLayout(container)

        # --- Titre ---
        header_label = QLabel("Roles Management")
        header_label.setStyleSheet("font-size: 30px; font-weight: bold; color:  #151B54;")
        main_layout.addWidget(header_label)

        # --- Sous-titre ---
        subtitle = QLabel(
            "Overview of all application users and their assigned roles ."
        )
        subtitle.setStyleSheet("font-size: 15pt; color: #333; margin-bottom: 10px;")
        main_layout.addWidget(subtitle)
        bar = QWidget()
        main_layout.addWidget(bar)
        top_bar = QHBoxLayout(bar)
        top_bar.setSpacing(10)

        self.combo = QComboBox()
        # Supposons que self.combo est ton QComboBox
        self.combo.setStyleSheet("""
            QComboBox {
                border: 2px solid  #151B54;   /* Bordure principale */
                border-radius: 6px;          /* Coins arrondis */
                padding: 5px 10px;
                font-size: 12pt;
                min-width: 150px;
                background-color: white;
                color: #1E1E1E;
            }

            QComboBox::drop-down {
                border-left: 1px solid  #151B54; /* Ligne séparatrice du bouton */
                width: 25px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                background-color: #E6E6E6;
            }

            QComboBox::down-arrow {
                image: url(path_to_arrow_icon.png); /* optionnel : flèche personnalisée */
                width: 12px;
                height: 12px;
            }

            QComboBox QAbstractItemView {
                border: 2px solid #151B54;  /* Bordure du menu déroulant */
                border-radius: 6px;
                background-color: white;
                selection-background-color:  #151B54;
                selection-color: white;
            }
        """)

        files = get_files_by_user(load_current_user())  # Liste de dicts
        file_names = [f['path'] for f in files]  # Extraire les chemins

        self.combo.addItems(file_names)  # Ajouter à la combo
        if file_names:
            self.combo.setCurrentIndex(0)
        self.combo.setEditable(False)  # permet de taper du texte aussi
        top_bar.addWidget(self.combo)
        self.btn = QPushButton("Show roles")
        self.btn.setToolTip("Permissions of users for selected file will appear here")
        self.btn.setObjectName("saveButton")
        self.btn.clicked.connect(self.add_file)
        top_bar.addWidget(self.combo, stretch=1)
        top_bar.addWidget(self.btn, stretch=0)
        self.defaultLabel = QLabel("Default List : ")
        main_layout.addWidget(self.defaultLabel)
        # --- Splitter horizontal ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Username", "Email", "Role"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # --- Style simple avec coins arrondis ---
        self.table.setStyleSheet("""
       QTableWidget { background-color: white; border-radius: 8px; border: 1px solid #ddd;  font-size: 12pt; }


        """)


        # Remplir le tableau (list_users doit retourner une liste de dicts)
        # Remplir le tableau (list_users doit retourner une liste de dicts)
        users = list_users() or []
        for user in users:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            username_item = QTableWidgetItem(user.get("username", ""))
            email_item = QTableWidgetItem(user.get("email", ""))
            role_item = QTableWidgetItem(user.get("role", ""))

            if username_item.text() in ["Username"]:  # si c’est un mot clé
                username_item.setForeground(QColor("blue"))
                username_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            if role_item.text() in ["Role"]:  # mot clé pour role
                role_item.setForeground(QColor("blue"))  # <-- ici on doit modifier role_item
                role_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

            if email_item.text() in ["Email"]:  # mot clé pour email
                email_item.setForeground(QColor("blue"))  # <-- ici on doit modifier email_item
                email_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

            if role_item.text() in ["Admin"]:  # mots clés pour la colonne role
                role_item.setForeground(QColor("red"))
            if role_item.text() in ["Guest"]:  # mots clés pour la colonne role
                role_item.setForeground(QColor("green"))
                role_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

            self.table.setItem(row_position, 0, username_item)
            self.table.setItem(row_position, 1, email_item)
            self.table.setItem(row_position, 2, role_item)

        splitter.addWidget(self.table)
        main_layout.addStretch()

        splitter.setSizes([800, 200])  # Largeur initiale des panneaux
        btn_change = QPushButton("Change role")
        btn_change.clicked.connect(self.changeRole)
        btn_change.setToolTip("Change the role of user ")
        btn_change.setObjectName("saveButton")
        main_layout.addWidget(btn_change, alignment=Qt.AlignmentFlag.AlignRight)
        page.setWidget(container)
        return page

    def refresh_table(self, admin_list):
        # Vider toutes les lignes existantes
        self.table.setRowCount(0)

        # Récupérer la nouvelle liste d'utilisateurs
        print(admin_list)
        users = list_users()
        # Mise à jour du rôle
        admin_assigned = admin_list[0]
        print(admin_assigned)

        for user in users:
            if user['username'] in admin_list:
                if user['username'] == admin_assigned:
                    print(user['username'])
                    user['role'] = 'Admin'  # Premier de la liste admin = Admin

                else:
                    user['role'] = 'Guest'

        for user in users:
            row = self.table.rowCount()
            self.table.insertRow(row)

            username_item = QTableWidgetItem(user.get("username", ""))
            email_item = QTableWidgetItem(user.get("email", ""))
            role_item = QTableWidgetItem(user.get("role", ""))

            if username_item.text() in ["Username"]:  # si c’est un mot clé
                username_item.setForeground(QColor("blue"))
                username_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            if role_item.text() in ["Role"]:  # mot clé pour role
                role_item.setForeground(QColor("blue"))  # <-- ici on doit modifier role_item
                role_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

            if email_item.text() in ["Email"]:  # mot clé pour email
                email_item.setForeground(QColor("blue"))  # <-- ici on doit modifier email_item
                email_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

            # --- COLORATION ---

            # Admin rouge
            if role_item.text() == "Admin":
                role_item.setForeground(QColor("red"))
                role_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

            # Guest vert
            elif role_item.text() == "Guest":
                role_item.setForeground(QColor("green"))
                role_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))


            self.table.setItem(row, 0, username_item)
            self.table.setItem(row, 1, email_item)
            self.table.setItem(row, 2, role_item)

    def changeRole(self):
        selected_row = self.table.currentRow()
        if selected_row != -1:  # Vérifier qu'une ligne est sélectionnée
            username = self.table.item(selected_row, 0).text()
            role_item = self.table.item(selected_row, 2)
            current_role = role_item.text()
            new_role = "Guest" if current_role != "Guest" else "UserStandard"
            role_item.setText(new_role)
            if new_role == "Guest":
                path = self.combo.currentText()
                user = get_baseline_owner(path)
                user += "," + username
                set_baseline_owner(path, user)
            else:
                path = self.combo.currentText()
                user = get_baseline_owner(path)
                users = user.split(",")  # transforme en liste
                users = [u for u in users if u != username]  # filtre le username
                users = ",".join(users)
                set_baseline_owner(path, users)

    def add_file(self):

        selected_file = self.combo.currentText()
        self.defaultLabel.setText("List of users : ")
        if selected_file:
            admin = get_baseline_owner(selected_file)

            admin_list = admin.split(",")
            print(admin_list)
            self.refresh_table(admin_list)

    def after_file_selected(self):
        # Récupère le fichier sélectionné
        selected = getattr(self.file_window, "selected_file", None)
        if selected:
            self.path_edit.setText(selected)

    def _create_welcome_page(self):
        page = QWidget()
        page.setLayout(QVBoxLayout())
        header_label = QLabel("Welcome to Settings")
        header_label.setProperty("property", "title")
        page.layout().addWidget(header_label)
        page.layout().addWidget(QLabel("Click the ⚙️ icon to open the **Settings** sidebar and navigate."))
        page.layout().addStretch(1)
        return page

    def _create_generic_page(self, title, content_text):
        page = QWidget()
        layout = QVBoxLayout(page)
        header_label = QLabel(title)
        header_label.setProperty("property", "title")
        layout.addWidget(header_label)
        layout.addWidget(QLabel(content_text))
        layout.addStretch(1)
        return page

    def _create_personal_info_page(self):
        page = QScrollArea()
        page.setStyleSheet("""
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
        page.setWidgetResizable(True)
        container = QWidget()
        self.layout_personal_info = QVBoxLayout(container)

        header_label = QLabel("Personal Information")
        header_label.setProperty("property", "title")
        header_label.setObjectName("header_label")
        self.layout_personal_info.addWidget(header_label)

        subtitle1 = QLabel("User Identification")
        subtitle1.setObjectName("subtitle")
        subtitle1.setProperty("property", "subtitle")
        self.layout_personal_info.addWidget(subtitle1)

        self.grid_personal_info = QGridLayout()

        self.grid_personal_info.addWidget(QLabel("Username:"), 0, 0)
        self.usernameEdit = QLineEdit(f"{self.username}")
        self.usernameEdit.setReadOnly(True)
        self.grid_personal_info.addWidget(self.usernameEdit, 0, 1)

        self.grid_personal_info.addWidget(QLabel("Email Address:"), 1, 0)
        self.emaiEdit = QLineEdit(get_email_by_username(self.username))
        self.emaiEdit.setReadOnly(True)
        self.grid_personal_info.addWidget(self.emaiEdit, 1, 1)

        self.grid_personal_info.addWidget(QLabel("Date of Birth:"), 2, 0)
        self.dobEdit = QDateEdit()
        self.dobEdit.setCalendarPopup(True)
        self.dobEdit.setDisplayFormat("yyyy-MM-dd")
        self.dobEdit.setReadOnly(True)

        dob_str = get_date_of_birth_by_username(self.username)

        if dob_str and dob_str != "":
            try:
                year, month, day = map(int, dob_str.split("-"))
                self.dobEdit.setDate(QDate(year, month, day))
            except ValueError:
                self.dobEdit.setDate(QDate(2000, 1, 1))
        else:
            self.dobEdit.setDate(QDate(2000, 1, 1))

        self.grid_personal_info.addWidget(self.dobEdit, 2, 1)

        self.edit_btn = QPushButton("Edit Profil")
        self.edit_btn.setToolTip("Edit Profil")
        self.edit_btn.setObjectName("saveButton")
        self.edit_btn.clicked.connect(self.edit_func)

        self.layout_personal_info.addLayout(self.grid_personal_info)

        self.button_container = QHBoxLayout()
        self.button_container.addStretch(1)
        self.button_container.addWidget(self.edit_btn)
        self.layout_personal_info.addLayout(self.button_container)
        subtitle2 = QLabel("Boot mode")
        subtitle2.setObjectName("header_label")
        self.layout_personal_info.addWidget(subtitle2)
        Autoscan_frame = QFrame()
        Autoscan_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #dddddd;
            }
        """)
        Autoscan_frame.setMinimumHeight(120)

        Autoscan_layout = QHBoxLayout(Autoscan_frame)
        Autoscan_layout.setContentsMargins(30, 20, 30, 20)
        Autoscan_layout.setSpacing(20)

        # ICON


        # TEXT BLOCK
        Autoscan_widget = QWidget()
        vbox = QVBoxLayout(Autoscan_widget)
        vbox.setAlignment(Qt.AlignmentFlag.AlignLeft)
        vbox.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Auto scan ")
        title.setFont(QFont("sans-serif", 18, QFont.Weight.Bold))
        title.setStyleSheet("border : none;")
        vbox.addWidget(title)
        # TOGGLE SWITCH
        self.auto_scan_switch = ModernSwitch()
        self.auto_scan_switch.toggled.connect(self.on_auto_scan_toggled)

        if get_mode() == "auto":
            self.auto_scan_switch.setChecked(True)

        # FINAL LAYOUT

        Autoscan_layout.addWidget(Autoscan_widget)
        Autoscan_layout.addStretch()
        Autoscan_layout.addWidget(self.auto_scan_switch)

        # ADD AUTOSCAN TO PAGE
        self.layout_personal_info.addWidget(Autoscan_frame)


        self.layout_personal_info.addStretch(1)
        page.setWidget(container)
        return page

    def on_auto_scan_toggled(self, checked):
        """Gère le changement d'état du switch Auto Scan"""
        if checked:
            print("Auto scan activé - Analyse au démarrage de Windows activée")
            update_mode("auto")

        else:
            print("Auto scan désactivé - Analyse au démarrage de Windows désactivée")
            update_mode("manuel")



    # --- Méthodes de Logique (edit_func, cancel_edit, etc.) ---

    def edit_func(self):

        if self.edit_btn.text().strip() == "Edit Profil":
            self.usernameEdit.setReadOnly(False)
            self.emaiEdit.setReadOnly(False)
            self.dobEdit.setReadOnly(False)

            self.edit_btn.setText("Save")
            self.cancel_btn = QPushButton("Cancel")
            self.cancel_btn.setToolTip("Cancel")
            self.cancel_btn.setObjectName("grayButton")
            self.cancel_btn.clicked.connect(self.cancel_edit)

            self.button_container.insertWidget(0, self.cancel_btn)

        elif self.edit_btn.text().strip() == "Save":

            password, ok = QInputDialog.getText(self, "Confirm Password",
                                                "Enter your current password: ")

            if password and ok:
                hashed_password_stored = get_hashed_password_by_username(self.username)

                if hashed_password_stored == hash_password(password):

                    new_username = self.usernameEdit.text().strip()
                    new_email = self.emaiEdit.text().strip()

                    dob = self.dobEdit.date()

                    edit_user(new_username, new_email, password, dob.toString("yyyy-MM-dd"))

                    self.username = new_username

                    QMessageBox.information(self, "Success", "Profile updated successfully!")

                    self.finish_edit_mode()
                else:

                    QMessageBox.warning(self, "Error", "Incorrect password! Changes not saved.")
            else:

                QMessageBox.warning(self, "Error", "Incorrect passwo   rd! Changes not saved.")

    def cancel_edit(self):
        self.usernameEdit.setText(self.username)
        self.emaiEdit.setText(get_email_by_username(self.username))

        dob_str = get_date_of_birth_by_username(self.username)
        if dob_str:
            try:
                year, month, day = map(int, dob_str.split("-"))
                self.dobEdit.setDate(QDate(year, month, day))
            except ValueError:
                self.dobEdit.setDate(QDate(2000, 1, 1))
        else:
            self.dobEdit.setDate(QDate(2000, 1, 1))

        self.finish_edit_mode()

    def finish_edit_mode(self):
        self.usernameEdit.setReadOnly(True)
        self.emaiEdit.setReadOnly(True)
        self.dobEdit.setReadOnly(True)

        self.edit_btn.setText("Edit Profil")

        if hasattr(self, "cancel_btn") and self.cancel_btn.parent():
            self.button_container.removeWidget(self.cancel_btn)
            self.cancel_btn.deleteLater()

    def _create_security_page(self):
        page = QScrollArea()
        page.setStyleSheet("""
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
        page.setWidgetResizable(True)
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)

        # ------- Titre principal -------
        header_label = QLabel("Security")
        header_label.setProperty("property", "title")
        header_label.setObjectName("header_label")
        header_label.setWordWrap(True)
        self.layout.addWidget(header_label)

        subtitle_label = QLabel(f".{self.username.capitalize()}")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        subtitle_label.setStyleSheet("font-weight: bold;")
        subtitle_label.setWordWrap(True)
        self.layout.addWidget(subtitle_label)

        subtitle = QLabel("Control your account security with password management and device activity tracking.")
        subtitle.setStyleSheet("font-size: 15pt; color: #333; margin-bottom: 10px;")
        subtitle.setWordWrap(True)
        self.layout.addWidget(subtitle)

        # ============================
        #       SECTION PASSWORD
        # ============================
        password_title = QLabel("Password")
        password_title.setProperty("property", "subtitle")
        password_title.setStyleSheet("font-size: 22px; font-weight: bold; margin-top: 10px;")
        password_title.setWordWrap(True)
        self.layout.addWidget(password_title)

        section_name, widgets = self.create_password_section()
        for w in widgets:
            if isinstance(w, QLabel):
                w.setWordWrap(True)
            elif isinstance(w, QPushButton):
                w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                w.setMinimumWidth(0)
            self.layout.addWidget(w)

        # ============================
        #    SECTION LOGIN HISTORY
        # ============================
        history_title = QLabel("Account Login Activity")
        history_title.setProperty("property", "subtitle")
        history_title.setStyleSheet("font-size: 22px; font-weight: bold; margin-top: 20px;")
        history_title.setWordWrap(True)
        self.layout.addWidget(history_title)

        section_name2, widgets2 = self.create_history_section()
        for w in widgets2:
            if isinstance(w, QLabel):
                w.setWordWrap(True)
            elif isinstance(w, QPushButton):
                w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                w.setMinimumWidth(0)
            self.layout.addWidget(w)

        self.layout.addStretch(1)
        page.setWidget(container)
        return page

    def create_password_section(self):
        current_pwd = QLineEdit()
        current_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        current_pwd.setPlaceholderText("Current Password")

        new_pwd = QLineEdit()
        new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        new_pwd.setPlaceholderText("New Password")

        confirm_pwd = QLineEdit()
        confirm_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_pwd.setPlaceholderText("Confirm Password")

        btn_save = QPushButton("Save")
        btn_save.setObjectName("saveButton")
        btn_save.clicked.connect(lambda: QMessageBox.information(self, "Saved", "Password saved!"))
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("saveButton")
        btn_cancel.clicked.connect(lambda: QMessageBox.information(self, "Cancelled", "Action cancelled!"))

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        btn_container = QWidget()
        btn_container.setLayout(btn_layout)

        return ("Password", [current_pwd, new_pwd, confirm_pwd, btn_container])

    def create_history_section(self):
        historique = load_historique()
        user_entries = [e for e in historique if e.get("user") == self.username]

        if not user_entries:
            last_label_text = "No login activity."
            remaining_entries = []
        else:
            last_entry = user_entries[-1]
            last_label_text = f"{last_entry.get('device', '')} - {last_entry.get('location', '')} - {last_entry.get('timestamp', '')}"
            remaining_entries = user_entries[:-1]

        last_label = QLabel(f"{last_label_text} - <span style='color: green; font-weight: bold;'>This device</span>")
        last_label.setTextFormat(Qt.TextFormat.RichText)

        subtitle_label = QLabel("Connections on other devices:")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        for entry in remaining_entries:
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            frame.setFrameShadow(QFrame.Shadow.Raised)
            text_label = QLabel(f"{entry.get('device', '')}\n{entry.get('location', '')}\n{entry.get('timestamp', '')}")
            frame_layout = QVBoxLayout(frame)
            frame_layout.addWidget(text_label)
            container_layout.addWidget(frame)

        return ("Account login activity", [last_label, subtitle_label, container])

    def setup_animation(self):
        self.animation = QPropertyAnimation(self.sidebar_widget, b"minimumWidth")
        self.animation.setDuration(ANIMATION_DURATION)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.sidebar_widget.setFixedWidth(SIDEBAR_WIDTH_MIN)
        self.is_sidebar_open = False

        self.animation.finished.connect(self.update_button_text)

    def setup_connections(self):
        self.settings_button.clicked.connect(self.toggle_sidebar)

        for index, btn in enumerate(self.buttons):
            # Index + 1 car l'index 0 est la page de bienvenue
            btn.clicked.connect(lambda checked, i=index + 1, b=btn: self.switch_page(i, b))

        for btn in self.buttons:
            btn.setChecked(False)

    def toggle_sidebar(self):
        """Lance l'animation pour ouvrir ou fermer la sidebar."""

        if self.is_sidebar_open:
            # Animation de fermeture
            target_width = SIDEBAR_WIDTH_MIN
            start_width = SIDEBAR_WIDTH_MAX
            self.is_sidebar_open = False

            # Optionnel: Revenir à la page d'accueil (index 0) lors de la fermeture
            # self.stacked_widget.setCurrentIndex(0)
            # for btn in self.buttons: btn.setChecked(False)

        else:
            # Animation d'ouverture
            target_width = SIDEBAR_WIDTH_MAX
            start_width = SIDEBAR_WIDTH_MIN
            self.is_sidebar_open = True

            # CORRECTION: Ouvrir la sidebar et sélectionner la page "Personal Info" (Index 1)
            self.switch_page(1, self.buttons[0])

        self.animation.setStartValue(start_width)
        self.animation.setEndValue(target_width)

        if not self.is_sidebar_open:
            self.update_button_text()

        self.animation.start()

    def update_button_text(self):
        """Met à jour le texte des boutons de la sidebar (Icône seule vs Icône + Texte)."""
        width = self.sidebar_widget.minimumWidth()

        if width <= SIDEBAR_WIDTH_MIN:
            for btn in self.buttons:
                btn.setText("")
                btn.setToolTip(btn.full_text)

        else:
            for btn in self.buttons:
                btn.setText(f" {btn.full_text}")
                btn.setToolTip("")

    def switch_page(self, index, clicked_button):
        for btn in self.buttons:
            btn.setChecked(False)

        clicked_button.setChecked(True)

        self.stacked_widget.setCurrentIndex(index)


if __name__ == "__main__":
    # Assurez-vous d'avoir une icône nommée 'icons/user_icon.png' ou changez les chemins dans BUTTONS_DATA.
    # Pour tester rapidement, vous pouvez définir une icône par défaut si les fichiers manquent.
    if not QIcon("icons/user_icon.png").isNull():
        print("Icônes trouvées. Démarrage de l'application.")
    else:
        print("AVERTISSEMENT: Icônes non trouvées. Les boutons n'auront pas d'images.")

    app = QApplication(sys.argv)

    main_window = QMainWindow()

    settings_widget = SettingsPage()
    main_window.setCentralWidget(settings_widget)

    main_window.setWindowTitle("Modern Settings Panel")
    main_window.setGeometry(100, 100, 800, 600)

    main_window.show()

    sys.exit(app.exec())