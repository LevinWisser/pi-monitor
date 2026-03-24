# Pi Monitor

Automatisches Performance-Monitoring für den Raspberry Pi 5.
Sammelt alle 5 Minuten Systemdaten und schickt alle 3 Tage ein HTML-Dashboard per E-Mail.

---

## Features

- Erfasst CPU-Temperatur, -Auslastung und -Frequenz
- RAM & Swap-Nutzung
- Disk-Auslastung
- Netzwerk-Traffic (KB/s)
- System Load (1/5/15 Min)
- Uptime
- Speichert alle Metriken in einer lokalen SQLite-Datenbank
- Generiert eingebettete Matplotlib-Charts im HTML-Dashboard
- Farbcodierter Statusüberblick (grün/gelb/rot) nach konfigurierbaren Schwellenwerten
- Versendet das Dashboard als HTML-E-Mail via Gmail SMTP

---

## Schnellstart

```bash
git clone https://github.com/LevinWisser/pi-monitor.git
cd pi-monitor
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp config.example.py config.py
# config.py öffnen und EMAIL_PASSWORD eintragen
venv/bin/python collector.py   # Testmessung
venv/bin/python reporter.py    # Test-Dashboard senden
```

---

## Konfiguration

Alle Einstellungen in `config.py` (aus `config.example.py` erstellen):

| Variable | Bedeutung | Standard |
|---|---|---|
| `EMAIL_PASSWORD` | Gmail App-Passwort | – muss gesetzt werden |
| `EMAIL_SENDER` | Absender-Adresse | wisserlevin@gmail.com |
| `EMAIL_RECIPIENT` | Empfänger-Adresse | wisserlevin@gmail.com |
| `REPORT_LOOKBACK_DAYS` | Zeitraum des Dashboards in Tagen | 3 |
| `TEMP_WARN_C` / `TEMP_CRIT_C` | Temperatur-Schwellenwerte | 70 / 80 °C |
| `CPU_WARN_PCT` | CPU-Auslastung Warnschwelle | 80 % |
| `RAM_WARN_PCT` | RAM-Auslastung Warnschwelle | 85 % |
| `DISK_WARN_PCT` | Disk-Auslastung Warnschwelle | 85 % |

---

## Cron Jobs

```bash
crontab -e
```

```
# Metriken alle 5 Minuten sammeln
*/5 * * * * cd /home/levinwisser/pi-monitor && /home/levinwisser/pi-monitor/venv/bin/python collector.py >> /home/levinwisser/pi-monitor/logs/collector.log 2>&1

# Dashboard alle 3 Tage um 19 Uhr senden
0 19 */3 * * cd /home/levinwisser/pi-monitor && /home/levinwisser/pi-monitor/venv/bin/python reporter.py >> /home/levinwisser/pi-monitor/logs/reporter.log 2>&1
```

---

## Projektstruktur

```
pi-monitor/
├── collector.py          # Einmalige Messung – wird per Cron aufgerufen
├── reporter.py           # Dashboard generieren und per Mail senden
├── config.py             # Einstellungen (nicht im Git)
├── config.example.py     # Vorlage
├── requirements.txt
├── README.md
├── documentation.md
├── database/
│   ├── __init__.py
│   └── db.py             # SQLite-Datenbankzugriff
├── data/
│   └── metrics.db        # Wird automatisch erstellt (nicht im Git)
└── logs/
    ├── collector.log
    └── reporter.log
```

---

## Logs beobachten

```bash
tail -f logs/collector.log
tail -f logs/reporter.log
```
