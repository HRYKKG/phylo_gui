import TkEasyGUI as eg
import subprocess
import tkinter.filedialog as fd
import tempfile
import os
import re
import webbrowser
import shutil
import time
import tkinter as tk  # for clipboard operations

# Helper function to set clipboard text using tkinter
def clipboard_set_text(text):
    r = tk.Tk()
    r.withdraw()  # hide window
    r.clipboard_clear()
    r.clipboard_append(text)
    r.update()
    r.destroy()

# ----- Preprocessing function -----
def preprocess_newick(newick_str):
    return newick_str

# ----- Basic functions -----
def load_file(window_obj, key):
    file_path = eg.popup_get_file(title="Please select a FASTA file")
    if file_path:
        try:
            with open(file_path, "r") as f:
                content = f.read()
            window_obj[key].update(content)
        except Exception as e:
            eg.popup("An error occurred while reading the file:\n" + str(e))

def run_mafft(fasta_text, threads=4, mode="auto"):
    try:
        mode_option = "--auto" if mode=="auto" else f"--{mode}"
        cmd = ["mafft", mode_option, "--thread", str(threads), "-"]
        result = subprocess.run(cmd, input=fasta_text, text=True, capture_output=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def get_trimal_version():
    try:
        result = subprocess.run(["trimal", "--version"], text=True, capture_output=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "Failed to retrieve version"

def get_iqtree_version():
    try:
        result = subprocess.run(["iqtree", "--version"], text=True, capture_output=True, check=True)
        output = result.stdout.strip()
        first_line = output.splitlines()[0]
        m = re.search(r"version\s+([0-9.]+)", first_line, re.IGNORECASE)
        return m.group(1) if m else first_line
    except subprocess.CalledProcessError:
        return "Failed to retrieve version"

# Get the first occurrence of the line starting with "Numbers in parentheses are"
def get_model_line(iqtree_file, prefix):
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

# ----- IQTREE functions -----
def build_iqtree_cmd(iqtree_input, threads, ufboot, sh_alr, lbp, abayes, subst_model, prefix):
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
    if subst_model.strip().lower() == "auto":
        cmd.extend(["-m", "MFP"])
    else:
        cmd.extend(["-m", subst_model])
    return cmd

def run_iqtree(iqtree_input, threads, ufboot, sh_alr, lbp, abayes, subst_model, output_prefix):
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
    try:
        output_dir = os.path.dirname(win.treefile)
        edited_filename = win.output_prefix + "_edited.nwk" if hasattr(win, "output_prefix") else "edited.nwk"
        edited_file_path = os.path.join(output_dir, edited_filename)
        with open(edited_file_path, "w") as f:
            f.write(win.tree_content)
        temp_base = tempfile.mktemp(prefix="iqtree_all_")
        archive_file = temp_base + ".zip"
        shutil.make_archive(base_name=temp_base, format="zip", root_dir=output_dir)
    except Exception as e:
        eg.popup("Failed to create archive:\n" + str(e))
        return
    default_zip_name = "iqtree_all_" + win.output_prefix if hasattr(win, "output_prefix") else "iqtree_all_output"
    save_path = fd.asksaveasfilename(defaultextension=".zip",
                                     initialfile=default_zip_name,
                                     filetypes=[("Zip Files", "*.zip"), ("All Files", "*.*")])
    if save_path:
        try:
            shutil.copyfile(archive_file, save_path)
            eg.popup("Result saved: " + save_path)
        except Exception as e:
            eg.popup("Failed to save file:\n" + str(e))
    os.remove(archive_file)

# ----- ETE3 custom layout function -----
def my_layout(node):
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
    try:
        from ete3 import Tree, TreeStyle
    except ImportError:
        eg.popup("Error: ETE3 is not installed.")
        return
    try:
        newick_str = win.tree_content.strip()
        newick_str = preprocess_newick(newick_str)
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
    gene_file = "./dat/Athaliana_447_Araport11.geneName.txt"
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
        pattern = r'\b' + re.escape(agi) + r'\b(?!<)'
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

# ----- Alignment functions -----
def open_alignment_options_window(portal_text):
    layout = [
        [eg.Multiline(key="alignment_input", default_text=portal_text, size=(80,20))],
        [eg.Text("Threads:"), eg.Input(default_text="4", key="threads", size=(5,1))],
        [eg.Text("Mode:"), 
         eg.Radio("auto", "align_mode", default=True, key="mode_auto"),
         eg.Radio("linsi", "align_mode", key="mode_linsi"),
         eg.Radio("ginsi", "align_mode", key="mode_ginsi"),
         eg.Radio("einsi", "align_mode", key="mode_einsi")],
        [eg.Button("Run Alignment"), eg.Button("Cancel")]
    ]
    win = eg.Window("Alignment Options", layout)
    while True:
        event, values = win.read()
        if event in ("Cancel", eg.WINDOW_CLOSED):
            break
        elif event == "Run Alignment":
            try:
                threads = int(values["threads"])
                if threads < 1:
                    raise ValueError("Threads must be at least 1.")
            except ValueError as ve:
                eg.popup("Threads input error: " + str(ve))
                continue
            mode = ("auto" if values.get("mode_auto") 
                    else "linsi" if values.get("mode_linsi") 
                    else "ginsi" if values.get("mode_ginsi") 
                    else "einsi")
            alignment_input = values["alignment_input"]
            success, output = run_mafft(alignment_input, threads, mode)
            if not success:
                eg.popup("Error: mafft execution failed.\n" + output)
            else:
                win.close()
                open_alignment_result_window(output)
                return
    win.close()

def open_alignment_result_window(result_text):
    layout = [
         [eg.Multiline(key="alignment_output", default_text=result_text, size=(80,20))],
         [eg.Button("Copy"), eg.Button("Download"), 
          eg.Button("Go to Trim"), eg.Button("Go to IQTREE"), eg.Button("Close")]
    ]
    win = eg.Window("Alignment Result", layout, modal=True, finalize=True)
    while True:
        event, values = win.read()
        if event in ("Close", eg.WINDOW_CLOSED):
            break
        elif event == "Copy":
            clipboard_set_text(values["alignment_output"])
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
        elif event == "Go to Trim":
            win.close()
            open_trim_options_window(values["alignment_output"])
            return
        elif event == "Go to IQTREE":
            win.close()
            open_iqtree_options_window(values["alignment_output"])
            return
    win.close()

# ----- Trim functions (Options and Result) -----
def open_trim_options_window(portal_text):
    trimal_version = get_trimal_version()
    layout = [
        [eg.Multiline(key="trim_input", default_text=portal_text, size=(80,20))],
        [eg.Text("trimal: " + trimal_version)],
        [eg.Text("Mode:"), 
         eg.Radio("automated1", "trim_mode", default=True, key="trim_mode_automated1"),
         eg.Radio("gappyout", "trim_mode", key="trim_mode_gappyout"),
         eg.Radio("strict", "trim_mode", key="trim_mode_strict"),
         eg.Radio("strictplus", "trim_mode", key="trim_mode_strictplus"),
         eg.Radio("nogap", "trim_mode", key="trim_mode_nogap")],
        [eg.Button("Run Trim"), eg.Button("Cancel")]
    ]
    win = eg.Window("Trim Options", layout)
    while True:
        event, values = win.read()
        if event in ("Cancel", eg.WINDOW_CLOSED):
            win.close()
            return
        elif event == "Run Trim":
            trim_input = values["trim_input"]
            mode = ("automated1" if values.get("trim_mode_automated1") 
                    else "gappyout" if values.get("trim_mode_gappyout") 
                    else "strict" if values.get("trim_mode_strict") 
                    else "strictplus" if values.get("trim_mode_strictplus") 
                    else "nogap")
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
                win.close()
                return
            with open(output_path, "r") as f:
                trimmed_result = f.read()
            win.close()
            open_trim_result_window(trimmed_result, output_path, html_path)
            return

def open_trim_result_window(trimmed_result, output_path, html_path):
    layout = [
        [eg.Multiline(key="trimmed_output", default_text=trimmed_result, size=(80,20))],
        [eg.Button("Copy"), eg.Button("Show result"), eg.Button("Download"), 
         eg.Button("Go to IQTREE"), eg.Button("Close")]
    ]
    win = eg.Window("Trim Result", layout, modal=True, finalize=True)
    win.html_path = html_path
    win.output_file = output_path
    while True:
        event, vals = win.read()
        if event in ("Close", eg.WINDOW_CLOSED):
            break
        elif event == "Copy":
            clipboard_set_text(vals["trimmed_output"])
            eg.popup("Result copied to clipboard.")
        elif event == "Show result":
            webbrowser.open("file://" + os.path.abspath(win.html_path))
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
            win.close()
            open_iqtree_options_window(vals["trimmed_output"])
            return
    win.close()
    for p in (output_path, html_path):
        os.remove(p)

# ----- IQTREE functions -----
def open_iqtree_options_window(portal_text):
    layout = [
        [eg.Multiline(key="iqtree_input", default_text=portal_text, size=(80,20))],
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
    win = eg.Window("IQTREE Options", layout)
    while True:
        event, values = win.read()
        if event in ("Cancel", eg.WINDOW_CLOSED):
            break
        elif event == "Run IQTREE":
            allowed_models = {"LG", "Poisson", "cpREV", "mtREV", "Dayhoff", "mtMAM",
                              "JTT", "WAG", "mtART", "mtZOA", "VT", "rtREV", "DCMut", "PMB", "HIVb",
                              "HIVw", "JTTDCMut", "FLU", "Blosum62", "GTR20", "mtMet", "mtVer", "mtInv", "FLAVI",
                              "Q.LG", "Q.pfam", "Q.pfam_gb", "Q.bird", "Q.mammal", "Q.insect", "Q.plant", "Q.yeast",
                              "auto"}
            if values["subst_model"] not in allowed_models:
                eg.popup("Error: Invalid substitution model.")
                continue
            prog_layout = [
                [eg.Multiline(key="progress", default_text="IQTREE analysis is running...\n", size=(80,10))],
                [eg.Button("OK", key="ok", disabled=True)]
            ]
            prog_win = eg.Window("Progress", prog_layout)
            prog_win.refresh()
            success, output, treefile, input_file, cmd_str_ret = run_iqtree(
                values["iqtree_input"],
                values["threads"],
                values["ufboot"],
                values["sh_alr"],
                values["lbp"],
                values["abayes"],
                values["subst_model"],
                values["output_prefix"]
            )
            if not success:
                prog_win["progress"].update("Error: " + output + "\nPress OK to close.")
            else:
                prog_win["progress"].update("IQTREE analysis completed.\nPress OK to continue.")
            prog_win["ok"].update(disabled=False)
            while True:
                event_prog, _ = prog_win.read()
                if event_prog and event_prog.lower() == "ok":
                    break
            prog_win.close()
            if not success:
                eg.popup("Error: IQTREE execution failed.\n" + output)
            else:
                open_iqtree_result_window(values, treefile)
        # Allow multiple executions
    win.close()

def open_iqtree_result_window(values, treefile):
    try:
        with open(treefile, "r") as f:
            tree_content = f.read()
        iqtree_txt = os.path.join(os.path.dirname(treefile), values["output_prefix"] + ".iqtree")
        model_info = get_model_line(iqtree_txt, values["output_prefix"])
        result_header = f"{model_info}\n"
        layout = [
            [eg.Text(result_header)],
            [eg.Multiline(key="tree_output", default_text=tree_content, size=(80,20))],
            [eg.Button("Copy"), eg.Button("View Tree"), eg.Button("Add Atha gene names")],
            [eg.Button("Download Newick"), eg.Button("Download all files")],
            [eg.Button("Close")]
        ]
        win_res = eg.Window("IQTREE Result", layout, modal=True, finalize=True)
        win_res.output_prefix = values["output_prefix"]
        win_res.tree_content = tree_content
        win_res.treefile = treefile
        while True:
            event, _ = win_res.read()
            if event in ("Close", eg.WINDOW_CLOSED):
                break
            elif event == "Copy":
                clipboard_set_text(win_res["tree_output"].get())
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

# ----- Portal Window -----
def open_portal_window():
    portal_layout = [
        [eg.Multiline(key="portal_input", size=(80,20))],
        [eg.Button("Load File"),
         eg.Button("Go to Alignment"),
         eg.Button("Go to Trim"),
         eg.Button("Go to IQTREE"),
         eg.Button("Quit")]
    ]
    win = eg.Window("Portal", portal_layout)
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