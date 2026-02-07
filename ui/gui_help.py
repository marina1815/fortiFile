
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QPixmap , QIcon
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve ,QSize
import os

from core.user_manager import load_current_user, get_email_by_username
from core.email_sender import send_custom_email
basee_dir = os.path.dirname(os.path.abspath(__file__))
back_path = os.path.join(basee_dir, "../img/back.png")
base_dir = os.path.dirname(os.path.abspath(__file__))
img_dir = os.path.join(base_dir, "../img")
gmail_path = os.path.abspath(os.path.join(img_dir, "gmail.png")).replace("\\", "/")
python_path = os.path.abspath(os.path.join(img_dir, "python.png")).replace("\\", "/")
pycharm_path = os.path.abspath(os.path.join(img_dir, "pycharm.png")).replace("\\", "/")
pyqt6_path = os.path.abspath(os.path.join(img_dir, "pyqt6.png")).replace("\\", "/")
sqlLite_path = os.path.abspath(os.path.join(img_dir, "sqlLite.png")).replace("\\", "/")
vs_path = os.path.abspath(os.path.join(img_dir, "VS.png")).replace("\\", "/")
github_path = os.path.abspath(os.path.join(img_dir, "github.png")).replace("\\", "/")
img1_path = os.path.abspath(os.path.join(img_dir, "autoScan.png")).replace("\\", "/")
img2_path = os.path.abspath(os.path.join(img_dir, "autoSca.png")).replace("\\", "/")



# ---------- Carte de titre ----------
class TitleCard(QFrame):
    def __init__(self, title, icon="❓", parent=None):
        super().__init__(parent)
        self.title = title

        self.setObjectName("title_card")
        self.setStyleSheet("""
            QFrame#title_card {
                background-color: #f5f5f5;
                border-radius: 20px;
                border: 1px solid #ddd;
                padding: 20px;
            }
            QFrame#title_card:hover {
                background-color: #e8f0fe;
                border: 1px solid #a0c4ff;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(self.title_label)

        self.anim = None

    # Animation hover
    def enterEvent(self, event):
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(150)
        self.anim.setEndValue(self.geometry().adjusted(-5, -5, 5, 5))
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(150)
        self.anim.setEndValue(self.geometry().adjusted(5, 5, -5, -5))
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.start()
        super().leaveEvent(event)


from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QTextEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class DetailFrame(QFrame):
    def __init__(self, title, question, answer, parent=None):
        super().__init__(parent)
        self.setObjectName("detail_frame")
        self.setStyleSheet("""
            QFrame#detail_frame {
                background-color: #ffffff;
                border-radius: 15px;
                padding: 20px;
            }
            QLabel#content_label {
                font-family: 'Segoe UI', sans-serif;
                color: #333333;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # ---------------- Question ----------------
        q_label = QLabel(f"{question}")
        q_label.setWordWrap(True)
        q_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        q_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        q_label.setStyleSheet("""
            color: #444444;
            margin: 5px 0 20px 0;
        """)
        layout.addWidget(q_label)

        # ---------------- Réponse HTML ----------------
        if title != "SUPPORT":
            html_content = f"""
            <div style='line-height:1.5; font-size:12pt; color:#333333;'>{answer}</div>
            """
            a_label = QLabel()
            a_label.setObjectName("content_label")
            a_label.setText(html_content)
            a_label.setWordWrap(True)
            a_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            a_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(a_label)

        # ---------------- Section SUPPORT ----------------
        if title == "SUPPORT":
            # Label email
            email_label = QLabel(f"<img src='file:///{gmail_path}' width='40' height='40'> Email: <b>fortifile.app@gmail.com</b>")
            email_label.setTextFormat(Qt.TextFormat.RichText)
            email_label.setStyleSheet("font-size: 15pt;")
            email_label.setWordWrap(True)
            layout.addWidget(email_label)

            # Zone de texte pour message
            self.message_edit = QTextEdit()
            self.message_edit.setPlaceholderText("Type your message here...")
            self.message_edit.setFixedHeight(200)
            layout.addWidget(self.message_edit)

            # Bouton envoyer
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

            # Connexion du bouton
            send_btn.clicked.connect(self.send_message)

        layout.addStretch(True)

    # ---------------- Fonction pour envoyer message ----------------
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
            success = send_custom_email(user,get_email_by_username(user),message)
            if success:
                QMessageBox.information(self, "Success", "Your message has been sent!")
                self.message_edit.clear()
            else:
                QMessageBox.critical(self, "Error", "Failed to send your message.")
        except Exception as e:
            print("Exception in send_message:", e)
            QMessageBox.critical(self, "Error", f"Failed to send message:\n{e}")


# ---------- Main Window ----------
class HelpPage(QWidget):
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
        self.back_btn.setVisible(False)  # invisible au départ
        header_layout.addWidget(self.back_btn)

        header_layout.addStretch(True)

        # Image
        image_label = QLabel()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(base_dir, "../img/robot.png")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            image_label.setPixmap(pixmap)
        image_label.setFixedSize(40, 40)
        image_label.setScaledContents(True)
        header_layout.addWidget(image_label)

        header_layout.setSpacing(20)

        # Titre principal
        self.title_label = QLabel("HELP CENTER")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("sans-serif", 30, QFont.Weight.ExtraBold)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("color: #151B54; letter-spacing: 2px;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch(True)
        main_layout.addWidget(header)

        self.subTitle = QLabel(f"Welcome back {self.username}")
        self.subTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)  # centrer le texte
        self.subTitle.setFont(QFont("sans-serif", 18, QFont.Weight.Bold))  # taille 14, gras

        # Sous-titre secondaire
        self.subTitle2 = QLabel("Need help ❓ We are here for you .")
        self.subTitle2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subTitle2.setFont(QFont("sans-serif", 14))
        main_layout.addWidget(self.subTitle)
        main_layout.addWidget(self.subTitle2)

        # ---------------- Stack ----------------
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # ---------------- Page cartes ----------------
        self.cards_page = QWidget()
        grid_layout = QGridLayout(self.cards_page)
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(20, 20, 20, 20)

        # Sections FAQ
        self.sections = [
            ("GETTING STARTED",
             "Forti File is a File Integrity Monitoring application that helps you protect sensitive files, track changes, and manage user permissions easily.",
             f"""
             <h1>How to use?</h1>
             <ol>
                 <li>Create a User Account</li>
                 <li>Navigate to Scan</li>
                 <li>Select files</li>
                 <li>Scan Selected</li>
                 <li>Check Dashboard</li>
             </ol>

             <h1>Details</h1>

             <h2>Create a User Account</h2>
             <ul>
                 <li>On first launch, create a new user account by providing your email, username, and password.</li>
                 <li>Verify your account by entering the confirmation code sent to your email.</li>
                 <li>After verification, you will be logged in and redirected to the Home page.</li>
             </ul>

             <h2>Log In</h2>
             <ul>
                 <li>Enter your registered email and password to access the application.</li>
                 <li>If you forget your password, use the “Forgot Password” option to reset it via email.</li>
             </ul>

             <h2>Add Files or Folders to Protect</h2>
             <ul>
                 <li>Navigate to the Scan page and click <strong>"Add File/Folder"</strong>.</li>
                 <li>Select the files or folders you want to secure.</li>
                 <li><strong>Note:</strong> The user who adds a file or folder becomes its <strong>Administrator</strong> by default.</li>
                 <li>Set the access permissions for other users:
                     <ul>
                         <li><strong>Administrator:</strong> Full access, including modify, delete, and rename.</li>
                         <li><strong>Normal User:</strong> Read-only access.</li>
                     </ul>
                 </li>
                 <li>Click <strong>Save</strong> to confirm.</li>
             </ul>

             <h2>Monitoring and Notifications</h2>
             <ul>
                 <li>Forti File continuously monitors your selected files and folders for any changes.</li>
                 <li>All actions are logged automatically, including modifications, deletions, and access attempts.</li>
                 <li>Notifications appear for any unauthorized or suspicious activity.</li>
             </ul>

             <h2>Restore a File</h2>
             <ul>
                 <li>If a file is modified or deleted, select it from the Log or Events page.</li>
                 <li>Click <strong>Restore</strong> to revert the file back to its baseline state.</li>
                 <li>All restorations are logged for audit purposes.</li>
             </ul>

             <h2>Advanced Settings</h2>
             <ul>
                 <li>Access the Settings page to configure application preferences:</li>
                 <ul>
                     <li>Change the interface theme (light or dark).</li>
                     <li>Configure notifications for specific events.</li>
                     <li>Manage user roles and permissions (Admin only).</li>
                     <li>Set the frequency of automatic scans.</li>
                 </ul>
             </ul>

             <h2>Viewing Logs and Events</h2>
             <ul>
                 <li>Access the Log file to view all recorded actions with timestamps and user details.</li>
                 <li>The Events page provides detailed information about each detected change, including alerts for blocked access or unauthorized modifications.</li>
             </ul>
             """, ""),

            ("USING FortiFile", "With Forti File, users can:",
             f"""
             <ul>
                 <li>Monitor files and folders in real-time for unauthorized changes, deletions, or access attempts.</li>
                 <li>View a comprehensive dashboard showing file activity, modification history, and visual graphs or histograms.</li>
                 <li>Perform scans manually or automatically, ensuring files are always protected.</li>
                 <li>Manage events and logs to track all actions, filter notifications, and quickly respond to alerts.</li>
                 <li>Restore altered files automatically if changes are unauthorized.</li>
                 <li>Assign and manage user roles, distinguishing between Administrators (full access), Standard Users (read-only), and Guests (read and write but without permission to create roles or change user privileges).</li>
                 <li>Customize settings, including scan frequency, notification preferences, themes, and personal account information.</li>
             </ul>
             <p>This section is intended for users who want to master the application, understand all functionalities, and effectively secure their files.</p>
             """, ""),
            ("AUTO SCAN", "How to Enable AutoScan and Configure Automatic Startup Using Task Scheduler",
             f"""
                            <div style="font-family: 'Segoe UI'; font-size:14pt; color:#333; line-height:1.5;">

            <p>
                FortiFile provides an option to start the application automatically when Windows boots.
                If you select <b>Auto Mode</b>, the system will open the Task Scheduler window to configure this behavior.
            </p>

            <h2  style="color:green; font-weight:bold;">Steps to Enable Automatic Startup:</h2>

            <p><b>1. Enable Auto Mode in FortiFile</b><br>
                In the application settings, choose the option to start FortiFile automatically at system startup.<br>
                When this option is selected, Windows will automatically open the Task Scheduler.
            </p>

            <p style="overflow:hidden;">
                <img src="file:///{img1_path}" width="420" style="float:right; margin-left:20px; border:1px solid #ccc;">
                <b>2. Open Task Scheduler Library</b><br>
                In the Task Scheduler window, navigate to the left panel and click on:<br>
                <b>Task Scheduler Library</b><br>
            </p>

            <p>
                <b>3. Locate the FortiFile Task</b><br>
                Inside the library, you should see a scheduled task named:<br>
                <b>FortiFileApp</b><br>
                Select this task to view its details.
            </p>
            <p>
                <b>4. Run the Startup Task</b><br>
                After selecting <b>FortiFileApp</b>, click on <b>Run</b> to test the startup process and ensure that the task is correctly configured.
                <br><br>

            </p>


        </div>
        <div>
            <h2 style="color:red; font-weight:bold;">⚠️Important Note</h2>
            <p  style= "font-weight:bold;">
                Even with automatic startup enabled, you will still need to authenticate yourself each time Windows starts.
                This is a security requirement to ensure that only authorized users can access FortiFile.
            </p>

        </div>
                            """, ""),
            ("ACCOUNT SETTINGS", "You can manage your account settings at any time.",
             """
             <p>You have multiple ways to access and modify your account information:</p>
             <ul>
                 <li><strong>Quick Access:</strong> Click the user profile or settings icon in the top-right header to access account settings quickly.</li>
                 <li><strong>Settings Page:</strong> Navigate to the Settings section for full account management options.</li>
             </ul>
             <h2>With your personal information settings, you can update:</h2>
             <ul>
                 <li>Username</li>
                 <li>Email address</li>
                 <li>Password</li>
                 <li>Profile photo</li>
                 <li>Date of birth</li>
             </ul>
             <p>Additionally, you can assign a user as an <strong>Administrator</strong> for your account if needed, giving them elevated access to manage certain features.</p>
             """, ""),

            ("FAQ", "Common Questions",
             """
             <h2>Account & Login</h2>
             <ul>
                 <li><strong>Q:</strong> How do I reset my password?<br><strong>A:</strong> Use the “Forgot Password” link on the login page. A reset code will be sent to your registered email.</li>
                 <li><strong>Q:</strong> Can I change my email or username?<br><strong>A:</strong> Yes, go to the Settings page or use Quick Access from the header to modify your personal information.</li>
                 <li><strong>Q:</strong> What is a legacy contact or administrator?<br><strong>A:</strong> An administrator has full access to manage files and roles. A legacy contact is a trusted user you can assign for account management.</li>
             </ul>

             <h2>File & Folder Protection</h2>
             <ul>
                 <li><strong>Q:</strong> How do I add a new file or folder to monitor?<br><strong>A:</strong> Go to the Scan page, click “Add File” or “Add Folder”, select the item, set permissions, and click Save.</li>
                 <li><strong>Q:</strong> Who becomes the Admin of a file/folder?<br><strong>A:</strong> The user who adds the file/folder is automatically assigned as the Admin by default.</li>
                 <li><strong>Q:</strong> Can I remove a file from monitoring?<br><strong>A:</strong> Yes, select the file/folder in the Scan page and click “Remove” or reset the baseline.</li>
             </ul>

             <h2>Monitoring & Logs</h2>
             <ul>
                 <li><strong>Q:</strong> How does Forti File detect changes?<br><strong>A:</strong> It monitors files against their baseline state in real-time or during scheduled scans. Any unauthorized changes are logged.</li>
                 <li><strong>Q:</strong> What types of events are recorded?<br><strong>A:</strong> Alerts, Warnings, and Informational events are logged in the Events and Logs pages.</li>
                 <li><strong>Q:</strong> Can I filter or export logs?<br><strong>A:</strong> Yes, logs can be filtered by type, date, or user, and exported for auditing purposes.</li>
             </ul>

             <h2>Restoring Files</h2>
             <ul>
                 <li><strong>Q:</strong> What happens if a file is modified or deleted without authorization?<br><strong>A:</strong> Forti File automatically restores it to its baseline state. Admins can also manually restore files from the Log or Events panel.</li>
             </ul>

             <h2>Settings & Roles</h2>
             <ul>
                 <li><strong>Q:</strong> How do I change user roles?<br><strong>A:</strong> Only Administrators can modify roles via the Settings page.</li>
                 <li><strong>Q:</strong> Can I customize notifications or scan frequency?<br><strong>A:</strong> Yes, these options are available in the Settings page under Scan and Notifications.</li>
             </ul>

             <h2>Troubleshooting</h2>
             <ul>
                 <li><strong>Q:</strong> I don’t see my file in the Scan page. What should I do?<br><strong>A:</strong> Ensure the file is not excluded and that the baseline has been updated. Click “Reset” to refresh all selections.</li>
                 <li><strong>Q:</strong> I receive repeated alerts for the same file.<br><strong>A:</strong> This may happen if the file keeps changing outside of allowed actions. Check permissions and file integrity.</li>
                 <li><strong>Q:</strong> How do I contact support?<br><strong>A:</strong> Use the Help section in the app or contact the support team via your registered email.</li>
             </ul>
             """, ""),

            ("TOOLS & TECHNOLOGIES", "Overview of tools, frameworks, and technologies used in the project.",
             f"""
             <h2>1. Programming Languages</h2>
             <p><img src="file:///{python_path}" width="20" height="20"> <b>Python 3.11+</b>: Core language for application logic.</p>

             <h2>2. GUI Framework</h2>
             <p><img src="file:///{pyqt6_path}" width="20" height="20"> <b>PyQt6</b>: Used for building the desktop interface with modern widgets and layouts.</p>

             <h2>3. Database</h2>
             <p><img src="file:///{sqlLite_path}" width="20" height="20"> <b>SQLite / JSON</b>: Storage of user data and application state.</p>

             <h2>4. Security & Monitoring</h2>
             <p><b>File Integrity Monitoring</b>: Detect file changes and user activity.<br>
             <b>Hashing Algorithms (SHA-256)</b>: Ensure file authenticity.</p>

             <h2>5. Development Tools</h2>
             <p><img src="file:///{pycharm_path}" width="20" height="20"> <b>PyCharm</b>: IDE for coding.</p>
             <p><img src="file:///{vs_path}" width="20" height="20"> <b>VSCode</b>: IDE for coding.</p>
             <p><img src="file:///{github_path}" width="20" height="20"> <b>Git & GitHub</b>: Version control.</p>
             """, ""),


            ("SUPPORT", "Contact us",
             f"""
             <div style="font-family: 'Segoe UI'; font-size:14pt; color:#333;">
                 <p><img src='file:///{gmail_path}' width='40' height='40'> Email: <b>fortifile.app@gmail.com</b></p>
                 <p><textarea rows="4" cols="40" placeholder="Type your message here..."></textarea></p>
                 <p><button>Send Message</button></p>
             </div>
             """, "")
        ]

        self.cards = []
        for i, (title, question, answer, icon) in enumerate(self.sections):
            card = TitleCard(title, icon)
            self.cards.append(card)
            row, col = divmod(i, 3)
            grid_layout.addWidget(card, row, col)
            card.mousePressEvent = lambda e, t=title, q=question, a=answer: self.show_detail(t, q, a)

        self.stack.addWidget(self.cards_page)

        # Connexion du back button
        self.back_btn.clicked.connect(lambda: self.back_to_cards())

    # ---------------- Afficher le détail ----------------
    def show_detail(self, title, question, answer):
        self.back_btn.setVisible(True)
        self.subTitle.setText('')
        self.subTitle2.setText('')
        # montrer le back
        self.title_label.setText(title)          # changer le titre

        detail_frame = DetailFrame(title, question, answer)
        detail_frame.setObjectName("detail_frame")
        scroll = QScrollArea()
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
        scroll.setWidgetResizable(True)
        scroll.setWidget(detail_frame)
        self.stack.addWidget(scroll)
        self.stack.setCurrentWidget(scroll)

    # ---------------- Retour aux cartes ----------------
    def back_to_cards(self):
        self.stack.setCurrentWidget(self.cards_page)
        # Supprime les pages détail restantes pour libérer la mémoire
        for i in range(self.stack.count() - 1, 0, -1):
            widget = self.stack.widget(i)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self.back_btn.setVisible(False)
        self.subTitle.setText(f"Welcome back {self.username}")
        self.subTitle2.setText("Need help ❓ We are here for you .")
        self.title_label.setText("HELP CENTER")


# ---------------- Main ----------------
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = HelpPage()
    window.setWindowTitle("Dynamic Help / FAQ")
    window.setGeometry(100, 100, 900, 650)
    window.show()
    sys.exit(app.exec())