#!/usr/bin/env python3
"""Single entry point for the visualizer.

    OPENROUTER_KEY=sk-or-... python3 proxy.py   ->   open http://localhost:8787

Serves index.html, proxies MCP JSON-RPC (the hub sends no CORS headers, so the
browser cannot call it directly), and — when OPENROUTER_KEY is set — proxies
OpenRouter chat completions adding the Authorization header server-side, so the
key never reaches the browser. Without the env var the UI falls back to its
paste-key flow (direct OpenRouter from the browser).
"""
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TARGET = os.environ.get("MCP_TARGET", "https://trip2g.com/_system/mcp")
OPENROUTER = "https://openrouter.ai/api/v1/chat/completions"
KEY = os.environ.get("OPENROUTER_KEY", "").strip()
PORT = int(os.environ.get("PORT", "8787"))
DIR = os.path.dirname(os.path.abspath(__file__))


def forward(url, body, headers):
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.read(), r.status
    except urllib.error.HTTPError as e:
        return e.read(), e.code
    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "id": None,
                           "error": {"code": -32000, "message": f"proxy: {e}"}}).encode(), 502


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _send(self, code, data, ctype="application/json"):
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(os.path.join(DIR, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif path == "/config":
            self._send(200, json.dumps({"hasKey": bool(KEY), "mcpTarget": TARGET}).encode())
        else:
            self._send(404, b'{"error":"not found"}')

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path.split("?")[0] == "/openrouter":
            if not KEY:
                self._send(403, b'{"error":{"message":"proxy started without OPENROUTER_KEY"}}')
                return
            data, code = forward(OPENROUTER, body, {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + KEY,  # key stays server-side
            })
        else:
            # custom User-Agent: the hub 403s default library UAs
            data, code = forward(TARGET, body, {
                "Content-Type": "application/json",
                "User-Agent": "mcp-graph-visualizer/1.0",
            })
        self._send(code, data)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"visualizer: http://localhost:{PORT}  (MCP -> {TARGET}, "
          f"OpenRouter key: {'from env, server-side' if KEY else 'not set - paste in UI'})")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
