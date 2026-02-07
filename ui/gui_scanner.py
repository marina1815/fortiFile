import os
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.integrity_monitoring import startMonitoring, stopMonitoring, build_baseline_for_folder, build_baseline_for_file
from core.config_manager import get_mode, update_mode

from core.user_manager import load_current_user
from core.gestion_db import get_baseline_by_user, get_files, add_scan_history


base_dir = os.path.dirname(os.path.abspath(__file__))
addFile_path = os.path.join(base_dir, "../img/file.png")
document_path = os.path.join(base_dir, "../img/dossier.png")
scann_path = os.path.join(base_dir,"../img/scan.png")
log_path = os.path.join(base_dir,"../img/exit.png")
arret_path = os.path.join(base_dir,"../img/arret.png")
# -------------------------
# Worker thread pour baseline
# -------------------------
class BaselineWorker(QThread):
    finished_build = pyqtSignal(int)  # emit nombre de fichiers traités
    error = pyqtSignal(str)  # emit message d'erreur
    log = pyqtSignal(str)  # emit log lines

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
        self.username = username
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
        self.right_panel.setVisible(False)

        # File details section
        details_label = QLabel("File Details")
        details_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.main_layout.addWidget(details_label)

        self.detail_box = QTextEdit()
        self.detail_box.setReadOnly(True)
        self.detail_box.setStyleSheet("""
            QTextEdit {
                background: #ffffff;
                border: 2px solid #c5cae9;
                border-radius: 10px;
                padding: 12px;
                color: #2c2c54;
                font-size: 15px;
                font-weight: 500;
                font-family: 'Segoe UI';
            }
        """)
        self.detail_box.setMinimumHeight(140)
        self.detail_box.setVisible(False)

        self.main_layout.addWidget(self.detail_box, stretch=0)
        self.main_layout.setStretchFactor(self.splitter, 5)  # Table + logs take most space
        self.main_layout.setStretchFactor(self.detail_box, 1)  # Detail is smaller

        # --- Scan Info Label ---
        self.labelScan = QLabel()
        self.labelScan.setStyleSheet("color: #555; font-style: italic;")
        self.main_layout.addWidget(self.labelScan)

        # --- Load from DB ---
        self.load_baseline_from_db()

        # --- Global Style ---
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f5fa; font-family: 'Segoe UI'; }
            QLineEdit {
                border: 1px solid #ccc; border-radius: 8px; padding: 8px; font-size: 14px; }

            QPushButton:checked {
                    background-color: #5A4FDF;
                    font-weight: bold;
                    border-radius: 5px;
                }
            QPushButton:hover {
                    background-color: #3A3A8D;
                }

            QPushButton {
                background-color: #151B54; 
                color: white; 
                border-radius: 8px; 
                padding: 8px 16px; 
                font-size: 14px; 
                font-weight: 600; 
                }
            QTableWidget 
                { background-color: white; border-radius: 8px; border: 1px solid #ddd; }
            QHeaderView::section 
                { background-color: #e0e0e0; border: none; font-weight: bold; padding: 6px; }
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
        self.btn_add_folder.setIcon(QIcon(document_path))
        self.btn_add_folder.clicked.connect(self.add_folder)
        top_bar.addWidget(self.btn_add_folder)

        # Add File Button
        self.btn_add_file = QPushButton("Add File")
        self.btn_add_file.setIcon(QIcon(addFile_path))
        self.btn_add_file.clicked.connect(self.create_file_in_folder)
        top_bar.addWidget(self.btn_add_file)

        # Scan Button (manuel start/stop monitoring)
        self.scan_button = QPushButton("Scan")
        self.scan_button.setIcon(QIcon(scann_path))
        self.scan_button.clicked.connect(self.lance_scan)
        top_bar.addWidget(self.scan_button)

        self.log_button = QPushButton("Logs")
        self.log_button.setIcon(QIcon(log_path))
        self.log_button.clicked.connect(self.toggle_log_panel)
        top_bar.addWidget(self.log_button)

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
    # Right Panel (Logs )
    # ------------------------------------
    def _setup_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Logs section
        logs_label = QLabel("Log Panel")
        logs_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(logs_label)

        self.log_area = QScrollArea()
        self.log_area.setWidgetResizable(True)
        log_content = QWidget()
        self.log_layout = QVBoxLayout(log_content)
        self.log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.log_area.setWidget(log_content)
        layout.addWidget(self.log_area, stretch=2)

        return panel

    # ------------------------------------
    # Append Logs
    # ------------------------------------

    def toggle_log_panel(self):
        self.right_panel.setVisible(not self.right_panel.isVisible())

    def _append_log(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("""
            QLabel {
                background-color: #EEF1FF;
                border-left: 4px solid #5A4FDF;
                border-radius: 6px;
                padding: 8px 10px;
                color: #1A237E;
                font-size: 13px;
            }
        """)
        self.log_layout.addWidget(label)
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
            self.detail_box.setVisible(False)  # hide if no row selected
            return
        details = []
        for i in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(i).text()
            value = self.table.item(selected, i).text()
            details.append(f"{header}: {value}")
        self.detail_box.setText("\n".join(details))
        self.detail_box.setVisible(True)  # show when row selected

    # ------------------------------------
    # Folder and File Actions (avec worker)
    # ------------------------------------
    def add_folder(self):
        if get_mode() == "manuel" :

            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        else:
            QMessageBox.warning(self, "Warning", "Scan already running (auto mode active).")
            return

        if folder  :
            # affiche le path
            self.path_edit.setText(folder)
            self._append_log(f"Selected folder: {folder}")

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
        self._append_log(f"Build finished: {count} files saved to baseline.")
        self._set_controls_enabled(True)
        # reload table
        self.load_baseline_from_db()
        QMessageBox.information(self, "Build done", f"{count} files saved for the selected folder.")

    def _on_build_error(self, message):
        self._append_log(f"❗ Erreur pendant le build: {message}")
        self._set_controls_enabled(True)
        QMessageBox.critical(self, "Erreur", f"Erreur pendant le build baseline:\n{message}")

    def _set_controls_enabled(self, enabled: bool):
        # désactive/active les boutons pour éviter re-entrance
        self.btn_add_folder.setEnabled(enabled)
        self.btn_add_file.setEnabled(enabled)
        self.scan_button.setEnabled(enabled)
        self.log_button.setEnabled(enabled)

    def create_file_in_folder(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.path_edit.setText(file_path)
            self._append_log(f"Selected file: {file_path}")

            try:
                user = load_current_user()
                # Si ta fonction attend une liste :
                build_baseline_for_file(file_path, user)
                self.load_baseline_from_db()  # recharge la table
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error while adding file:\n{e}")
        else:
            QMessageBox.warning(self, "Error", "Please select a valid file  .")

    # ------------------------------------
    # Scan Button Logic
    # ------------------------------------
    def lance_scan(self):
        if get_mode() == "manuel":
            if self.scan_button.text().lower() == "scan":
                username = load_current_user()
                print(username)
                paths = get_files()
                print(paths)

                startMonitoring(paths, username)
                add_scan_history(username,"in_progress")
                self.scan_button.setText("Stop")
                self.scan_button.setIcon(QIcon(arret_path))

                self.labelScan.setText("🟢 Monitoring started...")
                self._append_log("Started monitoring process.")
            else:
                username = load_current_user()
                stopMonitoring()
                add_scan_history(username, "completed")
                self.scan_button.setText("Scan")
                self.scan_button.setIcon(QIcon(scann_path))
                self.labelScan.setText("🛑 Monitoring stopped.")
                self._append_log("Stopped monitoring process.")
        else:
            QMessageBox.warning(self, "Warning", "Scan already running (auto mode active).")

    # ------------------------------------
    # Change Mode
    # ------------------------------------


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = ScanPage()
    w.setWindowTitle("File Integrity Scan")
    w.resize(1000, 600)
    w.show()
    sys.exit(app.exec())