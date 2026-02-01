import atexit
import os
import shutil
import tempfile
import webbrowser

import TkEasyGUI as eg


def my_layout(node):
    """Custom layout function for ETE3 tree rendering."""
    from ete3 import TextFace

    if not node.is_leaf() and node.name:
        if "/" in node.name:
            supports = node.name.split("/")
            display_text = "\n".join(supports)
        else:
            try:
                display_text = str(float(node.name))
            except ValueError:
                display_text = node.name
        face = TextFace(display_text, fsize=10)
        node.add_face(face, column=0, position="branch-top")


def handle_view_tree(win):
    """Renders the tree using ETE3 and opens the result in a web browser."""
    try:
        from ete3 import Tree, TreeStyle
    except ImportError:
        eg.popup("Error: ETE3 is not installed.")
        return
    try:
        newick_str = win.tree_content.strip()
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
        tmp_dir = tempfile.mkdtemp(prefix="iqtree_ete_")
        atexit.register(shutil.rmtree, tmp_dir, ignore_errors=True)
        img_path = os.path.join(tmp_dir, "tree.png")
        html_path = os.path.join(tmp_dir, "tree.html")
        t.render(img_path, w=600, units="px", tree_style=ts)
        html_content = """<html>
  <head>
    <meta charset="UTF-8">
    <title>IQTREE Tree Viewer</title>
  </head>
  <body>
    <h1>IQTREE Tree Viewer</h1>
    <img src="tree.png" alt="Tree">
  </body>
</html>"""
        with open(html_path, "w") as f:
            f.write(html_content)
        webbrowser.open("file://" + os.path.abspath(html_path))
    except Exception as e:
        eg.popup("Failed to display tree:\n" + str(e))
