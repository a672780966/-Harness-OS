"""Preview Server — local read-only static file server.

Serves files from a given directory on a local port.
No external service calls, no file writes, no agent control.
"""

from __future__ import annotations

import http.server
import os
import socket
import sys
from typing import Optional


def serve_preview(
    directory: str,
    port: int = 8080,
    open_browser: bool = False,
) -> None:
    """Start a local read-only HTTP server for dashboard preview.

    Args:
        directory: Directory containing index.html and assets.
        port: Local port to bind (default: 8080).
        open_browser: Whether to suggest opening browser (no-op in CLI).

    Raises:
        SystemExit: If directory doesn't exist or port is in use.
    """
    doc_root = os.path.abspath(directory)
    if not os.path.isdir(doc_root):
        print(f"Error: Directory '{doc_root}' not found", file=sys.stderr)
        sys.exit(1)

    index_path = os.path.join(doc_root, "index.html")
    if not os.path.isfile(index_path):
        print(f"Warning: No index.html found in '{doc_root}'", file=sys.stderr)

    # Check port availability
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        sock.close()
    except OSError:
        print(f"Error: Port {port} is already in use", file=sys.stderr)
        sys.exit(1)

    class ReadOnlyHandler(http.server.SimpleHTTPRequestHandler):
        """Read-only handler that refuses PUT/POST/DELETE."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=doc_root, **kwargs)

        def do_PUT(self) -> None:
            self.send_response(403)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Forbidden: read-only server")

        def do_POST(self) -> None:
            self.send_response(403)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Forbidden: read-only server")

        def do_DELETE(self) -> None:
            self.send_response(403)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Forbidden: read-only server")

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            print(f"[preview] {args[0]} {args[1]} {args[2]}", file=sys.stderr)

    server = http.server.HTTPServer(("127.0.0.1", port), ReadOnlyHandler)

    print(f"✅ Harness Copilot Dashboard — 本地预览", file=sys.stderr)
    print(f"   URL: http://127.0.0.1:{port}", file=sys.stderr)
    print(f"   目录: {doc_root}", file=sys.stderr)
    print(f"   只读模式: 是 (无写入权限)", file=sys.stderr)
    print(f"   按 Ctrl+C 停止服务", file=sys.stderr)

    if open_browser:
        print(f"   请在浏览器中打开 http://127.0.0.1:{port}", file=sys.stderr)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  预览服务已停止", file=sys.stderr)
        server.server_close()
