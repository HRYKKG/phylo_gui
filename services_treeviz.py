import atexit
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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
    """Renders the tree using a worker process and opens the result in a web browser."""
    try:
        context = getattr(win, "context", None)
        newick_str = (context.tree_newick_text if context and context.tree_newick_text is not None else win.tree_content).strip()
        if not newick_str:
            eg.popup("Tree data is empty.")
            return
        tmp_dir = tempfile.mkdtemp(prefix="iqtree_ete_")
        atexit.register(shutil.rmtree, tmp_dir, ignore_errors=True)
        newick_path = os.path.join(tmp_dir, "tree.nwk")
        img_path = os.path.join(tmp_dir, "tree.png")
        html_path = os.path.join(tmp_dir, "tree.html")
        with open(newick_path, "w") as f:
            f.write(newick_str)
        worker_path = Path(__file__).resolve().parent / "treeviz_worker.py"
        subprocess.Popen(
            [sys.executable, str(worker_path), newick_path, img_path, html_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as e:
        eg.popup("Failed to display tree:\n" + str(e))
