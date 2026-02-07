import os
import subprocess
from PyQt6.QtGui import  QPixmap, QIcon, QPainter, QColor
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QDateTime, pyqtProperty, QRect
from matplotlib.backends.backend_template import FigureCanvas
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from core.config_manager import update_mode, get_mode
from core.gestion_db import get_dashboard_stats, get_user_history
from core.integrity_monitoring import  build_baseline_for_folder
from core.user_manager import load_current_user
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
import sys

from core.user_manager import load_current_user, get_email_by_username
from core.email_sender import send_custom_email
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

base_dir = os.path.dirname(os.path.abspath(__file__))
back_path = os.path.join(base_dir, "../img/back.png")
scan_path = os.path.join(base_dir, "../img/logoApplication.png")
completed_path = os.path.join(base_dir, "../img/scanning-device_2.png")
icon_path = os.path.join(base_dir, "../img/iconFortiFile.PNG")
quick_path = os.path.join(base_dir, "../img/dossier-ouvert.png")
auto_path = os.path.join(base_dir, "../img/auto.png")
historic_path = os.path.join(base_dir, "../img/archiver.png")
reset_path = os.path.join(base_dir,"../img/recharger.png")
add_path = os.path.join(base_dir,"../img/add.png")


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
                border: 1px solid #808080;
                border-radius: 25px;
                margin: 5px;
            }
            ShadowFrame:hover {
                border: 3px solid #151B54 ;
            }
        """)
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(25)
        shadow_effect.setColor(QColor("#808080"))  # Bleu avec opacité
        shadow_effect.setOffset(0, 0)
        self.setGraphicsEffect(shadow_effect)


def create_step_widget(step_number, step_text, is_last_step):
    v_container = QVBoxLayout()
    v_container.setSpacing(0)
    v_container.setContentsMargins(0, 0, 0, 0)

    # Ligne horizontale pour le numéro et le texte
    h_step = QHBoxLayout()
    h_step.setSpacing(10)
    h_step.setContentsMargins(0, 0, 0, 0)

    # Cercle numéro
    num_label = QLabel(str(step_number))
    num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    num_label.setFixedSize(28, 28)
    num_label.setStyleSheet("""
        QLabel {
            background-color: #151B54;
            color: white;
            border-radius: 14px;
            font-weight: bold;
            font-size: 11pt;
        }
    """)

    # Texte de l'étape
    text_label = QLabel(step_text)
    text_font = QFont("Arial", 11)
    text_font.setWeight(QFont.Weight.Bold)
    text_label.setFont(text_font)
    text_label.setStyleSheet("color: #333333;")

    h_step.addWidget(num_label)
    h_step.addWidget(text_label, stretch=1)
    v_container.addLayout(h_step)

    # Ligne verticale si ce n'est pas la dernière étape
    if not is_last_step:
        line_frame = QFrame()
        line_frame.setFixedWidth(2)
        line_frame.setFixedHeight(30)
        line_frame.setStyleSheet("background-color: #151B54; border: none;")

        # Conteneur horizontal pour centrer la ligne sous le cercle
        h_line_container = QHBoxLayout()
        h_line_container.addSpacing(13)  # Déplacement pour centrer
        h_line_container.addWidget(line_frame)
        h_line_container.addStretch()
        v_container.addLayout(h_line_container)
        v_container.addSpacing(3)  # Ajuste l'espace entre la ligne et l'étape suivante

    step_widget = QWidget()
    step_widget.setLayout(v_container)
    return step_widget


class HomePage(QWidget):
    def __init__(self, username="User"):
        super().__init__()
        self.username = username.upper()
        self.is_dark_theme = False
        self.scan_frame_visible = False
        self.mode = True
        self.init_ui()

    def init_ui(self):
        # Splitter principal horizontal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)

        # Titre principal
        # Titre principal
        title_label = QLabel("  Welcome to FortiFile")
        title_font = QFont("Segoe UI", 26, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            color: #151B54;           /* Bleu profond pour confiance et sécurité */
            background-color: transparent;
            letter-spacing: 1px;
        """)

        # Sous-titre
        subtitle_label = QLabel(
            "Where you can monitor file changes and secure your critical data in real-time"
        )
        subtitle_font = QFont("Segoe UI", 14, QFont.Weight.Medium)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("""
            color: #212121;          
            background-color: transparent;
            padding-left: 12px;
            font-style: italic;
        """)

        subtitle_label.setFont(subtitle_font)

        left_layout.addWidget(title_label)
        left_layout.addWidget(subtitle_label)

        # Frame Add Folder
        add_folder_frame = ShadowFrame()
        add_folder_frame.apply_shadow_style()
        add_folder_frame.setFrameShape(QFrame.Shape.StyledPanel)

        add_folder_frame.setFixedHeight(120)

        add_folder_layout = QHBoxLayout(add_folder_frame)
        add_folder_layout.setContentsMargins(30,20,30,20)
        scan_icon_label = QLabel()
        scan_icon_label.setStyleSheet("background-color: transparent; border: none;")
        scan_icon_pixmap = QPixmap(quick_path)
        if not scan_icon_pixmap.isNull():
            scan_icon_pixmap = scan_icon_pixmap.scaled(30, 30,
                                                       Qt.AspectRatioMode.KeepAspectRatio,
                                                       Qt.TransformationMode.SmoothTransformation)
            scan_icon_label.setPixmap(scan_icon_pixmap)
        else:
            scan_icon_label.setText("🔍")
            scan_icon_label.setStyleSheet(
                f"font-size: 24px; color: white;border:none;background-color:transparent;")

        title_widget = QWidget()
        title_widget.setStyleSheet("background-color: transparent;")
        title_layout = QVBoxLayout(title_widget)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.setSpacing(5)
        title_layout.setContentsMargins(0, 0, 0, 0)
        scan_title = QLabel("Quick add")
        scan_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        scan_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        scan_title.setStyleSheet("color: black; background-color: transparent; padding: 0; margin: 0;border:none;")

        lastScan = QLabel("Add a folder to secure it")
        lastScan.setObjectName("last_scan_label")
        lastScan.setFont(QFont("Segoe UI",10, QFont.Weight.Medium))
        lastScan.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lastScan.setStyleSheet(
            "color: #525063; background-color: transparent; padding: 0; margin: 0;border:none;font-weight:bold;")

        title_layout.addWidget(scan_title)
        title_layout.addWidget(lastScan)
        scan_icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        add_folder_layout.addWidget(scan_icon_label)
        add_folder_layout.addWidget(title_widget)
        add_folder_layout.addStretch(True)
        add_folder_button = QPushButton("")
        icon_pixmap = QPixmap(add_path).scaled(
            30, 30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        add_folder_button.setIcon(QIcon(icon_pixmap))
        add_folder_button.setIconSize(QSize(40, 40))
        add_folder_button.setToolTip("Add Folder ")
        add_folder_button.setStyleSheet("""
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
        add_folder_button.clicked.connect(self.show_scan_frame)

        add_folder_button.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))

        add_folder_layout.addWidget(add_folder_button)
        add_folder_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)


        # Frame Historique
        history_frame =  ShadowFrame()
        history_frame.apply_shadow_style()
        history_frame.setFrameShape(QFrame.Shape.StyledPanel)
        history_frame.setMinimumHeight(200)
        history_layout = QVBoxLayout(history_frame)



        # Widget pour contenir l'icône et le titre de l'historique
        history_icon_title_widget = QWidget()
        history_icon_title_widget.setStyleSheet("background-color: transparent;")
        history_icon_title_layout = QHBoxLayout(history_icon_title_widget)
        history_icon_title_layout.setContentsMargins(20,20,20,0)
        history_icon_title_layout.setSpacing(15)
        history_icon_title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        history_label = QLabel()
        history_label.setStyleSheet("background-color: transparent; border: none;")
        history_icon_pixmap = QPixmap(historic_path)
        if not history_icon_pixmap.isNull():
            history_icon_pixmap = history_icon_pixmap.scaled(30, 30,
                                                             Qt.AspectRatioMode.KeepAspectRatio,
                                                             Qt.TransformationMode.SmoothTransformation)
            history_label.setPixmap(history_icon_pixmap)
        else:
            history_label.setText("📋")
            history_label.setStyleSheet(
                f"font-size: 24px; color: white;border:none;background-color:transparent;")

        historyTitle = QLabel("Scan History")
        historyTitle.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        historyTitle.setAlignment(Qt.AlignmentFlag.AlignLeft)
        historyTitle.setStyleSheet("color: black; background-color: transparent; padding: 0; margin: 0; border: none;")

        history_icon_title_layout.addWidget(history_label)
        history_icon_title_layout.addWidget(historyTitle)
        reset_button = QPushButton()
        reset_button.setIcon(QIcon(reset_path))  # remplace par le chemin de ton icône
        reset_button.setIconSize(QSize(20, 20))
        reset_button.setFixedSize(28, 28)
        reset_button.setStyleSheet("""
                   QPushButton {
                       background-color: transparent;
                       border: none;
                   }
                   QPushButton:hover {
                       background-color: rgba(255, 255, 255, 0.1);
                       border-radius: 5px;
                   }
               """)
        reset_button.setToolTip("Reset Scan History")
        reset_button.clicked.connect(self.update_scan_history_display)  # Assure-toi d'avoir cette fonction

        # Ajouter le bouton à la fin du layout horizontal
        history_icon_title_layout.addStretch()  # pousse le bouton à droite
        history_icon_title_layout.addWidget(reset_button)

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
        self.history_content_layout.setSpacing(8)
        self.history_content_layout.setContentsMargins(
           2,
          2,
           8,
           2
        )

        self.history_scroll_area.setWidget(self.history_content)

        history_layout.addWidget(history_icon_title_widget)
        history_layout.addWidget(self.history_scroll_area)

        Autoscan_frame = ShadowFrame()
        Autoscan_frame.apply_shadow_style()
        Autoscan_frame.setMinimumHeight(120)

        Autoscan_layout = QHBoxLayout(Autoscan_frame)
        Autoscan_layout.setContentsMargins(30,20,30,20)
        Autoscan_layout.setSpacing(20)

        Autoscan_label = QLabel()
        Autoscan_label.setStyleSheet("background-color: transparent; border: none;")
        Autoscan_icon_pixmap = QPixmap(auto_path)
        if not Autoscan_icon_pixmap.isNull():
            Autoscan_icon_pixmap = Autoscan_icon_pixmap.scaled(40, 40,
                                                               Qt.AspectRatioMode.KeepAspectRatio,
                                                               Qt.TransformationMode.SmoothTransformation)
            Autoscan_label.setPixmap(Autoscan_icon_pixmap)
        else:
            Autoscan_label.setText("🔍")
            Autoscan_label.setStyleSheet(
                f"font-size: 24px; color: white;border:none;background-color:transparent;")

        Autoscan_widget = QWidget()
        Autoscan_widget.setStyleSheet("background-color: transparent;")
        Autoscan_title_layout = QVBoxLayout(Autoscan_widget)
        Autoscan_title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        Autoscan_title_layout.setSpacing(5)
        Autoscan_title_layout.setContentsMargins(0, 0, 0, 0)

        Autoscan_title = QLabel("Auto scan")
        Autoscan_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        Autoscan_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        Autoscan_title.setStyleSheet("color: black; background-color: transparent; padding: 0; margin: 0;border:none;")

        Autoscan_lastScan = QLabel("Scan at Windows startup")
        Autoscan_lastScan.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        Autoscan_lastScan.setAlignment(Qt.AlignmentFlag.AlignLeft)
        Autoscan_lastScan.setStyleSheet(
            "color: #525063; background-color: transparent; padding: 0; margin: 0;border:none;;font-weight:bold;")

        Autoscan_title_layout.addWidget(Autoscan_title)
        Autoscan_title_layout.addWidget(Autoscan_lastScan)


        # Ajouter le toggle switch
        self.auto_scan_switch = ModernSwitch()
        self.auto_scan_switch.toggled.connect(self.on_auto_scan_toggled)

        if get_mode() == "auto":
            self.auto_scan_switch.setChecked(True)

        else:
            self.auto_scan_switch.setChecked(False)

        Autoscan_layout.addWidget(Autoscan_label)
        Autoscan_layout.addWidget(Autoscan_widget)
        Autoscan_layout.addStretch()
        Autoscan_layout.addWidget(self.auto_scan_switch)
        add_folder_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)



        left_layout.addWidget(add_folder_frame)
        left_layout.addWidget(Autoscan_frame)
        left_layout.addWidget(history_frame)
        left_layout.addStretch(True)



        # ------------------
        # Zone droite
        # ------------------
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(20)

        # Ligne avec titre + bouton Hi [username] + AutoScan
        # Frame Graph
        stats_frame = ShadowFrame()
        stats_frame.apply_shadow_style()
        stats_frame.setFrameShape(QFrame.Shape.StyledPanel)
        stats_frame.setMinimumHeight(200)
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(
            30,
            20,
            30,
            20
        )
        stats_layout.setSpacing(20)

        # Widget pour contenir l'icône et le titre (sur la même ligne)
        icon_title_widget = QWidget()
        icon_title_widget.setStyleSheet("background-color: transparent;")
        icon_title_layout = QHBoxLayout(icon_title_widget)
        icon_title_layout.setContentsMargins(0, 0, 0, 0)
        icon_title_layout.setSpacing(15)
        icon_title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)



        stats_layout.addWidget(icon_title_widget, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
        stats_layout.addStretch()
        stats_layout.addWidget(self.create_graph_box())

        right_layout.addWidget(stats_frame)



        # Frame Guide
        guide_frame = QFrame()

        guide_frame.setMinimumWidth(350)
        guide_frame.setMaximumWidth(450)  # Une taille agréable pour une carte de guide

        # --- 2. Le Layout principal (QVBoxLayout) ---
        guide_layout = QVBoxLayout(guide_frame)
        guide_layout.setSpacing(10)
        guide_layout.setContentsMargins(30, 30, 30, 30)  # Marge intérieure

        # --- 3. Titre général ---
        title_text = "Avoid Risks and Compliance issue in\na few clicks!"
        title_label = QLabel(title_text)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.ExtraBold))
        # Couleur de police très foncée pour le titre
        title_label.setStyleSheet("color: #1a1a1a;")
        guide_layout.addWidget(title_label)

        # --- 4. Sous-titre ---
        subtitle_text = "FortiFile onboarding will help you set up in just\n3 easy steps"
        subtitle_label = QLabel(subtitle_text)
        subtitle_label.setFont(QFont("Arial", 11))
        # Couleur de police gris foncé pour le sous-titre
        subtitle_label.setStyleSheet("color: #666666;")
        guide_layout.addWidget(subtitle_label)

        guide_layout.addSpacing(20)  # Espacement avant les étapes

        # --- 5. Les étapes de l'onboarding ---
        # Nous utilisons la nouvelle fonction en passant le statut de dernière étape (True/False)

        # Étape 1 (is_last_step=False)
        step1 = create_step_widget(1, "Select a folder", False)
        guide_layout.addWidget(step1)

        # Étape 2 (is_last_step=False)
        step2 = create_step_widget(2, "Launch the scan", False)
        guide_layout.addWidget(step2)

        # Étape 3 (is_last_step=True)
        step3 = create_step_widget(3, "Monitor events and review notifications ", True)
        guide_layout.addWidget(step3)

        # --- 6. Remplissage vertical pour centrer le contenu ou pousser le contenu vers le haut ---
        guide_layout.addStretch()


        right_layout.addWidget(guide_frame)
        right_layout.addStretch()


        # ------------------
        # Ajouter widgets au splitter
        # ------------------
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([700, 300])  # Ajuster la largeur initiale

        # Layout principal
        # ----------------------
        # Scroll Area pour tout le contenu
        # ----------------------
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: rgba(45, 55, 72, 0.1);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(74, 85, 104, 0.5);
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(74, 85, 104, 0.8);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        # Widget conteneur pour le scroll
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(splitter)

        scroll_area.setWidget(container_widget)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

        # Initialiser l'historique et le scan frame
        self.update_scan_history_display()
        self.create_scan_frame()

    def create_scan_frame(self):
        self.scan_frame = QFrame(self)
        self.scan_frame.setFixedSize(500, 500)  # Taille fixe
        self.scan_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                border: 2px solid #151B54;
            }
        """)
        self.scan_frame.setVisible(False)

        scan_layout = QVBoxLayout(self.scan_frame)
        scan_layout.setContentsMargins(30, 20, 30, 20)
        scan_layout.setSpacing(20)

        # ------------------ Title ------------------
        title_widget = QWidget()
        title_widget.setStyleSheet("background-color: white;")
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(15)

        back_btn = QPushButton()
        back_btn.setFixedSize(45, 45)
        back_btn.setFont(QFont("Segoe UI", 10))
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
        icon_pixmap = QPixmap(back_path).scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation)
        back_btn.setIcon(QIcon(icon_pixmap))
        back_btn.setIconSize(QSize(30, 30))
        back_btn.clicked.connect(self.hide_scan_frame)

        title_label = QLabel("Select folder to scan")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #151B54; background-color: white; border:none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_layout.addWidget(back_btn)
        title_layout.addWidget(title_label)
        scan_layout.addWidget(title_widget)

        # ------------------ Path widget ------------------
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(15)

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

        self.folder_btn = QPushButton("Browse folder")
        self.folder_btn.setFixedHeight(45)
        self.folder_btn.setMinimumWidth(150)
        self.folder_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
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

        # ------------------ Image & Status ------------------
        self.image_status_widget = QWidget()
        self.image_status_layout = QVBoxLayout(self.image_status_widget)
        self.image_status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_status_layout.setSpacing(25)
        self.image_status_widget.setStyleSheet("background-color: transparent; border:none;")

        # Image scan
        self.scan_image_label = QLabel()
        self.scan_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scan_image_label.setStyleSheet("background-color: transparent; border:none;")

        scan_pixmap = QPixmap(scan_path)
        if not scan_pixmap.isNull():
            scan_pixmap = scan_pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
            self.scan_image_label.setPixmap(scan_pixmap)
        else:
            self.scan_image_label.setText("🔄")
            self.scan_image_label.setStyleSheet("font-size: 100px;")

        # Bouton Scan
        self.scan_action_btn = QPushButton("Scan")
        self.scan_action_btn.setFixedSize(300, 45)
        self.scan_action_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
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

        # Scan completed
        self.scan_completed_label = QLabel("Data loaded successfully !")
        self.scan_completed_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.scan_completed_label.setStyleSheet("color: #059669; background-color: transparent; border:none;")
        self.scan_completed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scan_completed_label.setVisible(False)

        self.completed_image_label = QLabel()
        self.completed_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.completed_image_label.setStyleSheet("background-color: transparent; border:none;")
        self.completed_image_label.setVisible(False)

        completed_pixmap = QPixmap(completed_path)
        if not completed_pixmap.isNull():
            completed_pixmap = completed_pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                                       Qt.TransformationMode.SmoothTransformation)
            self.completed_image_label.setPixmap(completed_pixmap)
        else:
            self.completed_image_label.setText("✅")
            self.completed_image_label.setStyleSheet("font-size: 100px;")

        self.image_status_layout.addWidget(self.scan_image_label)
        self.image_status_layout.addWidget(self.scan_action_btn)
        self.image_status_layout.addWidget(self.completed_image_label)
        self.image_status_layout.addWidget(self.scan_completed_label)

        scan_layout.addWidget(self.image_status_widget)
        scan_layout.addStretch()

    def hide_scan_frame(self):
        self.scan_frame_visible = False
        self.scan_frame.hide()

        self.scan_image_label.setVisible(True)
        self.scan_action_btn.setVisible(True)
        self.completed_image_label.setVisible(False)
        self.scan_completed_label.setVisible(False)

        self.path_edit.clear()
        self.path_edit.setPlaceholderText("No selected folder")

    from PyQt6.QtCore import QTimer

    def create_graph_box(self):
        if self.is_dark_theme:
            bg_color = "#2B2B3C"
            text_color = "#EDEDED"
            chart_bg = "#2B2B3C"
        else:
            bg_color = "#FFFFFF"
            text_color = "#2E2E2E"
            chart_bg = "#FFFFFF"

        # Conteneur principal
        box = QWidget()
        box.setStyleSheet(f"background-color: {bg_color}; border-radius: 8px;")
        main_layout = QHBoxLayout(box)

        # ---------------------------------------------------------
        # 1) LÉGENDE
        # ---------------------------------------------------------
        legend_widget = QWidget()
        legend_layout = QVBoxLayout(legend_widget)

        legend_items = [
            ("#4A90E2", "New"),
            ("#F5A623", "Modified"),
            ("#D0021B", "Deleted"),
        ]

        for color, text in legend_items:
            item = QHBoxLayout()
            color_box = QLabel()
            color_box.setFixedSize(14, 14)
            color_box.setStyleSheet(f"background-color: {color}; border-radius: 3px;")

            label = QLabel(text)
            label.setStyleSheet(f"color: {text_color}; font-size: 13px; font-weight: bold; margin-left: 6px;")

            item.addWidget(color_box)
            item.addWidget(label)
            legend_layout.addLayout(item)

        main_layout.addWidget(legend_widget, alignment=Qt.AlignmentFlag.AlignLeft)

        # ---------------------------------------------------------
        # 2) GRAPH DONUT (fig + canvas stockés dans l'objet)
        # ---------------------------------------------------------
        self.graph_fig = Figure(figsize=(7, 7), facecolor=chart_bg)
        self.graph_ax = self.graph_fig.add_subplot(111)

        self.graph_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.graph_ax.axis("equal")
        self.graph_ax.set_facecolor(chart_bg)

        # Canvas
        self.graph_canvas = FigureCanvas(self.graph_fig)
        main_layout.addWidget(self.graph_canvas, alignment=Qt.AlignmentFlag.AlignRight)

        # ---------------------------------------------------------
        # 3) APPEL INITIAL + QTimer POUR LE REFRESH AUTOMATIQUE
        # ---------------------------------------------------------
        self.update_graph()  # première mise à jour

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(1500)  # rafraîchissement toutes les 1.5 secondes

        return box

    def update_graph(self):
        stats = get_dashboard_stats(username=load_current_user())
        new_files = stats.get("suspects_new", 0)
        modified_files = stats.get("suspects_modified", 0)
        deleted_files = stats.get("suspects_deleted", 0)

        values = [new_files, modified_files, deleted_files]
        colors = ["#4A90E2", "#F5A623", "#D0021B"]
        total = sum(values)

        # Clear l’ancien graphique
        self.graph_ax.clear()
        self.graph_ax.axis("auto")

        if total > 0:
            self.graph_ax.pie(values, colors=colors, startangle=90,
                              wedgeprops=dict(width=0.4))
            self.graph_ax.text(0, 0, str(total), ha='center', va='center',
                               color="#FFFFFF" if self.is_dark_theme else "#2E2E2E",
                               fontsize=20, fontweight='bold')
        else:
            self.graph_ax.pie([1], colors=["#B0BEC5"], startangle=90,
                              wedgeprops=dict(width=0.4))
            self.graph_ax.text(0, 0, "No Data", ha='center', va='center',
                               color="#FFFFFF" if self.is_dark_theme else "#2E2E2E",
                               fontsize=14, fontweight='bold')

        self.graph_canvas.draw()

    def on_auto_scan_toggled(self, checked):
        """Gère le changement d'état du switch Auto Scan"""
        if self.mode:
            self.mode = False
            return
        if checked:
            print("Auto scan activé - Analyse au démarrage de Windows activée")
            update_mode("auto")

        else:
            print("Auto scan désactivé - Analyse au démarrage de Windows désactivée")
            update_mode("manuel")
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Confirmation")
        msg_box.setText("Do you really want to restart the application?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        ret = msg_box.exec()

        if ret == QMessageBox.StandardButton.Ok:
            update_mode("none")
            # Quitter toute l'application
            try:
                # Lance une nouvelle instance du même script
                subprocess.Popen([sys.executable] + sys.argv)
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Cannot restart: {e}")
                # Ferme l’application actuelle
            QApplication.quit()
        else:
            # Cancel : ne fait rien, juste fermer la boîte de dialogue
            pass

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
                       background-color: white;
                       margin: 0px;
                       padding: 0px;
                       border: none;
                   }
                   QLabel {
                       color: #5D5898;
                       background-color: white;
                       margin: 0px;
                       padding: 0px;
                   }
               """)

    def apply_window_style(self):
        self.setStyleSheet("""
              QWidget {
               margin: 0px;
               padding: 0px;
               border: none;
               background-color: white;  /* <- couleur de fond blanche */
           }
           """)

    def center_scan_frame(self):
        if not hasattr(self, 'scan_frame') or self.scan_frame is None:
            return

        parent_size = self.size()
        frame_size = self.scan_frame.size()

        # Calcul de la position pour centrer
        x = (parent_size.width() - frame_size.width()) // 2
        y = (parent_size.height() - frame_size.height()) // 2

        self.scan_frame.move(x, y)


    def show_scan_frame(self):
        if not self.scan_frame_visible:
            self.scan_frame_visible = True
            self.center_scan_frame()
            self.scan_frame.show()
            self.scan_frame.raise_()

            self.path_edit.clear()
            self.path_edit.setPlaceholderText("No selected folder")
    def browse_folder(self):
        """Ouvre le dialogue de sélection de dossier"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select a folder to scan",
            ""
        )

        if folder_path:
            self.path_edit.setText(folder_path)

    def update_scan_history_display(self):
        """Met à jour l'affichage de l'historique à partir de get_user_history"""
        if not hasattr(self, 'history_content_layout'):
            print("Erreur: history_content_layout non initialisé")
            return

        # Vider l'ancien contenu
        for i in reversed(range(self.history_content_layout.count())):
            widget = self.history_content_layout.itemAt(i).widget()
            if widget:
                self.history_content_layout.removeWidget(widget)
                widget.deleteLater()

        self.history_items = []

        username = load_current_user()
        history_list = get_user_history(username, limit=10)
        print(get_user_history(username))  # récupère les 10 scans les plus récents

        if not history_list:
            # Ajouter le message "No scan history"
            no_history_label = QLabel("No scan history available")
            no_history_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_history_label.setFont(QFont("Segoe UI", 11))
            no_history_label.setStyleSheet("""
                   color: #525063; 
                   background-color: transparent; 
                   padding: 20px;
                   border: 1px solid #b2b3b8;
                   font-weight: bold;
               """)
            no_history_label.setMinimumHeight(100)
            self.history_content_layout.addWidget(no_history_label)
            return

        # Ajouter chaque scan à l'interface
        for scan in history_list:
            history_item = QFrame()
            history_item.setFixedHeight(60)
            history_item.setStyleSheet("""
                   QFrame {
                       background-color: white;
                       border-radius: 10px;
                       border: 1px solid #b2b3b8;
                   }
               """)

            item_layout = QHBoxLayout(history_item)
            item_layout.setContentsMargins(15,10,15,10)
            item_layout.setSpacing(15)

            # Icône de statut
            status_icon = QLabel()
            if scan.get("status") == "completed":
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
            info_layout.setSpacing(4)

            path = scan.get("status")
            display_path = path if len(path) < 60 else path[:37] + "..."
            path_label = QLabel(display_path)
            path_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
            path_label.setStyleSheet(
                "color: black; background-color: transparent; border: none; font-weight: bold;"
            )

            path_label.setToolTip(path)

            time_label = QLabel(scan.get("time", "Unknown datetime"))
            time_label.setFont(QFont("Segoe UI", 9))
            time_label.setStyleSheet("color: black; background-color: transparent;border:none;")

            info_layout.addWidget(path_label)
            info_layout.addWidget(time_label)

            item_layout.addWidget(status_icon)
            item_layout.addWidget(info_widget, 1)

            # Ajouter au début de la liste (le plus récent en premier)
            self.history_content_layout.insertWidget(0, history_item)
            self.history_items.insert(0, history_item)

    def start_scan(self):
        path = self.path_edit.text().strip()

        if not path:
            QMessageBox.warning(self, "Warning", "Please select a file or a folder to scan")
            return

        if not os.path.exists(path):
            QMessageBox.critical(self, "Erreur", "the path doesn't exist")
            return

        user = load_current_user()
        # Si ta fonction attend une liste :
        build_baseline_for_folder(path, user)
        # Mettre à jour l'affichage dans la carte bleue

        # self.add_scan_to_history(scan_info)

        self.scan_image_label.setVisible(False)
        self.scan_action_btn.setVisible(False)

        # Afficher l'image de complétion et le texte
        self.completed_image_label.setVisible(True)
        self.scan_completed_label.setVisible(True)


# ---------------- Main ----------------
if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = HomePage()
    window.setWindowTitle("About FortiFile")
    window.setGeometry(100, 100, 900, 650)
    window.show()
    sys.exit(app.exec())