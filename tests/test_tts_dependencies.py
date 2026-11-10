"""Offline guards against using stale speech authentication from the CI image."""

import re
import unittest
from importlib.metadata import version
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TestTTSDependencies(unittest.TestCase):
    def test_edge_tts_has_current_authentication_fixes(self):
        installed = tuple(int(part) for part in version("edge-tts").split(".")[:3])
        self.assertGreaterEqual(installed, (7, 3, 1))

    def test_generation_refreshes_image_dependencies_before_tts(self):
        workflow = (ROOT / ".github/workflows/daily-news-digest.yml").read_text()
        generation = workflow.split("  generate-one-language:\n", 1)[1].split("\n  merge:", 1)[0]
        install = generation.index("python -m pip install --no-cache-dir -r requirements.txt")
        generate = generation.index("python scripts/github_ai_news_digest.py")
        self.assertLess(install, generate)

    def test_requirements_exclude_old_authentication_clients(self):
        requirements = (ROOT / "requirements.txt").read_text()
        match = re.search(r"^edge-tts>=([\d.]+),<8\.0\.0$", requirements, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(tuple(int(part) for part in match.group(1).split(".")), (7, 3, 1))


if __name__ == "__main__":
    unittest.main()
