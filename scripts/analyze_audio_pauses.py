#!/usr/bin/env python3
"""
Audio Pause Analysis – detect pauses in TTS audio and align with transcript.

Loads an MP3, finds silence segments, and maps them to the transcript so you can
see where odd pauses occur in the text. Outputs a text report (and optional JSON).

Usage:
    python scripts/analyze_audio_pauses.py <audio_file> [transcript_file]
    python scripts/analyze_audio_pauses.py docs/en_GB/audio/news_digest_ai_2026_01_26.mp3
    python scripts/analyze_audio_pauses.py docs/en_GB/audio/news_digest_ai_2026_01_26.mp3 docs/en_GB/news_digest_ai_2026_01_26.txt

Output:
    Prints a report to stdout. Use --json to write results to <basename>.pause_report.json
    Use --report to write a text report to <basename>.pause_report.txt
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

try:
    from pydub import AudioSegment
    from pydub.silence import detect_silence
except ImportError:
    print("Error: pydub is required. Install with: pip install pydub")
    sys.exit(1)


# Minimum pause duration to report (ms). Shorter gaps are normal speech.
MIN_PAUSE_MS = 400
# Silence threshold (dBFS). Audio below this is considered silence.
SILENCE_THRESH_DB = -40
# Minimum length of silence to count as one segment (ms).
MIN_SILENCE_LEN_MS = 200
# Context: characters of transcript to show before/after estimated position.
CONTEXT_CHARS = 60


def load_transcript(path: Path) -> str:
    """Load transcript and return body text (strip header)."""
    text = path.read_text(encoding="utf-8")
    # Strip header (GITHUB ... ========== ...); take content after last separator block
    for sep in ("========================================", "============"):
        if sep in text:
            parts = text.split(sep, 1)
            if len(parts) > 1:
                text = parts[-1].strip()
    # Remove any remaining = or header-like lines
    lines = text.strip().split("\n")
    start = 0
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if line_stripped.startswith("Generated:") or line_stripped.startswith("AI Analysis:") or line_stripped.startswith("Type:") or line_stripped.startswith("GITHUB"):
            continue
        if set(line_stripped.strip()) <= set("= \t"):
            continue
        start = i
        break
    body = " ".join(lines[start:]).replace("\n", " ").strip()
    return re.sub(r"\s+", " ", body)


def detect_pauses(audio_path: Path, min_pause_ms: int = MIN_PAUSE_MS) -> List[Tuple[int, int]]:
    """Return list of (start_ms, end_ms) for each silence segment."""
    audio = AudioSegment.from_mp3(str(audio_path))
    # Use dBFS relative to segment so different volumes still work
    thresh = audio.dBFS + SILENCE_THRESH_DB if audio.dBFS else SILENCE_THRESH_DB
    silence_ranges = detect_silence(
        audio,
        min_silence_len=MIN_SILENCE_LEN_MS,
        silence_thresh=thresh,
        seek_step=10,
    )
    # Merge very close silences and keep only long enough pauses
    merged: List[Tuple[int, int]] = []
    for start_ms, end_ms in silence_ranges:
        duration_ms = end_ms - start_ms
        if duration_ms < min_pause_ms:
            continue
        if merged and (start_ms - merged[-1][1]) < 300:
            merged[-1] = (merged[-1][0], end_ms)
        else:
            merged.append((start_ms, end_ms))
    return merged


def ms_to_mmss(ms: int) -> str:
    """Format milliseconds as M:SS."""
    s = ms // 1000
    m = s // 60
    s = s % 60
    return f"{m}:{s:02d}"


def transcript_snippet(transcript: str, position_ratio: float, context_chars: int = CONTEXT_CHARS) -> str:
    """Return a snippet of transcript around position_ratio (0.0–1.0)."""
    if not transcript:
        return "(no transcript)"
    pos = int(position_ratio * len(transcript))
    start = max(0, pos - context_chars)
    end = min(len(transcript), pos + context_chars)
    snippet = transcript[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(transcript):
        snippet = snippet + "…"
    return snippet


def snippet_with_marker(transcript: str, position_ratio: float, marker: str, context_chars: int = CONTEXT_CHARS) -> str:
    """Return a snippet with the pause position marked (e.g. '…text before ▶ PAUSE ◀ text after…')."""
    if not transcript:
        return "(no transcript)"
    pos = int(position_ratio * len(transcript))
    start = max(0, pos - context_chars)
    end = min(len(transcript), pos + context_chars)
    before = transcript[start:pos]
    after = transcript[pos:end]
    if start > 0:
        before = "…" + before
    if end < len(transcript):
        after = after + "…"
    return f"{before} {marker} {after}"


def run_analysis(
    audio_path: Path,
    transcript_path: Optional[Path] = None,
    min_pause_ms: int = MIN_PAUSE_MS,
) -> dict:
    """Run full analysis and return a dict suitable for report and JSON."""
    transcript = ""
    if transcript_path and transcript_path.exists():
        transcript = load_transcript(transcript_path)
    elif transcript_path is None:
        # Infer transcript path: .../audio/name.mp3 -> .../name.txt
        base = audio_path.stem
        parent = audio_path.parent.parent  # docs/en_GB
        inferred = parent / f"{base}.txt"
        if inferred.exists():
            transcript_path = inferred
            transcript = load_transcript(transcript_path)

    audio = AudioSegment.from_mp3(str(audio_path))
    duration_ms = len(audio)
    pauses = detect_pauses(audio_path, min_pause_ms=min_pause_ms)

    # Total speech time = audio duration minus all pause time (silence doesn't advance transcript)
    total_pause_ms = sum(end_ms - start_ms for start_ms, end_ms in pauses)
    total_speech_ms = max(1, duration_ms - total_pause_ms)

    def speech_time_before(until_ms: int) -> int:
        """Milliseconds of actual speech before until_ms (excludes pause segments)."""
        t = 0
        for start_ms, end_ms in pauses:
            if end_ms <= until_ms:
                t += end_ms - start_ms
            elif start_ms < until_ms:
                t += until_ms - start_ms
            else:
                break
        return until_ms - t

    entries = []
    for start_ms, end_ms in pauses:
        duration_ms_pause = end_ms - start_ms
        # Map position using speech time only, so pause locations align with transcript
        speech_before = speech_time_before(start_ms)
        ratio = speech_before / total_speech_ms if total_speech_ms else 0
        ratio = min(1.0, max(0.0, ratio))
        char_pos = int(ratio * len(transcript)) if transcript else 0
        snippet = transcript_snippet(transcript, ratio) if transcript else ""
        duration_sec = round(duration_ms_pause / 1000.0, 2)
        marked_snippet = snippet_with_marker(
            transcript, ratio, f"▶ PAUSE {duration_sec}s ◀", context_chars=CONTEXT_CHARS
        ) if transcript else ""
        entries.append({
            "start_ms": start_ms,
            "end_ms": end_ms,
            "duration_ms": duration_ms_pause,
            "start_time": ms_to_mmss(start_ms),
            "end_time": ms_to_mmss(end_ms),
            "duration_sec": duration_sec,
            "position_ratio": round(ratio, 3),
            "char_position": char_pos,
            "transcript_snippet": snippet,
            "transcript_snippet_marked": marked_snippet,
        })

    # Build annotated transcript: insert markers at each pause position (from end to start)
    annotated = transcript
    for p in sorted(entries, key=lambda x: x["char_position"], reverse=True):
        pos = p["char_position"]
        label = f" [PAUSE {p['duration_sec']}s @ {p['start_time']}] "
        annotated = annotated[:pos] + label + annotated[pos:]

    return {
        "audio_file": str(audio_path),
        "transcript_file": str(transcript_path) if transcript_path else None,
        "duration_ms": duration_ms,
        "duration_formatted": ms_to_mmss(duration_ms),
        "min_pause_ms": min_pause_ms,
        "total_pauses": len(pauses),
        "pauses": entries,
        "transcript_length_chars": len(transcript),
        "transcript_preview": transcript[:200] + "…" if len(transcript) > 200 else transcript,
        "annotated_transcript": annotated,
    }


def write_pause_document(data: dict, output_path: Path) -> None:
    """Write a Markdown document mapping pauses to transcript for debugging."""
    audio_name = Path(data["audio_file"]).name
    lines = [
        "# Pause analysis: where pauses fall in the transcript",
        "",
        "This document shows where each detected pause occurs in the audio and the corresponding place in the transcript, so you can see what text might be causing the pause.",
        "",
        "## Summary",
        "",
        f"- **Audio:** `{data['audio_file']}`",
        f"- **Transcript:** `{data['transcript_file'] or '(inferred)'}`",
        f"- **Duration:** {data['duration_formatted']}",
        f"- **Pauses detected:** {data['total_pauses']} (minimum {data['min_pause_ms']} ms)",
        "",
        "## Pauses in order (time and transcript context)",
        "",
        "Each pause is listed with its time in the audio and a snippet of the transcript **with the pause position marked** as `▶ PAUSE X.Xs ◀`.",
        "",
    ]
    for i, p in enumerate(data["pauses"], 1):
        lines.extend([
            f"### Pause {i}: {p['start_time']} – {p['end_time']} ({p['duration_sec']} s)",
            "",
            f"**Position in audio:** ~{p['position_ratio']*100:.1f}% through the track.",
            "",
            "**Transcript around this point:**",
            "",
            "> " + p["transcript_snippet_marked"].replace("\n", " "),
            "",
            "---",
            "",
        ])
    lines.extend([
        "## Annotated full transcript",
        "",
        "The full transcript with every pause marked inline. Each marker shows pause length and time, e.g. `[PAUSE 1.0s @ 0:27]`.",
        "",
        "<details>",
        "<summary>Click to expand</summary>",
        "",
        "```",
        data.get("annotated_transcript", "(no transcript)"),
        "```",
        "",
        "</details>",
        "",
        "---",
        "",
        "*Generated by `scripts/analyze_audio_pauses.py`.*",
    ])
    output_path.write_text("\n".join(lines), encoding="utf-8")


def print_report(data: dict) -> None:
    """Print human-readable report to stdout."""
    print("=" * 80)
    print("AUDIO PAUSE ANALYSIS REPORT")
    print("=" * 80)
    print(f"Audio:       {data['audio_file']}")
    print(f"Transcript:  {data['transcript_file'] or '(none)'}")
    print(f"Duration:    {data['duration_formatted']}")
    print(f"Pauses:      {data['total_pauses']} (min {data.get('min_pause_ms', MIN_PAUSE_MS)} ms)")
    print("=" * 80)
    if not data["pauses"]:
        print("\nNo significant pauses detected.")
        return
    print()
    for i, p in enumerate(data["pauses"], 1):
        print(f"--- Pause {i} ---")
        print(f"  Time:       {p['start_time']} – {p['end_time']}  ({p['duration_sec']} s)")
        print(f"  Position:   ~{p['position_ratio']*100:.1f}% through audio")
        print(f"  Transcript: {p['transcript_snippet']}")
        print()
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze TTS audio for pauses and align with transcript."
    )
    parser.add_argument(
        "audio_file",
        type=Path,
        help="Path to MP3 file (e.g. docs/en_GB/audio/news_digest_ai_2026_01_26.mp3)",
    )
    parser.add_argument(
        "transcript_file",
        type=Path,
        nargs="?",
        default=None,
        help="Path to transcript .txt (optional; inferred from audio path if not given)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write JSON report to <audio_basename>.pause_report.json",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Write text report to <audio_basename>.pause_report.txt",
    )
    parser.add_argument(
        "--doc",
        action="store_true",
        help="Write Markdown document to docs/.../PAUSE_ANALYSIS_<basename>.md showing pauses in transcript",
    )
    parser.add_argument(
        "--min-pause-ms",
        type=int,
        default=MIN_PAUSE_MS,
        help=f"Minimum pause length to report in ms (default: {MIN_PAUSE_MS})",
    )
    args = parser.parse_args()

    audio_path = args.audio_file
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    data = run_analysis(audio_path, args.transcript_file, min_pause_ms=args.min_pause_ms)
    print_report(data)

    base = audio_path.with_suffix("").name
    if args.json:
        out = audio_path.parent.parent / f"{base}.pause_report.json"
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nJSON report written to: {out}")
    if args.report:
        out = audio_path.parent.parent / f"{base}.pause_report.txt"
        buf = []
        buf.append("AUDIO PAUSE ANALYSIS REPORT")
        buf.append("=" * 80)
        buf.append(f"Audio: {data['audio_file']}")
        buf.append(f"Transcript: {data['transcript_file'] or '(none)'}")
        buf.append(f"Duration: {data['duration_formatted']} | Pauses: {data['total_pauses']}")
        buf.append("")
        for i, p in enumerate(data["pauses"], 1):
            buf.append(f"--- Pause {i} ---")
            buf.append(f"  Time: {p['start_time']} – {p['end_time']}  ({p['duration_sec']} s)")
            buf.append(f"  Transcript: {p['transcript_snippet']}")
            buf.append("")
        out.write_text("\n".join(buf), encoding="utf-8")
        print(f"Text report written to: {out}")
    if args.doc:
        out = audio_path.parent.parent / f"PAUSE_ANALYSIS_{base}.md"
        write_pause_document(data, out)
        print(f"Pause document written to: {out}")


if __name__ == "__main__":
    main()
