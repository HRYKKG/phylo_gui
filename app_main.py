import shutil

import TkEasyGUI as eg

from ui_portal import open_portal_window


def check_required_tools():
    required = ["mafft", "trimal"]
    missing = [tool for tool in required if shutil.which(tool) is None]
    if shutil.which("iqtree") is None and shutil.which("iqtree3") is None:
        missing.append("iqtree (or iqtree3)")
    if missing:
        eg.popup("Missing required tools:\n" + "\n".join(missing))
        return False
    return True


def main():
    if not check_required_tools():
        return
    open_portal_window()


if __name__ == "__main__":
    main()
