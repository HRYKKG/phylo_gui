import TkEasyGUI as eg
from pathlib import Path

from constants import version
from context import AnalysisContext
from fasta_utils import build_leaf_label_map, parse_fasta_records
from feature_flags import ENABLE_PORTAL_TREE_RESULT_BYPASS
from ui_common import (
    discard_pending_events,
    install_inactive_button_indicator,
    install_active_title_indicator,
    load_file,
    reactivate_window,
    set_window_buttons_disabled,
)
from ui_alignment import open_alignment_options_window
from ui_iqtree import open_iqtree_result_window


def _sync_original_input(context, fasta_text):
    records = parse_fasta_records(fasta_text)
    context.set_original_input(fasta_text, records)


def _load_text_file(title):
    file_path = eg.popup_get_file(title=title)
    if not file_path:
        return None, None
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            return file_path, handle.read()
    except Exception as exc:
        eg.popup("Failed to read file:\n" + str(exc))
        return None, None


def _open_tree_result_bypass(context, portal_fasta_text):
    fasta_path = None
    fasta_text = portal_fasta_text.strip()
    if not fasta_text:
        fasta_path, fasta_text = _load_text_file("Please select a FASTA file")
        if fasta_text is None:
            return
    try:
        _sync_original_input(context, fasta_text)
    except ValueError as exc:
        eg.popup("FASTA input error:\n" + str(exc))
        return

    tree_path, tree_text = _load_text_file("Please select a tree file")
    if tree_text is None:
        return

    tree_path_obj = Path(tree_path)
    context.set_iqtree_output(
        output_dir=str(tree_path_obj.parent),
        prefix=tree_path_obj.stem,
        treefile_path=str(tree_path_obj),
        report_path=None,
        newick_text=tree_text,
    )
    context.leaf_label_map = build_leaf_label_map(context.original_records, tree_text)
    action = open_iqtree_result_window(context)
    if action == "Open in Alignment":
        open_alignment_options_window(context)


def open_portal_window(context=None):
    """Opens the main portal window for Phylo_GUI."""
    context = context or AnalysisContext()
    action_buttons = [eg.Button("Start Pipeline"), eg.Button("Load File")]
    if ENABLE_PORTAL_TREE_RESULT_BYPASS:
        action_buttons.append(eg.Button("Open Tree Result"))
    action_buttons.append(eg.Button("Quit"))
    portal_layout = [
        [eg.Text("Phylo_GUI Portal: " + version)],
        [
            eg.Multiline(
                key="portal_input",
                default_text=context.original_fasta_text,
                size=(80, 20),
                expand_x=True,
                expand_y=True,
            )
        ],
        action_buttons,
    ]
    win = eg.Window("Phylo_GUI Portal", portal_layout, resizable=True)
    install_inactive_button_indicator(win)
    install_active_title_indicator(win)
    win.context = context
    while True:
        event, values = win.read()
        if event in ("Quit", eg.WINDOW_CLOSED):
            break
        elif event == "Load File":
            loaded_text = load_file(win, "portal_input")
            if loaded_text is None:
                continue
            try:
                _sync_original_input(context, loaded_text)
            except ValueError as exc:
                eg.popup("FASTA input error:\n" + str(exc))
        elif event == "Start Pipeline":
            portal_text = values["portal_input"].strip()
            try:
                _sync_original_input(context, portal_text)
            except ValueError as exc:
                eg.popup("FASTA input error:\n" + str(exc))
                continue
            set_window_buttons_disabled(win, True)
            try:
                open_alignment_options_window(context)
            finally:
                set_window_buttons_disabled(win, False)
                reactivate_window(win)
            discard_pending_events(win)
        elif ENABLE_PORTAL_TREE_RESULT_BYPASS and event == "Open Tree Result":
            set_window_buttons_disabled(win, True)
            try:
                _open_tree_result_bypass(context, values["portal_input"])
            finally:
                set_window_buttons_disabled(win, False)
                reactivate_window(win)
            discard_pending_events(win)
    win.close()
