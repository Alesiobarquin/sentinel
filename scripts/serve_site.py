"""Preview the exact Pages export under /sentinel, bound only to loopback."""

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1] / "apps/web/out"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def translate_path(self, path):
        url = urlsplit(path)
        if url.path == "/sentinel":
            return str(ROOT)
        if not url.path.startswith("/sentinel/"):
            return str(ROOT / "__missing_route__")
        return super().translate_path(url.path.removeprefix("/sentinel"))

    def list_directory(self, path):
        self.send_error(404)
        return None

    def send_error(self, code, message=None, explain=None):
        fallback = ROOT / "404.html"
        if code == 404 and fallback.is_file():
            body = fallback.read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
            return
        super().send_error(code, message, explain)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()
    if not (ROOT / "index.html").is_file():
        parser.error("Run npm run build in apps/web first")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Static export: http://127.0.0.1:{args.port}/sentinel/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
