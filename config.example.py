# ============================================================
# KONFIGURATION – hier alles anpassen bevor du das Script startest
# ============================================================

# --- E-Mail ---
EMAIL_ENABLED = True
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "wisserlevin@gmail.com"
EMAIL_PASSWORD = ""          # Gmail App-Passwort
EMAIL_RECIPIENT = "wisserlevin@gmail.com"

# --- Datenbank ---
DB_PATH = "data/metrics.db"

# --- Collector ---
# Wird per Cron alle 5 Minuten aufgerufen
COLLECT_INTERVAL_MIN = 5

# --- Report ---
# Wie viele Tage soll das Dashboard zurückblicken?
REPORT_LOOKBACK_DAYS = 3

# --- Schwellenwerte für farbliche Warnung im Report ---
TEMP_WARN_C = 70       # °C – gelb
TEMP_CRIT_C = 80       # °C – rot
CPU_WARN_PCT = 80      # % – gelb
RAM_WARN_PCT = 85      # % – gelb
DISK_WARN_PCT = 85     # % – gelb
