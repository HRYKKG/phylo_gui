import importlib
import sys
import types
import unittest


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


if __name__ == "__main__":
    unittest.main()
