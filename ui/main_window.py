from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QMessageBox
from ui.profil import ProfileMenuMixin

# --- Import des pages ---
try:
    from ui.gui_about import AboutPage
except ImportError:
    AboutPage = None
    print("AboutPage non disponible")

try:
    from ui.gui_event import EventsPage
except ImportError:
    EventsPage = None
    print("EventsPage non disponible")

try:
    from ui.gui_help import HelpPage
except ImportError:
    HelpPage = None
    print("HelpPage non disponible")

try:
    from ui.gui_dashboard import DashboardPage
except ImportError:
    DashboardPage = None
    print("DashboardPage non disponible")

try:
    from ui.gui_scanner import ScanPage
except ImportError:
    ScanPage = None
    print("ScanPage non disponible")

try:
    from ui.gui_settings import SettingsPage
except ImportError:
    SettingsPage = None
    print("SettingsPage non disponible")

try:
    from ui.gui_home import HomePage
except ImportError:
    HomePage = None
    print("MainPage non disponible")


class AppWindow(QWidget, ProfileMenuMixin):
    def __init__(self):
        super().__init__()

        self.setMinimumSize(1000, 600)

        # Layout principal vertical
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- HEADER (menu horizontal) ---
        self.create_header_menu()

        # --- Zone centrale ---
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # Pages
        self.home_page = None
        self.dashboard_page = None
        self.scan_page = None
        self.settings_page = None
        self.help_page = None
        self.about_page = None
        self.event_page = None

        # Page par défaut
        self.load_home(username="User")

    def create_header_menu(self):
        self.header = QWidget()
        self.header.setFixedHeight(60)
        self.header.setStyleSheet("""
            background-color: #151B54;
            border-radius: 10px;
        """)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(7)

        self.menu_buttons = []
        menu_items = [
            ("Home", "Home"),
            ("Dashboard", "Dashboard"),
            ("Scan", "Scan"),
            ("Events", "Events"),
            ("Settings", "setting"),
            ("Help", "question"),
            ("About", "about")
        ]

        def make_callback(button):
            return lambda checked: self.on_nav_button_clicked(button)

        for text, btn_id in menu_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setProperty("button_id", btn_id)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: none;
                    padding: 10px 18px;
                    font-size: 14px;
                    font-weight: 500;
                }

                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.12);
                    border-radius: 6px;
                }

                QPushButton:checked {
                    background-color: rgba(255, 255, 255, 0.12);
                    color: white ;
                    border-radius: 6px;
                    padding-bottom: 8px;
                    border-bottom: 3px solid white;
                }

                QPushButton:checked:hover {
                    background-color: rgba(255, 255, 255, 0.12);
                }
            """)

            btn.clicked.connect(make_callback(btn))
            self.menu_buttons.append(btn)
            header_layout.addWidget(btn)

        if self.menu_buttons:
            self.menu_buttons[0].setChecked(True)

        header_layout.addStretch(True)

        # Ajouter le profil
        profile_menu = self.create_profile_menu()
        if profile_menu:

            header_layout.addWidget(profile_menu)

        self.main_layout.addWidget(self.header)

    # --- Chargement des pages avec exceptions ---
    def load_home(self, username):
        try:
            if self.home_page is None:
                if HomePage is None:
                    raise RuntimeError("HomePage indisponible")
                self.home_page = HomePage(username=username)
                self.stack.addWidget(self.home_page)
            self.stack.setCurrentWidget(self.home_page)
        except Exception as e:
            self.show_error("Home", e)

    def load_dashboard(self, username):
        try:
            if self.dashboard_page is None:
                if DashboardPage is None:
                    raise RuntimeError("DashboardPage indisponible")
                self.dashboard_page = DashboardPage(username=username)
                self.stack.addWidget(self.dashboard_page)
            self.stack.setCurrentWidget(self.dashboard_page)
        except Exception as e:
            self.show_error("Dashboard", e)

    def load_scan(self, username):
        try:
            if self.scan_page is None:
                if ScanPage is None:
                    raise RuntimeError("ScanPage indisponible")
                self.scan_page = ScanPage(username=username)
                self.stack.addWidget(self.scan_page)
            self.stack.setCurrentWidget(self.scan_page)
        except Exception as e:
            self.show_error("Scan", e)

    def load_event(self, username):
        try:
            if self.event_page is None:
                if EventsPage is None:
                    raise RuntimeError("EventsPage indisponible")
                self.event_page = EventsPage(username=username)
                self.stack.addWidget(self.event_page)
            self.stack.setCurrentWidget(self.event_page)
        except Exception as e:
            self.show_error("Events", e)

    def load_setting(self, username):
        try:
            if self.settings_page is None:
                if SettingsPage is None:
                    raise RuntimeError("SettingsPage indisponible")
                self.settings_page = SettingsPage(username=username)
                self.stack.addWidget(self.settings_page)
            self.stack.setCurrentWidget(self.settings_page)
        except Exception as e:
            self.show_error("Settings", e)

    def load_help(self, username):
        try:
            if self.help_page is None:
                if HelpPage is None:
                    raise RuntimeError("HelpPage indisponible")
                self.help_page = HelpPage(username=username)
                self.stack.addWidget(self.help_page)
            self.stack.setCurrentWidget(self.help_page)
        except Exception as e:
            self.show_error("Help", e)

    def load_about(self, username):
        try:
            if self.about_page is None:
                if AboutPage is None:
                    raise RuntimeError("AboutPage indisponible")
                self.about_page = AboutPage(username=username)
                self.stack.addWidget(self.about_page)
            self.stack.setCurrentWidget(self.about_page)
        except Exception as e:
            self.show_error("About", e)

    # --- Gestion du clic sur menu ---
    def on_nav_button_clicked(self, clicked_button):
        try:
            for btn in self.menu_buttons:
                btn.setChecked(False)
            clicked_button.setChecked(True)

            button_id = clicked_button.property("button_id")
            if button_id == "Home":
                self.load_home("User")
            elif button_id == "Dashboard":
                self.load_dashboard("User")
            elif button_id == "Scan":
                self.load_scan("User")
            elif button_id == "Events":
                self.load_event("User")
            elif button_id == "setting":
                self.load_setting("User")
            elif button_id == "question":
                self.load_help("User")
            elif button_id == "about":
                self.load_about("User")
        except Exception as e:
            self.show_error("Navigation", e)

    # --- Boîte d'erreur centralisée ---
    def show_error(self, page_name, exception):
        QMessageBox.critical(self, f"Erreur {page_name}", f"Une erreur est survenue :\n{str(exception)}")
        print(f"Erreur {page_name} :", exception)


from PyQt6.QtWidgets import QApplication
import sys
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Optionnel : activer le style Fusion pour un rendu uniforme
    app.setStyle("Fusion")

    # Crée et affiche la fenêtre principale
    window = AppWindow()
    window.setWindowTitle("FortiFile Dashboard")  # Titre de la fenêtre
    window.resize(1200, 700)  # Taille initiale
    window.show()

    # Lancer la boucle principale
    sys.exit(app.exec())