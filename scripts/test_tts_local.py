#!/usr/bin/env python3
"""
Local TTS Testing Tool

Generate audio from transcript files locally to test TTS pause issues
without running the full CI workflow.

Usage:
    # Generate audio from a transcript file
    python3 scripts/test_tts_local.py docs/en_GB/news_digest_ai_2026_01_22.txt
    
    # Generate with text normalization applied
    python3 scripts/test_tts_local.py docs/en_GB/news_digest_ai_2026_01_22.txt --normalize
    
    # Compare original vs normalized
    python3 scripts/test_tts_local.py docs/en_GB/news_digest_ai_2026_01_22.txt --compare
    
    # Specify output directory
    python3 scripts/test_tts_local.py docs/en_GB/news_digest_ai_2026_01_22.txt --output-dir /tmp/tts_test
"""

import asyncio
import edge_tts
import os
import sys
import re
import argparse
from pathlib import Path
from typing import Optional
import json

# Load voice configuration
def load_config_file(filename: str) -> dict:
    """Load configuration from JSON file"""
    config_path = Path(__file__).parent.parent / 'config' / filename
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {config_path}: {e}")
        raise

VOICE_CONFIG = load_config_file('voice_config.json')

# Language to voice mapping
LANGUAGE_VOICES = {
    'en_GB': 'en-IE-EmilyNeural',
    'en_GB_LON': 'en-GB-SoniaNeural',
    'en_GB_LIV': 'en-GB-RyanNeural',
    'pl_PL': 'pl-PL-ZofiaNeural',
    'bella': 'en-IE-EmilyNeural',
    'fr_FR': 'fr-FR-DeniseNeural',
    'de_DE': 'de-DE-KatjaNeural',
    'es_ES': 'es-ES-ElviraNeural',
    'it_IT': 'it-IT-ElsaNeural',
    'nl_NL': 'nl-NL-ColetteNeural',
}


def extract_transcript_text(filepath: Path) -> str:
    """Extract transcript text from file, skipping header"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip header lines
    lines = content.split('\n')
    transcript_start = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('GITHUB') and not line.startswith('=') and not line.startswith('Generated') and not line.startswith('AI') and not line.startswith('Type'):
            transcript_start = i
            break
    
    transcript_text = '\n'.join(lines[transcript_start:]).strip()
    return transcript_text


def detect_language(filepath: Path) -> str:
    """Detect language from file path"""
    path_str = str(filepath)
    for lang in LANGUAGE_VOICES.keys():
        if f'/{lang}/' in path_str or f'\\{lang}\\' in path_str:
            return lang
    # Default to en_GB
    return 'en_GB'


def normalize_text_for_tts(text: str, language: str = 'en_GB') -> str:
    """
    Apply text normalization to reduce TTS pauses.
    This mimics the normalization done in github_ai_news_digest.py
    """
    normalized = text
    
    # Replace newlines with spaces
    normalized = re.sub(r'\r\n|\r|\n', ' ', normalized)
    
    # Normalize multiple spaces
    normalized = re.sub(r' +', ' ', normalized)
    
    # Replace em dashes with commas
    normalized = re.sub(r'—', ', ', normalized)
    normalized = re.sub(r'–', ', ', normalized)
    
    # Fix section transitions based on language
    if language == 'bella':
        normalized = re.sub(r'\.\s+(Turning to|On the|Meanwhile|For banking|For those|From a|Looking at|Here\'?s|Heres)', 
                          r'; \1', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\.\s+(The|This|These|When|Understanding|From a banking|For your)', 
                          r', \1', normalized, flags=re.IGNORECASE)
    elif language == 'en_GB':
        normalized = re.sub(r'\.\s+In (politics|economy|health|international|climate|technology|crime) news', 
                          r'; in \1 news', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\.\s+(Meanwhile|Additionally|Furthermore|However)', 
                          r'; \1', normalized, flags=re.IGNORECASE)
    elif language == 'pl_PL':
        normalized = re.sub(r'\.\s+W wiadomościach (polityka|ekonomia|zdrowie|międzynarodowe|klimat|technologia|przestępczość) dzisiaj', 
                          r'; w wiadomościach \1 dzisiaj', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\.\s+(Tymczasem|Dodatkowo|Ponadto|Jednakże)', 
                          r'; \1', normalized, flags=re.IGNORECASE)
    
    # Remove quote marks
    normalized = re.sub(r'["\']', '', normalized)
    
    # Fix period before "Heres" or "Here's"
    normalized = re.sub(r'\.\s+(Heres|Here\'?s)', r'; \1', normalized, flags=re.IGNORECASE)
    
    # Sentence-internal non-breaking spaces: prevent mid-sentence pauses (same as github_ai_news_digest.py)
    # Only . ! ? create breaks; no phrase list to maintain
    _sentence_delim = re.compile(r'([.!?]+\s+)')
    _parts = _sentence_delim.split(normalized)
    for _i, _part in enumerate(_parts):
        if not re.match(r'^[.!?]+\s*$', _part.strip() or ' '):
            _parts[_i] = _part.replace(' ', '\u00A0')
    normalized = ''.join(_parts)
    # Additional fixes for common pause issues
    # Break up very long sentences at natural points (semicolons already present)
    # This is a simplified version - full version would be more sophisticated
    
    return normalized.strip()


def compress_short_silences(mp3_path: Path, min_ms: int = 400, max_ms: int = 1100, target_ms: int = 90) -> None:
    """Shorten only wrong mid-sentence pauses (400-1100ms); leaves brief and long sentence gaps alone."""
    try:
        from pydub import AudioSegment
        from pydub.silence import detect_silence
    except ImportError:
        print("   ⚠️ pydub required for --compress-silences")
        return
    audio = AudioSegment.from_mp3(str(mp3_path))
    thresh = (audio.dBFS - 35) if audio.dBFS else -35
    silences = detect_silence(audio, min_silence_len=60, silence_thresh=thresh, seek_step=10)
    out = AudioSegment.empty()
    last_end = 0
    for start_ms, end_ms in silences:
        duration = end_ms - start_ms
        out += audio[last_end:start_ms]
        if min_ms <= duration <= max_ms:
            out += AudioSegment.silent(duration=target_ms)
        else:
            out += audio[start_ms:end_ms]
        last_end = end_ms
    out += audio[last_end:]
    out.export(str(mp3_path), format="mp3", bitrate="192k")


async def generate_audio(text: str, voice_name: str, output_path: Path, rate: str = "+0%"):
    """Generate audio using Edge TTS"""
    print(f"   🎤 Generating audio with voice: {voice_name}")
    print(f"   ⚙️  Speech rate: {rate}")
    
    # Edge TTS requires "+0%" not "0%" for no speed adjustment
    if rate == "0%":
        rate = "+0%"
    
    try:
        communicate = edge_tts.Communicate(text, voice_name, rate=rate)
        
        with open(output_path, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
        
        # Get file size
        file_size = output_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"   ✅ Audio generated: {output_path}")
        print(f"   📊 File size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Error generating audio: {error_msg}")
        
        # Check if it's a network/connectivity issue
        if "No audio was received" in error_msg or "network" in error_msg.lower():
            print(f"   💡 This might be a network connectivity issue.")
            print(f"   💡 Try:")
            print(f"      - Check your internet connection")
            print(f"      - Verify Edge TTS service is accessible")
            print(f"      - Try again in a few moments")
        
        # Check if text might be too long
        if len(text) > 5000:
            print(f"   💡 Text is quite long ({len(text)} chars). Edge TTS may have limits.")
            print(f"   💡 Consider splitting the text into smaller chunks.")
        
        raise


def compare_texts(original: str, normalized: str) -> dict:
    """Compare original and normalized text"""
    changes = []
    
    # Find differences
    orig_words = original.split()
    norm_words = normalized.split()
    
    # Simple diff (this could be more sophisticated)
    if original != normalized:
        # Find changed sections
        orig_sentences = re.split(r'([.;,])', original)
        norm_sentences = re.split(r'([.;,])', normalized)
        
        # Count punctuation changes
        orig_punct = len(re.findall(r'[.;,]', original))
        norm_punct = len(re.findall(r'[.;,]', normalized))
        
        changes.append({
            'type': 'punctuation_count',
            'original': orig_punct,
            'normalized': norm_punct,
            'difference': norm_punct - orig_punct
        })
    
    return {
        'original_length': len(original),
        'normalized_length': len(normalized),
        'original_words': len(original.split()),
        'normalized_words': len(normalized.split()),
        'changes': changes
    }


async def main():
    parser = argparse.ArgumentParser(
        description='Local TTS testing tool for transcript files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  Generate audio from transcript:
    python3 scripts/test_tts_local.py docs/en_GB/news_digest_ai_2026_01_22.txt
  
  Generate with normalization:
    python3 scripts/test_tts_local.py docs/en_GB/news_digest_ai_2026_01_22.txt --normalize
  
  Compare original vs normalized:
    python3 scripts/test_tts_local.py docs/en_GB/news_digest_ai_2026_01_22.txt --compare
  
  Custom output directory:
    python3 scripts/test_tts_local.py docs/en_GB/news_digest_ai_2026_01_22.txt --output-dir /tmp/tts_test
        '''
    )
    
    parser.add_argument('transcript_file', type=str, help='Path to transcript file')
    parser.add_argument('--normalize', action='store_true', 
                       help='Apply text normalization before generating audio')
    parser.add_argument('--compare', action='store_true',
                       help='Generate both original and normalized audio for comparison')
    parser.add_argument('--output-dir', type=str, default='test_audio',
                       help='Output directory for generated audio files (default: test_audio)')
    parser.add_argument('--rate', type=str, default=None,
                       help='Speech rate override (e.g., +10%%, -5%%). Defaults to config value.')
    parser.add_argument('--voice', type=str, default=None,
                       help='Voice override (e.g., en-IE-EmilyNeural). Defaults to language-based selection.')
    parser.add_argument('--compress-silences', action='store_true',
                       help='Shorten wrong mid-sentence pauses only (400-1100ms → 90ms) after generating audio.')
    
    args = parser.parse_args()
    
    # Validate input file
    transcript_path = Path(args.transcript_file)
    if not transcript_path.exists():
        print(f"❌ Error: Transcript file not found: {transcript_path}")
        sys.exit(1)
    
    # Detect language
    language = detect_language(transcript_path)
    print(f"📝 Detected language: {language}")
    
    # Get voice
    if args.voice:
        voice_name = args.voice
    else:
        voice_name = LANGUAGE_VOICES.get(language, 'en-IE-EmilyNeural')
    print(f"🎙️  Using voice: {voice_name}")
    
    # Get rate from config or override
    if args.rate:
        rate = args.rate
    else:
        rate = VOICE_CONFIG['tts_settings']['edge_tts'].get('rate', '+0%')
    
    # Extract transcript text
    print(f"\n📄 Reading transcript: {transcript_path}")
    original_text = extract_transcript_text(transcript_path)
    print(f"   📊 Text length: {len(original_text)} characters, {len(original_text.split())} words")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {output_dir.absolute()}")
    
    # Generate audio
    if args.compare:
        # Generate both versions
        print("\n" + "="*80)
        print("🔄 COMPARISON MODE: Generating both original and normalized audio")
        print("="*80)
        
        # Original
        print("\n1️⃣ Generating ORIGINAL audio (no normalization)...")
        original_output = output_dir / f"{transcript_path.stem}_original.mp3"
        await generate_audio(original_text, voice_name, original_output, rate)
        if args.compress_silences:
            compress_short_silences(original_output)
            print(f"   ✅ Compressed short silences: {original_output.name}")
        
        # Normalized
        print("\n2️⃣ Generating NORMALIZED audio (with fixes)...")
        normalized_text = normalize_text_for_tts(original_text, language)
        normalized_output = output_dir / f"{transcript_path.stem}_normalized.mp3"
        await generate_audio(normalized_text, voice_name, normalized_output, rate)
        if args.compress_silences:
            compress_short_silences(normalized_output)
            print(f"   ✅ Compressed short silences: {normalized_output.name}")
        
        # Compare
        print("\n" + "="*80)
        print("📊 COMPARISON SUMMARY")
        print("="*80)
        comparison = compare_texts(original_text, normalized_text)
        print(f"Original length: {comparison['original_length']} chars, {comparison['original_words']} words")
        print(f"Normalized length: {comparison['normalized_length']} chars, {comparison['normalized_words']} words")
        
        if comparison['changes']:
            for change in comparison['changes']:
                if change['type'] == 'punctuation_count':
                    print(f"Punctuation count: {change['original']} → {change['normalized']} ({change['difference']:+d})")
        
        print(f"\n✅ Audio files generated:")
        print(f"   Original:  {original_output.absolute()}")
        print(f"   Normalized: {normalized_output.absolute()}")
        print(f"\n💡 Listen to both files to compare pause patterns!")
        
    elif args.normalize:
        # Generate normalized only
        print("\n🔧 Applying text normalization...")
        normalized_text = normalize_text_for_tts(original_text, language)
        print(f"   📊 Normalized length: {len(normalized_text)} characters, {len(normalized_text.split())} words")
        
        output_path = output_dir / f"{transcript_path.stem}_normalized.mp3"
        await generate_audio(normalized_text, voice_name, output_path, rate)
        if args.compress_silences:
            compress_short_silences(output_path)
            print(f"   ✅ Compressed short silences")
        print(f"\n✅ Audio file generated: {output_path.absolute()}")
        
    else:
        # Generate original only
        output_path = output_dir / f"{transcript_path.stem}_original.mp3"
        await generate_audio(original_text, voice_name, output_path, rate)
        if args.compress_silences:
            compress_short_silences(output_path)
            print(f"   ✅ Compressed short silences")
        print(f"\n✅ Audio file generated: {output_path.absolute()}")
        print(f"\n💡 Tip: Use --compare to generate both original and normalized versions!")


if __name__ == '__main__':
    asyncio.run(main())
