"""Local companion dashboard inspired by a desktop status island, without OS hooks."""
from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs


def render_dashboard(core: object, reply: str = "") -> str:
    """Render a portable local page; all dynamic values are escaped."""
    mission_rows = "".join(
        f"<li><b>{escape(mission.state.value)}</b> — {escape(mission.objective)}</li>"
        for mission in core.missions.values()
    ) or "<li>Nenhuma missão em andamento.</li>"
    response = f'<section class="reply">{escape(reply)}</section>' if reply else ""
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>JARVIS Essence</title>
<style>
body{{margin:0;background:#080d16;color:#e9f7ff;font:16px system-ui,sans-serif;min-height:100vh;display:grid;place-items:start center}}
.island{{margin:22px;width:min(760px,calc(100% - 32px));background:linear-gradient(135deg,#142840,#08111f);border:1px solid #3c7194;border-radius:28px;padding:24px;box-shadow:0 20px 70px #0008}}
.head{{display:flex;gap:18px;align-items:center}} .orb{{width:70px;height:70px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#d8ffff 0 6%,#55bde7 7% 27%,#153f69 28% 60%,#06101d 61%);box-shadow:0 0 30px #48cdf2;animation:breathe 3s ease-in-out infinite}} @keyframes breathe{{50%{{transform:scale(1.07)}}}}
h1{{margin:0;font-size:24px}} .status{{color:#7ef1b1}} form{{display:flex;gap:8px;margin-top:20px}} input{{flex:1;padding:12px;border-radius:12px;border:1px solid #5481a0;background:#07101b;color:white}} button{{padding:12px 16px;border:0;border-radius:12px;background:#57c8ed;color:#03131c;font-weight:700}} .reply{{margin-top:14px;padding:12px;border-radius:12px;background:#102238;white-space:pre-wrap}} ul{{padding-left:20px}} small{{color:#98b5c8}}
</style></head><body><main class="island"><div class="head"><div class="orb" aria-label="JARVIS companion"></div><div><h1>JARVIS ESSENCE</h1><div class="status">● ONLINE · modo {escape(core.personality.mode.value)}</div><small>Companion local — sem telemetria e sem acesso automático a aplicativos.</small></div></div>
{response}<form method="post"><input name="message" autofocus placeholder="Converse com JARVIS…"><button>Enviar</button></form><h2>Missões</h2><ul>{mission_rows}</ul><h2>Plugins</h2><pre>{escape(core.plugins.summary())}</pre></main></body></html>"""


def serve_dashboard(core: object, port: int = 8765) -> None:
    """Serve localhost only; the dashboard is not exposed to the network."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self._send(render_dashboard(core))

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            values = parse_qs(self.rfile.read(length).decode("utf-8"))
            message = values.get("message", [""])[0]
            self._send(render_dashboard(core, core.process(message)))

        def _send(self, page: str) -> None:
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"JARVIS dashboard: http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
