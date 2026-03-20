import json
import tkinter.filedialog as fd

import TkEasyGUI as eg

from fasta_utils import format_fasta_records, select_records_by_ids
from ui_common import (
    install_inactive_button_indicator,
    install_active_title_indicator,
    relax_modal_window,
    reactivate_window,
)


def _resolve_selected_ids(context, selected_leaf_names):
    if not context or not context.leaf_label_map:
        return selected_leaf_names
    return [context.leaf_label_map.get(name, name) for name in selected_leaf_names]


def _build_selected_fasta(context, selected_leaf_names):
    resolved_ids = _resolve_selected_ids(context, selected_leaf_names)
    records = select_records_by_ids(context.original_records, resolved_ids)
    return records, format_fasta_records(records)


def open_leaf_selection_window(context, selection_payload, parent_iqtree_window=None):
    selected_leaf_names = selection_payload.get("selected_leaf_names", [])
    records, fasta_text = _build_selected_fasta(context, selected_leaf_names)
    missing_count = max(0, len(selected_leaf_names) - len(records))

    layout = [
        [eg.Text(f"Selected leaves: {len(selected_leaf_names)}")],
        [eg.Text(f"Matched original FASTA records: {len(records)}")],
        [eg.Text(f"Unmatched leaf names: {missing_count}")],
        [eg.Text("Selected leaf names")],
        [eg.Multiline(key="selected_leaf_names", default_text="", size=(80, 12), expand_x=True, expand_y=True)],
        [eg.Text("Selected FASTA")],
        [eg.Multiline(key="selected_fasta", default_text="", size=(80, 16), expand_x=True, expand_y=True)],
        [eg.Button("Open in Alignment")],
        [eg.Button("Copy FASTA"), eg.Button("Export FASTA")],
        [eg.Button("Close")],
    ]
    window = eg.Window("Leaf Selection", layout, modal=True, finalize=True, resizable=True)
    install_inactive_button_indicator(window)
    install_active_title_indicator(window)
    relax_modal_window(window)
    window["selected_leaf_names"].update("\n".join(selected_leaf_names))
    window["selected_fasta"].update(fasta_text)

    while True:
        event, _ = window.read()
        if event in ("Close", eg.WINDOW_CLOSED):
            break
        if event == "Copy FASTA":
            eg.set_clipboard(fasta_text)
            eg.popup("Selected FASTA copied to clipboard.")
            reactivate_window(window)
        elif event == "Export FASTA":
            save_path = fd.asksaveasfilename(
                defaultextension=".fa",
                initialfile="selected_leaves",
                filetypes=[("FASTA Files", "*.fa *.fasta"), ("All Files", "*.*")],
            )
            reactivate_window(window)
            if save_path:
                try:
                    with open(save_path, "w", encoding="utf-8") as handle:
                        handle.write(fasta_text)
                    eg.popup("Selected FASTA saved: " + save_path)
                    reactivate_window(window)
                except Exception as exc:
                    eg.popup("Failed to save FASTA:\n" + str(exc))
                    reactivate_window(window)
        elif event == "Open in Alignment":
            try:
                should_continue = eg.popup_yes_no(
                    "Opening Alignment with the selected FASTA will reset the current alignment, trim, and IQ-TREE results.\n\nContinue?"
                )
                reactivate_window(window)
                if should_continue != "Yes":
                    continue
                window.close()
                return {
                    "action": "open_alignment",
                    "fasta_text": fasta_text,
                    "records": records,
                }
            except Exception as exc:
                eg.popup("Failed to open Alignment window:\n" + str(exc))
                reactivate_window(window)

    window.close()
    return None


def load_selection_payload(selection_path):
    with open(selection_path, "r", encoding="utf-8") as handle:
        return json.load(handle)
