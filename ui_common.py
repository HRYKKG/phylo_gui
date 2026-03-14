import TkEasyGUI as eg
from pathlib import Path


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


def relax_modal_window(window):
    """Keep modal grab behavior but clear the topmost flag after the window is shown."""
    try:
        window.window.after_idle(lambda: window.keep_on_top(False))
    except Exception:
        return


def reactivate_window(window):
    """Best-effort restore of focus to a window after native dialogs close."""
    if window is None:
        return
    try:
        window.un_hide()
    except Exception:
        pass
    try:
        window.normal()
    except Exception:
        pass
    try:
        window.focus()
    except Exception:
        return


def _release_current_grab(window):
    try:
        current_grab = window.window.grab_current()
    except Exception:
        return None
    if current_grab is None:
        return None
    try:
        current_grab.grab_release()
    except Exception:
        return None
    return current_grab


def _restore_grab(widget):
    if widget is None:
        return
    try:
        if widget.winfo_exists():
            widget.grab_set()
    except Exception:
        return


def run_with_progress(initial_message, run_func, *args, parent_window=None, **kwargs):
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
    prog_win = eg.Window("Progress", prog_layout, modal=False, resizable=True)
    previous_grab = _release_current_grab(prog_win)
    parent_hidden = False
    if parent_window is not None:
        try:
            parent_window.hide()
            parent_hidden = True
        except Exception:
            parent_hidden = False
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
    if parent_hidden:
        try:
            parent_window.un_hide()
            parent_window.refresh()
        except Exception:
            pass
    _restore_grab(previous_grab)
    return result


def load_file(window_obj, key):
    """Opens a file dialog to load a FASTA file and updates the given GUI element."""
    context = getattr(window_obj, "context", None)
    initial_folder = str(context.last_open_dir) if context and getattr(context, "last_open_dir", None) else None
    file_path = eg.popup_get_file(title="Please select a FASTA file", initial_folder=initial_folder)
    try:
        if file_path:
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                if context is not None:
                    context.last_open_dir = Path(file_path).resolve().parent
                window_obj[key].update(content)
                return content
            except Exception as e:
                eg.popup("An error occurred while reading the file:\n" + str(e))
    finally:
        reactivate_window(window_obj)
    return None
