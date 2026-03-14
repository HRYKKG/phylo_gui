import argparse
import json
import mimetypes
import tempfile
import webbrowser
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
VENDOR_DIR = ROOT / "vendor"
VIEWER_DIR = ROOT / "viewer"

# Ordered list of viewer JS modules. Must be loaded in this exact sequence.
VIEWER_JS_MODULES = [
    "state",
    "dev-tools",
    "node-utils",
    "panels",
    "selection",
    "rect-select",
    "display",
    "tree-render",
    "zoom",
    "node-actions",
    "app",
]


def _required_assets():
    assets = {
        "phylotree_js": VENDOR_DIR / "phylotree" / "phylotree.js",
        "phylotree_css": VENDOR_DIR / "phylotree" / "phylotree.css",
        "underscore_js": VENDOR_DIR / "underscore" / "underscore.min.js",
        "lodash_js": VENDOR_DIR / "lodash" / "lodash.min.js",
        "viewer_css": VIEWER_DIR / "style.css",
    }
    for name in VIEWER_JS_MODULES:
        key = name.replace("-", "_") + "_js"
        assets[key] = VIEWER_DIR / (name + ".js")
    return assets


def _validate_assets():
    missing = [str(path) for path in _required_assets().values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing viewer assets:\n" + "\n".join(missing))


def _viewer_script_tags(asset_urls):
    lines = []
    for name in VIEWER_JS_MODULES:
        key = name.replace("-", "_") + "_js"
        lines.append(
            f'    <script src="{asset_urls[key]}" onerror="window.__viewerReport(\'Failed to load {name}.js\', true)"></script>'
        )
    return "\n".join(lines)


def _build_html(payload, asset_urls):
    data_json = json.dumps(payload, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{payload["title"]}</title>
    <link rel="stylesheet" href="{asset_urls["phylotree_css"]}">
    <link rel="stylesheet" href="{asset_urls["viewer_css"]}">
  </head>
  <body>
    <div id="viewer-root">
      <header class="viewer-header">
        <div>
          <p class="viewer-kicker">Phylo GUI</p>
          <h1 id="viewer-title">{payload["title"]}</h1>
        </div>
        <p id="viewer-dev-note" class="viewer-note" data-dev-only hidden>Minimal milestone: local Newick rendering with phylotree.js.</p>
      </header>
      <main class="viewer-main">
        <section class="tree-panel">
          <div class="tree-toolbar">
            <button id="zoom-in-button" type="button">Zoom In</button>
            <button id="zoom-out-button" type="button">Zoom Out</button>
            <button id="reset-view-button" type="button">Reset Zoom</button>
            <button id="fit-tree-button" type="button">Fit to Tree</button>
            <label class="toolbar-control" for="font-size-slider">
              <span>Text</span>
              <input id="font-size-slider" type="range" min="2" max="16" step="0.5" value="10">
            </label>
            <span id="font-size-indicator" class="toolbar-indicator">Text 10px</span>
            <label class="toolbar-control" for="node-size-slider">
              <span>Node</span>
              <input id="node-size-slider" type="range" min="0.5" max="4" step="0.25" value="3">
            </label>
            <span id="node-size-indicator" class="toolbar-indicator">Node 3px</span>
            <button id="rectangle-select-toggle" type="button">Rectangle Select: Off</button>
          </div>
          <p id="selection-mode-note" class="selection-mode-note">Browse mode: click nodes to inspect them.</p>
          <div id="tree-container" class="tree-container">
            <div id="selection-box" class="selection-box" hidden></div>
          </div>
        </section>
        <aside class="info-panel">
          <section id="viewer-status-section" data-dev-only hidden>
            <h2>Viewer Status</h2>
            <p id="viewer-status">Loading browser assets...</p>
          </section>
          <h2>Selected Node</h2>
          <div id="selected-node-card" class="selected-node-card is-empty">
            <p id="selected-node-empty">Click a node to inspect it.</p>
            <dl id="selected-node-details" class="selected-node-details" hidden>
              <dt>Name</dt>
              <dd id="selected-node-name"></dd>
              <dt>Type</dt>
              <dd id="selected-node-type"></dd>
              <dt>Branch length</dt>
              <dd id="selected-node-branch-length"></dd>
              <dt>Depth</dt>
              <dd id="selected-node-depth"></dd>
              <dt>Children</dt>
              <dd id="selected-node-children"></dd>
              <dt>Leaf descendants</dt>
              <dd id="selected-node-leaf-count"></dd>
            </dl>
          </div>
          <h2>Node Actions</h2>
          <div class="node-actions">
            <button id="toggle-collapse-button" type="button" disabled>Collapse Subtree</button>
            <button id="select-descendants-button" type="button" disabled>Select Descendant Leaves</button>
            <button id="select-opposite-side-button" type="button" disabled>Select Opposite-Side Leaves</button>
            <button id="clear-active-node-button" type="button" disabled>Clear Active Node</button>
          </div>
          <h2>Selected Leaves</h2>
          <div id="selected-leaves-card" class="selected-leaves-card is-empty">
            <p id="selected-leaves-summary">No leaves selected.</p>
            <div class="selected-leaf-actions">
              <button id="save-selection-json-button" type="button" disabled>{payload.get("selectionActionLabel", "Save Selection JSON")}</button>
              <button id="copy-selected-leaves-button" type="button" disabled>Copy Leaf Names</button>
              <button id="clear-selected-leaves-button" type="button" disabled>Clear Selected Leaves</button>
            </div>
            <ul id="selected-leaf-list" class="selected-leaf-list" hidden></ul>
          </div>
          <section id="viewer-input-section" data-dev-only hidden>
            <h2>Input</h2>
            <p id="viewer-summary">Newick length: {len(payload["newick"])} characters</p>
          </section>
          <section id="viewer-notes-section" data-dev-only hidden>
            <h2>Notes</h2>
            <p>This build only proves local interactive rendering. Selection/export comes next.</p>
          </section>
          <section id="viewer-debug-section" data-dev-only hidden>
            <h2>Debug</h2>
            <pre id="viewer-debug" class="viewer-debug">Waiting for initialization logs...</pre>
          </section>
        </aside>
      </main>
    </div>
    <script>
      window.__TREE_VIEWER_DATA__ = {data_json};
      document.documentElement.dataset.devMode = window.__TREE_VIEWER_DATA__ && window.__TREE_VIEWER_DATA__.devMode ? "on" : "off";
      window.__viewerReport = function (message, isError) {{
        var statusSection = document.getElementById("viewer-status-section");
        var status = document.getElementById("viewer-status");
        var debug = document.getElementById("viewer-debug");
        var devMode = document.documentElement.dataset.devMode === "on";
        if (statusSection) {{
          statusSection.hidden = !devMode && !isError;
        }}
        if (status) {{
          status.textContent = message;
          status.className = isError ? "is-error" : "";
        }}
        if (debug) {{
          debug.textContent = message;
        }}
      }};
      window.addEventListener("error", function (event) {{
        var detail = event && event.message ? event.message : "Unknown browser error";
        window.__viewerReport("Browser error: " + detail, true);
      }});
      window.addEventListener("unhandledrejection", function (event) {{
        var reason = event && event.reason ? String(event.reason) : "Unknown promise rejection";
        window.__viewerReport("Unhandled promise rejection: " + reason, true);
      }});
    </script>
    <script src="{asset_urls["underscore_js"]}" onerror="window.__viewerReport('Failed to load underscore.min.js', true)"></script>
    <script>
      window.__underscore = window._.noConflict();
      window.__viewerReport("Loaded underscore.", false);
    </script>
    <script src="{asset_urls["lodash_js"]}" onerror="window.__viewerReport('Failed to load lodash.min.js', true)"></script>
    <script>
      window._$1 = window._;
      window._ = window.__underscore;
      window.__viewerReport("Loaded lodash.", false);
    </script>
    <script src="{asset_urls["phylotree_js"]}" onerror="window.__viewerReport('Failed to load phylotree.js', true)"></script>
{_viewer_script_tags(asset_urls)}
  </body>
</html>
"""


def _read_newick(args):
    if args.newick_file:
        return Path(args.newick_file).read_text().strip()
    return args.newick_text.strip()


def _write_viewer_html(payload, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "index.html"
    assets = _required_assets()
    asset_urls = {name: path.as_uri() for name, path in assets.items()}
    html_path.write_text(_build_html(payload, asset_urls), encoding="utf-8")
    return html_path


def _default_output_dir():
    try:
        return Path(tempfile.mkdtemp(prefix="phylotree_viewer_"))
    except OSError:
        return ROOT / ".viewer_tmp"


def _asset_routes():
    assets = _required_assets()
    routes = {
        "/assets/phylotree.js": assets["phylotree_js"],
        "/assets/phylotree.css": assets["phylotree_css"],
        "/assets/underscore.min.js": assets["underscore_js"],
        "/assets/lodash.min.js": assets["lodash_js"],
        "/assets/style.css": assets["viewer_css"],
    }
    for name in VIEWER_JS_MODULES:
        key = name.replace("-", "_") + "_js"
        routes[f"/assets/viewer/{name}.js"] = assets[key]
    return routes


class _ViewerRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, html_text: str, asset_routes: dict[str, Path], selection_output: Path | None, **kwargs):
        self._html_text = html_text
        self._asset_routes = asset_routes
        self._selection_output = selection_output
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        return

    def _send_text(self, body: str, content_type: str = "text/html; charset=utf-8", status: int = 200):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, path: Path):
        mime_type, _ = mimetypes.guess_type(str(path))
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = urlparse(self.path).path
        if route in ("/", "/index.html"):
            self._send_text(self._html_text)
            return
        if route in self._asset_routes:
            self._send_file(self._asset_routes[route])
            return
        self._send_text("Not found", "text/plain; charset=utf-8", 404)

    def do_POST(self):
        route = urlparse(self.path).path
        if route != "/api/selection" or self._selection_output is None:
            self._send_text("Not found", "text/plain; charset=utf-8", 404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        payload = json.loads(raw_body.decode("utf-8"))
        self._selection_output.parent.mkdir(parents=True, exist_ok=True)
        self._selection_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._send_text(
            json.dumps({"ok": True, "path": str(self._selection_output)}, ensure_ascii=False),
            "application/json; charset=utf-8",
            200,
        )


def _serve_viewer(payload: dict, selection_output: Path, open_browser: bool):
    asset_routes = _asset_routes()
    asset_urls = {
        "phylotree_js": "/assets/phylotree.js",
        "phylotree_css": "/assets/phylotree.css",
        "underscore_js": "/assets/underscore.min.js",
        "lodash_js": "/assets/lodash.min.js",
        "viewer_css": "/assets/style.css",
    }
    for name in VIEWER_JS_MODULES:
        key = name.replace("-", "_") + "_js"
        asset_urls[key] = f"/assets/viewer/{name}.js"
    html_text = _build_html(payload, asset_urls)
    handler = partial(
        _ViewerRequestHandler,
        html_text=html_text,
        asset_routes=asset_routes,
        selection_output=selection_output,
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    url = f"http://127.0.0.1:{server.server_port}/"
    if open_browser:
        webbrowser.open(url)
    print(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Render a local interactive phylogenetic tree viewer.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--newick-file", help="Path to a Newick tree file.")
    group.add_argument("--newick-text", help="Raw Newick text.")
    parser.add_argument("--title", default="Phylo GUI Tree Viewer", help="Page title for the viewer.")
    parser.add_argument("--output-dir", help="Directory to write the generated HTML viewer into.")
    parser.add_argument("--selection-output", help="Write selected leaf names as JSON to this path via a localhost callback.")
    parser.add_argument("--no-open-browser", action="store_true", help="Generate the viewer without opening a browser.")
    args = parser.parse_args()

    _validate_assets()
    newick_text = _read_newick(args)
    if not newick_text:
        raise ValueError("Newick input is empty.")

    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    payload = {
        "title": args.title,
        "newick": newick_text,
        "devMode": False,
        "selectionApiUrl": "/api/selection" if args.selection_output else None,
        "selectionActionLabel": "Send to GUI" if args.selection_output else "Save Selection JSON",
    }
    if args.selection_output:
        _serve_viewer(payload, Path(args.selection_output), not args.no_open_browser)
        return

    html_path = _write_viewer_html(payload, output_dir)
    if not args.no_open_browser:
        webbrowser.open(html_path.as_uri())
    print(html_path)


if __name__ == "__main__":
    main()
