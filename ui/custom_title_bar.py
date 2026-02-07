import os
import sys
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPainter, QColor
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QDateTime, pyqtProperty, QRect
from matplotlib.backends.backend_template import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core.gestion_db import get_dashboard_stats
from core.user_manager import load_current_user
from ui.profil import ProfileMenuMixin
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor


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


class ShadowFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

    def apply_shadow_style(self):
        self.setStyleSheet("""
            ShadowFrame {
                background-color: white;
                color:black;
                border: 1px solid #3342CC;
                border-radius: 25px;
                margin: 5px;
            }
            ShadowFrame:hover {
                border: 3px solid #3342CC ;
            }
        """)
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(25)
        shadow_effect.setColor(QColor("#6A76E8"))  # Bleu avec opacité
        shadow_effect.setOffset(0, 0)
        self.setGraphicsEffect(shadow_effect)


class MainPage(QWidget, ProfileMenuMixin):
    def __init__(self, is_dark_theme=False, current_style=None, username=None, email=None):
        super().__init__()
        self.is_dark_theme = is_dark_theme
        self.current_style = current_style
        self.username = load_current_user().upper()
        self.email = email
        self.sidebar_expanded = False
        self.scan_frame_visible = False
        self.last_scan_time = "Never"
        self.history_items = []

        # Variables pour les tailles relatives
        self.screen_size = QApplication.primaryScreen().availableSize()
        self.base_width = 1400
        self.base_height = 900

        self.apply_window_style()
        if current_style:
            self.setStyleSheet(current_style)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.create_main_content()
        self.content_layout.addWidget(self.main_content, 1)

        self.create_scan_frame()
        main_layout.addWidget(self.content_widget, 1)

        # Initialiser l'historique
        self.update_scan_history_display()

    def scale_value(self, value, is_width=True):
        if is_width:
            return int(value * self.screen_size.width() / self.base_width)
        else:
            return int(value * self.screen_size.height() / self.base_height)

    def create_scan_frame(self):
        self.scan_frame = QFrame(self.main_content)

        # Tailles relatives basées sur la résolution d'écran
        frame_width = self.scale_value(800)
        frame_height = self.scale_value(600, False)
        self.scan_frame.setFixedSize(frame_width, frame_height)

        self.scan_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                border: 2px solid #151B54;
            }
        """)
        self.scan_frame.setVisible(False)

        scan_layout = QVBoxLayout(self.scan_frame)
        scan_layout.setContentsMargins(
            self.scale_value(30),
            self.scale_value(20, False),
            self.scale_value(30),
            self.scale_value(20, False)
        )
        scan_layout.setSpacing(self.scale_value(20, False))

        title_widget = QWidget()
        title_widget.setStyleSheet("background-color: transparent;")
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(self.scale_value(15))

        back_btn = QPushButton()
        back_btn.setFixedSize(self.scale_value(45), self.scale_value(45, False))
        back_btn.setFont(QFont("Segoe UI", self.scale_value(10)))
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
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

        icon_size = self.scale_value(30)
        icon_pixmap = QPixmap("img/back.png").scaled(
            icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        back_btn.setIcon(QIcon(icon_pixmap))
        back_btn.setIconSize(QSize(icon_size, icon_size))
        back_btn.clicked.connect(self.hide_scan_frame)

        # Titre
        title_label = QLabel("Select the file/folder to scan")
        title_label.setFont(QFont("Segoe UI", self.scale_value(16), QFont.Weight.Bold))
        title_label.setStyleSheet("color: #151B54; background-color: transparent;border:none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_layout.addWidget(back_btn)
        title_layout.addWidget(title_label)
        scan_layout.addWidget(title_widget)

        # Widget pour le champs et le bouton scan
        path_widget = QWidget()
        path_widget.setStyleSheet("background-color: transparent;")
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(self.scale_value(15))

        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("No selected file/folder")
        self.path_edit.setStyleSheet("""
            QLineEdit {
                background-color: #F7FAFC;
                border: 2px solid #E2E8F0;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                color: #4A5568;
            }
        """)

        self.folder_btn = QPushButton("Browse folders")
        self.folder_btn.setFixedHeight(self.scale_value(45, False))
        self.folder_btn.setMinimumWidth(self.scale_value(150))
        self.folder_btn.setFont(QFont("Segoe UI", self.scale_value(12), QFont.Weight.Bold))
        self.folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #151B54;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #120A37;
            }
            QPushButton:pressed {
                background-color: #120A37;
            }
        """)
        self.folder_btn.clicked.connect(self.browse_folder)

        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.folder_btn)
        scan_layout.addWidget(path_widget)

        # Zone pour l'image et le statut
        self.image_status_widget = QWidget()
        self.image_status_layout = QVBoxLayout(self.image_status_widget)
        self.image_status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_status_layout.setSpacing(self.scale_value(25, False))
        self.image_status_widget.setStyleSheet("background-color: transparent;border:none;")

        self.scan_image_label = QLabel()
        self.scan_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scan_image_label.setStyleSheet("background-color: transparent;border:none;")

        image_size = self.scale_value(200)
        scan_pixmap = QPixmap("img/Scan.png")
        if not scan_pixmap.isNull():
            scan_pixmap = scan_pixmap.scaled(image_size, image_size, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
            self.scan_image_label.setPixmap(scan_pixmap)
        else:
            self.scan_image_label.setText("🔄")
            self.scan_image_label.setStyleSheet(f"font-size: {self.scale_value(100)}px;")

        self.scan_action_btn = QPushButton("Scan")
        self.scan_action_btn.setFixedSize(self.scale_value(200), self.scale_value(45, False))
        self.scan_action_btn.setFont(QFont("Segoe UI", self.scale_value(12), QFont.Weight.Bold))
        self.scan_action_btn.setStyleSheet("""
            QPushButton {
                background-color: #151B54;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #120A37;
            }
            QPushButton:pressed {
                background-color: #120A37;
            }
        """)
        self.scan_action_btn.clicked.connect(self.start_scan)

        self.scan_completed_label = QLabel("Scan completed")
        self.scan_completed_label.setFont(QFont("Segoe UI", self.scale_value(14), QFont.Weight.Bold))
        self.scan_completed_label.setStyleSheet("color: #059669; background-color: transparent;border:none")
        self.scan_completed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scan_completed_label.setVisible(False)

        self.completed_image_label = QLabel()
        self.completed_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.completed_image_label.setStyleSheet("background-color: transparent;border:none;")
        self.completed_image_label.setVisible(False)

        completed_pixmap = QPixmap("img/scanning-device_2.png")
        if not completed_pixmap.isNull():
            completed_pixmap = completed_pixmap.scaled(image_size, image_size, Qt.AspectRatioMode.KeepAspectRatio,
                                                       Qt.TransformationMode.SmoothTransformation)
            self.completed_image_label.setPixmap(completed_pixmap)
        else:
            self.completed_image_label.setText("✅")
            self.completed_image_label.setStyleSheet(f"font-size: {self.scale_value(100)}px;")

        self.image_status_layout.addWidget(self.scan_image_label)
        self.image_status_layout.addWidget(self.scan_action_btn)
        self.image_status_layout.addWidget(self.completed_image_label)
        self.image_status_layout.addWidget(self.scan_completed_label)

        scan_layout.addWidget(self.image_status_widget)
        scan_layout.addStretch()

    def show_scan_frame(self):
        if not self.scan_frame_visible:
            self.scan_frame_visible = True
            self.center_scan_frame()
            self.scan_frame.show()
            self.scan_frame.raise_()

            self.path_edit.clear()
            self.path_edit.setPlaceholderText("No selected folder")

    def hide_scan_frame(self):
        self.scan_frame_visible = False
        self.scan_frame.hide()

        self.scan_image_label.setVisible(True)
        self.scan_action_btn.setVisible(True)
        self.completed_image_label.setVisible(False)
        self.scan_completed_label.setVisible(False)

        self.path_edit.clear()
        self.path_edit.setPlaceholderText("No selected folder")

    def browse_file(self):
        """Ouvre le dialogue de sélection de fichier"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select a file/folder to scan",
            "",
            "Tous les fichiers (*)"
        )

        if file_path:
            self.path_edit.setText(file_path)

    def browse_folder(self):
        """Ouvre le dialogue de sélection de dossier"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select a folder to scan",
            ""
        )

        if folder_path:
            self.path_edit.setText(folder_path)

    def add_scan_to_history(self, scan_info):
        """Ajoute une entrée à l'historique des scans"""
        if not hasattr(self, 'history_content_layout'):
            print("Erreur: history_content_layout non initialisé")
            return

        # Supprimer le message "No scan history" s'il existe
        for i in reversed(range(self.history_content_layout.count())):
            widget = self.history_content_layout.itemAt(i).widget()
            if widget and isinstance(widget, QLabel) and "No scan history" in widget.text():
                self.history_content_layout.removeWidget(widget)
                widget.deleteLater()

        # Créer un widget pour l'entrée d'historique
        history_item = QFrame()
        history_item.setFixedHeight(self.scale_value(60, False))
        history_item.setStyleSheet("""
            QFrame {
                background-color: #151B54;
                border-radius: 10px;
                border: 1px solid #3342CC;
            }
        """)

        item_layout = QHBoxLayout(history_item)
        item_layout.setContentsMargins(
            self.scale_value(15),
            self.scale_value(10, False),
            self.scale_value(15),
            self.scale_value(10, False)
        )
        item_layout.setSpacing(self.scale_value(15))

        # Icône de statut
        status_icon = QLabel()
        if scan_info.get("status") == "completed":
            status_icon.setStyleSheet("""
                QLabel {
                    background-color: #10B981;
                    border-radius: 7px;
                    min-width: 14px;
                    min-height: 14px;
                    max-width: 14px;
                    max-height: 14px;
                }
            """)
        else:
            status_icon.setStyleSheet("""
                QLabel {
                    background-color: #EF4444;
                    border-radius: 7px;
                    min-width: 14px;
                    min-height: 14px;
                    max-width: 14px;
                    max-height: 14px;
                }
            """)

        # Informations du scan
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(self.scale_value(4, False))

        # Tronquer le chemin si trop long
        path = scan_info.get("path", "Unknown path")
        display_path = path if len(path) < 60 else path[:37] + "..."

        path_label = QLabel(display_path)
        path_label.setFont(QFont("Segoe UI", self.scale_value(10), QFont.Weight.Medium))
        path_label.setStyleSheet("color: white; background-color: transparent;border:none;")
        path_label.setToolTip(path)  # Tooltip avec le chemin complet

        time_label = QLabel(scan_info.get("time", "Unknown time"))
        time_label.setFont(QFont("Segoe UI", self.scale_value(9)))
        time_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); background-color: transparent;border:none;")

        info_layout.addWidget(path_label)
        info_layout.addWidget(time_label)

        # Résultat
        result_label = QLabel(scan_info.get("result", "No threats"))
        result_label.setFont(QFont("Segoe UI", self.scale_value(10), QFont.Weight.Medium))
        if scan_info.get("threats_found", 0) > 0:
            result_label.setStyleSheet("color: #EF4444; background-color: transparent;border:none;")
        else:
            result_label.setStyleSheet("color: #10B981; background-color: transparent;border:none;")

        item_layout.addWidget(status_icon)
        item_layout.addWidget(info_widget, 1)
        item_layout.addWidget(result_label)

        # Ajouter au début de la liste (le plus récent en premier)
        self.history_content_layout.insertWidget(0, history_item)
        self.history_items.insert(0, history_item)

        # Limiter à 10 entrées maximum
        if len(self.history_items) > 10:
            old_item = self.history_items.pop()
            self.history_content_layout.removeWidget(old_item)
            old_item.deleteLater()

    def update_scan_history_display(self):
        """Met à jour l'affichage de l'historique"""
        # Effacer l'historique actuel
        for i in reversed(range(self.history_content_layout.count())):
            widget = self.history_content_layout.itemAt(i).widget()
            if widget and widget != self.history_content_layout.itemAt(i).widget():  # Éviter les doublons
                self.history_content_layout.removeWidget(widget)
                widget.deleteLater()

        # Réinitialiser la liste
        self.history_items.clear()

        # Si pas d'historique, afficher un message
        if len(self.history_items) == 0:
            no_history_label = QLabel("No scan history available")
            no_history_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_history_label.setFont(QFont("Segoe UI", self.scale_value(11)))
            no_history_label.setStyleSheet("""
                color: #525063; 
                background-color: transparent; 
                padding: 20px;
                border :1px solid #3342CC;
                font-weight:bold;
            """)
            no_history_label.setMinimumHeight(self.scale_value(100, False))
            self.history_content_layout.addWidget(no_history_label)

    def start_scan(self):
        path = self.path_edit.text().strip()

        if not path:
            QMessageBox.warning(self, "Warning", "Please select a file or a folder to scan")
            return

        if not os.path.exists(path):
            QMessageBox.critical(self, "Erreur", "the path doesn't exist")
            return

        # Enregistrer l'heure actuelle du scan
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.last_scan_time = current_time

        # Mettre à jour l'affichage dans la carte bleue
        self.update_last_scan_display()

        # Simuler un résultat de scan (à remplacer par votre logique réelle)
        threats_found = 0  # Simuler aucune menace trouvée
        scan_status = "completed"

        # Ajouter à l'historique
        scan_info = {
            "path": path,
            "time": current_time,
            "status": scan_status,
            "result": "No threats found" if threats_found == 0 else f"{threats_found} threats found",
            "threats_found": threats_found
        }

        self.add_scan_to_history(scan_info)

        self.scan_image_label.setVisible(False)
        self.scan_action_btn.setVisible(False)

        # Afficher l'image de complétion et le texte
        self.completed_image_label.setVisible(True)
        self.scan_completed_label.setVisible(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.scan_frame_visible:
            self.center_scan_frame()

    def center_scan_frame(self):
        # Obtenir la géométrie du contenu principal
        main_rect = self.main_content.rect()

        x = (main_rect.width() - self.scan_frame.width()) // 2
        y = (main_rect.height() - self.scan_frame.height()) // 2

        self.scan_frame.move(x, y)

    def create_main_content(self):
        """Crée la zone de contenu principale avec des tailles relatives"""
        self.main_content = QWidget()
        self.apply_main_content_style()

        main_layout = QVBoxLayout(self.main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)



        # Mettre à jour le nom d'utilisateur dans le menu profil
        if hasattr(self, 'username') and self.username:
            self.set_username(self.username)


        # Contenu principal avec message de bienvenue personnalisé
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.setSpacing(self.scale_value(40, False))
        content_layout.setContentsMargins(
            self.scale_value(40),
            self.scale_value(20, False),
            self.scale_value(40),
            self.scale_value(20, False)
        )

        icon_text_widget = QWidget()
        icon_text_layout = QHBoxLayout(icon_text_widget)
        icon_text_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_text_layout.setSpacing(self.scale_value(20))

        icon_label = QLabel()
        icon_size = self.scale_value(50)
        icon_pixmap = QPixmap("img/evaluation.png")
        if not icon_pixmap.isNull():
            icon_pixmap = icon_pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
        else:
            icon_label.setText("🛡️")
            icon_label.setStyleSheet(f"font-size: {self.scale_value(32)}px;")

        # Ajouter le texte
        text_label = QLabel(
            f"Welcome {self.username} to FortiFile ,where you can monitor file changes and secure your critical data in real-time.")
        text_label.setFont(QFont("Segoe UI", self.scale_value(16), QFont.Weight.Bold))
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: #151B54;")
        text_label.setMinimumWidth(self.scale_value(600))

        icon_text_layout.addWidget(icon_label)
        icon_text_layout.addWidget(text_label)
        content_layout.addWidget(icon_text_widget)

        # Layout principal pour les sections
        main_sections_widget = QWidget()
        main_sections_layout = QHBoxLayout(main_sections_widget)
        main_sections_layout.setContentsMargins(0, 0, 0, 0)
        main_sections_layout.setSpacing(self.scale_value(20))

        # Colonne de gauche
        left_column_widget = QWidget()
        left_column_layout = QVBoxLayout(left_column_widget)
        left_column_layout.setContentsMargins(0, 0, 0, 0)
        left_column_layout.setSpacing(self.scale_value(20, False))

        # File/folder selection
        file_frame = ShadowFrame()
        file_frame.apply_shadow_style()
        file_frame.setMinimumHeight(self.scale_value(120, False))

        frame_layout = QHBoxLayout(file_frame)
        frame_layout.setContentsMargins(
            self.scale_value(30),
            self.scale_value(20, False),
            self.scale_value(30),
            self.scale_value(20, False)
        )
        frame_layout.setSpacing(self.scale_value(20))

        scan_icon_label = QLabel()
        scan_icon_label.setStyleSheet("background-color: transparent; border: none;")
        scan_icon_size = self.scale_value(30)
        scan_icon_pixmap = QPixmap("img/quickScan.png")
        if not scan_icon_pixmap.isNull():
            scan_icon_pixmap = scan_icon_pixmap.scaled(scan_icon_size, scan_icon_size,
                                                       Qt.AspectRatioMode.KeepAspectRatio,
                                                       Qt.TransformationMode.SmoothTransformation)
            scan_icon_label.setPixmap(scan_icon_pixmap)
        else:
            scan_icon_label.setText("🔍")
            scan_icon_label.setStyleSheet(
                f"font-size: {self.scale_value(24)}px; color: white;border:none;background-color:transparent;")

        title_widget = QWidget()
        title_widget.setStyleSheet("background-color: transparent;")
        title_layout = QVBoxLayout(title_widget)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.setSpacing(self.scale_value(5, False))
        title_layout.setContentsMargins(0, 0, 0, 0)

        scan_title = QLabel("Quick Scan")
        scan_title.setFont(QFont("Segoe UI", self.scale_value(14), QFont.Weight.Bold))
        scan_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        scan_title.setStyleSheet("color: black; background-color: transparent; padding: 0; margin: 0;border:none;")

        lastScan = QLabel("Last Scan: Never")
        lastScan.setObjectName("last_scan_label")
        lastScan.setFont(QFont("Segoe UI", self.scale_value(10), QFont.Weight.Medium))
        lastScan.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lastScan.setStyleSheet(
            "color: #525063; background-color: transparent; padding: 0; margin: 0;border:none;font-weight:bold;")

        title_layout.addWidget(scan_title)
        title_layout.addWidget(lastScan)

        # Bouton Scan
        scan_btn = QPushButton("Scan Now")
        scan_btn.setFixedSize(self.scale_value(120), self.scale_value(45, False))
        scan_btn.setFont(QFont("Segoe UI", self.scale_value(12), QFont.Weight.Bold))
        scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        scan_btn.clicked.connect(self.show_scan_frame)

        frame_layout.addWidget(scan_icon_label)
        frame_layout.addWidget(title_widget)
        frame_layout.addStretch()
        frame_layout.addWidget(scan_btn)

        # Auto scan frame
        Autoscan_frame = ShadowFrame()
        Autoscan_frame.apply_shadow_style()
        Autoscan_frame.setMinimumHeight(self.scale_value(120, False))

        Autoscan_layout = QHBoxLayout(Autoscan_frame)
        Autoscan_layout.setContentsMargins(
            self.scale_value(30),
            self.scale_value(20, False),
            self.scale_value(30),
            self.scale_value(20, False)
        )
        Autoscan_layout.setSpacing(self.scale_value(20))

        Autoscan_label = QLabel()
        Autoscan_label.setStyleSheet("background-color: transparent; border: none;")
        Autoscan_icon_pixmap = QPixmap("img/encrypted.png")
        if not Autoscan_icon_pixmap.isNull():
            Autoscan_icon_pixmap = Autoscan_icon_pixmap.scaled(scan_icon_size, scan_icon_size,
                                                               Qt.AspectRatioMode.KeepAspectRatio,
                                                               Qt.TransformationMode.SmoothTransformation)
            Autoscan_label.setPixmap(Autoscan_icon_pixmap)
        else:
            Autoscan_label.setText("🔍")
            Autoscan_label.setStyleSheet(
                f"font-size: {self.scale_value(24)}px; color: white;border:none;background-color:transparent;")

        Autoscan_widget = QWidget()
        Autoscan_widget.setStyleSheet("background-color: transparent;")
        Autoscan_title_layout = QVBoxLayout(Autoscan_widget)
        Autoscan_title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        Autoscan_title_layout.setSpacing(self.scale_value(5, False))
        Autoscan_title_layout.setContentsMargins(0, 0, 0, 0)

        Autoscan_title = QLabel("Auto scan")
        Autoscan_title.setFont(QFont("Segoe UI", self.scale_value(14), QFont.Weight.Bold))
        Autoscan_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        Autoscan_title.setStyleSheet("color: black; background-color: transparent; padding: 0; margin: 0;border:none;")

        Autoscan_lastScan = QLabel("Scan at Windows startup")
        Autoscan_lastScan.setFont(QFont("Segoe UI", self.scale_value(10), QFont.Weight.Medium))
        Autoscan_lastScan.setAlignment(Qt.AlignmentFlag.AlignLeft)
        Autoscan_lastScan.setStyleSheet(
            "color: #525063; background-color: transparent; padding: 0; margin: 0;border:none;;font-weight:bold;")

        Autoscan_title_layout.addWidget(Autoscan_title)
        Autoscan_title_layout.addWidget(Autoscan_lastScan)

        # Ajouter le toggle switch
        self.auto_scan_switch = ModernSwitch()
        self.auto_scan_switch.toggled.connect(self.on_auto_scan_toggled)

        Autoscan_layout.addWidget(Autoscan_label)
        Autoscan_layout.addWidget(Autoscan_widget)
        Autoscan_layout.addStretch()
        Autoscan_layout.addWidget(self.auto_scan_switch)

        # Frame de l'historique des scans
        history_frame = ShadowFrame()
        history_frame.apply_shadow_style()
        history_frame.setMinimumHeight(self.scale_value(300, False))

        history_layout = QVBoxLayout(history_frame)
        history_layout.setContentsMargins(
            self.scale_value(30),
            self.scale_value(20, False),
            self.scale_value(30),
            self.scale_value(20, False)
        )
        history_layout.setSpacing(self.scale_value(20, False))

        # Widget pour contenir l'icône et le titre de l'historique
        history_icon_title_widget = QWidget()
        history_icon_title_widget.setStyleSheet("background-color: transparent;")
        history_icon_title_layout = QHBoxLayout(history_icon_title_widget)
        history_icon_title_layout.setContentsMargins(0, 0, 0, 0)
        history_icon_title_layout.setSpacing(self.scale_value(15))
        history_icon_title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        history_label = QLabel()
        history_label.setStyleSheet("background-color: transparent; border: none;")
        history_icon_pixmap = QPixmap("img/history.png")
        if not history_icon_pixmap.isNull():
            history_icon_pixmap = history_icon_pixmap.scaled(scan_icon_size, scan_icon_size,
                                                             Qt.AspectRatioMode.KeepAspectRatio,
                                                             Qt.TransformationMode.SmoothTransformation)
            history_label.setPixmap(history_icon_pixmap)
        else:
            history_label.setText("📋")
            history_label.setStyleSheet(
                f"font-size: {self.scale_value(24)}px; color: white;border:none;background-color:transparent;")

        historyTitle = QLabel("Scan History")
        historyTitle.setFont(QFont("Segoe UI", self.scale_value(14), QFont.Weight.Bold))
        historyTitle.setAlignment(Qt.AlignmentFlag.AlignLeft)
        historyTitle.setStyleSheet("color: black; background-color: transparent; padding: 0; margin: 0; border: none;")

        history_icon_title_layout.addWidget(history_label)
        history_icon_title_layout.addWidget(historyTitle)

        # Zone de défilement pour l'historique
        self.history_scroll_area = QScrollArea()
        self.history_scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: rgba(45, 55, 72, 0.8);
                width: 10px;
                border-radius: 5px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(74, 85, 104, 0.8);
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(113, 128, 150, 0.8);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        self.history_scroll_area.setWidgetResizable(True)
        self.history_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.history_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Widget pour contenir les éléments d'historique
        self.history_content = QWidget()
        self.history_content.setStyleSheet("background-color: transparent;")
        self.history_content_layout = QVBoxLayout(self.history_content)
        self.history_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.history_content_layout.setSpacing(self.scale_value(8, False))
        self.history_content_layout.setContentsMargins(
            self.scale_value(2),
            self.scale_value(2, False),
            self.scale_value(8),
            self.scale_value(2, False)
        )

        self.history_scroll_area.setWidget(self.history_content)

        history_layout.addWidget(history_icon_title_widget)
        history_layout.addWidget(self.history_scroll_area)

        # Ajouter les frames à la colonne de gauche
        left_column_layout.addWidget(file_frame)
        left_column_layout.addWidget(Autoscan_frame)
        left_column_layout.addWidget(history_frame)

        # Colonne de droite - Stats
        stats_frame = ShadowFrame()
        stats_frame.apply_shadow_style()
        stats_frame.setMinimumHeight(self.scale_value(500, False))

        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(
            self.scale_value(30),
            self.scale_value(20, False),
            self.scale_value(30),
            self.scale_value(20, False)
        )
        stats_layout.setSpacing(self.scale_value(20, False))

        # Widget pour contenir l'icône et le titre (sur la même ligne)
        icon_title_widget = QWidget()
        icon_title_widget.setStyleSheet("background-color: transparent;")
        icon_title_layout = QHBoxLayout(icon_title_widget)
        icon_title_layout.setContentsMargins(0, 0, 0, 0)
        icon_title_layout.setSpacing(self.scale_value(15))
        icon_title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        stats_label = QLabel()
        stats_label.setStyleSheet("background-color: transparent; border: none;")
        stats_icon_pixmap = QPixmap("img/file overview.png")
        if not stats_icon_pixmap.isNull():
            stats_icon_pixmap = stats_icon_pixmap.scaled(scan_icon_size, scan_icon_size,
                                                         Qt.AspectRatioMode.KeepAspectRatio,
                                                         Qt.TransformationMode.SmoothTransformation)
            stats_label.setPixmap(stats_icon_pixmap)
        else:
            stats_label.setText("📊")
            stats_label.setStyleSheet(
                f"font-size: {self.scale_value(24)}px; color: white;border:none;background-color:transparent;")

        statsTitle = QLabel("File status overview")
        statsTitle.setFont(QFont("Segoe UI", self.scale_value(14), QFont.Weight.Bold))
        statsTitle.setAlignment(Qt.AlignmentFlag.AlignLeft)
        statsTitle.setStyleSheet("color: black; background-color: transparent; padding: 0; margin: 0; border: none;")

        icon_title_layout.addWidget(stats_label)
        icon_title_layout.addWidget(statsTitle)

        stats_layout.addWidget(icon_title_widget, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
        stats_layout.addStretch()

        # Ajouter les colonnes au layout principal
        main_sections_layout.addWidget(left_column_widget)
        main_sections_layout.addWidget(stats_frame, alignment=Qt.AlignmentFlag.AlignTop)

        content_layout.addWidget(main_sections_widget)
        stats_layout.addWidget(self.create_graph_box())

        main_layout.addWidget(content_widget, 1)

    def create_graph_box(self):
        stats = get_dashboard_stats()
        new_files = stats.get("suspects_new", 0)
        modified_files = stats.get("suspects_modified", 0)
        deleted_files = stats.get("suspects_deleted", 0)

        labels = ["New", "Modified", "Deleted"]
        values = [new_files, modified_files, deleted_files]
        colors = ["#29ABE2", "#F2C94C", "#EB5757"]

        total = sum(values)

        # --- Widget contenant le graphique ---
        graph_widget = QWidget()
        graph_layout = QVBoxLayout(graph_widget)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(5)

        # --- Titre ---
        title_label = QLabel("File Status Overview")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: black;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        graph_layout.addWidget(title_label)

        # --- Graphique Pie ---
        fig = Figure(figsize=(3, 3), facecolor='white')
        ax = fig.add_subplot(111)
        fig.subplots_adjust(0.05, 0.05, 0.95, 0.95)

        if total > 0:
            wedges, texts = ax.pie(
                values,
                colors=colors,
                startangle=90,
                wedgeprops=dict(width=0.4, edgecolor='white'),
            )
            ax.text(0, 0, str(total), ha='center', va='center', fontsize=16, fontweight='bold')
        else:
            ax.pie([1], colors=["#CCCCCC"], startangle=90, wedgeprops=dict(width=0.4, edgecolor='white'))
            ax.text(0, 0, "No Data", ha='center', va='center', fontsize=12, fontweight='bold')

        ax.axis("equal")
        canvas = FigureCanvas(fig)
        graph_layout.addWidget(canvas)

        # --- Légende ---
        legend = QLabel("🟦 New   🟨 Modified   🟥 Deleted")
        legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        legend.setStyleSheet("font-size: 12px;")
        graph_layout.addWidget(legend)

        return graph_widget

    def on_auto_scan_toggled(self, checked):
        """Gère le changement d'état du switch Auto Scan"""
        if checked:
            print("Auto scan activé - Analyse au démarrage de Windows activée")
            # Ici vous pouvez ajouter la logique pour activer l'analyse au démarrage
        else:
            print("Auto scan désactivé - Analyse au démarrage de Windows désactivée")
            # Ici vous pouvez ajouter la logique pour désactiver l'analyse au démarrage


    def apply_main_content_style(self):
        if self.is_dark_theme:
            self.main_content.setStyleSheet("""
                QMainWindow {
                    margin: 0px;
                    padding: 0px;
                    background-color: #FFFFFF;
                }
                QWidget {
                    margin: 0px;
                    padding: 0px;
                    border: none;
                }
                QWidget {
                    background-color: #FFFFFF;
                }
                QLabel {
                    color: #FFFFFF;
                    background-color: transparent;
                    margin: 0px;
                    padding: 0px;
                }
            """)
        else:
            self.main_content.setStyleSheet("""
                QWidget {
                    background-color: #DFDFED;
                    margin: 0px;
                    padding: 0px;
                    border: none;
                }
                QLabel {
                    color: #5D5898;
                    background-color: transparent;
                    margin: 0px;
                    padding: 0px;
                }
            """)

    def update_last_scan_display(self):
        """Met à jour l'affichage du dernier scan dans la carte bleue"""
        last_scan_label = self.findChild(QLabel, "last_scan_label")
        if last_scan_label:
            if self.last_scan_time == "Never":
                last_scan_label.setText("Last Scan: Never")
            else:
                last_scan_label.setText(f"Last Scan: {self.last_scan_time}")

    def apply_window_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                margin: 0px;
                padding: 0px;
                border: none;
            }
        """)

    def go_back(self):
        """Retourne à la page de login"""
        pass

    def toggle_sidebar(self):
        self.sidebar_expanded = not self.sidebar_expanded

        self.animation_min = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.animation_max = QPropertyAnimation(self.sidebar, b"maximumWidth")

        for anim in (self.animation_min, self.animation_max):
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuart)

        if self.sidebar_expanded:
            self.animation_min.setStartValue(self.scale_value(100))
            self.animation_min.setEndValue(self.scale_value(200))
            self.animation_max.setStartValue(self.scale_value(100))
            self.animation_max.setEndValue(self.scale_value(200))
            self.animation_max.finished.connect(lambda: self.show_sidebar_text(True))
        else:
            self.show_sidebar_text(False)
            self.animation_min.setStartValue(self.scale_value(200))
            self.animation_min.setEndValue(self.scale_value(100))
            self.animation_max.setStartValue(self.scale_value(200))
            self.animation_max.setEndValue(self.scale_value(100))

        self.animation_min.start()
        self.animation_max.start()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Créer et afficher la fenêtre principale
    window = MainPage(
        is_dark_theme=False,
        current_style=None,
        username="Tester",
        email="tester@example.com"
    )
    window.resize(1200, 700)
    window.show()

    sys.exit(app.exec())