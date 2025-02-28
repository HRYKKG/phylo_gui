import TkEasyGUI as eg
import subprocess
import tkinter.filedialog as fd
import tempfile
import os
import re
import webbrowser
import shutil
from pathlib import Path

# Version of the Phylo_GUI
version = "v0.2.1"

# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------

def run_with_progress(initial_message, run_func, *args, **kwargs):
    """
    Displays a progress window with an initial message, executes the given function
    (blocking), then updates the progress window with a success message and waits for
    user confirmation.
    
    If an error occurs, the progress window is closed immediately.
    """
    prog_layout = [
        [eg.Multiline(key="progress", default_text=initial_message, size=(80,10))],
        [eg.Button("OK", key="ok", disabled=True)]
    ]
    prog_win = eg.Window("Progress", prog_layout, resizable=True)
    prog_win.refresh()
    
    # Execute the blocking function.
    result = run_func(*args, **kwargs)
    
    if result[0]:
        final_message = initial_message.replace("running", "completed") + "\nPress OK to continue."
        prog_win["progress"].update(final_message)
        prog_win["ok"].update(disabled=False)
        while True:
            event_prog, _ = prog_win.read()
            if event_prog and event_prog.lower() == "ok":
                break
        prog_win.close()
    else:
        # エラー発生時はすぐにウィンドウを閉じる
        prog_win.close()
    return result

# ------------------------------------------------------------------------------
# Basic functions
# ------------------------------------------------------------------------------

def load_file(window_obj, key):
    """Opens a file dialog to load a FASTA file and updates the given GUI element."""
    file_path = eg.popup_get_file(title="Please select a FASTA file")
    if file_path:
        try:
            with open(file_path, "r") as f:
                content = f.read()
            window_obj[key].update(content)
        except Exception as e:
            eg.popup("An error occurred while reading the file:\n" + str(e))

def run_mafft(fasta_text, threads=4, mode="auto"):
    """Executes MAFFT with the given parameters and returns (success, output)."""
    try:
        mode_option = "--auto" if mode == "auto" else f"--{mode}"
        cmd = ["mafft", mode_option, "--thread", str(threads), "-"]
        result = subprocess.run(cmd, input=fasta_text, text=True, capture_output=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def get_trimal_version():
    """Returns the version of trimal or an error message."""
    try:
        result = subprocess.run(["trimal", "--version"], text=True, capture_output=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "Failed to retrieve version"

def get_iqtree_version():
    """Returns the version of IQ-TREE or an error message."""
    try:
        result = subprocess.run(["iqtree", "--version"], text=True, capture_output=True, check=True)
        output = result.stdout.strip()
        first_line = output.splitlines()[0]
        m = re.search(r"version\s+([0-9.]+)", first_line, re.IGNORECASE)
        return m.group(1) if m else first_line
    except subprocess.CalledProcessError:
        return "Failed to retrieve version"

def get_model_line(iqtree_file):
    """
    Extracts the model and node support lines from the IQ-TREE output file.
    """
    model_line = None
    support_line = None
    try:
        with open(iqtree_file, "r") as f:
            for line in f:
                if line.startswith("Model of substitution:"):
                    model_line = line.strip()
                if support_line is None and line.startswith("Numbers in parentheses are"):
                    support_line = line.strip().replace("Numbers in parentheses are", "Node support(s):")
        if model_line:
            if support_line:
                return f"{model_line}\n{support_line}"
            else:
                return model_line
        else:
            return "Model information not found"
    except Exception as e:
        return "Failed to retrieve information: " + str(e)

# ------------------------------------------------------------------------------
# IQTREE functions
# ------------------------------------------------------------------------------

def build_iqtree_cmd(iqtree_input, threads, ufboot, sh_alr, lbp, abayes, subst_model, prefix):
    """
    Builds the IQ-TREE command based on provided parameters.
    """
    cmd = ["iqtree", "-s", iqtree_input, "--prefix", prefix]
    try:
        nt = int(threads)
    except ValueError:
        nt = 0
    cmd.extend(["-nt", "AUTO" if nt == 0 else str(nt)])
    try:
        bb = int(ufboot)
    except ValueError:
        bb = 0
    if bb != 0:
        cmd.extend(["-bb", str(bb)])
    try:
        alrt = int(sh_alr)
    except ValueError:
        alrt = 0
    if alrt != 0:
        cmd.extend(["-alrt", str(alrt)])
    try:
        lbp_val = int(lbp)
    except ValueError:
        lbp_val = 0
    if lbp_val != 0:
        cmd.extend(["-lbp", str(lbp_val)])
    if abayes:
        cmd.append("-abayes")
    # 置換モデルチェックはせず、入力された値をそのまま使用
    cmd.extend(["-m", subst_model])
    return cmd

def run_iqtree(iqtree_input, threads, ufboot, sh_alr, lbp, abayes, subst_model, output_prefix):
    """
    Executes IQ-TREE with the specified parameters.
    Returns a tuple: (success, message, treefile, input_file, command_string).
    """
    output_dir = tempfile.mkdtemp(prefix="tmp_iqtree_")
    os.makedirs(output_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=output_dir, prefix="tmp_input", suffix=".fasta") as temp_in:
        input_file = temp_in.name
        temp_in.write(iqtree_input)
    cmd = build_iqtree_cmd(input_file, threads, ufboot, sh_alr, lbp, abayes, subst_model, output_prefix)
    cmd_str = " ".join(cmd)
    try:
        subprocess.run(cmd, text=True, capture_output=True, check=True, cwd=output_dir)
    except subprocess.CalledProcessError as e:
        return False, e.stderr, None, input_file, cmd_str
    treefile = os.path.join(output_dir, output_prefix + ".treefile")
    return True, "IQTREE execution complete", treefile, input_file, cmd_str

def handle_download_newick(win):
    """Handles saving the Newick tree to a file."""
    default_name = win.output_prefix if hasattr(win, "output_prefix") else "output"
    save_path = fd.asksaveasfilename(defaultextension=".newick",
                                     initialfile=default_name,
                                     filetypes=[("Newick Files", "*.newick"), ("All Files", "*.*")])
    if save_path:
        try:
            with open(save_path, "w") as f:
                f.write(win.tree_content)
            eg.popup("Result saved: " + save_path)
        except Exception as e:
            eg.popup("Failed to save file:\n" + str(e))

def handle_download_all_files(win):
    """Creates an archive of all IQ-TREE output files and allows the user to save it."""
    try:
        output_dir = os.path.dirname(win.treefile)
        edited_filename = f"{win.output_prefix}_edited.nwk" if hasattr(win, "output_prefix") else "edited.nwk"
        edited_file_path = os.path.join(output_dir, edited_filename)
        with open(edited_file_path, "w") as f:
            f.write(win.tree_content)
        # 安全なテンポラリディレクトリを作成してアーカイブを作成
        temp_dir = tempfile.mkdtemp(prefix="iqtree_archive_")
        base_name = os.path.join(temp_dir, "archive")
        archive_file = shutil.make_archive(base_name=base_name, format="zip", root_dir=output_dir)
    except Exception as e:
        eg.popup("Failed to create archive:\n" + str(e))
        return
    default_zip_name = f"iqtree_all_{win.output_prefix}" if hasattr(win, "output_prefix") else "iqtree_all_output"
    save_path = fd.asksaveasfilename(defaultextension=".zip",
                                     initialfile=default_zip_name,
                                     filetypes=[("Zip Files", "*.zip"), ("All Files", "*.*")])
    if save_path:
        try:
            shutil.copyfile(archive_file, save_path)
            eg.popup("Result saved: " + save_path)
        except Exception as e:
            eg.popup("Failed to save file:\n" + str(e))
    # 一時ディレクトリを削除してクリーンアップ
    shutil.rmtree(temp_dir)

# ------------------------------------------------------------------------------
# ETE3 visualization functions
# ------------------------------------------------------------------------------

def my_layout(node):
    """Custom layout function for ETE3 tree rendering."""
    from ete3 import TextFace
    if not node.is_leaf() and node.name:
        if "/" in node.name:
            supports = node.name.split('/')
            display_text = "\n".join(supports)
        else:
            try:
                display_text = str(float(node.name))
            except ValueError:
                display_text = node.name
        face = TextFace(display_text, fsize=10)
        node.add_face(face, column=0, position="branch-top")

def handle_view_tree(win):
    """Renders the tree using ETE3 and opens the result in a web browser."""
    try:
        from ete3 import Tree, TreeStyle
    except ImportError:
        eg.popup("Error: ETE3 is not installed.")
        return
    try:
        newick_str = win.tree_content.strip()
        t = Tree(newick_str, format=1)
        for node in t.traverse():
            if not node.is_leaf() and node.support is not None:
                support_str = str(node.support)
                if "/" in support_str:
                    node.support = "\n".join(support_str.split("/"))
                else:
                    try:
                        node.support = str(float(support_str))
                    except ValueError:
                        node.support = support_str
        ts = TreeStyle()
        ts.show_leaf_name = True
        ts.layout_fn = my_layout
        ts.show_branch_support = False
        midpoint = t.get_midpoint_outgroup()
        t.set_outgroup(midpoint)
        tmp_dir = tempfile.mkdtemp(prefix="iqtree_ete_")
        img_path = os.path.join(tmp_dir, "tree.png")
        html_path = os.path.join(tmp_dir, "tree.html")
        t.render(img_path, w=600, units="px", tree_style=ts)
        html_content = f"""<html>
  <head>
    <meta charset="UTF-8">
    <title>IQTREE Tree Viewer</title>
  </head>
  <body>
    <h1>IQTREE Tree Viewer</h1>
    <img src="tree.png" alt="Tree">
  </body>
</html>"""
        with open(html_path, "w") as f:
            f.write(html_content)
        webbrowser.open("file://" + os.path.abspath(html_path))
    except Exception as e:
        eg.popup("Failed to display tree:\n" + str(e))

def handle_add_atha_gene_names(win):
    """
    Searches for AGI codes in the tree content and appends the corresponding gene name
    (from the reference file) enclosed in '<>' immediately after the match.
    """
    parent = Path(__file__).resolve().parent
    gene_file = parent.joinpath("dat/Athaliana_447_Araport11.geneName.txt")
    mapping = {}
    try:
        with open(gene_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    mapping[parts[0]] = parts[1]
    except Exception as e:
        eg.popup("Failed to load gene name file:\n" + str(e))
        return
    new_text = win.tree_content
    for agi, gene_name in mapping.items():
        pattern = re.escape(agi) + r'(?!<)'
        replacement = r'\g<0><' + gene_name + '>'
        new_text = re.sub(pattern, replacement, new_text)
    win.tree_content = new_text
    try:
        with open(win.treefile, "w") as f:
            f.write(new_text)
    except Exception as e:
        eg.popup("Failed to update tree file:\n" + str(e))
    try:
        win["tree_output"].update(new_text)
    except Exception:
        pass
    eg.popup("Gene names added successfully.")

# ------------------------------------------------------------------------------
# Alignment functions
# ------------------------------------------------------------------------------

def open_alignment_options_window(portal_text):
    """
    Opens the alignment options window.
    When "Run Alignment" is executed, runs MAFFT via a progress window.
    If the resulting alignment result window returns "Go to Trim" or "Go to IQTREE",
    the alignment option window is automatically closed and the corresponding option
    window is opened.
    """
    layout = [
        [eg.Multiline(key="alignment_input", default_text=portal_text, size=(80,20),
                      expand_x=True, expand_y=True)],
        [eg.Text("Threads:"), eg.Input(default_text="4", key="threads", size=(5,1))],
        [eg.Text("Mode:"), 
         eg.Radio("auto", "align_mode", default=True, key="mode_auto"),
         eg.Radio("linsi", "align_mode", key="mode_linsi"),
         eg.Radio("ginsi", "align_mode", key="mode_ginsi"),
         eg.Radio("einsi", "align_mode", key="mode_einsi")],
        [eg.Button("Run Alignment"), eg.Button("Cancel")]
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
            mode = "auto" if values.get("mode_auto") else (
                "linsi" if values.get("mode_linsi") else (
                    "ginsi" if values.get("mode_ginsi") else "einsi"
                )
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
                        open_trim_options_window(result[1])
                    else:
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
         [eg.Multiline(key="alignment_output", default_text=result_text, size=(80,20),
                        expand_x=True, expand_y=True)],
         [eg.Button("Copy"), eg.Button("Download"), 
          eg.Button("Go to Trim"), eg.Button("Go to IQTREE"), eg.Button("Close")]
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
            save_path = fd.asksaveasfilename(defaultextension=".txt",
                                               initialfile="alignment_result",
                                               filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
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

# ------------------------------------------------------------------------------
# Trim functions
# ------------------------------------------------------------------------------

def open_trim_options_window(portal_text):
    """
    Opens the trim options window.
    When "Run Trim" is executed, runs trimal.
    If the resulting trim result window returns "Go to IQTREE", the trim option window is closed
    and the IQTREE option window is automatically opened.
    """
    trimal_version = get_trimal_version()
    layout = [
        [eg.Multiline(key="trim_input", default_text=portal_text, size=(80,20),
                      expand_x=True, expand_y=True)],
        [eg.Text("trimal: " + trimal_version)],
        [eg.Text("Mode:"), 
         eg.Radio("automated1", "trim_mode", default=True, key="trim_mode_automated1"),
         eg.Radio("gappyout", "trim_mode", key="trim_mode_gappyout"),
         eg.Radio("strict", "trim_mode", key="trim_mode_strict"),
         eg.Radio("strictplus", "trim_mode", key="trim_mode_strictplus"),
         eg.Radio("nogap", "trim_mode", key="trim_mode_nogap")],
        [eg.Button("Run Trim"), eg.Button("Cancel")]
    ]
    opt_win = eg.Window("Trim Options", layout, resizable=True)
    while True:
        event, values = opt_win.read()
        if event in ("Cancel", eg.WINDOW_CLOSED):
            break
        elif event == "Run Trim":
            mode = ("automated1" if values.get("trim_mode_automated1") 
                    else "gappyout" if values.get("trim_mode_gappyout") 
                    else "strict" if values.get("trim_mode_strict") 
                    else "strictplus" if values.get("trim_mode_strictplus") 
                    else "nogap")
            trim_input = values["trim_input"]
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".fasta") as temp_in:
                input_path = temp_in.name
                temp_in.write(trim_input)
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".fasta") as temp_out:
                output_path = temp_out.name
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as temp_html:
                html_path = temp_html.name
            cmd = ["trimal", "-in", input_path, "-out", output_path, "-htmlout", html_path, f"-{mode}"]
            try:
                subprocess.run(cmd, text=True, capture_output=True, check=True)
            except subprocess.CalledProcessError as e:
                eg.popup("Error: trimal execution failed.\n" + e.stderr)
                for p in (input_path, output_path, html_path):
                    os.remove(p)
                continue
            with open(output_path, "r") as f:
                trimmed_result = f.read()
            action = open_trim_result_window(trimmed_result, output_path, html_path)
            if action == "Go to IQTREE":
                opt_win.close()
                open_iqtree_options_window(trimmed_result)
                return
    opt_win.close()

def open_trim_result_window(trimmed_result, output_path, html_path):
    """
    Displays the trim result window.
    If the user selects "Go to IQTREE", returns that event.
    Otherwise, closes normally.
    """
    layout = [
        [eg.Multiline(key="trimmed_output", default_text=trimmed_result, size=(80,20),
                        expand_x=True, expand_y=True)],
        [eg.Button("Copy"), eg.Button("Show result"), eg.Button("Download"), 
         eg.Button("Go to IQTREE"), eg.Button("Close")]
    ]
    res_win = eg.Window("Trim Result", layout, modal=True, finalize=True, resizable=True)
    ret = None
    while True:
        event, vals = res_win.read()
        if event in ("Close", eg.WINDOW_CLOSED):
            break
        elif event == "Copy":
            eg.set_clipboard(vals["trimmed_output"])
            eg.popup("Result copied to clipboard.")
        elif event == "Show result":
            webbrowser.open("file://" + os.path.abspath(html_path))
        elif event == "Download":
            save_path = fd.asksaveasfilename(defaultextension=".fasta",
                                               filetypes=[("FASTA Files", "*.fasta"), ("Text Files", "*.txt"), ("All Files", "*.*")])
            if save_path:
                try:
                    with open(save_path, "w") as f:
                        f.write(vals["trimmed_output"])
                    eg.popup("Result saved: " + save_path)
                except Exception as e:
                    eg.popup("Failed to save file:\n" + str(e))
        elif event == "Go to IQTREE":
            ret = event
            break
    res_win.close()
    return ret

# ------------------------------------------------------------------------------
# IQTREE GUI functions
# ------------------------------------------------------------------------------

def open_iqtree_options_window(portal_text):
    """
    Opens the IQ-TREE options window.
    When "Run IQTREE" is executed, runs IQ-TREE via a progress window.
    After execution, displays the IQ-TREE result window.
    """
    layout = [
        [eg.Multiline(key="iqtree_input", default_text=portal_text, size=(80,20),
                      expand_x=True, expand_y=True)],
        [eg.Text("IQ-TREE version: " + get_iqtree_version())],
        [eg.Text("threads (0 = auto):"), eg.Input(default_text="0", key="threads", size=(10,1))],
        [eg.Text("Confidence analyses")],
        [eg.Text("UFboot:"), eg.Input(default_text="1000", key="ufboot", size=(10,1)),
         eg.Text("SH-aLR:"), eg.Input(default_text="1000", key="sh_alr", size=(10,1)),
         eg.Text("lbp:"), eg.Input(default_text="0", key="lbp", size=(10,1))],
        [eg.Text("abayes:"), eg.Checkbox("Use abayes", default=False, key="abayes")],
        [eg.Text("Substitution model:"), eg.Input(default_text="auto", key="subst_model", size=(20,1))],
        [eg.Text("Output prefix:"), eg.Input(default_text="tmp", key="output_prefix", size=(10,1))],
        [eg.Button("Run IQTREE"), eg.Button("Cancel")]
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
            # 置換モデルチェックは行わず、入力された値をそのまま使用
            subst_model_input = values["subst_model"].strip()
            iqtree_input = values["iqtree_input"].strip()
            output_prefix = values["output_prefix"].strip()
            result = run_with_progress("IQTREE analysis is running...", run_iqtree,
                                       iqtree_input,
                                       threads,
                                       ufboot_input,
                                       sh_alr_input,
                                       lbp_input,
                                       values["abayes"],
                                       subst_model_input,
                                       output_prefix)
            if not result[0]:
                eg.popup("Error: IQTREE execution failed.\n" + result[1])
            else:
                open_iqtree_result_window(values, result[2])
        # Allow multiple executions
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
            [eg.Multiline(key="tree_output", default_text=tree_content, size=(80,20),
                          expand_x=True, expand_y=True)],
            [eg.Button("Copy"), eg.Button("View Tree"), eg.Button("Add Atha gene names")],
            [eg.Button("Download Newick"), eg.Button("Download all files")],
            [eg.Button("Close")]
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

# ------------------------------------------------------------------------------
# Portal Window
# ------------------------------------------------------------------------------

def open_portal_window():
    """Opens the main portal window for Phylo_GUI."""
    portal_layout = [
        [eg.Text("Phylo_GUI Portal: " + version)],
        [eg.Multiline(key="portal_input", size=(80,20), 
                      expand_x=True, expand_y=True)],
        [eg.Button("Load File"),
         eg.Button("Go to Alignment"),
         eg.Button("Go to Trim"),
         eg.Button("Go to IQTREE"),
         eg.Button("Quit")]
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

def main():
    open_portal_window()

if __name__ == "__main__":
    main()