from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QFileDialog, QMessageBox, QGridLayout, QDateEdit
)
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt, QSize, QDate, pyqtSignal
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor


from core.user_manager import (
    load_current_user, get_email_by_username, get_hashed_password_by_username,
    get_date_of_birth_by_username, edit_user, hash_password, list_users, ensure_profile_file, get_user_photo
)
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
user = load_current_user()
photo_path = get_user_photo(user)
if photo_path:
    profil_path = os.path.normpath(photo_path)
else:

    profil_path = os.path.join(base_dir, "../img/profile.png")

edit_path = os.path.join(base_dir,"../img/edit.png")
save_path = os.path.join(base_dir,"../img/save.png")



class EditProfileWindow(QWidget):
    profile_updated = pyqtSignal(str, str)  # username, email

    def __init__(self, username="", email="", password="", is_dark_theme=False, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Edit Profile")
        self.setFixedSize(450, 500)
        self.is_dark_theme = is_dark_theme
        # Ajouter ces lignes pour forcer un fond opaque
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        # Charger la police
        # Charger la police
        font_id = QFontDatabase.addApplicationFont("fonts/Poppins-Bold.ttf")
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                poppins_font = font_families[0]
                print(f"Police chargée : {poppins_font}")
            else:
                poppins_font = "Poppins"  # ou un fallback
        else:
            poppins_font = "Arial"  # fallback si le chargement échoue

        # --- Layout principal ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Image de profil ---
        self.profile_label = QLabel()
        self.profile_label.setFixedSize(100, 100)
        self.profile_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_rounded_pixmap(profil_path)

        self.profile_label.setStyleSheet("border-radius: 50px;")

        self.change_pic_btn = QPushButton("Change Picture")
        self.change_pic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.change_pic_btn.setStyleSheet("background: transparent; border: none; color: #2B6CB0;")
        self.change_pic_btn.clicked.connect(self.change_picture)

        pic_layout = QVBoxLayout()
        pic_layout.addWidget(self.profile_label, alignment=Qt.AlignmentFlag.AlignCenter)
        pic_layout.addWidget(self.change_pic_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Champs d'édition avec disposition horizontale ---
        # Utilisation d'un QGridLayout pour aligner les labels et champs
        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(15)  # Espacement entre label et champ
        form_layout.setVerticalSpacing(15)  # Espacement entre les lignes

        # Username
        self.username = load_current_user()
        username_label = QLabel("Username:")
        self.username_input = QLineEdit(username)
        self.username_input.setPlaceholderText("Enter new username")
        self.username_input.setFixedHeight(35)
        self.username_input.setReadOnly(True)
        form_layout.addWidget(username_label, 0, 0)
        form_layout.addWidget(self.username_input, 0, 1)

        # Email
        email_label = QLabel("Email:")
        self.email_input = QLineEdit(email)
        self.email_input.setPlaceholderText("Enter new email")
        self.email_input.setFixedHeight(35)
        self.email_input.setReadOnly(True)
        form_layout.addWidget(email_label, 1, 0)
        form_layout.addWidget(self.email_input, 1, 1)

        # Date of Birth
        dob_label = QLabel("Date of Birth:")
        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDisplayFormat("yyyy-MM-dd")
        self.dob_input.setFixedHeight(37)
        self.dob_input.setReadOnly(True)
        form_layout.addWidget(dob_label, 2, 0)
        form_layout.addWidget(self.dob_input, 2, 1)
        # Charger la date depuis la base
        dob_str = get_date_of_birth_by_username(self.username)
        if dob_str and dob_str != "N/A":
            try:
                year, month, day = map(int, dob_str.split("-"))
                self.dob_input.setDate(QDate(year, month, day))
            except ValueError:
                self.dob_input.setDate(QDate(2000, 1, 1))
        else:
            self.dob_input.setDate(QDate(2000, 1, 1))

        self.username_input.setFixedHeight(37)  # ← DE 35 À 50
        self.email_input.setFixedHeight(37)  # ← DE 35 À 50
        self.dob_input.setFixedHeight(37)

        # Définir la largeur des colonnes
        form_layout.setColumnStretch(0, 0)  # Colonne labels - pas d'expansion
        form_layout.setColumnStretch(1, 1)  # Colonne champs - expansion maximale

        # --- Boutons ---
        self.save_btn = QPushButton("Edit")
        self.save_btn.setIcon(QIcon(save_path))
        self.save_btn.setIconSize(QSize(16, 16))
        self.save_btn.setFixedHeight(40)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self.handle_save_click)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.close)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)

        # --- Ajouter tous les éléments ---
        layout.addLayout(pic_layout)
        layout.addLayout(form_layout)  # Ajouter le formulaire au lieu des widgets individuels
        layout.addStretch()
        layout.addLayout(buttons_layout)

        # --- Appliquer le thème ---
        self.apply_theme()

        # --- Appliquer l'effet d'ombre ---
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(50)
        shadow_effect.setColor(QColor("#6A76E8"))  # Bleu avec opacité
        shadow_effect.setOffset(0, 0)
        self.setGraphicsEffect(shadow_effect)

    def handle_save_click(self):
        if self.save_btn.text() == "Edit":
            # Passer en mode édition
            self.username_input.setReadOnly(False)
            self.email_input.setReadOnly(False)
            self.dob_input.setReadOnly(False)

            self.save_btn.setText("Save")
            self.save_btn.setIcon(QIcon(save_path))
        else:
            # Sauvegarder les modifications
            try:
                QMessageBox.information(self, "Success", "Profile updated successfully!")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update profile:\n{str(e)}")

    def finish_edit_mode(self):
        """Revient en mode lecture après enregistrement."""
        self.username_input.setReadOnly(True)
        self.email_input.setReadOnly(True)
        self.dob_input.setReadOnly(True)

        self.save_btn.setText("Edit")
        self.save_btn.setIcon(QIcon(edit_path))

    def toggle_edit_mode(self):
        if self.save_btn.text() == "Edit":
            # Passer en mode édition
            self.username_input.setReadOnly(False)
            self.email_input.setReadOnly(False)
            self.dob_input.setReadOnly(False)

            self.save_btn.setText("Save")
            self.save_btn.setIcon(QIcon(save_path))
            self.cancel_btn.show()

        else:
            # Sauvegarder les modifications
            new_username = self.username_input.text().strip()
            new_email = self.email_input.text().strip()
            dob = self.dob_input.date().toString("yyyy-MM-dd")

            # Mise à jour dans la base
            edit_user(new_username, new_email, None, dob)

            QMessageBox.information(self, "Success", "Profile updated successfully!")

            # Revenir en mode lecture
            self.username = new_username
            self.finish_edit_mode()

    def set_rounded_pixmap(self, image_path):
        """Crée et applique un QPixmap circulaire à partir d'une image."""
        pixmap = QPixmap(image_path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                            Qt.TransformationMode.SmoothTransformation)
        size = min(pixmap.width(), pixmap.height())
        rounded = QPixmap(size, size)
        rounded.fill(Qt.GlobalColor.transparent)

        # Dessiner un cercle masqué
        from PyQt6.QtGui import QPainter, QBrush, QPainterPath

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        self.profile_label.setPixmap(rounded)

    def change_picture(self):
        """Ouvre un sélecteur de fichier pour changer la photo de profil"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Profile Picture", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.set_rounded_pixmap(file_path)
            username = load_current_user()
            ensure_profile_file(username ,file_path)


    def save_changes(self):
        """Enregistre les modifications et ferme la fenêtre"""
        new_username = self.username_input.text().strip()
        new_email = self.email_input.text().strip()
        current_password = self.password_input.text().strip()
        new_password = self.new_password_input.text().strip()
        confirm_password = self.confirm_new_password_input.text().strip()

        if not new_username or not new_email:
            QMessageBox.warning(self, "Error", "Please fill in username and email fields.")
            return

        # Vérification des mots de passe si modification
        if new_password or confirm_password:
            if not current_password:
                QMessageBox.warning(self, "Error", "Please enter your current password to change it.")
                return

            if new_password != confirm_password:
                QMessageBox.warning(self, "Error", "New passwords do not match.")
                return

        QMessageBox.information(self, "Profile Updated", "Profile updated successfully!")
        # Ici, tu peux notifier le parent ou sauvegarder dans une base de données
        self.close()

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

    def apply_theme(self):
        """Thème clair/sombre"""
        if self.is_dark_theme:
            self.setStyleSheet("""
                QWidget {
                    border-radius:30px;
                    background-color: #141313;
                    color: #E2E8F0;
                }

                QLineEdit {

                    border: 2px solid #0E2B51;
                    border-radius: 10px;
                    padding-left: 8px;
                    color: #E2E8F0;

                }
                QLineEdit:focus { background-color: rgba(255,255,255,0.11);border: 3px solid #0E2B51; }
                   QPushButton#blueButton:hover {
            background-color: #120A37;
        }
             QDateEdit{
               border: 2px solid #0E2B51;
                    border-radius: 10px;
                    padding-left: 8px;
                    color: #E2E8F0;





                 }
                     QDateEdit:focus {
        border: 2px solid #0E2B51;
    }
    QDateEdit::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid #D6D9F5
    }

                QPushButton {
                    background-color:  #0E2B51;
                    color: white;
                    border-radius: 6px;
                    font-weight: bold;
                     border-radius:20px;
                }

                QLabel {
                    color: #E6E6E6;
                    font-weight: bold;
                      font-family:{self.poppins_font};
                      font-size:15px;

                }
            """)

            change_pic_btn_style = """
                           QPushButton {
                               background-color: transparent;
                               border: none;
                               color: #63B3ED;
                               font-weight: bold;
                               border-radius=30px;
                           }
                           QPushButton:hover {


                           }
                       """
            cancel_btn_style = """
                                        QPushButton {
                                        background-color:  transparent;
                                        color: white;
                                        border:3px solid #0E2B51;
                                        font-weight: bold;
                                         border-radius:20px;
                                    }
                                      QPushButton:hover {
                                      background-color: rgba(255,255,255,0.11);

                           }
                                    """

            self.change_pic_btn.setStyleSheet(change_pic_btn_style)
            self.cancel_btn.setStyleSheet(cancel_btn_style)

        else:

            self.setStyleSheet("""
                QWidget {


                    background-color: #F7F7FD;
                    border-radius:30px;
                }
                QLineEdit {
                    background-color: #D6D9F5;
                    color: black;
                    border: 2px solid #151B54;
                    border-radius: 10px;
                    padding-left: 8px;
                }
                    QDateEdit{
                    background-color: #D6D9F5;
                    color: black;
                    border: 2px solid #151B54;
                    border-radius: 10px;
                    padding-left: 8px;

                 }
                     QDateEdit:focus {
        border: 2px solid #3342CC;
    }
    QDateEdit::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid #D6D9F5
    }
                QPushButton {
                    background-color: #151B54;
                    color: white;
                    border-radius: 6px;
                    font-family:{self.poppins_font};
                    font-weight: bold;
                    border-radius:20px;

                }
                QPushButton:hover {

                }
                QLabel {
                    color: #151B54;
                    font-weight: bold;
                    font-family:{self.poppins_font};
                    font-size:15px;


                }
            """)

            change_pic_btn_style = """
                            QPushButton {
                                background-color: transparent;
                                border: none;
                                color: #151B54;
                                font-weight: bold;
                                border-radius=30px;
                            }
                            QPushButton:hover {

                                text-decoration: underline;
                            }
                        """
            cancel_btn_style = """
                            QPushButton {
                            background-color:  transparent;
                            color: #151B54;
                            border:3px solid #151B54;
                            font-weight: bold;
                             border-radius:20px;
                        }
                                        QPushButton:hover {
                                      background-color: rgba(255,255,255,0.11);

                           }
                        """

            self.change_pic_btn.setStyleSheet(change_pic_btn_style)
            self.cancel_btn.setStyleSheet(cancel_btn_style)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Créer et afficher la fenêtre de test
    test_window = EditProfileWindow(
        username="John Doe",
        email="john.doe@example.com",
        is_dark_theme=False  # Mets True pour tester le thème sombre
    )
    test_window.show()

    sys.exit(app.exec())