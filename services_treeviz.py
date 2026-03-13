import atexit
import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType

import TkEasyGUI as eg
from remap_support_labels import remap_support_labels


def _get_tree_text(win) -> str:
    context = getattr(win, "context", None)
    if context is not None and context.tree_newick_text is not None:
        return context.tree_newick_text.strip()
    return getattr(win, "tree_content", "").strip()


def _install_cgi_compat():
    """Provide the minimal cgi.escape API expected by older ete3 code."""
    if "cgi" in sys.modules:
        return
    cgi_module = ModuleType("cgi")
    cgi_module.escape = html.escape
    sys.modules["cgi"] = cgi_module


def _midpoint_root_newick(newick_text: str) -> str:
    _install_cgi_compat()
    from ete3 import Tree

    tree = Tree(newick_text, format=1)
    outgroup = tree.get_midpoint_outgroup()
    if outgroup is not None:
        tree.set_outgroup(outgroup)
    return tree.write(format=1)


def _write_display_tree(newick_text: str) -> tuple[Path, bool, str | None]:
    tmp_dir = Path(tempfile.mkdtemp(prefix="phylotree_display_"))
    atexit.register(shutil.rmtree, tmp_dir, ignore_errors=True)
    newick_path = tmp_dir / "display_tree.nwk"
    rooted_text = newick_text
    rooted_ok = False
    error_messages = []
    try:
        rooted_text = _midpoint_root_newick(newick_text)
        rooted_ok = True
    except Exception as exc:
        rooted_text = newick_text
        error_messages.append(f"Midpoint rooting failed: {exc}")

    if rooted_ok:
        try:
            rooted_text, _ = remap_support_labels(
                newick_text,
                rooted_text,
                suppress_root_duplicate_labels=False,
            )
        except Exception as exc:
            error_messages.append(f"Support relabeling failed: {exc}")
    newick_path.write_text(rooted_text, encoding="utf-8")
    error_message = "\n".join(error_messages) if error_messages else None
    return newick_path, rooted_ok, error_message


def _launch_interactive_viewer(newick_path: Path):
    return _launch_interactive_viewer_with_selection(newick_path, None)


def _launch_interactive_viewer_with_selection(newick_path: Path, selection_output_path: Path | None):
    viewer_path = Path(__file__).resolve().parent / "interactive_tree_viewer.py"
    cmd = [sys.executable, str(viewer_path), "--newick-file", str(newick_path)]
    if selection_output_path is not None:
        cmd.extend(["--selection-output", str(selection_output_path)])
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def create_tree_view_session(win):
    session_dir = Path(tempfile.mkdtemp(prefix="phylotree_selection_"))
    atexit.register(shutil.rmtree, session_dir, ignore_errors=True)
    selection_path = session_dir / "selection.json"
    setattr(win, "tree_selection_path", selection_path)
    setattr(win, "tree_selection_seen_mtime_ns", None)
    return selection_path


def handle_view_tree(win):
    """Midpoint-root a display copy of the tree and open it in the interactive viewer."""
    try:
        newick_text = _get_tree_text(win)
        if not newick_text:
            eg.popup("Tree data is empty.")
            return
        display_tree_path, rooted_ok, error_message = _write_display_tree(newick_text)
        setattr(win, "display_tree_path", display_tree_path)
        selection_path = create_tree_view_session(win)
        _launch_interactive_viewer_with_selection(display_tree_path, selection_path)
        if error_message:
            if rooted_ok:
                eg.popup("Tree preprocessing warning:\n" + error_message)
            else:
                eg.popup("Midpoint rooting failed. Showing the original tree instead.\n" + error_message)
    except Exception as e:
        eg.popup("Failed to display tree:\n" + str(e))
