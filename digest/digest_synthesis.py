"""
Build full digest text from themes: intro, AI synthesis per theme, closings, TTS-oriented post-processing.
"""

import re
from datetime import date
from typing import Dict, List, Any

from .models import NewsStory
from . import ai_analysis


async def create_ai_enhanced_digest(
    anthropic_client: Any,
    language: str,
    config: dict,
    themes: Dict[str, List[NewsStory]],
    ai_prompts_config: dict,
) -> str:
    """
    Create full digest string: intro, per-theme synthesis via Claude, closing, then
    TTS-oriented normalization (section transitions, sentence breaking, abbreviations, etc.).
    """
    if not themes:
        return "No significant news themes identified today."

    today = date.today().strftime("%B %d, %Y")
    greeting = config["greeting"]
    region_name = (config.get("region_name") or "UK").replace("&", "and")

    # Intro
    if language == "fr_FR":
        digest = f"{greeting}. Voici votre résumé d'actualités {region_name} pour {today}, présenté par Dynamic Devices. "
    elif language == "de_DE":
        digest = f"{greeting}. Hier ist Ihre {region_name} Nachrichtenzusammenfassung für {today}, präsentiert von Dynamic Devices. "
    elif language == "es_ES":
        digest = f"{greeting}. Aquí está su resumen de noticias {region_name} para {today}, presentado por Dynamic Devices. "
    elif language == "it_IT":
        digest = f"{greeting}. Ecco il vostro riepilogo delle notizie {region_name} per {today}, presentato da Dynamic Devices. "
    elif language == "nl_NL":
        digest = f"{greeting}. Hier is uw {region_name} nieuwsoverzicht voor {today}, gepresenteerd door Dynamic Devices. "
    elif language == "pl_PL":
        months_pl = [
            "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
            "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
        ]
        d = date.today()
        today_pl = f"{d.day} {months_pl[d.month - 1]} {d.year}"
        digest = f"{greeting}. Oto Twój przegląd wiadomości {region_name} na {today_pl}, przygotowany przez Dynamic Devices."
    else:
        digest = f"{greeting}. Here's your {region_name} news digest for {today}, brought to you by Dynamic Devices."

    previous_content = ""
    for theme, stories in themes.items():
        if not stories:
            continue
        theme_content = await ai_analysis.ai_synthesize_content(
            anthropic_client, language, theme, stories, previous_content, ai_prompts_config
        )
        if not theme_content:
            continue
        theme_content = theme_content.strip()
        theme_content = re.sub(r"\r\n|\r|\n", " ", theme_content)
        theme_content = re.sub(r" +", " ", theme_content)
        if theme_content:
            digest = digest.rstrip()
            if digest and not digest.endswith(" "):
                digest += " "
            digest += theme_content
            previous_content += f"\n[{theme}]: {theme_content}"

    # Closings
    if language == "fr_FR":
        digest += " Ce résumé fournit une synthèse des actualités les plus importantes d'aujourd'hui. "
        digest += "Tout le contenu est une analyse originale conçue pour l'accessibilité. "
        digest += "Pour une couverture complète, visitez directement les sites d'actualités."
    elif language == "de_DE":
        digest += " Diese Zusammenfassung bietet eine Synthese der wichtigsten Nachrichten von heute. "
        digest += "Alle Inhalte sind ursprüngliche Analysen, die für die Barrierefreiheit entwickelt wurden. "
        digest += "Für eine vollständige Berichterstattung besuchen Sie direkt die Nachrichten-Websites."
    elif language == "es_ES":
        digest += " Este resumen proporciona una síntesis de las noticias más importantes de hoy. "
        digest += "Todo el contenido es un análisis original diseñado para la accesibilidad. "
        digest += "Para una cobertura completa, visite directamente los sitios web de noticias."
    elif language == "it_IT":
        digest += " Questo riepilogo fornisce una sintesi delle notizie più importanti di oggi. "
        digest += "Tutti i contenuti sono analisi originali progettate per l'accessibilità. "
        digest += "Per una copertura completa, visitate direttamente i siti web di notizie."
    elif language == "nl_NL":
        digest += " Deze samenvatting biedt een synthese van het belangrijkste nieuws van vandaag. "
        digest += "Alle inhoud is originele analyse ontworpen voor toegankelijkheid. "
        digest += "Voor volledige dekking, bezoek direct de nieuwswebsites."
    elif language == "pl_PL":
        digest += " Ten przegląd zawiera syntezę najważniejszych wiadomości z dzisiaj. "
        digest += "Cała treść to oryginalna analiza przygotowana z myślą o dostępności. "
        digest += "Aby uzyskać pełne informacje, odwiedź bezpośrednio strony z wiadomościami."
    else:
        digest += " This digest provides a synthesis of today's most significant news stories. "
        digest += "All content is original analysis designed for accessibility. "
        digest += "For complete coverage, visit news websites directly."

    digest = _normalize_for_tts(digest, language)
    return digest


def _normalize_for_tts(digest: str, language: str) -> str:
    """Apply TTS-oriented normalization: dashes, transitions, quotes, sentence breaking, abbreviations, spacing."""
    digest = re.sub(r"—", ", ", digest)
    digest = re.sub(r"–", ", ", digest)

    if language == "bella":
        digest = re.sub(
            r"\.\s+(Turning to|On the|Meanwhile|For banking|For those|From a|Looking at|Here's|Heres)\b",
            r"; \1", digest, flags=re.IGNORECASE
        )
        digest = re.sub(
            r"\.\s+(The|This|These|When|Understanding|From a banking|For your)\b",
            r", \1", digest, flags=re.IGNORECASE
        )
    elif language == "en_GB":
        digest = re.sub(
            r"\.\s+In (politics|economy|health|international|climate|technology|crime) news\b",
            r"; in \1 news", digest, flags=re.IGNORECASE
        )
        digest = re.sub(r"\.\s+(Meanwhile|Additionally|Furthermore|However)\b", r"; \1", digest, flags=re.IGNORECASE)
    elif language == "pl_PL":
        digest = re.sub(
            r"\.\s+W wiadomościach (polityka|ekonomia|zdrowie|międzynarodowe|klimat|technologia|przestępczość) dzisiaj\b",
            r"; w wiadomościach \1 dzisiaj", digest, flags=re.IGNORECASE
        )
        digest = re.sub(r"\.\s+(Tymczasem|Dodatkowo|Ponadto|Jednakże)\b", r"; \1", digest, flags=re.IGNORECASE)

    digest = re.sub(r'["\']', "", digest)

    if language == "bella":
        digest = _bella_sentence_breaking(digest)
        digest = re.sub(r",\s*;\s*", ", ", digest)
        digest = re.sub(r";\s*\.\s*", ". ", digest)
        digest = re.sub(r";\s*,\s*", "; ", digest)
        digest = re.sub(r";\s*;\s*", "; ", digest)
        digest = re.sub(r"\.\s*;\s*", ". ", digest)
        digest = re.sub(r"([,;])\s*;\s+", r"\1 ", digest)

    # Non-breaking spaces within sentences (Edge TTS)
    _delim = re.compile(r"([.!?]+\s+)")
    parts = _delim.split(digest)
    for i, part in enumerate(parts):
        if not re.match(r"^[.!?]+\s*$", (part.strip() or " ")):
            parts[i] = part.replace(" ", "\u00A0")
    digest = "".join(parts)

    abbreviations = [
        (r"\bNATO\b", "N\u00A0A\u00A0T\u00A0O"),
        (r"\bNHS\b", "N\u00A0H\u00A0S"),
        (r"\bBBC\b", "B\u00A0B\u00A0C"),
        (r"\bEU\b", "E\u00A0U"),
        (r"\bUK\b", "U\u00A0K"),
        (r"\bUS\b", "U\u00A0S"),
        (r"\bMP\b", "M\u00A0P"),
        (r"\bMPs\b", "M\u00A0P\u00A0s"),
        (r"\bCEO\b", "C\u00A0E\u00A0O"),
        (r"\bGDP\b", "G\u00A0D\u00A0P"),
    ]
    for pat, repl in abbreviations:
        digest = re.sub(pat, repl, digest)
    digest = re.sub(r"\bUkraines\b", "Ukraine's", digest, flags=re.IGNORECASE)
    digest = re.sub(r"\bHeres\b", "Here's", digest, flags=re.IGNORECASE)

    if language != "bella":
        digest = _break_long_sentences(digest, max_words=100, comma_break=80, sub_break=50)

    digest = re.sub(r"[ \t]+", " ", digest)
    digest = re.sub(r", ,", ",", digest)
    digest = re.sub(r",,", ",", digest)
    digest = re.sub(r";\s*,", ";", digest)
    digest = re.sub(r" ,", ",", digest)
    digest = re.sub(r"\.([^\s])", r". \1", digest)
    digest = re.sub(r",([^\s])", r", \1", digest)
    digest = re.sub(r";([^\s])", r"; \1", digest)
    return digest


def _bella_sentence_breaking(digest: str) -> str:
    """Break long Bella sentences (over 40 words) at natural points."""
    sentences = re.split(r"([.!?]+\s+)", digest)
    new_sentences = []
    for sentence in sentences:
        if not sentence.strip() or len(sentence.strip()) <= 2:
            new_sentences.append(sentence)
            continue
        words = sentence.split()
        if len(words) <= 40:
            new_sentences.append(sentence)
            continue
        parts = re.split(r"([.!?]+\s+)", sentence)
        for sent_part in parts:
            if not sent_part.strip():
                continue
            sent_words = sent_part.split()
            if len(sent_words) <= 30:
                new_sentences.append(sent_part)
                continue
            segs = re.split(r"([,;])\s+", sent_part)
            current = ""
            for part in segs:
                if part in (";", ","):
                    current += part + " "
                else:
                    test = current + part
                    test_words = test.split()
                    if len(test_words) > 25 and current.strip():
                        cleaned = current.strip().rstrip(";,. ")
                        if cleaned and not cleaned.endswith((";", ",")):
                            new_sentences.append(cleaned + ",")
                        current = part + " "
                    else:
                        current = test + " "
            if current.strip():
                cleaned = current.strip().rstrip(";,. ")
                if cleaned:
                    new_sentences.append(cleaned)
    return " ".join(new_sentences)


def _break_long_sentences(digest: str, max_words: int = 100, comma_break: int = 80, sub_break: int = 50) -> str:
    """Break extremely long sentences (e.g. >100 words) at semicolons then commas."""
    sentences = re.split(r"([.!?]+\s+)", digest)
    new_sentences = []
    for sentence in sentences:
        if not sentence.strip() or len(sentence.strip()) <= 2:
            new_sentences.append(sentence)
            continue
        words = sentence.split()
        if len(words) <= max_words:
            new_sentences.append(sentence)
            continue
        parts = re.split(r"([;])\s+", sentence)
        current = ""
        for part in parts:
            if part == ";":
                if current.strip():
                    new_sentences.append(current.strip() + ";")
                current = ""
            else:
                test = current + part
                test_words = test.split()
                if len(test_words) > comma_break:
                    if current.strip():
                        new_sentences.append(current.strip() + ",")
                    sub_parts = re.split(r"([,;])\s+", part)
                    sub_current = ""
                    for sub_part in sub_parts:
                        if sub_part in (",", ";"):
                            if sub_current.strip():
                                new_sentences.append(sub_current.strip() + sub_part)
                            sub_current = ""
                        else:
                            sub_test = sub_current + sub_part
                            if len(sub_test.split()) > sub_break and sub_current.strip():
                                new_sentences.append(sub_current.strip() + ",")
                                sub_current = sub_part + " "
                            else:
                                sub_current = sub_test + " "
                    if sub_current.strip():
                        new_sentences.append(sub_current.strip())
                    current = ""
                else:
                    current = test + " "
        if current.strip():
            new_sentences.append(current.strip())
    return " ".join(new_sentences) if new_sentences else digest
