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
        'title': 'AudioNews Daily',
        'subtitle': 'Daily UK News',
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
        'title': 'AudioNews Polska Daily',
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
        'title': 'BellaNews Daily',
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

def create_gradient_background(size, start_color, end_color, horizontal=False):
    """Create a gradient background (vertical by default, horizontal if specified)"""
    width, height = size
    image = Image.new('RGB', size, start_color)
    draw = ImageDraw.Draw(image)

    if horizontal:
        # Horizontal gradient (left to right)
        for x in range(width):
            ratio = x / width
            r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
            g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
            b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
            draw.line([(x, 0), (x, height)], fill=(r, g, b))
    else:
        # Vertical gradient (top to bottom)
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
    
    # Helper function to load and resize an image
    def load_and_resize_image(img_path, target_size):
        """Load an image and resize it to target size, handling transparency"""
        img = Image.open(img_path)
        img = img.convert('RGBA')
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        
        # Save as RGB (remove alpha channel if needed)
        if img.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', target_size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = background
        else:
            img = img.convert('RGB')
        return img
    
    # Special case: BellaNews uses custom image
    if language == 'bella':
        bella_path = Path('/home/ajlennon/Pictures/Bella-1.png')
        if bella_path.exists():
            bella_img = load_and_resize_image(bella_path, size)
            bella_img.save(output_path, 'PNG', optimize=True)
            print(f"✅ Generated: {output_path} (using Bella image)")
            return
        else:
            print(f"⚠️ Bella image not found at {bella_path}, using logo instead...")
    
    # Special case: en_GB and pl_PL use the main logo
    if language in ['en_GB', 'pl_PL']:
        logo_path = Path(__file__).parent.parent / 'docs' / 'images' / 'audionews_logo.png'
        if logo_path.exists():
            logo_img = load_and_resize_image(logo_path, size)
            logo_img.save(output_path, 'PNG', optimize=True)
            print(f"✅ Generated: {output_path} (using logo)")
            return
        else:
            print(f"⚠️ Logo not found at {logo_path}, generating standard cover...")

    # Convert colors to RGB
    start_rgb = hex_to_rgb(colors['gradient_start'])
    end_rgb = hex_to_rgb(colors['gradient_end'])
    primary_rgb = hex_to_rgb(colors['primary'])
    accent_rgb = hex_to_rgb(colors['accent'])
    text_rgb = hex_to_rgb(colors['text'])
    text_secondary_rgb = hex_to_rgb(colors['text_secondary'])

    # Create horizontal gradient background for landscape feel
    img = create_gradient_background(size, start_rgb, end_rgb, horizontal=True)
    draw = ImageDraw.Draw(img)

    # Convert to RGBA for transparency effects
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Add decorative elements with landscape-oriented positioning
    # Left side accent circles
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    add_circular_element(overlay_draw, (350, 350), 200, (*primary_rgb, 40), outline=None)
    add_circular_element(overlay_draw, (250, 700), 150, (*accent_rgb, 50), outline=None)
    add_circular_element(overlay_draw, (450, 1050), 180, (*primary_rgb, 35), outline=None)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Right side accent circles
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    add_circular_element(overlay_draw, (1050, 350), 180, (*accent_rgb, 45), outline=None)
    add_circular_element(overlay_draw, (1150, 700), 160, (*primary_rgb, 40), outline=None)
    add_circular_element(overlay_draw, (950, 1050), 140, (*accent_rgb, 50), outline=None)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Left side content area (for icon) - rounded rectangle effect
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    # Create a rounded rectangle area on the left
    left_area = (100, 200, 600, 1200)
    overlay_draw.rounded_rectangle(left_area, radius=80, fill=(*text_rgb, 200), outline=None)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Convert back to RGB for final rendering
    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)

    # Try to load a nice font, fallback to default
    try:
        # Try to use a system font - larger for landscape layout
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 140)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
        icon_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 300)
    except:
        try:
            # Try alternative font paths
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 140)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 90)
            icon_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 300)
        except:
            # Fallback to default font
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            icon_font = ImageFont.load_default()

    # Landscape-oriented layout: icon on left, text on right
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

    # Draw icon on the left side (in the rounded rectangle area)
    icon_x = 350  # Left side, centered vertically in the left area
    icon_y = 700
    try:
        # Try to center the emoji
        if hasattr(draw, 'textbbox'):
            icon_bbox = draw.textbbox((0, 0), icon_text, font=icon_font)
            icon_width = icon_bbox[2] - icon_bbox[0]
            icon_x = 350 - icon_width // 2
        # Use primary color for icon to contrast with white background
        draw.text((icon_x, icon_y), icon_text, font=icon_font, fill=primary_rgb, anchor='mm')
    except:
        # If emoji fails, just skip it
        pass

    # Draw title on the right side (landscape layout)
    title_x = 750  # Right side of center
    title_y = 600  # Upper portion
    draw.text((title_x, title_y), title_text, font=title_font, fill=text_rgb)

    # Draw subtitle on the right side, below title
    subtitle_x = 750
    subtitle_y = 600 + title_height + 30
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

    # Position URL on the right side, bottom (landscape layout)
    url_x = 750
    url_y = size[1] - 100
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
        output_path = output_dir / f'podcast-cover-{filename}-v2.png'
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
