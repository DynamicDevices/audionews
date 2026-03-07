"""
Load AI prompts and voice configuration from config/ JSON files.
"""

import json
from pathlib import Path
from typing import Dict, Any

# Project root: parent of digest package
_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_config_file(filename: str) -> dict:
    """Load configuration from JSON file in project config/."""
    config_path = _CONFIG_DIR / filename
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {config_path}: {e}") from e


def _build_language_configs(voice_config: dict) -> Dict[str, Any]:
    """Build LANGUAGE_CONFIGS with voice names from voice_config."""
    voices = voice_config.get("voices", {})
    # Static structure per language; voice name comes from config
    templates = {
        "en_GB": {
            "name": "English (UK)",
            "native_name": "English (UK)",
            "sources": {
                "BBC News": "https://www.bbc.co.uk/news",
                "Guardian": "https://www.theguardian.com/uk",
                "Independent": "https://www.independent.co.uk",
                "Sky News": "https://news.sky.com",
                "Telegraph": "https://www.telegraph.co.uk",
            },
            "greeting": "Good morning",
            "region_name": "UK",
            "themes": ["politics", "economy", "health", "international", "climate", "technology", "crime"],
            "output_dir": "docs/en_GB",
            "audio_dir": "docs/en_GB/audio",
            "service_name": "AudioNews Daily",
        },
        "fr_FR": {
            "name": "French (France)",
            "native_name": "Français",
            "sources": {
                "Le Monde": "https://www.lemonde.fr/",
                "Le Figaro": "https://www.lefigaro.fr/",
                "Libération": "https://www.liberation.fr/",
                "France 24": "https://www.france24.com/fr/",
            },
            "greeting": "Bonjour",
            "region_name": "françaises",
            "themes": ["politique", "économie", "santé", "international", "climat", "technologie", "société"],
            "output_dir": "docs/fr_FR",
            "audio_dir": "docs/fr_FR/audio",
            "service_name": "AudioNews France",
        },
        "de_DE": {
            "name": "German (Germany)",
            "native_name": "Deutsch",
            "sources": {
                "Der Spiegel": "https://www.spiegel.de/",
                "Die Zeit": "https://www.zeit.de/",
                "Süddeutsche Zeitung": "https://www.sueddeutsche.de/",
                "Frankfurter Allgemeine": "https://www.faz.net/",
            },
            "greeting": "Guten Morgen",
            "region_name": "deutsche",
            "themes": ["politik", "wirtschaft", "gesundheit", "international", "klima", "technologie", "gesellschaft"],
            "output_dir": "docs/de_DE",
            "audio_dir": "docs/de_DE/audio",
            "service_name": "AudioNews Deutschland",
        },
        "es_ES": {
            "name": "Spanish (Spain)",
            "native_name": "Español",
            "sources": {
                "El País": "https://elpais.com/",
                "El Mundo": "https://www.elmundo.es/",
                "ABC": "https://www.abc.es/",
                "La Vanguardia": "https://www.lavanguardia.com/",
            },
            "greeting": "Buenos días",
            "region_name": "españolas",
            "themes": ["política", "economía", "salud", "internacional", "clima", "tecnología", "crimen"],
            "output_dir": "docs/es_ES",
            "audio_dir": "docs/es_ES/audio",
            "service_name": "AudioNews España",
        },
        "it_IT": {
            "name": "Italian (Italy)",
            "native_name": "Italiano",
            "sources": {
                "Corriere della Sera": "https://www.corriere.it/",
                "La Repubblica": "https://www.repubblica.it/",
                "La Gazzetta dello Sport": "https://www.gazzetta.it/",
                "Il Sole 24 Ore": "https://www.ilsole24ore.com/",
            },
            "greeting": "Buongiorno",
            "region_name": "italiane",
            "themes": ["politica", "economia", "salute", "internazionale", "clima", "tecnologia", "crimine"],
            "output_dir": "docs/it_IT",
            "audio_dir": "docs/it_IT/audio",
            "service_name": "AudioNews Italia",
        },
        "nl_NL": {
            "name": "Dutch (Netherlands)",
            "native_name": "Nederlands",
            "sources": {
                "NOS": "https://nos.nl/",
                "De Telegraaf": "https://www.telegraaf.nl/",
                "Volkskrant": "https://www.volkskrant.nl/",
                "NRC": "https://www.nrc.nl/",
            },
            "greeting": "Goedemorgen",
            "region_name": "Nederlandse",
            "themes": ["politiek", "economie", "gezondheid", "internationaal", "klimaat", "technologie", "misdaad"],
            "output_dir": "docs/nl_NL",
            "audio_dir": "docs/nl_NL/audio",
            "service_name": "AudioNews Nederland",
        },
        "pl_PL": {
            "name": "Polish (Poland)",
            "native_name": "Polski",
            "sources": {
                "Gazeta Wyborcza": "https://www.gazeta.pl/",
                "Rzeczpospolita": "https://www.rp.pl/",
                "TVN24": "https://tvn24.pl/",
                "Onet": "https://www.onet.pl/",
                "Polskie Radio": "https://www.polskieradio.pl/",
            },
            "greeting": "Dzień dobry",
            "region_name": "polskie",
            "themes": ["polityka", "ekonomia", "zdrowie", "międzynarodowe", "klimat", "technologia", "przestępczość"],
            "output_dir": "docs/pl_PL",
            "audio_dir": "docs/pl_PL/audio",
            "service_name": "AudioNews Polska Daily",
        },
        "en_GB_LON": {
            "name": "English (London)",
            "native_name": "English (London)",
            "sources": {
                "Evening Standard": "https://www.standard.co.uk/",
                "Time Out London": "https://www.timeout.com/london/news",
                "MyLondon": "https://www.mylondon.news/",
                "BBC London": "https://www.bbc.co.uk/news/england/london",
                "ITV London": "https://www.itv.com/news/london",
            },
            "greeting": "Good morning London",
            "region_name": "London",
            "themes": ["transport", "housing", "westminster", "culture", "crime", "business", "tfl"],
            "output_dir": "docs/en_GB_LON",
            "audio_dir": "docs/en_GB_LON/audio",
            "service_name": "AudioNews London",
        },
        "en_GB_LIV": {
            "name": "English (Liverpool)",
            "native_name": "English (Liverpool)",
            "sources": {
                "Liverpool Echo": "https://www.liverpoolecho.co.uk/",
                "Liverpool FC": "https://www.liverpoolfc.com/news",
                "BBC Merseyside": "https://www.bbc.co.uk/news/england/merseyside",
                "Radio City": "https://www.radiocity.co.uk/news/liverpool-news/",
                "The Guide Liverpool": "https://www.theguideliverpool.com/news/",
            },
            "greeting": "Good morning Liverpool",
            "region_name": "Liverpool",
            "themes": ["football", "merseyside", "culture", "waterfront", "music", "business", "transport"],
            "output_dir": "docs/en_GB_LIV",
            "audio_dir": "docs/en_GB_LIV/audio",
            "service_name": "AudioNews Liverpool",
        },
        "bella": {
            "name": "BellaNews - Business & Finance",
            "native_name": "BellaNews 📊",
            "sources": {
                "Financial Times": "https://www.ft.com/",
                "Guardian Business": "https://www.theguardian.com/business",
                "BBC Business": "https://www.bbc.co.uk/news/business",
                "Reuters Business": "https://www.reuters.com/business/",
                "Bloomberg": "https://www.bloomberg.com/europe",
            },
            "greeting": "Good morning Bella",
            "region_name": "Business & Finance",
            "themes": ["markets", "investment_banking", "venture_capital", "fintech", "corporate_finance", "economics", "startups", "technology"],
            "output_dir": "docs/bella",
            "audio_dir": "docs/bella/audio",
            "service_name": "BellaNews Daily",
        },
    }
    out = {}
    for lang, cfg in templates.items():
        voice_cfg = voices.get(lang, voices.get("en_GB", {}))
        out[lang] = {**cfg, "voice": voice_cfg.get("name", "en-IE-EmilyNeural")}
    return out


# Load at import
AI_PROMPTS_CONFIG = load_config_file("ai_prompts.json")
VOICE_CONFIG = load_config_file("voice_config.json")
LANGUAGE_CONFIGS = _build_language_configs(VOICE_CONFIG)
