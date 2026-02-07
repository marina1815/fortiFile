from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QColor
import sys
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as mticker

from core.gestion_db import *
import os

from core.user_manager import load_current_user


class UserBaselineTable(QFrame):
    """Displays baseline files for a user in a table.
    Clicking a row shows detailed stats below.
    """

    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.setStyleSheet("QFrame { background-color: transparent; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File Path", "Size (bytes)", "Last Modified", "Folder"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border-radius: 10px;
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #F4F6FA;
                padding: 5px;
                border: 0px;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #D0E4FF;
            }
        """)
        layout.addWidget(self.table)

        # Stats display
        self.stats_label = QLabel("Select a file to see details")
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("color: #333333; font-size: 10pt;")
        layout.addWidget(self.stats_label)

        # Load user baseline
        self.load_files()

        # Connect click
        self.table.cellClicked.connect(self.show_file_stats)

    def load_files(self):
        from core.gestion_db import get_baseline_by_user
        files = get_baseline_by_user(self.username)
        self.table.setRowCount(len(files))
        for row_idx, f in enumerate(files):
            self.table.setItem(row_idx, 0, QTableWidgetItem(f["path"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(f["size"])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(f["modified_time"])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f["folder_path"]))

    def show_file_stats(self, row, column):
        from core.gestion_db import get_file_stats_for_user_file
        path_item = self.table.item(row, 0)
        if not path_item:
            return
        path = path_item.text()
        stats = get_file_stats_for_user_file(path, self.username)

        baseline = stats.get("baseline")
        suspect = stats.get("suspect")
        counts = stats.get("suspect_counts", {})

        modified_count = counts.get("modified", 0)
        deleted_count = counts.get("deleted", 0)
        total_count = modified_count + deleted_count

        text = f"<b>File:</b> {baseline['path'] if baseline else path}<br>"
        if baseline:
            text += f"<b>Size:</b> {baseline['size']} bytes<br>"
            text += f"<b>Last Modified:</b> {baseline['modified_time']}<br>"
            text += f"<b>Folder:</b> {baseline['folder_path']}<br>"

        if suspect:
            text += f"<b>State:</b> {suspect['state']}<br>"
            text += f"<b>First Detected:</b> {suspect['first_detected']}<br>"
            text += f"<b>Last Seen:</b> {suspect['last_seen']}<br>"

        text += f"<b>Events Count:</b> Modified={modified_count}, Deleted={deleted_count}<br>"
        text += f"<b>Total Events:</b> {total_count}"

        self.stats_label.setText(text)


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

    def _animate_color(self, to_color):
        if self.anim_color:
            self.anim_color.stop()
        self.anim_color = QPropertyAnimation(self, b"windowOpacity")
        self.anim_color.setDuration(180)
        self.anim_color.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.setStyleSheet(f"border-radius: {self.radius}px; background-color: {to_color.name()};")

    def enterEvent(self, event):
        self.shadow.setEnabled(True)
        self._animate_color(self.hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.shadow.setEnabled(False)
        self._animate_color(self.base_color)
        super().leaveEvent(event)


class DashboardPage(QWidget):
    def __init__(self, username="User", dark_mode=False):
        super().__init__()
        self.username = username
        self.dark_mode = dark_mode

        # Store references to labels for updates
        self.stat_labels = {}
        self.last_scan_label = None
        self.recent_activity_layout = None
        self.trend_canvas = None
        self.dist_canvas = None
        self.dist_ax = None
        self.dist_fig = None
        self.baseline_table = None

        # === Theme colors ===
        if self.dark_mode:
            self.bg_color = "#121212"
            self.card_color = "#1E1E1E"
            self.text_color = "#FFFFFF"
            self.subtext_color = "#B0B0B0"
        else:
            self.bg_color = "#F4F6FA"
            self.card_color = "#FFFFFF"
            self.text_color = "#222222"
            self.subtext_color = "#555555"

        # === Load initial data ===
        stats = get_dashboard_stats(username=load_current_user())
        events = get_recent_events(limit=5)

        added = str(stats.get("suspects_new", 0))
        modified = str(stats.get("suspects_modified", 0))
        deleted = str(stats.get("suspects_deleted", 0))
        total = str(stats.get("total_baseline_files", 0))
        folders_total = str(stats.get("total_folders", 0))

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
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # === Row 1: Stats ===
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        stats_layout.addWidget(self.create_stat_box(" Added Files", added, "added"))
        stats_layout.addWidget(self.create_stat_box(" Modified Files", modified, "modified"))
        stats_layout.addWidget(self.create_stat_box(" Deleted Files", deleted, "deleted"))
        stats_layout.addWidget(self.create_stat_box(" Total Monitored", total, "total"))
        stats_layout.addWidget(self.create_stat_box(" Folders", folders_total, "folders"))

        # === Row 2: Last Scan ===
        last_scan_box = self.create_long_box("Last Scan", last_scan_text)

        # === Row 3: History + Distribution ===
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(20)
        row3_layout.addWidget(self.create_user_baseline_table_box())
        row3_layout.addWidget(self.create_graph_box("Change Distribution"))

        # === Row 4: Trend + Notifications ===
        row4_layout = QHBoxLayout()
        row4_layout.setSpacing(20)
        row4_layout.addWidget(self.create_suspect_trend_box())
        row4_layout.addWidget(self.create_recent_activity_box())

        # === Assemble ===
        main_layout.addLayout(stats_layout)
        main_layout.addLayout(row3_layout)
        main_layout.addLayout(row4_layout)
        main_layout.addWidget(last_scan_box)

        # === Scroll Area ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        scroll_area.setStyleSheet(f"""
                    QScrollArea {{
                        background-color: {self.bg_color};
                        border: none;
                    }}
                    QScrollBar:vertical {{
                    border: none;
                    background: #f0f0f0;
                    width: 12px;
                    margin: 0px 0px 0px 0px;
                    border-radius: 6px;
                    }}
                    QScrollBar::handle:vertical {{
                        background: #c0c0c0;
                        min-height: 20px;
                        border-radius: 6px;
                    }}
                    QScrollBar::handle:vertical:hover {{
                        background: #a0a0a0;
                    }}
                    QScrollBar::add-line, QScrollBar::sub-line {{
                        height: 0;
                    }}
                """)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll_area)
        self.setLayout(layout)
        self.setStyleSheet(f"background-color: {self.bg_color}; QLabel {{ font-family: 'Segoe UI'; }}")

        # === Real-time Update Timer ===
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_dashboard)
        self.timer.start(2000)  # Refresh every 2 seconds

    def refresh_dashboard(self):
        """Updates dashboard data in real-time"""
        try:
            # 1. Update Stats
            stats = get_dashboard_stats(username=load_current_user())
            self.stat_labels["added"].setText(str(stats.get("suspects_new", 0)))
            self.stat_labels["modified"].setText(str(stats.get("suspects_modified", 0)))
            self.stat_labels["deleted"].setText(str(stats.get("suspects_deleted", 0)))
            self.stat_labels["total"].setText(str(stats.get("total_baseline_files", 0)))
            self.stat_labels["folders"].setText(str(stats.get("total_folders", 0)))

            # 2. Update Last Scan
            events = get_recent_events(limit=5)
            if events:
                last_event = events[0]
                last_scan_text = (
                    f"Type: {last_event[1]}  |  "
                    f"Description: {last_event[2]}  |  "
                    f"Time: {last_event[0]}"
                )
                self.last_scan_label.setText(last_scan_text)

            # 3. Update Pie Chart
            new_files = stats.get("suspects_new", 0)
            modified_files = stats.get("suspects_modified", 0)
            deleted_files = stats.get("suspects_deleted", 0)
            values = [new_files, modified_files, deleted_files]
            colors = ["#4A90E2", "#F5A623", "#D0021B"]
            total = sum(values)

            self.dist_ax.clear()
            if total > 0:
                self.dist_ax.pie(values, colors=colors, startangle=90, wedgeprops=dict(width=0.4))
                self.dist_ax.text(0, 0, str(total), ha='center', va='center', color=self.text_color, fontsize=20,
                                  fontweight='bold')
            else:
                self.dist_ax.pie([1], colors=["#B0BEC5"], startangle=90, wedgeprops=dict(width=0.4))
                self.dist_ax.text(0, 0, "No Data", ha='center', va='center', color=self.text_color, fontsize=14,
                                  fontweight='bold')
            self.dist_ax.axis("equal")
            self.dist_canvas.draw()

            # 4. Update Recent Activity
            # Clear existing items (except title)
            while self.recent_activity_layout.count() > 1:
                item = self.recent_activity_layout.takeAt(1)
                if item.widget():
                    item.widget().deleteLater()

            if not events:
                empty = QLabel("No recent events.")
                empty.setStyleSheet(f"color: {self.subtext_color}; font-style: italic;")
                self.recent_activity_layout.addWidget(empty)
            else:
                for ts, event_type, desc, path, level in events:
                    color = {
                        "info": "#4A90E2",
                        "warning": "#F5A623",
                        "error": "#D0021B",
                        "alert": "#E74C3C",
                        "baseline": "#7ED321"
                    }.get(event_type, "#AAAAAA")
                    lbl = QLabel(f"● {event_type.upper()} — {desc[:60]}")
                    lbl.setStyleSheet(f"color: {color}; font-size: 10pt; margin-bottom: 3px;")
                    self.recent_activity_layout.addWidget(lbl)

            # 5. Update Baseline Table (optional, might be heavy)
            # self.baseline_table.load_files()

        except Exception as e:
            print(f"Error refreshing dashboard: {e}")

    # --- Box builders ---
    def create_stat_box(self, title, value, key):
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

        # Store label reference
        self.stat_labels[key] = label_value

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

        # Store label reference
        self.last_scan_label = label_content

        layout.addWidget(label_title)
        layout.addWidget(label_content)
        return frame

    def create_recent_activity_box(self):
        frame = HoverFrame(self.card_color)
        self.recent_activity_layout = QVBoxLayout(frame)
        self.recent_activity_layout.setContentsMargins(15, 10, 15, 10)
        title = QLabel("Recent Activity")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.text_color}; margin-bottom: 5px;")
        self.recent_activity_layout.addWidget(title)

        events = get_recent_events(6)
        if not events:
            empty = QLabel("No recent events.")
            empty.setStyleSheet(f"color: {self.subtext_color}; font-style: italic;")
            self.recent_activity_layout.addWidget(empty)
            return frame

        for ts, event_type, desc, path, level in events:
            color = {
                "info": "#4A90E2",
                "warning": "#F5A623",
                "error": "#D0021B",
                "alert": "#E74C3C",
                "baseline": "#7ED321"
            }.get(event_type, "#AAAAAA")
            lbl = QLabel(f"● {event_type.upper()} — {desc[:60]}")
            lbl.setStyleSheet(f"color: {color}; font-size: 10pt; margin-bottom: 3px;")
            self.recent_activity_layout.addWidget(lbl)
        return frame

    def create_suspect_trend_box(self):
        frame = HoverFrame(self.card_color)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)

        # Title
        title_label = QLabel("Suspect Trend (7 Days)")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.text_color};")
        layout.addWidget(title_label)
        user = load_current_user()
        data = get_suspect_trend(7, username=user)
        if not data:
            label = QLabel("No data available.")
            label.setStyleSheet(f"color: {self.subtext_color}; font-style: italic;")
            layout.addWidget(label)
            return frame

        # Extract data
        days = [d[0][-5:] for d in data]
        counts = [d[1] for d in data]

        # ===== Modern Clean Figure =====
        fig = Figure(figsize=(4, 3), facecolor="none")
        ax = fig.add_subplot(111)

        # Transparent & seamless
        fig.patch.set_alpha(0)
        ax.set_facecolor("none")

        # Modern line
        ax.plot(
            days,
            counts,
            linewidth=3,
            marker="o",
            markersize=7,
            alpha=0.9
        )

        # No borders / spines
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Grid with soft opacity
        ax.grid(True, alpha=0.15)

        # Tick styling
        ax.tick_params(axis='x', colors=self.subtext_color, rotation=0, labelsize=9)
        ax.tick_params(axis='y', colors=self.subtext_color, labelsize=9)

        # No top/bottom labels overlapping
        ax.margins(x=0.05)

        # Clean layout
        fig.tight_layout()

        # Add canvas
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

        return frame

    def create_user_baseline_table_box(self):
        # Create a HoverFrame like other cards
        frame = HoverFrame(self.card_color)
        frame.setFixedHeight(400)  # Adjust height as needed
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # Title inside HoverFrame
        title_label = QLabel("User Baseline Files")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.text_color};")
        layout.addWidget(title_label)

        # Table widget
        self.baseline_table = UserBaselineTable(username=load_current_user())
        layout.addWidget(self.baseline_table)

        return frame

    # --- Chart ---
    def create_graph_box(self, title="Change Distribution"):
        if self.dark_mode:
            bg_color = "#2B2B3C"
            text_color = "#EDEDED"
            chart_bg = "#2B2B3C"
        else:
            bg_color = "#FFFFFF"
            text_color = "#2E2E2E"
            chart_bg = "#FFFFFF"

        box = HoverFrame(bg_color)
        layout = QVBoxLayout(box)
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {text_color}; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(title_label)

        stats = get_dashboard_stats(username=load_current_user())
        new_files = stats.get("suspects_new", 0)
        modified_files = stats.get("suspects_modified", 0)
        deleted_files = stats.get("suspects_deleted", 0)
        labels = ["New", "Modified", "Deleted"]
        values = [new_files, modified_files, deleted_files]
        colors = ["#4A90E2", "#F5A623", "#D0021B"]
        total = sum(values)

        self.dist_fig = Figure(figsize=(3, 3), facecolor=chart_bg)
        self.dist_ax = self.dist_fig.add_subplot(111)

        if total > 0:
            self.dist_ax.pie(values, colors=colors, startangle=90, wedgeprops=dict(width=0.4))
            self.dist_ax.text(0, 0, str(total), ha='center', va='center', color=text_color, fontsize=20,
                              fontweight='bold')
        else:
            self.dist_ax.pie([1], colors=["#B0BEC5"], startangle=90, wedgeprops=dict(width=0.4))
            self.dist_ax.text(0, 0, "No Data", ha='center', va='center', color=text_color, fontsize=14,
                              fontweight='bold')

        self.dist_ax.set_facecolor(chart_bg)
        self.dist_ax.axis("equal")

        self.dist_canvas = FigureCanvas(self.dist_fig)
        layout.addWidget(self.dist_canvas)

        legend = QLabel("🟦 New   🟧 Modified   🟥 Deleted")
        legend.setStyleSheet(f"color: {text_color}; font-size: 12px; margin-top: 8px;")
        legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(legend)
        return box


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Add QTimer import here just in case


    dashboard = DashboardPage(dark_mode=False)
    dashboard.resize(1100, 700)
    dashboard.show()
    sys.exit(app.exec())