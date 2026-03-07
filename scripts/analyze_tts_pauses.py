#!/usr/bin/env python3
"""
Text Analysis Tool for TTS Pause Detection

Analyzes transcript text to identify patterns that may cause unwanted pauses
in Text-to-Speech output. This tool helps diagnose and fix speech synthesis issues.

Usage:
    python3 scripts/analyze_tts_pauses.py <transcript_file>
    python3 scripts/analyze_tts_pauses.py docs/en_GB/news_digest_ai_2026_01_22.txt
"""

import re
import sys
import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Set


class TTSPauseAnalyzer:
    """Analyzes text for patterns that cause TTS pauses"""
    
    # Patterns that typically cause pauses in TTS
    PAUSE_TRIGGERS = {
        'periods': r'\.',
        'semicolons': r';',
        'commas': r',',
        'question_marks': r'\?',
        'exclamation_marks': r'!',
        'colons': r':',
        'ellipses': r'\.{2,}',
        'parentheses': r'[()]',
        'brackets': r'[\[\]]',
        'quotes': r'["\']',
        'em_dashes': r'—',
        'en_dashes': r'–',
        'hyphens': r'-',
    }
    
    # Patterns that may cause unnatural pauses
    PROBLEMATIC_PATTERNS = {
        'multiple_punctuation': r'[.!?]{2,}',
        'period_before_capital': r'\.\s+[A-Z]',
        'semicolon_before_capital': r';\s+[A-Z]',
        'comma_space_comma': r',\s+,',
        'trailing_punctuation': r'[.,;:]\s*$',
        'numbers_with_commas': r'\d{1,3}(?:,\d{3})+',
        'abbreviations': r'\b[A-Z]{2,}\b',
        'mixed_case_words': r'\b[A-Z][a-z]+[A-Z]',
    }
    
    def __init__(self, text: str):
        self.original_text = text
        self.text = text
        self.analysis_results = {}
        
    def analyze(self) -> Dict:
        """Run comprehensive analysis"""
        results = {
            'basic_stats': self._analyze_basic_stats(),
            'punctuation_analysis': self._analyze_punctuation(),
            'sentence_analysis': self._analyze_sentences(),
            'problematic_patterns': self._find_problematic_patterns(),
            'section_transitions': self._analyze_section_transitions(),
            'number_formatting': self._analyze_numbers(),
            'abbreviations': self._analyze_abbreviations(),
            'capitalization_issues': self._analyze_capitalization(),
            'recommendations': []
        }
        
        # Generate recommendations based on findings
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _analyze_basic_stats(self) -> Dict:
        """Basic text statistics"""
        words = self.text.split()
        sentences = re.split(r'[.!?]+\s+', self.text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return {
            'total_characters': len(self.text),
            'total_words': len(words),
            'total_sentences': len(sentences),
            'avg_words_per_sentence': len(words) / len(sentences) if sentences else 0,
            'avg_chars_per_word': sum(len(w) for w in words) / len(words) if words else 0,
            'total_paragraphs': len([p for p in self.text.split('\n\n') if p.strip()]),
        }
    
    def _analyze_punctuation(self) -> Dict:
        """Analyze punctuation usage"""
        punctuation_counts = {}
        punctuation_positions = defaultdict(list)
        
        for name, pattern in self.PAUSE_TRIGGERS.items():
            matches = list(re.finditer(pattern, self.text))
            punctuation_counts[name] = len(matches)
            punctuation_positions[name] = [
                {
                    'position': m.start(),
                    'context': self._get_context(m.start(), m.end(), 30)
                }
                for m in matches
            ]
        
        # Find consecutive punctuation
        consecutive_punct = list(re.finditer(r'[.,;:!?]{2,}', self.text))
        
        return {
            'counts': punctuation_counts,
            'positions': dict(punctuation_positions),
            'consecutive_punctuation': [
                {
                    'match': m.group(),
                    'position': m.start(),
                    'context': self._get_context(m.start(), m.end(), 30)
                }
                for m in consecutive_punct
            ],
            'punctuation_density': sum(punctuation_counts.values()) / len(self.text) if self.text else 0,
        }
    
    def _analyze_sentences(self) -> Dict:
        """Analyze sentence structure"""
        # Split by sentence endings
        sentences = re.split(r'([.!?]+\s+)', self.text)
        sentences = [s.strip() for s in sentences if s.strip() and not re.match(r'^[.!?]+$', s.strip())]
        
        sentence_lengths = [len(s.split()) for s in sentences]
        
        # Find very long sentences (potential pause issues)
        long_sentences = []
        for i, sentence in enumerate(sentences):
            word_count = len(sentence.split())
            if word_count > 30:  # Threshold for long sentences
                long_sentences.append({
                    'index': i + 1,
                    'word_count': word_count,
                    'sentence': sentence[:200] + '...' if len(sentence) > 200 else sentence,
                })
        
        # Find very short sentences (may cause choppy speech)
        short_sentences = []
        for i, sentence in enumerate(sentences):
            word_count = len(sentence.split())
            if word_count < 5:
                short_sentences.append({
                    'index': i + 1,
                    'word_count': word_count,
                    'sentence': sentence,
                })
        
        return {
            'total_sentences': len(sentences),
            'avg_words_per_sentence': sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0,
            'min_words': min(sentence_lengths) if sentence_lengths else 0,
            'max_words': max(sentence_lengths) if sentence_lengths else 0,
            'long_sentences': long_sentences,
            'short_sentences': short_sentences,
        }
    
    def _find_problematic_patterns(self) -> Dict:
        """Find patterns that may cause TTS issues"""
        issues = {}
        
        for pattern_name, pattern in self.PROBLEMATIC_PATTERNS.items():
            matches = list(re.finditer(pattern, self.text, re.MULTILINE))
            if matches:
                issues[pattern_name] = [
                    {
                        'match': m.group(),
                        'position': m.start(),
                        'context': self._get_context(m.start(), m.end(), 40)
                    }
                    for m in matches
                ]
        
        return issues
    
    def _analyze_section_transitions(self) -> Dict:
        """Analyze section transition patterns"""
        # Common section transition patterns
        transitions = {
            'in_news_patterns': list(re.finditer(r'[.;]\s+in\s+(politics|economy|health|international|climate|technology|crime)\s+news', 
                                                self.text, re.IGNORECASE)),
            'meanwhile_patterns': list(re.finditer(r'[.;]\s+meanwhile', self.text, re.IGNORECASE)),
            'turning_to_patterns': list(re.finditer(r'[.;]\s+turning\s+to', self.text, re.IGNORECASE)),
            'period_before_transition': list(re.finditer(r'\.\s+(In|Meanwhile|Turning|Here\'?s|Heres)', 
                                                         self.text, re.IGNORECASE)),
        }
        
        results = {}
        for name, matches in transitions.items():
            results[name] = [
                {
                    'match': m.group(),
                    'position': m.start(),
                    'context': self._get_context(m.start(), m.end(), 50),
                    'suggestion': 'Consider replacing period with semicolon for smoother transition'
                }
                for m in matches
            ]
        
        return results
    
    def _analyze_numbers(self) -> Dict:
        """Analyze number formatting"""
        # Find numbers with commas (e.g., 1,000,000)
        comma_numbers = list(re.finditer(r'\d{1,3}(?:,\d{3})+', self.text))
        
        # Find standalone numbers
        standalone_numbers = list(re.finditer(r'\b\d+\b', self.text))
        
        # Find number ranges
        number_ranges = list(re.finditer(r'\d+\s*[-–—]\s*\d+', self.text))
        
        return {
            'comma_separated_numbers': [
                {
                    'match': m.group(),
                    'position': m.start(),
                    'context': self._get_context(m.start(), m.end(), 30),
                    'suggestion': 'TTS may pause at commas - consider "one million" instead of "1,000,000"'
                }
                for m in comma_numbers
            ],
            'standalone_numbers': len(standalone_numbers),
            'number_ranges': [
                {
                    'match': m.group(),
                    'position': m.start(),
                    'context': self._get_context(m.start(), m.end(), 30)
                }
                for m in number_ranges
            ],
        }
    
    def _analyze_abbreviations(self) -> Dict:
        """Find abbreviations that may cause pauses"""
        # Common abbreviations
        abbreviations = list(re.finditer(r'\b[A-Z]{2,}\b', self.text))
        
        # Filter out common words that are all caps
        common_words = {'UK', 'US', 'EU', 'AI', 'CEO', 'NATO', 'MP', 'MPs'}
        
        found_abbrevs = []
        for m in abbreviations:
            word = m.group()
            if word not in common_words and len(word) >= 2:
                found_abbrevs.append({
                    'match': word,
                    'position': m.start(),
                    'context': self._get_context(m.start(), m.end(), 30),
                    'suggestion': 'TTS may spell out abbreviations letter-by-letter, causing pauses'
                })
        
        return {
            'abbreviations': found_abbrevs,
            'count': len(found_abbrevs),
        }
    
    def _analyze_capitalization(self) -> Dict:
        """Find capitalization issues"""
        # Words that start with capital after punctuation (may indicate sentence breaks)
        capital_after_punct = list(re.finditer(r'[.;]\s+([A-Z][a-z]+)', self.text))
        
        # All-caps words (may be read as acronyms)
        all_caps = list(re.finditer(r'\b[A-Z]{2,}\b', self.text))
        
        return {
            'capital_after_punctuation': len(capital_after_punct),
            'all_caps_words': [
                {
                    'match': m.group(),
                    'position': m.start(),
                    'context': self._get_context(m.start(), m.end(), 30)
                }
                for m in all_caps
            ],
        }
    
    def _get_context(self, start: int, end: int, context_len: int = 30) -> str:
        """Get context around a position"""
        context_start = max(0, start - context_len)
        context_end = min(len(self.text), end + context_len)
        context = self.text[context_start:context_end]
        
        # Mark the match
        match_start = start - context_start
        match_end = end - context_start
        marked = context[:match_start] + f'>>>{context[match_start:match_end]}<<<' + context[match_end:]
        
        return marked
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Check sentence length
        avg_words = results['sentence_analysis']['avg_words_per_sentence']
        if avg_words > 25:
            recommendations.append(
                f"⚠️ Average sentence length is {avg_words:.1f} words. "
                "Consider breaking long sentences into shorter ones using semicolons or commas."
            )
        
        # Check punctuation density
        punct_density = results['punctuation_analysis']['punctuation_density']
        if punct_density > 0.15:
            recommendations.append(
                f"⚠️ High punctuation density ({punct_density:.2%}). "
                "This may cause choppy speech. Consider reducing unnecessary punctuation."
            )
        
        # Check for period-before-transition patterns
        period_transitions = results['section_transitions'].get('period_before_transition', [])
        if period_transitions:
            recommendations.append(
                f"⚠️ Found {len(period_transitions)} period-before-transition patterns. "
                "Consider replacing periods with semicolons before section transitions for smoother flow."
            )
        
        # Check for long sentences
        long_sentences = results['sentence_analysis'].get('long_sentences', [])
        if long_sentences:
            recommendations.append(
                f"⚠️ Found {len(long_sentences)} very long sentences (>30 words). "
                "These may cause unnatural pauses. Consider breaking them up."
            )
        
        # Check for comma-separated numbers
        comma_numbers = results['number_formatting'].get('comma_separated_numbers', [])
        if comma_numbers:
            recommendations.append(
                f"⚠️ Found {len(comma_numbers)} comma-separated numbers. "
                "TTS may pause at commas. Consider spelling out large numbers."
            )
        
        # Check for abbreviations
        abbrevs = results['abbreviations'].get('abbreviations', [])
        if len(abbrevs) > 5:
            recommendations.append(
                f"⚠️ Found {len(abbrevs)} abbreviations. "
                "TTS may spell these out letter-by-letter, causing pauses."
            )
        
        if not recommendations:
            recommendations.append("✅ No major issues detected. Text structure looks good for TTS.")
        
        return recommendations


def print_analysis_report(results: Dict, filename: str):
    """Print formatted analysis report"""
    print("=" * 80)
    print(f"TTS PAUSE ANALYSIS REPORT")
    print(f"File: {filename}")
    print("=" * 80)
    print()
    
    # Basic Stats
    print("📊 BASIC STATISTICS")
    print("-" * 80)
    stats = results['basic_stats']
    print(f"  Total Characters: {stats['total_characters']:,}")
    print(f"  Total Words: {stats['total_words']:,}")
    print(f"  Total Sentences: {stats['total_sentences']}")
    print(f"  Avg Words/Sentence: {stats['avg_words_per_sentence']:.1f}")
    print(f"  Avg Chars/Word: {stats['avg_chars_per_word']:.1f}")
    print()
    
    # Punctuation Analysis
    print("🔤 PUNCTUATION ANALYSIS")
    print("-" * 80)
    punct = results['punctuation_analysis']
    print("  Counts:")
    for name, count in punct['counts'].items():
        if count > 0:
            print(f"    {name.replace('_', ' ').title()}: {count}")
    print(f"  Punctuation Density: {punct['punctuation_density']:.2%}")
    
    if punct['consecutive_punctuation']:
        print(f"\n  ⚠️ Found {len(punct['consecutive_punctuation'])} instances of consecutive punctuation:")
        for item in punct['consecutive_punctuation'][:5]:  # Show first 5
            print(f"    Position {item['position']}: {item['context']}")
    print()
    
    # Sentence Analysis
    print("📝 SENTENCE ANALYSIS")
    print("-" * 80)
    sent = results['sentence_analysis']
    print(f"  Total Sentences: {sent['total_sentences']}")
    print(f"  Avg Words/Sentence: {sent['avg_words_per_sentence']:.1f}")
    print(f"  Min Words: {sent['min_words']}")
    print(f"  Max Words: {sent['max_words']}")
    
    if sent['long_sentences']:
        print(f"\n  ⚠️ Found {len(sent['long_sentences'])} long sentences (>30 words):")
        for item in sent['long_sentences'][:3]:  # Show first 3
            print(f"    Sentence {item['index']} ({item['word_count']} words):")
            print(f"      {item['sentence']}")
    print()
    
    # Section Transitions
    print("🔄 SECTION TRANSITIONS")
    print("-" * 80)
    transitions = results['section_transitions']
    total_transitions = sum(len(v) for v in transitions.values())
    if total_transitions > 0:
        for name, items in transitions.items():
            if items:
                print(f"  {name.replace('_', ' ').title()}: {len(items)} found")
                for item in items[:2]:  # Show first 2
                    print(f"    {item['context']}")
    else:
        print("  No section transitions detected")
    print()
    
    # Problematic Patterns
    print("⚠️ PROBLEMATIC PATTERNS")
    print("-" * 80)
    problems = results['problematic_patterns']
    if problems:
        for name, items in problems.items():
            if items:
                print(f"  {name.replace('_', ' ').title()}: {len(items)} found")
                for item in items[:2]:  # Show first 2
                    print(f"    {item['context']}")
    else:
        print("  No problematic patterns detected")
    print()
    
    # Numbers
    print("🔢 NUMBER FORMATTING")
    print("-" * 80)
    numbers = results['number_formatting']
    if numbers['comma_separated_numbers']:
        print(f"  ⚠️ Found {len(numbers['comma_separated_numbers'])} comma-separated numbers:")
        for item in numbers['comma_separated_numbers'][:3]:
            print(f"    {item['match']} - {item['context']}")
    else:
        print("  No comma-separated numbers found")
    print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 80)
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"  {i}. {rec}")
    print()
    
    print("=" * 80)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/analyze_tts_pauses.py <transcript_file>")
        sys.exit(1)
    
    filename = sys.argv[1]
    filepath = Path(filename)
    
    if not filepath.exists():
        print(f"Error: File not found: {filename}")
        sys.exit(1)
    
    # Read file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract just the transcript text (skip header)
    lines = content.split('\n')
    transcript_start = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('GITHUB') and not line.startswith('=') and not line.startswith('Generated') and not line.startswith('AI') and not line.startswith('Type'):
            transcript_start = i
            break
    
    transcript_text = '\n'.join(lines[transcript_start:]).strip()
    
    # Analyze
    analyzer = TTSPauseAnalyzer(transcript_text)
    results = analyzer.analyze()
    
    # Print report
    print_analysis_report(results, filename)
    
    # Optionally save JSON report
    if len(sys.argv) > 2 and sys.argv[2] == '--json':
        json_file = filepath.with_suffix('.analysis.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 JSON report saved to: {json_file}")


if __name__ == '__main__':
    main()
