#!/usr/bin/env python3
"""
Multi-language website updater - avoids conflicts with development
Only updates language-specific pages, not the root redirect page
"""

import os
import re
import json
import argparse
from datetime import date
from pathlib import Path

def format_date_localized(date_obj, language):
    """Format date with localized month names"""
    # Month names by language
    month_names = {
        'en_GB': ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December'],
        'fr_FR': ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
        'de_DE': ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
                  'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'],
        'es_ES': ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'],
        'it_IT': ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
                  'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'],
        'nl_NL': ['januari', 'februari', 'maart', 'april', 'mei', 'juni',
                  'juli', 'augustus', 'september', 'oktober', 'november', 'december'],
        'pl_PL': ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca',
                  'lipca', 'sierpnia', 'września', 'października', 'listopada', 'grudnia']
    }
    
    # Get month name for the language (default to English)
    months = month_names.get(language, month_names.get(language[:5], month_names['en_GB']))
    month_name = months[date_obj.month - 1]
    
    # Format based on language conventions
    if language == 'pl_PL':
        # Polish: "14 stycznia 2026"
        return f"{date_obj.day} {month_name} {date_obj.year}"
    elif language in ['de_DE', 'fr_FR', 'es_ES', 'it_IT', 'nl_NL']:
        # European format: "14 janvier 2026"
        return f"{date_obj.day} {month_name} {date_obj.year}"
    else:
        # English format: "January 14, 2026"
        return f"{month_name} {date_obj.day}, {date_obj.year}"

def update_language_page(language='en_GB'):
    """Update the language-specific page with new content"""
    
    # Language configuration - all 8 supported languages
    config = {
        'en_GB': {
            'page_path': 'docs/en_GB/index.html',
            'audio_dir': 'docs/en_GB/audio',
            'text_dir': 'docs/en_GB'
        },
        'fr_FR': {
            'page_path': 'docs/fr_FR/index.html', 
            'audio_dir': 'docs/fr_FR/audio',
            'text_dir': 'docs/fr_FR'
        },
        'de_DE': {
            'page_path': 'docs/de_DE/index.html',
            'audio_dir': 'docs/de_DE/audio',
            'text_dir': 'docs/de_DE'
        },
        'es_ES': {
            'page_path': 'docs/es_ES/index.html',
            'audio_dir': 'docs/es_ES/audio',
            'text_dir': 'docs/es_ES'
        },
        'it_IT': {
            'page_path': 'docs/it_IT/index.html',
            'audio_dir': 'docs/it_IT/audio',
            'text_dir': 'docs/it_IT'
        },
        'nl_NL': {
            'page_path': 'docs/nl_NL/index.html',
            'audio_dir': 'docs/nl_NL/audio',
            'text_dir': 'docs/nl_NL'
        },
        'pl_PL': {
            'page_path': 'docs/pl_PL/index.html',
            'audio_dir': 'docs/pl_PL/audio',
            'text_dir': 'docs/pl_PL'
        },
        'en_GB_LON': {
            'page_path': 'docs/en_GB_LON/index.html',
            'audio_dir': 'docs/en_GB_LON/audio',
            'text_dir': 'docs/en_GB_LON'
        },
        'en_GB_LIV': {
            'page_path': 'docs/en_GB_LIV/index.html',
            'audio_dir': 'docs/en_GB_LIV/audio',
            'text_dir': 'docs/en_GB_LIV'
        },
        'bella': {
            'page_path': 'docs/bella/index.html',
            'audio_dir': 'docs/bella/audio',
            'text_dir': 'docs/bella'
        }
    }
    
    if language not in config:
        print(f"❌ Unsupported language: {language}")
        return False
    
    lang_config = config[language]
    page_path = lang_config['page_path']
    
    # Check if the page exists
    if not os.path.exists(page_path):
        print(f"⚠️ Language page not found: {page_path}")
        return False
    
    # Get today's files
    today_str = date.today().strftime("%Y_%m_%d")
    audio_file = f"{lang_config['audio_dir']}/news_digest_ai_{today_str}.mp3"
    text_file = f"{lang_config['text_dir']}/news_digest_ai_{today_str}.txt"
    
    # Check if today's content exists
    if not (os.path.exists(audio_file) and os.path.exists(text_file)):
        print(f"⚠️ Today's content not found for {language}")
        print(f"   Expected: {audio_file}")
        print(f"   Expected: {text_file}")
        return False
    
    # Read the current page
    with open(page_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Read the digest text
    with open(text_file, 'r', encoding='utf-8') as f:
        digest_text = f.read()
    
    # Get audio file stats
    audio_size = os.path.getsize(audio_file)
    audio_size_mb = audio_size / (1024 * 1024)
    
    # Calculate duration (rough estimate: 1MB ≈ 1 minute for speech)
    duration_minutes = int(audio_size_mb)
    duration_seconds = int((audio_size_mb - duration_minutes) * 60)
    duration_formatted = f"{duration_minutes}min {duration_seconds}sec"
    
    # Update title with today's date (localized)
    today_formatted = format_date_localized(date.today(), language)
    
    # Language-specific titles and descriptions
    lang_titles = {
        'en_GB': (f"AudioNews.uk - Daily Voice News Digest - {today_formatted}",
                  f"Daily AI-generated audio news digest for {today_formatted} brought to you by Dynamic Devices. Professional Irish voice, screen reader optimized."),
        'fr_FR': (f"AudioNews France - Digest Audio Quotidien - {today_formatted}",
                  f"Résumé quotidien d'actualités audio généré par IA pour {today_formatted} présenté par Dynamic Devices. Voix française professionnelle, optimisé pour lecteurs d'écran."),
        'de_DE': (f"AudioNews Deutschland - Tägliche Audio-Nachrichtenzusammenfassung - {today_formatted}",
                  f"Tägliche KI-generierte Audio-Nachrichtenzusammenfassung für {today_formatted} präsentiert von Dynamic Devices. Professionelle deutsche Stimme, für Screenreader optimiert."),
        'es_ES': (f"AudioNews España - Resumen Diario de Noticias en Audio - {today_formatted}",
                  f"Resumen diario de noticias en audio generado por IA para {today_formatted} presentado por Dynamic Devices. Voz española profesional, optimizado para lectores de pantalla."),
        'it_IT': (f"AudioNews Italia - Notiziario Audio Quotidiano - {today_formatted}",
                  f"Notiziario audio quotidiano generato dall'IA per {today_formatted} presentato da Dynamic Devices. Voce italiana professionale, ottimizzato per lettori di schermo."),
        'nl_NL': (f"AudioNews Nederland - Dagelijks Audio Nieuwsoverzicht - {today_formatted}",
                  f"Dagelijks AI-gegenereerd audio nieuwsoverzicht voor {today_formatted} aangeboden door Dynamic Devices. Professionele Nederlandse stem, geoptimaliseerd voor schermlezers."),
        'pl_PL': (f"AudioNews Polska - Codzienny Przegląd Wiadomości Audio - {today_formatted}",
                  f"Codzienny przegląd wiadomości audio generowany przez AI dla {today_formatted} prezentowany przez Dynamic Devices. Profesjonalny polski głos, zoptymalizowany dla czytników ekranu."),
        'en_GB_LON': (f"AudioNews London - Daily Voice News Digest - {today_formatted}",
                      f"Daily AI-generated audio news digest for {today_formatted} brought to you by Dynamic Devices. Professional London voice, screen reader optimized."),
        'en_GB_LIV': (f"AudioNews Liverpool - Daily Voice News Digest - {today_formatted}",
                      f"Daily AI-generated audio news digest for {today_formatted} brought to you by Dynamic Devices. Professional Liverpool voice, screen reader optimized."),
        'bella': (f"BellaNews - Business & Finance Briefing - {today_formatted}",
                  f"Daily AI-generated business and finance briefing for {today_formatted} covering investment banking, VC, markets, and strategic insights. Tailored for aspiring finance professionals.")
    }
    
    if language in lang_titles:
        new_title, new_description = lang_titles[language]
    else:
        new_title = f"AudioNews - Daily Audio Digest - {today_formatted}"
        new_description = f"Daily AI-generated audio news digest for {today_formatted}."
    
    # Update HTML content (only for actual content pages, not coming soon pages)
    # Check if this is a real content page (has audio player), not a "coming soon" placeholder
    has_content = '<audio' in html and 'digest-card' in html
    if has_content:
        # Update title
        html = re.sub(r'<title>.*?</title>', f'<title>{new_title}</title>', html)
        
        # Update meta description
        html = re.sub(r'<meta name="description" content=".*?"', f'<meta name="description" content="{new_description}"', html)
        
        # Update date in structured data (JSON-LD)
        today_iso = date.today().isoformat()
        html = re.sub(
            r'"name": "Daily [^"]*News Digest - [^"]*"',
            f'"name": "Daily News Digest - {today_formatted}"',
            html
        )
        
        # Update the <time> element with today's date
        html = re.sub(
            r'<time datetime="[^"]*" class="digest-date">[^<]*</time>',
            f'<time datetime="{today_iso}" class="digest-date">{today_formatted}</time>',
            html
        )
        
        # Update audio source (relative path from language directory)
        audio_filename = f"audio/news_digest_ai_{today_str}.mp3"
        html = re.sub(r'<source src="audio/[^"]*"', f'<source src="{audio_filename}"', html)
        
        # Update every download/fallback link to today's audio (any attribute order)
        html = re.sub(r'href="audio/news_digest_ai_\d{4}_\d{2}_\d{2}\.mp3"', f'href="{audio_filename}"', html)
        
        # Update preload link in head
        html = re.sub(r'<link rel="preload" href="audio/[^"]*" as="audio"', f'<link rel="preload" href="{audio_filename}" as="audio"', html)
        
        # JSON-LD AudioObject: contentUrl (correct language path), datePublished, duration
        base_url = "https://audionews.uk"
        content_url = f"{base_url}/{language}/audio/news_digest_ai_{today_str}.mp3"
        html = re.sub(r'"contentUrl":\s*"https://audionews\.uk/[^"]*"', f'"contentUrl": "{content_url}"', html)
        html = re.sub(r'"datePublished":\s*"[^"]*"', f'"datePublished": "{today_iso}T06:00:00Z"', html)
        duration_iso = f"PT{duration_minutes}M{duration_seconds}S"
        html = re.sub(r'"duration":\s*"PT[^"]*"', f'"duration": "{duration_iso}"', html)
        
        # Update digest content in the page
        digest_pattern = r'(<div class="digest-content"[^>]*>)(.*?)(</div>)'
        if re.search(digest_pattern, html, re.DOTALL):
            # Convert text to HTML paragraphs
            digest_paragraphs = []
            for paragraph in digest_text.split('\n\n'):
                if paragraph.strip():
                    digest_paragraphs.append(f'<p>{paragraph.strip()}</p>')
            
            digest_html = '\n            '.join(digest_paragraphs)
            html = re.sub(digest_pattern, f'\\1\n            {digest_html}\n        \\3', html, flags=re.DOTALL)
    
    # Write the updated HTML
    with open(page_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Updated {language} page: {page_path}")
    print(f"   📄 Content: {len(digest_text)} characters")
    print(f"   🎧 Audio: {audio_size_mb:.1f}MB ({duration_formatted})")
    
    return True

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description='Update language-specific website pages')
    parser.add_argument('--language', '-l', 
                       choices=['en_GB', 'fr_FR', 'de_DE', 'es_ES', 'it_IT', 'nl_NL', 'pl_PL', 'bella', 'en_GB_LON', 'en_GB_LIV'], 
                       default='en_GB',
                       help='Language to update (default: en_GB)')
    
    args = parser.parse_args()
    
    print(f"🌐 Updating {args.language} website page...")
    success = update_language_page(args.language)
    
    if success:
        print(f"🎉 Website update completed for {args.language}")
    else:
        print(f"❌ Website update failed for {args.language}")
        exit(1)

if __name__ == "__main__":
    main()
