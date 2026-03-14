import TkEasyGUI as eg

from feature_flags import ENABLE_DOWNLOAD_DISPLAY_TREE
from ui_common import discard_pending_events, run_with_progress
from services_iqtree import get_iqtree_version, run_iqtree, get_model_line
from services_treeviz import handle_view_tree
from services_downloads import handle_download_newick, handle_download_display_tree, handle_download_all_files, handle_add_atha_gene_names
from ui_leaf_selection import load_selection_payload, open_leaf_selection_window


def _sync_tree_output(win_res):
    tree_text = win_res["tree_output"].get()
    win_res.tree_content = tree_text
    if hasattr(win_res, "context"):
        win_res.context.tree_newick_text = tree_text
    return tree_text


def _maybe_handle_tree_selection(win_res):
    selection_path = getattr(win_res, "tree_selection_path", None)
    if not selection_path or not selection_path.exists():
        return

    mtime_ns = selection_path.stat().st_mtime_ns
    if getattr(win_res, "tree_selection_seen_mtime_ns", None) == mtime_ns:
        return

    selection_payload = load_selection_payload(selection_path)
    win_res.tree_selection_seen_mtime_ns = mtime_ns
    action = open_leaf_selection_window(win_res.context, selection_payload, parent_iqtree_window=win_res)
    discard_pending_events(win_res)
    return action


def open_iqtree_options_window(context):
    """
    Opens the IQ-TREE options window.
    When "Run IQTREE" is executed, runs IQ-TREE via a progress window.
    After execution, displays the IQ-TREE result window.
    """
    layout = [
        [eg.Multiline(key="iqtree_input", default_text=context.get_iqtree_input_text(), size=(80, 20), expand_x=True, expand_y=True)],
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
        [eg.Button("Run IQTREE"), eg.Button("Back to Trim"), eg.Button("Back to Alignment"), eg.Button("Cancel")],
    ]
    win = eg.Window("IQTREE Options", layout, modal=True, resizable=True)
    setattr(context, "close_iqtree_stage_requested", False)
    while True:
        event, values = win.read()
        if event in ("Cancel", eg.WINDOW_CLOSED):
            break
        elif event == "Back to Trim":
            win.close()
            from ui_trim import open_trim_options_window

            open_trim_options_window(context)
            return
        elif event == "Back to Alignment":
            win.close()
            from ui_alignment import open_alignment_options_window

            open_alignment_options_window(context)
            return
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
            discard_pending_events(win)
            if not result[0]:
                eg.popup("Error: IQTREE execution failed.\n" + result[1])
            else:
                treefile = result[2]
                with open(treefile, "r") as f:
                    tree_content = f.read()
                context.set_iqtree_output(
                    output_dir=result[5],
                    prefix=output_prefix,
                    treefile_path=treefile,
                    report_path=result[6],
                    newick_text=tree_content,
                )
                action = open_iqtree_result_window(context)
                discard_pending_events(win)
                if action == "Open in Alignment":
                    win.close()
                    from ui_alignment import open_alignment_options_window

                    open_alignment_options_window(context)
                    return
    win.close()


def open_iqtree_result_window(context):
    """Displays the IQ-TREE result window and offers further actions."""
    try:
        treefile = str(context.treefile_path)
        tree_content = context.tree_newick_text or ""
        model_info = get_model_line(str(context.iqtree_report_path)) if context.iqtree_report_path else "External tree loaded"
        result_header = f"{model_info}\n"
        action_buttons = [eg.Button("View Tree")]
        utility_buttons = [eg.Button("Copy"), eg.Button("Add Atha gene names"), eg.Button("Download Newick")]
        if ENABLE_DOWNLOAD_DISPLAY_TREE:
            utility_buttons.append(eg.Button("Download Display Tree"))
        utility_buttons.append(eg.Button("Download all files"))
        layout = [
            [eg.Text(result_header)],
            [eg.Multiline(key="tree_output", default_text=tree_content, size=(80, 20), expand_x=True, expand_y=True)],
            action_buttons,
            utility_buttons,
            [eg.Button("Close")],
        ]
        win_res = eg.Window("IQTREE Result", layout, modal=True, finalize=True, resizable=True)
        win_res.context = context
        win_res.output_prefix = context.iqtree_prefix
        win_res.tree_content = tree_content
        win_res.treefile = treefile
        win_res.display_tree_path = None
        win_res.tree_selection_path = None
        win_res.tree_selection_seen_mtime_ns = None
        ret = None
        while True:
            event, _ = win_res.read(timeout=250)
            _sync_tree_output(win_res)
            selection_action = _maybe_handle_tree_selection(win_res)
            if selection_action and selection_action.get("action") == "open_alignment":
                context.set_original_input(selection_action["fasta_text"], selection_action["records"])
                ret = "Open in Alignment"
                break
            if event in ("Close", eg.WINDOW_CLOSED):
                break
            elif event == "Copy":
                eg.set_clipboard(win_res.tree_content)
                eg.popup("Result copied to clipboard.")
            elif event == "Add Atha gene names":
                handle_add_atha_gene_names(win_res)
            elif event == "View Tree":
                handle_view_tree(win_res)
            elif event == "Download Newick":
                handle_download_newick(win_res)
            elif ENABLE_DOWNLOAD_DISPLAY_TREE and event == "Download Display Tree":
                handle_download_display_tree(win_res)
            elif event == "Download all files":
                handle_download_all_files(win_res)
        win_res.close()
        return ret
    except Exception as e:
        eg.popup("Failed to load output file:\n" + str(e))
