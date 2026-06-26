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

from .exporter import EXPORT_MANIFEST_NAME, EXPORT_REPORT_NAME, export_run
from .runner import BANNER, SCENARIO_TEMPLATES, get_scenario_template, run_demo

ARTIFACT_NAMES = {
    "scenario.json",
    "phantoms.json",
    "validation.json",
    "red_team.json",
    "timeline.json",
    "REPORT.md",
}
EXPORT_ARTIFACT_NAMES = {
    EXPORT_REPORT_NAME,
    EXPORT_MANIFEST_NAME,
    "scenario.json",
    "validation.json",
    "red_team.json",
    "timeline.json",
    "REPORT.md",
    "phantoms.json",
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
                run_summaries = load_run_registry(output_dir)
                body = render_dashboard(
                    output_dir=output_dir,
                    run_id=run_id,
                    artifacts=artifacts,
                    run_summaries=run_summaries,
                    message=message,
                )
                self._send_html(body)
                return
            if parsed.path.startswith("/artifact/"):
                self._send_artifact(parsed.path)
                return
            if parsed.path.startswith("/export-artifact/"):
                self._send_export_artifact(parsed.path)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            parsed = urlparse(self.path)
            if parsed.path == "/export":
                self._handle_export()
                return
            if parsed.path != "/run":
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return

            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length).decode("utf-8")
            form = parse_qs(payload)
            try:
                run_id = _safe_run_id(_first(form, "run_id", default_run_id))
                scenario_key = _first(form, "scenario", "demo")
                template = get_scenario_template(scenario_key)
                phantom_count = _bounded_int(_first(form, "phantoms", "10000"), 1, 10000)
                contaminated = _bounded_int(_first(form, "contaminated", "5"), 0, 50)
                seed = _bounded_int(_first(form, "seed", "42"), 0, 999999)
                run_demo(
                    output_dir=output_dir,
                    run_id=run_id,
                    scenario_key=template.key,
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
                    run_summaries=load_run_registry(output_dir),
                    message=f"Input error: {exc}",
                )
                self._send_html(body, status=HTTPStatus.BAD_REQUEST)

        def _handle_export(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length).decode("utf-8")
            form = parse_qs(payload)
            run_id = default_run_id
            try:
                run_id = _safe_run_id(_first(form, "run_id", default_run_id))
                include_phantoms = _first(form, "include_phantoms", "0") == "1"
                export_dashboard_run(
                    output_dir=output_dir,
                    run_id=run_id,
                    include_phantoms=include_phantoms,
                )
                location = f"/?run_id={quote(run_id)}&message=Executive+export+ready"
                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", location)
                self.end_headers()
            except (FileNotFoundError, ValueError) as exc:
                artifacts = load_run_artifacts(output_dir / run_id)
                body = render_dashboard(
                    output_dir=output_dir,
                    run_id=run_id,
                    artifacts=artifacts,
                    run_summaries=load_run_registry(output_dir),
                    message=f"Export error: {exc}",
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

        def _send_export_artifact(self, path: str) -> None:
            parts = [unquote(p) for p in path.split("/") if p]
            if len(parts) != 3:
                self.send_error(HTTPStatus.NOT_FOUND, "Export artifact not found")
                return
            _, run_id, filename = parts
            try:
                run_id = _safe_run_id(run_id)
                if filename not in EXPORT_ARTIFACT_NAMES:
                    raise ValueError("unknown export artifact")
            except ValueError:
                self.send_error(HTTPStatus.BAD_REQUEST, "Invalid export artifact")
                return

            artifact_path = dashboard_export_root(output_dir) / run_id / filename
            if not artifact_path.exists():
                self.send_error(HTTPStatus.NOT_FOUND, "Export artifact not found")
                return

            data = artifact_path.read_bytes()
            content_type = "text/markdown; charset=utf-8" if filename.endswith(".md") else "application/json"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
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


def dashboard_export_root(output_dir: Path) -> Path:
    """Return the dashboard export root paired with a run output directory."""
    return output_dir.parent / "exports"


def export_dashboard_run(
    output_dir: Path,
    run_id: str,
    include_phantoms: bool = False,
) -> Dict[str, str]:
    """Export a dashboard run into the paired executive export directory."""
    return export_run(
        run_dir=output_dir / _safe_run_id(run_id),
        output_dir=dashboard_export_root(output_dir),
        include_phantoms=include_phantoms,
    )


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


def load_run_registry(output_dir: Path) -> list[Dict[str, Any]]:
    """Load compact summaries for all generated SYNCON runs."""
    summaries: list[Dict[str, Any]] = []
    if not output_dir.exists():
        return summaries

    for run_dir in sorted(output_dir.iterdir(), key=lambda p: p.name):
        if not run_dir.is_dir():
            continue
        artifacts = load_run_artifacts(run_dir)
        scenario = artifacts.get("scenario")
        if not isinstance(scenario, dict):
            continue
        validation = artifacts.get("validation", {})
        red_team = artifacts.get("red_team", {})
        timeline = artifacts.get("timeline", {})
        summaries.append(
            {
                "run_id": scenario.get("run_id", run_dir.name),
                "scenario_id": scenario.get("scenario_id", "-"),
                "scenario_template": scenario.get("scenario_template", "demo"),
                "scenario_label": scenario.get("scenario_label", "Demo"),
                "phantom_count": scenario.get("phantom_count"),
                "contaminated_phantoms": scenario.get("contaminated_phantoms"),
                "approved_count": validation.get("approved_count"),
                "rejected_count": validation.get("rejected_count"),
                "snr": red_team.get("snr"),
                "detection_rate": red_team.get("detection_rate"),
                "completed_at_utc": scenario.get("completed_at_utc", "-"),
                "event_count": len(timeline.get("events", [])) if isinstance(timeline, dict) else 0,
            }
        )

    return sorted(
        summaries,
        key=lambda item: (
            str(item.get("completed_at_utc", "")),
            str(item.get("run_id", "")),
        ),
        reverse=True,
    )


def generate_comparison_insights(summaries: list[Dict[str, Any]]) -> list[Dict[str, str]]:
    """Generate deterministic reviewer insights across completed runs."""
    complete = [summary for summary in summaries if isinstance(summary.get("phantom_count"), int)]
    if len(complete) < 2:
        return [
            {
                "title": "More runs needed",
                "body": "Generate at least two scenario runs to unlock comparison insights.",
            }
        ]

    insights: list[Dict[str, str]] = []
    volume_leader = max(complete, key=lambda item: int(item.get("phantom_count", 0)))
    rejection_leader = max(complete, key=lambda item: int(item.get("rejected_count", 0) or 0))
    snr_values = [item for item in complete if isinstance(item.get("snr"), (int, float))]
    detection_values = [item for item in complete if isinstance(item.get("detection_rate"), (int, float))]
    scenario_labels = sorted({str(item.get("scenario_label", "Unknown")) for item in complete})

    insights.append(
        {
            "title": "Highest synthetic volume",
            "body": (
                f"{volume_leader.get('run_id', '-')} produced "
                f"{_fmt_int(volume_leader.get('phantom_count'))} phantom records under the "
                f"{volume_leader.get('scenario_label', 'Unknown')} profile."
            ),
        }
    )
    insights.append(
        {
            "title": "Strongest validation exercise",
            "body": (
                f"{rejection_leader.get('run_id', '-')} rejected "
                f"{_fmt_int(rejection_leader.get('rejected_count'))} seeded unsafe records, "
                "highlighting Agent C boundary enforcement."
            ),
        }
    )
    if snr_values:
        lowest_snr = min(snr_values, key=lambda item: float(item.get("snr", 0.0)))
        insights.append(
            {
                "title": "Lowest red-team SNR",
                "body": (
                    f"{lowest_snr.get('run_id', '-')} reported SNR "
                    f"{_fmt_float(lowest_snr.get('snr'), 4)}, a simplified prototype metric "
                    "for reviewer comparison only."
                ),
            }
        )
    if detection_values:
        highest_detection = max(detection_values, key=lambda item: float(item.get("detection_rate", 0.0)))
        insights.append(
            {
                "title": "Detection-rate watch item",
                "body": (
                    f"{highest_detection.get('run_id', '-')} has the highest detector rate at "
                    f"{_fmt_percent(highest_detection.get('detection_rate'))}, useful for comparing "
                    "scenario pressure without making operational claims."
                ),
            }
        )
    insights.append(
        {
            "title": "Scenario coverage",
            "body": (
                f"{len(scenario_labels)} scenario profile(s) represented: "
                f"{', '.join(scenario_labels)}."
            ),
        }
    )
    return insights


def render_dashboard(
    output_dir: Path,
    run_id: str,
    artifacts: Dict[str, Any],
    run_summaries: list[Dict[str, Any]] | None = None,
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
    selected_scenario = str(scenario.get("scenario_template", "demo"))
    scenario_options = _scenario_options(selected_scenario)
    artifact_links = _artifact_links(run_id)
    export_links = _export_links(run_id, dashboard_export_root(output_dir))
    scenario_label = html.escape(str(scenario.get("scenario_id", "synthetic-contested-logistics-demo")))
    run_label = html.escape(run_id)
    registry = run_summaries if run_summaries is not None else load_run_registry(output_dir)
    comparison_insights = generate_comparison_insights(registry)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SYNCON Dashboard</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #071017;
      --bg-2: #0d1822;
      --panel: #111d28;
      --panel-2: #142331;
      --ink: #eef6fb;
      --muted: #8fa2b2;
      --line: #263746;
      --line-strong: #335064;
      --accent: #32d3c7;
      --accent-strong: #7df5e8;
      --blue: #6ca8ff;
      --ok: #47d16c;
      --warn: #e2b84d;
      --danger: #ff6b6b;
      --shadow: 0 18px 44px rgba(0, 0, 0, 0.28);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background:
        linear-gradient(180deg, rgba(13, 28, 39, 0.95), rgba(7, 16, 23, 1) 360px),
        var(--bg);
      color: var(--ink);
      line-height: 1.45;
    }}
    header {{
      background:
        linear-gradient(90deg, rgba(50, 211, 199, 0.13), rgba(108, 168, 255, 0.05)),
        #0a141d;
      color: #fff;
      padding: 26px 28px;
      border-bottom: 1px solid var(--line-strong);
    }}
    .topbar {{
      max-width: 1180px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .mark {{
      width: 42px;
      height: 42px;
      border: 1px solid rgba(50, 211, 199, 0.7);
      border-radius: 8px;
      display: grid;
      place-items: center;
      color: var(--accent-strong);
      font-weight: 800;
      background: rgba(50, 211, 199, 0.08);
      box-shadow: 0 0 28px rgba(50, 211, 199, 0.13);
    }}
    header h1 {{
      margin: 0;
      font-size: 30px;
      letter-spacing: 0;
    }}
    header p {{
      margin: 6px 0 0;
      color: #b8c8d6;
      max-width: 1100px;
    }}
    .status-strip {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }}
    .chip {{
      border: 1px solid rgba(50, 211, 199, 0.35);
      background: rgba(17, 29, 40, 0.8);
      color: #d6fbf6;
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      white-space: nowrap;
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
      color: #f4fbff;
    }}
    .notice {{
      background: rgba(226, 184, 77, 0.12);
      border: 1px solid rgba(226, 184, 77, 0.45);
      color: #ffe3a3;
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
      box-shadow: var(--shadow);
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
      color: #ffffff;
    }}
    .metric.primary {{
      border-color: rgba(50, 211, 199, 0.5);
      background: linear-gradient(180deg, rgba(50, 211, 199, 0.10), rgba(17, 29, 40, 1));
    }}
    .metric.primary .value {{
      color: var(--accent-strong);
    }}
    .mission-brief {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 14px;
      align-items: stretch;
    }}
    .brief-copy {{
      color: #c5d5df;
      margin: 0;
    }}
    .brief-list {{
      margin: 12px 0 0;
      padding-left: 18px;
      color: #d8e6ef;
    }}
    .brief-aside {{
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 14px;
    }}
    .brief-aside div {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      margin-bottom: 4px;
    }}
    .brief-aside strong {{
      display: block;
      color: #fff;
      overflow-wrap: anywhere;
    }}
    form {{
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 12px;
      align-items: end;
    }}
    label {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
      text-transform: uppercase;
    }}
    input, select {{
      width: 100%;
      padding: 9px 10px;
      border: 1px solid var(--line-strong);
      border-radius: 5px;
      font-size: 14px;
      background: #09131c;
      color: var(--ink);
    }}
    input:focus, select:focus {{
      outline: 2px solid rgba(50, 211, 199, 0.35);
      border-color: var(--accent);
    }}
    button {{
      background: var(--accent);
      color: #071017;
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
      color: #dce8ef;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      background: #0c1822;
    }}
    tr:hover td {{
      background: rgba(50, 211, 199, 0.04);
    }}
    .run-link {{
      color: var(--accent-strong);
      font-weight: 700;
      text-decoration: none;
    }}
    .run-link:hover {{ text-decoration: underline; }}
    .selected-run td {{
      background: rgba(50, 211, 199, 0.08);
    }}
    .status-badge {{
      display: inline-block;
      border: 1px solid rgba(71, 209, 108, 0.4);
      color: #b9f5c8;
      background: rgba(71, 209, 108, 0.08);
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 12px;
      white-space: nowrap;
    }}
    .insights {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}
    .insight {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 14px;
      min-height: 118px;
    }}
    .insight-title {{
      color: var(--accent-strong);
      font-weight: 700;
      margin-bottom: 6px;
    }}
    .insight-body {{
      color: #c5d5df;
    }}
    .timeline {{
      display: grid;
      gap: 10px;
    }}
    .timeline-item {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px 14px;
      display: grid;
      grid-template-columns: 150px 1fr;
      gap: 12px;
    }}
    .stage {{
      color: var(--accent-strong);
      font-size: 12px;
      text-transform: uppercase;
      font-weight: 700;
    }}
    .timeline-title {{
      color: #fff;
      font-weight: 700;
      margin-bottom: 3px;
    }}
    .timeline-detail {{
      color: #b9c9d5;
    }}
    .links a {{
      display: inline-block;
      margin: 0 8px 8px 0;
      color: var(--accent-strong);
      font-weight: 700;
      border: 1px solid rgba(50, 211, 199, 0.35);
      border-radius: 5px;
      padding: 8px 10px;
      text-decoration: none;
      background: rgba(50, 211, 199, 0.07);
    }}
    .export-panel {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      align-items: center;
    }}
    .export-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }}
    .export-actions form {{
      display: block;
    }}
    .secondary-button {{
      background: transparent;
      color: var(--accent-strong);
      border: 1px solid rgba(50, 211, 199, 0.45);
    }}
    .secondary-button:hover {{
      background: rgba(50, 211, 199, 0.09);
    }}
    footer {{
      color: var(--muted);
      font-size: 12px;
      padding-top: 8px;
    }}
    @media (max-width: 900px) {{
      .grid, form, .insights {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .mission-brief {{ grid-template-columns: 1fr; }}
      .topbar {{ align-items: flex-start; flex-direction: column; }}
      .status-strip {{ justify-content: flex-start; }}
    }}
    @media (max-width: 560px) {{
      main {{ padding: 16px; }}
      .grid, form, .insights {{ grid-template-columns: 1fr; }}
      .timeline-item {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div class="brand">
        <div class="mark">SC</div>
        <div>
          <h1>SYNCON</h1>
          <p>Synthetic Convoy Operations Network. Local demo dashboard for the Logistics Phantom architecture.</p>
        </div>
      </div>
      <div class="status-strip">
        <span class="chip">Synthetic Demo</span>
        <span class="chip">Local Only</span>
        <span class="chip">Not Deployment Ready</span>
      </div>
    </div>
  </header>
  <main>
    {_message_html(message)}
    <section class="panel">
      <h2>Mission Command Brief</h2>
      <div class="mission-brief">
        <div>
          <p class="brief-copy">SYNCON runs a controlled synthetic convoy lifecycle: configure the scenario, generate phantom telemetry, validate every record through Agent C, evaluate the red-team detector, and export evidence artifacts.</p>
          <ul class="brief-list">
            <li>Pre-mission setup stays synthetic and reproducible.</li>
            <li>During-mission simulation records generated volume and validation decisions.</li>
            <li>Post-mission output produces reviewable evidence files.</li>
          </ul>
        </div>
        <div class="brief-aside">
          <div>Active Run</div>
          <strong>{run_label}</strong>
          <div style="margin-top: 12px;">Scenario</div>
          <strong>{scenario_label}</strong>
        </div>
      </div>
    </section>
    <section class="panel">
      <h2>Mission Setup</h2>
      <form method="post" action="/run">
        <div>
          <label for="run_id">Run ID</label>
          <input id="run_id" name="run_id" value="{selected_run}" pattern="[A-Za-z0-9_.-]+" required>
        </div>
        <div>
          <label for="scenario">Scenario</label>
          <select id="scenario" name="scenario">{scenario_options}</select>
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
      <h2>Run Registry And Comparison</h2>
      {_run_registry_table(registry, run_id)}
    </section>
    <section>
      <h2>Comparison Insights</h2>
      {_comparison_insight_cards(comparison_insights)}
    </section>
    <section>
      <h2>Run Summary</h2>
      <div class="grid">
        {_metric("Protected Convoys", scenario.get("real_convoy_count", "-"), primary=True)}
        {_metric("Phantom Records", _fmt_int(scenario.get("phantom_count")), primary=True)}
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
      {_timeline_cards(events)}
    </section>
    <section class="panel">
      <h2>Evidence Artifacts</h2>
      <div class="links">{artifact_links}</div>
    </section>
    <section class="panel">
      <h2>Executive Export</h2>
      <div class="export-panel">
        <div>
          <p class="brief-copy">Generate a reviewer-ready leave-behind package for this run. The compact export includes the executive report, manifest, detailed report, and core JSON artifacts.</p>
          <div class="links">{export_links}</div>
        </div>
        <div class="export-actions">
          <form method="post" action="/export">
            <input type="hidden" name="run_id" value="{selected_run}">
            <button type="submit">Export Brief</button>
          </form>
          <form method="post" action="/export">
            <input type="hidden" name="run_id" value="{selected_run}">
            <input type="hidden" name="include_phantoms" value="1">
            <button class="secondary-button" type="submit">Export With Payload</button>
          </form>
        </div>
      </div>
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


def _export_links(run_id: str, export_root: Path) -> str:
    export_dir = export_root / run_id
    if not export_dir.exists():
        return '<span class="chip">No export generated</span>'

    links = []
    for name in [EXPORT_REPORT_NAME, EXPORT_MANIFEST_NAME, "REPORT.md"]:
        path = export_dir / name
        if path.exists():
            href = f"/export-artifact/{quote(run_id)}/{quote(name)}"
            links.append(f'<a href="{href}" target="_blank">{html.escape(name)}</a>')
    return "\n".join(links) if links else '<span class="chip">Export pending</span>'


def _run_registry_table(summaries: list[Dict[str, Any]], selected_run: str) -> str:
    if not summaries:
        return (
            '<div class="panel">'
            "<p class=\"brief-copy\">No completed runs found yet. Run a mission to populate the registry.</p>"
            "</div>"
        )

    rows = [
        "<table>",
        "<tr><th>Run</th><th>Scenario</th><th>Phantoms</th><th>Rejected</th><th>SNR</th><th>Detection</th><th>Events</th><th>Status</th></tr>",
    ]
    for summary in summaries:
        run_id = str(summary.get("run_id", "-"))
        row_class = ' class="selected-run"' if run_id == selected_run else ""
        href = f"/?run_id={quote(run_id)}"
        rows.append(
            f"<tr{row_class}>"
            f'<td><a class="run-link" href="{href}">{html.escape(run_id)}</a></td>'
            f"<td>{html.escape(str(summary.get('scenario_label', '-')))}</td>"
            f"<td>{_fmt_int(summary.get('phantom_count'))}</td>"
            f"<td>{_fmt_int(summary.get('rejected_count'))}</td>"
            f"<td>{_fmt_float(summary.get('snr'), 4)}</td>"
            f"<td>{_fmt_percent(summary.get('detection_rate'))}</td>"
            f"<td>{_fmt_int(summary.get('event_count'))}</td>"
            '<td><span class="status-badge">Evidence Ready</span></td>'
            "</tr>"
        )
    rows.append("</table>")
    return "\n".join(rows)


def _comparison_insight_cards(insights: list[Dict[str, str]]) -> str:
    rows = ['<div class="insights">']
    for insight in insights:
        rows.append(
            '<div class="insight">'
            f'<div class="insight-title">{html.escape(insight.get("title", "-"))}</div>'
            f'<div class="insight-body">{html.escape(insight.get("body", "-"))}</div>'
            "</div>"
        )
    rows.append("</div>")
    return "\n".join(rows)


def _message_html(message: str) -> str:
    if not message:
        return ""
    return f'<div class="notice">{html.escape(message)}</div>'


def _scenario_options(selected: str) -> str:
    options = []
    for key, template in SCENARIO_TEMPLATES.items():
        selected_attr = " selected" if key == selected else ""
        label = f"{template.label} - {template.review_focus}"
        options.append(
            f'<option value="{html.escape(key)}"{selected_attr}>{html.escape(label)}</option>'
        )
    return "\n".join(options)


def _metric(label: str, value: object, primary: bool = False) -> str:
    class_name = "metric primary" if primary else "metric"
    return (
        f'<div class="{class_name}">'
        f'<div class="label">{html.escape(label)}</div>'
        f'<div class="value">{html.escape(str(value))}</div>'
        "</div>"
    )


def _timeline_cards(events: Iterable[Dict[str, Any]]) -> str:
    rows = ['<div class="timeline">']
    has_events = False
    for event in events:
        has_events = True
        rows.append(
            '<div class="timeline-item">'
            f'<div class="stage">{html.escape(str(event.get("stage", "-")))}</div>'
            "<div>"
            f'<div class="timeline-title">{html.escape(str(event.get("event", "-")))}</div>'
            f'<div class="timeline-detail">{html.escape(str(event.get("detail", "-")))}</div>'
            "</div>"
            "</div>"
        )
    if not has_events:
        rows.append('<div class="timeline-item"><div class="stage">Standby</div><div><div class="timeline-title">No run artifacts found yet.</div><div class="timeline-detail">Run the demo to populate the mission timeline.</div></div></div>')
    rows.append("</div>")
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
