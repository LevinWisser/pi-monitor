"""
reporter.py – Erstellt ein HTML-Dashboard mit eingebetteten Charts
und schickt es per E-Mail.
"""

import io
import smtplib
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db import fetch_since, fetch_latest
import config


def _parse_ts(rows):
    from datetime import datetime
    for r in rows:
        r["_dt"] = datetime.strptime(r["ts"], "%Y-%m-%d %H:%M:%S")
    return rows


def _fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return buf.read()


def _none_to_nan(values):
    """Ersetzt None durch float('nan') damit Matplotlib Lücken korrekt darstellt."""
    return [v if v is not None else float("nan") for v in values]


def _color(value, warn, crit):
    if value is None:
        return "#888"
    if value >= crit:
        return "#e74c3c"
    if value >= warn:
        return "#f39c12"
    return "#27ae60"


def build_charts(rows):
    """Erstellt ein zusammengesetztes Chart und gibt es als PNG-Bytes zurück."""
    ts = [r["_dt"] for r in rows]

    BG = "#1a1a2e"
    PANEL = "#16213e"
    GRID = "#2a2a4a"
    TEXT = "#e0e0e0"
    C = ["#00d4ff", "#ff6b6b", "#51cf66", "#ffd43b", "#cc5de8", "#ff922b"]

    fig = plt.figure(figsize=(14, 18), facecolor=BG)
    gs = GridSpec(4, 2, figure=fig, hspace=0.5, wspace=0.35)

    def styled_ax(ax, title):
        ax.set_facecolor(PANEL)
        ax.set_title(title, color=TEXT, fontsize=11, pad=8)
        ax.tick_params(colors=TEXT, labelsize=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID)
        ax.yaxis.label.set_color(TEXT)
        ax.grid(color=GRID, linewidth=0.5)
        return ax

    # 1 – CPU-Temperatur
    ax = styled_ax(fig.add_subplot(gs[0, 0]), "CPU-Temperatur (°C)")
    temps = _none_to_nan([r["cpu_temp"] for r in rows])
    ax.plot(ts, temps, color=C[0], linewidth=1.5)
    ax.axhline(config.TEMP_WARN_C, color="#f39c12", linestyle="--", linewidth=0.8, label=f"Warn {config.TEMP_WARN_C}°C")
    ax.axhline(config.TEMP_CRIT_C, color="#e74c3c", linestyle="--", linewidth=0.8, label=f"Krit {config.TEMP_CRIT_C}°C")
    ax.legend(fontsize=7, labelcolor=TEXT, facecolor=PANEL)
    ax.set_ylabel("°C")
    ax.fill_between(ts, temps, alpha=0.15, color=C[0])

    # 2 – CPU-Auslastung
    ax = styled_ax(fig.add_subplot(gs[0, 1]), "CPU-Auslastung (%)")
    cpu_pct = _none_to_nan([r["cpu_pct"] for r in rows])
    ax.plot(ts, cpu_pct, color=C[1], linewidth=1.5)
    ax.fill_between(ts, cpu_pct, alpha=0.15, color=C[1])
    ax.set_ylim(0, 100)
    ax.set_ylabel("%")

    # 3 – RAM-Nutzung
    ax = styled_ax(fig.add_subplot(gs[1, 0]), "RAM-Nutzung (%)")
    ram_pct = _none_to_nan([r["ram_pct"] for r in rows])
    ax.plot(ts, ram_pct, color=C[2], linewidth=1.5)
    ax.fill_between(ts, ram_pct, alpha=0.15, color=C[2])
    ax.set_ylim(0, 100)
    ax.set_ylabel("%")

    # 4 – System Load (1/5/15 Min)
    ax = styled_ax(fig.add_subplot(gs[1, 1]), "System Load")
    ax.plot(ts, _none_to_nan([r["load_1"] for r in rows]),  color=C[3], linewidth=1.2, label="1 Min")
    ax.plot(ts, _none_to_nan([r["load_5"] for r in rows]),  color=C[4], linewidth=1.2, label="5 Min")
    ax.plot(ts, _none_to_nan([r["load_15"] for r in rows]), color=C[5], linewidth=1.2, label="15 Min")
    ax.legend(fontsize=7, labelcolor=TEXT, facecolor=PANEL)

    # 5 – Netzwerk-Traffic
    ax = styled_ax(fig.add_subplot(gs[2, 0]), "Netzwerk-Traffic (KB/s)")
    ax.plot(ts, _none_to_nan([r["net_recv_kb"] for r in rows]), color=C[0], linewidth=1.2, label="Empfangen")
    ax.plot(ts, _none_to_nan([r["net_sent_kb"] for r in rows]), color=C[1], linewidth=1.2, label="Gesendet")
    ax.legend(fontsize=7, labelcolor=TEXT, facecolor=PANEL)
    ax.set_ylabel("KB/s")

    # 6 – CPU-Frequenz
    ax = styled_ax(fig.add_subplot(gs[2, 1]), "CPU-Frequenz (MHz)")
    freq = _none_to_nan([r["cpu_freq_mhz"] for r in rows])
    ax.plot(ts, freq, color=C[2], linewidth=1.5)
    ax.fill_between(ts, freq, alpha=0.15, color=C[2])
    ax.set_ylabel("MHz")

    # 7 – Disk-Nutzung (Verlauf, unterer Bereich)
    ax = styled_ax(fig.add_subplot(gs[3, :]), "Disk-Nutzung (%)")
    disk_pct = _none_to_nan([r["disk_pct"] for r in rows])
    ax.plot(ts, disk_pct, color=C[5], linewidth=1.5)
    ax.fill_between(ts, disk_pct, alpha=0.15, color=C[5])
    ax.set_ylim(0, 100)
    ax.set_ylabel("%")

    fig.suptitle(
        f"Pi Monitor – Dashboard ({datetime.now().strftime('%d.%m.%Y %H:%M')})",
        color=TEXT, fontsize=14, y=0.98
    )

    png_bytes = _fig_to_bytes(fig)
    plt.close(fig)
    return png_bytes


def build_html(rows, latest):
    chart_png = build_charts(rows)
    n = len(rows)
    days = config.REPORT_LOOKBACK_DAYS

    def stat(label, value, unit, warn, crit):
        c = _color(value, warn, crit)
        v = f"{value}{unit}" if value is not None else "–"
        return f'<td style="padding:8px 14px;"><b style="color:{c}">{v}</b><br><small style="color:#aaa">{label}</small></td>'

    uptime_h = latest.get("uptime_h", 0)
    uptime_str = f"{int(uptime_h // 24)}d {int(uptime_h % 24)}h"

    html = f"""
    <html><body style="background:#1a1a2e;color:#e0e0e0;font-family:Arial,sans-serif;margin:0;padding:20px;">
    <div style="max-width:900px;margin:auto;">

      <h1 style="color:#00d4ff;border-bottom:2px solid #00d4ff;padding-bottom:8px;">
        🖥️ Pi Monitor – {datetime.now().strftime('%d.%m.%Y %H:%M')}
      </h1>
      <p style="color:#aaa">Zeitraum: letzte {days} Tage &nbsp;|&nbsp; {n} Messwerte &nbsp;|&nbsp; Uptime: {uptime_str}</p>

      <h2 style="color:#00d4ff;">Aktueller Status</h2>
      <table style="border-collapse:collapse;width:100%;background:#16213e;border-radius:8px;">
        <tr>
          {stat("CPU-Temp", latest.get("cpu_temp"), "°C", config.TEMP_WARN_C, config.TEMP_CRIT_C)}
          {stat("CPU-Last", latest.get("cpu_pct"), "%", config.CPU_WARN_PCT, 95)}
          {stat("RAM", latest.get("ram_pct"), "%", config.RAM_WARN_PCT, 95)}
          {stat("Disk", latest.get("disk_pct"), "%", config.DISK_WARN_PCT, 95)}
        </tr>
        <tr>
          <td style="padding:8px 14px;"><b style="color:#e0e0e0">{latest.get("cpu_freq_mhz")} MHz</b><br><small style="color:#aaa">CPU-Frequenz</small></td>
          <td style="padding:8px 14px;"><b style="color:#e0e0e0">{latest.get("load_1")} / {latest.get("load_5")} / {latest.get("load_15")}</b><br><small style="color:#aaa">Load 1/5/15 Min</small></td>
          <td style="padding:8px 14px;"><b style="color:#e0e0e0">{latest.get("ram_used_mb")} / {latest.get("ram_total_mb")} MB</b><br><small style="color:#aaa">RAM genutzt / gesamt</small></td>
          <td style="padding:8px 14px;"><b style="color:#e0e0e0">{latest.get("disk_used_gb")} / {latest.get("disk_total_gb")} GB</b><br><small style="color:#aaa">Disk genutzt / gesamt</small></td>
        </tr>
      </table>

      <h2 style="color:#00d4ff;margin-top:28px;">Dashboard (letzte {days} Tage)</h2>
      <img src="cid:dashboard_chart"
           style="width:100%;border-radius:8px;border:1px solid #2a2a4a;" />

      <p style="color:#555;font-size:11px;margin-top:20px;">
        Pi Monitor &nbsp;|&nbsp; Raspberry Pi 5 &nbsp;|&nbsp; Automatisch generiert
      </p>
    </div>
    </body></html>
    """
    return html, chart_png


def send_report():
    rows = fetch_since(config.REPORT_LOOKBACK_DAYS)
    latest = fetch_latest()

    if not rows:
        print("[reporter] Keine Daten in der Datenbank – Abbruch.")
        return

    rows = _parse_ts(rows)
    html, chart_png = build_html(rows, latest or {})

    # multipart/related: HTML + eingebettetes Bild per Content-ID (cid:)
    # Notwendig weil Gmail und andere Clients data:-URIs in HTML-Mails blockieren.
    msg = MIMEMultipart("related")
    msg["Subject"] = f"Pi Monitor – Dashboard {datetime.now().strftime('%d.%m.%Y')}"
    msg["From"] = config.EMAIL_SENDER
    msg["To"] = config.EMAIL_RECIPIENT

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html, "html"))
    msg.attach(alt)

    img = MIMEImage(chart_png, _subtype="png")
    img.add_header("Content-ID", "<dashboard_chart>")
    img.add_header("Content-Disposition", "inline", filename="dashboard.png")
    msg.attach(img)

    with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
        smtp.sendmail(config.EMAIL_SENDER, config.EMAIL_RECIPIENT, msg.as_string())

    print(f"[reporter] Dashboard gesendet ({len(rows)} Datenpunkte).")


if __name__ == "__main__":
    send_report()
