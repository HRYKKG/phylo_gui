import os

import TkEasyGUI as eg

from ui_common import run_with_progress
from services_iqtree import get_iqtree_version, run_iqtree, get_model_line
from services_treeviz import handle_view_tree
from services_downloads import handle_download_newick, handle_download_all_files, handle_add_atha_gene_names


def open_iqtree_options_window(portal_text):
    """
    Opens the IQ-TREE options window.
    When "Run IQTREE" is executed, runs IQ-TREE via a progress window.
    After execution, displays the IQ-TREE result window.
    """
    layout = [
        [eg.Multiline(key="iqtree_input", default_text=portal_text, size=(80, 20), expand_x=True, expand_y=True)],
        [eg.Text("IQ-TREE version: " + get_iqtree_version())],
        [eg.Text("threads (0 = auto):"), eg.Input(default_text="0", key="threads", size=(10, 1))],
        [eg.Text("Confidence analyses")],
        [
            eg.Text("UFboot:"),
            eg.Input(default_text="1000", key="ufboot", size=(10, 1)),
            eg.Text("SH-aLR:"),
            eg.Input(default_text="1000", key="sh_alr", size=(10, 1)),
            eg.Text("lbp:"),
            eg.Input(default_text="0", key="lbp", size=(10, 1)),
        ],
        [eg.Text("abayes:"), eg.Checkbox("Use abayes", default=False, key="abayes")],
        [eg.Text("Substitution model:"), eg.Input(default_text="auto", key="subst_model", size=(20, 1))],
        [eg.Text("Output prefix:"), eg.Input(default_text="tmp", key="output_prefix", size=(10, 1))],
        [eg.Button("Run IQTREE"), eg.Button("Cancel")],
    ]
    win = eg.Window("IQTREE Options", layout, resizable=True)
    while True:
        event, values = win.read()
        if event in ("Cancel", eg.WINDOW_CLOSED):
            break
        elif event == "Run IQTREE":
            try:
                threads = int(values["threads"].strip())
            except ValueError as ve:
                eg.popup("Threads input error: " + str(ve))
                continue

            ufboot_input = values["ufboot"].strip()
            sh_alr_input = values["sh_alr"].strip()
            lbp_input = values["lbp"].strip()
            subst_model_input = values["subst_model"].strip()
            iqtree_input = values["iqtree_input"].strip()
            output_prefix = values["output_prefix"].strip()
            result = run_with_progress(
                "IQTREE analysis is running...",
                run_iqtree,
                iqtree_input,
                threads,
                ufboot_input,
                sh_alr_input,
                lbp_input,
                values["abayes"],
                subst_model_input,
                output_prefix,
            )
            if not result[0]:
                eg.popup("Error: IQTREE execution failed.\n" + result[1])
            else:
                open_iqtree_result_window(values, result[2])
    win.close()


def open_iqtree_result_window(values, treefile):
    """Displays the IQ-TREE result window and offers further actions."""
    try:
        with open(treefile, "r") as f:
            tree_content = f.read()
        iqtree_txt = os.path.join(os.path.dirname(treefile), values["output_prefix"] + ".iqtree")
        model_info = get_model_line(iqtree_txt)
        result_header = f"{model_info}\n"
        layout = [
            [eg.Text(result_header)],
            [eg.Multiline(key="tree_output", default_text=tree_content, size=(80, 20), expand_x=True, expand_y=True)],
            [eg.Button("Copy"), eg.Button("View Tree"), eg.Button("Add Atha gene names")],
            [eg.Button("Download Newick"), eg.Button("Download all files")],
            [eg.Button("Close")],
        ]
        win_res = eg.Window("IQTREE Result", layout, modal=True, finalize=True, resizable=True)
        win_res.output_prefix = values["output_prefix"]
        win_res.tree_content = tree_content
        win_res.treefile = treefile
        while True:
            event, _ = win_res.read()
            if event in ("Close", eg.WINDOW_CLOSED):
                break
            elif event == "Copy":
                eg.set_clipboard(win_res["tree_output"].get())
                eg.popup("Result copied to clipboard.")
            elif event == "Add Atha gene names":
                handle_add_atha_gene_names(win_res)
            elif event == "View Tree":
                handle_view_tree(win_res)
            elif event == "Download Newick":
                handle_download_newick(win_res)
            elif event == "Download all files":
                handle_download_all_files(win_res)
        win_res.close()
    except Exception as e:
        eg.popup("Failed to load output file:\n" + str(e))
