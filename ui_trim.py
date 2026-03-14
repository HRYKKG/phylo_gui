import os
import webbrowser
import tkinter.filedialog as fd

import TkEasyGUI as eg

from services_trim import get_trimal_version, run_trimal
from ui_common import discard_pending_events


def open_trim_options_window(context):
    """
    Opens the trim options window.
    When "Run Trim" is executed, runs trimal.
    If the resulting trim result window returns "Go to IQTREE", the trim option window is closed
    and the IQTREE option window is automatically opened.
    """
    trimal_version = get_trimal_version()
    layout = [
        [eg.Multiline(key="trim_input", default_text=context.get_trim_input_text(), size=(80, 20), expand_x=True, expand_y=True)],
        [eg.Text("trimal: " + trimal_version)],
        [
            eg.Text("Mode:"),
            eg.Radio("automated1", "trim_mode", default=True, key="trim_mode_automated1"),
            eg.Radio("gappyout", "trim_mode", key="trim_mode_gappyout"),
            eg.Radio("strict", "trim_mode", key="trim_mode_strict"),
            eg.Radio("strictplus", "trim_mode", key="trim_mode_strictplus"),
            eg.Radio("nogaps", "trim_mode", key="trim_mode_nogap"),
        ],
        [eg.Button("Run Trim"), eg.Button("Skip to IQTREE"), eg.Button("Back to Alignment"), eg.Button("Cancel")],
    ]
    opt_win = eg.Window("Trim Options", layout, modal=True, resizable=True)
    while True:
        event, values = opt_win.read()
        if event in ("Cancel", eg.WINDOW_CLOSED):
            break
        elif event == "Back to Alignment":
            opt_win.close()
            from ui_alignment import open_alignment_options_window

            open_alignment_options_window(context)
            return
        elif event == "Skip to IQTREE":
            trim_input = values["trim_input"].strip()
            context.set_trim_output(trim_input)
            opt_win.close()
            from ui_iqtree import open_iqtree_options_window

            open_iqtree_options_window(context)
            return
        elif event == "Run Trim":
            mode = (
                "automated1"
                if values.get("trim_mode_automated1")
                else "gappyout"
                if values.get("trim_mode_gappyout")
                else "strict"
                if values.get("trim_mode_strict")
                else "strictplus"
                if values.get("trim_mode_strictplus")
                else "nogaps"
            )
            trim_input = values["trim_input"]
            success, message, trimmed_result, output_path, html_path = run_trimal(trim_input, mode)
            if not success:
                eg.popup("Error: trimal execution failed.\n" + message)
                continue
            context.set_trim_output(trimmed_result)
            action = open_trim_result_window(context, output_path, html_path)
            discard_pending_events(opt_win)
            if action == "Go to IQTREE":
                opt_win.close()
                from ui_iqtree import open_iqtree_options_window

                open_iqtree_options_window(context)
                return
            if action == "Close Stage":
                opt_win.close()
                return
    opt_win.close()


def open_trim_result_window(context, output_path, html_path):
    """
    Displays the trim result window.
    If the user selects "Go to IQTREE", returns that event.
    Otherwise, closes normally.
    """
    layout = [
        [eg.Multiline(key="trimmed_output", default_text=context.trim_output_text or "", size=(80, 20), expand_x=True, expand_y=True)],
        [eg.Button("Go to IQTREE")],
        [eg.Button("Copy"), eg.Button("Show result"), eg.Button("Download")],
        [eg.Button("Back to Options"), eg.Button("Close Stage")],
    ]
    res_win = eg.Window("Trim Result", layout, modal=True, finalize=True, resizable=True)
    ret = None
    while True:
        event, vals = res_win.read()
        if vals and "trimmed_output" in vals:
            context.trim_output_text = vals["trimmed_output"]
        if event in ("Back to Options", eg.WINDOW_CLOSED):
            break
        elif event == "Copy":
            eg.set_clipboard(vals["trimmed_output"])
            eg.popup("Result copied to clipboard.")
        elif event == "Show result":
            webbrowser.open("file://" + os.path.abspath(html_path))
        elif event == "Download":
            save_path = fd.asksaveasfilename(
                defaultextension=".fasta",
                filetypes=[("FASTA Files", "*.fasta"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            )
            if save_path:
                try:
                    with open(save_path, "w") as f:
                        f.write(vals["trimmed_output"])
                    eg.popup("Result saved: " + save_path)
                except Exception as e:
                    eg.popup("Failed to save file:\n" + str(e))
        elif event in ("Go to IQTREE", "Close Stage"):
            ret = event
            break
    res_win.close()
    return ret
