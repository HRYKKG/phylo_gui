import TkEasyGUI as eg

from constants import version
from context import AnalysisContext
from fasta_utils import parse_fasta_records
from ui_common import load_file
from ui_alignment import open_alignment_options_window
from ui_trim import open_trim_options_window
from ui_iqtree import open_iqtree_options_window


def _sync_original_input(context, fasta_text):
    records = parse_fasta_records(fasta_text)
    context.set_original_input(fasta_text, records)


def open_portal_window(context=None):
    """Opens the main portal window for Phylo_GUI."""
    context = context or AnalysisContext()
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
        [eg.Button("Load File"), eg.Button("Go to Alignment"), eg.Button("Go to Trim"), eg.Button("Go to IQTREE"), eg.Button("Quit")],
    ]
    win = eg.Window("Phylo_GUI Portal", portal_layout, resizable=True)
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
        elif event in ("Go to Alignment", "Go to Trim", "Go to IQTREE"):
            portal_text = values["portal_input"].strip()
            try:
                _sync_original_input(context, portal_text)
            except ValueError as exc:
                eg.popup("FASTA input error:\n" + str(exc))
                continue
            if event == "Go to Alignment":
                open_alignment_options_window(context)
            elif event == "Go to Trim":
                open_trim_options_window(context)
            else:
                open_iqtree_options_window(context)
    win.close()
