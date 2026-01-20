#!/usr/bin/env python3
"""
Generate RSS feeds for podcast distribution (Spotify, Apple Podcasts, etc.)
Creates RSS 2.0 compliant feeds for each language/service
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
import json
import re
from typing import Dict, List, Optional

# Podcast configuration
PODCAST_CONFIG = {
    'en_GB': {
        'title': 'AudioNews UK - Daily News Digest',
        'description': 'Daily AI-enhanced news digest for blind and partially sighted users. Professional Irish voice delivers concise summaries of UK news covering politics, economy, health, international affairs, climate, technology, and crime.',
        'subtitle': 'AI-powered daily UK news podcast for blind and partially sighted users. Tech for good delivering accessible news summaries.',
        'author': 'Dynamic Devices',
        'email': 'audionews@dynamicdevices.co.uk',
        'language': 'en-GB',
        'category': 'News',
        'subcategory': 'Daily News',
        'keywords': ['news', 'ai', 'techforgood', 'accessibility', 'uk news', 'daily news', 'audio news', 'visually impaired', 'blind', 'partially sighted', 'blind and partially sighted', 'assistive technology', 'screen reader', 'accessible news'],
        'explicit': 'no',
        'image_url': 'https://audionews.uk/images/podcast-cover-en-gb-v2.png',
        'base_url': 'https://audionews.uk/en_GB'
    },
    'pl_PL': {
        'title': 'AudioNews Polska - Codzienny Przegląd Wiadomości',
        'description': 'Codzienny przegląd wiadomości audio generowany przez AI dla osób niewidomych i słabowidzących. Profesjonalny polski głos dostarcza zwięzłe podsumowania polskich wiadomości.',
        'subtitle': 'Codzienne wiadomości z Polski generowane przez AI. Technologia dla dobra - dostępne wiadomości audio.',
        'author': 'Dynamic Devices',
        'email': 'audionews@dynamicdevices.co.uk',
        'language': 'pl-PL',
        'category': 'News',
        'subcategory': 'Daily News',
        'keywords': ['news', 'ai', 'techforgood', 'accessibility', 'polish news', 'wiadomości', 'dostępność', 'niewidomi', 'słabowidzący', 'niewidomi i słabowidzący', 'technologia wspomagająca', 'screen reader', 'dostępne wiadomości'],
        'explicit': 'no',
        'image_url': 'https://audionews.uk/images/podcast-cover-pl-pl-v2.png',
        'base_url': 'https://audionews.uk/pl_PL'
    },
    'bella': {
        'title': 'BellaNews - Daily News for Undergraduate Business and Finance',
        'description': 'Daily news for undergraduate business and finance students. Personalized business and finance news digest for mathematics undergraduates interested in investment banking, VC finance, and business strategy. AI-enhanced analysis connecting news to career insights.',
        'subtitle': 'Daily news for undergraduate business and finance. AI-powered analysis connecting news to investment banking and VC careers.',
        'author': 'Dynamic Devices',
        'email': 'audionews@dynamicdevices.co.uk',
        'language': 'en-GB',
        'category': 'Business',
        'subcategory': 'Finance',
        'keywords': ['news', 'ai', 'techforgood', 'business', 'finance', 'investment banking', 'vc', 'career', 'business strategy'],
        'explicit': 'no',
        'image_url': 'https://audionews.uk/images/podcast-cover-bella-v2.png',
        'base_url': 'https://audionews.uk/bella'
    }
}

def format_date_for_rss(dt: datetime) -> str:
    """Format datetime as RFC 822 date for RSS"""
    return dt.strftime('%a, %d %b %Y %H:%M:%S %z')


def get_episode_date_from_filename(filename: str) -> Optional[datetime]:
    """Extract date from filename like news_digest_ai_2026_01_19.mp3"""
    match = re.search(r'(\d{4})_(\d{2})_(\d{2})', filename)
    if match:
        year, month, day = match.groups()
        try:
            # Create datetime at 6 AM UTC (when digest is published)
            return datetime(int(year), int(month), int(day), 6, 0, 0, tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def get_file_size(filepath: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0


def get_audio_duration(filepath: str) -> Optional[str]:
    """Get audio duration in HH:MM:SS or MM:SS format for iTunes RSS"""
    try:
        # Try using pydub first (most accurate)
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(filepath)
        duration_seconds = len(audio) / 1000.0
    except ImportError:
        # Fallback: estimate from file size (rough estimate)
        # MP3 at ~64kbps = ~8KB per second
        file_size = get_file_size(filepath)
        duration_seconds = file_size / 8192.0  # Very rough estimate
    except Exception:
        return None
    
    if duration_seconds <= 0:
        return None
    
    # Format as HH:MM:SS or MM:SS
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    seconds = int(duration_seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def read_transcript(transcript_path: str) -> Dict[str, str]:
    """Read transcript and extract metadata"""
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract generation time
        gen_match = re.search(r'Generated: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
        generated_time = None
        if gen_match:
            try:
                generated_time = datetime.strptime(gen_match.group(1), '%Y-%m-%d %H:%M:%S')
                generated_time = generated_time.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        
        # Extract main content (skip header)
        parts = content.split('========================================')
        main_content = parts[-1].strip() if len(parts) > 1 else content.strip()
        
        # Remove repetitive opening greetings/introductions
        # Patterns to remove (case-insensitive):
        opening_patterns = [
            r'^Good morning[^.]*\.\s*Here\'?s your[^.]*news digest[^.]*brought to you by Dynamic Devices\.?\s*',
            r'^Good morning[^.]*\.\s*Here\'?s your[^.]*brought to you by Dynamic Devices\.?\s*',
            r'^Dzień dobry[^.]*\.\s*Oto Twój przegląd wiadomości[^.]*przygotowany przez Dynamic Devices\.?\s*',
            r'^Good morning Bella[^.]*\.\s*Heres your[^.]*brought to you by Dynamic Devices\.?\s*',
            r'^Good morning Bella[^.]*\.\s*Here\'?s your[^.]*brought to you by Dynamic Devices\.?\s*',
        ]
        
        for pattern in opening_patterns:
            main_content = re.sub(pattern, '', main_content, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up any leading whitespace or "In X news..." patterns that might remain
        main_content = re.sub(r'^\s*In\s+\w+\s+news[^.]*\.?\s*', '', main_content, flags=re.IGNORECASE | re.MULTILINE)
        # Note: We keep "Looking at", "Turning to" etc. in the content as they're part of the actual content
        main_content = main_content.strip()
        
        # Extract headline/topic for more interesting episode titles
        # Get first sentence or first 60 chars as headline
        headline = ""
        # Clean up any leading dots/spaces first
        main_content_clean = main_content.lstrip('. \t\n\r')
        
        first_sentence_match = re.search(r'^([A-Z][^.]{15,70})\.', main_content_clean)
        if first_sentence_match:
            headline = first_sentence_match.group(1).strip()
            # Clean up headline - remove extra spaces, limit length
            headline = re.sub(r'\s+', ' ', headline)
            if len(headline) > 60:
                headline = headline[:57] + '...'
        else:
            # Fallback: use first 60 chars, starting from first capital letter
            first_cap_match = re.search(r'([A-Z][^.]{0,60})', main_content_clean)
            if first_cap_match:
                headline = first_cap_match.group(1).replace('\n', ' ').strip()
                headline = re.sub(r'\s+', ' ', headline)
                if len(headline) > 60:
                    headline = headline[:57] + '...'
            else:
                headline = main_content_clean[:60].replace('\n', ' ').strip()
                if len(main_content_clean) > 60:
                    headline = headline.rstrip('.') + '...'
        
        # Get first 300 chars for description (after removing opening)
        # Clean up any leading punctuation/spaces first (dots, semicolons, etc.)
        main_content_clean = re.sub(r'^[.;,:\s]+', '', main_content).strip()
        
        # For better descriptions, extract the first substantial content
        # This should be episode-specific, not generic
        description = ""
        
        # Try to find first sentence that's at least 40 characters (skip very short phrases)
        # Split by periods, semicolons, and exclamation marks, but preserve the content
        sentences = re.split(r'([.!?;])\s+', main_content_clean)
        # Reconstruct sentences with their punctuation
        reconstructed_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                reconstructed_sentences.append(sentences[i] + sentences[i + 1])
            else:
                reconstructed_sentences.append(sentences[i])
        
        # Find first substantial sentence
        for i, sentence in enumerate(reconstructed_sentences):
            sentence = sentence.strip()
            # Skip very short sentences or generic phrases
            if len(sentence) >= 40 and not re.match(r'^(Here\'?s|This|Daily|Today|Good morning|This digest)', sentence, re.IGNORECASE):
                description = sentence
                # Add next sentence for context if available
                if i < len(reconstructed_sentences) - 1:
                    next_sentence = reconstructed_sentences[i + 1].strip()
                    if len(next_sentence) >= 30 and not re.match(r'^(This|Daily|Today|For|This digest)', next_sentence, re.IGNORECASE):
                        description += " " + next_sentence
                        # Try to add one more if we have space
                        if i + 1 < len(reconstructed_sentences) - 1 and len(description) < 200:
                            third_sentence = reconstructed_sentences[i + 2].strip()
                            if len(third_sentence) >= 20 and not re.match(r'^(This|Daily|Today|For|This digest)', third_sentence, re.IGNORECASE):
                                description += " " + third_sentence
                break
        
        # Fallback: get first 300-400 chars of meaningful content
        if not description or len(description) < 40:
            # Get first substantial chunk, skipping generic phrases
            description = main_content_clean[:400].replace('\n', ' ').strip()
            # Remove any remaining generic opening phrases
            description = re.sub(r'^(Here\'?s|This|Daily|Today|Good morning)[^.]*\.\s*', '', description, flags=re.IGNORECASE).strip()
            # If still starts with generic, find first capital letter after generic phrase
            if re.match(r'^(This|Daily|Today)', description, re.IGNORECASE):
                match = re.search(r'[A-Z][^.]{30,}', description)
                if match:
                    description = match.group(0)
        
        # Clean up description
        description = re.sub(r'\s+', ' ', description).strip()
        # Remove any trailing generic phrases
        description = re.sub(r'\s+(This digest|Daily news digest|brought to you by|All content is original)[^.]*\.?$', '', description, flags=re.IGNORECASE)
        description = re.sub(r'\s+For complete coverage[^.]*\.?$', '', description, flags=re.IGNORECASE)
        
        # Ensure we have a good length (at least 50 chars, up to 300)
        if len(description) > 300:
            # Truncate at word boundary
            description = description[:297].rsplit(' ', 1)[0] + '...'
        elif len(description) < 50 and len(main_content_clean) > len(description):
            # If description is too short, add more content
            remaining = main_content_clean[len(description):].strip()
            if remaining:
                # Find next good sentence
                next_sentences = re.split(r'[.!?;]\s+', remaining)
                for next_sent in next_sentences:
                    next_sent = next_sent.strip()
                    if len(next_sent) >= 30 and not re.match(r'^(This|Daily|Today|For|This digest)', next_sent, re.IGNORECASE):
                        description += " " + next_sent
                        if len(description) > 300:
                            description = description[:297].rsplit(' ', 1)[0] + '...'
                        break
        
        return {
            'description': description,
            'headline': headline,
            'generated_time': generated_time,
            'full_content': main_content
        }
    except Exception as e:
        print(f"   ⚠️ Error reading transcript: {e}")
        return {
            'description': 'Daily news digest',
            'headline': '',
            'generated_time': None,
            'full_content': ''
        }


def generate_rss_feed(language: str, output_dir: str) -> str:
    """Generate RSS feed for a language"""
    config = PODCAST_CONFIG.get(language)
    if not config:
        raise ValueError(f"No podcast config for language: {language}")
    
    audio_dir = Path(output_dir) / 'audio'
    transcript_dir = Path(output_dir)
    
    if not audio_dir.exists():
        print(f"   ⚠️ Audio directory not found: {audio_dir}")
        return None
    
    # Find all audio files
    audio_files = sorted(audio_dir.glob('news_digest_ai_*.mp3'), reverse=True)
    
    if not audio_files:
        print(f"   ⚠️ No audio files found in {audio_dir}")
        return None
    
    # Limit to last 50 episodes (RSS best practice)
    audio_files = audio_files[:50]
    
    print(f"   📻 Found {len(audio_files)} episodes")
    
    # Create RSS root
    rss = ET.Element('rss', version='2.0')
    rss.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    
    channel = ET.SubElement(rss, 'channel')
    
    # Channel metadata
    ET.SubElement(channel, 'title').text = config['title']
    ET.SubElement(channel, 'link').text = config['base_url']
    ET.SubElement(channel, 'description').text = config['description']
    ET.SubElement(channel, 'language').text = config['language']
    # Copyright notice with content license information
    copyright_text = f"Copyright {datetime.now().year} {config['author']}. Generated content licensed under CC BY-NC 4.0 (see CONTENT_LICENSE.md)"
    ET.SubElement(channel, 'copyright').text = copyright_text
    ET.SubElement(channel, 'managingEditor').text = f"{config['email']} ({config['author']})"
    ET.SubElement(channel, 'webMaster').text = config['email']
    
    # Atom link for self-reference
    atom_link = ET.SubElement(channel, 'atom:link')
    atom_link.set('href', f"{config['base_url']}/podcast.rss")
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    # iTunes metadata
    ET.SubElement(channel, 'itunes:author').text = config['author']
    ET.SubElement(channel, 'itunes:summary').text = config['description']
    ET.SubElement(channel, 'itunes:explicit').text = config['explicit']
    ET.SubElement(channel, 'itunes:type').text = 'episodic'
    
    # iTunes subtitle (important for SEO - short, keyword-rich summary)
    subtitle = config.get('subtitle', config['description'][:150])
    if len(subtitle) > 150:
        subtitle = subtitle[:147] + '...'
    ET.SubElement(channel, 'itunes:subtitle').text = subtitle
    
    # iTunes owner (required by Apple Podcasts)
    itunes_owner = ET.SubElement(channel, 'itunes:owner')
    ET.SubElement(itunes_owner, 'itunes:name').text = config['author']
    ET.SubElement(itunes_owner, 'itunes:email').text = config['email']
    
    # Standard RSS categories (for RSS 2.0 compatibility)
    # Main category
    ET.SubElement(channel, 'category').text = config['category']
    
    # Additional category tags for keywords/tags
    if 'keywords' in config:
        for keyword in config['keywords']:
            ET.SubElement(channel, 'category').text = keyword
    
    # iTunes category (for Apple Podcasts and other platforms)
    itunes_category = ET.SubElement(channel, 'itunes:category')
    itunes_category.set('text', config['category'])
    if 'subcategory' in config:
        itunes_subcategory = ET.SubElement(itunes_category, 'itunes:category')
        itunes_subcategory.set('text', config['subcategory'])
    
    # iTunes keywords (comma-separated for Apple Podcasts)
    if 'keywords' in config:
        keywords_str = ', '.join(config['keywords'])
        ET.SubElement(channel, 'itunes:keywords').text = keywords_str
    
    # Add cache-busting parameter to image URL based on file modification time
    # This forces Spotify and other platforms to refresh cached images
    image_url_with_cache = config['image_url']
    image_path = Path('docs/images') / Path(config['image_url']).name
    if image_path.exists():
        # Use file modification timestamp as cache buster
        mtime = int(image_path.stat().st_mtime)
        separator = '&' if '?' in image_url_with_cache else '?'
        image_url_with_cache = f"{config['image_url']}{separator}v={mtime}"
    
    # iTunes image
    itunes_image = ET.SubElement(channel, 'itunes:image')
    itunes_image.set('href', image_url_with_cache)
    
    # Channel image
    image = ET.SubElement(channel, 'image')
    ET.SubElement(image, 'url').text = image_url_with_cache
    ET.SubElement(image, 'title').text = config['title']
    ET.SubElement(image, 'link').text = config['base_url']
    
    # Generate time (now)
    now = datetime.now(timezone.utc)
    ET.SubElement(channel, 'lastBuildDate').text = format_date_for_rss(now)
    ET.SubElement(channel, 'pubDate').text = format_date_for_rss(now)
    ET.SubElement(channel, 'generator').text = 'AudioNews Podcast Generator'
    
    # Add episodes
    total_episodes = len(audio_files)
    for i, audio_file in enumerate(audio_files):
        episode_date = get_episode_date_from_filename(audio_file.name)
        if not episode_date:
            continue
        
        # Find corresponding transcript
        transcript_file = transcript_dir / audio_file.name.replace('.mp3', '.txt')
        transcript_data = read_transcript(str(transcript_file)) if transcript_file.exists() else {}
        
        # Episode URL
        episode_url = f"{config['base_url']}/audio/{audio_file.name}"
        
        # Create item
        item = ET.SubElement(channel, 'item')
        
        # Episode title - make it more interesting with headline
        # Format: "Service Name - Date: Headline" (e.g., "AudioNews UK - January 19, 2026: Prince Harry Legal Case")
        service_name = config['title'].split(' - ')[0]  # Get service name without subtitle
        headline = transcript_data.get('headline', '')
        
        if headline:
            # Use headline to make title more interesting
            title = f"{service_name} - {episode_date.strftime('%B %d, %Y')}: {headline}"
        else:
            # Fallback to simple format
            title = f"{service_name} - {episode_date.strftime('%B %d, %Y')}"
        
        ET.SubElement(item, 'title').text = title
        
        # Episode link
        ET.SubElement(item, 'link').text = f"{config['base_url']}?date={episode_date.strftime('%Y-%m-%d')}"
        
        # Episode description - SEO optimized
        description = transcript_data.get('description', '')
        
        # For BellaNews, create more engaging business/finance-focused descriptions
        if language == 'bella':
            # If description is too generic or missing, try to extract better content from full text
            if not description or len(description) < 50 or 'Daily news digest' in description:
                full_content = transcript_data.get('full_content', '')
                if full_content:
                    # Find first substantial business/finance content
                    # Look for patterns like "Looking at", "turning to", "on the", "for banking", etc.
                    business_patterns = [
                        r'(Looking at|turning to|on the|for banking|for your|investment|venture capital|markets|finance|business strategy)[^.]{30,250}',
                        r'(Arctic geopolitics|tariffs|trade policy|monetary policy|central bank|economy|corporate)[^.]{30,250}',
                        r'(geopolitical|strategic|negotiation|banking|financial|investment|VC|M&A)[^.]{30,250}',
                    ]
                    for pattern in business_patterns:
                        match = re.search(pattern, full_content, re.IGNORECASE)
                        if match:
                            extracted = match.group(0).strip()
                            # Clean up and limit length
                            extracted = re.sub(r'\s+', ' ', extracted).strip()
                            # Remove any remaining generic phrases
                            extracted = re.sub(r'^(Looking at|turning to|on the)\s+', '', extracted, flags=re.IGNORECASE).strip()
                            if len(extracted) > 50:
                                description = extracted[:250].rsplit(' ', 1)[0] + '...' if len(extracted) > 250 else extracted
                                break
                
                # If still no good description, use a better default for BellaNews
                if not description or len(description) < 50 or 'Daily news digest' in description:
                    description = f"Business and finance news analysis covering investment banking, VC finance, markets, and strategic insights for January 20, 2026"
        
        # Fallback for other languages
        if not description:
            description = f"Daily news digest for {episode_date.strftime('%B %d, %Y')}"
        
        # Ensure description is keyword-rich and engaging
        # Add date context for better SEO (but don't duplicate if already there)
        date_prefix = f"{episode_date.strftime('%B %d, %Y')} news: "
        if not description.startswith(date_prefix) and not description.startswith(episode_date.strftime('%B %d, %Y')):
            # Prepend date if not already there (helps with search)
            description = f"{date_prefix}{description}"
        
        ET.SubElement(item, 'description').text = description
        
        # Episode GUID (unique identifier)
        guid = ET.SubElement(item, 'guid')
        guid.text = episode_url
        guid.set('isPermaLink', 'true')
        
        # Publication date
        pub_date = transcript_data.get('generated_time') or episode_date
        ET.SubElement(item, 'pubDate').text = format_date_for_rss(pub_date)
        
        # Enclosure (audio file)
        file_size = get_file_size(str(audio_file))
        enclosure = ET.SubElement(item, 'enclosure')
        enclosure.set('url', episode_url)
        enclosure.set('type', 'audio/mpeg')
        enclosure.set('length', str(file_size))
        
        # Calculate audio duration
        audio_duration = get_audio_duration(str(audio_file))
        
        # iTunes episode metadata
        ET.SubElement(item, 'itunes:title').text = title
        ET.SubElement(item, 'itunes:summary').text = description
        ET.SubElement(item, 'itunes:explicit').text = config['explicit']
        ET.SubElement(item, 'itunes:episodeType').text = 'full'  # full, bonus, or trailer
        
        # Episode number (reverse order: newest = highest number)
        episode_number = total_episodes - i
        ET.SubElement(item, 'itunes:episode').text = str(episode_number)
        
        # Subtitle (short version of description for display)
        subtitle = description[:100].replace('...', '').strip()
        if len(description) > 100:
            subtitle += '...'
        ET.SubElement(item, 'itunes:subtitle').text = subtitle
        
        if audio_duration:
            ET.SubElement(item, 'itunes:duration').text = audio_duration
        else:
            # Empty duration if we can't calculate it
            ET.SubElement(item, 'itunes:duration')
        
        # Note: Full transcripts are NOT included in RSS feed
        # Only the description/synopsis is included for cleaner podcast listings
    
    # Convert to string
    # Note: ET.indent() is only available in Python 3.9+
    try:
        ET.indent(rss, space='  ')
    except AttributeError:
        # Python < 3.9 - formatting will be less pretty but still valid
        pass
    
    xml_string = ET.tostring(rss, encoding='utf-8', xml_declaration=True).decode('utf-8')
    
    return xml_string


def main():
    """Generate RSS feeds for all active languages"""
    print("🎙️ Generating Podcast RSS Feeds\n")
    
    languages = {
        'en_GB': 'docs/en_GB',
        'pl_PL': 'docs/pl_PL',
        'bella': 'docs/bella'
    }
    
    for lang, output_dir in languages.items():
        print(f"📻 Generating RSS for {lang}...")
        try:
            rss_content = generate_rss_feed(lang, output_dir)
            if rss_content:
                rss_path = Path(output_dir) / 'podcast.rss'
                with open(rss_path, 'w', encoding='utf-8') as f:
                    f.write(rss_content)
                print(f"   ✅ Generated: {rss_path}")
            else:
                print(f"   ⚠️ Skipped {lang} - no content found")
        except Exception as e:
            print(f"   ❌ Error generating RSS for {lang}: {e}")
    
    print("\n✅ RSS feed generation complete!")
    print("\n📋 Next steps:")
    print("   1. Create podcast artwork (1400x1400px square images)")
    print("   2. Upload artwork to docs/images/")
    print("   3. Submit RSS feeds to Spotify: https://podcasters.spotify.com/")
    print("   4. Submit to Apple Podcasts: https://podcastsconnect.apple.com/")
    print("   5. RSS feeds are available at:")
    for lang in languages.keys():
        print(f"      - https://audionews.uk/{lang}/podcast.rss")


if __name__ == '__main__':
    main()
