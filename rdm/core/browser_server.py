"""Local HTTP server for browser extension: receive download URLs and optionally launch RDM."""

import queue
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Optional
from urllib.parse import parse_qs, unquote, urlparse


DEFAULT_PORT = 8765

# Thread-safe queue for URLs received from browser; main thread polls this
_url_queue: queue.Queue = queue.Queue()


class _Handler(BaseHTTPRequestHandler):
    """Handle GET /add?url=... and POST with url in body or form."""

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/add" or parsed.path == "/":
            qs = parse_qs(parsed.query)
            urls = qs.get("url", []) + qs.get("u", [])
            if urls:
                _url_queue.put(urls[0])
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/add" or self.path == "/":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8", errors="replace")
            url = body.strip()
            if "url=" in body:
                for part in body.split("&"):
                    if part.startswith("url="):
                        url = unquote(part[4:].strip())
                        break
            if url:
                _url_queue.put(url)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            return
        self.send_response(404)
        self.end_headers()


class BrowserExtServer:
    """Run a small HTTP server in a background thread to receive URLs from the browser extension."""

    def __init__(self, port: int = DEFAULT_PORT):
        self._port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._on_url: Optional[Callable[[str], None]] = None

    def set_on_url(self, callback: Callable[[str], None]) -> None:
        self._on_url = callback

    def start(self) -> bool:
        try:
            self._server = HTTPServer(("127.0.0.1", self._port), _Handler)
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            self._thread.start()
            return True
        except OSError:
            return False

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None

    def drain_queue(self) -> None:
        """Process any URLs received from the browser (call from main thread)."""
        while True:
            try:
                url = _url_queue.get_nowait()
                if self._on_url and url:
                    self._on_url(url)
            except queue.Empty:
                break

    @property
    def port(self) -> int:
        return self._port
