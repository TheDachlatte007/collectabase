import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PILLOW_AVAILABLE = importlib.util.find_spec("PIL") is not None


@unittest.skipUnless(PILLOW_AVAILABLE, "Install scripts/requirements.txt to run asset optimizer tests")
class ConsoleAssetOptimizerTests(unittest.TestCase):
    def test_check_and_conversion_preserve_source_and_create_webp(self):
        root = Path(__file__).resolve().parents[2]
        script = root / "scripts" / "optimize_console_fallbacks.py"
        from PIL import Image

        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source"
            output = Path(temp_dir) / "output"
            source.mkdir()
            original = source / "console.png"
            Image.new("RGBA", (2, 1), (20, 40, 60, 128)).save(original)
            source_bytes = original.read_bytes()

            check = subprocess.run(
                [sys.executable, str(script), "--source", str(source), "--output", str(output), "--check"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertFalse(output.exists())
            self.assertIn("1 image", check.stdout)

            conversion = subprocess.run(
                [sys.executable, str(script), "--source", str(source), "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(conversion.returncode, 0, conversion.stderr)
            self.assertEqual(original.read_bytes(), source_bytes)
            self.assertTrue((output / "console.webp").is_file())

