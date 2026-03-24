"""
collector.py – Einmalige Messung aller Pi-Performance-Metriken.
Wird per Cron Job alle 5 Minuten aufgerufen.
"""

import psutil
import subprocess
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db import init_db, insert_metric


def get_cpu_temp():
    try:
        out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True)
        return float(out.strip().replace("temp=", "").replace("'C", ""))
    except Exception:
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                return round(int(f.read().strip()) / 1000, 1)
        except Exception:
            return None


def get_net_delta():
    """Misst Netzwerk-Traffic über 1 Sekunde (KB/s)."""
    before = psutil.net_io_counters()
    time.sleep(1)
    after = psutil.net_io_counters()
    sent_kb = round((after.bytes_sent - before.bytes_sent) / 1024, 2)
    recv_kb = round((after.bytes_recv - before.bytes_recv) / 1024, 2)
    return sent_kb, recv_kb


def collect():
    init_db()

    cpu_temp = get_cpu_temp()
    cpu_pct = psutil.cpu_percent(interval=1)
    cpu_freq = psutil.cpu_freq()
    cpu_freq_mhz = round(cpu_freq.current, 1) if cpu_freq else None

    load_1, load_5, load_15 = [round(x, 2) for x in psutil.getloadavg()]

    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()

    disk = psutil.disk_usage("/")

    net_sent_kb, net_recv_kb = get_net_delta()

    uptime_h = round((time.time() - psutil.boot_time()) / 3600, 2)

    row = {
        "cpu_temp":     cpu_temp,
        "cpu_pct":      cpu_pct,
        "cpu_freq_mhz": cpu_freq_mhz,
        "load_1":       load_1,
        "load_5":       load_5,
        "load_15":      load_15,
        "ram_pct":      ram.percent,
        "ram_used_mb":  round(ram.used / 1024**2, 1),
        "ram_total_mb": round(ram.total / 1024**2, 1),
        "swap_pct":     swap.percent,
        "disk_pct":     disk.percent,
        "disk_used_gb": round(disk.used / 1024**3, 2),
        "disk_total_gb": round(disk.total / 1024**3, 2),
        "net_sent_kb":  net_sent_kb,
        "net_recv_kb":  net_recv_kb,
        "uptime_h":     uptime_h,
    }

    insert_metric(row)
    print(f"[collector] Gespeichert: CPU {cpu_pct}% | {cpu_temp}°C | RAM {ram.percent}%")


if __name__ == "__main__":
    collect()
