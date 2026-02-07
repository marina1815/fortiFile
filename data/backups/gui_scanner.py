import os
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from tkinter import messagebox
from core.integrityManuel import check_integrity
# importe ta fonction longue ici (inchangée)
from core.integrityManuel import build_baseline_for_folder
from core.integrity_monitoring  import startMonitoring , stopMonitoring
from core.config_manager import get_mode, update_mode
from core.user_manager import load_current_user
from core.gestion_db import get_baseline_by_user , get_files
import threading

monitor_thread = None
# -------------------------
# Worker thread pour baseline
# -------------------------
class BaselineWorker(QThread):
    finished_build = pyqtSignal(int)      # emit nombre de fichiers traités
    error = pyqtSignal(str)               # emit message d'erreur
    log = pyqtSignal(str)                 # emit log lines

    def __init__(self, folder: str, username: str):
        super().__init__()
        self.folder = folder
        self.username = username

    def run(self):
        try:
            self.log.emit(f"🔍 Démarrage du build pour : {self.folder}")
            # appelle ta fonction existante (couteuse) dans le thread
            count = build_baseline_for_folder(self.folder, self.username)
            if count is None:
                count = 0
            self.log.emit(f"✅ Build terminé : {count} fichiers enregistrés.")
            self.finished_build.emit(count)
        except Exception as e:
            # envoie l'erreur pour affichage
            self.error.emit(str(e))


# -------------------------
# Main GUI
# -------------------------
class ScanPage(QWidget):
    def __init__(self, username="User"):
        super().__init__()
        self.username = load_current_user()
        self.worker = None  # BaselineWorker instance when running

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)

        # --- Top Controls ---
        self._setup_top_bar()

        # --- Splitter (Table + Right Panel) ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # --- Table ---
        self._setup_table_widget()

        # --- Right Panel (Logs + Details) ---
        self.right_panel = self._setup_right_panel()
        self.splitter.addWidget(self.right_panel)

        # --- Scan Info Label ---
        self.labelScan = QLabel()
        self.labelScan.setStyleSheet("color: #555; font-style: italic;")
        self.main_layout.addWidget(self.labelScan)

        # --- Load from DB ---
        self.load_baseline_from_db()

        # --- Global Style ---
        self.setStyleSheet("""
            QWidget { background-color: #f4f5fa; font-family: 'Segoe UI'; }
            QLineEdit { border: 1px solid #ccc; border-radius: 8px; padding: 8px; font-size: 14px; }
            QPushButton { background-color: #4A47FF; color: white; border-radius: 8px; padding: 8px 16px; font-size: 14px; font-weight: 600; }
            QPushButton:hover { background-color: #3030d0; }
            QTableWidget { background-color: white; border-radius: 8px; border: 1px solid #ddd; }
            QHeaderView::section { background-color: #e0e0e0; border: none; font-weight: bold; padding: 6px; }
            QScrollArea { border: 1px solid #ccc; border-radius: 8px; background: white; }
        """)

    # ------------------------------------
    # Top Bar with Separate Buttons
    # ------------------------------------
    def _setup_top_bar(self):
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # Folder Path
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select folder path...")
        self.path_edit.setReadOnly(True)
        self.path_edit.setFixedHeight(38)
        top_bar.addWidget(self.path_edit, stretch=1)

        # Add Folder Button
        self.btn_add_folder = QPushButton("Add Folder")
        self.btn_add_folder.setIcon(QIcon("img/document.png"))
        self.btn_add_folder.clicked.connect(self.add_folder)
        top_bar.addWidget(self.btn_add_folder)

        # Add File Button
        self.btn_add_file = QPushButton("Add File")
        self.btn_add_file.setIcon(QIcon("img/file.png"))
        self.btn_add_file.clicked.connect(self.create_file_in_folder)
        top_bar.addWidget(self.btn_add_file)

        # Scan Button (manuel start/stop monitoring)
        self.scan_button = QPushButton("Scan")
        self.scan_button.setIcon(QIcon("img/scan.png"))
        self.scan_button.clicked.connect(self.lance_scan)
        top_bar.addWidget(self.scan_button)

        # Mode Toggle
        self.mode_button = QPushButton("Mode: Manual")
        self.mode_button.clicked.connect(self.change_mode)
        top_bar.addWidget(self.mode_button)

        # State Label
        self.state_label = QLabel('')
        if get_mode() == "manuel":
            self.state_label.setText('<span style="color: red; font-weight: bold;">Stopped</span>')
        else:
            self.state_label.setText('<span style="color: green; font-weight: bold;">Auto</span>')

        top_bar.addWidget(self.state_label)

        self.main_layout.addLayout(top_bar)

    # ------------------------------------
    # Table Widget
    # ------------------------------------
    def _setup_table_widget(self):
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Folder", "Size (Bytes)", "Modified Time", "User"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.display_file_details)
        self.splitter.addWidget(self.table)

    # ------------------------------------
    # Right Panel (Logs + Details)
    # ------------------------------------
    def _setup_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Logs section
        logs_label = QLabel("📜 Log Panel")
        logs_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(logs_label)

        self.log_area = QScrollArea()
        self.log_area.setWidgetResizable(True)
        log_content = QWidget()
        self.log_layout = QVBoxLayout(log_content)
        self.log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.log_area.setWidget(log_content)
        layout.addWidget(self.log_area, stretch=2)

        # File details section
        details_label = QLabel("📁 File Details")
        details_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(details_label)

        self.detail_box = QTextEdit()
        self.detail_box.setReadOnly(True)
        self.detail_box.setStyleSheet("QTextEdit { background: #fafafa; border-radius: 8px; padding: 8px; }")
        layout.addWidget(self.detail_box, stretch=1)

        return panel

    # ------------------------------------
    # Append Logs
    # ------------------------------------
    def _append_log(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("""
            QLabel {
                background-color: #E8EAF6;
                border: 1px solid #C5CAE9;
                border-radius: 6px;
                padding: 6px 10px;
                color: #1A237E;
            }
        """)
        self.log_layout.addWidget(label)
        # auto-scroll: scroll to bottom
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    # ------------------------------------
    # Load baseline from DB
    # ------------------------------------
    def load_baseline_from_db(self):
        try:
            username = load_current_user()
            baseline_files = get_baseline_by_user(username)
        except Exception:
            baseline_files = []

        self.table.setRowCount(0)
        for row_index, file_info in enumerate(baseline_files):
            self.table.insertRow(row_index)
            self.table.setItem(row_index, 0, QTableWidgetItem(os.path.basename(file_info["path"])))
            self.table.setItem(row_index, 1, QTableWidgetItem(os.path.dirname(file_info["path"])))
            self.table.setItem(row_index, 2, QTableWidgetItem(str(file_info.get("size", 0))))
            self.table.setItem(row_index, 3, QTableWidgetItem(file_info.get("modified_time", "-")))
            self.table.setItem(row_index, 4, QTableWidgetItem(file_info.get("username", "-")))

    # ------------------------------------
    # File Details Display
    # ------------------------------------
    def display_file_details(self):
        selected = self.table.currentRow()
        if selected == -1:
            return
        details = []
        for i in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(i).text()
            value = self.table.item(selected, i).text()
            details.append(f"{header}: {value}")
        self.detail_box.setText("\n".join(details))

    # ------------------------------------
    # Folder and File Actions (avec worker)
    # ------------------------------------
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        print(folder)
        if folder:
            # affiche le path
            self.path_edit.setText(folder)
            self._append_log(f"📂 Selected folder: {folder}")


            # démarre le build baseline dans un thread pour éviter freeze/crash
            if self.worker and self.worker.isRunning():
                QMessageBox.warning(self, "Warning", "A baseline build is already running.")
                return

            username = load_current_user()
            self.worker = BaselineWorker(folder, username)
            # connections
            self.worker.log.connect(self._append_log)
            self.worker.finished_build.connect(self._on_build_finished)
            self.worker.error.connect(self._on_build_error)

            # disable buttons while building
            self._set_controls_enabled(False)
            self._append_log("↪ Lancement du build baseline en arrière-plan...")
            self.worker.start()

    def _on_build_finished(self, count):
        self._append_log(f"🎉 Build finished: {count} fichiers enregistrés.")
        self._set_controls_enabled(True)
        # reload table
        self.load_baseline_from_db()
        QMessageBox.information(self, "Build terminé", f"{count} fichiers enregistrés pour le dossier sélectionné.")

    def _on_build_error(self, message):
        self._append_log(f"❗ Erreur pendant le build: {message}")
        self._set_controls_enabled(True)
        QMessageBox.critical(self, "Erreur", f"Erreur pendant le build baseline:\n{message}")

    def _set_controls_enabled(self, enabled: bool):
        # désactive/active les boutons pour éviter re-entrance
        self.btn_add_folder.setEnabled(enabled)
        self.btn_add_file.setEnabled(enabled)
        self.scan_button.setEnabled(enabled)
        self.mode_button.setEnabled(enabled)

    def create_file_in_folder(self):
        folder = self.path_edit.text().strip()
        if not folder or not os.path.isdir(folder):
            QMessageBox.warning(self, "Error", "Please select a valid folder first.")
            return
        file_name, ok = QInputDialog.getText(self, "Create File", "Enter file name:")
        if ok and file_name:
            file_path = os.path.join(folder, file_name)
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("")
                self._append_log(f"📝 Created file: {file_path}")
                QMessageBox.information(self, "Success", f"File created:\n{file_path}")
                # reload DB entries (si la création est incluse dans la baseline ou tu veux voir le chemin)
                self.load_baseline_from_db()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Impossible de créer le fichier:\n{e}")

    # ------------------------------------
    # Scan Button Logic
    # ------------------------------------

    def start_monitoring(self,file_list, username):
        global monitor_thread
        if monitor_thread and monitor_thread.is_alive():
            print("La surveillance est déjà en cours.")
            return

        # Lancer la surveillance dans un thread pour ne pas bloquer la GUI
        monitor_thread = threading.Thread(target=startMonitoring, args=(file_list, username), daemon=True)
        monitor_thread.start()
        print(f"Surveillance démarrée pour {len(file_list)} fichiers.")

    def stop_monitoring(self):
        stopMonitoring()
        print( "Surveillance arrêtée.")

    def lance_scan(self):
        if get_mode() == "manuel":
            if self.scan_button.text().lower() == "scan":
                self.state_label.setText('<span style="color: green; font-weight: bold;">Running</span>')
                username = load_current_user()
                check_integrity(username)

                self.scan_button.setText("Stop")
                self.labelScan.setText("🟢 Monitoring started...")
                self._append_log("Started monitoring process.")
                paths = get_files()
                self.start_monitoring(paths, username)
            else:
                self.state_label.setText('<span style="color: red; font-weight: bold;">Stopped</span>')
                self.stop_monitoring()
                self.scan_button.setText("Scan")
                self.labelScan.setText("🛑 Monitoring stopped.")
                self._append_log("Stopped monitoring process.")

        else:
            QMessageBox.warning(self, "Warning", "Scan already running (auto mode active).")

    # ------------------------------------
    # Change Mode
    # ------------------------------------
    def change_mode(self):
        if get_mode() == "manuel":
            update_mode("auto")
            self.state_label.setText('<span style="color: green; font-weight: bold;">Auto</span>')
            self.mode_button.setText("Mode: Auto")
        else:
            update_mode("manuel")
            self.mode_button.setText("Mode: Manual")
            self.state_label.setText('<span style="color: red; font-weight: bold;">Stopped</span>')





if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = ScanPage()
    w.setWindowTitle("File Integrity Scan")
    w.resize(1000, 600)
    w.show()
    sys.exit(app.exec())