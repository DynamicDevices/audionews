# Configuration Files

This directory contains JSON configuration files that control AI prompts and voice settings for the AudioNews service.

## Files

### `ai_prompts.json`
Controls all AI-related prompts and model settings.

**Structure:**
- `system_messages`: Language-specific system messages for the AI (instructions for accessible content creation)
- `analysis_prompt`: Configuration for news story analysis and categorization
  - `template`: The prompt template for analyzing headlines
  - `system_instruction`: Wrapper instruction emphasizing duplicate elimination
  - `region_names`: Language-specific region names (e.g., "UK", "French", "German")
- `synthesis_prompts`: Language-specific prompts for generating audio content
  - Each language has a `template` field with placeholders for `{theme}`, `{headlines}`, and `{previous_context}`
  - `{previous_context}` enables context-aware generation to avoid repetition across themes
  - Each language has a `max_words` field (80 for most languages, 100 for BellaNews)
- `ai_model`: Claude model configuration
  - `name`: Model identifier (e.g., "claude-sonnet-4-5-20250929")
  - `analysis_max_tokens`: Max tokens for story analysis (1500)
  - `analysis_temperature`: Temperature for analysis (0.1 for consistency)
  - `synthesis_max_tokens`: Max tokens for content synthesis (300)
  - `synthesis_temperature`: Temperature for synthesis (0.4 for creativity)

**Supported Languages:**
- `en_GB`: English (UK) - **Active**
- `pl_PL`: Polish (Poland) - **Active**
- `bella`: BellaNews (Personalized business/finance) - **Active**

**Disabled Languages (cost optimization):**
- `en_GB_LON`: English (London)
- `en_GB_LIV`: English (Liverpool)
- `fr_FR`: French (France)
- `de_DE`: German (Germany)
- `es_ES`: Spanish (Spain)
- `it_IT`: Italian (Italy)
- `nl_NL`: Dutch (Netherlands)

### `voice_config.json`
Controls voice settings and TTS configuration.

**Structure:**
- `voices`: **One entry per language** – each digest (en_GB, pl_PL, bella) uses its own voice so the three audio outputs sound distinct.
  - `name`: Edge TTS voice (e.g. "en-IE-EmilyNeural", "pl-PL-ZofiaNeural")
  - `tts_provider`: `edge_tts` | `pocket_tts` | `elevenlabs`
  - `pocket_voice`: Pocket TTS voice id (e.g. "alba") when using Pocket TTS
  - `elevenlabs_voice_id`: ElevenLabs voice id when using ElevenLabs (e.g. "EXAVITQu4vr4xnSDxMaL" = Rachel, "pNInz6obpgDQGcFmaJgB" = Adam)
  - `display_name`, `language`, `gender`, `provider`: metadata
- `tts_settings`: Provider-specific options (Edge, Pocket, ElevenLabs)
  - `edge_tts`:
    - `max_retries`: Number of retry attempts (5)
    - `initial_retry_delay`: Initial delay in seconds (5)
    - `retry_backoff_multiplier`: Backoff multiplier for exponential delay (1.5)
    - `force_ipv4`: Force IPv4 connections for GitHub Actions compatibility (true)
    - `ssl_verify`: SSL certificate verification (true)
    - `rate`: Speech rate adjustment (default: "+10%")
      - Valid range: "-50%" to "+100%"
      - Examples: "+10%" (10% faster), "+20%" (20% faster), "0%" (normal), "-10%" (10% slower)
      - Recommended: "+10%" to "+15%" for optimal speech rate (120-150 WPM)
  - `fallback`:
    - `enabled`: Whether fallback is enabled (false)
    - `provider`: Fallback provider if Edge TTS fails ("google_tts")
- `audio_settings`: Audio file settings
  - `format`: Audio format ("mp3")
  - `quality`: Quality level ("high")
  - `estimated_words_per_second`: Speech rate estimation (2.0)
  - `min_file_size_kb`: Minimum acceptable file size (100)

## Usage

Configuration is loaded by the **digest** package when you run the main script:

```bash
python scripts/github_ai_news_digest.py --language en_GB
```

The digest package reads `config/ai_prompts.json` and `config/voice_config.json` and builds language configs (including sources and themes from `digest/config_loader.py`).

## Editing Guidelines

### Adding a New Language

1. **In `ai_prompts.json`:**
   - Add system message to `system_messages` object
   - Add region name to `analysis_prompt.region_names`
   - Add synthesis prompt template to `synthesis_prompts`

2. **In `voice_config.json`:**
   - Add voice configuration to `voices` object with appropriate Edge TTS (or other provider) voice

3. **In `digest/config_loader.py`:**
   - Add the language to the `templates` dictionary with `sources`, `themes`, `greeting`, `region_name`, `output_dir`, `audio_dir`, `service_name` (see existing entries such as `en_GB` or `pl_PL`)

### Changing AI Model

Update the `ai_model` section in `ai_prompts.json`:
```json
{
  "ai_model": {
    "name": "claude-sonnet-4-5-20250929",
    "analysis_max_tokens": 1500,
    "analysis_temperature": 0.1,
    "synthesis_max_tokens": 300,
    "synthesis_temperature": 0.4
  }
}
```

### Changing Voice

Update the voice name in `voice_config.json`:
```json
{
  "voices": {
    "en_GB": {
      "name": "en-IE-EmilyNeural",
      ...
    }
  }
}
```

Available Edge TTS voices: https://speech.microsoft.com/portal/voicegallery

### Adjusting Retry Logic

Update `tts_settings.edge_tts` in `voice_config.json`:
```json
{
  "tts_settings": {
    "edge_tts": {
      "max_retries": 5,
      "initial_retry_delay": 5,
      "retry_backoff_multiplier": 1.5
    }
  }
}
```

## Testing Changes

After editing configuration files, test that they load correctly:

```bash
python3 -c "from digest.config_loader import AI_PROMPTS_CONFIG, VOICE_CONFIG, LANGUAGE_CONFIGS; print('✅ Config loaded')"
```

## Version Control

Always commit configuration changes with clear descriptions:
```bash
git add config/
git commit -m "🔧 Update AI prompts for better synthesis" 
```

