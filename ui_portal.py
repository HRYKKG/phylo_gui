import TkEasyGUI as eg

from constants import version
from ui_common import load_file
from ui_alignment import open_alignment_options_window
from ui_trim import open_trim_options_window
from ui_iqtree import open_iqtree_options_window


def open_portal_window():
    """Opens the main portal window for Phylo_GUI."""
    portal_layout = [
        [eg.Text("Phylo_GUI Portal: " + version)],
        [eg.Multiline(key="portal_input", size=(80, 20), expand_x=True, expand_y=True)],
        [eg.Button("Load File"), eg.Button("Go to Alignment"), eg.Button("Go to Trim"), eg.Button("Go to IQTREE"), eg.Button("Quit")],
    ]
    win = eg.Window("Phylo_GUI Portal", portal_layout, resizable=True)
    while True:
        event, values = win.read()
        if event in ("Quit", eg.WINDOW_CLOSED):
            break
        elif event == "Load File":
            load_file(win, "portal_input")
        elif event == "Go to Alignment":
            open_alignment_options_window(values["portal_input"])
        elif event == "Go to Trim":
            open_trim_options_window(values["portal_input"])
        elif event == "Go to IQTREE":
            open_iqtree_options_window(values["portal_input"])
    win.close()
