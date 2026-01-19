#!/usr/bin/env python3
"""
Generate modern, vibrant podcast cover images for AudioNews
Creates 1400x1400px square images optimized for Spotify, Apple Podcasts, etc.
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

# Color schemes for each podcast
PODCAST_DESIGNS = {
    'en_GB': {
        'title': 'AudioNews UK',
        'subtitle': 'Daily News Digest',
        'colors': {
            'primary': '#1E3A8A',      # Deep blue (UK flag blue)
            'secondary': '#DC2626',      # Red (UK flag red)
            'accent': '#FBBF24',        # Gold accent
            'gradient_start': '#1E40AF', # Bright blue
            'gradient_end': '#3B82F6',   # Lighter blue
            'text': '#FFFFFF',           # White text
            'text_secondary': '#F3F4F6'  # Light gray
        },
        'icon': '🇬🇧'
    },
    'pl_PL': {
        'title': 'AudioNews Polska',
        'subtitle': 'Codzienny Przegląd Wiadomości',
        'colors': {
            'primary': '#DC2626',       # Red (Polish flag red)
            'secondary': '#FFFFFF',      # White (Polish flag white)
            'accent': '#FBBF24',         # Gold accent
            'gradient_start': '#EF4444', # Bright red
            'gradient_end': '#DC2626',   # Deep red
            'text': '#FFFFFF',            # White text
            'text_secondary': '#F3F4F6'  # Light gray
        },
        'icon': '🇵🇱'
    },
    'bella': {
        'title': 'BellaNews',
        'subtitle': 'Business & Finance',
        'colors': {
            'primary': '#059669',        # Emerald green (finance)
            'secondary': '#0D9488',      # Teal
            'accent': '#F59E0B',         # Amber (wealth/gold)
            'gradient_start': '#10B981', # Bright green
            'gradient_end': '#059669',   # Deep green
            'text': '#FFFFFF',            # White text
            'text_secondary': '#F3F4F6'  # Light gray
        },
        'icon': '💼'
    }
}

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_gradient_background(size, start_color, end_color):
    """Create a gradient background"""
    width, height = size
    image = Image.new('RGB', size, start_color)
    draw = ImageDraw.Draw(image)

    # Create gradient by drawing lines
    for y in range(height):
        ratio = y / height
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return image

def add_circular_element(draw, center, radius, color, outline=None, outline_width=0):
    """Add a circular design element"""
    x, y = center
    bbox = [x - radius, y - radius, x + radius, y + radius]
    draw.ellipse(bbox, fill=color, outline=outline, width=outline_width)

def generate_podcast_cover(language, output_path):
    """Generate a podcast cover image for the specified language"""
    design = PODCAST_DESIGNS[language]
    colors = design['colors']

    # Image size (Spotify recommends 1400x1400 minimum)
    size = (1400, 1400)

    # Convert colors to RGB
    start_rgb = hex_to_rgb(colors['gradient_start'])
    end_rgb = hex_to_rgb(colors['gradient_end'])
    primary_rgb = hex_to_rgb(colors['primary'])
    accent_rgb = hex_to_rgb(colors['accent'])
    text_rgb = hex_to_rgb(colors['text'])
    text_secondary_rgb = hex_to_rgb(colors['text_secondary'])

    # Create gradient background
    img = create_gradient_background(size, start_rgb, end_rgb)
    draw = ImageDraw.Draw(img)

    # Convert to RGBA for transparency effects
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Add decorative circular elements with transparency
    # Large background circle (subtle)
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    add_circular_element(overlay_draw, (700, 700), 600, (*primary_rgb, 30), outline=None)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Medium accent circle
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    add_circular_element(overlay_draw, (700, 500), 350, (*accent_rgb, 40), outline=None)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Small accent circles for visual interest
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    add_circular_element(overlay_draw, (300, 300), 120, (*accent_rgb, 50), outline=None)
    add_circular_element(overlay_draw, (1100, 1100), 150, (*primary_rgb, 40), outline=None)
    add_circular_element(overlay_draw, (1100, 300), 100, (*accent_rgb, 45), outline=None)
    add_circular_element(overlay_draw, (300, 1100), 130, (*primary_rgb, 35), outline=None)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Main content circle (white/light with transparency effect)
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    add_circular_element(overlay_draw, (700, 700), 400, (*text_rgb, 180),
                        outline=(*text_rgb, 255), outline_width=8)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Convert back to RGB for final rendering
    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)

    # Try to load a nice font, fallback to default
    try:
        # Try to use a system font
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        icon_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 200)
    except:
        try:
            # Try alternative font paths
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 120)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
            icon_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 200)
        except:
            # Fallback to default font
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            icon_font = ImageFont.load_default()

    # Calculate text positions (centered)
    title_text = design['title']
    subtitle_text = design['subtitle']
    icon_text = design['icon']

    # Get text bounding boxes
    if hasattr(draw, 'textbbox'):
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    else:
        # Fallback for older PIL versions
        title_bbox = draw.textsize(title_text, font=title_font)
        subtitle_bbox = draw.textsize(subtitle_text, font=subtitle_font)
        title_bbox = (0, 0, title_bbox[0], title_bbox[1])
        subtitle_bbox = (0, 0, subtitle_bbox[0], subtitle_bbox[1])

    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]

    # Draw icon (centered, above title)
    # Note: Emoji rendering may vary by system, but we'll try
    icon_x = 700
    icon_y = 500
    try:
        # Try to center the emoji
        if hasattr(draw, 'textbbox'):
            icon_bbox = draw.textbbox((0, 0), icon_text, font=icon_font)
            icon_width = icon_bbox[2] - icon_bbox[0]
            icon_x = (size[0] - icon_width) // 2
        draw.text((icon_x, icon_y), icon_text, font=icon_font, fill=text_rgb, anchor='mm')
    except:
        # If emoji fails, just skip it
        pass

    # Draw title (centered)
    title_x = (size[0] - title_width) // 2
    title_y = 700 - title_height // 2 - 60
    draw.text((title_x, title_y), title_text, font=title_font, fill=text_rgb)

    # Draw subtitle (centered, below title)
    subtitle_x = (size[0] - subtitle_width) // 2
    subtitle_y = 700 + title_height // 2 + 20
    draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=text_secondary_rgb)

    # Add "audionews.uk" at the bottom
    try:
        url_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        try:
            url_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        except:
            url_font = ImageFont.load_default()

    url_text = "audionews.uk"
    if hasattr(draw, 'textbbox'):
        url_bbox = draw.textbbox((0, 0), url_text, font=url_font)
        url_width = url_bbox[2] - url_bbox[0]
    else:
        url_size = draw.textsize(url_text, font=url_font)
        url_width = url_size[0]

    url_x = (size[0] - url_width) // 2
    url_y = size[1] - 80
    draw.text((url_x, url_y), url_text, font=url_font, fill=text_secondary_rgb)

    # Save the image
    img.save(output_path, 'PNG', optimize=True)
    print(f"✅ Generated: {output_path}")

def main():
    """Generate all podcast cover images"""
    print("🎨 Generating Podcast Cover Images\n")

    # Output directory
    output_dir = Path(__file__).parent.parent / 'docs' / 'images'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate covers for all languages
    filename_map = {
        'en_GB': 'en-gb',
        'pl_PL': 'pl-pl',
        'bella': 'bella'
    }

    for language in PODCAST_DESIGNS.keys():
        filename = filename_map.get(language, language.lower().replace('_', '-'))
        output_path = output_dir / f'podcast-cover-{filename}.png'
        try:
            generate_podcast_cover(language, output_path)
        except Exception as e:
            print(f"❌ Error generating cover for {language}: {e}")
            import traceback
            traceback.print_exc()

    print("\n✅ All podcast covers generated!")
    print("\n📋 Next steps:")
    print("   1. Review the generated images")
    print("   2. Commit and push to update the podcast feeds")
    print("   3. The images will be automatically used in RSS feeds")

if __name__ == '__main__':
    main()
