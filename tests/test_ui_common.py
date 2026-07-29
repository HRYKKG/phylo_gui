import importlib
import sys
import types
import unittest
import threading
from unittest.mock import patch


class FakeButton:
    def __init__(self, key, disabled=False):
        self.key = key
        self.disabled = disabled

    def update(self, *, disabled):
        self.disabled = disabled


sys.modules["TkEasyGUI"] = types.SimpleNamespace(
    Button=FakeButton,
    WINDOW_CLOSED="__WINDOW_CLOSED__",
)
ui_common = importlib.import_module("ui_common")


class FakeTkWindow:
    def __init__(self):
        self.bindings = {}

    def bind(self, event_name, callback, add=None):
        self.bindings[event_name] = callback


class FakeWindow:
    modal = True

    def __init__(self, buttons):
        self.key_elements = {button.key: button for button in buttons}
        self.window = FakeTkWindow()


class InactiveButtonIndicatorTests(unittest.TestCase):
    def install_indicator(self, buttons):
        window = FakeWindow(buttons)
        ui_common.install_inactive_button_indicator(window)
        return window

    def test_repeated_focus_out_preserves_original_button_states(self):
        enabled = FakeButton("enabled")
        disabled = FakeButton("disabled", disabled=True)
        window = self.install_indicator([enabled, disabled])

        window.window.bindings["<FocusOut>"]()
        window.window.bindings["<FocusOut>"]()
        window.window.bindings["<FocusIn>"]()

        self.assertFalse(enabled.disabled)
        self.assertTrue(disabled.disabled)

    def test_each_inactive_transition_takes_a_fresh_snapshot(self):
        button = FakeButton("button")
        window = self.install_indicator([button])

        window._inactive_buttons_set_inactive()
        window._inactive_buttons_set_active()
        button.disabled = True
        window._inactive_buttons_set_inactive()
        window._inactive_buttons_set_active()

        self.assertTrue(button.disabled)


class FakeProgressRoot:
    def grab_current(self):
        return None

    def protocol(self, _name, _callback):
        return None


class FakeProgressWindow:
    modal = False

    def __init__(self):
        self.window = FakeProgressRoot()
        self.closed = False

    def refresh(self):
        return None

    def read(self, timeout=None):
        return "__TIMEOUT__", {}

    def close(self):
        self.closed = True


class FakeParentWindow:
    def __init__(self):
        self.hidden = False
        self.refreshed = False

    def hide(self):
        self.hidden = True

    def un_hide(self):
        self.hidden = False

    def refresh(self):
        self.refreshed = True


class ProgressWindowTests(unittest.TestCase):
    def test_analysis_runs_off_the_calling_thread_and_parent_is_restored(self):
        progress_window = FakeProgressWindow()
        parent_window = FakeParentWindow()
        caller_thread = threading.get_ident()
        worker_threads = []

        def run_analysis():
            worker_threads.append(threading.get_ident())
            return False, "expected failure"

        with (
            patch.object(ui_common.eg, "Window", return_value=progress_window, create=True),
            patch.object(ui_common.eg, "Multiline", return_value=object(), create=True),
            patch.object(ui_common.eg, "Button", return_value=object(), create=True),
        ):
            result = ui_common.run_with_progress(
                "Analysis is running...",
                run_analysis,
                parent_window=parent_window,
            )

        self.assertEqual(result, (False, "expected failure"))
        self.assertNotEqual(worker_threads, [caller_thread])
        self.assertTrue(progress_window.closed)
        self.assertFalse(parent_window.hidden)
        self.assertTrue(parent_window.refreshed)


if __name__ == "__main__":
    unittest.main()
