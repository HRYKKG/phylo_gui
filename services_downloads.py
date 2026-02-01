import os
import re
import shutil
import tempfile
from pathlib import Path
import tkinter.filedialog as fd

import TkEasyGUI as eg


def handle_download_newick(win):
    """Handles saving the Newick tree to a file."""
    default_name = win.output_prefix if hasattr(win, "output_prefix") else "output"
    save_path = fd.asksaveasfilename(
        defaultextension=".newick",
        initialfile=default_name,
        filetypes=[("Newick Files", "*.newick"), ("All Files", "*.*")],
    )
    if save_path:
        try:
            with open(save_path, "w") as f:
                f.write(win.tree_content)
            eg.popup("Result saved: " + save_path)
        except Exception as e:
            eg.popup("Failed to save file:\n" + str(e))


def handle_download_all_files(win):
    """Creates an archive of all IQ-TREE output files and allows the user to save it."""
    output_dir = os.path.dirname(win.treefile)
    edited_filename = f"{win.output_prefix}_edited.nwk" if hasattr(win, "output_prefix") else "edited.nwk"
    edited_file_path = os.path.join(output_dir, edited_filename)
    try:
        with open(edited_file_path, "w") as f:
            f.write(win.tree_content)
    except Exception as e:
        eg.popup("Failed to write edited tree file:\n" + str(e))
        return

    try:
        with tempfile.TemporaryDirectory(prefix="iqtree_archive_") as temp_dir:
            base_name = os.path.join(temp_dir, "archive")
            archive_file = shutil.make_archive(base_name=base_name, format="zip", root_dir=output_dir)
            default_zip_name = f"iqtree_all_{win.output_prefix}" if hasattr(win, "output_prefix") else "iqtree_all_output"
            save_path = fd.asksaveasfilename(
                defaultextension=".zip",
                initialfile=default_zip_name,
                filetypes=[("Zip Files", "*.zip"), ("All Files", "*.*")],
            )
            if save_path:
                shutil.copyfile(archive_file, save_path)
                eg.popup("Result saved: " + save_path)
    except Exception as e:
        eg.popup("Failed to create archive:\n" + str(e))


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
        pattern = re.escape(agi) + r"(?!<)"
        replacement = r"\g<0><" + gene_name + ">"
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
