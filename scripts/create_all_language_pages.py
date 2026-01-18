#!/usr/bin/env python3
"""
Create all language-specific pages with unified structure and full language selector
"""

import os
import re
from datetime import date

# Language configurations for all 8 supported languages
LANGUAGE_CONFIGS = {
    'en_GB': {
        'title': 'AudioNews.uk',
        'flag': '🇬🇧',
        'native_name': 'English',
        'subtitle': 'Daily Voice News Digest',
        'tagline': 'Brought to you by Dynamic Devices',
        'section_today': "Today's Audio Digest",
        'section_description': 'Updated daily at 6:00 AM UK time',
        'date_title': 'UK News Summary',
        'audio_description': "Today's news digest. Use your browser's audio controls or download for offline listening.",
        'download_button': 'Download MP3',
        'share_button': 'Copy Auto-Play Link',
        'download_help': 'Download MP3 file to your device for WhatsApp sharing or offline listening',
        'share_help': 'Copy link that will automatically start playing when opened - perfect for WhatsApp sharing',
        'recent_heading': 'Recent Digests',
        'recent_description': "Catch up on previous days' news summaries",
        'about_heading': 'About This Service',
        'footer_service': 'AudioNews.uk',
        'footer_by': 'Service by',
        'footer_love': 'Built with ❤️ for accessibility',
        'canonical_url': 'https://audionews.uk/en_GB/',
        'locale': 'en_GB',
        'lang_code': 'en'
    },
    'fr_FR': {
        'title': 'AudioNews France',
        'flag': '🇫🇷',
        'native_name': 'Français',
        'subtitle': 'Digest Audio Quotidien',
        'tagline': 'Présenté par Dynamic Devices',
        'section_today': "Digest Audio d'Aujourd'hui",
        'section_description': 'Mis à jour quotidiennement à 6h00 (heure du Royaume-Uni)',
        'date_title': 'Résumé des Actualités',
        'audio_description': "Résumé d'actualités d'aujourd'hui. Utilisez les contrôles audio de votre navigateur ou téléchargez pour écouter hors ligne.",
        'download_button': 'Télécharger MP3',
        'share_button': 'Copier le Lien Auto-Play',
        'download_help': 'Téléchargez le fichier MP3 sur votre appareil pour le partager sur WhatsApp ou écouter hors ligne',
        'share_help': 'Copiez le lien qui se lancera automatiquement - parfait pour le partage WhatsApp',
        'recent_heading': 'Digests Récents',
        'recent_description': 'Rattrapez les résumés des jours précédents',
        'about_heading': 'À Propos de ce Service',
        'footer_service': 'AudioNews France',
        'footer_by': 'Service par',
        'footer_love': 'Créé avec ❤️ pour l\'accessibilité',
        'canonical_url': 'https://audionews.uk/fr_FR/',
        'locale': 'fr_FR',
        'lang_code': 'fr'
    },
    'de_DE': {
        'title': 'AudioNews Deutschland',
        'flag': '🇩🇪',
        'native_name': 'Deutsch',
        'subtitle': 'Tägliche Audio-Nachrichtenzusammenfassung',
        'tagline': 'Präsentiert von Dynamic Devices',
        'section_today': 'Heutiger Audio-Digest',
        'section_description': 'Täglich um 6:00 Uhr (UK-Zeit) aktualisiert',
        'date_title': 'Nachrichtenzusammenfassung',
        'audio_description': 'Heutige Nachrichtenzusammenfassung. Verwenden Sie die Audio-Steuerelemente Ihres Browsers oder laden Sie für Offline-Hören herunter.',
        'download_button': 'MP3 Herunterladen',
        'share_button': 'Auto-Play-Link Kopieren',
        'download_help': 'Laden Sie die MP3-Datei auf Ihr Gerät zum WhatsApp-Teilen oder Offline-Hören herunter',
        'share_help': 'Link kopieren, der automatisch abgespielt wird - perfekt zum WhatsApp-Teilen',
        'recent_heading': 'Aktuelle Digests',
        'recent_description': 'Holen Sie die Nachrichtenzusammenfassungen der letzten Tage nach',
        'about_heading': 'Über diesen Service',
        'footer_service': 'AudioNews Deutschland',
        'footer_by': 'Service von',
        'footer_love': 'Mit ❤️ für Barrierefreiheit entwickelt',
        'canonical_url': 'https://audionews.uk/de_DE/',
        'locale': 'de_DE',
        'lang_code': 'de'
    },
    'es_ES': {
        'title': 'AudioNews España',
        'flag': '🇪🇸',
        'native_name': 'Español',
        'subtitle': 'Resumen Diario de Noticias en Audio',
        'tagline': 'Presentado por Dynamic Devices',
        'section_today': 'Resumen de Audio de Hoy',
        'section_description': 'Actualizado diariamente a las 6:00 AM (hora del Reino Unido)',
        'date_title': 'Resumen de Noticias',
        'audio_description': 'Resumen de noticias de hoy. Use los controles de audio de su navegador o descargue para escuchar sin conexión.',
        'download_button': 'Descargar MP3',
        'share_button': 'Copiar Enlace de Auto-Reproducción',
        'download_help': 'Descargue el archivo MP3 a su dispositivo para compartir en WhatsApp o escuchar sin conexión',
        'share_help': 'Copie el enlace que se reproducirá automáticamente - perfecto para compartir en WhatsApp',
        'recent_heading': 'Resúmenes Recientes',
        'recent_description': 'Póngase al día con los resúmenes de días anteriores',
        'about_heading': 'Acerca de este Servicio',
        'footer_service': 'AudioNews España',
        'footer_by': 'Servicio de',
        'footer_love': 'Hecho con ❤️ para accesibilidad',
        'canonical_url': 'https://audionews.uk/es_ES/',
        'locale': 'es_ES',
        'lang_code': 'es'
    },
    'it_IT': {
        'title': 'AudioNews Italia',
        'flag': '🇮🇹',
        'native_name': 'Italiano',
        'subtitle': 'Notiziario Audio Quotidiano',
        'tagline': 'Presentato da Dynamic Devices',
        'section_today': 'Notiziario Audio di Oggi',
        'section_description': 'Aggiornato quotidianamente alle 6:00 (ora del Regno Unito)',
        'date_title': 'Riepilogo Notizie',
        'audio_description': 'Notiziario di oggi. Usa i controlli audio del tuo browser o scarica per ascoltare offline.',
        'download_button': 'Scarica MP3',
        'share_button': 'Copia Link Auto-Play',
        'download_help': 'Scarica il file MP3 sul tuo dispositivo per condividere su WhatsApp o ascoltare offline',
        'share_help': 'Copia il link che si avvierà automaticamente - perfetto per condividere su WhatsApp',
        'recent_heading': 'Notiziari Recenti',
        'recent_description': 'Recupera i riepiloghi delle notizie dei giorni precedenti',
        'about_heading': 'Informazioni su questo Servizio',
        'footer_service': 'AudioNews Italia',
        'footer_by': 'Servizio di',
        'footer_love': 'Realizzato con ❤️ per l\'accessibilità',
        'canonical_url': 'https://audionews.uk/it_IT/',
        'locale': 'it_IT',
        'lang_code': 'it'
    },
    'nl_NL': {
        'title': 'AudioNews Nederland',
        'flag': '🇳🇱',
        'native_name': 'Nederlands',
        'subtitle': 'Dagelijks Audio Nieuwsoverzicht',
        'tagline': 'Aangeboden door Dynamic Devices',
        'section_today': 'Audio Overzicht van Vandaag',
        'section_description': 'Dagelijks bijgewerkt om 6:00 uur (VK-tijd)',
        'date_title': 'Nieuwsoverzicht',
        'audio_description': 'Nieuwsoverzicht van vandaag. Gebruik de audiobesturing van uw browser of download voor offline luisteren.',
        'download_button': 'MP3 Downloaden',
        'share_button': 'Auto-Play Link Kopiëren',
        'download_help': 'Download het MP3-bestand naar uw apparaat voor WhatsApp delen of offline luisteren',
        'share_help': 'Kopieer de link die automatisch wordt afgespeeld - perfect voor WhatsApp delen',
        'recent_heading': 'Recente Overzichten',
        'recent_description': 'Haal de nieuwsoverzichten van vorige dagen in',
        'about_heading': 'Over deze Service',
        'footer_service': 'AudioNews Nederland',
        'footer_by': 'Service door',
        'footer_love': 'Gemaakt met ❤️ voor toegankelijkheid',
        'canonical_url': 'https://audionews.uk/nl_NL/',
        'locale': 'nl_NL',
        'lang_code': 'nl'
    },
    'pl_PL': {
        'title': 'AudioNews Polska',
        'flag': '🇵🇱',
        'native_name': 'Polski',
        'subtitle': 'Codzienny Przegląd Wiadomości Audio',
        'tagline': 'Przedstawione przez Dynamic Devices',
        'section_today': 'Dzisiejszy Przegląd Audio',
        'section_description': 'Aktualizowane codziennie o 6:00 rano (czas brytyjski)',
        'date_title': 'Podsumowanie Wiadomości',
        'audio_description': 'Dzisiejszy przegląd wiadomości. Użyj kontrolek audio przeglądarki lub pobierz do słuchania offline.',
        'download_button': 'Pobierz MP3',
        'share_button': 'Kopiuj Link Auto-Play',
        'download_help': 'Pobierz plik MP3 na swoje urządzenie do udostępniania przez WhatsApp lub słuchania offline',
        'share_help': 'Skopiuj link, który automatycznie zacznie się odtwarzać - idealny do udostępniania przez WhatsApp',
        'recent_heading': 'Ostatnie Przeglądy',
        'recent_description': 'Nadróbcie podsumowania wiadomości z poprzednich dni',
        'about_heading': 'O Tej Usłudze',
        'footer_service': 'AudioNews Polska',
        'footer_by': 'Usługa przez',
        'footer_love': 'Stworzone z ❤️ dla dostępności',
        'canonical_url': 'https://audionews.uk/pl_PL/',
        'locale': 'pl_PL',
        'lang_code': 'pl'
    },
    'en_GB_LON': {
        'title': 'AudioNews London',
        'flag': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
        'native_name': 'London',
        'subtitle': 'Daily Voice News Digest',
        'tagline': 'Brought to you by Dynamic Devices',
        'section_today': "Today's Audio Digest",
        'section_description': 'Updated daily at 6:00 AM UK time',
        'date_title': 'London News Summary',
        'audio_description': "Today's news digest. Use your browser's audio controls or download for offline listening.",
        'download_button': 'Download MP3',
        'share_button': 'Copy Auto-Play Link',
        'download_help': 'Download MP3 file to your device for WhatsApp sharing or offline listening',
        'share_help': 'Copy link that will automatically start playing when opened - perfect for WhatsApp sharing',
        'recent_heading': 'Recent Digests',
        'recent_description': "Catch up on previous days' news summaries",
        'about_heading': 'About This Service',
        'footer_service': 'AudioNews London',
        'footer_by': 'Service by',
        'footer_love': 'Built with ❤️ for accessibility',
        'canonical_url': 'https://audionews.uk/en_GB_LON/',
        'locale': 'en_GB',
        'lang_code': 'en'
    },
    'en_GB_LIV': {
        'title': 'AudioNews Liverpool',
        'flag': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
        'native_name': 'Liverpool',
        'subtitle': 'Daily Voice News Digest',
        'tagline': 'Brought to you by Dynamic Devices',
        'section_today': "Today's Audio Digest",
        'section_description': 'Updated daily at 6:00 AM UK time',
        'date_title': 'Liverpool News Summary',
        'audio_description': "Today's news digest. Use your browser's audio controls or download for offline listening.",
        'download_button': 'Download MP3',
        'share_button': 'Copy Auto-Play Link',
        'download_help': 'Download MP3 file to your device for WhatsApp sharing or offline listening',
        'share_help': 'Copy link that will automatically start playing when opened - perfect for WhatsApp sharing',
        'recent_heading': 'Recent Digests',
        'recent_description': "Catch up on previous days' news summaries",
        'about_heading': 'About This Service',
        'footer_service': 'AudioNews Liverpool',
        'footer_by': 'Service by',
        'footer_love': 'Built with ❤️ for accessibility',
        'canonical_url': 'https://audionews.uk/en_GB_LIV/',
        'locale': 'en_GB',
        'lang_code': 'en'
    },
    'bella': {
        'title': 'BellaNews',
        'flag': '📊',
        'native_name': 'BellaNews',
        'subtitle': 'Your Daily Business & Finance Briefing',
        'tagline': 'Personalized for Investment Banking & VC Finance',
        'section_today': "Today's Business Briefing",
        'section_description': 'Updated daily at 6:00 AM UK time - Finance news tailored for your career',
        'date_title': 'Business & Finance Summary',
        'audio_description': "Today's business and finance briefing covering markets, investment banking, VC, fintech, and strategic insights.",
        'download_button': 'Download MP3',
        'share_button': 'Copy Auto-Play Link',
        'download_help': 'Download MP3 file to your device for offline listening',
        'share_help': 'Copy link that will automatically start playing when opened',
        'recent_heading': 'Recent Briefings',
        'recent_description': "Catch up on previous days' business summaries",
        'about_heading': 'About BellaNews',
        'footer_service': 'BellaNews',
        'footer_by': 'Personalized by',
        'footer_love': 'Built with ❤️ for aspiring finance professionals',
        'canonical_url': 'https://audionews.uk/bella/',
        'locale': 'en_GB',
        'lang_code': 'en'
    }
}

def generate_language_selector(current_lang):
    """Generate the language selector HTML with all languages including BellaNews"""
    # Order: Core languages first, then special services
    lang_order = ['en_GB', 'fr_FR', 'de_DE', 'es_ES', 'it_IT', 'nl_NL', 'pl_PL', 'bella', 'en_GB_LON', 'en_GB_LIV']
    
    html_parts = []
    for lang in lang_order:
        cfg = LANGUAGE_CONFIGS[lang]
        active_class = ' active" aria-current="page' if lang == current_lang else ''
        html_parts.append(
            f'                <a href="/{lang}/" class="lang-link{active_class}" title="{cfg["native_name"]}">'
            f'{cfg["flag"]} {cfg["native_name"]}</a>'
        )
    
    return '\n'.join(html_parts)

def create_language_page(language):
    """Create a language-specific page based on the English template"""
    
    if language not in LANGUAGE_CONFIGS:
        print(f"❌ Unsupported language: {language}")
        return False
    
    cfg = LANGUAGE_CONFIGS[language]
    
    # Read the English template
    template_path = 'docs/en_GB/index.html'
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Replace language-specific content
    
    # HTML lang attribute
    html = re.sub(r'<html lang="[^"]*">', f'<html lang="{cfg["lang_code"]}">', html)
    
    # Meta tags - title
    html = html.replace('AudioNews.uk - Daily Voice News Digest', f'{cfg["title"]} - {cfg["subtitle"]}')
    
    # Canonical URL
    html = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{cfg["canonical_url"]}">', html)
    
    # Open Graph
    html = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{cfg["canonical_url"]}">', html)
    html = re.sub(r'<meta property="og:site_name" content="[^"]*">', f'<meta property="og:site_name" content="{cfg["title"]}">', html)
    html = re.sub(r'<meta property="og:locale" content="[^"]*">', f'<meta property="og:locale" content="{cfg["locale"]}">', html)
    
    # Twitter Card
    html = re.sub(r'<meta name="twitter:url" content="[^"]*">', f'<meta name="twitter:url" content="{cfg["canonical_url"]}">', html)
    
    # Header - title
    html = re.sub(
        r'(<h1 class="site-title">.*?<span class="site-icon"[^>]*>📰</span>\s*)AudioNews\.uk',
        f'\\1{cfg["title"]}',
        html,
        flags=re.DOTALL
    )
    html = re.sub(
        r'<p class="site-tagline">Brought to you by Dynamic Devices</p>',
        f'<p class="site-tagline">{cfg["tagline"]}</p>',
        html
    )
    
    # Replace the language selector with full 8-language version
    lang_selector = generate_language_selector(language)
    html = re.sub(
        r'<!-- Language Selector -->.*?</nav>',
        f'<!-- Language Selector -->\n            <nav class="language-selector" aria-label="Language selection" style="margin-top: 1rem;">\n{lang_selector}\n            </nav>',
        html,
        flags=re.DOTALL
    )
    
    # Main content sections
    html = re.sub(
        r'<span class="section-icon"[^>]*>🎧</span>\s*Today\'s Audio Digest',
        f'<span class="section-icon" aria-hidden="true">🎧</span>\n                    {cfg["section_today"]}',
        html
    )
    html = re.sub(
        r'<p class="section-description">Updated daily at 6:00 AM UK time</p>',
        f'<p class="section-description">{cfg["section_description"]}</p>',
        html
    )
    html = re.sub(
        r'- UK News Summary',
        f'- {cfg["date_title"]}',
        html
    )
    html = re.sub(
        r'Today\'s news digest\. Use your browser\'s audio controls or download for offline listening\.',
        cfg["audio_description"],
        html
    )
    
    # Buttons
    html = re.sub(
        r'(<span class="button-icon"[^>]*>⬇️</span>\s*)Download MP3',
        f'\\1{cfg["download_button"]}',
        html
    )
    html = re.sub(
        r'(<span class="button-icon"[^>]*>📱</span>\s*)Copy Auto-Play Link',
        f'\\1{cfg["share_button"]}',
        html
    )
    
    # Help text
    html = re.sub(
        r'Download MP3 file to your device for WhatsApp sharing or offline listening',
        cfg["download_help"],
        html
    )
    html = re.sub(
        r'Copy link that will automatically start playing when opened - perfect for WhatsApp sharing',
        cfg["share_help"],
        html
    )
    
    # Recent digests section
    html = re.sub(
        r'(<span class="section-icon"[^>]*>📅</span>\s*)Recent Digests',
        f'\\1{cfg["recent_heading"]}',
        html
    )
    html = re.sub(
        r'Catch up on previous days\' news summaries',
        cfg["recent_description"],
        html
    )
    
    # About section
    html = re.sub(
        r'About This Service',
        cfg["about_heading"],
        html
    )
    
    # Footer
    html = re.sub(
        r'<strong>AudioNews\.uk</strong> - Service by',
        f'<strong>{cfg["footer_service"]}</strong> - {cfg["footer_by"]}',
        html
    )
    html = re.sub(
        r'Built with ❤️ for accessibility',
        cfg["footer_love"],
        html
    )
    
    # Write the new page
    output_path = f'docs/{language}/index.html'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Created {language} page: {output_path}")
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'all':
            print("🌍 Creating all language pages...")
            success_count = 0
            for lang in LANGUAGE_CONFIGS.keys():
                if lang != 'en_GB':  # Skip English as it's the template
                    if create_language_page(lang):
                        success_count += 1
            print(f"\n✅ Created {success_count} language pages")
        else:
            language = sys.argv[1]
            create_language_page(language)
    else:
        print("Usage: python3 create_all_language_pages.py <language|all>")
        print(f"Languages: {', '.join(LANGUAGE_CONFIGS.keys())}")
        sys.exit(1)

