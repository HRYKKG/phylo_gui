import tkinter.filedialog as fd

import TkEasyGUI as eg

from ui_common import run_with_progress
from services_alignment import run_mafft


def open_alignment_options_window(portal_text):
    """
    Opens the alignment options window.
    When "Run Alignment" is executed, runs MAFFT via a progress window.
    If the resulting alignment result window returns "Go to Trim" or "Go to IQTREE",
    the alignment option window is automatically closed and the corresponding option
    window is opened.
    """
    layout = [
        [eg.Multiline(key="alignment_input", default_text=portal_text, size=(80, 20), expand_x=True, expand_y=True)],
        [eg.Text("Threads:"), eg.Input(default_text="4", key="threads", size=(5, 1))],
        [
            eg.Text("Mode:"),
            eg.Radio("auto", "align_mode", default=True, key="mode_auto"),
            eg.Radio("linsi", "align_mode", key="mode_linsi"),
            eg.Radio("ginsi", "align_mode", key="mode_ginsi"),
            eg.Radio("einsi", "align_mode", key="mode_einsi"),
        ],
        [eg.Button("Run Alignment"), eg.Button("Cancel")],
    ]
    opt_win = eg.Window("Alignment Options", layout, resizable=True)
    while True:
        event, values = opt_win.read()
        if event in ("Cancel", eg.WINDOW_CLOSED):
            break
        elif event == "Run Alignment":
            try:
                threads = int(values["threads"].strip())
                if threads < 1:
                    raise ValueError("Threads must be at least 1.")
            except ValueError as ve:
                eg.popup("Threads input error: " + str(ve))
                continue
            mode = (
                "auto"
                if values.get("mode_auto")
                else ("linsi" if values.get("mode_linsi") else ("ginsi" if values.get("mode_ginsi") else "einsi"))
            )
            alignment_input = values["alignment_input"].strip()
            result = run_with_progress("MAFFT alignment is running...", run_mafft, alignment_input, threads, mode)
            if not result[0]:
                eg.popup("Error: MAFFT execution failed.\n" + result[1])
            else:
                action = open_alignment_result_window(result[1])
                if action in ("Go to Trim", "Go to IQTREE"):
                    opt_win.close()
                    if action == "Go to Trim":
                        from ui_trim import open_trim_options_window

                        open_trim_options_window(result[1])
                    else:
                        from ui_iqtree import open_iqtree_options_window

                        open_iqtree_options_window(result[1])
                    return
    opt_win.close()


def open_alignment_result_window(result_text):
    """
    Displays the alignment result window.
    If the user selects "Go to Trim" or "Go to IQTREE", returns that event.
    Otherwise, closes normally.
    """
    layout = [
        [eg.Multiline(key="alignment_output", default_text=result_text, size=(80, 20), expand_x=True, expand_y=True)],
        [eg.Button("Copy"), eg.Button("Download"), eg.Button("Go to Trim"), eg.Button("Go to IQTREE"), eg.Button("Close")],
    ]
    res_win = eg.Window("Alignment Result", layout, modal=True, finalize=True, resizable=True)
    ret = None
    while True:
        event, values = res_win.read()
        if event in ("Close", eg.WINDOW_CLOSED):
            break
        elif event == "Copy":
            eg.set_clipboard(values["alignment_output"])
            eg.popup("Result copied to clipboard.")
        elif event == "Download":
            save_path = fd.asksaveasfilename(
                defaultextension=".txt",
                initialfile="alignment_result",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            )
            if save_path:
                try:
                    with open(save_path, "w") as f:
                        f.write(values["alignment_output"])
                    eg.popup("Result saved: " + save_path)
                except Exception as e:
                    eg.popup("Failed to save file: " + str(e))
        elif event in ("Go to Trim", "Go to IQTREE"):
            ret = event
            break
    res_win.close()
    return ret
