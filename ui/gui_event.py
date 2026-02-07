from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize
import os
from core.gestion_db import get_events_by_user, get_events_by_level
from core.user_manager import load_current_user

class EventsPage(QWidget):
    def __init__(self,username=None):
        super().__init__()
        self.username = load_current_user().upper()
        self.is_dark_theme = False
        self.setObjectName("EventsPage")

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # --- Filter Section ---
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(15)

        # Titre
        title_label = QLabel("Events - All Files Audit Activity")
        font = QFont("sans-serif", 24, QFont.Weight.ExtraBold)
        title_label.setFont(font)
        title_label.setStyleSheet("color: #151B54; letter-spacing: 2px;")

        # Bouton Reset
        reset_button = QPushButton()
        reset_button.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../img/recharger.png")))
        reset_button.setIconSize(QSize(20, 20))
        reset_button.setFixedSize(28, 28)
        reset_button.setToolTip("Reset Event History")
        reset_button.clicked.connect(self.reset_table)
        reset_button.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; }
            QPushButton:hover { background-color: rgba(255,255,255,0.1); border-radius:5px; }
        """)

        # Bouton Details
        detail_button = QPushButton()
        detail_button.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../img/bar.png")))
        detail_button.setIconSize(QSize(20, 20))
        detail_button.setFixedSize(28, 28)
        detail_button.setToolTip("Show/Hide Details")
        detail_button.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; }
            QPushButton:hover { background-color: rgba(255,255,255,0.1); border-radius:5px; }
        """)

        # ComboBox type
        self.combo = QComboBox()
        self.combo.setEditable(False)  # Rendre non éditable, car c'est un filtre
        self.combo.addItem("Filter by Event Type")  # Placeholder / Élément par défaut
        self.combo.addItems(['INFO', 'WARNING', 'ERROR', 'ALERT'])
        self.combo.setCurrentIndex(0)
        self.combo.setStyleSheet("""
                           QComboBox {
                               border: 1px solid black;
                               border-radius: 6px;
                               padding: 3px 10px 3px 10px;
                               background-color: white;
                               min-width: 120px;
                           }
                           QComboBox::drop-down {
                               border: none;
                           }
                           QComboBox QAbstractItemView {
                               border: 1px solid black;
                               selection-background-color: #c0c0c0;
                           }
                       """)

        self.combo.view().pressed.connect(self.on_combo_pressed)

        # Ajout au layout filter
        filter_layout.addWidget(title_label)
        filter_layout.addWidget(self.combo)
        filter_layout.addWidget(reset_button)
        filter_layout.addWidget(detail_button)
        layout.addWidget(filter_widget)

        # --- Splitter horizontal ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.splitter)
        layout.setStretch(1, 1)  # <-- le splitter prend tout l'espace vertical restant

        # --- Left: Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(["EVENT TYPE", "FILE PATH", "DETECTION TIME", "DESCRIPTION"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet(self.table_style())
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        self.splitter.addWidget(self.table)

        # --- Right: Details Panel ---
        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        self.details_label = QLabel("Select an event to see details")
        self.details_label.setWordWrap(True)
        details_layout.addWidget(self.details_label)
        details_layout.addStretch()
        self.details_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.splitter.addWidget(self.details_widget)
        self.splitter.setSizes([600, 0])  # panneau de détails masqué par défaut

        self.details_visible = False  # état du panneau

        # Connecter le bouton Details
        detail_button.clicked.connect(self.toggle_details)

        # Charger les données
        self._populate_table()


    def reset_table_display(self, level=None):
        user = load_current_user()

        if level is None or level == "filter by event type":
            data = get_events_by_user(user)
        else:
            data = get_events_by_level(user, level)  # À créer si nécessaire dans core.gestion_db

        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, item in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(item)))

        # Styliser la première colonne en gras
        for row_idx in range(self.table.rowCount()):
            item = self.table.item(row_idx, 0)
            font = item.font()
            font.setBold(True)
            item.setFont(font)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
    # --- Stylesheets ---
    def combo_style(self):
        return """
            QComboBox {
                border: 1px solid black;
                border-radius: 6px;
                padding: 3px 10px;
                background-color: white;
                min-width: 120px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                border: 1px solid black;
                selection-background-color: #c0c0c0;
            }
        """

    def table_style(self):
        return """
            QTableWidget {
                background-color: #f9f9f9;
                alternate-background-color: #eaeaea;
                gridline-color: #d0d0d0;
                font-size: 12pt;
                border: 1px solid #ccc;
            }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #87cefa; color: black; }
            QHeaderView::section {
                background-color: #e0e0e0;
                color: black;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
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
        """

    # --- Toggle details panel ---
    def toggle_details(self):
        if self.details_visible:
            # Masquer
            self.splitter.setSizes([self.splitter.width(), 0])
            self.details_visible = False
        else:
            # Afficher (300px par exemple)
            self.splitter.setSizes([self.splitter.width()-300, 300])
            self.details_visible = True

    # --- Table population ---
    def _populate_table(self):
        self.reset_table()

    def reset_table(self):
        user = load_current_user()
        data = get_events_by_user(user)
        self.populate_table_with_data(data)

    def populate_table_with_data(self, data):
        self.table.setRowCount(len(data))
        for r_idx, row in enumerate(data):
            for c_idx, item in enumerate(row):
                self.table.setItem(r_idx, c_idx, QTableWidgetItem(str(item)))
        for r_idx in range(self.table.rowCount()):
            item = self.table.item(r_idx,0)
            if item:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.details_label.setText("Select an event to see details")

    def on_combo_pressed(self, index):
        level = self.combo.itemText(index.row()).lower()
        print("Combo clicked, selected level:", level)
        self.reset_table_display(level)
    # --- Event when row selected ---
    def on_row_selected(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.details_label.setText("Select an event to see details")
            return
        row_data = [self.table.item(selected_items[0].row(), c).text() for c in range(self.table.columnCount())]
        details_text = f"""
        <div style="
            font-family: 'Segoe UI', sans-serif;
            font-size: 12pt;
            color: #151B54;
            line-height: 1.5em;
            padding: 5px;
        ">
            <b style='color:green;'>Event Type:</b> {row_data[0]}<br>
            <b style='color:green;'>File Path:</b> {row_data[1]}<br>
            <b style='color:green;'>Detection Time:</b> {row_data[2]}<br>
            <b style='color:green;'>Description:</b> {row_data[3]}
        </div>
        """
        self.details_label.setText(details_text)

    def apply_filters(self):
        # Pour demo, on reset le tableau
        self.reset_table()


# --- Main ---
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = EventsPage()
    window.setWindowTitle("About FortiFile")
    window.setGeometry(100,100,950,650)
    window.show()
    sys.exit(app.exec())