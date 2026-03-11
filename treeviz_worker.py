import html
import os
import sys
import webbrowser
from types import ModuleType


def _install_cgi_compat():
    """Provide the minimal cgi.escape API expected by older ete3 code."""
    if "cgi" in sys.modules:
        return
    cgi_module = ModuleType("cgi")
    cgi_module.escape = html.escape
    sys.modules["cgi"] = cgi_module


def _write_html(html_path, body):
    with open(html_path, "w") as f:
        f.write(
            """<html>
  <head>
    <meta charset="UTF-8">
    <title>IQTREE Tree Viewer</title>
  </head>
  <body>
"""
            + body
            + """
  </body>
</html>"""
        )


def _render_tree(newick_path, img_path, html_path):
    _install_cgi_compat()
    from ete3 import Tree, TreeStyle, TextFace

    def my_layout(node):
        if not node.is_leaf() and node.name:
            if "/" in node.name:
                display_text = "\n".join(node.name.split("/"))
            else:
                try:
                    display_text = str(float(node.name))
                except ValueError:
                    display_text = node.name
            face = TextFace(display_text, fsize=10)
            node.add_face(face, column=0, position="branch-top")

    with open(newick_path, "r") as f:
        newick_str = f.read().strip()

    t = Tree(newick_str, format=1)
    for node in t.traverse():
        if not node.is_leaf() and node.support is not None:
            support_str = str(node.support)
            if "/" in support_str:
                node.support = "\n".join(support_str.split("/"))
            else:
                try:
                    node.support = str(float(support_str))
                except ValueError:
                    node.support = support_str

    ts = TreeStyle()
    ts.show_leaf_name = True
    ts.layout_fn = my_layout
    ts.show_branch_support = False
    midpoint = t.get_midpoint_outgroup()
    t.set_outgroup(midpoint)
    t.render(img_path, w=600, units="px", tree_style=ts)

    _write_html(
        html_path,
        """    <h1>IQTREE Tree Viewer</h1>
    <img src="tree.png" alt="Tree">
""",
    )


def main():
    if len(sys.argv) != 4:
        raise SystemExit("Usage: treeviz_worker.py <newick_path> <img_path> <html_path>")

    newick_path, img_path, html_path = sys.argv[1:4]
    try:
        _render_tree(newick_path, img_path, html_path)
    except Exception as exc:
        _write_html(
            html_path,
            "    <h1>IQTREE Tree Viewer</h1>\n"
            "    <p>Tree rendering failed.</p>\n"
            f"    <pre>{html.escape(str(exc))}</pre>\n",
        )
    webbrowser.open("file://" + os.path.abspath(html_path))


if __name__ == "__main__":
    main()
