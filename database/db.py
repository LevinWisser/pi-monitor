import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def get_conn():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    return sqlite3.connect(config.DB_PATH)


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ts          DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_temp    REAL,
                cpu_pct     REAL,
                cpu_freq_mhz REAL,
                load_1      REAL,
                load_5      REAL,
                load_15     REAL,
                ram_pct     REAL,
                ram_used_mb REAL,
                ram_total_mb REAL,
                swap_pct    REAL,
                disk_pct    REAL,
                disk_used_gb REAL,
                disk_total_gb REAL,
                net_sent_kb REAL,
                net_recv_kb REAL,
                uptime_h    REAL
            )
        """)
        conn.commit()


def insert_metric(row: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO metrics (
                cpu_temp, cpu_pct, cpu_freq_mhz,
                load_1, load_5, load_15,
                ram_pct, ram_used_mb, ram_total_mb,
                swap_pct, disk_pct, disk_used_gb, disk_total_gb,
                net_sent_kb, net_recv_kb, uptime_h
            ) VALUES (
                :cpu_temp, :cpu_pct, :cpu_freq_mhz,
                :load_1, :load_5, :load_15,
                :ram_pct, :ram_used_mb, :ram_total_mb,
                :swap_pct, :disk_pct, :disk_used_gb, :disk_total_gb,
                :net_sent_kb, :net_recv_kb, :uptime_h
            )
        """, row)
        conn.commit()


def fetch_since(days: int):
    """Gibt alle Metriken der letzten `days` Tage zurück."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("""
            SELECT * FROM metrics
            WHERE ts >= datetime('now', ? || ' days')
            ORDER BY ts ASC
        """, (f"-{days}",))
        return [dict(r) for r in cur.fetchall()]


def fetch_latest():
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM metrics ORDER BY ts DESC LIMIT 1")
        row = cur.fetchone()
        return dict(row) if row else None
