"""
TTS: Edge TTS, Pocket TTS, ElevenLabs. Helpers for transcript parsing and silence compression.
"""

import asyncio
import os
import re
import tempfile
import threading
from typing import List, Optional

import edge_tts

# Optional: ElevenLabs uses aiohttp
try:
    import aiohttp
except ImportError:
    aiohttp = None

# Lazy imports for heavy deps
_pydub = None
_pocket_tts_cache = None
_pocket_tts_lock = None


def parse_existing_transcript(path: str) -> str:
    """Return digest body from a saved transcript file (after the header separator)."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    sep = "========================================\n\n"
    idx = content.find(sep)
    if idx == -1:
        return content.strip()
    idx2 = content.find(sep, idx + len(sep))
    if idx2 == -1:
        return content[idx + len(sep) :].strip()
    return content[idx2 + len(sep) :].strip()


def reverse_edge_tts_edits(text: str) -> str:
    """Undo Edge TTS edits (non-breaking spaces, spaced acronyms) for Pocket/ElevenLabs."""
    text = text.replace("\u00A0", " ")
    unabbrev = [
        (r"N\s+A\s+T\s+O\b", "NATO"),
        (r"N\s+H\s+S\b", "NHS"),
        (r"B\s+B\s+C\b", "BBC"),
        (r"E\s+U\b", "EU"),
        (r"U\s+K\b", "UK"),
        (r"U\s+S\b", "US"),
        (r"M\s+P\s+s\b", "MPs"),
        (r"M\s+P\b", "MP"),
        (r"C\s+E\s+O\b", "CEO"),
        (r"G\s+D\s+P\b", "GDP"),
    ]
    for pattern, replacement in unabbrev:
        text = re.sub(pattern, replacement, text)
    return text


def _compress_short_silences(
    mp3_path: str,
    min_ms: int = 400,
    max_ms: int = 1100,
    target_ms: int = 90,
) -> None:
    """Shorten mid-sentence pauses in 400–1100 ms range to target_ms."""
    global _pydub
    if _pydub is None:
        try:
            from pydub import AudioSegment
            from pydub.silence import detect_silence
        except ImportError:
            return
        _pydub = (AudioSegment, detect_silence)
    AudioSegment, detect_silence = _pydub
    audio = AudioSegment.from_mp3(mp3_path)
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
    out.export(mp3_path, format="mp3", bitrate="192k")


def _pocket_tts_chunk_text(text: str, max_chars: int = 120) -> List[str]:
    """Split text for Pocket TTS streaming limit."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_chars:
            chunks.append(text.strip())
            break
        break_at = max_chars
        for sep in (". ", "; ", ", ", " "):
            idx = text.rfind(sep, 0, max_chars + 1)
            if idx > 0:
                break_at = idx + len(sep)
                break
        chunks.append(text[:break_at].strip())
        text = text[break_at:].lstrip()
    return [c for c in chunks if c]


def _pocket_tts_generate_sync(
    digest_text: str,
    output_filename: str,
    voice_id: str,
    voice_config: dict,
) -> None:
    """Synchronous Pocket TTS generation (run in thread)."""
    global _pocket_tts_cache, _pocket_tts_lock
    try:
        from pocket_tts import TTSModel
        import scipy.io.wavfile
        from pydub import AudioSegment
    except ImportError as e:
        raise ImportError(
            "Pocket TTS dependencies not installed. Install with: pip install -r requirements-tts-pocket.txt"
        ) from e
    if _pocket_tts_lock is None:
        _pocket_tts_lock = threading.Lock()
        _pocket_tts_cache = {"model": None, "voices": {}}
    with _pocket_tts_lock:
        if _pocket_tts_cache["model"] is None:
            _pocket_tts_cache["model"] = TTSModel.load_model()
        model = _pocket_tts_cache["model"]
        if voice_id not in _pocket_tts_cache["voices"]:
            _pocket_tts_cache["voices"][voice_id] = model.get_state_for_audio_prompt(voice_id)
        voice_state = _pocket_tts_cache["voices"][voice_id]
    settings = voice_config.get("tts_settings", {}).get("pocket_tts", {})
    bitrate = settings.get("bitrate", "256k")
    crossfade_ms = settings.get("crossfade_ms", 50)
    normalize = settings.get("normalize", True)
    chunks = _pocket_tts_chunk_text(digest_text)
    if not chunks:
        raise ValueError("Digest text is empty after chunking")
    wav_paths = []
    try:
        for i, chunk in enumerate(chunks):
            audio_tensor = model.generate_audio(voice_state, chunk)
            fd, wav_path = tempfile.mkstemp(suffix=f"_pocket_{i}.wav")
            os.close(fd)
            scipy.io.wavfile.write(wav_path, model.sample_rate, audio_tensor.numpy())
            wav_paths.append(wav_path)
        combined = AudioSegment.empty()
        for i, wav_path in enumerate(wav_paths):
            seg = AudioSegment.from_wav(wav_path)
            if i == 0:
                combined = seg
            else:
                combined = combined.append(seg, crossfade=crossfade_ms)
        if normalize:
            combined = combined.normalize()
        combined.export(output_filename, format="mp3", bitrate=bitrate)
    finally:
        for p in wav_paths:
            try:
                os.unlink(p)
            except OSError:
                pass


async def _generate_audio_elevenlabs(
    digest_text: str,
    output_filename: str,
    voice_id: str,
    voice_config: dict,
) -> None:
    """Generate audio via ElevenLabs API with chunking."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key or not api_key.strip():
        raise ValueError(
            "ELEVENLABS_API_KEY environment variable is not set. "
            "Set it with: export ELEVENLABS_API_KEY=your_api_key"
        )
    if not aiohttp:
        raise ImportError("aiohttp is required for ElevenLabs TTS")
    settings = voice_config.get("tts_settings", {}).get("elevenlabs", {})
    model_id = settings.get("model_id", "eleven_multilingual_v2")
    output_format = settings.get("output_format", "mp3_44100_128")
    chunk_size = settings.get("chunk_size", 4500)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    text = digest_text.strip()
    chunks = []
    while text:
        if len(text) <= chunk_size:
            chunks.append(text)
            break
        break_at = text.rfind(" ", 0, chunk_size + 1)
        if break_at <= 0:
            break_at = chunk_size
        chunks.append(text[:break_at].strip())
        text = text[break_at:].lstrip()
    if not chunks:
        raise ValueError("Digest text is empty")
    async with aiohttp.ClientSession() as session:
        if len(chunks) == 1:
            payload = {"text": chunks[0], "model_id": model_id, "output_format": output_format}
            async with session.post(url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                with open(output_filename, "wb") as f:
                    f.write(await resp.read())
            return
        mp3_paths = []
        try:
            for i, chunk in enumerate(chunks):
                payload = {"text": chunk, "model_id": model_id, "output_format": output_format}
                async with session.post(url, json=payload, headers=headers) as resp:
                    resp.raise_for_status()
                    fd, path = tempfile.mkstemp(suffix=f"_el_{i}.mp3")
                    os.close(fd)
                    with open(path, "wb") as f:
                        f.write(await resp.read())
                    mp3_paths.append(path)
            from pydub import AudioSegment
            combined = AudioSegment.empty()
            for path in mp3_paths:
                combined += AudioSegment.from_mp3(path)
            combined.export(output_filename, format="mp3", bitrate="128k")
        finally:
            for path in mp3_paths:
                try:
                    os.unlink(path)
                except OSError:
                    pass


async def generate_audio_digest(
    digest_text: str,
    output_filename: str,
    *,
    tts_provider: str,
    voice_name: str,
    language: str,
    voice_config: dict,
    elevenlabs_voice_id: Optional[str] = None,
    pocket_voice: Optional[str] = None,
) -> dict:
    """
    Generate audio file from digest text. Dispatches to Edge TTS, Pocket TTS, or ElevenLabs.
    Returns dict with filename, duration, words, wps, size_kb.
    """
    print(f"\n🎤 Generating AI-enhanced audio: {output_filename} (provider: {tts_provider})")
    if tts_provider == "elevenlabs":
        print("   🔊 Using ElevenLabs TTS (voice_id from config)")
    elif tts_provider == "edge_tts":
        print("   🔊 Using Edge TTS")
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

    if tts_provider == "pocket_tts":
        voice_id = pocket_voice or voice_config.get("voices", {}).get(language, {}).get("pocket_voice") or "alba"
        if hasattr(asyncio, "to_thread"):
            await asyncio.to_thread(
                _pocket_tts_generate_sync, digest_text, output_filename, voice_id, voice_config
            )
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: _pocket_tts_generate_sync(digest_text, output_filename, voice_id, voice_config),
            )
        print("   ✅ Pocket TTS audio generated successfully")
    elif tts_provider == "elevenlabs":
        vid = elevenlabs_voice_id or voice_config.get("tts_settings", {}).get("elevenlabs", {}).get("voice_id") or "EXAVITQu4vr4xnSDxMaL"
        await _generate_audio_elevenlabs(digest_text, output_filename, vid, voice_config)
        print("   ✅ ElevenLabs audio generated successfully")
    else:
        # Edge TTS
        tts_settings = voice_config["tts_settings"]["edge_tts"]
        max_retries = tts_settings["max_retries"]
        retry_delay = tts_settings["initial_retry_delay"]
        retry_backoff = tts_settings["retry_backoff_multiplier"]
        force_ipv4 = tts_settings.get("force_ipv4", True)
        import socket
        original_getaddrinfo = socket.getaddrinfo

        def getaddrinfo_ipv4_only(*args, **kwargs):
            results = original_getaddrinfo(*args, **kwargs)
            return [r for r in results if r[0] == socket.AF_INET]

        current_delay = retry_delay
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"   🔄 Retry attempt {attempt + 1}/{max_retries}")
                if force_ipv4:
                    socket.getaddrinfo = getaddrinfo_ipv4_only
                try:
                    rate = tts_settings.get("rate", "+0%") or "+0%"
                    communicate = edge_tts.Communicate(digest_text, voice_name, rate=rate)
                    with open(output_filename, "wb") as f:
                        async for chunk in communicate.stream():
                            if chunk.get("type") == "audio":
                                f.write(chunk["data"])
                finally:
                    if force_ipv4:
                        socket.getaddrinfo = original_getaddrinfo
                print("   ✅ Edge TTS audio generated successfully")
                break
            except Exception as e:
                err = str(e)
                print(f"   ⚠️ Edge TTS attempt {attempt + 1} failed: {err}")
                is_net = "Network is unreachable" in err or "Cannot connect" in err or "Connection refused" in err or "Temporary failure" in err
                is_auth = "401" in err or "authentication" in err.lower() or "handshake" in err.lower()
                if (is_net or is_auth) and attempt < max_retries - 1:
                    print(f"   ⏳ Waiting {current_delay}s...")
                    await asyncio.sleep(current_delay)
                    current_delay = min(current_delay * retry_backoff, 30)
                    continue
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Edge TTS failed after {max_retries} attempts: {err}") from e
                raise RuntimeError(f"Edge TTS failed: {err}") from e

        if tts_settings.get("compress_silences", False):
            _compress_short_silences(
                output_filename,
                min_ms=tts_settings.get("short_silence_min_ms", 400),
                max_ms=tts_settings.get("short_silence_max_ms", 1100),
                target_ms=tts_settings.get("target_silence_ms", 90),
            )
            print("   ✅ Short silences compressed")

    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(output_filename)
        duration_s = len(audio) / 1000.0
        word_count = len(digest_text.split())
        wps = word_count / duration_s if duration_s > 0 else 0
        size_kb = os.path.getsize(output_filename) / 1024
        print(f"   ✅ AI Audio created: {duration_s:.1f}s, {word_count} words, {wps:.2f} WPS, {size_kb:.0f}KB")
    except Exception as analysis_error:
        print(f"   ⚠️ Audio analysis failed: {analysis_error}")
        duration_s = len(digest_text.split()) / 2.0
        word_count = len(digest_text.split())
        wps = 2.0
        size_kb = os.path.getsize(output_filename) / 1024 if os.path.exists(output_filename) else 0
        print(f"   ✅ AI Audio created: {duration_s:.1f}s (est), {word_count} words, {wps:.2f} WPS, {size_kb:.0f}KB")

    return {
        "filename": output_filename,
        "duration": duration_s,
        "words": word_count,
        "wps": wps,
        "size_kb": size_kb,
    }
