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
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Node Telemetry Dashboard</title>
  <style>
    :root {{
      --bg: #0f172a;
      --surface: #1e293b;
      --surface-alt: #0b1220;
      --border: #334155;
      --text: #f1f5f9;
      --muted: #94a3b8;
      --accent: #6366f1;
      --accent-hover: #4f46e5;
      --success-bg: rgba(16, 185, 129, 0.15);
      --success-border: #10b981;
      --success-text: #6ee7b7;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
      background: radial-gradient(circle at top, #1e1b4b 0%, var(--bg) 45%);
      color: var(--text);
      min-height: 100vh;
      padding: 2rem 1rem;
      line-height: 1.5;
    }}
    .container {{
      max-width: 960px;
      margin: 0 auto;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.75rem;
    }}
    header h1 {{
      font-size: 1.65rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }}
    header p {{
      color: var(--muted);
      font-size: 0.9rem;
    }}
    .pill {{
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.4);
      color: #a5b4fc;
      padding: 0.35rem 0.75rem;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 600;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.5rem;
      margin-bottom: 1.75rem;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.35);
    }}
    .card h2 {{
      font-size: 1.15rem;
      margin-bottom: 1.1rem;
      color: #e2e8f0;
    }}
    .form-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1rem;
    }}
    .field {{
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }}
    label {{
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    input {{
      background: var(--surface-alt);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.65rem 0.85rem;
      border-radius: 8px;
      font-size: 0.95rem;
      transition: border-color 0.2s, box-shadow 0.2s;
    }}
    input:focus {{
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25);
    }}
    .actions {{
      margin-top: 1.25rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
    }}
    button {{
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 0.7rem 1.4rem;
      border-radius: 8px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s, transform 0.1s;
    }}
    button:hover {{
      background: var(--accent-hover);
    }}
    button:active {{
      transform: translateY(1px);
    }}
    .alert {{
      background: var(--success-bg);
      border: 1px solid var(--success-border);
      color: var(--success-text);
      padding: 0.55rem 0.9rem;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 500;
    }}
    .table-wrap {{
      overflow-x: auto;
      border-radius: 10px;
      border: 1px solid var(--border);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
      text-align: left;
    }}
    th {{
      background: var(--surface-alt);
      color: var(--muted);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.75rem;
      letter-spacing: 0.05em;
      padding: 0.8rem 0.9rem;
      border-bottom: 1px solid var(--border);
    }}
    td {{
      padding: 0.75rem 0.9rem;
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
    tr:hover td {{
      background: rgba(255, 255, 255, 0.03);
    }}
    .badge {{
      display: inline-block;
      padding: 0.2rem 0.55rem;
      border-radius: 6px;
      font-size: 0.78rem;
      font-weight: 600;
      background: rgba(56, 189, 248, 0.15);
      color: #7dd3fc;
      border: 1px solid rgba(56, 189, 248, 0.3);
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>Node Telemetry Collector</h1>
        <p>Ansible-Pull &amp; SQLite Infrastructure Snapshot Store</p>
      </div>
      <span class="pill">SQLite Live Store</span>
    </header>

    <section class="card">
      <h2>Add Node Snapshot Entry</h2>
      <form method="POST" action="/add">
        <div class="form-grid">
          <div class="field">
            <label for="hostname">Hostname</label>
            <input id="hostname" name="hostname" value="{hostname}" required>
          </div>
          <div class="field">
            <label for="os_version">OS Version</label>
            <input id="os_version" name="os_version" value="{os_version}" required>
          </div>
          <div class="field">
            <label for="cpu_vcpus">CPU vCPUs</label>
            <input id="cpu_vcpus" type="number" name="cpu_vcpus" value="2" required>
          </div>
          <div class="field">
            <label for="memory_total_mb">Memory (MB)</label>
            <input id="memory_total_mb" type="number" name="memory_total_mb" value="908" required>
          </div>
          <div class="field">
            <label for="environment">Environment</label>
            <input id="environment" name="environment" value="lab" required>
          </div>
          <div class="field">
            <label for="owner_label">Owner Label</label>
            <input id="owner_label" name="owner_label" value="platform-team" required>
          </div>
        </div>
        <div class="actions">
          <button type="submit">Save to SQLite</button>
          {message_html}
        </div>
      </form>
    </section>

    <section class="card">
      <h2>Recent Entries</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Recorded At (UTC)</th>
              <th>Hostname</th>
              <th>OS</th>
              <th>vCPUs</th>
              <th>RAM (MB)</th>
              <th>Environment</th>
              <th>Owner</th>
            </tr>
          </thead>
          <tbody>
            {rows}
          </tbody>
        </table>
      </div>
    </section>
  </div>
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
            rows_html += (
                f"<tr>"
                f"<td><strong>#{html.escape(str(r[0]))}</strong></td>"
                f"<td>{html.escape(str(r[1]))}</td>"
                f"<td>{html.escape(str(r[2]))}</td>"
                f"<td>{html.escape(str(r[3]))}</td>"
                f"<td>{html.escape(str(r[4]))}</td>"
                f"<td>{html.escape(str(r[5]))}</td>"
                f"<td><span class='badge'>{html.escape(str(r[6]))}</span></td>"
                f"<td>{html.escape(str(r[7]))}</td>"
                f"</tr>"
            )
        conn.close()

        message_html = f'<div class="alert">{html.escape(message)}</div>' if message else ""

        page = HTML_TEMPLATE.format(
            hostname="ip-172-31-41-125",
            os_version="Ubuntu 26.04",
            message_html=message_html,
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
