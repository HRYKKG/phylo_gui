import argparse
import json
import tempfile
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENDOR_DIR = ROOT / "vendor"
VIEWER_DIR = ROOT / "viewer"


def _required_assets():
    return {
        "phylotree_js": VENDOR_DIR / "phylotree" / "phylotree.js",
        "phylotree_css": VENDOR_DIR / "phylotree" / "phylotree.css",
        "underscore_js": VENDOR_DIR / "underscore" / "underscore.min.js",
        "lodash_js": VENDOR_DIR / "lodash" / "lodash.min.js",
        "app_js": VIEWER_DIR / "app.js",
        "viewer_css": VIEWER_DIR / "style.css",
    }


def _validate_assets():
    missing = [str(path) for path in _required_assets().values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing viewer assets:\n" + "\n".join(missing))


def _build_html(payload):
    assets = _required_assets()
    data_json = json.dumps(payload, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{payload["title"]}</title>
    <link rel="stylesheet" href="{assets["phylotree_css"].as_uri()}">
    <link rel="stylesheet" href="{assets["viewer_css"].as_uri()}">
  </head>
  <body>
    <div id="viewer-root">
      <header class="viewer-header">
        <div>
          <p class="viewer-kicker">Phylo GUI</p>
          <h1 id="viewer-title">{payload["title"]}</h1>
        </div>
        <p class="viewer-note">Minimal milestone: local Newick rendering with phylotree.js.</p>
      </header>
      <main class="viewer-main">
        <section class="tree-panel">
          <div class="tree-toolbar">
            <button id="zoom-in-button" type="button">Zoom In</button>
            <button id="zoom-out-button" type="button">Zoom Out</button>
            <button id="reset-view-button" type="button">Reset View</button>
            <button id="rectangle-select-toggle" type="button">Rectangle Select: Off</button>
          </div>
          <p id="selection-mode-note" class="selection-mode-note">Browse mode: click nodes to inspect them.</p>
          <div id="tree-container" class="tree-container">
            <div id="selection-box" class="selection-box" hidden></div>
          </div>
        </section>
        <aside class="info-panel">
          <h2>Viewer Status</h2>
          <p id="viewer-status">Loading browser assets...</p>
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
            <button id="clear-active-node-button" type="button" disabled>Clear Active Node</button>
          </div>
          <h2>Selected Leaves</h2>
          <div id="selected-leaves-card" class="selected-leaves-card is-empty">
            <p id="selected-leaves-summary">No leaves selected.</p>
            <div class="selected-leaf-actions">
              <button id="copy-selected-leaves-button" type="button" disabled>Copy Leaf Names</button>
              <button id="clear-selected-leaves-button" type="button" disabled>Clear Selected Leaves</button>
            </div>
            <ul id="selected-leaf-list" class="selected-leaf-list" hidden></ul>
          </div>
          <h2>Input</h2>
          <p id="viewer-summary">Newick length: {len(payload["newick"])} characters</p>
          <h2>Notes</h2>
          <p>This build only proves local interactive rendering. Selection/export comes next.</p>
          <h2>Debug</h2>
          <pre id="viewer-debug" class="viewer-debug">Waiting for initialization logs...</pre>
        </aside>
      </main>
    </div>
    <script>
      window.__TREE_VIEWER_DATA__ = {data_json};
      window.__viewerReport = function (message, isError) {{
        var status = document.getElementById("viewer-status");
        var debug = document.getElementById("viewer-debug");
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
    <script src="{assets["underscore_js"].as_uri()}" onerror="window.__viewerReport('Failed to load underscore.min.js', true)"></script>
    <script>
      window.__underscore = window._.noConflict();
      window.__viewerReport("Loaded underscore.", false);
    </script>
    <script src="{assets["lodash_js"].as_uri()}" onerror="window.__viewerReport('Failed to load lodash.min.js', true)"></script>
    <script>
      window._$1 = window._;
      window._ = window.__underscore;
      window.__viewerReport("Loaded lodash.", false);
    </script>
    <script src="{assets["phylotree_js"].as_uri()}" onerror="window.__viewerReport('Failed to load phylotree.js', true)"></script>
    <script src="{assets["app_js"].as_uri()}" onerror="window.__viewerReport('Failed to load viewer/app.js', true)"></script>
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
    html_path.write_text(_build_html(payload), encoding="utf-8")
    return html_path


def _default_output_dir():
    try:
        return Path(tempfile.mkdtemp(prefix="phylotree_viewer_"))
    except OSError:
        return ROOT / ".viewer_tmp"


def main():
    parser = argparse.ArgumentParser(description="Render a local interactive phylogenetic tree viewer.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--newick-file", help="Path to a Newick tree file.")
    group.add_argument("--newick-text", help="Raw Newick text.")
    parser.add_argument("--title", default="Phylo GUI Tree Viewer", help="Page title for the viewer.")
    parser.add_argument("--output-dir", help="Directory to write the generated HTML viewer into.")
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
    }
    html_path = _write_viewer_html(payload, output_dir)

    if not args.no_open_browser:
        webbrowser.open(html_path.as_uri())

    print(html_path)


if __name__ == "__main__":
    main()
