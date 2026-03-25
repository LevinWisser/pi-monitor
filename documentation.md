# Pi Monitor – Dokumentation

## Was ist das?

Pi Monitor ist ein leichtgewichtiges Performance-Monitoring-System für den Raspberry Pi 5.
Es sammelt alle 5 Minuten Systemmetriken, speichert sie lokal in SQLite und verschickt alle 3 Tage
ein visuelles HTML-Dashboard als E-Mail – vollständig automatisch, ohne externen Server.

---

## Für Claude Code auf dem Raspberry Pi – Schnellstart

> Du liest diese Datei auf dem Pi und sollst das Projekt einrichten. Hier ist genau was zu tun ist:

### Schritt 1 – Abhängigkeiten installieren

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### Schritt 2 – config.py anlegen

```bash
cp config.example.py config.py
```

In `config.py` das Gmail App-Passwort eintragen:

```python
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx"
```

### Schritt 3 – Test-Lauf

```bash
venv/bin/python collector.py   # Sollte eine Zeile mit Messwerten ausgeben
venv/bin/python reporter.py    # Verschickt das Dashboard per Mail
```

### Schritt 4 – Cron Jobs einrichten

```bash
crontab -e
```

Einträge:
```
*/5 * * * * cd /home/levinwisser/pi-monitor && /home/levinwisser/pi-monitor/venv/bin/python collector.py >> /home/levinwisser/pi-monitor/logs/collector.log 2>&1
0 19 */3 * * cd /home/levinwisser/pi-monitor && /home/levinwisser/pi-monitor/venv/bin/python reporter.py >> /home/levinwisser/pi-monitor/logs/reporter.log 2>&1
```

---

## Architektur

```
collector.py  →  database/db.py  →  data/metrics.db
reporter.py   →  database/db.py  →  Matplotlib-Charts  →  HTML-Mail
```

### collector.py

Wird per Cron alle 5 Minuten aufgerufen. Misst einmalig alle Metriken und schreibt einen Datensatz in die SQLite-Datenbank. Laufzeit ca. 3 Sekunden (davon 1s für Netzwerk-Delta-Messung und 1s für CPU-Auslastung).

### reporter.py

Wird alle 3 Tage um 19 Uhr aufgerufen. Liest alle Datenpunkte der letzten 3 Tage aus der Datenbank, generiert 7 Matplotlib-Charts (dark theme) und verschickt sie via Gmail SMTP.

Das PNG-Chart wird als MIME-Inline-Attachment (`multipart/related`) eingebettet und im HTML per `<img src="cid:dashboard_chart">` referenziert. **Wichtig:** `data:`-URIs (base64 direkt im `src`-Attribut) werden von Gmail und den meisten E-Mail-Clients aus Sicherheitsgründen geblockt und dürfen nicht verwendet werden.

### database/db.py

SQLite-Zugriffschicht. Initialisiert die Datenbank beim ersten Start, schreibt Messpunkte und liest sie für den Report zurück.

---

## Erfasste Metriken

| Metrik | Quelle | Einheit |
|---|---|---|
| CPU-Temperatur | `vcgencmd` / `/sys/class/thermal` | °C |
| CPU-Auslastung | `psutil.cpu_percent` | % |
| CPU-Frequenz | `psutil.cpu_freq` | MHz |
| System Load | `psutil.getloadavg` | – (1/5/15 Min) |
| RAM-Nutzung | `psutil.virtual_memory` | % und MB |
| Swap-Nutzung | `psutil.swap_memory` | % |
| Disk-Nutzung | `psutil.disk_usage("/")` | % und GB |
| Netzwerk-Traffic | `psutil.net_io_counters` (Delta 1s) | KB/s |
| Uptime | `psutil.boot_time` | Stunden |

---

## Dashboard-Charts

Das Dashboard enthält 7 Zeitreihen-Charts im Dark Theme:

1. CPU-Temperatur mit Warn- und Kritisch-Schwellenwerten
2. CPU-Auslastung
3. RAM-Nutzung
4. System Load (1/5/15 Min)
5. Netzwerk-Traffic (Senden / Empfangen)
6. CPU-Frequenz
7. Disk-Nutzung (volle Breite)

---

## Technologie-Entscheidungen

| Entscheidung | Begründung |
|---|---|
| **SQLite** | Kein Datenbankserver nötig, atomare Writes, einfache Zeitreihen-Abfragen |
| **Matplotlib mit MIME-Inline-Attachment** | Keine externen Bild-URLs, funktioniert zuverlässig in Gmail und anderen Clients (CID-Referenz statt `data:`-URI, die von Gmail geblockt wird) |
| **Cron statt internem Scheduler** | Script läuft einmal durch und beendet sich – stabiler auf dem Pi, kein Daemon nötig |
| **Gmail SMTP** | Kein eigener Mailserver, zuverlässig, bereits für Wohnungsscout eingerichtet |
| **psutil** | Plattformübergreifend, ARM-kompatibel, deckt alle relevanten Metriken ab |

---

## Mögliche Erweiterungen

- [ ] Telegram-Benachrichtigung bei Überschreitung von Schwellenwerten
- [ ] Weitere Plattformen / Dateisysteme (z.B. externe Festplatte)
- [ ] Web-Dashboard (Flask) für Live-Ansicht
- [ ] Daten-Export als CSV
