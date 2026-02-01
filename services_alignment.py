import subprocess


def run_mafft(fasta_text, threads=4, mode="auto"):
    """Executes MAFFT with the given parameters and returns (success, output)."""
    try:
        cmd = ["mafft", "--thread", str(threads)]

        if mode == "auto":
            cmd.append("--auto")
        elif mode == "linsi":
            cmd.extend(["--localpair", "--maxiterate", "1000"])
        elif mode == "ginsi":
            cmd.extend(["--globalpair", "--maxiterate", "1000"])
        elif mode == "einsi":
            cmd.extend(["--genafpair", "--maxiterate", "1000", "--ep", "0"])

        cmd.append("-")

        result = subprocess.run(cmd, input=fasta_text, text=True, capture_output=True, check=True)
        return True, result.stdout
    except (subprocess.CalledProcessError, OSError) as e:
        err = e.stderr if isinstance(e, subprocess.CalledProcessError) and e.stderr else str(e)
        return False, err
