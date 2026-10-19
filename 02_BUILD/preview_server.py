#!/usr/bin/env python3
"""Local preview of ../01_SITE at http://127.0.0.1:4173 with caching off, so every rebuild shows at once."""
import functools
import http.server
from pathlib import Path

SITE = str(Path(__file__).resolve().parent.parent / "01_SITE")


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


http.server.ThreadingHTTPServer(("127.0.0.1", 4173), functools.partial(Handler, directory=SITE)).serve_forever()
