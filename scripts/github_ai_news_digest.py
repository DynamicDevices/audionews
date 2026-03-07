#!/usr/bin/env python3
"""
GitHub AI-Enhanced Ethical News Digest Generator (orchestrator).
Uses the digest package: fetch -> AI analysis -> synthesis -> TTS -> output.
"""

import asyncio
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

# Ensure project root is on path for "digest" package
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from digest.config_loader import (
    AI_PROMPTS_CONFIG,
    VOICE_CONFIG,
    LANGUAGE_CONFIGS,
)
from digest.models import NewsStory
from digest import fetch as fetch_module
from digest import ai_analysis
from digest import digest_synthesis
from digest import tts as tts_module

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None
    print("❌ ERROR: Anthropic library not installed. Run: pip install anthropic")


class GitHubAINewsDigest:
    """Orchestrates fetch -> AI analysis -> digest synthesis -> TTS -> file output."""

    def __init__(
        self,
        language: str = "en_GB",
        tts_provider_override: Optional[str] = None,
        use_existing_transcript: bool = False,
        force_regenerate: bool = False,
    ):
        self.language = language
        self.config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS["en_GB"])
        self.sources = self.config["sources"]
        self.use_existing_transcript = use_existing_transcript
        self.force_regenerate = force_regenerate
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.voice_name = self.config["voice"]
        voice_cfg = VOICE_CONFIG.get("voices", {}).get(language, {})
        self.tts_provider = (tts_provider_override or voice_cfg.get("tts_provider") or "edge_tts").lower()
        if self.tts_provider not in ("edge_tts", "pocket_tts", "elevenlabs"):
            self.tts_provider = "edge_tts"
        self.pocket_voice = voice_cfg.get("pocket_voice") or VOICE_CONFIG.get("tts_settings", {}).get("pocket_tts", {}).get("voice") or "alba"
        self.elevenlabs_voice_id = (
            voice_cfg.get("elevenlabs_voice_id")
            or VOICE_CONFIG.get("tts_settings", {}).get("elevenlabs", {}).get("voice_id")
            or "EXAVITQu4vr4xnSDxMaL"
        )
        if use_existing_transcript:
            self.ai_enabled = False
            self.anthropic_client = None
        else:
            self._setup_ai()

    def _setup_ai(self) -> None:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        print("🔍 Debug - Checking AI setup:")
        print(f"   - ANTHROPIC_AVAILABLE (library): {ANTHROPIC_AVAILABLE}")
        print(f"   - ANTHROPIC_API_KEY (env): {'✅ Present (length: ' + str(len(anthropic_key)) + ')' if anthropic_key else '❌ Missing'}")
        print(f"   - Language: {self.language}")
        if anthropic_key and ANTHROPIC_AVAILABLE:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
            self.ai_enabled = True
            print("🤖 AI Analysis: ANTHROPIC ENABLED")
        else:
            msg = "🚨 CRITICAL: AI Analysis is REQUIRED. ANTHROPIC_API_KEY not set or library missing."
            print(msg)
            raise RuntimeError("AI Analysis requires valid ANTHROPIC_API_KEY. Cannot continue without it.")

    async def generate_daily_ai_digest(self) -> Optional[dict]:
        """Main entry: generate or reuse today's digest and audio."""
        print("🤖 GITHUB AI-ENHANCED NEWS DIGEST")
        print("🎯 Intelligent analysis for visually impaired users")
        print("=" * 60)
        today_str = date.today().strftime("%Y_%m_%d")
        base = os.environ.get("AUDIONEWS_OUTPUT_BASE", "").strip()
        if base:
            output_dir = os.path.join(base, self.config["output_dir"])
            audio_dir = os.path.join(base, self.config["audio_dir"])
        else:
            output_dir = self.config["output_dir"]
            audio_dir = self.config["audio_dir"]
        text_filename = os.path.join(output_dir, f"news_digest_ai_{today_str}.txt")
        audio_filename = os.path.join(audio_dir, f"news_digest_ai_{today_str}.mp3")

        if self.use_existing_transcript:
            if not os.path.exists(text_filename):
                raise FileNotFoundError(
                    f"Transcript not found: {text_filename}. "
                    "Generate a full digest first (with ANTHROPIC_API_KEY) or use an existing transcript file."
                )
            print(f"\n📄 Using existing transcript (no API): {text_filename}")
            digest_text = tts_module.parse_existing_transcript(text_filename)
            if self.tts_provider in ("pocket_tts", "elevenlabs"):
                digest_text = tts_module.reverse_edge_tts_edits(digest_text)
                print(f"   📝 Using unedited text for {self.tts_provider} (Edge TTS edits reversed)")
            os.makedirs(os.path.dirname(audio_filename), exist_ok=True)
            audio_stats = await tts_module.generate_audio_digest(
                digest_text,
                audio_filename,
                tts_provider=self.tts_provider,
                voice_name=self.voice_name,
                language=self.language,
                voice_config=VOICE_CONFIG,
                elevenlabs_voice_id=self.elevenlabs_voice_id,
                pocket_voice=self.pocket_voice,
            )
            print(f"\n🤖 AUDIO FROM EXISTING TRANSCRIPT")
            print("=" * 35)
            print(f"📅 Date: {date.today().strftime('%B %d, %Y')}")
            print(f"🎧 Audio: {audio_filename}")
            print(f"📄 Text: {text_filename}")
            print(f"⏱️ Duration: {audio_stats['duration']:.1f}s | 🎤 WPS: {audio_stats['wps']:.2f}")
            return {
                "audio_file": audio_filename,
                "text_file": text_filename,
                "stats": audio_stats,
                "ai_enabled": False,
                "regenerated": True,
            }

        if not self.force_regenerate:
            audio_size = os.path.getsize(audio_filename) if os.path.exists(audio_filename) else 0
            if os.path.exists(text_filename) and os.path.exists(audio_filename) and audio_size > 50000:
                print("\n💰 COST OPTIMIZATION: Today's content already exists")
                print(f"   ✅ Text: {text_filename}")
                print(f"   ✅ Audio: {audio_filename} ({audio_size:,} bytes)")
                print("   🚀 Skipping regeneration for efficiency")
                size_kb = os.path.getsize(audio_filename) / 1024
                print(f"\n🤖 EXISTING DIGEST SUMMARY")
                print("=" * 35)
                print(f"📅 Date: {date.today().strftime('%B %d, %Y')}")
                print(f"🎧 Audio: {audio_filename}")
                print(f"📄 Text: {text_filename}")
                print(f"💾 Size: {size_kb:.1f} KB")
                return {
                    "audio_file": audio_filename,
                    "text_file": text_filename,
                    "ai_enabled": self.ai_enabled,
                    "regenerated": False,
                    "size_kb": size_kb,
                }

        all_stories = []
        for source_name, url in self.sources.items():
            stories = fetch_module.fetch_headlines_from_source(
                self.language, source_name, url, self.headers
            )
            all_stories.extend(stories)
            time.sleep(1)
        if not all_stories:
            print("❌ No stories found")
            return None
        print(f"\n📊 Total stories collected: {len(all_stories)}")

        themes = await ai_analysis.ai_analyze_stories(
            self.anthropic_client,
            self.language,
            all_stories,
            AI_PROMPTS_CONFIG,
        )
        digest_text = await digest_synthesis.create_ai_enhanced_digest(
            self.anthropic_client,
            self.language,
            self.config,
            themes,
            AI_PROMPTS_CONFIG,
        )

        os.makedirs(os.path.dirname(text_filename), exist_ok=True)
        with open(text_filename, "w", encoding="utf-8") as f:
            f.write("GITHUB AI-ENHANCED NEWS DIGEST\n")
            f.write("=" * 40 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"AI Analysis: {'ENABLED' if self.ai_enabled else 'DISABLED'}\n")
            f.write("Type: AI-synthesized content for accessibility\n")
            f.write("=" * 40 + "\n\n")
            f.write(digest_text)
        print(f"\n📄 AI digest text saved: {text_filename}")

        audio_stats = await tts_module.generate_audio_digest(
            digest_text,
            audio_filename,
            tts_provider=self.tts_provider,
            voice_name=self.voice_name,
            language=self.language,
            voice_config=VOICE_CONFIG,
            elevenlabs_voice_id=self.elevenlabs_voice_id,
            pocket_voice=self.pocket_voice,
        )

        print(f"\n🤖 AI-ENHANCED DIGEST COMPLETE")
        print("=" * 35)
        print(f"📅 Date: {date.today().strftime('%B %d, %Y')}")
        print(f"🤖 AI Analysis: {'ENABLED' if self.ai_enabled else 'FALLBACK MODE'}")
        print(f"📰 Stories: {len(all_stories)} from {len(self.sources)} sources")
        print(f"⏱️ Duration: {audio_stats['duration']:.1f}s")
        print(f"🎤 Speed: {audio_stats['wps']:.2f} WPS")
        print(f"🎧 Audio: {audio_filename}")
        print(f"📄 Text: {text_filename}")
        return {
            "audio_file": audio_filename,
            "text_file": text_filename,
            "stats": audio_stats,
            "ai_enabled": self.ai_enabled,
            "stories_analyzed": len(all_stories),
            "regenerated": True,
        }


async def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Generate multi-language AI news digest")
    parser.add_argument(
        "--language", "-l",
        choices=["en_GB", "fr_FR", "de_DE", "es_ES", "it_IT", "nl_NL", "pl_PL", "bella", "en_GB_LON", "en_GB_LIV"],
        default="en_GB",
        help="Language for news digest (default: en_GB)",
    )
    parser.add_argument(
        "--tts-provider",
        choices=["edge_tts", "pocket_tts", "elevenlabs"],
        default=None,
        help="TTS provider override (default: use per-language config)",
    )
    parser.add_argument(
        "--use-existing-transcript",
        action="store_true",
        help="Use today's existing transcript only; skip fetch and Anthropic API",
    )
    parser.add_argument(
        "--force-regenerate",
        action="store_true",
        help="Regenerate even if today's content already exists",
    )
    args = parser.parse_args()

    print(f"🌍 Language: {LANGUAGE_CONFIGS[args.language]['native_name']}")
    print(f"🎤 Voice: {LANGUAGE_CONFIGS[args.language]['voice']}")
    print(f"📁 Output: {LANGUAGE_CONFIGS[args.language]['output_dir']}")
    if args.use_existing_transcript:
        print("📄 Mode: use existing transcript (no API)")

    digest_generator = GitHubAINewsDigest(
        language=args.language,
        tts_provider_override=args.tts_provider,
        use_existing_transcript=args.use_existing_transcript,
        force_regenerate=args.force_regenerate,
    )
    print(f"🔊 TTS provider: {digest_generator.tts_provider}")
    if digest_generator.force_regenerate:
        print("🔄 Force regenerate: ON (will regenerate even if today's content exists)")

    result = await digest_generator.generate_daily_ai_digest()
    if result:
        print("\n🎉 SUCCESS: AI-enhanced digest ready!")
        print(f"   🤖 AI Analysis: {'ENABLED' if result['ai_enabled'] else 'FALLBACK'}")
        print(f"   🎧 Audio: {result['audio_file']}")
        print(f"   📄 Text: {result['text_file']}")
    else:
        print("\n⚠️ WARNING: No result returned from digest generation")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
