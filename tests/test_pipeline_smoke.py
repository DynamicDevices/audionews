"""
Smoke test: run pipeline with --use-existing-transcript and edge_tts.
Uses AUDIONEWS_OUTPUT_BASE to write to a temp dir. Requires edge-tts (network).
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "github_ai_news_digest.py"

# Transcript header expected by parse_existing_transcript; body after second separator
TRANSCRIPT_HEADER = """GITHUB AI-ENHANCED NEWS DIGEST
========================================
Generated: 2026-01-01 12:00:00
AI Analysis: DISABLED
Type: AI-synthesized content for accessibility
========================================

"""
MINIMAL_BODY = "Good morning. This is a short test for the audio pipeline.\n"


class TestPipelineSmoke(unittest.TestCase):
    """Run digest with fixture transcript and Edge TTS."""

    def test_use_existing_transcript_produces_audio(self):
        with tempfile.TemporaryDirectory(prefix="audionews_test_") as tmp:
            base = Path(tmp)
            out_dir = base / "docs" / "en_GB"
            audio_dir = base / "docs" / "en_GB" / "audio"
            out_dir.mkdir(parents=True)
            audio_dir.mkdir(parents=True)
            today = __import__("datetime").date.today().strftime("%Y_%m_%d")
            transcript_path = out_dir / f"news_digest_ai_{today}.txt"
            transcript_path.write_text(TRANSCRIPT_HEADER + MINIMAL_BODY, encoding="utf-8")
            env = {**os.environ, "AUDIONEWS_OUTPUT_BASE": str(base)}
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--language", "en_GB", "--use-existing-transcript", "--tts-provider", "edge_tts"],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}\nstdout: {result.stdout}")
            audio_path = audio_dir / f"news_digest_ai_{today}.mp3"
            self.assertTrue(audio_path.exists(), msg=f"Expected {audio_path} to exist")
            self.assertGreater(audio_path.stat().st_size, 1000, msg="MP3 should be non-trivial")


if __name__ == "__main__":
    unittest.main()
