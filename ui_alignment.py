import TkEasyGUI as eg

from fasta_utils import parse_fasta_records
from ui_common import discard_pending_events, relax_modal_window, run_with_progress
from services_alignment import run_mafft


def open_alignment_options_window(context):
    """
    Opens the alignment options window.
    When "Run Alignment" is executed, runs MAFFT via a progress window and then
    advances directly to the Trim options window.
    """
    layout = [
        [eg.Multiline(key="alignment_input", default_text=context.get_alignment_input_text(), size=(80, 20), expand_x=True, expand_y=True)],
        [eg.Text("Threads:"), eg.Input(default_text="4", key="threads", size=(5, 1))],
        [
            eg.Text("Mode:"),
            eg.Radio("auto", "align_mode", default=True, key="mode_auto"),
            eg.Radio("linsi", "align_mode", key="mode_linsi"),
            eg.Radio("ginsi", "align_mode", key="mode_ginsi"),
            eg.Radio("einsi", "align_mode", key="mode_einsi"),
        ],
        [eg.Button("Run Alignment"), eg.Button("Skip to Trim"), eg.Button("Cancel")],
    ]
    opt_win = eg.Window("Alignment Options", layout, modal=True, resizable=True)
    relax_modal_window(opt_win)
    while True:
        event, values = opt_win.read()
        if event in ("Cancel", eg.WINDOW_CLOSED):
            break
        elif event == "Skip to Trim":
            alignment_input = values["alignment_input"].strip()
            try:
                records = parse_fasta_records(alignment_input)
                context.set_original_input(alignment_input, records)
                context.set_alignment_output(alignment_input)
            except ValueError as exc:
                eg.popup("FASTA input error:\n" + str(exc))
                continue
            opt_win.close()
            from ui_trim import open_trim_options_window

            open_trim_options_window(context)
            return
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
            try:
                context.set_original_input(alignment_input, parse_fasta_records(alignment_input))
            except ValueError as exc:
                eg.popup("FASTA input error:\n" + str(exc))
                continue
            result = run_with_progress(
                "MAFFT alignment is running...",
                run_mafft,
                alignment_input,
                threads,
                mode,
                parent_window=opt_win,
            )
            discard_pending_events(opt_win)
            if not result[0]:
                eg.popup("Error: MAFFT execution failed.\n" + result[1])
            else:
                context.set_alignment_output(result[1])
                opt_win.close()
                from ui_trim import open_trim_options_window

                open_trim_options_window(context)
                return
    opt_win.close()
