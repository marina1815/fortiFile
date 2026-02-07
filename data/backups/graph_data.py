import sqlite3
from datetime import datetime

class DashboardData:
    def __init__(self, db_path="fim_database.db"):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def fetch_dashboard_stats(self):
        """Fetch key metrics for dashboard display."""
        data = {
            "added": 0,
            "modified": 0,
            "deleted": 0,
            "total_monitored": 0,
            "last_scan": None
        }

        conn = self.get_connection()
        cur = conn.cursor()

        # Count files by state in suspects
        cur.execute("SELECT COUNT(*) FROM suspects WHERE state='new';")
        data["added"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM suspects WHERE state='modified';")
        data["modified"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM suspects WHERE state='deleted';")
        data["deleted"] = cur.fetchone()[0]

        # Total monitored files from baseline
        cur.execute("SELECT COUNT(*) FROM baseline;")
        data["total_monitored"] = cur.fetchone()[0]

        # Last scan info from events table (assuming event_type='baseline' or 'info')
        cur.execute("""
            SELECT timestamp, event_type, description
            FROM events
            WHERE event_type IN ('baseline', 'info')
            ORDER BY timestamp DESC
            LIMIT 1;
        """)
        last_scan = cur.fetchone()
        if last_scan:
            ts, etype, desc = last_scan
            data["last_scan"] = {
                "type": etype,
                "description": desc or "No details",
                "datetime": ts
            }

        conn.close()
        return data



def fetch_change_distribution(self):
    conn = self.get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT state, COUNT(*) FROM suspects
        GROUP BY state;
    """)
    data = dict(cur.fetchall())
    conn.close()
    return data
