import sys
import types
import unittest
from unittest.mock import patch

from ui_pipeline import run_pipeline_windows


class PipelineNavigationTests(unittest.TestCase):
    def test_stage_changes_are_driven_by_one_loop(self):
        calls = []
        modules = {
            "ui_alignment": types.SimpleNamespace(
                open_alignment_options_window=lambda context: calls.append("alignment") or "trim"
            ),
            "ui_trim": types.SimpleNamespace(
                open_trim_options_window=lambda context: calls.append("trim") or "iqtree"
            ),
            "ui_iqtree": types.SimpleNamespace(
                open_iqtree_options_window=lambda context: calls.append("iqtree") or None
            ),
        }

        with patch.dict(sys.modules, modules):
            run_pipeline_windows(object())

        self.assertEqual(calls, ["alignment", "trim", "iqtree"])

    def test_unknown_stage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown pipeline stage"):
            run_pipeline_windows(object(), "unknown")


if __name__ == "__main__":
    unittest.main()
