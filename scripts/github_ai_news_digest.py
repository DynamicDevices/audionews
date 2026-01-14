#!/usr/bin/env python3
"""
GitHub AI-Enhanced Ethical News Digest Generator
Uses GitHub Copilot API for intelligent content analysis and synthesis
"""

import asyncio
import edge_tts
import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, date
import json
from typing import List, Dict, Optional
import time
import argparse
from dataclasses import dataclass
from pathlib import Path

# AI provider - Anthropic Claude
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("❌ ERROR: Anthropic library not installed. Run: pip install anthropic")

# Load AI prompts and voice configuration
def load_config_file(filename: str) -> dict:
    """Load configuration from JSON file (in project root config/)"""
    # Config is in project root, not in scripts/
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

# Load configurations at module level
AI_PROMPTS_CONFIG = load_config_file('ai_prompts.json')
VOICE_CONFIG = load_config_file('voice_config.json')

# Multi-language configuration
LANGUAGE_CONFIGS = {
    'en_GB': {
        'name': 'English (UK)',
        'native_name': 'English (UK)',
        'sources': {
            'BBC News': 'https://www.bbc.co.uk/news',
            'Guardian': 'https://www.theguardian.com/uk',
            'Independent': 'https://www.independent.co.uk',
            'Sky News': 'https://news.sky.com',
            'Telegraph': 'https://www.telegraph.co.uk'
        },
        'voice': VOICE_CONFIG['voices']['en_GB']['name'],
        'greeting': 'Good morning',
        'region_name': 'UK',
        'themes': ['politics', 'economy', 'health', 'international', 'climate', 'technology', 'crime'],
        'output_dir': 'docs/en_GB',
        'audio_dir': 'docs/en_GB/audio',
        'service_name': 'AudioNews UK'
    },
    'fr_FR': {
        'name': 'French (France)',
        'native_name': 'Français',
        'sources': {
            'Le Monde': 'https://www.lemonde.fr/',
            'Le Figaro': 'https://www.lefigaro.fr/',
            'Libération': 'https://www.liberation.fr/',
            'France 24': 'https://www.france24.com/fr/'
        },
        'voice': VOICE_CONFIG['voices']['fr_FR']['name'],
        'greeting': 'Bonjour',
        'region_name': 'françaises',
        'themes': ['politique', 'économie', 'santé', 'international', 'climat', 'technologie', 'société'],
        'output_dir': 'docs/fr_FR',
        'audio_dir': 'docs/fr_FR/audio',
        'service_name': 'AudioNews France'
    },
    'de_DE': {
        'name': 'German (Germany)',
        'native_name': 'Deutsch',
        'sources': {
            'Der Spiegel': 'https://www.spiegel.de/',
            'Die Zeit': 'https://www.zeit.de/',
            'Süddeutsche Zeitung': 'https://www.sueddeutsche.de/',
            'Frankfurter Allgemeine': 'https://www.faz.net/'
        },
        'voice': VOICE_CONFIG['voices']['de_DE']['name'],
        'greeting': 'Guten Morgen',
        'region_name': 'deutsche',
        'themes': ['politik', 'wirtschaft', 'gesundheit', 'international', 'klima', 'technologie', 'gesellschaft'],
        'output_dir': 'docs/de_DE',
        'audio_dir': 'docs/de_DE/audio',
        'service_name': 'AudioNews Deutschland'
    },
    'es_ES': {
        'name': 'Spanish (Spain)',
        'native_name': 'Español',
        'sources': {
            'El País': 'https://elpais.com/',
            'El Mundo': 'https://www.elmundo.es/',
            'ABC': 'https://www.abc.es/',
            'La Vanguardia': 'https://www.lavanguardia.com/'
        },
        'voice': VOICE_CONFIG['voices']['es_ES']['name'],
        'greeting': 'Buenos días',
        'region_name': 'españolas',
        'themes': ['política', 'economía', 'salud', 'internacional', 'clima', 'tecnología', 'crimen'],
        'output_dir': 'docs/es_ES',
        'audio_dir': 'docs/es_ES/audio',
        'service_name': 'AudioNews España'
    },
    'it_IT': {
        'name': 'Italian (Italy)',
        'native_name': 'Italiano',
        'sources': {
            'Corriere della Sera': 'https://www.corriere.it/',
            'La Repubblica': 'https://www.repubblica.it/',
            'La Gazzetta dello Sport': 'https://www.gazzetta.it/',
            'Il Sole 24 Ore': 'https://www.ilsole24ore.com/'
        },
        'voice': VOICE_CONFIG['voices']['it_IT']['name'],
        'greeting': 'Buongiorno',
        'region_name': 'italiane',
        'themes': ['politica', 'economia', 'salute', 'internazionale', 'clima', 'tecnologia', 'crimine'],
        'output_dir': 'docs/it_IT',
        'audio_dir': 'docs/it_IT/audio',
        'service_name': 'AudioNews Italia'
    },
    'nl_NL': {
        'name': 'Dutch (Netherlands)',
        'native_name': 'Nederlands',
        'sources': {
            'NOS': 'https://nos.nl/',
            'De Telegraaf': 'https://www.telegraaf.nl/',
            'Volkskrant': 'https://www.volkskrant.nl/',
            'NRC': 'https://www.nrc.nl/'
        },
        'voice': VOICE_CONFIG['voices']['nl_NL']['name'],
        'greeting': 'Goedemorgen',
        'region_name': 'Nederlandse',
        'themes': ['politiek', 'economie', 'gezondheid', 'internationaal', 'klimaat', 'technologie', 'misdaad'],
        'output_dir': 'docs/nl_NL',
        'audio_dir': 'docs/nl_NL/audio',
        'service_name': 'AudioNews Nederland'
    },
    'pl_PL': {
        'name': 'Polish (Poland)',
        'native_name': 'Polski',
        'sources': {
            'Gazeta Wyborcza': 'https://www.gazeta.pl/',
            'Rzeczpospolita': 'https://www.rp.pl/',
            'TVN24': 'https://tvn24.pl/',
            'Onet': 'https://www.onet.pl/',
            'Polskie Radio': 'https://www.polskieradio.pl/'
        },
        'voice': VOICE_CONFIG['voices']['pl_PL']['name'],
        'greeting': 'Dzień dobry',
        'region_name': 'polskie',
        'themes': ['polityka', 'ekonomia', 'zdrowie', 'międzynarodowe', 'klimat', 'technologia', 'przestępczość'],
        'output_dir': 'docs/pl_PL',
        'audio_dir': 'docs/pl_PL/audio',
        'service_name': 'AudioNews Polska'
    },
    'en_GB_LON': {
        'name': 'English (London)',
        'native_name': 'English (London)',
        'sources': {
            'Evening Standard': 'https://www.standard.co.uk/',
            'Time Out London': 'https://www.timeout.com/london/news',
            'MyLondon': 'https://www.mylondon.news/',
            'BBC London': 'https://www.bbc.co.uk/news/england/london',
            'ITV London': 'https://www.itv.com/news/london'
        },
        'voice': VOICE_CONFIG['voices']['en_GB_LON']['name'],
        'greeting': 'Good morning London',
        'region_name': 'London',
        'themes': ['transport', 'housing', 'westminster', 'culture', 'crime', 'business', 'tfl'],
        'output_dir': 'docs/en_GB_LON',
        'audio_dir': 'docs/en_GB_LON/audio',
        'service_name': 'AudioNews London'
    },
    'en_GB_LIV': {
        'name': 'English (Liverpool)',
        'native_name': 'English (Liverpool)',
        'sources': {
            'Liverpool Echo': 'https://www.liverpoolecho.co.uk/',
            'Liverpool FC': 'https://www.liverpoolfc.com/news',
            'BBC Merseyside': 'https://www.bbc.co.uk/news/england/merseyside',
            'Radio City': 'https://www.radiocity.co.uk/news/liverpool-news/',
            'The Guide Liverpool': 'https://www.theguideliverpool.com/news/'
        },
        'voice': VOICE_CONFIG['voices']['en_GB_LIV']['name'],
        'greeting': 'Good morning Liverpool',
        'region_name': 'Liverpool',
        'themes': ['football', 'merseyside', 'culture', 'waterfront', 'music', 'business', 'transport'],
        'output_dir': 'docs/en_GB_LIV',
        'audio_dir': 'docs/en_GB_LIV/audio',
        'service_name': 'AudioNews Liverpool'
    }
}

@dataclass
class NewsStory:
    title: str
    source: str
    link: Optional[str]
    timestamp: str
    theme: Optional[str] = None
    significance_score: Optional[float] = None

class GitHubAINewsDigest:
    """
    AI-Enhanced news synthesis using GitHub Copilot API
    Provides intelligent analysis while maintaining copyright compliance
    """
    
    def __init__(self, language='en_GB'):
        self.language = language
        self.config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['en_GB'])
        self.sources = self.config['sources']
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.voice_name = self.config['voice']
        
        # Initialize GitHub Copilot API
        self.setup_github_ai()
    
    def setup_github_ai(self):
        """
        Setup AI integration with Anthropic (primary provider)
        """
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Enhanced debugging
        print(f"🔍 Debug - Checking AI setup:")
        print(f"   - ANTHROPIC_AVAILABLE (library): {ANTHROPIC_AVAILABLE}")
        print(f"   - ANTHROPIC_API_KEY (env): {'✅ Present (length: ' + str(len(anthropic_key)) + ')' if anthropic_key else '❌ Missing'}")
        print(f"   - Language: {self.language}")
        
        if anthropic_key and ANTHROPIC_AVAILABLE:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                self.ai_provider = 'anthropic'
                self.ai_enabled = True
                print("🤖 AI Analysis: ANTHROPIC ENABLED")
                print(f"   ✅ Successfully initialized Anthropic client")
            except Exception as init_error:
                error_msg = f"🚨 CRITICAL ERROR: Failed to initialize Anthropic client: {init_error}"
                print(error_msg)
                print(f"   🔍 API key starts with: {anthropic_key[:20]}..." if anthropic_key and len(anthropic_key) > 20 else "   🔍 API key too short or invalid")
                raise Exception(f"Anthropic initialization failed: {init_error}")
        else:
            # CRITICAL: For professional news service, AI MUST work
            error_msg = "🚨 CRITICAL ERROR: AI Analysis is REQUIRED for professional news service"
            if not ANTHROPIC_AVAILABLE:
                error_msg += "\n❌ Anthropic library not installed"
            elif not anthropic_key:
                error_msg += "\n❌ ANTHROPIC_API_KEY environment variable not found"
            else:
                error_msg += "\n❌ Unknown issue with Anthropic setup"
            
            print(error_msg)
            print("💡 This service requires Anthropic API access")
            print("🔧 Please configure ANTHROPIC_API_KEY and retry")
            
            # Enhanced debugging for CI environment
            print(f"🔍 Environment variables present:")
            print(f"   - ANTHROPIC_API_KEY: {'✅ Present' if anthropic_key else '❌ Missing'}")
            print(f"   - ANTHROPIC_AVAILABLE: {ANTHROPIC_AVAILABLE}")
            print(f"   - Current working directory: {os.getcwd()}")
            print(f"   - Language: {self.language}")
            
            # FAIL FAST - don't produce garbage content
            raise Exception("AI Analysis requires valid ANTHROPIC_API_KEY. Cannot continue without it.")
    
    def get_selectors_for_language(self) -> List[str]:
        """Get language and source-specific CSS selectors"""
        base_selectors = [
            'h1, h2, h3',
            '[data-testid*="headline"]',
            '.headline',
            '.title',
            'article h1, article h2'
        ]
        
        if self.language == 'fr_FR':
            # French news site specific selectors
            french_selectors = [
                '.article__title',           # Le Monde
                '.fig-headline',             # Le Figaro
                '.teaser__title',           # Libération
                '.t-content__title',        # France 24
                '.article-title',
                '.titre',
                '.headline-title'
            ]
            return base_selectors + french_selectors
        
        elif self.language == 'de_DE':
            # German news site specific selectors
            german_selectors = [
                '.article-title',           # Der Spiegel
                '.zon-teaser__title',       # Die Zeit
                '.entry-title',             # Süddeutsche Zeitung
                '.js-headline',             # FAZ
                '.headline',
                '.titel',
                '.schlagzeile'
            ]
            return base_selectors + german_selectors
        
        elif self.language == 'es_ES':
            # Spanish news site specific selectors
            spanish_selectors = [
                '.c_h_t',                   # El País
                '.ue-c-cover-content__headline',  # El Mundo
                '.titular',                 # ABC
                '.tit',                     # La Vanguardia
                '.headline',
                '.titulo',
                '.cabecera'
            ]
            return base_selectors + spanish_selectors
        
        elif self.language == 'it_IT':
            # Italian news site specific selectors
            italian_selectors = [
                '.title-art',               # Corriere della Sera
                '.entry-title',             # La Repubblica
                '.gazzetta-title',          # Gazzetta dello Sport
                '.article-title',           # Il Sole 24 Ore
                '.headline',
                '.titolo',
                '.intestazione'
            ]
            return base_selectors + italian_selectors
        
        elif self.language == 'nl_NL':
            # Dutch news site specific selectors
            dutch_selectors = [
                '.sc-1x7olzq',              # NOS
                '.ArticleTeaser__title',    # De Telegraaf
                '.teaser__title',           # Volkskrant
                '.article__title',          # NRC
                '.headline',
                '.titel',
                '.kop'
            ]
            return base_selectors + dutch_selectors
        
        elif self.language in ['en_GB_LON', 'en_GB_LIV']:
            # London/Liverpool specific selectors (extends UK selectors)
            uk_selectors = [
                '.fc-item__title',          # Guardian
                '.story-headline',          # BBC
                '.headline-text',           # Independent
                '.standard-headline',       # Evening Standard
                '.echo-headline',           # Liverpool Echo
                '.article-headline'
            ]
            return base_selectors + uk_selectors
        
        else:
            # Default UK news site specific selectors
            uk_selectors = [
                '.fc-item__title',          # Guardian
                '.story-headline',          # BBC
                '.headline-text'            # Independent
            ]
            return base_selectors + uk_selectors

    def fetch_headlines_from_source(self, source_name: str, url: str) -> List[NewsStory]:
        """
        Extract headlines and create NewsStory objects
        """
        try:
            print(f"📡 Scanning {source_name}...")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            stories = []
            
            # Get language-specific selectors
            selectors = self.get_selectors_for_language()
            
            seen_headlines = set()
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements[:15]:
                    text = element.get_text(strip=True)
                    if (text and 
                        len(text) > 15 and 
                        len(text) < 200 and 
                        text not in seen_headlines and
                        not text.lower().startswith(('cookie', 'accept', 'subscribe', 'sign up', 'follow us'))):
                        
                        # Extract link
                        link = None
                        link_elem = element.find('a') or element.find_parent('a')
                        if link_elem and link_elem.get('href'):
                            href = link_elem.get('href')
                            if href.startswith('/'):
                                link = url + href
                            elif href.startswith('http'):
                                link = href
                        
                        story = NewsStory(
                            title=text,
                            source=source_name,
                            link=link,
                            timestamp=datetime.now().isoformat()
                        )
                        
                        stories.append(story)
                        seen_headlines.add(text)
                        
                        if len(stories) >= 12:
                            break
                
                if stories:
                    break
            
            print(f"   ✅ Found {len(stories)} stories from {source_name}")
            return stories
            
        except Exception as e:
            print(f"   ❌ Error fetching from {source_name}: {e}")
            return []
    
    async def ai_analyze_stories(self, all_stories: List[NewsStory]) -> Dict[str, List[NewsStory]]:
        """
        Use GitHub AI to intelligently categorize and analyze stories - REQUIRED for professional service
        """
        if not self.ai_enabled or not all_stories:
            raise Exception("🚨 CRITICAL: AI Analysis is REQUIRED. Cannot produce professional news digest without AI analysis.")
        
        print("\n🤖 AI ANALYSIS: Intelligent story categorization")
        print("=" * 50)
        
        try:
            # Prepare stories for AI analysis
            story_titles = [f"{i+1}. {story.title} (Source: {story.source})" 
                          for i, story in enumerate(all_stories)]
            
            # Get region name from config
            region_name = AI_PROMPTS_CONFIG['analysis_prompt']['region_names'].get(
                self.language, 
                AI_PROMPTS_CONFIG['analysis_prompt']['region_names']['en_GB']
            )
            
            # Format the analysis prompt template
            ai_prompt = AI_PROMPTS_CONFIG['analysis_prompt']['template'].format(
                region=region_name,
                headlines=chr(10).join(story_titles)
            )
            
            # Format the system instruction
            system_instruction = AI_PROMPTS_CONFIG['analysis_prompt']['system_instruction'].format(
                prompt=ai_prompt
            )
            
            # Use Anthropic Claude for AI analysis with config settings
            ai_model_config = AI_PROMPTS_CONFIG['ai_model']
            response = self.anthropic_client.messages.create(
                model=ai_model_config['name'],
                max_tokens=ai_model_config['analysis_max_tokens'],
                temperature=ai_model_config['analysis_temperature'],
                messages=[
                    {"role": "user", "content": system_instruction}
                ]
            )
            
            # Extract and clean the response text
            response_text = response.content[0].text.strip()
            print(f"   🔍 Raw AI response length: {len(response_text)} chars")
            print(f"   🔍 Response starts with: {response_text[:50]}")
            print(f"   🔍 Response ends with: {response_text[-50:]}")
            
            # Clean the response - remove any markdown formatting
            cleaned_text = response_text
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]  # Remove ```json
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]   # Remove ```
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]  # Remove trailing ```
            
            cleaned_text = cleaned_text.strip()
            
            # Try to extract JSON from the response
            try:
                ai_analysis = json.loads(cleaned_text)
                print(f"   ✅ JSON parsed successfully: {len(ai_analysis)} themes")
            except json.JSONDecodeError as json_error:
                print(f"   ❌ JSON parsing failed: {json_error}")
                print(f"   📝 Cleaned text: {cleaned_text[:500]}")
                
                # Try to extract JSON using regex as fallback
                import re
                json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group()
                        ai_analysis = json.loads(json_str)
                        print(f"   ✅ JSON extracted with regex: {len(ai_analysis)} themes")
                    except json.JSONDecodeError:
                        raise Exception(f"Claude returned invalid JSON even after regex extraction: {json_error}. Full response: {response_text}")
                else:
                    raise Exception(f"No JSON found in Claude response: {json_error}. Full response: {response_text}")
            
            
            # Apply AI analysis to stories and add programmatic deduplication
            themes = {}
            for theme, story_analyses in ai_analysis.items():
                theme_stories = []
                seen_keywords = set()  # Track keywords to prevent similar stories
                
                # Flatten if the AI double-nested the list (Claude sometimes does this)
                if story_analyses and isinstance(story_analyses[0], list):
                    story_analyses = [item for sublist in story_analyses for item in sublist]
                
                for analysis in story_analyses:
                    story_idx = analysis['index'] - 1  # Convert to 0-based
                    if 0 <= story_idx < len(all_stories):
                        story = all_stories[story_idx]
                        
                        # Extract key terms for deduplication check
                        story_keywords = set(word.lower() for word in story.title.split() 
                                           if len(word) > 3 and word.isalpha())
                        
                        # Check for significant overlap with existing stories
                        overlap_threshold = 0.4  # 40% keyword overlap indicates duplicate
                        is_duplicate = False
                        
                        for existing_keywords in seen_keywords:
                            if existing_keywords and story_keywords:
                                overlap = len(story_keywords & existing_keywords) / len(story_keywords | existing_keywords)
                                if overlap > overlap_threshold:
                                    is_duplicate = True
                                    print(f"   🔄 Skipping potential duplicate: '{story.title[:50]}...' (overlap: {overlap:.2f})")
                                    break
                        
                        if not is_duplicate:
                            story.theme = theme
                            story.significance_score = analysis['significance']
                            theme_stories.append(story)
                            seen_keywords.add(frozenset(story_keywords))
                
                if theme_stories:
                    # Sort by significance score
                    theme_stories.sort(key=lambda x: x.significance_score or 0, reverse=True)
                    themes[theme] = theme_stories
                    print(f"   🎯 {theme.capitalize()}: {len(theme_stories)} stories (AI analyzed, duplicates removed)")
            
            return themes
            
        except Exception as e:
            print(f"   ⚠️ AI analysis failed: {e}")
            print("   🚨 CRITICAL: Cannot continue without AI analysis")
            raise Exception(f"AI Analysis failed and fallback is not acceptable for professional service: {e}")
    
    def fallback_categorization(self, all_stories: List[NewsStory]) -> Dict[str, List[NewsStory]]:
        """
        Fallback to keyword-based categorization if AI fails, with deduplication
        """
        theme_keywords = {
            'politics': ['government', 'minister', 'parliament', 'election', 'policy', 'mp', 'labour', 'conservative'],
            'economy': ['economy', 'inflation', 'bank', 'interest', 'market', 'business', 'financial', 'gdp'],
            'health': ['health', 'nhs', 'medical', 'hospital', 'covid', 'vaccine', 'doctor'],
            'international': ['ukraine', 'russia', 'china', 'usa', 'europe', 'war', 'conflict'],
            'climate': ['climate', 'environment', 'green', 'carbon', 'renewable', 'energy'],
            'technology': ['technology', 'tech', 'ai', 'digital', 'cyber', 'internet'],
            'crime': ['police', 'court', 'crime', 'arrest', 'investigation', 'trial']
        }
        
        themes = {}
        for theme, keywords in theme_keywords.items():
            theme_stories = []
            seen_keywords = set()  # Track keywords to prevent similar stories
            
            for story in all_stories:
                if any(keyword in story.title.lower() for keyword in keywords):
                    # Extract key terms for deduplication check
                    story_keywords = set(word.lower() for word in story.title.split() 
                                       if len(word) > 3 and word.isalpha())
                    
                    # Check for significant overlap with existing stories
                    overlap_threshold = 0.5  # 50% overlap for fallback mode (more strict)
                    is_duplicate = False
                    
                    for existing_keywords in seen_keywords:
                        if existing_keywords and story_keywords:
                            overlap = len(story_keywords & existing_keywords) / len(story_keywords | existing_keywords)
                            if overlap > overlap_threshold:
                                is_duplicate = True
                                break
                    
                    if not is_duplicate:
                        story.theme = theme
                        theme_stories.append(story)
                        seen_keywords.add(frozenset(story_keywords))
            
            if len(theme_stories) >= 2:
                themes[theme] = theme_stories
        
        return themes
    
    def get_synthesis_prompt(self, theme: str, stories: List[NewsStory]) -> str:
        """Generate language-specific synthesis prompt from config"""
        headlines = chr(10).join([f"- {story.title}" for story in stories[:3]])
        
        # Get the template for this language, fallback to en_GB
        prompt_config = AI_PROMPTS_CONFIG['synthesis_prompts'].get(
            self.language, 
            AI_PROMPTS_CONFIG['synthesis_prompts']['en_GB']
        )
        
        # Format the template with theme and headlines
        return prompt_config['template'].format(theme=theme, headlines=headlines)
    
    def get_system_message(self) -> str:
        """Generate language-specific system message for AI"""
        return AI_PROMPTS_CONFIG['system_messages'].get(
            self.language, 
            AI_PROMPTS_CONFIG['system_messages']['en_GB']
        )

    async def ai_synthesize_content(self, theme: str, stories: List[NewsStory]) -> str:
        """
        Use GitHub AI to create intelligent, coherent content synthesis
        """
        if not self.ai_enabled:
            raise Exception("🚨 CRITICAL: AI Analysis is REQUIRED. Cannot produce professional news digest without AI analysis.")
        
        if not stories:
            return ""
        
        try:
            story_info = []
            for story in stories[:5]:  # Top 5 stories
                info = f"- {story.title} (Source: {story.source}"
                if story.significance_score:
                    info += f", Significance: {story.significance_score}/10"
                info += ")"
                story_info.append(info)
            
            sources = list(set(story.source for story in stories))
            
            ai_prompt = self.get_synthesis_prompt(theme, stories)
            
            # Use Anthropic Claude for content synthesis with config settings
            ai_model_config = AI_PROMPTS_CONFIG['ai_model']
            system_msg = self.get_system_message()
            response = self.anthropic_client.messages.create(
                model=ai_model_config['name'],
                max_tokens=ai_model_config['synthesis_max_tokens'],
                temperature=ai_model_config['synthesis_temperature'],
                messages=[
                    {"role": "user", "content": f"{system_msg} {ai_prompt}"}
                ]
            )
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"   ⚠️ AI synthesis failed for {theme}: {e}")
            print("   🚨 CRITICAL: Cannot continue without AI analysis")
            raise Exception(f"AI Analysis failed and fallback is not acceptable for professional service: {e}")
    
    
    async def create_ai_enhanced_digest(self, all_stories: List[NewsStory]) -> str:
        """
        Create comprehensive digest using AI analysis
        """
        today = date.today().strftime("%B %d, %Y")
        
        # AI analyze all stories
        themes = await self.ai_analyze_stories(all_stories)
        
        if not themes:
            return "No significant news themes identified today."
        
        # Create language-specific introduction
        greeting = self.config['greeting']
        service_name = self.config['service_name']
        region_name = self.config.get('region_name', 'UK')  # Default to UK if not specified
        
        # Language-specific openings with proper region naming
        if self.language == 'fr_FR':
            digest = f"{greeting}. Voici votre résumé d'actualités {region_name} pour {today}, présenté par Dynamic Devices. "
        elif self.language == 'de_DE':
            digest = f"{greeting}. Hier ist Ihre {region_name} Nachrichtenzusammenfassung für {today}, präsentiert von Dynamic Devices. "
        elif self.language == 'es_ES':
            digest = f"{greeting}. Aquí está su resumen de noticias {region_name} para {today}, presentado por Dynamic Devices. "
        elif self.language == 'it_IT':
            digest = f"{greeting}. Ecco il vostro riepilogo delle notizie {region_name} per {today}, presentato da Dynamic Devices. "
        elif self.language == 'nl_NL':
            digest = f"{greeting}. Hier is uw {region_name} nieuwsoverzicht voor {today}, gepresenteerd door Dynamic Devices. "
        else:  # English variants (en_GB, en_GB_LON, en_GB_LIV)
            digest = f"{greeting}. Here's your {region_name} news digest for {today}, brought to you by Dynamic Devices. "
        
        # Add AI-synthesized content for each theme
        for theme, stories in themes.items():
            if stories:
                theme_content = await self.ai_synthesize_content(theme, stories)
                if theme_content:
                    digest += f"\n\n{theme_content}"
        
        # Language-specific closing
        if self.language == 'fr_FR':
            digest += "\n\nCe résumé fournit une synthèse des actualités les plus importantes d'aujourd'hui. "
            digest += "Tout le contenu est une analyse originale conçue pour l'accessibilité. "
            digest += "Pour une couverture complète, visitez directement les sites d'actualités."
        elif self.language == 'de_DE':
            digest += "\n\nDiese Zusammenfassung bietet eine Synthese der wichtigsten Nachrichten von heute. "
            digest += "Alle Inhalte sind ursprüngliche Analysen, die für die Barrierefreiheit entwickelt wurden. "
            digest += "Für eine vollständige Berichterstattung besuchen Sie direkt die Nachrichten-Websites."
        elif self.language == 'es_ES':
            digest += "\n\nEste resumen proporciona una síntesis de las noticias más importantes de hoy. "
            digest += "Todo el contenido es un análisis original diseñado para la accesibilidad. "
            digest += "Para una cobertura completa, visite directamente los sitios web de noticias."
        elif self.language == 'it_IT':
            digest += "\n\nQuesto riepilogo fornisce una sintesi delle notizie più importanti di oggi. "
            digest += "Tutti i contenuti sono analisi originali progettate per l'accessibilità. "
            digest += "Per una copertura completa, visitate direttamente i siti web di notizie."
        elif self.language == 'nl_NL':
            digest += "\n\nDeze samenvatting biedt een synthese van het belangrijkste nieuws van vandaag. "
            digest += "Alle inhoud is originele analyse ontworpen voor toegankelijkheid. "
            digest += "Voor volledige dekking, bezoek direct de nieuwswebsites."
        else:  # English variants
            digest += "\n\nThis digest provides a synthesis of today's most significant news stories. "
            digest += "All content is original analysis designed for accessibility. "
            digest += "For complete coverage, visit news websites directly."
        
        return digest
    
    async def generate_audio_digest(self, digest_text: str, output_filename: str):
        """
        Generate professional audio from AI-synthesized digest using Edge TTS with retry logic
        """
        print(f"\n🎤 Generating AI-enhanced audio: {output_filename}")
        
        # Get TTS settings from config
        tts_settings = VOICE_CONFIG['tts_settings']['edge_tts']
        max_retries = tts_settings['max_retries']
        retry_delay = tts_settings['initial_retry_delay']
        retry_backoff = tts_settings['retry_backoff_multiplier']
        force_ipv4 = tts_settings['force_ipv4']
        
        # Force IPv4 by monkey-patching socket.getaddrinfo to filter out IPv6 addresses
        # This is necessary because GitHub Actions runners have broken IPv6 connectivity
        import socket
        original_getaddrinfo = socket.getaddrinfo
        
        def getaddrinfo_ipv4_only(*args, **kwargs):
            """Wrapper that filters out IPv6 addresses"""
            results = original_getaddrinfo(*args, **kwargs)
            # Filter to only IPv4 (AF_INET)
            return [res for res in results if res[0] == socket.AF_INET]
        
        current_retry_delay = retry_delay
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"   🔄 Retry attempt {attempt + 1}/{max_retries}")
                    
                # Ensure the directory exists
                os.makedirs(os.path.dirname(output_filename), exist_ok=True)
                
                # Apply IPv4-only patch if configured
                if force_ipv4:
                    socket.getaddrinfo = getaddrinfo_ipv4_only
                
                try:
                    communicate = edge_tts.Communicate(digest_text, self.voice_name)
                    with open(output_filename, "wb") as file:
                        async for chunk in communicate.stream():
                            if chunk["type"] == "audio":
                                file.write(chunk["data"])
                finally:
                    # Restore original getaddrinfo
                    if force_ipv4:
                        socket.getaddrinfo = original_getaddrinfo
                
                print(f"   ✅ Edge TTS audio generated successfully")
                break  # Success, exit retry loop
                
            except Exception as e:
                error_msg = str(e)
                print(f"   ⚠️ Edge TTS attempt {attempt + 1} failed: {error_msg}")
                
                # Check error type for appropriate retry strategy
                is_network_error = ("Network is unreachable" in error_msg or 
                                  "Cannot connect" in error_msg or
                                  "Connection refused" in error_msg or
                                  "Temporary failure" in error_msg)
                is_auth_error = ("401" in error_msg or 
                               "authentication" in error_msg.lower() or 
                               "handshake" in error_msg.lower())
                
                if (is_network_error or is_auth_error) and attempt < max_retries - 1:
                    # Retryable error and not the last attempt
                    print(f"   ⏳ {'Network' if is_network_error else 'Authentication'} issue detected, waiting {current_retry_delay} seconds before retry...")
                    await asyncio.sleep(current_retry_delay)
                    current_retry_delay = min(current_retry_delay * retry_backoff, 30)  # Exponential backoff, max 30s
                    continue
                elif attempt == max_retries - 1:
                    # Last attempt failed - NEVER fall back to gTTS
                    print(f"   ❌ All {max_retries} retry attempts exhausted")
                    print(f"   🎤 CRITICAL: VOICE QUALITY PROTECTED - No fallback to robotic voice")
                    print(f"   🚫 Refusing to generate content with inferior voice quality")
                    print(f"   💡 This failure will trigger a re-run with proper Edge TTS")
                    raise Exception(f"Edge TTS failed after {max_retries} attempts: {error_msg}")
                else:
                    # Non-retryable error, fail fast
                    print(f"   ❌ Non-retryable Edge TTS error: {error_msg}")
                    print(f"   🎤 VOICE CONSISTENCY: Failing rather than degrading to robotic voice")
                    print(f"   📋 See GitHub Issue #17 for voice quality concerns")
                    raise Exception(f"Edge TTS failed with non-retryable error: {error_msg}")
        
        # Analyze the generated audio with error handling
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(output_filename)
            duration_s = len(audio) / 1000.0
            word_count = len(digest_text.split())
            words_per_second = word_count / duration_s if duration_s > 0 else 0
            file_size_kb = os.path.getsize(output_filename) / 1024
            
            print(f"   ✅ AI Audio created: {duration_s:.1f}s, {word_count} words, {words_per_second:.2f} WPS, {file_size_kb:.0f}KB")
            
        except Exception as analysis_error:
            print(f"   ⚠️ Audio analysis failed: {analysis_error}")
            # Return basic stats without analysis
            file_size_kb = os.path.getsize(output_filename) / 1024 if os.path.exists(output_filename) else 0
            word_count = len(digest_text.split())
            duration_s = word_count / 2.0  # Estimate 2 words per second
            words_per_second = 2.0
            
            print(f"   ✅ AI Audio created: {duration_s:.1f}s (estimated), {word_count} words, {words_per_second:.2f} WPS, {file_size_kb:.0f}KB")
        
        return {
            'filename': output_filename,
            'duration': duration_s,
            'words': word_count,
            'wps': words_per_second,
            'size_kb': file_size_kb
        }
    
    async def generate_daily_ai_digest(self):
        """
        Main function for AI-enhanced daily digest generation
        """
        print("🤖 GITHUB AI-ENHANCED NEWS DIGEST")
        print("🎯 Intelligent analysis for visually impaired users")
        print("⚖️ Copyright-compliant AI synthesis")
        print("=" * 60)
        
        # Check if today's files already exist
        today_str = date.today().strftime("%Y_%m_%d")
        text_filename = f"{self.config['output_dir']}/news_digest_ai_{today_str}.txt"
        audio_filename = f"{self.config['audio_dir']}/news_digest_ai_{today_str}.mp3"
        
        # Check if files exist AND audio file has reasonable size (>50KB)
        audio_size = os.path.getsize(audio_filename) if os.path.exists(audio_filename) else 0
        
        if os.path.exists(text_filename) and os.path.exists(audio_filename) and audio_size > 50000:
            print(f"\n💰 COST OPTIMIZATION: Today's content already exists")
            print(f"   ✅ Text: {text_filename}")
            print(f"   ✅ Audio: {audio_filename} ({audio_size:,} bytes)")
            print(f"   🚀 Skipping regeneration for efficiency")
            
            # Get existing file stats for summary
            audio_size_kb = os.path.getsize(audio_filename) / 1024
            
            print(f"\n🤖 EXISTING DIGEST SUMMARY")
            print("=" * 35)
            print(f"📅 Date: {date.today().strftime('%B %d, %Y')}")
            print(f"🎧 Audio: {audio_filename}")
            print(f"📄 Text: {text_filename}")
            print(f"💾 Size: {audio_size_kb:.1f} KB")
            print(f"🚀 Status: Using existing files (no regeneration needed)")
            
            return {
                'audio_file': audio_filename,
                'text_file': text_filename,
                'ai_enabled': self.ai_enabled,
                'regenerated': False,
                'size_kb': audio_size_kb
            }
        
        # Aggregate all stories
        all_stories = []
        for source_name, url in self.sources.items():
            stories = self.fetch_headlines_from_source(source_name, url)
            all_stories.extend(stories)
            time.sleep(1)  # Be respectful
        
        if not all_stories:
            print("❌ No stories found")
            return
        
        print(f"\n📊 Total stories collected: {len(all_stories)}")
        
        # Create AI-enhanced digest
        digest_text = await self.create_ai_enhanced_digest(all_stories)
        
        # Save files (only if they don't exist)
        
        # Save text with metadata
        # Ensure the directory exists for text file
        os.makedirs(os.path.dirname(text_filename), exist_ok=True)
        
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write("GITHUB AI-ENHANCED NEWS DIGEST\n")
            f.write("=" * 40 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"AI Analysis: {'ENABLED' if self.ai_enabled else 'DISABLED'}\n")
            f.write("Type: AI-synthesized content for accessibility\n")
            f.write("=" * 40 + "\n\n")
            f.write(digest_text)
        
        print(f"\n📄 AI digest text saved: {text_filename}")
        
        # Generate audio
        audio_stats = await self.generate_audio_digest(digest_text, audio_filename)
        
        # Summary
        print(f"\n🤖 AI-ENHANCED DIGEST COMPLETE")
        print("=" * 35)
        print(f"📅 Date: {date.today().strftime('%B %d, %Y')}")
        print(f"🤖 AI Analysis: {'ENABLED' if self.ai_enabled else 'FALLBACK MODE'}")
        print(f"📰 Stories: {len(all_stories)} from {len(self.sources)} sources")
        print(f"⏱️ Duration: {audio_stats['duration']:.1f}s")
        print(f"🎤 Speed: {audio_stats['wps']:.2f} WPS")
        print(f"🎧 Audio: {audio_filename}")
        print(f"📄 Text: {text_filename}")
        
        return {
            'audio_file': audio_filename,
            'text_file': text_filename,
            'stats': audio_stats,
            'ai_enabled': self.ai_enabled,
            'stories_analyzed': len(all_stories),
            'regenerated': True
        }

async def main():
    """
    Generate AI-enhanced daily digest using GitHub infrastructure with comprehensive error handling
    """
    parser = argparse.ArgumentParser(description='Generate multi-language AI news digest')
    parser.add_argument('--language', '-l', 
                       choices=['en_GB', 'fr_FR', 'de_DE', 'es_ES', 'it_IT', 'nl_NL', 'en_GB_LON', 'en_GB_LIV'], 
                       default='en_GB',
                       help='Language for news digest (default: en_GB)')
    
    args = parser.parse_args()
    
    print(f"🌍 Language: {LANGUAGE_CONFIGS[args.language]['native_name']}")
    print(f"🎤 Voice: {LANGUAGE_CONFIGS[args.language]['voice']}")
    print(f"📁 Output: {LANGUAGE_CONFIGS[args.language]['output_dir']}")
    
    try:
        print(f"🔧 Initializing digest generator...")
        digest_generator = GitHubAINewsDigest(language=args.language)
        print(f"✅ Digest generator initialized successfully")
        
        print(f"🚀 Starting digest generation...")
        result = await digest_generator.generate_daily_ai_digest()
        print(f"✅ Digest generation completed successfully")
        
        if result:
            print(f"\n🎉 SUCCESS: AI-enhanced digest ready!")
            print(f"   🤖 AI Analysis: {'ENABLED' if result['ai_enabled'] else 'FALLBACK'}")
            print(f"   🎧 Audio: {result['audio_file']}")
            print(f"   📄 Text: {result['text_file']}")
        else:
            print(f"\n⚠️ WARNING: No result returned from digest generation")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR in {args.language} generation:")
        print(f"   🔍 Error type: {type(e).__name__}")
        print(f"   📝 Error message: {str(e)}")
        
        # Print stack trace for debugging
        import traceback
        print(f"\n📋 Full stack trace:")
        traceback.print_exc()
        
        # Exit with error code
        print(f"\n💥 Exiting with error code 1")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
