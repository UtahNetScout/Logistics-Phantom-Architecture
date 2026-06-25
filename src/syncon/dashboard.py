#!/usr/bin/env python3
"""
SYNCON local dashboard.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA
PORTFOLIO PROOF-OF-CONCEPT - NOT OPERATIONAL TELEMETRY
NOT DEPLOYMENT-READY DECEPTION TOOLING
"""

from __future__ import annotations

import html
import json
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable
from urllib.parse import parse_qs, quote, unquote, urlparse

from .runner import BANNER, run_demo

ARTIFACT_NAMES = {
    "scenario.json",
    "phantoms.json",
    "validation.json",
    "red_team.json",
    "timeline.json",
    "REPORT.md",
}
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def serve_dashboard(
    host: str = "127.0.0.1",
    port: int = 8765,
    output_dir: Path | str = "runs",
    default_run_id: str = "demo-run-001",
) -> None:
    """Serve the SYNCON dashboard until interrupted."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    handler_cls = make_handler(output_path, default_run_id)
    server = ThreadingHTTPServer((host, port), handler_cls)
    print(f"SYNCON dashboard available at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    finally:
        server.server_close()


def make_handler(output_dir: Path, default_run_id: str) -> type[BaseHTTPRequestHandler]:
    """Create a request handler bound to a dashboard output directory."""

    class SynconDashboardHandler(BaseHTTPRequestHandler):
        server_version = "SYNCONDashboard/0.1"

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            parsed = urlparse(self.path)
            if parsed.path == "/":
                query = parse_qs(parsed.query)
                run_id = _safe_run_id(query.get("run_id", [default_run_id])[0])
                message = query.get("message", [""])[0]
                artifacts = load_run_artifacts(output_dir / run_id)
                body = render_dashboard(
                    output_dir=output_dir,
                    run_id=run_id,
                    artifacts=artifacts,
                    message=message,
                )
                self._send_html(body)
                return
            if parsed.path.startswith("/artifact/"):
                self._send_artifact(parsed.path)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            parsed = urlparse(self.path)
            if parsed.path != "/run":
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return

            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length).decode("utf-8")
            form = parse_qs(payload)
            try:
                run_id = _safe_run_id(_first(form, "run_id", default_run_id))
                phantom_count = _bounded_int(_first(form, "phantoms", "10000"), 1, 10000)
                contaminated = _bounded_int(_first(form, "contaminated", "5"), 0, 50)
                seed = _bounded_int(_first(form, "seed", "42"), 0, 999999)
                run_demo(
                    output_dir=output_dir,
                    run_id=run_id,
                    seed=seed,
                    phantom_count=phantom_count,
                    contaminated_phantoms=contaminated,
                    n_workers=1,
                )
                location = f"/?run_id={quote(run_id)}&message=Run+complete"
                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", location)
                self.end_headers()
            except ValueError as exc:
                artifacts = load_run_artifacts(output_dir / default_run_id)
                body = render_dashboard(
                    output_dir=output_dir,
                    run_id=default_run_id,
                    artifacts=artifacts,
                    message=f"Input error: {exc}",
                )
                self._send_html(body, status=HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: Any) -> None:
            """Use a concise dashboard log line."""
            print("SYNCON dashboard:", format % args)

        def _send_html(self, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_artifact(self, path: str) -> None:
            parts = [unquote(p) for p in path.split("/") if p]
            if len(parts) != 3:
                self.send_error(HTTPStatus.NOT_FOUND, "Artifact not found")
                return
            _, run_id, filename = parts
            try:
                run_id = _safe_run_id(run_id)
                if filename not in ARTIFACT_NAMES:
                    raise ValueError("unknown artifact")
            except ValueError:
                self.send_error(HTTPStatus.BAD_REQUEST, "Invalid artifact")
                return

            artifact_path = output_dir / run_id / filename
            if not artifact_path.exists():
                self.send_error(HTTPStatus.NOT_FOUND, "Artifact not found")
                return

            data = artifact_path.read_bytes()
            content_type = "text/markdown; charset=utf-8" if filename.endswith(".md") else "application/json"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return SynconDashboardHandler


def load_run_artifacts(run_dir: Path) -> Dict[str, Any]:
    """Load generated SYNCON artifacts for dashboard rendering."""
    artifacts: Dict[str, Any] = {"exists": run_dir.exists(), "run_dir": str(run_dir)}
    for name in ["scenario", "validation", "red_team", "timeline"]:
        path = run_dir / f"{name}.json"
        if path.exists():
            artifacts[name] = json.loads(path.read_text(encoding="utf-8"))
    report_path = run_dir / "REPORT.md"
    if report_path.exists():
        artifacts["report"] = report_path.read_text(encoding="utf-8")
    return artifacts


def render_dashboard(
    output_dir: Path,
    run_id: str,
    artifacts: Dict[str, Any],
    message: str = "",
) -> str:
    """Render the SYNCON dashboard page."""
    scenario = artifacts.get("scenario", {})
    validation = artifacts.get("validation", {})
    red_team = artifacts.get("red_team", {})
    timeline = artifacts.get("timeline", {})
    events = timeline.get("events", [])
    selected_run = html.escape(run_id)
    default_phantoms = scenario.get("phantom_count", 10000)
    default_contaminated = scenario.get("contaminated_phantoms", 5)
    default_seed = scenario.get("seed", 42)
    artifact_links = _artifact_links(run_id)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SYNCON Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f8fb;
      --panel: #ffffff;
      --ink: #18222f;
      --muted: #5f6d7a;
      --line: #d8e0ea;
      --accent: #126c7a;
      --accent-strong: #0f4f5c;
      --ok: #14743b;
      --warn: #9b4d00;
      --danger: #a02626;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.45;
    }}
    header {{
      background: #17202c;
      color: #fff;
      padding: 22px 28px;
      border-bottom: 4px solid var(--accent);
    }}
    header h1 {{
      margin: 0;
      font-size: 28px;
      letter-spacing: 0;
    }}
    header p {{
      margin: 6px 0 0;
      color: #dbe5ee;
      max-width: 1100px;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    section {{
      margin-bottom: 22px;
    }}
    h2 {{
      font-size: 18px;
      margin: 0 0 12px;
      letter-spacing: 0;
    }}
    .notice {{
      background: #fff8e6;
      border: 1px solid #e7cf8a;
      color: #5d4600;
      padding: 10px 12px;
      border-radius: 6px;
      margin-bottom: 18px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }}
    .metric, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 14px;
    }}
    .metric .label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }}
    .metric .value {{
      font-size: 24px;
      font-weight: 700;
      margin-top: 4px;
      overflow-wrap: anywhere;
    }}
    form {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 12px;
      align-items: end;
    }}
    label {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }}
    input {{
      width: 100%;
      padding: 9px 10px;
      border: 1px solid var(--line);
      border-radius: 5px;
      font-size: 14px;
    }}
    button {{
      background: var(--accent);
      color: white;
      border: 0;
      border-radius: 5px;
      padding: 10px 14px;
      font-weight: 700;
      cursor: pointer;
      min-height: 38px;
    }}
    button:hover {{ background: var(--accent-strong); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      overflow: hidden;
    }}
    th, td {{
      text-align: left;
      padding: 10px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      background: #eef3f7;
    }}
    .links a {{
      display: inline-block;
      margin: 0 8px 8px 0;
      color: var(--accent-strong);
      font-weight: 700;
    }}
    footer {{
      color: var(--muted);
      font-size: 12px;
      padding-top: 8px;
    }}
    @media (max-width: 900px) {{
      .grid, form {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 560px) {{
      main {{ padding: 16px; }}
      .grid, form {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>SYNCON</h1>
    <p>Synthetic Convoy Operations Network. Local demo dashboard for the Logistics Phantom architecture.</p>
  </header>
  <main>
    {_message_html(message)}
    <section class="panel">
      <h2>Mission Setup</h2>
      <form method="post" action="/run">
        <div>
          <label for="run_id">Run ID</label>
          <input id="run_id" name="run_id" value="{selected_run}" pattern="[A-Za-z0-9_.-]+" required>
        </div>
        <div>
          <label for="phantoms">Phantom Records</label>
          <input id="phantoms" name="phantoms" type="number" min="1" max="10000" value="{html.escape(str(default_phantoms))}" required>
        </div>
        <div>
          <label for="contaminated">Seeded Unsafe Records</label>
          <input id="contaminated" name="contaminated" type="number" min="0" max="50" value="{html.escape(str(default_contaminated))}" required>
        </div>
        <div>
          <label for="seed">Seed</label>
          <input id="seed" name="seed" type="number" min="0" max="999999" value="{html.escape(str(default_seed))}" required>
        </div>
        <button type="submit">Run Demo</button>
      </form>
    </section>
    <section>
      <h2>Run Summary</h2>
      <div class="grid">
        {_metric("Protected Convoys", scenario.get("real_convoy_count", "-"))}
        {_metric("Phantom Records", _fmt_int(scenario.get("phantom_count")))}
        {_metric("Rejected Records", _fmt_int(validation.get("rejected_count")))}
        {_metric("Red-Team SNR", _fmt_float(red_team.get("snr"), 4))}
      </div>
    </section>
    <section>
      <h2>Validation And Red-Team Metrics</h2>
      <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Approved records</td><td>{_fmt_int(validation.get("approved_count"))}</td></tr>
        <tr><td>Approval rate</td><td>{_fmt_percent(validation.get("approval_rate"))}</td></tr>
        <tr><td>Validation elapsed</td><td>{_fmt_float(validation.get("elapsed_ms"), 3)} ms</td></tr>
        <tr><td>Seeded unsafe rejected</td><td>{html.escape(str(validation.get("all_seeded_unsafe_rejected", "-")))}</td></tr>
        <tr><td>Detector detection rate</td><td>{_fmt_percent(red_team.get("detection_rate"))}</td></tr>
        <tr><td>Detector precision</td><td>{_fmt_float(red_team.get("precision"), 4)}</td></tr>
      </table>
    </section>
    <section>
      <h2>Mission Timeline</h2>
      {_timeline_table(events)}
    </section>
    <section class="panel">
      <h2>Evidence Artifacts</h2>
      <div class="links">{artifact_links}</div>
    </section>
    <footer>{html.escape(BANNER)}<br>Output directory: {html.escape(str(output_dir))}</footer>
  </main>
</body>
</html>
"""


def _artifact_links(run_id: str) -> str:
    links = []
    for name in sorted(ARTIFACT_NAMES):
        href = f"/artifact/{quote(run_id)}/{quote(name)}"
        links.append(f'<a href="{href}" target="_blank">{html.escape(name)}</a>')
    return "\n".join(links)


def _message_html(message: str) -> str:
    if not message:
        return ""
    return f'<div class="notice">{html.escape(message)}</div>'


def _metric(label: str, value: object) -> str:
    return (
        '<div class="metric">'
        f'<div class="label">{html.escape(label)}</div>'
        f'<div class="value">{html.escape(str(value))}</div>'
        "</div>"
    )


def _timeline_table(events: Iterable[Dict[str, Any]]) -> str:
    rows = [
        "<table>",
        "<tr><th>Stage</th><th>Event</th><th>Detail</th></tr>",
    ]
    has_events = False
    for event in events:
        has_events = True
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(event.get('stage', '-')))}</td>"
            f"<td>{html.escape(str(event.get('event', '-')))}</td>"
            f"<td>{html.escape(str(event.get('detail', '-')))}</td>"
            "</tr>"
        )
    if not has_events:
        rows.append('<tr><td colspan="3">No run artifacts found yet.</td></tr>')
    rows.append("</table>")
    return "\n".join(rows)


def _fmt_int(value: object) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    return "-"


def _fmt_float(value: object, decimals: int) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.{decimals}f}"
    return "-"


def _fmt_percent(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.2%}"
    return "-"


def _safe_run_id(value: str) -> str:
    if not RUN_ID_PATTERN.fullmatch(value):
        raise ValueError("run_id may contain only letters, numbers, dots, hyphens, and underscores")
    return value


def _bounded_int(value: str, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"expected integer, got {value!r}") from exc
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"value must be between {minimum} and {maximum}")
    return parsed


def _first(form: Dict[str, list[str]], key: str, default: str) -> str:
    values = form.get(key)
    return values[0] if values else default
