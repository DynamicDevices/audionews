"""
AI analysis and synthesis using Anthropic Claude.
"""

import json
import re
from typing import Dict, List, Any

from .models import NewsStory

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None


def ai_analyze_stories(
    anthropic_client: Any,
    language: str,
    all_stories: List[NewsStory],
    ai_prompts_config: dict,
) -> Dict[str, List[NewsStory]]:
    """Categorize and analyze stories with Claude; return themes -> list of NewsStory."""
    if not all_stories:
        raise ValueError("No stories to analyze")
    print("\n🤖 AI ANALYSIS: Intelligent story categorization")
    print("=" * 50)
    story_titles = [
        f"{i+1}. {s.title} (Source: {s.source})" for i, s in enumerate(all_stories)
    ]
    region_names = ai_prompts_config["analysis_prompt"]["region_names"]
    region_name = region_names.get(language, region_names["en_GB"])
    template = ai_prompts_config["analysis_prompt"]["template"]
    ai_prompt = template.format(
        region=region_name,
        headlines="\n".join(story_titles),
    )
    system_instruction = ai_prompts_config["analysis_prompt"]["system_instruction"].format(
        prompt=ai_prompt
    )
    model_cfg = ai_prompts_config["ai_model"]
    response = anthropic_client.messages.create(
        model=model_cfg["name"],
        max_tokens=model_cfg["analysis_max_tokens"],
        temperature=model_cfg["analysis_temperature"],
        messages=[{"role": "user", "content": system_instruction}],
    )
    response_text = response.content[0].text.strip()
    cleaned = response_text
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    try:
        ai_analysis = json.loads(cleaned)
    except json.JSONDecodeError as e:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            ai_analysis = json.loads(m.group())
        else:
            raise ValueError(f"Claude returned invalid JSON: {e}") from e

    themes = {}
    for theme, story_analyses in ai_analysis.items():
        theme_stories = []
        seen_keywords = set()
        if story_analyses and isinstance(story_analyses[0], list):
            story_analyses = [x for sub in story_analyses for x in sub]
        for analysis in story_analyses:
            idx = analysis["index"] - 1
            if idx < 0 or idx >= len(all_stories):
                continue
            story = all_stories[idx]
            keywords = frozenset(
                w.lower() for w in story.title.split()
                if len(w) > 3 and w.isalpha()
            )
            overlap_threshold = 0.4
            is_dup = False
            for existing in seen_keywords:
                if keywords and existing:
                    inter = len(keywords & existing) / len(keywords | existing)
                    if inter > overlap_threshold:
                        is_dup = True
                        print(f"   🔄 Skipping potential duplicate: '{story.title[:50]}...'")
                        break
            if not is_dup:
                story.theme = theme
                story.significance_score = analysis.get("significance")
                theme_stories.append(story)
                seen_keywords.add(keywords)
        if theme_stories:
            theme_stories.sort(key=lambda x: x.significance_score or 0, reverse=True)
            themes[theme] = theme_stories
            print(f"   🎯 {theme.capitalize()}: {len(theme_stories)} stories")
    return themes


def fallback_categorization(all_stories: List[NewsStory]) -> Dict[str, List[NewsStory]]:
    """Keyword-based categorization fallback with deduplication."""
    keywords_map = {
        "politics": ["government", "minister", "parliament", "election", "policy", "mp", "labour", "conservative"],
        "economy": ["economy", "inflation", "bank", "interest", "market", "business", "financial", "gdp"],
        "health": ["health", "nhs", "medical", "hospital", "covid", "vaccine", "doctor"],
        "international": ["ukraine", "russia", "china", "usa", "europe", "war", "conflict"],
        "climate": ["climate", "environment", "green", "carbon", "renewable", "energy"],
        "technology": ["technology", "tech", "ai", "digital", "cyber", "internet"],
        "crime": ["police", "court", "crime", "arrest", "investigation", "trial"],
    }
    themes = {}
    for theme, kws in keywords_map.items():
        theme_stories = []
        seen_kw = set()
        for story in all_stories:
            if not any(k in story.title.lower() for k in kws):
                continue
            story_kw = frozenset(
                w.lower() for w in story.title.split()
                if len(w) > 3 and w.isalpha()
            )
            is_dup = any(
                story_kw and ex and len(story_kw & ex) / len(story_kw | ex) > 0.5
                for ex in seen_kw
            )
            if not is_dup:
                story.theme = theme
                theme_stories.append(story)
                seen_kw.add(story_kw)
        if len(theme_stories) >= 2:
            themes[theme] = theme_stories
    return themes


def get_synthesis_prompt(
    language: str,
    theme: str,
    stories: List[NewsStory],
    previous_content: str,
    ai_prompts_config: dict,
) -> str:
    """Build synthesis prompt for a theme."""
    headlines = "\n".join(f"- {s.title}" for s in stories[:3])
    prompts = ai_prompts_config["synthesis_prompts"]
    prompt_cfg = prompts.get(language, prompts["en_GB"])
    theme_for_prompt = theme
    if language == "pl_PL":
        trans = {
            "politics": "polityka", "economy": "ekonomia", "health": "zdrowie",
            "international": "międzynarodowe", "climate": "klimat",
            "technology": "technologia", "crime": "przestępczość",
        }
        theme_for_prompt = trans.get(theme, theme)
    context = ""
    if previous_content:
        context = f"PREVIOUSLY COVERED CONTENT (DO NOT REPEAT):\n{previous_content}\n\n"
    return prompt_cfg["template"].format(
        theme=theme_for_prompt,
        headlines=headlines,
        previous_context=context,
    )


def get_system_message(language: str, ai_prompts_config: dict) -> str:
    """Return system message for the language."""
    return ai_prompts_config["system_messages"].get(
        language,
        ai_prompts_config["system_messages"]["en_GB"],
    )


async def ai_synthesize_content(
    anthropic_client: Any,
    language: str,
    theme: str,
    stories: List[NewsStory],
    previous_content: str,
    ai_prompts_config: dict,
) -> str:
    """Synthesize content for one theme using Claude."""
    prompt = get_synthesis_prompt(
        language, theme, stories, previous_content, ai_prompts_config
    )
    system_msg = get_system_message(language, ai_prompts_config)
    model_cfg = ai_prompts_config["ai_model"]
    response = anthropic_client.messages.create(
        model=model_cfg["name"],
        max_tokens=model_cfg["synthesis_max_tokens"],
        temperature=model_cfg["synthesis_temperature"],
        messages=[{"role": "user", "content": f"{system_msg} {prompt}"}],
    )
    return response.content[0].text.strip()
