import json
import tempfile
import unittest
from pathlib import Path

from interactive_tree_viewer import _write_json_atomic


class ViewerIoTests(unittest.TestCase):
    def test_atomic_json_write_replaces_existing_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "selection.json"
            output_path.write_text('{"old": true}', encoding="utf-8")

            _write_json_atomic(output_path, {"selected_leaf_names": ["A", "B"]})

            self.assertEqual(
                json.loads(output_path.read_text(encoding="utf-8")),
                {"selected_leaf_names": ["A", "B"]},
            )
            self.assertEqual(list(output_path.parent.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
