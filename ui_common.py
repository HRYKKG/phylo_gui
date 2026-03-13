import TkEasyGUI as eg


def discard_pending_events(window, max_reads=3):
    """Best-effort flush of queued GUI events after a modal child window closes."""
    for _ in range(max_reads):
        try:
            event, _ = window.read(timeout=1)
        except Exception:
            break
        if event in (None, eg.WINDOW_CLOSED, "__TIMEOUT__"):
            break
        if isinstance(event, str) and event.lower() == "__timeout__":
            break


def run_with_progress(initial_message, run_func, *args, **kwargs):
    """
    Displays a progress window with an initial message, executes the given function
    (blocking), then updates the progress window with a success message and waits for
    user confirmation.

    If an error occurs, the progress window is closed immediately.
    """
    prog_layout = [
        [eg.Multiline(key="progress", default_text=initial_message, size=(80, 10))],
        [eg.Button("OK", key="ok", disabled=True)],
    ]
    prog_win = eg.Window("Progress", prog_layout, modal=True, resizable=True)
    prog_win.refresh()

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
        prog_win.close()
    return result


def load_file(window_obj, key):
    """Opens a file dialog to load a FASTA file and updates the given GUI element."""
    file_path = eg.popup_get_file(title="Please select a FASTA file")
    if file_path:
        try:
            with open(file_path, "r") as f:
                content = f.read()
            window_obj[key].update(content)
            return content
        except Exception as e:
            eg.popup("An error occurred while reading the file:\n" + str(e))
    return None
