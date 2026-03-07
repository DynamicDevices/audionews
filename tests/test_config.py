"""
Tests for digest config loading. No network or TTS required.
"""
import sys
import unittest
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestConfigLoad(unittest.TestCase):
    """Config loader produces expected structure."""

    def test_ai_prompts_config_loaded(self):
        from digest.config_loader import AI_PROMPTS_CONFIG
        self.assertIn("system_messages", AI_PROMPTS_CONFIG)
        self.assertIn("analysis_prompt", AI_PROMPTS_CONFIG)
        self.assertIn("synthesis_prompts", AI_PROMPTS_CONFIG)
        self.assertIn("ai_model", AI_PROMPTS_CONFIG)
        self.assertIn("en_GB", AI_PROMPTS_CONFIG["system_messages"])
        self.assertIn("name", AI_PROMPTS_CONFIG["ai_model"])

    def test_voice_config_loaded(self):
        from digest.config_loader import VOICE_CONFIG
        self.assertIn("voices", VOICE_CONFIG)
        self.assertIn("tts_settings", VOICE_CONFIG)
        self.assertIn("en_GB", VOICE_CONFIG["voices"])
        self.assertIn("edge_tts", VOICE_CONFIG["tts_settings"])

    def test_language_configs_built(self):
        from digest.config_loader import LANGUAGE_CONFIGS
        for lang in ("en_GB", "pl_PL", "bella"):
            self.assertIn(lang, LANGUAGE_CONFIGS, msg=f"missing {lang}")
            cfg = LANGUAGE_CONFIGS[lang]
            self.assertIn("sources", cfg)
            self.assertIn("voice", cfg)
            self.assertIn("output_dir", cfg)
            self.assertIn("audio_dir", cfg)
            self.assertIn("themes", cfg)


if __name__ == "__main__":
    unittest.main()
