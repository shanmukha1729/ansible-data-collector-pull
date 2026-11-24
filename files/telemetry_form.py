#!/usr/bin/env python3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import html
import sqlite3
import urllib.parse

DB_PATH = "/var/lib/node-telemetry/metrics.db"
HOST = "0.0.0.0"
PORT = 8080

HTML_TEMPLATE = """<!doctype html>
<html>
<head><meta charset="utf-8"><title>Node Telemetry Form</title></head>
<body>
  <h2>Add Node Snapshot Entry</h2>
  <form method="POST" action="/add">
    <label>Hostname: <input name="hostname" value="{hostname}" required></label><br><br>
    <label>OS Version: <input name="os_version" value="{os_version}" required></label><br><br>
    <label>CPU vCPUs: <input type="number" name="cpu_vcpus" value="2" required></label><br><br>
    <label>Memory (MB): <input type="number" name="memory_total_mb" value="908" required></label><br><br>
    <label>Environment: <input name="environment" value="lab" required></label><br><br>
    <label>Owner Label: <input name="owner_label" value="platform-team" required></label><br><br>
    <button type="submit">Save to SQLite</button>
  </form>
  <p>{message}</p>
  <h3>Recent Entries</h3>
  <table border="1" cellpadding="6">
    <tr><th>ID</th><th>Recorded At</th><th>Hostname</th><th>OS</th><th>vCPUs</th><th>RAM (MB)</th><th>Env</th><th>Owner</th></tr>
    {rows}
  </table>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def render_page(self, message=""):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, recorded_at, hostname, os_version, cpu_vcpus, memory_total_mb, environment, owner_label "
            "FROM node_snapshots ORDER BY id DESC LIMIT 10"
        )
        rows_html = ""
        for r in cur.fetchall():
            rows_html += "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>"
        conn.close()

        page = HTML_TEMPLATE.format(
            hostname="ip-172-31-41-125",
            os_version="Ubuntu 26.04",
            message=html.escape(message),
            rows=rows_html,
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def do_GET(self):
        self.render_page()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        data = urllib.parse.parse_qs(body)

        hostname = data.get("hostname", [""])[0].strip()
        os_version = data.get("os_version", [""])[0].strip()
        cpu_vcpus = int(data.get("cpu_vcpus", ["1"])[0])
        memory_total_mb = int(data.get("memory_total_mb", ["0"])[0])
        environment = data.get("environment", ["lab"])[0].strip()
        owner_label = data.get("owner_label", ["platform-team"])[0].strip()
        recorded_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO node_snapshots (recorded_at, hostname, os_version, cpu_vcpus, memory_total_mb, environment, owner_label) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (recorded_at, hostname, os_version, cpu_vcpus, memory_total_mb, environment, owner_label),
        )
        conn.commit()
        conn.close()
        self.render_page("Saved entry to SQLite!")

if __name__ == "__main__":
    HTTPServer((HOST, PORT), Handler).serve_forever()
