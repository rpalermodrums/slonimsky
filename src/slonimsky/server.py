"""Tiny stdlib web server for the UI, plus a static-site builder.

Routes:
  /                   the single-page UI (web/index.html)
  /data/catalog.json  the catalog (built once at startup)
  /api/midi           ?id=ditone:-1,2,9&root=60&direction=up&tempo=100
  /<file>             other files from web/
"""

from __future__ import annotations

import json
import mimetypes
import shutil
import webbrowser
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .catalog import build_catalog, dumps
from .midi import to_midi
from .realize import realize
from .thesaurus import parse_pattern_id

WEB_FILES = ("index.html", "styles.css", "engine.js", "audio.js", "app.js")
VENDOR_FILES = ("vendor/abcjs-basic-min.js", "vendor/abcjs-LICENSE.txt")


def _web_root():
    return resources.files("slonimsky").joinpath("web")


class Handler(BaseHTTPRequestHandler):
    server_version = "slonimsky"

    def __init__(self, *args, catalog: bytes, **kwargs):
        self.catalog = catalog
        super().__init__(*args, **kwargs)

    def log_request(self, code="-", size="-"):  # only log problems
        if not str(getattr(code, "value", code)).startswith(("2", "3")):
            super().log_request(code, size)

    def _send(self, body: bytes, ctype: str, status: int = 200, extra: dict | None = None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str):
        self._send(json.dumps({"error": message}).encode(), "application/json", status)

    def do_GET(self):  # noqa: N802
        url = urlparse(self.path)
        path = url.path
        if path == "/data/catalog.json":
            return self._send(self.catalog, "application/json")
        if path == "/api/midi":
            return self._midi(parse_qs(url.query))
        rel = "index.html" if path in ("", "/") else path.lstrip("/")
        if rel not in WEB_FILES + VENDOR_FILES:
            return self._error(HTTPStatus.NOT_FOUND, f"not found: {path}")
        data = _web_root().joinpath(rel).read_bytes()
        ctype = mimetypes.guess_type(rel)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype.endswith("javascript"):
            ctype += "; charset=utf-8"
        self._send(data, ctype)

    def _midi(self, q: dict):
        try:
            prog, cell = parse_pattern_id(q["id"][0])
            root = int(q.get("root", ["60"])[0])
            direction = q.get("direction", ["up"])[0]
            tempo = float(q.get("tempo", ["100"])[0])
            notes = realize(prog, cell, root, direction)
        except (KeyError, ValueError) as e:
            return self._error(HTTPStatus.BAD_REQUEST, str(e))
        name = f"slonimsky_{prog.key}_{'_'.join(str(x) for x in cell[1:])}.mid"
        self._send(to_midi(notes, tempo_bpm=tempo), "audio/midi", extra={
            "Content-Disposition": f'attachment; filename="{name}"'
        })


def make_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    catalog = dumps(build_catalog()).encode("utf-8")
    return ThreadingHTTPServer((host, port), partial(Handler, catalog=catalog))


def serve(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = False) -> None:
    httpd = make_server(host, port)
    url = f"http://{host}:{httpd.server_address[1]}/"
    print(f"Slonimsky UI on {url}  (Ctrl+C to stop)")
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        httpd.server_close()


def build_site(directory: Path, single_file: bool = False) -> Path:
    """Write the UI as static files (or one self-contained HTML file)."""
    directory.mkdir(parents=True, exist_ok=True)
    catalog = dumps(build_catalog())
    web = _web_root()
    if not single_file:
        for rel in WEB_FILES + VENDOR_FILES:
            target = directory / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with web.joinpath(rel).open("rb") as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
        (directory / "data").mkdir(exist_ok=True)
        (directory / "data" / "catalog.json").write_text(catalog, encoding="utf-8")
        return directory / "index.html"

    html = web.joinpath("index.html").read_text("utf-8")

    def inline_script(name: str) -> str:
        code = web.joinpath(name).read_text("utf-8").replace("</script", "<\\/script")
        return f"<script>\n{code}\n</script>"

    css = web.joinpath("styles.css").read_text("utf-8")
    html = html.replace('<link rel="stylesheet" href="styles.css" />', f"<style>\n{css}\n</style>")
    for name in ("vendor/abcjs-basic-min.js", "engine.js", "audio.js", "app.js"):
        tag = f'<script src="{name}"></script>'
        if name == "app.js":
            data = catalog.replace("</", "<\\/")
            html = html.replace(tag, f"<script>window.SLONIMSKY_CATALOG = {data};</script>\n{inline_script(name)}")
        else:
            html = html.replace(tag, inline_script(name))
    out = directory / "index.html"
    out.write_text(html, encoding="utf-8")
    return out
