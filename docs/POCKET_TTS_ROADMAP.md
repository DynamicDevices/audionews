# Roadmap: Add Pocket TTS as an Audio Provider Option

## Context

- **Current**: Audio is generated with **Edge TTS** (en_GB, pl_PL) and **ElevenLabs** (bella in CI). TTS logic lives in `digest/tts.py`; `scripts/github_ai_news_digest.py` is the thin orchestrator. `generate_audio_digest()` in `digest/tts.py` supports Edge, Pocket, and ElevenLabs; it streams to MP3 and optionally runs silence compression.
- **Goal**: Support **Pocket TTS** (Kyutai) as an alternative: local, CPU-only, English-only, no API key. Useful for offline runs, privacy, or CI without depending on Edge availability.

## Pocket TTS summary

| Aspect | Detail |
|--------|--------|
| **Install** | `pip install pocket-tts` (needs PyTorch 2.5+, CPU ok) |
| **Language** | English only (for now) |
| **Voices** | Pre-built: `alba`, `marius`, `javert`, `jean`, `fantine`, `cosette`, `eponine`, `azelma`; or voice clone from WAV |
| **API** | Sync Python: `TTSModel.load_model()` → `get_state_for_audio_prompt(voice)` → `generate_audio(state, text)` → PCM tensor; write WAV then convert to MP3 (e.g. pydub) |
| **Output** | PCM / WAV (we need MP3 for compatibility with existing pipeline and RSS) |
| **Speed** | ~6× real-time on CPU (e.g. M4 MacBook Air); first chunk ~200 ms |

## Roadmap (phased)

### Phase 1: Config and provider selection

1. **Extend `config/voice_config.json`**
   - Add top-level `tts_provider`: `"edge_tts"` | `"pocket_tts"` (default `"edge_tts"`).
   - Add `tts_settings.pocket_tts` with:
     - `voice`: Pocket voice id (e.g. `"alba"`, `"marius"`) or path to WAV for cloning.
     - Optional: `model_cache_dir`, `device` (e.g. `"cpu"`), later speed/quality knobs if the API supports them.
   - Keep `tts_settings.edge_tts` unchanged for Edge-only use.

2. **Voice mapping**
   - In `voice_config.json`, under `voices`, each language can optionally get a `pocket_voice` (e.g. `en_GB` → `"alba"`, `bella` → `"alba"` or another).
   - For languages Pocket doesn’t support (e.g. `pl_PL`, `fr_FR`): if provider is Pocket, either **skip** those languages in CI with a clear log, or **fall back to Edge** for non-English (config-driven).

3. **CLI / env**
   - Add `--tts-provider pocket_tts` (and optionally `edge_tts`) to the orchestrator script; the digest CLI already supports `--tts-provider`. Provider selection is implemented in `digest/tts.py`.
   - Optional: env var `TTS_PROVIDER` overrides config (useful for CI).

**Deliverable**: Config and CLI support; no actual Pocket generation yet. Script still uses Edge only.

---

### Phase 2: TTS abstraction in the digest script

1. **Single entry point**
   - Keep `generate_audio_digest(digest_text, output_filename)` as the only caller-facing API.
   - Inside it, branch on `tts_provider` (from config + CLI/env):
     - `edge_tts` → existing Edge logic (async stream → MP3, then optional silence compression).
     - `pocket_tts` → new path that writes a temporary WAV (or in-memory), converts to MP3, then runs the same silence compression if enabled.

2. **Shared post-processing**
   - Keep `_compress_short_silences()` as-is: it takes an MP3 path. So Pocket path must produce an MP3 (e.g. write WAV → pydub → export MP3 to `output_filename`), then call the same compressor.

3. **Error handling**
   - Pocket: no retries for network (local); retries only if you add transient failure handling (e.g. OOM). Clear message if `pocket_tts` is chosen for a non-English language: “Pocket TTS is English-only; use Edge TTS for this language or skip.”

**Deliverable**: `generate_audio_digest()` can call either Edge or Pocket; output remains MP3 + same compression behaviour.

---

### Phase 3: Pocket TTS backend implementation

1. **Optional dependency**
   - Add `pocket-tts` (and ensure PyTorch is in `requirements.txt` or a separate `requirements-tts-pocket.txt`) so default install stays light for Edge-only users. Option: `pip install -r requirements.txt` (Edge only) vs `pip install -r requirements.txt -r requirements-tts-pocket.txt` (Pocket capable).

2. **Pocket generation helper (sync)**
   - New function (e.g. in `digest/tts.py` or a dedicated `scripts/tts_pocket.py` if you want to keep Pocket-specific code separate):
     - Load model once (or lazily) and cache voice state per language/voice to avoid reloading every digest.
     - For each run: `generate_audio(voice_state, digest_text)` → PCM tensor → write WAV (e.g. temp file) → convert to MP3 (pydub) at `output_filename`.
   - Run this from the async digest script via `asyncio.to_thread()` (or `run_in_executor`) so it doesn’t block the event loop.

3. **Voice resolution**
   - From config: for current language, read `pocket_voice` (or fallback to a default Pocket voice). If missing for a language and provider is Pocket, treat as unsupported (skip or fall back to Edge per Phase 1).

4. **Long text**
   - Pocket supports long text; if we ever need chunking (e.g. for memory), define a simple chunk size and concatenate WAVs before converting to MP3. Not required for first version.

**Deliverable**: Pocket TTS can generate English digests (en_GB, bella) end-to-end to MP3, with same silence compression as Edge.

---

### Phase 4: Local testing and script parity

1. **`scripts/test_tts_local.py`**
   - Add `--provider pocket_tts` (and keep `edge_tts`). Use the same provider abstraction (or a small shared helper) so local test script uses config + CLI to pick Edge vs Pocket.
   - Ensure `--normalize` and `--compress-silences` work with Pocket-generated MP3s (they should, since post-processing is identical).

2. **Docs**
   - Short section in README or `docs/`: when to use Pocket vs Edge, how to set `tts_provider` and install Pocket deps, and that non-English languages need Edge (or are skipped).

**Deliverable**: Developers can run Pocket TTS locally and compare with Edge using the same test script and options.

---

### Phase 5: CI and production use

1. **CI (GitHub Actions)**
   - **Default**: Keep CI on Edge TTS only (no PyTorch / Pocket in the main workflow) to avoid long installs and runner memory limits.
   - **Optional**: Add a separate workflow or job (e.g. `pocket-tts-daily.yml` or a job with `tts_provider: pocket_tts`) that:
     - Installs PyTorch + `pocket-tts`, and
     - Runs digest only for en_GB (and bella if desired) with Pocket, then commits artifacts or uploads them.
   - Or: make Pocket run only on `workflow_dispatch` with an input like `use_pocket_tts: true` for occasional/local-style runs.

2. **Config in repo**
   - `tts_provider` remains `edge_tts` by default so current behaviour is unchanged. Pocket is opt-in via config or CLI.

3. **Quality and ops**
   - Document that Pocket is English-only and may differ in prosody from Edge; silence compression still applies. If needed, add a simple “Pocket TTS” note in the commit message or release notes when Pocket is used.

**Deliverable**: Clear path to run Pocket in CI optionally without affecting the default Edge-based daily digest.

---

## Implementation order (checklist)

- [ ] **Phase 1**: Config schema + `tts_provider` + voice mapping + CLI/env.
- [ ] **Phase 2**: Branch in `generate_audio_digest()` on provider; shared MP3 + compression.
- [x] **Phase 3**: Pocket backend (load model, voice state, generate → WAV → MP3), run via `to_thread`/executor.
- [ ] **Phase 4**: `test_tts_local.py` provider option; docs.
- [ ] **Phase 5**: CI strategy (optional job or manual dispatch); default remains Edge.

## Constraints and notes

- **English-only**: Pocket TTS is English-only; pl_PL, fr_FR, etc. must keep using Edge (or be skipped when provider is Pocket).
- **Output format**: Pipeline and RSS expect MP3; Pocket outputs PCM/WAV, so conversion (e.g. pydub) is required.
- **Dependencies**: PyTorch + pocket-tts are heavier than edge-tts; keep them optional or in a separate requirements file so Edge-only installs stay fast.
- **Async**: Pocket API is synchronous; run it in a thread so the rest of the digest script stays async.
- **Voice quality**: Pocket voices (alba, marius, etc.) will not match Edge’s en-IE-EmilyNeural; document this for users who switch.

## File changes (summary)

| File | Changes |
|------|--------|
| `config/voice_config.json` | `tts_provider`, `tts_settings.pocket_tts`, optional `pocket_voice` per voice entry |
| `digest/tts.py` | Provider branch in `generate_audio_digest()`; Pocket path (WAV→MP3, executor); optional `scripts/tts_pocket.py` for Pocket-specific helpers |
| `scripts/test_tts_local.py` | `--provider pocket_tts \| edge_tts`; use same provider abstraction |
| `requirements.txt` or new file | Optional `pocket-tts` (+ PyTorch) for Pocket support |
| `.github/workflows/` | Optional job or workflow for Pocket (en_GB/bella only) |
| `README.md` or `docs/` | When to use Pocket, install, and language limits |

This roadmap should be enough to implement Pocket TTS as an option alongside Edge TTS without breaking existing behaviour.
