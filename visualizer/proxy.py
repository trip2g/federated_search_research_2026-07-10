#!/usr/bin/env python3
"""Tiny CORS proxy: browser -> localhost:8787 -> trip2g MCP endpoint.

The hub does not send Access-Control-Allow-Origin headers, so the browser
cannot call it directly. Run `python3 proxy.py` and point the visualizer's
endpoint field at http://localhost:8787 (the default).
"""
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TARGET = os.environ.get("MCP_TARGET", "https://trip2g.com/_system/mcp")
PORT = int(os.environ.get("PORT", "8787"))


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        # custom User-Agent: the hub 403s default library UAs
        req = urllib.request.Request(TARGET, data=body, headers={
            "Content-Type": "application/json",
            "User-Agent": "mcp-graph-visualizer/1.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data, code = r.read(), r.status
        except urllib.error.HTTPError as e:
            data, code = e.read(), e.code
        except Exception as e:
            data = json.dumps({"jsonrpc": "2.0", "id": None,
                               "error": {"code": -32000, "message": f"proxy: {e}"}}).encode()
            code = 502
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"MCP CORS proxy: http://localhost:{PORT} -> {TARGET}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
