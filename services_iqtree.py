import os
import re
import shutil
import subprocess
import tempfile


def _iqtree_bin():
    return "iqtree" if shutil.which("iqtree") else ("iqtree3" if shutil.which("iqtree3") else None)


def get_iqtree_version():
    """Returns the version of IQ-TREE or an error message."""
    iqtree_bin = _iqtree_bin()
    if iqtree_bin is None:
        return "Failed to retrieve version"
    try:
        result = subprocess.run([iqtree_bin, "--version"], text=True, capture_output=True, check=True)
        output = result.stdout.strip() or result.stderr.strip()
        if not output:
            return "Failed to retrieve version"
        first_line = output.splitlines()[0]
        m = re.search(r"version\s+([0-9.]+)", first_line, re.IGNORECASE)
        return m.group(1) if m else first_line
    except (subprocess.CalledProcessError, OSError):
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
            return model_line
        return "Model information not found"
    except Exception as e:
        return "Failed to retrieve information: " + str(e)


def build_iqtree_cmd(iqtree_input, threads, ufboot, sh_alr, lbp, abayes, subst_model, prefix, iqtree_bin):
    """
    Builds the IQ-TREE command based on provided parameters.
    If subst_model is "auto" (case-insensitive), the option "-m MFP" is used.
    """
    cmd = [iqtree_bin, "-s", iqtree_input, "--prefix", prefix]
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
    if subst_model.lower() == "auto":
        cmd.extend(["-m", "MFP"])
    else:
        cmd.extend(["-m", subst_model])
    return cmd


def run_iqtree(iqtree_input, threads, ufboot, sh_alr, lbp, abayes, subst_model, output_prefix):
    """
    Executes IQ-TREE with the specified parameters.
    Returns a tuple: (success, message, treefile, input_file, command_string).
    """
    iqtree_bin = _iqtree_bin()
    if iqtree_bin is None:
        return False, "iqtree not found", None, None, ""
    output_dir = tempfile.mkdtemp(prefix="tmp_iqtree_")
    os.makedirs(output_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=output_dir, prefix="tmp_input", suffix=".fasta") as temp_in:
        input_file = temp_in.name
        temp_in.write(iqtree_input)
    cmd = build_iqtree_cmd(input_file, threads, ufboot, sh_alr, lbp, abayes, subst_model, output_prefix, iqtree_bin)
    cmd_str = " ".join(cmd)
    try:
        subprocess.run(cmd, text=True, capture_output=True, check=True, cwd=output_dir)
    except (subprocess.CalledProcessError, OSError) as e:
        err = e.stderr if isinstance(e, subprocess.CalledProcessError) and e.stderr else str(e)
        return False, err, None, input_file, cmd_str
    treefile = os.path.join(output_dir, output_prefix + ".treefile")
    return True, "IQTREE execution complete", treefile, input_file, cmd_str
