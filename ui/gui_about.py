from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt
import os

from core.user_manager import load_current_user, get_email_by_username
from core.email_sender import send_custom_email

base_dir = os.path.dirname(os.path.abspath(__file__))
img_dir = os.path.join(base_dir, "../img")
gmail_path = os.path.abspath(os.path.join(img_dir, "gmail.png")).replace("\\", "/")


class AboutPage(QWidget):
    def __init__(self, username="User"):
        super().__init__()
        self.username = load_current_user().upper()
        self.is_dark_theme = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ---------------- Header ----------------
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addStretch(True)

        # Image
        self.image_label = QLabel()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(base_dir, "../img/informations.png")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap)
        else :
            print("nn")
        self.image_label.setFixedSize(40, 40)
        self.image_label.setScaledContents(True)
        header_layout.addWidget(self.image_label)

        header_layout.setSpacing(20)

        # Titre principal
        self.title_label = QLabel("ABOUT FORTIFILE")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("sans-serif", 30, QFont.Weight.ExtraBold)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("color: #151B54; letter-spacing: 2px;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch(True)
        main_layout.addWidget(header)

        # Sous-titre
        self.subTitle = QLabel(f"Welcome back {self.username}")
        self.subTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subTitle.setFont(QFont("sans-serif", 18, QFont.Weight.Bold))
        main_layout.addWidget(self.subTitle)

        # ---------------- Contenu défilant (Scroll Area) ----------------
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.setContentsMargins(50, 20, 50, 20)

        # Contenu HTML
        html_about = f"""
        <div style="font-family: 'Segoe UI', Roboto, Arial, sans-serif; background-color: transparent; padding: 12px; line-height: 1.5;">

          <h2 style="margin: 0 0 12px 0; font-size: 11pt;">
            FortiFile is a desktop application designed to protect your data
            by monitoring the integrity of your files and detecting any unauthorized changes.
          </h2>

          <h2 style="margin: 10px 0 6px 0; font-size: 12pt;">Key Features</h2>
          <ul style="margin: 0 0 12px 20px; font-size: 11pt;">
            <li>Real-time integrity monitoring</li>
            <li>Automatic alert notifications</li>
            <li>History of file modifications</li>
            <li>Modern and secure interface</li>
          </ul>

          <div style="margin-top: 10px; font-size: 11pt;">
            <h2 style="margin: 4px 0;"> <strong>Developed by:</strong></h2>

            <ul style="margin: 0 0 12px 20px; font-size: 11pt; list-style-type: none; padding: 0;">
              <li style="margin: 6px 0;">
                <img src="file:///{gmail_path}" width="18" height="18" style="vertical-align:middle; margin-right:6px;">
                <strong>Taha Hanaa Amira</strong> —
                <a href="mailto:hanaaamira9@gmail.com" style="text-decoration:none; color:black;">hanaaamira9@gmail.com</a>
              </li>
              <li style="margin: 6px 0;">
                <img src="file:///{gmail_path}" width="18" height="18" style="vertical-align:middle; margin-right:6px;">
                <strong>Taha Wahiba</strong> —
                <a href="mailto:hibataha787@gmail.com" style="text-decoration:none; color:black;">hibataha787@gmail.com</a>
              </li>
              <li style="margin: 6px 0;">
                <img src="file:///{gmail_path}" width="18" height="18" style="vertical-align:middle; margin-right:6px;">
                <strong>Benamara Marina Feriel Manel</strong> —
                <a href="mailto:benamaramarina@gmail.com" style="text-decoration:none; color:black;">benamaramarina@gmail.com</a>
              </li>
              <li style="margin: 6px 0;">
                <img src="file:///{gmail_path}" width="18" height="18" style="vertical-align:middle; margin-right:6px;">
                <strong>Melouk Romaissa Malek</strong> —
                <a href="mailto:meloukromaissamalek@gmail.com" style="text-decoration:none; color:black;">meloukromaissamalek@gmail.com</a>
              </li>
              <li style="margin: 6px 0;">
                <img src="file:///{gmail_path}" width="18" height="18" style="vertical-align:middle; margin-right:6px;">
                <strong>Fergani Aya</strong> —
                <a href="mailto:fergani2004aya@gmail.com" style="text-decoration:none; color:black;">fergani2004aya@gmail.com</a>
              </li>
            </ul>
            <h2 style="margin: 6px 0 0 0;">
              <strong>Version:</strong> 1.0.0 &nbsp;|&nbsp; Built with PyQt6 &amp; Python 3.11
            </h2>
          </div>
        </div>
        """

        about_label = QLabel()
        about_label.setText(html_about)
        about_label.setTextFormat(Qt.TextFormat.RichText)
        about_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        about_label.setOpenExternalLinks(True)
        about_label.setWordWrap(True)
        contactWidget = QWidget()
        contact_layout = QHBoxLayout(contactWidget)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "../img/gmail.png")
        self.img_label = QLabel()
        if os.path.exists(path):
            pixmap = QPixmap(path)
            self.img_label.setPixmap(pixmap)
        self.img_label.setFixedSize(30, 30)
        self.img_label.setScaledContents(True)
        self.contactLabel = QLabel("Contact us : fortifile.app@gmail.com")
        self.contactLabel.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: black;
                border: 2px solid #4a90e2;
                border-radius: 8px;
                padding: 8px 15px;
                background-color: #f5f7fa;
                transition: all 0.3s ease;
            }
            QLabel:hover {
                background-color: #4a90e2;
                color: white;
                border: 2px solid #357ABD;
            }
            QLabel:pressed {
                background-color: #2c5aa0;
                color: white;
            }
        """)

        self.contactLabel.mouseDoubleClickEvent = self.show_window
        contact_layout.addWidget(self.img_label)
        contact_layout.addWidget(self.contactLabel)
        contact_layout.addStretch(True)
        content_layout.addWidget(about_label)
        content_layout.addWidget(contactWidget)


        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        scroll_area.setStyleSheet("""
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

    def show_window(self, event):
        """Ouvre la fenêtre d'envoi"""
        self.msg_window = ShowWindow(is_dark_theme=False)
        self.msg_window.show()


class ShowWindow(QWidget):
    def __init__(self,  is_dark_theme=False, parent=None):
        super().__init__(parent)


        self.is_dark_theme = is_dark_theme
        self.setFixedSize(550, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setStyleSheet("""
            border: 2px solid #0078D7;
            border-radius: 10px;
        """)

        # --- Layout principal ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header.setStyleSheet("border: none;")
        self.back_btn = QPushButton("← Back")
        self.back_btn.setObjectName("back_btn")
        self.back_btn.setStyleSheet("""
                    QPushButton#back_btn {
                        background-color: #f5f5f5;
                        color: #151B54;
                        border: 2px solid #a0c4ff;
                        border-radius: 12px;
                        padding: 8px 15px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton#back_btn:hover {
                        background-color: #d0e0ff;
                        border-color: #4a90e2;
                        color: #0d1b2a;
                    }
                    QPushButton#back_btn:pressed {
                        background-color: #a0c4ff;
                        border-color: #1e3a8a;
                    }
                """)
        self.back_btn.clicked.connect(self.close)
        header_layout.addWidget(self.back_btn)
        header_layout.addStretch(True)
        layout.addWidget(header)

        # --- Image de profil ---
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("Type your message here...")
        self.message_edit.setFixedHeight(300)
        layout.addWidget(self.message_edit)
        self.message_edit.setStyleSheet("border: none;")
        send_btn = QPushButton("Send Message")
        send_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #4a90e2;
                            color: white;
                            border-radius: 10px;
                            padding: 8px 15px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #357ABD;
                        }
                    """)
        layout.addWidget(send_btn)
        send_btn.clicked.connect(self.send_message)

    def send_message(self):
        message = self.message_edit.toPlainText().strip()
        print(message)
        if not message:
            QMessageBox.warning(self, "Warning", "Please enter a message!")
            return

        try:
            user = load_current_user()
            print(user)
            print(get_email_by_username(user))
            success = send_custom_email(user, get_email_by_username(user), message)
            if success:
                QMessageBox.information(self, "Success", "Your message has been sent!")
                self.message_edit.clear()
            else:
                QMessageBox.critical(self, "Error", "Failed to send your message.")
        except Exception as e:
            print("Exception in send_message:", e)
            QMessageBox.critical(self, "Error", f"Failed to send message:\n{e}")




    def showEvent(self, event):
        """Centrer la fenêtre une fois qu'elle est visible."""
        super().showEvent(event)
        self.center_window()

    def center_window(self):
        """Centre la fenêtre par rapport à la fenêtre parente (Home/MainWindow)."""
        if self.parent():
            # Obtenir la géométrie du parent
            parent_geometry = self.parent().frameGeometry()
            parent_center = parent_geometry.center()

            # Calculer la position pour centrer
            x = parent_center.x() - self.width() // 2
            y = parent_center.y() - self.height() // 2

            self.move(x, y)
        else:
            # Si aucun parent → fallback sur le centrage écran
            screen = self.screen().availableGeometry()
            x = screen.center().x() - self.width() // 2
            y = screen.center().y() - self.height() // 2
            self.move(x, y)



# ---------------- Main ----------------
if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = AboutPage()
    window.setWindowTitle("About FortiFile")
    window.setGeometry(100, 100, 900, 650)
    window.show()
    sys.exit(app.exec())