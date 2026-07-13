import base64
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from export_preview import export_with_powerpoint


class PowerPointExportTests(unittest.TestCase):
    def test_stages_unicode_source_path_before_invoking_powerpoint_com(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "材料.pptx"
            source.write_bytes(b"test")
            output = root / "preview"
            output.mkdir()
            commands = []

            def fake_run(command, **_kwargs):
                commands.append(command)
                power_shell = base64.b64decode(command[-1]).decode("utf-16-le")
                match = re.search(r"Export\('([^']+)'", power_shell)
                self.assertIsNotNone(match)
                Path(match.group(1)).joinpath("Slide1.PNG").write_bytes(b"png")

            with patch("export_preview.subprocess.run", side_effect=fake_run):
                export_with_powerpoint(source, output, 1600, 900)

            command_text = base64.b64decode(commands[0][-1]).decode("utf-16-le")
            self.assertIn("deck.pptx", command_text)
            self.assertNotIn("材料", command_text)
            self.assertTrue((output / "Slide1.PNG").is_file())


if __name__ == "__main__":
    unittest.main()
