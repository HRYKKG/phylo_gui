import os
import subprocess
import tempfile


def get_trimal_version():
    """Returns the version of trimal or an error message."""
    try:
        result = subprocess.run(["trimal", "--version"], text=True, capture_output=True, check=True)
        output = result.stdout.strip() or result.stderr.strip()
        return output if output else "Failed to retrieve version"
    except (subprocess.CalledProcessError, OSError):
        return "Failed to retrieve version"


def run_trimal(trim_input, mode):
    """
    Runs trimal and returns (success, message, trimmed_result, output_path, html_path).
    On failure, message contains stderr and temp files are cleaned up.
    """
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
    except (subprocess.CalledProcessError, OSError) as e:
        for p in (input_path, output_path, html_path):
            if os.path.exists(p):
                os.remove(p)
        err = e.stderr if isinstance(e, subprocess.CalledProcessError) and e.stderr else str(e)
        return False, err, None, None, None

    with open(output_path, "r") as f:
        trimmed_result = f.read()
    return True, "trimal execution complete", trimmed_result, output_path, html_path
