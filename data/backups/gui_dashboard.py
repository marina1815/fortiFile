from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QColor
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as mticker

from core.gestion_db import *

class HoverFrame(QFrame):
    """A QFrame that brightens, enlarges, and casts shadow on hover."""
    def __init__(self, base_color: str, radius: int = 16, hover_factor: float = 1.15):
        super().__init__()
        self.base_color = QColor(base_color)
        self.hover_color = self._brighter_color(self.base_color, hover_factor)
        self.current_color = self.base_color
        self.radius = radius

        # Shadow
        self.shadow = QGraphicsDropShadowEffect(blurRadius=25, xOffset=0, yOffset=4, color=QColor(0, 0, 0, 120))
        self.setGraphicsEffect(self.shadow)
        self.shadow.setEnabled(False)

        # Default appearance
        self.setStyleSheet(f"border-radius: {self.radius}px; background-color: {self.base_color.name()};")
        self.anim_color = None
        self.anim_scale = None

    def _brighter_color(self, color, factor):
        r = min(int(color.red() * factor), 255)
        g = min(int(color.green() * factor), 255)
        b = min(int(color.blue() * factor), 255)
        return QColor(r, g, b)

    # --- Color transition ---
    def _animate_color(self, to_color):
        if self.anim_color:
            self.anim_color.stop()

        self.anim_color = QPropertyAnimation(self, b"windowOpacity")
        self.anim_color.setDuration(180)
        self.anim_color.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.setStyleSheet(f"border-radius: {self.radius}px; background-color: {to_color.name()};")

    # --- Scale animation ---
    def animate_scale(self, scale_factor):
        parent = self.parentWidget()
        if not parent:
            return
        geo = self.geometry()
        cx, cy = geo.center().x(), geo.center().y()
        new_w, new_h = geo.width() * scale_factor, geo.height() * scale_factor
        new_x = cx - new_w / 2
        new_y = cy - new_h / 2

        if self.anim_scale:
            self.anim_scale.stop()

        self.anim_scale = QPropertyAnimation(self, b"geometry")
        self.anim_scale.setDuration(150)
        self.anim_scale.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim_scale.setStartValue(geo)
        self.anim_scale.setEndValue(QRect(int(new_x), int(new_y), int(new_w), int(new_h)))
        self.anim_scale.start()

    def enterEvent(self, event):
        self.shadow.setEnabled(True)
        self._animate_color(self.hover_color)
        self.animate_scale(1.04)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.shadow.setEnabled(False)
        self._animate_color(self.base_color)
        self.animate_scale(1.0)
        super().leaveEvent(event)





class DashboardPage(QWidget):
    def __init__(self, username="User", dark_mode=False):
        super().__init__()
        self.username = username
        self.dark_mode = dark_mode

        # === Theme colors ===
        if self.dark_mode:
            self.bg_color = "#202020"
            self.card_color = "#444444"
            self.text_color = "#FFFFFF"
            self.subtext_color = "#CCCCCC"
        else:
            self.bg_color = "#eef2f6"
            self.card_color = "#151b54"
            self.text_color = "#FFFFFF"
            self.subtext_color = "#E0E0E0"


        # === Load data from DB ===
        stats = get_dashboard_stats()
        events = get_recent_events(limit=5)

        added = str(stats.get("suspects_new", 0))
        modified = str(stats.get("suspects_modified", 0))
        deleted = str(stats.get("suspects_deleted", 0))
        total = str(stats.get("total_baseline_files", 0))

        # Construct last scan summary from latest event
        if events:
            last_event = events[0]
            last_scan_text = (
                f"Type: {last_event[1]}  |  "
                f"Description: {last_event[2]}  |  "
                f"Time: {last_event[0]}"
            )
        else:
            last_scan_text = "No scans recorded yet."

        # === Layout ===
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # === Row 1: Stats ===
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        stats_layout.addWidget(self.create_stat_box(" Added Files", added))
        stats_layout.addWidget(self.create_stat_box(" Modified Files", modified))
        stats_layout.addWidget(self.create_stat_box(" Deleted Files", deleted))
        stats_layout.addWidget(self.create_stat_box(" Total Monitored", total))

        # === Row 2: Last Scan ===
        last_scan_box = self.create_long_box("Last Scan", last_scan_text)

        # === Row 3: History + Distribution ===
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(20)
        row3_layout.addWidget(self.create_big_box(" Scan History", "History of scans or events"))
        row3_layout.addWidget(self.create_graph_box("Change Distribution"))

        # === Assemble ===
        main_layout.addLayout(stats_layout)
        main_layout.addWidget(last_scan_box)
        main_layout.addLayout(row3_layout)

        self.setLayout(main_layout)
        self.setStyleSheet(f"background-color: {self.bg_color}; QLabel {{ font-family: 'Segoe UI'; }}")


    # --- Box builders ---
    def create_stat_box(self, title, value):
        frame = HoverFrame(self.card_color)
        frame.setFixedHeight(120)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        label_title = QLabel(title)
        label_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        label_title.setStyleSheet(f"color: {self.subtext_color};")
        label_value = QLabel(value)
        label_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_value.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        label_value.setStyleSheet(f"color: {self.text_color};")
        layout.addWidget(label_title)
        layout.addStretch()
        layout.addWidget(label_value)
        return frame

    def create_long_box(self, title, content):
        frame = HoverFrame(self.card_color)
        frame.setFixedHeight(100)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        label_title = QLabel(title)
        label_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        label_title.setStyleSheet(f"color: {self.text_color};")
        label_content = QLabel(content)
        label_content.setFont(QFont("Segoe UI", 10))
        label_content.setStyleSheet(f"color: {self.subtext_color};")
        layout.addWidget(label_title)
        layout.addWidget(label_content)
        return frame

    def create_big_box(self, title, placeholder_text):
        frame = HoverFrame(self.card_color)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        label_title = QLabel(title)
        label_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        label_title.setStyleSheet(f"color: {self.text_color};")
        label_placeholder = QLabel(placeholder_text)
        label_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_placeholder.setStyleSheet(f"color: {self.subtext_color}; font-style: italic;")
        layout.addWidget(label_title)
        layout.addStretch()
        layout.addWidget(label_placeholder)
        layout.addStretch()
        return frame


# -------------------------------------------------
    # 🟣 Chart Section
    # -------------------------------------------------
    def create_graph_box(self, title=" Change Distribution"):
        box = HoverFrame(self.card_color)
        box.setStyleSheet(f"""
            QFrame {{
                background-color: #151b54;
                border-radius: 20px;
                padding: 15px;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 10px;
            }}
        """)

        layout = QVBoxLayout(box)

        # --- Title ---
        title_label = QLabel(title)
        layout.addWidget(title_label)

        # --- Data ---
        stats = get_dashboard_stats()
        new_files = stats.get("suspects_new", 0)
        modified_files = stats.get("suspects_modified", 0)
        deleted_files = stats.get("suspects_deleted", 0)

        labels = ["New", "Modified", "Deleted"]
        values = [new_files, modified_files, deleted_files]
        colors = ["#29ABE2", "#F2C94C", "#EB5757"]  # blue, yellow, red

        total = sum(values)

        # --- Create Matplotlib Figure ---
        fig = Figure(figsize=(3, 3), facecolor="#151b54")
        ax = fig.add_subplot(111)
        fig.subplots_adjust(0.05, 0.05, 0.95, 0.95)

        if total > 0:
            # Normal donut chart
            wedges, texts = ax.pie(
                values,
                colors=colors,
                startangle=90,
                wedgeprops=dict(width=0.4, edgecolor="#151b54"),
            )
            ax.text(
                0, 0, str(total),
                ha='center', va='center',
                color='white', fontsize=20, fontweight='bold'
            )
        else:
            # Placeholder “No Data” circle
            ax.pie(
                [1],
                colors=["#2E3A9D"],
                startangle=90,
                wedgeprops=dict(width=0.4, edgecolor="#151b54"),
            )
            ax.text(
                0, 0, "No Data",
                ha='center', va='center',
                color='white', fontsize=14, fontweight='bold'
            )

        ax.set_facecolor("#151b54")
        ax.axis("equal")  # keep perfect circle

        # --- Embed chart in Qt ---
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

        # Optional: add legend
        legend = QLabel("🟦 New   🟨 Modified   🟥 Deleted")
        legend.setStyleSheet("color: white; font-size: 12px; margin-top: 8px;")
        legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(legend)

        return box


# === Standalone test ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = DashboardPage(dark_mode=False)
    dashboard.resize(1100, 700)
    dashboard.show()
    sys.exit(app.exec())









def start_monitoring(folder):
    ensure_backup_dir()
    event_handler = IntegrityHandler(folder)
    observer = Observer()
    observer.schedule(event_handler, folder, recursive=True)
    observer.start()
    db.log_event("info", f"Surveillance activée sur {folder} (utilisateur : {current_user})")
    notify("Surveillance activée", folder)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        notify("Surveillance arrêtée", folder)
    observer.join()

# ===============================
# MAIN ENTRY POINT
# ===============================
"""if __name__ == "__main__":
    db.init_db()
    folder = r"C:Users\DELL\Desktoptest"
    current_user = input("🔐 Nom d’utilisateur : ").strip().lower()
    # TODO: you could look up user_id from DB if needed
    current_user_id = None

    build_baseline_for_folder(folder, current_user)
    start_monitoring(folder)"""